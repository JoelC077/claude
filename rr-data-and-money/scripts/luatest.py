#!/usr/bin/env python3
"""Test RR_Analytics.lua + the generated RR_AnalyticsPlan.lua in a real Lua 5.1 VM with stubbed Roblox services.

  luatest.py [--plan-lua FILE] [-v]

Checks: syntax (node luaparse, Lua 5.1 subset), onboarding once per player and persisted through the store,
recurring funnel step numbers, economy validation (NaN, <= 0, unplanned sku/type), progression enums and range,
custom-event enum coercion and numeric buckets, per-player rate limits, experiment arms identical to the Python
mirror (abtest.assign_arm) for 5,000 UserIds, one exposure event per player, experiment tags in the next free
custom field, pcall safety when AnalyticsService throws, debug (Studio) mode prints instead of sending.
Needs lupa (pip install --target ~/.cache/rr-tools/py lupa); node luaparse is optional (npm i --prefix
~/.cache/rr-tools luaparse). Missing tools are reported as SKIP. Exit 0 = all passed. Stubs prove logic, not Roblox.
"""
import argparse, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
TOOLS = Path.home() / ".cache" / "rr-tools"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TOOLS / "py"))
import abtest  # noqa: E402

STUBS = r"""
local T = { calls = {}, now = 0, fail = false, warns = 0, prints = 0 }
RRT = T
warn = function(...) T.warns = T.warns + 1 end
print = function(...) T.prints = T.prints + 1 end
local function item(name) return { Name = name } end
Enum = {
  AnalyticsCustomFieldKeys = { CustomField01 = item("CustomField01"), CustomField02 = item("CustomField02"),
                               CustomField03 = item("CustomField03") },
  AnalyticsEconomyFlowType = { Source = item("Source"), Sink = item("Sink") },
  AnalyticsProgressionType = { Start = item("Start"), Complete = item("Complete"), Fail = item("Fail") },
  AnalyticsEconomyTransactionType = { IAP = item("IAP"), Shop = item("Shop"), Gameplay = item("Gameplay"),
    ContextualPurchase = item("ContextualPurchase"), TimedReward = item("TimedReward"), Onboarding = item("Onboarding") },
}
local function rec(name)
  return function(self, ...)
    if T.fail then error("service down") end
    table.insert(T.calls, { name, ... })
  end
end
T.svc = {
  LogOnboardingFunnelStepEvent = rec("onb"), LogFunnelStepEvent = rec("funnel"), LogEconomyEvent = rec("econ"),
  LogProgressionEvent = rec("prog"), LogCustomEvent = rec("custom"),
}
T.store = { data = {} }
T.store.get = function(p, k) return T.store.data[p.UserId .. k] end
T.store.set = function(p, k, v) T.store.data[p.UserId .. k] = v end
function T.P(id) return { UserId = id, Name = "p" .. id } end
function T.reset() T.calls = {} end
function T.last() return T.calls[#T.calls] end
game = { GetService = function(_, n)
  if n == "Players" then return { PlayerRemoving = { Connect = function() end } } end
  if n == "RunService" then return { IsStudio = function() return false end } end
  return nil
end }
"""


def lua_runtime():
    try:
        from lupa import lua51
    except ImportError:
        return None
    return lua51.LuaRuntime(unpack_returned_tuples=True)


def luaparse(files):
    lp = TOOLS / "node_modules" / "luaparse"
    if not shutil.which("node") or not lp.is_dir():
        return "SKIP", "node or luaparse missing (npm i --prefix ~/.cache/rr-tools luaparse)"
    js = ("const lp=require(process.argv[1]);const fs=require('fs');let bad=0;for(const f of process.argv.slice(2)){try{"
          "lp.parse(fs.readFileSync(f,'utf8'),{luaVersion:'5.1'});}catch(e){bad++;console.log(f+': '+e.message);}}"
          "process.exit(bad?1:0);")
    r = subprocess.run(["node", "-e", js, str(lp), *map(str, files)], capture_output=True, text=True)
    return ("PASS" if r.returncode == 0 else "FAIL"), (r.stdout + r.stderr).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan-lua", default=str(SKILL / "assets" / "luau" / "RR_AnalyticsPlan.lua"))
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    mod = SKILL / "assets" / "luau" / "RR_Analytics.lua"
    hooks = SKILL / "assets" / "luau" / "RR_AnalyticsHooks.lua"
    results = []

    def ok(name, cond, detail=""):
        results.append((name, bool(cond)))
        if a.v or not cond:
            print(f"  {'ok  ' if cond else 'FAIL'} {name} {detail}")

    st, msg = luaparse([mod, Path(a.plan_lua), hooks])
    print(f"luaparse: {st} {msg if st != 'PASS' else ''}".rstrip())
    if st == "FAIL":
        return 1
    L = lua_runtime()
    if L is None:
        print("SKIP luatest: lupa not installed (pip install --target ~/.cache/rr-tools/py lupa)")
        return 0
    L.execute(STUBS)
    plan = L.execute(Path(a.plan_lua).read_text(encoding="utf-8"))
    A = L.execute(mod.read_text(encoding="utf-8"))
    L.globals().PLAN = plan
    L.globals().A = A
    L.execute("RRT.players = 50; A.init(PLAN, { service = RRT.svc, store = RRT.store, debug = false, "
              "clock = function() return RRT.now end, playerCount = function() return RRT.players end })")
    run = L.execute

    # onboarding
    run('P1 = RRT.P(101); RRT.reset(); A.onboarding(P1, "join"); A.onboarding(P1, "join"); A.onboarding(P1, "pulled_lever")')
    ok("onboarding once per step", run("return #RRT.calls") == 2)
    ok("onboarding step index", run("return RRT.calls[2][3]") == 4 and run("return RRT.calls[2][4]") == "Pulled lever")
    run('A.forget(P1); RRT.reset(); A.onboarding(P1, "join"); A.onboarding(P1, "run_end"); A.onboarding(P1, "first_bank")')
    ok("onboarding persisted through store (rejoin)", run("return #RRT.calls") == 2 and run("return RRT.calls[1][3]") == 6)
    ok("a step reached later (first bank on run 2) still logs once", run("return RRT.calls[2][3]") == 5 and
       run('return A.onboarding(P1, "first_bank")') is False)
    run('RRT.reset(); A.onboarding(P1, "nope")')
    ok("unknown onboarding step dropped", run("return #RRT.calls") == 0 and run("return A.stats().dropped") >= 1)

    # funnel
    run('P2 = RRT.P(202); RRT.reset(); A.funnel(P2, "trip", "trip-9", "departed")')
    c = run("return RRT.calls[1]")
    ok("funnel args", c[1] == "funnel" and c[3] == "trip" and c[4] == "trip-9" and c[5] == 3 and c[6] == "Departed")
    ok("unknown funnel dropped", run('return A.funnel(P2, "nope", "x", "departed")') is False)

    # economy
    run('RRT.reset(); A.source(P2, 1250, 3000, "Gameplay", "fare_bank", { difficulty = "Hard" })')
    c = run("return RRT.calls[1]")
    ok("economy source args", c[1] == "econ" and c[3].Name == "Source" and c[4] == "Coins" and c[5] == 1250
       and c[6] == 3000 and c[7] == "Gameplay" and c[8] == "fare_bank" and c[9]["CustomField01"] == "Hard")
    bad = run('return { A.sink(P2, 0/0, 10, "Shop", "coal"), A.sink(P2, -5, 10, "Shop", "coal"), '
              'A.sink(P2, 40, 10, "Shop", "gold"), A.sink(P2, 40, 10, "Bribe", "coal"), A.sink(P2, 40, 1/0, "Shop", "coal") }')
    ok("economy rejects NaN, <= 0, unplanned sku/type, inf balance", all(bad[i] is False for i in range(1, 6)))
    run('RRT.reset(); A.sink(P2, 40, 2960, "Shop", "coal", { difficulty = "Weird" })')
    ok("enum coerced to other", run('return RRT.calls[1][9]["CustomField01"]') == "other")

    # progression
    run('RRT.reset(); A.progress(P2, "trip", "Fail", 3, nil, { crew = 4, reason = "stall" })')
    c = run("return RRT.calls[1]")
    ok("progression args + buckets", c[3] == "trip" and c[4].Name == "Fail" and c[5] == 3 and c[6] == "Hard"
       and c[7]["CustomField01"] == "3-5" and c[7]["CustomField02"] == "stall")
    ok("progression level range", run('return A.progress(P2, "trip", "Start", 9)') is False)
    ok("progression status check", run('return A.progress(P2, "trip", "Won", 1)') is False)

    # custom events + buckets + unplanned
    run('RRT.reset(); A.event(P2, "lever_pulled", 3.2, { choice = "risky", time_left = 3.2, crew = 1 })')
    f = run("return RRT.calls[1][5]")
    ok("custom event fields", f["CustomField01"] == "risky" and f["CustomField02"] == "2-5" and f["CustomField03"] == "<2")
    run('RRT.reset(); A.event(P2, "lever_pulled", 0/0, { choice = "safe", time_left = 99 })')
    c = run("return RRT.calls[1]")
    ok("NaN value -> 1, top bucket, missing field none", c[4] == 1 and c[5]["CustomField02"] == "8+" and c[5]["CustomField03"] == "none")
    ok("unplanned event dropped", run('return A.event(P2, "free_robux", 1)') is False)

    # rate limit (lever_pulled max 12/min)
    run('P3 = RRT.P(303); RRT.reset(); for i = 1, 40 do A.event(P3, "lever_pulled", 1, { choice = "safe" }) end')
    n1 = run("return #RRT.calls")
    run('RRT.now = RRT.now + 60; for i = 1, 40 do A.event(P3, "lever_pulled", 1, { choice = "safe" }) end')
    n2 = run("return #RRT.calls")
    ok("rate limit caps a burst and refills per minute", n1 == 12 and n2 == 24, f"({n1}, {n2})")

    # server-wide budget: 20 x players + 20 per minute
    run('RRT.now = RRT.now + 120; RRT.players = 1; RRT.reset(); for i = 1, 10 do for k = 1, 6 do '
        'A.event(RRT.P(7000 + i), "crisis_end", 5, { kind = "coal_low" }) end end')
    ng = run("return #RRT.calls")
    ok("server-wide rate budget (1 player -> 40/min)", ng == 40, f"({ng})")
    run('RRT.now = RRT.now + 120; RRT.players = 50')

    # experiments: parity with python, exposure once, tag slot
    run('PLAN.experiments.example_onboarding_hint.active = true')
    exp = run("return PLAN.experiments.example_onboarding_hint")
    arms = [exp.arms[i] for i in range(1, len(exp.arms) + 1)]
    weights = [exp.weights[i] for i in range(1, len(exp.weights) + 1)]
    mism = 0
    for i in range(5000):
        uid = 1000 + i * 7919 + (i % 13) * 1000003
        la = run(f'return A.arm(RRT.P({uid}), "example_onboarding_hint")')
        if la != abtest.assign_arm(exp.salt, arms, weights, uid):
            mism += 1
    ok("experiment arms identical to Python for 5,000 UserIds", mism == 0, f"({mism} mismatches)")
    ok("large UserId parity", run('return A.arm(RRT.P(5123456789), "example_onboarding_hint")') ==
       abtest.assign_arm(exp.salt, arms, weights, 5123456789))
    run('P4 = RRT.P(404); RRT.reset(); A.expose(P4, "example_onboarding_hint"); A.expose(P4, "example_onboarding_hint")')
    c = run("return RRT.calls")
    ok("one exposure event per player", len(c) == 1 and c[1][3] == "exp_exposure" and c[1][5]["CustomField01"] ==
       "example_onboarding_hint" and c[1][5]["CustomField02"] in arms)
    run('RRT.reset(); A.onboarding(P4, "join")')
    ok("experiment tag in next free field", str(run('return RRT.calls[1][5]["CustomField01"]')).startswith("example_onboarding_hint:"))
    ok("inactive experiment returns nil", run('PLAN.experiments.example_onboarding_hint.active = false; '
                                             'return A.arm(P4, "example_onboarding_hint")') is None)

    # hooks module (game moments -> several calls)
    L.globals().script = L.table_from({"Parent": L.table_from({"RR_Analytics": "RR_Analytics"})})
    run("require = function(x) return A end")
    H = L.execute(hooks.read_text(encoding="utf-8"))
    L.globals().H = H
    run('RRT.reset(); H.runEnded({ RRT.P(601), RRT.P(602), RRT.P(603) }, "stall", 3, 212, "trip-1")')
    kinds = [run(f"return RRT.calls[{i}][1]") for i in range(1, run("return #RRT.calls") + 1)]
    ok("hook runEnded: 3 x (onboarding, run_end, progression)", kinds.count("onb") == 3 and kinds.count("custom") == 3
       and kinds.count("prog") == 3 and "funnel" not in kinds)
    ok("hook runEnded fields", run('return RRT.calls[2][5]["CustomField02"]') == "Hard" and
       run('return RRT.calls[3][4].Name') == "Fail")
    run('RRT.reset(); H.unlockBought(RRT.P(604), 2, 2500, 120)')
    ok("hook unlockBought: sink loco_2 + locomotives level 1", run("return RRT.calls[1][8]") == "loco_2" and
       run("return RRT.calls[2][5]") == 1 and run("return RRT.calls[2][6]") == "loco_2")

    # pcall safety
    run('RRT.fail = true; RRT.reset()')
    safe = run('local ok, r = pcall(A.event, RRT.P(505), "run_end", 100, { reason = "stall" }); return ok and r == false')
    ok("service error never propagates", safe and run("return A.stats().errors") >= 1)
    run('RRT.fail = false')

    # debug mode prints
    L.execute(STUBS)
    A2 = L.execute(mod.read_text(encoding="utf-8"))
    L.globals().A2 = A2
    L.globals().PLAN2 = L.execute(Path(a.plan_lua).read_text(encoding="utf-8"))
    run('A2.init(PLAN2, { service = RRT.svc, debug = true }); A2.event(RRT.P(1), "run_end", 10, { reason = "arrived" })')
    ok("debug mode prints and does not send", run("return RRT.prints") == 1 and run("return #RRT.calls") == 0)

    bad = [n for n, c in results if not c]
    print(f"luatest: {len(results) - len(bad)}/{len(results)} passed" + (f"; failed: {', '.join(bad)}" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
