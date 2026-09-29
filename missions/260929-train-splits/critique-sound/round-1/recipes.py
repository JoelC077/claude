"""Risky Rails: the carriage-split sounds (mission 260929-train-splits), synthesised from code.

These recipes are the delivery, not throwaway placeholders: the owner said "Sounds: yes. Make some if you can and
include them if they fit". Nothing here is sampled or recorded: every value comes from numpy maths driven by the
seeded `rng`, so the output is deterministic and licence-clean (self-made).

Contract (rr-soundsmith references/schema.md): r_<sound id>(rng) returns mono float samples at 48 kHz.
`sound.py synth` levels each file to its class standard (impact: momentary max -14 LUFS, true peak at or under
-1 dBTP), and the soundmap sets the in-game level from the ladder plus trim. So these recipes shape only the
sound and its timing; the loudness hierarchy lives in soundmap.json: boom -10 > tear -12.5 > crash -13 (glass -13
under the boom) > debris and scrape -16 LUFS. On a phone speaker each drops by its phone loss, so the low-heavy boom
and crash also carry their thump as harmonics (_phone_bass) and the order holds there too (about -13.1 > -13.8 >
-15.9 > -17.1), without putting a split layer more than 1 LU under a lower-tier sound (the sheet's inversion check).

Timeline (src/kit/break_spec.json events, t 0 = the snap). Each file starts at its event:
  metal_tear       t -0.25   the snap inside the file sits at SNAP_AT = 0.25 s, so it lands on the boom
  split_explosion  t  0      2D train-wide plus a quieter positional layer at the break (soundmap layer3d)
  split_glass      t  0      glass_smash's built-in recipe ("synth": "glass_smash" in the soundmap)
  wreck_scrape     t  0.3    grinds until the wreck reaches the terrain's speed: V/brake = 35/12 = 2.92 s
  debris_rain      t  0.8
  topple_crash     t  1.5 (broken half: delay 0.45 + roll 1.05) and 2.0 (carriage 2: 0.8 + 1.2); the topple
                   bounce (bounce_time 0.35 s) is the second, smaller thud inside the file

Tone: heavy but slapstick (droopy, clunky, cartoon; never war or horror). Every layer that has to be heard keeps
its energy in 0.5-4 kHz so phone speakers carry it; the sub layers only add weight on headphones and TVs.
"""
import numpy as np

from synth import SR, buf, decay, filt, modal, n_, noise, osc, place, sweep, t_

SNAP_AT = 0.25                           # metal_tear: the snap lands on the explosion (event at t -0.25)
BOUNCE_AT = 0.35                         # topple_crash: break_spec topple bounce_time
SPEED, BRAKE, SCRAPE_FROM = 35.0, 12.0, 0.3
SLIDE = SPEED / BRAKE - SCRAPE_FROM      # 2.62 s of grinding at the normal speed (gameplay.speed.normal)


# ---------------------------------------------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------------------------------------------

def _unit(x):
    """Scale to peak 1, so layers are mixed by explicit, readable gains."""
    p = float(np.max(np.abs(x))) if len(x) else 0.0
    return x / p if p > 0 else x


def _glide(f0, f1, dur, total):
    """Per-sample frequency for `total` seconds: exponential glide f0 -> f1 over `dur`, then held."""
    g = sweep(f0, f1, dur)
    return np.concatenate([g, np.full(n_(total) - len(g), float(f1))])


def _fade_out(x, dur):
    """Equal-power fade over the last `dur` seconds, so no file ends on a click."""
    n = n_(dur)
    x[-n:] *= np.cos(np.linspace(0.0, np.pi / 2, n)) ** 2
    return x


def _train(dur, rate, rng, jitter=0.2, t0=0.0):
    """Times of a jittered pulse train from t0 to dur; `rate(t)` is the instantaneous rate in Hz."""
    ts, t = [], t0
    while t < dur:
        ts.append(t)
        t += (1.0 + jitter * rng.uniform(-1.0, 1.0)) / max(rate(t), 1e-3)
    return np.array(ts)


def _spikes(dur, times, amps):
    """Impulses of height `amps` at `times` (the excitation for crackles, grains and stick-slip)."""
    x = buf(dur)
    i = np.clip((np.asarray(times) * SR).astype(int), 0, len(x) - 1)
    np.add.at(x, i, amps)
    return x


def _conv(x, h):
    """FFT convolution cut to len(x): impulses ringing a resonator."""
    n = len(x) + len(h) - 1
    size = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(h, size), size)[:len(x)]


def _band_sweep(x, fc, centres, width=0.4):
    """Time-varying band-pass: cross-fades a bank of fixed bands (half-width `width` octaves) to follow fc(t)."""
    y = np.zeros_like(x)
    for c in centres:
        w = np.exp(-0.5 * (np.log2(fc / c) / width) ** 2)
        y += filt(x, c * 2.0 ** -width, c * 2.0 ** width) * w
    return y


def _phone_bass(x, drive=6.0, lo=400, hi=2000):
    """Upper harmonics of a low thump (tanh saturation, steep band-pass): phone speakers cannot play 40-90 Hz, but
    the ear rebuilds the low pitch from its overtones, so the thump still lands on a phone (psychoacoustic bass)."""
    return _unit(filt(np.tanh(drive * _unit(x)), lo, hi, order=4))


ROOF = [(182, 0.06, 1.0), (268, 0.05, 0.7), (411, 0.04, 0.5)]   # the kept half's metal roof, struck softly


def _hit(kind, rng):
    """One small debris impact: 'wood' knock, 'metal' tink, 'pebble' tick or 'chunk' (a bigger wooden piece)."""
    if kind == "wood":
        f, d = rng.uniform(420, 1150), 0.1
        x = modal(d, [(f, rng.uniform(0.012, 0.03), 1.0), (f * 2.31, 0.012, 0.45), (f * 3.87, 0.007, 0.25)], rng)
        x = _unit(x) + 0.4 * _unit(filt(noise(d, rng), 700, 5000)) * decay(d, 0.0025)
    elif kind == "metal":
        f, d = rng.uniform(1700, 4200), 0.25
        x = modal(d, [(f, rng.uniform(0.04, 0.09), 1.0), (f * 1.58, 0.045, 0.55), (f * 2.37, 0.03, 0.3),
                      (f * 0.63, 0.05, 0.3)], rng)
        x = _unit(x) + 0.3 * _unit(filt(noise(d, rng), 2500, 9000)) * decay(d, 0.0015)
    elif kind == "pebble":
        d = 0.02
        x = filt(noise(d, rng), 2000, 7000) * decay(d, rng.uniform(0.001, 0.003))
    else:
        f, d = rng.uniform(200, 420), 0.18
        x = modal(d, [(f, 0.045, 1.0), (f * 2.13, 0.03, 0.6), (f * 3.4, 0.02, 0.4), (f * 5.2, 0.012, 0.25)], rng)
        x = _unit(x) + 0.5 * _unit(filt(noise(d, rng), 300, 3500)) * decay(d, 0.006)
    return _unit(x)


def _clatter(dur, times, kinds, amps, rng, roof=0.0):
    """Scattered hits; `roof` adds a faint metal-roof boom under the wooden ones (they land on the kept half)."""
    x = buf(dur)
    boom = _unit(modal(0.2, ROOF))
    for t, k, a in zip(times, kinds, amps):
        place(x, _hit(k, rng), float(t), float(a))
        if roof and k in ("wood", "chunk"):
            place(x, boom, float(t), float(a) * roof)
    return x


# ---------------------------------------------------------------------------------------------------------------
# metal_tear: groan + rising rip + snap, then the torn sheet wobbling and drooping
# ---------------------------------------------------------------------------------------------------------------

def r_metal_tear(rng):
    L = 1.05
    t = t_(L)
    # 1 groan: stick-slip creak. A jittered pulse train, its rate rising 60 -> 150 Hz with the strain, rings
    #   inharmonic plate modes (0.3-3.1 kHz, the phone band); crescendo into the snap, which releases it.
    gt = _train(SNAP_AT + 0.02, lambda s: 60.0 + 90.0 * min(s / SNAP_AT, 1.0) ** 1.5, rng, jitter=0.18)
    ga = (0.45 + 0.55 * np.clip(gt / SNAP_AT, 0, 1) ** 1.2) * rng.uniform(0.7, 1.0, len(gt))
    plate = modal(0.09, [(310, 0.03, 0.75), (745, 0.024, 0.8), (1180, 0.02, 0.75), (1690, 0.016, 0.6),
                         (2350, 0.012, 0.45), (3100, 0.009, 0.3)])
    groan = _unit(_conv(_spikes(L, gt, ga), plate))
    # 2 rip: crackle grains plus hiss in a band sweeping 0.7 -> 3.5 kHz, accelerating (140 -> 1040 grains/s);
    #   it builds to the snap and dies 15 ms after it.
    fc = 700.0 * 5.0 ** np.clip(t / SNAP_AT, 0, 1)
    rt = _train(SNAP_AT, lambda s: 140.0 + 900.0 * (s / SNAP_AT) ** 2, rng, jitter=0.6)
    centres = (700, 1000, 1400, 2000, 2800, 3500)
    crackle = _unit(_band_sweep(_spikes(L, rt, rng.uniform(0.2, 1.0, len(rt)) ** 2), fc, centres))
    hiss = _unit(_band_sweep(noise(L, rng), fc, centres))
    rip_env = np.where(t <= SNAP_AT, 0.2 + 0.8 * np.clip(t / SNAP_AT, 0, 1) ** 1.3,
                       np.exp(-np.maximum(t - SNAP_AT, 0) / 0.015))
    rip = (0.8 * crackle + 0.35 * hiss) * rip_env
    # 3 snap at SNAP_AT: a sharp crack, a cartoon metal ping and a small low thunk
    d = L - SNAP_AT
    crack = _unit(filt(noise(d, rng), 1200, 8000)) * decay(d, 0.012, attack=0.0005)
    ping = _unit(modal(d, [(1320, 0.18, 1.0), (1870, 0.12, 0.7), (2640, 0.09, 0.5), (3480, 0.06, 0.35)], rng))
    thunk = osc(_glide(140, 70, 0.12, d), d) * decay(d, 0.05, attack=0.001)
    snap = 1.0 * crack + 0.45 * ping + 0.3 * thunk
    # 4 droop: the torn sheet flaps wub-wub-wub, its pitch sagging 420 -> 180 Hz, the wobble slowing 7 -> 4 Hz
    w0 = SNAP_AT + 0.01
    d = L - w0
    tw = t_(d)
    lfo = np.sin(2 * np.pi * np.cumsum(7.0 * (4.0 / 7.0) ** (tw / d)) / SR)
    f = 420.0 * (180.0 / 420.0) ** np.clip(tw / 0.75, 0, 1) * (1 + 0.05 * lfo)
    sheet = filt(osc(f, d, partials=[(1, 1.0), (2, 0.6), (3, 0.45), (4, 0.3), (5, 0.2), (6, 0.12)]), 330, 3000)
    wobble = _unit(sheet) * (0.55 + 0.45 * lfo) * decay(d, 0.28, attack=0.015)

    x = 0.55 * groan + rip
    place(x, snap, SNAP_AT, 1.0)
    place(x, wobble, w0, 0.4)
    return _fade_out(x, 0.06)


# ---------------------------------------------------------------------------------------------------------------
# split_explosion: sub thump + noise burst with decay + crackle + debris tail (plus the pitched cartoon body)
# ---------------------------------------------------------------------------------------------------------------

def r_split_explosion(rng):
    L = 2.75
    # 1 sub thump: 90 -> 38 Hz in 0.4 s (weight on headphones; phones get the body and the burst)
    sub = osc(_glide(90, 38, 0.4, L), L) * decay(L, 0.32, attack=0.003)
    # 2 pitched body: the cartoon BWOOM, 150 -> 62 Hz, saw-like partials so its harmonics reach 0.3-1.8 kHz;
    #   a bright attack fading into a darker, longer tail
    raw = osc(_glide(150, 62, 0.55, L), L, partials=[(k, 1.0 / k ** 0.85) for k in range(1, 17)])
    body = (_unit(filt(raw, 120, 2200)) * decay(L, 0.22, attack=0.004)
            + 0.45 * _unit(filt(raw, 50, 650)) * decay(L, 0.45, attack=0.01))
    # 3 noise burst with decay: crack (bright, 35 ms), roar (mid, 0.3 s), fireball whoosh (mid, swells then
    #   0.45 s: keeps the boom alive on phones), low roar (0.5 s), settle (soft tail)
    crack = _unit(filt(noise(L, rng), 1500, 7500)) * decay(L, 0.035, attack=0.0008)
    roar = _unit(filt(noise(L, rng, "pink"), 400, 2600)) * decay(L, 0.3, attack=0.006)
    whoosh = _unit(filt(noise(L, rng, "pink"), 500, 2200)) * decay(L, 0.45, attack=0.03)
    low = _unit(filt(noise(L, rng, "brown"), 60, 500)) * decay(L, 0.5, attack=0.012)
    settle = _unit(filt(noise(L, rng, "pink"), 250, 1400)) * decay(L, 0.9, attack=0.05)
    # 4 firework crackle: sparse fizzy clicks 1.8-7 kHz, about 70/s at first, thinning over 1.5 s
    ct = _train(1.5, lambda s: 4.0 + 70.0 * np.exp(-s / 0.45), rng, jitter=0.9, t0=0.02)
    crackle = _unit(filt(_spikes(L, ct, rng.uniform(0.1, 1.0, len(ct)) ** 2), 1800, 7000)) * decay(L, 0.6)
    # 5 debris tail: clunky wood and tin bits falling from 0.3 s, fading out by about 2.3 s
    times = np.sort(0.3 + rng.exponential(0.5, 16))
    times = times[times < 2.3]
    kinds = rng.choice(["wood", "wood", "chunk", "metal", "metal", "pebble"], len(times))
    amps = rng.uniform(0.5, 1.0, len(times)) * np.exp(-(times - 0.3) / 0.8)
    debris = _unit(_clatter(L, times, kinds, amps, rng))

    x = (0.22 * sub + 0.5 * _phone_bass(sub) + 0.75 * body + 0.55 * crack + 1.0 * roar + 0.7 * whoosh
         + 0.14 * low + 0.12 * settle + 0.6 * crackle + 0.4 * debris)
    return _fade_out(x, 0.12)


# ---------------------------------------------------------------------------------------------------------------
# topple_crash: low impact + wood crunch + metal clang + gravel tail, and the topple's bounce
# ---------------------------------------------------------------------------------------------------------------

def r_topple_crash(rng):
    L = 1.45
    t = t_(L)
    # 1 low impact: 70 -> 45 Hz thump plus a short low thud
    thump = osc(_glide(70, 45, 0.25, L), L) * decay(L, 0.18, attack=0.002)
    thud = _unit(filt(noise(L, rng, "brown"), 60, 400)) * decay(L, 0.08, attack=0.002)
    # 2 wood crunch: about 30 splinter cracks inside 0.22 s (densest at the hit) through wood-knock resonances
    st = np.sort(np.concatenate([[0.0], 0.22 * rng.random(29) ** 1.6]))
    sa = rng.uniform(0.3, 1.0, len(st))
    sa[0] = 1.0
    grains = _spikes(L, st, sa)
    wood = modal(0.06, [(230, 0.03, 1.0), (480, 0.025, 0.8), (830, 0.02, 0.7), (1450, 0.012, 0.5), (2600, 0.006, 0.3)])
    crunch = 0.7 * _unit(_conv(grains, wood)) + 0.5 * _unit(filt(grains, 400, 3500))
    # 3 metal clang: a bin-lid set of inharmonic modes, pitch drooping 4% as it rings (the cartoon sag)
    droop = 1.0 - 0.04 * (1.0 - np.exp(-t / 0.3))
    modes = [(290, 0.24, 0.7), (523, 0.21, 1.0), (861, 0.18, 0.8), (1247, 0.15, 0.6), (1662, 0.12, 0.45),
             (2211, 0.09, 0.3), (2893, 0.06, 0.2)]
    clang = _unit(sum(a * osc(f * droop, L) * decay(L, tau, attack=0.001) for f, tau, a in modes))
    # 4 gravel tail: pebble grains 1.5-6 kHz, about 280/s at the hit, thinning over 1.2 s, over a dust hiss
    gt = _train(1.3, lambda s: 20.0 + 260.0 * np.exp(-s / 0.3), rng, jitter=0.9, t0=0.03)
    gravel = _unit(filt(_spikes(L, gt, rng.uniform(0.05, 1.0, len(gt)) ** 2), 1500, 6000)) * decay(L, 0.5)
    dust = _unit(filt(noise(L, rng, "pink"), 1000, 4000)) * decay(L, 0.35, attack=0.02)
    # 5 bounce at BOUNCE_AT: the body rocks back and lands again, smaller
    d = L - BOUNCE_AT
    bounce = (0.6 * osc(_glide(62, 45, 0.15, d), d) * decay(d, 0.1, attack=0.002)
              + 0.5 * _unit(filt(noise(d, rng, "brown"), 80, 600)) * decay(d, 0.05, attack=0.002))
    place(bounce, _hit("chunk", rng), 0.0, 0.35)

    x = (0.22 * thump + 0.45 * _phone_bass(thump) + 0.18 * thud + 0.9 * crunch + 0.75 * clang + 0.5 * gravel
         + 0.12 * dust)
    place(x, bounce, BOUNCE_AT, 0.35)
    return _fade_out(x, 0.1)


# ---------------------------------------------------------------------------------------------------------------
# debris_rain: scattered small clatters, dense then sparse, on the kept half's roof and the track
# ---------------------------------------------------------------------------------------------------------------

def r_debris_rain(rng):
    L = 1.8
    times = np.sort(np.concatenate([[0.0, 0.35], rng.exponential(0.42, 28)]))
    times = times[times < 1.55]
    kinds = list(rng.choice(["wood", "wood", "metal", "metal", "pebble", "pebble", "pebble"], len(times)))
    kinds[0] = "chunk"                                   # a bigger piece opens it (no lead-in silence)
    kinds[int(np.argmin(np.abs(times - 0.35)))] = "chunk"
    amps = rng.uniform(0.35, 1.0, len(times)) * (0.3 + 0.7 * np.exp(-times / 0.6))
    amps[0] = 1.0
    x = _unit(_clatter(L, times, kinds, amps, rng, roof=0.3))
    dust = _unit(filt(noise(L, rng, "pink"), 1000, 5000)) * decay(L, 0.6, attack=0.01)
    return _fade_out(x + 0.06 * dust, 0.1)


# ---------------------------------------------------------------------------------------------------------------
# wreck_scrape: grinding noise with wobble, slowing with the wreck's speed over the ground
# ---------------------------------------------------------------------------------------------------------------

def r_wreck_scrape(rng):
    L = round(SLIDE + 0.08, 3)
    t = t_(L)
    v = np.clip(1.0 - t / SLIDE, 0.0, 1.0)         # speed relative to the ground, 1 -> 0 at V/brake
    lfo = np.sin(2 * np.pi * np.cumsum(3.0 + 2.0 * v) / SR)   # the wreck rocking: wobble 5 -> 3 Hz
    # stick-slip roughness: jittered bumps at 60 -> 16 Hz, the grinding "grrrr"
    pt = _train(L, lambda s: 16.0 + 44.0 * max(0.0, 1.0 - s / SLIDE), rng, jitter=0.35)
    rough = 0.3 + 0.7 * _unit(_conv(_spikes(L, pt, rng.uniform(0.5, 1.0, len(pt))), decay(0.05, 0.008)))
    # grinding noise: two bands swayed by the wobble (timbre goes wow-wow as it rocks); the bright band
    #   thins out as the wreck slows, so the grind sags darker as well as quieter
    nz = noise(L, rng)
    grind = (_unit(filt(nz, 280, 1100)) * (0.6 + 0.4 * lfo)
             + _unit(filt(nz, 900, 2800)) * (0.6 - 0.4 * lfo) * (0.4 + 0.6 * v)) * rough
    # a faint droopy metal whine, 520 -> 430 Hz, only while it moves
    fw = (430.0 + 90.0 * v) * (1 + 0.015 * lfo)
    whine = _unit(osc(fw, L, partials=[(1, 1.0), (2, 0.5), (3, 0.3), (4.2, 0.15)])) * rough * v
    # gravel pops, thinning as it slows, and a low rumble under it
    gp = _train(L, lambda s: 3.0 + 30.0 * max(0.0, 1.0 - s / SLIDE), rng, jitter=0.9)
    pops = _unit(filt(_spikes(L, gp, rng.uniform(0.2, 1.0, len(gp)) ** 2), 1500, 6000)) * (0.3 + 0.7 * v)
    rumble = _unit(filt(noise(L, rng, "brown"), 45, 220)) * v

    shape = (0.12 + 0.88 * v ** 0.8) * (1 + 0.15 * lfo) * np.clip(t / 0.03, 0, 1)
    x = (0.8 * grind + 0.12 * whine + 0.25 * pops + 0.35 * rumble) * shape
    return _fade_out(x, 0.25)
