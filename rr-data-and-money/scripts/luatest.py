#!/usr/bin/env python3
"""Test RR_Analytics.lua + RR_AnalyticsHooks.lua + the generated RR_AnalyticsPlan.lua in a real Lua 5.1 VM with
stubbed Roblox services.

  luatest.py [--src DIR] [--plan-lua FILE] [--gate] [-v]

--src DIR tests the copies the owner ships (DIR/RR_Analytics.lua, RR_AnalyticsHooks.lua, RR_AnalyticsPlan.lua);
default: the skill's assets/luau. --gate: exit 3 when tools are missing (SKIP), for pre-flight use.
Checks: syntax (node luaparse, Lua 5.1 subset), onboarding once per player and persisted through the store,
recurring funnel step numbers, economy validation (NaN, <= 0, unplanned sku/type), progression enums and range,
custom-event enum coercion and numeric buckets, per-player and per-server rate limits, experiment arms identical to
the Python mirror (abtest.assign_arm) for 5,000 UserIds (on an injected test experiment, so any real plan works),
one exposure event per player, experiment tags in the next free custom field, pcall safety when AnalyticsService
throws, debug (Studio) mode prints; hooks: crew-wide steps for every crew member, supply steps on the orderer when a
crewmate fetches, purchase steps sharing one prompt id, unlock ids to progression levels, and a scripted two-player
trip through every hook that exists with nothing dropped.
Needs lupa (pip install --target ~/.cache/rr-tools/py lupa); node luaparse is optional (npm i --prefix
~/.cache/rr-tools luaparse). Missing tools are reported as SKIP. Exit 0 = all passed. Stubs prove logic, not Roblox.
"""
import sys; sys.dont_write_bytecode = True  # never write __pycache__ into the skill
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
    ap.add_argument("--src", help="folder with the owner's RR_Analytics.lua, RR_AnalyticsHooks.lua, RR_AnalyticsPlan.lua")
    ap.add_argument("--plan-lua", help="generated plan (default: SRC/RR_AnalyticsPlan.lua)")
    ap.add_argument("--gate", action="store_true", help="exit 3 on SKIP (missing tools) instead of 0")
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    src = Path(a.src) if a.src else SKILL / "assets" / "luau"
    find = lambda stem: next((p for p in (src / f"{stem}.lua", src / f"{stem}.luau") if p.is_file()), src / f"{stem}.lua")  # noqa: E731
    mod, hooks = find("RR_Analytics"), find("RR_AnalyticsHooks")
    a.plan_lua = a.plan_lua or str(find("RR_AnalyticsPlan"))
    missing = [str(p) for p in (mod, Path(a.plan_lua)) if not p.is_file()]
    if missing:
        print(f"FAIL luatest: missing {', '.join(missing)} (build the plan with track.py build --out {src})")
        return 1
    print(f"luatest on {mod.parent}" + (f" with plan {a.plan_lua}" if Path(a.plan_lua).parent != mod.parent else ""))
    results = []

    def ok(name, cond, detail=""):
        results.append((name, bool(cond)))
        if a.v or not cond:
            print(f"  {'ok  ' if cond else 'FAIL'} {name} {detail}")

    st, msg = luaparse([mod, Path(a.plan_lua)] + ([hooks] if hooks.is_file() else []))
    print(f"luaparse: {st} {msg if st != 'PASS' else ''}".rstrip())
    if st == "FAIL":
        return 1
    L = lua_runtime()
    if L is None:
        print("SKIP luatest: lupa not installed (pip install --target ~/.cache/rr-tools/py lupa)")
        return 3 if a.gate else 0
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

    # server-wide budget: 20 x players per minute (sums to 20 x CCU across servers: inside 120 + 20 x CCU)
    run('RRT.now = RRT.now + 120; RRT.players = 1; RRT.reset(); for i = 1, 10 do for k = 1, 6 do '
        'A.event(RRT.P(7000 + i), "crisis_end", 5, { kind = "coal_low" }) end end')
    ng = run("return #RRT.calls")
    ok("server-wide rate budget (1 player -> 20/min)", ng == 20, f"({ng})")
    run('RRT.now = RRT.now + 120; RRT.players = 50')

    # experiments: parity with python, exposure once, tag slot. A test experiment is injected (and every other one
    # switched off) so this works on any real plan, with or without the shipped example.
    run('for k, x in pairs(PLAN.experiments) do x.active = false end; '
        'PLAN.experiments.luatest_exp = { arms = { "A", "B" }, weights = { 50, 50 }, salt = "luatest-2026", '
        'active = true, tag = { "onboarding" } }')
    exp = run("return PLAN.experiments.luatest_exp")
    arms = [exp.arms[i] for i in range(1, len(exp.arms) + 1)]
    weights = [exp.weights[i] for i in range(1, len(exp.weights) + 1)]
    mism = 0
    for i in range(5000):
        uid = 1000 + i * 7919 + (i % 13) * 1000003
        la = run(f'return A.arm(RRT.P({uid}), "luatest_exp")')
        if la != abtest.assign_arm(exp.salt, arms, weights, uid):
            mism += 1
    ok("experiment arms identical to Python for 5,000 UserIds", mism == 0, f"({mism} mismatches)")
    ok("large UserId parity", run('return A.arm(RRT.P(5123456789), "luatest_exp")') ==
       abtest.assign_arm(exp.salt, arms, weights, 5123456789))
    run('P4 = RRT.P(404); RRT.reset(); A.expose(P4, "luatest_exp"); A.expose(P4, "luatest_exp")')
    c = run("return RRT.calls")
    ok("one exposure event per player", len(c) == 1 and c[1][3] == "exp_exposure" and c[1][5]["CustomField01"] ==
       "luatest_exp" and c[1][5]["CustomField02"] in arms)
    run('RRT.reset(); A.onboarding(P4, "join")')
    ok("experiment tag in next free field", str(run('return RRT.calls[1][5]["CustomField01"]')).startswith("luatest_exp:"))
    ok("inactive experiment returns nil", run('PLAN.experiments.luatest_exp.active = false; '
                                             'return A.arm(P4, "luatest_exp")') is None)

    # hooks module (game moments -> several calls)
    if not hooks.is_file():
        print(f"  note: no {hooks.name} in {src}: hook checks skipped")
    else:
        L.globals().script = L.table_from({"Parent": L.table_from({"RR_Analytics": "RR_Analytics"})})
        run("require = function(x) return A end")
        H = L.execute(hooks.read_text(encoding="utf-8"))
        L.globals().H = H
        has = lambda name: run(f"return H.{name} ~= nil")  # noqa: E731
        calls = lambda: [run(f"return RRT.calls[{i}]") for i in range(1, run("return #RRT.calls") + 1)]  # noqa: E731

        def hook_case(name, code, cond):
            """Run a hook scenario; a Lua error is a failed check (old or edited hooks), never a traceback."""
            try:
                run("RRT.reset(); " + code)
                ok(name, cond())
            except Exception as e:  # lupa.LuaError and friends
                ok(name, False, f"(Lua error: {str(e).splitlines()[0][:160]})")
        run("RRT.now = RRT.now + 120")
        hook_case("hook runEnded: 3 x (onboarding, run_end, progression Fail)",
                  'H.runEnded({ RRT.P(601), RRT.P(602), RRT.P(603) }, "stall", 3, 212, "trip-1")',
                  lambda: [c[1] for c in calls()].count("onb") == 3 and [c[1] for c in calls()].count("custom") == 3 and
                  [c[1] for c in calls()].count("prog") == 3 and "funnel" not in [c[1] for c in calls()] and
                  run('return RRT.calls[2][5]["CustomField02"]') == "Hard" and run('return RRT.calls[3][4].Name') == "Fail")
        hook_case("hook runEnded arrived: every crew member reaches 'arrived'",
                  'H.runEnded({ RRT.P(611), RRT.P(612) }, "arrived", 1, 250, "trip-2")',
                  lambda: [c[6] for c in calls() if c[1] == "funnel"] == ["Arrived", "Arrived"])
        for need, name, code, cond in (
            ("forkResolved", "hook forkResolved: first_fork for the whole crew",
             'H.forkResolved({ RRT.P(621), RRT.P(622), RRT.P(623) }, "trip-3", true)',
             lambda: len(calls()) == 3 and all(c[3] == "trip" and c[6] == "First fork" for c in calls())),
            ("tripDeparted", "hook tripDeparted: departed + progression Start per crew member",
             'H.tripDeparted({ RRT.P(631), RRT.P(632) }, "trip-4", 2)',
             lambda: sum(1 for c in calls() if c[1] == "funnel" and c[5] == 3) == 2 and
             sum(1 for c in calls() if c[1] == "prog" and c[4].Name == "Start" and c[6] == "Medium") == 2),
            ("crateResolved", "hook crateResolved: funnel 'fetched' on the orderer's session, event on the fetcher",
             'H.crateResolved(RRT.P(701), RRT.P(702), "coal", "fetched", 14, "Easy", "sess-9")',
             lambda: any(c[1] == "funnel" and c[2].UserId == 701 and c[4] == "sess-9" and c[5] == 3 for c in calls()) and
             any(c[1] == "custom" and c[2].UserId == 702 and c[3] == "crate_resolved" for c in calls())),
            ("purchasePrompted", "hook purchase flow: prompt_shown, accepted, granted share one prompt id (granted once)",
             'PP = RRT.P(801); H.purchasePrompted(PP, 1234); H.purchaseAccepted(PP, 1234); H.purchaseGranted(PP, 1234); '
             'H.purchaseGranted(PP, 1234)',
             lambda: [c[5] for c in calls()] == [1, 2, 3] and len({c[4] for c in calls()}) == 1),
        ):
            if has(need):
                hook_case(name, code, cond)
            else:
                ok(name, False, f"(no Hooks.{need}: add it from the skill's RR_AnalyticsHooks.lua)")
        hook_case("hook unlockBought: sink loco_2 + locomotives level 1", 'H.unlockBought(RRT.P(604), "loco_2", 2500, 120)',
                  lambda: run("return RRT.calls[1][8]") == "loco_2" and run("return RRT.calls[2][5]") == 1 and
                  run("return RRT.calls[2][6]") == "loco_2")
        hook_case("hook unlockBought: numeric id still means loco_N", 'H.unlockBought(RRT.P(605), 3, 9000, 50)',
                  lambda: run("return RRT.calls[1][8]") == "loco_3")
        if run('return PLAN.progression.lines ~= nil'):
            hook_case("hook unlockBought: line_2 -> lines level 1", 'H.unlockBought(RRT.P(606), "line_2", 16000, 10)',
                      lambda: run("return RRT.calls[2][3]") == "lines" and run("return RRT.calls[2][5]") == 1)
        # a scripted two-player trip through every hook that exists: nothing may be dropped as unplanned
        d0 = run("return A.stats().dropped")
        hook_case("scripted two-player trip through every hook: nothing dropped as unplanned", r"""RRT.now = RRT.now + 600
          local p1, p2 = RRT.P(901), RRT.P(902)
          local crew = { p1, p2 }
          local function call(name, ...) if H[name] then H[name](...) end end
          call("playerJoined", p1); call("playerJoined", p2)
          call("tripQueued", p1, "t9"); call("tripQueued", p2, "t9")
          call("tripBoarded", p1, "t9"); call("tripBoarded", p2, "t9"); call("tripDeparted", crew, "t9", 4)
          call("toolPickedUp", p1); call("coalShovelled", p1); call("leverCommitted", p2, "risky", 3.1, 2)
          call("forkResolved", crew, "t9", true)
          call("terminalOpened", p1, "s1"); call("orderAccepted", p1, "coal", 40, 960, "Insane", "s1")
          call("crateResolved", p1, p2, "coal", "fetched", 11, "Insane", "s1")
          call("stationPaid", p1, 1800, 2760, "Insane", "t9", true); call("stationPaid", p2, 1800, 1800, "Insane", "t9", true)
          call("recoveryCharged", p2, 5, 1795, "Insane"); call("crisisEnded", p1, "pressure_high", "fixed", 9, 2)
          call("runEnded", crew, "arrived", 4, 437, "t9"); call("resultsAction", p1, "requeue", 6)
          call("unlockBought", p1, "loco_2", 2500, 260); call("liveryBought", p2, 800, 995)
          call("purchasePrompted", p2, 42); call("purchaseAccepted", p2, 42); call("purchaseGranted", p2, 42)
          call("farePackGranted", p2, "fare_pack_s", 2500, 3495); call("promoRedeemed", p1, 100, 360)
          call("playerLeft", p2, "results", 12, "Insane")""",
                  lambda: run("return A.stats().dropped") - d0 == 0)

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
