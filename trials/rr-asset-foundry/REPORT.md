# rr-asset-foundry: fix round 1 (2026-09-28)

The skill is fixed, the full selftest passes 18/18, quick_validate says "Skill is valid!", and the package is at `/home/user/claude/dist/rr-asset-foundry.skill`. I did not write `/home/user/claude/trials/rr-asset-foundry/REPORT.md`: the harness blocks subagents from writing report files. The report is below instead.

Inputs were FRICTION F1-F12, the critic's pass 1 on WagonOpenCoal and the skill review. Review scores: [7, 6.5]. The re-trial is not scored; `retrial/crit/pass-1/critic.md` is built and ready for a fresh multiuse-critic.

## Changes to the skill
- **A5 check measures the right thing** (F1, review H1):
  - `fkit.feature_px` now measures each piece (mesh island) separately and takes its thinnest on-screen width. The old check took the longest side of a whole part, so it could never warn.
  - Keys match the exact `<Part>` name token (the `<Group>` token for merged parts).
  - It reports the smallest piece per key and how many pieces are under 5 px. It warns on the 400 px game view; the POV 3P sizes go in facts.md only.
  - The selftest plants a thin feature that must warn, and checks that the key `Bloc` does not match `Block`.
- **Player-view premises** (F2/F3/F4, review H2 and the crit med finding):
  - A family can list several viewing premises, each with 1-3 camera stands.
  - `--pov` on plan/make/crit switches premise and re-renders only; nothing is rebuilt.
  - The wagon default is `siding`: seen from the coach at the world.prefabs.15 siding spacing, read from canon via `@world.prefabs.15#1`. To support that, `Bible.number` now reads the note's numbers when the value has none.
  - `lobby` is also available. The old next-vehicle view survives as `coupled`, labelled "CONTRADICTS canon".
  - Every premise cites canon keys and says ASSUMED.
  - Every premise renders 2 player-view stands. Carriage and track have their own; other families get a second stand 35° round from the first.
- **Batch robustness** (three review meds):
  - A variant's identity is now separate from its build inputs. The build hash also covers the family file, the helpers it imports, fkit, forge and the plan's canon, stage and view.
  - Out-of-date and errored variants rebuild without `--force`; a different variant in the same folder is still refused.
  - Each variant catches its own crash or refusal, and a batch exits 1 if any variant failed or errored.
  - Bad `--vary` input now exits 2 instead of hanging or silently making 0 variants: step ≤ 0, lo > hi, non-numbers, and grids over 400 without `--n`.
  - New `--same-seed` option. A batch that varies presets is named `<Family>Mix`.
- **Copies work** (review med): renders go through a temporary plan pointing at the folder given, the current sibling-skill paths and the current family file, and the palette image is re-pointed. `crit`, `sheet` and `make` all use this, and the selftest checks renders stay in the copy.
- **crit brief** (F6/F12):
  - Purpose is now a TODO line, and Player view has one line per variant with its premise and stands.
  - When the owner can't be asked, the skill says to write ASSUMPTION lines. crit prints how many TODOs remain.
  - crit refuses a variant whose checks failed (`--allow-fail` overrides) and puts extra stands on the contact sheet or closeups.
- **Unused colour groups** (F7): `studio_setup.lua` and the facts.md colours line list only groups the variant uses.
- **Sheet for single variants** (F5): `fdy sheet VARIANT_DIR... --out`.
- **Cheap lows:**
  - Back faces are checked from every player and construction camera, with parallel rays for side, end and top (F9).
  - The side and end views include the scale avatar (F8).
  - `list --match` ranks results (F10); `show` lists premises and the open questions from canon keys (F11).
  - The hut checks both door numbers; track warns when a piece length doesn't divide `segment_len`.
  - Bad input exits 2 with a message instead of a traceback, and the README atlas line respects `--no-atlas`.
  - The broken "make --params vNNN/plan.json" route is removed.
- **Docs:**
  - SKILL.md (96 lines) adds: start overnight batches from the main session, the resume rules, the new sheet command and premises, and that in a mission plan.json plus the family file stand in for build.py.
  - checks.md explains the new A5 measure and variant identity.
  - families.md documents the premise/stand API, `k.heightfield`, `underframe(outside=True)` and a "Lessons from critic passes" section.
  - design-notes.md holds the proposed rr-mission-control patch and the drafted rr-bible question.

## Changes to the wagon, from the critic
- **C1-1 straps:** Strap is now 1.3 × 0.3, EndStrap 1.5 × 0.3, DoorStrap 1.1 tall. The critic's ×2 estimate only reached 3.8 px because the 3/4 view foreshortens the side.
- **C1-2 coal:** the heap is two symmetric peaks with the crest 2.75 above the side top (new `heap` and `peaks` params), with fewer, bigger lumps.
- **C1-3 running gear:** axleboxes, springs and W-irons (or bogie frames) now hang on the solebar line, wheel radius is 2.0, and Wheel and Axlebox are measured keys.
- **C1-4 patch:** the red-oxide side patch is replaced by whole light-timber planks running strap to strap.
- **C1-5:** light cap rails along the top edges.
- **C1-6 light ticks:** these were see-through gaps between deck planks; the planks now lap, so the gaps are gone.
- Also: flat-wagon stanchions are 0.8 × 0.7, bogie axleboxes and the tape are chunkier.

**Re-trial against the critic's done-when checks (WagonOpenCoal):**
- At 400 px: Strap 5.6 px, EndStrap 5.7 px, DoorStrap 5.4 px (8.5 px in POV 3P).
- Height 12.66 studs (critic asked for 11.5 or more).
- Lump 5.4 px, Axlebox 8.4 px, Cap 5.8 px.
- No patches left.
- 0 back faces in 6 views, 0 coplanar overlaps, 0 floating parts.
- verify passes on all 3 variants.

By eye, the side view shows two peaks, the first-person view shows coal above the rim, and the end view has no light ticks.

## Rejected or changed, with reasons
- **multiuse-critic's `blender_kit.py` is not in the build hash:** that sibling skill is changing often, so every edit would rebuild every batch. This is documented; `--force` covers it.
- **C1-7 seam width:** the seams are 0.08-stud depth steps, not grooves, so there is no width to measure. Each plank row is now a measured key instead (6.3 px).
- **C1-6 method:** fixed at the source (the deck gaps), not by extending the end planks.
- **The review's building door finding is partly wrong:** the signal box and shelter never used `door_w`/`door_h`. The signal box has a fixed lineside upper door and the shelter has an open front. The plan now warns that those params don't apply to them.
- **Critic size estimates** (×2, ×1.7) were replaced by measured sizes.
- **The wagon question is not recorded in rr-bible:** both the review and this session's folder limit forbid it. It was drafted in design-notes.md (its dry run said OQ-042, since taken by another lane); the 2026-09-28 bible reconcile recorded it as OQ-045 and wagon.py cites it.
- **rr-mission-control patch:** written as a proposal only, because the skill may not edit a sibling.
- **Left for the owner:** OQ-030 (whether yard wagons use the coach width, 17.4 on gauge 8), the Studio import test, and OQ-025 (livery).

## Now visible, not yet fixed
The corrected A5 check now warns on pieces the old one missed. These are for the next tuning pass:
- **Carriage:** LadderRung 1.6 px, Railing 1.5 px, Handrail 1.4 px, BufferHead 3.8 px.
- **tank_long:** LadderRung 1.6 px.
- **open_bogie (50 studs):** most keys are 4.1-4.7 px, because the 400 px view is framed to the whole asset.

## Validation
- **Selftest:** the full run with bpy 5.0 passed 18/18, including the new tests for crash resume, helper-file staleness, crit on a copy, premise switch and the planted thin feature. `--quick` also passes 8/8 after the last edit.
- **Scripts and validator:** all 4 scripts answer `--help`. quick_validate says "Skill is valid!"; the description is 976 characters with no angle brackets. No `__pycache__` anywhere.
- **Package:** `/home/user/claude/dist/rr-asset-foundry.skill` (15 files, no .pyc).

Files are in `/home/user/claude/trials/rr-asset-foundry/retrial`:
- `variants/`
- `sheet-wagon-variants.png`
- `crit/brief.md`
- `crit/pass-1/critic.md`
- `crit/pass-1/contact.png`

## Independent certification after fixes
Fresh critic on the fixed re-trial: overall 7 ({'A1': 7, 'A2': 7, 'A3': 8, 'A4': 8, 'A5': 7, 'A6': 8, 'A7': 7}); 3 blocks-8 issues. Verdict saved at /home/user/claude/trials/rr-asset-foundry/retrial/crit/pass-1/verdict.md.
