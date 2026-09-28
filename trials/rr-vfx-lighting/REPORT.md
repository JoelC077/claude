# rr-vfx-lighting fix report (2026-09-28)

**Note on REPORT.md:** I could not write `/home/user/claude/trials/rr-vfx-lighting/REPORT.md`. The harness blocks report files from subagents, so the report is this text; save it there if the file is needed.

Inputs: FRICTION.md (18 items) and review scores [5, 6]. Nothing was published, nothing was written to the bible, and there was no git.

## Changes

**Pipeline: one pack, one board, one critic**
- **Names are honoured.** `preview all NAMES` splits the names into looks and presets; an unknown name exits with code 2 (R2-H1, F4).
- **Player views (POVs) come from the names.**
  - Each named look is shown with the named loops plus the look's `fx_on`, from roof3p and door1p, plus the camera nearest each anchor (`stand.near_camera`).
  - Each burst gets its own POV and fires after the loops warm up.
  - Each roof POV also runs at phone rates over an 844x390 phone plate.
  - The default POV sets moved into `lighting.json preview.pov_sets` (R2-H2, R2-M phone tier, F5, F9, F10).
- **One board.** `board/` holds:
  - `contact.png`: the phone POV at 1:1, then the player views.
  - `closeups.png`: the effect strips at 1:1.
  - a merged `facts.md` and a `manifest.json`.
- **One critic.** `crit --from <preview>` builds one brief from the manifest, covering only the pack's uses and the OQs it depends on.
  - `--profile` passes through (default F; B is for UI) (R2-M two critics, F6–F8).
- **Fast rebuild.** `preview vfx NAMES` reuses the plates and rebuilds the board in about 5 s.
- **Per-preset visibility in facts.md.** For each preset in each POV:
  - visible/live, hidden by the train or ground, off-screen, and share of the screen;
  - the mean and 90th-percentile luma change, with the preset drawn alone over the plate.
- **Warnings and flags in facts.md.**
  - A WARN when a preset covers under 0.1% of the screen in every POV, plus "mostly hidden" and "faint" lines.
  - Heuristic flags for train vs world under 2:1 and crush over 5%.
  - Budgets are one line per tier, naming the tightest set (F10, F11).
- **Captions and strips** (R1 B6-1, B3-1).
  - Captions name only what covers at least 0.05% of the frame, plus "hid ..."; the phone tile says what it drops.
  - Strips are cropped to the particles and burst strips are narrower.
  - Labels are 12 px.

**Correctness**
- **Canon check** (R2-H4). `canon_agrees` reads the number next to the property name and ignores hex digits; a ref can carry an optional `match` regex. The swapped-values cases fail now and are in selftest.
- **validate**
  - It checks every look alone, with each override, and with all overrides stacked, and reports each problem once with the look that breaks it (R2-M).
  - It warns when a preset is in no budget set; glass_burst is now in a `windows` set.
  - `none:` presets need an oq or the word "proposed".
  - Flicker over 3 Hz on a light with Range 20 or more warns (R2-L).
- **Work copy** (R2-M, F1).
  - `--presets DIR` works on every command, and `vfx init DIR` makes a work copy (it refuses the shipped folder).
  - Every command prints the presets folder it read.
  - A `sys.modules` alias fixes a latent bug: preview and lookdev were silently reading the shipped library instead of the work copy.
- **lookdev cameras and stand** (R2-M/L, F9, F12, R1 B4-2).
  - A `CAMERAS` table: roof3p, door1p (now looking along the train), cab1p (from tech.camera.cab_view) and coach1p. An unknown camera is an error.
  - The stand uses the canon gauge, width, roof and floor (OQ-030), with cream interiors.
  - It has hazard capped-post roof rails (style.form.rails), measured per look.
  - It has an open cab with the canon cab and firebox lights.
  - The poles are grey-brown, replacing the walnut that read as red.
  - Temp EXRs are cleaned up.
- **Other**
  - Anchors and offsets accept canon expressions such as `"gauge/2"`.
  - Every script sets `dont_write_bytecode`.
  - The Rojo note in the export README maps only the four modules.
  - `build --only` exports just the pack, with a wiring row per preset (R2-L, F13, F14).

**Runtime**
- **Burst lights:** a refresh no longer switches a flash off mid-burst (R2-H3).
- **Start rules:** priority-1 and `start: "off"` loops start off. Presets a look switches on follow the look even when attached late, via `VFX.setLookFx` (R2-M, F13).
- **Speed-linked lights** dim with Speed.
- **Flashes setting:** `VFX.setFlashes` and `Lighting.setFlashes` soften pulses, freeze flicker and skip flash overrides (R2-L).
- **New `scripts/luatest.py`:** lupa with Lua 5.1 and Roblox stubs, 19 checks. The old RR_VFX fails 10 of them.

**Presets**
- **New `sparks_brake` (proposed):**
  - outward fans at ±gauge/2, Speed 30–44, Drag 0.4, Size 2.2 to 0.8;
  - a ground glow linked to Speed, starts off, in 3 budget sets.
- **New grassland `dusk` (OQ-026):** mauve decay, rose ColorShift_Top, Saturation 0.22, exposure compensation 1.05.
- **Crisis presets:**
  - `smoke_chimney` is darker.
  - `sparks_axle` and `sparks_powerbox` are thrown and sized so players can see them.
  - The window moved to coach A.
- **Canon and lighting fixes:**
  - The headlamp cites style.thumb.glow.
  - Night Ambient is raised as far as the tunnel clamp allows.
- **Docs.**
  - SKILL.md is 123 lines: work copy, "author, never substitute", one board and one critic, a maker visibility check, runtime start rules, a dry-run route for canon gaps, and the scripts' critic lookup order.
  - presets.md gains an authoring checklist and a "Visible from the players' views" section.
  - fidelity.md, rubric-fx.md and design-notes.md are updated.

## Rejected or partly applied
- **R1 B1-1, "roof3p hidden at most 50%":** not reachable. From coach B's roof, coach A's body hides the loco wheels (roof3p shows 3 of 92 sparks).
  - The outward fans, glow and WARN are in.
  - B1-2 is met in the door view: 28 of 92 visible, 0.16% of the screen.
  - Whether roof players must see brake sparks is the owner's call.
- **R1 B2-1, raise OutdoorAmbient:** OutdoorAmbient is canon (70,80,70), so I used the canon cream interiors and night Ambient 38,42,52 instead. The new all-combinations check caught that 42,46,58 breaks the tunnel clamp.
- **R1 B2-3, a roof lamp per coach:** that would add a prop with no canon; the facts flag the train-vs-world numbers instead.
- **R1 B5-1, diesel "23" livery:** its files are out of reach (OQ-020) and the livery is open (OQ-025).
  - I took the critic's other option: the tiles and brief say "stand-in train".
  - The hazard rails are measured per look instead.
- **R1 B4-1:** I used a softer rose (150,100,84) than #D9A08C and tuned to the numbers.
- **R2-L, share the flashes setting with RR_Feel:** that is a sibling skill I may not edit; the docs point both runtimes at the same player setting.
- **R2-M, refuse edits inside the skill:** a script can't stop an agent editing files. `init` refuses the shipped folder, every command prints where it read from, and SKILL.md states the rule.
- **F18:** belongs to multiuse-critic's critic_kit, not this skill.
- **F3:** the dry-run route is documented; I made no bible writes.

## Re-trial
The re-trial is in `/home/user/claude/trials/rr-vfx-lighting/retrial/`: a work copy, the same pack, a full-resolution board, a pack export, and a pass-1 critic prompt that is built but not yet run.

| Check | Before | Now | Target | Met? |
|---|---|---|---|---|
| Pack preview | 2 manual calls + 2 hand-written tools | 1 command, 55 s; rebuild 5 s | — | — |
| Brake sparks in a player view | none | door1p: 28 visible, 0.16% | ≥ 20 visible | yes |
| Phone 1:1 hero tile | none | 844x390 at phone rates | present | yes |
| door1p crush, day / dusk / night | 14.7 / 15.0 / 26.2% | 4.6 / 0.0 / 6.2% | ≤ 5% | 2 of 3 |
| door1p train vs world, day / dusk / night | 2.46 / 1.2 / 1.23 | 2.04 / 1.11 / 1.05 | ≥ 2 | 1 of 3 |
| Dusk roof3p ground saturation | 0.14 | 0.20 | ≥ 0.20 | yes |
| Dusk roof3p luma | 73.4 | 84.5 | ≥ 85 | no, 0.5 short |
| Dusk roof3p train vs world | 1.92 | 2.28 | ≥ 2.5 | no |
| Night roof3p train vs world | 1.64 | 1.57 | ≥ 2 | no, flagged |
| Coal dust player view | strip only | cab1p, 1.64% | — | — |
| Default crisis presets under 0.1% in every view | 3, unreported | 0 (axle 0.73%, power box 0.12%, glass 0.78%) | — | — |
| Colour bands / spawn-edge fog | none / ≥ 0.956 | none / ≥ 0.956 | none / ≥ 0.95 | yes |

- **New flags:** steam and smoke are faint against the dusk sky, and smoke is faint at night.
- **Critic prompt:** critic.md is 19.6 KB. No critic was spawned in this fix pass; running pass 1 is the next step.

## Result
- **Validator:** quick_validate says "Skill is valid!" (the description is exactly 1024 characters).
- **Tests:** selftest 47/47 (including Blender), luatest 19/19, `validate --strict` PASS, `budget` PASS, build PASS (luaparse and canon).
- **Hygiene:** no `__pycache__` anywhere.
- **Package:** `/home/user/claude/dist/rr-vfx-lighting.skill`
- **Scores:** review scores [5, 6]. There is no new critic score yet.

Files are in `/home/user/claude/rr-vfx-lighting/`:
- scripts/vfx.py
- scripts/preview.py
- scripts/fxsim.py
- scripts/lookdev_bpy.py
- scripts/luatest.py (new)
- scripts/selftest.py
- assets/luau/RR_VFX.lua
- assets/luau/RR_Lighting.lua
- assets/luau/RR_FXDemo.client.lua
- presets/vfx.json
- presets/lighting.json
- presets/budgets.json
- SKILL.md
- references/presets.md
- references/fidelity.md
- references/rubric-fx.md
- design-notes.md

The re-trial board is `/home/user/claude/trials/rr-vfx-lighting/retrial/preview/board/`.

## Independent certification after fixes
Fresh critic on the fixed re-trial: overall 4 ({'F1': 4, 'F2': 6, 'F3': 5, 'F4': 5, 'F5': 6, 'F6': 6}); 9 blocks-8 issues. Verdict saved at /home/user/claude/trials/rr-vfx-lighting/retrial/crit/pass-1/verdict.md.
