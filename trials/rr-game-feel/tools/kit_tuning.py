#!/usr/bin/env python3
"""Tuning table for the five-moment feel kit (lever pull, hard brake, crate landed, crisis alarm, fare banked).

Reads the mission's feel.json and the rr-game-feel measurements (`feel.py show EVENT --json`, full and reduce
motion), writes TUNING.md (one row per knob, with its safe range from `limits`) and tuning.csv.

  python3 kit_tuning.py --presets DIR_OR_FILE --feel FEEL_PY --out DIR
Standard library only. Exit 0 ok, 2 missing input.
"""
import argparse, csv, json, os, subprocess, sys
from pathlib import Path

KIT = [("lever pull", ["lever_detent_tick", "lever_commit", "lever_commit_crew", "lever_snapback"]),
       ("hard brake", ["hard_brake"]),
       ("crate landed", ["alert_crate_landed"]),
       ("crisis alarm", ["hud_crisis_arrival", "alert_coal_low", "alert_pressure_high", "alert_breakdown",
                         "alert_passengers_upset"]),
       ("fare banked", ["alert_fare_banked"])]
SKIP = {"type", "target", "note", "canon", "before"}


def val(v):
    return v["v"] if isinstance(v, dict) and "v" in v else v


def src(v):
    return f"canon {v['canon']}" if isinstance(v, dict) and "canon" in v else "knob"


def ranges(lim, a11y, ch, key, tier):
    t = ch["type"]
    table = {
        ("camkick", "angles_deg"): f"spring impulse; measured peak <= {lim['kick_deg_max']} deg, roll <= {lim['roll_deg_max']}",
        ("camkick", "freq_hz"): f"{lim['punch_freq_hz'][0]}-{lim['punch_freq_hz'][1]} Hz",
        ("camkick", "damping"): f"{lim['damping'][0]}-{lim['damping'][1]}",
        ("punch", "freq_hz"): f"{lim['punch_freq_hz'][0]}-{lim['punch_freq_hz'][1]} Hz",
        ("punch", "damping"): f"{lim['damping'][0]}-{lim['damping'][1]}",
        ("punch", "amp"): (f"<= {lim['punch_scale_amp_max']}" if ch.get("prop") in ("scale", "rot") else "px; noise shape delivers ~30% of amp"),
        ("shake", "trauma"): f"0-1; camera <= {lim['tier_shake_px'][str(tier)]} px (tier {tier}); shake = trauma^2",
        ("fovkick", "delta_deg"): f"|delta| <= {lim['fov_delta_max']} deg",
        ("hitstop", "ms"): f"<= {lim['hitstop_ms_max']} ms, cooldown {lim['hitstop_cooldown_s']} s",
        ("flash", "peak"): f"screen/vignette <= {a11y['flash']['screen_peak_max']} (red {a11y['flash']['red_peak_max']}); element exempt",
        ("haptic", "keys"): f"[ms, 0..1], end at 0, <= {lim['haptic_ms_max']} ms",
    }
    return table.get((t, key), "")


def show(feel, event, rm=False):
    cmd = [sys.executable, feel, "show", event, "--json"] + (["--rm"] if rm else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"feel.py show {event} failed: {r.stderr.strip()[-300:]}")
    return json.loads(r.stdout)["metrics"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--presets", required=True, help="feel.json or the folder holding it")
    ap.add_argument("--feel", required=True, help="path to rr-game-feel scripts/feel.py")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = Path(a.presets)
    p = p / "feel.json" if p.is_dir() else p
    if not p.is_file() or not Path(a.feel).is_file():
        print("missing presets or feel.py", file=sys.stderr)
        return 2
    os.environ["RR_FEEL_PRESETS"] = str(p)
    d = json.loads(p.read_text())
    ev, lim, a11y = d["events"], d["limits"], d["a11y"]
    rows, md = [], []
    md += ["# Feel kit tuning table", "",
           f"Generated from `{p}` by tools/kit_tuning.py. Edit the numbers in feel.json, then re-run "
           "`feel.py validate --strict` and `feel.py build`; never edit RR_FeelPresets.lua by hand. "
           "`canon` rows must keep their value (rr-bible); `knob` rows are free within the range.", ""]
    for moment, names in KIT:
        md += [f"## {moment}", "", "| event | tier / who | channel | knobs (edit in feel.json) | safe range | canon-locked |",
               "|---|---|---|---|---|---|"]
        for n in names:
            e = ev[n]
            tier = e["priority"]
            for ch in e.get("channels", []):
                label = ch["type"] + (f" {ch['target']}.{ch.get('prop', '')}".rstrip(".") if ch.get("target") else "")
                knobs, rngs, locked = [], [], []
                for k, v in ch.items():
                    if k in SKIP or k == "prop":
                        continue
                    vv = val(v)
                    rng = ranges(lim, a11y, ch, k, tier)
                    rows.append([moment, n, f"t{tier} {e['who']}", label, k, json.dumps(vv), rng, src(v)])
                    knobs.append(f"{k} {json.dumps(vv)}")
                    if rng:
                        rngs.append(f"{k}: {rng}")
                    if src(v) != "knob":
                        locked.append(f"{k} ({v['canon']})")
                md.append(f"| {n} | t{tier} {e['who']} | {label} | {' · '.join(knobs)} | {'; '.join(rngs)} | {', '.join(locked) or '-'} |")
            for inc in e.get("include", []):
                md.append(f"| {n} | t{tier} {e['who']} | include | {inc['event']} at +{inc.get('delay', 0)} s | | - |")
        md.append("")
        md += ["| event | camera px (RM) | kick deg | FOV deg | hit-stop ms | flash | haptic | secs | loudness | RM still reads via |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        for n in names:
            m, r = show(a.feel, n), show(a.feel, n, rm=True)
            md.append(f"| {n} | {m['cam_px']} ({r['cam_px']}) | {m['kick_deg']} | {m['fov_deg']} | {m['hitstop_ms']} | "
                      f"{m['flash_peak']} | {m['haptic_peak']} / {m['haptic_ms']} ms | {m['total_s']}{' + loop' if m['loops'] else ''} | "
                      f"{m['loudness']} | {', '.join(r['communicates'])} |")
        md.append("")
    lv = d["lever"]
    md += ["## lever drag (global `lever` section)", "", "| knob | value | meaning |", "|---|---|---|",
           f"| detent | {lv['detent']} | finger travel where the tick and commit fire |",
           f"| resist | {lv['resist']} | knob = detent x (finger/detent)^resist: higher feels heavier |",
           f"| snap | {lv['snap']['style']} {lv['snap']['dir']} {lv['snap']['dur']} s | knob home after commit |",
           f"| snapback | {lv['snapback']['style']} {lv['snapback']['dir']} {lv['snapback']['dur']} s | knob home when released early |",
           f"| throw_deg | {lv['throw_deg']} | in-world lever handle throw |", ""]
    for k in ("detent", "resist", "throw_deg"):
        rows.append(["lever pull", "lever", "", "drag", k, json.dumps(lv[k]), "", "knob"])
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "TUNING.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    with open(out / "tuning.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["moment", "event", "tier_who", "channel", "knob", "value", "safe_range", "source"])
        w.writerows(rows)
    print(f"wrote {out / 'TUNING.md'} and tuning.csv ({len(rows)} knobs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
