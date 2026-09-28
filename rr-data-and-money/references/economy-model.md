# Economy model (econ.py sim)

Read when running or tuning the sim, or when its numbers go into a memo or a pricing decision.

## What it simulates
Two cohorts from one preset (`presets/economy.json`), seeded and deterministic:
- **Population**: `installs_per_day x days` players. Retention r(t) = a t^-b is fitted through canon D1/D7/D30
  (`release.kpi.*`); each player gets a last active day L with P(L >= t) = r(t)/q and plays each day up to L with
  probability q (`play_prob_retained`), so expected D1/D7/D30 match canon. Answers: day-0 reach of the first
  unlock, faucets vs sinks, balances (inflation), short-of-kit runs, payer conversion, revenue.
- **Engaged**: players who play `engaged_runs_per_day` every day up to `engaged_hours` of play, once as
  non-payers and once with Double Fare from the canon prompt run. Answers pacing (hours and runs to each unlock), which churn hides,
  and the pay-to-skip ratio.

Per run: difficulty from `difficulty_mix` by runs played; buy the difficulty's supply kit at canon prices if the
balance allows (else the run starts short: arrival chance x `short_penalty`). The kit is per train (one Depotron order
at a time, `gameplay.supplies.one_order`); with `kit_paid` = split each player pays kit / `crew_mean` on average,
with `each` the whole kit (a preset without `kit_paid` means each, and the sim warns). Both are assumed: the ORDER of
the difficulty tiers is robust to it, the sign of a low tier's net is not, so say which you report; arrive with `p_arrive x skill`;
fare = `fare_full` x lognormal(`fare_cv`); a failed run pays per OQ-011 option (A: banked share, B: 0, C: banked
minus penalty); Double Fare doubles it; recovery fees; buy unlocks in order when affordable. Prompts follow the canon rules
carried in the preset (`economy.rules.no_early_prompts`, `economy.passes.double_fare`, `economy.passes.fare_packs`); only would-be payers
(`payer_share`) buy, with the assumed odds; they may also buy Double Fare unprompted.

## Reading the checks
| check | canon | meaning of a miss |
|---|---|---|
| time to first upgrade | `gameplay.progress.first_unlock` | median runs/minutes to loco 2 too slow |
| day-0 reach (INFO) | same | share of all installs who unlock anything before leaving; the lever for D1 |
| runs started short of the supply kit | `economy.currency.float` (superseded) | 5%+ of runs (first runs shown apart); usually `start_coins` 0 |
| harder pays more | `gameplay.difficulty.band_*` | net coins per run (fare - kit - fees) falls or stays flat (< +5%) from one tier to the next |
| failed trip rule | the open question named in `failed_trip` | the option differs from its default: label every result |
| pacing per unlock | `gameplay.progress.pacing` | gap to the previous unlock outside 0.5-1.5x of the canon gap |
| item size | `gameplay.progress.pacing` | price above the canon run count |
| fare pack cap | `economy.passes.fare_packs` | largest pack above the canon cap x mean run fare (WATCH inside the printed 10% tolerance) |
| fare packs vs playing well | `economy.rules.fair_packs` | a pack buys more fare per R$ than Double Fare earns (our interpretation; confirm) |
| completion | `release.kpi.completion` | arrivals / runs outside the canon band |
| payer conversion | `release.kpi.conversion` | driven by assumed buying odds: a sanity check, not a forecast |
| sink left for veterans | `economy.passes.whale_total` | many actives own everything while balances climb: add fare cosmetics (N/A while the top unlock is out of reach) |

Suggestions cover the first unlock (target runs and minutes), slow or fast gaps (target gap / simulated gap) and
unreached unlocks (net coins per hour x the canon gap), kept in ascending order; for a canon price they say to tune
fares or `start_coins` first. They are starting points for a sweep, not decisions.

## Reporting (what went wrong in trials)
- A proposal is "fixed" only when every check passes or the owner accepts the rest; list the open WATCH/MISS items
  with it (a 40% short-of-kit rate is not fixed because first upgrade passes).
- Name a cause only when its sweep moves the metric: v0's sink/source fall came from the unlock curve (its sweep
  moved it 0.44 -> 0.33), not the crate prices (0.30-0.33 across their sweep).

## Tuning loop
1. `econ.py validate` (canon agreement; lists every assumed value).
2. `econ.py sim --sweep difficulty.Easy.fare_full=1500,1700,1900` (one knob, several values; full sample and the
   same seed on every row; paths must exist, list items by id: `unlocks.loco_2.price`; writes `sweep-<path>.md`).
3. Change your copy in `<R>/presets/economy.json` (never canon numbers: those change through the owner and
   bible.py; an override is reported), rerun `sim`.
4. Once live: replace assumed values with measured ones from the dashboard economy export (mean `fare_bank` per
   trip = fare source / trips; supplies per trip = coal+toolbox+sandwich+medkit sinks / trips; completion from the
   trip progression path) and compare `sink/source` with the memo (`dash.py memo --sim econ.json`).

## Limits
Parametric fares, not a fork-by-fork game model; crews are not simulated together (fare assumed paid to each member
in full, kit split by `kit_paid`/`crew_mean`: proposed open questions); cosmetic revenue is not modelled; buying odds are guesses. Use it to compare
options and catch structural problems (a pack over the cap, a first unlock nobody reaches on day 0, a dead sink),
never as a revenue forecast.
