# rr-data-and-money trial mission: brief (SYNTHETIC DATA)

Everything here runs on **synthetic** inputs made for the trial (`synthetic/make_synthetic.py`, seed 20260928, and
`econ/proposal-v0.json`). None of it is Risky Rails data. Numbers are quoted from script output; the owner decides every price.
Data root for the run: `data/` (`RR_DATA_ROOT`).

## 1 Instrument: tracking plan + Luau
- Plan: `track/tracking-plan.json` (a copy of the skill preset plus `crate_resolved(kind, outcome, difficulty)`, value =
  seconds from landing to fetch or slide-off). `track.py validate`: PASS, 1 warning (currency name is OQ-003, labelled assumed).
- Built: `track/src/RR_AnalyticsPlan.lua`, `track/src/TRACKING_PLAN.md`; shipped with `RR_Analytics.lua` and
  `RR_AnalyticsHooks.lua`. `luatest.py`: 28/28; `track.py scan track/src`: PASS, 0 issues.
- Hooks added in this copy: the skill's hooks never log trip steps 1-3 (queued, boarded, departed) or supply steps 1 and 3
  (opened, fetched), so those dashboard funnels would start at zero. Added `tripStep`, `terminalOpened`, `crateResolved`;
  `track/test_mission_hooks.py` 5/5.
- Wiring (3 lines): (1) put the three modules in ServerScriptService in the lobby and trip places; each place calls
  `A.init(require(RR_AnalyticsPlan), { store = <ProfileStore get/set adapter> })` once (`tech.data.store`). (2) Call each hook
  after the server has applied the change: lobby = playerJoined, tripStep("queued"); trip = tripStep boarded/departed,
  toolPickedUp, coalShovelled, leverCommitted, stationPaid, crisisEnded, runEnded; Depotron = terminalOpened, orderAccepted,
  crateResolved; shop = unlockBought; purchases = purchaseStep (the "granted" step comes after ProcessReceipt, owned by
  rr-exploit-guard); PlayerRemoving = playerLeft. (3) Create the trip id in the lobby and send it in TeleportData next to the
  UserIds (`tech.data.teleport_data`). Canon parks the analytics funnel for alpha (`release.alpha.sidings`): wire it before soft launch.

## 5 Economy sim: problems in the proposed fares/crates/upgrades economy (v0)
Report: `data/econ/2026-09-28-proposal-v0/ECON_REPORT.md` (+ 3 SVG charts). Baseline for comparison: `.../2026-09-28-baseline/`.
1. **First upgrade too slow:** loco_2 at 4,000 takes a median of 7.0 runs / 94 min. The target is about 2 runs inside 30 min
   (`gameplay.progress.first_unlock`). Only 2% of installs reach it on day 0 (baseline 39%).
2. **Difficulty ladder inverted:** net coins per run are Easy 688, Medium 614, Hard 164 and Insane -306
   (`econ/difficulty_ev.md`). Farming Easy is the best strategy and Insane loses coins. The causes are flat fares, a crate
   price hike, heavier kits and failed trips paying nothing.
3. **Upgrade curve out of reach:** loco_3 comes +4.0 h after loco_2 and loco_4 +5.8 h after loco_3. loco_5 and line_2 are
   not reached within 12 h. Canon wants about 2 h per unlock (`gameplay.progress.pacing`).
4. **Fare pack cap broken:** the 20,000 pack is far above 10 x the mean run fare of 722 (= 7,224). Against v0, the money
   gate FAILs fare_pack_l on M07 (`money/gate-canon-catalogue-vs-v0/`).
5. **Crates starve runs:** 52% of runs start short of the supply kit. The sim's summary lines and check table never show
   this; it appears only in the report's population table. Even the baseline preset has 40%, because new players start
   with 0 coins. Giving 100 starting coins cuts it to 2% and turns first upgrade into a PASS at 2.0 runs / 27 min (`econ/sweeps.md`).
6. **The crate sink backfires:** sink/source falls to 0.32 (baseline 0.52). Nobody reaches the unlocks, so coins pile up
   (median balance 1,123 -> 1,348).
7. **Failed trips pay nothing (option B),** against the OQ-011 default (A, a pillar). The sim models this without flagging it.

**v1** (`econ/proposal-v1.json` changes loco_2 back to canon 2,500, uses option A, sets fares to 1,700/2,300/3,100/4,200
and unlocks to 12k/15k/18k/22k, and keeps the crate hike). Result: first upgrade is WATCH at 2.5 runs / 34 min (the sweep
reaches 2.0 runs at an Easy fare of 1,800). Day-0 reach is 40%, all 4 pacing checks PASS, the pack cap PASSes (within the
cap's 10% tolerance), sink/source is 0.53, and net coins per run rise with difficulty (1.00x/1.20x/1.26x/1.41x). The sim
compares options; it does not forecast revenue. 35 values are still assumed.

## 4 Money: launch ladder + gate
`money/catalogue-trial.json`, `money/ladder.md`, `data/gate/MONEY_GATE.md|json` (verdict **HOLD**: 0 fail, 1 hold, 5 future).

| step | item | R$ | sells | why |
|---|---|---|---|---|
| entry | Launch Whistle (horn) | 49 | identity | first purchase is the hardest; canon puts liveries post-launch -> owner question (bible-proposals.sh) |
| 1 | Fare pack S | 99 | time | shown only when short by under 30%, after run 3 |
| 2 | Private server | 150/month | access | HOLD M01: owner confirms it counts as time or identity |
| 3 | Fare pack M | 249 | time | |
| core | Double Fare | 299 | time | one prompt, on the results of the best run so far |
| anchor | First Class | 399 | identity/status | makes Double Fare the sensible buy |
| top | Fare pack L, resized to 15,000 | 449 | time | same 33.4 fare/R$ as canon 20,000/599, and fits under the 10-run cap |

Post-launch: liveries (49-199 R$ or fare) and Express Depot (canon: ship private servers first). Toolbelt comes off the
launch ladder. Applying the mechanic-reviewer checklist, the verdict is **Needs adjustment**: +2 slots breaks
carry-one-thing (`gameplay.supplies.hand`, `identity.pillars.reuse_verbs`). Fewer trips per crisis is survival power
under D-007, so either rework it as a cosmetic toolbelt at the same price or cut it. Auto Stoker is never sold as designed
(M01 + M04). Robux supplies stay hidden (OQ-010). Read prices in game with `GetProductInfo` from day one, because price
optimization needs about 60,000 transactions in 30 days.

## 3 Experiments: 2-arm thumbnail test
The plan is `data/experiments/thumb_lever_vs_crash/plan.json`: 3.0% -> 3.45% needs 24,193 impressions per arm, which is
14 days at 4,000/day. Traffic was adaptive (thumbnail personalization), so the test is read descriptively
(`.../compare.txt`) with no verdict. B_boiler_blast had 3.66% QPTR (95% CI 3.46%-3.88%, n 31,092). A_lever_calm had 3.06%
(2.85%-3.28%, n 24,870) and is clearly below the best: replace A at the next update. Guardrail not read by the script: in
the export, session per qualified play is 10.1 min for B vs 10.9 for A (no CI). Check the bounce of B's players before B
becomes the only thumbnail (honesty rule in `release.thumbs.formula`). The variants were never judged by multiuse-critic
(the synthetic test has no images).

## 2 Weekly memo (week ending 2026-09-27)
`data/memos/2026-09-27/memo.html` (+ memo.md, facts.json, charts/dau|retention|money.svg). Headline: payer conversion is
0.71% (CI 0.4%-1.2%), a MISS on the 1.5% continue gate. D1 is 12.2%: the spend gate PASSes and the scale gate is UNCLEAR.
There are 3 actions. Bounce has NO DATA, so the spend gate cannot be read.

Canon proposals (not run; the trial may not write canon): `bible-proposals.sh`.
