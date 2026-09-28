# Economy model (econ.py sim)

Read when running or tuning the sim, or when its numbers go into a memo or a pricing decision.

## What it simulates
Two cohorts from one preset (`presets/economy.json`), seeded and deterministic:
- **Population**: `installs_per_day x days` players. Retention r(t) = a t^-b is fitted through canon D1/D7/D30
  (`release.kpi.*`); each player gets a last active day L with P(L >= t) = r(t)/q and plays each day up to L with
  probability q (`play_prob_retained`), so expected D1/D7/D30 match canon. Answers: day-0 reach of the first
  unlock, faucets vs sinks, balances (inflation), short-of-kit runs, payer conversion, revenue.
- **Engaged**: players who play `engaged_runs_per_day` every day up to `engaged_hours` of play, once as
  non-payers and once with Double Fare from run 3. Answers pacing (hours and runs to each unlock), which churn hides,
  and the pay-to-skip ratio.

Per run: difficulty from `difficulty_mix` by runs played; buy the difficulty's supply kit at canon prices if the
balance allows (else the run starts short: arrival chance x `short_penalty`); arrive with `p_arrive x skill`;
fare = `fare_full` x lognormal(`fare_cv`); a failed run pays per OQ-011 option (A: banked share, B: 0, C: banked
minus penalty); Double Fare doubles it; recovery fees; buy unlocks in order when affordable. Prompts follow canon
(after run 3; Double Fare once after a best run; a pack when short by under 30%, once a day); only would-be payers
(`payer_share`) buy, with the assumed odds; they may also buy Double Fare unprompted.

## Reading the checks
| check | canon | meaning of a miss |
|---|---|---|
| time to first upgrade | `gameplay.progress.first_unlock` | median runs/minutes to loco 2 too slow |
| day-0 reach (INFO) | same | share of all installs who unlock anything before leaving; the lever for D1 |
| pacing per unlock | `gameplay.progress.pacing` | gap to the previous unlock outside 0.5-1.5x of about 2 h |
| item size | `gameplay.progress.pacing` | price above about 15 successful runs |
| fare pack cap | `economy.passes.fare_packs` | largest pack above 10 x mean run fare |
| fare packs vs playing well | `economy.rules.fair_packs` | a pack buys more fare per R$ than Double Fare earns (our interpretation; confirm) |
| completion | `release.kpi.completion` | arrivals / runs outside the canon band |
| payer conversion | `release.kpi.conversion` | driven by assumed buying odds: a sanity check, not a forecast |
| sink left for veterans | `economy.passes.whale_total` | many actives own everything while balances climb: add fare cosmetics |

Suggestions scale a price by target gap / simulated gap; they are starting points for a sweep, not decisions.

## Tuning loop
1. `econ.py validate` (canon agreement; lists every assumed value).
2. `econ.py sim --sweep difficulty.Easy.fare_full=1500,1700,1900` (one knob, several values, compact table).
3. Change the preset (never canon numbers: those change through the owner and bible.py), rerun `sim`.
4. Once live: replace assumed values with measured ones from the dashboard economy export (mean `fare_bank` per
   trip = fare source / trips; supplies per trip = coal+toolbox+sandwich+medkit sinks / trips; completion from the
   trip progression path) and compare `sink/source` with the memo (`dash.py memo --sim econ.json`).

## Limits
Parametric fares, not a fork-by-fork game model; crews are not simulated together (fare assumed paid to each member
in full: proposed open question); cosmetic revenue is not modelled; buying odds are guesses. Use it to compare
options and catch structural problems (a pack over the cap, a first unlock nobody reaches on day 0, a dead sink),
never as a revenue forecast.
