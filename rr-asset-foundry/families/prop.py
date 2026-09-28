"""Yard and supply props: the supply crate (boards over a dark core, iron bands, optional hazard band; stacks of
up to 4 with one bent), oil drum clusters (one tipped over), and the taped 'temporary' barrier (A-frame trestles,
hazard/ink striped plank, warning lamp). Frame: z = 0 ground, the prop centred on the origin."""
import math

FAMILY = "prop"
DESC = "Yard props: supply crate (stackable), oil drum cluster, hazard-striped trestle barrier."
TAGS = ["prop", "crate", "box", "supply", "drum", "barrel", "barrier", "clutter", "lobby", "yard", "roadblock"]
OPEN = []
PARAMS = {
    "kind": ("choice", "crate", ["crate", "drum", "barrier"], "prop type"),
    "size": ("float", 4.0, 2.0, 8.0, "crate edge / barrier height, studs"),
    "count": ("int", 1, 1, 4, "crates in the stack / drums in the cluster"),
    "planks": ("int", 3, 2, 6, "crate boards per face"),
    "bands": ("bool", True, "crate iron bands and corner posts"),
    "stripe": ("bool", False, "crate hazard band around the middle"),
    "drum_r": ("float", 1.3, 0.8, 2.0, "drum radius"),
    "drum_h": ("float", 3.6, 2.0, 5.0, "drum height"),
    "tipped": ("bool", True, "one drum on its side when there are 3 or more (style.form.handmade)"),
    "barrier_w": ("float", 8.0, 4.0, 16.0, "barrier length"),
    "stripes": ("int", 6, 3, 12, "barrier plank stripes"),
    "lamp": ("bool", True, "barrier warning lamp"),
    "weathering": ("float", 0.3, 0.0, 1.0, "crates: a patch board; drums: sooty hoops; barrier: taped leg"),
}
GROUPS = {
    "Crate": ("style.thumb.crate", "WoodPlanks"),
    "CrateDark": ("style.depot_kit.timber_dark", "Wood"),
    "Iron": ("style.depot_kit.iron", "Metal"),
    "Hazard": ("style.world.hazard", "SmoothPlastic"),
    "Ink": ("style.brand.ink", "SmoothPlastic"),
    "Drum": ("style.depot_kit.red_oxide", "Metal"),
    "DrumAlt": ("style.depot_kit.teal_trim", "Metal"),
    "Steel": ("style.thumb.steel", "Metal"),
    "Timber": ("style.depot_kit.timber_light", "Wood"),
    "Soot": ("style.depot_kit.soot", "CorrodedMetal"),
    "Lamp": ("style.depot_kit.window_glow", "Neon"),
}
PRESETS = {
    "crate_single": {"params": {"kind": "crate"}, "note": "one supply crate (the parachute drop)"},
    "crate_stack": {"params": {"kind": "crate", "count": 3, "weathering": 0.5}, "note": "three crates, one on top, one bent"},
    "crate_hazard": {"params": {"kind": "crate", "stripe": True}, "note": "crate with a hazard band"},
    "drum_cluster": {"params": {"kind": "drum", "count": 3, "weathering": 0.6}, "note": "three drums, one tipped over"},
    "barrier_taped": {"params": {"kind": "barrier", "size": 3.6, "weathering": 0.6},
                      "note": "trestle barrier with a striped plank and lamp"},
}
DEFAULT_PRESET = "crate_single"
VIEW = {"ground": "style.lobby.concrete", "features": ["Band", "Post", "Hoop", "Plank", "Lamp", "Stripe"],
        "player": "Seen at walking distance in the Depot Lobby clutter (heaviest near the building), and on the coach "
                  "roof when a supply crate lands; players grab crates, so the silhouette must read at a glance."}
OPTIONS = {"merge": "none", "collide": True, "lod": False}


def build(k, p):
    {"crate": crates, "drum": drums, "barrier": barrier}[p["kind"]](k, p)


def _rot(c, ang, o=(0, 0)):
    """Rotate point c about the vertical axis through o by ang degrees."""
    a = math.radians(ang)
    x, y = c[0] - o[0], c[1] - o[1]
    return (o[0] + x * math.cos(a) - y * math.sin(a), o[1] + x * math.sin(a) + y * math.cos(a), c[2])


def crates(k, p):
    s, n = p["size"], p["count"]
    h = s * 0.9
    g = s * 1.2 + 0.3                    # room for the bent crate to turn without touching
    spots = [(0, 0, 0), (g, 0, 0), (g / 2, 0, h), (0, g, 0)][:n]
    bent = k.rng.randrange(n) if n > 1 else -1
    for i, (x, y, z) in enumerate(spots):
        ang = k.rng.choice((-6, 7)) if i == bent else 0          # one bent thing (style.form.handmade)
        crate(k, p, (x - (g / 2 if n > 1 else 0), y, z), s, h, ang, patch=(i == 0 and p["weathering"] >= 0.4))
    k.measure("crate", f"{s:g} x {s:g} x {h:.2f} studs; {n} in the set")


def crate(k, p, o, s, h, ang, patch):
    ox, oy, oz = o
    P = lambda x, y, z: _rot((ox + x, oy + y, oz + z), ang, (ox, oy))
    R = (0, 0, ang)
    k.box("Core", "CrateDark", P(0, 0, h / 2), (s - 0.3, s - 0.3, h - 0.3), rot=R)
    n, boards, inner = p["planks"], [], s / 2 - 0.15
    bh = (h - 0.3) / n
    for e in (-1, 1):
        for i in range(n):
            z = 0.15 + bh * (i + 0.5)
            boards.append((P(e * (s / 2 - 0.075), 0, z), (0.15, 2 * inner, bh - 0.1), R))
            boards.append((P(0, e * (s / 2 - 0.075), z), (2 * inner, 0.15, bh - 0.1), R))
    for i in range(n):
        boards.append((P(0, -inner + 2 * inner * (i + 0.5) / n, h - 0.075), (2 * inner, 2 * inner / n - 0.1, 0.15), R))
    k.boxes("Boards", "Crate", boards)
    grp = "Iron" if p["bands"] else "CrateDark"
    k.boxes("Post", grp, [(P(ex * (s / 2 - 0.1), ey * (s / 2 - 0.1), h / 2 + 0.05), (0.4, 0.4, h + 0.1), R)
                          for ex in (-1, 1) for ey in (-1, 1)])            # posts stand 0.1 proud of the lid
    if p["bands"]:
        bands = []
        for z in (h * 0.2, h * 0.8):
            for e in (-1, 1):
                bands.append((P(e * (s / 2 + 0.06), 0, z), (0.12, s + 0.24, 0.35), R))
                bands.append((P(0, e * (s / 2 + 0.06), z), (s + 0.24, 0.12, 0.35), R))
        k.boxes("Band", "Iron", bands, detail=1)
    if p["stripe"]:
        st = []
        for e in (-1, 1):
            st.append((P(e * (s / 2 + 0.07), 0, h / 2), (0.14, s + 0.28, 0.6), R))
            st.append((P(0, e * (s / 2 + 0.07), h / 2), (s + 0.28, 0.14, 0.6), R))
        k.boxes("Stripe", "Hazard", st)
    if patch:                                   # a mismatched replacement board
        k.box("PatchBoard", "Timber", P(-(s / 2 + 0.03), s * 0.1, h * 0.55), (0.1, s * 0.45, bh * 0.8), rot=(ang * 0 + 4, 0, ang))
    k.proxy(P(0, 0, h / 2), (s, s, h), rot=R)


def drums(k, p):
    r, h, n = p["drum_r"], p["drum_h"], p["count"]
    spots, tipped = [], p["tipped"] and n >= 3
    upright = n - 1 if tipped else n
    jit = 10.0                                  # angular jitter; spacing is sized so neighbours never touch
    d = 0.0 if upright == 1 else (r + 0.2) / math.sin(math.pi / upright - math.radians(jit))
    for i in range(upright):
        a = math.radians(i * 360 / max(1, upright) + k.rng.uniform(-jit / 2, jit / 2))
        spots.append((d * math.cos(a), d * math.sin(a)))
    sooty = k.rng.randrange(n) if p["weathering"] >= 0.5 else -1
    for i, (x, y) in enumerate(spots):
        body = "Drum" if i % 2 == 0 else "DrumAlt"
        hoop = "Soot" if i == sooty else "Steel"
        k.cyl("Drum", body, (x, y, h / 2), r, h, segs=16)
        for z in (h / 3, 2 * h / 3):
            k.cyl("Hoop", hoop, (x, y, z), r + 0.09, 0.26, segs=16, detail=1)
        k.cyl("Rim", "Steel", (x, y, h - 0.05), r + 0.05, 0.2, segs=16)
        k.cyl("Bung", "Iron", (x + r * 0.5, y, h + 0.12), 0.25, 0.15, segs=8, detail=1)
        k.proxy((x, y, h / 2), (2 * r, 2 * r, h))
    if tipped:
        ext = max((math.hypot(x, y) for x, y in spots), default=0) + r + 0.3
        x, y = 0.0, -(ext + r)
        zc = r + 0.09                          # resting on its hoops
        k.cyl("Drum", "Drum", (x, y, zc), r, h, axis="X", segs=16)
        for dx in (-h / 6, h / 6):
            k.cyl("Hoop", "Soot" if sooty == n - 1 else "Steel", (x + dx, y, zc), r + 0.09, 0.26, axis="X", segs=16)
        k.cyl("Rim", "Steel", (x + h / 2 - 0.05, y, zc), r + 0.05, 0.2, axis="X", segs=16)
        k.proxy((x, y, zc), (h, 2 * r, 2 * r))
    k.measure("drum", f"r {r:g}, h {h:g}; {n} in the cluster" + (", one tipped" if tipped else ""))


def barrier(k, p):
    H, bw, n = p["size"], p["barrier_w"], p["stripes"]
    spread = 0.9
    leg = math.hypot(H, spread)
    ang = math.degrees(math.atan2(spread, H))
    legs = []
    for x in (-(bw / 2 - 0.6), bw / 2 - 0.6):
        for s in (-1, 1):
            legs.append(((x, s * spread / 2, H / 2), (0.3, 0.3, leg), (s * ang, 0, 0)))
    k.boxes("Leg", "Timber", legs)
    seg = {"Hazard": [], "Ink": []}
    for i in range(n):
        x = -bw / 2 + bw * (i + 0.5) / n
        seg["Hazard" if i % 2 == 0 else "Ink"].append(((x, 0, H - 0.3), (bw / n, 0.3, 0.8)))
    for g, items in seg.items():
        k.boxes("Plank", g, items)
    k.box("Rail", "Timber", (0, 0.22, H * 0.45), (bw - 0.2, 0.25, 0.4))
    if p["lamp"]:
        lx = bw / 2 - 0.6
        k.box("LampBase", "Iron", (lx, 0, H + 0.25), (0.5, 0.5, 0.4))
        k.cyl("Lamp", "Lamp", (lx, 0, H + 0.7), 0.35, 0.5, segs=10)
    if p["weathering"] >= 0.5:        # a leg held together with tape
        k.box("TapeWrap", "Ink", (-(bw / 2 - 0.6), -spread / 4, H * 0.3), (0.42, 0.42, 0.5), rot=(-ang, 0, 0), detail=1)
    k.proxy((0, 0, H / 2), (bw, 1.4, H))
    k.measure("barrier", f"{bw:g} long, top {H + (0.95 if p['lamp'] else 0.1):.2f} studs")
