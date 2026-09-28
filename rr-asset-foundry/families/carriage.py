"""Passenger coaches: panelled body with a brass waist band at the 3-stud rail line (style.form.wall_lines), windows,
side doors at the canon doorway size, arched roof, open end balconies with railings and a roof ladder, on bogies.
Frame: x along, y across, z up, z = 0 rail top. Livery is OQ-025 (open): presets carry both candidate liveries."""
import math
import fkit
import _rolling as R

FAMILY = "carriage"
DESC = "Passenger coaches: windows, side doors, arched roof, open end balconies, roof ladder, bogies; two liveries."
TAGS = ["carriage", "coach", "passenger", "rolling stock", "train", "car", "balcony"]
OPEN = ["OQ-025"]
PARAMS = {
    "length": ("float", 56.0, 32, 100, "over the buffer beams, studs"),
    "width": ("float", "@tech.units.stock_width", 12, 20, "body width over the sides, studs"),
    "gauge": ("float", "@tech.units.gauge", 4, 12, "rail centre to centre, studs"),
    "floor": ("float", "@tech.units.stock_floor", 3, 8, "floor top above the rail top, studs"),
    "roof": ("float", "@tech.units.stock_roof", 10, 18, "roof crown above the rail top, studs"),
    "roof_rise": ("float", 1.4, 0.6, 3.0, "arch rise from the eave to the crown"),
    "waist": ("float", 3.0, 2.0, 4.0, "brass waist band above the floor (style.form.wall_lines: rail at 3)"),
    "windows": ("int", 5, 0, 12, "windows per side"),
    "window_w": ("float", 4.0, 2.0, 6.0, "window width"),
    "window_h": ("float", 3.0, 2.0, 5.0, "window height"),
    "door_w": ("float", "@tech.units.train_doorway#0", 4, 7, "door opening width (canon doorway)"),
    "door_h": ("float", "@tech.units.train_doorway#1", 6, 9, "door opening height (canon doorway)"),
    "side_doors": ("int", 1, 0, 2, "side doors per side (1: centre, 2: near the ends)"),
    "balcony": ("bool", True, "open end balconies (gameplay.train.layout)"),
    "balcony_len": ("float", 3.5, 2.5, 6.0, "balcony depth at each end"),
    "balcony_roof": ("bool", False, "roof carried over the balconies on posts (then no roof ladder)"),
    "ladder": ("bool", True, "roof ladder at the +x end (assets.train.roof_ladder)"),
    "vents": ("int", 4, 0, 10, "roof vents"),
    "running": ("choice", "bogies", ["auto", "axles", "bogies"], "running gear"),
    "wheel_r": ("float", 1.6, 1.0, 2.5, "wheel radius, studs"),
    "bogie_inset": ("float", 0.18, 0.1, 0.3, "bogie centre from the end, as a fraction of the length"),
}
GROUPS = {
    "Body": ("style.world.cream", "SmoothPlastic"),
    "Lower": ("style.world.navy", "SmoothPlastic"),
    "Brass": ("style.world.brass", "Metal", 0.12),
    "Sash": ("style.world.walnut", "Wood"),
    "Glass": ("style.depot_kit.interior_dark", "SmoothPlastic"),
    "Door": ("style.world.walnut", "Wood"),
    "Roof": ("style.depot_kit.slate_roof", "Metal"),
    "Floor": ("style.world.diamond_plate", "DiamondPlate"),
    "Iron": ("style.world.ironwork", "Metal"),
    "Hazard": ("style.world.hazard", "SmoothPlastic"),
    "Chassis": ("style.world.soot_black", "Metal"),
    "Steel": ("style.thumb.steel", "Metal"),
    "Buffer": ("style.brand.buffer_red", "SmoothPlastic"),
}
PRESETS = {
    "coach_works": {"params": {}, "note": "cream body, navy lower panels (the Works Report's navy/cream; OQ-025 default A)"},
    "coach_brand": {"params": {}, "groups": {"Body": "style.brand.teal", "Lower": "style.brand.teal_dark",
                                             "Sash": "style.brand.cream"},
                    "note": "brand livery, teal with a cream sash and red buffer beams (OQ-025 option B)"},
    "coach_short": {"params": {"length": 40, "windows": 3, "side_doors": 0, "vents": 2},
                    "note": "short coach, end doors only"},
    "coach_long": {"params": {"length": 72, "windows": 7, "side_doors": 2, "vents": 6},
                   "note": "long coach, two doors a side"},
}
DEFAULT_PRESET = "coach_works"
VIEW = {"stage": "track", "ground": "style.ground.pasture",
        "features": ["BufferHead", "Window", "Door", "LadderRung", "Railing", "Handrail", "Vent"],
        "player": "Players ride the train and never leave it: they walk between vehicles over the end balconies, climb "
                  "to the roof for crates, and see the coach from the next vehicle. The train stays put; the world scrolls.",
        "rules": [R.RUNG_RULE]}
OPTIONS = {"merge": "none", "collide": True, "lod": False}


def validate(p, canon):
    w = []
    if p["roof"] > canon("tech.units.stock_roof"):
        w.append(f"roof {p['roof']:g} is above tech.units.stock_roof (tunnel crouch clearance)")
    if p["floor"] + p["door_h"] > p["roof"] - p["roof_rise"] - 0.3:
        w.append("door opening reaches the eave: lower door_h or raise the roof")
    if p["floor"] + p["waist"] + 0.6 + p["window_h"] > p["roof"] - p["roof_rise"] - 0.2:
        w.append("windows reach the eave: lower window_h or the waist")
    clash = R.wheel_clash(p, p["floor"])
    if clash:
        w.append(clash)
    if p["running"] == "bogies" and not R.bogies_fit(p, p["length"]):
        w.append(f"bogies do not fit at length {p['length']:g}: two axles will be used")
    return w


def door_xs(p, Lb):
    return {0: [], 1: [0.0], 2: [-(Lb / 2 - p["door_w"] / 2 - 2.5), Lb / 2 - p["door_w"] / 2 - 2.5]}[p["side_doors"]]


def window_xs(p, Lb, doors):
    n, ww = p["windows"], p["window_w"]
    if n == 0:
        return []
    free = [x for x in (-Lb / 2 + 2.2 + ww / 2 + (Lb - 4.4 - ww) * i / max(1, 2 * n - 1) for i in range(2 * n))]
    free = [x for x in free if all(abs(x - d) > p["door_w"] / 2 + ww / 2 + 0.9 for d in doors)]
    if len(free) <= n:
        return free
    step = len(free) / n
    return [free[int(i * step + step / 2)] for i in range(n)]


def build(k, p):
    L, W, fl = p["length"], p["width"], p["floor"]
    eave, crown = p["roof"] - p["roof_rise"], p["roof"]
    bl = p["balcony_len"] if p["balcony"] else 0.0
    Lb = L - 2 * bl
    top = fl - 0.6
    R.underframe(k, p, L, W, top)
    k.box("Floor", "Floor", (0, 0, top + 0.3), (L, W, 0.6))
    k.proxy((0, 0, top + 0.3), (L, W, 0.6))
    dw, dh = p["door_w"], p["door_h"]
    doors = door_xs(p, Lb)
    wins = window_xs(p, Lb, doors)
    wz0 = fl + p["waist"] + 0.6
    zw = fl + p["waist"]
    for s in (-1, 1):
        y = s * (W / 2 - 0.25)
        k.wall("Lower", "Lower", "X", -Lb / 2, Lb / 2, y, fl, zw, 0.5, holes=[(d, fl, dw, dh) for d in doors])
        k.wall("Side", "Body", "X", -Lb / 2, Lb / 2, y, zw, eave, 0.5,
               holes=[(d, fl, dw, dh) for d in doors] + [(x, wz0, p["window_w"], p["window_h"]) for x in wins])
        k.wall("Waist", "Brass", "X", -Lb / 2 - 0.12, Lb / 2 + 0.12, y, zw - 0.25, zw + 0.25, 0.74,
               holes=[(d, fl, dw + 0.16, dh) for d in doors])
        k.proxy((0, y, (fl + eave) / 2), (Lb, 0.6, eave - fl))
        sash, glass = [], []
        for x in wins:
            glass.append(((x, y - s * 0.1, wz0 + p["window_h"] / 2), (p["window_w"], 0.2, p["window_h"])))
            sash += fkit.frame_boxes(x, y, wz0, p["window_w"], p["window_h"])
        for d in doors:
            k.box("Door", "Door", (d, y - s * 0.12, fl + dh / 2), (dw, 0.26, dh))
            sash += fkit.frame_boxes(d, y, fl, dw, dh, bottom=False)
            k.boxes("Handrail", "Brass", [((d + e * (dw / 2 + 0.55), s * (W / 2 + 0.14), fl + 2.8), (0.24, 0.24, 3.4))
                                          for e in (-1, 1)], detail=1)
            k.boxes("Step", "Iron", [((d, s * (W / 2 + 0.45), top - 0.9), (dw + 0.6, 1.1, 0.3)),
                                     ((d - dw / 2, s * (W / 2 + 0.05), top - 0.45), (0.3, 0.3, 1.2)),
                                     ((d + dw / 2, s * (W / 2 + 0.05), top - 0.45), (0.3, 0.3, 1.2))])
            k.measure(f"side door {'+-'[s < 0]}y at x {d:g}", f"{dw:g} x {dh:g} clear (avatar 5 tall)")
        if glass:
            k.boxes("Window", "Glass", glass)
        if sash:
            k.boxes("Sash", "Sash", sash)
    # arched roof sheet and the end walls that follow it
    Wr, segs = W + 1.0, k.segs(12)
    Lr = (L if p["balcony_roof"] else Lb) + 0.6
    k.prism("Roof", "Roof", fkit.shell(fkit.arc(Wr, p["roof_rise"], segs, eave), fkit.arc(Wr, p["roof_rise"], segs, eave - 0.45)),
            Lr, (0, 0, 0), axis="X")
    zt = fkit.arc_z(Wr, p["roof_rise"], eave - 0.2)
    half = W / 2 - 0.5
    for e in (-1, 1):
        xe = e * (Lb / 2 - 0.25)
        end_wall(k, xe, half, fl, eave, zt, dw, dh, segs)
        k.boxes("Sash", "Sash", fkit.frame_boxes(0, xe, fl, dw, dh, axis="Y", bottom=False))
        for yy, ww in (((-half - dw / 2) / 2, half - dw / 2), ((half + dw / 2) / 2, half - dw / 2)):
            k.proxy((xe, yy, (fl + eave) / 2), (0.6, ww, eave - fl))
        k.proxy((xe, 0, (fl + dh + eave) / 2), (0.6, dw, eave - fl - dh))
        k.measure(f"end doorway {'+-'[e < 0]}x", f"{dw:g} x {dh:g} clear")
        if bl:
            balcony(k, p, e, L, Lb, W, fl, eave)
    # roof collision: a flat crown slab and two slopes, so crates and players stand on it
    k.proxy((0, 0, crown - 0.3), (Lr, W * 0.5, 0.6))
    for s in (-1, 1):
        y0, y1 = s * W * 0.25, s * (Wr / 2)
        z0, z1 = crown - 0.3, eave - 0.1
        ang = math.degrees(math.atan2(z1 - z0, abs(y1 - y0)))
        k.proxy((0, (y0 + y1) / 2, (z0 + z1) / 2), (Lr, abs(y1 - y0) + 0.3, 0.6), rot=(s * ang, 0, 0))
    if p["vents"]:
        n = p["vents"]
        k.boxes("Vent", "Iron", [((-Lb / 2 + Lb * (i + 0.5) / n, 0, crown + 0.2), (0.9, 0.9, 0.8)) for i in range(n)], detail=1)
    if p["ladder"] and not p["balcony_roof"]:   # beside the roof end, stands on the balcony (or the buffer beam)
        xl, yl = Lb / 2 + 0.55, dw / 2 + 1.6
        z0 = fl if bl else top - 1.4
        R.ladder(k, xl, yl, z0, fkit.arc_z(Wr, p["roof_rise"], eave)(yl + 0.8) + 1.0, along="Y")
        k.boxes("LadderBracket", "Iron", [((Lb / 2 + 0.2, yl + s * 0.8, z), (0.5, 0.2, 0.2))
                                          for s in (-1, 1) for z in (fl + 2.0, eave - 0.6)])
    k.measure("floor top / eave / crown above rail", f"{fl:g} / {eave:g} / {crown:g} studs")


def end_wall(k, xe, half, fl, eave, zt, dw, dh, segs):
    """End wall with a doorway, its top following the roof arch: two side pieces and a lintel, never overlapping."""
    for u0, u1 in ((-half, -dw / 2), (dw / 2, half)):
        us = [u0 + (u1 - u0) * i / max(2, segs // 2) for i in range(max(2, segs // 2) + 1)]
        k.prism("EndWall", "Body", [(u0, 0.0), (u1, 0.0)] + [(u, zt(u) - fl) for u in reversed(us)], 0.5,
                (xe, 0, fl), axis="X")
    us = [-dw / 2 + dw * i / 3 for i in range(4)]
    k.prism("EndWall", "Body", [(-dw / 2, dh), (dw / 2, dh)] + [(u, zt(u) - fl) for u in reversed(us)], 0.5,
            (xe, 0, fl), axis="X")


def balcony(k, p, e, L, Lb, W, fl, eave):
    """Open end platform: posts to the roof, railings (a bar about every stud, brass top rail at the 3-stud line),
    a gangway gap at the end, and hazard edge lining."""
    x0, x1 = e * Lb / 2, e * L / 2
    xm, bl = (x0 + x1) / 2, abs(x1 - x0)
    gap = p["door_w"]
    ph = eave - fl + 0.2 if p["balcony_roof"] else 3.4         # chunky capped corner posts (style.form.railing)
    for s in (-1, 1):
        k.box("Post", "Iron", (x1 - e * 0.3, s * (W / 2 - 0.3), fl + ph / 2), (0.6, 0.6, ph))
        if not p["balcony_roof"]:
            k.box("PostCap", "Iron", (x1 - e * 0.3, s * (W / 2 - 0.3), fl + ph + 0.12), (0.85, 0.85, 0.25), detail=1)
    bars, rails = [], []
    for s in (-1, 1):   # side railings
        n = max(2, int(bl - 0.6))
        bars += [((x0 + e * (0.3 + (bl - 0.6) * (i + 0.5) / n), s * (W / 2 - 0.3), fl + 1.45), (0.16, 0.16, 2.9)) for i in range(n)]
        rails.append(((xm, s * (W / 2 - 0.3), fl + 3.0), (bl - 0.2, 0.36, 0.26)))
        k.proxy((xm, s * (W / 2 - 0.3), fl + 1.6), (bl, 0.4, 3.2))
        seg = (W / 2 - 0.3) - gap / 2          # end railing each side of the gangway gap
        yc = s * (gap / 2 + seg / 2)
        n2 = max(2, int(seg))
        bars += [((x1 - e * 0.3, s * (gap / 2 + seg * (i + 0.5) / n2), fl + 1.45), (0.16, 0.16, 2.9)) for i in range(n2)]
        rails.append(((x1 - e * 0.3, yc, fl + 3.0), (0.36, seg, 0.26)))
        k.proxy((x1 - e * 0.3, yc, fl + 1.6), (0.4, seg, 3.2))
    k.boxes("RailingBar", "Iron", bars)
    k.boxes("Railing", "Brass", rails)
    k.box("EdgeLine", "Hazard", (x1 - e * 0.26, 0, fl + 0.02), (0.48, gap, 0.1))


def avatar(p, lo, hi):
    bl = p["balcony_len"] if p["balcony"] else 0
    return (hi[0] - 1.5 - bl / 2, p["width"] / 4, p["floor"]) if bl else (hi[0] + 2.5, hi[1] + 1.5, -2.2)


def stands(p, lo, hi, view):
    """Two player positions (the world scrolls, the players move): the next vehicle's end, and the roof, where
    crews go for crates (gameplay.train.layout: roof ladder)."""
    s, l = R.pov_next_vehicle(p, lo, hi, p["floor"])
    return [("from the next vehicle", s, l),
            ("on the roof", (hi[0] - 3.0, 0.0, p["roof"]), (lo[0] + 0.3 * (hi[0] - lo[0]), lo[1], p["roof"] - 1.0))]
