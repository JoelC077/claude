"""Draw the carriage_split row that the rr-soundsmith sheet cannot (its timeline shows rr-game-feel events only).

Writes sheet/split_timeline.png in the sheet's timeline style: each split sound's envelope (RMS per 10 ms, as the
sheet draws it) at the owner's offsets from src/kit/break_spec.json (t 0 = the snap), from -0.3 to 3.5 s. Fill
height = the file's envelope x its in-game level (ladder + trim from soundmap.json, linear), so the boom is full
height and the hierarchy reads at a glance. The split has no rr-game-feel channels: TrainSplitClient plays these
events directly and drives its own camera shake, drawn as markers on the last lane.

    python3 <this folder>/split_timeline.py        (reads final/<id>.wav, which is the delivered audio)
"""
import json
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
T0, T1 = -0.3, 3.5
# (sound id, file, offset s, playback speed): break_spec events; topple_crash_2 is topple_crash's file at 0.84
ROWS = [("metal_tear", "metal_tear", -0.25, 1.0), ("split_explosion", "split_explosion", 0.0, 1.0),
        ("split_glass", "split_glass", 0.0, 1.0), ("wreck_scrape", "wreck_scrape", 0.3, 1.0),
        ("debris_rain", "debris_rain", 0.8, 1.0), ("topple_crash", "topple_crash", 1.5, 1.0),
        ("topple_crash_2", "topple_crash", 2.0, 0.84)]
SHAKE = [(0.0, "shake big"), (1.5, "shake medium"), (2.0, "shake medium")]
# the rr-soundsmith sheet palette (sheet.py)
BG, INK, DIM, GRID = (21, 23, 28), (236, 236, 236), (150, 152, 160), (54, 58, 66)
TIER = {1: (226, 58, 46), 2: (226, 58, 46), 3: (242, 194, 48), 4: (47, 143, 134), 5: (170, 172, 180)}
SHAKE_COL = (242, 194, 48)


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def read(path):
    with wave.open(str(path), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32768.0, w.getframerate()


def envelope(x, rate, speed):
    """RMS per 10 ms of the file as played at `speed` (a slower PlaybackSpeed stretches it), peak 1."""
    k = max(1, int(0.01 * rate * speed))
    n = len(x) // k
    r = np.sqrt(np.mean(x[:n * k].reshape(n, k) ** 2, axis=1))
    return r / (r.max() or 1.0)


def main():
    m = json.loads((HERE / "soundmap.json").read_text(encoding="utf-8"))
    ladder, sounds = m["ladder"], m["sounds"]
    level = {sid: ladder[f"t{sounds[sid]['tier']}"] + sounds[sid].get("trim_db", 0) for sid, *_ in ROWS}
    boom = level["split_explosion"]

    w, left, lane, top = 900, 190, 24, 62
    h = top + 22 + lane * len(ROWS) + 20 + 26
    im = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(im)
    X = lambda t: left + (t - T0) / (T1 - T0) * (w - left - 10)  # noqa: E731
    d.text((6, 4), "carriage_split: sound envelopes (fill) at the owner's offsets, t 0 = the snap "
                   "(src/kit/break_spec.json); fill height = envelope x in-game level", fill=INK, font=font(11))
    d.text((6, 20), "No rr-game-feel channels: TrainSplitClient plays these direct events and drives its own "
                    "camera shake (markers on the last lane).", fill=DIM, font=font(10))
    for i in range(int(round((T1 - T0) / 0.1)) + 1):
        t = round(T0 + i * 0.1, 2)
        major = abs(t * 2 - round(t * 2)) < 1e-6
        d.line([(X(t), top - 4), (X(t), h - 22)], fill=GRID if major else (34, 37, 43))
        if major:
            d.text((X(t) - 8, h - 20), f"{t:.1f}", fill=DIM, font=font(9))
    d.line([(X(0), top - 14), (X(0), h - 22)], fill=INK, width=1)

    d.text((6, top + 2), "carriage_split", fill=INK, font=font(12))
    d.text((6, top + 16), "direct events, TrainSplitClient", fill=DIM, font=font(9))
    marks = {}
    for i, (sid, fname, off, speed) in enumerate(ROWS):
        x, rate = read(HERE / "final" / f"{fname}.wav")
        env = envelope(x, rate, speed)
        gain = 10 ** ((level[sid] - boom) / 20)
        y = top + 30 + i * lane
        s = sounds[sid]
        label = f"{sid} @{off:+.2f} s" + (f" x{speed:g}" if speed != 1.0 else "")
        d.text((18, y + 4), label, fill=INK, font=font(10))
        d.text((18, y + 15), f"t{s['tier']} {s['group']}, {level[sid]:g} LUFS", fill=DIM, font=font(8))
        base = y + lane - 3
        pts = [(X(off + j * 0.01), base - v * gain * (lane - 5)) for j, v in enumerate(env) if off + j * 0.01 <= T1]
        d.polygon([(pts[0][0], base)] + pts + [(pts[-1][0], base)], fill=TIER.get(s["tier"], INK))
        pk = int(np.argmax(env))
        marks[sid] = off + (pk + 0.5) * 0.01
    y = top + 30 + len(ROWS) * lane + 4
    d.text((18, y), "shake (TrainSplitClient)", fill=DIM, font=font(9))
    for t, name in SHAKE:
        d.line([(X(t), y + 2), (X(t) + 14, y + 2)], fill=SHAKE_COL, width=3)
        d.text((X(t) + 17, y - 4), name, fill=DIM, font=font(8))

    snap = marks["metal_tear"] * 1000
    peak = marks["split_explosion"] * 1000
    d.text((X(0) + 4, top - 14), f"tear snap {snap:+.0f} ms, boom peak {peak:+.0f} ms (10 ms envelope bins)",
           fill=INK, font=font(9))
    out = HERE / "sheet" / "split_timeline.png"
    im.save(out)
    print(f"wrote {out} {im.size}; tear snap {snap:+.1f} ms, boom peak {peak:+.1f} ms from t 0")


if __name__ == "__main__":
    main()
