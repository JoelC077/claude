# Mission 260927-depot-buildings
Objective: Build the Depot (station house) and the Main Hall for the Depot Lobby in Blender, each to 8/10 on multiuse-critic, exported Roblox-ready (FBX per building) with every recolourable part separate and named.
Kind: 3d · Profile: A · Bar: 8 (owner said 6/10; clarification C2 = 8) · Cap: 5 passes (one CRIT for both buildings)
Env: cloud; blender=bpy-headless (bpy 5.0.1, Cycles); agents=yes; design-critic=not installed; owner=away (no answers this run)

## Source prompt
prompt.txt + lines.md (7 lines + 2 clarifications).

## Requirements
| id | owner words | requirement | type | source | status | done-when |
|---|---|---|---|---|---|---|
| R1 | "have a look through this" | Use the Depot Lobby Blueprint (artifact UiWCrrC9g7Zw1firdy6fP2) as layout source | reference | L1,C1 | verified | refs/blueprint.facts.md exists; depot footprint 24x14 at (18,76) within 0.5 stud |
| R2 | "the two buildings" | Two separate models | deliverable | L2 | done | two build.py + two FBX |
| R3 | "the main hall" | Main Hall (not in blueprint, see A1) | deliverable | L3 | done | critic overall >= 8, final agrees |
| R4 | "and the depot" | Depot: two-gable stone station house 24x14, front north to yard | deliverable | L3 | done | critic overall >= 8, final agrees |
| R5 | "run through the critic skill /multiuse-critic" | multiuse-critic loop, profile A, both buildings | process | L4 | fallback | critique-buildings/ledger.md |
| R6 | "rating of 6/10" | bar 6 | quality | L4 | superseded | - |
| R7 | "The target is 8/10, not 6" | Bar 8 every criterion | quality | C2 | fallback | every A1-A7 >= 8 per building with final pass |
| R8 | "make it in blender" | Built in Blender from one build.py per building (src/<building>/) | tool | L5 | verified | build.py rebuilds from empty scene |
| R9 | "watch it go up in real time" | Live build needs Blender MCP (absent) -> numbered milestone frames + stitched GIF/MP4 | comms | L5 | fallback | >= 4 milestone frames per building + buildup.gif |
| R10 | "as many parts seperate as possible" | Every editable part its own named object | editability | L6 | verified | parts.csv >= 1 row per wall/roof/trim/window/door; no merged meshes |
| R11 | "edit them later if they need recolouring" | Recolour by material group (one palette cell / one Color3 per group) | editability | L6 | done | studio_setup.lua recolour table by group |
| R*12 | (implied) | Roblox scale in studs, reimport verified | derived | L6 | verified | reimport reports studs (not 3.57x) |
| R*13 | (implied, technical) | Mobile perf budget for a small hub | derived | L6 | verified | <= 10k tris per MeshPart, <= 20k per building |
| R14 | "Thank you" | - | noise | L7 | noise | - |

## Decisions and assumptions
A1 "Main hall" is not on the blueprint (default, FLAGGED): lobby anchor building north of the join-queue platform, facing spawn. v1 28x12; after pass 1 (hall read as a copy of the depot) enlarged to 34x14 at plan (13,-16), eaves 16, ridge 26, porch gable 31 + cupola.
A2 Heights: depot eaves 14, ridge 22 studs; doors 7 wide x 9 tall min; facades with recessed open doorways + dark interior plane, no furnished interiors.
A3 Live view: no Blender MCP -> build.py renders numbered milestone frames (shell, roof, details, dressing) from fixed cameras; stitched to progress/buildup.gif.
A4 Player view (rr-profile): 3P eye 9.5, FOV 70, lobby walk-around, static; spawn (30,60) faces north.
A5 FBX export carries palette-atlas UVs (owner clarification asked for "palette atlas") AND studio_setup.lua sets Color3 per group; conflict with roblox-export.md noted in SKILL-FRICTION.
Q1 Main hall where/what? default A1 - no answer (owner away), default taken
Q2 Interiors? default facade + open doorway - no answer, default taken
Q3 Signage (station name board)? default: plain name-board blank panel only, no invented text - no answer, default taken
Blocking: none.

## Spec
### Shared kit (T0)
Palette cells (index: hex): 0 stone #9a9384, 1 stone dark #7d776b, 2 mortar/sill #cabb8a, 3 timber dark #8f5a2a, 4 timber light #b87a3d, 5 slate roof #4a4f57, 6 iron #2b2f36, 7 moss #6d7d43, 8 glass/interior dark #1f2a33, 9 window glow #e8c46a, 10 brass #b08a3e, 11 paving #f7f3e6, 12 soot #3a3f48, 13 red-oxide door #b1502b, 14 gravel #b7a17a, 15 chimney brick #8a4b36.
Naming: <Bldg>_<Part>_<Mat>_<nn> (Depot_WallN_Stone_01). One mesh object per part; collections Depot / Hall / Stage (ground, avatars, cams).
World: 1 BU = 1 stud; plan (x,y) -> Blender (x, -y), z up; ground slab under each at z=0.
Modules: wall panel w/ plinth + quoin corners, gable wall, pitched roof slab with ridge cap + eave trim, chimney, window (frame, sill, lintel, glass, mullions), door (frame, leaf/opening, step), gutters + downpipes, lamp, moss clumps, crates/drums (depot dressing).
### Depot
Footprint 24x14 at plan (18,76); long side faces north (yard/display track); two gables (twin cross-gables on the north facade). Stone walls, timber gable boards, slate roof, iron gutters, moss/ivy heaviest near base, a few crates/drums.
### Main Hall
28x12 at plan (16,-14), front faces south toward the join-queue platform/spawn; single storey, central entrance under a gable, same kit.
Cameras (per building, never moved): Cam_POV_3P (from spawn-side approach, eye 9.5), Cam_Game (3/4 at 400x225), Cam_34, Cam_Side, Cam_Door closeup. 5-stud avatar stand-ins at doors.

## Acceptance
- A1/A5 clear focal point at game distance (400x225: key features >= 5 px)
- A2 5-stud avatars; doors >= 7x9; steps/rails at Roblox scale
- A3 <= 10k tris per MeshPart (cap 20k); no hidden interior faces; backfaces clean per camera
- A4 one 256px palette atlas, 32px cells, verify_palette passes; weathering from palette cells
- A6 Risky Rails house style; A7 no floating parts, trims meet, pivots sane
- Every editable part separately named; parts.csv; reimport in studs; depot footprint matches R1
- R9: numbered milestone frames + buildup.gif
One CRIT: critique-buildings/, per-building score block, both on one contact sheet.

## Needs owner / placeholders
- Main hall placement/size (A1) is a default. Station name board is blank (no invented text).
- Fence/station footprints to be measured in Studio (blueprint note).

## Status notes
R5/R7 fallback: every critic pass was SELF-ASSESSED (no Agent tool in this session), so 8/10 is not independently certified.
R9 fallback: no Blender MCP; 8 numbered stage frames + progress/buildup.gif (no ffmpeg, so no MP4).

## Next action
Owner: review; optionally re-run an independent fresh critic on critique-buildings/pass-4 (critic_kit build --kind final).
