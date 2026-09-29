# Critic pass 1: 3D look of the torn carriages (T1, mission 260929-train-splits)

Question for the critic: does each split look really good and accurate (R3; acceptance A1-A7, bar 8)? Geometry, cut and topple come from break_spec.json v2.2.0 via src/render/build.py; numbers below are from src/render/out/preflight.md (2026-09-29 23:52).

## Images in this folder

- contact.png: top band at true size = the player views: break 1 t=4.0 Cam_POV_In and Cam_Roof3P (1600x900 renders scaled to 640x360) and Cam_Game (rendered at 400x225). Grid below (fitted 224x126 tiles): intact seam out, intact roof, exploded, b1 t1.0 wide, b1 t4.0 hero, b1 t4.0 wide, b1 t4.0 side, b2 t4.0 hero. contact.json maps every tile to its file.
- closeups.png: 1:1 crops, no scaling: intact inside, seam at the tear line (1:1 crop) = intact__Cam_SeamIn.png box [511, 48, 1131, 748]; break1 t4.0 hero, torn end of the kept half (1:1 crop) = break1_t4.0__Cam_Hero.png box [591, 27, 1211, 727].
- Full-resolution sources (1600x900, Cam_Game 400x225) are copied here as <state>__<camera>.png; also intact__Cam_SeamRoof_debug.png (tear line drawn in red on the roof) and reference_uncut__Cam_SeamIn/SeamOut.png (the same cameras on the uncut original).

## States and poses

| state | what it shows | pose (drift along +Z; per lost body roll / yaw / sink / lift / extra back) |
|---|---|---|
| intact | all halves in place, seam must be invisible | - |
| exploded | C1 front half -3, everything behind +3 along Z (design view) | - |
| break1_t0.3 | break 1 just after the snap | drift 1.34 / roll 0.0 yaw 0.0 sink 0.00 / roll 0.0 yaw 0.0 sink 0.00 |
| break1_t1.0 | C1 rear half rolling, C2 starting | drift 6.80 / roll 26.79 yaw 1.9 sink 0.00 lift 0.21 back 0.00 / roll 2.71 yaw -0.1 sink 0.00 lift 0.02 back 0.02 |
| break1_t1.6 | C1 rear half bouncing on its side, C2 rolling | drift 16.16 / roll 93.57 yaw 7.0 sink 0.15 lift 0.72 back 0.00 / roll 43.40 yaw -1.8 sink 0.00 lift 0.33 back 0.27 |
| break1_t4.0 | break 1 at rest, wreck ~90 studs behind | drift 89.76 / roll 97.65 yaw 7.0 sink 0.15 lift 0.75 back 0.00 / roll 97.65 yaw -4.0 sink 0.15 lift 0.75 back 0.60 |
| break2_t1.2 | break 2, C2 rear half rolling toward -X | drift 9.44 / roll 49.03 yaw -3.6 sink 0.00 lift 0.10 back 0.00 |
| break2_t4.0 | break 2 at rest | drift 89.76 / roll 96.10 yaw -7.0 sink 0.15 lift 0.20 back 0.00 |

Break 1 falls toward +X, break 2 toward -X (the game picks the side at random). Lost sets: break 1 = C1.Rear (body 1) + all of C2 (body 2, incl. the gangway); break 2 = C2.Rear. Motion: recoil 0.8 in 0.2 s, brake 12 studs/s^2 from 35 studs/s, then static on the terrain.

## Pre-flight numbers

- Cut accuracy: front+rear volume vs original, worst 0.0000 % over 20 crossers (limit 0.5 %); intact cut faces meet with gap 0.0e+00 (0 = below float32 resolution); seam pixels vs the uncut original: Cam_SeamOut max 7/255, 0 px > 12; Cam_SeamIn max 5/255, 0 px > 12.
- Slivers: true slivers (faces within 15 deg of parallel to a cut) under 0.05: 0; thinnest true sliver 0.183 (Union19.F). Feathering (slanted faces running into a cut) under 0.05: 35 samples, thinnest 0.002, on X = +3.70 (0.002, Union109/Union28/Union38/Union56/Union80), X = -4.60 (0.003, Union134/Union28).
- Floaters after the cut: break 1: 0 of 61 pieces near the tear float; break 2: 0 of 61 pieces near the tear float.
- Wreck at rest, break 1 body 1 (C1.Rear): lowest y 5.177 vs limit 5.130; bogie side 5.179, roof side 5.177 (ground 5.33, sink 0.15) -> PASS.
- Wreck at rest, break 1 body 2 (C2 incl. gangway): lowest y 5.174 vs limit 5.130; bogie side 5.176, roof side 5.174 (ground 5.33, sink 0.15) -> PASS.
- Wreck at rest, break 2 body 1 (C2.Rear): lowest y 5.037 vs limit 5.130; bogie side 5.037, roof side 5.182 (ground 5.33, sink 0.15) -> FAIL.
- Wreck bodies at rest (break 1, C1.Rear vs C2): max interpenetration 0.000 (no intersecting parts), limit 0.3, target < 0.1; intact model 0.003.
- Other groups crossing the tear surface: none.

## Parts

- 957 OBJ groups imported (Studio export temp2.obj); 20 crossers cut (10 per carriage); every other group goes whole to one half by its bbox centre; the gangway Union22 belongs to C2.FrontHalf.
- Objects per half after the cut (whole parts + cut pieces): C1F 243, C1R 188, C2F 233, C2R 333.

## Cut method per crosser

| carriage | crosser | method | cut faces F / R | volume off % | note |
|---|---|---|---|---|---|
| C1 | Carpet1 | manifold3d | 22 / 22 | +0.0000 |  |
| C1 | CurtainCorroded1 | manifold3d | 336 / 336 | +0.0000 |  |
| C1 | Part269 | block sliced per cell | 6 boxes / 6 boxes | +0.0000 |  |
| C1 | Union12 | manifold3d | 41 / 41 | +0.0000 |  |
| C1 | Union16 | manifold3d | 4 / 4 | -0.0000 |  |
| C1 | Union19 | clip+caps | 242 / 242 | +0.0000 | not watertight after weld (3 non-manifold edges, 1 fin pairs); manifold3d would import it as 713.139 (-0.14 %) |
| C1 | Union28 | manifold3d | 157 / 157 | -0.0000 | 4 zero-area triangles dropped at weld |
| C1 | Union38 | manifold3d | 102 / 102 | +0.0000 |  |
| C1 | Union56 | manifold3d | 102 / 102 | +0.0000 |  |
| C1 | Union61 | clip+caps | 130 / 130 | +0.0000 | not watertight after weld (1 non-manifold edges, 0 fin pairs); manifold3d would import it as 1414.736 (-0.05 %) |
| C2 | Carpet2 | manifold3d | 22 / 22 | -0.0000 |  |
| C2 | CurtainCorroded2 | manifold3d | 362 / 362 | +0.0000 |  |
| C2 | Part409 | block sliced per cell | 6 boxes / 6 boxes | +0.0000 |  |
| C2 | Union109 | manifold3d | 95 / 95 | -0.0000 |  |
| C2 | Union134 | manifold3d | 148 / 148 | +0.0000 | 4 zero-area triangles dropped at weld |
| C2 | Union138 | manifold3d | 4 / 4 | +0.0000 |  |
| C2 | Union77 | manifold3d | 43 / 43 | +0.0000 |  |
| C2 | Union80 | manifold3d | 93 / 93 | -0.0000 |  |
| C2 | Union84 | clip+caps | 127 / 127 | -0.0000 | not watertight after weld (2 non-manifold edges, 0 fin pairs); manifold3d would import it as 1414.757 (-0.05 %) |
| C2 | Union86 | clip+caps | 242 / 242 | +0.0000 | not watertight after weld (3 non-manifold edges, 1 fin pairs); manifold3d would import it as 687.017 (-3.80 %) |

manifold3d = mesh minus the per-cell cutter boxes (cap faces from the cutter, crosser material). block sliced per cell = the plain Block intersected with each cell box (separate sub-blocks, as Studio will slice it). clip+caps = fallback for non-watertight unions: triangles clipped per cell, caps built from the exact cross-section of the original mesh (the order's literal fallback has no caps).

## Open items the numbers show

- Break 2 body 1 rest pose (spec roll 96.1, lift 0.2): lowest point y 5.037 is 0.29 below ground, allowed 0.20. The geometry two-point rest for that side is roll 96.78, lift 0.435. In the render this shows as the bogie frame corner dug 0.14 deeper than the designed 0.15 sink.
- Feathering: the roof steps at X = +3.70 and X = -4.60 run into slanted roof-panel edges, leaving thin wedges down to 0.002 (acceptable per coordinator).
- 4 unions (Union19/61 in C1, Union84/86 in C2) are not watertight in the export; here they are capped from exact cross-sections, Studio CSG on them is unverified.

## Render limits (by design, do not score them as defects of the split)

- No fx, smoke, sparks, debris, glass shards or sound in these renders: the explosion, torn-edge smoke and topple dust are T3, sounds T4.
- Cycles preview materials approximate Roblox: texture x part colour, roughness 0.7, normal maps dropped, glass alpha 0.35, AgX view transform, sun and sky from scene.py. Roblox lighting, materials and LOD will differ.
- Ground (flat plane at rail level y 5.33), rails, sleepers and ballast are render props, not part of the model; rail heads stand 0.25 proud, so the wheels sit 0.25 into them.
- Cycles CPU, 22 samples + OpenImageDenoise, 1600x900 (Cam_Game 400x225). Cameras are in the B frame of the breaking carriage (intact and exploded use carriage 1); Cam_Side at t=4.0 is widened to centre Z 45, ortho 140.
- Motion details not fixed by the spec: yaw eases like the roll and turns about the vertical line through the rolled body's centre, mirrored with the side; lift eases in with the roll; extra back eases in over the roll.

