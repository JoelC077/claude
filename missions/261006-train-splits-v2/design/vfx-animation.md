# P5 design: VFX + animation v2 (70% split, 30% split, 0% full train)
> **Read with mission.md Overrides O1-O12** (2026-10-06, after the 3-lens review in ../review/): where this file disagrees with mission.md, mission.md wins. Key ones here: O2 one 0% timeline (hero blast t0+1.5, SequenceDone t0+4.5), O3 client-side motion (0 server writes/frame), O7 coverage + carry-over + fallback board, O10 6 cameras.

Planning only. Paths: M, V1, SK as in refs/context.md. `vfx` = `python3 SK/rr-vfx-lighting/scripts/vfx.py`,
`feel` = `python3 SK/rr-game-feel/scripts/feel.py`. Sound ids follow design/sound.md (P6 owns them). est. = estimate.

## 1. Diagnosis (v1 fx critic: overall 5, F2 5; pass-2 fixes never re-scored)
| cause (v1 evidence) | fix in v2 |
|---|---|
| Too small: split_explosion had 6+5+7 particles (20 live); F1-1 "BIG >= 30 studs" open | **1. Layered hero burst**: flash, fireball >= 30 studs, soot column, Disc-rim shock ring (ShapePartial=1), debris; sized to the phone peak |
| Formless blobs: smoke_main for fire, soot and dust (F2-1..4) | **2. Authored flipbooks** from headless Blender (fireball 8x8; soot, steam, black smoke 4x4; 1024²), each with a plain fallback that alone reaches 8 |
| Wrong viewpoint: stand cams face forward, no tear; rail-level burst 0% visible from roof3p; no burst phone tiles (F4-1) | **3. Rear-facing stand**: roof3p_back, door1p_back, clip cam; phone tile per burst; real tear geometry after the owner export |
| Motion apart from fx: GIFs use sphere/cube stand-ins; topple is a plain roll | **4. One timeline** drives fx, motion, camera, sound; GIFs composite real sprites on the moving wreck |
| Grey-on-grey torn smoke, no ember glow (F3-1) | **5. Declared colour ramps per flavour** (white-yellow core, orange, soot; coal embers / diesel black), validated out of the sepia band |

## 2. Beat sheets (t in s from the snap; nominal; integrity drain sets the real lead)
Camera presets = rr-game-feel; no forced camera at 70/30 (co-op keeps playing). P = PROPOSED, C = CORE.

**70% split (C2)** — lost set per P8; fx anchor at the break plane either way.
| t | beat | VFX layers | motion | camera | sound | C/P |
|---|---|---|---|---|---|---|
| -3..-0.3 | warning (integrity within ~5 pts, P8 sets) | crack-line Beam along the tear, seam sparks crackle, interior light flicker; rate rises with proximity | carriage wobble 0.3-1 deg, 3-5 Hz | micro shake 0.1 deg | creak_warn | P |
| -0.25 | pre-crack | spark spit at roof bites | recoil starts | - | tear_70 | C |
| 0.00 | snap + blast | PointLight pulse 0.12 s (Shadows off); ColorCorrection flash <= 0.35; fireball flipbook 30-36 studs; shock ring at floor level 0 -> 40 studs in 0.35 s | gap opens 0.8 studs in 0.2 s | hit-stop 100 ms local; big shake; HapticEffect GameplayExplosion | boom_70 | C |
| 0.00-0.10 | glass | all panes within 6 studs of the plane: 12-23 shards each, glint, 0.1 s stagger | - | - | glass | C |
| 0.05 | debris launch | 8 real chunks phone / 16 PC (4 with Trails) + 40/80 particle chips | scripted arcs, seeded | - | debris_rain (t 0.8) | C |
| 0.1-1.0 | soot column | soot flipbook rolls into a mushroom, streams back on GlobalWind; hot bits | - | - | - | C |
| 0.25 | brake-off | - | brake to terrain speed, then drift back (v1 maths) | - | scrape_loop | C |
| 0.45-1.5 | topple | rail sparks along ground contact | lean-back 3 deg 0.15 s, then roll ~97 deg QuadIn, overshoot 5 deg, settle | - | scrape_loop | C |
| 1.5 | landing | topple_dust band >= 30 studs, 16 puffs | bounce, sink 0.15 | medium shake | topple_crash | C |
| 1.6 | secondary blast | fireball at 60% scale, 4 chunks, no screen flash | wreck hop 1 stud | small shake | land_boom (new id) | P |
| 0.05-20 | torn edge | ember specks + fire tongues 6 s, then smoke 20 s; ember PointLight flicker | - | - | fire_loop | C (fire: L8) |
| 3-8 | wreck burns away | wreck smoke trail into the haze | drift to 700 studs / 30 s despawn | - | wreck_land | C |

**30% split (C1 and rest)**: same rows with these changes: blast scale x1.25 (fireball 38-45 studs, ring 50); ids
tear_30 / boom_30; up to 2 bodies (body 2 jackknifes, yaw 25 deg, P); interior blast tile judged from coach1p
because players are inside C1; a "dying train" loop on the kept part until 0% (sparks crackle + loco smoke, P).

**0% full train (game over)**
| t | beat | VFX layers | motion | camera | sound | C/P |
|---|---|---|---|---|---|---|
| -3..0 | meltdown warning | heart glow (SurfaceLight pulse 2 Hz), steam jets (coal) / fuel spurts (diesel), sparks on every coupling | whole train shudders 1 deg | shake 0.2 deg | creak_warn | P |
| -0.2 | inhale | glows drop to 0, particles TimeScale 0.5 | - | FOV -3 deg | preboom_suck | C |
| 0.0-1.2 | chain reaction, rear to front | one pop per chunk every 0.25-0.3 s: fireball 18 studs, 2 chunks, no screen flash (lamps only) | each chunk launched: scripted arc 15-35 studs up, tumble 90-360 deg/s | small shake per pop | chain_pop (rising pitch) | C |
| 1.2 | hero blast at the heart (boiler / fuel tank) | 2nd and last screen flash <= 0.35; fireball 50-60 studs; double shock ring 0 -> 80 studs; mushroom column 60 studs | loco launched 40 studs up, slow tumble | hit-stop 150 ms; big shake; FOV kick +6; haptic | final_blast | C |
| 1.2-1.6 | clip beat | particle TimeScale 0.3, chunk playback 0.3x (scripted, so it can slow) | - | pull-out to clip cam (P7 owns) | final_blast `_slow` tail | P |
| 1.6-3.5 | landings | dust bands + debris rain; one runaway wheelset rolls off | chunks land on raycast ground, bounce, settle; world scroll brakes to 0 by +3 (P8) | landing shakes | wreck_land, debris_rain | C (wheelset P) |
| 2.0-3.5 | secondary booms | 2 small blasts on landed chunks | hop | - | land_boom | P |
| 3.5-8 | hand-off | fires + smoke columns stay; fx keep running under the UI | still | camera holds wide; at +5 stamp (P7/UI), at +8 results | gameover_sting | C |
Players are flung at 0.0-1.2 by P7's fling layer; this design only leaves it room (no collision with chunks).

## 3. Animation approach
| item | pick | reasons | fallback |
|---|---|---|---|
| (a) topple | **scripted** (v1 Shared.bodyCFrame + anticipation, overshoot, settle) | smooth on phones; server writes 1 root CFrame per body, clients re-run the seeded curve; deterministic; bbox pivot fits any train; physics will not ride a CFrame-scrolled world (unverified) | v1 roll |
| (b) debris | **hybrid**: client-only real chunks on seeded scripted arcs (one ground raycast) + particle chips | no server cost or replication; no client-owned physics (exploit, refs B); slow-mo works | skill `Debris` class (client VectorForce) |
| (c) 0% blow-up | **scripted chunks, client-side** (server sends seed, t0, chunk list; anchors the train) | 0 server writes at the climax; one seed = same picture for all; no ownership hand-off; run is over, server state moot | server-driven at 20 Hz (v1 wreck pattern) |
Debris = a small kit (plank, panel, wheel, coal lump / fuel can) tinted from the train; real train parts move only as
wreck bodies (70/30) and chunks (0%).

## 4. Train-agnostic rules
- One config block per train in `TrainSplitConfig.Trains[name]`; a missing block falls back to `generic` (L3).
  Keys: `flavour`, `heart` (part name, else the largest part in the front car), `chunks` {auto, max}, `glass` ("auto" =
  Material Glass within 6 studs of the plane), `blast_scale`, `colours` (declared fx colours).
- Flavour = overlay layers on the shared presets. Coal: steam burst, ember sprinkles, coal-lump debris, boiler heart.
  Diesel: bigger fuel fireball (longer, more yellow), black oily smoke, fuel-can debris, diesel_sweet. Future: add a
  flavour, no code (e.g. electric arcs, P).
- Anchors (SplitCore, TornEdge, WreckDust, Heart) are created by the setup script from the break frames, never placed by hand.
- 0% chunking, in order: explicit `RR_Chunk` attributes; else RR_Half labels for carriage halves plus each top-level car
  (loco, tender); else slice the remaining train's bounding box along its axis into >= 20-stud segments (est.); merge
  tiny ones; cap 6 phone / 8 PC. Computed at edit time by the setup script, cached at spawn as fallback, never at 0%.

## 5. Budgets (mid-range phone; caps = budgets.json, OQ-029 default A; our numbers are targets, est.)
| event | burst peak (cap 800/2 s) | steady live (400) | emitters (12) | lights in view (8, 0 shadowed) | beams (4) | real debris (8) | moving bodies | server CFrame writes/frame |
|---|---|---|---|---|---|---|---|---|
| 70% | 560 | 220 | 10 | 3 | 2 | 8 | 1 | 1 |
| 30% | 640 | 260 | 11 (pooled) | 3 | 2 | 8 | <= 2 | <= 3 (with a live 70% wreck) |
| 0% | <= 780 in any 2 s window (pops staggered) | 380 | 12 (3 pop rigs round-robin) | 4 (pooled) | 2 | 8 (recycled) | chunks 6 (PC 8) | 0 (+ any live wrecks) |
- Bursts use Emit() on pre-built pooled emitters; no runtime property churn (refs A).
- Tiers: **PC**: everything, debris 16. **Phone**: flipbooks on, rate_scale by priority, no Bloom/SunRays. **Low**
  (quality <= 3 or low-memory, where flipbooks auto-off): plain textures, 1 flash light, debris 4, shock ring kept
  (priority 1). The low tier alone must reach F 8.
- Flash: <= 3/s, peak 0.35 (red 0.25) (av.feel.flash_limit); only 2 screen flashes at 0%, 1.2 s apart; pops use lamps
  only; Flashes setting off -> no screen flash, lights halved.
- Reduce Motion (GuiService.ReducedMotionEnabled): no shake, FOV kick, wobble-cam or pull-out; slow-mo becomes a
  0.4 s hold on the hero frame; fx and sound unchanged; hit-stop <= 150 ms kept local (av.feel.hitstop_local).

## 6. Preview plan
- **Boards**: `vfx preview all <pack> --gif` over the upgraded stand (rear cams, phone tile per burst); stand-in train
  until the owner export, then the real CoalTrain and Diesel geometry.
- **Real textures**: our Blender flipbooks are the shipping textures, so previews use them exactly (fxsim needs a
  PNG sprite input: V2). Roblox built-ins from a public GitHub client mirror: unverified, preview only.
- **Motion GIFs**: v1 render rig (src/render/anim.py) with fxsim sprites composited per frame instead of spheres;
  per event: roof3p_back, door1p_back, clip cam, phone 844x390; 24 fps, -1 to +6 s (0%: -3 to +8).
- **Critic**: Profile F (F1-F6) on the board, bar 8, target 9. Plus a **motion check** (no animation profile exists):
  frame strips at t = -1, 0, 0.1, 0.3, 0.6, 1.2, 2.5, 5 scored M1 snap readable, M2 arcs and weight, M3 timing and
  spacing (chain cadence), M4 continuity (no pops, wreck drift matches terrain), anchors 4/7/9; overall = lowest of F and M.

## 7. Build tasks
| id | deliverable | skill / commands | depends | model/effort | est. tok | done-when |
|---|---|---|---|---|---|---|
| V1 | fx work copy, flavour colour ramps, 3 budget sets | `vfx init M/src/fx`; edit vfx.json, budgets.json; `vfx validate --strict`, `vfx budget` | P8 intake | opus/medium | 40k | both PASS |
| V2 | preview stand: rear cams, clip cam, burst phone tiles, PNG sprites in fxsim | mission-local wrapper over lookdev_bpy.py / fxsim.py | V1 | opus/high | 80k | board shows every burst from a rear POV + phone; WARN-free |
| V3 | 4 flipbook sheets + plain fallbacks | headless bpy (Cycles CPU) script, Pillow packer | - | opus/high | 70k | exact grid, 1024², padded; owner upload list |
| V4 | presets: split_blast (70/30 scale), shock_ring, soot_column, glass_v2, torn_edge_v2, chain_pop, final_blast, warning (P), land_boom (P), flavour overlays | `vfx` validate, budget, preview, build `--only` | V1-V3 | opus/high | 120k | strict PASS; every tile >= 0.1% screen, p90 >= 25 |
| V5 | flash/look overrides + feel events (hit-stop, shake, FOV, haptics, reduce motion) | `vfx` lighting overrides; `feel set/validate --strict/preview/crit` (Profile G) | V4 | opus/medium | 60k | strict PASS; G >= 8 |
| V6 | Shared maths v2: topple anticipation/overshoot, debris arcs, chunk flight, terrain drift + Lune tests | Lune `run_tests.luau` | P8 harness refresh | opus/high | 90k | tests green; curves plotted |
| V7 | setup labels: anchors, glass auto, RR_Chunk slicing, per-train config | rework RR_TrainSplit_Setup (with P8) | owner export | opus/high | 80k | Lune fixtures for Coal + Diesel pass; <= cap chunks |
| V8 | client beat runner v2 (data-driven beats, pools, tiers, flashes, reduce motion) | TrainSplitClient rework; `luatest.py` stubs | V4-V7 | opus/high | 110k | stubs PASS; budget guard never cuts priority 1 |
| V9 | motion GIFs with real fx, 3 events x 4 cams | anim.py + fxsim composite | V2-V4, V6 | opus/medium | 70k | 12 GIFs + frame strips |
| V10 | critic loop to target 9 | `vfx crit CRIT --pass N --from P`, critic_kit `--profile F` + motion check | V4, V9 | opus/high (fresh critic) | 150k / pass x <= 5 | F and M >= 8 each, aim 9 |
| V11 | export + owner Studio checklist (MicroProfiler per event on his phone) | `vfx build`, `feel build` | V8, V10 | sonnet/low | 25k | build PASS; "Studio test pending (owner)" |
| V12 | skill-smith proposals: flipbook authoring, motion profile, rear cams (G1, G2) | rr-skill-smith `harvest.py patch`, `ship.py stage` | V10 | opus/medium | 40k | staged; owner approves |
