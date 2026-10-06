# P2 facts: canon + JARVIS skill map for train splits v2 (scout, 2026-10-06)
Source: `bible.py get/search` (734 facts, 56 OQ, 22 D) and each skill's SKILL.md + named refs. SK paths omitted.

## 1. Canon table
| id | fact | value | v2 relevance |
|---|---|---|---|
| identity.tone.company | tone | slapstick safety failures, not grim horror | explosion + fling stay cartoon |
| D-002 | train never moves | world scrolls; "falling off is handled by the company, not physics" | fling must not need real train motion; conflicts with physics fling (ask) |
| D-003 | four crisis systems | cut list includes "integrity separate from breakdowns" | **CONFLICT**: owner's integrity system (L4-L7) contradicts D-003; record as owner decision |
| gameplay.crisis.fail_states | fail list | boiler explosion, all passengers dead, stall, buffer overrun | 0% train explosion not listed: add |
| gameplay.crisis.fail_cinematic / av.feel.clip_moments | fail moment | 3 s camera moment per fail, designed to be clipped (proposed) | explosion = clip moment; "clipability" fits canon |
| av.vfx.boiler_fail | fail fx | boiler bursts, then YOU'RE FIRED stamp | reuse stamp for 0% explosion? |
| gameplay.run.fail_screen | fail | same results screen; banked fare kept | 0% = fail path, OQ-011 |
| gameplay.results.incident_report | results | joke grade, one silly award per player | hook for "most flung" award (PROPOSED) |
| gameplay.crisis.coupling | coupling | snaps: lose carriage + passengers (proposed) | splits = this, passengers lost |
| gameplay.train.keep_on | keep-on rule | outside train area 1.5 s -> back in coach, **5-coin fee** | flung players get fined unless exempted: ask |
| gameplay.crew.max / min | crew | 6 / 1 | fling + fx budget for 6 |
| gameplay.speed.slow/normal/fast | Speed | 20 / 35 / 50 | wreck brake-off, fling impulse scale |
| gameplay.speed.loco_table | loco speeds | Starter .35, Diesel .50, Electric .75, Bullet 1.00 mi/s (proposed) | per-train tuning |
| D-006 | one loco family | eras = models + stat sheets (incl. durability) | integrity per train = stat sheet |
| D-015 / gameplay.progress.diesel | scope | alpha wk 12 Oct, steam only; diesel after alpha | owner already built diesel: v2 straddles alpha |
| tech.units.train_len / stud_m / avatar_h | units | 165 studs / 0.28 m / 5 studs | fling distances, despawn 700 |
| tech.camera.eye_3p / eye_1p / fov_v | camera | 9.5 / 4.5 / 70 | death-cam framing |
| av.audio.slapstick / priority | audio | slapstick lands through sound; alarms first | hierarchy fail > crisis |
| av.audio.licence | licence | owner uploads (self-made, commissioned, CC0, bought w/ game licence, proof) or Roblox-licensed Creator Store only; no NC/ND/SA/CC-BY | gates "best sounds" sourcing |
| av.audio.file_standard | loudness | one-shots -14 LUFS momentary, loops -20, all <= -1 dBTP | mastering target |
| av.audio.placeholder | synth | PLACEHOLDER_ never ships (proposed) | v1's 6 synth wavs cannot ship |
| tech.audio.import_limits / quota | import | <20 MB, <7 min, <=48 kHz; 2,000/30 d verified, 100 unverified | upload batches |
| tech.audio.soundgroup_status | API | Sound/SoundGroup legacy; Audio API recommended | runtime choice |
| tech.streaming.sfx_pool / fx_client | runtime | client sound pool; fx client-side, never tween world parts | v1 pattern holds |
| av.feel.flash_limit | flashes | <=3/s, peak opacity 0.35 (red 0.25) (proposed) | explosion whiteout capped |
| av.feel.hitstop_local | hit-stop | local, <=150 ms (proposed) | explosion beat |
| av.feel.reduce_motion / tech.feel.reduced_motion | a11y | shake/kicks off, meaning kept; GuiService.ReducedMotionEnabled | flung camera must respect |
| tech.feel.haptic_types | haptics | incl. GameplayExplosion, GameplayCollision | explosion + landing |
| identity.audience.devices / tech.ui_platform.phone | devices | phones first, 844x390 | fx budget |
| tech.mesh.tris_target / cap | mesh | 10k / 20k | debris chunks |
| tech.security.never_trust_client / fare_grants | security | server-authoritative | integrity + fling server-side |
| tech.analytics.server_only | analytics | server only | fling events from server |
| tech.cloud.no_studio / no_ffmpeg | cloud | no Studio; GIF via Pillow | all Studio tests owner-side |

## 2. Open questions / decisions v2 touches
| id | text | current default |
|---|---|---|
| OQ-028 | derailment: breakdown task or explosion? | A: only boiler explodes (v1 A6 overrode to "big but slapstick" for splits) |
| OQ-011 | does a failed trip pay? | A: banked fare kept |
| OQ-021 | audio identity | A: diegetic only, no music in runs |
| OQ-035 | alarms train-wide or at source | A: 2D + positional layer |
| OQ-036 | community Creator Store audio | A: no (Roblox/partner only) |
| OQ-029 | phone fx budget | A: budgets.json (400 live, 800 peak 2 s, 12 emitters, 8 debris parts, 4 beams) |
| OQ-032 | feel settings menu | A: Roblox Reduce Motion only in alpha |
| OQ-039 | place perf budgets | A: regression only (+15%) |
| OQ-020 | approved diesel "23" not in reach | A: owner pastes/exports once |
| OQ-030 | rolling-stock envelope | A: gauge 8, width 17.4, roof 14 |
| OQ-042 | shutdown mid-trip | A: award banked fare |
| D-003 | integrity cut | owner's L4-L7 supersedes: needs `bible decide`/add-fact |
| D-020 | quality bar | 8/10 every criterion, independent critic |
| NEW (no canon) | ragdoll/fling, 0% explosion, integrity numbers (70/30/0), split order | nothing matches "fling", "ragdoll", "game over", "integrity" |

## 3. Per skill
**rr-vfx-lighting** (`vfx`=python3 <fx>/scripts/vfx.py)
- Makes: preset JSON -> Luau. `vfx init <M>/src/fx`; `vfx validate --strict --presets W`; `vfx budget`; `vfx preview all NAMES --presets W --out P --gif`; `vfx crit CRIT --pass N --from P`; `vfx build --presets W --out E --only NAMES`. Shipped: derail_explosion, boiler_burst, glass_burst, sparks_*, coal_dust (13 presets).
- Gate: validate+budget PASS, build PASS (luaparse + bible check). Critic: Profile F (F1 signal, F2 form and motion, F3 colour, F4 phone, F5 style, F6 polish).
- Limits: layer classes = ParticleEmitter, Beam, Point/Spot/SurfaceLight, Debris only. **No Explosion instance, no mesh shockwave/ring, no flipbook authoring** (built-in textures only; custom flipbooks need owner upload). GIF yes (fxsim). Preview is approximation, phone cost unmeasured. v1 fx critic: 1 pass, overall 5 (F2 5).

**rr-soundsmith** (`sound`=python3 <snd>/scripts/sound.py)
- Makes: soundmap, `sound synth all --out DIR` (PLACEHOLDER_ only, 29 recipes, numpy), `sound analyze FILES --fix-out DIR [--mono]` (LUFS, true peak, seams, phone loss; levels/trims to standard), `sound register ID ... --origin ... --proof P` (licence gate), `build` (AUDIO_BRIEFS.md with sourcing route: alarms/fail = commission or self-made), `sound sheet`, `sound crit`, `sound validate --release`, `sound promote`.
- Gate: `validate --strict`, build PASS, `--release` fails on placeholders. Critic: Profile S (S1-S6); it **cannot hear**, scores plan/levels/timing only.
- Limits: synth = placeholder quality, never ships; "best sounds ever" must come from commissioned/purchased/Roblox-licensed audio picked by owner's ears. Analyze/fix of owner files works on wav; ogg/mp3 need ffmpeg (absent; `pip install --target ~/.cache/rr-tools/py imageio-ffmpeg`). No layering/designing tool beyond fix (no EQ/compress-design, no stem mixing). Shipped map has no split, creak, fling, wreck-landing or train-explosion events. Freesound/Sonniss/create.roblox.com blocked from shell.

**rr-game-feel** (`feel`=python3 <feel>/scripts/feel.py --presets F)
- Makes: shake, hit-stop, FOV kick, flash, haptics, UI punch events: `feel set`, `feel validate --strict`, `feel plot`, `feel preview E1,E2 --out D --gif`, `feel crit`, `feel build --out D`, `feel tune`. Existing fail events: boiler_burst, fired_stamp; coupling_snap.
- Gate: validate --strict (flash, hit-stop, reduce motion, hierarchy), build PASS (luau-compile/luau-lsp if installed). Critic: Profile G (G1-G6).
- Limits: camera/UI juice only; **no character animation, ragdoll, rig, or body physics**. Preview = mock plates.

**rr-exploit-guard** (`guard`)
- Makes: `guard scan <M>/export --out <M>/security --fail-on high`, `explain`, `pack` (independent review), `fuzz` kit (owner runs), `gate --stage alpha`.
- Gate: PASS/HOLD/FAIL -> release G5. Reviewer independence rule (no critic profile).
- Limits: **physics/movement exploits out of static reach** (fling abuse, client-owned character position). Will catch a client-fired integrity/split remote.

**multiuse-critic**: native Profiles A (3D) and B (2D); skills add F (fx), S (sound plan), G (feel). **No profile for 3D/character animation or ragdoll motion; no listening critic.** F2/G2 only partly cover motion. 3D wreck/debris -> Profile A.

**risky-rails-mechanic-reviewer**: no scripts; checklist (4 crisis systems, reuse verbs, funny not punishing, physical/loud, scope, where to log). Use on integrity system, 0% explosion, fling. Expect hit on check 1 (D-003) and check 5 (alpha scope).

**rr-skill-smith**: `harvest.py scan`, `health.py`, `drift.py S`, `harvest.py patch S`, `ship.py stage/propose`; apply only with owner's words. Needs friction logs: v1 left none.

**rr-release-train**: `rel status/init/attach/collect/gate/plan`, dry-run only; `scripts/placefile.py` reads binary/XML places (useful to extract owner's Diesel + integrity scripts from a .rbxl). Live publish blocked from cloud.

**rr-data-and-money**: can track fling/clip: tracking plan uses 6 of 30 custom events; add e.g. `train_split` (stage 1/2/3), `player_flung` (server-detected), and add `train_explosion` to `run_end.reason` enum (currently arrived/boiler_explosion/passengers_dead/stall/buffer_overrun/abandoned). `track.py validate/build/scan --strict`. Funnel parked for alpha (release.alpha.sidings).

## 4. JARVIS gaps v2 will hit (candidates for rr-skill-smith)
| gap | evidence |
|---|---|
| G1 vfx: add Explosion-like shockwave (mesh ring/sphere tween), flipbook schema, smoke-column layers | presets.md classes list; SKILL "built-in textures stand in for custom flipbooks"; v1 F2=5 |
| G2 animation/ragdoll: no skill or critic for body motion (wreck tumble, ragdoll fling, rig) | grep: no ragdoll/rig/keyframe in any rr-* SKILL; rubric profiles A/B/F/S/G only |
| G3 sound: no "hero sound design" route (layered build from licensed sources, sourcing shortlist, A/B listening sheet for owner) | soundsmith synth = PLACEHOLDER only; Profile S "cannot hear"; licence rule |
| G4 sound: ffmpeg missing for ogg/mp3 analyze | context env probe; SKILL deps |
| G5 exploit-guard: physics/fling rules (server-applied impulse, rate, network ownership) | SKILL §2 "physics/movement exploits outside static reach" |
| G6 canon: no facts for integrity, split order, fling, game over; D-003 conflict | bible search empty for 4 terms; D-003 text |
| G7 friction logging: v1 mission left no SKILL-FRICTION.md; ticket-hud/depot logs show recurring "no Agent tool -> self-review" critic route | find result; 260927-ticket-hud friction #2 |
| G8 shipped soundmap/feel presets lack split events (v1 work not promoted) | soundmap 29 sounds, no split ids; `sound promote` not run |
