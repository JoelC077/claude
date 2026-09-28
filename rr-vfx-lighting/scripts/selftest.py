#!/usr/bin/env python3
"""selftest.py: exercises every rr-vfx-lighting command on temp copies; prints "selftest: N/N passed".

  python3 selftest.py [--no-render] [--keep]

--no-render skips Blender (lookdev, preview lighting); --keep leaves the temp folder for inspection.
Never writes inside the skill folder or the bible (bible calls are read-only: get and check).
"""
import sys
sys.dont_write_bytecode = True  # never leave __pycache__ inside the skill
import argparse, json, os, shutil, subprocess, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PY = sys.executable
RESULTS = []


def run(args, env=None, timeout=900, stdout_only=False):
    e = dict(os.environ, **(env or {}))
    e.pop("RR_VFX_PRESETS", None) if env is None else None
    r = subprocess.run([PY, *args], capture_output=True, text=True, env=e, timeout=timeout)
    return r.returncode, (r.stdout if stdout_only else r.stdout + r.stderr)


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {detail}" if detail and not ok else ""))


def vfx(*args, env=None, stdout_only=False):
    return run([str(HERE / "vfx.py"), *args], env=env, stdout_only=stdout_only)


def planted(tmp):
    """A presets copy with one known fault per rule."""
    d = tmp / "bad_presets"
    shutil.copytree(SKILL / "presets", d)
    v = json.loads((d / "vfx.json").read_text())
    p = v["presets"]["steam_chimney"]["layers"][0]["props"]
    p["Wobble"] = 3                                              # unknown property
    p["LightEmission"] = 1.5                                     # hard range
    p["Transparency"] = [[0.1, 0.2], [1, 1]]                     # keypoints must start at 0
    p["Color"] = [[0, "#123456"], [1, "#FFFFFF"]]                # raw colour
    v["presets"]["steam_chimney"]["speed_link"]["layers"] = ["nope"]
    v["fx_colours"]["sepia_haze"] = {"hex": "#A87F50", "why": "planted"}
    v["presets"]["rain"]["oq"] = "OQ-999"
    v["presets"]["boiler_burst"]["layers"][-1]["debris"]["trail"] = "missing_trail"
    fg = v["presets"]["firebox_glow"]["layers"][0]["props"]                 # swapped: canon Brightness 2, Range 9
    fg["Range"], fg["Brightness"] = {"v": 22, "canon": "style.light.firebox"}, {"v": 7, "canon": "style.light.firebox"}
    v["presets"]["derail_explosion"]["canon"] = "none: no canon"             # no oq, not 'proposed'
    v["presets"]["derail_explosion"].pop("oq", None)
    (d / "vfx.json").write_text(json.dumps(v))
    L = json.loads((d / "lighting.json").read_text())
    L["base"]["Atmosphere"]["Density"] = {"v": 0.5, "canon": "tech.lighting.atmosphere"}   # contradicts canon
    cc = L["base"]["ColorCorrectionEffect"]                                  # swapped: canon Saturation +0.12, Contrast +0.05
    cc["Saturation"], cc["Contrast"] = {"v": 0.05, "canon": "tech.lighting.color_correction"}, {"v": 0.12, "canon": "tech.lighting.color_correction"}
    L["overrides"]["tunnel_under"]["Lighting"]["ExposureCompensation"] = {"add": 4.5}   # 5.4 only in night+tunnel
    (d / "lighting.json").write_text(json.dumps(L))
    b = json.loads((d / "budgets.json").read_text())
    b["tiers"]["phone"]["live_particles"] = 50
    for sd in b["sets"].values():
        if "glass_burst" in sd["presets"]:
            sd["presets"].remove("glass_burst")                             # a preset in no set
    (d / "budgets.json").write_text(json.dumps(b))
    return d


def synthetic_view(tmp):
    """A plate and view.json without Blender, for fxsim pov."""
    from PIL import Image
    Image.new("RGB", (192, 108), (190, 200, 175)).save(tmp / "plate.png")
    view = {"camera": "roof3p", "eye": [-70, 23.5, 0], "forward": [0.9, -0.08, 0.43], "right": [-0.43, 0, 0.9],
            "up": [0.03, 1, 0.07], "fov_v": 70, "res": [192, 108], "plate": "plate.png", "particle_light": [1, 1, 1],
            "fog": {"k": 0.0015, "colour": [194, 202, 176]}}
    (tmp / "view.json").write_text(json.dumps(view))
    return tmp / "view.json"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args(argv)
    tmp = Path(tempfile.mkdtemp(prefix="rrfx_selftest_"))
    try:
        for s in ("vfx.py", "fxsim.py", "lookdev_bpy.py", "preview.py", "selftest.py"):
            code, out = run([str(HERE / s), "--help"])
            check(f"{s} --help", code == 0 and "usage" in out.lower(), out[-200:])
        code, out = vfx("list")
        check("list", code == 0 and "steam_chimney" in out and "grassland.day" in out, out[-300:])
        check("every command names its presets folder", "presets: " in out and "shipped library" in out, out[:200])
        for n in ("steam_valve", "debris_smoke", "grassland.night", "cutting.day+tunnel_under"):
            code, out = vfx("show", n, "--json", stdout_only=True)
            check(f"show {n}", code == 0 and json.loads(out), out[-200:])
        code, out = vfx("show", "no_such_thing")
        check("show unknown exits 1", code == 1, out[-200:])
        code, out = vfx("init", str(SKILL / "presets"))
        check("init refuses the shipped folder", code == 2, out[-200:])
        work = tmp / "work_fx"
        code, out = vfx("init", str(work))
        code2, out2 = vfx("list", "--presets", str(work))
        check("init + --presets uses the work copy", code == 0 and (work / "vfx.json").is_file() and str(work) in out2
              and "shipped" not in out2.splitlines()[0], out2[:300])
        code, out = vfx("show", "cutting.day+tunnel_under", "--json", stdout_only=True)
        lk = json.loads(out)
        check("override applies (tunnel darkens, headlamp on)",
              lk["classes"]["Lighting"]["Brightness"] < 1 and "headlamp" in lk["fx_on"], str(lk["classes"]["Lighting"])[:200])
        code, out = vfx("validate", "--strict")
        check("validate --strict passes on shipped presets", code == 0 and "validate PASS" in out, out[-400:])
        code, out = vfx("budget")
        check("budget passes on shipped sets", code == 0 and "budget PASS" in out, out[-400:])

        bad = planted(tmp)
        env = {"RR_VFX_PRESETS": str(bad)}
        code, out = vfx("validate", env=env)
        want = ["no property Wobble", "outside 0..1", "keypoint times must start at 0", "raw colour",
                "layer 'nope' does not exist", "sepia", "OQ-999 not found", "missing_trail", "contradicts Density 0.3 in canon",
                "value 22 contradicts Range 9", "value 7 contradicts Brightness 2", "value 0.05 contradicts Saturation +0.12",
                "value 0.12 contradicts Contrast +0.05", "outside -5..5 (in grassland.dusk+tunnel_under)", "needs an oq", "glass_burst: in no budgets.json set"]
        missing = [w for w in want if w not in out]
        check("validate catches every planted fault (swapped canon values, override x look ranges, sets, none: rule)",
              code == 1 and not missing, f"missing {missing}; {out[-900:]}")
        code, out = vfx("budget", "--tier", "phone", env=env)
        check("budget fails when over the phone tier", code == 1 and "OVER" in out, out[-300:])
        code, out = vfx("build", "--out", str(tmp / "bad_export"), env=env)
        check("build refuses invalid presets", code == 1 and "build refused" in out, out[-300:])

        exp = tmp / "export"
        code, out = vfx("build", "--out", str(exp))
        files = sorted(p.name for p in exp.glob("*"))
        check("build passes (syntax + canon gates)", code == 0 and "build PASS" in out, out[-500:])
        check("build writes the package", {"RR_FXPresets.lua", "RR_LightingPresets.lua", "RR_VFX.lua", "RR_Lighting.lua",
                                           "RR_FXDemo.client.lua", "studio_lighting_setup.lua", "README.md"} <= set(files), str(files))
        lp = (exp / "RR_LightingPresets.lua").read_text()
        check("derived colours export as Lerp of sources", ":Lerp(hex(" in lp and "lvl(70, 80, 70)" in lp, lp[:200])
        tool = "luaparse" if "(luaparse)" in out else "balance"
        check(f"syntax checker ran ({tool})", "syntax ok" in out, out[-300:])

        sys.path.insert(0, str(HERE))
        import vfx as V
        ok1 = V.balance_check("local function f()\n if x then return 1 end\nend\n")[0]
        ok2 = not V.balance_check("local function f()\n if x then return 1\nend\n")[0]
        check("balance check", ok1 and ok2)
        ca = lambda *x: V.canon_agrees(*x)[0]
        check("canon_agrees reads the number next to the property; hex never counts",
              ca(0.3, "Density about 0.3, grey-green", "Density") and not ca(0.5, "Density about 0.3", "Density")
              and ca([70, 80, 70], "70,80,70 | x") and ca(False, "MaterialService.Use2022Materials = false", "Use2022Materials")
              and not ca(22, "#FF7A22 | PointLight Brightness 2, Range 9", "Range")
              and not ca(0.05, "Saturation +0.12, Contrast +0.05", "Saturation") and ca(0.05, "Saturation +0.12, Contrast +0.05", "Contrast")
              and ca(9, "range nine studs (9)", "Range", r"\((\d+)\)") and not ca(3, "between 2 and 3 studs", "Size"))

        import fxsim
        model = V.Model()
        br = model.presets["sparks_brake"]["layers"]
        g = model.dims["gauge"]
        check("stand expressions resolve from canon (fan offsets = +-gauge/2)",
              br[0]["offset"][2] == g / 2 and br[1]["offset"][2] == -g / 2 and model.anchors["Axle"][2] == g / 2, str(model.dims))
        s = fxsim.Sim(model, ["steam_chimney"], speed=0)
        e = s.emitters[0]
        e.parts = []
        e.spawn(1)
        q = e.parts[0]
        v0 = sum(x * x for x in q["vel"]) ** 0.5
        drag = e.drag
        e.acc = [0, 0, 0]
        e.rate = 0
        for _ in range(int(round((1 / drag) / fxsim.DT))):
            e.step(fxsim.DT, [0, 0, 0])
        v1 = sum(x * x for x in q["vel"]) ** 0.5
        check("drag halves speed every 1/Drag s", abs(v1 / v0 - 0.5) < 0.06, f"{v1 / v0:.3f}")
        s = fxsim.Sim(model, ["steam_chimney"], speed=model.meta["speeds"]["normal"])
        s.run_to(2.0)
        xs = [p["pos"][0] for p in s.emitters[0].parts]
        check("steam drifts back with GlobalWind (train never moves)", xs and min(xs) < model.anchors["Chimney"][0] - 20, f"min x {min(xs) if xs else None}")
        r = fxsim.strip(model, "steam_valve", tmp / "strip_loop.png", quick=True)
        check("fxsim strip loop", (tmp / "strip_loop.png").is_file() and r["live"][0] > 0, str(r))
        r = fxsim.strip(model, "boiler_burst", tmp / "strip_burst.png", quick=True)
        check("fxsim strip burst", (tmp / "strip_burst.png").is_file() and r["live"][0] > 0, str(r))
        r = fxsim.pov(model, ["steam_chimney", "smoke_chimney"], synthetic_view(tmp), tmp / "pov.png")
        pp = r.get("per_preset", {}).get("steam_chimney", {})
        check("fxsim pov + overdraw + per-preset visibility", (tmp / "pov.png").is_file() and "overdraw_max" in r and r["live"] > 0
              and pp.get("live", 0) == pp.get("visible", 0) + pp.get("hidden", 0) + pp.get("offscreen", 0) and "covered" in pp, str(r)[:400])
        r = fxsim.pov(model, ["steam_chimney", "coal_dust"], tmp / "view.json", tmp / "pov_b.png", t=0.3, tier="phone")
        check("fxsim pov: burst fires after loops warm up; phone tier", r["t"] > 0.3 and r["tier"] == "phone"
              and r["per_preset"]["coal_dust"]["live"] > 0, str(r)[:300])
        r = fxsim.gif(model, "coal_dust", tmp / "anim.gif", seconds=0.5, fps=6, quick=True)
        check("fxsim gif", (tmp / "anim.gif").is_file(), str(r))

        code, out = vfx("preview", "all", "grassland.day", "no_such_preset", "--out", str(tmp / "bad_prev"), "--quick")
        check("preview refuses unknown names", code == 2 and "not a preset or look" in out, out[-300:])
        code, out = vfx("preview", "vfx", "sparks_brake", "--out", str(tmp / "pv_names"), "--quick")
        strips = sorted(p.name for p in (tmp / "pv_names" / "vfx").glob("strip_*.png"))
        check("preview renders only the named presets", code == 0 and strips == ["strip_sparks_brake.png"], str(strips) + out[-300:])
        exp2 = tmp / "export_pack"
        code, out = vfx("build", "--out", str(exp2), "--only", "sparks_brake", "grassland.night", "--no-check")
        fxl = (exp2 / "RR_FXPresets.lua").read_text() if (exp2 / "RR_FXPresets.lua").is_file() else ""
        check("build --only exports a pack (+ the looks' fx_on) with wiring notes",
              code == 0 and "sparks_brake = {" in fxl and "headlamp = {" in fxl and "steam_valve = {" not in fxl
              and "starts off" in (exp2 / "README.md").read_text(), out[-300:])
        code, out = run([str(HERE / "luatest.py")])
        check("runtime logic in a Lua VM (luatest.py)" + (" skipped: no lupa" if code == 3 else ""), code in (0, 3), out[-600:])

        import importlib.util
        render = not a.no_render and importlib.util.find_spec("bpy") is not None
        if render:
            import lookdev_bpy as LB
            try:
                LB.Look(model, "grassland.day@cab", "+Z")
                bad_cam = False
            except KeyError:
                bad_cam = True
            check("unknown camera is an error, not a mislabelled roof render", bad_cam)
        pv = tmp / "preview"
        if render:
            names = ["steam_chimney", "sparks_brake", "coal_dust", "grassland.day", "grassland.dusk"]
            code, out = vfx("preview", "all", *names, "--out", str(pv), "--quick")
            B = pv / "board"
            man = json.loads((B / "manifest.json").read_text()) if (B / "manifest.json").is_file() else {}
            check("preview all NAMES: one board (contact, facts, manifest) for the pack", code == 0 and (B / "contact.png").is_file()
                  and (B / "facts.md").is_file() and man.get("presets") == ["steam_chimney", "sparks_brake", "coal_dust"]
                  and man.get("looks") == ["grassland.day", "grassland.dusk"], out[-600:])
            L = pv / "lighting"
            check("pack renders roof, door, near cameras and phone plates",
                  all((L / f).is_file() for f in ("grassland.dusk.png", "grassland.day_door1p.png", "grassland.day_cab1p.png",
                                                  "grassland.day.phone.png", "view_grassland.day.phone.json")), str(sorted(p.name for p in L.glob("*.png"))))
            facts = json.loads((L / "grassland.day.facts.json").read_text())
            ph = json.loads((L / "grassland.day.phone.facts.json").read_text())
            check("lookdev facts measured (fog, contrast, hazard rails, phone aspect)", facts["spawn_edge_fog"] > 0.5
                  and facts["train_vs_world_contrast"] and facts.get("hazard_vs_world") and ph["res"][0] / ph["res"][1] > 2, str(facts)[:300])
            fm = (B / "facts.md").read_text()
            check("board facts carry per-preset visibility and phone POVs", "hid " in fm and "| phone |" in fm and "pov_coal_dust" in fm, fm[-600:])
            src = pv
        else:
            code, out = vfx("preview", "vfx", "--out", str(pv), "--quick")
            check("preview vfx --quick (no render)", code == 0 and (pv / "vfx" / "contact.png").is_file(), out[-400:])
            print("note: Blender steps skipped (--no-render or no bpy)")
            src = pv / "vfx"
        crit = tmp / "crit"
        os.makedirs(tmp / "cwd", exist_ok=True)
        r = subprocess.run([PY, str(HERE / "vfx.py"), "crit", "crit_rel", "--pass", "1", "--from", str(src)], cwd=tmp / "cwd",
                           capture_output=True, text=True)
        code, out = r.returncode, r.stdout + r.stderr
        crit = tmp / "cwd" / "crit_rel"
        rub = (crit / "rubric.md").read_text() if (crit / "rubric.md").is_file() else ""
        check("crit writes rubric with Profile F and brief; absolute paths in the command", code == 0 and "## Profile F" in rub
              and "A6, B5, F5" in rub and (crit / "brief.md").is_file() and (crit / "pass-1" / "contact.png").is_file()
              and f"build {crit}" in out and "critic: " in out, out[-500:])
        critic = V.find_sibling("multiuse-critic", "RR_CRITIC_SKILL")
        if critic:
            code, out = run([str(critic / "scripts" / "critic_kit.py"), "build", str(crit), "--pass", "1", "--kind", "full",
                             "--profile", "F", "--role", "senior VFX and lighting artist"])
            cm = (crit / "pass-1" / "critic.md").read_text() if (crit / "pass-1" / "critic.md").is_file() else ""
            check("critic_kit builds a Profile F pass", code == 0 and "### F1 Signal" in cm and "### House style" in cm, out[-300:])
        else:
            print("note: multiuse-critic not found; critic_kit step skipped")
    finally:
        if a.keep:
            print(f"kept {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)
        for pc in SKILL.rglob("__pycache__"):
            shutil.rmtree(pc, ignore_errors=True)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"selftest: {passed}/{len(RESULTS)} passed" + ("" if passed == len(RESULTS) else " (FAILURES above)"))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
