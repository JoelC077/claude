#!/usr/bin/env python3
"""T1 torn-carriage renders (mission 260929-train-splits). One script; rebuilds everything from an empty scene.

Imports Joel's OBJ (scene.import_train), puts every group in one half (bbox-centre z; the gangway Union22 goes where
break_spec 'structure' says: v2.1 = Carriage2.FrontHalf),
cuts the break_spec crossers the way Studio CSG will (break frame B, FRONT/REAR cutters = per-cell boxes):
  * watertight after weld (merge by position, zero-area faces dropped) -> manifold3d booleans (caps = cutter faces)
  * the plain Blocks (Part269, Part409)                                -> sliced per cell into boxes
  * not watertight                                                     -> fallback: per-cell triangle clipping,
    plus exact caps from the mesh cross-sections (Clipper via manifold3d.CrossSection) unless --fallback-caps off
Cap faces use the crosser's own material. Then ground at rail level + track, poses the states and renders.

  python3 build.py                                  all states, their cameras, preflight.md, progress sheets
  python3 build.py --states intact,break1_t4.0      subset of states   (--cams Cam_Wide,... subset of cameras)
  python3 build.py --no-render                      cut + preflight only
  python3 build.py --samples 22 --scale 100 --out DIR --fallback-caps on|off --no-preflight --no-sheets
States: intact seamref exploded break1_t0.3 break1_t1.0 break1_t1.6 break1_t4.0 break2_t1.2 break2_t4.0
(seamref = the uncut original on the two seam cameras, pixel-diffed against intact into preflight.md section 7)
"""
import argparse, itertools, json, math, os, subprocess, sys, time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
MISSION = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import numpy as np
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import manifold3d as m3
import scene as S

SHEET_TOOL = ('/root/.claude/skills/synced/80b8703d-5ce2-4cfa-8173-3f10e032ad2b_d09bd656-edae-46f7-90d5-de67eb3c3270/'
              'multiuse-critic/scripts/contact_sheet.py')

# ---------------------------------------------------------------- spec / order numbers
SPEC = json.load(open(os.path.join(MISSION, 'src', 'kit', 'break_spec.json')))
CELLS = [(c['X'][0], c['X'][1], c['Y'][0], c['Y'][1], c['d']) for c in SPEC['cells']]
ZEXT = float(SPEC['zext'])
D_LO = min(c[4] for c in CELLS); D_HI = max(c[4] for c in CELLS)
ORIGIN = {1: np.array([-58.05, 13.927, 86.20]), 2: np.array([-58.055, 13.927, 153.60])}   # B frames (T1 order)
CROSSERS = {int(k): list(v) for k, v in SPEC['expected_crossers_export'].items()}
BLOCKS = set(SPEC['block_parts_export'])
Z_JOIN = 116.876
GANGWAY = 'Union22'
RAIL_Y = 5.33
V_SPEED = float(SPEC['motion']['speed_default']); BRAKE = float(SPEC['motion']['brake'])
REC_D = float(SPEC['motion']['recoil']['dist']); REC_T = float(SPEC['motion']['recoil']['time'])
PIVOT_X = float(SPEC['topple']['pivot']['X_abs']); PIVOT_Y = float(SPEC['topple']['pivot']['Y'])
BODY1, BODY2 = SPEC['topple']['bodies']            # all motion / topple numbers come from the spec (v2.2: rest per side)


def profile(b, side):
    """Normalised topple profile of one body for a falling side (+1 = +X, -1 = -X). Spec v2.2: topple.rest per side gives the
    rest roll and a lift that eases in with the roll; bounce = rest roll - bounce_back then back; extra_back eases in over the
    roll. Older specs (roll / bounce list per body, no lift) still work."""
    rest = SPEC['topple'].get('rest')
    if rest:
        r = rest['+X' if side > 0 else '-X']
        roll, lift = float(r['roll']), float(r.get('lift', 0.0))
        lo = roll - float(b['bounce_back'])
    else:
        roll, lift = float(b['roll']), 0.0
        lo = float(b['bounce'][0])
    return dict(delay=b['delay'], roll_time=b['roll_time'], roll=roll, lo=lo, hi=roll, bounce_time=b['bounce_time'],
                yaw=b['yaw'], sink=b['sink'], lift=lift, extra_back=float(b.get('extra_back', 0.0)))
HALF_OF = {'Carriage1.FrontHalf': 'C1F', 'Carriage1.RearHalf': 'C1R', 'Carriage2.FrontHalf': 'C2F', 'Carriage2.RearHalf': 'C2R'}
GANGWAY_HALF = HALF_OF[SPEC.get('structure', {}).get('gangway', 'Carriage1.RearHalf')]
SIDE = {1: +1, 2: -1}            # renders: break 1 falls toward +X, break 2 toward -X

AFTER = ['Cam_Hero', 'Cam_POV_In', 'Cam_Roof3P', 'Cam_Wide', 'Cam_Side', 'Cam_Game']
STATES = {   # state: (kind, breaking carriage k, t, cameras in render order)
    'intact':      ('intact', 1, None, ['Cam_SeamOut', 'Cam_SeamRoof_debug', 'Cam_SeamRoof', 'Cam_SeamIn']),
    'seamref':     ('seamref', 1, None, ['Cam_SeamOut', 'Cam_SeamIn']),   # uncut original, diffed against intact
    'exploded':    ('exploded', 1, None, ['Cam_Exploded']),
    'break1_t0.3': ('break', 1, 0.3, ['Cam_Wide', 'Cam_Side']),
    'break1_t1.0': ('break', 1, 1.0, ['Cam_Wide', 'Cam_Side']),
    'break1_t1.6': ('break', 1, 1.6, ['Cam_Wide', 'Cam_Side']),
    'break1_t4.0': ('break', 1, 4.0, ['Cam_Wide', 'Cam_Hero', 'Cam_POV_In', 'Cam_Roof3P', 'Cam_Side', 'Cam_Game']),
    'break2_t1.2': ('break', 2, 1.2, ['Cam_Wide']),
    'break2_t4.0': ('break', 2, 4.0, ['Cam_Hero', 'Cam_POV_In', 'Cam_Wide']),
}
CAMS = {     # name: (loc B, look-at B, vertical FOV deg or None, ortho scale or None, resolution)
    'Cam_SeamOut':  ((16, 6, 0), (9.7, 6, 0), 40, None, (1600, 900)),
    'Cam_SeamIn':   ((0, 5, -7), (-9.4, 5, 1), 70, None, (1600, 900)),
    'Cam_SeamRoof': ((0, 30, 0), (0, 14, 0.01), None, 26, (1600, 900)),
    'Cam_Exploded': ((22, 14, -10), (0, 5, 0), 70, None, (1600, 900)),
    'Cam_Hero':     ((15, 9, 9), (0, 5, -1.5), 70, None, (1600, 900)),
    'Cam_POV_In':   ((1.2, 5.0, -12), (0, 4, 2), 70, None, (1600, 900)),
    'Cam_Roof3P':   ((2, 22, -20), (0, 8, 6), 70, None, (1600, 900)),
    'Cam_Wide':     ((70, 45, -40), (0, 0, 35), 70, None, (1600, 900)),
    'Cam_Side':     ((60, 6, 20), (0, 6, 20), None, 90, (1600, 900)),
    'Cam_Game':     ((45, 30, -40), (0, 5, 5), 70, None, (400, 225)),
}
CAM_AT = {   # per-time overrides (coordinator, spec v2.1): at t = 4.0 Cam_Side frames the kept train and the wreck
    ('Cam_Side', 4.0): ((60, 6, 45), (0, 6, 45), None, 140, (1600, 900)),
}
SHEETS = {
    'p2_tear_design.png': [('Seam out (intact)', 'intact__Cam_SeamOut.png'),
                           ('Roof top, tear line red', 'intact__Cam_SeamRoof_debug.png'),
                           ('Exploded 6 studs', 'exploded__Cam_Exploded.png')],
    'p3_topple.png': [('Break 1  t 0.3 s', 'break1_t0.3__Cam_Wide.png'), ('Break 1  t 1.0 s', 'break1_t1.0__Cam_Wide.png'),
                      ('Break 1  t 1.6 s', 'break1_t1.6__Cam_Wide.png'), ('Break 1  t 4.0 s', 'break1_t4.0__Cam_Wide.png')],
    'p4_torn_ends.png': [('Break 1 hero t 4.0', 'break1_t4.0__Cam_Hero.png'), ('Break 1 POV inside', 'break1_t4.0__Cam_POV_In.png'),
                         ('Break 1 roof 3rd person', 'break1_t4.0__Cam_Roof3P.png'), ('Break 2 hero t 4.0', 'break2_t4.0__Cam_Hero.png')],
}


# ---------------------------------------------------------------- small geometry helpers
def svol(P):
    """Signed volume of a triangle soup P (n,3,3)."""
    if len(P) == 0:
        return 0.0
    return float(np.einsum('ij,ij->i', P[:, 0], np.cross(P[:, 1], P[:, 2])).sum() / 6.0)


def tri_normals(P):
    n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(ln, 1e-30), ln[:, 0] / 2


def weld(P, tol=1e-5):
    flat = P.reshape(-1, 3)
    q = np.round(flat / tol).astype(np.int64)
    _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    return flat[first], inv.reshape(-1, 3)


def edge_report(F):
    nd = (F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 2] != F[:, 0])
    G = F[nd].astype(np.int64)
    n = int(G.max()) + 1
    a = G.reshape(-1); b = G[:, [1, 2, 0]].reshape(-1)
    fwd = a * n + b
    _, c = np.unique(fwd, return_counts=True)
    missing = int((~np.isin(b * n + a, fwd)).sum())
    und = np.unique(np.minimum(a, b) * n + np.maximum(a, b), return_counts=True)[1]
    Fs = np.sort(G, axis=1)
    fins = int((np.unique(Fs, axis=0, return_counts=True)[1] > 1).sum())
    rep = dict(degenerate=int((~nd).sum()), boundary=int((und == 1).sum()), nonmanifold=int((und > 2).sum()), fins=fins,
               watertight=bool((c > 1).sum() == 0 and missing == 0))
    return rep, nd


def uv_density(P, UV):
    n3, a3 = tri_normals(P)
    a2 = 0.5 * np.abs(np.cross(UV[:, 1] - UV[:, 0], UV[:, 2] - UV[:, 0]))
    ok = a3 > 1e-6
    if not ok.any():
        return 0.25
    return float(np.median(np.sqrt(a2[ok] / a3[ok]))) or 0.25


def planar_attrs(P, scale):
    """UV + normal for flat axis-aligned cap triangles P (n,3,3) (coords in B)."""
    n, _ = tri_normals(P)
    ax = np.argmax(np.abs(n), axis=1)
    u_ax = (ax + 1) % 3; w_ax = (ax + 2) % 3
    rows = np.arange(len(P))[:, None]
    U = P[rows, np.arange(3)[None, :], u_ax[:, None]]
    W = P[rows, np.arange(3)[None, :], w_ax[:, None]]
    UV = np.stack([U, W], axis=2) * scale
    N = np.repeat(n[:, None, :], 3, axis=1)
    return UV, N


# ---------------------------------------------------------------- cutters (manifold3d)
def make_cutters():
    fr, rr = [], []
    for (x0, x1, y0, y1, d) in CELLS:
        fr.append(m3.Manifold.cube([x1 - x0, y1 - y0, d + ZEXT]).translate([x0, y0, -ZEXT]))
        rr.append(m3.Manifold.cube([x1 - x0, y1 - y0, ZEXT - d]).translate([x0, y0, d]))
    return (m3.Manifold.batch_boolean(fr, m3.OpType.Add).as_original(),
            m3.Manifold.batch_boolean(rr, m3.OpType.Add).as_original())


def unpack(man, cap_id):
    mg = man.to_mesh64()
    vp = np.asarray(mg.vert_properties, dtype=np.float64)
    tv = np.asarray(mg.tri_verts).astype(np.int64)
    ri = np.asarray(mg.run_index).astype(np.int64); rid = np.asarray(mg.run_original_id).astype(np.int64)
    tid = np.repeat(rid, np.diff(ri) // 3)
    C = vp[tv]
    return dict(P=C[:, :, :3].copy(), UV=C[:, :, 3:5].copy(), N=C[:, :, 5:8].copy(), cap=(tid == cap_id))


def to_manifold(V, F, nd, UV, N):
    """Welded mesh with per-corner UV + normal as manifold3d properties. Returns (Manifold, None) or (None, reason)."""
    Fk = F[nd]
    props = np.concatenate([V[Fk], UV[nd], N[nd]], axis=2).reshape(-1, 8)
    uq, inv = np.unique(props, axis=0, return_inverse=True)
    tri = inv.reshape(-1, 3).astype(np.uint32)
    q = np.round(uq[:, :3] / 1e-5).astype(np.int64)
    _, first, pinv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    to = first[pinv.reshape(-1)]; frm = np.arange(len(uq)); sel = to != frm
    man = m3.Manifold(m3.Mesh64(vert_properties=np.ascontiguousarray(uq), tri_verts=np.ascontiguousarray(tri),
                                merge_from_vert=frm[sel].astype(np.uint32), merge_to_vert=to[sel].astype(np.uint32)))
    if man.status() != m3.Error.NoError:
        return None, 'manifold3d status %s' % man.status()
    v_in = svol(V[Fk])
    if abs(man.volume() - v_in) > 1e-4 * abs(v_in):
        return None, 'manifold3d import changed the volume %.3f -> %.3f' % (v_in, man.volume())
    return man, None


def cut_manifold(V, F, nd, UV, N, cutters):
    """Returns (front, rear, info) or (None, None, reason)."""
    man, why = to_manifold(V, F, nd, UV, N)
    if man is None:
        return None, None, why
    fcut, rcut = cutters
    front = unpack(man - rcut, rcut.original_id())
    rear = unpack(man - fcut, fcut.original_id())
    return front, rear, 'manifold3d'


# ---------------------------------------------------------------- fallback: per-cell clipping (+ exact caps)
def _isect(p, q, ax, val):
    if tuple(p[:3]) > tuple(q[:3]):
        p, q = q, p
    t = (val - p[ax]) / (q[ax] - p[ax])
    r = p + (q - p) * t
    r[ax] = val
    return r


def _clip(poly, ax, val, keep_ge):
    out = []
    n = len(poly)
    for i in range(n):
        c = poly[i]; nx = poly[(i + 1) % n]
        ci = (c[ax] >= val) if keep_ge else (c[ax] < val)
        ni = (nx[ax] >= val) if keep_ge else (nx[ax] < val)
        if ci:
            out.append(c)
        if ci != ni:
            out.append(_isect(c, nx, ax, val))
    return out


def _fan(poly, out):
    for i in range(1, len(poly) - 1):
        t = np.stack([poly[0], poly[i], poly[i + 1]])
        if np.linalg.norm(np.cross(t[1, :3] - t[0, :3], t[2, :3] - t[0, :3])) > 1e-12:
            out.append(t)


def xsection(V, F, ax, val):
    """Oriented cross-section loops (2D, coords (ax+1)%3, (ax+2)%3) of the closed surface (V, F) with plane coord[ax]=val."""
    above = V[:, ax] >= val
    A = above[F]
    s = A.sum(1)
    segs = []
    for i in np.where((s == 1) | (s == 2))[0]:
        f = F[i]; a = A[i]; down = up = None
        for j in range(3):
            p, q = int(f[j]), int(f[(j + 1) % 3])
            if a[j] and not a[(j + 1) % 3]:
                down = (min(p, q), max(p, q))
            elif (not a[j]) and a[(j + 1) % 3]:
                up = (min(p, q), max(p, q))
        segs.append((down, up))
    cache = {}

    def pt(e):
        if e not in cache:
            cache[e] = _isect(V[e[0]].copy(), V[e[1]].copy(), ax, val)
        return cache[e]
    starts = defaultdict(list)
    for si, (a0, _) in enumerate(segs):
        starts[a0].append(si)
    used = np.zeros(len(segs), bool); loops = []; open_chains = 0
    for si in range(len(segs)):
        if used[si]:
            continue
        loop = []; cur = si; closed = False
        while True:
            used[cur] = True
            a0, b0 = segs[cur]; loop.append(a0)
            if b0 == segs[si][0]:
                closed = True; break
            nxt = next((k for k in starts[b0] if not used[k]), None)
            if nxt is None:
                break
            cur = nxt
        if closed and len(loop) >= 3:
            loops.append(loop)
        elif not closed:
            open_chains += 1
    u_ax, w_ax = (ax + 1) % 3, (ax + 2) % 3
    polys = [np.array([[pt(e)[u_ax], pt(e)[w_ax]] for e in lp]) for lp in loops]
    area = sum(0.5 * float(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])) for p in polys)
    if area < 0:
        polys = [p[::-1].copy() for p in polys]
    return (m3.CrossSection(polys, m3.FillRule.Positive) if polys else m3.CrossSection()), open_chains


def rect_caps(cs, ax, val, u0, u1, w0, w1):
    """Triangles (n,3,3) of cross-section cs clipped to the rectangle, lifted to 3D, normal +axis."""
    if u1 - u0 <= 1e-9 or w1 - w0 <= 1e-9:
        return np.zeros((0, 3, 3))
    r = cs ^ m3.CrossSection.square([u1 - u0, w1 - w0]).translate([u0, w0])
    polys = [np.asarray(p) for p in r.to_polygons()]
    if not polys:
        return np.zeros((0, 3, 3))
    tri = np.asarray(m3.triangulate(polys))
    pts = np.concatenate(polys)
    P3 = np.zeros((len(pts), 3)); P3[:, ax] = val; P3[:, (ax + 1) % 3] = pts[:, 0]; P3[:, (ax + 2) % 3] = pts[:, 1]
    return P3[tri] if len(tri) else np.zeros((0, 3, 3))


def boundaries():
    """Shared cell boundaries: (axis, value, lo, hi, d_neg, d_pos) for d_neg != d_pos."""
    out = []
    for a, b in itertools.permutations(CELLS, 2):
        if abs(a[1] - b[0]) < 1e-9:                      # a | b across X = a.x1
            lo, hi = max(a[2], b[2]), min(a[3], b[3])
            if hi - lo > 1e-9 and a[4] != b[4]:
                out.append((0, a[1], lo, hi, a[4], b[4]))
        if abs(a[3] - b[2]) < 1e-9:                      # a below b across Y = a.y1
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if hi - lo > 1e-9 and a[4] != b[4]:
                out.append((1, a[3], lo, hi, a[4], b[4]))
    return out


def cut_clip(V, F, nd, UV, N, caps=True):
    Fk = F[nd]
    P = V[Fk]
    attrs = np.concatenate([P, UV[nd], N[nd]], axis=2)
    zmn = P[:, :, 2].min(1); zmx = P[:, :, 2].max(1)
    fr = [attrs[zmx < D_LO]]; rr = [attrs[zmn >= D_HI]]
    ftri, rtri = [], []
    for i in np.where(~(zmx < D_LO) & ~(zmn >= D_HI))[0]:
        tri = attrs[i]
        xmn, xmx = tri[:, 0].min(), tri[:, 0].max(); ymn, ymx = tri[:, 1].min(), tri[:, 1].max()
        for (x0, x1, y0, y1, d) in CELLS:
            if xmx < x0 or xmn >= x1 or ymx < y0 or ymn >= y1:
                continue
            poly = [tri[0].copy(), tri[1].copy(), tri[2].copy()]
            for ax, val, ge in ((0, x0, True), (0, x1, False), (1, y0, True), (1, y1, False)):
                poly = _clip(poly, ax, val, ge)
                if len(poly) < 3:
                    break
            if len(poly) < 3:
                continue
            _fan(_clip(poly, 2, d, False), ftri)
            _fan(_clip(poly, 2, d, True), rtri)
    if ftri: fr.append(np.stack(ftri))
    if rtri: rr.append(np.stack(rtri))
    fa = np.concatenate(fr); ra = np.concatenate(rr)
    front = dict(P=fa[:, :, :3], UV=fa[:, :, 3:5], N=fa[:, :, 5:8], cap=np.zeros(len(fa), bool))
    rear = dict(P=ra[:, :, :3], UV=ra[:, :, 3:5], N=ra[:, :, 5:8], cap=np.zeros(len(ra), bool))
    info = {'open_chains': 0}
    if caps:
        Vn = V; Fn = Fk
        xs = {}
        fcap, rcap = [], []
        for (x0, x1, y0, y1, d) in CELLS:
            if (2, d) not in xs:
                xs[(2, d)] = xsection(Vn, Fn, 2, d)
            t = rect_caps(xs[(2, d)][0], 2, d, x0, x1, y0, y1)
            fcap.append(t); rcap.append(t[:, ::-1])
        for (ax, val, lo, hi, dn, dp) in boundaries():
            if (ax, val) not in xs:
                xs[(ax, val)] = xsection(Vn, Fn, ax, val)
            zl, zh = min(dn, dp), max(dn, dp)
            if ax == 0:
                t = rect_caps(xs[(ax, val)][0], 0, val, lo, hi, zl, zh)      # (y, z) plane, normal +X
            else:
                t = rect_caps(xs[(ax, val)][0], 1, val, zl, zh, lo, hi)      # (z, x) plane, normal +Y
            if dn < dp:      # front piece lives on the + side in [dn, dp] -> faces -axis ; rear faces +axis
                fcap.append(t[:, ::-1]); rcap.append(t)
            else:
                fcap.append(t); rcap.append(t[:, ::-1])
        info['open_chains'] = sum(v[1] for v in xs.values())
        for piece, caps_ in ((front, fcap), (rear, rcap)):
            C = np.concatenate([c for c in caps_ if len(c)]) if any(len(c) for c in caps_) else np.zeros((0, 3, 3))
            piece['P'] = np.concatenate([piece['P'], C])
            piece['UV'] = np.concatenate([piece['UV'], np.zeros((len(C), 3, 2))])
            piece['N'] = np.concatenate([piece['N'], np.zeros((len(C), 3, 3))])
            piece['cap'] = np.concatenate([piece['cap'], np.ones(len(C), bool)])
    return front, rear, ('clip+caps' if caps else 'clip (no caps)'), info


# ---------------------------------------------------------------- plain Blocks: per-cell boxes
def cut_block(V, F, nd, UV, N):
    """Plain Block sliced per cell: piece_i = block ^ cell box (exact; the export's Blocks are tilted ~0.001 deg).
    Cut faces flagged = the faces at Z = d (the X/Y slice faces between sub-blocks of one half are internal)."""
    man, why = to_manifold(V, F, nd, UV, N)
    assert man is not None, why
    fronts, rears = [], []
    for (x0, x1, y0, y1, d) in CELLS:
        for lst, z0, z1 in ((fronts, -ZEXT, d), (rears, d, ZEXT)):
            box = m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0]).as_original()
            pc = man ^ box
            if pc.is_empty() or pc.volume() <= 1e-9:
                continue
            u = unpack(pc, box.original_id())
            n, _ = tri_normals(u['P'])
            u['cap'] = u['cap'] & (np.abs(n[:, 2]) > 0.99)
            u['slice'] = (x1 - x0, z1 - z0)
            lst.append(u)
    return fronts, rears


# ---------------------------------------------------------------- Blender plumbing
def obj_tris(o):
    """Corner arrays of an imported object (mesh data are Roblox world coords): P (n,3,3), UV (n,3,2), N (n,3,3)."""
    me = o.data
    me.calc_loop_triangles()
    nv = len(me.vertices); co = np.empty(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    nt = len(me.loop_triangles)
    tv = np.empty(nt * 3, np.int64); me.loop_triangles.foreach_get('vertices', tv); tv = tv.reshape(-1, 3)
    tl = np.empty(nt * 3, np.int64); me.loop_triangles.foreach_get('loops', tl); tl = tl.reshape(-1, 3)
    nl = len(me.loops)
    uv = np.zeros(nl * 2)
    if me.uv_layers:
        me.uv_layers[0].data.foreach_get('uv', uv)
    cn = np.empty(nl * 3); me.corner_normals.foreach_get('vector', cn)
    return co[tv], uv.reshape(-1, 2)[tl], cn.reshape(-1, 3)[tl]


def obj_world_tris(o):
    """Triangles of any mesh object in Roblox world coords (mesh data are Roblox coords for everything we build)."""
    me = o.data
    me.calc_loop_triangles()
    nv = len(me.vertices); co = np.empty(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    nt = len(me.loop_triangles)
    tv = np.empty(nt * 3, np.int64); me.loop_triangles.foreach_get('vertices', tv)
    return co, tv.reshape(-1, 3)


def make_obj(name, P, UV, N, mat, R):
    flat = P.reshape(-1, 3)
    q = np.round(flat / 1e-6).astype(np.int64)
    _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    verts = flat[first]; faces = inv.reshape(-1, 3)
    ok = (faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 2] != faces[:, 0])
    faces = faces[ok]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], faces.tolist())
    me.materials.append(mat)
    uvl = me.uv_layers.new(name='UVMap')
    uvl.data.foreach_set('uv', UV[ok].reshape(-1).astype(np.float32))
    me.polygons.foreach_set('use_smooth', np.ones(len(faces), bool))
    nn = N[ok].reshape(-1, 3)
    nn = nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)
    me.normals_split_custom_set(nn.tolist())
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.matrix_world = R
    return ob


def emit_mat(name, rgb, strength=4.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*rgb, 1); em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m


def plain_mat(name, rgb, rough=0.8, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m


def srgb(hexs):
    h = hexs.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def boxes_obj(name, boxes, mat, R):
    """boxes: list of (x0,x1,y0,y1,z0,z1) Roblox coords -> one mesh object."""
    verts, faces = [], []
    for (x0, x1, y0, y1, z0, z1) in boxes:
        b = len(verts)
        verts += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        faces += [(b + i, b + j, b + k, b + l) for (i, j, k, l) in
                  [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)]]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.materials.append(mat); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); ob.matrix_world = R
    return ob


# ---------------------------------------------------------------- motion (Roblox coords, 4x4)
def drift(t):
    rec = REC_D * (1 - math.cos(math.pi * min(t / REC_T, 1.0))) / 2
    tb = V_SPEED / BRAKE
    return rec + (0.5 * BRAKE * t * t if t <= tb else 0.5 * BRAKE * tb * tb + V_SPEED * (t - tb))


def topple(t, b):
    """b = profile(). Returns roll, yaw, sink, roll progress (u^2 during the roll, 1 after)."""
    d, R_, T_ = b['delay'], b['roll'], b['roll_time']
    lo, hi = b['lo'], b['hi']; Tb = b['bounce_time']
    if t <= d:
        return 0.0, 0.0, 0.0, 0.0
    if t <= d + T_:
        u = (t - d) / T_
        return R_ * u * u, b['yaw'] * u * u, b['sink'] * max(0.0, (t - (d + T_ - 0.1)) / 0.1), u * u
    tau = t - d - T_
    if tau < Tb / 2:
        v = tau / (Tb / 2); roll = R_ + (lo - R_) * (1 - (1 - v) ** 2)          # QuadOut rest -> rest - bounce_back
    elif tau < Tb:
        v = (tau - Tb / 2) / (Tb / 2); roll = lo + (hi - lo) * v * v             # QuadIn back to rest
    else:
        roll = hi
    return roll, b['yaw'], b['sink'], 1.0


def Tm(v):
    m = np.eye(4); m[:3, 3] = v; return m


def Rz(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    m = np.eye(4); m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c; return m


def Ry(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    m = np.eye(4); m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c; return m


def body_matrix(t, frame_k, side, prof, centre):
    roll, yaw, sink, prog = topple(t, prof)
    lift = prof['lift'] * min(1.0, roll / prof['roll']) if prof['roll'] else 0.0     # lift eases in with the roll
    back = prof['extra_back'] * prog                                                  # extra +Z eased in over the roll
    P = ORIGIN[frame_k] + np.array([side * PIVOT_X, PIVOT_Y, 0.0])
    Mr = Tm(P) @ Rz(-side * roll) @ Tm(-P)                  # top of the body goes toward the falling side
    c2 = (Mr @ np.append(centre, 1.0))[:3]
    My = Tm(c2) @ Ry(side * yaw) @ Tm(-c2)                  # yaw about the vertical line through the body centre
    return Tm([0.0, lift - sink, drift(t) + back]) @ My @ Mr, (roll, side * yaw, sink, lift, back)


# ---------------------------------------------------------------- the build
class Build:
    def __init__(self, args):
        self.args = args
        self.t0 = time.time()
        S.reset()
        self.objs = S.import_train()
        self.R = self.objs[0].matrix_world.copy()
        self.Rnp = np.array(self.R)
        assert np.allclose(self.Rnp, np.array(Matrix.Rotation(math.radians(90), 4, 'X'))), 'unexpected import axes'
        self.by = {o.name: o for o in self.objs}
        self.half = {'C1F': [], 'C1R': [], 'C2F': [], 'C2R': []}
        self.piece_info = []            # per crosser rows for preflight
        self.pieces = {}                # crosser -> {'F': [objs], 'R': [objs], 'k': k}
        self.originals = {}             # crosser -> original (uncut, hidden) object
        self.cap_flags = {}             # obj name -> bool array per face (mesh polygon order)
        self.cutters = make_cutters()
        self.assign()
        self.cut_all()
        self.scene_dressing()

    # ---- halves by bbox centre
    def assign(self):
        cross = set(CROSSERS[1]) | set(CROSSERS[2])
        self.rest_bbox = {}
        for o in self.objs:
            co = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
            self.rest_bbox[o.name] = (co.min(0), co.max(0))
            if o.name in cross:
                continue
            zc = 0.5 * (co[:, 2].min() + co[:, 2].max())
            if o.name == GANGWAY:
                h = GANGWAY_HALF
            elif zc < ORIGIN[1][2]:
                h = 'C1F'
            elif zc < Z_JOIN:
                h = 'C1R'
            elif zc < ORIGIN[2][2]:
                h = 'C2F'
            else:
                h = 'C2R'
            self.half[h].append(o)

    # ---- cut every crosser
    def cut_all(self):
        caps = self.args.fallback_caps == 'on'
        for k in (1, 2):
            Ok = ORIGIN[k]
            for name in CROSSERS[k]:
                o = self.by[name]
                mat = o.data.materials[0]
                P, UV, N = obj_tris(o)
                Pb = P - Ok
                ext = (Pb.reshape(-1, 3).min(0), Pb.reshape(-1, 3).max(0))
                assert ext[0][0] > -14 and ext[1][0] < 14 and ext[0][1] > -12 and ext[1][1] < 18 and ext[0][2] > -ZEXT and ext[1][2] < ZEXT, name
                V, F = weld(Pb)
                rep, nd = edge_report(F)
                v_orig = svol(V[F[nd]])
                row = dict(name=name, k=k, v_orig=v_orig, rep=rep)
                fobjs, robjs = [], []
                if name in BLOCKS:
                    fb, rb = cut_block(V, F, nd, UV, N)
                    scale = uv_density(P, UV)
                    for tag, lst, out in (('F', fb, fobjs), ('R', rb, robjs)):
                        for i, bx in enumerate(lst):
                            cm = np.all(np.abs(bx['UV']) < 1e-12, axis=(1, 2)) & np.all(np.abs(bx['N']) < 1e-12, axis=(1, 2))
                            if cm.any():
                                cu, cn = planar_attrs(bx['P'][cm], scale)
                                bx['UV'][cm] = cu; bx['N'][cm] = cn
                            ob = make_obj('%s.%s%d' % (name, tag, i), bx['P'] + Ok, bx['UV'], bx['N'], mat, self.R)
                            self.cap_flags[ob.name] = self._flags_after_weld(bx['P'] + Ok, bx['cap'])
                            out.append(ob)
                    row['path'] = 'block sliced per cell'
                    row['v_front'] = sum(svol(b['P']) for b in fb); row['v_rear'] = sum(svol(b['P']) for b in rb)
                    row['n_pieces'] = (len(fb), len(rb))
                else:
                    front = rear = None
                    if rep['watertight']:
                        front, rear, why = cut_manifold(V, F, nd, UV, N, self.cutters)
                    else:
                        why = 'not watertight (%d non-manifold edges, %d fin pairs)' % (rep['nonmanifold'], rep['fins'])
                    if front is None:
                        row['fallback_reason'] = why
                        try:                                  # what manifold3d itself would make of it (for the record)
                            mi = m3.Manifold(m3.Mesh64(vert_properties=np.ascontiguousarray(V), tri_verts=F[nd].astype(np.uint32)))
                            if mi.status() == m3.Error.NoError:
                                row['m3_import'] = 'manifold3d would import it as %.3f (%+.2f %%)' % (mi.volume(), 100 * (mi.volume() - v_orig) / abs(v_orig))
                            else:
                                row['m3_import'] = 'manifold3d rejects it (%s)' % mi.status()
                        except Exception as ex:
                            row['m3_import'] = 'manifold3d error %s' % ex
                        front, rear, path, info = cut_clip(V, F, nd, UV, N, caps=caps)
                        row['path'] = path; row['open_chains'] = info['open_chains']
                    else:
                        row['path'] = 'manifold3d'
                    scale = uv_density(P, UV)
                    for tag, pc, out in (('F', front, fobjs), ('R', rear, robjs)):
                        if pc['cap'].any():
                            cu, cn = planar_attrs(pc['P'][pc['cap']], scale)
                            pc['UV'][pc['cap']] = cu; pc['N'][pc['cap']] = cn
                        ob = make_obj('%s.%s' % (name, tag), pc['P'] + Ok, pc['UV'], pc['N'], mat, self.R)
                        # polygon order = kept (non-degenerate) triangles; recompute flags against the welded mesh
                        self.cap_flags[ob.name] = self._flags_after_weld(pc['P'] + Ok, pc['cap'])
                        out.append(ob)
                    row['v_front'] = svol(front['P']); row['v_rear'] = svol(rear['P'])
                    row['caps'] = (int(front['cap'].sum()), int(rear['cap'].sum()))
                self.piece_info.append(row)
                self.pieces[name] = {'F': fobjs, 'R': robjs, 'k': k}
                self.half['C%dF' % k] += fobjs
                self.half['C%dR' % k] += robjs
                o.hide_render = True                                  # kept only for the uncut reference renders
                self.originals[name] = o
                del self.by[name]

    @staticmethod
    def _flags_after_weld(P, cap):
        flat = P.reshape(-1, 3)
        q = np.round(flat / 1e-6).astype(np.int64)
        _, inv = np.unique(q, axis=0, return_inverse=True)
        f = inv.reshape(-1, 3)
        ok = (f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 2] != f[:, 0])
        return cap[ok]

    # ---- ground, track, sun/world, cameras, tear line
    def scene_dressing(self):
        S.world()
        sc = bpy.context.scene
        sc.render.use_persistent_data = True
        self.ground = S.ground(z=RAIL_Y, size=4000)
        steel = plain_mat('RailSteel', srgb('#363A42'), 0.35, 0.85)
        wood = plain_mat('Sleeper', srgb('#3B2A1E'), 0.9)
        ballast = plain_mat('Ballast', srgb('#6B665E'), 0.95)
        z0, z1 = -500.0, 900.0
        rails = [(-66.70 - 0.36, -66.70 + 0.36), (-49.015 - 0.36, -49.015 + 0.36)]   # under the wheel treads
        self.track = [
            boxes_obj('Rails', [(a, b, RAIL_Y, RAIL_Y + 0.25, z0, z1) for (a, b) in rails], steel, self.R),
            boxes_obj('Sleepers', [(-69.6, -46.1, RAIL_Y, RAIL_Y + 0.12, z, z + 1.1) for z in np.arange(z0, z1, 2.6)], wood, self.R),
            boxes_obj('Ballast', [(-70.3, -45.4, RAIL_Y - 0.05, RAIL_Y + 0.03, z0, z1)], ballast, self.R),
        ]
        self.cams = {}
        red = emit_mat('TearRed', (1.0, 0.02, 0.02), 6.0)
        self.tearline = self.make_tearline(1, red)
        self.tearline.hide_render = True

    def make_tearline(self, k, mat):
        segs = []
        for name in CROSSERS[k]:
            for ob in self.pieces[name]['F']:
                if name in BLOCKS:
                    continue
                co, F = obj_world_tris(ob)
                flags = self.cap_flags[ob.name]
                if len(flags) != len(F) or not flags.any():
                    continue
                e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
                fl = np.tile(flags, 3)
                key = np.sort(e, axis=1)
                d = defaultdict(set)
                for (a, b), c in zip(map(tuple, key), fl):
                    d[(a, b)].add(bool(c))
                for (a, b), s in d.items():
                    if len(s) == 2:
                        segs.append((co[a], co[b]))
        cu = bpy.data.curves.new('TearLine', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.07; cu.bevel_resolution = 1
        for a, b in segs:
            sp = cu.splines.new('POLY'); sp.points.add(1)
            sp.points[0].co = (*a, 1.0); sp.points[1].co = (*b, 1.0)
        ob = bpy.data.objects.new('TearLine', cu); bpy.context.scene.collection.objects.link(ob)
        ob.matrix_world = self.R; cu.materials.append(mat)
        self.tear_segments = len(segs)
        return ob

    def camera(self, cname, k, t=None):
        spec = CAM_AT.get((cname, t), CAMS[cname])
        key = (cname, k) + tuple(spec[:4])
        if key in self.cams:
            return self.cams[key]
        loc, look, fov, ortho, res = spec
        lw = ORIGIN[k] + np.array(loc, float); kw = ORIGIN[k] + np.array(look, float)
        nm = '%s_k%d_%d' % (cname, k, len(self.cams))
        c = bpy.data.objects.new(nm, bpy.data.cameras.new(nm))
        bpy.context.scene.collection.objects.link(c)
        c.location = S.r2b(lw)
        c.rotation_euler = (S.r2b(kw) - S.r2b(lw)).to_track_quat('-Z', 'Y').to_euler()
        c.data.clip_start = 0.05; c.data.clip_end = 6000
        if ortho:
            c.data.type = 'ORTHO'; c.data.ortho_scale = ortho
        else:
            c.data.sensor_fit = 'VERTICAL'; c.data.sensor_height = 24.0
            c.data.lens = 12.0 / math.tan(math.radians(fov) / 2)
        self.cams[key] = (c, res)
        return self.cams[key]

    # ---- poses
    def bodies(self, k):
        """Lost bodies of break k: list of (objects, frame carriage, profile)."""
        if k == 1:
            return [(self.half['C1R'], 1, profile(BODY1, SIDE[1])), (self.half['C2F'] + self.half['C2R'], 2, profile(BODY2, SIDE[1]))]
        return [(self.half['C2R'], 2, profile(BODY1, SIDE[2]))]

    def kept(self, k):
        return self.half['C1F'] if k == 1 else self.half['C1F'] + self.half['C1R'] + self.half['C2F']

    def centre(self, objs):
        lo = np.min([self.bbox_of(o)[0] for o in objs], axis=0); hi = np.max([self.bbox_of(o)[1] for o in objs], axis=0)
        return 0.5 * (lo + hi)

    def bbox_of(self, o):
        if o.name not in self.rest_bbox:
            co = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
            self.rest_bbox[o.name] = (co.min(0), co.max(0))
        return self.rest_bbox[o.name]

    def pose_matrices(self, state):
        """Roblox-space 4x4 per object name (missing = identity) + a description."""
        kind, k, t, _ = STATES[state]
        mats = {}; desc = []
        if kind == 'exploded':
            for o in self.half['C1F']:
                mats[o.name] = Tm([0, 0, -3.0])
            for h in ('C1R', 'C2F', 'C2R'):
                for o in self.half[h]:
                    mats[o.name] = Tm([0, 0, 3.0])
        elif kind == 'break':
            side = SIDE[k]
            for objs, fk, prof in self.bodies(k):
                Mb, (roll, yaw, sink, lift, back) = body_matrix(t, fk, side, prof, self.centre(objs))
                for o in objs:
                    mats[o.name] = Mb
                desc.append('roll %.2f yaw %.1f sink %.2f lift %.2f back %.2f' % (roll, yaw, sink, lift, back))
            desc.insert(0, 'drift %.2f' % drift(t))
        return mats, desc

    def apply_pose(self, state):
        mats, desc = self.pose_matrices(state)
        for h in self.half.values():
            for o in h:
                o.matrix_world = self.R @ Matrix(mats.get(o.name, np.eye(4)).tolist())
        self.tearline.matrix_world = self.R @ Matrix(mats.get(self.half['C1F'][0].name, np.eye(4)).tolist())
        return desc

    # ---- uncut reference: same cameras with the original crossers, pixel diff against the intact renders
    def render_reference(self, samples, out_dir, scale, log, pf_path):
        self.apply_pose('intact')
        pieces = [ob for pc in self.pieces.values() for t in ('F', 'R') for ob in pc[t]]
        for ob in pieces: ob.hide_render = True
        for o in self.originals.values(): o.hide_render = False
        try:
            for cname in STATES['seamref'][3]:
                c, res = self.camera(cname, 1)
                path = os.path.join(out_dir, 'reference_uncut__%s.png' % cname)
                r = (max(16, res[0] * scale // 100), max(16, res[1] * scale // 100))
                t1 = time.time(); S.render(c, path, res=r, samples=samples); dt = time.time() - t1
                log.append(('reference_uncut', cname, dt, 'original crossers, no cut'))
                print('[render] reference_uncut %s %.1fs' % (cname, dt), flush=True)
        finally:
            for ob in pieces: ob.hide_render = False
            for o in self.originals.values(): o.hide_render = True
        if pf_path:
            put_seam_section(pf_path, out_dir)

    # ---- render
    def render_state(self, state, cams_filter, samples, out_dir, scale, log):
        kind, k, t, cams = STATES[state]
        desc = self.apply_pose(state)
        done = []
        for cname in cams:
            base = cname.replace('_debug', '')
            if cams_filter and base not in cams_filter and cname not in cams_filter:
                continue
            c, res = self.camera(base, k, t)
            self.tearline.hide_render = not cname.endswith('_debug')
            path = os.path.join(out_dir, '%s__%s.png' % (state, cname))
            r = (max(16, res[0] * scale // 100), max(16, res[1] * scale // 100))
            t1 = time.time()
            S.render(c, path, res=r, samples=samples)
            dt = time.time() - t1
            log.append((state, cname, dt, ' / '.join(desc)))
            print('[render] %s %s %.1fs' % (state, cname, dt), flush=True)
            done.append(path)
            self.tearline.hide_render = True
            yield path


# ---------------------------------------------------------------- preflight
def mesh_world(o, Mw=None):
    co, F = obj_world_tris(o)
    if Mw is not None:
        co = co @ Mw[:3, :3].T + Mw[:3, 3]
    return co, F


def bvh_of(co, F):
    return BVHTree.FromPolygons([Vector(p) for p in co], [tuple(int(i) for i in f) for f in F], all_triangles=True)


def components(co, F):
    parent = np.arange(len(co))

    def find(x):
        r = x
        while parent[r] != r:
            r = parent[r]
        while parent[x] != r:
            parent[x], x = r, parent[x]
        return r
    for a, b, c in F:
        ra, rb, rc = find(a), find(b), find(c)
        parent[rb] = ra; parent[find(rc)] = ra
    roots = np.array([find(i) for i in range(len(co))])
    tri_root = roots[F[:, 0]]
    return [np.where(tri_root == r)[0] for r in np.unique(tri_root)]


class Unit:
    def __init__(self, name, co, F):
        used = np.unique(F)
        self.name = name
        self.co = co; self.F = F
        self.lo = co[used].min(0); self.hi = co[used].max(0)
        cen = co[F].mean(1)
        pts = np.concatenate([co[used], cen])
        if len(pts) > 6000:
            pts = pts[:: int(math.ceil(len(pts) / 6000))]
        self.pts = pts
        self._bvh = None

    @property
    def bvh(self):
        if self._bvh is None:
            self._bvh = bvh_of(self.co, self.F)
        return self._bvh


def touching(a, b, tol=0.02):
    if np.any(a.lo - tol > b.hi) or np.any(b.lo - tol > a.hi):
        return False
    for u, v in ((a, b), (b, a)):
        sel = np.all((u.pts >= v.lo - tol) & (u.pts <= v.hi + tol), axis=1)
        for p in u.pts[sel]:
            if v.bvh.find_nearest(Vector(p), tol)[0] is not None:
                return True
    return len(a.bvh.overlap(b.bvh)) > 0


def inside(bvh, p, lo, hi):
    if np.any(p < lo) or np.any(p > hi):
        return False
    d = Vector((0.5773, 0.5774, 0.5775)).normalized()
    o = Vector(p); n = 0
    for _ in range(64):
        hit = bvh.ray_cast(o, d)
        if hit[0] is None:
            break
        n += 1; o = hit[0] + d * 1e-5
    return n % 2 == 1


def penetration(A, B):
    """Max depth of vertices of unit A inside closed unit B (and vice versa)."""
    best = (0.0, None)
    for u, v in ((A, B), (B, A)):
        sel = np.all((u.pts >= v.lo) & (u.pts <= v.hi), axis=1)
        for p in u.pts[sel]:
            if inside(v.bvh, p, v.lo, v.hi):
                d = v.bvh.find_nearest(Vector(p))[3]
                if d > best[0]:
                    best = (d, (u.name, v.name, tuple(np.round(p, 3))))
    return best


PF = {}          # key pre-flight numbers, written to out/preflight.json (facts for the critic pack)


def seam_numbers(out_dir):
    from PIL import Image
    res = []
    for cname in STATES['seamref'][3]:
        a_p = os.path.join(out_dir, 'reference_uncut__%s.png' % cname); b_p = os.path.join(out_dir, 'intact__%s.png' % cname)
        if not (os.path.exists(a_p) and os.path.exists(b_p)):
            continue
        a = np.asarray(Image.open(a_p).convert('RGB')).astype(int); b = np.asarray(Image.open(b_p).convert('RGB')).astype(int)
        if a.shape == b.shape:
            d = np.abs(a - b).max(axis=2)
            res.append((cname, int(d.max()), float(d.mean()), int((d > 12).sum())))
    return res


def seam_section(out_dir):
    rows = ['| %s | %d | %.3f | %d |' % x for x in seam_numbers(out_dir)]
    if not rows:
        return ''
    return ('\n## 7. Seam check in pixels: intact (cut pieces) vs the uncut original, same camera, same samples\n\n'
            '| camera | max channel diff (0-255) | mean | pixels > 12 |\n|---|---|---|---|\n' + '\n'.join(rows) + '\n'
            '\nFiles: out/intact__<Cam>.png vs out/reference_uncut__<Cam>.png. Same seed and settings; a visible seam would show as '
            'a line of large differences. Small values come from the re-triangulated pieces (float noise), not from a gap.\n')


def put_seam_section(pf_path, out_dir):
    if not os.path.exists(pf_path):
        return
    txt = open(pf_path).read()
    i = txt.find('\n## 7. Seam check')
    if i >= 0:
        txt = txt[:i] + '\n'
    sec = seam_section(out_dir)
    with open(pf_path, 'w') as f:
        f.write(txt.rstrip('\n') + '\n' + sec)


def preflight(B, path):
    L = []
    w = L.append
    t0 = time.time()
    PF.clear()
    PF['spec'] = SPEC['version']; PF['counts'] = {h: len(v) for h, v in B.half.items()}
    PF['groups_imported'] = len(B.objs)
    w('# T1 pre-flight (mission 260929-train-splits)\n')
    w('Generated by src/render/build.py on %s from break_spec.json v%s. Units: studs; world = Roblox coords; B = break frame of the carriage.\n' % (
        time.strftime('%Y-%m-%d %H:%M'), SPEC['version']))
    for k, lab in ((1, 'break 1 (+X)'), (2, 'break 2 (-X)')):
        for bi, (objs, fk, pr) in enumerate(B.bodies(k)):
            w('Topple used, %s body %d: rest roll %.2f lift %.2f, bounce to %.2f and back over %.2f s, roll time %.2f after delay %.2f, '
              'yaw %+.0f (mirrored with side), sink %.2f, extra back %.2f.' % (lab, bi + 1, pr['roll'], pr['lift'], pr['lo'], pr['bounce_time'],
                                                                                pr['roll_time'], pr['delay'], pr['yaw'], pr['sink'], pr['extra_back']))
    w('\nPivot X +-%s Y %s (B); gangway %s -> %s. Object counts after the cut: %s.\n' % (
        PIVOT_X, PIVOT_Y, GANGWAY, GANGWAY_HALF, ', '.join('%s %d' % (h, len(v)) for h, v in B.half.items())))
    # 1 volumes + paths
    w('## 1. Cut crossers: boolean path and volume(front)+volume(rear) vs original (limit 0.5 %)\n')
    w('| carriage | crosser | weld: degenerate / non-manifold edges / fin pairs | path | caps F/R (tris) | V orig | V front | V rear | off % | ok |')
    w('|---|---|---|---|---|---|---|---|---|---|')
    worst = 0.0
    for r in B.piece_info:
        rep = r['rep']
        off = 100.0 * (r['v_front'] + r['v_rear'] - r['v_orig']) / abs(r['v_orig'])
        worst = max(worst, abs(off))
        caps = r.get('caps', r.get('n_pieces'))
        caps_s = ('%d boxes / %d boxes' % caps) if r['path'].startswith('block') else '%d / %d' % caps
        w('| C%d | %s | %d / %d / %d | %s | %s | %.3f | %.3f | %.3f | %+.4f | %s |' % (
            r['k'], r['name'], rep['degenerate'], rep['nonmanifold'], rep['fins'], r['path'], caps_s, r['v_orig'],
            r['v_front'], r['v_rear'], off, 'PASS' if abs(off) <= 0.5 else 'FAIL'))
        PF.setdefault('crossers', []).append(dict(k=r['k'], name=r['name'], path=r['path'], caps=caps_s, v_orig=r['v_orig'],
                                                  off_pct=off, nonmanifold=rep['nonmanifold'], fins=rep['fins'],
                                                  degenerate=rep['degenerate'], m3_import=r.get('m3_import', '')))
    fb = [r for r in B.piece_info if 'fallback_reason' in r]
    w('\nFallback (not watertight after weld -> per-cell clipping): %s.' % (', '.join('%s (%s; %s)' % (r['name'], r['fallback_reason'], r.get('m3_import', '')) for r in fb) or 'none'))
    if fb and B.args.fallback_caps == 'on':
        w('Fallback pieces were capped with exact cross-sections of the original mesh (open cross-section chains: %s); '
          'with --fallback-caps off they stay open (the order\'s literal fallback).' % ', '.join('%s %d' % (r['name'], r.get('open_chains', 0)) for r in fb))
    w('Worst volume deviation: %.4f %%.\n' % worst)
    PF['vol_worst_pct'] = worst

    # per piece meshes (Roblox coords), cap flags
    piece_mesh = {}
    for name, pc in B.pieces.items():
        for tag in ('F', 'R'):
            for ob in pc[tag]:
                co, F = obj_world_tris(ob)
                piece_mesh[ob.name] = (co, F, B.cap_flags[ob.name])

    # 2 slivers
    w('## 2. Thinnest sliver created by the cut (flag < 0.05)\n')
    w('Material thickness behind every cut face: rays go inward from the centroid + 3 inset points of each cap triangle (area > 1e-4) '
      'to the next surface of the same piece. A hit face within 15 deg of parallel to the cut is a true sliver; a hit face tilted more '
      'than 15 deg is curved-surface feathering (thin wedge where a slanted or curved face runs into the cut), reported separately. '
      'Sliced Blocks: sub-box width/length.\n')
    w('| crosser | true sliver min F / R | feathering min F / R | flag |')
    w('|---|---|---|---|')
    COS15 = math.cos(math.radians(15))
    worst_sl = (9e9, None); worst_fe = (9e9, None)
    planes = {'sliver': {}, 'feather': {}}
    for name, pc in B.pieces.items():
        sl = []; fe = []
        for tag in ('F', 'R'):
            mn_s = 9e9; mn_f = 9e9
            for ob in pc[tag]:
                co, F, flags = piece_mesh[ob.name]
                if len(flags) != len(F) or not flags.any():
                    continue
                if name in BLOCKS:                   # sliced boxes: X width and Z length come from the cut
                    ext = co.max(0) - co.min(0); mn_s = min(mn_s, float(ext[0]), float(ext[2])); continue
                bvh = bvh_of(co, F)
                T = co[F[flags]]
                n, area = tri_normals(T)
                keep = area > 1e-4
                T, n = T[keep], n[keep]
                cen = T.mean(1)
                for i in range(len(T)):
                    for p in [cen[i]] + [0.8 * T[i, j] + 0.2 * cen[i] for j in range(3)]:
                        hit = bvh.ray_cast(Vector(p - n[i] * 1e-4), Vector(-n[i]), 50.0)
                        if hit[0] is None:
                            continue
                        th = hit[3] + 1e-4
                        kind = 'sliver' if abs(Vector(hit[1]).dot(Vector(n[i]))) >= COS15 else 'feather'
                        if kind == 'sliver':
                            mn_s = min(mn_s, th)
                        else:
                            mn_f = min(mn_f, th)
                        if th < 0.05:
                            ax = int(np.argmax(np.abs(n[i])))
                            cb = p - ORIGIN[pc['k']]
                            key = '%s = %+.2f' % ('XYZ'[ax], round(float(cb[ax]), 2))
                            e = planes[kind].setdefault(key, [9e9, set(), None, 0])
                            e[3] += 1
                            if th < e[0]:
                                e[0] = th; e[2] = tuple(np.round(cb, 2))
                            e[1].add(name)
            sl.append(mn_s); fe.append(mn_f)
            if mn_s < worst_sl[0]: worst_sl = (mn_s, '%s.%s' % (name, tag))
            if mn_f < worst_fe[0]: worst_fe = (mn_f, '%s.%s' % (name, tag))
        fmt = lambda v: ('%.3f' % v) if v < 9e8 else '-'
        w('| %s | %s / %s | %s / %s | %s |' % (name, fmt(sl[0]), fmt(sl[1]), fmt(fe[0]), fmt(fe[1]), 'SLIVER' if min(sl) < 0.05 else 'ok'))
    n_sl = sum(v[3] for v in planes['sliver'].values())
    w('\nTrue slivers under 0.05: %d samples on %d cutter planes; thinnest true sliver %.3f (%s). Feathering under 0.05: %d samples on %d planes; thinnest %.3f (%s).\n' % (
        n_sl, len(planes['sliver']), worst_sl[0], worst_sl[1], sum(v[3] for v in planes['feather'].values()), len(planes['feather']), worst_fe[0], worst_fe[1]))
    PF['slivers'] = dict(true_count=n_sl, true_min=worst_sl, feather_count=sum(v[3] for v in planes['feather'].values()), feather_min=worst_fe,
                         feather_planes=[(kk, v[0], v[3], sorted(v[1])) for kk, v in sorted(planes['feather'].items(), key=lambda x: x[1][0])],
                         true_planes=[(kk, v[0], v[3], sorted(v[1])) for kk, v in sorted(planes['sliver'].items(), key=lambda x: x[1][0])])
    for kind, title in (('sliver', 'True slivers < 0.05'), ('feather', 'Feathering < 0.05 (acceptable per coordinator, listed for the record)')):
        if planes[kind]:
            w('%s:\n' % title)
            w('| cutter plane (B) | thinnest | samples | at (B) | crossers |')
            w('|---|---|---|---|---|')
            for key, (th, names, at, cnt) in sorted(planes[kind].items(), key=lambda x: x[1][0]):
                w('| %s | %.3f | %d | %s | %s |' % (key, th, cnt, at, ', '.join(sorted(names))))
            w('')

    # 3 floaters
    w('## 3. Kept-half pieces touch other geometry (no floaters after the cut; contact tol 0.02)\n')
    for k in (1, 2):
        kept = B.kept(k)
        zb = ORIGIN[k][2]
        units = []
        for o in kept:
            co, F = obj_world_tris(o)
            if o.name in piece_mesh:
                for ci, idx in enumerate(components(co, F)):
                    units.append(Unit('%s#%d' % (o.name, ci), co, F[idx]))
            else:
                units.append(Unit(o.name, co, F))
        lost = [o for objs, _, _ in B.bodies(k) for o in objs]
        lost_units = [Unit(o.name, *obj_world_tris(o)) for o in lost if B.bbox_of(o)[0][2] < zb + D_HI + 2]
        zone = [u for u in units if (u.hi[2] >= zb + D_LO - 1.5 and u.lo[2] <= zb + D_HI + 1.5) or u.name.split('#')[0] in piece_mesh]
        zone = [u for u in zone if u.hi[2] >= zb + D_LO - 1.5]          # pieces far from this break do not count
        bad, pre = [], []
        for u in zone:
            if any(touching(u, v) for v in units if v is not u):
                continue
            if any(touching(u, v) for v in lost_units):
                bad.append(u.name)
            else:
                pre.append(u.name)
        PF.setdefault('floaters', {})[k] = dict(kept=len(kept), checked=len(zone), created=bad, preexisting=pre)
        w('- Break %d: kept set %d objects -> %d units near the tear checked; floaters created by the cut: %s; isolated already in the intact model: %s.' % (
            k, len(kept), len(zone), (', '.join(bad) if bad else 'none'), (', '.join(pre) if pre else 'none')))
    w('')

    # 4 wreck at rest
    w('## 4. Wreck at rest (t = 4.0)\n')
    w('Lowest points after the pose, split by where the vertex sits on the carriage at rest (B frame): bogie side = lower half (Y < 4, '
      'bogies, underframe, floor), roof side = upper half (Y >= 4, upper walls, roof eave). Resting on bogie edge + roof eave = both '
      'lowest points within [ground - sink - 0.05, ground + 0.05] (ground y %.2f).\n' % RAIL_Y)
    names = {(1, 0): 'C1.Rear', (1, 1): 'C2 incl. gangway' if GANGWAY_HALF.startswith('C2') else 'C2', (2, 0): 'C2.Rear'}
    for k in (1, 2):
        mats, desc = B.pose_matrices('break%d_t4.0' % k)
        for bi, (objs, fk, prof) in enumerate(B.bodies(k)):
            Mb = mats[objs[0].name]
            low_all = (9e9, None); low_bog = (9e9, None); low_roof = (9e9, None)
            for o in objs:
                co_r, F = obj_world_tris(o)
                yb = co_r[:, 1] - ORIGIN[fk][1]
                co = co_r @ Mb[:3, :3].T + Mb[:3, 3]
                y = co[:, 1]
                i = int(np.argmin(y))
                if y[i] < low_all[0]: low_all = (float(y[i]), o.name)
                m = yb < 4.0
                if m.any():
                    j = int(np.argmin(np.where(m, y, 9e9)))
                    if y[j] < low_bog[0]: low_bog = (float(y[j]), o.name)
                m = yb >= 4.0
                if m.any():
                    j = int(np.argmin(np.where(m, y, 9e9)))
                    if y[j] < low_roof[0]: low_roof = (float(y[j]), o.name)
            lo_lim = RAIL_Y - prof['sink'] - 0.05; hi_lim = RAIL_Y + 0.05
            ok = lambda v: 'PASS' if lo_lim <= v <= hi_lim else ('FAIL (sunk %.2f)' % (RAIL_Y - v) if v < lo_lim else 'FAIL (hangs %.2f)' % (v - RAIL_Y))
            PF.setdefault('rest', []).append(dict(k=k, body=bi + 1, name=names[(k, bi)], pose=desc[bi + 1], lowest=low_all[0], lowest_part=low_all[1],
                                                  limit=lo_lim, bogie=low_bog[0], bogie_part=low_bog[1], roof=low_roof[0], roof_part=low_roof[1],
                                                  sink=prof['sink'], ok=bool(low_all[0] >= lo_lim and lo_lim <= low_bog[0] <= hi_lim and lo_lim <= low_roof[0] <= hi_lim)))
            w('- Break %d body %d (%s; %s): lowest point y %.3f (%s) vs limit %.3f -> %s. Bogie side y %.3f (%s) -> %s; roof side y %.3f (%s) -> %s.' % (
                k, bi + 1, names[(k, bi)], desc[bi + 1], low_all[0], low_all[1], lo_lim, 'PASS' if low_all[0] >= lo_lim else 'FAIL',
                low_bog[0], low_bog[1], ok(low_bog[0]), low_roof[0], low_roof[1], ok(low_roof[0])))
    # interpenetration break 1 bodies
    mats, _ = B.pose_matrices('break1_t4.0')
    b1 = B.bodies(1)[0][0]; b2 = B.bodies(1)[1][0]

    def units_of(objs, pose):
        out = []
        for o in objs:
            Mw = pose.get(o.name) if pose is not None else None
            co, F = mesh_world(o, Mw)
            out.append(Unit(o.name, co, F))
        return out
    worst = {}
    for label, pose in (('t=4.0', mats), ('intact', None)):
        U1 = [u for u in units_of(b1, pose)]; U2 = [u for u in units_of(b2, pose)]
        lo2 = np.min([u.lo for u in U2], 0); hi2 = np.max([u.hi for u in U2], 0)
        U1 = [u for u in U1 if np.all(u.hi >= lo2 - 0.1) and np.all(u.lo <= hi2 + 0.1)]
        res = []
        for a in U1:
            for b in U2:
                if np.any(a.lo > b.hi) or np.any(b.lo > a.hi):
                    continue
                if not a.bvh.overlap(b.bvh):
                    continue
                d, where = penetration(a, b)
                res.append((d, a.name, b.name, where))
        res.sort(key=lambda x: -x[0])
        worst[label] = res
    r4 = worst['t=4.0']; r0 = worst['intact']
    PF['penetration'] = dict(t4=r4[0][0] if r4 else 0.0, pair=(r4[0][1], r4[0][2]) if r4 else None, pairs=len(r4),
                             intact=r0[0][0] if r0 else 0.0, intact_pair=(r0[0][1], r0[0][2]) if r0 else None)
    w('- Break 1 bodies (C1.Rear vs C2%s) at t = 4.0: %d intersecting part pairs; max depth %.3f%s -> %s.' % (
        ' incl. gangway' if GANGWAY_HALF.startswith('C2') else '',
        len(r4), r4[0][0] if r4 else 0.0, (' (%s in %s)' % (r4[0][1], r4[0][2])) if r4 else '', 'PASS' if (not r4 or r4[0][0] <= 0.3) else 'FAIL'))
    if r4:
        w('  Pairs: ' + '; '.join('%s/%s %.3f' % (x[1], x[2], x[0]) for x in r4[:8]))
    w('  Same part pairs in the intact model: %d intersecting, max depth %.3f%s.' % (
        len(r0), r0[0][0] if r0 else 0.0, (' (%s in %s)' % (r0[0][1], r0[0][2])) if r0 else ''))
    for k in (1, 2):
        mats, _ = B.pose_matrices('break%d_t4.0' % k)
        lo_l = min(float(mesh_world(o, mats[o.name])[0][:, 2].min()) for objs, _, _ in B.bodies(k) for o in objs)
        hi_k = max(float(B.bbox_of(o)[1][2]) for o in B.kept(k))
        w('- Break %d wreck vs kept train at t = 4.0: nearest z gap %.2f studs (no contact possible).' % (k, lo_l - hi_k))
    w('')

    # 5 intact gaps
    w('## 5. Intact state: the two pieces of each crosser meet with no gap\n')
    w('Max distance from every cut-face vertex of one piece to the other piece\'s cut faces (both directions; BVH in float32, '
      'so 0 means below ~1e-5).\n')
    w('| crosser | max gap |')
    w('|---|---|')
    gmax = 0.0
    for name, pc in B.pieces.items():
        caps = {}
        for tag in ('F', 'R'):
            cos, Fs = [], []; off = 0
            for ob in pc[tag]:
                co, F, flags = piece_mesh[ob.name]
                if len(flags) != len(F) or not flags.any():
                    continue
                cos.append(co); Fs.append(F[flags] + off); off += len(co)
            caps[tag] = (np.concatenate(cos), np.concatenate(Fs)) if cos else None
        if not caps['F'] or not caps['R']:
            w('| %s | no cut faces |' % name); continue
        m = 0.0
        for a, b in (('F', 'R'), ('R', 'F')):
            coa, Fa = caps[a]; cob, Fb = caps[b]
            tb = bvh_of(cob, Fb)
            for p in coa[np.unique(Fa)]:
                d = tb.find_nearest(Vector(p))[3]
                m = max(m, d)
        gmax = max(gmax, m)
        w('| %s | %.2e |' % (name, m))
    w('\nLargest gap: %.2e studs.\n' % gmax)
    PF['gap_max'] = gmax

    # 6 tear clearance for everything else
    w('## 6. Non-crosser groups cut by the tear surface (should be none)\n')
    hits = []
    for k in (1, 2):
        for h in ('C%dF' % k, 'C%dR' % k):
            for o in B.half[h]:
                if o.name in piece_mesh:
                    continue
                lo, hi = B.bbox_of(o)
                zb = ORIGIN[k][2]
                if hi[2] < zb + D_LO or lo[2] > zb + D_HI:
                    continue
                co, _ = obj_world_tris(o)
                Pb = co - ORIGIN[k]
                dd = np.full(len(Pb), np.nan)
                for (x0, x1, y0, y1, d) in CELLS:
                    m_ = (Pb[:, 0] >= x0) & (Pb[:, 0] < x1) & (Pb[:, 1] >= y0) & (Pb[:, 1] < y1)
                    dd[m_] = d
                fr = Pb[:, 2] < dd; rr = Pb[:, 2] > dd
                if fr.any() and rr.any():
                    hits.append('%s (%s)' % (o.name, h))
    w('- %s\n' % (', '.join(hits) if hits else 'none'))
    PF['tear_hits'] = hits
    w('_pre-flight computed in %.0f s_\n' % (time.time() - t0))
    with open(path, 'w') as f:
        f.write('\n'.join(L) + '\n')
    put_seam_section(path, os.path.dirname(path))
    with open(os.path.splitext(path)[0] + '.json', 'w') as f:
        json.dump(PF, f, indent=1, default=str)
    print('[preflight] written %s (%.0fs)' % (path, time.time() - t0), flush=True)
    return L


# ---------------------------------------------------------------- critic evidence pack
PACK_BAND = [('break1 t4.0 POV inside (player view)', 'break1_t4.0__Cam_POV_In.png', (640, 360)),
             ('break1 t4.0 roof 3rd person (player view)', 'break1_t4.0__Cam_Roof3P.png', (640, 360)),
             ('break1 t4.0 game distance 400x225', 'break1_t4.0__Cam_Game.png', None)]
PACK_GRID = [('intact seam out', 'intact__Cam_SeamOut.png'), ('intact roof', 'intact__Cam_SeamRoof.png'),
             ('exploded', 'exploded__Cam_Exploded.png'), ('b1 t1.0 wide', 'break1_t1.0__Cam_Wide.png'),
             ('b1 t4.0 hero', 'break1_t4.0__Cam_Hero.png'), ('b1 t4.0 wide', 'break1_t4.0__Cam_Wide.png'),
             ('b1 t4.0 side', 'break1_t4.0__Cam_Side.png'), ('b2 t4.0 hero', 'break2_t4.0__Cam_Hero.png')]


def cam_project(cname, k, t, pts):
    """Pixel coords of B-frame points in a camera of CAMS/CAM_AT (same maths as the Blender camera: vertical FOV, Y up)."""
    loc, look, fov, ortho, (W, H) = CAM_AT.get((cname, t), CAMS[cname])
    L = ORIGIN[k] + np.array(loc, float); A = ORIGIN[k] + np.array(look, float)
    f = (A - L) / np.linalg.norm(A - L)
    rg = np.cross(f, [0.0, 1.0, 0.0]); rg /= np.linalg.norm(rg); up = np.cross(rg, f)
    P = ORIGIN[k] + np.asarray(pts, float) - L
    zf, xr, yu = P @ f, P @ rg, P @ up
    if ortho:
        sc = W / ortho
        return np.stack([W / 2 + xr * sc, H / 2 - yu * sc], 1), (W, H)
    fp = (H / 2) / math.tan(math.radians(fov) / 2)
    return np.stack([W / 2 + fp * xr / zf, H / 2 - fp * yu / zf], 1), (W, H)


def crop_box(pix, size, WH):
    cx, cy = (pix[:, 0].min() + pix[:, 0].max()) / 2, (pix[:, 1].min() + pix[:, 1].max()) / 2
    w, h = size
    x0 = int(round(min(max(cx - w / 2, 0), WH[0] - w))); y0 = int(round(min(max(cy - h / 2, 0), WH[1] - h)))
    return (x0, y0, x0 + w, y0 + h)


def run_sheet(out, items, tile):
    cmd = [sys.executable, SHEET_TOOL, out] + items + ['--tile', '%dx%d' % tile]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def critic_pack(out_dir, pack):
    import shutil
    from PIL import Image
    os.makedirs(pack, exist_ok=True)
    if not PF and os.path.exists(os.path.join(out_dir, 'preflight.json')):
        PF.update(json.load(open(os.path.join(out_dir, 'preflight.json'))))
    srcs = sorted({p for _, p, _ in PACK_BAND} | {p for _, p in PACK_GRID} | {'intact__Cam_SeamIn.png', 'reference_uncut__Cam_SeamIn.png',
                                                                         'reference_uncut__Cam_SeamOut.png', 'intact__Cam_SeamRoof_debug.png'})
    for p in srcs:
        shutil.copy2(os.path.join(out_dir, p), os.path.join(pack, p))
    band = []
    for lab, p, size in PACK_BAND:
        if size:
            q = 'band_%s_%dx%d.png' % (os.path.splitext(p)[0], size[0], size[1])
            Image.open(os.path.join(pack, p)).convert('RGB').resize(size, Image.LANCZOS).save(os.path.join(pack, q))
        else:
            q = p
        band.append('%s=%s@1' % (lab, os.path.join(pack, q)))
    grid = ['%s=%s' % (lab, os.path.join(pack, p)) for lab, p in PACK_GRID]
    used_tile = None
    for tw in (400, 384, 368, 352, 336, 320, 304, 288, 272, 256, 240, 224, 208, 192, 176):
        tile = (tw, int(round(tw * 9 / 16)))
        rc, msg = run_sheet(os.path.join(pack, 'contact.png'), band + grid, tile)
        if rc == 0:
            used_tile = tile; print('[pack] contact.png tile %dx%d: %s' % (tile[0], tile[1], msg.splitlines()[0]), flush=True); break
    # 1:1 crops of the seam (intact, inside) and the torn end (break 1, t = 4.0, hero)
    crops = []
    seam = [(-8.8, y, c[4]) for c in CELLS if c[1] <= -7.1 and c[2] >= 0.6 - 1e-9 and c[3] <= 11.18 + 1e-9 for y in (c[2], c[3])]
    pix, WH = cam_project('Cam_SeamIn', 1, None, seam)
    torn = [(x, y, z) for x in (-9.74, 9.74) for y in (-0.5, 14.05) for z in (D_LO, D_HI)]
    pix2, WH2 = cam_project('Cam_Hero', 1, 4.0, torn)
    for lab, src, px, wh in (('intact inside, seam at the tear line (1:1 crop)', 'intact__Cam_SeamIn.png', pix, WH),
                             ('break1 t4.0 hero, torn end of the kept half (1:1 crop)', 'break1_t4.0__Cam_Hero.png', pix2, WH2)):
        box = crop_box(px, (620, 700), wh)
        q = 'crop_%s_%d_%d_%d_%d.png' % (os.path.splitext(src)[0], *box)
        Image.open(os.path.join(pack, src)).convert('RGB').crop(box).save(os.path.join(pack, q))
        crops.append((lab, src, box, q))
    rc, msg = run_sheet(os.path.join(pack, 'closeups.png'), ['%s=%s@1' % (lab, os.path.join(pack, q)) for lab, _, _, q in crops], (400, 225))
    print('[pack] closeups.png rc=%d %s' % (rc, msg.splitlines()[0] if msg else ''), flush=True)
    write_facts(out_dir, pack, used_tile, crops)


def write_facts(out_dir, pack, tile, crops):
    poses = {}
    lp = os.path.join(out_dir, 'render_log.md')
    if os.path.exists(lp):
        for l in open(lp).read().split('\n'):
            c = [x.strip() for x in l.split('|')]
            if len(c) == 6 and c[1] not in ('state', '---'):
                poses[c[1]] = c[4]
    sl = PF.get('slivers', {}); pen = PF.get('penetration', {}); counts = PF.get('counts', {})
    sm = seam_numbers(out_dir)
    L = []
    w = L.append
    w('# Critic pass 1: 3D look of the torn carriages (T1, mission 260929-train-splits)\n')
    w('Question for the critic: does each split look really good and accurate (R3; acceptance A1-A7, bar 8)? '
      'Geometry, cut and topple come from break_spec.json v%s via src/render/build.py; numbers below are from '
      'src/render/out/preflight.md (%s).\n' % (PF.get('spec', '?'), time.strftime('%Y-%m-%d %H:%M')))
    w('## Images in this folder\n')
    w('- contact.png: top band at true size = the player views: break 1 t=4.0 Cam_POV_In and Cam_Roof3P (1600x900 renders scaled to 640x360) '
      'and Cam_Game (rendered at 400x225). Grid below (fitted %s tiles): %s. contact.json maps every tile to its file.' % (
          '%dx%d' % tile if tile else '?', ', '.join(lab for lab, _ in PACK_GRID)))
    w('- closeups.png: 1:1 crops, no scaling: ' + '; '.join('%s = %s box %s' % (lab, src, list(box)) for lab, src, box, _ in crops) + '.')
    w('- Full-resolution sources (1600x900, Cam_Game 400x225) are copied here as <state>__<camera>.png; also intact__Cam_SeamRoof_debug.png '
      '(tear line drawn in red on the roof) and reference_uncut__Cam_SeamIn/SeamOut.png (the same cameras on the uncut original).\n')
    w('## States and poses\n')
    w('| state | what it shows | pose (drift along +Z; per lost body roll / yaw / sink / lift / extra back) |')
    w('|---|---|---|')
    what = {'intact': 'all halves in place, seam must be invisible', 'exploded': 'C1 front half -3, everything behind +3 along Z (design view)',
            'break1_t0.3': 'break 1 just after the snap', 'break1_t1.0': 'C1 rear half rolling, C2 starting',
            'break1_t1.6': 'C1 rear half bouncing on its side, C2 rolling', 'break1_t4.0': 'break 1 at rest, wreck ~90 studs behind',
            'break2_t1.2': 'break 2, C2 rear half rolling toward -X', 'break2_t4.0': 'break 2 at rest'}
    for st in ('intact', 'exploded', 'break1_t0.3', 'break1_t1.0', 'break1_t1.6', 'break1_t4.0', 'break2_t1.2', 'break2_t4.0'):
        w('| %s | %s | %s |' % (st, what[st], poses.get(st, '') or '-'))
    w('\nBreak 1 falls toward +X, break 2 toward -X (the game picks the side at random). Lost sets: break 1 = C1.Rear (body 1) + all of C2 '
      '(body 2, incl. the gangway); break 2 = C2.Rear. Motion: recoil 0.8 in 0.2 s, brake 12 studs/s^2 from 35 studs/s, then static on the terrain.\n')
    w('## Pre-flight numbers\n')
    w('- Cut accuracy: front+rear volume vs original, worst %.4f %% over 20 crossers (limit 0.5 %%); intact cut faces meet with gap %.1e '
      '(0 = below float32 resolution); seam pixels vs the uncut original: %s.' % (
          PF.get('vol_worst_pct', float('nan')), PF.get('gap_max', float('nan')),
          '; '.join('%s max %d/255, %d px > 12' % (c, mx, n) for c, mx, _, n in sm) or 'n/a'))
    w('- Slivers: true slivers (faces within 15 deg of parallel to a cut) under 0.05: %s; thinnest true sliver %.3f (%s). '
      'Feathering (slanted faces running into a cut) under 0.05: %s samples, thinnest %.3f, on %s.' % (
          sl.get('true_count'), sl.get('true_min', [0, ''])[0], sl.get('true_min', [0, ''])[1], sl.get('feather_count'),
          sl.get('feather_min', [0, ''])[0], ', '.join('%s (%.3f, %s)' % (kk, th, '/'.join(n)) for kk, th, _, n in sl.get('feather_planes', [])) or 'none'))
    fl = PF.get('floaters', {})
    w('- Floaters after the cut: ' + '; '.join('break %s: %s of %s pieces near the tear float' % (k, len(v['created']), v['checked']) for k, v in fl.items()) + '.')
    for r in PF.get('rest', []):
        w('- Wreck at rest, break %d body %d (%s): lowest y %.3f vs limit %.3f; bogie side %.3f, roof side %.3f (ground 5.33, sink %.2f) -> %s.' % (
            r['k'], r['body'], r['name'], r['lowest'], r['limit'], r['bogie'], r['roof'], r['sink'], 'PASS' if r['ok'] else 'FAIL'))
    w('- Wreck bodies at rest (break 1, C1.Rear vs C2): max interpenetration %.3f (%s), limit 0.3, target < 0.1; intact model %.3f.' % (
        pen.get('t4', float('nan')), '/'.join(pen['pair']) if pen.get('pair') else 'no intersecting parts', pen.get('intact', float('nan'))))
    w('- Other groups crossing the tear surface: %s.\n' % (', '.join(PF.get('tear_hits', [])) or 'none'))
    w('## Parts\n')
    w('- %s OBJ groups imported (Studio export temp2.obj); 20 crossers cut (10 per carriage); every other group goes whole to one half by '
      'its bbox centre; the gangway Union22 belongs to C2.FrontHalf.' % PF.get('groups_imported', '?'))
    w('- Objects per half after the cut (whole parts + cut pieces): ' + ', '.join('%s %d' % kv for kv in counts.items()) + '.\n')
    w('## Cut method per crosser\n')
    w('| carriage | crosser | method | cut faces F / R | volume off % | note |')
    w('|---|---|---|---|---|---|')
    for c in PF.get('crossers', []):
        note = ''
        if c['nonmanifold'] or c['fins']:
            note = 'not watertight after weld (%d non-manifold edges, %d fin pairs); %s' % (c['nonmanifold'], c['fins'], c['m3_import'])
        elif c['degenerate']:
            note = '%d zero-area triangles dropped at weld' % c['degenerate']
        w('| C%d | %s | %s | %s | %+.4f | %s |' % (c['k'], c['name'], c['path'], c['caps'], c['off_pct'], note))
    w('\nmanifold3d = mesh minus the per-cell cutter boxes (cap faces from the cutter, crosser material). block sliced per cell = the plain '
      'Block intersected with each cell box (separate sub-blocks, as Studio will slice it). clip+caps = fallback for non-watertight unions: '
      'triangles clipped per cell, caps built from the exact cross-section of the original mesh (the order\'s literal fallback has no caps).\n')
    w('## Render limits (by design, do not score them as defects of the split)\n')
    w('- No fx, smoke, sparks, debris, glass shards or sound in these renders: the explosion, torn-edge smoke and topple dust are T3, sounds T4.')
    w('- Cycles preview materials approximate Roblox: texture x part colour, roughness 0.7, normal maps dropped, glass alpha 0.35, AgX view '
      'transform, sun and sky from scene.py. Roblox lighting, materials and LOD will differ.')
    w('- Ground (flat plane at rail level y 5.33), rails, sleepers and ballast are render props, not part of the model; rail heads stand 0.25 '
      'proud, so the wheels sit 0.25 into them.')
    w('- Cycles CPU, 22 samples + OpenImageDenoise, 1600x900 (Cam_Game 400x225). Cameras are in the B frame of the breaking carriage '
      '(intact and exploded use carriage 1); Cam_Side at t=4.0 is widened to centre Z 45, ortho 140.')
    w('- Motion details not fixed by the spec: yaw eases like the roll and turns about the vertical line through the rolled body\'s centre, '
      'mirrored with the side; lift eases in with the roll; extra back eases in over the roll.\n')
    with open(os.path.join(pack, 'facts.md'), 'w') as f:
        f.write('\n'.join(L) + '\n')
    print('[pack] facts.md written', flush=True)


def write_sheet(out_dir, sheet, items, prog_dir):
    paths = [os.path.join(out_dir, p) for _, p in items]
    if not all(os.path.exists(p) for p in paths):
        return False
    cmd = [sys.executable, SHEET_TOOL, os.path.join(prog_dir, sheet)] + ['%s=%s' % (lab, p) for (lab, _), p in zip(items, paths)] + ['--tile', '640x360']
    r = subprocess.run(cmd, capture_output=True, text=True)
    print('[sheet] %s rc=%d %s' % (sheet, r.returncode, (r.stdout + r.stderr).strip()[-200:]), flush=True)
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--states', default=','.join(STATES))
    ap.add_argument('--cams', default='')
    ap.add_argument('--samples', type=int, default=22)
    ap.add_argument('--scale', type=int, default=100, help='resolution percent (tests)')
    ap.add_argument('--out', default=os.path.join(HERE, 'out'))
    ap.add_argument('--progress', default=os.path.join(MISSION, 'progress'))
    ap.add_argument('--fallback-caps', default='on', choices=['on', 'off'])
    ap.add_argument('--no-render', action='store_true')
    ap.add_argument('--no-preflight', action='store_true')
    ap.add_argument('--no-sheets', action='store_true')
    ap.add_argument('--sheets-only', action='store_true', help='rebuild the progress sheets from the PNGs in --out and exit')
    ap.add_argument('--critic-pack', default='', help='after rendering: copy the critic evidence into DIR (contact.png, closeups.png, facts.md)')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    if args.sheets_only:
        for sheet, items in SHEETS.items():
            write_sheet(args.out, sheet, items, args.progress)
        return
    B = Build(args)
    print('[build] scene ready in %.1fs' % (time.time() - B.t0), flush=True)
    pf = os.path.join(args.out, 'preflight.md')
    if not args.no_preflight:
        preflight(B, pf)
    if args.no_render:
        if args.critic_pack:
            critic_pack(args.out, args.critic_pack)
        return
    states = [s for s in args.states.split(',') if s]
    cams_filter = set(c for c in args.cams.split(',') if c)
    log = []
    sheets_done = set()
    # a sheet is written only when none of its images is still waiting to be rendered in this run (no stale mixes)
    pending = set()
    for st in states:
        if st in STATES and st != 'seamref':
            for cname in STATES[st][3]:
                if not cams_filter or cname in cams_filter or cname.replace('_debug', '') in cams_filter:
                    pending.add('%s__%s.png' % (st, cname))
    t_all = time.time()
    for st in states:
        if st == 'seamref':
            B.render_reference(args.samples, args.out, args.scale, log, pf)
            continue
        for rendered in B.render_state(st, cams_filter, args.samples, args.out, args.scale, log):
            pending.discard(os.path.basename(rendered))
            if args.no_sheets:
                continue
            for sheet, items in SHEETS.items():
                names = [p for _, p in items]
                if sheet not in sheets_done and os.path.basename(rendered) in names and not (set(names) & pending):
                    if write_sheet(args.out, sheet, items, args.progress):
                        sheets_done.add(sheet)
    total = time.time() - t_all
    lp = os.path.join(args.out, 'render_log.md')
    rows = {}
    if os.path.exists(lp):                                   # keep entries of earlier partial runs
        for l in open(lp).read().split('\n'):
            c = [x.strip() for x in l.split('|')]
            if len(c) == 6 and c[1] not in ('state', '---') and c[3].replace('.', '').isdigit():
                rows[(c[1], c[2])] = (c[1], c[2], float(c[3]), c[4])
    for x in log:
        rows[(x[0], x[1])] = x
    secs = sum(x[2] for x in rows.values())
    lines = ['## Render log (%d images, %.1f min render time, Cycles CPU %d samples + denoise)\n' % (len(rows), secs / 60, args.samples),
             '| state | camera | seconds | pose |', '|---|---|---|---|']
    lines += ['| %s | %s | %.0f | %s |' % x for x in rows.values()]
    with open(lp, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print('[done] %d renders in %.1f min; sheets %s' % (len(log), total / 60, sorted(sheets_done)), flush=True)
    if args.critic_pack:
        critic_pack(args.out, args.critic_pack)


if __name__ == '__main__':
    main()
