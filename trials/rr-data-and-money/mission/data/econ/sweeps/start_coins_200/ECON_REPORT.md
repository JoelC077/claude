# Risky Rails economy sim (2026-09-28)

Config hash d89b0dc714e7; seed 7; retention fitted r(t) = 0.098 t^-0.784 through canon D1/D7/D30.

## Checks vs canon

| check | status | detail | canon |
|---|---|---|---|
| time to first upgrade | PASS | loco_2: median 2.0 runs / 27 min (p90 3.0 runs); target about 2 runs inside 30 min | `gameplay.progress.first_unlock` |
| new players who get it on day 0 | INFO | 45% of installs (ever: 52%); day-0 runs mean 1.8 (assumed) | `gameplay.progress.first_unlock` |
| pacing loco_3 | PASS | +2.0 h after the previous unlock (at 2.5 h); target about 2 h | `gameplay.progress.pacing` |
| pacing loco_4 | PASS | +2.0 h after the previous unlock (at 4.5 h); target about 2 h | `gameplay.progress.pacing` |
| pacing loco_5 | PASS | +2.7 h after the previous unlock (at 7.2 h); target about 2 h | `gameplay.progress.pacing` |
| pacing line_2 | PASS | +2.9 h after the previous unlock (at 10.1 h); target about 2 h | `gameplay.progress.pacing` |
| fare pack cap | PASS | largest pack 20,000 vs 10 x run fare 1,920 (mean, first 12 h) = 19,200 | `economy.passes.fare_packs` |
| fare packs vs playing well | PASS | best pack 33.4 fare/R$ vs Double Fare 338.7 fare/R$ over 12 h of play (interpretation: buying fare must not beat earning it with the pass) | `economy.rules.fair_packs` |
| completion | WATCH | 62% of runs arrive; canon 30%-60% | `release.kpi.completion` |
| payer conversion | WATCH | 0.46% of DAU pay per day (driven by assumed buying odds) | `release.kpi.conversion` |
| sink left for veterans | PASS | 1% of active players own every unlock in the last week; balances 1,519 -> 1,827 (median, first vs last week) | `economy.passes.whale_total` |

## Population

| metric | value |
|---|---|
| installs / avg DAU | 9,000 / 414 |
| runs, completion | 23,770, 62% |
| minted / burned coins | 36,791,798 / 20,861,240 (sink/source 0.57) |
| paid share of faucet (packs / Double Fare bonus) | 0.1% / 1.2% |
| runs started short of the supply kit | 2% |
| payer conversion (daily) | 0.46% |
| revenue gross / earned R$ | 15,792 / 11,054 (~$42.01 DevEx) |
| earned ARPDAU | 0.890 R$ |
| pay-to-skip (payer / non-payer hours per unlock) | 0.66 |

## Unlock pacing (engaged cohort, no churn)

| unlock | price | reached | median h | p90 h | median runs | Double Fare median h | successful runs |
|---|---|---|---|---|---|---|---|
| loco_2 | 2,500 | 100% | 0.5 | 0.7 | 2 | 0.5 | 1.1 |
| loco_3 | 12,000 | 100% | 2.5 | 2.9 | 11 | 1.6 | 5.4 |
| loco_4 | 15,000 | 100% | 4.5 | 5.4 | 20 | 2.7 | 6.8 |
| loco_5 | 18,000 | 100% | 7.2 | 8.1 | 32 | 3.8 | 8.2 |
| line_2 | 22,000 | 99% | 10.1 | 11.5 | 45 | 5.2 | 10.0 |

## Assumed (no canon yet)

- `horizon.days` = 30: one month of installs
- `horizon.installs_per_day` = 300: soft-launch scale; only changes totals, not per-player pacing
- `retention.play_prob_retained` = 0.6: share of still-engaged players who play on a given day
- `session.runs_day0_mean` = 1.8: first session length; canon asks >= 10 min (one run + results)
- `session.runs_later_mean` = 2.2: runs per active day after day 0
- `session.engaged_runs_per_day` = 4: pacing cohort: plays every day until the hour limit
- `session.engaged_hours` = 12: canon pacing runs through hour 10
- `difficulty.Easy.fare_full` = 1700: SYNTHETIC proposal v1 = v0 + fixes from the trial sim (2026-09-28): fares step up so net coins per run rise with difficulty after the crate hike
- `difficulty.Easy.p_arrive` = 0.65: arrival chance; overall completion is checked against release.kpi.completion
- `difficulty.Medium.fare_full` = 2300: SYNTHETIC proposal v1 = v0 + fixes from the trial sim (2026-09-28): fares step up so net coins per run rise with difficulty after the crate hike
- `difficulty.Medium.p_arrive` = 0.55: see Easy
- `difficulty.Hard.fare_full` = 3100: SYNTHETIC proposal v1 = v0 + fixes from the trial sim (2026-09-28): fares step up so net coins per run rise with difficulty after the crate hike
- `difficulty.Hard.p_arrive` = 0.4: see Easy
- `difficulty.Insane.fare_full` = 4200: SYNTHETIC proposal v1 = v0 + fixes from the trial sim (2026-09-28): fares step up so net coins per run rise with difficulty after the crate hike
- `difficulty.Insane.p_arrive` = 0.25: see Easy
- `fare_cv` = 0.35: run-to-run spread from forks, mood and crew
- `skill_range` = [0.85, 1.15]: per-player multiplier on arrival chance
- `failed_trip.banked_share` = [0.2, 0.8]: share of the run's fare already banked at stations when it fails
- `failed_trip.penalty` = 0.5: option C only
- `fare_split` = each_full: each crew member banks the full crew fare (no canon; proposed open question)
- `start_coins` = 200: override --set start_coins=200
- `prices.coal` = 60: SYNTHETIC owner proposal v0 (trial 2026-09-28): crate price hike to make supplies a real sink (canon economy.supplies.coal = 40)
- `prices.toolbox` = 200: SYNTHETIC owner proposal v0 (trial 2026-09-28): crate price hike to make supplies a real sink (canon economy.supplies.toolbox = 120)
- `prices.sandwich` = 30: SYNTHETIC owner proposal v0 (trial 2026-09-28): crate price hike to make supplies a real sink (canon economy.supplies.sandwich = 25)
- `prices.medkit` = 150: SYNTHETIC owner proposal v0 (trial 2026-09-28): crate price hike to make supplies a real sink (canon economy.supplies.medkit = 90)
- `short_penalty` = 0.9: arrival chance multiplier when a player could not afford the run's kit
- `recovery.falls_per_run` = 0.3: players falling off per run
- `unlocks[1].price` = 12000: SYNTHETIC proposal v1 = v0 + fixes from the trial sim (2026-09-28): about 2 h gaps
- `unlocks[2].price` = 15000: SYNTHETIC proposal v1 = v0 + fixes from the trial sim (2026-09-28): about 2 h gaps
- `unlocks[3].price` = 18000: SYNTHETIC proposal v1 = v0 + fixes from the trial sim (2026-09-28): about 2 h gaps
- `unlocks[4].price` = 22000: SYNTHETIC proposal v1 = v0 + fixes from the trial sim (2026-09-28): about 2 h gaps
- `buying.payer_share` = 0.12: players who would ever pay
- `buying.p_double_fare` = 0.1: a would-be payer buys Double Fare when shown
- `buying.p_pack` = 0.06: a would-be payer buys a pack when shown while short
- `buying.p_organic_daily` = 0.03: a would-be payer buys Double Fare unprompted (shop, store page) on an active day

![flows](econ-flows.svg)
![balance](econ-balance.svg)
![pacing](econ-pacing.svg)
