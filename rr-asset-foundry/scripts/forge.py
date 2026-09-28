"""Forge one variant inside Blender from a plan.json written by foundry.py: build, check, render, export.

  python3 forge.py PLAN.json [--render-only thumb|full] [--no-export]        (pip bpy)
  blender -b --factory-startup -P forge.py -- PLAN.json [...]                 (a Blender install)

Writes into plan["out"]: <Asset>.blend, <Asset>.fbx (plain, a material per recolour group), <Asset>_atlas.fbx +
palette.png, <Asset>_LOD1.fbx (option), parts.csv, studio_setup.lua, renders/*.png and result.json (every measured
check). foundry.py turns result.json into manifest.json, facts.md and README.md; call foundry.py, not this.
"""
import argparse, csv, json, math, os, re, sys, time

sys.dont_write_bytecode = True       # never leave __pycache__ in this or a sibling skill

RENDERS = {  # name: (camera, resolution, samples)
    "thumb": ("Cam_34", (320, 180), 10), "game": ("Cam_34", (400, 225), 16),
    "pov3p": ("Cam_POV_3P", (768, 432), 16), "pov1p": ("Cam_POV_1P", (768, 432), 16),
    "34": ("Cam_34", (640, 360), 16), "side": ("Cam_Side", (640, 360), 16), "end": ("Cam_End", (640, 360), 16),
    "top": ("Cam_Top", (640, 360), 16)}
SETS = {"none": [], "thumb": ["thumb", "game"], "full": ["thumb", "game", "pov3p", "pov1p", "34", "side", "end"]}


def args_after_dashes():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--render-only", choices=["thumb", "full"])
    ap.add_argument("--no-export", action="store_true")
    return ap.parse_args(argv)


def lin(hx):
    c = [int(hx.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1.0,)


def load_family(path):
    import importlib.util
    if os.path.dirname(path) not in sys.path:
        sys.path.insert(0, os.path.dirname(path))       # families share helpers (_rolling.py)
    spec = importlib.util.spec_from_file_location("family", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    a = args_after_dashes()
    plan = json.load(open(a.plan))
    sys.path[:0] = [plan["critic_scripts"], plan["foundry_scripts"]]
    import bpy
    from mathutils import Vector
    import blender_kit as bk
    import fkit
    out, asset = plan["out"], plan["asset"]
    os.makedirs(os.path.join(out, "renders"), exist_ok=True)
    fam = load_family(plan["family_file"])
    t0, res = time.time(), {"asset": asset, "timing": {}}
    rpath = os.path.join(out, "result.json")
    if a.render_only:
        old = json.load(open(rpath)) if os.path.isfile(rpath) else {}
        bpy.ops.wm.open_mainfile(filepath=os.path.join(out, f"{asset}.blend"))
        parts = [o for o in bpy.data.objects if o.get("rr_group") and o.name.startswith(asset + "_")]
        old.setdefault("renders", {}).update(render_set(bpy, bk, plan, out, a.render_only, parts, fkit, old))
        old["timing"]["render_only_s"] = round(time.time() - t0, 1)
        json.dump(old, open(rpath, "w"), indent=1)
        print(f"rendered {a.render_only} set in {time.time() - t0:.0f}s")
        return

    # ---------- scene ----------
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "NONE"
    img = bk.palette_image(plan["palette"], name="Palette", path=os.path.join(out, "palette.png"))
    mat = bk.palette_material(img)
    pmat = bpy.data.materials.new("Proxy")
    pmat.diffuse_color = (1, 0, 1, 0.3)
    coll = bpy.data.collections.new(asset)
    sc.collection.children.link(coll)

    # ---------- build ----------
    cells = {g: plan["cells"][g] for g in plan["groups"]}
    k = fkit.Kit(asset, cells, mat, pmat, coll, plan["params"], lod=0, seed=plan["seed"])
    fam.build(k, plan["params"])
    if plan["options"]["merge"] == "group":
        fkit.merge_groups(k)
    bpy.context.view_layer.update()
    parts, proxies = k.parts, k.proxies
    res["timing"]["build_s"] = round(time.time() - t0, 1)
    lo, hi = bbox(parts, Vector)
    size = [round(hi[i] - lo[i], 2) for i in range(3)]
    res.update(parts=len(parts), proxies=len(proxies), size=size, lo=[round(v, 2) for v in lo],
               hi=[round(v, 2) for v in hi], measures=k.measures, dropped_details=0)
    res["groups"] = {}
    for o in parts:
        res["groups"][o["rr_group"]] = res["groups"].get(o["rr_group"], 0) + 1

    # ---------- checks ----------
    cn = plan["canon"]
    rows = bk.tris(parts, target=cn["tris_target"], cap=cn["tris_cap"])
    tri_of = {n: t for n, t, _ in rows}
    top = max(rows, key=lambda r: r[1]) if rows else ("", 0, "")
    res["tris"] = {"total": sum(t for _, t, _ in rows), "max_part": top[1], "max_name": top[0],
                   "over_target": [n for n, t, _ in rows if t > cn["tris_target"]],
                   "over_cap": [n for n, t, _ in rows if t > cn["tris_cap"]]}
    pal = bk.verify_palette(parts, img, plan["palette"])
    res["palette"] = {k2: (v if isinstance(v, bool) else len(v) if isinstance(v, list) else v) for k2, v in pal.items()}
    res["names_bad"] = fkit.names(parts + proxies, asset)
    res["coplanar"] = [list(p) for p in fkit.coplanar(parts)]
    res["floating"] = fkit.floating(parts)
    res["timing"]["checks_s"] = round(time.time() - t0, 1)

    # ---------- stage, cameras, renders ----------
    stage(bpy, bk, plan, fam, parts, lo, hi, Vector)
    res["backfaces"] = {}
    for cam in ("Cam_34", "Cam_POV_3P"):
        bf = fkit.backfaces(bpy.data.objects[cam], parts, res=(200, 112))
        res["backfaces"][cam] = sum(bf.values())
        if bf:
            res.setdefault("backface_parts", {}).update(bf)
    res["features"] = fkit.feature_px(bpy.data.objects["Cam_34"], parts, plan["view"].get("features", []))
    res["renders"] = render_set(bpy, bk, plan, out, plan["options"]["renders"], parts, fkit, res)
    res["timing"]["renders_s"] = round(time.time() - t0, 1)
    if a.no_export:
        json.dump(res, open(rpath, "w"), indent=1)
        return

    # ---------- export ----------
    files = export(bpy, plan, out, asset, parts, proxies, mat, tri_of)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, f"{asset}.blend"), copy=True)
    files.append(f"{asset}.blend")
    rep = bk.reimport(os.path.join(out, f"{asset}.fbx"), expect=tuple(size))
    res["reimport"] = {k2: rep.get(k2) for k2 in ("meshes", "size", "tris", "ratio", "unit_warning", "no_uv")}
    lua = setup_lua(bk, plan, asset, bool(proxies))
    open(os.path.join(out, "studio_setup.lua"), "w").write(lua)
    files.append("studio_setup.lua")
    res["timing"]["export_s"] = round(time.time() - t0, 1)

    # ---------- LOD1 ----------
    if plan["options"]["lod"]:
        for o in parts + proxies:
            bpy.data.objects.remove(o)
        k1 = fkit.Kit(asset, cells, mat, pmat, coll, plan["params"], lod=1, seed=plan["seed"])
        fam.build(k1, plan["params"])
        for o in k1.proxies:
            bpy.data.objects.remove(o)
        k1.proxies = []
        lod_parts = fkit.merge_groups(k1, "Lod1")
        r1 = bk.tris(lod_parts, target=cn["tris_target"], cap=cn["tris_cap"])
        export_fbx(bpy, lod_parts, [], os.path.join(out, f"{asset}_LOD1.fbx"), plan, mat, plain=True)
        files.append(f"{asset}_LOD1.fbx")
        res["lod1"] = {"parts": len(lod_parts), "tris": sum(t for _, t, _ in r1), "dropped_details": k1.dropped,
                       "over_cap": [n for n, t, _ in r1 if t > cn["tris_cap"]]}
    res["files"] = files
    res["timing"]["total_s"] = round(time.time() - t0, 1)
    json.dump(res, open(rpath, "w"), indent=1)
    print(f"forge done: {asset} {len(parts)} parts, {res['tris']['total']} tris, {res['timing']['total_s']}s")


def bbox(objs, Vector):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return ([min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)])


# ---------- stage (render only; never exported) ----------

def _flat_mat(bpy, name, hx):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    if hasattr(m, "use_nodes"):
        m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = lin(hx)
    b.inputs["Roughness"].default_value = 0.9
    return m


def _stage_box(bpy, name, c, s, m, coll):
    import bmesh
    from mathutils import Vector
    bm = bmesh.new()
    vs = bmesh.ops.create_cube(bm, size=1.0)["verts"]
    bmesh.ops.scale(bm, vec=Vector(s), verts=vs)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    o.location = c
    me.materials.append(m)
    coll.objects.link(o)
    return o


def stage(bpy, bk, plan, fam, parts, lo, hi, Vector):
    sc, st, view = bpy.context.scene, plan["stage"], plan["view"]
    coll = bpy.data.collections.new("Stage")
    sc.collection.children.link(coll)
    w = bpy.data.worlds.new("World")
    sc.world = w
    if hasattr(w, "use_nodes"):
        w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = lin("#%02X%02X%02X" % tuple(st["ambient"]))
    bg.inputs[1].default_value = 1.6
    sun = bpy.data.objects.new("Stage_Sun", bpy.data.lights.new("Stage_Sun", "SUN"))
    sun.data.energy, sun.data.angle = 3.0, math.radians(3)
    sun.rotation_euler = (math.radians(50), 0, math.radians(35))
    coll.objects.link(sun)
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    ext = max(hi[0] - lo[0], hi[1] - lo[1], 8)
    gz = lo[2] if view.get("ground_z") is None else view["ground_z"]
    if view.get("stage") == "track":        # rails and ballast under rolling stock, from the same canon tokens
        g = plan["params"]["gauge"]
        rail, bal = _flat_mat(bpy, "Stage_Rail", st["rail"]), _flat_mat(bpy, "Stage_Ballast", st["ballast"])
        L = ext * 3
        for s in (-1, 1):
            _stage_box(bpy, f"Stage_Rail_{s}", (cx, s * g / 2, -0.6), (L, 0.8, 1.2), rail, coll)
        _stage_box(bpy, "Stage_Ballast", (cx, 0, -1.7), (L, 20, 1.0), bal, coll)
        gz = -2.2
    gz -= 0.02                       # the stage ground never shares a plane with the asset's underside
    ground = _stage_box(bpy, "Stage_Ground", (cx, cy, gz - 0.5), (ext * 12, ext * 12, 1.0),
                        _flat_mat(bpy, "Stage_Ground", st["ground"]), coll)
    n = int(view.get("tile_x", 0))                       # tiling pieces: copies show the seams
    offs = fam.tile_offsets(plan["params"]) if hasattr(fam, "tile_offsets") else \
        [s * i * plan["params"].get("length", 0) for i in range(1, n + 1) for s in (-1, 1)]
    for j, dx in enumerate(offs):
        for o in parts:
            c = o.copy()
            c.name = f"Stage_Tile{j}_{o.name}"
            c.location.x += dx
            coll.objects.link(c)
    # 5-stud stand-in avatar (legs, hazard vest, head) for scale
    # off the +x, +y corner: right of the asset in the 3/4, POV, side and end views, never in front of it
    av = fam.avatar(plan["params"], lo, hi) if hasattr(fam, "avatar") else (hi[0] + 2.5, hi[1] + 1.5, gz)
    ah = plan["canon"]["avatar_h"]
    for nm, c, s, key in (("Legs", (0, 0, 0.2 * ah), (2, 1, 0.4 * ah), "dark"),
                          ("Torso", (0, 0, 0.6 * ah), (2, 1, 0.4 * ah), "vest"),
                          ("Head", (0, 0, 0.9 * ah), (1.1, 1.1, 0.2 * ah), "skin")):
        _stage_box(bpy, f"Stage_Avatar{nm}", (av[0] + c[0], av[1] + c[1], av[2] + c[2]), s,
                   _flat_mat(bpy, f"Stage_Avatar{nm}", st["avatar"][key]), coll)
    # cameras
    focus = [min(lo[0], av[0] - 1), min(lo[1], av[1] - 1), min(lo[2], av[2])], \
            [max(hi[0], av[0] + 1), max(hi[1], av[1] + 1), max(hi[2], av[2] + ah)]
    c3 = Vector([(focus[0][i] + focus[1][i]) / 2 for i in range(3)])
    corners = [Vector((x, y, z)) for x in (focus[0][0], focus[1][0]) for y in (focus[0][1], focus[1][1])
               for z in (focus[0][2], focus[1][2])]
    d = Vector(view.get("dir34", (1.0, -1.3, 0.75))).normalized()
    cam34 = _cam(bpy, "Cam_34", c3 + d * 10, c3, view_deg=30)       # construction lens, not the player camera
    _fit(bpy, cam34, corners, c3, d)
    size = [hi[i] - lo[i] for i in range(3)]
    mid = Vector([(lo[i] + hi[i]) / 2 for i in range(3)])
    far = 10 * max(size) + 50
    _cam(bpy, "Cam_Side", mid + Vector((0, -far, 0)), mid, ortho=max(size[0], size[2] * 16 / 9) * 1.12)
    _cam(bpy, "Cam_End", mid + Vector((far, 0, 0)), mid, ortho=max(size[1], size[2] * 16 / 9) * 1.12)
    top = _cam(bpy, "Cam_Top", mid + Vector((0, 0, far)), mid, ortho=max(size[0], size[1] * 16 / 9) * 1.12)
    top.rotation_euler = (0, 0, 0)          # straight down, +y up in the frame
    if hasattr(fam, "pov"):
        stand, look = fam.pov(plan["params"], lo, hi)
    else:
        dd = Vector((0.45, -1, 0)).normalized() * max(14, 1.6 * max(size[0], size[1]))
        stand, look = (mid.x + dd.x, mid.y + dd.y, gz), tuple(mid)
    bk.pov_camera("Cam_POV_3P", stand, look, eye_height=plan["canon"]["eye_3p"], fov_v=plan["canon"]["fov_v"])
    bk.pov_camera("Cam_POV_1P", stand, look, eye_height=plan["canon"]["eye_1p"], fov_v=plan["canon"]["fov_v"])
    return cam34


def _fit(bpy, cam, pts, center, d, margin=0.06):
    """Move the camera along d until every point sits inside the 16:9 frame with a margin (binary search)."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 640, 360

    def fits(D):
        cam.location = center + d * D
        bpy.context.view_layer.update()
        for p in pts:
            v = world_to_camera_view(sc, cam, p)
            if v.z <= 0 or not (margin <= v.x <= 1 - margin and margin <= v.y <= 1 - margin):
                return False
        return True
    hi = max((p - center).length for p in pts)
    while not fits(hi):
        hi *= 1.5
    lo = hi / 3
    for _ in range(16):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if fits(mid) else (mid, hi)
    fits(hi)


def _cam(bpy, name, loc, look, view_deg=30, ortho=None, up="Y"):
    from mathutils import Vector
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    bpy.context.scene.collection.objects.link(cam)
    cam.data.sensor_fit = "VERTICAL" if ortho is None else "HORIZONTAL"
    cam.data.clip_start, cam.data.clip_end = 0.1, 20000
    if ortho:
        cam.data.type, cam.data.ortho_scale = "ORTHO", ortho
    else:
        cam.data.angle_y = math.radians(view_deg)
    cam.location = loc
    cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", up).to_euler()
    return cam


def render_set(bpy, bk, plan, out, which, parts, fkit, res):
    names = list(SETS.get(which, []))
    if which == "full" and plan["view"].get("top"):
        names.append("top")
    done = {}
    for n in names:
        cam, rr, samples = RENDERS[n]
        p = os.path.join(out, "renders", f"{n}.png")
        bk.render(bpy.data.objects[cam], p, res=rr, samples=samples)
        done[n] = os.path.relpath(p, out)
    return done


# ---------- export ----------

def export_fbx(bpy, parts, proxies, path, plan, atlas_mat, plain):
    groups = plan["groups"]
    if plain:
        for o in parts:
            g = o["rr_group"]
            m = bpy.data.materials.get(g) or bpy.data.materials.new(g)
            m.diffuse_color = lin(groups[g]["hex"])
            o.data.materials.clear()
            o.data.materials.append(m)
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts + proxies:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    kw = dict(filepath=path, use_selection=True, apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="FACE",
              bake_space_transform=True)
    if plain:
        bpy.ops.export_scene.fbx(path_mode="STRIP", **kw)
        for o in parts:
            o.data.materials.clear()
            o.data.materials.append(atlas_mat)
    else:
        bpy.ops.export_scene.fbx(path_mode="COPY", embed_textures=True, **kw)


def export(bpy, plan, out, asset, parts, proxies, atlas_mat, tri_of):
    files = []
    export_fbx(bpy, parts, proxies, os.path.join(out, f"{asset}.fbx"), plan, atlas_mat, plain=True)
    files.append(f"{asset}.fbx")
    if plan["options"]["atlas"]:
        export_fbx(bpy, parts, proxies, os.path.join(out, f"{asset}_atlas.fbx"), plan, atlas_mat, plain=False)
        files += [f"{asset}_atlas.fbx", "palette.png"]
    default, rules = collision(plan, bool(proxies))

    def collides(name):              # the same rules studio_setup.lua applies (plain Lua patterns)
        c = default
        for pat, props in rules:
            if "CanCollide" in props and re.search(pat.replace("%", "\\"), name):
                c = props["CanCollide"]
        return c
    with open(os.path.join(out, "parts.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "group", "token", "hex", "material", "palette_cell", "tris", "cancollide"])
        for o in sorted(parts, key=lambda o: o.name):
            g = plan["groups"][o["rr_group"]]
            w.writerow([o.name, o["rr_group"], g["token"], g["hex"], g["material"], plan["cells"][o["rr_group"]],
                        tri_of.get(o.name, ""), str(collides(o.name)).lower()])
        for o in proxies:
            w.writerow([o.name, "Proxy", "", "", "", "", 12, "true"])
    files.append("parts.csv")
    return files


def collision(plan, has_proxies):
    """(default CanCollide for visual parts, ordered rules): proxies collide and hide; LOD1 never collides;
    family rules last (e.g. climbable ladder rungs). A family with collide False collides nowhere."""
    collide = plan["options"]["collide"] and not has_proxies
    rules = [("_Collider_Proxy_", {"Transparency": 1, "CanCollide": True, "CastShadow": False,
                                   "CollisionFidelity": "Enum.CollisionFidelity.Box"}),
             ("_Lod1_", {"CanCollide": False, "CastShadow": False})]
    if plan["options"]["collide"]:
        rules += [(pat, props) for pat, props in plan["view"].get("rules", [])]
    return collide, rules


def setup_lua(bk, plan, asset, has_proxies):
    collide, rules = collision(plan, has_proxies)
    head = [f"-- {asset} (rr-asset-foundry {plan['family']}, preset {plan['preset']}). Studio command bar, model selected.",
            f"-- Collision: {'box proxies (Collider_Proxy parts) collide; visual parts do not' if has_proxies else ('visual parts collide' if collide else 'nothing collides (visual only)')}.",
            "-- Recolour: edit one GROUPS line and re-run. KEEP_ATLAS = true keeps the _atlas.fbx texture (Color is then hidden)."]
    body = bk.studio_setup_lua(asset, {"Anchored": True, "CanCollide": collide, "CastShadow": True}, rules)
    g = ["", "local KEEP_ATLAS = false", "local GROUPS = {"]
    for name, spec in plan["groups"].items():
        extra = f", reflectance = {spec['reflectance']}" if spec.get("reflectance") else ""
        g.append(f'  {name} = {{color = Color3.fromHex("{spec["hex"].lstrip("#")}"), '
                 f'material = Enum.Material.{spec["material"]}{extra}}}, -- {spec["token"]}')
    g += ["}",
          "local recoloured = 0",
          "for _, p in ipairs(root:GetDescendants()) do",
          '  if p:IsA("BasePart") then',
          '    local g = GROUPS[(p.Name:split("_")[3] or "")]',
          "    if g then",
          '      if p:IsA("MeshPart") and not KEEP_ATLAS then p.TextureID = "" end',
          "      if not KEEP_ATLAS then p.Color = g.color end",
          "      p.Material = g.material",
          "      if g.reflectance then p.Reflectance = g.reflectance end",
          "      recoloured += 1",
          "    end",
          "  end",
          "end",
          'print(("recolour groups applied to %d parts"):format(recoloured))']
    return "\n".join(head + [body] + g) + "\n"


if __name__ == "__main__":
    main()
