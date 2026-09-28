"""Freight wagons: flat (crates), open (coal), box van, oval tank; two axles or bogies with outside frames (running
gear shows under the wide OQ-030 body); weathering adds whole replaced planks, solebar patch plates and a taped
'temporary fix' (style.form.incompetence). Frame: x along, y across, z up, z = 0 rail top.
Critic lessons baked in (trial 2026-09-28): ironwork >= 0.9 stud across (A5 >= 5 px at 400 px), a two-peak coal heap
2.5+ above the side top, a light cap rail between dark coal and dark ironwork, no lone sticker-like patches."""
import math
import _rolling as R

FAMILY = "wagon"
DESC = "Freight wagons (flat with crates, open coal wagon, box van, oval tank) on two axles or bogies."
TAGS = ["wagon", "freight", "truck", "van", "tank", "coal", "flatbed", "rolling stock", "train"]
OPEN = ["OQ-025", "OQ-045"]  # livery undecided (every colour is assumed); where wagons appear undecided
PARAMS = {
    "kind": ("choice", "open", ["flat", "open", "box", "tank"], "body type"),
    "length": ("float", 30.0, 16, 64, "over the buffer beams, studs"),
    "width": ("float", "@tech.units.stock_width", 10, 20, "body width over the sides, studs"),
    "gauge": ("float", "@tech.units.gauge", 4, 12, "rail centre to centre, studs"),
    "deck": ("float", "@tech.units.stock_floor", 3, 8, "deck top above the rail top, studs"),
    "running": ("choice", "auto", ["auto", "axles", "bogies"], "auto: bogies from 40 studs long"),
    "wheel_r": ("float", 2.0, 1.0, 2.5, "wheel radius, studs (2.0 is the most a 5-stud deck clears)"),
    "side_h": ("float", 4.0, 1.5, 8.0, "open wagon side height above the deck"),
    "body_h": ("float", 7.0, 4.0, 9.0, "box van side height / tank height above the deck"),
    "planks": ("int", 4, 2, 8, "plank rows on sides and ends"),
    "load": ("choice", "auto", ["auto", "none", "coal", "crates"], "auto: coal in open wagons, crates on flats"),
    "heap": ("float", 2.75, 0.5, 4.0, "coal crest above the side top, studs"),
    "peaks": ("int", 2, 1, 3, "coal heap peaks along the length (symmetric: never a tender's stepped coal space)"),
    "weathering": ("float", 0.3, 0.0, 1.0, "replaced planks and solebar plates; 0.5+ adds a taped temporary fix"),
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
    "Cap": ("style.depot_kit.timber_light", "WoodPlanks"),        # open wagon top rails: a light line above dark coal
    "Repair": ("style.depot_kit.timber_light", "WoodPlanks"),     # whole replaced planks, strap to strap
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
        "features": ["BufferHead", "Door", "DoorStrap", "Strap", "EndStrap", "Cap", "Side", "Repair", "Lump", "Wheel",
                     "Axlebox", "LadderRung", "Dome", "Stanchion", "Tape"],
        "premise": "siding",
        "premises": {   # where the player sees a wagon; canon has no wagons in the crew train (OQ-045)
            "siding": "ASSUMED (OQ-045 default A; the owner decides): yard dressing on the marshalling-yard sidings "
                      "(world.prefabs.15, world.biomes.mvp_forks), seen from the coach on the running line "
                      "(gameplay.train.layout, gameplay.train.keep_on) at the siding spacing of world.prefabs.15 while "
                      "the world scrolls past (D-002); seen in motion, so style.dont.hairlines applies.",
            "lobby": "ASSUMED (OQ-045 option B): Depot Lobby yard dressing, seen on foot at walking distance.",
            "coupled": "CONTRADICTS canon (gameplay.train.layout is cab + coach; D-013 no tender car): only if the "
                       "owner picks OQ-045 option C (wagons in the crew's train); seen from the next vehicle's end platform."},
        "nums": {"siding": "@world.prefabs.15#1"},      # running line to siding centres (its note's second number)
        "rules": [R.RUNG_RULE]}
OPTIONS = {"merge": "none", "collide": True, "lod": False}


def validate(p, canon):
    coal = p["load"] == "coal" or (p["load"] == "auto" and p["kind"] == "open")
    top = p["deck"] + {"box": p["body_h"] + 1.2, "tank": p["body_h"] + 1.7,
                       "open": p["side_h"] + (p["heap"] + 0.9 if coal else 0.4), "flat": 3.6}[p["kind"]]
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
    R.underframe(k, p, L, W, top, outside=True)
    if kind == "tank":
        k.box("Platform", "Chassis", (0, 0, top + 0.3), (L, W, 0.6))
    else:
        n = max(4, round(W / 1.8))
        pw, items = W / n, []
        for i in range(n):       # odd planks sit 0.05 lower and lap under their neighbours: grooves read, no see-through gaps
            y0, y1 = (-W / 2 + pw * i + 0.06, -W / 2 + pw * (i + 1) - 0.06) if i % 2 == 0 else \
                (max(-W / 2, -W / 2 + pw * i - 0.05), min(W / 2, -W / 2 + pw * (i + 1) + 0.05))
            items.append(((0, (y0 + y1) / 2, top + 0.3 - 0.025 * (i % 2)),
                          (L - 0.04 * (i % 2), y1 - y0, 0.6 - 0.05 * (i % 2))))
        k.boxes("Deck", "Timber", items)
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
                coal(k, p, L, W, deck, H)
            k.measure("open wagon inside", f"{L - 1:g} x {W - 1:g} x {H:g} studs")
        else:
            van_roof(k, p, L, W, deck, H)
            k.proxy((0, 0, deck + (H + 1.2) / 2), (L, W, H + 1.2))
        weather_sides(k, p, L, W, deck, H, dw)
    elif kind == "flat":
        n = max(2, round(L / 8))
        for s in (-1, 1):
            k.boxes("Stanchion", "Iron", [((-L / 2 + 1 + (L - 2) * i / (n - 1), s * (W / 2 - 0.3), deck + 1.5),
                                           (0.8, 0.7, 3.0)) for i in range(n)])      # 0.5 measured 3.4 px
        if load == "crates":
            crates(k, L, W, deck)
        weather_solebars(k, p, L, W, top)
    else:
        tank(k, p, L, W, deck)
        weather_solebars(k, p, L, W, top)


def planked_body(k, p, L, W, deck, H, dw):
    rows, rh, is_open = p["planks"], H / p["planks"], p["kind"] == "open"
    for s in (-1, 1):   # sides: alternate rows stand 0.08 proud, so plank lines read without gaps
        k.boxes("Side", "Timber", [((0, s * (W / 2 - 0.25 + 0.04 * (i % 2 == 0)), deck + rh * (i + 0.5)),
                                    (L, 0.5 + 0.08 * (i % 2 == 0), rh)) for i in range(rows)])
        k.boxes("End", "Timber", [((s * (L / 2 - 0.25 + 0.04 * (i % 2 == 0)), 0, deck + rh * (i + 0.5)),
                                   (0.5 + 0.08 * (i % 2 == 0), W - 1.0, rh)) for i in range(rows)])
        for e in (-1, 1):
            ph = H + (0.3 if p["kind"] == "open" else -0.1)      # a van's posts stop under the roof sheet
            k.box("CornerPost", "Iron", (e * (L / 2 - 0.2), s * (W / 2 - 0.1), deck + ph / 2), (0.7, 0.7, ph))
        # ironwork sized for >= 5 px at the 400 px game view, where the 3/4 angle foreshortens a side to about 0.8
        # (measured: 0.45 wide gave 2.7 px, 0.9 x 0.18 gave 3.8 px; 1.3 x 0.3 about 5.6 px)
        # (tops stop 0.04 under the top plank's, so no up-facing faces share a plane when the top row is a proud one)
        k.boxes("Strap", "Iron", [((x, s * (W / 2 + 0.16), deck + H / 2 - 0.02), (1.3, 0.3, H - 0.04))
                                  for x in strap_xs(p, L, dw)], detail=1)
        k.boxes("EndStrap", "Iron", [((s * (L / 2 + 0.16), y, deck + H / 2 - 0.02), (0.3, 1.5, H - 0.04))
                                     for y in (-W / 4, W / 4)], detail=1)
        if is_open:              # light top rails: a value break between dark coal and dark ironwork
            k.box("Cap", "Cap", (0, s * (W / 2 - 0.19), deck + H - 0.1), (L - 0.8, 0.68, 0.9))
            k.box("Cap", "Cap", (s * (L / 2 - 0.2), 0, deck + H - 0.115), (0.66, W - 0.8, 0.87))
        if p["door"]:
            if is_open:          # the door stops under the cap rail
                k.box("Door", "Door", (0, s * (W / 2 + 0.05), deck + 0.1 + (H - 0.7) / 2), (dw, 0.3, H - 0.7))
                k.boxes("DoorStrap", "Iron", [((0, s * (W / 2 + 0.26), deck + H * f), (dw + 0.3, 0.14, 1.1))
                                              for f in (0.27, 0.68)], detail=1)
            else:
                k.box("Door", "Door", (dw / 2, s * (W / 2 + 0.15), deck + (H - 0.4) / 2 + 0.2), (dw, 0.3, H - 0.4))
                k.box("DoorRail", "Iron", (dw / 2, s * (W / 2 + 0.2), deck + H - 0.3), (2 * dw + 1, 0.3, 0.3))
                k.box("DoorHandle", "Iron", (0.5, s * (W / 2 + 0.36), deck + H * 0.45), (0.25, 0.14, 1.2), detail=1)


def strap_xs(p, L, dw):
    n = max(2, round(L / 7))
    xs = [-L / 2 + L * (i + 0.5) / n for i in range(n)]
    return [x for x in xs if not (p["door"] and abs(x) < dw / 2 + 1.0)]


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


def coal(k, p, L, W, deck, H):
    """A heap whose rim hides inside the walls and whose crest stands p['heap'] above the side top, with p['peaks']
    symmetric peaks along the length (a flat-topped prism read as a tarp in the trial), plus a few big lumps."""
    rim, crest, n = H - 0.35, H + p["heap"] + 0.05, p["peaks"]
    sx, sy = L - 1.1, W - 1.1

    def height(u, v):
        ends = math.sin(min(1.0, (1 - abs(u)) / 0.35) * math.pi / 2)
        along = 0.62 + 0.38 * (0.5 - 0.5 * math.cos(math.pi * n * (u + 1)))
        across = math.cos(min(1.0, abs(v)) * math.pi / 2) ** 0.7
        return rim + (crest - rim) * ends * along * across
    k.heightfield("Heap", "Load", (0, 0, deck - 0.05), (sx, sy), height, nx=max(8, round(L / 2.5)), ny=6)
    rnd, lumps = k.rng, []
    for _ in range(max(6, int(L * 0.3))):          # fewer, bigger lumps: >= 0.9 stud on the smallest side
        u, v, s = rnd.uniform(-0.8, 0.8), rnd.uniform(-0.7, 0.7), rnd.uniform(1.2, 2.0)
        lumps.append(((u * sx / 2, v * sy / 2, deck - 0.05 + height(u, v) - 0.05 * s), (s, s * 0.85, s * 0.75),
                      (rnd.uniform(-20, 20), rnd.uniform(-20, 20), rnd.uniform(0, 90))))
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
    """Whole replaced planks in light timber, strap to strap (a lone plate smaller than a plank read as a sticker in
    the trial), camera side (-y) first; weathering 0.5+ adds a taped temporary fix."""
    rnd, n, rows = k.rng, round(p["weathering"] * 4), p["planks"]
    rh = H / rows
    cuts = sorted([-L / 2 + 0.2, L / 2 - 0.2] + strap_xs(p, L, dw))
    spans = [(a, b) for a, b in zip(cuts, cuts[1:]) if not (p["door"] and a < dw / 2 + 0.3 and b > -dw / 2 - 0.3)]
    items = {-1: [], 1: []}
    for i in range(min(n, 2 * len(spans))):
        s = -1 if i % 2 == 0 else 1
        x0, x1 = spans[rnd.randrange(len(spans))]
        r = rnd.randrange(max(1, rows - 1))           # never the top row (under the cap rail or the eave)
        e = 0.08 * (r % 2 == 0)                       # proud rows stand 0.08 out; the repair 0.03 beyond its row
        yi, yo = W / 2 - 0.3, W / 2 + e + 0.03
        items[s].append((((x0 + x1) / 2, s * (yi + yo) / 2, deck + rh * (r + 0.5)), (x1 - x0, yo - yi, rh - 0.06)))
    for s in (-1, 1):
        k.boxes("Repair", "Repair", items[s])
    if p["weathering"] >= 0.5:   # a taped "temporary fix" across the camera-side planks
        x0, z0, ang = -L / 4 - 1.5, deck + H * 0.3, 28
        segs = {"Hazard": [], "Ink": []}
        for i in range(6):
            d = (i - 2.5) * 1.2
            c = (x0 + d * math.cos(math.radians(ang)), -(W / 2 + 0.22), z0 + d * math.sin(math.radians(ang)) + H * 0.2)
            segs["Hazard" if i % 2 == 0 else "Ink"].append((c, (1.2, 0.24, 0.9), (0, -ang, 0)))
        for g, items2 in segs.items():
            k.boxes("Tape", g, items2)


def weather_solebars(k, p, L, W, top):
    rnd, n = k.rng, round(p["weathering"] * 4)
    for s in (-1, 1):
        items = [((rnd.uniform(-L / 2 + 2, L / 2 - 2), s * (W / 2 - 0.1), top - 0.55), (rnd.uniform(1.0, 2.0), 0.1, 0.9))
                 for _ in range(n // 2 + (s < 0) * (n % 2))]
        k.boxes("Patch", "Patch", items)


def stands(p, lo, hi, view):
    """Player stands for the chosen premise: [(label, (x, y, floor_z), look_at)]; forge renders POV 3P at each and
    1P at the first. The coach shares the wagon's canon floor and width defaults (tech.units.stock_floor/_width)."""
    cx = (lo[0] + hi[0]) / 2
    look = (cx, 0.0, p["deck"] + 1.0)
    pr = view.get("premise") or "siding"
    if pr == "coupled":
        s, l = R.pov_next_vehicle(p, lo, hi, p["deck"])
        return [("next vehicle's end platform", s, l)]
    if pr == "lobby":
        d = max(14.0, 0.9 * (hi[0] - lo[0]))
        return [("on foot, 3/4", (cx + 0.5 * d, lo[1] - d, view["gz"]), look),
                ("on foot, abeam", (cx - 0.2 * d, lo[1] - 0.8 * d, view["gz"]), look)]
    if "siding" not in view.get("nums", {}):
        raise ValueError("this plan predates POV premises: rebuild with make --force")
    y = -(view["nums"]["siding"] - p["width"] / 2 - 0.7)       # the coach edge nearest the siding
    return [("from the coach, abeam", (cx, y, p["deck"]), look),
            ("from the coach, approaching", (cx + 50.0, y, p["deck"]), look)]
