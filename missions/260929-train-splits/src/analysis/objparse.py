"""Parse a Roblox Studio OBJ export into per-group arrays (stdlib + numpy)."""
import numpy as np, re, json, sys, os

def parse(path):
    V, VN, VT = [], [], []
    groups = []   # dict(name, mtl, faces:list of (vi,ti,ni) tuples)
    cur = None
    mtl = None
    with open(path) as f:
        for line in f:
            if not line or line[0] == '#':
                continue
            t = line.split()
            if not t:
                continue
            k = t[0]
            if k == 'v':
                V.append((float(t[1]), float(t[2]), float(t[3])))
            elif k == 'vn':
                VN.append((float(t[1]), float(t[2]), float(t[3])))
            elif k == 'vt':
                VT.append((float(t[1]), float(t[2])))
            elif k == 'g':
                cur = {'name': ' '.join(t[1:]), 'mtl': None, 'faces': []}
                groups.append(cur)
            elif k == 'usemtl':
                cur['mtl'] = t[1]
            elif k == 'f':
                face = []
                for c in t[1:]:
                    p = c.split('/')
                    vi = int(p[0]); ti = int(p[1]) if len(p) > 1 and p[1] else 0; ni = int(p[2]) if len(p) > 2 and p[2] else 0
                    face.append((vi, ti, ni))
                cur['faces'].append(face)
    V = np.array(V); VN = np.array(VN) if VN else np.zeros((0, 3)); VT = np.array(VT) if VT else np.zeros((0, 2))
    return V, VN, VT, groups

def group_vertex_ids(g, nV):
    ids = set()
    for face in g['faces']:
        for vi, _, _ in face:
            ids.add(vi - 1 if vi > 0 else nV + vi)
    return np.array(sorted(ids))

if __name__ == '__main__':
    V, VN, VT, G = parse(sys.argv[1])
    out = []
    for i, g in enumerate(G):
        ids = group_vertex_ids(g, len(V))
        P = V[ids]
        out.append({'i': i, 'name': g['name'], 'mtl': g['mtl'], 'nf': len(g['faces']), 'nv': len(ids),
                    'min': P.min(0).round(4).tolist(), 'max': P.max(0).round(4).tolist()})
    json.dump(out, open(sys.argv[2], 'w'))
    allmin = V.min(0); allmax = V.max(0)
    print('verts', len(V), 'groups', len(G), 'bbox', allmin.round(2), allmax.round(2), 'size', (allmax - allmin).round(2))
