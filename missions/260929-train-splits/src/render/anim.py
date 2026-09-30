"""Animated break GIFs (stand-in fx). Reuses build.py's import / cut / pose / camera code; cut once, move objects per frame.
python3 anim.py --jobs wide1,roof1,wide2 [--samples 8] [--fps 12]
World scrolls (sleepers move +Z at 35 studs/s, wrapped by the 2.6 sleeper pitch); the kept train stays put."""
import argparse, math, os, sys, time, types
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
from mathutils import Matrix
import build as BD
import scene as S
from PIL import Image, ImageDraw, ImageFont

JOBS = {  # name: (break k, cam loc B, look B, fov, out)
    'wide1': (1, (40, 25, -35), (0, 2, 12), 50, 'anim_break1_wide.gif'),
    'roof1': (1, (2, 22, -20), (0, 8, 6), 70, 'anim_break1_roof.gif'),
    'wide2': (2, (40, 25, -35), (0, 2, 12), 50, 'anim_break2_wide.gif'),
}
SCROLL, PITCH = 35.0, 2.6
RNG = np.random.default_rng(7)


def fx_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree.nodes['Principled BSDF']


def set_fx(b, base, emit=(0, 0, 0), strength=0.0, alpha=1.0):
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Roughness'].default_value = 1.0
    b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = strength
    b.inputs['Alpha'].default_value = max(0.0, min(1.0, alpha))


class Fx:
    def __init__(self, name, kind, flat=1.0):
        bpy.ops.mesh.primitive_cube_add(size=1) if kind == 'cube' else bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=16, ring_count=8)
        self.ob = bpy.context.active_object; self.ob.name = name
        self.mat, self.b = fx_mat(name + 'M'); self.ob.data.materials.append(self.mat)
        self.flat = flat

    def show(self, pos, size, **kw):     # pos: Roblox world, size: diameter (studs)
        if size is None or size <= 0.01 or kw.get('alpha', 1) <= 0.01:
            self.ob.hide_render = True; return
        self.ob.hide_render = False
        self.ob.location = S.r2b(np.asarray(pos, float))
        r = size / 2 if self.ob.name.startswith('fx_deb') is False else size
        self.ob.scale = (r, r, r * self.flat)       # Blender Z = Roblox Y (flatten dust vertically)
        set_fx(self.b, **kw)


def lerp(a, b, u):
    u = max(0.0, min(1.0, u)); return tuple(x + (y - x) * u for x, y in zip(a, b))


class Anim:
    def __init__(self, B):
        self.B = B
        self.sleepers = next(o for o in B.track if o.name == 'Sleepers')
        self.flash = Fx('fx_flash', 'sphere')
        self.fire = [Fx('fx_fire%d' % i, 'sphere') for i in range(6)]
        self.fire_off = [RNG.normal(0, 1, 3) * [5, 3, 5] for _ in range(6)]
        self.soot = [Fx('fx_soot%d' % i, 'sphere') for i in range(8)]
        self.soot_off = [(RNG.normal(0, 1, 3) * [6, 2, 5], RNG.uniform(0.9, 1.1), RNG.uniform(0, 0.25)) for _ in range(8)]
        self.deb = [Fx('fx_deb%d' % i, 'cube') for i in range(8)]
        self.deb_v = [np.array([RNG.uniform(-25, 25), RNG.uniform(25, 45), RNG.uniform(-20, 25)]) for _ in range(8)]
        self.dust = [[Fx('fx_dust%d_%d' % (j, i), 'sphere', flat=0.35) for i in range(5)] for j in range(2)]
        self.smoke = [Fx('fx_smoke%d' % i, 'sphere') for i in range(4)]
        self.fx_all = [self.flash] + self.fire + self.soot + self.deb + self.smoke + sum(self.dust, [])
        for f in self.fx_all:
            f.ob.visible_shadow = False
            f.ob.hide_render = True

    def pose(self, k, t):
        B = self.B; tt = max(0.0, t)
        mats = {}
        if t >= 0:
            for objs, fk, prof in B.bodies(k):
                Mb, _ = BD.body_matrix(tt, fk, BD.SIDE[k], prof, B.centre(objs))
                for o in objs:
                    mats[o.name] = Mb
        for h in B.half.values():
            for o in h:
                o.matrix_world = B.R @ Matrix(mats.get(o.name, np.eye(4)).tolist())
        off = (SCROLL * t) % PITCH
        self.sleepers.matrix_world = B.R @ Matrix(BD.Tm([0, 0, off]).tolist())

    def fx(self, k, t):
        O = BD.ORIGIN[k]; side = BD.SIDE[k]; P = lambda v: O + np.asarray(v, float)
        # flash: radius 3 -> 9 over 0-0.12 s, gone by 0.25 s
        if 0 <= t < 0.25:
            r = 3 + 6 * min(t / 0.12, 1)
            a = 1.0 if t < 0.12 else 1 - (t - 0.12) / 0.13
            self.flash.show(P([0, 5, 0]), 2 * r, base=(1, 1, 0.8), emit=(1, 0.95, 0.7), strength=25 * a, alpha=a)
        else:
            self.flash.show(None, 0)
        # fireball: 6 puffs growing to ~34 studs across by 0.4 s, cooling to charcoal by 0.6 s, gone ~1.0 s
        for f, o in zip(self.fire, self.fire_off):
            if 0.02 <= t < 1.0:
                g = min((t - 0.02) / 0.38, 1.0); g = 1 - (1 - g) ** 2
                size = 20 * g
                cool = (t - 0.4) / 0.2
                emit = lerp((1.0, 0.45, 0.08), (0.05, 0.03, 0.02), cool)
                st = 12 * (1 - max(0.0, min(1.0, cool)))
                a = 1 - max(0.0, (t - 0.6) / 0.4)
                f.show(P(np.array([0, 6 + 4 * g, 0]) + o * g * 1.3), size, base=lerp((1, 0.5, 0.1), (0.08, 0.08, 0.08), cool),
                       emit=emit, strength=st, alpha=a)
            else:
                f.show(None, 0)
        # soot: 10 -> 30 studs, rise ~12 studs/s, drift +Z ~20 studs/s, fade 1-3 s
        for f, (o, sp, d) in zip(self.soot, self.soot_off):
            tl = t - 0.3 - d
            if 0 <= tl and t < 3.0:
                size = 10 + 20 * min(tl / 2.5, 1)
                a = 0.85 * (1 - max(0.0, (t - 1.0) / 2.0))
                f.show(P(o + [0, 10 + 12 * sp * tl, 20 * tl]), size, base=(0.07, 0.07, 0.07), alpha=a)
            else:
                f.show(None, 0)
        # debris: small dark cubes on ballistic arcs, gone by 1.5 s
        for f, v in zip(self.deb, self.deb_v):
            if 0 <= t < 1.5:
                p = np.array([0, 6, 0]) + v * t + np.array([0, -0.5 * 60 * t * t, 0])
                f.show(P(p), 0.7, base=(0.05, 0.05, 0.05), alpha=1.0)
                f.ob.rotation_euler = (t * 7, t * 5, t * 3)
            else:
                f.show(None, 0)
        # topple dust: cream flattened puffs along each wreck's track-side edge at landing, 3 -> 10 studs over 1.6 s
        cream = BD.srgb('#CFC8A6')
        bodies = self.B.bodies(k)
        for j, row in enumerate(self.dust):
            if j >= len(bodies):
                for f in row: f.show(None, 0)
                continue
            objs, fk, prof = bodies[j]
            tl_land = prof['delay'] + prof['roll_time']
            u = t - tl_land
            c = self.B.centre(objs)
            zc = c[2] + BD.drift(max(0, tl_land)) + prof['extra_back']
            for i, f in enumerate(row):
                if 0 <= u < 1.6:
                    x = BD.ORIGIN[fk][0] + side * (BD.PIVOT_X + 1.5)
                    f.show([x, BD.RAIL_Y + 1 + 1.5 * u, zc + (i - 2) * 6.5], 3 + 7 * (u / 1.6), base=cream,
                           alpha=0.9 * (1 - u / 1.6) ** 0.7)
                else:
                    f.show(None, 0)
        # torn-edge smoke: grey puffs rising from the kept half's torn end from 0.05 s, drifting +Z
        grey = BD.srgb('#60645E')
        for i, f in enumerate(self.smoke):
            ph = 1.6
            tl = t - 0.05 - i * ph / 4
            if tl >= 0:
                u = (tl % ph) / ph
                x0 = [-4, 4, -1.5, 1.5][i]
                f.show(P([x0, 13 + 7 * u, -1.5 + 6 * u]), 1.5 + 4 * u, base=grey, alpha=0.8 * (1 - u))
            else:
                f.show(None, 0)


def cam(k, loc, look, fov):
    lw = BD.ORIGIN[k] + np.array(loc, float); kw = BD.ORIGIN[k] + np.array(look, float)
    c = bpy.data.objects.new('AnimCam', bpy.data.cameras.new('AnimCam')); bpy.context.scene.collection.objects.link(c)
    c.location = S.r2b(lw); c.rotation_euler = (S.r2b(kw) - S.r2b(lw)).to_track_quat('-Z', 'Y').to_euler()
    c.data.clip_start = 0.05; c.data.clip_end = 6000
    c.data.sensor_fit = 'VERTICAL'; c.data.sensor_height = 24.0; c.data.lens = 12.0 / math.tan(math.radians(fov) / 2)
    return c


def stamp(path, t):
    im = Image.open(path).convert('RGB'); d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 13)
    except OSError:
        f = ImageFont.load_default()
    for (x, y, s) in ((8, 6, 't = %.1f s' % t), (8, im.height - 20, 'stand-in fx - real particles in the VFX GIFs')):
        d.text((x + 1, y + 1), s, fill=(0, 0, 0), font=f); d.text((x, y), s, fill=(255, 255, 255), font=f)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jobs', default='wide1,roof1,wide2')
    ap.add_argument('--samples', type=int, default=8)
    ap.add_argument('--fps', type=int, default=12)
    ap.add_argument('--t0', type=float, default=-0.5); ap.add_argument('--t1', type=float, default=6.0)
    ap.add_argument('--res', default='480x270')
    ap.add_argument('--frames', type=int, default=0, help='test: only this many frames')
    ap.add_argument('--progress', default=os.path.join(BD.MISSION, 'progress'))
    a = ap.parse_args()
    W, H = map(int, a.res.split('x'))
    t_b = time.time()
    B = BD.Build(types.SimpleNamespace(fallback_caps='on'))
    A = Anim(B)
    sc = bpy.context.scene; sc.cycles.use_denoising = True
    print('[anim] scene ready %.1fs' % (time.time() - t_b), flush=True)
    n = int(round((a.t1 - a.t0) * a.fps))
    for job in a.jobs.split(','):
        k, loc, look, fov, out = JOBS[job]
        c = cam(k, loc, look, fov)
        tmp = os.path.join(HERE, 'out', 'anim_' + job); os.makedirs(tmp, exist_ok=True)
        frames = []; tj = time.time()
        for i in range(a.frames or n):
            t = a.t0 + i / a.fps
            A.pose(k, t); A.fx(k, t)
            p = os.path.join(tmp, 'f%03d.png' % i)
            S.render(c, p, res=(W, H), samples=a.samples)
            frames.append(stamp(p, t))
            print('[anim] %s %d/%d t=%.2f %.1fs' % (job, i + 1, n, t, time.time() - tj), flush=True)
        gp = os.path.join(a.progress, out)
        frames[0].save(gp, save_all=True, append_images=frames[1:], duration=int(1000 / a.fps), loop=0, optimize=True)
        print('[anim] wrote %s (%d frames, %.1f min)' % (gp, len(frames), (time.time() - tj) / 60), flush=True)
        bpy.data.objects.remove(c)


if __name__ == '__main__':
    main()
