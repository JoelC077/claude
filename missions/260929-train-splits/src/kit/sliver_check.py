"""Sliver check for the break cutter: every cutter plane (cell Z=d faces, X and Y step faces) must sit either exactly
on an existing face plane of the crossing geometry or >= MIN_CLEAR away from every parallel vertex plane in the region
it actually cuts. Uses the crossers' OBJ vertices in each carriage's break frame B.
python3 sliver_check.py [--min 0.1]"""
import json, sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'analysis'))
from objparse import parse, group_vertex_ids
OBJ = '/tmp/claude-0/-home-user-claude/7feb16c0-5cf3-5a92-a257-eb9720cba30b/scratchpad/train/temp2.obj'
MIN_CLEAR = float(sys.argv[sys.argv.index('--min') + 1]) if '--min' in sys.argv else 0.1

def load(spec):
    """Triangles (n, 3, 3) of every crosser per carriage, in that carriage's break frame, tagged with the crosser name."""
    V, VN, VT, G = parse(OBJ)
    by = {g['name']: g for g in G}
    tris = {}
    for k in ('1', '2'):
        c = spec['roof_centres_export'][k]
        o = np.array([c[0], c[1] + spec['floor_dy'], c[2] + spec['break_dz']])
        T, names = [], []
        for n in spec['expected_crossers_export'][k]:
            for f in by[n]['faces']:
                idx = [vi - 1 for vi, _, _ in f]
                for q in range(1, len(idx) - 1):
                    T.append(V[[idx[0], idx[q], idx[q + 1]]] - o); names.append(n)
        tris[k] = (np.array(T), np.array(names))
    return tris

def planes(cells):
    """(axis, value, region box lo/hi over the other axes, label) for every cutting face of the cutter."""
    out = []
    for i, c in enumerate(cells):
        out.append(('Z', c['d'], {'X': c['X'], 'Y': c['Y']}, f"cell{i} {c['region']} Z=d"))
    for i, a in enumerate(cells):
        for j, b in enumerate(cells):
            if j <= i or a['d'] == b['d']:
                continue
            zlo, zhi = sorted((a['d'], b['d']))
            # X step: share an X boundary and overlap in Y
            for ax, oth in (('X', 'Y'), ('Y', 'X')):
                for va in a[ax]:
                    if va in b[ax] and ((a[ax][0] == va and b[ax][1] == va) or (a[ax][1] == va and b[ax][0] == va)):
                        lo, hi = max(a[oth][0], b[oth][0]), min(a[oth][1], b[oth][1])
                        if hi > lo:
                            out.append((ax, va, {oth: [lo, hi], 'Z': [zlo, zhi]}, f"step {a['region']}|{b['region']} {ax}={va}"))
    return out

def clearance(TN, ax, val, region, max_tilt=15.0):
    """Nearest face (nearly) parallel to the cut plane inside the region the plane cuts: its distance is the sliver
    thickness. Faces exactly on the plane (< 1e-4) make no sliver; steeper faces feather out and are ignored."""
    T, names = TN
    idx = {'X': 0, 'Y': 1, 'Z': 2}; a = idx[ax]
    lo_t, hi_t = T.min(1), T.max(1)
    m = np.ones(len(T), bool)
    for k, (lo, hi) in region.items():
        m &= (hi_t[:, idx[k]] > lo) & (lo_t[:, idx[k]] < hi)
    if not m.any():
        return None
    Tm = T[m]; nm = names[m]
    nrm = np.cross(Tm[:, 1] - Tm[:, 0], Tm[:, 2] - Tm[:, 0]); L = np.linalg.norm(nrm, axis=1)
    ok = L > 1e-9
    cosang = np.zeros(len(Tm)); cosang[ok] = np.abs(nrm[ok, a]) / L[ok]
    par = cosang >= np.cos(np.radians(max_tilt))
    if not par.any():
        return None
    d = np.abs(Tm[par][:, :, a] - val).min(1)
    keep = d > 1e-4
    if not keep.any():
        return None
    i = np.argmin(np.where(keep, d, 9e9))
    return float(d[i]), str(nm[par][i])

if __name__ == '__main__':
    spec = json.load(open(os.path.join(HERE, 'break_spec.json')))
    tris = load(spec)
    worst = []
    for ax, val, region, label in planes(spec['cells']):
        for k, TN in tris.items():
            c = clearance(TN, ax, val, region)
            if c is not None and c[0] < MIN_CLEAR:
                worst.append((round(c[0], 4), k, c[1], label, region))
    worst.sort(key=lambda w: (w[0], w[1], w[3]))
    print(f"cutter planes checked: {len(planes(spec['cells']))} x 2 carriages; slivers under {MIN_CLEAR}: {len(worst)}")
    for w in worst:
        print('  ', w)
