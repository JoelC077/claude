"""Foundry kit: the primitives a family's build(k, p) calls, plus the geometry checks. Runs inside Blender
(bpy 4.x/5.x); forge.py creates the Kit. Units: 1 Blender unit = 1 stud, z up, origin at ground/rail top.

  k.box(part, group, center, size, rot=(0, 0, 0), detail=0)       one box, pivot at its centre, rot in degrees
  k.boxes(part, group, items, detail=0)                           several boxes as ONE part; items = [(c, s) | (c, s, rot)]
  k.cyl(part, group, center, r, depth, axis="Z", segs=12, r2=None, detail=0)
  k.prism(part, group, profile, depth, center, axis="X", detail=0)  2D profile across `axis`, extruded along it
  k.wall(part, group, axis, a0, a1, at, z0, z1, thick, holes=(), detail=0)
        straight wall along axis "X" (or "Y") from a0 to a1, centred on the plane at `at`, with rectangular
        openings holes = [(centre_along, bottom_z, width, height)]; one part
  k.proxy(center, size, rot=(0, 0, 0))                            collision proxy box (invisible collider in Studio)
  k.measure(label, text)                                          a measured fact for facts.md (openings, gaps)
  k.segs(n)   segment count for this LOD;  k.lod  0 or 1;  k.rng  seeded random.Random;  k.p  params
  arc(width, rise, segs, z0=0)  -> [(u, z)] upper arc for roof profiles;  shell(outer, inner) closes two arcs

detail=1 parts are dropped at LOD1. Part and group names are CamelCase; the object is <Asset>_<Part>_<Group>_<nn>.

Checks (return data and print one line each): names(objs, asset), coplanar(objs), floating(objs), feature_px(cam, objs,
keys, res). Usable from any mission build script: sys.path.insert(0, "<foundry>/scripts"); import fkit.
Run `python3 fkit.py --help` for this text; the module itself needs bpy.
"""
import math, random, re

try:
    import bpy, bmesh
    from mathutils import Matrix, Vector
except ImportError:          # --help without Blender
    bpy = None

NAME = re.compile(r"^[A-Z][A-Za-z0-9]*$")


def _rot_matrix(rot):
    rx, ry, rz = (math.radians(a) for a in rot)
    return Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y") @ Matrix.Rotation(rx, 4, "X")


def arc(width, rise, segs, z0=0.0):
    """Upper arc across `width` rising `rise` above z0: [(u, z)] from -width/2 to +width/2 (segs >= 2)."""
    if rise <= 1e-6:
        return [(-width / 2, z0), (width / 2, z0)]
    half = width / 2
    R = (half * half + rise * rise) / (2 * rise)          # circle through both ends and the crown
    a = math.asin(min(1.0, half / R))
    return [(R * math.sin(t), z0 + rise - R + R * math.cos(t))
            for t in (-a + 2 * a * i / segs for i in range(segs + 1))]


def shell(outer, inner):
    """Closed profile between an outer and an inner arc (both left to right): a curved roof sheet."""
    return list(outer) + list(reversed(inner))


class Kit:
    def __init__(self, asset, cells, material, proxy_material, collection, params, lod=0, seed=1):
        self.asset, self.cells, self.mat, self.pmat = asset, cells, material, proxy_material
        self.coll, self.p, self.lod = collection, params, lod
        self.rng = random.Random(seed)
        self.parts, self.proxies, self.measures, self.dropped = [], [], {}, 0
        self._nn = {}

    # ---------- naming ----------
    def _name(self, part, group):
        if not NAME.match(part) or not NAME.match(group):
            raise ValueError(f"part/group must be CamelCase letters and digits: {part!r}, {group!r}")
        if group not in self.cells:
            raise KeyError(f"group {group!r} is not in the family's GROUPS")
        n = self._nn[(part, group)] = self._nn.get((part, group), 0) + 1
        return f"{self.asset}_{part}_{group}_{n:02d}"

    def segs(self, n):
        return n if self.lod == 0 else max(6, n // 2)

    def _skip(self, detail):
        if self.lod > 0 and detail > 0:
            self.dropped += 1
            return True
        return False

    def _obj(self, name, bm, loc, group=None, proxy=False):
        me = bpy.data.meshes.new(name)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.normal_update()
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        ob.location = loc
        self.coll.objects.link(ob)
        if proxy:
            me.materials.append(self.pmat)
            ob.hide_render = True
            ob["rr_proxy"] = True
            self.proxies.append(ob)
        else:
            me.materials.append(self.mat)
            _bk().map_faces(ob, self.cells[group])
            ob["rr_group"] = group
            self.parts.append(ob)
        return ob

    # ---------- primitives ----------
    @staticmethod
    def _cube(bm, center, size, rot, origin):
        vs = bmesh.ops.create_cube(bm, size=1.0)["verts"]
        bmesh.ops.scale(bm, vec=Vector(size), verts=vs)
        if any(rot):
            bmesh.ops.transform(bm, matrix=_rot_matrix(rot), verts=vs)
        bmesh.ops.translate(bm, vec=Vector(center) - Vector(origin), verts=vs)

    def box(self, part, group, center, size, rot=(0, 0, 0), detail=0):
        if self._skip(detail):
            return None
        bm = bmesh.new()
        self._cube(bm, center, size, rot, center)
        return self._obj(self._name(part, group), bm, center, group)

    def boxes(self, part, group, items, detail=0):
        items = [it if len(it) == 3 else (it[0], it[1], (0, 0, 0)) for it in items]
        if not items or self._skip(detail):
            return None
        lo = [min(c[i] - s[i] / 2 for c, s, _ in items) for i in range(3)]
        hi = [max(c[i] + s[i] / 2 for c, s, _ in items) for i in range(3)]
        origin = tuple((a + b) / 2 for a, b in zip(lo, hi))
        bm = bmesh.new()
        for c, s, r in items:
            self._cube(bm, c, s, r, origin)
        return self._obj(self._name(part, group), bm, origin, group)

    def cyl(self, part, group, center, r, depth, axis="Z", segs=12, r2=None, detail=0):
        if self._skip(detail):
            return None
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=self.segs(segs), radius1=r,
                              radius2=r if r2 is None else r2, depth=depth)
        if axis == "X":
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"), verts=bm.verts)
        elif axis == "Y":
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"), verts=bm.verts)
        return self._obj(self._name(part, group), bm, center, group)

    def prism(self, part, group, profile, depth, center, axis="X", detail=0):
        """profile: [(u, v)] relative to center; axis X -> (y, z), Y -> (x, z), Z -> (x, y)."""
        if self._skip(detail):
            return None
        bm = bmesh.new()
        h = depth / 2
        pos = {"X": lambda u, v: (-h, u, v), "Y": lambda u, v: (u, -h, v), "Z": lambda u, v: (u, v, -h)}[axis]
        f = bm.faces.new([bm.verts.new(pos(u, v)) for u, v in profile])
        ext = bmesh.ops.extrude_face_region(bm, geom=[f])
        nv = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec={"X": (depth, 0, 0), "Y": (0, depth, 0), "Z": (0, 0, depth)}[axis], verts=nv)
        return self._obj(self._name(part, group), bm, center, group)

    def wall(self, part, group, axis, a0, a1, at, z0, z1, thick, holes=(), detail=0):
        a0, a1 = min(a0, a1), max(a0, a1)
        cuts = sorted({a0, a1} | {min(a1, max(a0, c + s * w / 2)) for c, _, w, _ in holes for s in (-1, 1)})
        strips = []
        for s0, s1 in zip(cuts, cuts[1:]):
            if s1 - s0 < 1e-4:
                continue
            m = (s0 + s1) / 2
            blocked = sorted((max(z0, hz), min(z1, hz + hh)) for c, hz, w, hh in holes if abs(m - c) < w / 2)
            solid, z = [], z0
            for b0, b1 in blocked:
                if b0 > z + 1e-4:
                    solid.append((z, b0))
                z = max(z, b1)
            if z1 > z + 1e-4:
                solid.append((z, z1))
            if strips and strips[-1][2] == solid and abs(strips[-1][1] - s0) < 1e-6:
                strips[-1][1] = s1                                 # same solid runs: widen the strip
            else:
                strips.append([s0, s1, solid])
        items = []
        for s0, s1, solid in strips:
            for zb, zt in solid:
                c, s = ((s0 + s1) / 2, at, (zb + zt) / 2), (s1 - s0, thick, zt - zb)
                if axis == "Y":
                    c, s = (at, c[0], c[2]), (thick, s[0], s[2])
                items.append((c, s))
        return self.boxes(part, group, items, detail)

    def proxy(self, center, size, rot=(0, 0, 0)):
        bm = bmesh.new()
        self._cube(bm, center, size, rot, center)
        n = self._nn[("Collider", "Proxy")] = self._nn.get(("Collider", "Proxy"), 0) + 1
        return self._obj(f"{self.asset}_Collider_Proxy_{n:02d}", bm, center, proxy=True)

    def measure(self, label, text):
        self.measures[label] = text


def _bk():
    import blender_kit
    return blender_kit


# ---------- merge (LOD1 and --merge group) ----------

def merge_groups(k, part="Merged"):
    """Join every visual part of the same group into one object <Asset>_<part>_<Group>_01 (UVs kept)."""
    by = {}
    for o in k.parts:
        by.setdefault(o["rr_group"], []).append(o)
    bpy.context.view_layer.update()
    out = []
    for g, objs in by.items():
        bm = bmesh.new()
        for o in objs:
            tmp = o.data.copy()
            tmp.transform(o.matrix_world)
            bm.from_mesh(tmp)
            bpy.data.meshes.remove(tmp)
        lo = [min(v.co[i] for v in bm.verts) for i in range(3)]
        hi = [max(v.co[i] for v in bm.verts) for i in range(3)]
        c = Vector([(a + b) / 2 for a, b in zip(lo, hi)])
        bmesh.ops.translate(bm, vec=-c, verts=bm.verts)
        name = f"{k.asset}_{part}_{g}_01"
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        ob.location = c
        ob["rr_group"] = g
        k.coll.objects.link(ob)
        for o in objs:
            data = o.data
            bpy.data.objects.remove(o)
            if data.users == 0:
                bpy.data.meshes.remove(data)
        out.append(ob)
    k.parts = out
    return out


# ---------- checks ----------

def world_box(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


def names(objs, asset):
    rx = re.compile(rf"^{re.escape(asset)}_[A-Z][A-Za-z0-9]*_[A-Z][A-Za-z0-9]*_\d{{2,3}}$")
    bad = [o.name for o in objs if not rx.match(o.name)]
    print(f"names: {len(objs)} parts, {len(bad)} off the <Asset>_<Part>_<Group>_<nn> pattern")
    return bad


def coplanar(objs, tol=0.004, min_overlap=0.02):
    """Same-facing faces of DIFFERENT parts in one plane that overlap: they z-fight and render black in Cycles.
    Down-facing faces are skipped (they rest on something and the Roblox camera sits above).
    Returns sorted unique (part, part) pairs."""
    bpy.context.view_layer.update()
    faces = {}
    for o in objs:
        mw, me = o.matrix_world, o.data
        n3 = mw.to_3x3().inverted().transposed()
        for f in me.polygons:
            n = (n3 @ f.normal).normalized()
            if n.z < -0.9:
                continue
            vs = [mw @ me.vertices[i].co for i in f.vertices]
            key = (round(n.x, 2), round(n.y, 2), round(n.z, 2))
            faces.setdefault(key, []).append((n.dot(vs[0]), o.name, vs, n))
    pairs = set()
    for key, fs in faces.items():
        if len(fs) < 2:
            continue
        n = fs[0][3]
        drop = max(range(3), key=lambda i: abs(n[i]))
        ax = [i for i in range(3) if i != drop]
        fs.sort(key=lambda t: t[0])
        for i, (d, name, vs, _) in enumerate(fs):
            a0 = [min(v[j] for v in vs) for j in ax]
            a1 = [max(v[j] for v in vs) for j in ax]
            for d2, name2, vs2, _ in fs[i + 1:]:
                if d2 - d > tol:
                    break
                if name2 == name:
                    continue
                b0 = [min(v[j] for v in vs2) for j in ax]
                b1 = [max(v[j] for v in vs2) for j in ax]
                if all(min(a1[j], b1[j]) - max(a0[j], b0[j]) > min_overlap for j in range(2)):
                    pairs.add(tuple(sorted((name, name2))))
    print(f"coplanar: {len(pairs)} overlapping same-facing face pairs")
    return sorted(pairs)


def floating(objs, gap=0.05):
    """Parts not connected (bounding boxes within `gap`) to anything that reaches the lowest level."""
    bpy.context.view_layer.update()
    boxes = {o.name: world_box(o) for o in objs}
    if not boxes:
        return []
    floor = min(lo[2] for lo, _ in boxes.values())
    touch = lambda a, b: all(a[0][i] - gap <= b[1][i] and b[0][i] - gap <= a[1][i] for i in range(3))
    seen = [n for n, (lo, _) in boxes.items() if lo[2] <= floor + gap]
    todo, seen = list(seen), set(seen)
    while todo:
        cur = boxes[todo.pop()]
        for n, b in boxes.items():
            if n not in seen and touch(cur, b):
                seen.add(n)
                todo.append(n)
    out = sorted(set(boxes) - seen)
    print(f"floating: {len(out)} parts not connected to the ground")
    return out


def feature_px(cam, objs, keys, res=(400, 225)):
    """Largest projected side (px) of the parts whose Part name contains each key, at the game-distance view.
    Returns {key: (px, part)} with the smallest such part per key (the one most at risk of vanishing)."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    bpy.context.view_layer.update()
    out = {}
    for key in keys:
        best = None
        for o in objs:
            if f"_{key}" not in o.name:
                continue
            pts = [world_to_camera_view(sc, cam, o.matrix_world @ Vector(c)) for c in o.bound_box]
            pts = [p for p in pts if p.z > 0]
            if not pts:
                continue
            w = (max(p.x for p in pts) - min(p.x for p in pts)) * res[0]
            h = (max(p.y for p in pts) - min(p.y for p in pts)) * res[1]
            span = max(w, h)
            if best is None or span < best[0]:
                best = (round(span, 1), o.name)
        if best:
            out[key] = best
    return out


if __name__ == "__main__":
    import argparse
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
