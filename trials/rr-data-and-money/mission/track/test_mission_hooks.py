#!/usr/bin/env python3
"""Mission-local check of the added hooks (tripStep, terminalOpened, crateResolved) against the generated plan,
reusing rr-data-and-money's luatest stubs (found by glob). luatest.py itself always loads the skill's own hooks file.
  python3 test_mission_hooks.py"""
import glob, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
cands = sorted(glob.glob(os.path.expanduser("~/.claude/skills/**/rr-data-and-money/scripts/luatest.py"), recursive=True)
               + glob.glob("/home/user/**/rr-data-and-money/scripts/luatest.py", recursive=True))
cands = [c for c in cands if "/trials/" not in c]
sys.path.insert(0, str(Path(cands[0]).parent))
import luatest  # noqa: E402
L = luatest.lua_runtime()
if L is None:
    print("SKIP: lupa missing"); sys.exit(0)
src = HERE / "src"
L.execute(luatest.STUBS)
L.globals().PLAN = L.execute((src / "RR_AnalyticsPlan.lua").read_text())
L.globals().A = L.execute((src / "RR_Analytics.lua").read_text())
run = L.execute
run("RRT.players = 12; A.init(PLAN, { service = RRT.svc, store = RRT.store, debug = false, "
    "clock = function() return RRT.now end, playerCount = function() return RRT.players end })")
L.globals().script = L.table_from({"Parent": L.table_from({"RR_Analytics": "RR_Analytics"})})
run("require = function(x) return A end")
L.globals().H = L.execute((src / "RR_AnalyticsHooks.lua").read_text())
res = []
def ok(name, cond):
    res.append(cond); print(f"  {'ok  ' if cond else 'FAIL'} {name}")
run('P = RRT.P(701); RRT.reset(); H.tripStep(P, "trip-7", "queued"); H.tripStep(P, "trip-7", "boarded"); H.tripStep(P, "trip-7", "departed")')
ok("tripStep logs trip steps 1-3", [run(f"return RRT.calls[{i}][5]") for i in (1, 2, 3)] == [1, 2, 3])
run('RRT.reset(); H.terminalOpened(P, "term-1")')
ok("terminalOpened -> supply step 1", run("return RRT.calls[1][3]") == "supply" and run("return RRT.calls[1][5]") == 1)
run('RRT.reset(); H.crateResolved(P, "coal", "fetched", 7.5, "Hard", "term-1")')
ok("crateResolved fetched -> event + supply step 3", run("return #RRT.calls") == 2 and run("return RRT.calls[1][3]") == "crate_resolved"
   and run("return RRT.calls[2][5]") == 3)
ok("crate fields in order", run('return RRT.calls[1][5]["CustomField01"]') == "coal"
   and run('return RRT.calls[1][5]["CustomField02"]') == "fetched" and run('return RRT.calls[1][5]["CustomField03"]') == "Hard")
run('RRT.reset(); H.crateResolved(P, "medkit", "slid_off", 20, "Insane", "term-2")')
ok("slid_off -> event only, no fetched step", run("return #RRT.calls") == 1)
print(f"mission hooks: {sum(res)}/{len(res)} passed"); sys.exit(0 if all(res) else 1)
