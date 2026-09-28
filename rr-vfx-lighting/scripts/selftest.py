#!/usr/bin/env python3
"""selftest.py: exercises every rr-vfx-lighting command on temp copies; prints "selftest: N/N passed".

  python3 selftest.py [--no-render] [--keep]

--no-render skips Blender (lookdev, preview lighting); --keep leaves the temp folder for inspection.
Never writes inside the skill folder or the bible (bible calls are read-only: get and check).
"""
import argparse, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PY = sys.executable
RESULTS = []


def run(args, env=None, timeout=900):
    e = dict(os.environ, **(env or {}))
    r = subprocess.run([PY, *args], capture_output=True, text=True, env=e, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {detail}" if detail and not ok else ""))


def vfx(*args, env=None):
    return run([str(HERE / "vfx.py"), *args], env=env)


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
    (d / "vfx.json").write_text(json.dumps(v))
    L = json.loads((d / "lighting.json").read_text())
    L["base"]["Atmosphere"]["Density"] = {"v": 0.5, "canon": "tech.lighting.atmosphere"}   # contradicts canon
    (d / "lighting.json").write_text(json.dumps(L))
    b = json.loads((d / "budgets.json").read_text())
    b["tiers"]["phone"]["live_particles"] = 50
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
        for n in ("steam_valve", "debris_smoke", "grassland.night", "cutting.day+tunnel_under"):
            code, out = vfx("show", n, "--json")
            check(f"show {n}", code == 0 and json.loads(out), out[-200:])
        code, out = vfx("show", "no_such_thing")
        check("show unknown exits 1", code == 1, out[-200:])
        code, out = vfx("show", "cutting.day+tunnel_under", "--json")
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
                "layer 'nope' does not exist", "sepia", "OQ-999 not found", "missing_trail", "contradicts canon tech.lighting.atmosphere"]
        missing = [w for w in want if w not in out]
        check("validate catches every planted fault", code == 1 and not missing, f"missing {missing}; {out[-600:]}")
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
        check("canon_agrees", V.canon_agrees(0.3, "Density about 0.3, grey-green") and not V.canon_agrees(0.5, "Density about 0.3")
              and V.canon_agrees([70, 80, 70], "70,80,70 | x") and V.canon_agrees(False, "Use2022Materials = false"))

        import fxsim
        model = V.Model()
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
        check("fxsim pov + overdraw", (tmp / "pov.png").is_file() and "overdraw_max" in r and r["live"] > 0, str(r))
        r = fxsim.gif(model, "coal_dust", tmp / "anim.gif", seconds=0.5, fps=6, quick=True)
        check("fxsim gif", (tmp / "anim.gif").is_file(), str(r))

        import importlib.util
        render = not a.no_render and importlib.util.find_spec("bpy") is not None
        pv = tmp / "preview"
        if render:
            code, out = vfx("preview", "all", "--out", str(pv), "--quick")
            check("preview all --quick", code == 0 and (pv / "lighting" / "contact.png").is_file()
                  and (pv / "vfx" / "contact.png").is_file(), out[-500:])
            facts = json.loads((pv / "lighting" / "grassland.day.facts.json").read_text())
            check("lookdev facts measured", facts["spawn_edge_fog"] > 0.5 and facts["train_vs_world_contrast"], str(facts)[:300])
            check("phone fallback rendered", (pv / "lighting" / "grassland.day.phone.png").is_file())
            check("POV composites over lookdev plates", (pv / "vfx" / "pov_crisis.png").is_file())
        else:
            code, out = vfx("preview", "vfx", "--out", str(pv), "--quick")
            check("preview vfx --quick (no render)", code == 0 and (pv / "vfx" / "contact.png").is_file(), out[-400:])
            print("note: Blender steps skipped (--no-render or no bpy)")
        src = pv / ("lighting" if render else "vfx")
        crit = tmp / "crit"
        code, out = vfx("crit", str(crit), "--pass", "1", "--from", str(src))
        rub = (crit / "rubric.md").read_text() if (crit / "rubric.md").is_file() else ""
        check("crit writes rubric with Profile F and brief", code == 0 and "## Profile F" in rub and "A6, B5, F5" in rub
              and (crit / "brief.md").is_file() and (crit / "pass-1" / "contact.png").is_file(), out[-400:])
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
