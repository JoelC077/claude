"""Risky Rails: the carriage-split sounds (mission 260929-train-splits), synthesised from code.

These recipes are the delivery, not throwaway placeholders: the owner said "Sounds: yes. Make some if you can and
include them if they fit". Nothing here is sampled or recorded: every value comes from numpy maths driven by the
seeded `rng` (split_glass reshapes the skill's own synthesised glass_smash), so the output is deterministic and
licence-clean (self-made).

Contract (rr-soundsmith references/schema.md): r_<sound id>(rng) returns mono float samples at 48 kHz.
`sound.py synth` levels each file to its class standard (impact: momentary max -14 LUFS, true peak at or under
-1 dBTP); the soundmap sets the in-game level (ladder + trim) and the group (Alarms for the boom, Split for the
other layers). So these recipes shape only the sound and its timing.

Timeline (src/kit/break_spec.json events, t 0 = the snap). Each file starts at its event:
  metal_tear       t -0.25   the snap inside the file sits at SNAP_AT = 0.25 s, so it lands on the boom
  split_explosion  t  0      2D train-wide plus a quieter positional layer at the break (soundmap layer3d)
  split_glass      t  0      glass_smash's shards, +3 semitones, its pane crack taken out (the boom is the hit)
  wreck_scrape     t  0.3    grinds until the wreck reaches the terrain's speed: V/brake = 35/12 = 2.92 s
  debris_rain      t  0.8
  topple_crash     t  1.5    the broken half lands (delay 0.45 + roll 1.05); the bounce (0.35 s) is inside the file
  topple_crash_2   t  2.0    break 1: carriage 2 lands (0.8 + 1.2); the same file at PlaybackSpeed 0.84, 3 dB down

Tone: heavy but slapstick (droopy, clunky, cartoon; never war or horror). Phones first: whatever must be heard sits
in 0.5-4 kHz, and the boom and the crash also carry their low thump as upper harmonics (_phone_bass), so the order
boom > tear > crash > debris and scrape holds on a phone speaker as well as on headphones. Every file fades to true
silence 20 ms before its end.
"""
import numpy as np

from synth import SR, buf, decay, filt, modal, n_, noise, osc, place, r_glass_smash, sweep, t_

SNAP_AT = 0.25                           # metal_tear: the snap lands on the explosion (event at t -0.25)
BOUNCE_AT = 0.35                         # topple_crash: break_spec topple bounce_time
SPEED, BRAKE, SCRAPE_FROM = 35.0, 12.0, 0.3
SLIDE = SPEED / BRAKE - SCRAPE_FROM      # 2.62 s of grinding at the normal speed (gameplay.speed.normal)
GLASS_CRACK = 0.015                      # glass_smash's pane crack: a broadband burst in its first 15 ms


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


def _finish(x, fade, pad=0.02):
    """End on true silence: drop DC and sub-audio drift (20 Hz high-pass), fade over `fade` s to zero `pad` s before
    the end, then remove the residual mean under the fade window so the file sums to zero and a later DC step in
    the render cannot lift the silent tail off zero."""
    x = filt(x, 20, None)
    n, p = n_(fade), n_(pad)
    end = len(x) - p
    w = np.ones(len(x))
    w[end - n:end] = np.cos(np.linspace(0.0, np.pi / 2, n)) ** 2
    w[end:] = 0.0
    x = x * w
    return x - w * (x.sum() / w.sum())


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


def _hp_sweep(x, t0, t1, f0, f1, steps=5):
    """High-pass whose corner glides f0 -> f1 (log) between t0 and t1 s, then holds f1: cross-fades zero-phase
    high-passes at log-spaced corners, so nothing smears in time."""
    t = np.arange(len(x)) / SR
    pos = np.clip((t - t0) / (t1 - t0), 0.0, 1.0) * (steps - 1)
    bank = np.stack([filt(x, f0 * (f1 / f0) ** (k / (steps - 1)), None, order=4) for k in range(steps)])
    i = np.minimum(pos.astype(int), steps - 2)
    fr = pos - i
    cols = np.arange(len(x))
    return bank[i, cols] * (1.0 - fr) + bank[i + 1, cols] * fr


def _phone_bass(tone, env, drive=4.0, lo=400, hi=2000):
    """Upper harmonics of a low thump: saturate its steady tone (tanh), keep lo-hi Hz (steep band-pass) and give
    them the thump's own envelope. Phone speakers cannot play 40-90 Hz, but the ear rebuilds the low pitch from its
    overtones (psychoacoustic bass), so the thump still lands on a phone, and it decays with the thump."""
    return _unit(filt(np.tanh(drive * _unit(tone)), lo, hi, order=4)) * env


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
    plate = modal(0.09, [(310, 0.03, 0.35), (745, 0.024, 0.8), (1180, 0.02, 0.75), (1690, 0.016, 0.6),
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
    # 3 snap at SNAP_AT: a sharp crack (the file's peak), a cartoon metal ping and a small low thunk
    d = L - SNAP_AT
    crack = _unit(filt(noise(d, rng), 1200, 8000)) * decay(d, 0.012, attack=0.0005)
    ping = _unit(modal(d, [(1320, 0.18, 1.0), (1870, 0.12, 0.7), (2640, 0.09, 0.5), (3480, 0.06, 0.35)], rng))
    thunk = osc(_glide(140, 70, 0.12, d), d) * decay(d, 0.05, attack=0.001)
    snap = 1.0 * crack + 0.45 * ping + 0.12 * thunk
    # 4 droop: the torn sheet flaps wub-wub-wub, its pitch sagging 420 -> 180 Hz, the wobble slowing 7 -> 4 Hz; only
    #   its harmonics above 450 Hz are kept (the ear hears the sag through them), so a phone plays it all
    w0 = SNAP_AT + 0.01
    d = L - w0
    tw = t_(d)
    lfo = np.sin(2 * np.pi * np.cumsum(7.0 * (4.0 / 7.0) ** (tw / d)) / SR)
    f = 420.0 * (180.0 / 420.0) ** np.clip(tw / 0.75, 0, 1) * (1 + 0.05 * lfo)
    sheet = filt(osc(f, d, partials=[(1, 1.0), (2, 0.6), (3, 0.45), (4, 0.3), (5, 0.2), (6, 0.12)]), 450, 3000)
    wobble = _unit(sheet) * (0.55 + 0.45 * lfo) * decay(d, 0.28, attack=0.015)

    x = 0.55 * groan + rip
    place(x, snap, SNAP_AT, 1.0)
    place(x, wobble, w0, 0.4)
    return _finish(x, 0.15)


# ---------------------------------------------------------------------------------------------------------------
# split_explosion: mid crack-body + sub thump + noise burst with decay + crackle + debris tail
# ---------------------------------------------------------------------------------------------------------------

def r_split_explosion(rng):
    L = 2.2
    # 1 mid crack-body, 0.6-2.5 kHz, gone within 0.3 s: the KA-BLAM a phone speaker plays. It is the boom's
    #   loudest moment, so the file peaks within a few ms of 0 and most of its loudness survives a phone.
    mid_osc = osc(_glide(150, 62, 0.55, L), L, partials=[(k, 1.0 / k ** 0.7) for k in range(1, 41)])
    mid_body = _unit(filt(mid_osc, 600, 2500, order=4)) * decay(L, 0.09, attack=0.002)
    mid_crack = _unit(filt(noise(L, rng, "pink"), 600, 2500, order=4)) * decay(L, 0.06, attack=0.001)
    # 2 pitched body: the cartoon BWOOM, 150 -> 62 Hz, saw-like partials (harmonics to 2.2 kHz), bright then darker
    raw = osc(_glide(150, 62, 0.55, L), L, partials=[(k, 1.0 / k ** 0.85) for k in range(1, 17)])
    body = (_unit(filt(raw, 120, 2200)) * decay(L, 0.22, attack=0.004)
            + 0.15 * _unit(filt(raw, 50, 650)) * decay(L, 0.45, attack=0.01))
    # 3 sub thump 90 -> 38 Hz (weight on headphones) and its upper harmonics (the same thump on a phone)
    sub_tone, sub_env = osc(_glide(90, 38, 0.4, L), L), decay(L, 0.32, attack=0.003)
    sub = sub_tone * sub_env
    # 4 noise burst with decay: KA click (8 ms, makes 0-10 ms the loudest moment), crack (bright, 35 ms), roar
    #   (mid, 0.3 s), fireball whoosh (mid, 0.45 s), low roar and a soft settle
    ka = _unit(filt(noise(L, rng), 800, 6000, order=4)) * decay(L, 0.008, attack=0.0003)
    crack = _unit(filt(noise(L, rng), 1500, 7500)) * decay(L, 0.035, attack=0.0008)
    roar = _unit(filt(noise(L, rng, "pink"), 400, 2600)) * decay(L, 0.3, attack=0.006)
    whoosh = _unit(filt(noise(L, rng, "pink"), 500, 2200)) * decay(L, 0.45, attack=0.012)
    low = _unit(filt(noise(L, rng, "brown"), 60, 500)) * decay(L, 0.5, attack=0.012)
    settle = _unit(filt(noise(L, rng, "pink"), 250, 1400)) * decay(L, 0.9, attack=0.05)
    # 5 firework crackle: sparse fizzy clicks 1.8-7 kHz, about 70/s at first, thinning over 1.5 s
    ct = _train(1.5, lambda s: 4.0 + 70.0 * np.exp(-s / 0.45), rng, jitter=0.9, t0=0.02)
    crackle = _unit(filt(_spikes(L, ct, rng.uniform(0.1, 1.0, len(ct)) ** 2), 1800, 7000)) * decay(L, 0.6)
    # 6 debris tail: clunky wood and tin bits falling from 0.3 s, done before the fade
    times = np.sort(0.3 + rng.exponential(0.5, 16))
    times = times[times < 1.8]
    kinds = rng.choice(["wood", "wood", "chunk", "metal", "metal", "pebble"], len(times))
    amps = rng.uniform(0.5, 1.0, len(times)) * np.exp(-(times - 0.3) / 0.8)
    debris = _unit(_clatter(L, times, kinds, amps, rng))

    x = (1.0 * ka + 1.3 * mid_crack + 1.0 * mid_body + 0.45 * body + 0.12 * sub + 0.8 * _phone_bass(sub_tone, sub_env)
         + 1.1 * crack + 1.0 * roar + 0.55 * whoosh + 0.05 * low + 0.08 * settle + 0.6 * crackle + 0.4 * debris)
    # 7 the tail sheds its lows: high-pass sweeping 20 -> 500 Hz from 1.0 to 1.4 s (no rolling rumble), then a
    #   300 ms fade to silence at 2.18 s
    x = _hp_sweep(x, 1.0, 1.4, 20.0, 500.0)
    return _finish(x, 0.3)


# ---------------------------------------------------------------------------------------------------------------
# split_glass: glass_smash's shards only, +3 semitones, so the split's windows sparkle over the boom
# ---------------------------------------------------------------------------------------------------------------

def r_split_glass(rng):
    g = r_glass_smash(rng)                           # the stock window glass (rr-soundsmith synth.py), reused
    g = g[n_(GLASS_CRACK):]                          # drop the pane crack; the shards rise from about 18 ms
    g = filt(g, 2200, 19000, order=4)                # shards only: no pane body under 2.2 kHz
    ratio = 2.0 ** (3.0 / 12.0)                      # +3 semitones (and 16% shorter)
    y = np.interp(np.arange(int(len(g) / ratio)) * ratio, np.arange(len(g)), g)[:n_(0.9)]
    y[:n_(0.002)] *= np.linspace(0.0, 1.0, n_(0.002))   # 2 ms onset ramp: no click where the crack was cut
    return _finish(y, 0.15)


# ---------------------------------------------------------------------------------------------------------------
# topple_crash: splinter + bin-lid clang up front, low impact, gravel tail, and the topple's bounce
# ---------------------------------------------------------------------------------------------------------------

def r_topple_crash(rng):
    L = 1.45
    t = t_(L)
    # 1 splinter burst: about 40 cracks inside the first 80 ms (densest at the hit), 0.8-2.5 kHz, ringing high
    #   wood-knock modes
    st = np.sort(np.concatenate([[0.0], 0.08 * rng.random(39) ** 1.5]))
    sa = rng.uniform(0.3, 1.0, len(st))
    sa[0] = 1.0
    grains = _spikes(L, st, sa)
    wood = modal(0.05, [(900, 0.018, 1.0), (1340, 0.014, 0.8), (1880, 0.01, 0.6), (2450, 0.008, 0.45)])
    splinter = 0.6 * _unit(_conv(grains, wood)) + 0.6 * _unit(filt(grains, 800, 2500, order=4))
    # 2 bin-lid clang, struck with the hit: inharmonic modes 0.8-2.5 kHz (one quieter body mode under them),
    #   pitch drooping 4% as it rings (the cartoon sag)
    droop = 1.0 - 0.04 * (1.0 - np.exp(-t / 0.3))
    modes = [(547, 0.2, 0.35), (812, 0.26, 1.0), (1187, 0.22, 0.85), (1543, 0.18, 0.7), (1978, 0.14, 0.55),
             (2441, 0.1, 0.4)]
    clang = _unit(sum(a * osc(f * droop, L) * decay(L, tau, attack=0.001) for f, tau, a in modes))
    # 3 low impact: a small 70 -> 45 Hz thump, its upper harmonics for phones, and a short low thud
    thump_tone, thump_env = osc(_glide(70, 45, 0.25, L), L), decay(L, 0.18, attack=0.002)
    thump = thump_tone * thump_env
    thud = _unit(filt(noise(L, rng, "brown"), 60, 400)) * decay(L, 0.08, attack=0.002)
    # 4 gravel tail: pebble grains 1.5-6 kHz, about 280/s at the hit, thinning over 1.2 s, over a dust hiss
    gt = _train(1.3, lambda s: 20.0 + 260.0 * np.exp(-s / 0.3), rng, jitter=0.9, t0=0.03)
    gravel = _unit(filt(_spikes(L, gt, rng.uniform(0.05, 1.0, len(gt)) ** 2), 1500, 6000)) * decay(L, 0.5)
    dust = _unit(filt(noise(L, rng, "pink"), 1000, 4000)) * decay(L, 0.35, attack=0.02)
    # 5 bounce at BOUNCE_AT: the body rocks back and lands again, a smaller mid clunk over a little thud
    d = L - BOUNCE_AT
    clunk = _unit(modal(0.2, [(620, 0.04, 1.0), (1010, 0.03, 0.6), (1530, 0.02, 0.4)], rng))
    bounce = (0.25 * osc(_glide(62, 45, 0.15, d), d) * decay(d, 0.1, attack=0.002)
              + 0.2 * _unit(filt(noise(d, rng, "brown"), 80, 600)) * decay(d, 0.05, attack=0.002))
    place(bounce, clunk, 0.0, 0.8)

    x = (0.9 * splinter + 0.8 * clang + 0.3 * thump + 0.35 * _phone_bass(thump_tone, thump_env) + 0.18 * thud + 0.45 * gravel
         + 0.1 * dust)
    place(x, bounce, BOUNCE_AT, 0.35)
    return _finish(x, 0.15)


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
    return _finish(x + 0.06 * dust, 0.1)


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
    # it emerges under the boom: fade in from -12 dB over 0.6 s; nothing above 2.5 kHz (glass and debris own it)
    x *= 10.0 ** ((-12.0 + 12.0 * np.clip(t / 0.6, 0, 1)) / 20.0)
    x = filt(x, None, 2500, order=4)
    return _finish(x, 0.25)
