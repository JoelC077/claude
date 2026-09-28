#!/usr/bin/env python3
"""rr-game-feel math: the exact formulas RR_FeelMath.lua uses, so plots and previews match the runtime.

  easing  ease(style, direction, t) for the 11 Roblox EasingStyles x In/Out/InOut (Penner forms)
  spring  spring(t, amp, freq_hz, damping, shape)   damped sine/cos punch, or decaying noise shake
  peak    peak_gain(freq_hz, damping, shape, dur)    largest |spring| of a unit spring: punches and camera kicks
                                                     divide by it, so amp and angles_deg are the delivered peak
  noise   noise1(seed, x)                            deterministic 1D gradient noise in [-1, 1]
  env     envelope(t, in, hold, out, style_in, style_out)   attack-hold-release (flashes, FOV kicks)
  pulse   pulse(t, lo, hi, period)                   sine loop starting at lo
  keys    keys_at(keys_ms, t)                        piecewise-linear haptic waveform
  lever   lever_display(u, detent, resist)           knob position for a finger at u (-1..1: sign = side)
  event   sample_event(model, name, ...)             simulate one event at 60 Hz: every lane, feel clock,
                                                     hit-stop freeze, trauma decay, reduce-motion, profiles
  phone   PhoneView(h_px, fov_deg)                   degrees and studs to phone pixels

Standard library only. `python3 feelmath.py --help` prints this; `python3 feelmath.py --demo` prints samples.
"""
import functools, math, sys

STYLES = ("Linear", "Sine", "Back", "Quad", "Quart", "Quint", "Bounce", "Elastic", "Exponential", "Circular", "Cubic")
DIRECTIONS = ("In", "Out", "InOut")
BACK_S = 1.70158
ELASTIC_C4 = 2 * math.pi / 3
# noise seeds per camera axis (same constants in RR_FeelMath.lua)
SEEDS = {"pitch": 11, "yaw": 23, "roll": 37, "x": 41, "y": 53, "ui": 67}
MOTION_TYPES = ("tween", "punch", "camkick", "shake", "fovkick", "pulse")   # run on the feel clock (freeze in hit-stop)
REALTIME_TYPES = ("hitstop", "flash", "haptic", "cue")                  # run on real time
REST = {"scale": 1.0, "rot": 0.0, "alpha": 1.0, "x": 0.0, "y": 0.0, "x_px": 0.0, "y_px": 0.0, "count": 1.0}


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def _bounce_out(t):
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    if t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    if t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    t -= 2.625 / d1
    return n1 * t * t + 0.984375


def ease_in(style, t):
    """The 'In' form of each style; Out and InOut are derived from it."""
    if style == "Linear":
        return t
    if style == "Sine":
        return 1 - math.cos(t * math.pi / 2)
    if style == "Quad":
        return t ** 2
    if style == "Cubic":
        return t ** 3
    if style == "Quart":
        return t ** 4
    if style == "Quint":
        return t ** 5
    if style == "Exponential":
        return 0.0 if t <= 0 else 2 ** (10 * t - 10)
    if style == "Circular":
        return 1 - math.sqrt(max(0.0, 1 - t * t))
    if style == "Back":
        return (BACK_S + 1) * t ** 3 - BACK_S * t ** 2
    if style == "Elastic":
        if t <= 0 or t >= 1:
            return float(t >= 1)
        return -(2 ** (10 * t - 10)) * math.sin((t * 10 - 10.75) * ELASTIC_C4)
    if style == "Bounce":
        return 1 - _bounce_out(1 - t)
    raise KeyError(f"unknown EasingStyle {style!r}")


def ease(style, direction, t):
    t = clamp(float(t), 0.0, 1.0)
    if direction == "In":
        return ease_in(style, t)
    if direction == "Out":
        return 1 - ease_in(style, 1 - t)
    if direction == "InOut":
        return ease_in(style, 2 * t) / 2 if t < 0.5 else 1 - ease_in(style, 2 - 2 * t) / 2
    raise KeyError(f"unknown EasingDirection {direction!r}")


def _frac(x):
    return x - math.floor(x)


def _grad(i, seed):
    return _frac(math.sin(i * 12.9898 + seed * 78.233) * 43758.5453) * 2 - 1


def noise1(seed, x):
    """1D gradient noise, smooth, 0 at integers, range about [-1, 1]."""
    i0 = math.floor(x)
    f = x - i0
    u = f * f * f * (f * (f * 6 - 15) + 10)
    n = _grad(i0, seed) * f * (1 - u) + _grad(i0 + 1, seed) * (f - 1) * u
    return 2 * n


def spring(t, amp, freq_hz, damping, shape="sin", dur=None, seed=67):
    """Punch value at local time t. sin: kicks out from 0; cos: starts displaced; noise: decaying jitter."""
    if t < 0 or (dur is not None and t >= dur):
        return 0.0
    if shape == "noise":
        d = dur or 0.5
        return amp * (1 - t / d) ** 2 * noise1(seed, t * freq_hz)
    w = 2 * math.pi * freq_hz
    z = clamp(damping, 0.0, 0.999)
    wd = w * math.sqrt(1 - z * z)
    s = math.sin(wd * t) if shape == "sin" else math.cos(wd * t)
    return amp * math.exp(-z * w * t) * s


PEAK_SAMPLES = 240


@functools.lru_cache(maxsize=512)
def peak_gain(freq_hz, damping, shape="sin", dur=0.5, seed=67):
    """Largest |spring(t, 1, ...)| over [0, dur), sampled at PEAK_SAMPLES points (RR_FeelMath.peakGain is
    identical). Dividing by it makes a punch's amp (and a camera kick's angles) the peak the player sees."""
    d = dur or 0.5
    g = 0.0
    for i in range(PEAK_SAMPLES):
        g = max(g, abs(spring(d * i / PEAK_SAMPLES, 1.0, freq_hz, damping, shape, d, seed)))
    return g if g > 1e-6 else 1.0


def envelope(t, t_in, hold, t_out, style_in="Quad", style_out="Quad"):
    """0 -> 1 over t_in (style_in Out), hold, 1 -> 0 over t_out (style_out InOut)."""
    if t < 0:
        return 0.0
    if t < t_in:
        return ease(style_in, "Out", t / t_in)
    t -= t_in
    if t < hold:
        return 1.0
    t -= hold
    if t < t_out:
        return 1 - ease(style_out, "InOut", t / t_out)
    return 0.0


def pulse(t, lo, hi, period):
    return lo + (hi - lo) * (0.5 - 0.5 * math.cos(2 * math.pi * t / period))


def keys_at(keys, t):
    """keys = [[ms, value], ...] sorted; linear between keys, 0 outside."""
    ms = t * 1000
    if not keys or ms < keys[0][0] or ms > keys[-1][0]:
        return 0.0
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if a <= ms <= b:
            return va if b == a else va + (vb - va) * (ms - a) / (b - a)
    return float(keys[-1][1])


def lever_display(u, detent, resist):
    """Knob position for a finger at u (-1..1 of travel, sign = side): heavy before the detent, 1 at it."""
    sgn = -1.0 if u < 0 else 1.0
    a = clamp(abs(u), 0.0, 1.0)
    if a >= detent:
        return sgn
    return sgn * detent * (a / detent) ** resist


class PhoneView:
    """Converts camera angles and offsets into pixels on the phone frame (height h, vertical FOV)."""

    def __init__(self, w_px, h_px, fov_deg):
        self.w, self.h, self.fov = w_px, h_px, fov_deg
        self.focal = (h_px / 2) / math.tan(math.radians(fov_deg) / 2)

    def deg_px(self, deg):
        return self.focal * math.tan(math.radians(abs(deg)))

    def roll_edge_px(self, deg):
        return (self.w / 2) * math.radians(abs(deg))

    def studs_px(self, studs, depth):
        return self.focal * abs(studs) / depth

    def fov_scale(self, delta_deg):
        """Screen magnification when FOV changes by delta (negative delta zooms in)."""
        return math.tan(math.radians(self.fov) / 2) / math.tan(math.radians(self.fov + delta_deg) / 2)


# ---------------------------------------------------------------- event simulation
def rm_factor(model, ch, reduce_motion):
    """Reduce-motion multiplier or mode for one channel: the channel's own 'rm' beats the a11y table."""
    if not reduce_motion:
        return 1.0
    if ch["type"] == "flash" and ch.get("scope") == "element":
        return 1.0   # a lamp lighting up is state, not a flash
    table = model["a11y"]["reduce_motion"]
    key = "tween_" + ch["prop"] if ch["type"] == "tween" else ch["type"]
    rm = ch.get("rm", table.get(key, table.get(ch["type"], 1.0)))
    return 1.0 if rm == "keep" else rm


def profile_gain(model, profile, ctype):
    return model["profiles"].get(profile, {}).get(ctype, 1.0)


def expand(model, name, delay=0.0, depth=0):
    """Channels of an event with includes resolved: list of (channel, start_delay)."""
    if depth > 4:
        raise ValueError(f"include depth > 4 at {name}")
    ev = model["events"][name]
    out = []
    for inc in ev.get("include", []):
        out += expand(model, inc["event"], delay + inc.get("delay", 0.0), depth + 1)
    for ch in ev.get("channels", []):
        out.append((ch, delay + ch.get("delay", 0.0)))
    return out


def channel_len(model, ch):
    t = ch["type"]
    if t in ("tween", "punch", "camkick"):
        return ch.get("dur", 0.0)
    if t == "hitstop":
        return ch["ms"] / 1000
    if t in ("flash", "fovkick"):
        return ch["in"] + ch.get("hold", 0.0) + ch["out"]
    if t == "haptic":
        return ch["keys"][-1][0] / 1000 if ch.get("keys") else 0.1
    if t == "pulse":
        return ch.get("dur") or 2 * ch["period"]
    if t == "shake":
        return ch["trauma"] / model["shake"]["decay_per_s"]
    return 0.0


def sample_event(model, name, fps=60, reduce_motion=False, profile="default", gain=1.0, side=1, tail=0.25):
    """Simulate one event. Returns dict(t, lanes, meta): each lane is a list aligned with t."""
    chans = expand(model, name)
    hitstops = sorted((d, ch["ms"] / 1000) for ch, d in chans if ch["type"] == "hitstop")
    total = max([d + channel_len(model, ch) for ch, d in chans] + [0.1]) + sum(h for _, h in hitstops) + tail
    n = int(total * fps) + 1
    dt = 1.0 / fps
    shake = model["shake"]
    lanes, meta = {}, {"channels": chans, "total": total, "hitstop": []}
    ts = [i * dt for i in range(n)]

    def frozen(t):
        return any(s <= t < s + h for s, h in hitstops)

    # feel clock: pauses while frozen
    tau, taus = 0.0, []
    for t in ts:
        taus.append(tau)
        if not frozen(t):
            tau += dt
    meta["hitstop"] = [(s, s + h) for s, h in hitstops]

    def lane(key):
        return lanes.setdefault(key, [0.0] * n)

    trauma_adds = []
    for idx, (ch, d) in enumerate(chans):
        ct = ch["type"]
        f = rm_factor(model, ch, reduce_motion)
        g = gain * profile_gain(model, profile, ct)
        if ct == "cue" or f == "skip":
            continue
        if ct == "shake":
            if isinstance(f, (int, float)) and f > 0:
                trauma_adds.append((d, ch["trauma"] * g * f))
            continue
        if ct == "hitstop":
            L = lane(f"{idx}:hitstop")
            for i, t in enumerate(ts):
                L[i] = 1.0 if d <= t < d + ch["ms"] / 1000 else 0.0
            continue
        if ct == "camkick":
            keys = [f"{idx}:camkick:{a}" for a in ("pitch", "yaw", "roll")]
            Ls = [lane(k) for k in keys]
            sgn = [1, side if ch.get("side_sign") else 1, side if ch.get("side_sign") else 1]
            for i in range(n):
                lt = taus[i] - d
                if lt >= 0:
                    u = channel_value(model, ch, lt, f, g, side)
                    for j in range(3):
                        Ls[j][i] = ch["angles_deg"][j] * sgn[j] * u
            continue
        if ct == "flash":
            key = f"{idx}:flash:{ch['scope']}"
        elif ct in ("fovkick", "haptic"):
            key = f"{idx}:{ct}"
        else:
            key = f"{idx}:{ct}:{ch['target']}:{ch['prop']}"
        L = lane(key)
        fade = lane(f"{idx}:tween:{ch['target']}:fadealpha") if (ct == "tween" and f == "fade") else None
        hidden = lane(f"{idx}:tween:{ch['target']}:hidden") if (ct == "tween" and ch.get("before") == "hidden") else None
        entering = ct == "tween" and abs(ch["to"] - REST.get(ch["prop"], 0.0)) < 1e-9
        for i, t in enumerate(ts):
            lt = (taus[i] if ct in MOTION_TYPES else t) - d
            if fade is not None:
                a = 0.0 if lt < 0 else ease("Quad", "Out", min(1.0, lt / ch["dur"]))
                fade[i] = a if entering else 1 - a
            if lt < 0:
                if ct == "tween":
                    b4 = ch.get("before", "from")
                    L[i] = ch["to"] if f == "snap" else fade_hold(ch) if f == "fade" else \
                        REST.get(ch["prop"], ch["to"]) if b4 == "rest" else ch["from"]
                    if hidden is not None:
                        hidden[i] = 1.0
                continue
            L[i] = channel_value(model, ch, lt, f, g, side)
    # camera: trauma + sustain floor -> shake amount -> angles/offsets (feel clock)
    if trauma_adds or shake.get("preview_sustain"):
        tr, amt, P, Y, R, X, Yo = (lane(k) for k in ("cam:trauma", "cam:shake", "cam:pitch", "cam:yaw",
                                                       "cam:roll", "cam:x", "cam:y"))
        trauma, last_tau = 0.0, 0.0
        pending = sorted(trauma_adds)
        for i, t in enumerate(ts):
            dtau = taus[i] - last_tau
            last_tau = taus[i]
            trauma = max(0.0, trauma - shake["decay_per_s"] * dtau)
            while pending and pending[0][0] <= taus[i]:
                trauma = min(shake["max_trauma"], trauma + pending.pop(0)[1])
            eff = trauma
            s = eff ** shake["power"]
            q = taus[i] * shake["freq_hz"]
            tr[i], amt[i] = trauma, s
            P[i] = shake["max_angle_deg"][0] * s * noise1(SEEDS["pitch"], q)
            Y[i] = shake["max_angle_deg"][1] * s * noise1(SEEDS["yaw"], q)
            R[i] = shake["max_angle_deg"][2] * s * noise1(SEEDS["roll"], q)
            X[i] = shake["max_offset_studs"][0] * s * noise1(SEEDS["x"], q)
            Yo[i] = shake["max_offset_studs"][1] * s * noise1(SEEDS["y"], q)
    return {"t": ts, "tau": taus, "lanes": lanes, "meta": meta}


def fade_hold(ch):
    """Reduce motion 'fade': keep the tween's rest end (to when entering, from when leaving)."""
    return ch["to"] if abs(ch["to"] - REST.get(ch["prop"], 0.0)) < 1e-9 else ch["from"]


def channel_value(model, ch, lt, f, g, side=1):
    """Value of one channel at its local time lt (seconds since it started)."""
    ct = ch["type"]
    num = f if isinstance(f, (int, float)) else 1.0
    if ct == "tween":
        dur = ch["dur"]
        if f in ("snap", "skip"):
            return ch["to"]
        if f == "fade":   # no travel: hold the end that is at rest; the alpha lane does the work
            return fade_hold(ch)
        a = ease(ch.get("style", "Quad"), ch.get("dir", "Out"), lt / dur if dur > 0 else 1.0)
        v = ch["from"] + (ch["to"] - ch["from"]) * a
        if num != 1.0:   # scaled motion: shrink the travel toward the end value
            v = ch["to"] + (v - ch["to"]) * num
        return v
    if ct == "punch":   # amp is the delivered peak (normalised by peak_gain)
        z, shape = ch.get("damping", 0.3), ch.get("shape", "sin")
        return spring(lt, ch["amp"] * g * num / peak_gain(ch["freq_hz"], z, shape, ch.get("dur")), ch["freq_hz"], z, shape,
                      ch.get("dur"))
    if ct == "camkick":   # unit response peaking at 1; callers multiply by angles_deg (yaw, roll by the side if side_sign)
        z, shape = ch.get("damping", 0.4), ch.get("shape", "sin")
        return spring(lt, g * num / peak_gain(ch["freq_hz"], z, shape, ch.get("dur")), ch["freq_hz"], z, shape, ch.get("dur"))
    if ct == "fovkick":
        return ch["delta_deg"] * g * num * envelope(lt, ch["in"], ch.get("hold", 0.0), ch["out"],
                                                   ch.get("style_in", "Quad"), ch.get("style_out", "Sine"))
    if ct == "flash":
        return ch["peak"] * g * num * envelope(lt, ch["in"], ch.get("hold", 0.0), ch["out"], "Linear", "Quad")
    if ct == "pulse":
        dur = ch.get("dur")
        if dur and lt >= dur:
            return 0.0
        return pulse(lt, ch["min"], ch["max"], ch["period"])
    if ct == "haptic":
        return min(1.0, keys_at(ch["keys"], lt) * g * num)
    return 0.0


def demo():
    print("t     Quad.Out  Back.Out  Elastic.Out  Bounce.Out")
    for t in (0, 0.1, 0.25, 0.5, 0.75, 1.0):
        print(f"{t:<5} {ease('Quad', 'Out', t):8.4f} {ease('Back', 'Out', t):9.4f} "
              f"{ease('Elastic', 'Out', t):11.4f} {ease('Bounce', 'Out', t):10.4f}")
    print("noise1(11, x):", [round(noise1(11, x / 4), 4) for x in range(8)])
    print("spring sin 0.12 @ 6 Hz z0.35:", [round(spring(x / 20, 0.12, 6, 0.35), 4) for x in range(8)])
    print("lever u->knob (detent 0.7, resist 1.6):", [round(lever_display(u / 10, 0.7, 1.6), 3) for u in range(-2, 11)])
    print("peak gain (unit spring peak) sin 6 Hz z0.35:", round(peak_gain(6, 0.35, "sin", 0.5), 4),
          " noise 12 Hz:", round(peak_gain(12, 0.3, "noise", 0.5), 4))
    pv = PhoneView(844, 390, 70)
    print(f"phone: 1 deg = {pv.deg_px(1):.2f} px, 0.1 stud at 10 studs = {pv.studs_px(0.1, 10):.2f} px")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
        sys.exit(0)
    print(__doc__)
    sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
