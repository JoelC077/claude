#!/usr/bin/env python3
"""fxsim.py: preview approximations of rr-vfx-lighting effect presets (Pillow; no Roblox).

  fxsim.py strip NAME --out strip.png [--speed S] [--quick]      side view: steady state on sky / pasture / dark
                                                                  backdrops (loops) or a time strip (bursts)
  fxsim.py gif NAME --out anim.gif [--seconds 3] [--fps 12]       side-view motion for the owner (not the critic)
  fxsim.py pov NAMES --view view.json --out pov.png [--speed S] [--time T] [--tier phone|pc]
                                                                  particles composited over a lookdev plate from
                                                                  the same camera; prints overdraw and, per preset,
                                                                  visible / hidden-by-geometry / off-screen counts,
                                                                  screen coverage and luma change over the plate

Re-implements the ParticleEmitter behaviour the presets rely on (RBXD docs, 2026-09-28): Rate and Emit(n),
Lifetime/Speed/Rotation/RotSpeed ranges, SpreadAngle, Acceleration, Drag (speed halves every 1/Drag s),
WindAffectsDrag toward Workspace.GlobalWind (= -forward x Speed x wind_scale, the train never moves),
Size/Transparency/Squash sequences with envelopes, ColorSequence, LightEmission (0 normal .. 1 additive),
LightInfluence/Brightness, VelocityParallel streaks, Box part emitters, Beams, debris with trails under
Roblox gravity 196.2 x gravity_scale. Textures are procedural stand-ins. Limits: references/fidelity.md.
"""
import sys
sys.dont_write_bytecode = True  # never leave __pycache__ inside the skill
import argparse, json, math, random
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageStat
except ImportError:  # pragma: no cover
    sys.exit("fxsim needs Pillow (python3 -m pip install pillow)")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import vfx  # noqa: E402

GRAVITY = 196.2  # Roblox default Workspace.Gravity, studs/s^2
DT = 1 / 30
SPRITE = 64


# ------------------------------------------------------------------ small vector helpers
def add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def mul(a, k):
    return [a[0] * k, a[1] * k, a[2] * k]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def norm(a):
    n = math.sqrt(dot(a, a)) or 1.0
    return [a[0] / n, a[1] / n, a[2] / n]


def rotate(v, axis, ang):
    """Rodrigues rotation of v about a unit axis by ang radians."""
    c, s = math.cos(ang), math.sin(ang)
    return add(add(mul(v, c), mul(cross(axis, v), s)), mul(axis, dot(axis, v) * (1 - c)))


def rgb(hx):
    hx = hx.lstrip("#")
    return [int(hx[i:i + 2], 16) for i in (0, 2, 4)]


def cseq_at(seq, t):
    for (t0, c0), (t1, c1) in zip(seq, seq[1:]):
        if t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0
            a, b = rgb(c0), rgb(c1)
            return [a[i] + (b[i] - a[i]) * f for i in range(3)]
    return rgb(seq[-1][1])


def nseq_env(seq, rnd):
    """Per-particle keypoint values with the envelope randomised once at emission (RBXD)."""
    return [(k[0], k[1] + (rnd.uniform(-k[2], k[2]) if k[2] else 0)) for k in seq]


def nseq_at(pts, t):
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * ((t - t0) / (t1 - t0) if t1 > t0 else 0)
    return pts[-1][1]


# ------------------------------------------------------------------ sprites
_BASE, _CACHE = {}, {}


def base_sprite(kind):
    if kind in _BASE:
        return _BASE[kind]
    im = Image.new("L", (SPRITE, SPRITE), 0)
    d = ImageDraw.Draw(im)
    c = SPRITE / 2
    if kind == "smoke":   # lumpy puff: a few overlapping soft blobs
        r = random.Random(7)
        for _ in range(6):
            ox, oy, rr = r.uniform(-9, 9), r.uniform(-9, 9), r.uniform(12, 18)
            d.ellipse([c + ox - rr, c + oy - rr, c + ox + rr, c + oy + rr], fill=200)
        im = im.filter(ImageFilter.GaussianBlur(5))
    elif kind == "spark":  # hot core + glow
        d.ellipse([c - 14, c - 14, c + 14, c + 14], fill=90)
        im = im.filter(ImageFilter.GaussianBlur(6))
        d = ImageDraw.Draw(im)
        d.ellipse([c - 6, c - 6, c + 6, c + 6], fill=255)
        im = im.filter(ImageFilter.GaussianBlur(1.5))
    elif kind == "streak":  # thin soft line (rain); preview-only stand-in for a streak texture
        d.rectangle([c - 3, 4, c + 3, SPRITE - 4], fill=255)
        im = im.filter(ImageFilter.GaussianBlur(1.5))
    else:                  # soft round
        d.ellipse([c - 22, c - 22, c + 22, c + 22], fill=255)
        im = im.filter(ImageFilter.GaussianBlur(7))
    _BASE[kind] = im
    return im


def sprite(kind, w, h, angle):
    key = (kind, w, h, int(angle // 10) * 10 if angle is not None else None)
    im = _CACHE.get(key)
    if im is None:
        im = base_sprite(kind).resize((max(1, w), max(1, h)), Image.BILINEAR)
        if key[3]:
            im = im.rotate(key[3], resample=Image.BILINEAR, expand=True)
        if len(_CACHE) > 4000:
            _CACHE.clear()
        _CACHE[key] = im
    return im


def texture_kind(tex):
    tex = (tex or "").lower()
    if "smoke" in tex:
        return "smoke"
    if "sparkle" in tex or "spark" in tex:
        return "spark"
    return "soft"


# ------------------------------------------------------------------ simulation
class Emitter:
    def __init__(self, preset, layer, anchor, rnd, rate_scale=1.0, name=""):
        pr = layer.get("props", {})
        self.p, self.L, self.pr, self.rnd, self.name = preset, layer, pr, rnd, name
        self.origin = add(anchor, layer.get("offset", [0, 0, 0]))
        self.dir = norm(layer.get("dir", [0, 1, 0]))
        self.rate = pr.get("Rate", ("num", 0))[1] * rate_scale
        sl = preset.get("speed_link") or {}
        self.linked = layer["name"] in sl.get("layers", [])
        self.sl = sl
        self.acc = list(pr.get("Acceleration", ("v3", 0, 0, 0))[1:])
        self.drag = pr.get("Drag", ("num", 0))[1]
        self.wind_on = pr.get("WindAffectsDrag", ("bool", False))[1]
        self.kind = layer.get("preview_sprite") or texture_kind(pr.get("Texture", ("str", ""))[1])
        self.le = pr.get("LightEmission", ("num", 0))[1]
        self.li = pr.get("LightInfluence", ("num", 0))[1]
        self.bright = pr.get("Brightness", ("num", 1))[1]
        self.orient = pr.get("Orientation", ("enum", "Enum.ParticleOrientation.FacingCamera"))[1].split(".")[-1]
        self.acc_carry = 0.0
        self.parts = []
        self.box = layer.get("part_size") if layer.get("parent") == "part" else None

    def set_intensity(self, k, scale):
        if self.linked:
            self.rate = (self.sl["rate_idle"] + (self.sl["rate_max"] - self.sl["rate_idle"]) * k) * scale

    def spawn(self, n):
        pr, r = self.pr, self.rnd
        lo, hi = pr.get("Lifetime", ("range", 1, 1))[1:]
        slo, shi = pr.get("Speed", ("range", 0, 0))[1:]
        sx, sy = pr.get("SpreadAngle", ("v2", 0, 0))[1:]
        rlo, rhi = pr.get("Rotation", ("range", 0, 0))[1:]
        vlo, vhi = pr.get("RotSpeed", ("range", 0, 0))[1:]
        ref = [0, 0, 1] if abs(self.dir[1]) > 0.9 else [0, 1, 0]
        u = norm(cross(self.dir, ref))
        v = norm(cross(u, self.dir))
        for _ in range(int(n)):
            d = rotate(rotate(self.dir, u, math.radians(r.uniform(-sx, sx))), v, math.radians(r.uniform(-sy, sy)))
            pos = list(self.origin)
            if self.box:
                pos = add(pos, [r.uniform(-b / 2, b / 2) for b in self.box])
            self.parts.append({
                "pos": pos, "vel": mul(d, r.uniform(slo, shi)), "age": 0.0, "life": max(1e-3, r.uniform(lo, hi)),
                "size": nseq_env(pr["Size"][1], r) if "Size" in pr else [(0, 1), (1, 1)],
                "tr": nseq_env(pr["Transparency"][1], r) if "Transparency" in pr else [(0, 0), (1, 0)],
                "sq": nseq_env(pr["Squash"][1], r) if "Squash" in pr else None,
                "rot": r.uniform(rlo, rhi), "rs": r.uniform(vlo, vhi)})

    def step(self, dt, wind, emit=True):
        if emit and self.rate > 0:
            self.acc_carry += self.rate * dt
            n = int(self.acc_carry)
            self.acc_carry -= n
            self.spawn(n)
        f = 2 ** (-self.drag * dt) if self.drag else 1.0
        alive = []
        for q in self.parts:
            q["age"] += dt
            if q["age"] >= q["life"]:
                continue
            v = add(q["vel"], mul(self.acc, dt))
            if self.drag:
                v = add(wind, mul(sub(v, wind), f)) if self.wind_on else mul(v, f)
            q["vel"] = v
            q["pos"] = add(q["pos"], mul(v, dt))
            q["rot"] += q["rs"] * dt
            alive.append(q)
        self.parts = alive


class Debris:
    def __init__(self, layer, anchor, rnd, speed, trails):
        d = layer["debris"]
        self.d, self.rnd = d, rnd
        self.origin = add(anchor, layer.get("offset", [0, 0, 0]))
        self.dir = norm(layer.get("dir", [0, 1, 0]))
        self.g = GRAVITY * d.get("gravity_scale", 1.0)
        self.carry = d.get("carry", 0.0) * speed
        self.trail = trails.get(d.get("trail") or "")
        self.parts = []

    def spawn(self):
        r = self.rnd
        ref = [0, 0, 1] if abs(self.dir[1]) > 0.9 else [0, 1, 0]
        u = norm(cross(self.dir, ref))
        v = norm(cross(u, self.dir))
        for i in range(self.d["count"]):
            dd = rotate(rotate(self.dir, u, math.radians(r.uniform(-self.d["spread"], self.d["spread"]))), v,
                        math.radians(r.uniform(-self.d["spread"], self.d["spread"])))
            vel = add(mul(dd, r.uniform(*self.d["speed"])), [-self.carry, 0, 0])
            self.parts.append({"pos": list(self.origin), "vel": vel, "age": 0.0, "hist": [],
                               "col": rgb(self.d["colours"][i % len(self.d["colours"])]), "rot": r.uniform(0, 360),
                               "rs": r.uniform(-500, 500)})

    def step(self, dt):
        alive = []
        for q in self.parts:
            q["age"] += dt
            if q["age"] >= self.d["lifetime"]:
                continue
            q["vel"][1] -= self.g * dt
            q["pos"] = add(q["pos"], mul(q["vel"], dt))
            q["rot"] += q["rs"] * dt
            q["hist"] = (q["hist"] + [list(q["pos"])])[-12:]
            alive.append(q)
        self.parts = alive


class Sim:
    """One or more presets at their stand anchors, stepped at DT."""

    def __init__(self, model, names, speed, tier="pc", seed=1, burst_at=0.0):
        """burst_at: seconds before bursts fire (loops warm up first, as in a running game)."""
        self.model, self.speed = model, speed
        self.wind = [-speed * model.meta.get("wind_scale", 1.0), 0, 0]
        self.rnd = random.Random(seed)
        self.t = 0.0
        self.emitters, self.debris, self.beams, self.lights, self.bursts, self.crackles = [], [], [], [], [], []
        cfg = model.budget_raw["tiers"][tier]
        smax = model.meta.get("speed_max") or 50
        for n in names:
            p = model.presets[n]
            scale = cfg["rate_scale"].get(str(p["priority"]), 1.0)
            anchor = list(model.anchors.get(p["anchor"], [0, 0, 0]))
            sl = p.get("speed_link") or {}
            k = min(1.0, speed / smax)
            frac = (sl["rate_idle"] + (sl["rate_max"] - sl["rate_idle"]) * k) / sl["rate_max"] if sl.get("rate_max") else 1.0
            for L in p["layers"]:
                if L["class"] == "ParticleEmitter":
                    e = Emitter(p, L, anchor, self.rnd, scale, n)
                    if p.get("kind") == "loop":
                        e.set_intensity(k, scale)
                    else:
                        e.rate = 0
                        self.bursts.append(((L.get("delay") or 0.0) + burst_at, e, math.ceil(L["emit"] * scale)))
                    self.emitters.append(e)
                    if p.get("crackle"):
                        self.crackles.append((e, p["crackle"], [self.rnd.uniform(*p["crackle"]["every"])]))
                elif L["class"] == "Debris":
                    db = Debris(L, anchor, self.rnd, speed, model.trails)
                    self.debris.append(db)
                    self.bursts.append(((L.get("delay") or 0.0) + burst_at, db, None))
                elif L["class"] == "Beam":
                    self.beams.append((add(anchor, L["offset"]), add(anchor, L["a1"]), L["props"]))
                else:   # a light named in speed_link.layers dims with the rate (brake glow fades as the train stops)
                    self.lights.append({"pos": add(anchor, L["offset"]), "L": L, "p": p, "level": 0.0, "pulse_t": None,
                                        "k": frac if L["name"] in sl.get("layers", []) else 1.0})
        self.fired = set()

    def step(self, dt=DT):
        self.t += dt
        for i, (delay, obj, n) in enumerate(self.bursts):
            if i not in self.fired and self.t >= delay:
                self.fired.add(i)
                if n is None:
                    obj.spawn()
                else:
                    obj.spawn(n)
                for li in self.lights:
                    if li["L"].get("pulse"):
                        li["pulse_t"] = self.t
        for e, cr, nxt in self.crackles:
            if self.t >= nxt[0]:
                e.spawn(self.rnd.randint(*cr["emit"]))
                nxt[0] = self.t + self.rnd.uniform(*cr["every"])
                for li in self.lights:
                    if li["p"] is e.p:
                        li["pulse_t"] = self.t
        for e in self.emitters:
            e.step(dt, self.wind)
        for db in self.debris:
            db.step(dt)
        for li in self.lights:
            pr = li["L"].get("props", {})
            base = pr.get("Brightness", ("num", 0))[1] * li.get("k", 1.0)
            if li["L"].get("flicker"):
                fl = li["L"]["flicker"]
                base *= fl["min"] + (fl["max"] - fl["min"]) * (0.5 + 0.5 * math.sin(self.t * fl["hz"] * 2 * math.pi + self.rnd.random()))
            peak = None
            if li["pulse_t"] is not None:
                pul = li["L"].get("pulse") or (li["p"].get("crackle") or {}).get("flash")
                if pul and self.t - li["pulse_t"] <= pul["duration"]:
                    peak = pul["peak"] * (1 - (self.t - li["pulse_t"]) / pul["duration"])
            li["level"] = max(base, peak or 0)

    def run_to(self, t):
        while self.t < t - 1e-9:
            self.step()

    def live(self):
        return sum(len(e.parts) for e in self.emitters)


# ------------------------------------------------------------------ rendering
class Side:
    """Orthographic view from the train's right side (+Z looking -Z): screen x = world X, y = world Y."""

    def __init__(self, W, H, cx, cy, scale):
        self.W, self.H, self.cx, self.cy, self.s = W, H, cx, cy, scale

    def project(self, p):
        return self.W / 2 + (p[0] - self.cx) * self.s, self.H / 2 - (p[1] - self.cy) * self.s, 10.0, self.s

    def vel2d(self, v):
        return v[0], -v[1]


class Pinhole:
    def __init__(self, view):
        self.v = view
        self.eye, self.f, self.u, self.r = view["eye"], norm(view["forward"]), norm(view["up"]), norm(view["right"])
        self.W, self.H = view["res"]
        self.fp = (self.H / 2) / math.tan(math.radians(view["fov_v"]) / 2)

    def project(self, p):
        rel = sub(p, self.eye)
        z = dot(rel, self.f)
        if z < 0.5:
            return None
        return self.W / 2 + dot(rel, self.r) / z * self.fp, self.H / 2 - dot(rel, self.u) / z * self.fp, z, self.fp / z

    def vel2d(self, v):
        return dot(v, self.r), -dot(v, self.u)


def blend(canvas, img_rgb, alpha_l, le, box, count=None):
    """Roblox LightEmission blend: dst * (1 - a(1 - LE)) + src * a  (LE 0 = normal alpha, 1 = additive)."""
    x0, y0 = box
    w, h = alpha_l.size
    if x0 >= canvas.width or y0 >= canvas.height or x0 + w <= 0 or y0 + h <= 0:
        return
    region = canvas.crop((x0, y0, x0 + w, y0 + h))
    if le < 1:
        keep = alpha_l.point(lambda v: 255 - int(v * (1 - le)))
        region = ImageChops.multiply(region, Image.merge("RGB", (keep, keep, keep)))
    src = ImageChops.multiply(img_rgb, Image.merge("RGB", (alpha_l, alpha_l, alpha_l)))
    region = ImageChops.add(region, src)
    canvas.paste(region, (x0, y0))
    if count is not None:
        m = alpha_l.point(lambda v: 1 if v > 8 else 0)
        cr = count.crop((x0, y0, x0 + w, y0 + h))
        count.paste(ImageChops.add(cr, m), (x0, y0))


def draw_particles(canvas, sim, proj, light=(1, 1, 1), fog=None, depth=None, depth_scale=16, count=None, per=None):
    """per: dict filled with {preset: {live, visible, hidden, offscreen, mask}} (POV visibility facts)."""
    items = []
    for e in sim.emitters:
        st = per.setdefault(e.name, {"live": 0, "visible": 0, "hidden": 0, "offscreen": 0,
                                     "mask": Image.new("L", canvas.size, 0)}) if per is not None else None
        for q in e.parts:
            if st:
                st["live"] += 1
            pp = proj.project(q["pos"])
            if pp is None or not (0 <= pp[0] < canvas.width and 0 <= pp[1] < canvas.height):
                if st:
                    st["offscreen"] += 1
                if pp is None:
                    continue
            items.append((pp[2], e, q, pp))
    items.sort(key=lambda x: -x[0])
    hidden = 0
    for z, e, q, (sx, sy, zz, spx) in items:
        st = per.get(e.name) if per is not None else None
        if depth is not None and 0 <= int(sx) < depth.width and 0 <= int(sy) < depth.height:
            dz = depth.getpixel((int(sx), int(sy))) / depth_scale
            if 0 < dz < zz - 1.0:
                hidden += 1
                if st:
                    st["hidden"] += 1
                continue
        if st and 0 <= sx < canvas.width and 0 <= sy < canvas.height:
            st["visible"] += 1
        t = q["age"] / q["life"]
        size = max(0.0, nseq_at(q["size"], t))
        a = max(0.0, min(1.0, 1 - nseq_at(q["tr"], t)))
        if a <= 0.004 or size <= 0:
            continue
        w = h = size
        if q["sq"]:
            s = nseq_at(q["sq"], t)
            w, h = (size / (1 + s), size * (1 + s)) if s >= 0 else (size * (1 - s), size / (1 - s))
        wp, hp = int(round(w * spx)), int(round(h * spx))
        if wp < 1 and hp < 1:
            wp = hp = 1
        if e.kind == "streak":
            wp, hp = max(1, wp), max(3, hp)
        wp, hp = min(wp, 2 * canvas.width), min(hp, 2 * canvas.height)
        if e.orient == "VelocityParallel":
            vx, vy = proj.vel2d(q["vel"])
            ang = -math.degrees(math.atan2(vx, -vy)) if (vx or vy) else 0
        else:
            ang = q["rot"] if e.kind == "smoke" else None
        spr = sprite(e.kind, wp, hp, ang)
        col = e.pr["Color"][1] if "Color" in e.pr else [(0, "#FFFFFF"), (1, "#FFFFFF")]
        c = cseq_at(col, t)
        lm = [e.li * light[i] + (1 - e.li) * e.bright for i in range(3)]
        c = [min(255, c[i] * lm[i]) for i in range(3)]
        if fog:
            f = 1 - math.exp(-fog["k"] * max(0.0, zz))
            c = [c[i] + (fog["colour"][i] - c[i]) * f for i in range(3)]
        alpha = spr.point(lambda v, a=a: int(v * a))
        img = Image.new("RGB", spr.size, tuple(int(x) for x in c))
        box = (int(sx - spr.width / 2), int(sy - spr.height / 2))
        blend(canvas, img, alpha, e.le, box, count)
        if st:
            st["mask"].paste(ImageChops.lighter(st["mask"].crop((box[0], box[1], box[0] + spr.width, box[1] + spr.height)),
                                                alpha.point(lambda v: 255 if v > 8 else 0)), box)
    return hidden


def draw_beams(canvas, sim, proj, light=(1, 1, 1)):
    for a0, a1, pr in sim.beams:
        p0, p1 = proj.project(a0), proj.project(a1)
        if not p0 or not p1:
            continue
        w0, w1 = pr.get("Width0", ("num", 1))[1], pr.get("Width1", ("num", 1))[1]
        tr = pr.get("Transparency", ("nseq", [(0, 0, 0), (1, 0, 0)]))[1]
        col = pr.get("Color", ("cseq", [(0, "#FFFFFF"), (1, "#FFFFFF")]))[1]
        le, li = pr.get("LightEmission", ("num", 0))[1], pr.get("LightInfluence", ("num", 0))[1]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        steps = 16
        mask = Image.new("L", canvas.size, 0)
        md = ImageDraw.Draw(mask)
        for i in range(steps):
            t0, t1 = i / steps, (i + 1) / steps
            a = 1 - vfx.seq_at([(k[0], k[1]) for k in tr], (t0 + t1) / 2)
            if a <= 0.004:
                continue
            wa = (w0 + (w1 - w0) * t0) * (p0[3] + (p1[3] - p0[3]) * t0) / 2
            wb = (w0 + (w1 - w0) * t1) * (p0[3] + (p1[3] - p0[3]) * t1) / 2
            xa, ya = p0[0] + dx * t0, p0[1] + dy * t0
            xb, yb = p0[0] + dx * (t1 + 0.02), p0[1] + dy * (t1 + 0.02)
            md.polygon([(xa + nx * wa, ya + ny * wa), (xb + nx * wb, yb + ny * wb), (xb - nx * wb, yb - ny * wb),
                        (xa - nx * wa, ya - ny * wa)], fill=int(255 * a))
        c = cseq_at(col, 0.5)
        c = [min(255, c[k] * (li * light[k] + (1 - li))) for k in range(3)]
        blend(canvas, Image.new("RGB", canvas.size, tuple(int(x) for x in c)), mask.filter(ImageFilter.GaussianBlur(1.5)), le, (0, 0))


def draw_debris(canvas, sim, proj):
    d = ImageDraw.Draw(canvas)
    for db in sim.debris:
        tr = db.trail
        for q in db.parts:
            pts = [proj.project(h) for h in q["hist"]]
            pts = [p for p in pts if p]
            if tr and len(pts) > 1:
                col = tr["props"].get("Color", ("cseq", [(0, "#FFFFFF"), (1, "#FFFFFF")]))[1]
                for i in range(1, len(pts)):
                    t = 1 - i / len(pts)
                    c = cseq_at(col, t)
                    wd = max(1, int(tr["width"] * pts[i][3] * (1 - t * 0.7)))
                    d.line([pts[i - 1][:2], pts[i][:2]], fill=tuple(int(x) for x in c), width=wd)
            p = proj.project(q["pos"])
            if p:
                s = max(2, int(max(db.d["size"]) * p[3] / 2))
                a = math.radians(q["rot"])
                poly = [(p[0] + s * math.cos(a + k * math.pi / 2) * (1 if k % 2 else 0.5), p[1] + s * math.sin(a + k * math.pi / 2) * (1 if k % 2 else 0.5)) for k in range(4)]
                d.polygon(poly, fill=tuple(q["col"]))


def draw_lights(canvas, sim, proj):
    """A soft dot where a light is, sized by Range and scaled by its current Brightness: it marks flashes and
    flicker timing only. Lights on surfaces are not simulated here (lookdev_bpy.py lights the scene)."""
    for li in sim.lights:
        lv = li["level"]
        if lv <= 0:
            continue
        p = proj.project(li["pos"])
        if not p:
            continue
        pr = li["L"]["props"]
        rng = pr.get("Range", ("num", 8))[1]
        r = max(3, int(min(rng * 0.12, 3.0) * p[3] * (0.5 if li["L"]["class"] == "SpotLight" else 1)))
        mask = Image.new("L", (6 * r, 6 * r), 0)
        ImageDraw.Draw(mask).ellipse([2 * r, 2 * r, 4 * r, 4 * r], fill=int(min(255, 45 * lv)))
        mask = mask.filter(ImageFilter.GaussianBlur(r * 0.8))
        c = rgb(pr["Color"][1]) if "Color" in pr else [255, 255, 255]
        blend(canvas, Image.new("RGB", mask.size, tuple(c)), mask, 1.0, (int(p[0] - 3 * r), int(p[1] - 3 * r)))


def font(size=12):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


# ------------------------------------------------------------------ side-view strips
def backdrops(model):
    c = model.ctx
    sky = [rgb(c.colour("$haze_grassland", "fxsim")[0]), rgb(c.colour("$decay_day", "fxsim")[0])]
    pasture = rgb(c.colour("@style.ground.pasture", "fxsim")[0])
    dark = rgb(c.colour("@style.world.soot_black", "fxsim")[0])
    return {"sky": (sky, 1.0), "pasture": ([pasture, pasture], 1.0), "dark": ([dark, dark], 0.22)}


def fill_backdrop(W, H, cols):
    top, bot = cols[1], cols[0]
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        f = y / max(1, H - 1)
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * f) for i in range(3)))
    return im


def frame_bounds(sims, anchor, avatar_h):
    xs, ys = [anchor[0] - 4, anchor[0] + 4], [anchor[1] - 1, anchor[1] + avatar_h + 1]
    for s in sims:
        for e in s.emitters:
            for q in e.parts:
                sz = nseq_at(q["size"], q["age"] / q["life"]) / 2
                xs += [q["pos"][0] - sz, q["pos"][0] + sz]
                ys += [q["pos"][1] - sz, q["pos"][1] + sz]
        for db in s.debris:
            for q in db.parts:
                xs.append(q["pos"][0])
                ys.append(q["pos"][1])
        for a0, a1, _ in s.beams:
            xs += [a0[0], a1[0]]
            ys += [a0[1], a1[1]]

    def trim(v):  # ignore the 2% outliers so one stray spark does not shrink everything
        v = sorted(v)
        k = int(len(v) * 0.02)
        return v[k:len(v) - k] if len(v) > 50 else v
    xs, ys = trim(xs), trim(ys)
    return min(xs), max(xs), min(ys), max(ys)


def panel(model, sim, bd, W, H, view, label, avatar_h, anchor):
    cols, light = bd
    im = fill_backdrop(W, H, cols)
    draw_beams(im, sim, view, (light,) * 3)
    draw_particles(im, sim, view, light=(light,) * 3)
    draw_debris(im, sim, view)
    draw_lights(im, sim, view)
    d = ImageDraw.Draw(im)
    # 5-stud avatar for scale (tech.units.avatar_h), standing at the anchor's rail level
    ax, ay, _, s = view.project([anchor[0] - 3, 0 if anchor[1] < 10 else anchor[1] - 0.5, 0])
    hgt = avatar_h * s
    ink = (21, 23, 28) if light >= 0.5 and sum(cols[0]) > 300 else (235, 228, 200)
    d.rectangle([ax - hgt * 0.18, ay - hgt, ax + hgt * 0.18, ay], outline=ink, width=1)
    d.ellipse([ax - hgt * 0.12, ay - hgt * 1.0, ax + hgt * 0.12, ay - hgt * 0.76], outline=ink, width=1)
    d.rectangle([0, 0, W, 16], fill=(21, 23, 28))
    d.text((4, 1), label, fill=(235, 228, 200), font=font(12))
    bar = 5 * s
    d.line([(6, H - 8), (6 + bar, H - 8)], fill=ink, width=2)
    d.text((10 + bar, H - 16), "5 studs", fill=ink, font=font(12))
    return im


def strip(model, name, out, speed=None, quick=False, tier="pc"):
    p = model.presets[name]
    speed = model.meta["speeds"].get("normal", 35) if speed is None else speed
    W, Hmax = (128, 112) if quick else (256, 224)
    if p["kind"] == "burst":   # four time panels: narrower, so a burst strip is as wide as a loop strip
        W = 96 if quick else 192
    avatar_h = model.bible.number("tech.units.avatar_h", 5) if model.bible.ok() else 5
    anchor = model.anchors.get(p["anchor"], [0, 0, 0])
    bds = backdrops(model)
    sims, labels = [], []
    if p["kind"] == "loop":
        life = max((L["props"].get("Lifetime", ("range", 1, 1))[2] for L in p["layers"] if L["class"] == "ParticleEmitter"), default=1)
        warm = life * 1.5 + 0.5
        for key in ("sky", "pasture", "dark"):
            s = Sim(model, [name], speed, tier)
            s.run_to(warm)
            best, bt = s.live(), s.t
            snap = None
            if p.get("crackle"):   # show a crackle, not the gap between two
                for _ in range(45):
                    s.step()
                    if s.live() > best:
                        best, bt = s.live(), s.t
                s = Sim(model, [name], speed, tier)
                s.run_to(bt)
            sims.append((s, key, snap))
            labels.append(f"{key} · Speed {speed:g} · live {s.live()}")
    else:
        times = [0.12, 0.4, 1.0] if not quick else [0.4]
        for t in times + [0.4]:
            s = Sim(model, [name], speed, tier)
            s.run_to(t)
            key = "dark" if len(sims) == len(times) else "sky"
            sims.append((s, key, None))
            labels.append(f"{key} t={t:g}s live {s.live()}")
    x0, x1, y0, y1 = (p.get("preview") or {}).get("window") or frame_bounds([s for s, _, _ in sims], anchor, avatar_h)
    if (p.get("preview") or {}).get("window"):
        anchor = [(x0 + x1) / 2 + 3, y0 + 0.5, 0]
    pad = 36   # label band on top, scale bar below
    scale = min(40.0, W / (max(x1 - x0, 10) * 1.08), (Hmax - pad) / (max(y1 - y0, 4) * 1.08))
    H = int(min(Hmax, max(Hmax * 0.5, (y1 - y0) * 1.08 * scale + pad)))   # crop to the particles: no empty bands
    view = Side(W, H, (x0 + x1) / 2, (y0 + y1) / 2, scale)
    panels = [panel(model, s, bds[k], W, H, view, lab, avatar_h, anchor) for (s, k, _), lab in zip(sims, labels)]
    im = Image.new("RGB", (W * len(panels) + 2 * (len(panels) - 1), H), (21, 23, 28))
    for i, pn in enumerate(panels):
        im.paste(pn, (i * (W + 2), 0))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    return {"preset": name, "out": str(out), "px_per_stud": round(scale, 2), "live": [s.live() for s, _, _ in sims],
            "speed": speed}


def gif(model, name, out, seconds=3.0, fps=12, speed=None, quick=False):
    speed = model.meta["speeds"].get("normal", 35) if speed is None else speed
    p = model.presets[name]
    W, H = (160, 120) if quick else (320, 240)
    anchor = model.anchors.get(p["anchor"], [0, 0, 0])
    avatar_h = model.bible.number("tech.units.avatar_h", 5) if model.bible.ok() else 5
    probe = Sim(model, [name], speed)
    snaps = []
    n = int(seconds * fps)
    for i in range(n):
        probe.run_to((i + 1) / fps)
        if i % 3 == 0:
            snaps.append(Sim(model, [name], speed))
            snaps[-1].run_to((i + 1) / fps)
    x0, x1, y0, y1 = frame_bounds(snaps, anchor, avatar_h)
    span = max(x1 - x0, (y1 - y0) * W / H, 10) * 1.1
    view = Side(W, H, (x0 + x1) / 2, (y0 + y1) / 2, min(40.0, W / span))
    s = Sim(model, [name], speed)
    bd = backdrops(model)["sky"]
    frames = []
    for i in range(n):
        s.run_to((i + 1) / fps)
        frames.append(panel(model, s, bd, W, H, view, f"{name} t={s.t:.1f}s", avatar_h, anchor).quantize(colors=128))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0)
    return {"preset": name, "out": str(out), "frames": n}


# ------------------------------------------------------------------ POV composite
def warm_time(model, names):
    loops = [n for n in names if model.presets[n]["kind"] == "loop"]
    life = max((L["props"].get("Lifetime", ("range", 1, 1))[2] for n in loops for L in model.presets[n]["layers"]
                if L["class"] == "ParticleEmitter"), default=1)
    return life * 1.5 + 0.5 if loops else 0.0


def luma(im, mask):
    st = ImageStat.Stat(im.convert("L"), mask)
    return st.mean[0] if st.count[0] else 0.0


def pov(model, names, view_path, out, speed=None, t=None, plate=None, tier="pc"):
    """Loops at steady state; bursts fire after the loops warm up and are shown t s later (default 0.4)."""
    view = json.loads(Path(view_path).read_text())
    base = Path(view_path).parent
    plate = plate or base / view["plate"]
    im = Image.open(plate).convert("RGB")
    if list(im.size) != list(view["res"]):
        im = im.resize(tuple(view["res"]))
    speed = model.meta.get("speed_max") or 50 if speed is None else speed
    warm = warm_time(model, names)
    has_burst = any(model.presets[n]["kind"] == "burst" for n in names)
    t_after = (0.4 if t is None else t) if has_burst else 0.0
    sim = Sim(model, names, speed, tier, burst_at=warm)
    sim.run_to(warm + t_after)
    cam = Pinhole(view)
    depth = None
    if view.get("depth") and (base / view["depth"]).is_file():
        depth = Image.open(base / view["depth"])
    count = Image.new("L", im.size, 0)
    light = view.get("particle_light", [1, 1, 1])
    plate_im = im.copy()
    per = {}
    draw_beams(im, sim, cam, light)
    hidden = draw_particles(im, sim, cam, light=light, fog=view.get("fog"), depth=depth,
                            depth_scale=view.get("depth_scale", 16), count=count, per=per)
    draw_debris(im, sim, cam)
    draw_lights(im, sim, cam)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    hist = count.histogram()
    covered = sum(hist[1:])
    total = im.width * im.height
    mx = max((i for i, v in enumerate(hist) if v), default=0)
    acc, p95 = 0, 0
    for i in range(1, 256):
        acc += hist[i]
        if covered and acc >= 0.95 * covered:
            p95 = i
            break
    mean = sum(i * v for i, v in enumerate(hist)) / covered if covered else 0
    presets = {}
    for n in names:
        st = per.get(n)
        if not st:   # lights, beams or debris only: no particle stats
            presets[n] = {"live": 0, "visible": 0, "hidden": 0, "offscreen": 0, "covered": 0.0, "dluma": None, "peak": None}
            continue
        m = st.pop("mask")
        cov = sum(m.histogram()[1:])
        peak = None
        if cov:   # 90th percentile of the luma change over its pixels: how hard its core reads against the plate
            h = ImageChops.difference(im.convert("L"), plate_im.convert("L")).histogram(mask=m)
            acc, tot = 0, sum(h)
            peak = next((i for i, v in enumerate(h) if (acc := acc + v) >= 0.9 * tot), 0)
        presets[n] = {**st, "covered": round(cov / total, 4),
                      "dluma": round(luma(im, m) - luma(plate_im, m), 1) if cov else None, "peak": peak}
    return {"out": str(out), "presets": names, "speed": speed, "tier": tier, "t": round(warm + t_after, 2),
            "live": sim.live(), "hidden_by_depth": hidden, "overdraw_max": mx, "overdraw_p95": p95,
            "overdraw_mean": round(mean, 2), "screen_covered": round(covered / total, 4), "per_preset": presets,
            "camera": view.get("camera"), "res": view["res"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("strip")
    s.add_argument("name")
    s.add_argument("--out", required=True)
    s.add_argument("--speed", type=float)
    s.add_argument("--quick", action="store_true")
    s = sub.add_parser("gif")
    s.add_argument("name")
    s.add_argument("--out", required=True)
    s.add_argument("--seconds", type=float, default=3.0)
    s.add_argument("--fps", type=int, default=12)
    s.add_argument("--speed", type=float)
    s.add_argument("--quick", action="store_true")
    s = sub.add_parser("pov")
    s.add_argument("names", help="comma-separated effect presets")
    s.add_argument("--view", required=True, help="view.json written by lookdev_bpy.py")
    s.add_argument("--out", required=True)
    s.add_argument("--plate", help="override the plate image named in view.json")
    s.add_argument("--speed", type=float)
    s.add_argument("--time", type=float, help="seconds after the bursts fire (loops warm up first)")
    s.add_argument("--tier", choices=["pc", "phone"], default="pc", help="rate scale by priority (budgets.json tiers)")
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 2
    model = vfx.Model()   # presets: $RR_VFX_PRESETS or the shipped library
    if a.cmd == "pov":
        names = [n for n in a.names.split(",") if n]
    else:
        names = [a.name]
    bad = [n for n in names if n not in model.presets]
    if bad:
        print(f"unknown preset(s): {', '.join(bad)}; presets: {', '.join(model.presets)}", file=sys.stderr)
        return 2
    if a.cmd == "strip":
        r = strip(model, a.name, a.out, a.speed, a.quick)
    elif a.cmd == "gif":
        r = gif(model, a.name, a.out, a.seconds, a.fps, a.speed, a.quick)
    else:
        r = pov(model, names, a.view, a.out, a.speed, a.time, a.plate, a.tier)
    print(json.dumps(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
