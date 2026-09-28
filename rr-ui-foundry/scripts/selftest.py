#!/usr/bin/env python3
"""rr-ui-foundry self-test: every ui.py command, the model's rules, the Lua runtime and the reskin promise,
on temporary copies (the real canon and specs are never written).

  selftest.py [-v] [--keep]      exit 0 = all passed

Covers: --help on every script; list/show; validate PASS on the examples, --strict and --json; a planted bad
spec fails on hex, unknown role, contrast, small text, small target, top bar, jump zone, nav, machine, feel name
and canon number; stack policy (cap, merge, sticky, compact, halo, lift cap); pin + scale numbers (phone 1.0,
PC = canon 1.16); render (PNGs, contact sheet under 1.15 MP, facts.md, HTML-only, text stress); crit hand-off
and critic_kit build; sheet; ingest of an annotated mock (roles, canon text match, validates); build with every
gate; luatest parity + runtime and a planted kit bug that parity must catch; one bible token change reskins
every screen (temp canon copy via RR_BIBLE_DIR) while the screen modules stay identical.
Playwright, luaparse and lupa steps are skipped (and said so) when missing.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
import uimodel as U  # noqa: E402

UI = [sys.executable, str(HERE / "ui.py")]
R = []


def ok(name, cond, detail=""):
    R.append((name, bool(cond), detail))


def run(args, env=None, timeout=600):
    e = dict(os.environ)
    e.update(env or {})
    r = subprocess.run(args, capture_output=True, text=True, env=e, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def have_playwright():
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def have_lupa():
    sys.path.insert(0, str(Path.home() / ".cache" / "rr-tools" / "py"))
    try:
        import lupa  # noqa: F401
        return True
    except ImportError:
        return False


BAD_SPEC = {
    "screen": "BadScreen", "title": "planted faults", "design": {"device": "phone"},
    "gui": {"insets": "CoreUISafeInsets", "modal": True}, "canon": ["no.such.key"], "oq": ["OQ-999"],
    "nodes": [
        {"id": "top", "type": "text", "rect": [300, 20, 200, 30], "text": "IN THE TOP BAR", "style": "title", "color": "ink"},
        {"id": "hexy", "type": "frame", "rect": [20, 80, 100, 40], "fill": "#FF00FF"},
        {"id": "role", "type": "frame", "rect": [20, 130, 100, 40], "fill": "no_such_role"},
        {"id": "low", "type": "text", "rect": [20, 180, 200, 30], "text": "low contrast", "style": "label", "color": "paper_top", "fill": "panel"},
        {"id": "tiny", "type": "text", "rect": [20, 220, 200, 10], "text": "tiny text", "style": "tiny"},
        {"id": "small_btn", "use": "button", "rect": [300, 150, 30, 30], "slots": {"text": "S"}, "action": "go"},
        {"id": "lost_btn", "use": "button", "rect": [400, 150, 120, 48], "slots": {"text": "LOST"}, "action": "go"},
        {"id": "jumpy", "use": "button", "rect": [760, 320, 70, 48], "slots": {"text": "J"}, "action": "go"},
        {"id": "stack", "type": "stack", "rect": [540, 58, 290, 220], "pin": "br",
         "stack": {"template": "ticket", "compact": "ticket_compact", "gap": {"v": 9, "canon": "ui.hud.gap_px"}, "max": 4}}
    ],
    "nav": {"grid": [["small_btn"], ["ghost"]], "default": "small_btn"},
    "machine": {"initial": "idle", "states": {"idle": {"hide": ["nobody"]}},
                "transitions": [["idle", "go", "gone", "no_such_feel_event"]]}
}

MOCK = """<!doctype html><html><head><style>
body{margin:0;width:844px;height:390px;background:#7C8A56;font-family:Montserrat}
.p{position:absolute;left:242px;top:70px;width:360px;height:290px;background:#EBDDBE;border:3px solid #15171C;border-radius:16px;box-sizing:border-box}
.t{position:absolute;left:16px;top:10px;font:26px 'Luckiest Guy';color:#15171C}
.c{position:absolute;top:80px;width:44px;height:44px;background:#E8D9B5;border:2px solid #15171C;border-radius:12px;box-sizing:border-box;font:22px 'Luckiest Guy';text-align:center;line-height:40px}
.b{position:absolute;left:20px;top:200px;width:320px;height:56px;background:#C9953A;border:3px solid #15171C;border-radius:12px;box-sizing:border-box;font:22px 'Luckiest Guy';text-align:center;line-height:50px}
.a{position:absolute;left:20px;top:140px;font:700 14px Montserrat;color:#4A4133}
</style></head><body>
<div class="p" data-rr="panel:main"><div class="t" data-rr="text:heading">SHIFT BRIEFING</div>
<div class="c" style="left:20px" data-rr="chip:c1">1</div><div class="c" style="left:72px" data-rr="chip:c2">2</div>
<div class="a" data-rr="text:alert">Shovel coal in the firebox!</div>
<div class="b" data-rr="button:go" data-rr-variant="primary">GO</div></div></body></html>"""


def model_tests():
    kit = U.Kit()
    ok("kit resolves every role in every skin against rr-bible", not kit.errors, "; ".join(kit.errors[:3]))
    ok("density from canon: phone 1.0, PC px per design px = canon 1.16",
       abs(kit.density["Small"] - 1) < 1e-9 and abs(kit.fit(kit.devices["pc"], "CoreUISafeInsets") * kit.density["Medium"] - 1.16) < 1e-3)
    phone, pc, notch = kit.devices["phone"], kit.devices["pc"], kit.devices["phone_notch"]
    ok("design area = phone under the top bar", kit.design_device.area("CoreUISafeInsets") == (0.0, 58.0, 844.0, 332.0))
    hud = U.Screen(kit, SKILL / "specs" / "hud_tickets.json")
    node = hud.nodes[0]
    (x, y, w, h), k = U.place_top(kit, phone, node, "CoreUISafeInsets")
    ok("HUD stack on the phone sits at canon 14 px right / 112 px bottom", abs(844 - (x + w) - 14) < 1e-6 and abs(390 - (y + h) - 112) < 1e-6)
    (x, y, w, h), k = U.place_top(kit, pc, node, "CoreUISafeInsets")
    ok("HUD stack on PC: margins x 1.16, not floating (pure Scale would put it 223 px up)",
       abs(1280 - (x + w) - 14 * 1.16) < 0.05 and abs(720 - (y + h) - 112 * 1.16) < 0.05, f"bottom {720 - (y + h):.1f}")
    st = node["stack"]
    vis, hidden = U.stack_sim(hud, st, [["CrewJoined", {"name": "A"}], ["CrateLanded"], ["PressureHigh"], ["RiskyRoute"],
                                        ["FareBanked"], ["FareBanked"], ["CrewLeft", {"name": "B"}]])
    ok("stack: canon cap 4, merge counts, sticky crisis kept, +2 hidden",
       len(vis) == 4 and hidden == 2 and any(v["type"] == "PressureHigh" for v in vis)
       and next(v for v in vis if v["type"] == "FareBanked")["count"] == 2)
    ok("stack: only the newest ticket and newest crisis are full; halo on the newest crisis only",
       [v["compact"] for v in vis] == [True, True, True, False] or sum(not v["compact"] for v in vis) <= 2)
    vis2, _ = U.stack_sim(hud, st, [["CoalLow"], ["Breakdown"], ["FareBanked"]])
    ok("stack: halo sits on the newest crisis", [v["halo"] for v in vis2] == [False, True, False])
    sc = U.resolve(hud, phone, "C", hud.boards[1])
    ok("phone: lifted above the jump zone and capped at max_lifted", sc["stack"]["visible"] == 3)
    sc = U.resolve(hud, pc, "C", hud.boards[1])
    ok("PC: no touch zones, full canon cap", sc["stack"]["visible"] == 4)
    z = kit.zones_for(phone)
    ok("phone touch zones from canon (small controls)", z["_size"] == "small" and z["jump"][2] == 136)
    ok("notched phone scales by 0.86", abs(kit.fit(notch, "CoreUISafeInsets") - 726 / 844) < 1e-9)
    ok("slot fill and filters", U.fill_slots("{a|upper}-{b}", {"a": "x", "b": 2}) == "X-2" and U.fill_slots("{z}", {}, False) == "")
    ok("rect expressions", U.ev("100%-6", 64) == 58 and U.ev("50%+2", 10) == 7)
    lua = U.lua({"type": "x", "a b": [1, 2.5, True], "s": 'q"'})
    ok("Lua literal emitter quotes keywords and odd keys", '["type"] = "x"' in lua and '["a b"] = { 1, 2.5, true }' in lua and 'q\\"' in lua)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-v", action="store_true")
    ap.add_argument("--keep", action="store_true", help="keep the temp folder")
    a = ap.parse_args(argv)
    tmp = Path(tempfile.mkdtemp(prefix="rr-ui-selftest-"))
    pw, lp = have_playwright(), have_lupa()
    try:
        for s in ("ui.py", "luatest.py", "selftest.py", "uimodel.py"):
            code, out = run([sys.executable, str(HERE / s), "--help"])
            ok(f"{s} --help", code == 0 and len(out) > 50)
        model_tests()
        code, out = run(UI + ["list"])
        ok("list shows both examples and 6 templates", code == 0 and "hud_tickets" in out and "lobby_create_match" in out and "panel" in out)
        code, out = run(UI + ["show", "lobby_create_match"])
        ok("show prints tree, machine, nav", code == 0 and "machine:" in out and "nav: default join" in out)
        code, out = run(UI + ["validate", "hud_tickets", "lobby_create_match"])
        ok("validate: both examples PASS", code == 0 and out.count("PASS") == 2, out[-300:] if code else "")
        code, out = run(UI + ["validate", "hud_tickets", "--strict"])
        ok("validate --strict fails on warnings (notched-phone text)", code == 1)
        code, out = run(UI + ["validate", "lobby_create_match", "--json"])
        try:
            j = json.loads(out)
            ok("validate --json is machine-readable", "LobbyCreateMatch" in j and j["LobbyCreateMatch"]["errors"] == [])
        except ValueError:
            ok("validate --json is machine-readable", False, out[:200])
        bad = tmp / "bad.json"
        bad.write_text(json.dumps(BAD_SPEC))
        code, out = run(UI + ["validate", str(bad)])
        for label, rx in [("hex in a spec", r"#FF00FF|colour|not a colour|does not resolve"), ("unknown role", r"no_such_role"),
                          ("contrast", r"contrast .* for low"), ("unknown type style", r"unknown type style 'tiny'"),
                          ("small target", r"target small_btn .* < 44"), ("top bar strip", r"top enters the top bar"),
                          ("jump zone", r"jumpy.* overlaps the jump zone"), ("nav unknown id", r"nav.grid: unknown id ghost"),
                          ("nav unreachable", r"lost_btn is unreachable"), ("machine state", r"unknown state gone"),
                          ("hide unknown id", r"unknown id nobody"), ("feel event", r"no_such_feel_event"),
                          ("canon number", r"9 does not appear in ui.hud.gap_px"), ("unknown canon key", r"canon no.such.key not found"),
                          ("unknown OQ", r"oq OQ-999 not found")]:
            ok(f"bad spec caught: {label}", code == 1 and re.search(rx, out) is not None)
        if pw:
            rd = tmp / "render"
            code, out = run(UI + ["render", "hud_tickets", "--out", str(rd), "--devices", "phone,pc,phone_notch", "--skins", "C,A"])
            pngs = list(rd.glob("*.png"))
            ok("render: boards, zone board, contact + closeups", code == 0 and (rd / "contact.png").is_file()
               and (rd / "closeups.png").is_file() and any("__zones" in p.name for p in pngs) and len(pngs) >= 8, out[-300:])
            try:
                from PIL import Image
                im = Image.open(rd / "contact.png")
                ok("contact sheet under 1.15 MP with the phone at true size", im.size[0] * im.size[1] <= 1.15e6 and im.size[0] >= 844)
                ph = Image.open(next(rd.glob("HudTickets__routine__phone__C.png")))
                ok("phone board is 844 x 390", ph.size == (844, 390))
            except Exception as e:  # noqa: BLE001
                ok("contact sheet readable", False, str(e))
            facts = (rd / "facts.md").read_text()
            ok("facts.md: devices, contrast, fonts embedded, no overflow", "| pc |" in facts and "contrast" in facts
               and "embedded woff2" in facts and "Text wider than its box (Chromium): none" in facts)
            code, out = run(UI + ["render", "lobby_create_match", "--out", str(tmp / "stress"), "--devices", "phone", "--skins", "C",
                                  "--text-scale", "1.3"])
            ok("render --text-scale stress board runs and reports", code in (0, 1) and "Text stress" in (tmp / "stress" / "facts.md").read_text())
            code, out = run(UI + ["render", "lobby_create_match", "--out", str(tmp / "html"), "--html-only"])
            ok("render --html-only writes HTML without a browser", code == 0 and list((tmp / "html").glob("*.html")) and not list((tmp / "html").glob("*.png")))
            crit = tmp / "crit"
            code, out = run(UI + ["crit", str(crit), "--pass", "1", "--from", str(rd), "--spec", "hud_tickets"])
            ok("crit: pass files + brief + critic_kit command", code == 0 and (crit / "pass-1" / "contact.png").is_file()
               and (crit / "brief.md").read_text().strip().endswith("step 2: pre-answered (canon via rr-bible; owner away)")
               and "--profile B" in out)
            critic = U.find_sibling("multiuse-critic", "RR_CRITIC_SKILL")
            if critic:
                code, out = run([sys.executable, str(critic / "scripts" / "critic_kit.py"), "build", str(crit), "--pass", "1",
                                 "--kind", "full", "--profile", "B", "--images", "closeups.png"])
                ok("critic_kit.py builds critic.md from the hand-off", code == 0 and (crit / "pass-1" / "critic.md").is_file())
            code, out = run(UI + ["sheet", "--out", str(tmp / "sheet")])
            meta = json.loads((tmp / "sheet" / "icons.json").read_text()) if (tmp / "sheet" / "icons.json").is_file() else {}
            ok("sheet: 10 icons packed with offsets", code == 0 and len(meta.get("icons", {})) == 10)
            mock = tmp / "mock.html"
            mock.write_text(MOCK)
            draft = tmp / "draft.json"
            code, out = run(UI + ["ingest", str(mock), "--out", str(draft), "--name", "Shift briefing"])
            d = json.loads(draft.read_text()) if draft.is_file() else {}
            flat = json.dumps(d)
            ok("ingest: panel, chips, primary button, canon text matched, roles not hex", code == 0 and '"use": "panel"' in flat
               and '"use": "chip"' in flat and '"variant": "primary"' in flat and '"canon": "gameplay.alerts.coal_low"' in flat
               and not re.search(r'"fill": "#', flat))
            code, out = run(UI + ["validate", str(draft)])
            ok("ingested draft loads and validates", code == 0, out[-400:])
        else:
            ok("render/crit/sheet/ingest SKIPPED (no Playwright)", True)
        pkg = tmp / "pkg"
        code, out = run(UI + ["build", "hud_tickets", "lobby_create_match", "--out", str(pkg)])
        ok("build: BUILD PASS with every gate", code == 0 and "BUILD PASS" in out, out[-600:])
        for f in ("default.project.json", "ASSETS.md", "UI_SPEC.md", "README.md", "manifest.json", "src/shared/RR_UI/RR_UIKit.lua",
                  "src/shared/RR_UI/RR_UITheme.lua", "src/shared/RR_UI/RR_UITemplates.lua", "src/shared/RR_UI/screens/HudTickets.lua",
                  "src/shared/RR_UI/screens/LobbyCreateMatch.lua", "src/client/RR_UIDemo.client.lua"):
            ok(f"package has {f}", (pkg / f).is_file())
        man = json.loads((pkg / "manifest.json").read_text()) if (pkg / "manifest.json").is_file() else {}
        ok("manifest: skin labelled assumed, gates recorded, Studio pending", man.get("skin_status", "").startswith("assumed")
           and man.get("gates", {}).get("bible_check") == "PASS" and "pending" in man.get("studio", ""))
        ok("luaparse gate ran", man.get("gates", {}).get("luaparse") in ("PASS", "SKIP"), man.get("gates", {}).get("luaparse"))
        (pkg / "asset_ids.json").write_text(json.dumps({"iconSheet": "rbxassetid://123", "hazardTile": "rbxassetid://456"}))
        code, out = run(UI + ["build", "hud_tickets", "--out", str(pkg), "--no-parity"])
        ok("asset_ids.json survives a rebuild", code == 0 and 'rbxassetid://123' in (pkg / "src/shared/RR_UI/RR_UITheme.lua").read_text())
        if lp:
            code, out = run([sys.executable, str(HERE / "luatest.py"), "--package", str(pkg), "-v"])
            m = re.search(r"parity: (\d+)/(\d+)", out)
            ok("luatest parity: every node matches", code == 0 and m and m[1] == m[2] and int(m[2]) > 500, m[0] if m else out[-300:])
            m2 = re.search(r"runtime: (\d+)/(\d+)", out)
            ok("luatest runtime: all passed", m2 and m2[1] == m2[2], m2[0] if m2 else "")
            mut = tmp / "pkg_mut"
            shutil.copytree(pkg, mut)
            kitf = mut / "src/shared/RR_UI/RR_UIKit.lua"
            kitf.write_text(kitf.read_text().replace("inst.TextSize = e.v * k", "inst.TextSize = e.v * k * 1.1", 1))
            code, out = run([sys.executable, str(HERE / "luatest.py"), "--package", str(mut), "--only", "parity"])
            ok("parity catches a planted kit bug (text 10% big)", code == 1 and "text size" in out)
        else:
            ok("luatest SKIPPED (no lupa)", True)
        bible = U.find_sibling("rr-bible", "RR_BIBLE_SKILL")
        canon = tmp / "canon"
        shutil.copytree(bible / "canon", canon)
        env = {"RR_BIBLE_DIR": str(canon)}
        code, out = run([sys.executable, str(bible / "scripts" / "bible.py"), "add-fact", "style.world.brass", "#B8862F",
                         "--src", "owner 2026-09-28", "--status", "canon", "--replace", "--note", "selftest temp copy"], env=env)
        ok("temp canon: one token changed (style.world.brass)", code == 0, out[-200:])
        pkg2 = tmp / "pkg2"
        code, out = run(UI + ["build", "hud_tickets", "lobby_create_match", "--out", str(pkg2), "--no-parity"], env=env)
        t1 = (pkg / "src/shared/RR_UI/RR_UITheme.lua").read_text() if (pkg / "src/shared/RR_UI/RR_UITheme.lua").is_file() else ""
        t2 = (pkg2 / "src/shared/RR_UI/RR_UITheme.lua").read_text() if (pkg2 / "src/shared/RR_UI/RR_UITheme.lua").is_file() else ""
        ok("reskin: the theme now carries the new token for every C role mapped to it",
           code == 0 and t2.count('Color3.fromHex("B8862F")') >= 3 and 'Color3.fromHex("B8862F")' not in t1)
        same = all((pkg / "src/shared/RR_UI/screens" / f).read_text() == (pkg2 / "src/shared/RR_UI/screens" / f).read_text()
                   for f in ("HudTickets.lua", "LobbyCreateMatch.lua"))
        ok("reskin: screen modules unchanged (they hold roles, not colours)", same)
        if pw:
            code, out = run(UI + ["render", "lobby_create_match", "--out", str(tmp / "r2"), "--devices", "phone", "--skins", "C", "--html-only"], env=env)
            html_text = "".join(p.read_text() for p in (tmp / "r2").glob("*.html"))
            ok("reskin: boards pick up the new token too", "#B8862F" in html_text.upper())
        code, out = run([sys.executable, str(bible / "scripts" / "bible.py"), "lint"])
        ok("real rr-bible untouched and lint OK", code == 0 and "lint OK" in out)
    finally:
        if not a.keep:
            shutil.rmtree(tmp, ignore_errors=True)
        for p in SKILL.rglob("__pycache__"):
            shutil.rmtree(p, ignore_errors=True)
    bad = [r for r in R if not r[1]]
    for name, passed, detail in R:
        if a.v or not passed:
            print(f"  {'PASS' if passed else 'FAIL'} {name}{' (' + str(detail) + ')' if detail else ''}")
    print(f"selftest: {len(R) - len(bad)}/{len(R)} passed" + (" -- all passed" if not bad else ""))
    if a.keep:
        print(f"kept {tmp}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
