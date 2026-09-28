# rr-data-and-money · design notes (2026-09-28)

## Job
Everything numeric about running Risky Rails as a business, in one skill: what to measure (a tracking plan and a
server Luau module on Roblox AnalyticsService), what the numbers say (Creator Dashboard CSV exports into a weekly
memo with charts, judged against canon targets), whether a change worked (A/B tests with honest statistics), and
how money is made without breaking the game (products, value ladder, prices, an economy simulation and a money
gate). Scripts compute; Claude interprets; the owner decides and presses every button that spends, publishes or
prices.

## Pipeline
```
bible get (targets, funnel, prices, rules) ----------------------------------------------+
presets/tracking-plan.json -> track.py validate|build|doc|scan -> RR_AnalyticsPlan.lua    |
                               + assets/luau/RR_Analytics.lua (server; pcall-safe; luatest in Lua 5.1)
Creator Dashboard CSVs -> dash.py inspect|ingest -> metrics.json -> dash.py memo -> memo.md/.html + SVG charts
experiment idea -> abtest.py plan (pre-registered once, hashed; days needed from traffic; --native for Roblox
               Experiments) -> run whole weeks -> analyze (custom: refuses before the horizon; SRM; CI; guardrails;
               planned looks read once) | record (native Results tab) | compare --plan (thumbnail bandit, descriptive)
presets/economy.json -> econ.py validate|sim (population + engaged-pacing cohorts, sweeps) -> ECON_REPORT + charts
presets/catalogue.json -> econ.py ladder (value ladder, USD per sale) | guard -> MONEY_GATE.md/.json
```

## Decisions (with why)
1. **Canon at run time, never restated.** Targets (release.kpi.*, release.gates.*), the funnel, prices and rules
   are read through bible.py; presets hold `{"v": n, "canon": key}` and validation proves the number is still in
   canon. Missing canon is `{"v": n, "assumed": why}` and every report prints the assumed list.
2. **Stdlib only.** Normal/t/chi-square/Fisher, Wilson/Newcombe CIs, sample size, O'Brien-Fleming bounds by
   seeded simulation, SVG charts: all Python stdlib, so it runs in cloud, Cowork and on the owner's PC.
   lupa + node luaparse (already cached by sibling skills) test the Luau; missing tools skip loudly.
3. **No peeking is enforced, not advised.** A plan is written once before launch and hashed (re-planning is kept
   in history and voids data already seen); analyze checks the date against today, refuses a verdict before the
   planned sample, reads each planned look once and shows no estimate until a boundary is crossed; the final look
   uses the planned final boundary. SRM is checked first. Roblox Experiments are the default for config-expressible
   in-game changes (native per-variant D1/D7/ARPU); abtest.py keeps sizing, pre-registration and readout discipline.
4. **Traffic realism.** Plans convert sample size to days at the owner's real traffic and say "not testable" when
   it takes over 6 weeks; small games test bold changes or accept a pre/post read labelled as such.
5. **Funnels see every step.** Roblox marks skipped funnel steps complete, so a missing hook reads as 100%
   pass-through, not zero. The hooks log every planned step on the player who owns the session (crew-wide steps
   for the whole crew; supply steps on the orderer), and `track.py scan` fails on any planned step, event, status or
   SKU no code logs. Purchases are "granted" where the benefit is saved: receipts for products, the Finished
   handler for passes.
5b. **Analytics never breaks gameplay.** Every AnalyticsService call is pcall-wrapped, rate-limited, schema-checked
   against the generated plan (unknown events dropped, enums and numeric buckets bound cardinality), and the
   experiment hash is identical in Python and Luau (tested on thousands of ids).
6. **Money gate like the security gate.** econ.py guard turns D-007 (time, status, identity only), co-op
   pay-to-win, paid random items, prompt rules, fare-pack rules and departures from canon prices into
   PASS/HOLD/FAIL (`--gate` exit codes); only the owner waives. rr-release-train does not read it yet (proposed
   extra check in SKILL.md).
6b. **Mission copies, never skill edits.** Presets are copied to `<R>/presets/` and picked up there; a value that
   was canon in the skill's preset and is "assumed" in a copy is reported as an override. The data root defaults to
   the project repo so plans and history survive a fresh cloud machine.
7. **Two sim cohorts.** A churned population (installs x days, retention fitted to canon D1/D7/D30) answers
   day-0 reach, inflation, short-of-kit runs and revenue; an engaged cohort answers pacing (hours to each unlock)
   and net coins per run by difficulty, which churn hides. The trial's biggest misses (an inverted difficulty
   ladder, 40-52% of runs short of supplies) are now checks, not table rows.
8. **Visual judgement stays with multiuse-critic.** Thumbnail/icon quality is risky-rails-thumbnail-ideas plus the
   critic; this skill only measures which one players click and keep playing. Roblox thumbnail personalization is a
   bandit, so it gets a descriptive `compare` (CIs, clear losers), never an A/B verdict.
9. **Platform facts verified, not remembered.** AnalyticsService limits (120 + 20 x CCU/min, 10 funnels, 100 event
   names, 8,000 field values), paid random items, Managed pricing (60k transactions), Roblox Plus, Creator Rewards,
   BindReceiptHandler were read from the creator-docs mirror on 2026-09-28 and drive the code (server-wide rate
   bucket, plan limits, price-test guidance); they go to the bible as source RBXM via the proposals script.

## Plugs
- rr-bible: canon read via bible.py (found by glob or RR_BIBLE_SKILL); gaps become add-question/add-fact commands
  (proposals for this build: `trials/rr-data-and-money/bible-proposals.sh`, replayed by the orchestrator).
- rr-exploit-guard: owns ProcessReceipt/price-trust code review; money gate points to it.
- rr-release-train: no money gate yet; proposed `extra_checks` entry running `econ.py guard --gate`.
- rr-mission-control: no data kind (mixed = UI + 3D with a critic loop); data/money work runs standalone or uses its
  ledger with this skill's gates as pre-flight.
- risky-rails-mechanic-reviewer: every gameplay-touching product (HOLD) goes through it before the owner.
- risky-rails-thumbnail-ideas + multiuse-critic: make and judge variants; abtest.py plans and reads the test.

## Limits
No Studio and no Creator Dashboard access from the cloud: the Luau is proven in a Lua 5.1 VM with stubs, not in a
live server; dashboard CSV headers are matched by synonyms and must be confirmed on the first real export
(`dash.py inspect`); platform facts are dated 2026-09-28. The sim's fares and buying odds are assumptions until live
data replaces them. Nothing here publishes, prices, spends or messages players.
