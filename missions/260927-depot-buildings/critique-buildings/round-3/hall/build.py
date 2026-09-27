"""Main Hall (ASSUMPTION A1: not on the blueprint): lobby anchor building, 28x12 studs at plan (16,-14),
north of the join-queue platform, front faces south (Blender -y) toward spawn. Depot style, grander.
Run: python3 build.py [--no-milestones] [--no-renders]. Rebuilds from an empty scene; saves hall.blend."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import kit
from kit import box, prism, cyl, C, gable_roof, window, lamp, moss, stone_face, hazard_nosing, downpipe, ivy

P = "Hall"
X0, X1 = 13.0, 47.0
YF, YB = 2.0, 16.0           # Blender y of front (south in plan) and back faces
EAVE, RIDGE = 16.0, 26.0
T = 1.0
XC, YC = 30.0, (YF + YB) / 2
PW, PD = 12.0, 3.0            # porch width / projection
PY = YF - PD                  # porch front face y
P_RIDGE = 31.0
P_EAVE = 20.0                 # porch walls rise above the main eave: the anchor's focal gable


def cameras():
    c = {}
    c["pov"] = kit.bk.pov_camera("Hall_Cam_POV_3P", stand=(30, -22, 0), look_at=(30, 4, 10), eye_height=9.5)
    c["game"] = kit.cam("Hall_Cam_Game", (72, -40, 30), (30, 6, 9), 40)
    c["34"] = kit.cam("Hall_Cam_34", (-10, -30, 22), (30, 6, 10), 45)
    c["side"] = kit.cam("Hall_Cam_Side", (82, 6, 13), (30, 6, 11), 40)
    c["back"] = kit.cam("Hall_Cam_Back", (50, 52, 20), (30, 8, 10), 45)
    c["door"] = kit.cam("Hall_Cam_Door", (34, -14, 7), (30, PY, 6), 45)
    return c


def shell(col):
    box(f"{P}_Ground_Paving_01", (XC, 5.0, -0.25), (46, 32, 0.5), C["paving"], col)
    for s, (c, sz) in {"S": ((XC, YF - 0.35, 0.75), (X1 - X0 + 0.7, 1.7, 1.5)), "N": ((XC, YB + 0.35, 0.75), (X1 - X0 + 0.7, 1.7, 1.5)),
                       "E": ((X1 + 0.35, YC, 0.75), (1.7, YB - YF - 1, 1.5)), "W": ((X0 - 0.35, YC, 0.75), (1.7, YB - YF - 1, 1.5))}.items():
        box(f"{P}_Plinth{s}_Stonedark_01", c, sz, C["stonedark"], col)
    box(f"{P}_WallS_Stone_01", ((X0 + 26) / 2, YF + T / 2, EAVE / 2), (26 - X0, T, EAVE), C["stone"], col)
    box(f"{P}_WallS_Stone_02", ((34 + X1) / 2, YF + T / 2, EAVE / 2), (X1 - 34, T, EAVE), C["stone"], col)
    box(f"{P}_WallS_Stone_03", (XC, YF + T / 2, 12.5), (8, T, 5), C["stone"], col)
    box(f"{P}_WallN_Stone_01", (XC, YB - T / 2, EAVE / 2), (X1 - X0, T, EAVE), C["stone"], col)
    box(f"{P}_WallE_Stone_01", (X1 - T / 2, YC, EAVE / 2), (T, YB - YF - 2 * T, EAVE), C["stone"], col)
    box(f"{P}_WallW_Stone_01", (X0 + T / 2, YC, EAVE / 2), (T, YB - YF - 2 * T, EAVE), C["stone"], col)
    prof = [(-(YB - YF) / 2, 0), ((YB - YF) / 2, 0), (0, RIDGE - EAVE)]
    prism(f"{P}_GableE_Stone_01", prof, T, (X1 - T / 2, YC, EAVE), C["stone"], col, axis="X")
    prism(f"{P}_GableW_Stone_01", prof, T, (X0 + T / 2, YC, EAVE), C["stone"], col, axis="X")
    # porch: front wall panels around an 8x10 doorway, side walls, gable
    dx0, dx1, dh = 26.0, 34.0, 10.0
    px0, px1 = XC - PW / 2, XC + PW / 2
    box(f"{P}_PorchFront_Stone_01", ((px0 + dx0) / 2, PY + T / 2, P_EAVE / 2), (dx0 - px0, T, P_EAVE), C["stone"], col)
    box(f"{P}_PorchFront_Stone_02", ((dx1 + px1) / 2, PY + T / 2, P_EAVE / 2), (px1 - dx1, T, P_EAVE), C["stone"], col)
    box(f"{P}_PorchFront_Stone_03", (XC, PY + T / 2, (dh + P_EAVE) / 2), (dx1 - dx0, T, P_EAVE - dh), C["stone"], col)
    box(f"{P}_PorchSideW_Stone_01", (px0 + T / 2, (PY + YF) / 2 + 1.5, P_EAVE / 2), (T, PD + 3, P_EAVE), C["stone"], col)
    box(f"{P}_PorchSideE_Stone_01", (px1 - T / 2, (PY + YF) / 2 + 1.5, P_EAVE / 2), (T, PD + 3, P_EAVE), C["stone"], col)
    box(f"{P}_PorchFloor_Stonedark_01", (XC, (PY + YF) / 2 + 0.5, 0.05), (PW - 2 * T, PD + 1, 0.1), C["stonedark"], col)
    box(f"{P}_Interior_Dark_01", (XC, YF + 2.5, dh / 2), (dx1 - dx0, 0.3, dh), C["dark"], col)
    prism(f"{P}_PorchGable_Stone_01", [(-PW / 2, 0), (PW / 2, 0), (0, P_RIDGE - P_EAVE)], T, (XC, PY + T / 2, P_EAVE), C["stone"], col)
    prism(f"{P}_PorchGableBack_Stone_01", [(-PW / 2, 0), (PW / 2, 0), (0, P_RIDGE - P_EAVE)], T, (XC, YF + 3.0 - T / 2, P_EAVE), C["stone"], col)
    box(f"{P}_PorchUpperBack_Stone_01", (XC, YF + 3.0 - T / 2, (EAVE + P_EAVE) / 2), (PW, T, P_EAVE - EAVE + 0.01), C["stone"], col)
    for s, xs in (("L", dx0 - 0.5), ("R", dx1 + 0.5)):
        box(f"{P}_DoorReveal{s}_Stonedark_01", (xs, (PY + YF) / 2 + 0.5, dh / 2), (1.0, PD + 1, dh), C["stonedark"], col)
    n = 0
    for cx, cy in [(X0, YF), (X1, YF), (X0, YB), (X1, YB), (px0, PY), (px1, PY)]:
        sx = 1 if cx in (X0, px0) else -1
        sy = 1 if cy in (YF, PY) else -1
        for k in range(9 if cy == PY else 7):
            n += 1
            size = (2.4, 1.3, 1.8) if k % 2 == 0 else (1.3, 2.4, 1.8)
            box(f"{P}_Quoin_Stonedark_{n:02d}", (cx + sx * (size[0] / 2 - 0.15), cy + sy * (size[1] / 2 - 0.15), 2.5 + k * 1.95),
                size, C["stonedark"], col)
    box(f"{P}_StringCourseS_Mortar_01", (XC, YF - 0.3, EAVE - 0.5), (X1 - X0 + 0.6, 0.8, 0.7), C["mortar"], col)
    box(f"{P}_StringCourseN_Mortar_01", (XC, YB + 0.3, EAVE - 0.5), (X1 - X0 + 0.6, 0.8, 0.7), C["mortar"], col)


def roof(col):
    gable_roof(P, X0, X1, YC, YB - YF, EAVE, RIDGE, col, overhang=1.4, thick=0.9, axis="X", nn=1, gap=(XC - PW / 2 + 0.2, XC + PW / 2 - 0.2))
    # porch roof, ridge along Y, from porch front back into the main roof
    rise, run = P_RIDGE - P_EAVE, PW / 2
    ang = math.degrees(math.atan2(rise, run))
    slope = math.hypot(run + 1.0, rise + rise / run) + 0.4
    L = PD + 3.0 + 1.0
    ym = PY - 1.0 + L / 2
    for s, t in ((1, "A"), (-1, "B")):
        box(f"{P}_PorchRoof{t}_Slate_01", (XC + s * (run + 1.0) / 2, ym, P_EAVE + (rise - rise / run) / 2 + 0.85),
            (slope, L, 0.9), C["slate"], col, rot=(0, s * ang, 0))
    box(f"{P}_PorchRidgeCap_Iron_01", (XC, ym, P_RIDGE + 1.0), (1.3, L, 0.9), C["iron"], col)
    bl = math.hypot(run + 0.8, rise + 0.8 * rise / run)
    for s, t in ((1, "R"), (-1, "L")):
        box(f"{P}_PorchBarge{t}_Timber_01", (XC + s * (run / 2 + 0.2), PY - 0.9, P_EAVE + rise / 2 + 0.5), (bl, 0.5, 1.0),
            C["timber"], col, rot=(0, s * ang, 0))
    box(f"{P}_PorchFinial_Timber_01", (XC, PY - 0.9, P_RIDGE + 1.7), (0.7, 0.7, 2.6), C["timber"], col)
    rise, run = RIDGE - EAVE, (YB - YF) / 2
    ang = math.degrees(math.atan2(rise, run))
    bl = math.hypot(run + 1.4, rise + 1.4 * rise / run)
    for ex, e in ((X1 + 1.5, "E"), (X0 - 1.5, "W")):
        for s, t in ((1, "N"), (-1, "S")):
            box(f"{P}_Barge{e}{t}_Timber_01", (ex, YC + s * (run / 2 + 0.3), EAVE + rise / 2 + 0.6), (0.5, bl, 0.9),
                C["timber"], col, rot=(-s * ang, 0, 0))
    for i, cx in enumerate((17.0, 43.0), 1):
        box(f"{P}_Chimney{i}_Brick_01", (cx, YC + 1.5, RIDGE - 0.5), (2.8, 2.8, 7.5), C["brick"], col)
        box(f"{P}_Chimney{i}Cap_Stonedark_01", (cx, YC + 1.5, RIDGE + 3.4), (3.4, 3.4, 0.6), C["stonedark"], col)
        cyl(f"{P}_Chimney{i}Pot_Soot_01", (cx, YC + 1.5, RIDGE + 4.4), 0.6, 1.6, C["soot"], col)


def details(col):
    for i, x in enumerate((17.2, 21.4, 38.6, 42.8), 1):
        window(P, i, x, YF, 3.0, 2.8, 8.5, col, facing=-1, arch=True)
    for i, x in enumerate((18.0, 26.0, 34.0, 42.0), 11):
        window(P, i, x, YB, 4.0, 3.4, 7.0, col, facing=1)
    window(P, 6, YC, X1, 3.5, 3.4, 8.0, col, facing=1, axis="Y", arch=True)
    window(P, 7, YC, X0, 3.5, 3.4, 8.0, col, facing=-1, axis="Y", arch=True)
    # roundel placeholder in the porch gable (blank clock face, no text)
    cyl(f"{P}_RoundelRim_Brass_01", (XC, PY - 0.2, P_EAVE + 3.6), 2.8, 0.4, C["brass"], col, segs=16, axis="Y")
    cyl(f"{P}_RoundelFace_Mortar_01", (XC, PY - 0.45, P_EAVE + 3.6), 2.3, 0.2, C["mortar"], col, segs=16, axis="Y")
    # door frame + open leaves + arch keystone
    box(f"{P}_DoorFrameL_Timber_01", (25.7, PY - 0.2, 5.0), (0.7, 0.6, 10.0), C["timber"], col)
    box(f"{P}_DoorFrameR_Timber_01", (34.3, PY - 0.2, 5.0), (0.7, 0.6, 10.0), C["timber"], col)
    prism(f"{P}_DoorArch_Stonedark_01", [(-5.2, 0), (5.2, 0), (5.2, 1.0), (0, 2.6), (-5.2, 1.0)], 0.8, (XC, PY - 0.2, 10.0), C["stonedark"], col)
    box(f"{P}_Keystone_Mortar_01", (XC, PY - 0.7, 12.0), (1.2, 0.6, 1.6), C["mortar"], col)
    box(f"{P}_DoorLeafL_Door_01", (26.6, PY + 2.0, 4.6), (0.3, 3.2, 9.0), C["door"], col, rot=(0, 0, 20))
    box(f"{P}_DoorLeafR_Door_01", (33.4, PY + 2.0, 4.6), (0.3, 3.2, 9.0), C["door"], col, rot=(0, 0, -20))
    for k in range(3):
        box(f"{P}_Step_Stonedark_{k + 1:02d}", (XC, PY - 0.6 - k * 1.2, 0.1 * (3 - k)),
            (12.0 + k * 2.0, 1.2 + k * 1.2, 0.2 * (3 - k)), C["stonedark"], col)
    box(f"{P}_GutterS_Iron_01", (XC, YF - 1.1, EAVE - 0.9), (X1 - X0 + 2.4, 0.8, 0.6), C["iron"], col)
    box(f"{P}_GutterN_Iron_01", (XC, YB + 1.1, EAVE - 0.9), (X1 - X0 + 2.4, 0.8, 0.6), C["iron"], col)
    downpipe(P, 1, X0 - 0.3, YF + 2.6, YF - 1.1, EAVE - 0.6, col)
    downpipe(P, 2, X1 + 0.3, YF + 2.6, YF - 1.1, EAVE - 0.6, col)
    downpipe(P, 3, X0 - 0.3, YB - 2.6, YB + 1.1, EAVE - 0.6, col)
    downpipe(P, 4, X1 + 0.3, YB - 2.6, YB + 1.1, EAVE - 0.6, col)
    wins_f = [(x - 2.2, x + 2.2, 2.5, 13.5) for x in (17.2, 21.4, 38.6, 42.8)]
    stone_face(P, "SW", X0 + 2.5, 24.0, 1.6, EAVE - 1.2, YF, -1, col, avoid=wins_f, seed=21)
    stone_face(P, "SE", 36.0, X1 - 2.5, 1.6, EAVE - 1.2, YF, -1, col, avoid=wins_f, seed=22)
    stone_face(P, "Porch", 24.0 + 2.5, 36.0 - 2.5, 11.0, P_EAVE - 0.4, PY, -1, col, avoid=[(26, 34, 0, 13.0)], seed=23)
    stone_face(P, "N", X0 + 2.5, X1 - 2.5, 1.6, EAVE - 1.2, YB, 1, col,
               avoid=[(x - 2.2, x + 2.2, 3.5, 11.5) for x in (18.0, 26.0, 34.0, 42.0)], seed=24)
    stone_face(P, "E", YF + 2.5, YB - 2.5, 1.6, EAVE - 0.4, X1, 1, col, axis="Y", avoid=[(YC - 2.2, YC + 2.2, 3.0, 13.0)], seed=25)
    stone_face(P, "W", YF + 2.5, YB - 2.5, 1.6, EAVE - 0.4, X0, -1, col, axis="Y", avoid=[(YC - 2.2, YC + 2.2, 3.0, 13.0)], seed=26)
    for e, xp, f in (("E", X1, 1), ("W", X0, -1)):
        stone_face(P, f"Gable{e}", YF + 1.0, YB - 1.0, EAVE + 0.2, RIDGE, xp, f, col, axis="Y",
                   seed=40 + f, tri=(YC, EAVE, RIDGE, (YB - YF) / 2))
    stone_face(P, "PorchGable", XC - PW / 2 + 1, XC + PW / 2 - 1, P_EAVE + 0.2, P_RIDGE, PY, -1, col, seed=45,
               avoid=[(XC - 3.2, XC + 3.2, P_EAVE + 0.4, P_EAVE + 6.8)], tri=(XC, P_EAVE, P_RIDGE, PW / 2))
    for k in range(3):
        hazard_nosing(P, k + 1, XC - (6.0 + k), XC + (6.0 + k), PY - 0.6 - k * 1.2 - (0.6 + k * 0.6) + 0.2, 0.2 * (3 - k) + 0.02, col, h=0.12, depth=0.5)
    # cupola on the main ridge behind the porch: the lobby anchor's skyline marker
    box(f"{P}_CupolaBase_Timberlt_01", (XC, YC + 2.5, RIDGE + 1.6), (3.6, 3.6, 3.2), C["timberlt"], col)
    for s2, t in ((1, "E"), (-1, "W")):
        box(f"{P}_CupolaLouvre{t}_Dark_01", (XC + s2 * 1.85, YC + 2.5, RIDGE + 1.8), (0.1, 2.0, 2.0), C["dark"], col)
    prism(f"{P}_CupolaRoof_Slate_01", [(-2.4, 0), (2.4, 0), (0, 2.6)], 4.8, (XC, YC + 2.5, RIDGE + 3.2), C["slate"], col, axis="X")
    box(f"{P}_CupolaFinial_Brass_01", (XC, YC + 2.5, RIDGE + 6.6), (0.5, 0.5, 2.2), C["brass"], col)
    box(f"{P}_CupolaVane_Brass_01", (XC, YC + 2.5, RIDGE + 7.4), (2.6, 0.2, 0.6), C["brass"], col)
    box(f"{P}_SootN_Soot_01", (19.5, YB + 0.05, 10.0), (1.8, 0.1, 6.0), C["soot"], col)


def dressing(col, stage):
    mz = [(17.5, YF - 1.4, 1.5, 3.0, 1.2, 1.0), (42.5, YF - 1.4, 1.5, 3.0, 1.2, 1.1), (X0 - 1.0, 9, 0, 1.4, 5.0, 1.5),
          (X1 + 1.0, 11, 0, 1.4, 4.0, 1.3), (33, YB + 1.0, 0, 6.0, 1.4, 1.0), (22.5, PY - 0.5, 0, 2.0, 1.2, 0.5),
          (37.5, PY - 0.5, 0, 2.0, 1.2, 0.5)]
    for i, m in enumerate(mz, 1):
        moss(P, i, *m, col)
    ivy(P, 1, YF + 3.2, X1, 1, 1.5, 12.0, col, seed=9)
    lamp(P, 1, 21.5, -5.0, 0, col, h=11)
    lamp(P, 2, 38.5, -5.0, 0, col, h=11)
    kit.avatar("Stage_AvatarHall1", (30.0, -8.0, 0), stage)
    kit.avatar("Stage_AvatarHall2", (28.5, YF - 0.6, 0.1), stage)


def build(milestones=True):
    kit.reset()
    col, stage = kit.coll("Hall"), kit.coll("Stage")
    cams = cameras()
    ms = [("pov", cams["pov"]), ("34", cams["34"])]
    for k, (name, fn) in enumerate([("shell", shell), ("roof", roof), ("details", details),
                                    ("dressing", lambda c: dressing(c, stage))], 1):
        fn(col)
        if milestones:
            kit.milestone("hall", k, name, ms)
    return cams


if __name__ == "__main__":
    import bpy
    here = os.path.dirname(os.path.abspath(__file__))
    cams = build(milestones="--no-milestones" not in sys.argv)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(here, "hall.blend"))
    if "--no-renders" not in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(here, "renders")
        os.makedirs(out, exist_ok=True)
        kit.bk.render(cams["pov"], os.path.join(out, "hall_pov3p.png"), res=(768, 432))
        kit.bk.render(cams["game"], os.path.join(out, "hall_game.png"), res=(400, 225))
        for k in ("34", "side", "back", "door"):
            kit.bk.render(cams[k], os.path.join(out, f"hall_{k}.png"), res=(1280, 720))
