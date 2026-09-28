#!/usr/bin/env python3
"""Self-test for rr-data-and-money: every script, on synthetic data, in a temp data root (nothing else is touched).

  selftest.py [-v] [--keep]

Covers statlib reference values (textbook numbers), track.py (canon funnel, negative plans, build, scan coverage),
luatest.py (Lua VM, a plan without the example experiment, crew hooks), abtest.py (plan, refusal to overwrite,
NOT DONE, verdicts, small cells, final O'Brien-Fleming boundary, hidden interim estimates, guardrail, SRM, edited
and re-planned plans, thumbnail redirect, compare record, native record, bad inputs), dash.py (parsers, ingest,
memo, charts, CI-aware spend gate, synthetic stamp, edge cases), econ.py (validate, canon drift, overrides, sim
checks incl. difficulty ladder and short-of-kit, sweep record and typo, ladder states, guard incl. hidden products,
departures from canon and --gate), svgchart XML validity and --help on every script. Exit 0 = all passed.
"""
import argparse, copy, json, os, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
import dash  # noqa: E402
import rrlib  # noqa: E402
import statlib as S  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-v", action="store_true")
    ap.add_argument("--keep", action="store_true", help="keep the temp root and print its path")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="rr-dm-selftest-"))
    env = dict(os.environ, RR_DATA_ROOT=str(tmp / "root"))
    res = []

    def ok(name, cond, detail=""):
        res.append((name, bool(cond)))
        if a.v or not cond:
            print(f"  {'ok  ' if cond else 'FAIL'} {name} {detail}")

    def run(*args, code=0):
        r = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, env=env, cwd=str(HERE))
        out = r.stdout + r.stderr
        if a.v and r.returncode != code:
            print(out[-2000:])
        return r.returncode == code and "Traceback" not in out, out

    # statlib vs textbook values
    ok("norm_ppf(0.975)", abs(S.norm_ppf(0.975) - 1.959964) < 1e-6)
    ok("n per arm 10% -> 12% = 3,841", S.n_two_prop(0.10, 0.12)[0] == 3841)
    ok("Fisher tea tasting p = 0.4857", abs(S.fisher_exact(3, 4, 1, 4) - 0.4857) < 1e-4)
    ok("chi2 sf(3.841, 1) = 0.05", abs(S.chi2_sf(3.841, 1) - 0.05) < 1e-4)
    ok("t 0.975 quantile df 10 = 2.228", abs(S.t_ppf(0.975, 10) - 2.2281) < 1e-3)
    lo, hi = S.newcombe(56, 70, 48, 80)
    ok("Newcombe 1998 example CI", abs(lo + 0.3339) < 1e-3 and abs(hi + 0.0524) < 1e-3, (lo, hi))
    b = S.obf_bounds([.2, .4, .6, .8, 1.0], sims=100000)
    ok("O'Brien-Fleming 5 looks vs table", all(abs(x - y) < 0.04 for x, y in zip(b, [4.562, 3.226, 2.634, 2.281, 2.040])), b)
    f10 = S.peek_fpr(10)
    ok("naive peeking FPR at 10 looks about 19%", 0.17 < f10 < 0.21, f10)
    ok("Holm", S.holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06])

    # help on every script
    for s in ("rrlib.py", "statlib.py", "svgchart.py", "track.py", "dash.py", "abtest.py", "econ.py", "luatest.py"):
        good, out = run(HERE / s, "--help")
        ok(f"{s} --help", good and len(out) > 100)

    # track.py
    good, out = run(HERE / "track.py", "validate")
    ok("tracking plan validates against canon", good and "PASS" in out, out[-300:])
    plan = rrlib.load_json(SKILL / "presets" / "tracking-plan.json")
    bad = copy.deepcopy(plan)
    bad["onboarding"]["steps"].pop(2)
    bad["events"][0]["fields"].append({"name": "username", "enum": ["x"]})
    bad["events"] = [e for e in bad["events"] if e["id"] != "player_left"]
    bp = tmp / "bad-plan.json"
    bp.write_text(json.dumps(bad))
    good, out = run(HERE / "track.py", "validate", "--plan", bp, code=1)
    ok("bad plan fails (canon drift, privacy, 4 fields, missing canon event)",
       good and "canon" in out and "username" in out and "4 fields" in out and "player_left" in out, out[-600:])
    good, out = run(HERE / "track.py", "build", "--out", tmp / "build")
    ok("plan builds Lua + doc", good and (tmp / "build" / "RR_AnalyticsPlan.lua").is_file() and
       (tmp / "build" / "TRACKING_PLAN.md").is_file())
    good, out = run(HERE / "luatest.py", "--plan-lua", tmp / "build" / "RR_AnalyticsPlan.lua")
    ok("luatest on the built plan", good and ("passed" in out or "SKIP" in out), out[-400:])
    src = tmp / "src"
    src.mkdir()
    (src / "Lever.server.lua").write_text('local AnalyticsService = game:GetService("AnalyticsService")\n'
                                          'A.event(player, "free_robux", 1)\nA.event(player, "lever_pulled", 2)\n')
    good, out = run(HERE / "track.py", "scan", src, code=1)
    ok("scan flags direct AnalyticsService + unplanned id", good and "direct AnalyticsService" in out and "free_robux" in out)
    good, out = run(HERE / "track.py", "scan", SKILL / "assets" / "luau")
    ok("scan passes the shipped Luau (every planned step, event, status and sku logged)", good and "PASS" in out, out[-300:])
    cov = tmp / "cov"
    shutil.copytree(SKILL / "assets" / "luau", cov)
    hk = cov / "RR_AnalyticsHooks.lua"
    hk.write_text(hk.read_text().replace('A.funnel(player, "trip", tripId, "queued")', 'A.funnel(player, "trip", tripId, "boarded")'))
    (cov / "Lobby.server.lua").write_text('local H = require(script.Parent.RR_AnalyticsHooks)\nH.playerJoined(p)\n')
    good, out = run(HERE / "track.py", "scan", cov, code=1)
    ok("scan: a planned funnel step no hook logs is an error; idle hooks are listed", good and "trip.queued" in out
       and "hooks never called" in out, out[-500:])
    noex = copy.deepcopy(plan)
    noex["experiments"] = {"_doc": "none yet"}
    (tmp / "noex.json").write_text(json.dumps(noex))
    run(HERE / "track.py", "build", "--plan", tmp / "noex.json", "--out", tmp / "noex")
    good, out = run(HERE / "luatest.py", "--plan-lua", tmp / "noex" / "RR_AnalyticsPlan.lua")
    ok("luatest works on a plan without the example experiment", good and ("passed" in out or "SKIP" in out), out[-300:])

    # abtest
    ex = tmp / "root" / "experiments"
    good, out = run(HERE / "abtest.py", "plan", "t1", "--surface", "onboarding", "--base", "0.10", "--mde-rel", "0.3",
                    "--daily", "150", "--guardrail", "sess:0.02", "--start", "2026-10-05")
    ok("plan written with whole weeks", good and "28 days" in out and (ex / "t1" / "plan.json").is_file(), out[-300:])
    csvp = tmp / "early.csv"
    csvp.write_text("arm,users,conversions\nA,700,70\nB,690,95\n")
    good, out = run(HERE / "abtest.py", "analyze", ex / "t1", "--data", csvp)
    ok("before the horizon: NOT DONE and no estimates", good and "NOT DONE" in out and "lift" not in out, out[-300:])
    csvp.write_text("arm,users,conversions,sess_users,sess_hits\nA,1800,180,1800,1000\nB,1790,240,1790,1060\n")
    good, out = run(HERE / "abtest.py", "analyze", ex / "t1", "--data", csvp, "--asof", "2026-11-03")
    ok("at the horizon: SHIP B with CI", good and "SHIP B" in out and "95% CI" in out, out[-400:])
    csvp.write_text("arm,users,conversions,sess_users,sess_hits\nA,1800,180,1800,1000\nB,1790,240,1790,900\n")
    good, out = run(HERE / "abtest.py", "analyze", ex / "t1", "--data", csvp, "--asof", "2026-11-03")
    ok("guardrail failure blocks the winner", good and "GUARDRAIL FAIL" in out)
    csvp.write_text("arm,users,conversions\nA,1900,190\nB,1500,150\n")
    good, out = run(HERE / "abtest.py", "analyze", ex / "t1", "--data", csvp)
    ok("sample ratio mismatch = INVALID", good and "INVALID" in out)
    pj = ex / "t1" / "plan.json"
    pl = json.loads(pj.read_text())
    pl["metric"]["target"] = 0.2
    pj.write_text(json.dumps(pl))
    good, out = run(HERE / "abtest.py", "analyze", ex / "t1", "--data", csvp, code=1)
    ok("edited plan is refused", good and "edited" in out)
    good, out = run(HERE / "abtest.py", "plan", "p1", "--surface", "price", "--metric", "rpu", "--base", "0.02",
                    "--price-a", "149", "--price-b", "99", "--mde-rel", "0.25", "--daily", "300")
    ok("price plan flags NOT TESTABLE at low traffic", good and "NOT TESTABLE" in out)
    tc = tmp / "thumbs.csv"
    tc.write_text("variant,impressions,qualified_plays\nA,48000,1510\nB,9000,230\nC,1200,40\n")
    good, out = run(HERE / "abtest.py", "compare", "--data", tc)
    ok("compare: descriptive, flags a clear loser, skips thin data", good and "no winner call" in out and
       "clearly below" in out and "too early" in out)
    good, out = run(HERE / "abtest.py", "plan", "t1", "--surface", "onboarding", "--base", "0.10", "--mde-rel", "0.5",
                    "--daily", "150", code=1)
    ok("plan refuses to overwrite a pre-registered plan", good and "--replace" in out)
    for args in (("--base", "0.6", "--mde-rel", "1.0", "--daily", "100"), ("--base", "0.1", "--mde-rel", "0.3", "--daily", "0")):
        good, out = run(HERE / "abtest.py", "plan", "bad", "--surface", "other", *args, code=1)
        ok(f"plan rejects {' '.join(args)}", good and "INVALID" in out, out[-200:])
    run(HERE / "abtest.py", "plan", "sm", "--surface", "price", "--base", "0.003", "--mde-rel", "3.0", "--daily", "300",
        "--guardrail", "refund:0.01", "--start", "2026-08-01")
    csvp.write_text("arm,users,conversions,refund_users,refund_hits\nA,2400,6,2400,3\nB,2400,11,2400,6\n")
    good, out = run(HERE / "abtest.py", "analyze", ex / "sm", "--data", csvp, "--asof", "2026-12-01")
    ok("small cells: Fisher exact, no crash", good and "fisher-exact" in out, out[-300:])
    run(HERE / "abtest.py", "plan", "s4", "--surface", "other", "--base", "0.10", "--mde-rel", "0.3", "--daily", "400",
        "--looks", "4", "--start", "2026-08-01")
    csvp.write_text("arm,users,conversions\nA,520,52\nB,520,58\n")
    good, out = run(HERE / "abtest.py", "analyze", ex / "s4", "--data", csvp, "--asof", "2026-08-05")
    ok("interim look: CONTINUE with no effect, CI or per-arm label", good and "CONTINUE" in out and "CI" not in out and
       "NO DIFFERENCE" not in out and (ex / "s4" / "looks.json").is_file(), out[-300:])
    good, out = run(HERE / "abtest.py", "analyze", ex / "s4", "--data", csvp, "--asof", "2026-08-06")
    ok("the same look is read once", good and "already read" in out)
    csvp.write_text("arm,users,conversions\nA,2100,210\nB,2100,250\n")
    good, out = run(HERE / "abtest.py", "analyze", ex / "s4", "--data", csvp, "--asof", "2026-08-15")
    ok("final look uses the planned final boundary (z 1.98 < 2.03 is no win)", good and "NO DIFFERENCE" in out
       and "SHIP" not in out, out[-400:])
    good, out = run(HERE / "abtest.py", "plan", "s4", "--surface", "other", "--base", "0.10", "--mde-rel", "0.5",
                    "--daily", "400", "--replace")
    good2, out2 = run(HERE / "abtest.py", "analyze", ex / "s4", "--data", csvp, "--asof", "2026-08-15", code=1)
    ok("re-planned after data: kept in history, analyze refuses", good and good2 and "re-planned" in out2 and
       (ex / "s4" / "history").is_dir(), out2[-300:])
    run(HERE / "abtest.py", "plan", "th", "--surface", "thumbnail", "--base", "0.03", "--mde-rel", "0.15", "--daily",
        "4000", "--guardrail", "bounce:0.02", "--start", "2026-08-01")
    tc.write_text("variant,impressions,qualified_plays,bounce\nA,24870,761,0.31\nB,31092,1138,0.36\n")
    good, out = run(HERE / "abtest.py", "analyze", ex / "th", "--data", tc, code=1)
    ok("analyze on a thumbnail plan redirects to compare and writes nothing", good and "compare" in out and
       not (ex / "th" / "RESULT.md").exists())
    good, out = run(HERE / "abtest.py", "compare", "--data", tc, "--plan", ex / "th", "--asof", "2026-09-01")
    rj = json.loads((ex / "th" / "result.json").read_text()) if (ex / "th" / "result.json").is_file() else {}
    ok("compare --plan records a descriptive result with the guardrail", good and rj.get("kind") == "descriptive" and
       rj.get("final") and "guardrail bounce" in out)
    run(HERE / "abtest.py", "plan", "nat", "--surface", "onboarding", "--native", "--primary", "d1", "--base", "0.10",
        "--mde-rel", "0.3", "--daily", "300", "--guardrail", "d7:5", "--start", "2026-08-01")
    good, out = run(HERE / "abtest.py", "record", ex / "nat", "--metric", "d1=8.02,22.03,17.4", "--guardrail", "d7=-7,2",
                    "--enrolled", "A=2900,B=2950", "--asof", "2026-09-01")
    ok("Roblox Experiments readout: primary WIN but guardrail FAIL blocks it", good and "GUARDRAIL FAIL" in out, out[-300:])
    good, out = run(HERE / "abtest.py", "peek", "--looks", "14")
    ok("peek explains inflated false wins", good and "false-positive rate" in out)

    # dash parsers + pipeline
    pv = dash.parse_value
    ok("value parsing", abs(pv("12.3%") - 0.123) < 1e-12 and pv("1,234") == 1234 and pv("R$ 1.2K") == 1200 and
       abs(pv("0:12:30") - 12.5) < 1e-9 and abs(pv("12m 30s") - 12.5) < 1e-9 and pv("-") is None)
    pdd = dash.parse_date
    ok("date parsing", str(pdd("09/21/2026", "mdy")) == "2026-09-21" and str(pdd("21/09/2026", "dmy")) == "2026-09-21"
       and str(pdd("Sep 21, 2026")) == "2026-09-21" and str(pdd("2026-09-21T00:00:00Z")) == "2026-09-21")
    ok("metric matching", dash.match_metric("Average Revenue per DAU") == "arpdau" and dash.match_metric("D7 Retention (%)") == "d7"
       and dash.match_metric("Paying Users") == "paying_users" and dash.match_metric("Daily Active Users") == "dau")
    edge = tmp / "edge"
    edge.mkdir()
    (edge / "long.csv").write_text("Date;Metric;Value\n21/09/2026;Daily Active Users;1.130\n21/09/2026;D1 Retention;11,5%\n"
                                   "22/09/2026;Revenue;R$ 1200\n")
    (edge / "tab.csv").write_text("Date\tCountry\tDAU\tPayer Conversion Rate\n2026-09-21\tTotal\t500\t1.8%\n"
                                  "2026-09-21\tUS\t300\t2.0%\n")
    d1 = dash.extract(dash.analyse(edge / "long.csv"))["daily"]
    d2 = dash.extract(dash.analyse(edge / "tab.csv"))["daily"]
    ok("long format, decimal commas, d/m dates, Total rows", d1.get("2026-09-21", {}).get("dau") == 1130 and
       abs(d1["2026-09-21"].get("d1", 0) - 0.115) < 1e-9 and d2["2026-09-21"]["dau"] == 500 and abs(d2["2026-09-21"]["payer_conversion"] - 0.018) < 1e-12, (d1, d2))
    exp_dir = tmp / "exports"
    good, _ = run(HERE / "dash.py", "demo", exp_dir)
    files = sorted(exp_dir.glob("SYNTHETIC_*.csv"))
    good2, out = run(HERE / "dash.py", "ingest", *[f for f in files if "funnel" not in f.name])
    good3, _ = run(HERE / "dash.py", "ingest", exp_dir / "SYNTHETIC_onboarding_funnel.csv", "--name", "onboarding")
    ok("ingest all synthetic shapes", good and good2 and good3 and "UNMAPPED" not in out, out[-400:])
    good, out = run(HERE / "dash.py", "memo", "--out", tmp / "memo", "--headline", "Test headline", "--action", "Test action")
    facts = json.loads((tmp / "memo" / "facts.json").read_text()) if (tmp / "memo" / "facts.json").is_file() else {}
    ok("memo builds with KPIs, gates, funnel drop, CI", good and facts.get("gates") and any("Biggest drop" in x for x in facts.get("funnels", []))
       and any("UNCLEAR" in str(r) or "PASS" in str(r) for r in facts.get("kpis", [])), out[-500:])
    html = (tmp / "memo" / "memo.html").read_text() if (tmp / "memo" / "memo.html").is_file() else ""
    ok("memo html has headline, charts, dark tokens", "Test headline" in html and html.count("<svg") >= 3 and "prefers-color-scheme" in html)
    memo_md = (tmp / "memo" / "memo.md").read_text() if (tmp / "memo" / "memo.md").is_file() else ""
    ok("synthetic inputs stamp the memo", "SYNTHETIC DATA" in memo_md.splitlines()[0] and "SYNTHETIC DATA: Test headline" in memo_md)
    spend = [r for r in facts.get("gates", []) if "weekly D1" in r[1]]
    d1g = [r for r in facts.get("gates", []) if r[0] == "spend" and r[1].startswith("D1")]
    ok("spend-gate cohort row never PASSes while the D1 gate is UNCLEAR", spend and d1g and
       not (d1g[0][4] == "UNCLEAR" and spend[0][4] == "PASS"), (spend, d1g))
    good, out = run(HERE / "dash.py", "memo", "--store", tmp / "nostore.json", code=1)
    ok("memo without a store: clean message", good and "ingest" in out)
    (tmp / "empty.csv").write_text("")
    good, out = run(HERE / "dash.py", "inspect", tmp / "empty.csv", code=1)
    ok("empty export: clean message", good and "empty" in out)
    try:
        for f in (tmp / "memo" / "charts").glob("*.svg"):
            ET.fromstring(f.read_text())
        ok("memo charts are valid SVG", True)
    except ET.ParseError as e:
        ok("memo charts are valid SVG", False, e)

    # econ
    good, out = run(HERE / "econ.py", "validate")
    ok("economy + catalogue agree with canon", good and "PASS" in out, out[-300:])
    eco = rrlib.load_json(SKILL / "presets" / "economy.json")
    eco["prices"]["coal"]["v"] = 45
    ep = tmp / "eco-drift.json"
    ep.write_text(json.dumps(eco))
    good, out = run(HERE / "econ.py", "validate", "--config", ep, code=1)
    ok("canon drift in a preset fails", good and "economy.supplies.coal" in out)
    eco = rrlib.load_json(SKILL / "presets" / "economy.json")
    eco["prices"]["coal"] = {"v": 10, "canon": "economy.supplies.coal"}
    ep.write_text(json.dumps(eco))
    good, out = run(HERE / "econ.py", "validate", "--config", ep, code=1)
    ok("a placeholder number from a canon note does not pass for the value", good and "not found" in out, out[-300:])
    good, out = run(HERE / "econ.py", "sim", "--quick", "--out", tmp / "econ")
    sim = json.loads((tmp / "econ" / "econ.json").read_text()) if (tmp / "econ" / "econ.json").is_file() else {}
    names = {x["check"] for x in sim.get("checks", [])}
    ok("sim runs with canon checks, difficulty ladder, short-of-kit and charts", good and len(names) >= 10 and
       {"harder pays more", "runs started short of the supply kit"} <= names and
       (tmp / "econ" / "econ-pacing.svg").is_file() and "harder pays more" in out, out[-500:])
    eco = rrlib.load_json(SKILL / "presets" / "economy.json")
    eco["difficulty"]["Insane"]["fare_full"] = {"v": 900, "assumed": "test"}
    eco["unlocks"][0]["price"] = {"v": 4000, "assumed": "test"}
    eco["failed_trip"]["option"] = "B"
    ep.write_text(json.dumps(eco))
    good, out = run(HERE / "econ.py", "sim", "--quick", "--config", ep, "--out", tmp / "econ-bad")
    ok("sim flags an inverted ladder, a canon override and an off-default open question", good and "INVERTED" in out and
       "overrides canon gameplay.progress.first_unlock" in out and "OQ-011 default A" in out, out[-600:])
    good, out = run(HERE / "econ.py", "sim", "--quick", "--sweep", "difficulty.Easy.fare_full=1500,1900", "--out", tmp / "sw")
    ok("sweep prints a table with its sample and writes it", good and out.count("\n| 1") >= 2 and "Sample:" in out and
       (tmp / "sw" / "sweep-difficulty.Easy.fare_full.md").is_file(), out[-300:])
    good, out = run(HERE / "econ.py", "sim", "--sweep", "difficulty.Easy.fare_ful=1500", code=1)
    ok("sweep path typo fails cleanly", good and "no key 'fare_ful'" in out)
    good, out = run(HERE / "econ.py", "ladder")
    ok("ladder prints earned R$ and USD, launch states only", good and "DevEx USD" in out and "auto_stoker |" not in out
       and "recurring" in out)
    good, out = run(HERE / "econ.py", "guard", "--sim", tmp / "econ" / "econ.json", "--out", tmp / "gate")
    g = json.loads((tmp / "gate" / "MONEY_GATE.json").read_text()) if (tmp / "gate" / "MONEY_GATE.json").is_file() else {}
    ok("gate on canon catalogue: toolbelt HOLD, auto stoker FUTURE", good and any(i["product"] == "toolbelt" for i in g.get("hold", []))
       and any(i["product"] == "auto_stoker" for i in g.get("future", [])), out[-400:])
    good, out = run(HERE / "econ.py", "guard", "--gate", code=1)
    ok("guard --gate needs a fare source", good and "--sim" in out)
    good, _ = run(HERE / "econ.py", "guard", "--sim", tmp / "econ" / "econ.json", "--out", tmp / "gate", "--gate", code=1)
    ok("guard --gate exits non-zero on FAIL", good)
    cat = rrlib.load_json(SKILL / "presets" / "catalogue.json")
    for pr in cat["products"]:
        if pr["id"] in ("express_depot", "toolbelt", "private_server"):
            pr["state"] = "hidden"
        if pr["id"] == "fare_pack_l":
            pr["fare"], pr["price_rs"] = {"v": 15000, "assumed": "test"}, {"v": 449, "assumed": "test"}
    cp = tmp / "hidden-catalogue.json"
    cp.write_text(json.dumps(cat))
    good, out = run(HERE / "econ.py", "guard", "--catalogue", cp, "--run-fare", "2000", "--out", tmp / "gate3")
    g3 = json.loads((tmp / "gate3" / "MONEY_GATE.json").read_text()) if (tmp / "gate3" / "MONEY_GATE.json").is_file() else {}
    ok("hidden products never HOLD; a price departing from canon does (M16)", good and
       not any(i["product"] in ("express_depot", "toolbelt", "private_server") for i in g3.get("hold", [])) and
       any(i["rule"] == "M16" and i["product"] == "fare_pack_l" for i in g3.get("hold", [])), out[-400:])
    cat = rrlib.load_json(SKILL / "presets" / "catalogue.json")
    cat["products"] += [
        {"id": "mystery_crate", "kind": "product", "price_rs": {"v": 25, "assumed": "test"}, "state": "live",
         "sells": "identity", "effect": "random livery", "random": True},
        {"id": "double_or_nothing", "kind": "product", "price_rs": {"v": 50, "assumed": "test"}, "state": "live",
         "sells": "time", "effect": "bet your bank on a coin flip", "stake": True},
        {"id": "revive_token", "kind": "product", "price_rs": {"v": 35, "assumed": "test"}, "state": "live",
         "sells": "time", "effect": "revive the train once", "prompt": {"where": "fail_screen", "after_run": 1}},
        {"id": "rank_boost", "kind": "pass", "price_rs": {"v": 99, "assumed": "test"}, "state": "live",
         "sells": "status", "effect": "x1.5 Daily Line score", "affects_rank": True}]
    cp = tmp / "bad-catalogue.json"
    cp.write_text(json.dumps(cat))
    good, out = run(HERE / "econ.py", "guard", "--catalogue", cp, "--run-fare", "2000", "--out", tmp / "gate2")
    g2 = json.loads((tmp / "gate2" / "MONEY_GATE.json").read_text()) if (tmp / "gate2" / "MONEY_GATE.json").is_file() else {}
    rules = {(i["product"], i["rule"]) for i in g2.get("blocking", []) + g2.get("hold", [])}
    ok("bad catalogue: random, stake, revive text, early prompt, 3 placements, rank all caught",
       g2.get("verdict") == "FAIL" and {("mystery_crate", "M05"), ("double_or_nothing", "M12"), ("revive_token", "M02"),
                                        ("revive_token", "M06"), ("(all)", "M06"), ("rank_boost", "M08")} <= rules, sorted(rules))

    # svgchart demo
    good, _ = run(HERE / "svgchart.py", "--demo", tmp / "svg")
    try:
        ok("svgchart demo is valid SVG", good and all(ET.fromstring(f.read_text()) is not None for f in (tmp / "svg").glob("*.svg")))
    except ET.ParseError as e:
        ok("svgchart demo is valid SVG", False, e)

    root = rrlib.data_root()
    print(f"  data root for real work: {root}" + ("" if rrlib.project_root() and str(root).startswith(
        str(rrlib.project_root())) else "  (outside a project repo: in the cloud a new session will not find it; "
                                        "set RR_DATA_ROOT to a folder in the repo)"))
    for d in (HERE, SKILL):
        shutil.rmtree(d / "__pycache__", ignore_errors=True)
    if a.keep:
        print(f"kept {tmp}")
    else:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, c in res if not c]
    print(f"selftest: {len(res) - len(failed)}/{len(res)} passed" + (f"; failed: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
