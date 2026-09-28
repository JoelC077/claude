# Asset register

Every known asset with its real status. Status words in the value: approved (owner approved), confirmed (seen working in the owner's Studio), delivered (handed over, not yet seen in Studio), self-assessed (built to the bar but not independently certified), design (drawn, not built), rejected. Update with `bible.py add-fact assets.<group>.<name> ... --replace`.

## approved · Approved by the owner
- `assets.approved.diesel_23` = `approved` | the approved diesel locomotive "23" that defines house style; location, files and specs not in reach (OQ-020) | src: RUB | canon

## train · Train kit (delivered via chat builders; files on the owner's Mac: Desktop/Claude stuff/roblox-models/out/)
- `assets.train.roof_ladder` = `confirmed` | mesh GLB + OBJ, 2.3 x 12.7 x 1.8; set the ironwork standard | src: WR | measured
- `assets.train.sandwich_bar` = `confirmed` | builder, 74 parts, TakeSandwich ProximityPrompt, 3.2 x 4.2 x 1.0, right of the coach doorway | src: WR | measured
- `assets.train.power_box` = `confirmed` | builder, 147 parts, clickable door, terminals with Side/WireColor attributes, 6 x 7 x 2, left of the coach doorway | src: WR | measured
- `assets.train.coach_doors_v3` = `delivered` | builder, 12 parts, 5.1 x 7.8, HingePivot per leaf; not placed (opening undecided, OQ-022) | src: WR | measured
- `assets.train.sandwich` = `delivered` | mesh 1.25 x 0.6 x 1.25; not yet seen | src: WR | measured
- `assets.train.toolbox` = `delivered` | mesh 3.1 x 1.8 x 1.6; not yet seen | src: WR | measured
- `assets.train.cab_buttons` = `delivered` | builder + 4 icon PNGs, 0.56 wide, Cap part recolours | src: WR | measured
- `assets.train.cab_desks` = `delivered` | measure-and-replace builder; desks still looked wooden on 22 Sep | src: WR | measured
- `assets.train.coach_doors_v1` = `rejected` | sliding, auto-open | src: WR | measured
- `assets.train.coach_doors_v2` = `rejected` | wooden, cream frame | src: WR | measured

## systems · Built game systems (status per the owner's boards)
- `assets.systems.segment_streamer` = `confirmed` | stationary train + streamed segments, done 14 Sep | src: WR | measured
- `assets.systems.junction_lever` = `in progress` | as of 22 Sep | src: WR | measured
- `assets.systems.end_segment` = `confirmed` | station arrival + results + back to lobby, done 26-27 Sep | src: R2A | measured
- `assets.systems.hud_notifications` = `in progress` | working on it 27 Sep | src: R2A | measured
- `assets.systems.cab_speed_screen` = `confirmed` | speed screen already works | src: WR | measured

## missions · Mission outputs (repo missions/)
- `assets.missions.depot_building` = `self-assessed` | Depot 24 x 14, 290 named parts, 3.8k tris, FBX plain + atlas, studio_setup.lua; not independently certified; Studio test pending | src: DEPM | measured
- `assets.missions.main_hall` = `self-assessed` | Main Hall 34 x 14, 347 named parts, 4.3k tris; placement assumed (OQ-015) | src: DEPM | measured
- `assets.missions.hud_package` = `self-assessed` | heritage-brass ticket HUD, ScreenGui builder + controller + demo + icon sheet; icons need upload; Studio test pending | src: HUDM | measured

## designs · Designs and drawings (not built)
- `assets.designs.depot_lobby_blueprint` = `design` | Rev 01 layout + paving plan | src: BP | measured
- `assets.designs.ticket_notifications` = `design` | HUD prototype the owner likes (ticket frame) | src: TN | measured
- `assets.designs.supply_terminal_v4` = `design` | final boards incl. animation | src: ST | measured
- `assets.designs.cab_interior` = `design` | dashboard, Depotron, wire panel, heights, plan | src: CI | measured
- `assets.designs.lever_panel` = `design` | rough UI sketch to refine | src: JLP | measured
- `assets.designs.create_match` = `design` | two accent reads | src: DTU | measured
- `assets.designs.line1_drawings` = `design` | 18 prefab sheets, 23 figures | src: DS | measured
- `assets.designs.junction_rev_b` = `design` | left-branch junction, recipe-exact views | src: LBJ, JTV | measured

## marketing · Marketing assets
- `assets.marketing.thumb_labels_used` = `PULL IT?, WRONG LEVER, BANK IT OR RISK IT, the explosion, the crew; WHICH WAY?!, GRAB IT!, NO BRAKES, NIGHT RUN; MINE!, NOT THAT!, UH OH!` | never re-tread these | src: THS | canon
