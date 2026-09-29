"""Write the upload files for the carriage-split sounds: final/rr_split_<id>.wav.

The audio is bit-identical to ph/PLACEHOLDER_<id>.wav (written by `sound.py synth` from recipes.py, seed 7);
only the WAV INFO tag changes. The synth tags every file PLACEHOLDER, and the licence gate refuses a
PLACEHOLDER-tagged file posing as final. These sounds are the owner-requested deliverable ("Sounds: yes. Make
some if you can"), made from code only, so the upload copies say "self-made, synthesised from code" instead.
The owner still decides by ear (Studio listening test) before uploading and registering them.

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
RECIPE["split_glass"] = "rr-soundsmith built-in glass_smash recipe"


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
    src, dst = HERE / "ph" / f"PLACEHOLDER_{sid}.wav", HERE / "final" / f"rr_split_{sid}.wav"
    ch, sw, sr, pcm = read_pcm(src)
    fmt = struct.pack("<HHIIHH", 1, ch, sr, sr * ch * sw, ch * sw, sw * 8)
    info = info_chunk([
        ("INAM", f"rr_split_{sid}"),
        ("IPRD", "Risky Rails"),
        ("ICMT", f"Carriage-split SFX synthesised from code ({RECIPE[sid]}, seed 7); no samples or "
                 f"third-party material; self-made"),
        ("ISFT", "numpy synthesis (rr-soundsmith sound.py synth, mission 260929-train-splits)"),
        ("IGNR", "sfx"),
    ])
    data = b"data" + struct.pack("<I", len(pcm)) + pcm + (b"\0" if len(pcm) % 2 else b"")
    body = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + info + data
    dst.parent.mkdir(exist_ok=True)
    dst.write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)
    same = read_pcm(dst) == (ch, sw, sr, pcm)
    print(f"{'ok ' if same else 'BAD'} {dst.name:30s} {len(pcm) / (sr * ch * sw):.3f} s  "
          f"sha1 {hashlib.sha1(dst.read_bytes()).hexdigest()[:12]}  pcm identical to {src.name}: {same}")
    return same


if __name__ == "__main__":
    sys.exit(0 if all([write_final(sid) for sid in IDS]) else 1)
