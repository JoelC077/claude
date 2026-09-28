"""Trial helper (not part of rr-asset-foundry): siding POV renders + per-piece A5 pixel sizes for a wagon variant.

Why: the wagon family's POV stands the player on a 'next vehicle' coupled to the wagon, but canon
gameplay.train.layout is cab + coach only (D-013: no tender). The canon place for wagons is the yard:
world.prefabs.15 'Yard interior, sidings | 5 roads at 40 centres'. So the player sees a wagon from the coach
on the running line, 40 studs from the siding centre, as the world scrolls past (D-002).

python3 siding_pov.py VARIANT_DIR OUT_DIR [--eye3p 9.5 --eye1p 4.5 --floor 5 --centres 40 --half 8.7]
Renders siding_3p_abeam.png, siding_3p_approach.png, siding_1p_abeam.png (768x432, Cycles 16 spp) and prints
the smallest on-screen size (smaller side, px) of each key feature's pieces (mesh islands, not whole parts)
on the 400x225 3/4 view and on the abeam 3P POV.
"""
import argparse, glob, os, sys

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("variant"); ap.add_argument("out")
ap.add_argument("--eye3p", type=float, default=9.5); ap.add_argument("--eye1p", type=float, default=4.5)
ap.add_argument("--floor", type=float, default=5.0, help="coach floor above rail top (tech.units.stock_floor)")
ap.add_argument("--centres", type=float, default=40.0, help="running line to siding centres (world.prefabs.15)")
ap.add_argument("--half", type=float, default=8.7, help="half the coach width (tech.units.stock_width / 2)")
ap.add_argument("--keys", default="BufferHead,Door,DoorStrap,Strap,EndStrap,Patch,Lump")
a = ap.parse_args()

import bpy, bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
crit = next(iter(glob.glob(os.path.expanduser("~/.claude/skills/**/multiuse-critic/scripts"), recursive=True)
                 + glob.glob("/home/user/**/multiuse-critic/scripts", recursive=True)), None)
sys.path.insert(0, crit)
import blender_kit as bk

v = os.path.abspath(a.variant)
blend = glob.glob(os.path.join(v, "*.blend"))[0]
bpy.ops.wm.open_mainfile(filepath=blend)
asset = os.path.basename(blend)[:-6]
parts = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(asset + "_")]
lo = [min((o.matrix_world @ Vector(c))[i] for o in parts for c in o.bound_box) for i in range(3)]
hi = [max((o.matrix_world @ Vector(c))[i] for o in parts for c in o.bound_box) for i in range(3)]
cx = (lo[0] + hi[0]) / 2
y = -(a.centres - a.half - 0.7)          # player at the coach edge nearest the siding, 3/4 side of the stage
look = (cx, 0.0, a.floor + 1.0)
os.makedirs(a.out, exist_ok=True)
shots = [("siding_3p_abeam", (cx, y, a.floor), a.eye3p), ("siding_3p_approach", (cx + 50, y, a.floor), a.eye3p),
         ("siding_1p_abeam", (cx, y, a.floor), a.eye1p)]
for name, stand, eye in shots:
    cam = bk.pov_camera("Cam_" + name, stand, look, eye_height=eye, fov_v=70.0)
    bk.render(cam, os.path.join(a.out, name + ".png"), res=(768, 432), samples=16)


def islands(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    seen, out = set(), []
    for v0 in bm.verts:
        if v0.index in seen:
            continue
        stack, isl = [v0], []
        seen.add(v0.index)
        while stack:
            x = stack.pop(); isl.append(o.matrix_world @ x.co)
            for e in x.link_edges:
                w = e.other_vert(x)
                if w.index not in seen:
                    seen.add(w.index); stack.append(w)
        out.append(isl)
    bm.free()
    return out


def px(cam, res):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    bpy.context.view_layer.update()
    rows = {}
    for key in a.keys.split(","):
        best = None
        for o in parts:
            if f"_{key}_" not in o.name:          # exact part-name token, so Door does not match DoorStrap
                continue
            for isl in islands(o):
                pts = [world_to_camera_view(sc, cam, p) for p in isl]
                pts = [p for p in pts if p.z > 0 and 0 <= p.x <= 1 and 0 <= p.y <= 1]
                if len(pts) < 2:
                    continue
                w = (max(p.x for p in pts) - min(p.x for p in pts)) * res[0]
                h = (max(p.y for p in pts) - min(p.y for p in pts)) * res[1]
                s = min(w, h)
                if best is None or s < best[0]:
                    best = (round(s, 1), round(max(w, h), 1), o.name)
        if best:
            rows[key] = best
    return rows


for label, cam, res in (("3/4 400x225", bpy.data.objects["Cam_34"], (400, 225)),
                        ("siding 3P abeam 768x432", bpy.data.objects["Cam_siding_3p_abeam"], (768, 432))):
    r = px(cam, res)
    print(f"A5 {label}: " + "; ".join(f"{k} {s} px (long {l}) {n.split('_', 1)[1]}" for k, (s, l, n) in r.items()))
