"""Shared rolling-stock parts for the carriage and wagon families (not a family: no PARAMS).
Frame: x along the vehicle, y across, z up; z = 0 is the rail top, so wheels stand on z = 0.
Parts meet by overlapping a little, never by sharing a face plane (coplanar faces render black and z-fight)."""


BOGIE_WB = 5.0


def bogie_inset(p, L):
    return max(4.5, L * p.get("bogie_inset", 0.18))


def bogies_fit(p, L):
    """Inner wheels of the two bogies must clear each other by 0.6."""
    return L >= 2 * bogie_inset(p, L) + BOGIE_WB + 2 * p["wheel_r"] + 0.6


def wheel_clash(p, floor, deck_t=0.6):
    """Refusal text when the wheels would reach the deck (top of wheel + 0.4 clearance above the deck underside)."""
    if 2 * p["wheel_r"] + 0.4 > floor - deck_t:
        return f"ERROR: wheel_r {p['wheel_r']:g} reaches the deck at floor {floor:g}: lower wheel_r or raise the floor"
    return None


def bogie_mode(p, L):
    want = p["running"] == "bogies" or (p["running"] == "auto" and L >= 40)
    return want and bogies_fit(p, L)


def underframe(k, p, L, W, top, groups=("Chassis", "Steel", "Buffer", "Iron")):
    """Everything under a deck whose underside is at z = top: solebars, buffer beams, buffers, coupling,
    and either two axles or two bogies. p needs gauge, wheel_r, running."""
    frame, steel, beam, iron = groups
    g, rw = p["gauge"], p["wheel_r"]
    bog = bogie_mode(p, L)
    # solebars along the sides, top hidden inside the deck
    for s in (-1, 1):
        k.box("Solebar", frame, (0, s * (W / 2 - 0.45), top - 0.55), (L - 1.0, 0.6, 1.2))
    # buffer beams proud of the deck end, buffers and couplings
    bz = top - 0.7
    for e in (-1, 1):
        k.box("BufferBeam", beam, (e * (L / 2 - 0.25), 0, bz), (0.7, W - 0.6, 1.4))
        for s in (-1, 1):
            y = s * (W / 2 - 2.4)
            k.cyl("BufferStock", frame, (e * (L / 2 + 0.6), y, bz), 0.5, 1.0, axis="X", segs=10)
            k.cyl("BufferHead", steel, (e * (L / 2 + 1.25), y, bz), 0.85, 0.3, axis="X", segs=14)
        k.box("Coupling", iron, (e * (L / 2 + 0.55), 0, bz - 0.1), (1.1, 0.5, 0.6), detail=1)
    if p["running"] == "bogies" and not bog:
        k.measure("running gear", f"bogies do not fit at length {L:g} with wheel_r {p['wheel_r']:g}: two axles used")
    if bog:
        inset = bogie_inset(p, L)
        for e in (-1, 1):
            bogie(k, p, e * (L / 2 - inset), top, frame, steel)
    else:
        wb = min(max(0.55 * L, 8.0), L - 9.0)
        for x in (-wb / 2, wb / 2):
            wheelset(k, p, x, steel)
            for s in (-1, 1):
                y = s * (g / 2 + 0.8)
                k.box("Axlebox", frame, (x, y, rw + 0.2), (1.2, 1.0, 1.4))
                k.box("Spring", frame, (x, y, rw + 0.62), (3.2, 0.5, 0.35), detail=1)
        for s in (-1, 1):   # running beams the axleboxes hang from
            k.box("RunBeam", frame, (0, s * (g / 2 + 0.8), (rw + 0.7 + top + 0.05) / 2), (L - 1.0, 0.8, top + 0.05 - rw - 0.7))
    return bog


def wheelset(k, p, x, steel):
    g, rw = p["gauge"], p["wheel_r"]
    k.cyl("Axle", steel, (x, 0, rw), 0.3, g + 1.6, axis="Y", segs=8)
    for s in (-1, 1):
        k.cyl("Wheel", steel, (x, s * g / 2, rw), rw, 0.6, axis="Y", segs=16)


def bogie(k, p, xb, top, frame, steel, wb=BOGIE_WB):
    g, rw = p["gauge"], p["wheel_r"]
    for x in (xb - wb / 2, xb + wb / 2):
        wheelset(k, p, x, steel)
    for s in (-1, 1):
        y = s * (g / 2 + 0.8)
        k.box("BogieSide", frame, (xb, y, rw), (wb + 2.6, 0.7, 1.1))
        for x in (xb - wb / 2, xb + wb / 2):
            k.box("Axlebox", frame, (x, s * (g / 2 + 1.3), rw), (1.0, 0.36, 0.9), detail=1)
    k.box("Bolster", frame, (xb, 0, rw + 0.75), (1.4, g + 2.0, 0.7))
    k.box("Pivot", frame, (xb, 0, (rw + 1.0 + top + 0.05) / 2), (1.8, 1.8, top + 0.05 - rw - 1.0))


def pov_next_vehicle(p, lo, hi, floor):
    """Players ride the train: the usual view of a vehicle is from the next one's end platform."""
    return (hi[0] + 8.0, 0.3 * lo[1], floor), ((lo[0] + hi[0]) / 2 - 0.15 * (hi[0] - lo[0]), lo[1], floor + 3.0)


def ladder(k, x, y, z0, z1, group="Iron", along="X", width=1.6, pitch=1.0):
    """Vertical ladder: two stiles and a rung set (the rungs part stays collidable, see RUNG_RULE)."""
    half = width / 2
    for s in (-1, 1):
        c = (x + s * half, y, (z0 + z1) / 2) if along == "X" else (x, y + s * half, (z0 + z1) / 2)
        k.box("LadderStile", group, c, (0.3, 0.3, z1 - z0))
    rungs, z = [], z0 + pitch
    while z < z1 - 0.3:
        rungs.append(((x, y, z), (width, 0.22, 0.22) if along == "X" else (0.22, width, 0.22)))
        z += pitch
    k.boxes("LadderRung", group, rungs)


# rungs keep collision so the ladder can be climbed (Studio climb test pending)
RUNG_RULE = ("_LadderRung_", {"CanCollide": True,
                              "CollisionFidelity": "Enum.CollisionFidelity.PreciseConvexDecomposition"})
