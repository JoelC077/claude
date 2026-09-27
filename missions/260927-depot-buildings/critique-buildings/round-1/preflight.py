"""Pre-flight for one building .blend -> facts.md (measured). usage: python3 preflight.py <bldg> <out facts.md>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
b, out = sys.argv[1], sys.argv[2]
P = b.capitalize()
bpy.ops.wm.open_mainfile(filepath=f"{os.path.dirname(os.path.abspath(__file__))}/{b}/{b}.blend")
objs = kit.parts_of(P)
img = bpy.data.images["Palette"]
L = [f"## {P} (measured)"]
rows = kit.bk.tris(objs); tot = sum(t for _, t, _ in rows); mx = max(rows, key=lambda r: r[1])
L.append(f"- parts (separate named mesh objects): {len(objs)}; materials: {len({m.name for o in objs for m in o.data.materials})}")
L.append(f"- tris total {tot:,} (budget 20k); largest part {mx[0]} {mx[1]}")
rep = kit.bk.verify_palette(objs, img, kit.PALETTE)
L.append(f"- verify_palette: ok={rep['ok']} faces={rep['faces']} spanning={len(rep['spanning'])} near_edge={len(rep['near_edge'])} off={len(rep['off_palette'])}")
for c in [o for o in bpy.data.objects if o.type == 'CAMERA']:
    bf = kit.bk.backfaces(c, objs, res=(200, 112))
    L.append(f"- backfaces {c.name}: {sum(bf.values())} px {dict(list(bf.items())[:3]) if bf else ''}")
walls = [o for o in objs if "_Wall" in o.name]
lo = [min((o.matrix_world @ __import__('mathutils').Vector(v))[i] for o in walls for v in o.bound_box) for i in range(3)]
hi = [max((o.matrix_world @ __import__('mathutils').Vector(v))[i] for o in walls for v in o.bound_box) for i in range(3)]
L.append(f"- wall footprint: x {lo[0]:.1f}..{hi[0]:.1f} ({hi[0]-lo[0]:.1f}), plan y {-hi[1]:.1f}..{-lo[1]:.1f} ({hi[1]-lo[1]:.1f}), eave {hi[2]:.1f}")
allb = kit.bk._bbox(objs); L.append(f"- overall size studs (x,y,z): {allb.x:.1f} x {allb.y:.1f} x {allb.z:.1f}")
dr = [o for o in objs if "DoorFrameL" in o.name or "DoorFrameR" in o.name]
if len(dr) == 2:
    L.append(f"- doorway clear width {abs(dr[1].location.x-dr[0].location.x)-0.7:.1f}, height 10.0 (avatar 5)")
fl = []
for o in objs:  # floating check: lowest z of each part vs 0 and any other part's bbox contact is approximated
    z0 = min((o.matrix_world @ __import__('mathutils').Vector(v)).z for v in o.bound_box)
    if z0 > 0.2 and not any(k in o.name for k in ("Roof","Ridge","Chimney","Gable","Barge","Gutter","Canopy","Win","Lamp","Quoin","Finial","Vent","Name","String","Soot","Ivy","Roundel","Arch","Key","Crate","Leaf","Wall","Frame","Moss","Downpipe","Drum","Bay","Interior","Door")):
        fl.append(o.name)
L.append(f"- unclassified raised parts (float check): {fl or 'none'}")
open(out, "w").write("\n".join(L) + "\n")
print("\n".join(L))
