#!/usr/bin/env python3
"""rr-game-feel plots and previews (Pillow). Imported by feel.py; run `feel.py plot ...` or `feel.py preview ...`.

plot    curves   easing sheet: 11 Roblox styles x In/Out/InOut, the styles the presets use are marked
        lever    finger vs knob (heavy until the detent), snap and snapback over time
        sustain  constant camera motion on a phone vs Speed and vs pressure, with the comfort limit
        EVENT    sparkline lanes per channel (camera, FOV, flash, each UI target, haptic), hit-stop shaded,
                 reduce-motion dashed; `all` = every plot
        --compare DUMP  overlays a Studio curve dump (RR_FeelDemo DUMP: lines "Style,Direction,t,value")

preview GROUP|EVENT|all: per group folder: hero peak frame (phone 844x390, true size), feel matrix, timelines,
        filmstrip, optional GIFs, contact.png + closeups.png via multiuse-critic contact_sheet.py, facts.md,
        preview.json. The phone plate is a mock (not Roblox rendering); the world keeps scrolling during hit-stop
        because the server moves it.
"""
import json, math, re, subprocess, sys, textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.dont_write_bytecode = True
import feelmath as fm

# chart roles (dataviz reference palette, light mode): recessive grid, ink text, slots 1-3 only
SURF, INK, INK2, GRID, BAND = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#ecebe7"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a")
FONTS = {}


def font(size=12):
    if size not in FONTS:
        try:
            FONTS[size] = ImageFont.load_default(size=size)
        except TypeError:
            FONTS[size] = ImageFont.load_default()
    return FONTS[size]


def rgb(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + ((a,) if a is not None else ())


def dashed(d, pts, fill, width=2, dash=6, gap=4):
    on, left = True, dash
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        pos = 0.0
        while seg > 0 and pos < seg:
            step = min(left, seg - pos)
            if on:
                a, b = pos / seg, (pos + step) / seg
                d.line([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)], fill=fill, width=width)
            pos += step
            left -= step
            if left <= 1e-9:
                on, left = not on, (gap if on else dash)


# ------------------------------------------------------------------ lanes from a sample
def lanes_of(model, name, s):
    """Group sample lanes into display lanes: [(title, unit_label, [(label, values, colour_idx)], normalised)]."""
    L, chans = s["lanes"], s["meta"]["channels"]
    out = []
    cam = {a: [0.0] * len(s["t"]) for a in ("pitch", "yaw", "roll")}
    has_cam = False
    for k, v in L.items():
        for a in cam:
            if k.endswith(":" + a) and (k.startswith("cam:") or ":camkick:" in k):
                has_cam = has_cam or any(abs(x) > 1e-6 for x in v)
                cam[a] = [p + q for p, q in zip(cam[a], v)]
    if has_cam:
        pv = model.phone()
        peak = max(math.hypot(p, y) for p, y in zip(cam["pitch"], cam["yaw"]))
        out.append(("camera", f"deg, peak {peak:.2f} ({pv.deg_px(peak):.0f} px)",
                    [(a, cam[a], i) for i, a in enumerate(("pitch", "yaw", "roll"))], False))
    fov = [k for k in L if k.endswith(":fovkick")]
    if fov:
        vals = [sum(L[k][i] for k in fov) for i in range(len(s["t"]))]
        out.append(("FOV", f"deg, peak {max(vals, key=abs):+.1f}", [("delta", vals, 0)], False))
    fl = [k for k in L if ":flash:" in k]
    if fl:
        def flabel(k):
            ch = chans[int(k.split(":")[0])][0]
            return f"{ch['scope']} {ch.get('target', '')} {ch['color']}".replace("  ", " ")
        ser = [(flabel(k), L[k], i) for i, k in enumerate(fl[:3])]
        pk = max(max(v) for _, v, _ in ser)
        out.append(("flash", (ser[0][0] + ", " if len(ser) == 1 else "") + f"opacity, peak {pk:.2f}", ser, False))
    targets = {}
    for k in L:
        parts = k.split(":")
        if parts[1] in ("tween", "punch", "pulse") and len(parts) >= 4:
            targets.setdefault(parts[2], []).append(k)
    for tgt, keys in targets.items():
        ser, desc = [], []
        for i, k in enumerate(keys[:3]):
            v = L[k]
            kind, prop = k.split(":")[1], k.split(":")[3]
            lo, hi = min(v), max(v)
            desc.append(f"{prop} {'punch ' if kind == 'punch' else ''}{lo:.3g}..{hi:.3g}")
            ser.append((f"{kind} {prop}", v, i))
        out.append((tgt, ", ".join(desc), ser, True))
    hp = [k for k in L if k.endswith(":haptic")]
    if hp:
        vals = [min(1.0, sum(L[k][i] for k in hp)) for i in range(len(s["t"]))]
        out.append(("haptic", f"0..1, peak {max(vals):.2f}", [("motor", vals, 0)], False))
    return out


def timeline(model, name, w=760, h=250, rm_overlay=True, reduce_motion=False, title=None, max_lanes=6):
    s = fm.sample_event(model.r, name, reduce_motion=reduce_motion)
    srm = fm.sample_event(model.r, name, reduce_motion=True) if (rm_overlay and not reduce_motion) else None
    lanes = lanes_of(model, name, s)[:max_lanes]
    lrm = {ln[0]: ln for ln in lanes_of(model, name, srm)} if srm else {}
    img = Image.new("RGB", (w, h), SURF)
    d = ImageDraw.Draw(img)
    ev = model.events[name]
    head = title or f"{name}  ·  tier {ev['priority']}  ·  {'REDUCE MOTION' if reduce_motion else 'full'}" + \
        ("  (dashed = reduce motion)" if srm else "")
    d.text((8, 5), head, fill=INK, font=font(13))
    left, right, top, bottom = 150, w - 12, 26, h - 22
    T = s["t"][-1]
    X = lambda t: left + (right - left) * t / T  # noqa: E731
    for a, b in s["meta"]["hitstop"]:
        d.rectangle([X(a), top, max(X(b), X(a) + 2), bottom], fill=BAND)
        d.text((X(a) + 2, bottom + 2), "hit-stop", fill=INK2, font=font(10))
    n = max(1, len(lanes))
    lh = (bottom - top) / n
    step = 0.25 if T <= 2.5 else 0.5
    t = 0.0
    while t <= T + 1e-9:
        d.line([(X(t), top), (X(t), bottom)], fill=GRID, width=1)
        d.text((X(t) - 8, bottom + 8), f"{t:g}s", fill=INK2, font=font(10))
        t += step
    if not lanes:
        d.text((left, top + 10), "no motion, flash or haptic channels (cues only)", fill=INK2, font=font(12))
    for li, (lt, unit, ser, norm) in enumerate(lanes):
        y0, y1 = top + li * lh + 3, top + (li + 1) * lh - 3
        d.line([(left, y1 + 3), (right, y1 + 3)], fill=GRID)
        d.text((8, y0 + 1), lt, fill=INK, font=font(12))
        for j, ln in enumerate(textwrap.wrap(unit, 26)[:max(1, int((lh - 16) // 12))]):
            d.text((8, y0 + 15 + 12 * j), ln, fill=INK2, font=font(10))
        allv = [x for _, v, _ in ser for x in v]
        rmser = lrm.get(lt, (None, None, [], None))[2]
        if not norm:
            allv += [x for _, v, _ in rmser for x in v]
        lo, hi = min(allv + [0.0]), max(allv + [0.0])
        if hi - lo < 1e-9:
            hi = lo + 1

        def Y(v, lo=lo, hi=hi, vlo=None, vhi=None):
            if vlo is not None:
                v = 0.5 if vhi - vlo < 1e-9 else (v - vlo) / (vhi - vlo)
                return y1 - (y1 - y0) * v
            return y1 - (y1 - y0) * (v - lo) / (hi - lo)
        if not norm and lo < 0 < hi:
            d.line([(left, Y(0)), (right, Y(0))], fill=GRID)
        ranges = {}
        for label, v, ci in ser:
            vl, vh = (min(v), max(v)) if norm else (None, None)
            ranges[label] = (vl, vh, ci)
            pts = [(X(tt), Y(x, vlo=vl, vhi=vh)) for tt, x in zip(s["t"], v)]
            d.line(pts, fill=SERIES[ci], width=2)
        for label, v, ci in rmser:
            if norm and label not in ranges:
                continue
            vl, vh, ci = ranges.get(label, (None, None, ci))
            if norm and max(v) - min(v) < 1e-9 and abs(v[0] - (vh if vh is not None else 0)) < 1e-9:
                continue
            pts = [(X(tt), Y(x, vlo=vl, vhi=vh)) for tt, x in zip(srm["t"], v) if tt <= T]
            dashed(d, pts, SERIES[ci], 2)
        if len(ser) > 1:
            lx = right - 6
            for label, v, ci in reversed(ser):
                tw = d.textlength(label, font=font(10))
                lx -= tw + 18
                d.line([(lx, y0 + 7), (lx + 10, y0 + 7)], fill=SERIES[ci], width=2)
                d.text((lx + 13, y0 + 1), label, fill=INK2, font=font(10))
    return img


# ------------------------------------------------------------------ plots
def plot_curves(model, out, compare=None):
    used = set()
    for ev in model.raw["events"].values():
        for ch in ev.get("channels", []):
            if ch.get("type") == "tween":
                used.add((ch.get("style", "Quad"), ch.get("dir", "Out")))
    for k in ("snap", "snapback"):
        used.add((model.r["lever"][k]["style"], model.r["lever"][k]["dir"]))
    dump = {}
    if compare:
        # Studio Output adds a timestamp before and "  -  Client - Script:line" after lines: find the CSV anywhere
        row = re.compile(r"\b(" + "|".join(fm.STYLES) + r"),(In|Out|InOut),(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?(?:[eE]-?\d+)?)")
        for line in Path(compare).read_text(errors="replace").splitlines():
            for mt in row.finditer(line):
                dump.setdefault((mt.group(1), mt.group(2)), []).append((float(mt.group(3)), float(mt.group(4))))
        if not dump:
            return None
    cw, chh, cols = 140, 112, 11
    W, H = cols * cw + 20, 3 * chh + 60
    img = Image.new("RGB", (W, H), SURF)
    d = ImageDraw.Draw(img)
    title = "Roblox easing (Penner forms, as RR_FeelMath)  ·  filled dot = used by the presets"
    if dump:
        title += "  ·  orange dots = Studio TweenService:GetValue dump"
    d.text((10, 8), title, fill=INK, font=font(13))
    worst = {}
    for r, dr in enumerate(fm.DIRECTIONS):
        for c, st in enumerate(fm.STYLES):
            x0, y0 = 10 + c * cw, 34 + r * chh
            px0, px1, py0, py1 = x0 + 8, x0 + cw - 10, y0 + 22, y0 + chh - 10
            Y = lambda v: py1 - (py1 - py0) * (v + 0.35) / 1.7  # noqa: E731
            d.rectangle([px0, py0, px1, py1], outline=GRID)
            d.line([(px0, Y(0)), (px1, Y(0))], fill=GRID)
            d.line([(px0, Y(1)), (px1, Y(1))], fill=GRID)
            d.text((x0 + 8, y0 + 5), f"{st} {dr}", fill=INK, font=font(11))
            if (st, dr) in used:
                d.ellipse([x0 + cw - 20, y0 + 7, x0 + cw - 12, y0 + 15], fill=SERIES[0])
            pts = [(px0 + (px1 - px0) * i / 60, Y(fm.ease(st, dr, i / 60))) for i in range(61)]
            d.line(pts, fill=SERIES[0], width=2)
            for tt, v in dump.get((st, dr), []):
                d.ellipse([px0 + (px1 - px0) * tt - 2, Y(v) - 2, px0 + (px1 - px0) * tt + 2, Y(v) + 2], fill=SERIES[1])
                worst[(st, dr)] = max(worst.get((st, dr), 0), abs(v - fm.ease(st, dr, tt)))
    name = "compare.png" if dump else "easing.png"
    img.save(out / name)
    lines = [f"wrote {out / name}"]
    if dump:
        bad = {k: v for k, v in worst.items() if v > 0.01}
        lines.append(f"compare: {len(worst)} curves from the dump; max error {max(worst.values(), default=0):.4f}")
        for (st, dr), e in sorted(bad.items(), key=lambda x: -x[1]):
            lines.append(f"  DIFF {st} {dr}: max |studio - python| = {e:.4f} (preview approximates this style)")
        if not bad:
            lines.append("  all within 0.01: previews match the engine curves")
    return lines


def plot_lever(model, out):
    lv = model.r["lever"]
    W, H = 900, 300
    img = Image.new("RGB", (W, H), SURF)
    d = ImageDraw.Draw(img)
    d.text((10, 8), f"Lever drag (two-way, one side shown): knob = detent x (finger/detent)^{lv['resist']}, tick at "
                    f"{lv.get('notch', lv['detent']):.0%}, commit at {lv['detent']:.0%} (OQ-031 default: drag console)",
           fill=INK, font=font(13))
    panels = [("finger -> knob (fraction of travel)", 0), ("after commit: snap home", 1), ("released early: snapback", 2)]
    for pi, (ttl, kind) in enumerate(panels):
        x0 = 10 + pi * 296
        px0, px1, py0, py1 = x0 + 34, x0 + 280, 60, 262
        d.text((x0 + 6, 36), ttl, fill=INK, font=font(12))
        d.rectangle([px0, py0, px1, py1], outline=GRID)
        Y = lambda v: py1 - (py1 - py0) * (v + 0.1) / 1.3  # noqa: E731
        for v in (0, 0.5, 1):
            d.line([(px0, Y(v)), (px1, Y(v))], fill=GRID)
            d.text((x0 + 6, Y(v) - 6), f"{v:g}", fill=INK2, font=font(10))
        if kind == 0:
            X = lambda u: px0 + (px1 - px0) * u  # noqa: E731
            dashed(d, [(X(0), Y(0)), (X(1), Y(1))], INK2, 1)
            pts = [(X(i / 100), Y(fm.lever_display(i / 100, lv["detent"], lv["resist"]))) for i in range(int(lv["detent"] * 100))]
            d.line(pts, fill=SERIES[0], width=2)
            d.line([(X(lv["detent"]), Y(lv["detent"])), (X(lv["detent"]), Y(1))], fill=SERIES[1], width=2)
            if lv.get("notch"):
                nx = X(lv["notch"])
                dashed(d, [(nx, Y(0)), (nx, Y(1))], SERIES[2] if len(SERIES) > 2 else INK2, 1)
                d.text((nx - 30, Y(0.12)), "tick", fill=INK2, font=font(10))
            d.text((X(lv["detent"]) + 4, Y(0.35)), "detent:\ncommit", fill=INK2, font=font(10))
            d.text((X(0.02), Y(0.95)), "dashed = finger", fill=INK2, font=font(10))
        else:
            sp = lv["snap"] if kind == 1 else lv["snapback"]
            a0, a1 = (lv["detent"], 1.0) if kind == 1 else (0.5, 0.0)
            T = sp["dur"] * 1.6
            X = lambda t: px0 + (px1 - px0) * t / T  # noqa: E731
            pts = [(X(T * i / 80), Y(a0 + (a1 - a0) * fm.ease(sp["style"], sp["dir"], min(1, T * i / 80 / sp["dur"])))) for i in range(81)]
            d.line(pts, fill=SERIES[0], width=2)
            d.text((px0 + 4, py1 - 16), f"{sp['style']} {sp['dir']} {sp['dur']} s", fill=INK2, font=font(10))
            d.text((px1 - 30, py1 + 4), f"{T:.2f}s", fill=INK2, font=font(10))
    img.save(out / "lever.png")
    return [f"wrote {out / 'lever.png'}"]


def plot_sustain(model, out):
    r, pv = model.r, model.phone()
    sh, near = r["shake"], float(r["meta"]["near_depth_studs"])
    lim = r["limits"]["sustain_px_max"]

    def px(floor):
        s = min(floor, sh["sustain_cap"]) ** sh["power"]
        return pv.deg_px(math.hypot(*sh["max_angle_deg"][:2]) * s) + pv.studs_px(math.hypot(*sh["max_offset_studs"][:2]) * s, near) \
            + pv.roll_edge_px(sh["max_angle_deg"][2] * s) * 0.5
    fast = float(r["sustain"]["speed"]["ref"])
    sp, pr = r["sustain"]["speed"], r["sustain"]["pressure"]
    W, H = 900, 300
    img = Image.new("RGB", (W, H), SURF)
    d = ImageDraw.Draw(img)
    d.text((10, 8), f"Sustained camera motion on a phone (peak px, upper bound)  ·  limit {lim} px (stable_train)", fill=INK, font=font(13))
    for pi, (ttl, xs, fn, xl) in enumerate([
            ("vs Speed (av.vfx.speed_link)", [fast * i / 50 for i in range(51)], lambda x: px(sp["gain"] * x / fast), "studs/s"),
            ("vs pressure 0..1 (OQ-013 default)", [i / 50 for i in range(51)],
             lambda x: px(pr["gain"] * fm.clamp((x - pr["threshold"]) / (1 - pr["threshold"]), 0, 1)), "of gauge"),
            ("both at max (capped)", [i / 50 for i in range(51)],
             lambda x: px((sp["gain"] + pr["gain"]) * x), "fraction")]):
        x0 = 10 + pi * 296
        px0, px1, py0, py1 = x0 + 34, x0 + 280, 60, 250
        d.text((x0 + 6, 36), ttl, fill=INK, font=font(12))
        d.rectangle([px0, py0, px1, py1], outline=GRID)
        top = max(lim * 1.4, 1)
        Y = lambda v: py1 - (py1 - py0) * v / top  # noqa: E731
        dashed(d, [(px0, Y(lim)), (px1, Y(lim))], INK2, 1)
        d.text((px0 + 4, Y(lim) - 13), f"limit {lim} px", fill=INK2, font=font(10))
        X = lambda x: px0 + (px1 - px0) * (x - xs[0]) / (xs[-1] - xs[0])  # noqa: E731
        d.line([(X(x), Y(fn(x))) for x in xs], fill=SERIES[0], width=2)
        d.text((px1 - 60, py1 + 4), f"{xs[-1]:g} {xl}", fill=INK2, font=font(10))
        d.text((px0, py1 + 4), f"{xs[0]:g}", fill=INK2, font=font(10))
        d.text((px1 - 70, Y(fn(xs[-1])) - 14), f"{fn(xs[-1]):.2f} px", fill=INK, font=font(10))
    img.save(out / "sustain.png")
    return [f"wrote {out / 'sustain.png'}"]


def plot(model, a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    what, lines = a.what, []
    if a.compare:
        got = plot_curves(model, out, a.compare)
        if got is None:
            print(f"--compare {a.compare}: no 'Style,Direction,t,value' rows found (paste the DUMP output lines)")
            return 2
        lines += got
    if what in ("curves", "all") and not a.compare:
        lines += plot_curves(model, out)
    if what in ("lever", "all"):
        lines += plot_lever(model, out)
    if what in ("sustain", "all"):
        lines += plot_sustain(model, out)
    names = list(model.events) if what == "all" else ([what] if what in model.events else
                                                       (model.names(what) if what not in ("curves", "lever", "sustain") else []))
    for n in names:
        timeline(model, n, 900, max(170, 70 + 56 * len(lanes_of(model, n, fm.sample_event(model.r, n)))), max_lanes=9).save(out / f"{n}.png")
    if names:
        lines.append(f"wrote {len(names)} event timelines to {out}/<event>.png")
    print("\n".join(lines))
    return 0


# ------------------------------------------------------------------ mock phone plate
class Plate:
    """A mock phone POV: world (sky, ground, rails, poles scrolling) + cab frame + HUD mock elements."""

    def __init__(self, model):
        self.m, self.r = model, model.r
        self.pv = model.phone()
        self.W, self.H = self.pv.w, self.pv.h
        pr = self.r["preview"]
        self.c = {k: pr[k] for k in ("sky", "ground", "ballast", "rail", "pole", "cab", "trim", "paper", "ink")}
        self.speed = float(pr["scroll_speed"])
        self.spacing = float(pr["pole_spacing"])
        tw, th = (int(x) for x in re.findall(r"\d+", str(pr["ticket_px"]))[:2])
        self.ticket = (tw, th)
        b = model.bible
        self.bv = lambda k, dft="": b.value(k, dft) if b.ok() else dft  # noqa: E731
        self.kind_cols = {}
        for kind in ("danger", "risk", "cash", "info"):
            key = f"ui.hud_kinds.{kind}_stub_top" if kind != "risk" else "ui.hud_kinds.risk_stripe"
            v = self.bv(key)
            self.kind_cols[kind] = v if re.match(r"^#[0-9A-Fa-f]{6}$", str(v)) else "#888888"

    def world(self, t):
        M = 70
        W, H = self.W + 2 * M, self.H + 2 * M
        img = Image.new("RGB", (W, H), rgb(self.c["sky"], None))
        d = ImageDraw.Draw(img)
        f, hy, cx, cam_h = self.pv.focal, M + self.H * 0.40, W / 2, 12.0
        d.rectangle([0, hy, W, H], fill=rgb(self.c["ground"], None))

        def P(x, z, y=0.0):
            return cx + f * x / z, hy + f * (cam_h - y) / z

        for half, col in ((12, self.c["ballast"]),):
            pts = [P(-half, 4), P(half, 4), P(half, 3000), P(-half, 3000)]
            d.polygon(pts, fill=rgb(col, None))
        for x in (-4, 4):
            d.line([P(x, 3.2), P(x, 3000)], fill=rgb(self.c["rail"], None), width=3)
        off = (self.speed * t) % self.spacing
        for side in (-1, 1):
            for k in range(0, 12):
                z = 20 + k * self.spacing - off
                if z < 6:
                    continue
                x0, yb = P(side * 16, z)
                _, yt = P(side * 16, z, 22)
                wpx = max(1, 60 / z * 3)
                d.rectangle([x0 - wpx / 2, yt, x0 + wpx / 2, yb], fill=rgb(self.c["pole"], None))
        return img, M

    def cab(self):
        M = 70
        W, H = self.W + 2 * M, self.H + 2 * M
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        col, trim = rgb(self.c["cab"]), rgb(self.c["trim"])
        d.rectangle([0, 0, W, M + 34], fill=col)
        d.rectangle([0, H - M - 70, W, H], fill=col)
        d.rectangle([0, 0, M + 44, H], fill=col)
        d.rectangle([W - M - 44, 0, W, H], fill=col)
        d.line([(M + 44, H - M - 70), (W - M - 44, H - M - 70)], fill=trim, width=5)
        d.rectangle([M + 44, M + 34, W - M - 44, H - M - 70], outline=trim, width=4)
        return img

    @staticmethod
    def affine(img, size, dx, dy, roll_deg, scale, M):
        th = math.radians(roll_deg)
        a, b = math.cos(th) / scale, math.sin(th) / scale
        dd, e = -math.sin(th) / scale, math.cos(th) / scale
        ocx, ocy = size[0] / 2 + dx, size[1] / 2 + dy
        icx, icy = img.width / 2, img.height / 2
        c = icx - a * ocx - b * ocy
        f = icy - dd * ocx - e * ocy
        return img.transform(size, Image.AFFINE, (a, b, c, dd, e, f), resample=Image.BILINEAR)

    def frame(self, name, s, i, show_ui=None, label=True):
        L, chans, t = s["lanes"], s["meta"]["channels"], s["t"][i]
        cam = {a: 0.0 for a in ("pitch", "yaw", "roll", "x", "y")}
        for k, v in L.items():
            for a in cam:
                if (k == "cam:" + a) or (":camkick:" in k and k.endswith(":" + a)):
                    cam[a] += v[i]
        fov = sum(v[i] for k, v in L.items() if k.endswith(":fovkick"))
        sc = self.pv.fov_scale(fov)
        world, M = self.world(t)
        size = (self.W, self.H)
        near = float(self.r["meta"]["near_depth_studs"])
        far = float(self.r["meta"]["far_depth_studs"])
        dx = -self.pv.deg_px(cam["yaw"]) * (1 if cam["yaw"] >= 0 else -1)
        dy = self.pv.deg_px(cam["pitch"]) * (1 if cam["pitch"] >= 0 else -1)
        tx_far, ty_far = self.pv.focal * cam["x"] / far, self.pv.focal * cam["y"] / far
        tx_n, ty_n = self.pv.focal * cam["x"] / near, self.pv.focal * cam["y"] / near
        frame = self.affine(world, size, dx - tx_far, dy + ty_far, cam["roll"], sc, M).convert("RGBA")
        cab = self.affine(self.cab(), size, dx - tx_n, dy + ty_n, cam["roll"], sc, M)
        frame.alpha_composite(cab)
        self.hud(frame, name, s, i, show_ui)
        for idx, (ch, d0) in enumerate(chans):
            k = f"{idx}:flash:{ch.get('scope')}"
            if ch["type"] == "flash" and k in L and ch["scope"] != "element" and L[k][i] > 0:
                self.flash(frame, ch["color"], L[k][i], ch["scope"])
        d = ImageDraw.Draw(frame)
        frozen = any(a <= t < b for a, b in s["meta"]["hitstop"])
        if label:
            d.rectangle([0, 0, self.W, 18], fill=(11, 11, 11, 170))
            d.text((6, 3), f"{name}  t={t:.2f}s{'  HIT-STOP (own effects frozen; world keeps scrolling)' if frozen else ''}"
                           f"  ·  mock phone {self.W}x{self.H}", fill=(255, 255, 255, 255), font=font(11))
        return frame.convert("RGB")

    def flash(self, frame, col, alpha, scope):
        if scope == "screen":
            ov = Image.new("RGBA", frame.size, rgb(col, int(255 * min(1, alpha))))
        else:
            ov = Image.new("RGBA", frame.size, (0, 0, 0, 0))
            px = ov.load()
            W, H = frame.size
            base = rgb(col, None)
            for y in range(0, H, 2):
                for x in range(0, W, 2):
                    dn = max(abs(x - W / 2) / (W / 2), abs(y - H / 2) / (H / 2))
                    a = int(255 * min(1, alpha) * max(0.0, (dn - 0.55) / 0.45) ** 1.5)
                    if a:
                        for yy in (y, y + 1):
                            for xx in (x, x + 1):
                                if xx < W and yy < H:
                                    px[xx, yy] = base + (a,)
        frame.alpha_composite(ov)

    # ---- HUD mock
    def props(self, s, i, target):
        """Composite transform for a UI role at frame i: dx, dy (px), scale, rot, alpha, count."""
        L, chans = s["lanes"], s["meta"]["channels"]
        out = {"dx": 0.0, "dy": 0.0, "scale": 1.0, "rot": 0.0, "alpha": 1.0, "count": None, "punch": 0.0}
        latest = {}
        for idx, (ch, d0) in enumerate(chans):
            if ch.get("target") != target:
                continue
            k = f"{idx}:{ch['type']}:{target}:{ch.get('prop')}"
            tau = s["tau"][i]
            if ch["type"] == "tween" and k in L:
                started = tau >= d0
                prev = latest.get(ch["prop"])
                if prev is None or (started and d0 >= prev[0]):
                    latest[ch["prop"]] = (d0 if started else -1, L[k][i])
                for suffix, inv in (("fadealpha", False), ("hidden", True)):
                    fk = f"{idx}:tween:{target}:{suffix}"
                    if fk in L:
                        out["alpha"] *= (1 - L[fk][i]) if inv else L[fk][i]
            elif ch["type"] == "punch" and k in L:
                v = L[k][i]
                p = ch["prop"]
                if p == "scale":
                    out["scale"] *= 1 + v
                elif p == "rot":
                    out["rot"] += v
                elif p == "x_px":
                    out["dx"] += v
                elif p == "y_px":
                    out["dy"] += v
            elif ch["type"] == "pulse" and k in L:
                out["alpha"] *= L[k][i] if ch["prop"] == "alpha" else 1
                if ch["prop"] == "scale":
                    out["scale"] *= L[k][i]
        for p, (_, v) in latest.items():
            if p == "scale":
                out["scale"] *= v
            elif p == "rot":
                out["rot"] += v
            elif p == "alpha":
                out["alpha"] *= v
            elif p == "count":
                out["count"] = v
            elif p in ("x", "y"):
                out["d" + p + "_frac"] = v
            elif p in ("x_px", "y_px"):
                out["d" + p[0]] += v
        return out

    def place(self, frame, el, cx, cy, pr):
        w, h = el.size
        if abs(pr["scale"] - 1) > 1e-3:
            el = el.resize((max(1, int(w * pr["scale"])), max(1, int(h * pr["scale"]))), Image.BILINEAR)
        if abs(pr["rot"]) > 0.05:
            el = el.rotate(-pr["rot"], resample=Image.BILINEAR, expand=True)
        if pr["alpha"] < 0.999:
            a = el.getchannel("A").point(lambda v: int(v * max(0.0, min(1.0, pr["alpha"]))))
            el.putalpha(a)
        frame.alpha_composite(el, (int(cx - el.width / 2), int(cy - el.height / 2)))

    def card(self, w, h, fill, stub=None, text="", stamp=None, radius=11):
        el = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
        d = ImageDraw.Draw(el)
        d.rounded_rectangle([4, 4, w + 3, h + 3], radius=radius, fill=rgb(fill), outline=rgb(self.c["ink"]), width=3)
        if stub:
            d.rounded_rectangle([6, 6, 60, h + 1], radius=9, fill=rgb(stub))
        if text:
            d.text((68 if stub else 14, 12), text, fill=rgb(self.c["ink"]), font=font(15))
        return el

    def hud(self, frame, name, s, i, show_ui):
        ev = self.m.events[name]
        targets = {ch.get("target") for ch, _ in s["meta"]["channels"] if ch.get("target")}
        W, H = self.W, self.H
        tw, th = self.ticket
        alert = ev.get("alert") or next((self.m.events[inc["event"]].get("alert") for inc in ev.get("include", [])
                                          if self.m.events[inc["event"]].get("alert")), None)
        if "ticket" in targets or alert:
            kind = "info"
            text, stamp_txt = "", None
            if alert:
                f = self.m.bible.fact(alert) if self.m.bible.ok() else None
                if f:
                    m = re.search(r"kind (\w+)", f.get("note", ""))
                    kind = m[1] if m else kind
                    parts = [p.strip() for p in str(f["value"]).split(" / ")]
                    text = parts[0]
                    stamp_txt = parts[2] if len(parts) > 2 else None
            pr = self.props(s, i, "ticket")
            cx = W - 18 - tw / 2 + pr.get("dx_frac", 0) * tw + pr["dx"]
            cy = H - 96 - th / 2 + pr["dy"]
            if "halo" in targets:
                hp = self.props(s, i, "halo")
                halo = Image.new("RGBA", (tw + 26, th + 22), (0, 0, 0, 0))
                ImageDraw.Draw(halo).rounded_rectangle([2, 2, tw + 22, th + 18], radius=18,
                                                       fill=rgb(self.bv("style.brand.danger_red", "#E23A2E")))
                self.place(frame, halo, cx, cy, {**pr, "alpha": pr["alpha"] * hp["alpha"], "rot": 0, "scale": pr["scale"]})
            el = self.card(tw, th, self.c["paper"], stub=self.kind_cols.get(kind), text=text)
            self.place(frame, el, cx, cy, pr)
            if stamp_txt and ("stamp" in targets or "cash" in targets):
                sp = self.props(s, i, "stamp")
                cp = self.props(s, i, "cash")
                txt = stamp_txt
                if cp["count"] is not None:
                    n = re.search(r"\d[\d,]*", stamp_txt)
                    if n:
                        txt = stamp_txt.replace(n[0], str(int(float(n[0].replace(",", "")) * cp["count"])))
                st = Image.new("RGBA", (76, 42), (0, 0, 0, 0))
                ImageDraw.Draw(st).rounded_rectangle([2, 2, 73, 39], radius=6, outline=rgb(self.kind_cols.get(kind)), width=3,
                                                     fill=rgb(self.c["paper"]))
                ImageDraw.Draw(st).text((12, 11), txt, fill=rgb(self.c["ink"]), font=font(16))
                base_rot = -8.0 if not any(ch.get("target") == "stamp" and ch.get("prop") == "rot" for ch, _ in s["meta"]["channels"]) else 0.0
                self.place(frame, st, cx + tw / 2 - 50, cy - 4, {**sp, "rot": sp["rot"] + base_rot, "alpha": sp["alpha"] * pr["alpha"]})
        if "gauge" in targets:
            pr = self.props(s, i, "gauge")
            g = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            d = ImageDraw.Draw(g)
            d.ellipse([4, 4, 60, 60], fill=rgb(self.c["paper"]), outline=rgb(self.c["ink"]), width=3)
            d.line([(32, 32), (18, 44)], fill=rgb(self.c["ink"]), width=3)
            self.place(frame, g, 60, 70, pr)
        if targets & {"lever_panel", "lever_knob", "lamp", "timer"}:
            pr = self.props(s, i, "lever_panel")
            pw, ph = 300, 90
            el = Image.new("RGBA", (pw + 8, ph + 8), (0, 0, 0, 0))
            d = ImageDraw.Draw(el)
            d.rounded_rectangle([4, 4, pw + 3, ph + 3], radius=12, fill=rgb(self.bv("ui.lever.panel_steel", "#48546E")),
                                outline=rgb(self.bv("ui.lever.ink", "#161B26")), width=3)
            tp = self.props(s, i, "timer")
            tcol = rgb(self.bv("style.brand.hazard_yellow", "#F2C230"), int(255 * max(0, min(1, tp["alpha"]))))
            d.rectangle([20, 12, pw - 12, 20], fill=tcol)
            lamp_a = 0.0
            for idx, (ch, d0) in enumerate(s["meta"]["channels"]):
                if ch["type"] == "flash" and ch.get("target") == "lamp":
                    lamp_a = max(lamp_a, s["lanes"].get(f"{idx}:flash:element", [0] * (i + 1))[i])
            lamp_col = rgb(self.bv("style.brand.hazard_yellow", "#F2C230")) if lamp_a > 0.05 else (60, 60, 60, 255)
            d.ellipse([14, 40, 34, 60], fill=lamp_col, outline=rgb(self.c["ink"]), width=2)
            kp = self.props(s, i, "lever_knob")
            knob_x = 70 if name in ("lever_commit", "route_locked") else pw / 2
            kr = 22 * kp["scale"]
            d.line([(pw / 2, 70), (knob_x, 48)], fill=rgb(self.c["ink"]), width=6)
            d.ellipse([knob_x - kr, 48 - kr, knob_x + kr, 48 + kr], fill=rgb(self.bv("ui.lever.knob", "#F0604C")),
                      outline=rgb(self.c["ink"]), width=3)
            self.place(frame, el, W / 2 + pr["dx"] + pr.get("dx_frac", 0) * pw, H - 62 + pr["dy"] + pr.get("dy_frac", 0) * ph, pr)
        if "button" in targets:
            pr = self.props(s, i, "button")
            self.place(frame, self.card(120, 44, self.bv("style.brand.hazard_yellow", "#F2C230"), radius=20), W - 110, 120, pr)
        if "panel" in targets:
            pr = self.props(s, i, "panel")
            self.place(frame, self.card(360, 190, self.c["paper"], radius=16), W / 2, H / 2, pr)
        if targets & {"report", "report_stamp"}:
            pr = self.props(s, i, "report")
            self.place(frame, self.card(380, 220, self.c["paper"], radius=14), W / 2, H / 2, pr)
            sp = self.props(s, i, "report_stamp")
            m = re.search(r"a (.+?) stamp", str(self.bv("av.vfx.boiler_fail")))
            st = Image.new("RGBA", (190, 54), (0, 0, 0, 0))
            d = ImageDraw.Draw(st)
            red = rgb(self.bv("style.brand.danger_red", "#E23A2E"))
            d.rounded_rectangle([3, 3, 186, 50], radius=6, outline=red, width=4)
            d.text((14, 16), m[1] if m else "", fill=red, font=font(18))
            self.place(frame, st, W / 2 + 40, H / 2 + 30, sp)


# ------------------------------------------------------------------ preview
def activity(model, s, i):
    L = s["lanes"]
    cam = sum(abs(v[i]) for k, v in L.items() if k.startswith("cam:") and k[4:] in ("pitch", "yaw", "roll")) + \
        sum(abs(v[i]) for k, v in L.items() if ":camkick:" in k)
    fl = sum(v[i] for k, v in L.items() if ":flash:" in k)
    fov = sum(abs(v[i]) for k, v in L.items() if k.endswith(":fovkick"))
    ui = sum(abs(v[i]) for k, v in L.items() if ":punch:" in k and k.endswith(":scale")) * 10 + \
        sum(abs(v[i]) for k, v in L.items() if ":punch:" in k and k.endswith("_px")) / 5
    tw = 0.0
    for k, v in L.items():
        parts = k.split(":")
        if parts[1] != "tween" or parts[3] in ("alpha", "count", "fadealpha", "hidden"):
            continue
        hid = L.get(f"{parts[0]}:tween:{parts[2]}:hidden")
        if hid and hid[i] > 0:
            continue
        vis = 1.0
        for k2, v2 in L.items():   # a slide counts only while the target is visible
            p2 = k2.split(":")
            if p2[1] == "tween" and p2[2] == parts[2] and p2[3] in ("alpha", "fadealpha"):
                vis *= v2[i]
        tw += abs(v[i] - v[-1]) * vis * (0.5 if parts[3] in ("x", "y") else 1.0)
    return cam * 2 + fl * 3 + fov / 3 + ui + tw


def matrix(model, names, group, w=700, h=390):
    from feel import metrics
    allm = {n: metrics(model, n) for n in model.events}
    refs = []
    for tier in sorted({e["priority"] for e in model.events.values()}):
        cands = [n for n in model.events if model.events[n]["priority"] == tier and n not in names]
        if cands:
            refs.append(max(cands, key=lambda n: allm[n]["loudness"]))
    rows = sorted(names, key=lambda n: (model.events[n]["priority"], -allm[n]["loudness"]))
    rows = [(n, True) for n in rows] + [(n, False) for n in refs]
    rows.sort(key=lambda x: (model.events[x[0]]["priority"], -allm[x[0]]["loudness"]))
    img = Image.new("RGB", (w, h), SURF)
    d = ImageDraw.Draw(img)
    d.text((8, 5), f"Feel matrix · {group} (grey rows: loudest event of other tiers, for scale)", fill=INK, font=font(13))
    cols = [("event", 8), ("tier", 178), ("cam px", 246), ("FOV", 298), ("stop ms", 336), ("flash", 392),
            ("haptic", 436), ("secs", 484), ("loudness 0-1", 526)]
    y = 28
    for c, x in cols:
        d.text((x, y), c, fill=INK2, font=font(11))
    d.line([(8, y + 16), (w - 8, y + 16)], fill=GRID)
    rh = min(26, (h - 70) / max(1, len(rows)))
    tiers = model.r["limits"]["tiers"]
    for ri, (n, mine) in enumerate(rows):
        m = allm[n]
        yy = y + 22 + ri * rh
        col = INK if mine else INK2
        vals = [n[:24], f"{m['tier']} {tiers[str(m['tier'])]}", f"{m['cam_px']:.0f}", f"{m['fov_signed']:+.0f}" if m["fov_signed"] else "-",
                str(m["hitstop_ms"] or "-"), f"{m['flash_peak']:.2f}" if m["flash_peak"] else "-",
                f"{m['haptic_peak']:.1f}" if m["haptic_peak"] else "-", f"{m['total_s']:.1f}{'+' if m['loops'] else ''}"]
        for (c, x), v in zip(cols, vals):
            d.text((x, yy), v, fill=col, font=font(11))
        bx = 526
        bw = (w - 40 - bx) * m["loudness"]
        d.rounded_rectangle([bx, yy + 2, bx + max(4, bw), yy + rh - 6], radius=3, fill=SERIES[0] if mine else "#c3c2b7")
        d.text((bx + max(4, bw) + 4, yy), f"{m['loudness']:.2f}", fill=col, font=font(10))
    d.text((8, h - 18), "cam px = upper bound of camera motion on the phone; secs '+' = a loop keeps running (halo)", fill=INK2, font=font(10))
    return img


def filmstrip(model, name, s, plate, times, w=784, h=256):
    img = Image.new("RGB", (w, h), SURF)
    d = ImageDraw.Draw(img)
    fw, fh = 256, int(256 * plate.H / plate.W)
    for j, t in enumerate(times[:6]):
        i = min(len(s["t"]) - 1, int(round(t * 60)))
        fr = plate.frame(name, s, i, label=False).resize((fw, fh), Image.LANCZOS)
        x, y = 4 + (j % 3) * (fw + 6), 4 + (j // 3) * (fh + 16)
        img.paste(fr, (x, y + 14))
        frozen = any(a <= s["t"][i] < b for a, b in s["meta"]["hitstop"])
        d.text((x + 2, y), f"{name} t={s['t'][i]:.2f}s{' hit-stop' if frozen else ''}", fill=INK, font=font(11))
    return img


def row(images, gap=8, bg=SURF):
    W = sum(im.width for im in images) + gap * (len(images) - 1)
    H = max(im.height for im in images)
    out = Image.new("RGB", (W, H), bg)
    x = 0
    for im in images:
        out.paste(im, (x, 0))
        x += im.width + gap
    return out


def sheet(critic, out, items, extra=()):
    if not critic:
        print("multiuse-critic not found (RR_CRITIC_SKILL): contact sheet skipped")
        return 3
    r = subprocess.run([sys.executable, str(critic / "scripts" / "contact_sheet.py"), str(out), *items, *extra],
                       capture_output=True, text=True)
    if r.returncode not in (0,):
        print((r.stdout + r.stderr).strip())
    return r.returncode


def preview(model, a):
    from feel import metrics, find_sibling
    critic = find_sibling("multiuse-critic", "RR_CRITIC_SKILL")
    out = Path(a.out)
    sel = a.sel
    heroes = dict(model.r["preview"].get("heroes", {}))
    if sel in model.events:   # one event: its own folder, never over a group's files
        folder = getattr(a, "name", None) or f"ev_{sel}"
        groups = {folder: [sel]}
        heroes[folder] = sel
    elif "," in sel:          # a set of events (a mission's moments): one critic sees all of them
        names = model.names(sel)
        folder = getattr(a, "name", None) or f"set_{names[0]}"
        groups = {folder: names}
        heroes[folder] = names[0]
    else:
        names = model.names(sel)
        groups = {}
        for n in names:
            groups.setdefault(model.events[n]["group"], []).append(n)
    plate = Plate(model)
    lv = model.r["lever"]
    lever_events = {lv["detent_event"], lv["commit_event"], lv["snapback_event"]}
    rc_all = 0
    for group, names in groups.items():
        d = out / group
        d.mkdir(parents=True, exist_ok=True)
        hero = heroes.get(group) if heroes.get(group) in names else max(names, key=lambda n: metrics(model, n)["loudness"])
        s = fm.sample_event(model.r, hero, reduce_motion=a.rm)
        acts = [activity(model, s, i) for i in range(len(s["t"]))]
        ipk = max(range(len(acts)), key=lambda i: acts[i])
        plate.frame(hero, s, ipk).save(d / f"{hero}.peak.png")
        tpk = s["t"][ipk]
        tend = max(metrics(model, hero)["total_s"], tpk + 0.2)
        times = [0.0, tpk] + [tpk + (tend - tpk) * k / 4 for k in range(1, 5)]
        if tpk < 0.05:   # peak at the start: spread the rest evenly instead
            times = [0.0] + [tend * k / 5 for k in range(1, 6)]
        filmstrip(model, hero, s, plate, times).save(d / f"{hero}.strip.png")
        matrix(model, names, group).save(d / "matrix.png")
        timeline(model, hero, 760, 256).save(d / f"{hero}.timeline.png")
        row1 = row([Image.open(d / f"{hero}.peak.png"), Image.open(d / "matrix.png")])
        row2 = row([Image.open(d / f"{hero}.timeline.png"), Image.open(d / f"{hero}.strip.png")])
        row1.save(d / "_row1.png")
        row2.save(d / "_row2.png")
        rc = sheet(critic, d / "contact.png", [f"{hero} peak frame (phone true size) + feel matrix={d / '_row1.png'}@1",
                                                f"{hero} timeline (dashed: reduce motion) + filmstrip={d / '_row2.png'}@1"])
        others = [n for n in names if n != hero]
        tl = [timeline(model, hero, 500, 230, reduce_motion=True, rm_overlay=False)] + \
             [timeline(model, n, 500, 230) for n in others[:8]]
        for n, im in zip(["_rm_" + hero] + others, tl):
            im.save(d / f"{n.lstrip('_')}.timeline.png" if not n.startswith("_") else d / f"{hero}.rm.timeline.png")
        rows = [row(tl[k:k + 3]) for k in range(0, len(tl), 3)]
        if rows:
            grid = Image.new("RGB", (max(r_.width for r_ in rows), sum(r_.height for r_ in rows) + 8 * (len(rows) - 1)), SURF)
            y = 0
            for r_ in rows:
                grid.paste(r_, (0, y))
                y += r_.height + 8
            grid.save(d / "_grid.png")
            items = []
            if lever_events & set(names):   # the drag curve is the core of the lever feel: the critic must see it
                plot_lever(model, d)
                items.append(f"lever drag: finger to knob, tick, commit, snap home, snapback={d / 'lever.png'}@1")
            elif any("setSpeed" in model.events[n].get("trigger", "") or "setPressure" in model.events[n].get("trigger", "")
                     for n in names):   # one true-size plot fits beside the grid; the rumble numbers are in facts.md
                plot_sustain(model, d)
                items.append(f"sustained rumble vs Speed and pressure (stable_train limit)={d / 'sustain.png'}@1")
            items.append(f"{group}: {hero} with reduce motion, then the other events={d / '_grid.png'}" + ("" if items else "@1"))
            extra = ["--tile", "1300x402", "--max-width", "1528"] if len(items) > 1 else []
            rc2 = sheet(critic, d / "closeups.png", items, extra)
            rc = rc or rc2
        if a.gif:
            for n in names:
                gif(model, plate, n, d / f"{n}.gif", reduce_motion=a.rm)
        facts(model, names, hero, d, tpk)
        (d / "preview.json").write_text(json.dumps({"group": group, "hero": hero, "events": names, "rm": a.rm,
                                                    "peak_t": tpk}, indent=1))
        print(f"preview {group}: {d} (hero {hero}, peak t={tpk:.2f}s, {len(names)} events){' contact sheet FAILED' if rc else ''}")
        rc_all = rc_all or rc
    return 0 if rc_all in (0, 3) else 1


def gif(model, plate, name, path, reduce_motion=False, fps=30):
    s = fm.sample_event(model.r, name, reduce_motion=reduce_motion)
    frames = []
    step = max(1, 60 // fps)
    for i in range(0, len(s["t"]), step):
        frames.append(plate.frame(name, s, i).resize((plate.W // 2, plate.H // 2), Image.BILINEAR).quantize(64))
    frames += [frames[-1]] * 10
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0)


def facts(model, names, hero, d, tpk):
    from feel import metrics, sustain_metrics, hierarchy
    r = model.r
    pairs, _ = hierarchy(model)
    lines = [f"# Facts: feel presets, group {model.events[hero]['group']} (measured by feel.py)", "",
             f"- Phone {r['meta']['phone']}, FOV {r['meta']['fov_deg']}; camera px = rotation at the screen centre + translation of "
             f"geometry {r['meta']['near_depth_studs']} studs away + half the roll at the screen edge (upper bound).",
             f"- Limits: camera px by tier {r['limits']['tier_shake_px']}; hit-stop <= {r['limits']['hitstop_ms_max']} ms; "
             f"screen flash <= {r['a11y']['flash']['screen_peak_max']} (red {r['a11y']['flash']['red_peak_max']}), "
             f"<= {r['a11y']['flash']['per_second_max']}/s; events <= {r['limits']['event_s_max']} s (fail {r['limits']['fail_s_max']} s).",
             f"- Hero {hero}: peak frame at t={tpk:.2f} s. Filmstrip frames are the same mock at six times.",
             "- Punch amps and kick angles are delivered peaks; camera pitch + tips the view up, - down.", ""]
    for n in names:
        m, rm = metrics(model, n), metrics(model, n, reduce_motion=True)
        lines.append(f"- {n} (tier {m['tier']}, {model.events[n]['who']}): camera {m['cam_px']} px (roll {m['roll_deg']} deg, "
                     f"kick {m['kick_deg']} deg), FOV {m['fov_deg']}, hit-stop {m['hitstop_ms']} ms, screen flash "
                     f"{m['flash_peak']}{' red' if m['flash_red'] else ''}, haptic {m['haptic_peak']} for {m['haptic_ms']} ms, "
                     f"UI punch {m['punch_scale']:.0%} / {m['punch_px']} px, lasts {m['total_s']} s{' + loop' if m['loops'] else ''}, "
                     f"loudness {m['loudness']}. Reduce motion: camera {rm['cam_px']} px; reads through "
                     f"{', '.join(rm['communicates']) or 'no feel channel'}"
                     f"{'; outside feel: ' + model.events[n]['rm_reads'] if model.events[n].get('rm_reads') else ''}. "
                     "Outshouts: " + (", ".join(f"{o} (tier {model.events[o]['priority']}, {lo:.2f})" for o, lo in pairs.get(n, []))
                                      or "no higher-tier event") +
                     "".join(f"; {k}: {model.events[n][k]}" for k in ("loud_ok", "quiet_ok") if model.events[n].get(k)) + ".")
    sm = sustain_metrics(model)
    lines += ["", f"- Sustained rumble (constant while running): Speed at max {sm['speed']['px_max']} px, pressure at redline "
              f"{sm['pressure']['px_max']} px, both capped {sm['both']['px_max']} px (limit {r['limits']['sustain_px_max']} px).",
              "- Limits of these images: the plate is a mock (flat colours, default font, no Roblox lighting); easing uses "
              "Penner forms (compare with a Studio dump: feel.py plot curves --compare); sound cues are not shown; the world "
              "keeps scrolling during hit-stop because the server moves it. Studio test pending (owner)."]
    (d / "facts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    print(__doc__)
    sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
