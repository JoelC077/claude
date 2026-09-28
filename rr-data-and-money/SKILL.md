---
name: rr-data-and-money
description: "Risky Rails analytics and money: AnalyticsService tracking plan, Creator Dashboard CSV weekly memo with KPI checks, A/B test design and statistics, passes, dev products, prices, value ladder, economy sim and a money gate. Not for thumbnail art or receipt-code security. Sub-skill of rr-mission-control (JARVIS): any Risky Rails request, even a short one squarely in this area, goes to rr-mission-control first, which routes here; fire directly only when this skill is named or another rr-* skill invokes it."
---

# RR Data and Money

What to measure, what the numbers say, whether a change worked, and how Risky Rails earns without breaking the
game. Scripts compute every number; you interpret, write the few sentences that need judgement, and hand every
decision that prices, publishes or spends to the owner. Precise, proactive, no filler.

Paths: `<me>` = this skill's folder. `<bible>` = `dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path
'*rr-bible/SKILL.md' 2>/dev/null | head -1)"` (or `$RR_BIBLE_SKILL`); scripts find it the same way. Data root `<R>` =
`$RR_DATA_ROOT`, else `<project>/.rr-data` (the git repo you are in), else `~/.rr-data`. Plans, looks, metrics history
and memos must survive a new session: in the cloud or Cowork a new session is a fresh machine, so keep `<R>` inside
the project repo (and tell the owner to commit it); never a session scratchpad. `selftest.py` prints where it resolves.
Presets: never edit `<me>/presets/` (a synced skill loses edits and every mission would share them). Copy what you
change: `mkdir -p <R>/presets && cp <me>/presets/<name>.json <R>/presets/`; scripts use `<R>/presets/` when it exists
(or `--plan/--config/--catalogue`) and report every value that departs from the skill's canon-checked preset.
All scripts: `python3 <me>/scripts/<name>.py --help`; stdlib only (luatest.py adds lupa and node luaparse from
`~/.cache/rr-tools`, shared with sibling skills; it reports SKIP when they are missing).

## Rules
1. **Canon at run time.** Targets, funnel steps, prices and rules come from rr-bible (`bible get release.kpi`,
   `economy.passes`, `economy.rules`, `D-007`). Presets store `{"v": n, "canon": key}` (the number must be in that
   canon value; `"in": "note"` when canon states it in the note) and the scripts fail when canon moved; values
   without canon are `{"v": n, "assumed": why}` and every report lists them. Never restate canon in prose; cite the key.
2. **Missing canon is recorded, never invented:** `bible add-question ... --default ...`, then label work "assumed
   (OQ-nnn default)"; owner decisions via `bible decide`; `bible lint` after writes. A session that may not write
   canon runs the same commands with `--dry-run` and saves them as a proposals script for the owner. Work built on a
   non-default option of an open question is an owner option, labelled, never a ladder step or a "fix".
3. **Every number you report comes from script output** (stdout, facts.json, econ.json, result.json). Small
   samples get CIs; UNCLEAR stays UNCLEAR. Words follow the stats: "rose/fell" only for a flagged move; a cause
   is named only when a sweep or test isolates it; "fixed" only when every check passes or the owner accepts the rest.
4. **No peeking.** Plans are written once before launch (hashed; re-planning is kept in history and voids earlier
   data); `abtest.py analyze` gives no estimates before the planned sample and date, reads each planned
   O'Brien-Fleming look once, and hides estimates until a look stops the test.
5. **Money gate before anything is sold.** D-007 (time, status, identity only), no co-op pay-to-win, paid random
   items rules, prompt rules, prices that depart from canon. FAIL blocks; HOLD goes to the owner (and
   risky-rails-mechanic-reviewer for gameplay).
6. **Prepare, never act:** no publishing, no live price changes, no Creator Hub experiment launches, no ad spend, no
   messages to players, no changes to the owner's Claude config. Dry-run and hand the gate to the owner. Visual
   judgement (thumbnails, icons, UI, the memo's look) is multiuse-critic's; this skill never scores looks.

## Route the request
| ask | do |
|---|---|
| "track X", "add analytics", "what should we measure" | 1 Instrument |
| dashboard CSVs, "how are we doing", weekly report, KPI check, gate check | 2 Weekly memo |
| A/B test, "is B better", thumbnail/icon/price/onboarding test, significance, sample size | 3 Experiments |
| price, pass, product, subscription, Premium, DevEx, "how do we make money" | 4 Money (ladder + gate) |
| economy, coins/fare balance, inflation, "too grindy", time to first upgrade, difficulty rewards | 5 Economy sim |

## 1 Instrument (read references/analytics.md first)
1. Copy the plan to `<R>/presets/tracking-plan.json`; `track.py validate` (canon funnel = `release.kpi.funnel`,
   canon events and fields, budgets, privacy).
2. Edit the copy for the ask: every event needs `question`, `where`, `value`; fields are enums or numeric buckets;
   no ids or free text. **Every new event, funnel step, SKU or progression status gets a hook** in the owner's copy
   of `RR_AnalyticsHooks.lua` (one call per game moment, literal ids; a variable SKU gets `-- @rr sink: a b` above it).
3. `track.py build --out <owner src or R/track>` -> `RR_AnalyticsPlan.lua` + `TRACKING_PLAN.md`; ship with
   `RR_Analytics.lua` and the hooks (server).
4. Gates: `luatest.py --src <that folder>` must pass; `track.py scan <owner tree> --strict` must PASS (coverage:
   Roblox marks skipped funnel steps complete, so an unlogged step hides its drop instead of showing zero).
5. Tell the owner the wiring in 3 lines: where to require and `init` (ProfileStore `store` adapter); which hooks go
   in which handler (crew-wide steps take the crew list; supply steps belong to the player who opened the
   terminal; purchases use `purchasePrompted/Accepted/Granted`, where "granted" for a pass is the server applying
   it, never ProcessReceipt); the trip id rides in TeleportData. Canon parks the analytics funnel for alpha
   (`release.alpha.sidings`): wire before soft launch.

## 2 Weekly memo
1. First real file of a kind: `dash.py inspect FILE` (fix headers with `--map "Header=metric"`). No exports yet:
   `dash.py demo DIR` writes labelled SYNTHETIC ones (memos built on them are stamped).
2. `dash.py ingest FILES...` (funnel: `--name onboarding`), then `dash.py memo [--week-ending D] [--sim econ.json]`.
   Read stdout only (KPIs, gates, flags, funnels, economy, experiment status).
3. One headline and at most 3 actions tied to flags, gates or drops (canon-aware: an open question to decide, a
   mechanic to review). A metric outside a gate reads "is X (CI a-b), below the gate"; it "fell" only when flagged.
   Rerun with `--headline ... --action ...` so memo.md and memo.html agree.
4. Deliver the paths (publish memo.html as a private Artifact when the owner wants a link). Charts follow the
   dataviz rules already; layout questions go to multiuse-critic.

## 3 Experiments (read references/experiments.md first)
1. Traffic check: `abtest.py size --base P --mde-rel R --daily N`. Over 6 weeks: say so and propose a bolder change
   or a labelled pre/post read. Roblox says experiments struggle under 1,000 DAU.
2. Pick the tool: an in-game change a Config value can express (number, flag, string, JSON) -> **Roblox
   Experiments**: `abtest.py plan NAME --native --primary d1|d7|playtime|arpu|payer_conversion ...`, the owner sets
   it up in Creator Hub, the code reads `ConfigService:GetConfigForPlayerAsync`. Shared crew mechanics randomise by
   server/crew (custom, design effect). Anything else in-game: custom plan + `A.expose`.
3. `abtest.py plan NAME --surface thumbnail|icon|price|onboarding|other --metric prop|rpu|mean ...` with guardrails.
   Custom in-game: copy the printed salt into the mission's plan experiments, set `active`, rebuild. Thumbnails:
   variants from risky-rails-thumbnail-ideas, judged by multiuse-critic first; personalization is a bandit, so read
   it with `abtest.py compare --plan <R>/experiments/NAME --data thumbs.csv` (descriptive, records result.json).
4. At the readout date only: custom `abtest.py analyze <R>/experiments/NAME --data counts.csv`; native `abtest.py
   record <R>/experiments/NAME --metric d1=LO,HI,EST --guardrail ... --enrolled A=n,B=n` (percent-change CIs from
   the Results tab). Report the verdict line, effect with CI, SRM and guardrails. Before then: "running, day X of Y".

## 4 Money (read references/money.md first)
- `econ.py ladder [--state launch|all]`: launch items by default, recurring items apart, earned R$ and DevEx USD per
  sale, whale-total gap. `econ.py guard --sim <econ.json> [--src <luau dir>] [--gate]` -> `MONEY_GATE.md/.json`
  (PASS/HOLD/FAIL/FUTURE; `--gate` exits 1 on FAIL, 3 on HOLD).
- New or changed products go into `<R>/presets/catalogue.json`, honestly labelled (`sells`, `gameplay`,
  `affects_crew`, `random`, `prompt`); a price or size that departs from canon HOLDs (M16) for the owner. Gameplay
  items: risky-rails-mechanic-reviewer before the owner; save its output next to the ladder, and base the verdict on
  what the item changes (e.g. Toolbelt: hotbar tool slots, fewer trips per crisis, D-007), not on a nearby rule.
- Premium engagement payouts ended (Creator Rewards, `economy.platform.creator_rewards`). Price optimization needs
  about 60,000 transactions a month and prices read with `GetProductInfo` (never hard-coded): say both when prices
  come up. Platform facts live in references/money.md until the owner merges them into the bible.

## 5 Economy sim (read references/economy-model.md first)
1. `econ.py validate`, then `econ.py sim --out <R>/econ/<date>`; tune one knob at a time with
   `--sweep path=a,b,c` (full sample, same seed, written to `sweep-<path>.md`) and `--set path=value`. Canon values
   change only through the owner.
2. Report every WATCH/MISS check with its canon key (incl. runs started short of the supply kit and "harder pays
   more"), day-0 reach, sink/source, net coins per run by difficulty (say which result rests on `kit_paid`),
   overrides of canon, price suggestions and the count of assumed values. Blame a problem on a knob only when its
   sweep moves the metric. Replace assumptions with live numbers as soon as the memo has them.

## Plugs
- rr-bible: canon reads through bible.py; gaps and platform facts recorded through it (never hand-edited).
- rr-mission-control: routes data/money work here standalone (no mission kind; its routing table), or
  uses its ledger with this skill's gates as pre-flight
  (`track.py validate`, `luatest.py --gate`, `track.py scan --strict`, `econ.py validate`, `econ.py guard --gate`).
- rr-release-train: does not read `MONEY_GATE.json` yet; the owner reads it. Proposed `presets/gates.json`
  `extra_checks` entry for its owner: `{"gate": "G9", "name": "money gate (rr-data-and-money)", "skill":
  "rr-data-and-money", "cmd": ["{python}", "{skill}/scripts/econ.py", "guard", "--gate", "--run-fare", "<mean fare>"]}`.
- rr-exploit-guard: owns receipt handlers, price trust and grant idempotency in code.
- risky-rails-thumbnail-ideas + multiuse-critic: make and judge variants; this skill plans and reads the test.

## Honest limits
- No Studio, no live servers and no Creator Dashboard or Creator Hub access from the cloud: the Luau is proven in a
  Lua 5.1 VM against stubs; export headers are matched by synonyms until the first real file is inspected.
- Platform facts (AnalyticsService limits and funnel rules, Experiments limits, subscriptions payouts) are dated;
  recheck them before launch-critical use and record changes through bible.py.
- The sim compares options and catches structural problems; it is not a revenue forecast (buying odds, most fares
  and who pays for the crew's supplies are assumed until live data replaces them).

## Maintain
`python3 <me>/scripts/selftest.py` runs every script on synthetic data in a temp root (must print all passed).
Remove `__pycache__` after running scripts. Design rationale: `<me>/design-notes.md`.
