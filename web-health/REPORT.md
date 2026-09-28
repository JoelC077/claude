# JARVIS web health report (2026-09-28)

This is the first full run of rr-skill-smith 1.0.0 over the whole web: the 11 rr-* skills, multiuse-critic and the two installed risky-rails skills. It was run by a subagent that did not build the smith.

Which SKILL.md steps it followed:
- Steps 1-3: harvest, health, drift.
- Step 4.1: one patch brief per skill.
- Step 6 by inspection only: I checked the claimed fixes against the code but wrote no proving checks, because that would edit live evals.
- Step 7: the friction logs are present for the 8 trials and 2 missions.

Nothing was staged, proposed, applied or packaged, and no skill folder was changed.

State and machine output are in `/home/user/claude/smith/`:
- `health.html` for the owner; `health.md` and `health.json` are the compact forms.
- `frictions.json` and `clusters.json`: the harvest.
- `proposals/<skill>/patch-brief-2026-09-28.md`: 10 patch briefs.

## What ran

| step | command | wall time | result |
|---|---|---|---|
| harvest | `harvest.py scan` | 0.5 s | 10 friction logs, 185 items, 34 score records, 7 cost records |
| health | `health.py` (runs quick evals) | 51 s | 6 critical, 5 warning, 3 good (snapshot 2) |
| drift | `drift.py` (whole web) | 1.3 s | 0 ERROR, 21 WARN |
| evals | `evals.py run all` (full, with slow selftests) | 9 min 1 s | checks 83/83 PASS, triggers 95/100, 0 regressions |
| triggers | `evals.py triggers` | 0.1 s | 5 lexical misses, all also failing at baseline |
| briefs | `harvest.py patch S`, 10 skills | <1 s each | about 800-1,300 tokens each |

The scripts cost no model tokens. This run's model tokens were not measured.

Evals I did not run:
- **Model-graded evals:** none exist. Every `evals.json` has an empty `evals` list, so `evals.py agent` has nothing to run.
- **Live trigger test** (`evals.py live`): not run, because it costs tokens and neither SKILL.md nor the owner asked for it. It is the only way to confirm the 5 lexical misses.

## Status: the smith's view and a checked reading

The smith's status depends on friction statuses. For 4 skills those are stale: items were fixed later, in prose reports or in skill edits the harvester cannot see (see "Status corrections"). The "checked" column is based on the current code.

| skill | smith | checked | what actually blocks 8/10 | next move |
|---|---|---|---|---|
| rr-vfx-lighting | critical | **critical** | Certified critic 4/10 (9 blocks-8 issues). The maker handed over looks that failed its own preview flags. | patches 4 and 13, then the bar loop |
| rr-game-feel | critical | **critical** | Certified critic 4/10 (9 blocks-8). `validate --strict` passes a broken tier hierarchy. | patches 5 and 12, then the bar loop |
| rr-soundsmith | critical | **critical** | Certified critic 5/10 (10 blocks-8): true-peak headroom, ducking that pumps, no variations. | patches 6 and 20, then the bar loop |
| rr-exploit-guard | critical | **critical** | Reviews found 8 issues the scanner missed (2 High). R10 (no DataStore session lock) is still a blocker in the fixed tree. | patches 1, 2, 9 and 10 |
| rr-ui-foundry | critical (3 open High) | **warning** | The 3 "open High" items were fixed in the fix pass. The real gaps: critic score 7, contrast measured without fades (B2-1), and a colour-role gap in the chrome. | patches 7 and 14 |
| rr-mission-control | critical (1 High, 27 open) | **warning** | Most items were fixed by the 23:15 edit, after the logs written at 22:18 and 22:34. Its "critic 7" scores the mission's deliverables, not the skill. | close the fixed items with checks; polish only |
| rr-asset-foundry | warning | warning | Certified critic 7. The per-piece A5 check misses seams (A5-1), and the running-gear offset is wrong (A2-1). | patch 11 |
| multiuse-critic | warning | **warning (real)** | The 9 open mission items are real: its files date from 09-26, before the missions ran. | patches 17 and 18 |
| rr-release-train | warning | warning (pycache only) | The claimed fixes hold: G2 has `--via`, and `config` and `notes` print one line each. It writes `__pycache__`. | patch 8 |
| rr-data-and-money | warning | warning | Writes `__pycache__` and cites one superseded canon key. | patch 8; drift D2 |
| rr-bible | good | good (never trialled) | none; no dist package | package once the owner agrees |
| rr-skill-smith | good | **warning** | The harvest misclassifies items, hygiene cannot fail, and about half the drift WARNs are false. | patches 3, 15, 16 and 19 |
| risky-rails-thumbnail-ideas | warning | warning | Restates 22 canon colours; SKILL.md is 24.7k chars (about 6.2k tokens). | fix at its source (installed copy) |
| risky-rails-mechanic-reviewer | good | good | none | none |

**Frictions** (smith counts, 185 items):
- 75 open (4 H, 40 M, 31 L).
- 106 claimed (25 H).
- 4 partial.
- 0 closed with evidence.

No claimed fix has a proving check yet. Only rr-bible's evals carry `covers` ids, and those 3 items stay open anyway.

**Score provenance:**
- The critic scores 4, 4, 5, 7 and 7 come from fresh independent critics (CERTIFY.md).
- The "rev" scores (6 to 6.5) are the lanes' own skill reviews, so they are self-assessed.

**Packages** (`ship.py status`):
- rr-bible and multiuse-critic have no `dist/*.skill`.
- 5 packages are stale (asset-foundry, data-and-money, game-feel, soundsmith, ui-foundry): the skills were edited after packaging, mostly by the bible reconcile.
- All 12 skills are unversioned.

### Web-wide themes (smith clusters in 2 or more skills)

| theme | skills | where it gets fixed once |
|---|---|---|
| silent-pass | 7 | Most claims hold. What is left: the vfx and game-feel flags warn but don't gate (patches 4 and 5). |
| critic-route | 6 | Already fixed once in rr-mission-control (SKILL.md:46 probe order; `mission_state.py` caps self scores as UNCERTIFIED). Close with a check. |
| canon-writes | 6 | Fixed in rr-bible (`--dry-run`, covered by the `question-dry-run` eval). Close with a check. |
| generic-brief | 6 | Mostly claimed fixed. |
| oq-ids | 5 | The bible reconcile is done; drift finds no unknown or decided ids. |
| critic-evidence | 5 | multiuse-critic maker spec (patch 18); game-feel true-size frames (patch 12). |

## Evals

- **Checks:** all 12 skills in the web pass, 83/83. The built-ins also pass: validate (quick_validate), lean, hygiene and drift.
- **Triggers:** 95/100 on the lexical proxy. None of the misses is a regression.

| skill | prompt | proxy routed to | verdict |
|---|---|---|---|
| rr-data-and-money | "what should the locomotive gamepass cost in robux?" | multiuse-critic | Proxy weakness: "gamepass" and "cost" are not in the description (1,014/1,024 chars). |
| rr-exploit-guard | "can exploiters give themselves coins through my shop remote?" | computer-use | Proxy weakness. |
| rr-release-train (negative) | "make the release trailer thumbnail" | rr-release-train | Real boundary gap: the description never says "not thumbnails". |
| rr-ui-foundry (negative) | "make a scrolling inventory list with a search box" | rr-ui-foundry | The proxy can't read "Not for scrolling lists"; the description is right. |
| rr-vfx-lighting (negative) | "boiler explosion sound effect" | rr-vfx-lighting | The proxy can't read negation; the description (at the 1,024 cap) lacks "not for sound". |

**Description headroom:** five descriptions are within 11 characters of the 1,024 cap (vfx, ui, soundsmith, release, data). Any trigger fix there has to cut words.

## Drift: 0 ERROR, 21 WARN, checked by hand

**Real (10):**
- **D1** risky-rails-thumbnail-ideas SKILL.md:81 restates 22 canon colours. It is an installed copy, so fix it at its source.
- **D2** rr-data-and-money `scripts/econ.py:337` and `references/economy-model.md:30` cite `economy.currency.float`, which is superseded ("replaced by ProfileStore in alpha week 2").
- **D3** rr-mission-control `references/rr-profile.md:6-7` restate 9.5 studs (`tech.camera.eye_3p`) and 5 studs (`tech.units.avatar_h`).
- **D4** rr-mission-control `references/examples/mission-p1.md:39` restates 8 hex colours, and `references/roblox-export.md:11` restates 1.
- **D5** rr-vfx-lighting `references/presets.md:91` restates 120 studs (`tech.lighting.light_range_max`).
- **D6** rr-vfx-lighting `scripts/preview.py:519` keeps a fallback OQ list (`["OQ-026".."OQ-029"]`).
- **D7** rr-game-feel `scripts/feel.py:1086-1087` writes a hard-coded "Open decisions in use" OQ list into generated text (the smith reports line 1080).

**False positives (11):**
- 6 × rr-game-feel "OQ-TBD placeholder not reconciled": the flagged lines are the rule text (`cite OQ-TBD-<slug>`) and a regex (`re.match(r"^OQ-TBD", oid)`), not placeholders.
- 2 × rr-ui-foundry specs "hard-coded OQ list": a spec's `"oq"` field is that screen's citation data. The smith reports line 2; the list is at line 9.
- rr-data-and-money `economy.json:65`: OQ-052 ("Locomotive 3-5 and Line 2 prices") is the right citation for `loco_4`'s price.
- rr-data-and-money `economy.json:45`: the reported line holds no OQ id.
- rr-exploit-guard `references/fixes.md:119`: OQ-010 (Robux in the supply terminal) is relevant next to ProcessReceipt.

## Proposed patches, ranked (none applied)

Ranking weighs:
- harm to players or to the owner;
- independent evidence;
- whether a skill's own check passed something a critic or reviewer then failed;
- cost.

Every patch writes its check first (SKILL.md hard rule 4).

1. **rr-exploit-guard: new rule for "check, then yield, then write" (race).**
   - Change: in remote and ProcessReceipt handlers, flag a yielding call between a balance read or check and the write that spends it. Yielding calls: DataStore `*Async`, HttpService, `InvokeClient`, `task.wait`, `WaitForChild`. Severity high. Fix F-ATOMIC: deduct before the yield, or use an `UpdateAsync` transform.
   - Why: N concurrent BuyItem calls all pass the check, so one balance pays for N items and Coins go negative. Bounding qty does not fix it.
   - Evidence: `trials/rr-exploit-guard/retrial/out-vuln/review/verdict.md`, NEW `ShopService.server.lua:41` (high, missed).
   - Check: `fr-yield-race` (a vulnerable fixture and a fixed fixture).
   - Risk: false positives when the handler re-checks after the yield. The rule should recognise a re-check or an atomic transform.

2. **rr-exploit-guard: widen `data-raw-set`.**
   - Change: also match `pcall(store.SetAsync, store, …)`, `pcall(function() … end)` wrappers, and GetAsync/UpdateAsync blind overwrites. Severity high when the key is built from a UserId and there is no session lock and no BindToClose.
   - Why: canon `tech.data.store` is ProfileStore. This is a rollback and duplication vector, and it is the last blocker in the fixed tree.
   - Evidence: out-vuln NEW `DataService.lua:28` (high); out-fixed R10 (blocker); `t:rr-exploit-guard#b28` (the pcall form is a blind spot). The rule exists at `guard_data.py:152` as medium.
   - Check: `fr-data-pcall-form`.
   - Risk: noise on global or config stores. Scope the rule to player-keyed stores.

3. **rr-skill-smith: the harvest sees fixes.**
   - Change:
     - A report's changes section that matches an item's title words marks it claimed.
     - A file named by an item that changed after the log date marks it claimed. This gives missions a fix channel.
     - A passing check whose `covers` lists an id marks it verified.
     - Heuristics may only move an item to claimed; only checks close items.
   - Why: 3 skills are ranked critical or "Act" on stale items. The ui-foundry, mission-control and exploit-guard briefs ask for fixes that already shipped, which wastes tokens every round.
   - Evidence: "Status corrections" below. `harvest.py:285-296` only knows ids and blanket phrases, and missions get `rep=None` (`harvest.py:309`).
   - Check: selftest fixtures: a prose report that fixes item 1 without citing it, and a mission log older than the skill file.
   - Risk: a false "claimed" could hide a real item. That is why claimed stays unverified and still shows in health.

4. **rr-vfx-lighting: the readability flags gate the critic hand-off.**
   - Change: `crit` refuses to build a brief (exit 2, naming the look or effect) in these cases, unless the pack carries `accept: <reason>`:
     - a look shows train vs world under 2:1 from a player view;
     - a look has crush over 5%;
     - an effect is "mostly hidden by the train" from every player view.
   - Why: certified 4/10. The maker handed over looks that failed its own flags, and a critic pass (about 90-140k tokens) was spent to hear it. SKILL.md:49 calls these flags "heuristics to weigh".
   - Evidence:
     - C1-1: sparks 89/92 hidden, 0.00% of the screen.
     - C1-2: night contrast 1.57:1 and 1.05:1.
     - C1-3: 27% crush in the cab view.
     - `trials/rr-vfx-lighting/REPORT.md:107-111`: targets missed in 2 of 3 views.
     - `preview.py:163-165, 341`.
   - Check: `fr-gate-before-crit` (a dark fixture look).
   - Risk: legitimately dark looks. `accept:` keeps the owner in control, and the flags stay heuristics.

5. **rr-game-feel: judge the hierarchy by pairs, not medians.**
   - Change: `validate --strict` fails when an event outshouts any event two or more tiers more important, or when the signature moment (`identity.pillars.fork_bet`, i.e. lever_commit) is not the loudest in its tier.
   - Why: certified 4/10. Today only the tier median can warn; pairwise inversions are a NOTE (`feel.py:568-580`), and the `validate-strict` eval passes.
   - Evidence:
     - G1-1 (high): fare_banked at 0.135 (tier 4) outshouts tier-2 events.
     - G1-2 (high): coal_low sits below fired_stamp.
     - G1-3 (high): lever_commit at 0.16 is below fired_stamp at 0.25.
   - Check: `fr-pair-hierarchy` on the shipped preset (it fails now).
   - Risk: presets fail strict until retuned, which is intended. `loud_ok` and `quiet_ok` remain as escapes.

6. **rr-soundsmith: mix-safety checks.**
   - Change:
     - In-game true peak = file TP + (tier target − file level) must be −1 dBTP or lower.
     - A duck whose attack + hold + release outlasts its trigger's repeat interval warns (pumping).
     - An event that repeats with no variations or cooldown warns.
     - Alarm tiers need a minimum phone-band share.
   - Why: certified 5/10, and the facts already hold all the numbers these checks need.
   - Evidence:
     - S4-1 (high): lever_clunk reaches −0.38 dBTP in game.
     - S4-2 (high): a 1 Hz duck pump on countdown_tick.
     - S4-3: no variations or cooldowns on repeated sounds.
     - S3-1 (high): alarm_coal loses 2.51 dB on phones.
   - Check: `fr-tp-headroom`.
   - Risk: the thresholds are heuristics; label them as such unless rr-bible records them.

7. **rr-ui-foundry: contrast on composited colours.**
   - Change: apply node and ancestor transparency (busy and disabled fades) before `contrast()`. Fail below 4.5 (3.0 for large text).
   - Why: wrong measure. Facts reported 6.7:1 where the render showed pale cream on tan.
   - Evidence: B2-1 (high, blocks-8); `uimodel.py:1183-1185` ignores opacity.
   - Check: `fr-faded-contrast` (the join button in the joining state).
   - Risk: low. Mirror the change in ingest.

8. **rr-data-and-money and rr-release-train: stop writing `__pycache__`.**
   - Change: add `sys.dont_write_bytecode = True` before local imports in these entry scripts:
     - rr-data-and-money: abtest, dash, econ, luatest, selftest, track.
     - rr-release-train: gates, release, selftest.
   - Why: owner rule.
   - Evidence: verified. `econ.py --help` and `release.py --help`, run without the env var in scratch copies, both wrote `scripts/__pycache__`.
   - Check: via patch 16.
   - Risk: none.

9. **rr-exploit-guard: the fork is never reset per junction.**
   - Change: flag lever handlers that do not reset route or side state when a new junction starts, or never record who pulled. Canon: `gameplay.fork.default` (nobody pulls means safe) and `gameplay.fork.cards`.
   - Evidence: found in 2 of 3 reviews: out-fixed NEW `LeverService.server.lua:49`; out-release-trial NEW `Lever.server.lua:4`. The canon keys are already listed at `guard_data.py:212`, but no rule fires.
   - Check: `fr-fork-reset`.
   - Risk: game-logic rules are heuristic. Report as medium with an `ask:` line.

10. **rr-exploit-guard: receipts and placeholders.**
    - Change:
      - A ProcessReceipt that returns PurchaseGranted for an unknown ProductId should return NotProcessedYet.
      - Flag placeholder ids (a low `OWNER_USER_ID`, placeholder product ids); release-train G9 could reuse this.
      - Flag an append-forever DataStore log key.
    - Evidence: out-vuln NEW `ShopService:53` and `Config.lua:6`; out-fixed NEW `DataService.lua:52` (all medium).
    - Check: `fr-receipt-unknown`.
    - Risk: low.

11. **rr-asset-foundry: A5 measures seams, and the running gear sits on the gauge.**
    - Change:
      - A5 facts also measure negative space: seam, recess and gap widths. Seams under 1 px at 400 px are flagged (`style.dont.hairlines`).
      - The wagon family puts the axleboxes at gauge/2 + wheel width + 0.5, not stock_width/2.
    - Why: the claimed F1 fix measures pieces only. The smallest piece reads 5.3 px while the seams are sub-pixel.
    - Evidence: A5-1 (high), A2-1 (high); `retrial/crit/pass-1/facts.md:11`.
    - Check: `fr-seam-px`, `fr-axlebox-on-gauge`.
    - Risk: low; needs a re-render.

12. **rr-game-feel: timing coherence and stacking.**
    - Change:
      - All channels of an impact peak within 2 frames, and hit-stop holds the peak pose.
      - The runtime clamps the summed camera offset to the loudest active tier's limit, with a per-event camera cooldown.
      - The kit adds an overlap plot.
      - Every non-hero event gets a true-size phone peak frame.
    - Evidence: G2-1 (high), G6-1 (high), G6-2, G4-1 (high). G4-1 shows the claimed fix `t:rr-game-feel#4` is only partial.
    - Check: `fr-peak-align`, `fr-stack-clamp` (luatest).
    - Risk: runtime change, so the Luau parity tests must be updated.

13. **rr-vfx-lighting: no emitters or lights inside the car body.**
    - Change: validate warns on an attachment within ±`tech.units.stock_width`/2 unless its anchor role is interior (firebox, cab). Point lights outside the body get shadows on.
    - Evidence: C1-1 (sparks inside the 17.4-wide body); C6-1 (a glow dot through the body in every POV).
    - Check: `fr-anchor-outboard`.
    - Risk: needs role tags on the existing anchors.

14. **rr-ui-foundry: no accent hue in chrome; steppers disable at their ends.**
    - Change: chrome text or fills within ΔE of the accent or of a yellow token warn under `ui.rules.one_accent` (exception: `role: brand`). Stepper templates render next and prev disabled at their bounds.
    - Evidence: B1-1 (high), B4-1, B6-1.
    - Check: `fr-chrome-accent`.
    - Risk: low.

15. **rr-skill-smith: harvest certified verdicts and security reviews.**
    - Change: blocks-8 lines from `pass-N/verdict.md` and `NEW:` lines from review verdicts become harvest items (source critic or review, severity from impact). Each is tagged output-only or skill; it is a skill item when the skill's own facts or validate passed what the critic failed.
    - Why: the three worst skills' briefs contain none of their 28 blocks-8 issues or the 8 missed security findings. Patches 1, 2 and 4-14 were found by hand.
    - Check: a selftest fixture verdict.
    - Risk: flooding the briefs with tuning issues; the output/skill tag keeps briefs to skill defects.

16. **rr-skill-smith: a hygiene check that can fail.**
    - Change: the built-in hygiene check runs each entry script's `--help` in a temp copy without `PYTHONDONTWRITEBYTECODE` and fails on `__pycache__`. It also reports `__pycache__` in installed copies.
    - Evidence: `evals.py:117` sets the env var for every check. The installed critic has `~/.claude/skills/synced/*/multiuse-critic/scripts/__pycache__/blender_kit.cpython-311.pyc` (03:05, from an older asset-foundry import). The owner's config was not touched.
    - Check: a selftest fixture.
    - Risk: none.

17. **multiuse-critic: an honest cost ledger.**
    - Change: add `critic_kit.py log --est`, and a `--mode self|handoff` that never subtracts carried tokens. `show` prints "est." on estimates.
    - Evidence: `m:260927-depot-buildings#13`, `m:260927-ticket-hud#9` (open; `critic_kit.py:207-210`).
    - Check: `fr-log-est`.
    - Risk: ledger schema change; keep old rows readable. Missions resolve the installed copy first, so this needs an owner reinstall.

18. **multiuse-critic: a maker evidence spec and a float check.**
    - Change:
      - `critic_kit.py spec --profile P` prints the contact-sheet, close-up and facts requirements, so makers don't have to read the pipeline docs.
      - Add `blender_kit.floating_parts()`.
      - Warn on coplanar front faces in overlapping clusters, which render black.
    - Evidence: `m:260927-depot-buildings#14`, #8, #17, #15 (open).
    - Check: `fr-maker-spec`, `fr-float`.
    - Risk: SKILL.md growth; keep it in scripts and references.

19. **rr-skill-smith: drift precision.**
    - Change:
      - correct line numbers for JSON and .py files;
      - skip rule text and regexes that quote `OQ-TBD-<slug>`;
      - don't flag a spec's `"oq"` citations;
      - loosen the topic matcher.
    - Evidence: the 11 false positives above.
    - Check: fixtures for each false-positive shape.
    - Risk: under-reporting; keep the dropped cases as INFO.

20. **rr-soundsmith: measured placeholders enter the register.**
    - Change: each measured `PLACEHOLDER_*.wav` is registered with `state=placeholder, licence=self-made`, the generator and the date.
    - Evidence: S6-1 (blocks-8). The register read "0 placeholder" while 5 placeholder files existed.
    - Check: `fr-register-placeholder`.
    - Risk: low.

### Also proposed, lower priority
- **Canon citations:** fix D2-D7 by citing canon keys instead of restating values.
- **multiuse-critic `render_design.py`:** treat a fixed-size root as an artboard (`m:ticket-hud#7`), and don't flag decoration clipped by the artboard's `overflow:hidden` (#8).
- **rr-vfx-lighting:** facts should state the preview's limits: no skybox, and lights drawn as dots (C3-3, C6-1).
- **rr-release-train:** add "not thumbnails or trailers" to the description (a real boundary gap). Check the other trigger fixes live (`evals.py live`) before cutting words.
- **rr-mission-control, still open:**
  - `mission-p1.md` almost holds the depot answer (#7, a token and independence risk);
  - no layout-parity tool (#11);
  - the house-style block is written for vehicles (#12);
  - a double `[8/10]` progress line (#14);
  - `step` adds the stage prefix automatically (#10).
- **Packaging** (after the owner agrees): `ship.py package` for rr-bible and multiuse-critic, `ship.py package all` for the 5 stale packages, and `ship.py init-changelog` so versions exist.

## Status corrections: open in the smith, fixed in the code

These need checks before they can be closed; nothing was closed. Once a check passes: `harvest.py close ID --by "eval <id>"`.

- **rr-ui-foundry.** Its REPORT.md "Changes" section cites no ids.
  - #1: luatest now builds runtime tests from each spec; line 741 is only the standalone self-build.
  - #2: every touch device now fails validate.
  - #3: `ui render A B` and `ui crit --spec A,B`.
  - #5: the `RR_UI_KIT` rule at SKILL.md:55, and the manifest records the kit diff.
  - #6: `ui render --kit`.
  - #7: a missing icon is now an error.
  - #10: the brief uses an absolute path.
  - #11: hygiene.
  - #13: facts start at H2.
- **rr-exploit-guard.**
  - b24: `--fail-on` counts suppressions the owner has not accepted (`guard.py:211-216`; selftest "fail-on with suppressions").
  - b23: where a suppression comment goes is documented (REPORT.md:127).
  - b27: batch explain (REPORT.md:121).
- **rr-release-train.**
  - #15 and #16: `config` and `notes` print one line (REPORT.md:72).
  - #18: a remake arrives as Changed (REPORT.md:70).
- **rr-game-feel** (REPORT.md:71-75).
  - #13: the FOV column shows the sign.
  - #14: sfx names are checked against rr-soundsmith.
  - #15: no `__pycache__`.
  - #17: the brief no longer repeats canon.
- **rr-vfx-lighting.** #2 and #15: the new dusk look and the authoring checklist (REPORT.md:70, 80).
- **rr-mission-control.** The 23:15 edit came after the logs (22:18 and 22:34).
  - Roots, depot #1 and HUD #1/#13: `RR_MISSIONS_ROOT` (SKILL.md:10, `mission_state.py:27`).
  - Critic route, depot #9/#18 and HUD #2/#10: SKILL.md:46 probe order; `mission_state.py` marks self scores UNCERTIFIED and notes handoff.
  - Owner away, depot #3 and HUD #4: SKILL.md:54.
  - Cost, depot #22: `--est`.
  - Toolchain, HUD #12: the luaparse fallback.
  - Atlas, depot #6/#16: the `_atlas.fbx` rule.
  - Subagent delivery, depot #20: SKILL.md:94.
- **Claimed High fixes that hold on inspection:**
  - release-train G2 `--via` (`release.py:469`, selftest:258).
  - Selftest coverage exists for vfx #4/#5, data #1/#2/#6/#14, guard b1, feel #2/#3, sound F1 and asset F2.
- **Partial:**
  - asset F1 measures per piece only (patch 11).
  - feel #4: non-hero events still have no true-size frames (patch 12).

## Frictions using rr-skill-smith

Severity: H = wrong output, M = extra work or tokens, L = polish.

1. [H] **Harvest claim detection is id-only, and missions have no fix channel.** rr-ui-foundry shows 3 open High and rr-mission-control shows 27 open, all fixed, and the briefs point at code that already shipped. Evidence: "Status corrections"; `harvest.py:285-296, 309`.
2. [H] **Hygiene cannot fail on `__pycache__`.** Checks run with `PYTHONDONTWRITEBYTECODE=1` (`evals.py:117`), so 2 skills that write `__pycache__` pass.
3. [H] **Patch briefs omit the strongest evidence.** Certified blocks-8 issues and review `NEW:` findings are not harvested, so the briefs for the skills scored 4, 4 and 5 contain only friction-log clusters.
4. [M] **Drift precision is about 50%** (10 real, 11 false WARN):
   - wrong line numbers in JSON and .py files (a spec list at line 9 reported as line 2; `feel.py` 1086 reported as 1080; `economy.json:45`);
   - OQ-TBD rule text flagged as a placeholder;
   - correct topic citations flagged.
5. [M] **Wrong themes give wrong fix hints.** `t:rr-exploit-guard#b28` (scanner blind spot) is clustered as critic-route. `m:depot#13` (critic_kit token semantics) is critic-route instead of cost-accounting. `t:rr-vfx-lighting#2` (missing-preset rule) is silent-pass.
6. [M] **Passing `covers` checks don't change status.** rr-bible's passing evals cover `t:rr-ui-foundry#9`, `t:rr-vfx-lighting#3` and `t:rr-game-feel#5`, which still read open, partial and claimed.
7. [M] **Timings are understated.** `health.py` took 51 s, not "about 10 s". `evals.py run all` (full) took 9 min, SKILL.md gives no estimate, and the full run repeats the quick evals that health already ran.
8. [M] **Mission critic scores are counted as rr-mission-control's score** ("critic 7 < bar 8"). They score the depot and HUD deliverables, not the skill, and they push mission-control to critical.
9. [M] **No fallback in step 4.** It says "one fresh subagent per skill", but this runner had no Agent tool. This is the same critic-route gap the smith reports in other skills.
10. [M] **There are two multiuse-critic copies.** `<critic>` resolves the installed copy under `~/.claude/skills` first, while the smith evaluates `/home/user/claude/multiuse-critic`, and divergence is not reported. They differ today only in `evals/` and the installed `__pycache__`. Critic patches need an owner reinstall.
11. [M] **The trigger proxy can't read "Not for …".** 3 of the 5 misses are negatives the descriptions already exclude, and they show as noise on every run.
12. [L] **The lean budget ignores description length.** 5 descriptions are within 11 characters of the 1,024 cap, and nothing warns before a trigger fix becomes impossible.
13. [L] **Briefs say "0.0.0" for unversioned skills**, while health and status say "unversioned".
14. [L] **SKILL.md says "`--full` … once, at propose"**, but `evals.py` only has `--quick`; `--full` belongs to `ship.py propose`.
15. [L] **`ship.py status` cuts the "last eval" column mid-word** at 60 characters.
16. [L] **There is no `harvest.py patch all`**, so 10 briefs took 10 calls.
17. [L] **Nothing flags a skill that was never trialled.** rr-bible and rr-skill-smith have no trial or friction log, so "0 open" reads as healthy.