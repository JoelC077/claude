#!/usr/bin/env python3
"""Critic and owner images for the sound plan (called by `sound.py sheet --from DIR --out DIR`).

Writes into OUT: tiles/<id>.png (waveform + log-frequency spectrogram, measurements in the header), ladder.png (in-game
level per sound by tier, the phone-speaker level beside it, ducked ambient levels), timeline.png (each rr-game-feel
event: the sound's envelope against the feel channels: hit-stop, kicks, flashes, haptics), contact.png + closeups.png
(multiuse-critic contact_sheet.py; under 1.15 MP each), facts.md (measurements, mix, hierarchy on phones, the event and
brief table the critic scores S5/S6 on, coverage split into mapped/briefed and files in this pass).
Needs numpy and Pillow. Images are evidence for a critic who cannot hear; the owner's ears are the final check.
"""
import json, math, subprocess, sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audiolib as al  # noqa: E402

BG, INK, DIM, GRID = (21, 23, 28), (236, 236, 236), (150, 152, 160), (54, 58, 66)
TIER = {1: (226, 58, 46), 2: (226, 58, 46), 3: (242, 194, 48), 4: (47, 143, 134), 5: (170, 172, 180), 6: (201, 149, 58),
        7: (140, 120, 200)}
CH_COL = {"hitstop": (226, 58, 46), "camkick": (242, 194, 48), "shake": (242, 194, 48), "punch": (47, 143, 134),
          "flash": (250, 250, 250), "haptic": (140, 120, 200), "fov": (201, 149, 58), "slide": (47, 143, 134),
          "pulse": (47, 143, 134), "tween": (47, 143, 134)}


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def colormap(v):
    """0..1 -> dark blue, teal, yellow, white (perceptually rising)."""
    stops = np.array([[21, 23, 28], [27, 42, 59], [47, 143, 134], [242, 194, 48], [255, 255, 240]], dtype=float)
    x = np.clip(v, 0, 1) * (len(stops) - 1)
    i = np.minimum(x.astype(int), len(stops) - 2)
    f = (x - i)[..., None]
    return (stops[i] * (1 - f) + stops[i + 1] * f).astype(np.uint8)


def spectrogram(x, rate, w, h, fmin=60, fmax=16000):
    n = 1024
    hop = max(64, (len(x) - n) // max(1, w) + 1)
    if len(x) < n:
        x = np.pad(x, (0, n - len(x)))
    win = np.hanning(n)
    frames = [np.abs(np.fft.rfft(x[s:s + n] * win)) for s in range(0, len(x) - n + 1, hop)] or [np.zeros(n // 2 + 1)]
    S = 20 * np.log10(np.array(frames).T + 1e-9)
    S = (S - (S.max() - 70)) / 70
    f = np.fft.rfftfreq(n, 1 / rate)
    ys = np.geomspace(fmin, min(fmax, rate / 2), h)[::-1]
    rows = np.clip(np.searchsorted(f, ys), 0, len(f) - 1)
    img = S[rows]
    cols = np.linspace(0, img.shape[1] - 1, w).astype(int)
    return colormap(img[:, cols])


def tile(sid, s, x, rate, rep, std, placeholder, w=250, h=100):
    im = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(im)
    col = TIER.get(s["tier"], INK)
    head = 13
    wave_h = 30
    d.rectangle([0, 0, 3, h], fill=col)
    lvl = rep.get(std["metric"])
    tag = "Mmax" if std["metric"] == "m_max" else "Int"
    txt = f"{sid} t{s['tier']} {rep['duration']:.2f}s {tag} {lvl} TP {rep.get('true_peak')}"
    d.text((6, 1), txt, fill=INK, font=font(10))
    # waveform (min/max per column)
    mono = np.mean(np.stack(x), axis=0) if len(x) > 1 else np.asarray(x[0])
    cols = w - 6
    edges = np.linspace(0, len(mono), cols + 1).astype(int)
    mid = head + wave_h // 2
    for i in range(cols):
        seg = mono[edges[i]:max(edges[i + 1], edges[i] + 1)]
        lo, hi = float(seg.min()), float(seg.max())
        d.line([(6 + i, mid - hi * wave_h / 2), (6 + i, mid - lo * wave_h / 2)], fill=col)
    spec_h = h - head - wave_h - 2
    sp = spectrogram(mono, rate, cols, spec_h)
    im.paste(Image.fromarray(sp, "RGB"), (6, head + wave_h + 2))
    # 1 kHz and 4 kHz guide ticks on the spectrogram (phone band)
    for fr in (500, 4000):
        yy = head + wave_h + 2 + int((1 - math.log(fr / 60) / math.log(16000 / 60)) * spec_h)
        d.line([(w - 8, yy), (w - 2, yy)], fill=DIM)
    if placeholder:
        d.text((w - 74, h - 12), "PLACEHOLDER", fill=(242, 194, 48), font=font(9))
    pl = rep.get("phone_loss_db")
    if pl is not None:
        d.text((6, h - 12), f"phone -{pl} dB", fill=INK if pl <= std.get("phone_loss_max", 6) else (226, 58, 46), font=font(9))
    return im


def ladder_png(m, rows, path, w=780):
    """rows: [(sid, tier, target, phone_level or None)]"""
    top, rh, left = 48, 13, 132
    h = top + rh * len(rows) + 50
    im = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(im)
    lo, hi = -44.0, -6.0
    X = lambda v: left + (v - lo) / (hi - lo) * (w - left - 12)  # noqa: E731
    d.text((6, 4), "In-game level by tier (LUFS; bar = mix target, dot = on a phone speaker). Loops: integrated.", fill=INK, font=font(11))
    for v in range(-42, -5, 3):
        d.line([(X(v), top - 4), (X(v), h - 44)], fill=GRID)
        d.text((X(v) - 8, h - 42), str(v), fill=DIM, font=font(9))
    L = m.ladder
    placed = []  # (x, row): labels closer than 40 px go on a second row
    for k in sorted(("t1", "t2", "t3", "t4", "t5", "ambient", "music"), key=lambda k_: L[k_]):
        x = X(L[k])
        row = 1 if any(abs(x - px) < 40 and pr == 0 for px, pr in placed) else 0
        placed.append((x, row))
        d.line([(x, top - 8), (x, top - 2)], fill=INK)
        d.text((x - 6, top - 20 - row * 10), k, fill=DIM, font=font(9))
    amb = L["ambient"]
    for name, dbv in (("crisis", -8), ("fail", -14)):
        rule = next((r for r in m.r["ducking"] if r["name"] == name), None)
        if rule and "Ambient" in rule["duck"]:
            v = amb + rule["duck"]["Ambient"]
            d.line([(X(v), top), (X(v), h - 44)], fill=(90, 94, 104))
            d.text((X(v) - 24, h - 16), f"ambient {name}", fill=DIM, font=font(9))
    for i, (sid, tier, target, phone) in enumerate(rows):
        y = top + i * rh
        col = TIER.get(tier, INK)
        d.text((6, y), f"t{tier} {sid}", fill=INK, font=font(10))
        d.rectangle([X(lo), y + 3, X(target), y + rh - 3], fill=col)
        if phone is not None:
            d.ellipse([X(phone) - 3, y + 3, X(phone) + 3, y + rh - 3], outline=INK, fill=BG)
    im.save(path)
    return im.size


def feel_spans(ch):
    t = ch.get("type")
    start = float(ch.get("delay", ch.get("at", 0)) or 0)
    if t == "hitstop":
        return start, ch.get("ms", 0) / 1000
    if t == "flash":
        return start, ch.get("in", 0) + ch.get("hold", 0) + ch.get("out", 0)
    if t == "haptic":
        keys = ch.get("keys", [[0, 0]])
        return start, keys[-1][0] / 1000
    return start, float(ch.get("dur", ch.get("period", 0.2)) or 0.2)


def timeline_png(m, items, feel, path, w=780, span=2.0):
    """items: [(event, sid, envelope (0..1 per 10 ms), lead_ms)]"""
    top, rh, left = 30, 30, 170
    h = top + rh * len(items) + 24
    im = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(im)
    X = lambda t: left + t / span * (w - left - 10)  # noqa: E731
    d.text((6, 4), "Sound envelope (fill) vs rr-game-feel channels from the event's 0 ms:", fill=INK, font=font(11))
    lx = 420
    for name in ("hitstop", "camkick", "punch", "flash", "haptic", "fov"):
        d.line([(lx, 11), (lx + 12, 11)], fill=CH_COL[name], width=3)
        d.text((lx + 15, 5), name, fill=DIM, font=font(9))
        lx += 58
    for t10 in range(0, int(span * 10) + 1, 2):
        d.line([(X(t10 / 10), top - 4), (X(t10 / 10), h - 20)], fill=GRID)
        d.text((X(t10 / 10) - 6, h - 18), f"{t10 / 10:.1f}", fill=DIM, font=font(9))
    for i, (ev, sid, env, lead) in enumerate(items):
        y = top + i * rh
        s = m.sounds[sid]
        col = TIER.get(s["tier"], INK)
        d.text((6, y + 2), f"{ev}", fill=INK, font=font(10))
        d.text((6, y + 14), f"-> {sid} (lead {lead} ms)", fill=DIM, font=font(9))
        base = y + rh - 4
        pts = [(X(j * 0.01), base - v * (rh - 12)) for j, v in enumerate(env) if j * 0.01 <= span]
        if pts:
            d.polygon([(pts[0][0], base)] + pts + [(pts[-1][0], base)], fill=col)
        chans = (feel.get(ev) or {}).get("channels", [])
        k = 0
        for ch in chans:
            if ch.get("type") in ("cue", None):
                continue
            st, du = feel_spans(ch)
            yy = y + 2 + k * 3
            d.line([(X(st), yy), (X(min(span, st + max(du, 0.01))), yy)], fill=CH_COL.get(ch["type"], INK), width=2)
            k += 1
    im.save(path)
    return im.size


def envelope(x, rate):
    mono = np.mean(np.stack(x), axis=0) if len(x) > 1 else np.asarray(x[0])
    k = max(1, int(0.01 * rate))
    n = len(mono) // k
    if n == 0:
        return [0.0]
    r = np.sqrt(np.mean(mono[:n * k].reshape(n, k) ** 2, axis=1))
    return list(r / (r.max() or 1))


def make(m, src, out, feel_path, critic):
    import sound as snd
    out.mkdir(parents=True, exist_ok=True)
    (out / "tiles").mkdir(exist_ok=True)
    files = {}
    for f in snd.audio_files([src]):
        sid = snd.sid_from_name(m, f)
        if sid and sid not in files:
            files[sid] = f
    if not files:
        print(f"no audio files named after sounds in {src} (PLACEHOLDER_<id>.wav or <id>.wav)")
        return 2
    feel = json.loads(Path(feel_path).read_text(encoding="utf-8")).get("events", {}) if feel_path else {}
    reps, tiles = {}, {}
    for sid in m.sounds:
        if sid not in files:
            continue
        s = m.sounds[sid]
        std = m.r["standards"][s["class"]]
        d = al.load(files[sid])
        rep = al.measure(files[sid], loop=std.get("seam", False))
        chk = snd.check_file(m, rep, sid)
        status = "FAIL" if any(c[0] == "FAIL" for c in chk) else "WARN" if any(c[0] == "WARN" for c in chk) else "PASS"
        reps[sid] = (rep, d, status, [c[1] for c in chk if c[0] in ("FAIL", "WARN")])
        ph = Path(files[sid]).name.startswith("PLACEHOLDER_")
        im = tile(sid, s, d["channels"], d["rate"], rep, std, ph)
        p = out / "tiles" / f"{sid}.png"
        im.save(p)
        tiles[sid] = p
    # ladder with phone levels
    lrows = []
    for sid, s in sorted(m.sounds.items(), key=lambda kv: (kv[1]["tier"], kv[0])):
        mx = m.mix(sid)
        pl = reps[sid][0].get("phone_loss_db") if sid in reps else None
        lrows.append((sid, s["tier"], mx["target"], mx["target"] - pl if pl is not None else None))
    ladder_png(m, lrows, out / "ladder.png")
    # timeline for feel events
    items = []
    for ev, e in m.events.items():
        sid = e.get("play")
        if e.get("via") == "feel" and sid in reps:
            items.append((ev, sid, envelope(reps[sid][1]["channels"], reps[sid][1]["rate"]), reps[sid][0].get("lead_ms")))
    items.sort(key=lambda it: (m.sounds[it[1]]["tier"], it[0]))
    timeline_png(m, items[:13], feel, out / "timeline.png")
    # contact sheets (multiuse-critic)
    order = sorted(tiles, key=lambda k: (m.sounds[k]["tier"], k))
    first = [k for k in order if m.sounds[k]["tier"] <= 3]
    rest = [k for k in order if m.sounds[k]["tier"] > 3]
    sheets = [("contact.png", "Ladder=" + str(out / "ladder.png") + "@1", first),
              ("closeups.png", "Timeline=" + str(out / "timeline.png") + "@1", rest)]
    cs = critic / "scripts" / "contact_sheet.py" if critic else None
    for name, band, ids in sheets:
        args = [band] + [f"{k}={tiles[k]}" for k in ids]
        done = False
        for tw, th in ((250, 100), (220, 88), (200, 80)):
            if cs and cs.is_file():
                r = subprocess.run([sys.executable, str(cs), str(out / name), *args, "--tile", f"{tw}x{th}"],
                                   capture_output=True, text=True)
                if r.returncode == 0:
                    done = True
                    break
            else:
                break
        if not done:
            fallback_sheet(out / name, band, [tiles[k] for k in ids])
            print(f"{name}: multiuse-critic contact_sheet.py {'not found' if not cs else 'over budget'}; wrote a plain sheet")
    # facts
    facts = facts_md(m, reps, files, items)
    (out / "facts.md").write_text(facts, encoding="utf-8")
    (out / "preview.json").write_text(json.dumps({"group": "sound", "files": {k: str(v) for k, v in files.items()}}, indent=1))
    fails = sum(1 for v in reps.values() if v[2] == "FAIL")
    print(f"sheet: {len(tiles)} tiles, ladder.png, timeline.png, contact.png, closeups.png, facts.md in {out}"
          f" ({fails} files FAIL analysis). Look at contact.png once before any critic pass.")
    return 1 if fails else 0


def fallback_sheet(path, band, tiles):
    top = Image.open(band.split("=", 1)[1][:-2])
    ims = [Image.open(t) for t in tiles]
    cols = 4
    tw, th = (ims[0].size if ims else (250, 100))
    W = max(top.width, cols * (tw + 4))
    H = top.height + 8 + ((len(ims) + cols - 1) // cols) * (th + 4)
    sheet = Image.new("RGB", (W, H), BG)
    sheet.paste(top, (0, 0))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * (tw + 4), top.height + 8 + (i // cols) * (th + 4)))
    sheet.save(path)


def facts_md(m, reps, files, items):
    L = m.ladder
    lines = ["# Facts (rr-soundsmith sheet; measured by audiolib, BS.1770-4)", "",
             "You cannot hear these sounds. Judge the plan and the measurements; the owner's ears in Studio are the final check.",
             f"Ladder (LUFS in game): t1 {L['t1']}, t2 {L['t2']}, t3 {L['t3']}, t4 {L['t4']}, t5 {L['t5']}, ambient {L['ambient']}, "
             f"music {L['music']}. Phone level = target minus the loss through a phone-speaker model (HP 450 Hz, LP 10 kHz).", "",
             "| sound | tier | file | s | level | TP | lead ms | tail ms | phone loss | bands sub/low/phone/air | seam | check |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for sid, (rep, _, status, msgs) in sorted(reps.items(), key=lambda kv: (m.sounds[kv[0]]["tier"], kv[0])):
        std = m.r["standards"][m.sounds[sid]["class"]]
        b = rep.get("bands") or {}
        bands = "/".join(f"{b.get(k, 0):.2f}" for k in ("sub", "low", "phone", "air"))
        seam = rep.get("seam")
        lines.append(f"| {sid} | {m.sounds[sid]['tier']} | {Path(files[sid]).name} | {rep['duration']:.2f} | "
                     f"{rep.get(std['metric'])} {std['metric']} | {rep.get('true_peak')} | {rep.get('lead_ms')} | "
                     f"{rep.get('tail_ms')} | {rep.get('phone_loss_db')} | {bands} | "
                     f"{'x%.2f' % seam['ratio'] if seam else '-'} | {status}{': ' + '; '.join(msgs)[:120] if msgs else ''} |")
    lines += ["", "## Hierarchy on a phone speaker", ""]
    ph = []
    for sid, s in m.sounds.items():
        if sid in reps and not s.get("looped") and reps[sid][0].get("phone_loss_db") is not None:
            ph.append((sid, s["tier"], m.mix(sid)["target"] - reps[sid][0]["phone_loss_db"]))
    bad = [(b_, a_) for a_ in ph for b_ in ph if a_[1] < b_[1] and b_[2] > a_[2] + L.get("overlap_lu", 1)]
    lines.append("holds: no lower tier is louder than a higher tier by over 1 LU on a phone" if not bad else
                 "inversions: " + "; ".join(f"{b_[0]} (t{b_[1]}, {b_[2]:.1f}) over {a_[0]} (t{a_[1]}, {a_[2]:.1f})" for b_, a_ in bad[:8]))
    lines += ["", "## Ducking", ""]
    for d in m.r["ducking"]:
        lines.append(f"- {d['name']}: {', '.join(d['when'].get('sounds', []) + ['group ' + g for g in d['when'].get('groups', [])])} "
                     f"-> {', '.join(f'{g} {v} dB' for g, v in d['duck'].items())}; attack {d['attack']} s, hold {d['hold']} s, release {d['release']} s")
    lines += ["", "## Event and brief table (phase order; from soundmap.json)", "",
              "| phase | sound | tier/group | space | events | must say | sounds like | avoid |", "|---|---|---|---|---|---|---|---|"]
    cut = lambda s, n: s if len(s) <= n else s[:n - 1].rstrip() + "…"  # noqa: E731
    for sid in m.by_phase():
        s, br = m.sounds[sid], m.sounds[sid]["brief"]
        sp = s["space"] + (f" @{s['emitter']}" if s.get("emitter") else "") + (
            f" +3d @{s['layer3d']['emitter']} {s['layer3d'].get('gain_db', -4)} dB" if s.get("layer3d") else "")
        evs = ", ".join(f"{e} ({m.events[e]['via']})" for e in m.events_for(sid)) or "NONE"
        lines.append(f"| {m.sound_phase(sid)} | {sid} | t{s['tier']} {s['group']} | {sp} | {evs} | {br.get('must_say', '')} | "
                     f"{cut(br.get('sounds_like', ''), 90)} | {cut(br.get('avoid', ''), 80)} |")
    silent = [e for e, ev in m.events.items() if not ([ev.get("play"), ev.get("toggle")] + ev.get("start", []) + ev.get("stop", []))]
    played = [k for k in m.sounds if m.events_for(k)]
    briefed = [k for k in m.sounds if all(m.sounds[k]["brief"].get(f) for f in ("moment", "must_say", "sounds_like", "avoid", "len"))]
    d3 = [k for k in m.sounds if m.sounds[k]["space"] == "3d"]
    d3ok = [k for k in d3 if m.sounds[k].get("emitter") in m.r["emitters"]]
    nofile = [k for k in m.by_phase() if k not in reps]
    lines += ["", "## Coverage", "",
              f"Mapped: {len(m.events) - len(silent)}/{len(m.events)} events play a sound"
              f"{' (silent: ' + ', '.join(silent) + ')' if silent else ''}; {len(played)}/{len(m.sounds)} sounds are played "
              f"by an event; {len(briefed)}/{len(m.sounds)} briefed; {len(d3ok)}/{len(d3)} 3D sounds have an emitter role.",
              f"Files in this pass: {len(reps)}/{len(m.sounds)} (the scope of this sheet). No file here (mapped and briefed "
              f"above; not a coverage gap): {', '.join(nofile) or 'none'}. {len(items)} rr-game-feel events drawn in the timeline.",
              "Asset states: " + ", ".join(f"{k} {m.asset_state(k)}" for k in m.sounds if m.asset_state(k) != "unassigned")
              if any(m.asset_state(k) != "unassigned" for k in m.sounds) else "Asset states: all unassigned (no uploads registered yet).",
              "Voices: " + json.dumps(m.r["voices"]["per_group"]) + f", max {m.r['voices']['max']}; new fail and crisis "
              "sounds always get a voice; a playing crisis alarm is cut only by the fail or another alarm."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import argparse
    argparse.ArgumentParser(description=__doc__ + "\nRun it through: python3 sound.py sheet --from DIR --out DIR",
                            formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    print("run it through: python3 sound.py sheet --from DIR --out DIR")
