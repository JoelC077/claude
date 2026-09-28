#!/usr/bin/env python3
"""Exercise every rr-soundsmith command on temp copies; the shipped presets are never written.

  selftest.py [-v] [--keep]

Covers: --help of every script; audiolib against the BS.1770 filter tables, EBU Tech 3341 cases 1-4, a 3342 LRA case,
true peak, WAV round trips, the no-numpy path, ffmpeg decoding and header-only probes; validate (shipped presets
strict, plus five planted errors); synth (all recipes, determinism, PLACEHOLDER tags); analyze (planted clipping,
96 kHz, late start, loop click; --fix-out never touches the source; mono cancel); register and the licence gate;
brief; sheet (contact sheets under 1.15 MP); crit + critic_kit Profile S; build (luaparse, bible check, map loads in
Lua); luatest (Lua runtime; skipped and said so without lupa). Exit 0 = all passed. Removes its temp folder.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
import numpy as np  # noqa: E402
import audiolib as al  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--keep", action="store_true", help="keep the temp folder and print its path")
    a = ap.parse_args(argv)
    tmp = Path(tempfile.mkdtemp(prefix="rr-sound-selftest-"))
    res = []

    def ok(cond, msg):
        res.append((bool(cond), msg))
        if a.verbose or not cond:
            print(("ok   " if cond else "FAIL ") + msg)

    def run(*args, env=None, presets=None):
        e = dict(os.environ)
        e.pop("RR_SOUND_PRESETS", None)
        if presets:
            e["RR_SOUND_PRESETS"] = str(presets)
        e.update(env or {})
        r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, env=e, cwd=tmp)
        return r.returncode, r.stdout + r.stderr

    S = HERE / "sound.py"
    try:
        # --help everywhere
        for f in ("sound.py", "audiolib.py", "synth.py", "sheet.py", "luatest.py", "selftest.py"):
            code, out = run(HERE / f, "--help")
            ok(code == 0 and "usage" in out.lower(), f"{f} --help")
        # audiolib: filter, EBU cases, true peak
        spec = [([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]),
                ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])]
        got = al.kweight_coeffs(48000)
        ok(all(abs(x - y) < 1e-12 for s1, s2 in zip(got, spec) for v1, v2 in zip(s1, s2) for x, y in zip(v1, v2)),
           "K-weighting equals the BS.1770 tables at 48 kHz")
        sr = 48000

        def sine(dbfs, dur, f=1000, rate=sr):
            t = np.arange(int(rate * dur)) / rate
            return 10 ** (dbfs / 20) * np.sin(2 * np.pi * f * t)
        c1 = al.loudness([sine(-23, 20)] * 2, sr)["integrated"]
        c2 = al.loudness([sine(-33, 20)] * 2, sr)["integrated"]
        x3 = np.concatenate([sine(-36, 10), sine(-23, 60), sine(-36, 10)])
        x4 = np.concatenate([sine(-72, 10), sine(-36, 10), sine(-23, 60), sine(-36, 10), sine(-72, 10)])
        c3, c4 = al.loudness([x3, x3], sr)["integrated"], al.loudness([x4, x4], sr)["integrated"]
        ok(abs(c1 + 23) <= 0.1 and abs(c2 + 33) <= 0.1 and abs(c3 + 23) <= 0.1 and abs(c4 + 23) <= 0.1,
           f"EBU 3341 cases 1-4 within 0.1 LU ({c1}, {c2}, {c3}, {c4})")
        ok(abs(al.loudness([sine(-23, 10)], sr)["integrated"] + 23) <= 0.1, "mono measured as dual mono")
        ok(abs(al.loudness([sine(-23, 10, rate=44100)] * 2, 44100)["integrated"] + 23) <= 0.1, "44.1 kHz filters")
        lra = al.loudness([np.concatenate([sine(-20, 20), sine(-30, 20)])] * 2, sr)["lra"]
        ok(abs(lra - 10) <= 1, f"EBU 3342 case 1 LRA 10 LU ({lra})")
        n = np.arange(4800)
        tp = al.true_peak([np.sin(2 * np.pi * (sr / 4) * n / sr + np.pi / 4)])
        ok(abs(tp) <= 0.3 and al.db(al.sample_peak([np.sin(2 * np.pi * 0.25 * n + np.pi / 4)])) < -2.9,
           f"true peak finds the inter-sample peak ({tp} dBTP vs -3 dB sample)")
        x = 0.4 * np.sin(2 * np.pi * 440 * np.arange(sr) / sr)
        errs = []
        for bits in (16, 24, 32):
            p = tmp / f"rt{bits}.wav"
            al.write_wav(p, sr, [x, -x], bits=bits, info={"ICMT": "PLACEHOLDER t"})
            d = al.read_wav(p)
            errs.append(max(float(np.max(np.abs(d["channels"][0] - x))), float(np.max(np.abs(d["channels"][1] + x)))))
            ok(d["info"].get("ICMT") == "PLACEHOLDER t" and d["bits"] == bits, f"WAV {bits}-bit round trip keeps INFO")
        ok(errs[0] < 4e-5 and errs[1] < 2e-7 and errs[2] < 1e-7, f"WAV round-trip error {errs}")
        code, out = run(HERE / "audiolib.py", tmp / "rt16.wav", "--json", env={"RR_SOUND_NO_NUMPY": "1"})
        slow = json.loads(out)[0]
        fast = al.measure(tmp / "rt16.wav")
        ok(code == 0 and not slow["numpy"] and abs(slow["m_max"] - fast["m_max"]) < 0.05 and slow["true_peak"] is None,
           "standard-library path matches numpy loudness (true peak skipped, said)")
        exe = al.find_ffmpeg()
        if exe:
            for ext, args in (("ogg", ["-c:a", "libvorbis"]), ("mp3", ["-c:a", "libmp3lame"]), ("flac", [])):
                subprocess.run([exe, "-v", "error", "-y", "-i", str(tmp / "rt16.wav"), *args, str(tmp / f"rt.{ext}")], check=True)
                m1 = al.measure(tmp / f"rt.{ext}")
                ok(m1["decoded"] and abs(m1["m_max"] - fast["m_max"]) < 0.8, f"ffmpeg decodes .{ext} (m_max {m1['m_max']} vs {fast['m_max']})")
                code, out = run(HERE / "audiolib.py", tmp / f"rt.{ext}", "--json", env={"RR_SOUND_NO_FFMPEG": "1"})
                pr = json.loads(out)[0]
                ok(not pr["decoded"] and abs(pr["duration"] - 1.0) < 0.06 and pr["nch"] == 2, f"header probe reads .{ext} length without a decoder")
        else:
            print("SKIP ffmpeg decode tests: no ffmpeg (pip install --target ~/.cache/rr-tools/py imageio-ffmpeg)")
        # validate: shipped presets, then planted errors
        code, out = run(S, "validate", "--strict")
        ok(code == 0 and "validate PASS" in out, "shipped presets: validate --strict PASS")
        base = json.loads((SKILL / "presets" / "soundmap.json").read_text(encoding="utf-8"))
        plants = [
            ("ladder inverted", lambda d: d["ladder"].update(t4=-10), "quieter than"),
            ("self-ducking", lambda d: d["ducking"][1]["duck"].update(SFX=-6), "self-ducking"),
            ("feel parity", lambda d: d["events"]["lever_commit"].update(play="whistle"), "feel parity"),
            ("trim beyond max", lambda d: d["sounds"]["ui_click"].update(trim_db=5), "trim_db"),
            ("canon disagreement", lambda d: d["speed_link"][0]["ref"].update(v=36), "disagrees with canon"),
        ]
        for name, fn, needle in plants:
            pdir = tmp / f"plant-{name.replace(' ', '-')}"
            pdir.mkdir()
            d = json.loads(json.dumps(base))
            fn(d)
            (pdir / "soundmap.json").write_text(json.dumps(d), encoding="utf-8")
            code, out = run(S, "validate", presets=pdir)
            ok(code == 1 and needle in out, f"planted {name}: validate FAIL ({needle})")
        # synth
        ph = tmp / "ph"
        code, out = run(S, "synth", "all", "--out", ph)
        files = sorted(ph.glob("PLACEHOLDER_*.wav"))
        ok(code == 0 and len(files) == len(base["sounds"]) and (ph / "PLACEHOLDERS.md").is_file(),
           f"synth all: {len(files)} placeholders, 0 fail, manifest")
        ok(all("PLACEHOLDER" in al.read_wav(f)["info"].get("ICMT", "") for f in files), "every placeholder carries the INFO tag")
        h1 = hashlib.sha1((ph / "PLACEHOLDER_lever_clunk.wav").read_bytes()).hexdigest()
        run(S, "synth", "lever_clunk", "--out", tmp / "ph2")
        ok(h1 == hashlib.sha1((tmp / "ph2" / "PLACEHOLDER_lever_clunk.wav").read_bytes()).hexdigest(), "synth is deterministic")
        # analyze: planted bad files
        bad = tmp / "bad"
        bad.mkdir()
        t = np.arange(int(sr * 0.5)) / sr
        y = np.sin(2 * np.pi * 600 * t) * np.exp(-t / 0.1)
        al.write_wav(bad / "lever_clunk_clipped.wav", sr, [np.clip(3 * y, -1, 1)])
        t96 = np.arange(48000) / 96000
        al.write_wav(bad / "crate_thump_96k.wav", 96000, [0.3 * np.sin(2 * np.pi * 500 * t96)])
        al.write_wav(bad / "stamp_slam_late.wav", sr, [np.concatenate([np.zeros(int(0.08 * sr)), 0.5 * y])])
        al.write_wav(bad / "wind_bed_click.wav", sr, [0.3 * np.sin(2 * np.pi * 97.3 * np.arange(sr * 4) / sr)])
        al.write_wav(bad / "shovel_thud_stereo.wav", sr, [0.4 * y, -0.4 * y])
        code, out = run(S, "analyze", bad, "--json")
        rows = {Path(r_["file"]).name: r_ for r_ in json.loads(out)}
        expect = {"lever_clunk_clipped.wav": "clipped", "crate_thump_96k.wav": "48 kHz", "stamp_slam_late.wav": "feel late",
                  "wind_bed_click.wav": "seam clicks"}
        for f, needle in expect.items():
            r_ = rows.get(f, {})
            ok(r_.get("status") == "FAIL" and any(needle in c[1] for c in r_.get("checks", [])), f"analyze {f}: FAIL ({needle})")
        ok(code == 1, "analyze exits 1 when a file fails")
        code, out = run(S, "analyze", ph / "PLACEHOLDER_whistle.wav")
        ok(code == 0 and "PASS" in out, "analyze passes a clean placeholder")
        src_hash = hashlib.sha1((bad / "stamp_slam_late.wav").read_bytes()).hexdigest()
        code, out = run(S, "analyze", bad / "stamp_slam_late.wav", "--fix-out", tmp / "fixed")
        ok(hashlib.sha1((bad / "stamp_slam_late.wav").read_bytes()).hexdigest() == src_hash and
           (tmp / "fixed" / "stamp_slam_late_std.wav").is_file(), "--fix-out writes a new file and never touches the source")
        code, out = run(S, "analyze", tmp / "fixed" / "stamp_slam_late_std.wav")
        ok(code == 0 and "PASS" in out, "the fixed copy passes (lead trimmed, levelled)")
        code, out = run(S, "analyze", bad / "shovel_thud_stereo.wav", "--fix-out", tmp / "fixed2", "--mono")
        m2 = al.measure(tmp / "fixed2" / "shovel_thud_stereo_std.wav")
        ok(m2["nch"] == 1 and m2["m_max"] > -20 and "cancel" in out, "mono fix survives anti-phase channels")
        # register and the licence gate
        pre = tmp / "presets"
        shutil.copytree(SKILL / "presets", pre)
        code, out = run(S, "register", "lever_clunk", "--file", ph / "PLACEHOLDER_lever_clunk.wav", "--id", "111",
                        "--source", "placeholder", presets=pre)
        ok(code == 0 and "registered" in out, "register a placeholder")
        before = (pre / "assets.json").read_text()
        shutil.copy2(ph / "PLACEHOLDER_alarm_coal.wav", tmp / "alarm_coal_v1.wav")
        al.write_wav(tmp / "clean.wav", sr, [0.2 * x])
        refusals = [
            (["alarm_coal", "--file", tmp / "alarm_coal_v1.wav", "--id", "2", "--source", "owner_upload", "--origin", "self-made",
              "--proof", "x"], "PLACEHOLDER tag"),
            (["whistle", "--file", tmp / "clean.wav", "--id", "3", "--source", "owner_upload", "--origin", "cc0",
              "--licence", "CC BY-NC 4.0", "--proof", "url"], "refused term"),
            (["whistle", "--id", "4", "--source", "roblox_licensed", "--creator", "someone", "--community", "--proof", "url"], "community"),
            (["whistle", "--file", tmp / "clean.wav", "--id", "5", "--source", "owner_upload", "--origin", "self-made"], "needs --proof"),
        ]
        for args, needle in refusals:
            code, out = run(S, "register", *args, presets=pre)
            ok(code == 1 and needle in out, f"licence gate refuses ({needle})")
        ok((pre / "assets.json").read_text() == before, "refusals write nothing")
        code, out = run(S, "register", "whistle", "--id", "6", "--source", "roblox_licensed", "--creator", "Roblox",
                        "--proof", "https://create.roblox.com/store/asset/6", presets=pre)
        ok(code == 0, "register Roblox-licensed audio by id")
        code, out = run(S, "validate", "--release", presets=pre)
        ok(code == 1 and "release: lever_clunk is placeholder" in out, "validate --release fails while placeholders remain")
        code, out = run(S, "show", "lever_clunk", "--json", presets=pre)
        ok(code == 0 and json.loads(out)["mix"]["level_from"] == "measured", "registered level feeds the mix")
        for args in (["list"], ["show", "trip_start"], ["list", "--group", "Alarms"]):
            code, out = run(S, *args)
            ok(code == 0, f"{' '.join(args)} runs")
        # brief
        code, out = run(S, "brief", "all", "--out", tmp / "briefs.md")
        txt = (tmp / "briefs.md").read_text()
        ok(code == 0 and txt.count("\n## ") == len(base["sounds"]) and "Done when" in txt, "brief all: one brief per sound")
        # sheet and crit
        code, out = run(S, "sheet", "--from", ph, "--out", tmp / "sheet")
        from PIL import Image
        mp = [Image.open(tmp / "sheet" / n).size for n in ("contact.png", "closeups.png")]
        ok(code == 0 and all(w * h <= 1.15e6 and w <= 1568 for w, h in mp) and (tmp / "sheet" / "facts.md").is_file(),
           f"sheet: contact sheets within critic limits {mp}")
        code, out = run(S, "crit", tmp / "CRIT", "--pass", "1", "--from", tmp / "sheet")
        ok(code == 0 and "## Profile S" in (tmp / "CRIT" / "rubric.md").read_text(), "crit writes the merged rubric")
        critic = next((p for p in [SKILL.parent / "multiuse-critic"] if (p / "scripts" / "critic_kit.py").is_file()), None)
        if critic:
            code, out = run(critic / "scripts" / "critic_kit.py", "build", tmp / "CRIT", "--pass", "1", "--kind", "full",
                            "--profile", "S", "--role", "senior game audio designer")
            ok(code == 0 and "S6" in out, "critic_kit builds a Profile S pass")
        # build
        code, out = run(S, "build", "--out", tmp / "export", presets=pre)
        ok(code == 0 and "build PASS" in out and "syntax" in out, "build PASS (syntax + bible check)")
        need = ["RR_SoundMap.lua", "RR_Sound.lua", "RR_SoundDemo.client.lua", "studio_sound_setup.lua", "SOUND_SPEC.md",
                "AUDIO_BRIEFS.md", "LICENCES.md", "README.md"]
        ok(all((tmp / "export" / f).is_file() for f in need), "build writes the package")
        ok("rbxassetid://111" in (tmp / "export" / "RR_SoundMap.lua").read_text() and
           "placeholders = 1" in (tmp / "export" / "RR_SoundMap.lua").read_text(), "registered ids and placeholder count reach the map")
        code, out = run(HERE / "luatest.py", "--map", tmp / "export" / "RR_SoundMap.lua")
        ok(code == 0, "generated RR_SoundMap loads in Lua" + (" (skipped: no lupa)" if "SKIP" in out else ""))
        # Lua runtime
        code, out = run(HERE / "luatest.py")
        if "SKIP" in out:
            print("SKIP luatest runtime: lupa not installed (pip install --target ~/.cache/rr-tools/py lupa)")
        else:
            ok(code == 0 and "passed" in out, "luatest: " + out.strip().splitlines()[-1])
    finally:
        if a.keep:
            print(f"kept {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)
        for pc in HERE.glob("__pycache__"):
            shutil.rmtree(pc, ignore_errors=True)
    passed = sum(1 for c, _ in res if c)
    print(f"selftest: {passed}/{len(res)} passed" + ("" if passed == len(res) else " (FAIL)"))
    return 0 if passed == len(res) else 1


if __name__ == "__main__":
    sys.exit(main())
