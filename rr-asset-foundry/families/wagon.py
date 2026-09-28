"""Freight wagons: flat (crates), open (coal), box van, oval tank; two axles or bogies; weathering adds mismatched
patch plates and a taped 'temporary fix' (style.form.incompetence). Frame: x along, y across, z up, z = 0 rail top."""
import math
import _rolling as R

FAMILY = "wagon"
DESC = "Freight wagons (flat with crates, open coal wagon, box van, oval tank) on two axles or bogies."
TAGS = ["wagon", "freight", "truck", "van", "tank", "coal", "flatbed", "rolling stock", "train"]
OPEN = ["OQ-025"]          # exterior livery undecided: every colour here is assumed
PARAMS = {
    "kind": ("choice", "open", ["flat", "open", "box", "tank"], "body type"),
    "length": ("float", 30.0, 16, 64, "over the buffer beams, studs"),
    "width": ("float", "@tech.units.stock_width", 10, 20, "body width over the sides, studs"),
    "gauge": ("float", "@tech.units.gauge", 4, 12, "rail centre to centre, studs"),
    "deck": ("float", "@tech.units.stock_floor", 3, 8, "deck top above the rail top, studs"),
    "running": ("choice", "auto", ["auto", "axles", "bogies"], "auto: bogies from 40 studs long"),
    "wheel_r": ("float", 1.6, 1.0, 2.5, "wheel radius, studs"),
    "side_h": ("float", 4.0, 1.5, 8.0, "open wagon side height above the deck"),
    "body_h": ("float", 7.0, 4.0, 9.0, "box van side height / tank height above the deck"),
    "planks": ("int", 4, 2, 8, "plank rows on sides and ends"),
    "load": ("choice", "auto", ["auto", "none", "coal", "crates"], "auto: coal in open wagons, crates on flats"),
    "weathering": ("float", 0.3, 0.0, 1.0, "patch plates; 0.5+ adds a taped temporary fix"),
    "door": ("bool", True, "side doors (open: drop door, box: sliding door)"),
}
GROUPS = {   # recolour group: (rr-bible colour token, Roblox material[, reflectance])
    "Chassis": ("style.world.soot_black", "Metal"),
    "Steel": ("style.thumb.steel", "Metal"),
    "Buffer": ("style.brand.buffer_red", "SmoothPlastic"),
    "Iron": ("style.world.ironwork", "Metal"),
    "Timber": ("style.depot_kit.timber_dark", "WoodPlanks"),
    "Door": ("style.depot_kit.timber_light", "WoodPlanks"),
    "Roof": ("style.depot_kit.slate_roof", "Metal"),
    "Tank": ("style.depot_kit.teal_trim", "Metal"),
    "Load": ("style.cab.coal", "Slate"),
    "Crate": ("style.thumb.crate", "WoodPlanks"),
    "Patch": ("style.depot_kit.red_oxide", "CorrodedMetal"),
    "Hazard": ("style.world.hazard", "SmoothPlastic"),
    "Ink": ("style.brand.ink", "SmoothPlastic"),
}
PRESETS = {
    "open_coal": {"params": {"kind": "open", "length": 30, "load": "coal"}, "note": "two-axle open wagon heaped with coal"},
    "open_bogie": {"params": {"kind": "open", "length": 48, "load": "coal", "weathering": 0.7, "planks": 5},
                   "note": "long bogie coal wagon, patched and taped"},
    "flat_crates": {"params": {"kind": "flat", "length": 36, "load": "crates", "weathering": 0.2},
                    "note": "flat wagon with supply crates"},
    "box_van": {"params": {"kind": "box", "length": 32, "weathering": 0.4}, "note": "box van with a sliding door"},
    "tank_long": {"params": {"kind": "tank", "length": 44, "weathering": 0.2}, "note": "bogie oval tank wagon"},
}
DEFAULT_PRESET = "open_coal"
VIEW = {"stage": "track", "ground": "style.ground.pasture",
        "features": ["BufferHead", "Door", "Strap", "LadderRung", "Dome", "Stanchion", "Tape"],
        "player": "Players ride the train and never leave it: they see a wagon from the next vehicle's end platform "
                  "or roof. The train stays put; the world scrolls past.",
        "rules": [R.RUNG_RULE]}
OPTIONS = {"merge": "none", "collide": True, "lod": False}


def validate(p, canon):
    top = p["deck"] + {"box": p["body_h"] + 1.2, "tank": p["body_h"] + 1.7,
                       "open": p["side_h"] + 1.4, "flat": 3.6}[p["kind"]]
    roof = canon("tech.units.stock_roof")
    w = [f"top about {top:.1f} is above tech.units.stock_roof {roof:g} (tunnel crouch clearance)"] if top > roof else []
    clash = R.wheel_clash(p, p["deck"])
    if clash:
        w.append(clash)
    if p["running"] == "bogies" and not R.bogies_fit(p, p["length"]):
        w.append(f"bogies do not fit at length {p['length']:g}: two axles will be used")
    return w


def build(k, p):
    L, W, deck = p["length"], p["width"], p["deck"]
    top, kind = deck - 0.6, p["kind"]
    load = p["load"] if p["load"] != "auto" else {"open": "coal", "flat": "crates"}.get(kind, "none")
    R.underframe(k, p, L, W, top)
    if kind == "tank":
        k.box("Platform", "Chassis", (0, 0, top + 0.3), (L, W, 0.6))
    else:
        n = max(4, round(W / 1.8))
        pw = W / n
        k.boxes("Deck", "Timber", [((0, -W / 2 + pw * (i + 0.5), top + 0.3 - 0.025 * (i % 2)), (L, pw - 0.12, 0.6 - 0.05 * (i % 2)))
                                   for i in range(n)])        # odd planks sit 0.05 lower: grooves read, no gaps
    k.proxy((0, 0, (top + deck) / 2), (L, W, deck - top))
    k.measure("deck top above rail", f"{deck:g} studs")
    dw = min(6.0, L * 0.22)
    if kind in ("open", "box"):
        H = p["side_h"] if kind == "open" else p["body_h"]
        planked_body(k, p, L, W, deck, H, dw)
        if kind == "open":
            for s in (-1, 1):
                k.proxy((0, s * (W / 2 - 0.25), deck + H / 2), (L, 0.5, H))
                k.proxy((s * (L / 2 - 0.25), 0, deck + H / 2), (0.5, W, H))
            if load == "coal":
                coal(k, L, W, deck, H)
            k.measure("open wagon inside", f"{L - 1:g} x {W - 1:g} x {H:g} studs")
        else:
            van_roof(k, p, L, W, deck, H)
            k.proxy((0, 0, deck + (H + 1.2) / 2), (L, W, H + 1.2))
        weather_sides(k, p, L, W, deck, H, dw)
    elif kind == "flat":
        n = max(2, round(L / 8))
        for s in (-1, 1):
            k.boxes("Stanchion", "Iron", [((-L / 2 + 1 + (L - 2) * i / (n - 1), s * (W / 2 - 0.3), deck + 1.5),
                                           (0.5, 0.5, 3.0)) for i in range(n)])
        if load == "crates":
            crates(k, L, W, deck)
        weather_solebars(k, p, L, W, top)
    else:
        tank(k, p, L, W, deck)
        weather_solebars(k, p, L, W, top)


def planked_body(k, p, L, W, deck, H, dw):
    rows, rh = p["planks"], H / p["planks"]
    for s in (-1, 1):   # sides: alternate rows stand 0.08 proud, so plank lines read without gaps
        k.boxes("Side", "Timber", [((0, s * (W / 2 - 0.25 + 0.04 * (i % 2 == 0)), deck + rh * (i + 0.5)),
                                    (L, 0.5 + 0.08 * (i % 2 == 0), rh)) for i in range(rows)])
        k.boxes("End", "Timber", [((s * (L / 2 - 0.25 + 0.04 * (i % 2 == 0)), 0, deck + rh * (i + 0.5)),
                                   (0.5 + 0.08 * (i % 2 == 0), W - 1.0, rh)) for i in range(rows)])
        for e in (-1, 1):
            ph = H + (0.3 if p["kind"] == "open" else -0.1)      # a van's posts stop under the roof sheet
            k.box("CornerPost", "Iron", (e * (L / 2 - 0.2), s * (W / 2 - 0.1), deck + ph / 2), (0.7, 0.7, ph))
        n = max(2, round(L / 7))
        xs = [-L / 2 + L * (i + 0.5) / n for i in range(n)]
        xs = [x for x in xs if not (p["door"] and abs(x) < dw / 2 + 0.8)]
        k.boxes("Strap", "Iron", [((x, s * (W / 2 + 0.15), deck + H / 2), (0.45, 0.14, H)) for x in xs], detail=1)
        k.boxes("EndStrap", "Iron", [((s * (L / 2 + 0.15), y, deck + H / 2), (0.14, 0.45, H)) for y in (-W / 4, W / 4)], detail=1)
        if p["door"]:
            if p["kind"] == "open":
                k.box("Door", "Door", (0, s * (W / 2 + 0.05), deck + H / 2), (dw, 0.3, H - 0.2))
                k.boxes("DoorStrap", "Iron", [((0, s * (W / 2 + 0.26), deck + H * f), (dw + 0.3, 0.12, 0.4)) for f in (0.25, 0.75)], detail=1)
            else:
                k.box("Door", "Door", (dw / 2, s * (W / 2 + 0.15), deck + (H - 0.4) / 2 + 0.2), (dw, 0.3, H - 0.4))
                k.box("DoorRail", "Iron", (dw / 2, s * (W / 2 + 0.2), deck + H - 0.3), (2 * dw + 1, 0.3, 0.3))
                k.box("DoorHandle", "Iron", (0.5, s * (W / 2 + 0.36), deck + H * 0.45), (0.25, 0.14, 1.2), detail=1)


def van_roof(k, p, L, W, deck, H):
    import fkit
    eave, rise, Wr = deck + H, 1.2, W + 0.8
    segs = k.segs(10)
    k.prism("Roof", "Roof", fkit.shell(fkit.arc(Wr, rise, segs, eave), fkit.arc(Wr, rise, segs, eave - 0.4)),
            L + 0.8, (0, 0, 0), axis="X")
    zt = fkit.arc_z(Wr, rise, eave - 0.2)
    half = W / 2 - 0.5
    us = [-half + 2 * half * i / segs for i in range(segs + 1)]
    for e in (-1, 1):   # end walls follow the roof curve so no gap shows under it
        k.prism("EndGable", "Timber", [(-half, 0.0), (half, 0.0)] + [(u, zt(u) - eave) for u in reversed(us)],
                0.5, (e * (L / 2 - 0.25), 0, eave), axis="X")
        k.boxes("Vent", "Iron", [((e * (L / 2 + 0.14), y, eave - 0.9), (0.24, 2.0, 0.9)) for y in (-W / 4, W / 4)], detail=1)


def coal(k, L, W, deck, H):
    """A rounded heap proud of the sides (what a 3P camera looks down on) plus chunky lumps on its surface."""
    h, top = W / 2 - 0.55, H + 1.1
    prof = [(-h, -0.05), (h, -0.05), (h, H - 0.4), (h * 0.6, H + 0.5), (h * 0.25, top), (-h * 0.25, top),
            (-h * 0.6, H + 0.5), (-h, H - 0.4)]
    k.prism("Heap", "Load", prof, L - 1.1, (0, 0, deck), axis="X")

    def surface(y):
        y = abs(y)
        pts = [(0, top), (h * 0.25, top), (h * 0.6, H + 0.5), (h, H - 0.4)]
        for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
            if y <= y1:
                return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
        return H - 0.4
    rnd, lumps = k.rng, []
    for _ in range(max(10, int(L * 0.8))):
        y = rnd.uniform(-h * 0.75, h * 0.75)
        s = rnd.uniform(0.7, 1.4)
        lumps.append(((rnd.uniform(-L / 2 + 1.6, L / 2 - 1.6), y, deck + surface(y) - s * 0.25), (s, s * 0.8, s * 0.7),
                      (rnd.uniform(-25, 25), rnd.uniform(-25, 25), rnd.uniform(0, 90))))
    k.boxes("Lump", "Load", lumps, detail=1)


def crates(k, L, W, deck):
    n = 2 if L < 34 else 3
    s, h = 4.2, 3.6
    bent = k.rng.randrange(n)
    for i in range(n):
        x = -L / 2 + L * (i + 0.5) / n
        ang = k.rng.choice((-7, 6)) if i == bent else 0      # one bent thing (style.form.handmade)
        k.box("Crate", "Crate", (x, 0, deck + h / 2), (s, s, h), rot=(0, 0, ang))
        c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        bands = [((x + dx * c, dx * sn, deck + h / 2), (0.35, s + 0.12, h + 0.1), (0, 0, ang)) for dx in (-s / 3, s / 3)]
        k.boxes("CrateBand", "Iron", bands, detail=1)
        k.proxy((x, 0, deck + h / 2), (s, s, h), rot=(0, 0, ang))


def tank(k, p, L, W, deck):
    Lt, rz = L - 3.0, p["body_h"] / 2
    ry = min(W / 2 - 1.5, rz * 1.6)
    zc = deck + 0.4 + rz
    k.cyl("Barrel", "Tank", (0, 0, zc), 1.0, Lt, axis="X", segs=24, scale=(1, ry, rz))
    k.cyl("Head", "Tank", (Lt / 2 + 0.4, 0, zc), 1.0, 0.8, axis="X", segs=24, r2=0.8, scale=(1, ry, rz))
    k.cyl("Head", "Tank", (-Lt / 2 - 0.4, 0, zc), 0.8, 0.8, axis="X", segs=24, r2=1.0, scale=(1, ry, rz))
    for x in (-Lt / 3, 0, Lt / 3):
        k.cyl("Band", "Iron", (x, 0, zc), 1.03, 0.3, axis="X", segs=24, scale=(1, ry, rz), detail=1)
        k.box("Saddle", "Chassis", (x + (1.2 if x == 0 else 0), 0, deck + rz * 0.45), (1.2, ry * 1.6, rz * 0.9))
    k.cyl("Dome", "Tank", (0, 0, zc + rz + 0.4), 1.4, 1.4, segs=16)
    k.cyl("Hatch", "Iron", (0, 0, zc + rz + 1.15), 1.1, 0.3, segs=16)
    R.ladder(k, Lt / 6, -(ry + 0.35), deck, zc + rz * 0.6)
    k.proxy((0, 0, zc), (Lt + 1.6, 2 * ry, 2 * rz))
    k.measure("tank", f"{Lt + 1.6:g} long, oval {2 * ry:.1f} x {2 * rz:.1f}")


def weather_sides(k, p, L, W, deck, H, dw):
    rnd, n = k.rng, round(p["weathering"] * 6)
    for s in (-1, 1):
        items = []
        for i in range(n // 2 + (s < 0) * (n % 2)):
            x = rnd.uniform(-L / 2 + 1.8, L / 2 - 1.8)
            if p["door"] and abs(x) < dw / 2 + 1.4:
                x = math.copysign(dw / 2 + 1.4 + rnd.uniform(0, 1.5), x or 1)
            w, h = rnd.uniform(1.2, 2.4), rnd.uniform(0.9, min(1.8, H - 0.6))
            items.append(((x, s * (W / 2 + 0.14), deck + rnd.uniform(0.4 + h / 2, H - 0.3 - h / 2)), (w, 0.1, h),
                          (0, rnd.uniform(-7, 7), 0)))
        k.boxes("Patch", "Patch", items)
    if p["weathering"] >= 0.5:   # a taped "temporary fix" across the camera-side planks
        x0, z0, ang = -L / 4 - 1.5, deck + H * 0.3, 28
        segs = {"Hazard": [], "Ink": []}
        for i in range(6):
            d = (i - 2.5) * 1.1
            c = (x0 + d * math.cos(math.radians(ang)), -(W / 2 + 0.18), z0 + d * math.sin(math.radians(ang)) + H * 0.2)
            segs["Hazard" if i % 2 == 0 else "Ink"].append((c, (1.1, 0.24, 0.55), (0, -ang, 0)))
        for g, items in segs.items():
            k.boxes("Tape", g, items)


def weather_solebars(k, p, L, W, top):
    rnd, n = k.rng, round(p["weathering"] * 4)
    for s in (-1, 1):
        items = [((rnd.uniform(-L / 2 + 2, L / 2 - 2), s * (W / 2 - 0.1), top - 0.55), (rnd.uniform(1.0, 2.0), 0.1, 0.9))
                 for _ in range(n // 2 + (s < 0) * (n % 2))]
        k.boxes("Patch", "Patch", items)


def pov(p, lo, hi):
    return R.pov_next_vehicle(p, lo, hi, p["deck"])
