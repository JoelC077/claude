#!/usr/bin/env python3
"""rr-game-feel self-test: every command on temp copies, planted-bad presets, the critic hand-off and the Lua runtime.

  selftest.py [--keep] [--no-lua]

--keep leaves the temp folder (printed) for inspection; --no-lua skips luatest.py. Needs rr-bible and
multiuse-critic (found like feel.py finds them), Pillow for plots/previews, lupa for the Lua runtime tests.
Prints one line per check and "selftest: all N passed" (exit 0) or the failures (exit 1).
"""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PY = sys.executable
RESULTS = []


def run(args, env=None, cwd=None):
    e = dict(os.environ)
    e.update(env or {})
    r = subprocess.run([PY, *args], capture_output=True, text=True, env=e, cwd=cwd)
    return r.returncode, r.stdout + r.stderr


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print(f"{'ok  ' if cond else 'FAIL'} {name}" + (f"  [{detail.strip().splitlines()[-1][:160]}]" if (detail and not cond) else ""))


def planted(tmp, name, mutate):
    data = json.loads((SKILL / "presets" / "feel.json").read_text())
    mutate(data)
    p = tmp / f"bad-{name}.json"
    p.write_text(json.dumps(data, indent=1))
    return p


def main():
    keep = "--keep" in sys.argv
    tmp = Path(tempfile.mkdtemp(prefix="rr-feel-selftest-"))
    feel = str(HERE / "feel.py")
    try:
        # help on every script
        for s in ("feel.py", "feelmath.py", "feelplot.py", "luatest.py", "selftest.py"):
            code, out = run([str(HERE / s), "--help"]) if s != "selftest.py" else (0, __doc__)
            check(f"{s} --help", code == 0 and len(out) > 100, out)
        code, out = run([str(HERE / "feelmath.py"), "--demo"])
        check("feelmath --demo", code == 0 and "Back.Out" in out, out)

        # read commands
        code, out = run([feel, "list"])
        check("list", code == 0 and "boiler_burst" in out and "lever_commit" in out, out)
        code, out = run([feel, "list", "--group", "lever"])
        check("list --group lever", code == 0 and "6 events" in out, out)
        code, out = run([feel, "show", "lever_commit"])
        check("show (spec text)", code == 0 and "Intent" in out and "Reduce motion" in out, out)
        code, out = run([feel, "show", "hud_ticket_enter", "--json", "--rm"])
        check("show --json --rm", code == 0 and json.loads(out)["metrics"]["rm"] is True, out)
        code, out = run([feel, "show", "nope"])
        check("show unknown event exits 2", code == 2, out)

        # the gate
        code, out = run([feel, "validate", "--strict"])
        check("validate --strict PASS on shipped presets", code == 0 and "validate PASS" in out, out)
        code, out = run([feel, "validate", "--json"])
        check("validate --json", code == 0 and json.loads(out)["ok"] is True, out)

        bad = {
            "canon contradicted": (lambda d: d["events"]["hud_merge_bump"]["channels"][0]["from"].__setitem__("v", 1.1),
                                   "not found in canon ui.hud.motion"),
            "red flash on a reward": (lambda d: d["events"]["alert_fare_banked"]["channels"].append(
                {"type": "flash", "scope": "screen", "color": "@style.brand.danger_red", "peak": 0.2, "in": 0.03, "out": 0.2}),
                "red flash on a tier 4 event"),
            "hit-stop on a crew event": (lambda d: d["events"]["lever_commit_crew"]["channels"].append({"type": "hitstop", "ms": 50}),
                                         "hit-stop on a crew event"),
            "reduce motion loses the event": (lambda d: d["events"]["lever_snapback"].__setitem__("channels", [
                {"type": "punch", "target": "lever_panel", "prop": "x_px", "shape": "noise", "amp": 1, "freq_hz": 14, "dur": 0.25}]),
                "with Reduce Motion on nothing is left"),
            "rumble gain over its cap": (lambda d: d["sustain"]["speed"].__setitem__("gain", 0.6), "flatten before its maximum"),
            "constant rumble too big": (lambda d: d["shake"].__setitem__("sustain_cap", 0.5), "px of constant camera motion"),
            "unknown easing": (lambda d: d["events"]["ui_panel_open"]["channels"][0].__setitem__("style", "Springy"),
                               "is not an Enum.EasingStyle"),
            "flash over the cap": (lambda d: d["events"]["windows_smash"]["channels"][1].__setitem__("peak", 0.6),
                                   "photosensitivity cap"),
            "unknown vfx cue": (lambda d: d["events"]["shovel_coal"]["channels"][4].__setitem__("vfx", "coal_confetti"),
                                "is not an rr-vfx-lighting preset"),
            "unknown OQ": (lambda d: d["events"]["lever_commit"]["oq"].append("OQ-999"), "OQ-999 not found"),
            "raw hex colour": (lambda d: d["events"]["windows_smash"]["channels"][1].__setitem__("color", "#FF00FF"),
                               "is not a token"),
            "haptic left running": (lambda d: d["events"]["depart"]["channels"][1]["keys"].__setitem__(-1, [1200, 0.3]),
                                    "last key must be 0"),
        }
        for label, (mut, expect) in bad.items():
            p = planted(tmp, label.replace(" ", "-"), mut)
            code, out = run([feel, "--presets", str(p), "validate"])
            check(f"validate catches: {label}", code == 1 and expect in out, out)
        p = planted(tmp, "hierarchy", lambda d: d["events"]["ui_button_release"]["channels"].append({"type": "shake", "trauma": 0.9}))
        code, out = run([feel, "--presets", str(p), "validate"])
        code2, out2 = run([feel, "--presets", str(p), "validate", "--strict"])
        check("hierarchy breach: warning, strict fails", "outshouts" in out and code2 == 1, out + out2)
        p = planted(tmp, "build-refused", lambda d: d["events"]["ui_panel_open"]["channels"][0].__setitem__("style", "Springy"))
        code, out = run([feel, "--presets", str(p), "build", "--out", str(tmp / "nobuild")])
        check("build refuses invalid presets", code == 1 and "build refused" in out, out)

        # env override (a mission copy)
        mission = tmp / "M" / "src" / "feel"
        shutil.copytree(SKILL / "presets", mission)
        code, out = run([feel, "list"], env={"RR_FEEL_PRESETS": str(mission)})
        check("RR_FEEL_PRESETS folder override", code == 0 and str(mission) in out, out)

        # spec
        code, out = run([feel, "spec", "all", "--out", str(tmp / "FEEL_SPEC.md")])
        spec = (tmp / "FEEL_SPEC.md").read_text() if (tmp / "FEEL_SPEC.md").is_file() else ""
        check("spec all", code == 0 and spec.count("\n## ") >= 33 and "Lever drag" in spec, out)
        code, out = run([feel, "spec", "crisis"])
        check("spec GROUP to stdout", code == 0 and "alert_breakdown" in out and "BREAKDOWN!" in out, out)

        # plots
        code, out = run([feel, "plot", "all", "--out", str(tmp / "plots")])
        pngs = list((tmp / "plots").glob("*.png"))
        check("plot all", code == 0 and len(pngs) >= 36 and (tmp / "plots" / "easing.png").is_file(), out)
        code, out = run([feel, "plot", "lever", "--out", str(tmp / "plots2")])
        check("plot lever", code == 0 and (tmp / "plots2" / "lever.png").is_file(), out)
        sys.path.insert(0, str(HERE))
        import feelmath as fm
        dump = tmp / "dump.csv"
        lines = []
        for st in fm.STYLES:
            for dr in fm.DIRECTIONS:
                for i in range(21):
                    v = fm.ease(st, dr, i / 20)
                    if st == "Elastic" and dr == "Out":
                        v += 0.05 * (i % 2)   # a planted engine difference
                    lines.append(f"{st},{dr},{i / 20:.4f},{v:.6f}")
        dump.write_text("\n".join(lines))
        code, out = run([feel, "plot", "curves", "--out", str(tmp / "cmp"), "--compare", str(dump)])
        check("plot --compare flags a differing style only", code == 0 and "DIFF Elastic Out" in out and out.count("DIFF") == 1, out)

        # previews + critic hand-off
        code, out = run([feel, "preview", "all", "--out", str(tmp / "prev")])
        groups = sorted(p.name for p in (tmp / "prev").iterdir() if p.is_dir())
        check("preview all: 6 groups", code == 0 and groups == ["actions", "crisis", "fail", "info", "lever", "ui"], out)
        from PIL import Image
        sizes_ok = True
        for g in groups:
            for n in ("contact.png", "closeups.png"):
                f = tmp / "prev" / g / n
                if not f.is_file():
                    sizes_ok = False
                    continue
                w, h = Image.open(f).size
                sizes_ok &= w * h <= 1.15e6 and max(w, h) <= 1568
            sizes_ok &= (tmp / "prev" / g / "facts.md").is_file()
        check("previews: contact + closeups within 1.15 MP, facts.md per group", sizes_ok)
        code, out = run([feel, "preview", "lever_commit", "--out", str(tmp / "prev1"), "--gif", "--rm"])
        check("preview EVENT --gif --rm", code == 0 and (tmp / "prev1" / "lever" / "lever_commit.gif").is_file(), out)
        crit = tmp / "M" / "critique-feel-fail"
        code, out = run([feel, "crit", str(crit), "--pass", "1", "--from", str(tmp / "prev" / "fail")])
        rub = (crit / "rubric.md").read_text() if (crit / "rubric.md").is_file() else ""
        check("crit: rubric with Profile G, brief, pass files", code == 0 and "## Profile G" in rub and "A6, B5, G5" in rub
              and (crit / "brief.md").is_file() and (crit / "pass-1" / "contact.png").is_file(), out)
        critic = next((l.split()[2] for l in out.splitlines() if l.startswith("next: python3")), None)
        if critic:
            code, out = run([critic, "build", str(crit), "--pass", "1", "--kind", "full", "--profile", "G",
                             "--role", "senior game-feel designer", "--images", "closeups.png"])
            cm = (crit / "pass-1" / "critic.md").read_text() if (crit / "pass-1" / "critic.md").is_file() else ""
            check("critic_kit build --profile G writes critic.md", code == 0 and "G1 Signal and hierarchy" in cm
                  and "Risky Rails house style" in cm, out)
        else:
            check("critic_kit build --profile G writes critic.md", False, out)

        # build
        code, out = run([feel, "build", "--out", str(tmp / "export")])
        files = sorted(p.name for p in (tmp / "export").iterdir()) if (tmp / "export").is_dir() else []
        check("build PASS (luaparse or balance + bible check)", code == 0 and "build PASS" in out and len(files) == 6, out)
        check("build ran a real Lua parser", "luaparse: ok" in out, "install luaparse: npm i --prefix ~/.cache/rr-tools luaparse")
        code, out = run([feel, "build", "--out", str(tmp / "export2"), "--no-check"])
        check("build --no-check", code == 0 and "wrote" in out, out)

        # Lua runtime
        if "--no-lua" in sys.argv:
            print("skip luatest (--no-lua)")
        else:
            code, out = run([str(HERE / "luatest.py")])
            if code == 3:
                print("SKIP luatest: " + out.strip())
            else:
                check("luatest: RR_FeelMath parity + RR_Feel runtime in Lua 5.1", code == 0 and "luatest PASS" in out, out)
    finally:
        if keep:
            print(f"kept {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)
        for d in (HERE / "__pycache__",):
            shutil.rmtree(d, ignore_errors=True)
    failed = [r for r in RESULTS if not r[1]]
    if failed:
        print(f"selftest: {len(failed)} of {len(RESULTS)} FAILED")
        return 1
    print(f"selftest: all {len(RESULTS)} passed")
    return 0


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        sys.exit(0)
    sys.exit(main())
