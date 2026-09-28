# Analytics: tracking plan, instrumentation, dashboard exports, weekly memo

Read when instrumenting, changing the tracking plan, ingesting Creator Dashboard exports or writing the memo.

## Platform facts (Roblox creator-docs, fetched 2026-09-28; proposed to rr-bible as source RBXM)
Events are sent **only from the server in published games** (not the client, not Studio), with the `Player` first.
Custom fields: a dictionary keyed by `Enum.AnalyticsCustomFieldKeys.CustomField01..03.Name`, string values.

| call | use | RR wrapper |
|---|---|---|
| `LogOnboardingFunnelStepEvent(player, step, stepName?, fields?)` | first-time funnel; repeated steps are ignored but still count against the rate limit | `A.onboarding(p, id)` |
| `LogFunnelStepEvent(player, funnelName, sessionId?, step, stepName?, fields?)` | recurring funnels (trip, supply, purchase) | `A.funnel(p, f, sid, id)` |
| `LogEconomyEvent(player, flowType, currency, amount, endingBalance, transactionType, itemSku?, fields?)` | every coin in and out (amount > 0, balance >= 0) | `A.source` / `A.sink` |
| `LogProgressionEvent(player, pathName, status, level, levelName?, fields?)` | Start / Complete / Fail per trip difficulty, unlocks | `A.progress` |
| `LogCustomEvent(player, eventName, value = 1, fields?)` | decisions and outcomes; aggregated as count, unique users, sum, avg, min, max | `A.event` |
| `LogJourneyEvent` | non-linear paths (not used yet) | - |

Limits (reset daily; events roll off 90 days after the last data): **120 + 20 x CCU requests per minute**
(RR_Analytics keeps each server under 20 x its players + 20); 3 custom fields, 8,000 combined values then "Other"; 10 funnels x 100 steps; 100 custom
event names; 20 transaction types and 100 SKUs then "Other"; currencies 10 (guide) or 5 (API reference): use one.
Prefer one event with a field over many event names. Charts take about 24 h; the dashboard's View Events tool shows
arrivals sooner. Transaction types: IAP, TimedReward, Onboarding (sources), Shop and Gameplay (either),
ContextualPurchase (sink); custom names are allowed. RR_Analytics prints instead of sending in Studio.
- Retention, DAU, session length, revenue, payer conversion, ARPDAU and acquisition charts need **no**
  instrumentation; the plan adds the why (funnel, economy, progression, custom events).

## The Risky Rails plan (presets/tracking-plan.json; build with track.py)
- Onboarding = canon `release.kpi.funnel`, step for step (validate fails on drift). Each step logs once per player
  **lifetime**, so pass a `store` backed by the ProfileStore profile (`tech.data.store`); without it the module
  logs once per server session and re-counts returning players. A step reached later still logs once (first bank
  on run 2). Steps can be reached out of order (lever before coal): read each step as "ever reached".
- Canon events `run_end(reason)`, `player_left(phase)`, `lever_pulled(by, choice, time_left)` exist with those
  fields; `by` is the player argument itself (no id fields: privacy and cardinality).
- Trip funnel spans two places: create the trip id in the lobby and send it in TeleportData next to the canon
  UserIds (`tech.data.teleport_data`); the trip place uses it as `funnelSessionId`.
- Log outcomes, not ticks: count coal shovels in the run and report totals in the Incident Report, never one event
  per shovel. Rate limits per player per event are in the plan (`max_per_min`).
- Economy: log after the server has changed the balance, with the new balance; SKUs must be planned (unknown ones
  are dropped with one warning). Purchases: `granted` funnel step and the IAP source only after ProcessReceipt saved
  the grant (rr-exploit-guard owns that code).
- Timing: canon parks the analytics funnel as an alpha siding (`release.alpha.sidings`); wire it before soft launch
  (`release.dates.soft_launch`) because the spend gate (`release.gates.spend`) is read from these numbers.

Wiring: `RR_Analytics.lua` + generated `RR_AnalyticsPlan.lua` + `RR_AnalyticsHooks.lua` (one call per game moment:
`playerJoined`, `toolPickedUp`, `coalShovelled`, `leverCommitted`, `stationPaid`, `runEnded`, `orderAccepted`,
`unlockBought`, `crisisEnded`, `resultsAction`, `purchaseStep`, `playerLeft`) into ServerScriptService; `A.init(require(plan), { store = ... })` once per place, then call hooks
after the server applied each change. `track.py scan <src>` finds direct AnalyticsService calls and ids the plan
does not define. Changing the plan: edit JSON -> `track.py validate` -> `build` -> `luatest.py` -> owner syncs.

## Creator Dashboard exports (weekly)
Export each chart's data as CSV from the Creator Dashboard analytics pages (the menu wording moves; recheck).
Weekly set: Engagement (DAU, new users, session length), Retention (D1/D7/D30 by cohort), Monetization
(revenue, paying users, ARPDAU, payer conversion), Acquisition (impressions, qualified play-through, visits),
the onboarding funnel, the economy sources/sinks. The first real file of each kind: `dash.py inspect` and fix
unmapped headers with `--map "Header=metric"`; breakdown exports (by platform, country) need a Total row for
ratios (counts are summed). Dates are ISO or US month/day; ambiguous d/m is flagged.

Definitions used (Roblox's own definitions can differ; the memo says which applied):
- D1/D7/D30: share of a day's new-user cohort that returns on day N; the memo averages the 7 newest mature
  cohorts weighted by cohort size and shows a Wilson 95% CI when new users are known.
- ARPDAU = revenue / DAU; payer conversion = paying users / DAU; ARPPU = revenue / paying users;
  R$ per visit = revenue / visits (`release.gates.continue`). Revenue is treated as earned Robux unless
  `--revenue-is gross` (then x `economy.platform.creator_share`).

## Weekly memo procedure
1. `dash.py ingest <exports>` (add `--name onboarding` for a funnel file), then `dash.py memo`. Read stdout only.
2. Write one headline and at most 3 actions, each tied to a flag, gate or funnel drop, e.g. "Lever -> first bank
   loses 38%: prototype the OQ-007 hint". Rerun with `--headline` and `--action` so md and html match.
3. Rules: a status is UNCLEAR when the CI straddles the target: say so, never round it into a pass. A week-on-week
   move is news only when flagged significant. One odd day is an anomaly to explain (update, featuring, outage),
   not a trend. Experiments appear as status only until their readout (no peeking).
4. Deliver `memo.html` (publish as a private Artifact when the owner wants a link) plus the md path. Canon gaps the
   memo exposes (a missing target, a KPI with no canon) become `bible add-question`, never an invented target.
