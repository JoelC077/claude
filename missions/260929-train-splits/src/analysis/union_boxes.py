"""Recover an exact axis-aligned box decomposition of one unioned group from the OBJ mesh.
Grid = unique vertex coords per axis; a cell is solid if its centre is inside the closed mesh (ray parity);
cells are then greedily merged into maximal boxes (z runs, then y, then x)."""
import sys, json, numpy as np
sys.path.insert(0, '.')
from objparse import parse, group_vertex_ids

def tri_list(g, V):
    T = []
    for f in g['faces']:
        idx = [(vi - 1) for vi, _, _ in f]
        for k in range(1, len(idx) - 1):
            T.append((V[idx[0]], V[idx[k]], V[idx[k + 1]]))
    return np.array(T)

def inside(p, T, d=np.array([0.5773, 0.5774, 0.5775])):
    # Moller-Trumbore ray-triangle parity, vectorised
    v0, v1, v2 = T[:, 0], T[:, 1], T[:, 2]
    e1, e2 = v1 - v0, v2 - v0
    h = np.cross(d, e2); a = (e1 * h).sum(1)
    ok = np.abs(a) > 1e-12
    f = np.where(ok, 1.0 / np.where(ok, a, 1), 0)
    s = p - v0; u = f * (s * h).sum(1)
    q = np.cross(s, e1); v = f * (q * d).sum(1)
    t = f * (e2 * q).sum(1)
    hit = ok & (u >= 0) & (u <= 1) & (v >= 0) & (u + v <= 1) & (t > 1e-9)
    return hit.sum() % 2 == 1

def boxes_for(name, obj):
    V, VN, VT, G = parse(obj)
    g = next(x for x in G if x['name'] == name)
    T = tri_list(g, V)
    ids = group_vertex_ids(g, len(V)); P = V[ids]
    axes = [np.unique(np.round(P[:, k], 3)) for k in range(3)]
    nx, ny, nz = [len(a) - 1 for a in axes]
    S = np.zeros((nx, ny, nz), bool)
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                c = np.array([(axes[0][i] + axes[0][i + 1]) / 2, (axes[1][j] + axes[1][j + 1]) / 2, (axes[2][k] + axes[2][k + 1]) / 2])
                S[i, j, k] = inside(c, T)
    used = np.zeros_like(S); out = []
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                if not S[i, j, k] or used[i, j, k]: continue
                k2 = k
                while k2 + 1 < nz and S[i, j, k2 + 1] and not used[i, j, k2 + 1]: k2 += 1
                j2 = j
                while j2 + 1 < ny and S[i, j2 + 1, k:k2 + 1].all() and not used[i, j2 + 1, k:k2 + 1].any(): j2 += 1
                i2 = i
                while i2 + 1 < nx and S[i2 + 1, j:j2 + 1, k:k2 + 1].all() and not used[i2 + 1, j:j2 + 1, k:k2 + 1].any(): i2 += 1
                used[i:i2 + 1, j:j2 + 1, k:k2 + 1] = True
                lo = [axes[0][i], axes[1][j], axes[2][k]]; hi = [axes[0][i2 + 1], axes[1][j2 + 1], axes[2][k2 + 1]]
                out.append({'min': [round(float(v), 3) for v in lo], 'max': [round(float(v), 3) for v in hi]})
    return out, axes, len(T)

if __name__ == '__main__':
    name, obj = sys.argv[1], sys.argv[2]
    out, axes, nt = boxes_for(name, obj)
    print(name, 'tris', nt, 'grid', [len(a) for a in axes], 'boxes', len(out))
    for b in sorted(out, key=lambda b: (b['min'][1], b['min'][0], b['min'][2])):
        size = [round(b['max'][k] - b['min'][k], 3) for k in range(3)]
        print('  min', b['min'], 'size', size)
    json.dump(out, open(name + '.boxes.json', 'w'), indent=1)
