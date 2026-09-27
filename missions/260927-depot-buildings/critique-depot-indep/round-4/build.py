"""Depot station house (Depot Lobby blueprint zone 7): 24x14 studs at plan (18,76), two gables facing north.
Run: python3 build.py [--no-milestones] [--no-renders]. Rebuilds from an empty scene; saves depot.blend."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import kit
from kit import box, prism, cyl, C, gable_roof, window, lamp, crate, drum, moss, stone_face, hazard_nosing, downpipe, ivy

P = "Depot"
X0, X1 = 18.0, 42.0          # plan x
YF, YB = -76.0, -90.0        # Blender y of north (front) and south (back) faces
EAVE, RIDGE = 14.0, 22.0
T = 1.0                      # wall thickness
XC, YC = 30.0, (YF + YB) / 2
GABLES = (21.5, 38.5)        # cross-gable centres on the front (r1: narrowed + moved out so the doorway is fully visible, A2-1/A5-1)
GW, G_RIDGE = 6.0, 20.5


def cameras():
    c = {}
    c["pov"] = kit.bk.pov_camera("Depot_Cam_POV_3P", stand=(30, -58, 0), look_at=(30, -80, 9), eye_height=9.5)
    c["game"] = kit.cam("Depot_Cam_Game", (70, -38, 30), (30, -83, 8), 40)
    c["34"] = kit.cam("Depot_Cam_34", (-6, -48, 22), (30, -83, 9), 45)
    c["side"] = kit.cam("Depot_Cam_Side", (78, -83, 12), (30, -83, 10), 40)
    c["back"] = kit.cam("Depot_Cam_Back", (48, -128, 18), (30, -83, 9), 45)
    c["door"] = kit.cam("Depot_Cam_Door", (34, -62, 7), (30, -76, 5), 45)
    return c


def shell(col):
    box(f"{P}_Ground_Pavingdk_01", (XC, YC + 6, -0.25), (40, 34, 0.5), C["pavingdk"], col)   # r2 A4-1: darker slab cell (wall/slab luma gap)
    box(f"{P}_Ballast_Gravel_01", (XC, -73.0, 0.1), (32, 4, 0.2), C["gravel"], col)  # yard edge toward display track
    # plinth (4 sides, separate)
    box(f"{P}_PlinthN_Stonedark_01", (XC, YF + 0.35, 0.75), (X1 - X0 + 0.7, 1.7, 1.5), C["stonedark"], col)
    box(f"{P}_PlinthS_Stonedark_01", (XC, YB - 0.35, 0.75), (X1 - X0 + 0.7, 1.7, 1.5), C["stonedark"], col)
    box(f"{P}_PlinthE_Stonedark_01", (X1 + 0.35, YC, 0.75), (1.7, YF - YB - 1.0, 1.5), C["stonedark"], col)
    box(f"{P}_PlinthW_Stonedark_01", (X0 - 0.35, YC, 0.75), (1.7, YF - YB - 1.0, 1.5), C["stonedark"], col)
    # front wall in panels around the central doorway (x 26..34, 10 tall)
    dx0, dx1, dh = 25.5, 34.5, 10.0
    box(f"{P}_WallN_Stone_01", ((X0 + dx0) / 2, YF - T / 2, EAVE / 2), (dx0 - X0, T, EAVE), C["stone"], col)
    box(f"{P}_WallN_Stone_02", ((dx1 + X1) / 2, YF - T / 2, EAVE / 2), (X1 - dx1, T, EAVE), C["stone"], col)
    box(f"{P}_WallN_Stone_03", (XC, YF - T / 2, (dh + EAVE) / 2), (dx1 - dx0, T, EAVE - dh), C["stone"], col)
    box(f"{P}_WallS_Stone_01", (XC, YB + T / 2, EAVE / 2), (X1 - X0, T, EAVE), C["stone"], col)
    box(f"{P}_WallE_Stone_01", (X1 - T / 2, YC, EAVE / 2), (T, YF - YB - 2 * T, EAVE), C["stone"], col)
    box(f"{P}_WallW_Stone_01", (X0 + T / 2, YC, EAVE / 2), (T, YF - YB - 2 * T, EAVE), C["stone"], col)
    box(f"{P}_Interior_Dark_01", (XC, YF - 2.2, dh / 2), (dx1 - dx0, 0.3, dh), C["dark"], col)
    for s, xs in (("L", dx0 - 0.5), ("R", dx1 + 0.5)):
        box(f"{P}_DoorReveal{s}_Stonedark_01", (xs, YF - 1.2, dh / 2), (1.0, 2.2, dh), C["stonedark"], col)
    box(f"{P}_DoorFloor_Stonedark_01", (XC, YF - 1.2, 0.05), (dx1 - dx0, 2.2, 0.1), C["stonedark"], col)
    # gable walls (end triangles) E/W
    prof = [(-(YF - YB) / 2, 0), ((YF - YB) / 2, 0), (0, RIDGE - EAVE)]
    prism(f"{P}_GableE_Stone_01", prof, T, (X1 - T / 2, YC, EAVE), C["stone"], col, axis="X")
    prism(f"{P}_GableW_Stone_01", prof, T, (X0 + T / 2, YC, EAVE), C["stone"], col, axis="X")
    # front cross-gable bays: projecting 1.5 stud, gable triangle above eave
    for i, gx in enumerate(GABLES, 1):
        box(f"{P}_Bay{i}_Stone_01", (gx, YF + 0.75, EAVE / 2), (GW, 1.5, EAVE), C["stone"], col)
        prism(f"{P}_Bay{i}Gable_Stone_01", [(-GW / 2, 0), (GW / 2, 0), (0, G_RIDGE - EAVE)], 1.5,
              (gx, YF + 0.75, EAVE), C["stone"], col)
    # quoins: alternating long/short blocks at 4 main corners + bay corners
    n = 0
    corners = [(X0, YF), (X1, YF), (X0, YB), (X1, YB)]
    for cx, cy in corners:
        sx = 1 if cx == X0 else -1
        sy = -1 if cy == YF else 1
        for k in range(6):
            z = 1.5 + k * 2.1 + 1.0
            n += 1
            long_x = k % 2 == 0
            size = (2.4, 1.3, 1.9) if long_x else (1.3, 2.4, 1.9)
            off = (sx * (size[0] / 2 - 0.15), sy * (size[1] / 2 - 0.15))
            box(f"{P}_Quoin_Stonedark_{n:02d}", (cx + off[0], cy + off[1], z), size, C["stonedark"], col)
    for i, gx in enumerate(GABLES, 1):
        for sx in (-1, 1):
            for k in range(6):
                n += 1
                z = 1.5 + k * 2.1 + 1.0
                w = 1.6 if k % 2 == 0 else 1.1
                box(f"{P}_Quoin_Stonedark_{n:02d}", (gx + sx * (GW / 2 - w / 2 + 0.15), YF + 1.55, z), (w, 0.3, 1.9), C["stonedark"], col)
    # string course under eaves
    box(f"{P}_StringCourseS_Mortar_01", (XC, YB - 0.3, EAVE - 0.5), (X1 - X0 + 0.6, 0.8, 0.7), C["mortar"], col)


def roof(col):
    gable_roof(P, X0, X1, YC, YF - YB, EAVE, RIDGE, col, overhang=1.4, thick=0.9, axis="X", nn=1, rcell="slatedk")
    for i, gx in enumerate(GABLES, 1):
        # cross-gable roof: ridge along Y from bay front back into the main roof
        yc_front = YF + 1.5
        L = 5.5
        rise, run = G_RIDGE - EAVE, GW / 2
        ang = math.degrees(math.atan2(rise, run))
        slope = math.hypot(run + 1.0, rise + rise / run) + 0.4
        for s, t in ((1, "A"), (-1, "B")):
            cx = gx + s * (run + 1.0) / 2
            cz = EAVE + (rise - rise / run) / 2 + 0.45 + 0.4
            box(f"{P}_Bay{i}Roof{t}_Slatedk_01", (cx, yc_front - L / 2 + 0.6, cz), (slope, L, 0.8), C["slatedk"], col, rot=(0, s * ang, 0))
        box(f"{P}_Bay{i}RidgeCap_Iron_01", (gx, yc_front - L / 2 + 0.6, G_RIDGE + 0.95), (1.2, L, 0.8), C["iron"], col)
        # bargeboards (timber) following the gable edges + finial
        for s, t in ((1, "R"), (-1, "L")):
            bl = math.hypot(run + 0.8, rise + 0.8 * rise / run)
            box(f"{P}_Bay{i}Barge{t}_Ink_01", (gx + s * (run / 2 + 0.2), yc_front + 0.9, EAVE + rise / 2 + 0.5),
                (bl, 0.5, 0.9), C["ink"], col, rot=(0, s * ang, 0))
        box(f"{P}_Bay{i}Finial_Teal_01", (gx, yc_front + 0.9, G_RIDGE + 1.6), (0.6, 0.6, 2.2), C["teal"], col)
    # end-gable bargeboards
    rise, run = RIDGE - EAVE, (YF - YB) / 2
    ang = math.degrees(math.atan2(rise, run))
    bl = math.hypot(run + 1.4, rise + 1.4 * rise / run)
    for ex, e in ((X1 + 1.5, "E"), (X0 - 1.5, "W")):
        for s, t in ((1, "N"), (-1, "S")):
            box(f"{P}_Barge{e}{t}_Ink_01", (ex, YC + s * (run / 2 + 0.3), EAVE + rise / 2 + 0.6), (0.5, bl, 0.9),
                C["ink"], col, rot=(-s * ang, 0, 0))
    # chimneys on the ridge line
    for i, cx in enumerate((22.5, 37.5), 1):
        box(f"{P}_Chimney{i}_Brick_01", (cx, YC - 1.5, RIDGE - 0.5), (2.6, 2.6, 7.0), C["brick"], col)
        box(f"{P}_Chimney{i}Cap_Stonedark_01", (cx, YC - 1.5, RIDGE + 3.2), (3.2, 3.2, 0.6), C["stonedark"], col)
        cyl(f"{P}_Chimney{i}Pot_Soot_01", (cx, YC - 1.5, RIDGE + 4.2), 0.6, 1.6, C["soot"], col)
        box(f"{P}_Chimney{i}SootBand_Soot_01", (cx, YC - 1.5, RIDGE + 2.2), (2.75, 2.75, 1.4), C["soot"], col)  # r1 A4-1
    # r1 A1-1: bell cote on the ridge over the doorway = one dominant central peak (apex ~30.3 > chimney pots 27)
    bz = RIDGE + 0.5
    box(f"{P}_BellCoteBase_Stonedark_01", (XC, YC, bz - 0.1), (3.2, 3.2, 4.8), C["stonedark"], col)
    for k, (ox, oy) in enumerate(((-1.2, -1.2), (1.2, -1.2), (-1.2, 1.2), (1.2, 1.2)), 1):
        box(f"{P}_BellCotePost_Teal_{k:02d}", (XC + ox, YC + oy, bz + 3.6), (0.5, 0.5, 2.6), C["teal"], col)
    cyl(f"{P}_BellCoteBell_Brass_01", (XC, YC, bz + 3.4), 0.8, 1.4, C["brass"], col, segs=8, r2=0.45)
    box(f"{P}_BellCoteLintel_Cream_01", (XC, YC, bz + 5.1), (3.4, 3.4, 0.5), C["cream"], col)
    prism(f"{P}_BellCoteCap_Slatedk_01", [(-2.1, 0), (2.1, 0), (0, 2.4)], 3.8, (XC, YC, bz + 5.35), C["slatedk"], col)
    box(f"{P}_BellCoteFinial_Teal_01", (XC, YC, bz + 8.2), (0.4, 0.4, 1.2), C["teal"], col)
    # r1 A1-1: rear dormer breaks the south roof run (ridge along y, window facing -y)
    box(f"{P}_DormerS_Stone_01", (XC, -87.4, 17.1), (4.4, 4.0, 4.6), C["stone"], col)
    prism(f"{P}_DormerSRoof_Slatedk_01", [(-2.9, 0), (2.9, 0), (0, 2.4)], 4.4, (XC, -87.6, 19.4), C["slatedk"], col)
    for s, t in ((1, "R"), (-1, "L")):
        box(f"{P}_DormerSBarge{t}_Ink_01", (XC + s * 1.45, -89.9, 20.6), (3.4, 0.4, 0.6), C["ink"], col, rot=(0, s * math.degrees(math.atan2(2.4, 2.9)), 0))


def details(col):
    # bay windows (tall, arched heads) and flank windows
    TL = dict(frame="Teal", sill="Cream")   # r1 A6-1: teal-cream house livery on all window joinery
    window(P, 1, GABLES[0], YF + 1.5, 3.0, 3.4, 7.0, col, facing=1, arch=True, **TL)
    window(P, 2, GABLES[1], YF + 1.5, 3.0, 3.4, 7.0, col, facing=1, arch=True, **TL)
    window(P, 4, 23.0, YB, 4.0, 3.5, 6.0, col, facing=-1, **TL)
    window(P, 5, 37.0, YB, 6.5, 2.0, 2.5, col, facing=-1, **TL)        # r1 A7-1: small lavatory window
    window(P, 6, YC, X1, 4.0, 3.5, 6.0, col, facing=1, axis="Y", **TL)
    window(P, 7, YC, X0, 4.0, 3.5, 6.0, col, facing=-1, axis="Y", **TL)
    window(P, 8, XC, -89.4, 16.0, 2.2, 2.2, col, facing=-1, **TL)       # r1 A1-1: dormer window
    # r1 A7-1: rear goods door (teal leaf, cream frame, stone step) replaces the middle of three identical windows
    box(f"{P}_RearDoorLeaf_Teal_01", (XC, YB - 0.2, 5.25), (3.6, 0.4, 7.5), C["teal"], col)
    for k, dxx in enumerate((-0.9, 0.9), 1):
        box(f"{P}_RearDoorPlank_Timber_{k:02d}", (XC + dxx, YB - 0.45, 5.25), (0.25, 0.1, 7.5), C["timber"], col)
    for s, t in ((-1, "L"), (1, "R")):
        box(f"{P}_RearDoorFrame{t}_Cream_01", (XC + s * 2.1, YB - 0.3, 5.4), (0.6, 0.6, 7.8), C["cream"], col)
    box(f"{P}_RearDoorFrameT_Cream_01", (XC, YB - 0.3, 9.6), (4.8, 0.6, 0.6), C["cream"], col)
    box(f"{P}_RearStep_Stonedark_01", (XC, YB - 2.0, 0.4), (5.0, 1.6, 0.8), C["stonedark"], col)
    # gable round vents
    for i, gx in enumerate(GABLES, 1):
        cyl(f"{P}_Bay{i}Vent_Dark_01", (gx, YF + 1.6, EAVE + 2.4), 0.9, 0.3, C["dark"], col, segs=10, axis="Y")
        cyl(f"{P}_Bay{i}VentRing_Stonedark_01", (gx, YF + 1.5, EAVE + 2.4), 1.3, 0.3, C["stonedark"], col, segs=10, axis="Y")
    # doorway: timber frame, two open leaves (red oxide), stone step, canopy on iron brackets
    # r1 A2-1/A5-1: clear opening 25.9..34.1 = 8.2 studs, teal jambs, 1-stud cream surround, 1-stud-deep hazard step
    box(f"{P}_DoorFrameL_Teal_01", (25.6, YF + 0.2, 5.0), (0.6, 0.6, 10.0), C["teal"], col)
    box(f"{P}_DoorFrameR_Teal_01", (34.4, YF + 0.2, 5.0), (0.6, 0.6, 10.0), C["teal"], col)
    box(f"{P}_DoorFrameT_Teal_01", (30.0, YF + 0.2, 10.3), (9.4, 0.6, 0.6), C["teal"], col)
    for s, t in ((-1, "L"), (1, "R")):
        box(f"{P}_DoorSurround{t}_Cream_01", (30 + s * 5.0, YF + 0.4, 5.6), (1.0, 0.8, 11.2), C["cream"], col)
    box(f"{P}_DoorSurroundT_Cream_01", (30.0, YF + 0.4, 10.7), (9.0, 0.8, 1.0), C["cream"], col)
    box(f"{P}_DoorLeafL_Teal_01", (26.4, YF - 2.0, 4.6), (0.3, 3.4, 9.0), C["teal"], col, rot=(0, 0, -20))
    box(f"{P}_DoorLeafR_Teal_01", (33.6, YF - 2.0, 4.6), (0.3, 3.4, 9.0), C["teal"], col, rot=(0, 0, 20))
    box(f"{P}_Step_Stonedark_01", (30.0, YF + 1.0, 0.3), (11.0, 2.0, 0.6), C["stonedark"], col)
    hazard_nosing(P, 1, 24.5, 35.5, YF + 2.75, 0.75, col, w=1.1, depth=1.5, h=1.5)   # r2 A5-1: hazard step 11x1.5x1.5 (>=5px at 400px)
    CZ = 12.4   # canopy raised 1 stud
    box(f"{P}_Canopy_Slatedk_01", (30.0, YF + 2.6, CZ), (11.0, 5.4, 0.6), C["slatedk"], col, rot=(-14, 0, 0))
    box(f"{P}_CanopyFascia_Teal_01", (30.0, YF + 5.2, CZ - 0.9), (11.0, 0.4, 1.0), C["teal"], col)
    box(f"{P}_CanopyValance_Hazard_01", (30.0, YF + 5.3, CZ - 1.6), (11.0, 0.3, 0.4), C["hazard"], col)
    for s, t in ((-1, "L"), (1, "R")):
        box(f"{P}_CanopyBracket{t}_Iron_01", (30 + s * 5.0, YF + 2.6, CZ - 1.0), (0.4, 5.0, 0.4), C["iron"], col)
        box(f"{P}_CanopyStrut{t}_Iron_01", (30 + s * 5.0, YF + 1.8, CZ - 2.1), (0.3, 0.3, 3.4), C["iron"], col, rot=(-40, 0, 0))
    # blank name board (placeholder, no invented text): cream on a teal frame, 2 studs tall, bottom 2.2 studs above the door head
    box(f"{P}_NameBoard_Cream_01", (30.0, YF + 5.05, 13.9), (7.6, 0.35, 2.8), C["cream"], col)
    box(f"{P}_NameBoardFrame_Teal_01", (30.0, YF + 4.85, 13.9), (8.4, 0.3, 3.4), C["teal"], col)   # r2 A5-1: board 2.8 tall
    # gutters + downpipes (iron)
    box(f"{P}_GutterN_Iron_01", (XC, YF + 1.1, EAVE - 0.9), (X1 - X0 + 2.4, 0.8, 0.6), C["iron"], col)
    box(f"{P}_GutterS_Iron_01", (XC, YB - 1.1, EAVE - 0.9), (X1 - X0 + 2.4, 0.8, 0.6), C["iron"], col)
    downpipe(P, 1, X0 - 0.3, YF - 2.6, YF + 1.1, EAVE - 0.6, col)
    downpipe(P, 2, X1 + 0.3, YF - 2.6, YF + 1.1, EAVE - 0.6, col)
    downpipe(P, 3, X0 - 0.3, YB + 2.6, YB - 1.1, EAVE - 0.6, col)
    downpipe(P, 4, X1 + 0.3, YB + 2.6, YB - 1.1, EAVE - 0.6, col)
    downpipe(P, 5, 34.0, YB - 0.45, YB - 1.1, EAVE - 0.6, col)   # r1 A7-1: vertical break mid back wall
    # ashlar coursing so the walls read as stone (proud blocks, palette cells)
    for i, gx in enumerate(GABLES, 1):
        stone_face(P, f"Bay{i}", gx - GW / 2 + 0.2, gx + GW / 2 - 0.2, 1.6, EAVE - 0.4, YF + 1.5, 1, col,
                   avoid=[(gx - 2.2, gx + 2.2, 3.0, 12.0)], seed=10 + i)
    stone_face(P, "S", X0 + 2.5, X1 - 2.5, 1.6, EAVE - 1.2, YB, -1, col,
               avoid=[(21.0, 25.0, 4.0, 10.5), (27.4, 32.6, 0.0, 10.2), (35.6, 38.4, 6.0, 9.6), (33.6, 34.4, 0.0, 14.0)], seed=3)
    stone_face(P, "E", YB + 2.5, YF - 2.5, 1.6, EAVE - 0.4, X1, 1, col, axis="Y", avoid=[(YC - 2.5, YC + 2.5, 4.0, 10.5), (-79.5, -77.0, 4.8, 8.4)], seed=4)
    stone_face(P, "W", YB + 2.5, YF - 2.5, 1.6, EAVE - 0.4, X0, -1, col, axis="Y", avoid=[(YC - 2.5, YC + 2.5, 4.0, 10.5)], seed=5)
    for e, xp, f in (("E", X1, 1), ("W", X0, -1)):
        stone_face(P, f"Gable{e}", YB + 1.0, YF - 1.0, EAVE + 0.2, RIDGE, xp, f, col, axis="Y",
                   seed=30 + f, tri=(YC, EAVE, RIDGE, (YF - YB) / 2))
    # r1 A4-1/A7-1: soot band under the back eaves + drips, soot band on the front/side wall tops
    box(f"{P}_SootEaveS_Soot_01", (XC, YB - 0.25, 12.8), (X1 - X0 - 5.0, 0.1, 0.7), C["soot"], col)
    box(f"{P}_SootS_Soot_01", (26.2, YB - 0.25, 11.2), (0.9, 0.1, 2.6), C["soot"], col)
    box(f"{P}_SootS_Soot_02", (39.5, YB - 0.25, 11.6), (0.7, 0.1, 1.8), C["soot"], col)
    for e, xp, f in (("E", X1, 1), ("W", X0, -1)):
        box(f"{P}_SootEave{e}_Soot_01", (xp + f * 0.25, YC, EAVE - 0.35), (0.1, YF - YB - 5.0, 0.6), C["soot"], col)
    # r1 A6-1: 1-stud hazard band on the yard/platform edge
    hazard_nosing(P, 2, 14.0, 46.0, -60.6, 0.06, col, w=2.0, depth=1.0, h=0.12)
    # r1 A7-1: teal notice board with a blank cream bill on the sparse east elevation
    box(f"{P}_NoticeE_Teal_01", (X1 + 0.3, -78.25, 6.6), (0.4, 2.8, 2.6), C["teal"], col)
    box(f"{P}_NoticeEBill_Cream_01", (X1 + 0.55, -78.25, 6.6), (0.1, 2.0, 1.8), C["cream"], col)
    # r2 A7-1: east wall lamp bracket beside the window
    box(f"{P}_SideLampArm_Iron_01", (X1 + 0.9, -88.0, 10.2), (1.8, 0.3, 0.3), C["iron"], col)
    box(f"{P}_SideLampPlate_Iron_01", (X1 + 0.1, -88.0, 10.2), (0.2, 0.8, 1.2), C["iron"], col)
    box(f"{P}_SideLampGlass_Glow_01", (X1 + 1.6, -88.0, 9.3), (0.9, 0.9, 1.2), C["glow"], col)
    box(f"{P}_SideLampCap_Iron_01", (X1 + 1.6, -88.0, 10.05), (1.2, 1.2, 0.3), C["iron"], col)
    # r2 A4-1: dark mortar joints between the corner quoin courses so the quoins read against the wall
    j = 0
    for cx, cy in ((X0, YF), (X1, YF), (X0, YB), (X1, YB)):
        sx, sy = (1 if cx == X0 else -1), (-1 if cy == YF else 1)
        for k in range(5):
            j += 1
            box(f"{P}_QuoinJoint_Soot_{j:02d}", (cx + sx * 1.0, cy + sy * 1.0, 1.5 + k * 2.1 + 3.05), (2.5, 2.5, 0.2), C["soot"], col)

def dressing(col, stage):
    # moss: heaviest at the base + roof edges (blueprint: heaviest near building)
    mz = [(19.8, YF + 1.4, 1.5, 3.0, 1.2, 1.0), (40.0, YF + 1.4, 1.5, 3.5, 1.2, 1.2), (X0 - 1.0, -84, 0, 1.4, 5.0, 1.6),
          (X1 + 1.0, -80, 0, 1.4, 4.0, 1.3), (27.5, YB - 1.0, 0, 5.0, 1.4, 1.0), (22, YF + 2.2, 0, 3.0, 1.2, 0.5),
          (39, YF + 2.2, 0, 2.5, 1.2, 0.5),
          # r1 A4-1: moss on the base course (plinth tops)
          (24.0, YB - 0.9, 1.5, 3.0, 0.8, 0.5), (36.0, YB - 0.9, 1.5, 2.2, 0.8, 0.4), (X1 + 0.9, -86.0, 1.5, 0.8, 3.0, 0.5),
          (X0 - 0.9, -79.0, 1.5, 0.8, 2.6, 0.5)]
    for i, m in enumerate(mz, 1):
        moss(P, i, *m, col)
    # ivy up the west quoins
    ivy(P, 1, YF - 4.6, X0, -1, 1.5, 11.0, col, seed=7)

    # yard clutter: r2 A7-1 a different prop group at each corner (NW crates, NE drums, SE hand cart, SW plank stack)
    crate(P, 1, 14.5, -73.5, 0, 2.6, col, 10)
    crate(P, 2, 14.7, -73.7, 2.6, 2.0, col, 35)
    drum(P, 1, 45.0, -73.5, 0, col)
    drum(P, 2, 46.8, -75.2, 0, col, "iron")
    box(f"{P}_CartBed_Timberlt_01", (44.8, -86.0, 1.7), (2.4, 4.0, 0.4), C["timberlt"], col)
    box(f"{P}_CartHandle_Timber_01", (44.8, -83.2, 2.2), (0.3, 2.0, 0.3), C["timber"], col, rot=(-15, 0, 0))
    for s, t in ((-1, "L"), (1, "R")):
        cyl(f"{P}_CartWheel{t}_Iron_01", (44.8 + s * 1.35, -86.8, 1.5), 1.5, 0.3, C["iron"], col, segs=10, axis="X")
    box(f"{P}_CartLeg_Iron_01", (44.8, -84.6, 0.75), (0.3, 0.3, 1.5), C["iron"], col)
    for k, (zz, rz) in enumerate(((0.2, 0), (0.6, 6), (1.0, -4)), 1):
        box(f"{P}_Planks_Timber_{k:02d}", (14.8, -87.5, zz), (1.8, 6.0, 0.4), C["timber"], col, rot=(0, 0, rz))
    # r2 A6-1: yellow capped-post rail on the yard front (y -68, inside the hazard edge band so it shows in the 3P view), gap on the door axis for the route
    k = 0
    for a0, a1 in ((14.0, 25.0), (35.0, 46.0)):
        # r3 A5-2: chunkier rail for the 400px read (>=5 px): top rail 1.2 tall x 1.0 deep, mid rail removed, posts 1.0x1.0
        box(f"{P}_YardRail_Hazard_{(a0 > 30) + 1:02d}", ((a0 + a1) / 2, -68.0, 2.6), (a1 - a0, 1.0, 1.2), C["hazard"], col)
        for i in range(4):
            k += 1
            xx = a0 + 0.5 + i * (a1 - a0 - 1.0) / 3
            box(f"{P}_YardPost_Hazard_{k:02d}", (xx, -68.0, 1.6), (1.0, 1.0, 3.2), C["hazard"], col)
            box(f"{P}_YardPostCap_Ink_{k:02d}", (xx, -68.0, 3.4), (1.3, 1.3, 0.4), C["ink"], col)
    lamp(P, 1, 19.5, -72.0, 0, col)
    lamp(P, 2, 40.5, -72.0, 0, col)
    kit.avatar("Stage_AvatarDepot1", (35.5, -71.0, 0), stage)   # r2 A2-1: off the door axis
    kit.avatar("Stage_AvatarDepot2", (22.0, -71.5, 0), stage)   # r2 A2-1: stand-in moved off the door axis


def build(milestones=True):
    kit.reset()
    col, stage = kit.coll("Depot"), kit.coll("Stage")
    cams = cameras()
    ms = [("pov", cams["pov"]), ("34", cams["34"])]
    steps = [("shell", shell), ("roof", roof), ("details", details), ("dressing", lambda c: dressing(c, stage))]
    for k, (name, fn) in enumerate(steps, 1):
        fn(col)
        if milestones:
            kit.milestone("depot", k, name, ms)
    return cams


if __name__ == "__main__":
    import bpy
    here = os.path.dirname(os.path.abspath(__file__))
    cams = build(milestones="--no-milestones" not in sys.argv)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(here, "depot.blend"))
    if "--no-renders" not in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(here, "renders")
        os.makedirs(out, exist_ok=True)
        kit.bk.render(cams["pov"], os.path.join(out, "depot_pov3p.png"), res=(768, 432))
        kit.bk.render(cams["game"], os.path.join(out, "depot_game.png"), res=(400, 225))
        for k in ("34", "side", "back", "door"):
            kit.bk.render(cams[k], os.path.join(out, f"depot_{k}.png"), res=(1280, 720))
