# Risky Rails economy sim (2026-09-28)

Config hash 8bfce60539cb; seed 7; retention fitted r(t) = 0.098 t^-0.784 through canon D1/D7/D30.

## Checks vs canon

| check | status | detail | canon |
|---|---|---|---|
| time to first upgrade | PASS | loco_2: median 2.0 runs / 27 min (p90 3.0 runs); target about 2 runs inside 30 min | `gameplay.progress.first_unlock` |
| new players who get it on day 0 | INFO | 39% of installs (ever: 46%); day-0 runs mean 1.8 (assumed) | `gameplay.progress.first_unlock` |
| pacing loco_3 | PASS | +1.8 h after the previous unlock (at 2.2 h); target about 2 h | `gameplay.progress.pacing` |
| pacing loco_4 | PASS | +1.8 h after the previous unlock (at 4.0 h); target about 2 h | `gameplay.progress.pacing` |
| pacing loco_5 | PASS | +2.0 h after the previous unlock (at 6.1 h); target about 2 h | `gameplay.progress.pacing` |
| pacing line_2 | PASS | +2.2 h after the previous unlock (at 8.3 h); target about 2 h | `gameplay.progress.pacing` |
| fare pack cap | MISS | largest pack 20,000 vs 10 x run fare 1,702 (mean, first 12 h) = 17,019 | `economy.passes.fare_packs` |
| fare packs vs playing well | PASS | best pack 33.4 fare/R$ vs Double Fare 304.1 fare/R$ over 12 h of play (interpretation: buying fare must not beat earning it with the pass) | `economy.rules.fair_packs` |
| completion | PASS | 59% of runs arrive; canon 30%-60% | `release.kpi.completion` |
| payer conversion | WATCH | 0.48% of DAU pay per day (driven by assumed buying odds) | `release.kpi.conversion` |
| sink left for veterans | PASS | 1% of active players own every unlock in the last week; balances 1,491 -> 1,758 (median, first vs last week) | `economy.passes.whale_total` |

## Population

| metric | value |
|---|---|
| installs / avg DAU | 9,000 / 409 |
| runs, completion | 23,338, 59% |
| minted / burned coins | 34,228,618 / 17,703,215 (sink/source 0.52) |
| paid share of faucet (packs / Double Fare bonus) | 0.1% / 1.2% |
| runs started short of the supply kit | 40% |
| payer conversion (daily) | 0.48% |
| revenue gross / earned R$ | 17,091 / 11,964 (~$45.46 DevEx) |
| earned ARPDAU | 0.976 R$ |
| pay-to-skip (payer / non-payer hours per unlock) | 0.65 |

## Unlock pacing (engaged cohort, no churn)

| unlock | price | reached | median h | p90 h | median runs | Double Fare median h | successful runs |
|---|---|---|---|---|---|---|---|
| loco_2 | 2,500 | 100% | 0.5 | 0.7 | 2 | 0.5 | 1.2 |
| loco_3 | 10,000 | 100% | 2.2 | 2.7 | 10 | 1.4 | 4.9 |
| loco_4 | 12,000 | 100% | 4.0 | 4.7 | 18 | 2.2 | 5.9 |
| loco_5 | 14,000 | 100% | 6.1 | 7.0 | 27 | 3.4 | 6.9 |
| line_2 | 16,000 | 100% | 8.3 | 9.4 | 37 | 4.5 | 7.9 |

## Assumed (no canon yet)

- `horizon.days` = 30: one month of installs
- `horizon.installs_per_day` = 300: soft-launch scale; only changes totals, not per-player pacing
- `retention.play_prob_retained` = 0.6: share of still-engaged players who play on a given day
- `session.runs_day0_mean` = 1.8: first session length; canon asks >= 10 min (one run + results)
- `session.runs_later_mean` = 2.2: runs per active day after day 0
- `session.engaged_runs_per_day` = 4: pacing cohort: plays every day until the hour limit
- `session.engaged_hours` = 12: canon pacing runs through hour 10
- `difficulty.Easy.fare_full` = 1700: fare banked by an arriving crew member; calibrated by sweep so loco 2 lands in about 2 runs (gameplay.progress.first_unlock)
- `difficulty.Easy.p_arrive` = 0.65: arrival chance; overall completion is checked against release.kpi.completion
- `difficulty.Medium.fare_full` = 2100: +25% per step like the trip miles (gameplay.difficulty.trip_miles)
- `difficulty.Medium.p_arrive` = 0.55: see Easy
- `difficulty.Hard.fare_full` = 2650: risky forks pay more (gameplay.fork.risky)
- `difficulty.Hard.p_arrive` = 0.4: see Easy
- `difficulty.Insane.fare_full` = 3300: up to x3.0 fork multipliers on Insane (gameplay.fork.risky)
- `difficulty.Insane.p_arrive` = 0.25: see Easy
- `fare_cv` = 0.35: run-to-run spread from forks, mood and crew
- `skill_range` = [0.85, 1.15]: per-player multiplier on arrival chance
- `failed_trip.banked_share` = [0.2, 0.8]: share of the run's fare already banked at stations when it fails
- `failed_trip.penalty` = 0.5: option C only
- `fare_split` = each_full: each crew member banks the full crew fare (no canon; proposed open question)
- `start_coins` = 0: no canon; the petty-cash float is superseded (economy.currency.float)
- `short_penalty` = 0.9: arrival chance multiplier when a player could not afford the run's kit
- `recovery.falls_per_run` = 0.3: players falling off per run
- `unlocks[1].price` = 10000: set for about 2 h after loco 2 (gameplay.progress.pacing)
- `unlocks[2].price` = 12000: about 2 h later
- `unlocks[3].price` = 14000: about 2 h later; 5 locomotives at 1.0 (gameplay.progress.ladder)
- `unlocks[4].price` = 16000: second line (gameplay.progress.ladder), about hour 8-10
- `buying.payer_share` = 0.12: players who would ever pay
- `buying.p_double_fare` = 0.1: a would-be payer buys Double Fare when shown
- `buying.p_pack` = 0.06: a would-be payer buys a pack when shown while short
- `buying.p_organic_daily` = 0.03: a would-be payer buys Double Fare unprompted (shop, store page) on an active day

![flows](econ-flows.svg)
![balance](econ-balance.svg)
![pacing](econ-pacing.svg)
