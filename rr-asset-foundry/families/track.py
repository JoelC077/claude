"""Track pieces that tile along x: ballast bed, sleepers, chairs, rails and a cinder verge; plus a buffer stop whose
beam and buffers sit at the rolling-stock buffer height. Pieces are exactly `length` long with sleepers at half-pitch
from each end, so copies butt seamlessly. Streamed scenery: merged one MeshPart per group, no collision.
Frame: x along the track, y across, z up, z = 0 rail top (the same datum as the carriage and wagon families)."""
import math

FAMILY = "track"
DESC = "Tiling track pieces (straight, buffer stop): ballast, sleepers, chairs, rails, cinder verge."
TAGS = ["track", "rail", "rails", "railway", "sleeper", "ballast", "buffer stop", "terminus", "segment", "line"]
OPEN = []
PARAMS = {
    "kind": ("choice", "straight", ["straight", "buffer_stop"], "piece type"),
    "length": ("float", "@tech.units.track_piece", 8, 64, "piece length, studs (tiles exactly)"),
    "gauge": ("float", "@tech.units.gauge", 4, 12, "rail centre to centre, studs"),
    "ballast_w": ("float", "@tech.units.ballast_w", 12, 40, "ballast bed width at its foot, studs"),
    "ballast_h": ("float", 1.4, 0.6, 3.0, "ballast bed depth below the sleepers' bed line"),
    "sleepers": ("int", 4, 2, 10, "sleepers per piece"),
    "sleeper_len": ("float", 14.0, 8.0, 22.0, "sleeper length across the track"),
    "sleeper_w": ("float", 1.6, 0.8, 3.0, "sleeper width along the track"),
    "rail_h": ("float", 1.2, 0.6, 2.0, "rail height (foot to head)"),
    "chairs": ("bool", True, "iron chairs under the rails"),
    "verge": ("bool", True, "cinder verge strips beside the sleeper ends"),
    "floor": ("float", "@tech.units.stock_floor", 3, 8, "rolling-stock floor, sets the buffer stop height"),
    "stock_width": ("float", "@tech.units.stock_width", 10, 20, "rolling-stock width, sets the buffer spacing"),
}
GROUPS = {
    "Ballast": ("style.ground.ballast", "Pebble"),
    "Sleeper": ("style.thumb.sleeper", "Wood"),
    "Rail": ("style.ground.rail", "Metal"),
    "Chair": ("style.depot_kit.iron", "Metal"),
    "Cinder": ("style.ground.cinder_verge", "Asphalt"),
    "Buffer": ("style.brand.buffer_red", "SmoothPlastic"),
    "Steel": ("style.thumb.steel", "Metal"),
    "Iron": ("style.world.ironwork", "Metal"),
    "Hazard": ("style.world.hazard", "SmoothPlastic"),
    "Ink": ("style.brand.ink", "SmoothPlastic"),
    "Lamp": ("style.depot_kit.window_glow", "Neon"),
}
PRESETS = {
    "straight": {"params": {"kind": "straight"}, "note": "one canon track piece; tiles along x"},
    "straight_long": {"params": {"kind": "straight", "length": 32, "sleepers": 8}, "note": "two canon pieces in one mesh set"},
    "buffer_stop": {"params": {"kind": "buffer_stop"}, "note": "terminus buffer stop on one piece, buffers at stock height"},
}
DEFAULT_PRESET = "straight"
VIEW = {"ground": "style.ground.pasture", "top": True,
        "features": ["Rail", "Sleeper", "Chair", "Buffer", "Lamp"],
        "player": "Seen from the train: the track scrolls past under and beside the carriages, and the terminus buffer "
                  "stop comes up ahead at the end of the line."}
OPTIONS = {"merge": "group", "collide": False, "lod": False}


def validate(p, canon):
    w = []
    seg = canon("tech.units.segment_len")
    if p["kind"] == "straight" and abs(seg / p["length"] - round(seg / p["length"])) > 1e-6:
        w.append(f"length {p['length']:g} does not divide tech.units.segment_len {seg:g}: pieces will not fill a segment")
    if p["sleeper_len"] < p["gauge"] + 3:
        w.append("sleepers barely reach past the rails: raise sleeper_len")
    top_w = p["ballast_w"] - 2 * p["ballast_h"] * 1.5
    if p["sleeper_len"] > top_w - 1:
        w.append(f"sleepers overhang the ballast top ({top_w:.1f} wide)")
    return w


def levels(p):
    chair = 0.3 if p["chairs"] else 0.0
    s_top = -p["rail_h"] - chair
    return chair, s_top, s_top - 0.8, s_top - 0.5       # chair h, sleeper top, sleeper bottom, ballast top


def build(k, p):
    L, g = p["length"], p["gauge"]
    chair, s_top, s_bot, b_top = levels(p)
    bw, bh = p["ballast_w"], p["ballast_h"]
    top_w = bw - 2 * bh * 1.5
    k.prism("Bed", "Ballast", [(-bw / 2, b_top - bh), (bw / 2, b_top - bh), (top_w / 2, b_top), (-top_w / 2, b_top)],
            L, (0, 0, 0), axis="X")
    n, pitch = p["sleepers"], L / p["sleepers"]
    stop = p["kind"] == "buffer_stop"
    xb = L / 2 - 4.0 if stop else None
    k.boxes("Sleepers", "Sleeper", [((-L / 2 + pitch * (i + 0.5), 0, (s_top + s_bot) / 2), (p["sleeper_w"], p["sleeper_len"], 0.8))
                                    for i in range(n)])
    x1 = xb + 0.6 if stop else L / 2
    rails = []
    for s in (-1, 1):
        y = s * g / 2
        rh = p["rail_h"]
        for w, z0, z1 in ((1.0, -rh, -rh + 0.25), (0.35, -rh + 0.2, -0.35), (0.7, -0.4, 0.0)):   # foot, web, head
            rails.append((((-L / 2 + x1) / 2, y, (z0 + z1) / 2), (x1 + L / 2, w, z1 - z0)))
    k.boxes("Rails", "Rail", rails)
    if chair:
        k.boxes("Chairs", "Chair", [((-L / 2 + pitch * (i + 0.5), s * g / 2, s_top + chair / 2 + 0.02), (1.1, 1.3, chair + 0.05))
                                    for i in range(n) for s in (-1, 1) if not stop or -L / 2 + pitch * (i + 0.5) < x1])
    if p["verge"]:
        off = p["sleeper_len"] / 2 + 1.0
        if off + 0.7 < top_w / 2:
            k.boxes("Verge", "Cinder", [((0, s * off, b_top + 0.03), (L, 1.4, 0.1)) for s in (-1, 1)])
    k.measure("tiling", f"piece {L:g} long, sleeper pitch {pitch:.2f} from {pitch / 2:.2f}; rail top at z 0, gauge {g:g}")
    if stop:
        buffer_stop(k, p, xb, b_top)


def buffer_stop(k, p, xb, b_top):
    """Beam and buffers at the stock's buffer height (floor - 1.3, as in the rolling-stock underframe)."""
    W, g = p["stock_width"], p["gauge"]
    bz = p["floor"] - 1.3
    half = W / 2 - 1.0
    k.box("BufferBeam", "Buffer", (xb + 0.6, 0, bz), (1.2, 2 * half, 1.4))
    for s in (-1, 1):
        y = s * (W / 2 - 2.4)
        k.cyl("BufferStock", "Iron", (xb - 0.5, y, bz), 0.5, 1.0, axis="X", segs=10)
        k.cyl("BufferHead", "Steel", (xb - 1.15, y, bz), 0.85, 0.3, axis="X", segs=14)
    posts = [((xb + 0.6, s * (g / 2 + 1.4), (b_top + bz - 0.7) / 2), (0.6, 0.6, bz - 0.7 - b_top + 0.1)) for s in (-1, 1)]
    k.boxes("Post", "Iron", posts)
    run = 3.2
    ln = math.hypot(run, bz - b_top)
    ang = math.degrees(math.atan2(bz - b_top, run))
    k.boxes("Strut", "Iron", [((xb + 1.2 + run / 2, s * (g / 2 + 1.4), (bz + b_top) / 2), (ln, 0.5, 0.5), (0, ang, 0))
                              for s in (-1, 1)])
    stripes, m = {"Hazard": [], "Ink": []}, 6
    for i in range(m):   # chunky stripes on the face that meets the train
        y = -half + 2 * half * (i + 0.5) / m
        stripes["Hazard" if i % 2 == 0 else "Ink"].append(((xb - 0.08, y, bz), (0.12, 2 * half / m, 1.1)))
    for grp, items in stripes.items():
        k.boxes("Stripe", grp, items)
    k.box("LampPost", "Iron", (xb + 0.6, 0, bz + 1.1), (0.4, 0.4, 0.9))
    k.cyl("Lamp", "Lamp", (xb + 0.6, 0, bz + 1.8), 0.4, 0.6, segs=10)
    k.measure("buffer stop", f"buffers at {bz:g} above rail top (stock floor {p['floor']:g} - 1.3), {2 * (W / 2 - 2.4):g} apart")


def tile_offsets(p):
    """Stage copies for the renders: 3 each way for a straight; none for a buffer stop (it ends the line)."""
    return [] if p["kind"] == "buffer_stop" else [s * i * p["length"] for i in (1, 2, 3) for s in (-1, 1)]


def stands(p, lo, hi, view):
    """From the end balcony of a coach standing on this track, looking along it; then two pieces further off, as the
    scrolling world brings it in (D-002)."""
    look = (hi[0], 0.0, -1.5)
    return [("coach end balcony", (lo[0] - 10.0, -2.0, p["floor"]), look),
            ("coach end balcony, piece further ahead", (lo[0] - 10.0 - 2 * p["length"], -2.0, p["floor"]), look)]
