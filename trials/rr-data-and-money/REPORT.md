# rr-data-and-money: fix report (2026-09-28)

The skill is fixed, validated and packaged to `/home/user/claude/dist/rr-data-and-money.skill`. I could not write `/home/user/claude/trials/rr-data-and-money/REPORT.md`: the harness blocks subagents from writing report files, so the report is here instead. The `BRIEF.md` errata line no longer points to that file.

Inputs were FRICTION.md (23 items) and two independent reviews, which scored the skill 6.5 and 6. Every high and medium finding is applied, along with every cheap low one. All 23 FRICTION items are fixed. Two suggestions were applied partly and one went further than asked; the reasons are under "Partly applied".

## Changes

**Analytics (hooks, plan, scan, luatest)**
- `RR_AnalyticsHooks.lua` was rewritten so every planned step, event and SKU is logged with a literal id:
  - **Trip:** `tripQueued`, `tripBoarded`, and `tripDeparted`, which logs departure and progression `Start` for the whole crew. `forkResolved` logs `first_fork` for the whole crew, not only the player who pulled the lever.
  - **Supply:** `terminalOpened`, and `crateResolved(orderer, fetcher, …)`. The funnel step goes to the orderer, who owns the session; the `crate_resolved` event goes to the fetcher.
  - **Purchases:** `purchasePrompted`, `purchaseAccepted` and `purchaseGranted` keep the prompt id per player and product. For a game pass, "granted" happens in the PromptGamePassPurchaseFinished handler, never in ProcessReceipt.
  - **Economy:** `farePackGranted`, `promoRedeemed`, `recoveryCharged` and `liveryBought`.
  - **Unlocks:** `unlockBought` takes an id (`loco_N` or `line_2`) and maps it to its progression level.
- `RR_Analytics.lua`:
  - The server budget is now 20 × players. Summed over all servers that is 20 × CCU, which fits inside 120 + 20 × CCU whether the limit is per server or for the whole game.
  - New `A.levelIndex` helper.
- Tracking plan:
  - Every step now says which player it is logged for.
  - "granted" is defined separately for products and passes.
  - Added: the `line_2` SKU, a `lines` progression path, allowed statuses per path, and a `crate_resolved` event.
- `track.py scan` now checks coverage:
  - It errors on any planned step, event, status or SKU that no code logs, and on unplanned ids.
  - Dynamic SKUs are declared with a `-- @rr sink:` comment.
  - Hooks that game code never calls are listed; `--strict` makes them errors.
- `track.py build` writes to `<R>/track` by default, never into the skill folder.
- `luatest.py`:
  - `--src DIR` tests the owner's copies; `--gate` exits 3 when tools are missing.
  - It injects its own test experiment, so a plan without the example no longer crashes it.
  - New crew hook tests: two-player crate, crew-wide steps, purchase flow, and a scripted two-player trip where nothing is dropped.
  - A Lua error in the hooks shows as a failed check, not a traceback.

**Experiments (`abtest.py`, `statlib.py`)**
- The small-sample Fisher test no longer crashes on decimal counts.
- The four no-peeking holes are closed:
  - `--asof` defaults to today.
  - `plan` refuses to overwrite a plan. `--replace` keeps the old one in `history/`, and analyze refuses the test if it was re-planned after data was seen.
  - The final look uses the last printed O'Brien-Fleming boundary.
  - Each interim look is recorded in `looks.json` and read once; CONTINUE shows no estimates.
- Roblox Experiments are now supported:
  - `plan --native --primary` checks 14–60 days and at most two variants, and prints the ConfigService setup.
  - `record` gives the pre-registered verdict from the Results-tab confidence intervals, with a sample-ratio check on enrolled counts and guardrails.
- Thumbnails:
  - `analyze` refuses thumbnail plans and redirects to `compare`.
  - `compare --plan` writes a descriptive `result.json` and prints guardrail columns.
  - Column aliases are shared between the two, and thumbnail plans print no salt line.
- Invalid inputs exit 1 with a clear message.

**Economy and money gate (`econ.py`, `rrlib.py`, presets)**
- New sim checks, each shown on stdout and in sweeps:
  - Runs started short of the supply kit, with first runs shown separately.
  - "Harder pays more", backed by a table of net coins per run for each difficulty.
  - Failed-trip rule, flagging an option that differs from the open question's default.
- Supply kits are per train (`gameplay.supplies.one_order`). New `kit_paid` and `crew_mean` settings are labelled as assumed values.
- Price suggestions:
  - They now cover `loco_2` and unlocks nobody reaches, kept in ascending order.
  - For a canon price they say to tune fares or `start_coins` first.
- "Sink left for veterans" reads N/A while the top unlock is out of reach. The fare-pack cap tolerance is printed, and a pack inside it is WATCH.
- Sweeps:
  - They run the full sample on the same seed, print the sample size and write `sweep-<path>.md`.
  - The noisy revenue columns are dropped.
  - A path typo fails cleanly.
- Canon checks:
  - A number must match the canon value itself; `"in": "note"` opts into the note, and mission copies inherit that flag. Before, coal = 10 passed by matching a "10 R$ placeholder" in the note.
  - A canon value relabelled "assumed" in a copy is reported as an override.
- Money gate (`guard`):
  - Hidden products no longer HOLD.
  - Rules come from the canon-checked preset instead of being parsed from prose.
  - New rule M16 holds a price or pack size that departs from canon.
  - New rule M17 holds a launch item whose canon says post-launch.
  - `--gate` exits 1 on FAIL and 3 on HOLD, and requires `--sim` or `--run-fare`.
- `ladder` shows launch items by default (`--state`), lists recurring items separately and reports the gap to the canon whale total.
- The Toolbelt is relabelled as hotbar tools under D-007, not the carry-one-thing rule.

**Weekly memo (`dash.py`)**
- The spend-gate cohort row uses a confidence interval per cohort and can read UNCLEAR.
- The payer-conversion interval uses weekly unique players when an export has them, otherwise player-days ÷ 1.5. The 1.5 is an assumption and is labelled.
- Memos built from files named SYNTHETIC_* are stamped as synthetic.
- Empty files, header-only files, a missing store and an unusable `--sim` give clean messages.
- Experiment status reads `result.json` and names the right readout tool.
- In the KPI table, status sits next to the value and the target column wraps. At 1000 px the table no longer scrolls sideways; at 390 px the status column is visible without scrolling. This is a structural check only; visual judgement stays with multiuse-critic.

**Docs (SKILL.md 138 lines, references, design-notes)**
- The data root defaults to `<project>/.rr-data` so it survives a fresh cloud machine.
- Missions copy presets into `<R>/presets` instead of editing the skill's own.
- New step: every new id gets a hook.
- Rule 2 covers sessions that cannot write canon: `--dry-run` plus a proposals script.
- Wording rules: "rose/fell" only for a flagged move; a cause only when a sweep isolates it; "fixed" only when every check passes.
- The Roblox funnel rules and Roblox Experiments facts are documented, and canon numbers are no longer restated.
- Plugs are now accurate:
  - rr-release-train does not read `MONEY_GATE.json`; SKILL.md carries a proposed `extra_checks` entry for it.
  - rr-mission-control has no data mission kind.

**Trial folder**
- `mission/BRIEF.md` has an errata block, and FRICTION item 1 is corrected (Roblox marks skipped funnel steps complete).
- `bible-proposals.sh`:
  - The Toolbelt question and the rate-limit note are fixed.
  - Three platform facts are added: funnel rules, pass grant, Roblox Experiments.
  - Two open questions are added: who pays for supplies, and starting coins.
  - It was dry-run on a copy of canon and lint passed; real canon was not written.
  - Applied to the real rr-bible on 2026-09-28 by the reconcile (the two starting-coins drafts merged): OQ-048..OQ-055; the mission draft is OQ-056.

## Re-trial of the changed parts (trial inputs, outputs in the scratchpad)
- **Mission hooks (`luatest --src`):** 27/34. It now catches the trial's real bugs: the 40/min server budget, `crateResolved` crediting the wrong player, missing hooks, and the old `unlockBought`.
- **Mission tree (`scan`):** FAIL. It lists the missing trip and purchase steps, trip Start, the fare-pack, promo and recovery-fee SKUs, and the hard-coded `loco_` id.
- **Fresh instrument run** (copy the plan, build, then check): luatest 35/35 on a build that landed in `<R>/track`; `scan --strict` lists 22 unwired hooks.
- **v0 sim.** It now flags:
  - An INVERTED difficulty ladder: Insane −252 net coins per run if each player pays the whole kit, +230 if the kit is split over a crew of 3.
  - 52% of runs starting short of the kit.
  - Option B against the OQ-011 default A.
  - 5 canon overrides.
  - A price suggestion for `loco_2`.
- **v1 sim:** 4 checks at WATCH or MISS, including 40% short runs. Sweeping `start_coins` 0/100/200 takes short runs from 40% to 2%, and first upgrade goes from WATCH to PASS.
- **Money gate on the trial catalogue:** HOLD, with M16 twice (large fare pack), M17 (horn) and M01 (private server). Launch passes total 747 R$, 1,253 below the whale total.
- **Mission memo:** payer conversion 0.71%, CI 0.4–1.4%, MISS. The spend-cohort row reads UNCLEAR, the memo is stamped SYNTHETIC, and the thumbnail plan points to `compare --plan`.
- **Experiments:** 6 vs 11 conversions in 2,400 per arm now runs Fisher's test (p = 0.33) instead of crashing. A final look at z = 1.98 against a 2.03 boundary now reads NO DIFFERENCE; before the fix it said "SHIP B".

## Partly applied (with reasons)
- **"Bind each canon number to its position in the text, or use rr-bible's structured tokens"** (review 2): I split value from note, and copies inherit the flag from the skill's preset. That catches the reported case. I did not bind by position, because positions in prose shift whenever canon is reworded, and rr-bible's `tokens` export only covers colours and fonts, not economy numbers.
- **"Divide the kit by crew size or label it"** (review 1): I did both. The split is the default, labelled as assumed, and can be switched back per preset. This moved the skill's baseline:
  - Short runs are now 22% (56% of first runs), still a MISS.
  - Completion is 60%, WATCH at the canon edge.
  - The fare-pack cap is still a MISS.
- **"Hide estimates on CONTINUE"** (review 2): applied, and I went one step further on the other side. A test that stops at an interim look (win or loss) prints every estimate, because a stopped test needs its effect size and confidence interval.

## Validation and package
- selftest: 71/71 passed (was 48)
- luatest: 35/35 passed
- `track.py validate`, `track.py scan` of the shipped Luau, and `econ.py validate`: all PASS
- `--help` works on all 9 scripts
- `quick_validate`: "Skill is valid!" (description 1,014 characters, no angle brackets)
- `__pycache__` removed from the skill and trial folders
- Package: `/home/user/claude/dist/rr-data-and-money.skill`
- Review scores before the fix: [6.5, 6]

Files changed:
- `/home/user/claude/rr-data-and-money/` (SKILL.md, design-notes.md, references/*.md, scripts/{abtest,dash,econ,luatest,rrlib,selftest,statlib,track}.py, assets/luau/{RR_Analytics,RR_AnalyticsHooks,RR_AnalyticsPlan}.lua, TRACKING_PLAN.md, presets/{tracking-plan,economy,catalogue}.json)
- `/home/user/claude/trials/rr-data-and-money/` (FRICTION.md, mission/BRIEF.md, bible-proposals.sh)