"""Blender helpers for the 3D critique pipeline (Roblox-bound assets). Blender 4.x/5.x.

Load it once per .blend into a text block, then each round:
    kit = bpy.data.texts["blender_kit.py"].as_module()
Units: 1 Blender unit = 1 stud unless you pass stud=.

  pov_camera(name, stand, look_at, eye_height=9.5, fov_v=70)  a camera where the player's eye really is
  render(cam, path, res=(1600, 900), samples=16, diag=None)    one view; diag="no_shadows" | "flat"
  palette_image(hexes, path=None)                              256 px atlas, 32 px cells, pixel-exact
  palette_material(img)                                        one material, Closest sampling
  map_faces(obj, index)                                        every face's UVs inside one cell
  verify_palette(objs, img, hexes)                             cells exact; each face in one cell, on a palette colour
  backfaces(cam, objs=None, res=(400, 225), mask_path=None)    pixels Roblox would cull (back faces in view)
  tris(objs=None)                                              triangles per mesh vs the 10k target / 20k cap
  reimport(path, expect=None)                                  re-import an FBX/OBJ: size, tris, UVs, materials
  import_studio_obj(path)                                      Studio OBJ with its 90° X rotation baked
  studio_setup_lua(model, default, rules)                      command-bar setup script for Studio
"""
import math, os
import bpy
from mathutils import Vector

SIZE, CELL = 256, 32
STUD_M = 0.28   # 1 stud = 0.28 m, so a metre/stud mix-up shows as 3.57x or 0.28x


# ---------- cameras and renders ----------

def pov_camera(name, stand, look_at, eye_height=9.5, fov_v=70.0, stud=1.0):
    """stand = (x, y, floor_z) where the player stands; Roblox third-person eye ~9.5 studs up, first-person ~5.
    Roblox's Camera.FieldOfView (default 70) is vertical, so the sensor fits vertically."""
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        bpy.context.scene.collection.objects.link(cam)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle_y = math.radians(fov_v)
    cam.data.clip_start, cam.data.clip_end = 0.1 * stud, 3000 * stud
    eye = Vector((stand[0], stand[1], stand[2] + eye_height * stud))
    cam.location = eye
    cam.rotation_euler = (Vector(look_at) - eye).to_track_quat("-Z", "Y").to_euler()
    return cam


def _gpu():
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except (KeyError, AttributeError):
        return False
    for kind in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
        except (TypeError, ValueError):
            continue
        gpus = [d for d in prefs.devices if d.type != "CPU"]
        if gpus:
            for d in prefs.devices:
                d.use = d.type != "CPU"
            return True
    return False


def render(cam, path, res=(1600, 900), samples=16, engine="CYCLES", diag=None):
    """diag="no_shadows": lights cast no shadows (settles "is that smear a shadow edge?").
    diag="flat": every material shows its base texture unlit, Standard view transform, so pixels equal palette hexes."""
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.engine = engine
    if engine == "CYCLES":
        sc.cycles.samples = samples
        sc.cycles.device = "GPU" if _gpu() else "CPU"
    sc.render.filepath = path
    undo = []
    if diag == "no_shadows":
        for L in bpy.data.lights:
            for owner, attr in ((L, "use_shadow"), (getattr(L, "cycles", None), "cast_shadow")):
                if owner is not None and hasattr(owner, attr):
                    undo.append((owner, attr, getattr(owner, attr)))
                    setattr(owner, attr, False)
    elif diag == "flat":
        undo.append((sc.view_settings, "view_transform", sc.view_settings.view_transform))
        undo.append((sc.render, "dither_intensity", sc.render.dither_intensity))
        sc.view_settings.view_transform, sc.render.dither_intensity = "Standard", 0.0
        for mat in bpy.data.materials:
            nt = mat.node_tree
            if not nt:
                continue
            out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None)
            tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None)
            if out and tex:
                old = [lk.from_socket for lk in out.inputs["Surface"].links]
                em = nt.nodes.new("ShaderNodeEmission")
                nt.links.new(tex.outputs["Color"], em.inputs["Color"])
                nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
                undo.append(("node", nt, em, out, old))
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        for u in reversed(undo):
            if u[0] == "node":
                _, nt, em, out, old = u
                nt.nodes.remove(em)
                for s in old:
                    nt.links.new(s, out.inputs["Surface"])
            else:
                setattr(u[0], u[1], u[2])
    return path


# ---------- palette atlas ----------

def _rgb(hx):
    hx = hx.lstrip("#")
    return tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4))


def _cell_box(k, size=SIZE, cell=CELL):
    """Cell k counts left to right, top to bottom as the PNG is viewed. Returns (u0, v0, u1, v1)."""
    n = size // cell
    col, row = k % n, k // n
    return col * cell / size, 1 - (row + 1) * cell / size, (col + 1) * cell / size, 1 - row * cell / size


def palette_image(hexes, name="Palette", path=None, size=SIZE, cell=CELL):
    n = size // cell
    if len(hexes) > n * n:
        raise ValueError(f"{len(hexes)} colours but only {n * n} cells")
    img = bpy.data.images.get(name) or bpy.data.images.new(name, size, size, alpha=False)
    if tuple(img.size) != (size, size):
        img.scale(size, size)
    px = [0.0, 0.0, 0.0, 1.0] * (size * size)
    for k, hx in enumerate(hexes):
        r, g, b = (c / 255 for c in _rgb(hx))
        u0, v0, _, _ = _cell_box(k, size, cell)
        x0, y0 = round(u0 * size), round(v0 * size)   # pixel rows start at the bottom, like UVs
        for y in range(y0, y0 + cell):
            for x in range(x0, x0 + cell):
                i = 4 * (y * size + x)
                px[i:i + 3] = (r, g, b)
    img.pixels.foreach_set(px)
    if path:
        img.filepath_raw, img.file_format = path, "PNG"
        img.save()
    return img


def palette_material(img, name="Palette"):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    if hasattr(mat, "use_nodes"):
        mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image, tex.interpolation = img, "Closest"
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.8
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def map_faces(obj, index, inset=4, size=SIZE, cell=CELL, uv_name="UVMap"):
    """index: one palette index for the whole mesh, a dict {face index: palette index}, or a function(face) -> index.
    Each face is projected on its main plane and fitted inside its cell, `inset` px clear of the cell edges
    so mipmaps never pull in a neighbour."""
    me = obj.data
    uv = me.uv_layers.get(uv_name) or me.uv_layers.new(name=uv_name)
    me.uv_layers.active = uv
    for f in me.polygons:
        k = index if isinstance(index, int) else (index(f) if callable(index) else index[f.index])
        u0, v0, u1, v1 = _cell_box(k, size, cell)
        d = inset / size
        u0, v0, u1, v1 = u0 + d, v0 + d, u1 - d, v1 - d
        drop = max(range(3), key=lambda i: abs(f.normal[i]))
        axes = [i for i in range(3) if i != drop]
        pts = [(me.vertices[me.loops[li].vertex_index].co[axes[0]], me.vertices[me.loops[li].vertex_index].co[axes[1]])
               for li in f.loop_indices]
        ax0, ax1 = min(p[0] for p in pts), max(p[0] for p in pts)
        ay0, ay1 = min(p[1] for p in pts), max(p[1] for p in pts)
        for li, (a, b) in zip(f.loop_indices, pts):
            s = (a - ax0) / (ax1 - ax0) if ax1 > ax0 else 0.5
            t = (b - ay0) / (ay1 - ay0) if ay1 > ay0 else 0.5
            uv.data[li].uv = (u0 + s * (u1 - u0), v0 + t * (v1 - v0))
    me.update()


def verify_palette(objs, img, hexes, inset=2, size=SIZE, cell=CELL):
    """(1) every cell's pixels equal its hex exactly; (2) every exported face keeps all its UVs inside one cell,
    at least `inset` px from the cell edges, and samples a palette colour. Returns a report dict and prints it."""
    n = size // cell
    px = list(img.pixels)
    at = lambda x, y: tuple(round(px[4 * (y * size + x) + c] * 255) for c in range(3))
    bad_cells = []
    for k, hx in enumerate(hexes):
        u0, v0, _, _ = _cell_box(k, size, cell)
        x0, y0 = round(u0 * size), round(v0 * size)
        want = _rgb(hx)
        wrong = sum(at(x, y) != want for y in range(y0, y0 + cell) for x in range(x0, x0 + cell))
        if wrong:
            bad_cells.append(f"cell {k} {hx}: {wrong} px differ")
    palette = {_rgb(h) for h in hexes}
    dg = bpy.context.evaluated_depsgraph_get()
    faces, spanning, near_edge, off = 0, [], [], []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        uv = me.uv_layers.active
        if uv is None:
            off.append(f"{o.name}: no UV map")
            ev.to_mesh_clear()
            continue
        for f in me.polygons:
            faces += 1
            us = [uv.data[li].uv for li in f.loop_indices]
            cells = {(min(n - 1, max(0, int(u * n))), min(n - 1, max(0, int((1 - v) * n)))) for u, v in us}
            if len(cells) > 1:
                spanning.append(f"{o.name} face {f.index}")
                continue
            edge = min(min(u * size % cell, cell - u * size % cell, v * size % cell, cell - v * size % cell) for u, v in us)
            if edge < inset:
                near_edge.append(f"{o.name} face {f.index} ({edge:.1f}px from edge)")
            uc, vc = sum(u for u, _ in us) / len(us), sum(v for _, v in us) / len(us)
            got = at(min(size - 1, int(uc * size)), min(size - 1, int(vc * size)))
            if got not in palette:
                off.append(f"{o.name} face {f.index} samples #{'%02x%02x%02x' % got}")
        ev.to_mesh_clear()
    rep = {"cells_exact": not bad_cells, "bad_cells": bad_cells, "faces": faces, "spanning": spanning,
           "near_edge": near_edge, "off_palette": off,
           "ok": not (bad_cells or spanning or near_edge or off)}
    print(f"palette: {len(hexes)} cells {'exact' if not bad_cells else 'WRONG'}; {faces} faces; "
          f"{len(spanning)} span two cells; {len(near_edge)} too close to a cell edge; {len(off)} off-palette")
    for line in (bad_cells + spanning + near_edge + off)[:20]:
        print("  ", line)
    return rep


# ---------- geometry checks ----------

def backfaces(cam, objs=None, res=(400, 225), mask_path=None):
    """Roblox culls back faces. Casts one ray per pixel from this (perspective) camera and counts the pixels
    whose first hit is a face seen from behind: those pixels change in Roblox. Same answer as a back-face-culled
    render diff, and it names the objects. Returns {object name: pixels}."""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    sc.render.resolution_x, sc.render.resolution_y = res
    mw = cam.matrix_world
    tr, br, bl, tl = [mw @ v for v in cam.data.view_frame(scene=sc)]
    origin = mw.translation
    names = {o.name for o in objs} if objs else None
    W, H = res
    counts, mask = {}, [0.0] * (W * H * 4)
    for j in range(H):
        for i in range(W):
            u, v = (i + 0.5) / W, (j + 0.5) / H
            p = tl.lerp(tr, u).lerp(bl.lerp(br, u), v)
            d = (p - origin).normalized()
            hit, _, nor, _, ob, _ = sc.ray_cast(dg, origin, d)
            k = 4 * ((H - 1 - j) * W + i)
            mask[k + 3] = 1.0
            if hit and nor.dot(d) > 0 and (names is None or ob.name in names):
                counts[ob.name] = counts.get(ob.name, 0) + 1
                mask[k] = 1.0
    if mask_path:
        img = bpy.data.images.new("_backface_mask", W, H, alpha=True)
        img.pixels.foreach_set(mask)
        img.filepath_raw, img.file_format = mask_path, "PNG"
        img.save()
        bpy.data.images.remove(img)
    print(f"back faces in view {cam.name}: " + (", ".join(f"{k} {v}px" for k, v in counts.items()) or "none"))
    return counts


def tris(objs=None, target=10000, cap=20000):
    dg = bpy.context.evaluated_depsgraph_get()
    rows = []
    for o in objs or [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        t = len(me.loop_triangles)
        ev.to_mesh_clear()
        rows.append((o.name, t, "OVER 20k CAP" if t > cap else ("over 10k target" if t > target else "")))
    flagged = [r for r in rows if r[2]]
    print(f"tris: {len(rows)} meshes, {sum(t for _, t, _ in rows):,} total, {len(flagged)} over the {target // 1000}k target")
    for name, t, flag in flagged:
        print(f"  {name}: {t:,} tris {flag}")
    return rows


def _bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return hi - lo


def reimport(path, expect=None, target=10000, cap=20000):
    """Import an exported .fbx/.obj into this scene, report what Roblox will get, then delete it again.
    expect = (x, y, z) size in studs of the whole model; a 3.57x or 0.28x mismatch means a metre/stud mix-up."""
    before, mats, imgs = set(bpy.data.objects), set(bpy.data.materials), set(bpy.data.images)
    if path.lower().endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        bpy.ops.wm.obj_import(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    size = _bbox(meshes) if meshes else Vector((0, 0, 0))
    rows = tris(meshes, target, cap)
    rep = {"file": os.path.basename(path), "meshes": len(meshes), "size": tuple(round(s, 2) for s in size),
           "tris": sum(t for _, t, _ in rows), "over_target": [n for n, t, _ in rows if t > target],
           "no_uv": [o.name for o in meshes if not o.data.uv_layers],
           "materials": sorted({s.material.name for o in meshes for s in o.material_slots if s.material})}
    if expect:
        ratio = [s / e for s, e in zip(sorted(size), sorted(expect)) if e]
        rep["ratio"] = [round(r, 2) for r in ratio]
        if all(abs(r - 1 / STUD_M) < 0.15 or abs(r - STUD_M) < 0.03 for r in ratio):
            rep["unit_warning"] = "size is off by 1/0.28 = 3.57: a metre/stud mix-up in the export or the importer"
        elif any(abs(r - 1) > 0.02 for r in ratio):
            rep["unit_warning"] = "size doesn't match the build"
    print(rep)
    for o in new:   # leave the .blend as it was
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    for m in set(bpy.data.materials) - mats:
        if m.users == 0:
            bpy.data.materials.remove(m)
    for i in set(bpy.data.images) - imgs:
        if i.users == 0:
            bpy.data.images.remove(i)
    return rep


def import_studio_obj(path):
    """Studio's OBJ export numbers parts Part1..N (in Studio they're all just "Part"), and it lands rotated
    90° about X. Imports it and bakes that rotation so measurements are true. Classify the parts by size or
    shape (see dims), never by these names. Returns the new mesh objects, largest first."""
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=path)
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in new:
        o.select_set(True)
    if new:
        bpy.context.view_layer.objects.active = new[0]
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    return sorted(new, key=lambda o: -(o.dimensions.x * o.dimensions.y * o.dimensions.z))


def dims(o):
    """Sorted world-space size (studs), for classifying parts by shape."""
    return tuple(sorted(round(v, 2) for v in _bbox([o])))


# ---------- Studio ----------

def _lua(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str) and v.split(".")[0] in ("Enum", "Color3", "Vector3", "BrickColor", "CFrame"):
        return v
    return '"' + str(v).replace('"', '\\"') + '"'


def studio_setup_lua(model, default, rules=()):
    """A script for Studio's command bar. default: {Property: value} for every BasePart under the model;
    rules: [(lua_name_pattern, {Property: value}), ...] applied after it, in order.
    Values like "Enum.CollisionFidelity.Box" are written as Lua, not strings."""
    tbl = lambda d: "{" + ", ".join(f"{k} = {_lua(v)}" for k, v in d.items()) + "}"
    lines = [f'-- Paste into Studio\'s command bar. Select the imported model, or name it "{model}" in Workspace.',
             f'local root = game.Selection:Get()[1] or workspace:FindFirstChild("{model}")',
             'assert(root, "select the imported model first")',
             f"local default = {tbl(default)}",
             "local rules = {"]
    lines += [f'  {{"{pat}", {tbl(props)}}},' for pat, props in rules]
    lines += ["}",
              "local n = 0",
              "for _, p in ipairs(root:GetDescendants()) do",
              '  if p:IsA("BasePart") then',
              "    for k, v in pairs(default) do p[k] = v end",
              "    for _, r in ipairs(rules) do",
              "      if p.Name:match(r[1]) then for k, v in pairs(r[2]) do p[k] = v end end",
              "    end",
              "    n += 1",
              "  end",
              "end",
              'print(("setup done: %d parts"):format(n))']
    return "\n".join(lines)
