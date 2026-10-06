"""Write the upload files for the carriage-split sounds: final/<id>.wav (six files).

The audio is bit-identical to ph/PLACEHOLDER_<id>.wav (written by `sound.py synth` from recipes.py); only the WAV
INFO tag changes. The synth tags every file it writes PLACEHOLDER, and the licence gate refuses a PLACEHOLDER-tagged
file posing as final. These sounds are the owner-requested deliverable ("Sounds: yes. Make some if you can"), made
from code only, so the upload copies are named after the sound and tagged "self-made, synthesised from code". The
owner still decides by ear (Studio listening test) before uploading and registering them.

topple_crash_2 has no file of its own: it is topple_crash's file played at 0.84 speed, 3 dB down (soundmap), so the
owner uploads topple_crash.wav once and registers that id for both.

Run from anywhere after `sound.py synth all --out <this folder>/ph`:
    python3 <this folder>/make_final.py
"""
import hashlib
import struct
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
IDS = ["metal_tear", "split_explosion", "split_glass", "debris_rain", "topple_crash", "wreck_scrape"]
RECIPE = {sid: f"recipes.py r_{sid}" for sid in IDS}
RECIPE["split_glass"] = "recipes.py r_split_glass: rr-soundsmith glass_smash shards, +3 semitones"


def info_chunk(fields):
    body = b"INFO"
    for key, text in fields:
        data = text.encode("ascii") + b"\0"
        if len(data) % 2:
            data += b"\0"
        body += key.encode("ascii") + struct.pack("<I", len(data)) + data
    return b"LIST" + struct.pack("<I", len(body)) + body


def read_pcm(path):
    with wave.open(str(path), "rb") as w:
        return w.getnchannels(), w.getsampwidth(), w.getframerate(), w.readframes(w.getnframes())


def write_final(sid):
    src, dst = HERE / "ph" / f"PLACEHOLDER_{sid}.wav", HERE / "final" / f"{sid}.wav"
    ch, sw, sr, pcm = read_pcm(src)
    fmt = struct.pack("<HHIIHH", 1, ch, sr, sr * ch * sw, ch * sw, sw * 8)
    info = info_chunk([
        ("INAM", sid),
        ("IPRD", "Risky Rails"),
        ("ICMT", f"Carriage-split SFX synthesised from code ({RECIPE[sid]}); no samples or third-party material; "
                 f"self-made"),
        ("ISFT", "numpy synthesis (rr-soundsmith sound.py synth, mission 260929-train-splits)"),
        ("IGNR", "sfx"),
    ])
    data = b"data" + struct.pack("<I", len(pcm)) + pcm + (b"\0" if len(pcm) % 2 else b"")
    body = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + info + data
    dst.parent.mkdir(exist_ok=True)
    dst.write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)
    same = read_pcm(dst) == (ch, sw, sr, pcm)
    print(f"{'ok ' if same else 'BAD'} {dst.name:22s} {len(pcm) / (sr * ch * sw):.3f} s  "
          f"sha1 {hashlib.sha1(dst.read_bytes()).hexdigest()[:12]}  pcm identical to {src.name}: {same}")
    return same


def write_preview():
    """preview/split_sequence_at_break.wav: break 1 as heard at the break, a listening aid (never upload it).
    Each final file sits at its break_spec offset with its in-game gain (ladder + trim, files are levelled to
    -14 LUFS momentary max); the boom adds its 3D layer (-4 dB, same samples); topple_crash_2 is topple_crash
    at 0.84 speed; wreck_scrape follows the client's rule at Speed 35 (PlaybackSpeed clamp(35/V, 0.7, 1.2) = 1.0,
    0.3 s fade once the wreck is under 2 studs/s: at (35 - 2) / 12 = 2.75 s, braking from the snap as in
    break_spec). Roll-off and engine ducking are left out (the Split layers are never ducked by the boom)."""
    import json
    import numpy as np
    m = json.loads((HERE / "soundmap.json").read_text(encoding="utf-8"))
    lad, snd = m["ladder"], m["sounds"]
    rate, t0, length = 48000, -0.25, 4.1

    def gain(sid, extra_db=0.0):
        return 10 ** ((lad[f"t{snd[sid]['tier']}"] + snd[sid].get("trim_db", 0) + 14.0 + extra_db) / 20)

    def load(fname, speed=1.0):
        x = np.frombuffer(read_pcm(HERE / "final" / f"{fname}.wav")[3], "<i2").astype(float) / 32768
        return np.interp(np.arange(0, len(x) - 1, speed), np.arange(len(x)), x) if speed != 1.0 else x

    V = 35.0
    scrape_speed, scrape_stop = min(max(35.0 / V, 0.7), 1.2), (V - 2.0) / 12.0

    mix = np.zeros(int(length * rate))
    for sid, fname, at, g, speed in [
            ("metal_tear", "metal_tear", -0.25, gain("metal_tear"), 1.0),
            ("split_explosion", "split_explosion", 0.0, gain("split_explosion") + gain("split_explosion", -4.0), 1.0),
            ("split_glass", "split_glass", 0.0, gain("split_glass"), 1.0),
            ("wreck_scrape", "wreck_scrape", 0.3, gain("wreck_scrape"), scrape_speed),
            ("debris_rain", "debris_rain", 0.8, gain("debris_rain"), 1.0),
            ("topple_crash", "topple_crash", 1.5, gain("topple_crash"), 1.0),
            ("topple_crash_2", "topple_crash", 2.0, gain("topple_crash_2"), 0.84)]:
        x = load(fname, speed)
        if sid == "wreck_scrape":                    # the client's stop: 0.3 s fade, then silence
            a, n = int((scrape_stop - at) * rate), int(0.3 * rate)
            x = x.copy()
            x[a:a + n] *= np.linspace(1.0, 0.0, n)[:max(0, len(x) - a)]
            x[a + n:] = 0.0
        i = int(round((at - t0) * rate))
        n = min(len(x), len(mix) - i)
        mix[i:i + n] += g * x[:n]
    mix *= 10 ** (-3 / 20) / np.abs(mix).max()
    out = HERE / "preview" / "split_sequence_at_break.wav"
    out.parent.mkdir(exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    print(f"ok  {out.relative_to(HERE)}  {length:.2f} s from t {t0:+.2f} s (listening aid, not for upload)")


if __name__ == "__main__":
    ok = all([write_final(sid) for sid in IDS])
    write_preview()
    sys.exit(0 if ok else 1)
