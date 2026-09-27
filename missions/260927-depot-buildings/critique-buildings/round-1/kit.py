"""Shared build kit for the Depot Lobby buildings (mission 260927-depot-buildings).
1 BU = 1 stud. Plan (x, y) -> Blender (x, -y), z up. One palette material, one mesh object per part."""
import math, os, sys
import bpy, bmesh
from mathutils import Vector, Matrix

CRITIC = "/home/user/claude/multiuse-critic/scripts"
sys.path.insert(0, CRITIC)
import blender_kit as bk  # noqa: E402

M = "/home/user/claude/missions/260927-depot-buildings"
PALETTE = ["#9a9384", "#7d776b", "#cabb8a", "#8f5a2a", "#b87a3d", "#4a4f57", "#2b2f36", "#6d7d43",
           "#1f2a33", "#e8c46a", "#b08a3e", "#f7f3e6", "#3a3f48", "#b1502b", "#b7a17a", "#8a4b36"]
C = dict(stone=0, stonedark=1, mortar=2, timber=3, timberlt=4, slate=5, iron=6, moss=7, dark=8,
         glow=9, brass=10, paving=11, soot=12, door=13, gravel=14, brick=15)
_state = {"mat": None, "img": None}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "NONE"
    img = bk.palette_image(PALETTE, path=os.path.join(M, "src", "palette.png"))
    _state["img"], _state["mat"] = img, bk.palette_material(img)
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.62, 0.70, 0.80, 1)
    bg.inputs[1].default_value = 0.9
    sun = bpy.data.objects.new("Stage_Sun", bpy.data.lights.new("Stage_Sun", "SUN"))
    sun.data.energy, sun.data.angle = 3.2, math.radians(3)
    sun.rotation_euler = (math.radians(50), 0, math.radians(35))
    sc.collection.objects.link(sun)
    sc.view_settings.view_transform = "AgX"
    return sc


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def _obj(name, bm, cell, collection, loc):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    me.materials.append(_state["mat"])
    collection.objects.link(ob)
    bk.map_faces(ob, cell)
    return ob


def box(name, center, size, cell, collection, rot=(0, 0, 0)):
    """Box centred at `center` (pivot = centre), size (sx, sy, sz), rotation in degrees."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if any(rot):
        R = Matrix.Rotation(math.radians(rot[2]), 4, "Z") @ Matrix.Rotation(math.radians(rot[1]), 4, "Y") @ Matrix.Rotation(math.radians(rot[0]), 4, "X")
        bmesh.ops.transform(bm, matrix=R, verts=bm.verts)
    return _obj(name, bm, cell, collection, center)


def prism(name, profile, depth, loc, cell, collection, axis="Y", rot_z=0):
    """Extrude a 2D profile [(a, z), ...] (counter-clockwise seen from +axis) by `depth` along Y (profile in XZ)
    or X (profile in YZ). Pivot at loc, profile centred in depth."""
    bm = bmesh.new()
    vs = []
    for a, z in profile:
        vs.append(bm.verts.new((a, -depth / 2, z) if axis == "Y" else (-depth / 2, a, z)))
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, depth, 0) if axis == "Y" else (depth, 0, 0), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if rot_z:
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(rot_z), 3, "Z"), verts=bm.verts)
    return _obj(name, bm, cell, collection, loc)


def cyl(name, center, r, h, cell, collection, segs=8, axis="Z", r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    if axis == "X":
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"), verts=bm.verts)
    elif axis == "Y":
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"), verts=bm.verts)
    return _obj(name, bm, cell, collection, center)


def gable_roof(prefix, x0, x1, ycen, depth, eave_z, ridge_z, collection, overhang=1.2, thick=0.8, axis="X", nn=1, tag=""):
    """Pitched roof, ridge along `axis` spanning x0..x1 (+ overhang at the ends), eaves at ycen +- depth/2.
    Returns [slab A, slab B, ridge cap]; slabs sit on top of the wall-plate line."""
    rise, run = ridge_z - eave_z, depth / 2
    ang = math.degrees(math.atan2(rise, run))
    drop = overhang * rise / run
    length = (x1 - x0) + 2 * overhang
    parts = []
    for s, t in ((1, "A"), (-1, "B")):
        p0 = Vector((ycen, ridge_z)); p1 = Vector((ycen + s * (run + overhang), eave_z - drop))
        mid = (p0 + p1) / 2
        n = Vector((s * rise, run)).normalized() * (thick / 2)
        slope = (p1 - p0).length + 0.6
        if axis == "X":
            parts.append(box(f"{prefix}_Roof{tag}{t}_Slate_{nn:02d}", ((x0 + x1) / 2, mid.x + n.x, mid.y + n.y),
                             (length, slope, thick), C["slate"], collection, rot=(-s * ang, 0, 0)))
        else:
            parts.append(box(f"{prefix}_Roof{tag}{t}_Slate_{nn:02d}", (mid.x + n.x, (x0 + x1) / 2, mid.y + n.y),
                             (slope, length, thick), C["slate"], collection, rot=(0, s * ang, 0)))
    rz = ridge_z + thick * 1.1
    if axis == "X":
        parts.append(box(f"{prefix}_RidgeCap{tag}_Iron_{nn:02d}", ((x0 + x1) / 2, ycen, rz), (length + 0.2, 1.3, 0.9), C["iron"], collection))
    else:
        parts.append(box(f"{prefix}_RidgeCap{tag}_Iron_{nn:02d}", (ycen, (x0 + x1) / 2, rz), (1.3, length + 0.2, 0.9), C["iron"], collection))
    return parts


def avatar(name, loc, collection):
    """5-stud stand-in: legs, torso, head (one object each, Stage only, not exported)."""
    x, y, z = loc
    box(f"{name}_Legs", (x, y, z + 1.0), (2, 1, 2), C["iron"], collection)
    box(f"{name}_Torso", (x, y, z + 3.0), (2, 1, 2), C["door"], collection)
    box(f"{name}_Head", (x, y, z + 4.5), (1.1, 1.1, 1.0), C["timberlt"], collection)


def milestone(prefix, k, stage, cams):
    """Numbered build-up frame(s) for R9: progress/<prefix>-<k>-<stage>-<cam>.png at 640x360."""
    out = []
    for tag, cam in cams:
        p = os.path.join(M, "progress", f"{prefix}-{k}-{stage}-{tag}.png")
        bk.render(cam, p, res=(640, 360), samples=12)
        out.append(p)
    return out


def cam(name, loc, look, lens_fov=50):
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    bpy.context.scene.collection.objects.link(c)
    c.data.sensor_fit = "VERTICAL"
    c.data.angle_y = math.radians(lens_fov)
    c.location = loc
    c.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return c


def parts_of(prefix):
    return [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(prefix + "_")]


# ---------- shared modules (both buildings) ----------

def window(P, nn, cx, face_y, z0, w, h, col, facing=1, arch=False, axis="X"):
    """Sash window on a wall plane at y=face_y (axis X wall) facing +y (facing=1) or -y. Parts: frame, glass, sill,
    lintel, mullion, transom. For axis 'Y' walls, cx is y and face_y is x."""
    f = facing
    def B(part, mat, c, s):
        if axis == "X":
            return box(f"{P}_Win{nn:02d}{part}_{mat}_01", (c[0], c[1], c[2]), s, C[mat.lower()], col)
        return box(f"{P}_Win{nn:02d}{part}_{mat}_01", (c[1], c[0], c[2]), (s[1], s[0], s[2]), C[mat.lower()], col)
    y = face_y + f * 0.15
    B("Glass", "Dark", (cx, y, z0 + h / 2), (w, 0.3, h))
    t = 0.45
    B("FrameL", "Timber", (cx - w / 2 - t / 2, y + f * 0.2, z0 + h / 2), (t, 0.5, h + t))
    B("FrameR", "Timber", (cx + w / 2 + t / 2, y + f * 0.2, z0 + h / 2), (t, 0.5, h + t))
    B("FrameT", "Timber", (cx, y + f * 0.2, z0 + h + t / 2), (w + 2 * t, 0.5, t))
    B("Mullion", "Timber", (cx, y + f * 0.25, z0 + h / 2), (0.3, 0.4, h))
    B("Transom", "Timber", (cx, y + f * 0.25, z0 + h * 0.55), (w, 0.4, 0.3))
    B("Sill", "Mortar", (cx, y + f * 0.45, z0 - 0.3), (w + 1.4, 1.1, 0.6))
    if arch:
        if axis == "X":
            prism(f"{P}_Win{nn:02d}Arch_Stonedark_01", [(-w / 2 - 0.9, 0), (w / 2 + 0.9, 0), (w / 2 + 0.9, 0.8), (0, 2.0), (-w / 2 - 0.9, 0.8)],
                  0.7, (cx, y + f * 0.2, z0 + h + t), C["stonedark"], col)
        else:
            prism(f"{P}_Win{nn:02d}Arch_Stonedark_01", [(-w / 2 - 0.9, 0), (w / 2 + 0.9, 0), (w / 2 + 0.9, 0.8), (0, 2.0), (-w / 2 - 0.9, 0.8)],
                  0.7, (y + f * 0.2, cx, z0 + h + t), C["stonedark"], col, axis="X")
    else:
        B("Lintel", "Stonedark", (cx, y + f * 0.3, z0 + h + t + 0.45), (w + 2.0, 0.8, 0.9))


def lamp(P, nn, x, y, z, col, h=10):
    """Iron railway lantern post: base, post, arm-less head with glowing glass."""
    cyl(f"{P}_Lamp{nn:02d}Base_Iron_01", (x, y, z + 0.5), 0.8, 1.0, C["iron"], col)
    cyl(f"{P}_Lamp{nn:02d}Post_Iron_01", (x, y, z + h / 2), 0.3, h, C["iron"], col, segs=6)
    box(f"{P}_Lamp{nn:02d}Glass_Glow_01", (x, y, z + h + 0.8), (1.3, 1.3, 1.6), C["glow"], col)
    prism(f"{P}_Lamp{nn:02d}Cap_Iron_01", [(-1.0, 0), (1.0, 0), (0, 1.0)], 2.0, (x, y, z + h + 1.6), C["iron"], col)
    box(f"{P}_Lamp{nn:02d}Collar_Brass_01", (x, y, z + h - 0.1), (1.5, 1.5, 0.4), C["brass"], col)


def crate(P, nn, x, y, z, s, col, rz=0):
    box(f"{P}_Crate{nn:02d}_Timberlt_01", (x, y, z + s / 2), (s, s, s), C["timberlt"], col, rot=(0, 0, rz))
    box(f"{P}_Crate{nn:02d}Band_Timber_01", (x, y, z + s / 2), (s + 0.1, s + 0.1, s * 0.25), C["timber"], col, rot=(0, 0, rz))


def drum(P, nn, x, y, z, col, cell="door"):
    cyl(f"{P}_Drum{nn:02d}_{cell.capitalize()}_01", (x, y, z + 1.5), 1.1, 3.0, C[cell], col, segs=10)
    cyl(f"{P}_Drum{nn:02d}Rim_Iron_01", (x, y, z + 2.2), 1.15, 0.3, C["iron"], col, segs=10)


def moss(P, nn, x, y, z, sx, sy, sz, col):
    box(f"{P}_Moss{nn:02d}_Moss_01", (x, y, z + sz / 2), (sx, sy, sz), C["moss"], col)
