# FRICTION: rr-data-and-money trial (2026-09-28)

The trial followed SKILL.md on this task: tracking plan + Luau, an economy sim on a proposed fares/crates/upgrades economy,
a monetization ladder, a synthetic 2-arm thumbnail test and a synthetic 30-day dashboard memo.
- Outputs: `mission/` (index in `mission/BRIEF.md`).
- The skill was not edited. A sha1 of every file taken at the start still matched at the end.
- The top-level `root/ gate/ dash/ econ/ track/ run.log bible-proposals.sh` came from the skill build (03:41-03:43 UTC)
  and are not from this trial.

Severity: H = wrong or missing result a real mission would ship, M = wasted work or a misleading output, L = polish.
**23 items: 5 H, 11 M, 7 L.**

## Analytics (step 1)
1. **H: hooks leave 5 of 12 recurring funnel steps unlogged, and scan cannot see it.** `assets/luau/RR_AnalyticsHooks.lua`
   never calls these steps (grep count 0 for each):
   - trip: `queued`, `boarded`, `departed`
   - supply: `opened`, `fetched`

   [Corrected after review: Roblox marks skipped earlier funnel steps complete, so steps 1-3 would equal `first_fork` and
   `opened` would equal `ordered`: 100% pass-through that hides the drop. Only `fetched` would read 0.]
   `track.py scan` compares only funnel *names* (`planned["funnel"] = set(plan["funnels"])`, around line 304), so it
   printed `PASS ... 0 issues`. The workaround was to add `tripStep`, `terminalOpened` and `crateResolved` to the mission
   copy (`mission/track/src/RR_AnalyticsHooks.lua`). Fix: ship those hooks, and make scan collect the step argument of
   `A.funnel` calls.
2. **H: luatest.py crashes once the example experiment is gone from the plan.** It hard-codes
   `PLAN.experiments.example_onboarding_hint`. A plan without it (which is what step 3.3 produces when a real experiment
   replaces the example) ends in `LuaError: attempt to index field 'example_onboarding_hint' (a nil value)` with a Python
   traceback. That breaks a mission-control pre-flight gate. Fix: inject a test experiment into the loaded plan inside luatest.
3. **M: luatest.py always tests the skill's own `RR_Analytics.lua` and `RR_AnalyticsHooks.lua`** (lines 87-88). Only
   `--plan-lua` is configurable, so the copies the owner actually ships, and any hook a mission adds, go untested. This
   needed `mission/track/test_mission_hooks.py` (5/5). Fix: add `--src DIR`.
4. **M: SKILL tells missions to edit the skill's own presets.** Three places:
   - step 1.2: "Edit `<me>/presets/tracking-plan.json`"
   - Money: "New or changed products go into `<me>/presets/catalogue.json`"
   - economy-model.md: "Change the preset"

   The installed skill is synced (edits get lost), was off-limits here, and a skill shared between missions should not
   carry one mission's plan. The scripts already take `--plan/$RR_TRACKING_PLAN`, `--config` and `--catalogue`, and
   `track.py build` defaults `--out` to the skill's own `assets/luau`. Fix: say "copy it to `<R>/` or the owner repo and
   pass the flag".
5. **M: no route from a new event to code.** After an event is added, scan says "planned event never called in code:
   crate_resolved". SKILL and analytics.md never say to add a hook, and the hooks file is a fixed asset. Fix: one line in
   step 1: "every new event or step gets a hook".

## Economy sim (step 5)
6. **H: nothing checks risk/reward by difficulty.** Proposal v0 paid Easy 688, Medium 614, Hard 164 and Insane -306 net
   coins per run (`mission/econ/difficulty_ev.md`, from the sim's own parameters). That is an inverted ladder in which
   Insane loses money, yet no check, stdout line or report row hinted at it. This needed the helper
   `mission/econ/difficulty_ev.py`. Fix: add a per-difficulty net fare row and a "harder pays more" check.
7. **H: the biggest crate problem stays out of the checks and stdout.** "Runs started short of the supply kit" was 52% for
   v0 and **40% for the skill's own baseline preset**, which is structural: `start_coins` 0 means every first run starts
   short. It is only a row in the ECON_REPORT population table. Step 5.2 says to report the check table, so it gets
   missed, and the sweep table leaves it out too. `--set start_coins=100` drops it to 2% and turns first upgrade from WATCH
   into a PASS (`mission/econ/sweeps.md`). Fix: a WATCH/MISS check, a stdout line and a sweep column.
8. **M: sweeps silently use a smaller, noisier sample and leave no record.** `cmd_sim` sweeps use installs/3 and 300
   engaged players (800 in a full sim). With the same v0 config:

   | | runs to loco_2 | minutes | earned ARPDAU |
   |---|---|---|---|
   | full sim | 7.0 | 94 | 0.974 |
   | sweep row | 6.0 | 81 | 1.323 |

   ARPDAU swings between 0.73 and 1.32 across near-identical configs. `--out` is ignored in sweep mode, so no file is
   written. Fix: print the sample size, average over seeds or drop the revenue columns, and write `sweep.md` to `--out`.
9. **M: canon can be overridden without a warning.** Re-labelling a canon-backed value `{"v", "assumed"}` passes
   `validate`, `sim` and `guard` with 0 warnings. v0 did this for supplies (60/200/30/150 vs canon 40/120/25/90) and for
   loco_2 (4,000 vs canon 2,500); the trial catalogue did it for fare_pack_l (15,000/449 vs 20,000/599). Each shows up
   only in a list of 36 assumed values. Fix: warn "overrides canon `<key>` = `<value>`" whenever the base preset had
   `canon` for that path.
10. **M: failed_trip option B runs without a flag.** It contradicts the OQ-011 default A and the banked-fare pillar
    (`identity.pillars.banked_fare`). Fix: add an INFO or WATCH row when an option differs from the open question's default.
11. **L: price suggestions miss the unlock that matters most.** v0 printed suggestions for loco_3 and loco_4 only: none
    for loco_2 (the first-upgrade MISS) and none for the unreachable loco_5 and line_2. Suggestions also ignore price
    order: a `--quick` run of v0 with the v1 fares and option A suggested loco_5 40,000 -> 14,500, below loco_4 at 20,000.
12. **L: "sink left for veterans" PASSes when nobody can reach the top.** In v0, 0% own every unlock because the unlocks
    are out of reach, and the check reports that as health. Fix: N/A, or MISS when the last unlock goes unreached in the
    engaged cohort.
13. **L: the pack-cap PASS hides a 10% tolerance.** "largest pack 20,000 vs ... = 19,239" prints PASS because of
    `big <= cap * 1.1` (econ.py line 318; guard around line 565), and the line never mentions the tolerance.

## Money (step 4)
14. **H: a `hidden` product still HOLDs the gate.** `express_depot` set to `state: hidden` still produced `HOLD M01`, and
    the verdict stayed HOLD, while `ladder` correctly dropped it. The access/convenience branch ignores `live`. The
    workaround was to set it to `post_launch`, which gives FUTURE. Fix: only `live` products HOLD.
15. **M: ladder mixes launch and post-launch items.**
    - The "entry" row is `livery_low`, a post-launch item, so the canon launch catalogue shows no identity entry at
      launch and the ladder does not say so.
    - "one-time passes total 1,495 R$" includes auto_stoker (post-launch, M01+M04 pay-to-win) but excludes post-launch liveries.

    Fix: a `--state` filter, with launch as the default.
16. **L: the gate is silent on prices that depart from canon.** M13 INFO rows cover only canon-proposed prices; the
    assumed fare_pack_l 15,000/449 gets no row.

## Experiments (step 3)
17. **M: `analyze` crashes on the thumbnail CSV that `compare` accepts.** The data had a `variant` column, and
    `cmd_analyze` fails with `KeyError: 'arm'` and a traceback (abtest.py line 212). compare accepts
    `variant|arm|thumbnail`. Fix: use the same aliases, or exit 1 with a clean message.
18. **M: `analyze` on a `--surface thumbnail` plan neither refuses nor redirects.** With `arm` columns it returned
    INVALID (SRM p = 1.8e-152, which is expected for bandit traffic) and **wrote RESULT.md and result.json into the
    experiment folder**; they were deleted after the check. It also said nothing about the planned `bounce` guardrail
    having no columns in the data. Fix: refuse on thumbnail plans with "use compare", and warn when guardrail data is missing.
19. **M: `compare` leaves no record and never reads guardrails, and the memo then points to the wrong tool.** compare
    writes nothing (its output had to be tee'd into `compare.txt`) and ignores the guardrails experiments.md names
    (session per qualified play, bounce). After the readout date, `dash.py memo` lists the plan as "readout due: run
    abtest.py analyze" (probe with `--week-ending 2026-10-04`), which is the wrong tool for this surface, and the plan can
    never show as read. Fix: `compare --plan DIR` writes a result.json with `kind: descriptive` that the memo reads.
20. **L: `plan --surface thumbnail` prints an in-game instruction.** It says "salt ... copy into tracking-plan
    experiments", which means nothing for a Roblox thumbnail test.

## Memo (step 2)
21. **M: the memo's decision column is cut off at desktop width.** At 1000 px the KPI table's `status` column is clipped
    (`✓ PAS`) and needs a horizontal scroll inside `.tw`, because the target cell holds `>= 10.0 min
    release.kpi.session_min` (`mission/evidence/memo-1000px.png`). There is no page scroll at 390 px. Handed to
    multiuse-critic; not scored here.
22. **L: `--sim` without economy rows is skipped silently.** The memo gives no note that the sim comparison could not
    run. Also, no memo text marks inputs as synthetic apart from the file name in "Data notes" and the headline written
    here; `SYNTHETIC_*` inputs could stamp the memo.

## Canon and discovery
23. **L: rule 2 conflicts with no-write sessions, and the synthetic-data generator is hidden.**
    - Rule 2 says to run `bible add-question`, but trial and mission sessions often may not write canon. SKILL never
      mentions `--dry-run` or the proposals-script pattern the build itself used (`../bible-proposals.sh`); this trial
      used both (`mission/bible-proposals.sh`, dry-run as OQ-042).
    - `dash.py demo` (synthetic exports) appears only in `--help`, not in SKILL.md.

## What worked (for balance)
- Routing and the reference split were right: each step needed exactly one reference. Every script has a working
  `--help`, and `quick_validate` and `selftest` pass (48/48).
- `dash.py inspect` mapped all 11 hand-written Creator-Dashboard-style headers first time, including seconds -> minutes
  and US dates.
- The memo's KPIs matched an independent recount. Payer conversion was 13/1,833 = 0.71% this week against 20/1,628 last
  week. The memo called that change "nothing beyond noise", and a recomputed two-proportion z test agrees (p ≈ 0.12).
  UNCLEAR stayed UNCLEAR (D7, scale gate).
- The sim, `--set` and `--sweep` found every structural v0 problem except 6 and 7 in about 1 s per run. The v0 -> v1
  loop took 4 short runs.
- Canon keys the skill cites all exist (`release.alpha.sidings`, `tech.data.teleport_data`, `release.gates.*`).
- The gate correctly FAILed the canon 20,000 pack against v0.
