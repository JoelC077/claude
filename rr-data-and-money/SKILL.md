---
name: rr-data-and-money
description: "Risky Rails (Roblox) analytics, experiments and money. Analytics: AnalyticsService tracking plan (onboarding, trip and purchase funnels, economy, progression, custom events) plus a tested server Luau module; Creator Dashboard CSVs into a weekly memo with charts and CI-aware checks against canon KPIs and release gates (D1/D7/D30, session length, payer conversion, ARPDAU). Experiments: A/B plans and readouts with sound statistics (sample size in days at real traffic, pre-registration, no peeking, SRM) for thumbnails, icons, prices and onboarding. Money: passes, dev products, subscriptions, Premium, value ladder, price points, an economy sim (faucets, sinks, inflation, time to first upgrade) and a money gate (never sell odds, no co-op pay-to-win, paid random items). Use whenever Risky Rails work mentions analytics, events, funnels, retention, KPIs, dashboards, weekly reports, A/B tests, significance, prices, Robux, monetization, economy, coins, fare or loot boxes. Not for thumbnail art or receipt-code security."
---

# RR Data and Money

What to measure, what the numbers say, whether a change worked, and how Risky Rails earns without breaking the
game. Scripts compute every number; you interpret, write the few sentences that need judgement, and hand every
decision that prices, publishes or spends to the owner. Precise, proactive, no filler.

Paths: `<me>` = this skill's folder. `<bible>` = `dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path
'*rr-bible/SKILL.md' 2>/dev/null | head -1)"` (or `$RR_BIBLE_SKILL`); scripts find it the same way. Data root
`<R>` = `$RR_DATA_ROOT`, else `~/.rr-data` (metrics.json, memos/, experiments/, econ/, gate/); never a session
scratchpad. All scripts: `python3 <me>/scripts/<name>.py --help`; stdlib only (luatest.py adds lupa and node
luaparse from `~/.cache/rr-tools`, shared with sibling skills; it reports SKIP when they are missing).

## Rules
1. **Canon at run time.** Targets, funnel steps, prices and rules come from rr-bible (`bible get release.kpi`,
   `economy.passes`, `economy.rules`, `D-007`). Presets store `{"v": n, "canon": key}` and the scripts fail when
   canon moved; values without canon are `{"v": n, "assumed": why}` and every report lists them. Never restate
   canon in prose you write; cite the key.
2. **Missing canon is recorded, never invented:** `bible add-question ... --default ...` (then label work "assumed
   (OQ-nnn default)"); owner decisions via `bible decide`. Run `bible lint` after writes.
3. **Every number you report comes from script output** (stdout, facts.json, econ.json, result.json). Small
   samples get CIs; UNCLEAR stays UNCLEAR.
4. **No peeking.** Experiments are planned (and hashed) before launch; `abtest.py analyze` gives no estimates before
   the planned sample and date. Only planned O'Brien-Fleming looks may stop early.
5. **Money gate before anything is sold.** D-007 (time, status, identity only), no co-op pay-to-win, paid random
   items rules, prompt rules. FAIL blocks; HOLD goes to the owner (and risky-rails-mechanic-reviewer for gameplay).
6. **Prepare, never act:** no publishing, no live price changes, no ad spend, no messages to players, no changes to
   the owner's Claude config. Dry-run and hand the gate to the owner. Visual judgement (thumbnails, icons, UI) is
   multiuse-critic's; this skill never scores looks.

## Route the request
| ask | do |
|---|---|
| "track X", "add analytics", "what should we measure" | 1 Instrument |
| dashboard CSVs, "how are we doing", weekly report, KPI check, gate check | 2 Weekly memo |
| A/B test, "is B better", thumbnail/icon/price/onboarding test, significance, sample size | 3 Experiments |
| price, pass, product, subscription, Premium, DevEx, "how do we make money" | 4 Money (ladder + gate) |
| economy, coins/fare balance, inflation, "too grindy", time to first upgrade | 5 Economy sim |

## 1 Instrument (read references/analytics.md first)
1. `track.py validate` (canon funnel = `release.kpi.funnel`, canon events and fields, budgets, privacy).
2. Edit `<me>/presets/tracking-plan.json` for the ask: every event needs `question`, `where`, `value`; fields are
   enums or numeric buckets; no ids or free text. Experiments get a `tag` only if a field slot is free.
3. `track.py build --out <owner src or export dir>` -> `RR_AnalyticsPlan.lua` + `TRACKING_PLAN.md`; ship with
   `<me>/assets/luau/RR_Analytics.lua` and `RR_AnalyticsHooks.lua` (server; hooks = one call per game moment).
4. `luatest.py` (Lua 5.1 VM + luaparse) must pass; `track.py scan <src>` on the owner's code when available.
5. Tell the owner the wiring in 3 lines: where to require and `init` (with the ProfileStore `store` adapter),
   which hooks go in which handler, that the trip id rides in TeleportData. Note canon parks the analytics funnel
   for alpha (`release.alpha.sidings`): wire before soft launch.

## 2 Weekly memo
1. First real file of a kind: `dash.py inspect FILE` (fix headers with `--map "Header=metric"`).
2. `dash.py ingest FILES...` (funnel: `--name onboarding`), then `dash.py memo [--week-ending D] [--sim econ.json]`.
   Read stdout only (KPIs, gates, flags, funnels, economy, experiment status).
3. Write one headline and at most 3 actions tied to flags, gates or drops (canon-aware: e.g. an open question to
   decide, a mechanic to review). Rerun with `--headline ... --action ...` so memo.md and memo.html agree.
4. Deliver the paths (and publish memo.html as a private Artifact when the owner wants a link). Charts follow the
   dataviz rules already; do not restyle them.

## 3 Experiments (read references/experiments.md first)
1. Traffic check: `abtest.py size --base P --mde-rel R --daily N`. Over 6 weeks: say so and propose a bolder change
   or a labelled pre/post read.
2. `abtest.py plan NAME --surface thumbnail|icon|price|onboarding|other --metric prop|rpu|mean ...` with guardrails;
   shared crew mechanics randomise by server/crew (design effect), not by player.
3. In-game: copy the printed salt into `tracking-plan.json` experiments, set `active`, rebuild; the game calls
   `A.expose(player, name)` where the change is seen. Thumbnails: variants from risky-rails-thumbnail-ideas, judged
   by multiuse-critic first; Roblox thumbnail personalization is adaptive, so read it with
   `abtest.py compare --data thumbs.csv` (descriptive CIs, flags clear losers, no verdict).
4. At the readout date: `abtest.py analyze <R>/experiments/NAME --data counts.csv --asof DATE`. Report the verdict
   line, the effect with CI, SRM and guardrails. Before then the answer is "running, day X of Y".

## 4 Money (read references/money.md first)
- `econ.py ladder`: value ladder, steps, earned R$ and DevEx USD per sale, whale-total check.
- `econ.py guard [--sim <econ.json>] [--src <luau dir>]` -> `MONEY_GATE.md/.json` (PASS/HOLD/FAIL/FUTURE).
  New or changed products go into `<me>/presets/catalogue.json` first, honestly labelled (`sells`, `gameplay`,
  `affects_crew`, `random`, `prompt`). Gameplay items: risky-rails-mechanic-reviewer before the owner.
- Premium engagement payouts ended (Creator Rewards, `economy.platform.creator_rewards`). Roblox price optimization
  needs about 60,000 transactions a month and prices read with `GetProductInfo` (never hard-coded): say both when
  prices come up. Platform facts live in references/money.md until the owner merges them into the bible.

## 5 Economy sim (read references/economy-model.md first)
1. `econ.py validate`, then `econ.py sim --out <R>/econ/<date>`; tune one knob at a time with
   `--sweep path=a,b,c` (and `--set path=value`). Canon values change only through the owner.
2. Report the check table (PASS/WATCH/MISS with canon keys), day-0 reach, sink/source, pack cap, price suggestions
   and the count of assumed values. Replace assumptions with live numbers as soon as the memo has them.

## Plugs
- rr-bible: canon reads through bible.py; gaps and platform facts recorded through it (never hand-edited).
- rr-mission-control: data/money deliverables are mixed-kind missions; this skill's gates are pre-flight
  (step 6): `track.py validate`, `luatest.py`, `econ.py validate`, `econ.py guard`.
- rr-release-train: reads `MONEY_GATE.json` (`verdict`, `blocking`, `hold`) and the memo's gate table.
- rr-exploit-guard: owns ProcessReceipt, price trust and grant idempotency in code.
- risky-rails-thumbnail-ideas + multiuse-critic: make and judge variants; this skill plans and reads the test.

## Honest limits
- No Studio, no live servers and no Creator Dashboard access from the cloud: the Luau is proven in a Lua 5.1 VM
  against stubs; export headers are matched by synonyms until the first real file is inspected.
- Platform facts (AnalyticsService limits, subscriptions payouts, native experiments) are dated; recheck them
  before launch-critical use and record changes through bible.py.
- The sim compares options and catches structural problems; it is not a revenue forecast (buying odds and most
  fares are assumed until live data replaces them).

## Maintain
`python3 <me>/scripts/selftest.py` runs every script on synthetic data in a temp root (must print all passed).
Remove `__pycache__` after running scripts. Design rationale: `<me>/design-notes.md`.
