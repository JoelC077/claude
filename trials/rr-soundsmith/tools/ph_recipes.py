#!/usr/bin/env python3
"""OBSOLETE since the rr-soundsmith fix (kept as evidence of FRICTION F1): the four lobby recipes are built in now, and a mission adds a placeholder through the soundmap "synth" field or <presets>/recipes.py without editing skill code.
TRIAL WORKAROUND (not part of rr-soundsmith): run `sound.py` with extra placeholder recipes for sounds added in a
mission copy of the soundmap. rr-soundsmith keys recipes by sound id inside synth.py, so a mission cannot add a sound
without editing skill code, and `validate --strict` fails on "no placeholder recipe". This wrapper registers
recipes for the Depot Lobby sounds (lobby_bed, queue_punch, queue_bell, guard_whistle) and then runs sound.py's main.

  python3 ph_recipes.py <sound.py args...>      e.g. validate --strict | synth all --out DIR | build --out DIR
  python3 ph_recipes.py --help-recipes          list the recipes this file adds

The rr-soundsmith skill folder is found by glob (env RR_SOUNDSMITH_SKILL overrides). Needs numpy (as synth does).
"""
import glob
import os
import sys
from pathlib import Path


def skill_dir():
    if os.environ.get("RR_SOUNDSMITH_SKILL"):
        return Path(os.environ["RR_SOUNDSMITH_SKILL"])
    pats = [str(Path.home() / ".claude/skills/**/rr-soundsmith/SKILL.md"), "/home/user/**/rr-soundsmith/SKILL.md"]
    for p in pats:
        hits = sorted(glob.glob(p, recursive=True))
        if hits:
            return Path(hits[0]).parent
    sys.exit("rr-soundsmith not found: set RR_SOUNDSMITH_SKILL")


sys.path.insert(0, str(skill_dir() / "scripts"))
import numpy as np  # noqa: E402
import synth as sy  # noqa: E402  (the same module object sound.py imports)
from synth import (bell, buf, click, decay, env, filt, loopify, modal, n_, noise, osc, place, place_wrap,  # noqa: E402
                   sweep, t_)


def r_lobby_bed(rng):
    L, xf = 12.0, 0.5
    b = 0.35 * loopify(filt(noise(L + xf, rng, "brown"), lo=40, hi=200), L, xf)       # resting loco idle rumble
    b += 0.02 * osc(100, L, [(1, 1.0), (2, 0.6), (3, 0.3), (4, 0.15)])               # lantern buzz (1200 whole cycles)
    for k in range(3):                                                                  # slow steam breaths, 4 s apart
        d = 1.1
        puff = filt(noise(d, rng), lo=1500, hi=7000) * env(d, 0.18, 0.7)
        place_wrap(b, puff, k * 4.0 + 0.4 + rng.uniform(-0.1, 0.1), 0.22)
    for _ in range(5):                                                                  # sparse distant birds
        at = rng.uniform(0, L)
        for j in range(int(rng.integers(2, 4))):
            d = 0.07
            chirp = osc(sweep(rng.uniform(2800, 3400), rng.uniform(4000, 4800), d), d) * env(d, 0.01, 0.03)
            place_wrap(b, chirp, at + j * 0.11, 0.05)
    return b


def r_queue_punch(rng):
    b = buf(0.3)
    for at, g in ((0.0, 1.0), (0.07, 0.85)):
        place(b, click(0.012, rng, lo=1200, tau=0.0015), at, 0.9 * g)                   # punch bite
        place(b, filt(noise(0.03, rng), lo=1000, hi=3000) * decay(0.03, 0.008), at + 0.002, 0.6 * g)  # card snap
        place(b, modal(0.12, [(1650, 0.025, 0.7), (2890, 0.018, 0.45), (4100, 0.01, 0.25)], rng), at + 0.001, 0.5 * g)
    return b


def r_queue_bell(rng):
    b = buf(0.45)
    place(b, click(0.006, rng, lo=2000, tau=0.0008), 0, 0.5)
    place(b, bell(1568, 0.44, 0.1, bright=1.2), 0, 0.9)
    return b


def r_guard_whistle(rng):
    dur = 0.95
    t = t_(dur)
    trill = 0.55 + 0.45 * np.sin(2 * np.pi * 30 * t) ** 2                                 # the pea rattling
    f = 2850 * (1 + 0.012 * np.sin(2 * np.pi * 30 * t)) * (1 - 0.04 * np.exp(-t / 0.03))
    tone = osc(f, dur, [(1, 1.0), (2, 0.12), (3, 0.05)]) * trill
    breath = filt(noise(dur, rng), lo=2000, hi=5500) * (0.25 + 0.75 * np.exp(-t / 0.06))
    return (tone + 0.35 * breath) * env(dur, 0.015, 0.09)


EXTRA = {"lobby_bed": r_lobby_bed, "queue_punch": r_queue_punch, "queue_bell": r_queue_bell,
         "guard_whistle": r_guard_whistle}
sy.RECIPES.update(EXTRA)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help-recipes":
        print("adds recipes: " + " ".join(EXTRA))
        sys.exit(0)
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help") and len(sys.argv) == 2:
        print(__doc__)
        sys.exit(0)
    import sound  # noqa: E402
    sys.exit(sound.main(sys.argv[1:]))
