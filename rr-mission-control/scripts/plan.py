#!/usr/bin/env python3
"""rr-mission-control plan: validate a task DAG, print parallel waves and a token estimate.

  plan.py check PLAN.json [--mission mission.md] [--budget N]
  plan.py table                      # print the cost table used for estimates

PLAN.json:
{ "mission": "260927-depot-buildings",
  "tasks": [
    {"id": "T1", "do": "Depot build v1", "deps": ["T0"], "role": "maker",
     "model": "strongest", "effort": "high", "kind": "v1",
     "reqs": ["R2","R6"], "out": "critique-depot/round-1/build.py",
     "done_when": "build.py rebuilds from empty scene; 4 milestone renders"} ] }

role:  orchestrator | scout | maker | script | critic | exporter
kind:  maker: v1 | fix   critic: full | delta | final   exporter: continued (default) | fresh
Checks: unique ids, deps exist, no cycles, required fields, critic/maker not on a
cheap model, critic kinds ordered (full before delta/final), and with --mission
every R-id in mission.md (except noise/superseded rows) is referenced by a task.
Exit 0 OK, 1 problems. Stdlib only.
"""
import argparse, json, re, sys

# Measured / estimated tokens per task (see references/agent-orders.md).
COST = {
    ("orchestrator", "-"): 8000,
    ("scout", "-"): 15000,
    ("maker", "v1"): 70000,
    ("maker", "fix"): 25000,
    ("script", "-"): 0,
    ("critic", "full"): 140000,    # 90-190k measured; ~92k with design-critic agent
    ("critic", "delta"): 35000,    # continued: new tokens only
    ("critic", "final"): 120000,
    ("exporter", "continued"): 30000,  # continued maker: new tokens only
    ("exporter", "fresh"): 70000,      # fresh agent pays the ~48k base
}
DESIGN_CRITIC_SAVING = 48000
CHEAP = re.compile(r"haiku|sonnet|small|cheap|mini", re.I)
REQ = ("id", "do", "deps", "role", "model", "effort", "done_when")


def load(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception as e:
        print(f"cannot read {p}: {e}"); sys.exit(1)


def waves(tasks):
    deps = {t["id"]: set(t.get("deps", [])) for t in tasks}
    done, out = set(), []
    while len(done) < len(deps):
        ready = sorted([i for i, d in deps.items() if i not in done and d <= done],
                       key=lambda x: (len(x), x))
        if not ready:
            return out, sorted(set(deps) - done)
        out.append(ready); done |= set(ready)
    return out, []


def est(t, design_critic):
    role = t.get("role", "")
    kind = t.get("kind", "-") if role in ("maker", "critic") else "-"
    if role == "exporter":
        kind = "fresh" if t.get("kind") == "fresh" else "continued"
    c = COST.get((role, kind))
    if c is None:
        return None
    if role == "critic" and kind in ("full", "final") and design_critic:
        c -= DESIGN_CRITIC_SAVING
    return c * int(t.get("repeat", 1))


def r_ids(mission_md):
    ids = []
    for ln in open(mission_md, encoding="utf-8"):
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if ln.strip().startswith("|") and cells and re.fullmatch(r"R\*?\d+", cells[0]):
            row = " ".join(cells).lower()
            if re.search(r"\b(noise|superseded)\b", row):
                continue
            ids.append(cells[0])
    return ids


def cmd_check(a):
    plan = load(a.plan)
    tasks = plan.get("tasks", [])
    probs, warn = [], []
    ids = [t.get("id") for t in tasks]
    for d in {i for i in ids if ids.count(i) > 1}:
        probs.append(f"duplicate id {d}")
    idset = set(ids)
    for t in tasks:
        tid = t.get("id", "?")
        for k in REQ:
            if k not in t or t[k] in ("", None):
                probs.append(f"{tid}: missing '{k}'")
        for d in t.get("deps", []):
            if d not in idset:
                probs.append(f"{tid}: unknown dep {d}")
        if t.get("role") in ("critic", "maker") and CHEAP.search(str(t.get("model", ""))):
            probs.append(f"{tid}: {t['role']} on cheap model '{t['model']}' (judgement stays strongest)")
        if t.get("role") not in {r for r, _ in COST}:
            probs.append(f"{tid}: unknown role '{t.get('role')}'")
        if t.get("role") in ("maker", "critic") and est(t, False) is None:
            probs.append(f"{tid}: {t['role']} needs kind ({'v1|fix' if t['role']=='maker' else 'full|delta|final'})")
    wv, cyc = waves(tasks)
    if cyc:
        probs.append(f"cycle among {', '.join(cyc)}")
    # critic ordering per CRIT (group by 'crit' field or 'out' prefix)
    pos = {i: n for n, w in enumerate(wv) for i in w}
    groups = {}
    for t in tasks:
        if t.get("role") == "critic":
            g = t.get("crit") or str(t.get("out", "")).split("/")[0]
            groups.setdefault(g, []).append(t)
    for g, ts in groups.items():
        fulls = [pos.get(t["id"], 0) for t in ts if t.get("kind") == "full"]
        for t in ts:
            if t.get("kind") in ("delta", "final") and (not fulls or pos.get(t["id"], 0) <= min(fulls)):
                probs.append(f"{t['id']}: {t['kind']} pass in '{g}' not after a full pass")
        npass = sum(int(t.get("repeat", 1)) for t in ts)
        if npass > 5:
            probs.append(f"'{g}': {npass} critic passes planned (cap 5)")
    if a.mission:
        refd = set()
        for t in tasks:
            refd |= set(t.get("reqs", []))
        for r in r_ids(a.mission):
            if r not in refd:
                probs.append(f"{r} (mission.md) not referenced by any task 'reqs'")
    # print
    print(f"Plan {plan.get('mission', '?')}: {len(tasks)} tasks, {len(wv)} waves")
    byid = {t["id"]: t for t in tasks if "id" in t}
    total = 0
    dc = bool(plan.get("design_critic_installed"))
    for n, w in enumerate(wv, 1):
        cells = []
        for i in w:
            t = byid[i]; c = est(t, dc) or 0; total += c
            k = t.get("kind", "")
            cells.append(f"{i}:{t.get('role')}{'/'+k if k and k!='-' else ''}({c//1000}k)")
        print(f"  wave {n}: " + "  ".join(cells))
    lo, hi = int(total * 0.75), int(total * 1.3)
    print(f"Estimate: ~{total//1000}k tokens (band {lo//1000}-{hi//1000}k)"
          + ("" if dc else f"; design-critic agent would save ~{DESIGN_CRITIC_SAVING//1000}k per fresh critic"))
    if a.budget and total > a.budget:
        warn.append(f"estimate {total//1000}k exceeds budget {a.budget//1000}k")
    for w in warn:
        print("WARN  " + w)
    for p in probs:
        print("ERROR " + p)
    print("PLAN OK" if not probs else "PLAN FAIL")
    sys.exit(1 if probs else 0)


def cmd_table(a):
    print(f"{'role':13}{'kind':10}tokens")
    for (r, k), c in COST.items():
        print(f"{r:13}{k:10}{c}")
    print(f"design-critic agent: -{DESIGN_CRITIC_SAVING} per fresh critic (full/final)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="validate DAG, print waves + estimate")
    c.add_argument("plan"); c.add_argument("--mission"); c.add_argument("--budget", type=int)
    sub.add_parser("table", help="print cost table")
    a = ap.parse_args()
    {"check": cmd_check, "table": cmd_table}[a.cmd](a)


if __name__ == "__main__":
    main()
