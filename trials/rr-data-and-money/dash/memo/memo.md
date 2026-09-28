# Risky Rails weekly memo · week ending 2026-09-27

**D1 is up 1.4 pts but still inside the noise around the 10% gate: hold ad spend.**

## KPIs vs canon targets

| metric | this week | last week | change | 95% CI | target | status |
|---|---|---|---|---|---|---|
| DAU (daily avg) | 169 | 148 | +14% | - | - | - |
| New users | 649 | 567 | +14% | - | - | - |
| Session length | 10.9 min | 10.8 min | +1% | - | >= 10.0 min `release.kpi.session_min` | PASS |
| D1 retention | 11.8% | 10.5% | +1.4 pts | 9.6%-14.6% (n 649) | >= 10.0% `release.kpi.d1` | UNCLEAR |
| D7 retention | 1.95% | 2.10% | -0.1 pts | 1.1%-3.4% (n 567) | >= 2.00% `release.kpi.d7` | UNCLEAR |
| Revenue | 617 R$ | 502 R$ | +23% | - | - | - |
| ARPDAU | 0.52 R$ | 0.48 R$ | +8% | - | - | - |
| Payer conversion | 1.77% | 1.64% | +0.1 pts | 1.2%-2.7% (n 1,184) | >= 1.50% `release.kpi.conversion` | UNCLEAR |
| ARPPU | 29.38 R$ | 29.53 R$ | -1% | - | - | - |
| R$ per visit | 0.33 R$ | 0.30 R$ | +8% | - | - | - |

## Release gates

| gate | check | now | needs | status | canon |
|---|---|---|---|---|---|
| scale | D1 before scaling spend | 11.8% | >= 13.0% | UNCLEAR | `release.kpi.d1` |
| spend | D1 before any ad spend | 11.8% | >= 10.0% | UNCLEAR | `release.gates.spend` |
| spend | bounce before any ad spend | n/a | < 25.0% | NO DATA | `release.gates.spend` |
| continue | DAU | 169 | >= 100 | PASS | `release.gates.continue` |
| continue | payer conversion | 1.77% | >= 1.50% | UNCLEAR | `release.gates.continue` |
| continue | R$ per visit | 0.33 R$ | >= 0.40 R$ | MISS | `release.gates.continue` |
| abandon | stop-spending trigger | 11.8% | < 8.00% | OK | `release.gates.abandon` |
| closed_test | session (mean; canon says median) | 10.9 min | >= 10.0 min | PASS | `release.gates.closed_test` |
| spend | weekly D1 cohorts at/above the gate (need 2; point estimates) | 3 of last 4 | >= 10.0% | PASS | `release.gates.spend` |

## What moved

- 2026-09-26: dau 195 is +3.0 sd vs the prior 14 days (check updates, featuring, outages)
- 2026-09-26: new_users 107 is +3.0 sd vs the prior 14 days (check updates, featuring, outages)

## Funnels

- onboarding: Joined 1,000 > Picked up tool 820 > Shovelled coal 700 > Pulled lever 610 > First bank 380 > Run end 350. Biggest drop: Pulled lever -> First bank loses 38%

## Economy

- sources 1,043,727, sinks 568,654, sink/source 0.54
- source fare_bank: 1,043,727
- sink loco_2: 422,842
- sink coal: 145,812
- sim predicted sink/source 0.52; live 0.54

## Experiments (status only, no peeking)

- onb_hint (onboarding): planned, starts 2026-10-05
- thumb_rotation (thumbnail): planned, starts 2026-10-05

## Charts

![dau](charts/dau.svg)
![retention](charts/retention.svg)
![money](charts/money.svg)
![funnel](charts/funnel-onboarding.svg)

## Actions (owner decides)

1. Lever -> first bank loses 38% of new players: prototype the OQ-007 branch hint.
2. Keep ads at zero until two weekly D1 cohorts clear the gate (release.gates.spend).

## Data notes

- D1 = mature cohorts 2026-09-21..2026-09-27
- D7 = mature cohorts 2026-09-14..2026-09-20
- revenue treated as earned (net) Robux
- payer conversion CI treats each DAU-day as one trial (approximate)
- SYNTHETIC_engagement_wide.csv: avg_session_min: seconds -> minutes
