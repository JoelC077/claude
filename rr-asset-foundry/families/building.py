"""Small railway buildings in the depot kit: a stone hut, a two-storey signal box (brick base, timber glazed cab,
outside stair and landing) and an open-fronted platform shelter. Weathered-rural: stone, iron, timber, moss, soot.
Frame: x = width, y = depth (front faces -y), z up, z = 0 ground. Blank boards only (style.dont.invented_text)."""
import math
import fkit

FAMILY = "building"
DESC = "Small railway buildings: stone hut, two-storey signal box with stair, open platform shelter."
TAGS = ["building", "hut", "shed", "signal box", "cabin", "shelter", "station", "house", "depot", "lobby", "platform"]
OPEN = []
PARAMS = {
    "kind": ("choice", "hut", ["hut", "signal_box", "shelter"], "building type"),
    "width": ("float", 18.0, 10, 40, "front width (x), studs"),
    "depth": ("float", 13.0, 8, 30, "depth (y), studs"),
    "wall_h": ("float", 11.0, 7, 16, "eave height above the ground (signal box: base storey height)"),
    "upper_h": ("float", 8.0, 6, 12, "signal box: glazed upper storey height"),
    "plinth_h": ("float", 0.8, 0.0, 2.0, "stone plinth / floor above the ground"),
    "roof_pitch": ("float", 35.0, 15, 55, "roof pitch, degrees"),
    "overhang": ("float", 1.0, 0.3, 2.5, "roof overhang at eaves and gables"),
    "door_w": ("float", "@tech.units.building_door#0", 5, 10, "door opening width (canon minimum)"),
    "door_h": ("float", "@tech.units.building_door#1", 7, 12, "door opening height (canon minimum)"),
    "windows": ("int", 2, 0, 6, "windows on the front (hut) / per side"),
    "window_w": ("float", 3.5, 2.0, 6.0, "window width"),
    "window_h": ("float", 4.0, 2.0, 6.0, "window height"),
    "chimney": ("bool", True, "chimney stack on the back slope"),
    "weathering": ("float", 0.4, 0.0, 1.0, "moss at the base; 0.4+ a patch plate; 0.6+ a taped window"),
    "signboard": ("bool", False, "blank board over the door (the owner writes the name)"),
}
GROUPS = {
    "Stone": ("style.depot_kit.stone", "Slate"),
    "StoneDark": ("style.depot_kit.stone_dark", "Slate"),
    "StoneLight": ("style.depot_kit.stone_light", "Slate"),
    "Brick": ("style.depot_kit.chimney_brick", "Brick"),
    "Timber": ("style.depot_kit.timber_dark", "Wood"),
    "Cladding": ("style.depot_kit.timber_light", "WoodPlanks"),
    "Roof": ("style.depot_kit.slate_roof", "Slate"),
    "Iron": ("style.depot_kit.iron", "Metal"),
    "Glass": ("style.depot_kit.interior_dark", "SmoothPlastic"),
    "Cream": ("style.depot_kit.cream", "SmoothPlastic"),
    "Door": ("style.depot_kit.teal_trim", "Wood"),
    "Moss": ("style.depot_kit.moss", "Grass"),
    "Patch": ("style.depot_kit.red_oxide", "CorrodedMetal"),
    "Hazard": ("style.world.hazard", "SmoothPlastic"),
    "Ink": ("style.brand.ink", "SmoothPlastic"),
}
PRESETS = {
    "hut_stone": {"params": {"kind": "hut", "windows": 1}, "note": "stone lineside hut, teal door, chimney"},
    "hut_taped": {"params": {"kind": "hut", "width": 14, "depth": 11, "weathering": 0.8, "windows": 1},
                  "note": "small hut, patched and taped (incompetent company)"},
    "signal_box": {"params": {"kind": "signal_box", "width": 16, "depth": 13, "wall_h": 7.5, "windows": 3,
                              "door_w": 7, "door_h": 9}, "note": "signal box (world.prefabs.18), brick base, glazed cab"},
    "shelter": {"params": {"kind": "shelter", "width": 20, "depth": 8, "wall_h": 10, "chimney": False},
                "note": "open-fronted platform shelter with bench and valance"},
}
DEFAULT_PRESET = "hut_stone"
VIEW = {"ground": "style.lobby.concrete", "features": ["Door", "Window", "Chimney", "RidgeCap", "Rail", "Bench", "Valance"],
        "player": "Walk-around scale in the Depot Lobby or seen from the train at the lineside; doors are the canon "
                  "minimum so a 5-stud avatar walks in."}
OPTIONS = {"merge": "none", "collide": True, "lod": False}


def validate(p, canon):
    w = []
    if p["kind"] == "shelter" and p["wall_h"] - p["plinth_h"] < 7:
        w.append("ERROR: a shelter needs wall_h at least plinth_h + 7 (front clear height)")
    if p["kind"] != "shelter" and p["plinth_h"] + p["door_h"] > p["wall_h"] - 0.8 and p["kind"] == "hut":
        w.append("door opening reaches the eave: raise wall_h or lower door_h")
    if p["door_w"] < canon("tech.units.building_door") and p["kind"] == "hut":
        w.append("door narrower than tech.units.building_door")
    return w


# ---------- shared pieces ----------

def gable_roof(k, W, D, z_eave, pitch, oh, t=0.7):
    """Pitched roof, ridge along x, underside through the wall-top outer edges. Returns (ridge_z, tv, tan)."""
    tn = math.tan(math.radians(pitch))
    tv = t / math.cos(math.radians(pitch))
    ridge = z_eave + D / 2 * tn
    ze = z_eave - oh * tn
    k.prism("Roof", "Roof", [(-(D / 2 + oh), ze), (0, ridge), (D / 2 + oh, ze), (D / 2 + oh, ze + tv), (0, ridge + tv),
                             (-(D / 2 + oh), ze + tv)], W + 2 * oh, (0, 0, 0), axis="X")
    cb = ridge + tv - 0.5 * tn - 0.1              # ridge cap reaches below the slope at its own edges
    k.box("RidgeCap", "Iron", (0, 0, (cb + ridge + tv + 0.2) / 2), (W + 2 * oh + 0.3, 1.0, ridge + tv + 0.2 - cb))
    if oh >= 0.6:           # a gutter needs an overhang to hang from; shorter ones would cut the wall head
        k.boxes("Gutter", "Iron", [((0, s * (D / 2 + oh - 0.15), ze - 0.1), (W + 2 * oh - 0.2, 0.45, 0.35)) for s in (-1, 1)],
                detail=1)
    for e in (-1, 1):   # gable triangles, inside the eave walls, following the roof underside
        a = D / 2 - 0.8
        zg = lambda y: z_eave + (D / 2 - abs(y)) * tn + 0.1
        k.prism("Gable", "Stone", [(-a, z_eave), (a, z_eave), (a, zg(a)), (0, ridge + 0.1), (-a, zg(a))],
                0.8, (e * (W / 2 - 0.4), 0, 0), axis="X")
    k.proxy((0, 0, ridge + tv / 2), (W + 2 * oh, 0.8, tv))
    for s in (-1, 1):
        run = D / 2 + oh
        k.proxy((0, s * run / 2, (ridge + ze) / 2 + tv / 2), (W + 2 * oh, run / math.cos(math.radians(pitch)), 0.5),
                rot=(s * pitch, 0, 0))
    return ridge, tv


def window(k, c, at, z0, w, h, axis, s, frame_group="Cream"):
    """Glass recessed in an opening, lapped frame, stone sill proud below. s = outward side (+1 / -1)."""
    gl = ((c, at - s * 0.15, z0 + h / 2), (w, 0.2, h)) if axis == "X" else ((at - s * 0.15, c, z0 + h / 2), (0.2, w, h))
    sill = ((c, at + s * 0.4, z0 - 0.12), (w + 0.9, 1.2, 0.4)) if axis == "X" else ((at + s * 0.4, c, z0 - 0.12), (1.2, w + 0.9, 0.4))
    return [gl], fkit.frame_boxes(c, at, z0, w, h, axis=axis, bottom=False, d=1.0), [sill]


def door_leaf(k, c, at, z0, w, h, axis, s):
    """Ledged plank door, recessed; returns its boxes (alternate boards proud so planks read)."""
    n, out = max(3, round(w / 1.2)), []
    for i in range(n):
        u = c - w / 2 + w * (i + 0.5) / n
        depth = 0.3 + 0.06 * (i % 2)
        y = at - s * 0.25 + s * depth / 2
        out.append(((u, y, z0 + h / 2), (w / n, depth, h)) if axis == "X" else ((y, u, z0 + h / 2), (depth, w / n, h)))
    return out


def moss(k, p, W, D, walls, door_x=0.0):
    """Two big blobs and five small (style.material.patches) at the plinth foot, never on the door path."""
    n = round(p["weathering"] * 7)
    items = []
    for i in range(n):
        big = i < 2
        s = walls[i % len(walls)]
        L = k.rng.uniform(1.6, 2.6) if big else k.rng.uniform(0.6, 1.1)
        if s in (-1, 1):   # front/back walls; on the front never on the door step
            x = k.rng.uniform(-W / 2 + 1.5, W / 2 - 1.5)
            clear = p["door_w"] / 2 + 1.0 + L / 2
            if s == -1 and abs(x - door_x) < clear:
                x = door_x + math.copysign(clear, (x - door_x) or 1)
                if abs(x) > W / 2 - L / 2:
                    continue
            items.append(((x, s * (D / 2 + 0.2 + 0.25), 0.18 + 0.05 * big), (L, 0.5, 0.36 + 0.1 * big)))
        else:
            y = k.rng.uniform(-D / 2 + 1.5, D / 2 - 1.5)
            items.append(((s / 2 * (W / 2 + 0.2 + 0.25), y, 0.18 + 0.05 * big), (0.5, L, 0.36 + 0.1 * big)))
    k.boxes("Moss", "Moss", items, detail=1)


# ---------- kinds ----------

def build(k, p):
    {"hut": hut, "signal_box": signal_box, "shelter": shelter}[p["kind"]](k, p)


def plinth(k, W, D, ph):
    if ph > 0:
        k.box("Plinth", "StoneDark", (0, 0, ph / 2), (W + 0.4, D + 0.4, ph))
        k.proxy((0, 0, ph / 2), (W + 0.4, D + 0.4, ph))


def quoins(k, W, D, z0, z1):
    items, z, row = [], z0, 0
    while z + 0.9 <= z1 + 0.01:
        for ex in (-1, 1):
            for ey in (-1, 1):
                if row % 2 == 0:    # long on the front/back face, wrapping the corner
                    items.append(((ex * (W / 2 - 0.5), ey * (D / 2 + 0.1), z + 0.45), (1.4, 0.2, 0.9)))
                else:
                    items.append(((ex * (W / 2 + 0.1), ey * (D / 2 - 0.5), z + 0.45), (0.2, 1.4, 0.9)))
        z, row = z + 0.9, row + 1
    k.boxes("Quoin", "StoneLight", items, detail=1)


def hut(k, p):
    W, D, H, ph = p["width"], p["depth"], p["wall_h"], p["plinth_h"]
    dw, dh = p["door_w"], p["door_h"]
    plinth(k, W, D, ph)
    tn = math.tan(math.radians(p["roof_pitch"]))
    ext = min(0.8 * tn + 0.1, 0.7 / math.cos(math.radians(p["roof_pitch"])) - 0.1)
    ww = p["window_w"]
    dx = -W / 2 + dw / 2 + 2.0 if p["windows"] else 0.0
    a0, a1 = dx + dw / 2 + 1.4, W / 2 - 1.6               # front windows share the span right of the door
    n = min(p["windows"], max(0, int((a1 - a0 + 1.2) // (ww + 1.2))))
    wx = [a0 + (a1 - a0) * (i + 0.5) / n for i in range(n)]
    if p["windows"] > n:
        k.measure("front windows", f"{n} of {p['windows']} fit beside the door at width {W:g}")
    wz = ph + 3.0
    glass, frames, sills = [], [], []
    yF, yB = -D / 2 + 0.4, D / 2 - 0.4
    k.wall("WallFront", "Stone", "X", -W / 2, W / 2, yF, ph, H + ext, 0.8,
           holes=[(dx, ph, dw, dh)] + [(x, wz, p["window_w"], p["window_h"]) for x in wx])
    k.wall("WallBack", "Stone", "X", -W / 2, W / 2, yB, ph, H + ext, 0.8, holes=[(W / 4, wz, p["window_w"], p["window_h"])])
    side_holes = [(0.0, wz, p["window_w"], p["window_h"])] if D >= p["window_w"] + 4 else []
    for e in (-1, 1):
        k.wall("WallSide", "Stone", "Y", -D / 2 + 0.8, D / 2 - 0.8, e * (W / 2 - 0.4), ph, H, 0.8, holes=side_holes)
    for c, at, axis, s in [(x, yF, "X", -1) for x in wx] + [(W / 4, yB, "X", 1)] + \
                          [(0.0, e * (W / 2 - 0.4), "Y", e) for e in (-1, 1) if side_holes]:
        g, f, sl = window(k, c, at, wz, p["window_w"], p["window_h"], axis, s)
        glass += g
        frames += f
        sills += sl
    k.boxes("Window", "Glass", glass)
    k.boxes("WindowFrame", "Cream", frames)
    k.boxes("Sill", "StoneDark", sills)
    k.boxes("Door", "Door", door_leaf(k, dx, yF, ph, dw, dh, "X", -1))
    k.boxes("DoorFrame", "Timber", fkit.frame_boxes(dx, yF, ph, dw, dh, bottom=False, d=1.0))
    lx0, lx1 = max(dx - dw / 2 - 0.8, -W / 2 + 1.3), min(dx + dw / 2 + 0.8, W / 2 - 1.3)    # clear of the quoins
    k.box("Lintel", "StoneDark", ((lx0 + lx1) / 2, yF - 0.3, ph + dh + 0.55), (lx1 - lx0, 0.7, 0.7))
    if ph > 0:
        k.box("Step", "StoneDark", (dx, -D / 2 - 0.2 - 0.7, ph / 4), (dw + 1.2, 1.4, ph / 2))
    k.measure("door clear opening", f"{dw:g} x {dh:g} studs (avatar 5 tall)")
    quoins(k, W, D, ph, H)
    ridge, tv = gable_roof(k, W, D, H, p["roof_pitch"], p["overhang"])
    if p["chimney"]:
        cx, cy = W / 2 - 2.6, D / 4
        top = ridge + 2.0
        k.box("Chimney", "Brick", (cx, cy, (H + top) / 2), (1.8, 1.8, top - H))
        k.box("ChimneyCap", "StoneDark", (cx, cy, top + 0.15), (2.3, 2.3, 0.3))
        k.cyl("ChimneyPot", "Iron", (cx, cy, top + 0.65), 0.45, 0.8, segs=10, detail=1)
    if p["signboard"]:              # clear of the quoins, 0.05 off the wall face
        sx0, sx1 = max(dx - dw / 2 - 1.0, -W / 2 + 1.3), min(dx + dw / 2 + 1.0, W / 2 - 1.3)
        k.box("Signboard", "Cream", ((sx0 + sx1) / 2, yF - 0.6, ph + dh + 1.6), (sx1 - sx0, 0.3, 1.3))
        k.measure("signboard", "blank; the owner names the building (style.dont.invented_text)")
    walls_proxy(k, W, D, ph, H, [(dx, dw, dh)])
    moss(k, p, W, D, [-1, 1, -2, 2], door_x=dx)
    if p["weathering"] >= 0.4:      # a mismatched tin patch on the door
        k.box("PatchPlate", "Patch", (dx + dw / 5, yF - 0.16, ph + dh * 0.35), (1.6, 0.1, 1.2), rot=(0, 6, 0))
    if p["weathering"] >= 0.6 and side_holes:
        tape_side(k, W, wz, p["window_w"], p["window_h"])


def tape_side(k, W, wz, w, h):
    """Tape X across the +x side window (the side the 3/4 camera sees), just proud of its frame."""
    segs = {"Hazard": [], "Ink": []}
    ang = math.degrees(math.atan2(h, w))
    diag, n = math.hypot(w, h) + 0.6, 7
    x = W / 2 + 0.13
    for sign, off in ((1, 0.0), (-1, 0.05)):
        for i in range(n):
            d = (i - (n - 1) / 2) * diag / n
            segs["Hazard" if i % 2 == 0 else "Ink"].append(
                ((x + off, d * math.cos(math.radians(ang)), wz + h / 2 + sign * d * math.sin(math.radians(ang))),
                 (0.05, diag / n, 0.45), (sign * ang, 0, 0)))
    for g, items in segs.items():
        k.boxes("Tape", g, items, detail=1)


def walls_proxy(k, W, D, z0, z1, front_doors):
    """Box colliders for the four walls, the front split around its doors."""
    h = z1 - z0
    xs = sorted([-W / 2, W / 2] + [c + s * w / 2 for c, w, _ in front_doors for s in (-1, 1)])
    for a, b in zip(xs[::2], xs[1::2]):
        if b - a > 0.1:
            k.proxy(((a + b) / 2, -D / 2 + 0.4, z0 + h / 2), (b - a, 0.8, h))
    for c, w, dh in front_doors:
        k.proxy((c, -D / 2 + 0.4, z0 + dh + (h - dh) / 2), (w, 0.8, h - dh))
    k.proxy((0, D / 2 - 0.4, z0 + h / 2), (W, 0.8, h))
    for e in (-1, 1):
        k.proxy((e * (W / 2 - 0.4), 0, z0 + h / 2), (0.8, D - 1.6, h))


def signal_box(k, p):
    W, D, Hb, Hu, ph = p["width"], p["depth"], p["wall_h"], p["upper_h"], p["plinth_h"]
    top = Hb + Hu
    plinth(k, W, D, ph)
    yF, yB = -D / 2 + 0.4, D / 2 - 0.4
    ww, n = p["window_w"], max(1, p["windows"])
    # locking room: brick, small windows
    small = [(-W / 2 + (W) * (i + 0.5) / n, ph + 2.2, min(ww, W / n - 1.5), 2.6) for i in range(n)]
    k.wall("BaseFront", "Brick", "X", -W / 2, W / 2, yF, ph, Hb, 0.8, holes=small)
    k.wall("BaseBack", "Brick", "X", -W / 2, W / 2, yB, ph, Hb, 0.8)
    for e in (-1, 1):
        k.wall("BaseSide", "Brick", "Y", -D / 2 + 0.8, D / 2 - 0.8, e * (W / 2 - 0.4), ph, Hb, 0.8)
    glass, frames, sills = [], [], []
    for c, z0, w, h in small:
        g, f, s = window(k, c, yF, z0, w, h, "X", -1)
        glass, frames, sills = glass + g, frames + f, sills + s
    k.box("Floor", "Timber", (0, 0, Hb + 0.3), (W + 0.2, D + 0.2, 0.6))       # floor band between storeys
    # glazed cab: a continuous band of windows on the front and both sides
    zc0, zc1 = Hb + 0.6, top
    band_z, band_h = zc0 + 2.2, Hu - 3.4
    fn = max(2, n + 1)
    fw = (W - 2.4) / fn - 0.9
    front = [(-W / 2 + 1.2 + (W - 2.4) * (i + 0.5) / fn, band_z, fw, band_h) for i in range(fn)]
    sn = max(1, round((D - 5.5) / (fw + 0.9)))
    sw = (D - 5.5) / sn - 0.9
    side = [(-D / 2 + 1.2 + (D - 5.5) * (i + 0.5) / sn, band_z, sw, band_h) for i in range(sn)]
    ud_w, ud_h = 4.5, min(7.0, Hu - 1.0)
    ud_y = D / 2 - 0.7 - ud_w / 2 - 0.6
    k.wall("CabFront", "Cladding", "X", -W / 2, W / 2, yF, zc0, zc1, 0.6, holes=front)
    k.wall("CabBack", "Cladding", "X", -W / 2, W / 2, yB, zc0, zc1, 0.6)
    k.wall("CabSide", "Cladding", "Y", -D / 2 + 0.7, D / 2 - 0.7, -(W / 2 - 0.3), zc0, zc1, 0.6, holes=side)
    k.wall("CabSide", "Cladding", "Y", -D / 2 + 0.7, D / 2 - 0.7, W / 2 - 0.3, zc0, zc1, 0.6,
           holes=side[:-1] + [(ud_y, zc0, ud_w, ud_h)])
    for c, z0, w, h in front:
        g, f, s = window(k, c, yF, z0, w, h, "X", -1)
        glass, frames, sills = glass + g, frames + f, sills + s
    for e in (-1, 1):
        for c, z0, w, h in (side if e < 0 else side[:-1]):
            g, f, s = window(k, c, e * (W / 2 - 0.3), z0, w, h, "Y", e)
            glass, frames, sills = glass + g, frames + f, sills + s
    k.boxes("Window", "Glass", glass)
    k.boxes("WindowFrame", "Cream", frames)
    k.boxes("Sill", "StoneDark", sills)
    k.boxes("Door", "Door", door_leaf(k, ud_y, W / 2 - 0.3, zc0, ud_w, ud_h, "Y", 1))
    k.boxes("DoorFrame", "Timber", fkit.frame_boxes(ud_y, W / 2 - 0.3, zc0, ud_w, ud_h, axis="Y", bottom=False, d=0.9))
    ridge, tv = gable_roof(k, W, D, top, p["roof_pitch"], p["overhang"])
    stair(k, p, W, D, Hb, ud_y)
    if p["chimney"]:
        cx, cy, ct = -W / 2 + 2.2, D / 4, ridge + 1.6
        k.box("Chimney", "Brick", (cx, cy, (top + ct) / 2), (1.6, 1.6, ct - top))
        k.box("ChimneyCap", "StoneDark", (cx, cy, ct + 0.15), (2.1, 2.1, 0.3))
    k.proxy((0, 0, Hb + 0.3), (W + 0.2, D + 0.2, 0.6))
    walls_proxy(k, W, D, ph, Hb, [])
    for s in (-1, 1):
        k.proxy((0, s * (D / 2 - 0.4), (zc0 + zc1) / 2), (W, 0.6, zc1 - zc0))
    k.proxy((-(W / 2 - 0.3), 0, (zc0 + zc1) / 2), (0.6, D - 1.4, zc1 - zc0))
    for a, b in ((-D / 2 + 0.7, ud_y - ud_w / 2), (ud_y + ud_w / 2, D / 2 - 0.7)):
        if b - a > 0.1:
            k.proxy((W / 2 - 0.3, (a + b) / 2, (zc0 + zc1) / 2), (0.6, b - a, zc1 - zc0))
    k.proxy((W / 2 - 0.3, ud_y, (zc0 + ud_h + zc1) / 2), (0.6, ud_w, zc1 - zc0 - ud_h))
    k.measure("upper door", f"{ud_w:g} x {ud_h:g} (lineside prefab, not a lobby door)")
    moss(k, p, W, D, [-1, 1, -2], door_x=W)


def stair(k, p, W, D, Hb, ud_y):
    """Outside timber stair up the +x side to an iron landing at the upper door, with railings (riser <= 0.9)."""
    x, sw = W / 2 + 1.6, 2.6
    land_y0 = ud_y - 2.8
    lt = Hb + 0.65                      # landing top 0.05 above the floor band so their tops never share a plane
    k.box("Landing", "Iron", (x - 0.1, (land_y0 + D / 2 + 0.2) / 2, lt - 0.325), (sw + 0.4, D / 2 + 0.2 - land_y0, 0.65))
    n = max(4, math.ceil(Hb / 0.85))
    rise = Hb / n
    y0 = -D / 2 - 1.0
    run = (land_y0 - y0) / n
    treads = [((x, y0 + run * (i + 0.5), rise * (i + 1) - 0.15), (sw, run + 0.12, 0.3)) for i in range(n - 1)]
    k.boxes("StairTread", "Timber", treads)
    L = math.hypot(land_y0 - y0, Hb)
    ang = math.degrees(math.atan2(Hb, land_y0 - y0))
    mid = ((y0 + land_y0) / 2, Hb / 2)
    k.boxes("Stringer", "Iron", [((x + s * (sw / 2 + 0.12), mid[0], mid[1]), (0.3, L, 0.7), (ang, 0, 0)) for s in (-1, 1)])
    posts = [((x + sw / 2 + 0.3, y, lt + 1.5), (0.3, 0.3, 3.0)) for y in (land_y0 + 0.3, D / 2)]
    posts += [((x + s * (sw / 2 + 0.3), y0 + 0.4, 1.5 + rise), (0.3, 0.3, 3.0)) for s in (-1, 1)]
    k.boxes("RailPost", "Iron", posts)
    rail = [((x + sw / 2 + 0.3, (land_y0 + D / 2) / 2, lt + 3.0), (0.4, D / 2 - land_y0, 0.3)),     # wider than posts
            ((x + sw / 2 + 0.3, mid[0], mid[1] + 3.0), (0.4, L, 0.3), (ang, 0, 0))]
    k.boxes("Rail", "Iron", rail)
    k.box("LandingEdge", "Hazard", (x - 0.1, land_y0 + 0.2, lt + 0.02), (sw + 0.3, 0.3, 0.06))
    k.proxy((x, mid[0], mid[1] - 0.2), (sw, L, 0.4), rot=(ang, 0, 0))
    k.proxy((x - 0.1, (land_y0 + D / 2 + 0.2) / 2, lt - 0.325), (sw + 0.4, D / 2 + 0.2 - land_y0, 0.65))
    k.measure("stair", f"{n} risers of {rise:.2f} studs, going {run:.2f}, width {sw:g}")


def shelter(k, p):
    W, D, H, ph = p["width"], p["depth"], p["wall_h"], p["plinth_h"]
    plinth(k, W, D, ph)
    yB, oh = D / 2 - 0.3, p["overhang"]
    tn = math.tan(math.radians(min(p["roof_pitch"], 20)))       # lean-to falls to the back
    if H - D * tn < ph + 5.5:                                     # keep 5.5 studs of back wall
        tn = max(0.05, (H - ph - 5.5) / D)
        k.measure("roof pitch", f"limited to {math.degrees(math.atan(tn)):.1f} deg so the back wall keeps 5.5 studs")
    front_h, back_h = H, H - D * tn
    zu = lambda y: (front_h + back_h) / 2 - tn * y              # roof underside
    ang = math.degrees(math.atan(tn))
    k.wall("WallBack", "Cladding", "X", -W / 2, W / 2, yB, ph, zu(D / 2 - 0.6) + 0.15, 0.6)
    for e in (-1, 1):   # side walls follow the roof, their tops hidden in the slab
        a0, a1 = -D / 2 + 0.2, D / 2 - 0.6
        k.prism("WallSide", "Cladding", [(a0, 0), (a1, 0), (a1, zu(a1) + 0.1 - ph), (a0, zu(a0) + 0.1 - ph)],
                0.6, (e * (W / 2 - 0.3), 0, ph), axis="X")
    Lr = (D + 2 * oh) / math.cos(math.radians(ang))
    zc = (front_h + back_h) / 2 + 0.35 / math.cos(math.radians(ang))
    k.box("Roof", "Roof", (0, 0, zc), (W + 2 * oh, Lr, 0.7), rot=(-ang, 0, 0))
    n = max(2, round(W / 6) + 1)
    posts = [(-W / 2 + 0.5 + (W - 1.0) * i / (n - 1)) for i in range(n)]
    yp = -D / 2 + 0.6
    k.boxes("Post", "Iron", [((x, yp, (ph - 0.3 + zu(yp) + 0.3) / 2), (0.5, 0.5, zu(yp) + 0.3 - ph + 0.3)) for x in posts])
    k.boxes("Bracket", "Iron", [((x, yp + 0.9, zu(yp + 0.9) - 0.6), (0.3, 1.8, 0.3), (-30, 0, 0)) for x in posts], detail=1)
    span = W + 2 * oh - 0.2                   # stops short of the roof ends: no shared end planes
    teeth, m = [], max(4, int(span / 0.9))
    ye = -(D / 2 + oh)
    for i in range(m):
        x = -span / 2 + span * (i + 0.5) / m
        h = 1.1 if i % 2 == 0 else 0.7        # chunky valance teeth, no hairlines (style.dont.hairlines)
        teeth.append(((x, ye + 0.3, zu(ye + 0.3) - h / 2 + 0.15), (span / m, 0.25, h)))
    k.boxes("Valance", "Cream", teeth, detail=1)
    bz = ph + 1.8
    k.box("Bench", "Timber", (0, yB - 1.3, bz), (W - 3.0, 1.6, 0.3))
    k.box("BenchBack", "Timber", (0, yB - 0.45, bz + 1.2), (W - 3.0, 0.3, 1.6))
    k.boxes("BenchLeg", "Iron", [((x, yB - 1.3, (ph + bz) / 2), (0.3, 1.2, bz - ph)) for x in (-(W / 2 - 2.5), 0, W / 2 - 2.5)])
    k.box("Noticeboard", "Cream", (W / 4, yB - 0.4, ph + 5.2), (3.2, 0.2, 2.2))
    k.measure("noticeboard", "blank; text needs the owner (style.dont.invented_text)")
    k.measure("clear height front / back", f"{zu(yp) - ph:.1f} / {zu(yB - 0.3) - ph:.1f} studs")
    k.proxy((0, yB, (ph + back_h) / 2), (W, 0.6, back_h - ph))
    for e in (-1, 1):
        k.proxy((e * (W / 2 - 0.3), 0.3, (ph + back_h) / 2), (0.6, D - 1.2, back_h - ph))
    k.proxy((0, 0, zc), (W + 2 * oh, Lr, 0.7), rot=(-ang, 0, 0))
    k.proxy((0, yB - 1.3, (ph + bz) / 2 + 0.1), (W - 3.0, 1.6, bz - ph + 0.2))
    moss(k, p, W, D, [1, -2, 2])
