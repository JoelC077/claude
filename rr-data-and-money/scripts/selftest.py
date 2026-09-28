#!/usr/bin/env python3
"""Self-test for rr-data-and-money: every script, on synthetic data, in a temp data root (nothing else is touched).

  selftest.py [-v] [--keep]

Covers statlib reference values (textbook numbers), track.py (canon funnel, negative plans, build, scan), luatest.py
(Lua VM), abtest.py (plan, NOT DONE, verdicts, guardrail, SRM, edited plan), dash.py (parsers, ingest, memo,
charts), econ.py (validate, canon drift, sim, ladder, guard on the canon catalogue and on a deliberately bad one),
svgchart XML validity and --help on every script. Exit 0 = all passed.
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
    ok("scan passes the shipped Luau", good and "PASS" in out, out[-300:])

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
    good, out = run(HERE / "econ.py", "sim", "--quick", "--out", tmp / "econ")
    sim = json.loads((tmp / "econ" / "econ.json").read_text()) if (tmp / "econ" / "econ.json").is_file() else {}
    ok("sim runs with canon checks and charts", good and len(sim.get("checks", [])) >= 8 and
       (tmp / "econ" / "econ-pacing.svg").is_file() and "time to first upgrade" in out, out[-500:])
    good, out = run(HERE / "econ.py", "sim", "--sweep", "difficulty.Easy.fare_full=1500,1900")
    ok("sweep prints a comparison table", good and out.count("\n| 1") >= 2, out[-300:])
    good, out = run(HERE / "econ.py", "ladder")
    ok("ladder prints earned R$ and USD", good and "DevEx USD" in out)
    good, out = run(HERE / "econ.py", "guard", "--sim", tmp / "econ" / "econ.json", "--out", tmp / "gate")
    g = json.loads((tmp / "gate" / "MONEY_GATE.json").read_text()) if (tmp / "gate" / "MONEY_GATE.json").is_file() else {}
    ok("gate on canon catalogue: toolbelt HOLD, auto stoker FUTURE", good and any(i["product"] == "toolbelt" for i in g.get("hold", []))
       and any(i["product"] == "auto_stoker" for i in g.get("future", [])), out[-400:])
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
