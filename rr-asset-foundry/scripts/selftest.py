#!/usr/bin/env python3
"""Self-test for rr-asset-foundry: runs every command on a temporary copy of the skill (the real families folder
is never touched) and prints one line per test, then 'N/N passed'.

  python3 selftest.py [--quick] [--keep]

--quick  skip everything that needs Blender (bpy): list, show, plan, errors, batch dry runs, Lua check, new-family
--keep   keep the temp folder (its path is printed) to inspect outputs
Needs rr-bible and multiuse-critic reachable the same way foundry.py finds them. Exit 1 if any test fails.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, time

sys.dont_write_bytecode = True       # never leave __pycache__ in this or a sibling skill

ME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFECT = '''"""Planted defects for the self-test (not a real family)."""
FAMILY = "defect"
DESC = "planted defects"
PARAMS = {"size": ("float", 4.0, 1, 10, "edge")}
GROUPS = {"A": ("style.depot_kit.stone", "Slate"), "B": ("style.depot_kit.iron", "Metal")}
PRESETS = {"base": {"params": {}, "note": "defects"}}
VIEW = {"ground": "style.lobby.concrete", "features": ["Wire", "Bloc"], "player": "test"}


def build(k, p):
    import bmesh
    s = p["size"]
    k.box("Block", "A", (0, 0, s / 2), (s, s, s))
    k.box("Wire", "B", (-s / 2 + 0.4, -s / 2 + 0.4, s + 1.45), (0.1, 0.1, 3.0))   # thin: must warn under 5 px
    k.box("Skin", "B", (0.3, 0, s / 2), (s, s, s))          # shares the y and z face planes: coplanar
    k.box("Float", "B", (0, 0, s + 3), (1, 1, 1))           # hovers: floating
    o = k.box("Flipped", "A", (s + 2, 0, 1), (2, 2, 2))     # inside-out: back faces in view
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
'''


CRASHY = '''"""Crashes on demand (env CRASHY=1, size > 4.5) for the batch resume test."""
import os
import _crashhelp
FAMILY = "crashy"
DESC = "crash test"
PARAMS = {"size": ("float", 3.0, 1, 10, "edge")}
GROUPS = {"A": ("style.depot_kit.stone", "Slate")}
PRESETS = {"base": {"params": {}, "note": "crash"}}
VIEW = {"ground": "style.lobby.concrete", "features": [], "player": "test"}


def build(k, p):
    if os.environ.get("CRASHY") and p["size"] > 4.5:
        raise RuntimeError("planted crash")
    k.box("Block", "A", (0, 0, p["size"] / 2), (p["size"],) * 3)
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(ME, "scripts"))
    import foundry
    bible_root, critic = foundry.find_skill("rr-bible", "RR_BIBLE"), foundry.find_skill("multiuse-critic", "RR_CRITIC")
    if not bible_root or not critic:
        sys.exit("rr-bible or multiuse-critic not found; set RR_BIBLE / RR_CRITIC")
    tmp = tempfile.mkdtemp(prefix="rr-foundry-selftest-")
    skill = os.path.join(tmp, "rr-asset-foundry")
    shutil.copytree(ME, skill, ignore=shutil.ignore_patterns("__pycache__"))
    out = os.path.join(tmp, "out")
    env = dict(os.environ, RR_FOUNDRY_OUT=out, RR_BIBLE=os.path.join(bible_root, "scripts", "bible.py"), RR_CRITIC=critic,
               PYTHONDONTWRITEBYTECODE="1")
    fdy = [sys.executable, os.path.join(skill, "scripts", "foundry.py")]
    results = []

    def run(*args, expect=0, timeout=900, extra_env=None):
        r = subprocess.run(fdy + [str(x) for x in args], capture_output=True, text=True, env=dict(env, **(extra_env or {})),
                           timeout=timeout)
        assert r.returncode == expect, f"exit {r.returncode} (want {expect}): {(r.stdout + r.stderr)[-500:]}"
        return r.stdout + r.stderr

    def test(name, fn):
        t = time.time()
        try:
            fn()
            results.append(True)
            print(f"PASS {name} ({time.time() - t:.0f}s)", flush=True)
        except (AssertionError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as e:
            results.append(False)
            print(f"FAIL {name}: {type(e).__name__}: {e}", flush=True)

    fams = {"carriage": ["coach_works", "coach_brand", "coach_short", "coach_long"],
            "wagon": ["open_coal", "open_bogie", "flat_crates", "box_van", "tank_long"],
            "building": ["hut_stone", "hut_taped", "signal_box", "shelter"],
            "prop": ["crate_single", "crate_stack", "crate_hazard", "drum_cluster", "barrier_taped"],
            "track": ["straight", "straight_long", "buffer_stop"]}

    def t_help():
        for script in ("foundry.py", "forge.py", "fkit.py", "selftest.py"):
            r = subprocess.run([sys.executable, os.path.join(skill, "scripts", script), "--help"], capture_output=True,
                               text=True, env=env)
            assert r.returncode == 0 and "usage" in r.stdout.lower(), f"{script} --help: {r.stderr[-200:]}"

    def t_list():
        o = run("list")
        assert all(f"{f}:" in o for f in fams), o
        o = run("list", "--match", "coal wagon please")
        assert "wagon:" in o and "building:" not in o, o
        o = run("list", "--match", "freight wagon open coal box van crate flat")
        assert o.startswith("wagon:"), f"best match not first: {o[:200]}"

    def t_show():
        for f in fams:
            assert "presets:" in run("show", f)
        o = run("show", "wagon")
        assert "OQ-030" in o and "premises" in o and "siding" in o, o[-400:]

    def t_plan():
        for f, presets in fams.items():
            for p in presets:
                plan = json.loads(run("plan", f, "--preset", p, "--json"))
                assert plan["palette"] and all(len(h) == 7 and h[0] == "#" for h in plan["palette"]), (f, p)
                assert not plan["warnings"], (f, p, plan["warnings"])
        c = json.loads(run("plan", "carriage", "--json"))
        assert c["param_sources"]["width"]["key"] == "tech.units.stock_width", c["param_sources"]
        assert {"OQ-025", "OQ-030"} <= set(c["open"]), c["open"]
        b = json.loads(run("plan", "building", "--json"))
        assert b["param_sources"]["door_w"]["key"] == "tech.units.building_door", b["param_sources"]
        t = json.loads(run("plan", "track", "--json"))
        assert "OQ-030" in t["open"] and t["params"]["length"] > 0, t["open"]
        w = json.loads(run("plan", "wagon", "--json"))
        assert w["options"]["pov"] == "siding" and w["view"]["nums"]["siding"] > 0, w["options"]
        assert json.loads(run("plan", "wagon", "--pov", "lobby", "--json"))["options"]["pov"] == "lobby"
        assert "segment_len" in run("plan", "track", "--set", "length=20"), "track length that misses the segment"
        assert "building_door" in run("plan", "building", "--preset", "hut_stone", "--set", "door_h=7"), "low door"

    def t_errors():
        run("plan", "nosuchfamily", expect=2)
        run("plan", "wagon", "--set", "length=999", expect=2)
        run("plan", "wagon", "--set", "kind=spaceship", expect=2)
        run("plan", "wagon", "--set", "nosuchparam=1", expect=2)
        run("plan", "carriage", "--group", "Body=style.nope.nope", expect=2)
        run("plan", "carriage", "--group", "Body=style.world.hazard_old", expect=2)      # superseded token
        run("plan", "prop", "--name", "bad_name", expect=2)
        run("plan", "wagon", "--set", "length", expect=2)                               # no =
        run("plan", "wagon", "--params", os.path.join(tmp, "nope.json"), expect=2)
        run("plan", "wagon", "--pov", "nope", expect=2)
        run("plan", "carriage", "--pov", "lobby", expect=2)                             # one player view only
        run("verify", os.path.join(tmp, "nope"), expect=2)
        for bad in ("length=24:48:0", "length=24:48:-8", "length=48:24:8", "length=a:b"):   # used to hang or trace
            run("batch", "wagon", "--vary", bad, "--dry-run", expect=2, timeout=30)
        run("batch", "prop", "--vary", "size=1:10:0.01", "--dry-run", expect=2, timeout=30)   # grid over the cap

    def t_dry():
        o = run("batch", "wagon", "--vary", "length=24:40:8", "--vary", "kind=open,box", "--dry-run")
        assert o.count("  v0") == 6, o
        o = run("batch", "prop", "--preset", "drum_cluster", "--vary", "drum_r=1:1.6", "--mode", "random", "--n", "4", "--dry-run")
        assert o.count("  v0") == 4, o

    def t_lua():
        sys.path.insert(0, os.path.join(skill, "scripts"))
        import foundry as f2
        good, bad = os.path.join(tmp, "good.lua"), os.path.join(tmp, "bad.lua")
        open(good, "w").write('local n = 0\nfor i = 1, 3 do\n  if i > 1 then n += i end\nend\nprint(("%d"):format(n))\n')
        open(bad, "w").write('local n = 0\nfor i = 1, 3 do\n  if i > 1 then n += i\nend\n')
        assert f2.lua_check(good)[0], f2.lua_check(good)
        assert not f2.lua_check(bad)[0], "a missing end passed"
        saved = list(f2._LUAPARSE)
        f2._LUAPARSE[:] = [None]                       # force the block-balance fallback
        assert f2.lua_check(good)[0] and not f2.lua_check(bad)[0], "fallback check"
        f2._LUAPARSE[:] = saved

    def t_newfam():
        run("new-family", "demo_shed")
        assert os.path.isfile(os.path.join(skill, "families", "demo_shed.py"))
        run("new-family", "demo_shed", expect=2)
        assert "DemoShed" in run("plan", "demo_shed")

    for name, fn in (("help on every script", t_help), ("list and --match", t_list), ("show every family", t_show),
                     ("plan every preset: canon keys, tokens, open questions, no warnings", t_plan),
                     ("refusals: family, range, choice, param, unknown and superseded token, name", t_errors),
                     ("batch dry runs (grid, random)", t_dry), ("Lua check (luaparse and fallback)", t_lua),
                     ("new-family scaffold", t_newfam)):
        test(name, fn)

    has_bpy = subprocess.run([sys.executable, "-c", "import bpy"], capture_output=True).returncode == 0
    if a.quick or not has_bpy:
        print("skipped Blender tests (" + ("--quick" if a.quick else "no bpy") + ")")
    else:
        made = {}

        def t_make_all():
            for f, presets in fams.items():
                extra = ["--lod"] if f == "wagon" else []
                o = run("make", f, "--preset", presets[0], "--renders", "thumb", *extra)
                asset = foundry.camel(f, presets[0])
                v = os.path.join(out, asset)
                man = json.load(open(os.path.join(v, "manifest.json")))
                assert man["status"] == "ok", (f, man.get("fails"), o[-300:])
                for fn_ in [f"{asset}.fbx", f"{asset}_atlas.fbx", f"{asset}.blend", "palette.png", "parts.csv",
                            "studio_setup.lua", "facts.md", "README.md", "renders/thumb.png", "renders/game.png"]:
                    assert os.path.isfile(os.path.join(v, fn_)), f"{f}: missing {fn_}"
                assert man["checks"]["bible_check"] == "PASS" and man["checks"]["lua"].startswith("ok"), man["checks"]
                res = json.load(open(os.path.join(v, "result.json")))
                assert not res["reimport"].get("unit_warning"), res["reimport"]
                made[f] = v
            assert os.path.isfile(os.path.join(made["wagon"], "WagonOpenCoal_LOD1.fbx")), "LOD1 missing"
            lod = json.load(open(os.path.join(made["wagon"], "manifest.json")))["lod1"]
            assert lod["parts"] < json.load(open(os.path.join(made["wagon"], "manifest.json")))["parts"], lod

        def t_every_preset():
            for f, presets in fams.items():
                for p in presets[1:]:
                    run("make", f, "--preset", p, "--renders", "none")

        def t_identity():
            t0 = time.time()
            assert "up to date" in run("make", "prop", "--preset", "crate_single", "--renders", "thumb")
            assert time.time() - t0 < 20, "an up-to-date make should not rebuild"
            run("make", "prop", "--preset", "crate_single", "--set", "size=5", expect=2)
            run("make", "prop", "--preset", "crate_single", "--set", "size=5", "--name", "CrateFive", "--renders", "none")
            plan = os.path.join(out, "CrateFive", "plan.json")
            assert "up to date" in run("make", "prop", "--params", plan, "--renders", "none")

        def t_defects():
            open(os.path.join(skill, "families", "defect.py"), "w").write(DEFECT)
            o = run("make", "defect", "--renders", "none", expect=1)
            assert "coplanar" in o and "floating" in o and "back faces" in o, o[-400:]
            assert "key features under" in o and "Wire" in o, f"thin feature not warned: {o[-400:]}"
            feats = json.load(open(os.path.join(out, "DefectBase", "result.json")))["features"]
            assert "Bloc" not in feats, f"feature keys must match the part token exactly: {feats}"
            run("crit", os.path.join(out, "DefectBase"), "--crit", os.path.join(tmp, "critfail"), expect=1)

        def t_batch():
            args = ("batch", "prop", "--preset", "crate_single", "--vary", "size=3,5", "--jobs", "2")
            run(*args)
            b = os.path.join(out, "batch-PropCrateSingle")
            st = json.load(open(os.path.join(b, "batch.json")))
            assert [v["status"] for v in st["variants"]] == ["ok", "ok"], st["variants"]
            assert os.path.isfile(os.path.join(b, "sheet-1.png")) and os.path.isfile(os.path.join(b, "batch.md"))
            t0 = time.time()
            run(*args)
            assert time.time() - t0 < 30, "resume rebuilt finished variants"
            run("sheet", made["prop"], made["building"], "--out", os.path.join(tmp, "vs.png"))
            assert os.path.isfile(os.path.join(tmp, "vs.png")), "variant sheet from single variants"

        def t_resume():
            fams_dir = os.path.join(skill, "families")
            open(os.path.join(fams_dir, "crashy.py"), "w").write(CRASHY)
            open(os.path.join(fams_dir, "_crashhelp.py"), "w").write("X = 1\n")
            args = ("batch", "crashy", "--vary", "size=3,5", "--renders", "none")
            b = os.path.join(out, "batch-Crashy")
            run(*args, expect=1, extra_env={"CRASHY": "1"})            # v002 crashes; the batch finishes, exit 1
            st = json.load(open(os.path.join(b, "batch.json")))
            assert [v["status"] for v in st["variants"]] == ["ok", "error"], st["variants"]
            made1 = json.load(open(os.path.join(b, "v001", "manifest.json")))["made"]
            run(*args)                                                    # resume: v001 skipped, v002 rebuilt
            st = json.load(open(os.path.join(b, "batch.json")))
            assert [v["status"] for v in st["variants"]] == ["ok", "ok"], st["variants"]
            assert json.load(open(os.path.join(b, "v001", "manifest.json")))["made"] == made1, "v001 was rebuilt"
            h1 = json.load(open(os.path.join(b, "v001", "manifest.json")))["hash"]
            open(os.path.join(fams_dir, "_crashhelp.py"), "a").write("# helper changed\n")
            run(*args)                                                    # a helper edit makes both stale
            assert json.load(open(os.path.join(b, "v001", "manifest.json")))["hash"] != h1, "helper edit ignored"

        def t_crit():
            crit = os.path.join(tmp, "crit")
            copy = os.path.join(tmp, "building-copy")              # crit works on copies (CRIT/round-N, export)
            shutil.copytree(made["building"], copy)
            o = run("crit", copy, "--crit", crit)
            for fn_ in ("pass-1/contact.png", "pass-1/contact.json", "pass-1/facts.md", "brief.md", "pass-1/pov3p.png",
                        "pass-1/pov3p_2.png"):
                assert os.path.isfile(os.path.join(crit, fn_)), f"missing {fn_}"
            assert os.path.isfile(os.path.join(copy, "renders", "pov3p.png")), "renders did not land in the copy"
            assert not os.path.isfile(os.path.join(made["building"], "renders", "pov3p.png")), "rendered into the original"
            brief = open(os.path.join(crit, "brief.md")).read()
            assert "NOT answered" in brief and "Purpose: TODO" in brief and "TODO line" in o, brief[:300]
            r = subprocess.run([sys.executable, os.path.join(critic, "scripts", "critic_kit.py"), "build", crit, "--pass", "1",
                                "--kind", "full", "--profile", "A"], capture_output=True, text=True)
            assert r.returncode == 0 and os.path.isfile(os.path.join(crit, "pass-1", "critic.md")), r.stdout + r.stderr
            crit2 = os.path.join(tmp, "crit2")
            run("crit", made["track"], made["prop"], "--crit", crit2)
            assert os.path.isfile(os.path.join(crit2, "pass-1", "closeups.png")), "two-variant closeups"

        def t_verify():
            run("verify", made["carriage"])
            bad = os.path.join(tmp, "tampered")
            shutil.copytree(made["carriage"], bad)
            lua = os.path.join(bad, "studio_setup.lua")
            txt = open(lua).read()
            off = "12" + "AB34"                         # an off-palette colour, built so this file passes the gate
            open(lua, "w").write(txt.replace('fromHex("', f'fromHex("{off}") -- ', 1))
            assert "canon gate FAIL" in run("verify", bad, expect=1)

        def t_newfam_make():
            run("make", "demo_shed", "--renders", "thumb")

        def t_premise():
            crit = os.path.join(tmp, "critw")
            run("crit", made["wagon"], "--crit", crit, "--pov", "lobby")
            man = json.load(open(os.path.join(made["wagon"], "manifest.json")))
            assert man["pov"] == "lobby" and "on foot" in man["pov_stands"][0]["label"], man.get("pov_stands")
            assert "premise lobby" in open(os.path.join(crit, "brief.md")).read()

        for name, fn in (("make one preset per family (+LOD1): files, checks, canon gate, reimport", t_make_all),
                         ("make every other preset (checks pass)", t_every_preset),
                         ("identity: up to date, refuse a different variant, rename, rebuild from plan.json", t_identity),
                         ("planted defects: coplanar, floating, back faces fail; thin feature warns; crit refuses", t_defects),
                         ("batch grid + sheet + resume; sheet of single variants", t_batch),
                         ("batch crash resume (error rebuilt, ok kept) and helper-file staleness", t_resume),
                         ("crit on a copy (renders stay in it), TODO brief, critic_kit build; two-variant closeups", t_crit),
                         ("verify good and tampered export", t_verify), ("make the scaffolded family", t_newfam_make),
                         ("POV premise switch re-renders the player views", t_premise)):
            test(name, fn)
    print(f"{sum(results)}/{len(results)} passed" + (f"; kept {tmp}" if a.keep else ""))
    if not a.keep:
        shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
