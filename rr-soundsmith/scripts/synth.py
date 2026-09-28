#!/usr/bin/env python3
"""Placeholder SFX for Risky Rails, synthesised from code only (no samples, so no third-party rights).

  python3 synth.py --list                      recipe names
  python3 synth.py ID [ID...] --out DIR        (sound.py synth is the normal entry: it adds the class standard)

Every recipe is deterministic (seeded) and returns mono float samples at 48 kHz. `render()` normalises to the class
standard with audiolib's BS.1770 meter (momentary max for one-shots, integrated for loops), soft-clipping peaks
to the -1 dBTP ceiling when needed, and writes PLACEHOLDER_<id>.wav (16-bit mono) whose INFO chunk says PLACEHOLDER.
They exist to prototype timing and mix in Studio; they are not final audio. Needs numpy.
"""
import argparse, hashlib, math, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audiolib as al  # noqa: E402

SR = 48000
CEIL = 10 ** (-1.2 / 20)


# ------------------------------------------------------------------ building blocks
def n_(dur):
    return int(round(dur * SR))


def t_(dur):
    return np.arange(n_(dur)) / SR


def buf(dur):
    return np.zeros(n_(dur))


def place(b, x, at, gain=1.0):
    i = n_(at)
    if i >= len(b):
        return b
    m = min(len(x), len(b) - i)
    b[i:i + m] += gain * x[:m]
    return b


def place_wrap(b, x, at, gain=1.0):
    """Add x at `at`, wrapping past the end to the start (for seamless loops)."""
    i = n_(at) % len(b)
    idx = (np.arange(len(x)) + i) % len(b)
    np.add.at(b, idx, gain * x)
    return b


def decay(dur, tau, attack=0.0):
    t = t_(dur)
    e = np.exp(-t / tau)
    if attack > 0:
        e *= np.clip(t / attack, 0, 1)
    return e


def env(dur, a, r, hold=None):
    """Attack a, flat, release r (linear-in-dB-ish cosine ramps)."""
    t = t_(dur)
    e = np.ones_like(t)
    if a > 0:
        e *= np.where(t < a, 0.5 - 0.5 * np.cos(np.pi * np.clip(t / a, 0, 1)), 1)
    if r > 0:
        end = dur if hold is None else a + hold + r
        e *= np.where(t > end - r, 0.5 + 0.5 * np.cos(np.pi * np.clip((t - (end - r)) / r, 0, 1)), 1)
        e[t > end] = 0
    return e


def osc(freq, dur, partials=((1, 1.0),), phase=0.0):
    """Additive oscillator; freq is a number or a per-sample array (pitch sweeps, vibrato)."""
    n = n_(dur)
    f = np.full(n, float(freq)) if np.isscalar(freq) else np.asarray(freq)[:n]
    ph = 2 * np.pi * np.cumsum(f) / SR + phase
    out = np.zeros(n)
    for k, a in partials:
        fk = f * k
        out += a * np.sin(ph * k) * (fk < SR * 0.45)
    return out


def sweep(f0, f1, dur, curve="exp"):
    t = t_(dur) / max(dur, 1e-9)
    return f0 * (f1 / f0) ** t if curve == "exp" else f0 + (f1 - f0) * t


def square(freq, dur, top=9):
    return osc(freq, dur, [(k, 1.0 / k) for k in range(1, top + 1, 2)])


def saw(freq, dur, top=10):
    return osc(freq, dur, [(k, 1.0 / k) for k in range(1, top + 1)])


def noise(dur, rng, color="white"):
    x = rng.standard_normal(n_(dur))
    if color == "white":
        return x
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    f[0] = f[1] if len(f) > 1 else 1
    X /= np.sqrt(f) if color == "pink" else f
    y = np.fft.irfft(X, len(x))
    return y / (np.std(y) or 1)


def filt(x, lo=None, hi=None, order=2):
    """Zero-phase Butterworth-magnitude band filter by FFT (zero-padded, no wrap)."""
    n = len(x)
    nfft = 1 << math.ceil(math.log2(2 * n + 1))
    X = np.fft.rfft(x, nfft)
    f = np.fft.rfftfreq(nfft, 1 / SR)
    H = np.ones_like(f)
    if hi:
        H /= np.sqrt(1 + (f / hi) ** (2 * order))
    if lo:
        with np.errstate(divide="ignore"):
            H /= np.sqrt(1 + (lo / np.maximum(f, 1e-9)) ** (2 * order))
    return np.fft.irfft(X * H, nfft)[:n]


def modal(dur, modes, rng=None):
    """Sum of decaying sines: (freq, tau, amp). Metal, wood, glass, bells."""
    t = t_(dur)
    out = np.zeros_like(t)
    for f, tau, a in modes:
        ph = rng.uniform(0, 2 * np.pi) if rng is not None else 0.0
        out += a * np.sin(2 * np.pi * f * t + ph) * np.exp(-t / tau)
    return out


def bell(f, dur, tau, bright=1.0):
    return modal(dur, [(f, tau, 1.0), (f * 2.0, tau * 0.6, 0.35 * bright), (f * 2.76, tau * 0.5, 0.25 * bright),
                       (f * 5.4, tau * 0.3, 0.12 * bright)])


def click(dur, rng, lo=1500, tau=0.0015):
    return filt(noise(dur, rng) * decay(dur, tau), lo=lo)


def loopify(x, L, xf):
    """Exact-length seamless loop: crossfade the overhang (x must be at least L + xf long)."""
    n, f = n_(L), n_(xf)
    y = x[:n].copy()
    w = np.sin(0.5 * np.pi * np.arange(f) / f) ** 2
    y[:f] = x[:f] * w + x[n:n + f] * (1 - w)
    return y


def formant_voice(dur, f0, rng, bend=0.25, vib=0.02, formants=((800, 80, 1.0), (1150, 90, 0.5), (2900, 120, 0.3))):
    t = t_(dur)
    s = np.clip(t / 0.5, 0, 1)
    f = f0 * (1 + bend * (3 * s ** 2 - 2 * s ** 3)) * (1 + vib * np.sin(2 * np.pi * rng.uniform(5.5, 6.5) * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    out = np.zeros_like(t)
    for k in range(1, 24):
        fk = f * k
        g = sum(a / (1 + ((fk - F) / (bw / 2)) ** 2) for F, bw, a in formants) / k ** 0.5
        out += g * np.sin(k * ph) * (fk < 6000)
    return out


# ------------------------------------------------------------------ recipes (each returns mono float)
def r_ui_click(rng):
    b = buf(0.08)
    place(b, click(0.01, rng, lo=2500, tau=0.0008), 0)
    place(b, osc(1850, 0.05) * decay(0.05, 0.012), 0.001, 0.6)
    return b


def r_ticket_chime(rng):
    b = buf(0.42)
    place(b, bell(1318.5, 0.3, 0.09), 0, 0.8)
    place(b, bell(1046.5, 0.3, 0.12), 0.11, 0.8)
    return b


def r_countdown_tick(rng):
    b = buf(0.16)
    place(b, modal(0.15, [(880, 0.03, 1), (1813, 0.02, 0.5), (2650, 0.015, 0.45)], rng), 0)
    place(b, click(0.01, rng, lo=1000), 0, 0.6)
    return b


def r_lever_clunk(rng):
    b = buf(0.5)
    place(b, click(0.012, rng, lo=1500, tau=0.002), 0, 0.8)
    place(b, osc(sweep(140, 55, 0.2), 0.2) * decay(0.2, 0.07), 0.002, 0.5)
    place(b, filt(noise(0.12, rng), hi=400) * decay(0.12, 0.03), 0.002, 0.3)
    place(b, modal(0.12, [(640, 0.03, 0.8), (1180, 0.025, 0.6)], rng), 0.001)
    place(b, modal(0.45, [(318, 0.12, 0.5), (781, 0.09, 0.45), (1453, 0.06, 0.35), (2210, 0.04, 0.2)], rng), 0.004)
    return b


def r_points_throw(rng):
    b = buf(0.5)
    for at, g in ((0, 1.0), (0.09, 0.8)):
        place(b, modal(0.2, [(610, 0.05, 1), (1420, 0.035, 0.6), (2530, 0.02, 0.4)], rng), at, g)
        place(b, click(0.008, rng, lo=800), at, 0.4 * g)
    place(b, osc(90, 0.2) * decay(0.2, 0.05), 0.1, 0.6)
    return filt(b, hi=3500)


def r_junction_beep(rng):
    b = buf(0.46)
    for at in (0, 0.22):
        place(b, square(1000, 0.14, top=5) * env(0.14, 0.005, 0.012), at, 0.7)
    return b


def r_stamp_slam(rng):
    b = buf(0.3)
    place(b, osc(sweep(95, 70, 0.15), 0.15) * decay(0.15, 0.05), 0, 0.5)
    place(b, filt(noise(0.08, rng), hi=600) * decay(0.08, 0.02), 0, 0.5)
    place(b, modal(0.2, [(220, 0.05, 0.6), (540, 0.04, 0.6), (1100, 0.02, 0.45)], rng), 0)
    place(b, filt(noise(0.05, rng), lo=1500, hi=5000) * decay(0.05, 0.012), 0.003, 1.0)
    return b


def r_whistle(rng):
    dur = 1.8
    t = t_(dur)
    b = np.zeros_like(t)
    e = env(dur, 0.06, 0.25)
    for i, f0 in enumerate((494, 622, 740)):
        f = f0 * (1 - 0.03 * np.exp(-t / 0.05)) * (1 + 0.003 * np.sin(2 * np.pi * 5.5 * t + i))
        b += osc(f, dur, [(1, 1), (2, 0.35), (3, 0.18), (4, 0.08)])
    b += 0.9 * filt(noise(dur, rng), lo=700, hi=3000)
    return b * e


def r_horn(rng):
    b = saw(311, 0.8, 10) + saw(370, 0.8, 10)
    return filt(b, hi=2500) * env(0.8, 0.03, 0.08)


def r_brake_hiss(rng):
    dur = 1.6
    t = t_(dur)
    e = np.clip(t / 0.04, 0, 1) * np.where(t > 0.5, np.exp(-(t - 0.5) / 0.4), 1)
    b = filt(noise(dur, rng), lo=1800, hi=9000) * e
    b += 0.3 * filt(noise(dur, rng), hi=120) * decay(dur, 0.3)
    place(b, osc(80, 0.2) * decay(0.2, 0.05), 0, 0.5)
    return b


def r_cash_register(rng):
    b = buf(0.95)
    d = 0.12
    drawer = filt(noise(d, rng), lo=900, hi=2600) * env(d, 0.02, 0.03)
    place(b, drawer, 0, 0.5)
    place(b, bell(2637, 0.8, 0.3), 0.13, 0.7)
    place(b, bell(3136, 0.8, 0.25), 0.13, 0.5)
    return b


def r_crate_thump(rng):
    b = buf(0.6)
    place(b, osc(sweep(75, 50, 0.25), 0.25) * decay(0.25, 0.09), 0, 0.3)
    place(b, modal(0.3, [(180, 0.06, 0.5), (410, 0.05, 0.8), (690, 0.04, 0.8), (1210, 0.025, 0.5)], rng), 0)
    place(b, modal(0.5, [(95, 0.2, 0.3), (260, 0.15, 0.2)], rng), 0.002)
    place(b, filt(noise(0.06, rng), hi=900) * decay(0.06, 0.02), 0, 0.6)
    t = t_(0.2)
    creak = osc(300 * (1 + 0.08 * np.sin(2 * np.pi * 18 * t)), 0.2, [(1, 1), (2, 0.5), (3, 0.3)]) * env(0.2, 0.03, 0.08)
    place(b, creak, 0.18, 0.15)
    return b


def r_shovel_thud(rng):
    b = buf(0.6)
    d = 0.15
    grain = np.repeat(rng.uniform(0.3, 1.0, n_(d) // 240 + 1), 240)[:n_(d)]
    place(b, filt(noise(d, rng), lo=2000, hi=6000) * grain * env(d, 0.1, 0.03), 0, 0.8)
    place(b, osc(85, 0.2) * decay(0.2, 0.06), 0.17, 0.4)
    place(b, modal(0.15, [(310, 0.04, 0.6), (720, 0.03, 0.5), (1350, 0.02, 0.3)], rng), 0.17)
    place(b, filt(noise(0.1, rng), hi=700) * decay(0.1, 0.03), 0.17, 0.6)
    for _ in range(6):
        place(b, click(0.01, rng, lo=1500), 0.17 + rng.uniform(0, 0.08), rng.uniform(0.15, 0.35))
    place(b, filt(noise(0.4, rng), hi=350) * env(0.4, 0.08, 0.25), 0.2, 0.6)
    return b


def r_wrench_clank(rng):
    b = buf(0.8)
    for at, g in ((0, 1.0), (0.15, 0.85)):
        place(b, modal(0.3, [(520, 0.08, 1), (1231, 0.06, 0.6), (2317, 0.04, 0.45), (3790, 0.03, 0.3)], rng), at, g)
        place(b, click(0.008, rng), at, 0.4 * g)
    place(b, bell(1568, 0.45, 0.25), 0.34, 0.6)
    return b


def r_alarm_coal(rng):
    b = buf(1.7)
    for base, g in ((0.0, 1.0), (0.85, 0.85)):
        for at, f0, d in ((0.0, 494, 0.34), (0.38, 370, 0.42)):
            f = sweep(f0, f0 * 0.93, d, curve="lin")
            tone = filt(square(f, d, top=9), hi=3500) * env(d, 0.03, 0.08)
            place(b, tone, base + at, g)
    return b


def r_alarm_pressure(rng):
    b = buf(1.7)
    for at in (0.0, 0.6):
        place(b, filt(saw(sweep(700, 1600, 0.55), 0.55, 6), hi=5000) * env(0.55, 0.02, 0.05), at, 0.8)
    for i in range(6):
        place(b, square(2000, 0.04, top=5) * env(0.04, 0.003, 0.008), 1.2 + i * 0.08, 0.6)
    t = t_(1.7)
    place(b, filt(noise(1.7, rng), lo=2500) * np.clip(t / 1.2, 0, 1) * env(1.7, 0.2, 0.1), 0, 0.15)
    return b


def r_breakdown_bang(rng):
    b = buf(1.3)
    place(b, noise(0.01, rng) * decay(0.01, 0.003), 0, 1.0)
    place(b, modal(0.6, [(170, 0.12, 0.35), (433, 0.12, 0.6), (912, 0.08, 0.7), (1650, 0.05, 0.6), (2710, 0.04, 0.4)], rng), 0)
    for _ in range(40):
        at = rng.uniform(0.05, 0.6)
        place(b, click(0.004, rng, lo=3000, tau=0.0008), at, rng.uniform(0.1, 0.5) * (1 - at))
    for at in (0.7, 0.95):
        place(b, filt(square(220, 0.18, top=15), hi=4000) * env(0.18, 0.005, 0.02), at, 0.6)
    return b


def r_passengers_scream(rng):
    b = buf(1.4)
    for i, f0 in enumerate((230, 290, 340, 400, 460)):
        d = rng.uniform(1.1, 1.25)
        v = formant_voice(d, f0 * rng.uniform(0.97, 1.03), rng) * env(d, 0.06, 0.25)
        place(b, v, i * 0.025 + rng.uniform(0, 0.08), rng.uniform(0.6, 1.0))
    b += 0.15 * filt(noise(1.4, rng), lo=1000, hi=4000) * env(1.4, 0.1, 0.3)
    return b


def r_glass_smash(rng):
    b = buf(1.1)
    place(b, filt(noise(0.015, rng), lo=800) * decay(0.015, 0.004), 0, 1.0)
    place(b, modal(0.1, [(1800, 0.02, 0.5), (3100, 0.015, 0.4)], rng), 0)
    for _ in range(45):
        at = min(0.9, 0.02 + rng.exponential(0.15))
        f = math.exp(rng.uniform(math.log(2500), math.log(8000)))
        tau = rng.uniform(0.03, 0.12)
        place(b, modal(tau * 5, [(f, tau, 1.0)], rng), at, rng.uniform(0.05, 0.3) * (1 - at))
    return b


def r_coupling_snap(rng):
    b = buf(1.2)
    place(b, click(0.006, rng, lo=2000, tau=0.001), 0, 1.0)
    place(b, osc(110, 0.2) * decay(0.2, 0.08), 0.02, 0.6)
    f = sweep(900, 600, 0.4)
    place(b, osc(f, 0.4, [(1, 1), (2.4, 0.4), (4.1, 0.2)]) * decay(0.4, 0.25), 0.005, 0.5)
    at, gap = 0.15, 0.06
    while at < 1.0:
        k = rng.uniform(0.85, 1.15)
        place(b, modal(0.05, [(1400 * k, 0.01, 1), (2600 * k, 0.008, 0.6)], rng), at, 0.35 * (1.05 - at))
        at += gap * rng.uniform(0.7, 1.3)
        gap *= 1.08
    return b


def r_boiler_boom(rng):
    b = buf(3.1)
    place(b, filt(noise(0.02, rng), lo=1000) * decay(0.02, 0.006), 0, 0.8)
    place(b, osc(sweep(90, 28, 1.2), 1.2) * decay(1.2, 0.5), 0, 0.6)
    place(b, filt(noise(2.0, rng), hi=250) * decay(2.0, 0.6, attack=0.005), 0, 0.6)
    place(b, filt(noise(1.0, rng), lo=300, hi=2000) * decay(1.0, 0.3, attack=0.003), 0, 1.2)
    for _ in range(25):
        at = rng.uniform(0.3, 1.8)
        f = rng.uniform(400, 3000)
        place(b, modal(0.3, [(f, rng.uniform(0.03, 0.1), 1), (f * 2.3, 0.03, 0.4)], rng), at, rng.uniform(0.1, 0.35) * (2 - at) / 2)
    place(b, filt(noise(1.6, rng), lo=2000) * decay(1.6, 0.8, attack=0.1), 0.2, 0.25)
    place(b, modal(0.8, [(700, 0.35, 0.7), (1880, 0.25, 0.4), (3300, 0.15, 0.3)], rng), 2.3, 0.8)
    place(b, modal(0.4, [(4200, 0.2, 1.0)], rng), 2.65, 0.3)
    return b


def r_wheels_loop(rng):
    L, xf = 4.8, 0.3
    b = np.zeros(n_(L))
    rum = filt(noise(L + xf, rng, "brown"), lo=35, hi=300)
    t = t_(L + xf)
    rum *= 1 + 0.15 * np.sin(2 * np.pi * t / L * 1)
    b += 0.5 * loopify(rum, L, xf)
    b += 0.03 * loopify(filt(noise(L + xf, rng), lo=2000, hi=4000), L, xf)
    clack = modal(0.15, [(380, 0.04, 1), (950, 0.03, 0.5), (2100, 0.015, 0.3)], rng)
    clack += 0.5 * filt(noise(0.15, rng), hi=700) * decay(0.15, 0.01) + 0.6 * osc(70, 0.15) * decay(0.15, 0.03)
    for bar in range(4):
        for off, g in ((0.0, 1.0), (0.13, 0.9), (0.6, 0.6), (0.73, 0.55)):
            place_wrap(b, clack, bar * 1.2 + off + rng.uniform(-0.005, 0.005), g * rng.uniform(0.9, 1.1))
    return b


def r_firebox_loop(rng):
    L, xf = 6.0, 0.4
    t = t_(L + xf)
    roar = filt(noise(L + xf, rng, "brown"), lo=40, hi=500)
    am = 1 + 0.2 * np.sin(2 * np.pi * t / L * 2 + 1) + 0.1 * np.sin(2 * np.pi * t / L * 5)
    b = loopify(roar * am, L, xf)
    for _ in range(60):
        f_lo = rng.uniform(1500, 3000)
        place_wrap(b, filt(noise(0.004, rng), lo=f_lo, hi=6000) * decay(0.004, 0.001), rng.uniform(0, L), rng.uniform(0.2, 0.8))
    return b


def r_wind_bed(rng):
    L, xf = 8.0, 0.5
    t = t_(L + xf)
    src = noise(L + xf, rng, "pink")
    bands = [filt(src, lo=250, hi=700), filt(src, lo=400, hi=1100), filt(src, lo=600, hi=1600)]
    w1 = 0.5 + 0.5 * np.sin(2 * np.pi * t / L)
    w2 = 0.5 + 0.5 * np.sin(2 * np.pi * t / L * 2 + 2)
    mix = bands[0] * (1 - w1) + bands[1] * w1 * (1 - w2) + bands[2] * w1 * w2
    gust = 1 + 0.5 * np.sin(2 * np.pi * t / L * 2 + 0.5) ** 2
    return loopify(mix * gust, L, xf)


def r_radio_loop(rng):
    L, beat = 8.0, 0.5
    b = np.zeros(n_(L))
    midi = lambda m: 440 * 2 ** ((m - 69) / 12)  # noqa: E731
    chords = [(60, 64, 67), (65, 69, 72), (67, 71, 74), (60, 64, 67)]
    shape = [0, 1, 2, 1, 3, 2, 1, 2]
    for bar, ch in enumerate(chords):
        tones = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[0] + 24]
        for i, s in enumerate(shape):
            at = bar * 4 * beat + i * beat / 2
            place_wrap(b, square(midi(tones[s]), 0.3, top=7) * decay(0.3, 0.1, attack=0.004), at, 0.35)
        for q in range(4):
            root = ch[0] - 24 if q % 2 == 0 else ch[2] - 24
            place_wrap(b, osc(midi(root), 0.45, [(1, 1), (3, 1 / 9), (5, 1 / 25)]) * decay(0.45, 0.2, attack=0.005),
                       bar * 4 * beat + q * beat, 0.6)
    b = filt(b, lo=350, hi=3200)
    b = np.tanh(2 * b / (np.max(np.abs(b)) or 1)) / np.tanh(2)
    b += 0.02 * filt(noise(L, rng), lo=1000)
    for _ in range(25):
        place_wrap(b, click(0.003, rng, lo=2000), rng.uniform(0, L), rng.uniform(0.05, 0.2))
    return b


RECIPES = {k[2:]: v for k, v in globals().items() if k.startswith("r_")}


# ------------------------------------------------------------------ render
def level(x, metric):
    r = al.loudness([x], SR)
    return r["m_max"] if metric == "m_max" else r["integrated"]


def normalise(x, std):
    """Gain to the class target; soft-clip into the ceiling when the peak would pass -1 dBTP. Returns (y, notes)."""
    metric, target = std["metric"], std["target"]
    ceil = min(CEIL, 10 ** ((std.get("tp_max", -1) - 0.2) / 20))
    x = x - np.mean(x)
    y, g, notes = x, 1.0, []
    for _ in range(8):
        cur = level(y, metric)
        if cur is None or abs(cur - target) < 0.1:
            break
        g *= 10 ** ((target - cur) / 20)
        z = x * g
        pk = np.max(np.abs(z)) or 1.0
        y = z if pk <= ceil else ceil * np.tanh(z / ceil)
    if np.max(np.abs(x * g)) > ceil:
        notes.append("soft-clipped into the ceiling")
    tp = al.true_peak([y])
    if tp is not None and tp > std.get("tp_max", -1):
        y = y * 10 ** ((std.get("tp_max", -1) - 0.1 - tp) / 20)
        notes.append("true peak trimmed after clipping")
    return y, notes


def render(sid, recipe, std, out_dir, seed=7):
    """Write PLACEHOLDER_<sid>.wav; return a manifest row (measured by audiolib)."""
    if recipe not in RECIPES:
        raise KeyError(f"no recipe {recipe!r}")
    rng = np.random.default_rng(seed + sum(map(ord, recipe)))
    x = RECIPES[recipe](rng)
    y, notes = normalise(np.asarray(x, dtype=np.float64), std)
    if std["metric"] != "integrated":
        y[-min(len(y), n_(0.004)):] *= np.linspace(1, 0, min(len(y), n_(0.004)))
    out = Path(out_dir) / f"PLACEHOLDER_{sid}.wav"
    info = {"INAM": f"PLACEHOLDER {sid}", "ICMT": "PLACEHOLDER - synthesised by rr-soundsmith for prototyping; not "
            "final audio; replace before release", "ISFT": "rr-soundsmith synth.py", "IGNR": "placeholder"}
    al.write_wav(out, SR, [y], bits=16, info=info)
    m = al.measure(out, loop=std["metric"] == "integrated")
    return {"id": sid, "file": out.name, "recipe": recipe, "seed": seed,
            "sha1": hashlib.sha1(out.read_bytes()).hexdigest()[:12], "notes": notes, "measured": m}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out", default=".")
    a = ap.parse_args(argv)
    if a.list or not a.ids:
        print(" ".join(sorted(RECIPES)))
        return 0
    std = {"metric": "m_max", "target": -14, "tp_max": -1}
    Path(a.out).mkdir(parents=True, exist_ok=True)
    for sid in a.ids:
        row = render(sid, sid, std, a.out)
        print(row["file"], row["measured"].get("m_max"), row["measured"].get("true_peak"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
