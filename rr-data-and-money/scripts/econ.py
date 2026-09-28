#!/usr/bin/env python3
"""Risky Rails money: economy simulation, value ladder and the money gate (policy guardrails).

  econ.py validate [--config F] [--catalogue F]        canon check of both presets; lists every assumed value and
                                                       every override of a canon value
  econ.py sim      [--config F] [--out DIR] [--set path=value ...] [--sweep path=v1,v2,...] [--quick]
                   population (installs x days, retention fitted to canon D1/D7/D30, payers, prompts) +
                   engaged cohorts (pacing without churn; non-payers vs Double Fare) -> faucets, sinks,
                   inflation, time-to-first-upgrade, unlock pacing, net coins per run by difficulty, runs started
                   short of the supply kit; PASS/WATCH/MISS vs canon; price suggestions. Writes econ.json,
                   ECON_REPORT.md and charts; a sweep writes sweep-<path>.md (same sample and seed on every row).
  econ.py ladder   [--catalogue F] [--state launch|all|live,proposed,...]   value ladder: one-time price steps,
                   entry/anchor, recurring items apart, Robux -> USD per sale, whale-total gap
  econ.py guard    [--catalogue F] [--config F] [--sim econ.json | --run-fare N] [--src LUAU_DIR] [--out DIR] [--gate]
                   money gate: D-007 (time, status, identity only), co-op pay-to-win, paid random items,
                   prompt rules, fare-pack rules, Daily Line fairness, departures from canon prices
                   -> MONEY_GATE.md/.json (PASS/HOLD/FAIL). --gate: exit 1 on FAIL, 3 on HOLD (pre-flight use).

Presets: rrlib.preset() order: --config/--catalogue, $RR_ECONOMY/$RR_CATALOGUE, <data root>/presets/ (a mission's
copy), else the skill's presets. --set/--sweep paths are dotted and must exist (difficulty.Easy.fare_full,
unlocks.loco_2.price or unlocks.0.price); an override of a canon value is reported as one. Default out:
<data root>/econ/<date>. Only the owner changes live prices; this prepares the numbers.
Exit 0 = ran (gate verdict in the file unless --gate), 1 = errors.
"""
import argparse, datetime as dt, hashlib, json, math, random, re, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rrlib  # noqa: E402
import svgchart as C  # noqa: E402

DIFFS = ["Easy", "Medium", "Hard", "Insane"]


def load_cfg(path=None, sets=()):
    """(raw preset, resolved values, Refs). Raises rrlib.PathError on a --set path that does not exist."""
    src = rrlib.preset("economy.json", path, "RR_ECONOMY")
    raw = rrlib.load_json(src)
    base = rrlib.load_json(rrlib.PRESETS / "economy.json")
    for s in sets:
        k, _, v = s.partition("=")
        rrlib.set_path(raw, k, v, base)
    refs = rrlib.Refs(None, *rrlib.base_refs(rrlib.PRESETS / "economy.json"))
    refs.source = src
    return raw, refs.resolve(raw), refs


def kit_split(c):
    """Players sharing one run's supply kit: kits are per train (one Depotron order at a time), so each player
    pays kit / crew_mean on average when kit_paid = split (assumed). Old presets without it: each pays all."""
    return c.get("crew_mean", 3) if c.get("kit_paid", "each") == "split" else 1


def oq_default(bible, oq):
    txt = bible.get_id(oq) if oq and bible.ok() else None
    m = re.search(r"default:\s*([A-Z])\b", txt or "")
    return m.group(1) if m else None


def q(xs, p):
    if not xs:
        return None
    xs = sorted(xs)
    i = (len(xs) - 1) * p
    lo, hi = math.floor(i), math.ceil(i)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def poisson(rng, lam):
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


class Player:
    __slots__ = ("install", "life", "balance", "runs", "minutes", "k", "double", "payer", "skill", "best",
                 "df_shown", "spend_rs", "unlock_at", "pack_day", "short_runs")

    def __init__(self, install, life, payer, skill, start):
        self.install, self.life, self.payer, self.skill = install, life, payer, skill
        self.balance, self.runs, self.minutes, self.k = float(start), 0, 0.0, 0
        self.double, self.best, self.df_shown, self.spend_rs = False, 0.0, False, 0
        self.unlock_at, self.pack_day, self.short_runs = [], -1, 0


class Econ:
    def __init__(self, c, seed=None):
        self.c = c
        self.rng = random.Random(c["horizon"]["seed"] if seed is None else seed)
        ss = c["session"]
        self.run_min = ss["run_min"] + (ss["queue_s"] + ss["board_s"] + ss["results_s"]) / 60
        cv = c["fare_cv"]
        self.sig = math.sqrt(math.log(1 + cv * cv))
        self.prices = [u["price"] for u in c["unlocks"]]
        r = c["retention"]
        # power law r(t) = a * t^-b through D1, D7, D30 (least squares in log space)
        pts = [(1, r["d1"]), (7, r["d7"]), (30, r["d30"])]
        xs, ys = [math.log(t) for t, _ in pts], [math.log(v) for _, v in pts]
        mx, my = sum(xs) / 3, sum(ys) / 3
        b = -sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
        self.ret_a, self.ret_b = math.exp(my + b * mx), b
        self.q = r["play_prob_retained"]

    def retention(self, t):
        return self.ret_a * t ** (-self.ret_b)

    def lifetime(self, horizon):
        u = self.rng.random()
        if u > self.retention(1) / self.q:
            return 0
        return min(horizon, int((self.ret_a / (self.q * u)) ** (1 / self.ret_b)))

    def pick_diff(self, runs):
        mix = [m for m in self.c["difficulty_mix"] if runs >= m["from_run"]][-1]["mix"]
        x, acc = self.rng.random(), 0.0
        for d, w in mix.items():
            acc += w
            if x < acc:
                return d
        return list(mix)[-1]

    def run(self, p, day, st, allow_buy=True):
        c, rng = self.c, self.rng
        d = self.pick_diff(p.runs)
        D = c["difficulty"][d]
        cost, short, split = 0.0, False, kit_split(c)
        for item, n in D["kit"].items():
            n = n / split
            cnt = int(n) + (1 if rng.random() < n - int(n) else 0)
            for _ in range(cnt):
                pr = c["prices"][item]
                if p.balance - cost >= pr:
                    cost += pr
                else:
                    short = True
        p.balance -= cost
        st["burn_supplies"] += cost
        if short:
            p.short_runs += 1
            st["short"] += 1
        if p.runs == 0:
            st["first_runs"] += 1
            st["short_first"] += 1 if short else 0
        pa = min(0.97, D["p_arrive"] * p.skill * (c["short_penalty"] if short else 1.0))
        arrive = rng.random() < pa
        full = D["fare_full"] * math.exp(rng.gauss(-self.sig * self.sig / 2, self.sig))
        if arrive:
            fare = full
        else:
            opt = c["failed_trip"]["option"]
            lo, hi = c["failed_trip"]["banked_share"]
            fare = 0.0 if opt == "B" else full * rng.uniform(lo, hi) * (1 - (c["failed_trip"]["penalty"] if opt == "C" else 0))
        base = fare
        if p.double:
            fare *= c["double_fare"]["mult"]
            st["mint_pass"] += fare - base
        st["mint_play"] += base
        st["arrive"] += 1 if arrive else 0
        st["fares"].append(base)
        if arrive:
            st["arrive_fares"].append(base)
        falls = poisson(rng, c["recovery"]["falls_per_run"])
        fee = min(p.balance + fare, falls * c["recovery"]["fee"])
        p.balance += fare - fee
        st["burn_fees"] += fee
        bd = st["by_diff"].setdefault(d, [0, 0.0, 0.0, 0.0])
        bd[0] += 1
        bd[1] += base
        bd[2] += cost
        bd[3] += fee
        p.runs += 1
        p.minutes += self.run_min
        st["runs"] += 1
        while p.k < len(self.prices) and p.balance >= self.prices[p.k]:
            p.balance -= self.prices[p.k]
            st["burn_unlock"] += self.prices[p.k]
            p.unlock_at.append((p.runs, p.minutes, day))
            p.k += 1
        if not allow_buy:
            p.best = max(p.best, base)
            return
        rules, buy = c["rules"], c["buying"]
        if p.runs >= rules["prompt_after_run"]:
            if not p.double and not p.df_shown and base > p.best:
                p.df_shown = True
                st["prompts"] += 1
                if p.payer and rng.random() < buy["p_double_fare"]:
                    p.double = True
                    p.spend_rs += c["double_fare"]["price_rs"]
                    st["rev"] += c["double_fare"]["price_rs"]
                    st["payers"].add(id(p))
            if p.k < len(self.prices) and p.pack_day != day:
                gap = self.prices[p.k] - p.balance
                if 0 < gap < rules["pack_short_pct"] / 100 * self.prices[p.k]:
                    p.pack_day = day
                    st["prompts"] += 1
                    if p.payer and rng.random() < buy["p_pack"]:
                        packs = sorted(c["fare_packs"], key=lambda x: x["fare"])
                        pk = next((x for x in packs if x["fare"] >= gap), packs[-1])
                        p.balance += pk["fare"]
                        p.spend_rs += pk["price_rs"]
                        st["rev"] += pk["price_rs"]
                        st["mint_paid"] += pk["fare"]
                        st["payers"].add(id(p))
                        while p.k < len(self.prices) and p.balance >= self.prices[p.k]:
                            p.balance -= self.prices[p.k]
                            st["burn_unlock"] += self.prices[p.k]
                            p.unlock_at.append((p.runs, p.minutes, day))
                            p.k += 1
        p.best = max(p.best, base)

    def newday(self):
        return {"dau": 0, "runs": 0, "arrive": 0, "mint_play": 0.0, "mint_pass": 0.0, "mint_paid": 0.0,
                "burn_supplies": 0.0, "burn_unlock": 0.0, "burn_fees": 0.0, "rev": 0, "payers": set(), "short": 0,
                "prompts": 0, "fares": [], "arrive_fares": [], "balances": [], "maxed": 0, "first_runs": 0,
                "short_first": 0, "by_diff": {}}

    def population(self):
        c, rng = self.c, self.rng
        days, inst = c["horizon"]["days"], c["horizon"]["installs_per_day"]
        lo, hi = c["skill_range"]
        players, daily = [], []
        for day in range(days):
            for _ in range(inst):
                players.append(Player(day, self.lifetime(days), rng.random() < c["buying"]["payer_share"],
                                      rng.uniform(lo, hi), c["start_coins"]))
            st = self.newday()
            for p in players:
                age = day - p.install
                if age < 0 or age > p.life:
                    continue
                if age > 0 and rng.random() >= self.q:
                    continue
                st["dau"] += 1
                if p.payer and not p.double and rng.random() < c["buying"]["p_organic_daily"]:
                    p.double = True
                    p.spend_rs += c["double_fare"]["price_rs"]
                    st["rev"] += c["double_fare"]["price_rs"]
                    st["payers"].add(id(p))
                lam = c["session"]["runs_day0_mean"] if age == 0 else c["session"]["runs_later_mean"]
                for _ in range(1 + poisson(rng, max(0.0, lam - 1))):
                    self.run(p, day, st)
                st["balances"].append(p.balance)
                st["maxed"] += 1 if p.k >= len(self.prices) else 0
            daily.append(st)
        return players, daily

    def engaged(self, n, payer=False):
        c = self.c
        lo, hi = c["skill_range"]
        hours, per_day = c["session"]["engaged_hours"], c["session"]["engaged_runs_per_day"]
        st = self.newday()
        ps = []
        for _ in range(n):
            p = Player(0, 10 ** 6, payer, self.rng.uniform(lo, hi), c["start_coins"])
            day = 0
            while p.minutes < hours * 60:
                for _ in range(per_day):
                    if payer and not p.double and p.runs >= c["rules"]["prompt_after_run"]:
                        p.double = True
                    self.run(p, day, st, allow_buy=False)
                day += 1
            ps.append(p)
        return ps, st


def simulate(c, n_engaged=800, bible=None):
    E = Econ(c)
    players, daily = E.population()
    eng, est = E.engaged(n_engaged)
    engp, _ = E.engaged(max(200, n_engaged // 3), payer=True)
    t = c["targets"]
    R = {"assumed_runtime": {}, "checks": []}
    tot = lambda k: sum(d[k] for d in daily)  # noqa: E731
    mint = tot("mint_play") + tot("mint_pass") + tot("mint_paid")
    burn = tot("burn_supplies") + tot("burn_unlock") + tot("burn_fees")
    dau = [d["dau"] for d in daily]
    installs = len(players)
    first = [p.unlock_at[0] for p in players if p.unlock_at]
    day0 = sum(1 for p in players if p.unlock_at and p.unlock_at[0][2] == p.install) / installs
    payers_daily = [len(d["payers"]) / d["dau"] for d in daily if d["dau"]]
    rev = tot("rev")
    share, devex = c["platform"]["creator_share"], c["platform"]["devex_usd"]
    last7 = daily[-7:]
    maxed = sum(d["maxed"] for d in last7) / max(1, sum(d["dau"] for d in last7))
    bal = [q(d["balances"], 0.5) for d in daily]
    R["population"] = {
        "installs": installs, "days": len(daily), "avg_dau": statistics.mean(dau), "runs": tot("runs"),
        "completion": tot("arrive") / max(1, tot("runs")), "minted": mint, "burned": burn,
        "sink_source_ratio": burn / mint if mint else None, "paid_faucet_share": tot("mint_paid") / mint if mint else 0,
        "pass_faucet_share": tot("mint_pass") / mint if mint else 0,
        "first_unlock_reach_day0": day0, "first_unlock_reach_ever": len(first) / installs,
        "short_run_share": tot("short") / max(1, tot("runs")), "payer_conversion": statistics.mean(payers_daily),
        "revenue_rs_gross": rev, "revenue_rs_earned": rev * share, "revenue_usd": rev * share * devex,
        "arpdau_earned": rev * share / max(1, sum(dau)), "maxed_share_last7": maxed,
        "median_balance_first7": statistics.mean([b for b in bal[:7] if b is not None] or [0]),
        "median_balance_last7": statistics.mean([b for b in bal[-7:] if b is not None] or [0]),
        "short_first_run_share": tot("short_first") / max(1, tot("first_runs")),
    }
    fares = sorted(est["arrive_fares"])
    run_fare = statistics.mean(est["fares"])
    R["engaged"] = {"players": len(eng), "mean_fare_per_run": run_fare, "median_fare_per_run": q(est["fares"], 0.5),
                    "median_arriving_fare": q(fares, 0.5)}
    unl = []
    for k, u in enumerate(c["unlocks"]):
        hrs = [p.unlock_at[k][1] / 60 for p in eng if len(p.unlock_at) > k]
        runs = [p.unlock_at[k][0] for p in eng if len(p.unlock_at) > k]
        hrs_p = [p.unlock_at[k][1] / 60 for p in engp if len(p.unlock_at) > k]
        unl.append({"id": u["id"], "price": u["price"], "reached": len(hrs) / len(eng), "h_p50": q(hrs, 0.5),
                    "h_p90": q(hrs, 0.9), "runs_p50": q(runs, 0.5), "runs_p90": q(runs, 0.9),
                    "payer_h_p50": q(hrs_p, 0.5), "runs_of_arriving_fare": u["price"] / q(fares, 0.5) if fares else None})
    R["unlocks"] = unl
    # checks vs canon
    chk = R["checks"]

    def add(name, status, detail, canon):
        chk.append({"check": name, "status": status, "detail": detail, "canon": canon})
    u0 = unl[0]
    r_ok = u0["runs_p50"] is not None and u0["runs_p50"] <= t["first_unlock_runs"] * 1.25
    m_ok = u0["h_p50"] is not None and u0["h_p50"] * 60 <= t["first_unlock_min"]
    first_st = "PASS" if r_ok and m_ok else ("WATCH" if u0["runs_p50"] and u0["runs_p50"] <= t["first_unlock_runs"] * 1.75 else "MISS")
    add("time to first upgrade", first_st,
        f"{u0['id']}: median {u0['runs_p50']} runs / {u0['h_p50'] * 60:.0f} min (p90 {u0['runs_p90']} runs); target about "
        f"{t['first_unlock_runs']} runs inside {t['first_unlock_min']} min" if u0["h_p50"] else "never reached",
        "gameplay.progress.first_unlock")
    add("new players who get it on day 0", "INFO", f"{day0:.0%} of installs (ever: {len(first) / installs:.0%}); day-0 runs "
        f"mean {c['session']['runs_day0_mean']} (assumed)", "gameplay.progress.first_unlock")
    # supply kit: a run started short is a harder run the player did not choose
    P = R["population"]
    sh, sh1 = P["short_run_share"], P["short_first_run_share"]
    add("runs started short of the supply kit", "PASS" if sh < 0.05 else ("WATCH" if sh < 0.15 else "MISS"),
        f"{sh:.0%} of runs (first runs {sh1:.0%}); start_coins {c.get('start_coins', 0):,.0f}; kit paid "
        + (f"split over a crew of {kit_split(c):g} (assumed)" if kit_split(c) > 1 else "in full by every player (assumed)")
        + "; target under 5%", "OQ-049")
    # risk/reward: net coins per run by difficulty (engaged non-payers: base fare - kit - recovery fees)
    bd = est["by_diff"]
    net = {d: (bd[d][1] - bd[d][2] - bd[d][3]) / bd[d][0] for d in DIFFS if d in bd and bd[d][0] >= 50}
    R["net_by_difficulty"] = {d: {"runs": bd[d][0], "fare": bd[d][1] / bd[d][0], "kit": bd[d][2] / bd[d][0],
                                  "fees": bd[d][3] / bd[d][0], "net": net.get(d)} for d in DIFFS if d in bd}
    order = [d for d in DIFFS if d in net]
    steps = [(a_, b_, net[b_] / net[a_] if net[a_] > 0 else None) for a_, b_ in zip(order, order[1:])]
    inverted = [f"{b_} < {a_}" for a_, b_, _ in steps if net[b_] <= net[a_]]
    flat = [f"{b_} ~ {a_}" for a_, b_, r in steps if r is not None and net[b_] > net[a_] and r < 1.05]
    add("harder pays more", "MISS" if inverted else ("WATCH" if flat else "PASS"),
        "net coins per run " + " / ".join(f"{d} {net[d]:,.0f}" for d in order)
        + (f": INVERTED ({', '.join(inverted)})" if inverted else f": flat ({', '.join(flat)})" if flat else "")
        + (f"; kit split over crew {kit_split(c):g} (assumed)" if kit_split(c) > 1 else "; each player pays the whole kit (assumed)"),
        "gameplay.difficulty.band_*")
    ft = c["failed_trip"]
    dflt = oq_default(bible, ft.get("question")) if bible else None
    if dflt and ft["option"] != dflt:
        add("failed trip rule", "WATCH", f"option {ft['option']} differs from the {ft['question']} default {dflt}: label "
            f"every result 'assumed ({ft['question']} option {ft['option']}, owner decides)'", ft["question"])
    prev = None
    sugg, sug_price = [], {}
    net_h = sum(v[1] - v[2] - v[3] for v in bd.values()) / max(1e-9, sum(p.minutes for p in eng) / 60)
    if first_st != "PASS" and u0["runs_p50"]:
        ratio = min(t["first_unlock_runs"] / u0["runs_p50"], t["first_unlock_min"] / (u0["h_p50"] * 60))
        sug_price[u0["id"]] = (round(u0["price"] * ratio, -2), f"for about {t['first_unlock_runs']} runs / "
                                                               f"{t['first_unlock_min']} min")
    for k, u in enumerate(unl):
        if u["h_p50"] is None:
            add(f"pacing {u['id']}", "MISS", f"not reached within {c['session']['engaged_hours']} h of play", "gameplay.progress.pacing")
            if k:
                sug_price[u["id"]] = (round(net_h * t["unlock_gap_h"], -2), f"about {t['unlock_gap_h']} h of net earnings "
                                                                             f"({net_h:,.0f} coins/h)")
            continue
        if prev is not None and prev <= t["pacing_through_h"]:
            gap = u["h_p50"] - prev
            ratio = gap / t["unlock_gap_h"]
            stt = "PASS" if 0.5 <= ratio <= 1.5 else ("WATCH" if 0.33 <= ratio <= 2 else "MISS")
            add(f"pacing {u['id']}", stt, f"+{gap:.1f} h after the previous unlock (at {u['h_p50']:.1f} h); target about "
                f"{t['unlock_gap_h']} h", "gameplay.progress.pacing")
            if stt != "PASS" and gap > 0:
                sug_price[u["id"]] = (round(u["price"] * t["unlock_gap_h"] / gap, -2), f"for a {t['unlock_gap_h']} h gap")
        prev = u["h_p50"]
        if u["runs_of_arriving_fare"] and u["runs_of_arriving_fare"] > t["max_item_runs"]:
            add(f"item size {u['id']}", "MISS", f"{u['runs_of_arriving_fare']:.1f} successful runs > {t['max_item_runs']}",
                "gameplay.progress.pacing")
    floor = 0
    for u in unl:  # suggestions keep the ladder in order: each unlock costs at least 5% more than the one before
        price, why = sug_price.get(u["id"], (u["price"], None))
        if price < floor:
            price, why = round(floor, -2) + 100, (why or "current price") + f"; raised to stay above the previous unlock"
        if why:
            sugg.append(f"{u['id']}: {u['price']:,.0f} -> about {price:,.0f} {why}")
        floor = price * 1.05
    big = max(fp["fare"] for fp in c["fare_packs"])
    cap = c["rules"]["pack_cap_runs"] * (run_fare or 0)
    add("fare pack cap", "PASS" if big <= cap else ("WATCH" if big <= cap * 1.1 else "MISS"),
        f"largest pack {big:,.0f} vs {c['rules']['pack_cap_runs']} x run fare {run_fare:,.0f} (mean, first "
        f"{c['session']['engaged_hours']} h) = {cap:,.0f}" + (" (inside the 10% tolerance for canon 'about')"
                                                             if cap < big <= cap * 1.1 else ""), "economy.passes.fare_packs")
    payer_extra = statistics.mean([p.balance + sum(u["price"] for u in c["unlocks"][:p.k]) for p in engp]) - \
        statistics.mean([p.balance + sum(u["price"] for u in c["unlocks"][:p.k]) for p in eng])
    df_rate = payer_extra / c["double_fare"]["price_rs"] if payer_extra > 0 else 0
    worst = max(fp["fare"] / fp["price_rs"] for fp in c["fare_packs"])
    add("fare packs vs playing well", "PASS" if worst <= df_rate else "WATCH",
        f"best pack {worst:.1f} fare/R$ vs Double Fare {df_rate:.1f} fare/R$ over {c['session']['engaged_hours']} h of play "
        f"(interpretation: buying fare must not beat earning it with the pass)", "economy.rules.fair_packs")
    comp = P["completion"]
    add("completion", "PASS" if t["completion"][0] <= comp <= t["completion"][1] else "WATCH",
        f"{comp:.0%} of runs arrive; canon {t['completion'][0]:.0%}-{t['completion'][1]:.0%}", "release.kpi.completion")
    pc = P["payer_conversion"]
    add("payer conversion", "PASS" if pc >= t["payer_conversion"] else "WATCH",
        f"{pc:.2%} of DAU pay per day (driven by assumed buying odds)", "release.kpi.conversion")
    ms = P["maxed_share_last7"]
    top = unl[-1]
    if top["reached"] < 0.5:
        add("sink left for veterans", "N/A", f"the top unlock ({top['id']}) is reached by {top['reached']:.0%} of engaged "
            f"players in {c['session']['engaged_hours']} h, so nobody runs out of things to buy yet; re-check once pacing "
            "passes", "economy.passes.whale_total")
    else:
        add("sink left for veterans", "PASS" if ms < 0.2 else "WATCH", f"{ms:.0%} of active players own every unlock in "
            f"the last week; balances {P['median_balance_first7']:,.0f} -> {P['median_balance_last7']:,.0f} "
            f"(median, first vs last week)", "economy.passes.whale_total")
    R["suggestions"] = sugg
    ph = [(u["payer_h_p50"] / u["h_p50"]) for u in unl if u["payer_h_p50"] and u["h_p50"]]
    R["pay_to_skip"] = statistics.mean(ph) if ph else None
    R["daily"] = [{k: (len(v) if isinstance(v, set) else v) for k, v in d.items()
                   if k not in ("fares", "arrive_fares", "balances", "by_diff")}
                  | {"bal_p50": q(d["balances"], 0.5), "bal_p90": q(d["balances"], 0.9)} for d in daily]
    return R


def report(raw, c, refs, R, out):
    out.mkdir(parents=True, exist_ok=True)
    P = R["population"]
    labs = [f"d{i}" for i in range(len(R["daily"]))]
    (out / "econ-flows.svg").write_text(C.columns(
        "Coins minted vs burned per day", labs,
        [("minted", [d["mint_play"] + d["mint_pass"] + d["mint_paid"] for d in R["daily"]]),
         ("burned", [d["burn_supplies"] + d["burn_unlock"] + d["burn_fees"] for d in R["daily"]])],
        lambda v: rrlib.fmt_num(v), subtitle=f"sim population, {P['installs']:,} installs; sink/source {P['sink_source_ratio']:.2f}"),
        encoding="utf-8")
    (out / "econ-balance.svg").write_text(C.line_chart(
        "Coin balance of active players", labs, [("median", [d["bal_p50"] for d in R["daily"]]),
                                                 ("90th percentile", [d["bal_p90"] for d in R["daily"]])],
        lambda v: rrlib.fmt_num(v), subtitle="end of day; rising p90 with nothing left to buy = inflation"), encoding="utf-8")
    (out / "econ-pacing.svg").write_text(C.hbar(
        "Median hours of play to each unlock", [(u["id"], u["h_p50"] or 0, f"{u['runs_p50']:.0f} runs" if u["runs_p50"] else "not reached")
                                                for u in R["unlocks"]],
        lambda v: f"{v:.1f} h", subtitle=f"engaged non-payers; canon target about {c['targets']['unlock_gap_h']} h apart"),
        encoding="utf-8")
    L = [f"# Risky Rails economy sim ({dt.date.today().isoformat()})", "",
         f"Config hash {hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()[:12]}; seed {c['horizon']['seed']}; "
         f"retention fitted r(t) = {Econ(c).ret_a:.3f} t^-{Econ(c).ret_b:.3f} through canon D1/D7/D30.", "",
         "## Checks vs canon", "", rrlib.md_table(["check", "status", "detail", "canon"],
                                                  [(x["check"], x["status"], x["detail"], f"`{x['canon']}`") for x in R["checks"]]),
         "", "## Population", "",
         rrlib.md_table(["metric", "value"], [
             ("installs / avg DAU", f"{P['installs']:,} / {P['avg_dau']:,.0f}"),
             ("runs, completion", f"{P['runs']:,}, {P['completion']:.0%}"),
             ("minted / burned coins", f"{P['minted']:,.0f} / {P['burned']:,.0f} (sink/source {P['sink_source_ratio']:.2f})"),
             ("paid share of faucet (packs / Double Fare bonus)", f"{P['paid_faucet_share']:.1%} / {P['pass_faucet_share']:.1%}"),
             ("runs started short of the supply kit (first runs)", f"{P['short_run_share']:.0%} ({P['short_first_run_share']:.0%})"),
             ("payer conversion (daily)", f"{P['payer_conversion']:.2%}"),
             ("revenue gross / earned R$", f"{P['revenue_rs_gross']:,.0f} / {P['revenue_rs_earned']:,.0f} (~${P['revenue_usd']:,.2f} DevEx)"),
             ("earned ARPDAU", f"{P['arpdau_earned']:.3f} R$"),
             ("pay-to-skip (payer / non-payer hours per unlock)", f"{R['pay_to_skip']:.2f}" if R["pay_to_skip"] else "n/a")]),
         "", "## Unlock pacing (engaged cohort, no churn)", "",
         rrlib.md_table(["unlock", "price", "reached", "median h", "p90 h", "median runs", "Double Fare median h", "successful runs"],
                        [(u["id"], f"{u['price']:,.0f}", f"{u['reached']:.0%}", f"{u['h_p50']:.1f}" if u["h_p50"] else "-",
                          f"{u['h_p90']:.1f}" if u["h_p90"] else "-", f"{u['runs_p50']:.0f}" if u["runs_p50"] else "-",
                          f"{u['payer_h_p50']:.1f}" if u["payer_h_p50"] else "-",
                          f"{u['runs_of_arriving_fare']:.1f}" if u["runs_of_arriving_fare"] else "-") for u in R["unlocks"]])]
    nb = R.get("net_by_difficulty", {})
    if nb:
        L += ["", "## Coins per run by difficulty (engaged non-payers)", "",
              rrlib.md_table(["difficulty", "runs", "fare banked", "supply kit", "recovery fees", "net", "vs Easy"],
                             [(d, f"{v['runs']:,}", f"{v['fare']:,.0f}", f"{v['kit']:,.0f}", f"{v['fees']:,.0f}",
                               f"{v['net']:,.0f}" if v["net"] is not None else "-",
                               f"{v['net'] / nb['Easy']['net']:.2f}x" if v["net"] is not None and nb.get("Easy", {}).get("net")
                               else "-") for d, v in nb.items()]),
              "", f"Kit per player = kit / {kit_split(c):g} (`kit_paid` {c.get('kit_paid', 'each')}, assumed): the sign "
              "of a low tier's net depends on it; the order of the tiers is the robust read."]
    if R["suggestions"]:
        L += ["", "## Price suggestions (owner decides; re-run after changing)", ""] + [f"- {s}" for s in R["suggestions"]]
    if refs.overrides:
        L += ["", "## Overrides of canon (owner decides)", ""] + [f"- `{w}` = {v} instead of canon `{k}` = \"{cv}\""
                                                                   for w, v, k, cv in refs.overrides]
    L += ["", "## Assumed (no canon yet)", ""] + [f"- `{w}` = {v}: {why}" for w, v, why in refs.assumed]
    if refs.warnings:
        L += ["", "## Canon warnings", ""] + [f"- {w}" for w in refs.warnings]
    L += ["", "![flows](econ-flows.svg)", "![balance](econ-balance.svg)", "![pacing](econ-pacing.svg)"]
    (out / "ECON_REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    rrlib.save_json(out / "econ.json", R)


def catalogue_warnings(cat, bible):
    """A launch-state product priced from a canon key that says post-launch is an owner decision, not a ladder step."""
    out = []
    for p in cat["products"]:
        key = p["price_rs"].get("canon") if isinstance(p.get("price_rs"), dict) else None
        f = bible.fact(key) if key and bible.ok() else None
        if f and re.search(r"post-?launch", f"{f.get('value', '')} {f.get('note') or ''}", re.I) and \
                p.get("state") in ("live", "proposed"):
            out.append(f"products[{p['id']}]: state {p['state']} but canon {key} says post-launch: an owner decision "
                       "(show it as an owner option, labelled)")
    return out


def cmd_validate(a):
    try:
        _, _, refs = load_cfg(a.config)
    except rrlib.PathError as e:
        return print(f"FAIL {e}") or 1
    raw_cat, _, r2 = load_catalogue(a.catalogue, refs.bible)
    E, W = refs.errors + r2.errors, refs.warnings + r2.warnings + catalogue_warnings(raw_cat, refs.bible)
    print(f"  presets: {refs.source} + {r2.source}")
    for w in W:
        print("  W", w)
    for e in E:
        print("  E", e)
    print(f"  {len(refs.canon) + len(r2.canon)} canon-checked values, {len(refs.assumed) + len(r2.assumed)} assumed:")
    for w, v, why in refs.assumed + r2.assumed:
        print(f"    assumed {w} = {v}")
    print(f"{'PASS' if not E else 'FAIL'} economy + catalogue presets: {len(E)} errors, {len(W)} warnings")
    return 1 if E else 0


def sweep(a, refs):
    path, _, vals = a.sweep.partition("=")
    rows, sample = [], None
    for v in vals.split(","):
        _, c2, _ = load_cfg(a.config, list(a.set) + [f"{path}={v}"])
        if a.quick:
            c2["horizon"]["installs_per_day"] = max(50, c2["horizon"]["installs_per_day"] // 4)
        n_eng = 400 if a.quick else 800
        R = simulate(c2, n_eng, refs.bible)
        sample = (f"{R['population']['installs']:,} installs over {c2['horizon']['days']} days + {n_eng} engaged "
                  f"players, seed {c2['horizon']['seed']} on every row")
        u, P, st = R["unlocks"], R["population"], {x["check"]: x["status"] for x in R["checks"]}
        nb = R.get("net_by_difficulty", {})
        rows.append((v, f"{u[0]['runs_p50']:.1f}" if u[0]["runs_p50"] else "-",
                     f"{u[0]['h_p50'] * 60:.0f}" if u[0]["h_p50"] else "-", st.get("time to first upgrade", "-"),
                     f"{P['first_unlock_reach_day0']:.0%}", f"{P['short_run_share']:.0%}",
                     " / ".join(f"{nb[d]['net']:,.0f}" if nb.get(d, {}).get("net") is not None else "-" for d in DIFFS),
                     " / ".join(f"{x['h_p50']:.1f}" if x["h_p50"] else "-" for x in u), f"{P['sink_source_ratio']:.2f}",
                     sum(1 for x in R["checks"] if x["status"] in ("WATCH", "MISS"))))
    table = rrlib.md_table([path, "runs to 1st", "min to 1st", "1st upgrade", "day-0 reach", "short runs",
                            "net/run E/M/H/I", "median h per unlock", "sink/src", "WATCH+MISS"], rows)
    note = (f"Sample: {sample}. Revenue columns are left out on purpose: a few simulated purchases swing them more "
            "than any knob; compare revenue only with full sims of the finalists.")
    print(table)
    print(note)
    out = Path(a.out) if a.out else rrlib.data_root() / "econ" / dt.date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    f = out / f"sweep-{re.sub(r'[^A-Za-z0-9_.-]+', '_', path)}.md"
    f.write_text(f"# Sweep {path} ({dt.date.today().isoformat()}; config {refs.source})\n\n{table}\n\n{note}\n"
                 + "".join(f"\n- set {x}" for x in a.set), encoding="utf-8")
    print(f"wrote {f}")
    return 0


def cmd_sim(a):
    try:
        raw, c, refs = load_cfg(a.config, a.set)
        if a.sweep:
            path, _, vals = a.sweep.partition("=")
            load_cfg(a.config, list(a.set) + [f"{path}={vals.split(',')[0]}"])
    except rrlib.PathError as e:
        print(f"FAIL {e}")
        return 1
    if refs.errors:
        for e in refs.errors:
            print("  E", e)
        print("FAIL: preset contradicts canon (run validate)")
        return 1
    for w in refs.warnings:
        print("  W", w)
    if "kit_paid" not in raw:
        print("  W no kit_paid in this preset: every player pays the whole difficulty kit (a per-train kit split over the "
              "crew is the skill default; add kit_paid/crew_mean to say which)")
    if a.sweep:
        return sweep(a, refs)
    if a.quick:
        c["horizon"]["installs_per_day"] = max(50, c["horizon"]["installs_per_day"] // 4)
    R = simulate(c, 400 if a.quick else 800, refs.bible)
    canon_ids = {w.split("[")[1].split("]")[0] for w, *_ in refs.canon if w.startswith("unlocks[")}
    R["suggestions"] = [x + (" (canon price: tune fares or start_coins first; changing canon is the owner's call)"
                             if x.split(":")[0] in canon_ids else "") for x in R["suggestions"]]
    out = Path(a.out) if a.out else rrlib.data_root() / "econ" / dt.date.today().isoformat()
    report(raw, c, refs, R, out)
    for x in R["checks"]:
        print(f"  {x['status']:5} {x['check']}: {x['detail']}")
    for s in R["suggestions"]:
        print(f"  suggest {s}")
    bad_ = [x["check"] for x in R["checks"] if x["status"] in ("WATCH", "MISS")]
    print(f"  {len(bad_)} checks WATCH/MISS" + (f" ({', '.join(bad_)}): not 'fixed' until they pass or the owner accepts them"
                                               if bad_ else "") + f"; {len(refs.assumed)} assumed values, "
          f"{len(refs.overrides)} canon overrides (listed in the report); wrote {out / 'ECON_REPORT.md'}")
    return 0


def load_catalogue(path, bible=None):
    src = rrlib.preset("catalogue.json", path, "RR_CATALOGUE")
    cat = rrlib.load_json(src)
    refs = rrlib.Refs(bible, *rrlib.base_refs(rrlib.PRESETS / "catalogue.json"))
    refs.source = src
    return cat, refs.resolve(cat), refs


STATES = {"launch": {"live", "proposed"}, "all": {"live", "proposed", "post_launch"}}


def cmd_ladder(a):
    raw, cat, refs = load_catalogue(a.catalogue)
    _, c, _ = load_cfg(a.config)
    share, devex = c["platform"]["creator_share"], c["platform"]["devex_usd"]
    want = STATES.get(a.state) or set(a.state.split(","))
    sel = [p for p in cat["products"] if p["state"] in want]
    once = sorted([p for p in sel if not p.get("period")], key=lambda p: p["price_rs"])
    recur = sorted([p for p in sel if p.get("period")], key=lambda p: p["price_rs"])
    rows, prev = [], None
    for p in once:
        step = f"x{p['price_rs'] / prev:.2f}" if prev else "entry"
        rows.append((p["id"], p["kind"], f"{p['price_rs']:,}", step, p["sells"], f"{p['price_rs'] * share:,.0f}",
                     f"${p['price_rs'] * share * devex:.2f}", p["state"]))
        prev = p["price_rs"] if p["price_rs"] != prev else prev
    rows += [(p["id"], p["kind"], f"{p['price_rs']:,} /{p['period']}", "recurring", p["sells"],
              f"{p['price_rs'] * share:,.0f}", f"${p['price_rs'] * share * devex:.2f}", p["state"]) for p in recur]
    print(f"states: {', '.join(sorted(want))} ({refs.source})")
    print(rrlib.md_table(["product", "kind", "R$", "step", "sells", "you earn R$", "DevEx USD", "state"], rows))
    notes = []
    ident = [p for p in once if p["sells"] in ("identity", "status")]
    if not any(p["price_rs"] <= 99 for p in ident):
        cheapest = once[0]["id"] + f" {once[0]['price_rs']} R$" if once else "none"
        notes.append(f"no identity entry item at or under 99 R$ in these states (cheapest one-time item: {cheapest}); "
                     "first purchases are the hardest")
    prices = sorted({p["price_rs"] for p in once})
    for x, y in zip(prices, prices[1:]):
        if y / x > 3:
            notes.append(f"gap {x} -> {y} R$ is x{y / x:.1f}: a mid step helps players climb")
    passes = [p for p in once if p["kind"] == "pass"]
    tot = sum(p["price_rs"] for p in passes)
    wt = refs.bible.value("economy.passes.whale_total", "")
    rng_ = rrlib.numbers_in(wt)[:2]
    gap = f"; {rng_[0] - tot:,.0f} R$ below the low end" if rng_ and tot < rng_[0] else ""
    notes.append(f"one-time passes in these states total {tot:,} R$ ({', '.join(p['id'] for p in passes) or 'none'}); "
                 f"canon whale total {wt or 'n/a'} (economy.passes.whale_total){gap}")
    left = [p["id"] for p in cat["products"] if p["state"] not in want and p["state"] != "hidden"]
    if left:
        notes.append(f"not in these states: {', '.join(left)} (--state all to include post-launch)")
    notes += catalogue_warnings(raw, refs.bible)
    notes.append(f"earned R$ = price x creator share {share:.0%}; USD at DevEx {devex} per earned R$ (economy.platform.*); "
                 "Creator Rewards (the Premium Payouts replacement) is rounding, not pricing (economy.platform.creator_rewards)")
    for n in notes:
        print(f"  - {n}")
    return 0


D007_WORDS = ("time", "status", "identity")
ODDS_RE = re.compile(r"reviv|re-?roll|extra life|second chance|skip (the )?(fork|crisis)|shield|immun|insuranc|"
                     r"auto-?(repair|fix|stok)|odds|luck|guarantee|survive|invincib", re.I)


def cmd_guard(a):
    raw, cat, refs = load_catalogue(a.catalogue)
    bible = refs.bible
    items = []
    if a.gate and not (a.sim or a.run_fare):
        print("FAIL: gate use needs --sim econ.json or --run-fare N (the fare-pack cap cannot be checked without it)")
        return 1

    def add(pid, sev, rule, msg, canon):
        items.append({"product": pid, "severity": sev, "rule": rule, "msg": msg, "canon": canon})
    d007 = bible.get_id("D-007") or ""
    allowed = [w for w in D007_WORDS if w in d007.lower()] or list(D007_WORDS)
    run_fare, fare_src = a.run_fare, "given"
    if a.sim and not run_fare:
        run_fare, fare_src = rrlib.load_json(a.sim).get("engaged", {}).get("mean_fare_per_run"), "sim, assumed fares"
    # prompt and pack rules come from the economy preset, whose values are checked against canon on every run
    _, ec, erefs = load_cfg(a.config)
    er = ec["rules"]
    rules = {"after_run": er["prompt_after_run"], "max_prompts": er["max_prompts"], "cap_runs": er["pack_cap_runs"],
             "short_pct": er["pack_short_pct"]}
    for e in erefs.errors:
        add("(economy preset)", "FAIL", "M00", e, "rr-bible")
    placements = set()
    for p in cat["products"]:
        pid, sells, st = p["id"], p["sells"], p["state"]
        live = st != "hidden"
        oq = p.get("question")
        if sells in ("odds", "survival", "power"):
            sev = "FAIL" if live else "INFO"
            add(pid, sev, "M01", f"sells {sells}: D-007 allows {', '.join(allowed)} only"
                + ("" if live else f" (hidden per {oq} default; keep it hidden)"), "D-007")
        elif sells not in allowed and live:
            add(pid, "HOLD", "M01", f"sells {sells}: not named in D-007 ({', '.join(allowed)}); owner confirms it is "
                "time or identity in practice", "D-007")
        if ODDS_RE.search(p.get("effect", "")) and sells not in ("odds", "survival", "power"):
            add(pid, "HOLD", "M02", f"effect text '{p['effect']}' reads like odds/survival; re-check the sells label", "D-007")
        if p.get("affects_crew") and live:
            add(pid, "FAIL", "M04", "one buyer changes the whole crew's run: pay-to-win in co-op", "identity.pillars.four_systems")
        if p.get("gameplay") and live and not p.get("affects_crew") and sells not in ("odds", "survival", "power"):
            touch = ", ".join(p.get("touches", [])) or "a crisis, tool or carry rule"
            add(pid, "HOLD", "M03", f"changes gameplay ({touch}): run risky-rails-mechanic-reviewer, then the owner decides",
                p.get("touches", ["D-007"])[0])
        if p.get("random"):
            odds = p.get("odds") or {}
            if not live:
                pass
            elif abs(sum(odds.values()) - 1) > 1e-6 if odds else True:
                add(pid, "FAIL", "M05", "paid random item (coin-priced counts: coins are Robux-purchasable) without an odds "
                    "table summing to 100% shown before purchase",
                    "platform: Roblox paid random items policy")
            if live and p.get("policy_check") != "ArePaidRandomItemsRestricted":
                add(pid, "FAIL", "M05", "no PolicyService ArePaidRandomItemsRestricted check (hide it where restricted)",
                    "platform: PolicyService")
            if live:
                add(pid, "FAIL", "M05", "canon says no gacha; needs an owner decision first", "economy.passes.whale_total")
        if p.get("stake"):
            add(pid, "FAIL", "M12", "stakes banked coins (buyable with Robux via fare packs) on a chance outcome: "
                "that is wagering, not a fork bet", "economy.passes.fare_packs")
        if p.get("affects_rank"):
            add(pid, "FAIL", "M08", "changes Daily Line rank", "economy.rules.daily_line_fair")
        if p.get("fare_mult") and p.get("rank") != "unboosted":
            add(pid, "HOLD", "M08", "multiplies fare: Daily Line must rank unboosted fare (declare rank: unboosted)",
                "economy.rules.daily_line_fair")
        pr = p.get("prompt")
        if pr and live:
            placements.add(pr["where"])
            if pr.get("after_run", 0) < rules["after_run"]:
                add(pid, "FAIL", "M06", f"prompt after run {pr.get('after_run', 0)}; canon: after run {rules['after_run']:.0f}+ "
                    "and never before the first bank", "economy.rules.no_early_prompts")
            if pr.get("short_pct") and pr["short_pct"] > rules["short_pct"]:
                add(pid, "HOLD", "M07", f"shown when short by {pr['short_pct']}% (canon under {rules['short_pct']:.0f}%)",
                    "economy.passes.fare_packs")
        if p.get("fare") and live:
            if run_fare:
                cap = rules["cap_runs"] * run_fare
                if p["fare"] > cap * 1.1:
                    add(pid, "FAIL", "M07", f"{p['fare']:,} fare > {rules['cap_runs']:.0f} runs of earnings "
                        f"({cap:,.0f}, +10% tolerance for canon 'about' = {cap * 1.1:,.0f}; run fare {run_fare:,.0f} "
                        f"from {fare_src})", "economy.passes.fare_packs")
                elif p["fare"] > cap:
                    add(pid, "INFO", "M07", f"{p['fare']:,} fare is over {rules['cap_runs']:.0f} runs ({cap:,.0f}) but "
                        "inside the 10% tolerance for canon 'about'", "economy.passes.fare_packs")
            else:
                add(pid, "INFO", "M07", "pack cap unchecked: pass --sim econ.json or --run-fare", "economy.passes.fare_packs")
        if p["kind"] == "subscription" and live:
            for k in ("benefit_period", "cancel_behaviour"):
                if not p.get(k):
                    add(pid, "HOLD", "M10", f"subscription without {k}", "platform: experience subscriptions")
        if oq and live:
            add(pid, "HOLD", "M15", f"depends on open question {oq}: the owner decides first", oq)
    states = {p["id"]: p["state"] for p in cat["products"]}
    pid_of = lambda w: re.search(r"products\[([^\]]+)\]", w).group(1) if w.startswith("products[") else None  # noqa: E731
    for w, v, key, status in refs.canon:
        pid = pid_of(w)
        if status == "proposed" and w.endswith("price_rs") and pid and states.get(pid) != "hidden":
            add(pid, "INFO", "M13", f"price {v} R$ is proposed in canon ({key}), not decided", key)
    for w, v, key, cv in refs.overrides:  # a mission's price or pack size that departs from canon: the owner decides
        pid = pid_of(w)
        if pid and states.get(pid) != "hidden":
            add(pid, "HOLD", "M16", f"{w.split('.', 1)[-1] if '.' in w else w} = {v} departs from canon {key} = \"{cv}\" "
                "(labelled assumed): an owner decision before it ships", key)
    for w in catalogue_warnings(raw, bible):
        add(w.split("]")[0].split("[")[-1], "HOLD", "M17", w.split(": ", 1)[-1], "economy.passes.liveries")
    if rules.get("max_prompts") and len(placements) > rules["max_prompts"]:
        add("(all)", "FAIL", "M06", f"{len(placements)} purchase prompt placements {sorted(placements)} > canon "
            f"{rules['max_prompts']:.0f}", "economy.rules.no_early_prompts")
    if a.src:
        sites = []
        for f in Path(a.src).rglob("*"):
            if f.suffix in (".lua", ".luau") and f.is_file():
                for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if re.search(r"Prompt(Product|GamePass|Subscription|Premium|Bundle)Purchase\s*\(", line) and not line.strip().startswith("--"):
                        sites.append(f"{f}:{n}")
        if rules.get("max_prompts") and len(sites) > rules["max_prompts"]:
            add("(code)", "HOLD", "M06", f"{len(sites)} purchase prompt call sites (canon allows two placements): "
                + ", ".join(sites[:8]), "economy.rules.no_early_prompts")
        add("(code)", "INFO", "M09", "ProcessReceipt, server price tables and grant idempotency are audited by rr-exploit-guard",
            "tech.security.process_receipt")
    for e in refs.errors:
        add("(preset)", "FAIL", "M00", e, "rr-bible")
    ship = set(a.ship.split(","))
    for i in items:
        stt = states.get(i["product"])
        if stt and stt not in ship and stt != "hidden" and i["severity"] in ("FAIL", "HOLD"):
            i["msg"] = f"[{stt}, not in this release] " + i["msg"]
            i["severity"] = "FUTURE"
    order = {"FAIL": 0, "HOLD": 1, "FUTURE": 2, "INFO": 3}
    items.sort(key=lambda x: (order[x["severity"]], x["product"]))
    verdict = "FAIL" if any(i["severity"] == "FAIL" for i in items) else ("HOLD" if any(i["severity"] == "HOLD" for i in items) else "PASS")
    out = Path(a.out) if a.out else rrlib.data_root() / "gate"
    out.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()[:16]
    gate = {"verdict": verdict, "checked_at": dt.date.today().isoformat(), "catalogue_sha256": digest,
            "blocking": [i for i in items if i["severity"] == "FAIL"], "hold": [i for i in items if i["severity"] == "HOLD"],
            "future": [i for i in items if i["severity"] == "FUTURE"], "info": [i for i in items if i["severity"] == "INFO"],
            "shipping_states": sorted(ship), "waivers": "owner only; record with bible decide"}
    rrlib.save_json(out / "MONEY_GATE.json", gate)
    md = [f"# Money gate: {verdict}", "", f"Catalogue {digest}, checked {gate['checked_at']}. FAIL blocks release; HOLD needs "
          "the owner (and risky-rails-mechanic-reviewer for gameplay items); only the owner waives.", "",
          rrlib.md_table(["severity", "product", "rule", "finding", "canon"],
                         [(i["severity"], i["product"], i["rule"], i["msg"], f"`{i['canon']}`") for i in items])]
    (out / "MONEY_GATE.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    for i in items:
        if i["severity"] not in ("INFO", "FUTURE") or a.verbose:
            print(f"  {i['severity']:4} {i['product']:15} {i['rule']} {i['msg']} [{i['canon']}]")
    print(f"MONEY GATE {verdict}: {len(gate['blocking'])} fail, {len(gate['hold'])} hold, {len(gate['future'])} future, "
          f"{len(gate['info'])} info -> {out / 'MONEY_GATE.md'}")
    if not (a.sim or a.run_fare):
        print("  note: fare-pack cap unchecked (no --sim/--run-fare): this verdict cannot PASS a pack")
    return ({"FAIL": 1, "HOLD": 3}.get(verdict, 0)) if a.gate else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    v = sub.add_parser("validate")
    v.add_argument("--config")
    v.add_argument("--catalogue")
    s = sub.add_parser("sim")
    s.add_argument("--config")
    s.add_argument("--out")
    s.add_argument("--set", action="append", default=[])
    s.add_argument("--sweep")
    s.add_argument("--quick", action="store_true")
    l_ = sub.add_parser("ladder")
    l_.add_argument("--catalogue")
    l_.add_argument("--config")
    l_.add_argument("--state", default="launch", help="launch (live+proposed, default), all, or a list")
    g = sub.add_parser("guard")
    g.add_argument("--catalogue")
    g.add_argument("--config", help="economy preset whose canon-checked rules the gate applies")
    g.add_argument("--gate", action="store_true", help="exit 1 on FAIL, 3 on HOLD; needs --sim or --run-fare")
    g.add_argument("--sim")
    g.add_argument("--run-fare", type=float)
    g.add_argument("--src")
    g.add_argument("--out")
    g.add_argument("--ship", default="live,proposed", help="states in this release (others are FUTURE, non-blocking)")
    g.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    if not a.cmd:
        ap.print_help()
        return 2
    return {"validate": cmd_validate, "sim": cmd_sim, "ladder": cmd_ladder, "guard": cmd_guard}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
