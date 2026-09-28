#!/usr/bin/env python3
"""Mission helper (not part of the skill): expected coins per run by difficulty for an econ.py config, to check the
risk/reward ladder (harder tiers should pay more on average after supplies). Same parameters econ.py uses:
p_arrive, fare_full, kit x crate prices, failed_trip option (A banked share mean, B zero, C banked minus penalty),
recovery fee x falls. Skill range and fare spread average out.
  python3 difficulty_ev.py CONFIG.json [CONFIG2.json ...] [--set path=value ...]"""
import argparse, json
def v(x): return x["v"] if isinstance(x, dict) and "v" in x else x
def setp(d, path, val):
    keys = path.split("."); o = d
    for k in keys[:-1]: o = o[int(k)] if isinstance(o, list) else o[k]
    k = keys[-1]; tgt = o[k] if not isinstance(o, list) else o[int(k)]
    val = json.loads(val) if val[:1] in "0123456789-[" else val
    if isinstance(tgt, dict) and "v" in tgt: tgt["v"] = val
    elif isinstance(o, list): o[int(k)] = val
    else: o[k] = val
def ev(c):
    ft = c["failed_trip"]; opt = ft["option"]; lo, hi = v(ft["banked_share"]); share = (lo + hi) / 2
    fail_pay = {"A": share, "B": 0.0, "C": share * (1 - v(ft["penalty"]))}[opt]
    rec = v(c["recovery"]["fee"]) * v(c["recovery"]["falls_per_run"])
    rows = []
    for name, d in c["difficulty"].items():
        fare, p = v(d["fare_full"]), v(d["p_arrive"])
        kit = sum(v(c["prices"][k]) * n for k, n in d["kit"].items())
        gross = p * fare + (1 - p) * fail_pay * fare
        rows.append((name, fare, p, kit, gross, gross - kit - rec))
    return opt, rows
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("configs", nargs="+"); ap.add_argument("--set", action="append", default=[])
a = ap.parse_args()
for f in a.configs:
    c = json.load(open(f))
    for s in a.set: setp(c, *s.split("=", 1))
    opt, rows = ev(c)
    print(f"{f.split('/')[-1]} (failed trip option {opt})")
    print("| difficulty | fare_full | p_arrive | kit cost | expected fare | net per run | vs Easy |\n|---|---|---|---|---|---|---|")
    base = rows[0][5]
    for n, fare, p, kit, g, net in rows:
        print(f"| {n} | {fare:,.0f} | {p:.2f} | {kit:,.0f} | {g:,.0f} | {net:,.0f} | {net / base:.2f}x |")
    inv = [rows[i + 1][0] for i in range(len(rows) - 1) if rows[i + 1][5] <= rows[i][5]]
    print(f"ladder: {'INVERTED at ' + ', '.join(inv) + ' (a harder tier pays less than the one below)' if inv else 'monotonic (harder pays more)'}\n")
