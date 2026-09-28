#!/usr/bin/env python3
"""A/B tests for Risky Rails done right: pre-registered plans, traffic-aware sizing, no peeking, honest reads.

  abtest.py size    --base P (--mde-rel R | --target P2) [--daily N] [--alpha A] [--power W] [--arms K]
  abtest.py plan    NAME --surface thumbnail|icon|price|onboarding|other --metric prop|mean|rpu --base X
                    (--mde-rel R | --mde-abs D | --target T) --daily N [--sd S] [--price-a P --price-b P]
                    [--arms A,B] [--weights 50,50] [--looks K] [--guardrail d1:0.01] [--hypothesis TEXT]
                    [--better higher|lower] [--start YYYY-MM-DD] [--max-weeks 6] [--out DIR]
  abtest.py analyze PLAN (dir or plan.json) --data FILE.csv [--asof YYYY-MM-DD] [--accept-edit]
  abtest.py compare --data thumbs.csv [--min-n 2000]   adaptive traffic (thumbnail personalization): per-variant
                    rate with CI, flags clear losers, never a verdict (variant,impressions,qualified_plays)
  abtest.py srm     --counts 5000,5210 [--weights 50,50]
  abtest.py peek    --looks K        false-positive rate of checking K times, and the O'Brien-Fleming fix
  abtest.py assign  --salt S [--arms A,B] [--weights 50,50] (--users 1,2,3 | --n 10000)

Data CSV for analyze (one row per arm; header names matter, order does not):
  prop: arm,users,conversions[,<g>_users,<g>_hits per guardrail g]     rpu: arm,users,buyers
  mean: arm,n,mean,sd  or per-user rows  arm,value   (per-user rows also give a bootstrap CI)
Plans live in <out>/<NAME>/plan.json (default out: $RR_DATA_ROOT/experiments, else ~/.rr-data/experiments) and
are hashed: analyze flags a plan edited after it was written. Exit 0 = ran, 1 = invalid input/plan, 2 = usage.
"""
import argparse, csv, datetime as dt, hashlib, json, math, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rrlib  # noqa: E402
import statlib as S  # noqa: E402

GUIDE = {
    "thumbnail": "Roblox thumbnail personalization is a bandit (it shifts impressions to winners per user group), not "
                 "a fixed A/B test: read it with `abtest.py compare` (descriptive, no SRM, no verdict). Plan a fixed "
                 "test only for a manual rotation you control. Primary = qualified play-through; guardrail = D1 or bounce. "
                 "One change per variant (canon release.thumbs.variant_rule).",
    "icon": "No native icon personalization found in the docs (2026-09-28): a controlled rotation needs whole weeks "
            "per icon and is confounded by updates; label it pre/post. Primary = qualified plays per impression; "
            "the icon must read at 64 px (canon release.thumbs.icon).",
    "price": "Roblox price optimization needs about 60,000 transactions in 30 days; below that, check this plan says "
             "TESTABLE before running one. One developer product per price, same benefit, external purchases off (the "
             "Store tab would leak the cheaper price; avoid pass price tests). Primary = Robux per exposed player (rpu); "
             "guardrail = payer conversion. Read prices with GetProductInfo, never hard-code. Owner sets live prices.",
    "onboarding": "New players only (expose at their first join); primary = D1 or first_bank reached; guardrail = "
                  "session length. Tag the onboarding funnel with the experiment (tracking plan 'tag').",
    "other": "Randomise by UserId (RR_Analytics.expose), expose at the moment the change is seen, run whole weeks.",
}


def default_out():
    return rrlib.data_root() / "experiments"


def plan_hash(p):
    body = {k: v for k, v in p.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


def djb2(s):
    h = 5381
    for ch in s.encode("utf-8"):
        h = (h * 33 + ch) % 4294967296
    return h


def assign_arm(salt, arms, weights, uid):
    """Python mirror of RR_Analytics armFor (same floats, same order)."""
    b = djb2(f"{salt}:{uid}") % 10000
    total, acc = float(sum(weights)), 0.0
    for a, w in zip(arms, weights):
        acc += w
        if b < acc / total * 10000:
            return a
    return arms[-1]


def weeks_for(n_total, daily, min_days=7):
    days = max(min_days, math.ceil(n_total / daily)) if daily else None
    return None if days is None else 7 * math.ceil(days / 7)


def sizes(metric, base, target, alpha, power, arms, weights, sd=None, price_a=None, price_b=None):
    k = len(arms)
    a = alpha / (k - 1) if k > 2 else alpha
    ratio = weights[1] / weights[0]
    if metric == "prop":
        nA, nB = S.n_two_prop(base, target, a, power, ratio=ratio)
    elif metric == "mean":
        nA = S.n_means(abs(target - base), sd, sd, a, power)
        nB = math.ceil(nA * ratio)
    else:
        conv_b = target * price_a / price_b  # target = RPU-equivalent conversion at price A
        nA = S.n_rpu(price_a, base, price_b, conv_b, a, power)
        nB = math.ceil(nA * ratio)
    per = [nA] + [math.ceil(nA * w / weights[0]) for w in weights[1:]] if k > 2 else [nA, nB]
    return per, a


def resolve_target(a):
    if a.target is not None:
        return a.target
    if a.mde_rel is not None:
        return a.base * (1 + (a.mde_rel if a.better == "higher" else -a.mde_rel))
    if a.mde_abs is not None:
        return a.base + (a.mde_abs if a.better == "higher" else -a.mde_abs)
    sys.exit("give --target, --mde-rel or --mde-abs")


def cmd_size(a):
    a.better = "higher"
    a.mde_abs = None
    t = resolve_target(a)
    arms = [chr(65 + i) for i in range(a.arms)]
    per, _ = sizes("prop", a.base, t, a.alpha, a.power, arms, [1] * a.arms)
    tot = sum(per)
    print(f"{rrlib.pct(a.base)} -> {rrlib.pct(t)} (alpha {a.alpha}, power {a.power}, {a.arms} arms): "
          f"{per[0]:,} per arm, {tot:,} total")
    if a.daily:
        d = weeks_for(tot, a.daily)
        print(f"at {a.daily:,.0f}/day: {d} days ({d // 7} whole weeks)")
        for wk in (2, 4, 6):
            n = a.daily * 7 * wk / a.arms
            print(f"  detectable in {wk} weeks: {rrlib.pct(a.base)} -> {rrlib.pct(S.mde_two_prop(a.base, n, a.alpha, a.power))}")
    return 0


def cmd_plan(a):
    arms = a.arms.split(",")
    weights = [float(w) for w in a.weights.split(",")] if a.weights else [1.0] * len(arms)
    if len(weights) != len(arms) or len(arms) < 2:
        sys.exit("need >= 2 arms and one weight per arm")
    if a.metric == "mean" and not a.sd:
        sys.exit("--metric mean needs --sd (from last week's data)")
    if a.metric == "rpu" and not (a.price_a and a.price_b):
        sys.exit("--metric rpu needs --price-a and --price-b (Robux) and --base = conversion at price A")
    if a.metric == "rpu" and a.mde_rel is None:
        sys.exit("--metric rpu needs --mde-rel (relative change in Robux per exposed player to detect)")
    target = resolve_target(a)  # rpu: RPU lift expressed as the conversion-at-price-A equivalent
    per, a_cmp = sizes(a.metric, a.base, target, a.alpha, a.power, arms, weights, a.sd, a.price_a, a.price_b)
    looks = [(i + 1) / a.looks for i in range(a.looks)] if a.looks > 1 else [1.0]
    infl = S.obf_inflation(looks, a_cmp, a.power) if a.looks > 1 else 1.0
    per = [math.ceil(n * infl) for n in per]
    tot = sum(per)
    days = weeks_for(tot, a.daily)
    start = a.start or dt.date.today().isoformat()
    readout = (dt.date.fromisoformat(start) + dt.timedelta(days=days)).isoformat()
    testable = days <= a.max_weeks * 7
    p = {"name": a.name, "created": dt.date.today().isoformat(), "surface": a.surface, "hypothesis": a.hypothesis,
         "metric": {"kind": a.metric, "base": a.base, "target": target, "sd": a.sd, "price_a": a.price_a,
                    "price_b": a.price_b, "better": a.better},
         "arms": arms, "weights": weights, "control": arms[0], "alpha": a.alpha, "alpha_per_comparison": a_cmp,
         "power": a.power, "n_per_arm": per, "daily_eligible": a.daily, "days": days, "start": start,
         "readout": readout, "looks": looks, "bounds": S.obf_bounds(looks, a_cmp) if a.looks > 1 else
         [S.norm_ppf(1 - a_cmp / 2)], "inflation": infl,
         "guardrails": [{"name": g.split(":")[0], "margin": float(g.split(":")[1])} for g in a.guardrail],
         "salt": f"{a.name}-{start}", "testable": testable}
    p["hash"] = plan_hash(p)
    out = Path(a.out or default_out()) / a.name
    rrlib.save_json(out / "plan.json", p)
    if a.metric == "prop":
        eff = f"{rrlib.pct(a.base, 2)} -> {rrlib.pct(target, 2)}"
    elif a.metric == "rpu":
        eff = (f"R$ per exposed player {a.price_a * a.base:.2f} -> {a.price_a * target:.2f} (needs "
               f"{rrlib.pct(target * a.price_a / a.price_b, 2)} conversion at {a.price_b:g} R$ vs {rrlib.pct(a.base, 2)} "
               f"at {a.price_a:g} R$)")
    else:
        eff = f"mean {a.base:g} -> {target:g} (sd {a.sd:g})"
    print(f"plan {a.name} ({a.surface}, {a.metric}): {eff}; {', '.join(f'{x}={n:,}' for x, n in zip(arms, per))} "
          f"(total {tot:,})")
    print(f"  {a.daily:,.0f} eligible/day -> {days} days = {days // 7} whole weeks; start {start}, readout {readout}")
    if a.looks > 1:
        print(f"  planned looks at {', '.join(f'{x:.0%}' for x in looks)}: stop only if |z| >= "
              f"{', '.join(f'{b:.2f}' for b in p['bounds'])} (O'Brien-Fleming, sample x{infl:.3f})")
    else:
        print("  fixed horizon: no verdict before the readout (analyze refuses)")
    if not testable:
        n4 = a.daily * 28 * weights[0] / sum(weights)
        print(f"  NOT TESTABLE in {a.max_weeks} weeks at this traffic. In 4 weeks the smallest detectable change is "
              f"{rrlib.fmt_num(a.base, 4)} -> {rrlib.fmt_num(S.mde_two_prop(a.base, n4, a_cmp, a.power), 4)}"
              if a.metric == "prop" else f"  NOT TESTABLE in {a.max_weeks} weeks: test a bolder change")
    print(f"  salt {p['salt']} (copy into tracking-plan experiments), plan hash {p['hash']}")
    print(f"  guide: {GUIDE[a.surface]}")
    print(f"wrote {out / 'plan.json'}")
    return 0


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{k.strip().lower(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def num(x):
    return float(str(x).replace(",", "").replace("%", "")) if str(x).strip() else 0.0


def cmd_analyze(a):
    pp = Path(a.plan)
    pp = pp / "plan.json" if pp.is_dir() else pp
    p = rrlib.load_json(pp)
    lines, status, res = [], None, {"plan": p["name"], "hash_ok": plan_hash(p) == p.get("hash")}
    if not res["hash_ok"] and not a.accept_edit:
        print(f"INVALID: {pp} was edited after it was written (hash mismatch). Moving goalposts voids the test; "
              "re-plan, or --accept-edit if only a typo changed (say so in the memo).")
        return 1
    rows = read_rows(a.data)
    kind = p["metric"]["kind"]
    arms = p["arms"]
    per_user = rows and "value" in rows[0] and "users" not in rows[0] and "n" not in rows[0]
    agg = {}
    if per_user:
        for r in rows:
            agg.setdefault(r["arm"], []).append(num(r["value"]))
        n_by = {k: len(v) for k, v in agg.items()}
    else:
        agg = {r["arm"]: r for r in rows}
        n_by = {k: num(r.get("users") or r.get("n")) for k, r in agg.items()}
    missing = [x for x in arms if x not in agg]
    if missing:
        print(f"INVALID: data has no rows for arms {missing}")
        return 1
    counts = [n_by[x] for x in arms]
    srm = S.srm(counts, p["weights"])
    res["srm"] = srm
    lines.append(f"SRM check: counts {', '.join(f'{x}={int(n):,}' for x, n in zip(arms, counts))}, p = {srm['p']:.4g}")
    if srm["p"] < 0.001:
        status = "INVALID (sample ratio mismatch: assignment or logging is broken; fix and restart)"
    frac = min(n / need for n, need in zip(counts, p["n_per_arm"]))
    look = None
    for j, t in enumerate(p["looks"]):
        if frac >= t * 0.97:
            look = j
    elapsed_ok = True
    if a.asof:
        elapsed_ok = dt.date.fromisoformat(a.asof) >= dt.date.fromisoformat(p["readout"])
    final = look == len(p["looks"]) - 1 and elapsed_ok
    if status is None and look is None:
        status = (f"NOT DONE: {frac:.0%} of the planned sample. No verdict before the planned horizon "
                  f"(readout {p['readout']}); peeking inflates false wins.")
    if status is None and look == len(p["looks"]) - 1 and not elapsed_ok:
        status = f"NOT DONE: sample reached but the readout date {p['readout']} is not (run whole weeks)."
        look = None if len(p["looks"]) == 1 else look
    bound = p["bounds"][look] if look is not None else None
    ctrl = arms[0]
    lines.append(f"progress: {frac:.0%} of the planned sample" + (f", look {look + 1} of {len(p['looks'])}"
                                                                  if look is not None else ""))
    if status is not None:  # no estimates before the horizon: seeing them is peeking
        res.update({"status": status, "fraction": frac, "look": None, "lines": lines})
        rrlib.save_json(pp.parent / "result.json", res)
        (pp.parent / "RESULT.md").write_text(f"# {p['name']} readout\n\n**{status}**\n\n" +
                                             "\n".join(f"- {ln}" for ln in lines) + "\n", encoding="utf-8")
        print(status)
        for ln in lines:
            print("  " + ln)
        return 0
    comps = []
    for x in arms[1:]:
        if kind == "prop":
            A_, B_ = agg[ctrl], agg[x]
            r = S.two_prop(num(A_["conversions"]), num(A_["users"]), num(B_["conversions"]), num(B_["users"]))
            est = f"{rrlib.pct(r['pa'], 2)} -> {rrlib.pct(r['pb'], 2)}, diff {r['diff'] * 100:+.2f} pts " \
                  f"(95% CI {r['diff_ci'][0] * 100:+.2f} to {r['diff_ci'][1] * 100:+.2f}), lift {r['lift']:+.1%}" \
                  if r["lift"] is not None else "control has zero conversions"
        elif kind == "rpu":
            A_, B_ = agg[ctrl], agg[x]
            pa, pb = p["metric"]["price_a"], p["metric"]["price_b"]
            na, nb = num(A_["users"]), num(B_["users"])
            ca, cb = num(A_["buyers"]) / na, num(B_["buyers"]) / nb
            ra, rb = pa * ca, pb * cb
            se = math.sqrt(pa ** 2 * ca * (1 - ca) / na + pb ** 2 * cb * (1 - cb) / nb)
            z = (rb - ra) / se if se > 0 else 0.0
            r = {"diff": rb - ra, "diff_ci": (rb - ra - 1.96 * se, rb - ra + 1.96 * se), "z": z,
                 "p": 2 * S.norm_sf(abs(z)), "method": "rpu-z"}
            est = (f"R$/exposed {ra:.3f} (conv {rrlib.pct(ca, 2)} at {pa}) -> {rb:.3f} (conv {rrlib.pct(cb, 2)} at "
                   f"{pb}), diff {rb - ra:+.3f} (95% CI {r['diff_ci'][0]:+.3f} to {r['diff_ci'][1]:+.3f})")
        else:
            if per_user:
                A_, B_ = agg[ctrl], agg[x]
                m1, m2 = sum(A_) / len(A_), sum(B_) / len(B_)
                s1 = math.sqrt(sum((v - m1) ** 2 for v in A_) / max(1, len(A_) - 1))
                s2 = math.sqrt(sum((v - m2) ** 2 for v in B_) / max(1, len(B_) - 1))
                r = S.welch(m1, s1, len(A_), m2, s2, len(B_))
                d, ci = S.bootstrap_diff(A_, B_)
                r["boot_ci"] = ci
            else:
                A_, B_ = agg[ctrl], agg[x]
                r = S.welch(num(A_["mean"]), num(A_["sd"]), num(A_["n"]), num(B_["mean"]), num(B_["sd"]), num(B_["n"]))
            est = f"diff {r['diff']:+.3f} (95% CI {r['diff_ci'][0]:+.3f} to {r['diff_ci'][1]:+.3f}, {r['method']})"
            if "boot_ci" in r:
                est += f"; bootstrap CI {r['boot_ci'][0]:+.3f} to {r['boot_ci'][1]:+.3f}"
        comps.append((x, r, est))
    adj = S.holm([r["p"] for _, r, _ in comps]) if len(comps) > 1 else [comps[0][1]["p"]]
    better = p["metric"].get("better", "higher")
    verdicts = []
    for (x, r, est), pa_ in zip(comps, adj):
        zlike = abs(r.get("z", r.get("t", 0.0)))
        sig = (pa_ < p["alpha"]) if final else (bound is not None and zlike >= bound)
        good = (r["diff"] > 0) == (better == "higher")
        v = ("WIN" if good else "LOSS") if sig else "NO DIFFERENCE"
        lines.append(f"{x} vs {ctrl}: {est}; p = {r['p']:.4g}" + (f" (Holm {pa_:.4g})" if len(comps) > 1 else "") +
                     f" [{r['method']}] -> {v if status is None else 'no verdict'}")
        verdicts.append((x, v, r))
    g_fail = []
    for g in p.get("guardrails", []):
        nm, margin = g["name"], g["margin"]
        if f"{nm}_users" not in agg[ctrl]:
            lines.append(f"guardrail {nm}: no {nm}_users/{nm}_hits columns: UNCHECKED")
            continue
        for x in arms[1:]:
            r = S.two_prop(num(agg[ctrl][f"{nm}_hits"]), num(agg[ctrl][f"{nm}_users"]),
                           num(agg[x][f"{nm}_hits"]), num(agg[x][f"{nm}_users"]))
            ok = r["diff_ci"][0] > -margin
            lines.append(f"guardrail {nm} {x}: {rrlib.pct(r['pa'], 2)} -> {rrlib.pct(r['pb'], 2)}, CI low "
                         f"{r['diff_ci'][0] * 100:+.2f} pts vs margin -{margin * 100:.2f}: {'OK' if ok else 'FAIL'}")
            if not ok:
                g_fail.append(f"{nm}:{x}")
    if status is None:
        wins = [x for x, v, _ in verdicts if v == "WIN"]
        if wins and any(g.split(":")[1] in wins for g in g_fail):
            status = "GUARDRAIL FAIL: the winner hurts a guardrail; do not ship, investigate"
        elif wins:
            best = max((vv for vv in verdicts if vv[1] == "WIN"), key=lambda vv: abs(vv[2]["diff"]))
            status = f"SHIP {best[0]} " + ("(stopped early at a planned look)" if not final else "(planned horizon)")
        elif any(v == "LOSS" for _, v, _ in verdicts):
            status = f"KEEP {ctrl}: a variant is significantly worse"
        elif final:
            status = f"NO DIFFERENCE at the planned horizon: keep {ctrl} (or the cheaper option); the CI bounds the effect"
        else:
            status = "CONTINUE: planned look passed without crossing the boundary; next look as planned"
    res.update({"status": status, "fraction": frac, "look": look, "lines": lines})
    out = pp.parent
    rrlib.save_json(out / "result.json", {**res, "comparisons": [{"arm": x, **{k: v for k, v in r.items()}}
                                                                   for x, r, _ in comps]})
    md = [f"# {p['name']} readout", "", f"**{status}**", "", f"Hypothesis: {p.get('hypothesis') or '-'}",
          f"Surface {p['surface']}, metric {kind}, planned {p['n_per_arm']} per arm, readout {p['readout']}.", ""]
    md += [f"- {ln}" for ln in lines]
    (out / "RESULT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(status)
    for ln in lines:
        print("  " + ln)
    print(f"wrote {out / 'RESULT.md'}")
    return 0


def cmd_compare(a):
    """Descriptive read of adaptive traffic (thumbnail personalization): per-variant rate with CI, no verdict."""
    rows = read_rows(a.data)
    key_n = next(k for k in ("impressions", "users", "n") if k in rows[0])
    key_x = next(k for k in ("qualified_plays", "plays", "conversions", "hits") if k in rows[0])
    data = [(r.get("variant") or r.get("arm") or r.get("thumbnail"), num(r[key_n]), num(r[key_x])) for r in rows]
    stats = [(v, n, x, x / n if n else 0, S.wilson(x, n)) for v, n, x in data if n]
    judged = [t for t in stats if t[1] >= a.min_n] or stats
    best = max(judged, key=lambda t: t[3])
    print("descriptive only: traffic was adaptive (personalization), so there is no SRM check and no winner call;")
    print(f"each rate is conditional on the players Roblox chose to show it to. {key_x} / {key_n}:")
    for v, n, x, r, (lo, hi) in sorted(stats, key=lambda t: -t[3]):
        flag = ""
        if v != best[0] and hi < best[4][0] and n >= a.min_n:
            flag = "  <- clearly below the best: a candidate to replace at the next update"
        elif n < a.min_n:
            flag = f"  (under {a.min_n:,} {key_n}: too early to judge)"
        print(f"  {v:18} {r:7.2%}  95% CI {lo:.2%}-{hi:.2%}  n {n:,.0f}{flag}")
    print("Roblox advice: keep several thumbnails active; swap losers at the next major update, not mid-week.")
    return 0


def cmd_srm(a):
    c = [float(x) for x in a.counts.split(",")]
    w = [float(x) for x in a.weights.split(",")] if a.weights else [1.0] * len(c)
    r = S.srm(c, w)
    print(f"chi2 {r['chi2']:.2f} (df {r['df']}), p = {r['p']:.4g}: "
          f"{'SAMPLE RATIO MISMATCH: do not read this test' if r['p'] < 0.001 else 'split OK'}")
    return 0


def cmd_peek(a):
    fpr = S.peek_fpr(a.looks, a.alpha)
    looks = [(i + 1) / a.looks for i in range(a.looks)]
    b = S.obf_bounds(looks, a.alpha, sims=100000)
    print(f"checking a null test {a.looks} times at p < {a.alpha}: false-positive rate {fpr:.1%} (not {a.alpha:.0%})")
    print(f"planned O'Brien-Fleming looks keep {a.alpha:.0%}: |z| >= " + ", ".join(f"{x:.2f}" for x in b))
    return 0


def cmd_assign(a):
    arms = a.arms.split(",")
    w = [float(x) for x in a.weights.split(",")] if a.weights else [1.0] * len(arms)
    if a.users:
        for u in a.users.split(","):
            print(f"{u}\t{assign_arm(a.salt, arms, w, u.strip())}")
        return 0
    cnt = {x: 0 for x in arms}
    for u in range(1, a.n + 1):
        cnt[assign_arm(a.salt, arms, w, 100000000 + u * 7919)] += 1
    r = S.srm([cnt[x] for x in arms], w)
    print(" ".join(f"{x}={cnt[x]}" for x in arms) + f"  (SRM p = {r['p']:.3f})")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("size")
    s.add_argument("--base", type=float, required=True)
    s.add_argument("--mde-rel", type=float)
    s.add_argument("--target", type=float)
    s.add_argument("--daily", type=float)
    s.add_argument("--alpha", type=float, default=0.05)
    s.add_argument("--power", type=float, default=0.8)
    s.add_argument("--arms", type=int, default=2)
    p = sub.add_parser("plan")
    p.add_argument("name")
    p.add_argument("--surface", choices=list(GUIDE), required=True)
    p.add_argument("--metric", choices=["prop", "mean", "rpu"], default="prop")
    p.add_argument("--base", type=float, required=True)
    p.add_argument("--mde-rel", type=float)
    p.add_argument("--mde-abs", type=float)
    p.add_argument("--target", type=float)
    p.add_argument("--sd", type=float)
    p.add_argument("--price-a", type=float)
    p.add_argument("--price-b", type=float)
    p.add_argument("--daily", type=float, required=True, help="eligible units per day across all arms")
    p.add_argument("--arms", default="A,B")
    p.add_argument("--weights")
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--power", type=float, default=0.8)
    p.add_argument("--looks", type=int, default=1)
    p.add_argument("--guardrail", action="append", default=[], help="name:margin, e.g. d1:0.01 (absolute)")
    p.add_argument("--hypothesis", default="")
    p.add_argument("--better", choices=["higher", "lower"], default="higher")
    p.add_argument("--start")
    p.add_argument("--max-weeks", type=int, default=6)
    p.add_argument("--out")
    z = sub.add_parser("analyze")
    z.add_argument("plan")
    z.add_argument("--data", required=True)
    z.add_argument("--asof")
    z.add_argument("--accept-edit", action="store_true")
    r = sub.add_parser("srm")
    r.add_argument("--counts", required=True)
    r.add_argument("--weights")
    c = sub.add_parser("compare")
    c.add_argument("--data", required=True, help="CSV: variant,impressions,qualified_plays")
    c.add_argument("--min-n", type=int, default=2000)
    k = sub.add_parser("peek")
    k.add_argument("--looks", type=int, required=True)
    k.add_argument("--alpha", type=float, default=0.05)
    g = sub.add_parser("assign")
    g.add_argument("--salt", required=True)
    g.add_argument("--arms", default="A,B")
    g.add_argument("--weights")
    g.add_argument("--users")
    g.add_argument("--n", type=int, default=10000)
    a = ap.parse_args()
    if not a.cmd:
        ap.print_help()
        return 2
    return {"size": cmd_size, "plan": cmd_plan, "analyze": cmd_analyze, "compare": cmd_compare, "srm": cmd_srm,
            "peek": cmd_peek, "assign": cmd_assign}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
