"""T0 break spec: where and how each carriage tears in half, and how the lost part leaves.

Break frame B (per carriage): origin on the carriage centre line, at floor-top height, at the break plane.
  +X across the carriage (east when the rear points to world +Z), +Y up, +Z toward the REAR of the train.
  In Joel's export: C1 origin world (-58.05, 13.927, 86.20); C2 origin world (-58.05, 13.927, 153.60); axes = world.
  Studio finds B from each carriage's roof union (size signature ROOF_SIG): B = roof centre + REAR*BREAK_DZ + UP*FLOOR_DY.
The tear is a stepped (jagged) surface z_break(X, Y) = d(cell) over CELLS that tile the whole cross-section.
Front piece of a crossing part = part minus the REAR cutter; rear piece = part minus the FRONT cutter, where
  FRONT cutter = boxes {cell X, cell Y, Z in [-ZEXT, d]} and REAR cutter = boxes {cell X, cell Y, Z in [d, +ZEXT]}.
Plain axis-aligned Block parts are sliced per cell instead (exact, no CSG).
Run: python3 break_spec.py [--check groups.json]  -> break_spec.json (+ clearance report)
"""
import json, math, os, sys

ROOF_SIG = [19.48, 3.59, 62.34]          # roof union bbox (Union28 / Union134 in the export)
ROOF_CENTRES = {1: [-58.05, 26.185, 82.89], 2: [-58.055, 26.185, 150.29]}
BREAK_DZ = 3.31                          # break plane = roof centre + 3.31 toward the rear (world z 86.20 / 153.60)
FLOOR_DY = -12.258                       # floor top (y 13.927) relative to the roof centre
ZEXT = 40.0                              # cutter reach along Z (carriage spans -34.5 .. +27.9 from the break)
XEXT, YLO, YHI = 14.0, -12.0, 18.0       # cutter reach across / below the bogies / above the roof

Y_FLOOR_TOP, Y_WALL_TOP = 0.4, 10.4      # band limits: floor | walls+mid | roof  (world y 14.33 / 24.33)
X_WALL = 7.5                             # |X| > 7.5 = wall column

cells = []
def cell(x0, x1, y0, y1, d, region):
    cells.append({"X": [x0, x1], "Y": [y0, y1], "d": d, "region": region})

# floor: tears reach back into the lost half (the kept floor sticks out past the walls, like a torn deck)
for (x0, x1), d in zip([(-XEXT, -6.2), (-6.2, -2.8), (-2.8, 0.6), (0.6, 4.1), (4.1, X_WALL), (X_WALL, XEXT)],
                       [0.6, 2.4, 0.9, 3.6, 1.5, -0.3]):
    cell(x0, x1, YLO, Y_FLOOR_TOP, d, "floor")
# walls: stay inside the solid pillar between windows 4 and 5 (clear band +-1.1); W and E tear differently
wall_y = [(Y_FLOOR_TOP, 1.5), (1.5, 3.3), (3.3, 5.7), (5.7, 7.4), (7.4, 9.1), (9.1, Y_WALL_TOP)]
for (y0, y1), dw, de in zip(wall_y, [0.7, -0.4, 0.9, 0.1, -0.8, 0.4], [-0.6, 0.5, -0.2, 0.8, -0.5, 0.2]):
    cell(-XEXT, -X_WALL, y0, y1, dw, "wall_W")
    cell(X_WALL, XEXT, y0, y1, de, "wall_E")
# mid (interior between the walls): curtain pelmet height gets its own teeth
cell(-X_WALL, X_WALL, Y_FLOOR_TOP, 9.1, 0.2, "mid")
for (x0, x1), d in zip([(-X_WALL, -2.5), (-2.5, 2.5), (2.5, X_WALL)], [0.3, -0.5, 0.6]):
    cell(x0, x1, 9.1, Y_WALL_TOP, d, "mid_pelmet")
# roof: rips further forward (the kept half loses a jagged bite of roof)
for (x0, x1), d in zip([(-XEXT, -X_WALL), (-X_WALL, -4.6), (-4.6, -1.9), (-1.9, 0.9), (0.9, 3.8), (3.8, X_WALL), (X_WALL, XEXT)],
                       [0.3, -1.6, -3.9, -2.2, -4.8, -1.1, 0.1]):
    cell(x0, x1, Y_WALL_TOP, YHI, d, "roof")

# ------------------------------------------------------------------ what happens when it snaps
motion = {
    "speed_source": "train attribute 'Speed' (studs/s) if present, else opts.speed, else 35 (gameplay.speed.normal)",
    "speed_default": 35,
    "brake": 12.0,             # studs/s^2: lost part decelerates in the world until it moves with the terrain
    "recoil": {"dist": 0.8, "time": 0.2},   # explosion shove backward at t=0
    "despawn_distance": 700, "despawn_time": 30,
    "note": "train-frame offset z(t) = recoil(t) + 0.5*brake*t^2 until t = V/brake, then + V*(t - V/brake): after that the wreck is static relative to the terrain",
}
topple = {
    "side": "random per snap (seeded), config 'left'|'right' forces it",
    "pivot": {"X_abs": 11.7, "Y": -8.6, "note": "rail level (world y 5.33) at the outer edge of the bogies on the falling side"},
    "bodies": [
        {"who": "the broken half (front-most lost body)", "delay": 0.45, "roll": 88, "roll_time": 1.05, "ease": "QuadIn",
         "bounce": [82, 88], "bounce_time": 0.35, "yaw": 7, "sink": 0.6},
        {"who": "a whole carriage dragged behind it (break 1 only: carriage 2)", "delay": 0.8, "roll": 86, "roll_time": 1.2,
         "ease": "QuadIn", "bounce": [80, 86], "bounce_time": 0.4, "yaw": -4, "sink": 0.5},
    ],
}
events = [  # t = seconds after the snap; anchors in B coords of the breaking carriage
    {"t": -0.25, "id": "metal_tear", "kind": "sound", "at": [0, 5, 0]},
    {"t": 0.0, "id": "split_explosion", "kind": "fx+sound+shake", "at": [0, 5, 0], "shake": "big"},
    {"t": 0.0, "id": "glass_burst", "kind": "fx+sound", "at": "the window panes nearest the break on both sides"},
    {"t": 0.05, "id": "torn_edge_smoke", "kind": "fx loop 20 s", "at": "along the kept half's torn end (and the wreck's)"},
    {"t": 0.8, "id": "debris_rain", "kind": "sound", "at": [0, 3, 2]},
    {"t": "topple impact (delay+roll_time)", "id": "topple_crash", "kind": "fx(topple_dust)+sound+shake", "shake": "medium"},
    {"t": "0.3 .. V/brake", "id": "wreck_scrape", "kind": "sound", "at": "wreck"},
]
lost_rule = {
    "break1": "Carriage1.RearHalf (with the gangway) + all of Carriage2 still attached",
    "break2": "Carriage2.RearHalf",
    "bodies": "each carriage's lost pieces animate as one body; break 1 gives two bodies (C1 rear half, C2)",
}

spec = {"version": "2.0.0", "frame": __doc__.split("\n")[2].strip(), "roof_signature": ROOF_SIG,
        "roof_centres_export": ROOF_CENTRES, "break_dz": BREAK_DZ, "floor_dy": FLOOR_DY, "zext": ZEXT,
        "cells": cells, "motion": motion, "topple": topple, "events": events, "lost": lost_rule,
        "expected_crossers_export": {
            "1": ["Carpet1", "CurtainCorroded1", "Part269", "Union12", "Union16", "Union19", "Union28", "Union38", "Union56", "Union61"],
            "2": ["Carpet2", "CurtainCorroded2", "Part409", "Union109", "Union134", "Union138", "Union77", "Union80", "Union84", "Union86"]},
        "block_parts_export": ["Part269", "Part409"]}


def world_origin(k):
    c = ROOF_CENTRES[k]
    return [c[0], c[1] + FLOOR_DY, c[2] + BREAK_DZ]


def d_at(X, Y):
    for c in cells:
        if c["X"][0] <= X < c["X"][1] and c["Y"][0] <= Y < c["Y"][1]:
            return c["d"]
    raise ValueError((X, Y))


def check(groups_path, margin=0.1):
    """Every non-crossing part must lie wholly on one side of the tear in every cell its bbox touches."""
    G = json.load(open(groups_path)); bad = []; counts = {}
    for k in (1, 2):
        o = world_origin(k)
        cross = set(spec["expected_crossers_export"][str(k)])
        for g in G:
            X0, X1 = g["min"][0] - o[0], g["max"][0] - o[0]
            Y0, Y1 = g["min"][1] - o[1], g["max"][1] - o[1]
            Z0, Z1 = g["min"][2] - o[2], g["max"][2] - o[2]
            if Z1 < -8 or Z0 > 8:
                continue
            touched = [c for c in cells if X1 > c["X"][0] and X0 < c["X"][1] and Y1 > c["Y"][0] and Y0 < c["Y"][1]]
            front = all(Z1 <= c["d"] - margin for c in touched); rear = all(Z0 >= c["d"] + margin for c in touched)
            if g["name"] in cross:
                if front or rear:
                    bad.append((k, g["name"], "listed as crosser but lies on one side"))
                continue
            if not (front or rear):
                bad.append((k, g["name"], [round(v, 2) for v in (Z0, Z1, Y0, Y1, X0, X1)]))
        counts[k] = sum(1 for g in G if abs((g["min"][2] + g["max"][2]) / 2 - o[2]) < 40)
    return bad


out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "break_spec.json")
json.dump(spec, open(out, "w"), indent=1)
print(f"break_spec.json: {len(cells)} cells, origins C1 {world_origin(1)} C2 {world_origin(2)} -> {out}")
if len(sys.argv) > 2 and sys.argv[1] == "--check":
    bad = check(sys.argv[2])
    print("clearance check (margin 0.1 stud):", "PASS" if not bad else f"FAIL {bad}")
