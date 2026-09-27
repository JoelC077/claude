# Mission 260927-depot-buildings
Objective: Build the Depot (station house) and the Main Hall for the Depot Lobby in Blender, each to 8/10 on multiuse-critic, exported Roblox-ready with every recolourable part separate and named.
Kind: 3d · Profile: A · Bar: 8 (owner correction; see R6/R7) · Cap: 5 passes per building
Env: cloud; blender=bpy-headless (pip bpy 5.0, Cycles); agents=yes; design-critic=not installed

## Source prompt
prompt.txt + lines.md (7 lines + 2 clarifications; ids are cited only in the R-table source column).

## Requirements
| id | owner words | requirement | type | source | status | done-when |
|---|---|---|---|---|---|---|
| R1 | "have a look through this" | Use the Depot Lobby Blueprint (artifact UiWCrrC9g7Zw1firdy6fP2) as the layout source | reference | L1,C1 | open | refs/blueprint.facts.md exists; footprints/positions within 0.5 stud of it |
| R2 | "the two buildings" | Two separate models | deliverable | L2 | open | two build.py + two FBX |
| R3 | "the main hall" | Main Hall building (not in blueprint, see A1) | deliverable | L3 | open | critic overall >= 8, final agrees |
| R4 | "and the depot" | Depot: two-gable stone station house 24x14 at (18,76), front north to yard | deliverable | L3 | open | critic overall >= 8, final agrees |
| R5 | "run through the critic skill /multiuse-critic" | multiuse-critic loop, profile A, per building | process | L4 | open | ledger.md per CRIT |
| R6 | "rating of 6/10" | bar 6 | quality | L4 | superseded | - |
| R7 | "actually 8/10" | Bar 8 every criterion | quality | C2 | open | every A1-A7 >= 8 with final pass |
| R8 | "make it in blender" | Built in Blender from one build.py per building (working source in src/<building>/) | tool | L5 | open | build.py rebuilds from empty scene in its own file |
| R9 | "watch it go up in real time" | Live build if Blender MCP; else milestone render strip | comms | L5 | open | 4 milestone frames per building posted at step 5 (fallback) |
| R10 | "as many parts seperate as possible" | Every editable part its own named object | editability | L6 | open | parts.csv lists >= 1 row per wall/roof/trim/window/door; no merged meshes |
| R11 | "edit them later if they need recolouring" | Recolour = change one palette cell / one Color per group | editability | L6 | open | studio_setup.lua recolour table by material group; TextureID empty, so changing a GROUPS Color visibly recolours those parts |
| R*12 | (implied) | Roblox scale in studs, reimport verified | derived | L6 | open | reimport reports studs (not 3.57x) |
| R*13 | (implied, technical) | Mobile perf budget for a small hub | derived | L6 | open | tris per building <= 20k total |
| R14 | "Thank you" | - | noise | L7 | noise | - |

## Decisions and assumptions
A1 "Main hall" is not in the blueprint. Default: single-storey stone hall fronting the join-queue platform (20,5; 20x10) as its backdrop, ~24x12 studs, same stonework as the depot. (Q1)
A2 Heights: eaves 14 studs, ridge 22; doors 7x9; facade + open doorway, no interiors. (Q2)
A3 Live view: no Blender MCP in this session -> milestone renders (shell, roof, details, dressing) from the fixed cameras. With an MCP: new file rr-depot-buildings.blend / collection RR_depot-buildings, never the open file.
A4 Player view (rr-profile): 3P eye 9.5, FOV 70, lobby walk-around, static world; spawn (30,60) faces north.
Q1 Main hall: where/what? default A1 - pending
Q2 Interiors: enterable or facade-only? default facade + open depot doorway - pending
Blocking: none (depot starts immediately; hall starts on A1 default).

## Spec
### Depot
Footprint 24x14 at plan (18,76), long side facing north; two gables; stone walls, timber gable boards, slate roof, iron gutters; moss/ivy heaviest near base (blueprint "heaviest near building").
Palette cells: stone #9a9384 / #7d776b, mortar #cabb8a, timber #8f5a2a/#b87a3d, slate #4a4f57, iron #2b2f36, moss #6d7d43.
### Main Hall
~24x12 behind the platform at north edge, single storey, same kit (T0) for coherence; main facade faces spawn.
Cameras (both, never moved): Cam_POV_3P from spawn (30,60) toward each building at eye 9.5; Cam_Game (3/4, 400x225); Cam_34, Cam_Side, Cam_EndE, Cam_EndW, Cam_Door closeup; 5-stud avatars at doors.

## Acceptance
Profile A list from mission-template.md, plus: footprint/position match R1; parts.csv; recolour table (colour via Color3, not texture); R9 strip.
One CRIT (critique-buildings/) with a per-building score block; both buildings on one contact sheet.

## Needs owner / placeholders
Fence-panel and station footprints measured in Studio (blueprint note) - may nudge positions.

## Next action
python3 <me>/scripts/plan.py check <M>/plan.json --mission <M>/mission.md
