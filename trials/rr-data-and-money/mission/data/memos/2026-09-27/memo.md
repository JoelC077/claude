# Risky Rails weekly memo · week ending 2026-09-27

**SYNTHETIC DATA. Payer conversion fell to 0.71% (95% CI 0.4%-1.2%), a MISS on the 1.5% continue gate; D1 holds at 12.2% (spend gate PASS, scale gate UNCLEAR).**

## KPIs vs canon targets

| metric | this week | last week | change | 95% CI | target | status |
|---|---|---|---|---|---|---|
| DAU (daily avg) | 262 | 233 | +13% | - | - | - |
| New users | 929 | 846 | +10% | - | - | - |
| Session length | 11.0 min | 11.5 min | -4% | - | >= 10.0 min `release.kpi.session_min` | PASS |
| D1 retention | 12.2% | 11.9% | +0.3 pts | 10.3%-14.3% (n 1,037) | >= 10.0% `release.kpi.d1` | PASS |
| D7 retention | 1.90% | 2.35% | -0.5 pts | 1.2%-3.0% (n 846) | >= 2.00% `release.kpi.d7` | UNCLEAR |
| Revenue | 2,125 R$ | 3,311 R$ | -36% | - | - | - |
| ARPDAU | 1.16 R$ | 2.03 R$ | -43% | - | - | - |
| Payer conversion | 0.71% | 1.23% | -0.5 pts | 0.4%-1.2% (n 1,833) | >= 1.50% `release.kpi.conversion` | MISS |
| ARPPU | 163.46 R$ | 165.55 R$ | -1% | - | - | - |
| R$ per visit | 0.82 R$ | 1.42 R$ | -42% | - | - | - |
| Qualified play-through | 3.04% | 3.18% | -0.1 pts | - | - | - |

## Release gates

| gate | check | now | needs | status | canon |
|---|---|---|---|---|---|
| scale | D1 before scaling spend | 12.2% | >= 13.0% | UNCLEAR | `release.kpi.d1` |
| spend | D1 before any ad spend | 12.2% | >= 10.0% | PASS | `release.gates.spend` |
| spend | bounce before any ad spend | n/a | < 25.0% | NO DATA | `release.gates.spend` |
| continue | DAU | 262 | >= 100 | PASS | `release.gates.continue` |
| continue | payer conversion | 0.71% | >= 1.50% | MISS | `release.gates.continue` |
| continue | R$ per visit | 0.82 R$ | >= 0.40 R$ | PASS | `release.gates.continue` |
| abandon | stop-spending trigger | 12.2% | < 8.00% | OK | `release.gates.abandon` |
| closed_test | session (mean; canon says median) | 11.0 min | >= 10.0 min | PASS | `release.gates.closed_test` |
| spend | weekly D1 cohorts at/above the gate (need 2; point estimates) | 3 of last 4 | >= 10.0% | PASS | `release.gates.spend` |

## What moved

- nothing beyond noise

## Experiments (status only, no peeking)

- thumb_lever_vs_crash (thumbnail): running, day 14 of 14, readout 2026-09-28

## Charts

![dau](charts/dau.svg)
![retention](charts/retention.svg)
![money](charts/money.svg)

## Actions (owner decides)

1. Payer conversion MISS (release.gates.continue): owner decides the launch ladder in MONEY_GATE.md (49 R$ identity entry; private-server HOLD) and the purchase funnel gets wired before soft launch. 13 payers this week: no live price change on this evidence.
2. Spend gate unreadable: bounce is NO DATA. Add the 60 s bounce export (release.kpi.bounce_60s) to next week's CSV set before any ad spend (release.gates.spend).
3. D1 12.2% is UNCLEAR against the 13% scale gate (CI 10.3%-14.3%): no scaling spend yet; D7 1.90% is UNCLEAR against 2%, so wait for more mature cohorts.

## Data notes

- D1 = mature cohorts 2026-09-20..2026-09-26
- D7 = mature cohorts 2026-09-14..2026-09-20
- revenue treated as earned (net) Robux
- payer conversion CI treats each DAU-day as one trial (approximate)
- SYNTHETIC_dashboard_30d.csv: avg_session_min: seconds -> minutes
