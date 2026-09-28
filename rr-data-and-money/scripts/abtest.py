#!/usr/bin/env python3
"""A/B tests for Risky Rails done right: pre-registered plans, traffic-aware sizing, no peeking, honest reads.

  abtest.py size    --base P (--mde-rel R | --target P2) [--daily N] [--alpha A] [--power W] [--arms K]
  abtest.py plan    NAME --surface thumbnail|icon|price|onboarding|other --metric prop|mean|rpu --base X
                    (--mde-rel R | --mde-abs D | --target T) --daily N [--sd S] [--price-a P --price-b P]
                    [--arms A,B] [--weights 50,50] [--looks K] [--guardrail d1:0.01] [--hypothesis TEXT]
                    [--better higher|lower] [--start YYYY-MM-DD] [--max-weeks 6] [--out DIR] [--replace]
                    [--native --primary d1|d7|playtime|arpu|arppu|payer_conversion|session_time]
  abtest.py analyze PLAN (dir or plan.json) --data FILE.csv [--asof YYYY-MM-DD (default today)] [--accept-edit]
  abtest.py record  PLAN --metric [ARM:]NAME=LO,HI[,EST] [--guardrail [ARM:]NAME=LO,HI ...] [--enrolled A=n,B=n]
                    readout of a Roblox Experiments (Creator Hub) test: percent-change CIs as the Results tab shows them
  abtest.py compare --data thumbs.csv [--plan DIR] [--min-n 2000]   adaptive traffic (thumbnail personalization):
                    per-variant rate with CI, flags clear losers, never a verdict; --plan writes result.json
  abtest.py srm     --counts 5000,5210 [--weights 50,50]
  abtest.py peek    --looks K        false-positive rate of checking K times, and the O'Brien-Fleming fix
  abtest.py assign  --salt S [--arms A,B] [--weights 50,50] (--users 1,2,3 | --n 10000)

Data CSV (one row per arm; header names matter, order does not; aliases: arm|variant|thumbnail|group,
users|n|impressions|exposed, conversions|hits|qualified_plays|plays):
  prop: arm,users,conversions[,<g>_users,<g>_hits per guardrail g]     rpu: arm,users,buyers
  mean: arm,n,mean,sd  or per-user rows  arm,value   (per-user rows also give a bootstrap CI)
Plans live in <out>/<NAME>/plan.json (default out: <data root>/experiments) and are hashed: analyze refuses a plan
edited after it was written; plan refuses to overwrite one (--replace keeps the old one in history/ and analyze
then refuses unless --accept-edit). Each interim look is recorded in looks.json and read once.
Exit 0 = ran, 1 = invalid input/plan, 2 = usage.
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
NATIVE = ("Roblox Experiments (Creator Hub > Experiments): the value lives in a Config key read with "
          "ConfigService:GetConfigForPlayerAsync(player):GetValue(key) at the moment the change is seen (the first "
          "GetValue enrols the player). 14-60 days, control + up to 2 variants, rollout 100% and an even split unless "
          "traffic is huge; the key is locked while it runs; results give D1, D7, playtime, ARPU, ARPPU, payer "
          "conversion and session time per variant with CIs. Roblox warns games under 1,000 DAU struggle. Open the "
          "Results tab only to check it runs; read it at the readout with `abtest.py record`.")
NATIVE_METRICS = ("d1", "d7", "playtime", "arpu", "arppu", "payer_conversion", "session_time")
ALIASES = {"arm": ("variant", "thumbnail", "group"), "users": ("n_users", "exposed", "impressions"),
           "conversions": ("hits", "qualified_plays", "plays", "converted")}


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


def bad(msg):
    print(f"INVALID: {msg}")
    return 1


def check_inputs(metric, base, target, daily=None, sd=None, prices=()):
    """Message for inputs no test can use, else None."""
    if daily is not None and not daily > 0:
        return "--daily must be > 0 (eligible players per day across all arms)"
    if metric == "prop" and not (0 < base < 1 and 0 < target < 1):
        return f"a proportion must be strictly between 0 and 1 (base {base:g} -> target {target:g})"
    if metric == "rpu" and not (0 < base < 1 and all(x and x > 0 for x in prices)):
        return "rpu needs 0 < --base < 1 (conversion at price A) and prices > 0"
    if metric == "mean" and not (sd and sd > 0):
        return "--metric mean needs --sd > 0"
    if base == target:
        return "base equals target: nothing to detect"
    return None


def cmd_size(a):
    a.better = "higher"
    a.mde_abs = None
    t = resolve_target(a)
    msg = check_inputs("prop", a.base, t, a.daily)
    if msg:
        return bad(msg)
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
        return bad("need >= 2 arms and one weight per arm")
    if a.metric == "mean" and not a.sd:
        return bad("--metric mean needs --sd (from last week's data)")
    if a.metric == "rpu" and not (a.price_a and a.price_b):
        return bad("--metric rpu needs --price-a and --price-b (Robux) and --base = conversion at price A")
    if a.metric == "rpu" and a.mde_rel is None:
        return bad("--metric rpu needs --mde-rel (relative change in Robux per exposed player to detect)")
    target = resolve_target(a)  # rpu: RPU lift expressed as the conversion-at-price-A equivalent
    msg = check_inputs(a.metric, a.base, target, a.daily, a.sd, (a.price_a, a.price_b) if a.metric == "rpu" else ())
    if a.metric == "rpu" and not msg and not 0 < target * a.price_a / a.price_b < 1:
        msg = "the rpu target needs a conversion at price B outside (0, 1): pick a smaller --mde-rel"
    if msg:
        return bad(msg)
    if a.native:
        if a.surface in ("thumbnail", "icon"):
            return bad("Roblox Experiments test in-game Config values; thumbnails use personalization (compare)")
        if len(arms) > 3:
            return bad("Roblox Experiments allow a control and at most two variants")
        if a.primary not in NATIVE_METRICS:
            return bad(f"--native needs --primary, one of {', '.join(NATIVE_METRICS)} (what the Results tab reports)")
    out = Path(a.out or default_out()) / a.name
    history = None
    if (out / "plan.json").is_file():
        if not a.replace:
            return bad(f"{out / 'plan.json'} exists: a plan is written once, before launch. Re-planning after data is "
                       "seen moves the goalposts; use a new NAME, or --replace (kept in history/, flagged at readout)")
        old_p = rrlib.load_json(out / "plan.json")
        seen = (out / "looks.json").is_file() or (out / "result.json").is_file()
        history = (old_p.get("replaced") or []) + [{"hash": old_p.get("hash"), "created": old_p.get("created"),
                                                    "replaced": dt.date.today().isoformat(), "after_data": seen}]
        rrlib.save_json(out / "history" / f"plan-{old_p.get('hash')}.json", old_p)
        for f in ("looks.json", "result.json", "RESULT.md"):
            if (out / f).is_file():
                (out / f).rename(out / "history" / f"{old_p.get('hash')}-{f}")
    per, a_cmp = sizes(a.metric, a.base, target, a.alpha, a.power, arms, weights, a.sd, a.price_a, a.price_b)
    looks = [(i + 1) / a.looks for i in range(a.looks)] if a.looks > 1 else [1.0]
    if a.native and a.looks > 1:
        return bad("Roblox Experiments have no planned interim looks: run the full duration (--looks 1)")
    infl = S.obf_inflation(looks, a_cmp, a.power) if a.looks > 1 else 1.0
    per = [math.ceil(n * infl) for n in per]
    tot = sum(per)
    days = weeks_for(tot, a.daily, 14 if a.native else 7)
    start = a.start or dt.date.today().isoformat()
    readout = (dt.date.fromisoformat(start) + dt.timedelta(days=days)).isoformat()
    testable = days <= (60 if a.native else a.max_weeks * 7)
    p = {"name": a.name, "created": dt.date.today().isoformat(), "surface": a.surface, "hypothesis": a.hypothesis,
         "source": "roblox-experiments" if a.native else ("personalization" if a.surface == "thumbnail" else "custom"),
         "primary": a.primary if a.native else None,
         "metric": {"kind": a.metric, "base": a.base, "target": target, "sd": a.sd, "price_a": a.price_a,
                    "price_b": a.price_b, "better": a.better},
         "arms": arms, "weights": weights, "control": arms[0], "alpha": a.alpha, "alpha_per_comparison": a_cmp,
         "power": a.power, "n_per_arm": per, "daily_eligible": a.daily, "days": days, "start": start,
         "readout": readout, "looks": looks, "bounds": S.obf_bounds(looks, a_cmp) if a.looks > 1 else
         [S.norm_ppf(1 - a_cmp / 2)], "inflation": infl,
         "guardrails": [{"name": g.split(":")[0], "margin": float(g.split(":")[1])} for g in a.guardrail],
         "salt": f"{a.name}-{start}" if a.surface not in ("thumbnail", "icon") and not a.native else None,
         "testable": testable}
    if history:
        p["replaced"] = history
    p["hash"] = plan_hash(p)
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
    elif not a.native:
        print("  fixed horizon: no verdict before the readout (analyze refuses)")
    limit = "60 days (Roblox Experiments maximum)" if a.native else f"{a.max_weeks} weeks"
    if not testable:
        n4 = a.daily * 28 * weights[0] / sum(weights)
        print(f"  NOT TESTABLE in {limit} at this traffic. In 4 weeks the smallest detectable change is "
              f"{rrlib.fmt_num(a.base, 4)} -> {rrlib.fmt_num(S.mde_two_prop(a.base, n4, a_cmp, a.power), 4)}"
              if a.metric == "prop" else f"  NOT TESTABLE in {limit}: test a bolder change")
    if a.native:
        print(f"  Roblox Experiments: primary {a.primary}; set duration {days} days, start {start}; guardrail margins are "
              "relative (d7:5 = the CI of the % change must stay above -5%). " + NATIVE)
    elif p["salt"]:
        print(f"  salt {p['salt']} (copy into the mission's tracking-plan experiments)")
    if history:
        print(f"  REPLACED an earlier plan (kept in history/){' after data was seen: analyze will refuse' if history[-1]['after_data'] else ''}")
    print(f"  plan hash {p['hash']}; guide: {GUIDE[a.surface]}")
    print(f"wrote {out / 'plan.json'}")
    return 0


def read_rows(path):
    """Rows with lower-case headers; alias columns renamed to the canonical names analyze and compare share."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [{k.strip().lower(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(f)]
    for r in rows:
        for canon, alts in ALIASES.items():
            if canon not in r:
                hit = next((x for x in alts if x in r), None)
                if hit:
                    r[canon] = r[hit]
    return rows


def num(x):
    return float(str(x).replace(",", "").replace("%", "")) if str(x).strip() else 0.0


def load_plan(path):
    pp = Path(path)
    pp = pp / "plan.json" if pp.is_dir() else pp
    if not pp.is_file():
        return pp, None
    return pp, rrlib.load_json(pp)


def plan_guard(p, pp, accept_edit):
    """None if the plan may be read, else the refusal text (edited or replaced after data was seen)."""
    if plan_hash(p) != p.get("hash") and not accept_edit:
        return (f"{pp} was edited after it was written (hash mismatch). Moving goalposts voids the test; re-plan, or "
                "--accept-edit if only a typo changed (say so in the memo).")
    late = [r for r in p.get("replaced") or [] if r.get("after_data")]
    if late and not accept_edit:
        return (f"plan {p['name']} was re-planned on {late[-1]['replaced']} after data had been seen (history/): the "
                "earlier data cannot count. Start a fresh test, or --accept-edit and report it as re-planned.")
    return None


def asof_date(a):
    return dt.date.fromisoformat(a.asof) if a.asof else dt.date.today()


def write_result(folder, p, status, lines, res):
    rrlib.save_json(folder / "result.json", {**res, "status": status, "lines": lines})
    md = [f"# {p['name']} readout", "", f"**{status}**", "", f"Hypothesis: {p.get('hypothesis') or '-'}",
          f"Surface {p['surface']}, source {p.get('source', 'custom')}, planned {p['n_per_arm']} per arm, "
          f"readout {p['readout']}.", ""] + [f"- {ln}" for ln in lines]
    (folder / "RESULT.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def say(status, lines, path=None):
    print(status)
    for ln in lines:
        print("  " + ln)
    if path:
        print(f"wrote {path}")


def cmd_analyze(a):
    pp, p = load_plan(a.plan)
    if p is None:
        return bad(f"no plan at {pp}")
    if p["surface"] == "thumbnail" or p.get("source") == "personalization":
        return bad("thumbnail personalization is adaptive (a bandit): an A/B verdict and SRM do not apply. "
                   f"Use: abtest.py compare --plan {pp.parent} --data FILE.csv")
    if p.get("source") == "roblox-experiments":
        return bad(f"a Roblox Experiments test is read from the Creator Hub Results tab: abtest.py record {pp.parent} ...")
    refusal = plan_guard(p, pp, a.accept_edit)
    if refusal:
        return bad(refusal)
    rows = read_rows(a.data)
    kind, arms = p["metric"]["kind"], p["arms"]
    if not rows or "arm" not in rows[0]:
        return bad(f"{a.data}: needs an arm column (arm|variant|thumbnail|group) and one row per arm")
    per_user = "value" in rows[0] and "users" not in rows[0] and "n" not in rows[0]
    need = {"prop": ("users", "conversions"), "rpu": ("users", "buyers"), "mean": ("n", "mean", "sd")}[kind]
    if not per_user and any(c not in rows[0] for c in need):
        return bad(f"{a.data}: metric {kind} needs columns arm,{','.join(need)} (have {', '.join(rows[0])})")
    lines, status, res = [], None, {"plan": p["name"], "kind": "ab", "hash_ok": plan_hash(p) == p.get("hash")}
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
        return bad(f"data has no rows for arms {missing}")
    counts = [n_by[x] for x in arms]
    srm = S.srm(counts, p["weights"])
    res["srm"] = srm
    lines.append(f"SRM check: counts {', '.join(f'{x}={int(n):,}' for x, n in zip(arms, counts))}, p = {srm['p']:.4g}")
    if srm["p"] < 0.001:
        status = "INVALID (sample ratio mismatch: assignment or logging is broken; fix and restart)"
    frac = min(n / need_ for n, need_ in zip(counts, p["n_per_arm"]))
    look = None
    for j, t in enumerate(p["looks"]):
        if frac >= t * 0.97:
            look = j
    asof = asof_date(a)
    elapsed_ok = asof >= dt.date.fromisoformat(p["readout"])
    last_look = len(p["looks"]) - 1
    final = look == last_look and elapsed_ok
    if status is None and look is None:
        status = (f"NOT DONE: {frac:.0%} of the planned sample. No verdict before the planned horizon "
                  f"(readout {p['readout']}); peeking inflates false wins.")
    if status is None and look == last_look and not elapsed_ok:
        status = f"NOT DONE: sample reached but the readout date {p['readout']} is not ({asof}; run whole weeks)."
    lines.append(f"progress: {frac:.0%} of the planned sample as of {asof}" +
                 (f", look {look + 1} of {len(p['looks'])}" if look is not None else ""))
    # interim looks are read once: a second call at the same look repeats the recorded answer, never re-tests
    lk_path = pp.parent / "looks.json"
    taken = rrlib.load_json(lk_path) if lk_path.is_file() else {}
    if status is None and look is not None and not final and str(look) in taken:
        t0 = taken[str(look)]
        status = (f"{t0['status'].split(':')[0]}: look {look + 1} was already read on {t0['date']} at "
                  f"{t0['fraction']:.0%} of the sample; the next look is at {p['looks'][look + 1]:.0%}")
        say(status, lines)
        return 0
    if status is not None:  # no estimates before the horizon: seeing them is peeking
        res.update({"fraction": frac, "look": None})
        write_result(pp.parent, p, status, lines, res)
        say(status, lines)
        return 0
    ctrl = arms[0]
    comps = []
    for x in arms[1:]:
        A_, B_ = agg[ctrl], agg[x]
        if kind == "prop":
            r = S.two_prop(num(A_["conversions"]), num(A_["users"]), num(B_["conversions"]), num(B_["users"]))
            est = f"{rrlib.pct(r['pa'], 2)} -> {rrlib.pct(r['pb'], 2)}, diff {r['diff'] * 100:+.2f} pts " \
                  f"(95% CI {r['diff_ci'][0] * 100:+.2f} to {r['diff_ci'][1] * 100:+.2f})" + \
                  (f", lift {r['lift']:+.1%}" if r["lift"] is not None else " (control has zero conversions)")
        elif kind == "rpu":
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
        elif per_user:
            m1, m2 = sum(A_) / len(A_), sum(B_) / len(B_)
            s1 = math.sqrt(sum((v - m1) ** 2 for v in A_) / max(1, len(A_) - 1))
            s2 = math.sqrt(sum((v - m2) ** 2 for v in B_) / max(1, len(B_) - 1))
            r = S.welch(m1, s1, len(A_), m2, s2, len(B_))
            r["boot_ci"] = S.bootstrap_diff(A_, B_)[1]
            est = (f"diff {r['diff']:+.3f} (95% CI {r['diff_ci'][0]:+.3f} to {r['diff_ci'][1]:+.3f}, {r['method']}); "
                   f"bootstrap CI {r['boot_ci'][0]:+.3f} to {r['boot_ci'][1]:+.3f}")
        else:
            r = S.welch(num(A_["mean"]), num(A_["sd"]), num(A_["n"]), num(B_["mean"]), num(B_["sd"]), num(B_["n"]))
            est = f"diff {r['diff']:+.3f} (95% CI {r['diff_ci'][0]:+.3f} to {r['diff_ci'][1]:+.3f}, {r['method']})"
        comps.append((x, r, est))
    adj = S.holm([r["p"] for _, r, _ in comps]) if len(comps) > 1 else [comps[0][1]["p"]]
    better = p["metric"].get("better", "higher")
    # final: the printed last boundary (O'Brien-Fleming spends alpha at earlier looks), as a family-level p cut-off
    # for Holm; a fixed design gives exactly alpha. Interim: |z| against that look's boundary.
    final_cut = 2 * S.norm_sf(p["bounds"][-1]) * max(1, len(arms) - 1)
    verdicts = []
    for (x, r, est), pa_ in zip(comps, adj):
        zlike = abs(r.get("z", r.get("t", 0.0)))
        sig = (pa_ < final_cut) if final else zlike >= p["bounds"][look]
        good = (r["diff"] > 0) == (better == "higher")
        v = ("WIN" if good else "LOSS") if sig else ("NO DIFFERENCE" if final else "not crossed")
        ci = r.get("diff_ci")
        if final and not sig and ci and (ci[0] > 0 or ci[1] < 0):
            v += f" (the unadjusted 95% CI excludes 0, but |z| {zlike:.2f} is under the planned final boundary " \
                 f"{p['bounds'][-1]:.2f}: alpha was spent on the planned looks)"
        verdicts.append((x, v, r, est, pa_))
    g_fail, g_lines = [], []
    for g in p.get("guardrails", []):
        nm, margin = g["name"], g["margin"]
        if f"{nm}_users" not in agg[ctrl]:
            g_lines.append(f"guardrail {nm}: no {nm}_users/{nm}_hits columns: UNCHECKED")
            continue
        for x in arms[1:]:
            r = S.two_prop(num(agg[ctrl][f"{nm}_hits"]), num(agg[ctrl][f"{nm}_users"]),
                           num(agg[x][f"{nm}_hits"]), num(agg[x][f"{nm}_users"]))
            ok = r["diff_ci"][0] > -margin
            g_lines.append(f"guardrail {nm} {x}: {rrlib.pct(r['pa'], 2)} -> {rrlib.pct(r['pb'], 2)}, CI low "
                           f"{r['diff_ci'][0] * 100:+.2f} pts vs margin -{margin * 100:.2f}: {'OK' if ok else 'FAIL'}")
            if not ok:
                g_fail.append(f"{nm}:{x}")
    wins = [x for x, v, *_ in verdicts if v == "WIN"]
    if wins and any(g.split(":")[1] in wins for g in g_fail):
        status = "GUARDRAIL FAIL: the winner hurts a guardrail; do not ship, investigate"
    elif wins:
        best = max((vv for vv in verdicts if vv[1] == "WIN"), key=lambda vv: abs(vv[2]["diff"]))
        status = f"SHIP {best[0]} " + ("(stopped early at a planned look)" if not final else "(planned horizon)")
    elif any(v == "LOSS" for _, v, *_ in verdicts):
        status = f"KEEP {ctrl}: a variant is significantly worse" + ("" if final else " (stopped at a planned look)")
    elif final:
        status = f"NO DIFFERENCE at the planned horizon: keep {ctrl} (or the cheaper option); the CI bounds the effect"
    else:
        status = (f"CONTINUE: look {look + 1} of {len(p['looks'])} did not cross |z| >= {p['bounds'][look]:.2f}; "
                  f"next look at {p['looks'][look + 1]:.0%} of the sample. Estimates stay hidden until then.")
    stop = not status.startswith("CONTINUE")
    if stop:  # a decision: show every estimate
        for x, v, r, est, pa_ in verdicts:
            lines.append(f"{x} vs {ctrl}: {est}; p = {r['p']:.4g}" + (f" (Holm {pa_:.4g})" if len(comps) > 1 else "")
                         + f" [{r['method']}] -> {v}")
        lines += g_lines
    else:  # CONTINUE shows no effect, CI or per-arm label: that would be peeking
        lines.append(f"{len(verdicts)} comparison(s) below the look-{look + 1} boundary; guardrails read at the stop")
    if look is not None and not final:
        taken[str(look)] = {"date": asof.isoformat(), "fraction": round(frac, 4), "status": status}
        rrlib.save_json(lk_path, taken)
    res.update({"fraction": frac, "look": look, "final": final})
    if stop:
        res["comparisons"] = [{"arm": x, "verdict": v, **r} for x, v, r, _, _ in verdicts]
    if final and taken.get("final"):
        lines.append(f"note: the final look was first read on {taken['final']}; a re-read with new data must be reported")
    if final and not taken.get("final"):
        taken["final"] = asof.isoformat()
        rrlib.save_json(lk_path, taken)
    write_result(pp.parent, p, status, lines, res)
    say(status, lines, pp.parent / "RESULT.md")
    return 0


def parse_ci(spec, default_arm):
    """'[ARM:]NAME=LO,HI[,EST]' in percent change (as the Results tab shows) -> (arm, name, lo, hi, est)."""
    head, _, vals = spec.partition("=")
    arm, _, name = head.rpartition(":")
    xs = [float(v.strip().rstrip("%")) for v in vals.split(",") if v.strip()]
    if len(xs) < 2 or xs[0] > xs[1]:
        raise ValueError(f"'{spec}': give LO,HI[,EST] percent change with LO <= HI")
    return arm or default_arm, name.strip().lower(), xs[0], xs[1], xs[2] if len(xs) > 2 else (xs[0] + xs[1]) / 2


def cmd_record(a):
    """Pre-registered readout of a Roblox Experiments test: verdict from the CI of the % change vs control."""
    pp, p = load_plan(a.plan)
    if p is None:
        return bad(f"no plan at {pp}")
    if p.get("source") != "roblox-experiments":
        return bad("record reads Roblox Experiments tests (plan --native); use analyze for exported counts")
    refusal = plan_guard(p, pp, a.accept_edit)
    if refusal:
        return bad(refusal)
    asof, lines = asof_date(a), []
    if asof < dt.date.fromisoformat(p["readout"]):
        status = (f"NOT DONE: running until {p['readout']} ({asof}). Roblox's Results tab is for checking the test runs, "
                  "not for acting: novelty swings in and out of significance.")
        say(status, lines)
        return 0
    try:
        prim = [parse_ci(x, p["arms"][1]) for x in a.metric]
        guards = [parse_ci(x, p["arms"][1]) for x in a.guardrail]
    except ValueError as e:
        return bad(str(e))
    if a.enrolled:
        cnt = dict(x.split("=") for x in a.enrolled.split(","))
        counts = [float(cnt.get(x, 0)) for x in p["arms"]]
        srm = S.srm(counts, p["weights"])
        lines.append(f"SRM check (enrolled): {', '.join(f'{x}={int(n):,}' for x, n in zip(p['arms'], counts))}, p = {srm['p']:.4g}")
        frac = min(n / need for n, need in zip(counts, p["n_per_arm"]))
        lines.append(f"enrolled {frac:.0%} of the planned sample per arm" + (" (under-powered: a NO DIFFERENCE is weak)"
                                                                              if frac < 0.9 else ""))
        if srm["p"] < 0.001:
            status = "INVALID (enrolment ratio mismatch: check targeting and where GetValue is called)"
            write_result(pp.parent, p, status, lines, {"plan": p["name"], "kind": "native"})
            say(status, lines, pp.parent / "RESULT.md")
            return 0
    better = p["metric"].get("better", "higher")
    wins, losses = [], []
    for arm, name, lo, hi, est in prim:
        if name != p.get("primary"):
            lines.append(f"{arm} {name}: {est:+.1f}% (CI {lo:+.1f}% to {hi:+.1f}%): secondary, not a decision metric")
            continue
        sig = lo > 0 or hi < 0
        good = (est > 0) == (better == "higher")
        v = ("WIN" if good else "LOSS") if sig else "NO DIFFERENCE"
        (wins if v == "WIN" else losses if v == "LOSS" else []).append(arm)
        lines.append(f"{arm} {name}: {est:+.1f}% vs control (95% CI {lo:+.1f}% to {hi:+.1f}%) -> {v}")
    if not any(n == p.get("primary") for _, n, *_ in prim):
        return bad(f"no --metric for the pre-registered primary '{p.get('primary')}'")
    if len(p["arms"]) > 2:
        lines.append("two variants: each 95% CI is unadjusted; treat a lone borderline win with care")
    g_fail = []
    margins = {g["name"]: g["margin"] for g in p.get("guardrails", [])}
    for arm, name, lo, hi, est in guards:
        m = margins.get(name)
        ok = m is None or lo > -m
        lines.append(f"guardrail {arm} {name}: {est:+.1f}% (CI low {lo:+.1f}%" + (f" vs margin -{m:g}%)" if m is not None
                                                                                  else ", no planned margin)")
                     + f": {'OK' if ok else 'FAIL'}")
        if not ok:
            g_fail.append(arm)
    for g in margins:
        if not any(n == g for _, n, *_ in guards):
            lines.append(f"guardrail {g}: not given: UNCHECKED")
    if wins and set(wins) & set(g_fail):
        status = "GUARDRAIL FAIL: the winner hurts a guardrail; do not roll it out, investigate"
    elif wins:
        status = f"SHIP {wins[0]} (planned duration): roll out with Make decision in Creator Hub (owner)"
    elif losses:
        status = f"KEEP {p['control']}: a variant is significantly worse"
    else:
        status = f"NO DIFFERENCE at the planned duration: keep {p['control']} (or the cheaper option)"
    write_result(pp.parent, p, status, lines, {"plan": p["name"], "kind": "native", "final": True})
    say(status, lines, pp.parent / "RESULT.md")
    return 0


def cmd_compare(a):
    """Descriptive read of adaptive traffic (thumbnail personalization): per-variant rate with CI, no verdict."""
    rows = read_rows(a.data)
    if not rows:
        return bad(f"{a.data}: no rows")
    key_n = "users" if "users" in rows[0] else next((k for k in ("n",) if k in rows[0]), None)
    key_x = "conversions" if "conversions" in rows[0] else None
    if "arm" not in rows[0] or not key_n or not key_x:
        return bad(f"{a.data}: needs variant,impressions,qualified_plays (aliases allowed; have {', '.join(rows[0])})")
    p = None
    if a.plan:
        pp, p = load_plan(a.plan)
        if p is None:
            return bad(f"no plan at {pp}")
    stats = [(r["arm"], num(r[key_n]), num(r[key_x]), r) for r in rows if num(r[key_n])]
    stats = [(v, n, x, x / n, S.wilson(x, n), r) for v, n, x, r in stats]
    judged = [t for t in stats if t[1] >= a.min_n] or stats
    best = max(judged, key=lambda t: t[3])
    lines = ["descriptive only: traffic was adaptive (personalization), so there is no SRM check and no winner call; "
             "each rate is conditional on the players Roblox chose to show it to (conversions / impressions)"]
    losers = []
    for v, n, x, r, (lo, hi), _ in sorted(stats, key=lambda t: -t[3]):
        flag = ""
        if v != best[0] and hi < best[4][0] and n >= a.min_n:
            flag = "  <- clearly below the best: a candidate to replace at the next update"
            losers.append(v)
        elif n < a.min_n:
            flag = f"  (under {a.min_n:,} impressions: too early to judge)"
        lines.append(f"{v:18} {r:7.2%}  95% CI {lo:.2%}-{hi:.2%}  n {n:,.0f}{flag}")
    guards = [g["name"] for g in (p or {}).get("guardrails", [])]
    for g in guards:
        if f"{g}_users" in rows[0] and f"{g}_hits" in rows[0]:
            for v, *_rest in stats:
                rr = _rest[-1]
                gn, gx = num(rr[f"{g}_users"]), num(rr[f"{g}_hits"])
                lo, hi = S.wilson(gx, gn) if gn else (0, 1)
                lines.append(f"guardrail {g} {v}: {gx / gn if gn else 0:.2%} (95% CI {lo:.2%}-{hi:.2%}, n {gn:,.0f})")
        elif g in rows[0]:
            lines.append(f"guardrail {g}: " + ", ".join(f"{t[0]} {t[5][g]}" for t in stats) +
                         " (aggregate export: no CI; check the players each thumbnail brings before it wins)")
        else:
            lines.append(f"guardrail {g}: no '{g}' column: UNCHECKED")
    lines.append("Roblox advice: keep several thumbnails active; swap losers at the next major update, not mid-week.")
    status = (f"DESCRIPTIVE: clearly below the best: {', '.join(losers)}" if losers else
              "DESCRIPTIVE: no thumbnail clearly below the best yet")
    say(status, lines)
    if p:
        final = asof_date(a) >= dt.date.fromisoformat(p["readout"])
        res = {"plan": p["name"], "kind": "descriptive", "final": final, "losers": losers,
               "variants": [{"variant": v, "n": n, "x": x, "rate": r, "ci": ci} for v, n, x, r, ci, _ in stats]}
        write_result(pp.parent, p, status if final else f"INTERIM ({asof_date(a)}, readout {p['readout']}): {status}",
                     lines, res)
        print(f"wrote {pp.parent / 'RESULT.md'}")
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
    p.add_argument("--replace", action="store_true", help="overwrite an existing plan (old one kept in history/)")
    p.add_argument("--native", action="store_true", help="a Roblox Experiments (Creator Hub) test")
    p.add_argument("--primary", help="--native: the Results-tab metric that decides (d1, d7, arpu, ...)")
    z = sub.add_parser("analyze")
    z.add_argument("plan")
    z.add_argument("--data", required=True)
    z.add_argument("--asof", help="readout date check (default today)")
    z.add_argument("--accept-edit", action="store_true")
    rc = sub.add_parser("record")
    rc.add_argument("plan")
    rc.add_argument("--metric", action="append", default=[], required=True,
                    help="[ARM:]NAME=LO,HI[,EST] percent change vs control, e.g. B:d1=8.02,22.03,17.4")
    rc.add_argument("--guardrail", action="append", default=[], help="[ARM:]NAME=LO,HI[,EST] percent change")
    rc.add_argument("--enrolled", help="A=5021,B=4987 (Overview tab) for the ratio check")
    rc.add_argument("--asof")
    rc.add_argument("--accept-edit", action="store_true")
    r = sub.add_parser("srm")
    r.add_argument("--counts", required=True)
    r.add_argument("--weights")
    c = sub.add_parser("compare")
    c.add_argument("--data", required=True, help="CSV: variant,impressions,qualified_plays")
    c.add_argument("--min-n", type=int, default=2000)
    c.add_argument("--plan", help="the pre-registered plan folder: writes result.json/RESULT.md there")
    c.add_argument("--asof")
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
    return {"size": cmd_size, "plan": cmd_plan, "analyze": cmd_analyze, "record": cmd_record, "compare": cmd_compare,
            "srm": cmd_srm, "peek": cmd_peek, "assign": cmd_assign}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
