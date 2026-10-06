"""T0 kit spec: the split kit for one carriage join, in the join frame J (studs).

J: origin = centre of the gangway union's bounding box; +X across (east), +Y up, +Z toward the REAR carriage.
From Joel's export: J origin = world (-58.114, 15.927, 117.226) with world axes (see refs/train.facts.md).
Coupling plane: z = ZC. Every part: which carriage owns it (front|rear), folder, Roblox class/shape, size, CFrame in J,
appearance, physics flags, and for moving parts the pose it swings to when the coupling snaps.

CFrame format everywhere: [x, y, z, R00, R01, R02, R10, R11, R12, R20, R21, R22]  (Roblox CFrame.new 12-number form,
row-major rotation; columns are RightVector, UpVector, -LookVector). Run: python3 kit_spec.py  -> kit_spec.json
"""
import json, math, os
import numpy as np

ZC = -0.35                      # coupling plane (world z 116.876)
FLOOR = -2.0                    # walkway top
PLATE_Y = (-2.2, -2.0)
POST_X = 4.35                   # posts at x = +-4.35
UNION = {"size": [9.7, 4.4, 7.3], "centre_world": [-58.114, 15.927, 117.226]}

IRON = [0x36, 0x3A, 0x42]       # style.world.ironwork
SOOT = [0x15, 0x18, 0x1B]       # style.world.soot_black
BRASS = [0xC9, 0x95, 0x3A]      # style.world.brass (Reflectance 0.12)
HAZARD = [0xF2, 0xC2, 0x30]     # style.brand.hazard_yellow
RUBBER = [0x1E, 0x1E, 0x20]
WALK = [163, 162, 165]          # union's own colour (copied from the live union at setup when possible)

parts = []


def R(ax='x', deg=0.0):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    if ax == 'x': return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if ax == 'y': return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def cf(pos, rot=None):
    rot = np.eye(3) if rot is None else rot
    return [round(float(v), 5) for v in list(pos) + list(rot.reshape(-1))]


def box(lo, hi):
    lo, hi = np.array(lo, float), np.array(hi, float)
    return ((lo + hi) / 2).tolist(), (hi - lo).tolist()


def add(name, side, folder, size, pos, rot=None, shape='Block', cls='Part', color=None, material='SmoothPlastic',
        refl=0.0, collide=True, deco=False, copy_union=False, anim=None, note=''):
    p = {"name": name, "side": side, "folder": folder, "class": cls, "shape": shape,
         "size": [round(float(v), 5) for v in size], "cf": cf(pos, rot),
         "color": color, "material": material, "reflectance": refl,
         "canCollide": collide and not deco, "canTouch": not deco, "canQuery": True, "castShadow": True,
         "massless": deco, "copyUnionLook": copy_union}
    if anim: p["anim"] = anim
    if note: p["note"] = note
    parts.append(p)
    return p


def hinge(pivot, axis, deg, delay, dur, style='Bounce', direction='Out'):
    return {"kind": "hinge", "pivot": [round(float(v), 5) for v in pivot], "axis": axis, "angle": deg,
            "delay": delay, "duration": dur, "style": style, "direction": direction}


def pose_after_hinge(p, anim):
    """Split pose of a hinged part: rotate its J CFrame about the pivot."""
    rot_h = R(anim["axis"], anim["angle"])
    pos = np.array(p["cf"][:3]); rot = np.array(p["cf"][3:]).reshape(3, 3)
    piv = np.array(anim["pivot"])
    return cf(piv + rot_h @ (pos - piv), rot_h @ rot)


# ---------------------------------------------------------------- walkway halves (rebuild of the union, cut at ZC)
GAP = 0.2                                   # open gap between the two plate ends, covered by the fall plate
F_END, R_START = ZC - GAP / 2, ZC + GAP / 2  # -0.45 / -0.25
for side, (z0, z1) in (("front", (-3.65, F_END)), ("rear", (R_START, 3.05))):
    c, s = box((-4.85, PLATE_Y[0], z0), (4.85, PLATE_Y[1], z1))
    add("RR_WalkPlate", side, "Walkway", s, c, material='DiamondPlate', color=WALK, copy_union=True,
        note="rebuilt union plate, cut at the coupling plane")
post_z = {"front": [-2.85, -1.85, -0.85], "rear": [0.15, 1.15, 2.15]}
for side, zs in post_z.items():
    for i, z in enumerate(zs):
        for sx, tag in ((-1, "W"), (1, "E")):
            add(f"RR_WalkPost_{tag}{i + 1}", side, "Walkway", [0.2, 4.2, 0.2], [sx * POST_X, 0.1, z],
                material='DiamondPlate', color=WALK, copy_union=True)
# rails end flush with the outer face of the end post of each half
for side, (z0, z1) in (("front", (-3.55, -0.75)), ("rear", (0.05, 2.95))):
    for sx, tag in ((-1, "W"), (1, "E")):
        c, s = box((sx * POST_X - 0.1, 2.0, z0), (sx * POST_X + 0.1, 2.2, z1))
        add(f"RR_WalkRail_{tag}", side, "Walkway", s, c, material='DiamondPlate', color=WALK, copy_union=True)

# hazard edge bars wrapping each cut plate end (0.02 proud of every plate face: no shared planes)
c, s = box((-4.86, -2.23, -0.74), (4.86, -1.97, F_END + 0.02))
add("RR_EdgeBar", "front", "Walkway", s, c, color=HAZARD, note="platform-edge nosing, reads as the split point")
c, s = box((-4.86, -2.23, R_START - 0.02), (4.86, -1.97, 0.04))
add("RR_EdgeBar", "rear", "Walkway", s, c, color=HAZARD)

# ---------------------------------------------------------------- fall plate, hinged at the front platform edge
PIV_FP = [0.0, -1.92, -0.37]
fp_anim = hinge(PIV_FP, 'x', 90.0, 0.18, 0.65, 'Bounce')
c, s = box((-3.0, -1.97, -0.43), (3.0, -1.85, 0.38))
fp = add("RR_FallPlate", "front", "Coupling", s, c, material='DiamondPlate', color=IRON, anim=dict(fp_anim),
         note="bridges the gap, rests on the rear edge bar; drops to hang when the rear car leaves")
# bevelled lip at the free end: WedgePart (tall at +Z local, thin at -Z local) turned 180 deg about Y -> thin toward +Z(J)
c, s = box((-3.0, -1.995, 0.38), (3.0, -1.85, 0.60))
add("RR_FallPlateLip", "front", "Coupling", s, c, R('y', 180), cls='WedgePart', shape='Wedge', material='DiamondPlate',
    color=IRON, anim=dict(fp_anim))
for i, x in enumerate((-2.2, 0.0, 2.2)):
    add(f"RR_HingeKnuckle_{i + 1}", "front", "Coupling", [0.6, 0.14, 0.14], [x, PIV_FP[1], PIV_FP[2]],
        shape='Cylinder', material='Metal', color=IRON, deco=True, anim=dict(fp_anim))

# ---------------------------------------------------------------- safety chains (one per side, front post -> rear post)
EYE_Y = 1.55
A_Z, B_Z, SAG, NL, LINK = -0.69, -0.01, 0.12, 3, 0.26
for sx, tag in ((-1, "W"), (1, "E")):
    x = sx * POST_X
    add(f"RR_ChainEye_{tag}", "front", "Coupling", [0.08, 0.08, 0.1], [x, EYE_Y, -0.70], material='Metal', color=IRON, deco=True)
    add(f"RR_ChainEye_{tag}", "rear", "Coupling", [0.08, 0.08, 0.1], [x, EYE_Y, 0.0], material='Metal', color=IRON, deco=True)
    for k in range(NL):
        s_ = (k + 0.5) / NL
        z = A_Z + (B_Z - A_Z) * s_
        y = EYE_Y - 4 * SAG * s_ * (1 - s_)
        dy = -4 * SAG * (1 - 2 * s_); dz = (B_Z - A_Z)
        tilt = math.degrees(math.atan2(-dy, dz))          # local Z follows the sag curve (third column = (0,-sin,cos))
        rot = R('x', tilt) @ R('z', 90 * (k % 2))          # follow the curve; alternate flat/edge links
        hang_rot = R('x', -90) @ R('z', 90 * (k % 2))       # long axis vertical
        hang_pos = [x, EYE_Y - 0.06 - LINK * 0.85 * (k + 0.5), -0.69]
        p = add(f"RR_ChainLink_{tag}{k + 1}", "front", "Coupling", [0.06, 0.12, LINK], [x, y, z], rot,
                material='Metal', color=IRON, deco=True)
        p["anim"] = {"kind": "pose", "pivot": [x, EYE_Y, -0.70], "splitCF": cf(hang_pos, hang_rot),
                     "delay": 0.10 + 0.05 * k, "duration": 0.5, "style": "Back", "direction": "Out"}

# ---------------------------------------------------------------- knuckle coupler pair on the centre line
HY, HH = -3.35, 0.9


def coupler(side):
    m = 1 if side == "front" else -1                  # mirror in z about ZC for the rear car
    def zz(a, b):                                     # front-side z range -> this side
        if m == 1: return a, b
        return 2 * ZC - b, 2 * ZC - a
    c, s = box((-0.8, -3.75, zz(-3.55, -2.65)[0]), (0.8, -2.2, zz(-3.55, -2.65)[1]))
    add("RR_CouplerBox", side, "Coupling", s, c, material='Metal', color=SOOT, deco=True, note="draft-gear pocket under the plate end")
    c, s = box((-0.25, HY - 0.25, zz(-2.66, -1.19)[0]), (0.25, HY + 0.25, zz(-2.66, -1.19)[1]))
    add("RR_CouplerShank", side, "Coupling", s, c, material='Metal', color=SOOT, deco=True)
    c, s = box((-0.55, HY - HH / 2, zz(-1.2, -0.6)[0]), (0.55, HY + HH / 2, zz(-1.2, -0.6)[1]))
    add("RR_CouplerHead", side, "Coupling", s, c, material='Metal', color=SOOT, deco=True)
    kx = (0.01, 0.55) if side == "front" else (-0.55, -0.01)
    c, s = box((kx[0], HY - HH / 2 + 0.02, zz(-0.62, -0.12)[0]), (kx[1], HY + HH / 2 - 0.02, zz(-0.62, -0.12)[1]))
    pin_x = (kx[0] + kx[1]) / 2
    pin_z = ZC - 0.2 * m                              # pin near the head end of the knuckle (clear of the dropped fall plate)
    kn_anim = hinge([pin_x, HY, pin_z], 'y', 30.0, 0.08, 0.35, 'Back')
    add("RR_CouplerKnuckle", side, "Coupling", s, c, material='Metal', color=SOOT, deco=True, anim=dict(kn_anim),
        note="knuckles sit side by side across the plane; each opens 30 deg on the snap")
    add("RR_CouplerPin", side, "Coupling", [0.36, 0.2, 0.2], [pin_x, HY + HH / 2 + 0.1, pin_z], R('z', 90), shape='Cylinder',
        material='Metal', color=BRASS, refl=0.12, deco=True, anim=dict(kn_anim))


coupler("front"); coupler("rear")

# ---------------------------------------------------------------- brake hoses (air pipe), meet at the plane in a V
HX = 0.95
for side in ("front", "rear"):
    m = 1 if side == "front" else -1
    mz = -2.3 if side == "front" else 2 * ZC + 2.3     # mount z (front -2.3, rear 1.6)
    gz = ZC - 0.19 * m                                  # glad-hand centre, 0.02 clear of the plane
    top = np.array([HX, -2.5, mz]); end = np.array([HX, -4.25, gz + 0.1 * m])
    c, s = box((HX - 0.15, -2.5, mz - 0.15), (HX + 0.15, -2.19, mz + 0.15))
    add("RR_HoseMount", side, "Coupling", s, c, material='Metal', color=SOOT, deco=True)
    d = end - top; L = float(np.linalg.norm(d)); X = d / L
    Y = np.array([1.0, 0, 0]); Z = np.cross(X, Y)
    rot = np.column_stack([X, Y, Z])                    # Roblox cylinder axis = local X
    ang = math.degrees(math.atan2(d[2], -d[1]))         # tilt from hanging straight down
    h_anim = hinge(top.tolist(), 'x', ang, 0.0, 1.1, 'Elastic')
    add("RR_Hose", side, "Coupling", [L + 0.1, 0.22, 0.22], (top + d / 2).tolist(), rot, shape='Cylinder',
        material='Rubber', color=RUBBER, deco=True, anim=dict(h_anim))
    c, s = box((HX - 0.12, -4.33, gz - 0.17), (HX + 0.12, -4.17, gz + 0.17))
    add("RR_GladHand", side, "Coupling", s, c, material='Metal', color=BRASS, refl=0.12, deco=True, anim=dict(h_anim))

# ---------------------------------------------------------------- split poses for hinged parts
for p in parts:
    a = p.get("anim")
    if a and a["kind"] == "hinge":
        a["splitCF"] = pose_after_hinge(p, a)

spec = {
    "version": "1.0.0",
    "frame": "J: origin gangway-union bbox centre; +X east, +Y up, +Z toward the rear carriage",
    "union_signature": UNION,
    "coupling_plane_z": ZC,
    "floor_y": FLOOR,
    "plane_note": "world z 116.876 in the export; midway between the end walls (113.68 / 120.08) and between posts 3 and 4",
    "fx": {"sparks": [0.0, HY, ZC], "air": "each RR_GladHand", "flash": [0.0, HY, ZC]},
    "motion": {"speed": 35, "brake": 10, "recoil": 0.4, "despawn": 400},
    "tokens": {"iron": "#363A42", "soot": "#15181B", "brass": "#C9953A", "hazard": "#F2C230", "walk": "163,162,165 DiamondPlate (union)"},
    "parts": parts,
}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit_spec.json")
json.dump(spec, open(out, "w"), indent=1)
n = {s: sum(1 for p in parts if p["side"] == s) for s in ("front", "rear")}
print(f"kit_spec.json: {len(parts)} parts (front {n['front']}, rear {n['rear']}), "
      f"{sum(1 for p in parts if 'anim' in p)} animated -> {out}")
