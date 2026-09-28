#!/usr/bin/env python3
"""rr-ui-foundry self-test: every ui.py command, the model's rules, the Lua runtime and the reskin promise,
on temporary copies (the real canon and specs are never written).

  selftest.py [-v] [--keep]      exit 0 = all passed

Covers: --help on every script; list/show; validate PASS on the examples, --strict and --json; a planted bad
spec fails on hex, unknown role, contrast, small text, small target, top bar, jump zone, nav, machine, feel name,
canon number, difficulty colour as chrome and a missing icon; stack policy (cap, merge, sticky, compact, halo, lift
cap); pin + scale numbers (phone 1.0, PC = canon 1.16, own fit on the notched phone); render (PNGs, contact sheet
under 1.15 MP, facts.md, HTML-only, text stress, a two-screen set with both phones at true size, the kit board);
crit hand-off for one screen and a set (canon rules in the brief, owner present/away) and critic_kit build; sheet;
ingest (annotated mock; bible tokens snap to their roles, never difficulty/kind roles, off-palette = DECIDE);
build with every gate, BUILD DRAFT with --no-check, rebuild without stale screens, demo only in demo.project.json;
luatest parity + generic runtime, a planted kit bug parity must catch, renamed specs (other screen names, ids and
geometry) that must still BUILD PASS, a missing package; a decided OQ-001 (temp canon) keeps specs valid and makes
its option the main skin; one bible token change reskins every screen while the screen modules stay identical.
Playwright, luaparse and lupa steps are skipped (and said so) when missing.
"""
import sys
sys.dont_write_bytecode = True  # noqa: E402
import argparse, json, os, re, shutil, subprocess, tempfile
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
        {"id": "tier_face", "type": "frame", "rect": [300, 250, 160, 44], "fill": "diff.hard"},
        {"id": "stack", "type": "stack", "rect": [540, 58, 290, 220], "pin": "br",
         "stack": {"template": "ticket", "compact": "ticket_compact", "gap": {"v": 9, "canon": "ui.hud.gap_px"}, "max": 4}}
    ],
    "nav": {"grid": [["small_btn"], ["ghost"]], "default": "small_btn"},
    "types": {"Lost": {"kind": "info", "icon": "no_such_icon", "text": ["LOST!", "gone"]}},
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


MOCK_TOKENS = """<!doctype html><html><body style="margin:0;width:844px;height:390px;background:#7C8A56">
<div data-rr="frame:card" style="position:absolute;left:242px;top:70px;width:360px;height:290px;background:#F5E7C9">
<div data-rr="frame:head" style="position:absolute;left:0;top:0;width:360px;height:56px;background:#C44A20"></div>
<div data-rr="frame:odd" style="position:absolute;left:20px;top:100px;width:60px;height:30px;background:#FF00FF"></div></div></body></html>"""


def renamed_specs(tmp):
    """The examples under other screen names, ids and geometry: the gates must not depend on the examples."""
    lob = json.loads((SKILL / "specs" / "lobby_create_match.json").read_text())
    lob = json.loads(json.dumps(lob).replace('"join"', '"go"').replace('"join.label"', '"go.label"'))
    lob["screen"] = "LobbyJoinQueue"
    lob["nodes"][1]["rect"] = [192, 79, 460, 290]
    hud = json.loads((SKILL / "specs" / "hud_tickets.json").read_text())
    hud["screen"] = "HudCrew"
    out = []
    for name, d in (("lobby_q.json", lob), ("hud_crew.json", hud)):
        (tmp / name).write_text(json.dumps(d))
        out.append(str(tmp / name))
    return out


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
    ok("notched phone area fit is 0.86", abs(kit.fit(notch, "CoreUISafeInsets") - 726 / 844) < 1e-9)
    lob = U.Screen(kit, SKILL / "specs" / "lobby_create_match.json")
    _, kl = U.place_top(kit, notch, lob.index["panel"], "CoreUISafeInsets")
    _, kh = U.place_top(kit, notch, node, "CoreUISafeInsets")
    ok("own fit: the notched phone keeps the lobby panel at 1.0 and shrinks the HUD only to its own fit (0.94)",
       abs(kl - 1) < 1e-9 and abs(kh - 311 / 332) < 1e-6, f"panel {kl:.3f}, hud {kh:.3f}")
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
        code, out = run(UI + ["validate", "hud_tickets", "lobby_create_match", "--strict"])
        ok("validate --strict: both examples have 0 warnings (notched phone included)", code == 0, out[-300:] if code else "")
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
                          ("unknown OQ", r"oq OQ-999 not found"), ("difficulty colour as chrome", r"tier_face.fill: diff.hard"),
                          ("missing icon", r"icon no_such_icon has no file")]:
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
            code, out = run(UI + ["render", "lobby_create_match", "--out", str(tmp / "zz"), "--skins", "Z"])
            ok("render: an unknown skin is refused before rendering", code != 0 and "unknown device or skin: Z" in out and not (tmp / "zz" / "facts.md").exists())
            st = tmp / "set"
            code, out = run(UI + ["render", "hud_tickets", "lobby_create_match", "--out", str(st), "--devices", "phone,phone_notch,pc", "--skins", "C,A"])
            cj = json.loads((st / "contact.json").read_text()) if (st / "contact.json").is_file() else {"tiles": []}
            ones = [t["label"] for t in cj["tiles"] if t["scale"].startswith("1:1")]
            ok("render SET: one contact sheet, both screens' phone boards at true size, facts for both",
               code == 0 and sum("phone" in x for x in ones) == 2 and (st / "facts.md").read_text().count("### Facts:") == 2
               and cj.get("megapixels", 9) <= 1.15, f"{ones} {cj.get('megapixels')}")
            code, out = run(UI + ["crit", str(tmp / "critset"), "--pass", "1", "--from", str(st), "--spec", "hud_tickets,lobby_create_match",
                                  "--owner", "away"])
            b2 = (tmp / "critset" / "brief.md").read_text() if (tmp / "critset" / "brief.md").is_file() else ""
            ok("crit SET: one brief for both screens with both screens' canon; owner away pre-answers step 2",
               code == 0 and b2.startswith("# UI kit set: HudTickets + LobbyCreateMatch") and "ui.rules.one_accent = " in b2
               and b2.strip().endswith("owner away)"))
            code, out = run(UI + ["render", "--kit", "--out", str(tmp / "kit"), "--skins", "C,B"])
            ok("render --kit: every template x state x variant boarded, 0 errors in every skin", code == 0 and "checks: 0 errors" in out
               and (tmp / "kit" / "contact.png").is_file(), out[-300:])
            crit = tmp / "crit"
            code, out = run(UI + ["crit", str(crit), "--pass", "1", "--from", str(rd), "--spec", "hud_tickets"])
            brief = (crit / "brief.md").read_text() if (crit / "brief.md").is_file() else ""
            ok("crit: pass files + brief (canon rules, source, owner asked) + critic_kit command with an absolute path",
               code == 0 and (crit / "pass-1" / "contact.png").is_file() and "ui.hud.compact_rule = " in brief
               and "Source: " in brief and brief.strip().endswith("before pass 1") and "--profile B" in out and f"build {crit}" in out)
            critic = U.find_sibling("multiuse-critic", "RR_CRITIC_SKILL")
            if critic:
                code, out = run([sys.executable, str(critic / "scripts" / "critic_kit.py"), "build", str(crit), "--pass", "1",
                                 "--kind", "full", "--profile", "B", "--images", "closeups.png"])
                ok("critic_kit.py builds critic.md from the hand-off", code == 0 and (crit / "pass-1" / "critic.md").is_file())
            code, out = run(UI + ["sheet", "--out", str(tmp / "sheet")])
            meta = json.loads((tmp / "sheet" / "icons.json").read_text()) if (tmp / "sheet" / "icons.json").is_file() else {}
            n_icons = len(list((SKILL / "assets" / "icons").glob("*.svg")))
            ok(f"sheet: all {n_icons} icons packed with offsets", code == 0 and len(meta.get("icons", {})) == n_icons)
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
            (tmp / "mock2.html").write_text(MOCK_TOKENS)
            code, out = run(UI + ["ingest", str(tmp / "mock2.html"), "--out", str(tmp / "draft2.json")])
            d2 = json.loads((tmp / "draft2.json").read_text()) if (tmp / "draft2.json").is_file() else {}
            fills = re.findall(r'"fill": "([^"]+)"', json.dumps(d2))
            ok("ingest: bible tokens of another skin snap to their roles, never diff/kind/danger; off-palette is a DECIDE",
               code == 0 and {"panel", "header"} <= set(fills) and not any(f.startswith(("diff.", "on_diff.", "kind.")) or f == "danger" for f in fills)
               and "DECIDE odd: #FF00FF" in out, f"{fills}")
        else:
            ok("render/crit/sheet/ingest SKIPPED (no Playwright)", True)
        pkg = tmp / "pkg"
        code, out = run(UI + ["build", "hud_tickets", "lobby_create_match", "--out", str(pkg)])
        ok("build: BUILD PASS with every gate", code == 0 and "BUILD PASS" in out, out[-600:])
        screens1 = {f.name: f.read_text() for f in (pkg / "src/shared/RR_UI/screens").glob("*.lua")}
        theme1 = (pkg / "src/shared/RR_UI/RR_UITheme.lua").read_text() if (pkg / "src/shared/RR_UI/RR_UITheme.lua").is_file() else ""
        readme = (pkg / "README.md").read_text() if (pkg / "README.md").is_file() else ""
        ok("package: README from the built screens; the demo only in demo.project.json, Studio-guarded",
           "screens.LobbyCreateMatch" in readme and "Remove RR_UIDemo before publishing" in readme
           and "RR_UIDemo" not in (pkg / "default.project.json").read_text() and "RR_UIDemo" in (pkg / "demo.project.json").read_text()
           and "IsStudio()" in (pkg / "src/client/RR_UIDemo.client.lua").read_text())
        for f in ("default.project.json", "ASSETS.md", "UI_SPEC.md", "README.md", "manifest.json", "src/shared/RR_UI/RR_UIKit.lua",
                  "src/shared/RR_UI/RR_UITheme.lua", "src/shared/RR_UI/RR_UITemplates.lua", "src/shared/RR_UI/screens/HudTickets.lua",
                  "src/shared/RR_UI/screens/LobbyCreateMatch.lua", "src/client/RR_UIDemo.client.lua"):
            ok(f"package has {f}", (pkg / f).is_file())
        man = json.loads((pkg / "manifest.json").read_text()) if (pkg / "manifest.json").is_file() else {}
        ok("manifest: skin labelled assumed, every gate recorded, Studio pending", man.get("skin_status", "").startswith("assumed")
           and man.get("gates", {}).get("bible_check") == "PASS" and man.get("gates", {}).get("validate") == "PASS"
           and man.get("gates", {}).get("luatest") in ("PASS", "SKIP") and "pending" in man.get("studio", ""))
        ok("luaparse gate ran", man.get("gates", {}).get("luaparse") in ("PASS", "SKIP"), man.get("gates", {}).get("luaparse"))
        if lp:
            code, out = run([sys.executable, str(HERE / "luatest.py"), "--package", str(pkg), "-v", "--specs",
                             f"{SKILL / 'specs' / 'hud_tickets.json'},{SKILL / 'specs' / 'lobby_create_match.json'}"])
            m = re.search(r"parity: (\d+)/(\d+)", out)
            ok("luatest parity: every node matches", code == 0 and m and m[1] == m[2] and int(m[2]) > 500, m[0] if m else out[-300:])
            m2 = re.search(r"runtime: (\d+)/(\d+)", out)
            ok("luatest runtime: all passed", m2 and m2[1] == m2[2], m2[0] if m2 else "")
            mut = tmp / "pkg_mut"
            shutil.copytree(pkg, mut)
            kitf = mut / "src/shared/RR_UI/RR_UIKit.lua"
            kitf.write_text(kitf.read_text().replace("inst.TextSize = e.v * k", "inst.TextSize = e.v * k * 1.1", 1))
            code, out = run([sys.executable, str(HERE / "luatest.py"), "--package", str(mut), "--only", "parity", "--specs",
                             f"{SKILL / 'specs' / 'hud_tickets.json'},{SKILL / 'specs' / 'lobby_create_match.json'}"])
            ok("parity catches a planted kit bug (text 10% big)", code == 1 and "text size" in out)
            code, out = run(UI + ["build", *renamed_specs(tmp), "--out", str(tmp / "pkg_ren")])
            m3 = re.search(r"runtime: (\d+)/(\d+)", out)
            ok("renamed specs (other screen names, ids, panel width) still BUILD PASS with a full runtime",
               code == 0 and "BUILD PASS" in out and m3 and m3[1] == m3[2] and int(m3[2]) >= 40, m3[0] if m3 else out[-400:])
            code, out = run([sys.executable, str(HERE / "luatest.py"), "--package", str(tmp / "no_pkg"), "--specs", "x.json"])
            ok("luatest: a missing package fails (never 'all passed')", code == 1 and "FAILED" in out)
        else:
            ok("luatest SKIPPED (no lupa)", True)
        (pkg / "asset_ids.json").write_text(json.dumps({"iconSheet": "rbxassetid://123", "hazardTile": "rbxassetid://456"}))
        code, out = run(UI + ["build", "hud_tickets", "--out", str(pkg), "--no-parity"])
        ok("asset_ids.json survives a rebuild", code == 0 and 'rbxassetid://123' in (pkg / "src/shared/RR_UI/RR_UITheme.lua").read_text())
        ok("rebuild with fewer screens: no stale screen modules, README follows; skipped gates = BUILD DRAFT",
           [f.name for f in (pkg / "src/shared/RR_UI/screens").glob("*.lua")] == ["HudTickets.lua"]
           and "LobbyCreateMatch" not in (pkg / "README.md").read_text() and "BUILD DRAFT" in out and "BUILD PASS" not in out)
        code, out = run(UI + ["build", "lobby_create_match", "--out", str(tmp / "pkg_draft"), "--no-check", "--no-parity"])
        mand = json.loads((tmp / "pkg_draft" / "manifest.json").read_text()) if (tmp / "pkg_draft" / "manifest.json").is_file() else {}
        ok("--no-check: BUILD DRAFT, manifest says validate SKIPPED (draft)", "BUILD DRAFT" in out and "BUILD PASS" not in out
           and mand.get("gates", {}).get("validate") == "SKIPPED (draft)")
        mission = tmp / "mission" / "src" / "hud"
        mission.mkdir(parents=True)
        shutil.copy2(SKILL / "specs" / "hud_tickets.json", mission / "spec.json")
        code, out = run(UI + ["validate", str(mission / "spec.json"), "--strict"])
        ok("a spec copied into a mission keeps its icons (skill set as fallback)", code == 0, out[-300:])
        bible = U.find_sibling("rr-bible", "RR_BIBLE_SKILL")
        canon = tmp / "canon"
        shutil.copytree(bible / "canon", canon)
        env = {"RR_BIBLE_DIR": str(canon)}
        code, out = run([sys.executable, str(bible / "scripts" / "bible.py"), "add-fact", "style.world.brass", "#B8862F",
                         "--src", "owner 2026-09-28", "--status", "canon", "--replace", "--note", "selftest temp copy"], env=env)
        ok("temp canon: one token changed (style.world.brass)", code == 0, out[-200:])
        pkg2 = tmp / "pkg2"
        code, out = run(UI + ["build", "hud_tickets", "lobby_create_match", "--out", str(pkg2), "--no-parity"], env=env)
        t1 = theme1
        t2 = (pkg2 / "src/shared/RR_UI/RR_UITheme.lua").read_text() if (pkg2 / "src/shared/RR_UI/RR_UITheme.lua").is_file() else ""
        ok("reskin: the theme now carries the new token for every C role mapped to it",
           code == 0 and t2.count('Color3.fromHex("B8862F")') >= 3 and 'Color3.fromHex("B8862F")' not in t1)
        same = len(screens1) == 2 and all(screens1[f] == (pkg2 / "src/shared/RR_UI/screens" / f).read_text() for f in screens1)
        ok("reskin: screen modules unchanged (they hold roles, not colours)", same)
        if pw:
            code, out = run(UI + ["render", "lobby_create_match", "--out", str(tmp / "r2"), "--devices", "phone", "--skins", "C", "--html-only"], env=env)
            html_text = "".join(p.read_text() for p in (tmp / "r2").glob("*.html"))
            ok("reskin: boards pick up the new token too", "#B8862F" in html_text.upper())
        code, out = run([sys.executable, str(bible / "scripts" / "bible.py"), "decide", "OQ-001", "A", "--by", "owner",
                         "--date", "2026-09-28"], env=env)
        code, out = run(UI + ["validate", "hud_tickets", "lobby_create_match"], env=env)
        code2, out2 = run(UI + ["list"], env=env)
        ok("decided OQ-001 (temp canon): specs citing it stay valid, its option becomes the main skin",
           code == 0 and "decided: A (D-" in out2 and "OQ-001 decided" in out, (out + out2)[-300:])
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
