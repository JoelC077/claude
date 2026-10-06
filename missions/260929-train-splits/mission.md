# Mission 260929-train-splits
Objective: Each of Joel's 2 carriages tears in half at its own break point (jagged, seamless until it snaps), cut exactly from the live unions in Studio; on the snap a big explosion, the lost part topples and falls behind with the terrain, with made-from-code sounds; 8/10 on multiuse-critic; delivered as Studio scripts, effects, sounds and renders.
Kind: mixed (3D look + Luau + fx + sound) · Profiles: A (3D look), F (fx board), S (sound plan) + exploit-guard gate · Bar: 8 · Cap: 5 passes each
Env: cloud; blender=bpy 5.0.1 headless (Cycles CPU); agents=yes (critic_mode agent); lune 0.10.5; Studio/Blender MCP: none

## Source prompt
prompt.txt + lines.md (2 lines + 22 clarification lines). Facts: refs/train.facts.md. Break design: src/kit/break_spec.py -> break_spec.json (T0).
Superseded: the coupling kit (src/kit/superseded/) after C6.

## Requirements
| id | owner words | requirement | type | source | status | done-when |
|---|---|---|---|---|---|---|
| R1 | "make splits inbetween the individual carriages" / "each carriage will have its own split point" | Each carriage breaks at its own point mid-body (C1 z 86.2, C2 z 153.6); train restructured into Carriage1/2 x FrontHalf/RearHalf | deliverable | L1,C16 | planned | Lune: 2 breaks, every part in exactly one half, gangway in C1.RearHalf |
| R2 | "split in half sometime later in the game" / "carriage1 splits, all of carriage 2 and half carriage one is lost" / "Carriage 2 splitting means only half carriage 2 lost" | Server TrainSplit.SplitAt(train, k): k=1 loses C1 rear half + all attached of C2; k=2 loses C2 rear half; any order | deliverable | L2,C17,C18 | planned | Lune tests of lost sets for 1, 2, 1-then-2, 2-then-1 |
| R3 | "make each split look really good and accurate" | Jagged stepped tear through walls, roof, floor; no seam before the snap; exact CSG from the live parts; torn ends read as torn (smoke/embers) | quality | L2 | planned | critic A1-A7 >= 8 on intact/split/topple renders, final pass agrees |
| R4 | "one problem" / "unioned a lot of shit together ... do you need to no seperate everything" | Only the 10 crossers per carriage are cut (CSG at setup; plain Blocks sliced per cell); all else untouched; checker lists crossers | constraint | C1,C2 | planned | checker on the synthetic train lists exactly the 20 expected crossers |
| R5 | archive "Go." | OBJ export is the geometry source | reference | C3 | done | refs/train.facts.md, break_spec clearance PASS |
| R6 | "Deploy JARVIS" | 10-step mission, independent critics, gates | process | C4 | open | progress.log steps 1-10; ledgers |
| R7 | "Give me photos of the progress along the way" | Photo sheet at each milestone | comms | C5 | open | >= 5 sheets sent |
| R8 | "dont bother with the coupling stuff." | No coupling hardware | constraint | C6 | done | coupling kit moved to superseded/ |
| R9 | "The snap will be driven by windows and walls not being fixed" | The owner's damage system calls SplitAt; kit has no auto trigger (demo trigger for testing only) | context | C7 | planned | README wiring line; demo is attribute-driven |
| R10 | "after the snap" / "the lost part will have to move with terrain" / "yes like i said, it stays still" | Lost part brakes from Speed to terrain speed, then moves with the terrain until it is far behind; train never moves | deliverable | C8,C9,C20 | planned | Lune: drift(t) reaches Speed at V/brake and is linear after; despawn at 700 studs |
| R11 | "I want a big explosion aswell" | Big split explosion (flash, fireball, soot, sparks, debris, glass) + camera shake, phone-budgeted | deliverable | C10 | planned | fx critic >= 8; budget pass |
| R12 | "maybe even an animation where the train sort of topples over." | Lost bodies derail and roll onto their side (break 1: carriage 2 follows) | deliverable | C11 | planned | topple renders; critic |
| R13 | "Sounds: yes." / "Make some if you can and include them if they fit" | Sounds synthesised from code, levelled, mapped to the split timeline, wired in the client | deliverable | C12,C13 | planned | sound validate PASS, files measured, critic >= 8 on the plan |
| R14 | "just 2 carriages" | Scope exactly 2 carriages | constraint | C22 | planned | setup refuses/warns on other counts |
| R15 | "questions:" "1." "2." "3." | - | noise | C14,C15,C19,C21 | noise | - |
| R16 | (earlier) coupling look at the join | superseded by C6 | quality | C6 | superseded | - |
| R*17 | (implied) | Frame-relative: breaks found from each carriage's roof union; works when the train is moved/rotated | derived | L1 | planned | Lune moved + rotated cases pass |
| R*18 | (implied) | Server-authoritative; RemoteEvent server->client only; non-destructive setup (backup + undo) | derived | L2 | planned | guard scan 0 high |
| R*19 | (implied) | Phone budget for fx; sound files to the class standard | derived | C10 | planned | vfx budget + sound analyze PASS |
| R20 | "gifs of the full animation afterwards aswell" | After the final look: animated GIFs of the whole split (intact -> tear -> explosion -> topple -> wreck falling behind) for break 1 and break 2 from wide, roof and inside views; effects shown as timed stand-ins (labelled) | comms | C23 | planned | >= 4 GIFs sent after the 3D final pass |

## Decisions and assumptions
A1 Break points 3.3 studs behind each carriage centre, in the solid pillar between windows 4 and 5 (world z 86.2 / 153.6). Only 10 long pieces per carriage cross it; no seat, window or lamp is cut (clearance check PASS).
A2 Stepped jagged tear, 29 cells: walls within +-0.9 (pillar), roof bites up to 4.8 forward, floor tongues up to 3.6 back; halves meet exactly before the snap.
A3 Cutting in Studio: part:SubtractAsync(cutter boxes) per crosser at setup; plain Blocks sliced per cell; failures reported, never guessed.
A4 Lost part: brakes 12 studs/s^2 from the train's Speed attribute (default 35) until it moves with the terrain (~2.9 s, ~51 studs), then drifts away with it; despawn at 700 studs / 30 s. Riders are carried with it; SplitAt returns them (your rules decide their fate).
A5 Topple: each lost body rolls ~88 deg onto its side in ~1 s with a bounce; break 1: carriage 2 follows 0.35 s later; side random per snap (config can force).
A6 Explosion: big but slapstick (canon tone), built on the fx library (derail_explosion, glass_burst, debris trails) + new split presets; owner decision 2026-09-29 overrides OQ-028 default for this event.
A7 Sounds synthesised (rr-soundsmith), licence-clean; owner uploads and pastes ids into TrainSplitConfig.
A8 Setup never deletes: train cloned to ServerStorage.RR_Backups; cut originals moved there; undo waypoint.
A9 Server moves each lost body's anchored root (welded parts follow; 1 CFrame per body per frame); a LocalScript smooths motion and plays fx/sound/shake (RemoteEvent server->client only).
Q: none open (owner answered Q1-Q3 in C15-C22).

## Spec
Break frame B, cells, motion, topple, events: src/kit/break_spec.json. Structure after setup:
Train/Carriage1/{FrontHalf, RearHalf(+gangway)}, Train/Carriage2/{FrontHalf, RearHalf}, Train/RR_Breaks/Break1..2.
Renders (T1): states intact, break1 t=0.3/1.2/4.0, break2 t=1.2/4.0; cameras in tasks/T1.md.
Scripts (T2): RR_BreakChecker, RR_TrainSplit_Setup, TrainSplit (server), TrainSplitShared, TrainSplitClient, TrainSplitConfig, TrainSplitDemo.
FX (T3): split_explosion, torn_edge_smoke, topple_dust + glass_burst, debris trails. Sound (T4): metal_tear, split_explosion, glass_burst, debris_rain, topple_crash, wreck_scrape.

## Acceptance
3D (A): the tear reads at game distance; no seam visible intact; torn ends look torn, not sliced; nothing floats after the cut; wrecks rest on the ground; A1-A7 >= 8.
FX (F): explosion is the loudest thing in frame from roof and door POVs; phone budget pass; flash-safety pass.
Sound (S): hierarchy boom > tear > crash > debris; phone band energy; timing matches events; validate PASS.
Luau: guard 0 high/critical; Lune suite PASS; setup dry-run report readable; no deprecated APIs.

## Needs owner / placeholders
Studio test of setup (CSG) and runtime; upload the sound files and paste ids; upload nothing else (fx use built-in textures).

## Next action
Spawn T1-T4 makers (wave 2), then pre-flight + critics.
