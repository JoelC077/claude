#!/usr/bin/env python3
"""Retro computer power-up / power-down jingles (1.0 s each), synthesised from code with rr-soundsmith's synth kit.

  python3 computer_power_sfx.py [--out DIR]

Writes PLACEHOLDER_computer_power_up.wav and PLACEHOLDER_computer_power_down.wav (48 kHz mono 16-bit, levelled to
the one-shot standard: momentary max -14 LUFS, <= -1 dBTP). The r_* functions follow the soundsmith recipes.py
convention, so this file can be copied to <presets>/recipes.py if the sounds join the soundmap.
"""
import argparse, sys
from pathlib import Path

sys.dont_write_bytecode = True


def _find_synth():
    for root in (Path.home() / ".claude/skills", Path("/home/user")):
        for p in sorted(root.glob("**/rr-soundsmith/scripts/synth.py")):
            return p.parent
    sys.exit("rr-soundsmith synth.py not found")


sys.path.insert(0, str(_find_synth()))
from synth import *  # noqa: E402,F401,F403  (buf, place, osc, sweep, env, decay, click, filt, square, t_, render)
import synth  # noqa: E402

C4, C5, E5, G5, C6, E6, C7 = 261.63, 523.25, 659.26, 783.99, 1046.5, 1318.51, 2093.0
ARP = [C5, E5, G5, C6]
ONESHOT = {"metric": "m_max", "target": -14, "tp_max": -1}


def pulse(freq, dur, duty=0.25, top=40):
    """Band-limited pulse wave (the NES/8-bit lead); duty 0.5 is a square."""
    return osc(freq, dur, [(k, (2 / (k * np.pi)) * np.sin(k * np.pi * duty)) for k in range(1, top + 1)])


def triangle(freq, dur, top=15):
    return osc(freq, dur, [(k, (-1) ** ((k - 1) // 2) / k ** 2) for k in range(1, top + 1, 2)])


def chip_note(b, f, at, dur=0.085, gain=0.45, duty=0.25, echo=0.09):
    x = pulse(f, dur, duty) * env(dur, 0.002, 0.03)
    place(b, x, at, gain)
    place(b, x, at + echo, gain * 0.27)  # one soft chip-style echo


def r_computer_power_up(rng):
    L = 1.0
    b = buf(L)
    # power switch: click + low thump
    place(b, click(0.015, rng, lo=1800, tau=0.0012), 0.0, 0.4)
    place(b, osc(sweep(120, 70, 0.08), 0.08) * decay(0.08, 0.025), 0.0, 0.5)
    # power supply spinning up: soft square whine 180 -> 900 Hz
    d = 0.16
    place(b, filt(square(sweep(180, 900, d), d, top=7), hi=3000) * env(d, 0.03, 0.05), 0.02, 0.18)
    # rising arpeggio C5 E5 G5 C6
    for i, f in enumerate(ARP):
        chip_note(b, f, 0.14 + i * 0.065)
    # "ta-da" chord from 0.40 to the end: lead scoops B5 -> C6, vibrato fades in
    at, d = 0.40, L - 0.40
    t = t_(d)
    scoop = np.minimum(t / 0.03, 1)
    vib = 1 + 0.011 * np.sin(2 * np.pi * 6.0 * t) * np.clip((t - 0.18) / 0.15, 0, 1)
    lead_f = C6 * 2 ** ((scoop - 1) / 12) * vib
    shape = env(d, 0.004, 0.2) * decay(d, 0.45)
    place(b, pulse(lead_f, d, 0.25) * shape, at, 0.42)
    place(b, pulse(E6 * vib, d, 0.125) * shape, at, 0.14)
    place(b, pulse(G5 * vib, d, 0.5) * shape, at, 0.2)
    place(b, triangle(C4, d) * shape, at, 0.4)
    place(b, bell(C7, 0.3, 0.07), at + 0.01, 0.12)  # "ready" sparkle
    return b


def r_computer_power_down(rng):
    L = 1.0
    b = buf(L)
    # falling arpeggio C6 G5 E5 C5
    for i, f in enumerate(reversed(ARP)):
        chip_note(b, f, i * 0.06, dur=0.08, echo=0.085)
    # droopy pitch dive C5 -> 50 Hz with a cartoon wobble (the "shrink")
    at, d = 0.25, 0.58
    t = t_(d)
    f = sweep(C5, 50, d) * (1 + 0.03 * np.sin(2 * np.pi * 7 * t))
    place(b, filt(pulse(f, d, 0.5) * env(d, 0.003, 0.2) * decay(d, 0.35), hi=5000), at, 0.5)
    # CRT whine collapsing
    place(b, osc(sweep(3200, 700, 0.35), 0.35) * decay(0.35, 0.12), at, 0.06)
    # off switch: click + small thump
    place(b, click(0.015, rng, lo=1800, tau=0.0012), 0.86, 0.35)
    place(b, osc(sweep(110, 60, 0.1), 0.1) * decay(0.1, 0.03), 0.86, 0.4)
    return b


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent))
    a = ap.parse_args(argv)
    Path(a.out).mkdir(parents=True, exist_ok=True)
    for sid, fn in (("computer_power_up", r_computer_power_up), ("computer_power_down", r_computer_power_down)):
        row = synth.render(sid, sid, ONESHOT, a.out, fn=fn)
        m = row["measured"]
        print(row["file"], f"{m.get('duration')} s", f"m_max {m.get('m_max')} LUFS", f"TP {m.get('true_peak')} dBTP",
              *row["notes"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
