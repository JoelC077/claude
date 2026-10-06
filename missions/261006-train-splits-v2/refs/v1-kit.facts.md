# v1 kit facts (P1 scout, mission 261006-train-splits-v2, 2026-10-06)
Source: V1 = missions/260929-train-splits. Paths below are relative to V1. All files read; nothing changed.
export/studio/* is byte-identical to src/luau/* except TrainSplitConfig (export has the `glass_split` fix; src still says `glass_burst`).
The v1 state.json stops at step 8/10 (2026-09-29 23:52Z).

## 1. Components
| file | role | public API / entry | status | v2 |
|---|---|---|---|---|
| studio/RR_BreakChecker.lua (578 L) | read-only command-bar scan: carriages, crossers | select train, paste | out of date (no IN_PLACE; CORE differs from setup; CoalTrain roof sig only) | rework: per-train profile |
| studio/RR_TrainSplit_Setup.lua (1365 L) | edit-time CSG cut along 29-cell tear, labels parts RR_Half, writes Train/RR_Breaks | DRY_RUN flag, paste | ran OK on live CoalTrain (owner) | rework: profile-driven, N carriages, Diesel |
| studio/TrainSplit.lua (543 L) | server: SplitAt, wreck bodies, motion drive, rider candidates | `SplitAt(train,k,opts)`, `IsIntact`, `GetBreaks`, `ConfirmRiders`, `Snapped`/`Despawned` BindableEvents | untested in Studio (RR_TestBreak silent) | keep core; add integrity trigger, final explosion and fling hooks |
| studio/TrainSplitShared.lua (342 L) | pure maths: drift, topple, lostHalves, rng, timeline | `bodyCFrame`, `drift`, `lostHalves`, `eventsTimeline`, `rng` | Lune 60/60 PASS | keep |
| studio/TrainSplitClient.lua (523 L) | client: timeline of fx, sound, shake; wreck smoothing | RemoteEvent `RR_TrainSplitFX` (server to client) | untested in Studio | rework: v2 fx, sound and anim layers |
| studio/TrainSplitConfig.lua (193 L) | all tunables (shared) | module table | glass fix applied in export only | rework: per-train blocks |
| studio/TrainSplitDemo.server.lua (51 L) | Studio-only trigger via attribute | `RR_TestBreak` = 1/2 on train (Server view) | silent in Studio | replace with an integrity test panel |
| fx/RR_VFX.lua + RR_FXPresets.lua | particle runtime + presets | `VFX.burst`, `attach`, `setIntensity`, `detach` | built, critic 5 (fixes unscored) | keep runtime; redo presets |
| fx/RR_Lighting*.lua | lighting presets | - | not wired to the split | keep (out of scope) |
| sounds/*.wav (6) + SOUNDS.md | synthesised sfx | Config.Sounds ids | not uploaded, never heard | rework / replace (L8-10 bar) |
| TrainSplitKit.rbxmx, train_split_kit.zip | packaged kit | - | as exported | rebuild |

## 2. v1 timeline and motion (Config.Events, break_spec v2.3.0)
| t (s) | id | fx | sound | shake |
|---|---|---|---|---|
| -0.25 | metal_tear | - | metal_tear | - |
| 0.0 | split_explosion | split_explosion | split_explosion (2D 0.792 + 3D 0.5) | big (1.5 deg, 0.9 s, 14 Hz, falloff 250) |
| 0.0 | glass_burst | glass_split (2 panes) | split_glass, 0.1 s stagger | - |
| 0.05 | torn_edge_smoke | torn_edge_smoke loop 20 s, fade 3.5 | - | - |
| 0.3 to V/12 (2.92 at 35) | wreck_scrape | - | wreck_scrape, speed clamp(35/V, 0.7-1.2), 0.3 s fade | - |
| 0.8 | debris_rain | - | debris_rain | - |
| impact: 1.5 body 1, 2.0 body 2 | topple_crash | topple_dust | topple_crash (body 2 pitch x0.94) | medium (0.6 deg, 0.5 s) |
Motion: SplitAt lead 0.25 s; Speed attr clamp 0..60, default 35; recoil 0.8 studs in 0.2 s; brake 12 studs/s^2 to terrain speed at V/12 s (~51 studs at 35), then falls behind at V. Despawn 700 studs or 30 s (~21.4 s at 35, computed).
Topple: pivot X_abs 11.7, Y -8.6 (rail level, outer bogie edge). Rest roll +X 97.64 (lift 0.747), -X 96.78 (lift 0.435). Body 1: delay 0.45, roll 1.05 s QuadIn, bounce 5 deg / 0.35 s, yaw 7, sink 0.15. Body 2: delay 0.8, roll 1.2 s, bounce 4 / 0.4 s, yaw -4, extra_back 0.6. Side random per seed.
Tear: 29 cells, walls +-0.9, roof bites up to 4.8 forward, floor tongues up to 3.6 back. Break plane = roof centre + 3.31 studs rearward (CoalTrain).

## 3. Critic scores (bar 8)
| deliverable | pass state | scores | top unresolved |
|---|---|---|---|
| FX (critique-fx-split) | pass 1 scored only; pass-2 delta is maker's report, never re-scored | F1 6, F2 5, F3 6, F4 7, F5 7, F6 6 = 5 | 1 F4-1 phone burst tiles: tool limit, unmeasured. 2 F6-1 debris trail scythe not met. 3 stand caveat: no tear, cameras face forward (players look back), so shares are inflated; derail_explosion 0% visible from roof3p |
| Sound (critique-sound) | pass 2 delta = 8; pass-3 polish done; final fresh pass not run | S1 8, S2 8, S3 8, S4 8, S5 8, S6 9 = 8 | 1 nobody has listened (Studio test pending). 2 metal_tear low end cut: owner to check weight on PC. 3 breakdown_bang phone-ladder flags accepted, not fixed; SOUNDS.md (group "Split", 0.796/0.502) drifts from Config (Alarms/Actions, 0.792/0.5) |
| 3D (critique-splits) | pass-1 board built, never scored | preflight: cut error 0.0000%, seam max 7/255, 0 floaters, rest PASS, true slivers 0 | 1 no score. 2 feathering 0.002 studs at X +3.70 / -4.60. 3 renders use the OBJ export roof (3.59 thick); live is 5.86 |
| Security (rr-exploit-guard) | HOLD, 0 blocking | - | OC1 LoadString, OC2 Http, OC4 bug bash open; reviewer re-check of 5 fixes unfinished |

## 4. Hard-coded assumptions blocking multi-train / integrity order
- Roof signature `ROOF_SIG {5.86,19.23,62.34}`, tol 0.1: Setup:34,225; Checker:24,214. Diesel will not match: refuses unless `ALLOW_PLANE_FALLBACK` (Setup:29), which gives a flat cut.
- Break frame offsets `BREAK_DZ 3.31`, `FLOOR_DY -11.443`, `CROSS_DX -0.05`: Setup:36-38. `EXPECTED_CROSSERS 10`: Setup:42.
- Exactly 2 carriages: Setup:685-686, loops `for k = 1, 2` at Setup:604,694,752,814,1156,1256,1263; Checker:572.
- `FRONT_AT = "min"` manual: Setup:25.
- Break k sits in carriage k, linear chain (all behind is lost): Shared:214-251, TrainSplit:404. The new order works as SplitAt(2) at 70%, then SplitAt(1) at 30% (lost set C1.Rear + C2.Front). But body 2 (half carriage) gets the whole-carriage topple entry (Config:46, TrainSplit:448).
- No integrity input, no 0% path, no game-over hook anywhere. The trigger is only an external SplitAt call.
- `Speed` attribute: Config:20 (default 35, max 60).
- CoalTrain cross-section: Config cells :53-83 (+-14/18) differ from Setup cells :46-76 (+-20/24). Pivot :37, ToppleRest :38-41, glass anchors +-9.75 :104-107, torn_edge :108.
- Paths: TrainSplit:28-29 and Client:23-24 need `ReplicatedStorage.Modules.TrainSplit.TrainSplitConfig/TrainSplitShared`. README says RS root. Demo:15 needs the `TrainSplit` module as its sibling. Names: RR_Breaks/BreakN, RR_Carriage<k>/FrontHalf, RR_Half "1Front", remote RR_TrainSplitFX, folder RR_Wrecks.
- IN_PLACE: lost parts stay parented under the train, only welded to BodyRoot (TrainSplit:197-210, 257-272). The owner's train scripts can still touch them.

## 5. Known bugs and loose ends
**RR_TestBreak silent: likely causes, ranked**
1. The attribute was set in the Client view. Play mode defaults to Client, attributes do not replicate up, and the Demo listens only on the server (Demo:4-6, 24).
2. Install-path mismatch. The code needs RS.Modules.TrainSplit.* (TrainSplit:28) and the Demo needs a sibling `TrainSplit` (Demo:15). If either is missing, WaitForChild yields forever before the hook, so the Demo is silent apart from a yellow "Infinite yield possible" line.
3. The play-time train is not the set-up model. If the train-select / universal layer clones a template without RR_Breaks, `consider` (Demo:42-46) never hooks it, and no "[TrainSplitDemo] ready" line prints.
4. SplitAt ran but nothing visibly moved. IN_PLACE parts stay under the train, so the game's own scripts or joints that `releaseFromTrain` misses (TrainSplit:165) can re-anchor or hold them. Sound ids are empty, so it is silent anyway.
5. The value was not changed. Setting the same number again fires no change signal; a non-number value is ignored (Demo:25).
Ask Joel: did "[TrainSplitDemo] ready" print, and in which view was the attribute set?

**Lune** (copied to the scratchpad, `lune run tests/run_tests.luau`): **91 PASS / 52 FAIL**, exit 1 (v1 log said 305/305).
- Shared maths 60/60 pass.
- Every failure cascades from 3 causes:
  1. The synthetic train is built from the OBJ roof (3.59), but ROOF_SIG is live (5.86), so "no roof union" breaks the checker, the setup, the server, the client and the Demo (0 runtime coverage).
  2. Setup/checker cells widened to +-20/24 vs break_spec +-14/18.
  3. The CORE blocks differ (IN_PLACE).

**Sounds:** 6 wavs (48 kHz/16-bit, -14 LUFS M max, <= -1 dBTP) not uploaded. All Config.Sounds SoundIds are "", so the client stays silent (Client:246).

**GIFs:** 3 Blender animations (src/render/out/anim_wide1, anim_wide2, anim_roof1, 78 frames each) use sphere and cube stand-in fx, labelled "stand-in fx" (anim.py:1,172). The real particles exist only in the per-preset GIFs (src/fx/preview/vfx/anim_*.gif).

**Other:**
- No FRICTION.md or SKILL-FRICTION.md exists under V1.
- The geometry source temp2.obj sits only in the session scratchpad (train/). It is not in git, so a fresh container loses it (src/analysis/groups.json survives).

## 6. Reusable in v2
| asset | path | use |
|---|---|---|
| Shared maths (drift, topple, rng, lostHalves, timeline) | src/luau/TrainSplitShared.lua | keep and extend for N bodies, fling arcs |
| server authority pattern (anchored root + welds, server->client remote, misuse flag, ConfirmRiders) | src/luau/TrainSplit.lua | base for the v2 server |
| client timeline runner + fallback fx + shake (reduce-motion) | src/luau/TrainSplitClient.lua | base for the v2 client |
| Lune harness + spec sync | src/luau/tests/{harness,run_tests,sync_spec}.luau | refresh fixtures, then CI |
| break design generator + sliver check | src/kit/break_spec.py, sliver_check.py | per-train tear profiles |
| OBJ parse / union boxes | src/analysis/objparse.py, union_boxes.py, groups.json | intake for the Diesel export |
| Blender render rig (cut, pose, cameras, anim) | src/render/{build,scene,anim}.py | v2 renders/GIFs (needs RR_TRAIN_OBJ) |
| VFX runtime + presets split_explosion, torn_edge_smoke, topple_dust, glass_split, beams debris_smoke/debris_spark/split_streak | src/fx/build/RR_VFX.lua, RR_FXPresets.lua, src/fx/vfx.json, budgets.json | v2 fx base; phone tier 400 live / 800 burst |
| sound recipes, soundmap, RR_Sound runtime (ducking, voice caps), briefs, licence log | src/sound/{recipes.py,soundmap.json,make_final.py,split_timeline.py}, src/sound/build/* | v2 sound layer; briefs seed sourcing |
| critic rubrics + briefs | critique-*/rubric.md, brief.md | v2 critic profiles F/S/A |
