#!/usr/bin/env python3
"""rr-game-feel self-test: every command on temp copies, planted-bad presets, the critic hand-off and the Lua runtime.

  selftest.py [--keep] [--no-lua]

--keep leaves the temp folder (printed) for inspection; --no-lua skips luatest.py. Needs rr-bible and
multiuse-critic (found like feel.py finds them), Pillow for plots/previews, lupa for the Lua runtime tests.
Prints one line per check and "selftest: all N passed" (exit 0) or the failures (exit 1).
"""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PY = sys.executable
RESULTS = []


def run(args, env=None, cwd=None):
    e = dict(os.environ)
    e["PYTHONDONTWRITEBYTECODE"] = "1"
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
        for s in ("feel.py", "feelmath.py", "feelplot.py", "luatest.py", "luau_check.py", "selftest.py"):
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
                                   "disagrees with canon ui.hud.motion"),
            "canon number from the wrong phrase": (lambda d: d["events"]["hud_crisis_arrival"]["channels"][0]["amp"].__setitem__("v", 0.5),
                                                   "disagrees with canon ui.hud.crisis_extra"),
            "swapped pulse range": (lambda d: d["events"]["hud_crisis_arrival"]["channels"][1].update(
                min={"v": 0.95, "canon": "ui.hud.crisis_extra", "match": "0.95"}, max={"v": 0.3, "canon": "ui.hud.crisis_extra", "match": "pulsing 0.3"}),
                "swapped range"),
            "unknown sound cue": (lambda d: d["events"]["shovel_coal"]["channels"][4].__setitem__("sfx", "shovel_bonk"),
                                  "is not an rr-soundsmith sound"),
            "camkick frequency out of range": (lambda d: d["events"]["depart"]["channels"][0].__setitem__("freq_hz", 20),
                                               "camkick freq_hz 20 outside"),
            "red flash on a reward": (lambda d: d["events"]["alert_fare_banked"]["channels"].append(
                {"type": "flash", "scope": "screen", "color": "@style.brand.danger_red", "peak": 0.2, "in": 0.03, "out": 0.2}),
                "red flash on a tier 4 event"),
            "hit-stop on a crew event": (lambda d: d["events"]["lever_commit_crew"]["channels"].append({"type": "hitstop", "ms": 50}),
                                         "hit-stop on a crew event"),
            "reduce motion keeps only a haptic": (lambda d: d["events"]["depart"]["channels"].pop(2),
                                                  "with Reduce Motion on only haptic is left"),
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
        check("hierarchy breach: warning, strict fails", "louder than most" in out and code2 == 1, out + out2)
        warn_cases = {
            "canon number without a phrase": (lambda d: d["events"]["hud_merge_bump"]["channels"][0]["from"].pop("match"), "holds several numbers"),
            "invisible shake": (lambda d: d["events"]["alert_crate_landed"]["channels"].append({"type": "shake", "trauma": 0.2}), "invisible"),
            "pitch against the intent": (lambda d: d["events"]["station_arrive"]["channels"][0]["angles_deg"].__setitem__(0, 0.32),
                                         "tips the view UP"),
            "OQ number about something else": (lambda d: d["events"]["lever_commit"]["oq"].append("OQ-037"), "shares no word"),
        }
        for label, (mut, expect) in warn_cases.items():
            p = planted(tmp, label.replace(" ", "-"), mut)
            code, out = run([feel, "--presets", str(p), "validate", "--strict"])
            check(f"validate --strict catches: {label}", code == 1 and expect in out, out)
        p = planted(tmp, "oq-tbd", lambda d: d["events"]["depart"].__setitem__("oq", ["OQ-TBD-hard-brake"]))
        code, out = run([feel, "--presets", str(p), "validate", "--strict"])
        check("OQ-TBD: a note (owner records it), not a failure", code == 0 and "NOTE events.depart: OQ-TBD-hard-brake" in out, out)
        code, out = run([feel, "show", "lever_commit"])
        check("show lists the higher-tier events it outshouts", code == 0 and "Hierarchy:" in out and "louder than" in out, out)
        p = planted(tmp, "build-refused", lambda d: d["events"]["ui_panel_open"]["channels"][0].__setitem__("style", "Springy"))
        code, out = run([feel, "--presets", str(p), "build", "--out", str(tmp / "nobuild")])
        check("build refuses invalid presets", code == 1 and "build refused" in out, out)

        # env override (a mission copy), --presets after the command, editing helpers
        mission = tmp / "M" / "src" / "feel"
        shutil.copytree(SKILL / "presets", mission)
        code, out = run([feel, "list"], env={"RR_FEEL_PRESETS": str(mission)})
        check("RR_FEEL_PRESETS folder override", code == 0 and str(mission) in out, out)
        mj = mission / "feel.json"
        before = mj.read_text()
        code, out = run([feel, "set", "events.alert_crate_landed.channels[0].angles_deg=[-0.9,0,0.2]",
                         "events.hud_crisis_arrival.channels[0].amp=-5", "events.alert_coal_low.channels[0].amp=0.08",
                         "--presets", str(mj)])
        d = json.loads(mj.read_text())
        check("set edits by path, keeps canon bindings and the layout", code == 0
              and d["events"]["alert_crate_landed"]["channels"][0]["angles_deg"] == [-0.9, 0, 0.2]
              and d["events"]["hud_crisis_arrival"]["channels"][0]["amp"].get("canon") == "ui.hud.crisis_extra"
              and len(mj.read_text().splitlines()) == len(before.splitlines()), out)
        code, out = run([feel, "fmt", "--check", "--presets", str(mj)])
        check("fmt --check: set output is in the house layout", code == 0, out)
        old = tmp / "old.json"
        old.write_text(before)
        code, out = run([feel, "changed", "--since", str(old), "--presets", str(mj)])
        check("changed: only the edited groups (+ includers)", code == 0 and "re-preview and re-critique only: crisis, info" in out, out)
        code, out = run([feel, "tune", "alert_crate_landed,hud_crisis_arrival", "--out", str(tmp / "tune"), "--presets", str(mj)])
        tm = (tmp / "tune" / "TUNING.md").read_text() if (tmp / "tune" / "TUNING.md").is_file() else ""
        check("tune: TUNING.md + tuning.csv with ranges and canon locks", code == 0 and "amp (ui.hud.crisis_extra)" in tm
              and "delivered" in tm and (tmp / "tune" / "tuning.csv").is_file(), out)

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
                    lines.append(f"12:00:0{i % 10}.123  {st},{dr},{i / 20:.4f},{v:.6f}" + ("  -  Client - RR_FeelDemo:154" if i == 20 else ""))
        dump.write_text("\n".join(lines))   # as copied from Studio's Output: timestamps before, source after
        code, out = run([feel, "plot", "curves", "--out", str(tmp / "cmp"), "--compare", str(dump)])
        check("plot --compare reads Studio Output lines, flags a differing style only", code == 0 and "DIFF Elastic Out" in out
              and out.count("DIFF") == 1, out)
        (tmp / "junk.txt").write_text("no curves here\n")
        code, out = run([feel, "plot", "curves", "--out", str(tmp / "cmp"), "--compare", str(tmp / "junk.txt")])
        check("plot --compare with no curve rows exits 2", code == 2, out)

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
        code, out = run([feel, "preview", "lever_commit", "--out", str(tmp / "prev"), "--gif", "--rm"])
        check("preview EVENT goes to ev_<event>/, never over its group", code == 0
              and (tmp / "prev" / "ev_lever_commit" / "lever_commit.gif").is_file()
              and json.loads((tmp / "prev" / "lever" / "preview.json").read_text())["events"].__len__() == 6, out)
        code, out = run([feel, "preview", "lever_commit,alert_crate_landed,depart", "--out", str(tmp / "prev"), "--name", "kit"])
        pj = json.loads((tmp / "prev" / "kit" / "preview.json").read_text()) if (tmp / "prev" / "kit" / "preview.json").is_file() else {}
        check("preview E1,E2 --name: one set for one critic, lever drag in its closeups", code == 0 and len(pj.get("events", [])) == 3
              and (tmp / "prev" / "kit" / "lever.png").is_file() and "lever drag" in (tmp / "prev" / "kit" / "closeups.json").read_text(), out)
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
        check("build PASS (Luau syntax + strict types + bible check)", code == 0 and "build PASS" in out and len(files) == 7, out)
        sys.path.insert(0, str(HERE))
        import luau_check
        tools = luau_check.status()
        if tools["luau-compile"]:
            check("build ran the real Luau compiler", "PASS RR_Feel.lua: luau-compile" in out, out)
        else:
            print("SKIP real Luau compiler check: luau-compile not installed (luau_check.py --install)")
        if all(tools.values()):
            x = tmp / "export"
            good = ('--!strict\nlocal RS = game:GetService("ReplicatedStorage")\n'
                    'local Feel = require(RS:WaitForChild("RRFeel"):WaitForChild("RR_FeelTyped"))\n'
                    'Feel.play("lever_commit", { side = -1, targets = { lever_panel = Instance.new("Frame") } })\n'
                    'local k: number = Feel.leverDrag(-0.5, { fork = 1 })\nprint(k)\n')
            (x / "Good.client.luau").write_text(good)
            (x / "Bad.client.luau").write_text(good.replace('"lever_commit"', '"lever_comit"').replace("lever_panel =", "lever_pnael ="))
            c1, o1 = run([str(HERE / "luau_check.py"), str(x / "Good.client.luau"), "--strict", str(x / "Good.client.luau") + "," + str(x / "RR_FeelTyped.luau")])
            c2, o2 = run([str(HERE / "luau_check.py"), str(x / "Bad.client.luau"), "--strict", str(x / "Bad.client.luau") + "," + str(x / "RR_FeelTyped.luau")])
            check("RR_FeelTyped: strict callers typecheck; a wrong event or role name is a type error", c1 == 0 and c2 == 1
                  and o2.count("TypeError") >= 2, o1 + o2)
        else:
            print("SKIP strict typecheck of RR_FeelTyped callers: luau-lsp or Roblox types missing")
        empty = tmp / "home"
        empty.mkdir()
        code, out = run([feel, "build", "--out", str(tmp / "export3")], env={"HOME": str(empty), "PATH": "/usr/bin:/bin"})
        check("build without any Luau tool: syntax SKIP, not FAIL", code == 0 and "syntax unchecked" in out and "FAIL" not in out, out)
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
