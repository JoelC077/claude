# Look-dev board: steam_chimney, smoke_chimney, sparks_brake, coal_dust, grassland.day, grassland.dusk, grassland.night (2026-09-28)

Presets from /home/user/claude/rr-vfx-lighting/presets. Tiles show the player's views (POV composites: particles over the lit plate); strips on closeups.png are construction views for shape and timing only.

## Looks

Cameras: roof3p = coach B roof, eye 9.5 (tech.camera.eye_3p); door1p = leaning out of coach A's doorway, eye 4.5 (tech.camera.eye_1p); cab1p = loco cab facing the firebox, eye 12.0 above rail (tech.camera.cab_view); coach1p = inside coach A facing the power box. FOV 70.0; phone renders at 844x390 (tech.ui_platform.phone). Stand envelope: gauge 8, body 17.4 wide, floor 5, roof 14 (tech.units.*, OQ-030); stand-in train: navy, cream band and interiors, hazard-yellow roof rails (style.form.rails); livery open (OQ-025).

| look | cam | sun elev | luma | clip/crush % (train) | train vs world | hazard vs world | ground (sat) | sky | spawn-edge fog | bands |
|---|---|---|---|---|---|---|---|---|---|---|
| grassland.day | roof3p | 38.8 | 149.4 | 0.0/0.0 (0.0) | 3.12:1 | 1.26:1 | #93A660 (0.28) | #ACBEAE | 0.956 at 2048 | none |
| grassland.day phone | roof3p | 38.8 | 153.0 | 0.0/0.0 (0.0) | 3.02:1 | 1.24:1 | #94A762 (0.28) | #ADBEAE | 0.956 at 2048 | none |
| grassland.day@door1p | door1p | 38.8 | 116.1 | 0.0/6.01 (13.75) | 2.08:1 | None:1 | #738A44 (0.34) | #A9BDAF | 0.956 at 2048 | none |
| grassland.dusk | roof3p | 1.7 | 77.4 | 0.0/0.0 (0.0) | 2.02:1 | 1.86:1 | #5C583E (0.19) | #675A60 | 0.968 at 2048 | none |
| grassland.dusk phone | roof3p | 1.7 | 80.8 | 0.0/0.0 (0.0) | 2.08:1 | 1.79:1 | #5F5A3F (0.2) | #685B60 | 0.968 at 2048 | none |
| grassland.dusk@door1p | door1p | 1.7 | 75.2 | 0.0/5.37 (12.28) | 1.04:1 | None:1 | #4F4F31 (0.24) | #65585F | 0.968 at 2048 | none |
| grassland.night | roof3p | -47.8 (moon) | 26.7 | 0.0/0.56 (0.43) | 1.48:1 | 1.86:1 | #2F4437 (0.18) | #01030F | 0.969 at 2048 | none |
| grassland.night phone | roof3p | -47.8 (moon) | 28.2 | 0.0/0.45 (0.36) | 1.45:1 | 1.92:1 | #2F4437 (0.18) | #010410 | 0.969 at 2048 | none |
| grassland.night@door1p | door1p | -47.8 (moon) | 42.9 | 0.0/8.61 (14.62) | 1.08:1 | None:1 | #344B38 (0.18) | #00030E | 0.969 at 2048 | none |
| grassland.day@cab1p | cab1p | 38.8 | 16.6 | 0.95/49.22 (51.52) | 5.4:1 | None:1 | #7B914A (0.32) | None | 0.956 at 2048 | none |

Checks against canon: spawn-edge fog >= 0.9 hides the streamer's spawn edge (tech.lighting.atmosphere, tech.streaming.window); ground saturation <= 0.45 (style.material.ground_value); bands = frame and sky means tested against the Dead Rails sepia and Land or Die blue-sky bands (style.dont.*); contrast = relative luminance ratio in the same frame.

Flags (maker heuristics, not canon: train vs world under 2:1 fades on a dim phone; crush over 5% loses shape):
- grassland.day@door1p (door1p): crush 6.01% > 5% (train 13.75%)
- grassland.dusk@door1p (door1p): train vs world 1.04:1 < 2:1; crush 5.37% > 5% (train 12.28%)
- grassland.night (roof3p): train vs world 1.48:1 < 2:1
- grassland.night phone (roof3p): train vs world 1.45:1 < 2:1
- grassland.night@door1p (door1p): train vs world 1.08:1 < 2:1; crush 8.61% > 5% (train 14.62%)
- grassland.day@cab1p (cab1p): crush 49.22% > 5% (train 51.52%)

Limits: Previews are approximations, not Roblox: Cycles + a numpy post (filmic curve, Atmosphere fog from depth, bloom, sun rays, ColorCorrection). Skybox, Future light falloff and Roblox tone mapping are not modelled; phone variants assume no shadows and no Bloom/SunRays (tech.lighting.post_low_quality). The train is a stand-in (livery open, OQ-025). Studio test pending (owner).

## Effects

Side strips: steady state at Speed 35.0 (gameplay.speed.normal) on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar (tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.

| preset | kind | priority | anchor | start | live phone / pc (budget formula, full rate) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|---|
| steam_chimney | loop | 2 | Chimney | on | 40 / 58 | 38/38/38 | 3.66 | av.vfx.speed_link, gameplay.speed.drives |
| smoke_chimney | loop | 3 | Chimney | on | 10 / 21 | 15/15/15 | 2.61 | av.vfx.speed_link |
| sparks_brake | loop | 2 | BrakeShoe | off | 50 / 72 | 34/34/34 | 23.13 | gameplay.run.brake_formula, gameplay.crisis.pressure |
| coal_dust | burst | 2 | Firebox | event | 15 / 20 | 20/20/11/20 | 17.78 | gameplay.crisis.firebox, gameplay.fuel.shovel_pct |

POV composites (particles over the lookdev plate from the same camera; loops at steady state, Speed = gameplay.speed.fast; bursts fire after the loops warm up). Per preset: visible / live, hidden by the train or ground, off-screen, share of the screen, luma change over its own pixels:

| POV | look | cam | tier | res | t s | overdraw max/p95 | screen | per preset |
|---|---|---|---|---|---|---|---|---|
| pov_grassland.day_roof3p | grassland.day | roof3p | pc | 768x432 | 6.8 | 29/18 | 4.3% | steam_chimney 51/51, hid 0, off 0, 2.86%, Δluma -8.2; smoke_chimney 17/18, hid 0, off 1, 3.74%, Δluma -9.9; sparks_brake 0/54, hid 54, off 0, 0.00% |
| pov_grassland.day_roof3p.phone | grassland.day | roof3p | phone | 844x390 | 6.8 | 22/15 | 2.1% | steam_chimney 37/37, hid 0, off 0, 1.68%, Δluma +2.7; smoke_chimney 9/9, hid 0, off 0, 1.59%, Δluma -2.7; sparks_brake 0/37, hid 37, off 0, 0.00% |
| pov_grassland.day_door1p | grassland.day | door1p | pc | 768x432 | 6.8 | 3/3 | 0.4% | steam_chimney 0/51, hid 35, off 16, 0.36%, Δluma +13.8; smoke_chimney 0/18, hid 10, off 8, 0.11%, Δluma +20.3; sparks_brake 9/54, hid 45, off 0, 0.01%, Δluma +25.3 |
| pov_grassland.day_cab1p | grassland.day | cab1p | pc | 768x432 | 6.8 | 0/0 | 0.0% | steam_chimney 0/51, hid 0, off 51, 0.00%; smoke_chimney 0/18, hid 0, off 18, 0.00%; sparks_brake 0/54, hid 53, off 1, 0.00% |
| pov_grassland.dusk_roof3p | grassland.dusk | roof3p | pc | 768x432 | 6.8 | 29/18 | 4.3% | steam_chimney 51/51, hid 0, off 0, 2.86%, Δluma -19.1; smoke_chimney 17/18, hid 0, off 1, 3.74%, Δluma -16.1; sparks_brake 0/54, hid 54, off 0, 0.00%; headlamp (light/beam) |
| pov_grassland.dusk_roof3p.phone | grassland.dusk | roof3p | phone | 844x390 | 6.8 | 22/15 | 2.1% | steam_chimney 37/37, hid 0, off 0, 1.68%, Δluma -15.6; smoke_chimney 9/9, hid 0, off 0, 1.59%, Δluma -16.2; sparks_brake 0/37, hid 37, off 0, 0.00%; headlamp (light/beam) |
| pov_grassland.dusk_door1p | grassland.dusk | door1p | pc | 768x432 | 6.8 | 3/3 | 0.4% | steam_chimney 0/51, hid 35, off 16, 0.36%, Δluma -16.4; smoke_chimney 0/18, hid 10, off 8, 0.11%, Δluma -27.9; sparks_brake 9/54, hid 45, off 0, 0.01%, Δluma +24.4; headlamp (light/beam) |
| pov_grassland.night_roof3p | grassland.night | roof3p | pc | 768x432 | 6.8 | 29/18 | 4.3% | steam_chimney 51/51, hid 0, off 0, 2.86%, Δluma +9.5; smoke_chimney 17/18, hid 0, off 1, 3.74%, Δluma +6.6; sparks_brake 0/54, hid 54, off 0, 0.00%; headlamp (light/beam) |
| pov_grassland.night_roof3p.phone | grassland.night | roof3p | phone | 844x390 | 6.8 | 22/15 | 2.1% | steam_chimney 37/37, hid 0, off 0, 1.68%, Δluma +13.5; smoke_chimney 9/9, hid 0, off 0, 1.59%, Δluma +11.1; sparks_brake 0/37, hid 37, off 0, 0.00%; headlamp (light/beam) |
| pov_grassland.night_door1p | grassland.night | door1p | pc | 768x432 | 6.8 | 3/3 | 0.4% | steam_chimney 0/51, hid 35, off 16, 0.36%, Δluma -15.4; smoke_chimney 0/18, hid 10, off 8, 0.11%, Δluma -26.1; sparks_brake 9/54, hid 45, off 0, 0.01%, Δluma +23.4; headlamp (light/beam) |
| pov_coal_dust | grassland.day | cab1p | pc | 768x432 | 7.2 | 10/8 | 1.7% | steam_chimney 0/51, hid 0, off 51, 0.00%; smoke_chimney 0/18, hid 0, off 18, 0.00%; sparks_brake 2/52, hid 47, off 3, 0.02%, Δluma +28.0; coal_dust 20/20, hid 0, off 0, 1.71%, Δluma -4.8 |

Visibility (warnings are for the maker to fix before the critic; hidden counts are facts):
- steam_chimney: faint in pov_grassland.day_roof3p (luma change -8.2 over its pixels; heuristic: under 15 reads weak)
- steam_chimney: faint in pov_grassland.day_roof3p.phone (luma change +2.7 over its pixels; heuristic: under 15 reads weak)
- steam_chimney: 35 of 51 hidden by the train or ground in pov_grassland.day_door1p
- steam_chimney: faint in pov_grassland.day_door1p (luma change +13.8 over its pixels; heuristic: under 15 reads weak)
- steam_chimney: 35 of 51 hidden by the train or ground in pov_grassland.dusk_door1p
- steam_chimney: faint in pov_grassland.night_roof3p (luma change +9.5 over its pixels; heuristic: under 15 reads weak)
- steam_chimney: faint in pov_grassland.night_roof3p.phone (luma change +13.5 over its pixels; heuristic: under 15 reads weak)
- steam_chimney: 35 of 51 hidden by the train or ground in pov_grassland.night_door1p
- smoke_chimney: faint in pov_grassland.day_roof3p (luma change -9.9 over its pixels; heuristic: under 15 reads weak)
- smoke_chimney: faint in pov_grassland.day_roof3p.phone (luma change -2.7 over its pixels; heuristic: under 15 reads weak)
- smoke_chimney: 10 of 18 hidden by the train or ground in pov_grassland.day_door1p
- smoke_chimney: 10 of 18 hidden by the train or ground in pov_grassland.dusk_door1p
- smoke_chimney: faint in pov_grassland.night_roof3p (luma change +6.6 over its pixels; heuristic: under 15 reads weak)
- smoke_chimney: faint in pov_grassland.night_roof3p.phone (luma change +11.1 over its pixels; heuristic: under 15 reads weak)
- smoke_chimney: 10 of 18 hidden by the train or ground in pov_grassland.night_door1p
- WARN sparks_brake: under 0.1% of the screen in every POV (best pov_coal_dust: 2 of 52 visible, 0.02%): players may never see it (references/presets.md, Visible from the players' views)
- sparks_brake: 54 of 54 hidden by the train or ground in pov_grassland.day_roof3p
- sparks_brake: 37 of 37 hidden by the train or ground in pov_grassland.day_roof3p.phone
- sparks_brake: 45 of 54 hidden by the train or ground in pov_grassland.day_door1p
- sparks_brake: 53 of 54 hidden by the train or ground in pov_grassland.day_cab1p
- sparks_brake: 54 of 54 hidden by the train or ground in pov_grassland.dusk_roof3p
- sparks_brake: 37 of 37 hidden by the train or ground in pov_grassland.dusk_roof3p.phone
- sparks_brake: 45 of 54 hidden by the train or ground in pov_grassland.dusk_door1p
- sparks_brake: 54 of 54 hidden by the train or ground in pov_grassland.night_roof3p
- sparks_brake: 37 of 37 hidden by the train or ground in pov_grassland.night_roof3p.phone
- sparks_brake: 45 of 54 hidden by the train or ground in pov_grassland.night_door1p
- sparks_brake: 47 of 52 hidden by the train or ground in pov_coal_dust
- coal_dust: faint in pov_coal_dust (luma change -4.8 over its pixels; heuristic: under 15 reads weak)

Budgets (assumed (OQ-029 default A): not canon until the owner decides; re-measure at the alpha live check (tech.streaming.live_check)); sets holding a pack preset:
- phone cruise: steady 54, peak 54, emitters 3, fill 3183 stud^2, lights 3 -> within
- phone crisis_stack: steady 191, peak 206, emitters 10, fill 3557 stud^2, lights 7 -> within
- phone night_tunnel: steady 105, peak 105, emitters 5, fill 3204 stud^2, lights 5 -> within
- phone storm_crisis: steady 384, peak 384, emitters 6, fill 3573 stud^2, lights 5 -> within
- phone boiler_fail: steady 14, peak 68, emitters 5, fill 2916 stud^2, lights 4 -> within
- phone derail: steady 54, peak 122, emitters 7, fill 5073 stud^2, lights 4 -> within
- phone windows: steady 90, peak 113, emitters 6, fill 3521 stud^2, lights 3 -> within
- phone arrival_brake: steady 105, peak 105, emitters 5, fill 3204 stud^2, lights 4 -> within
- phone pressure_brake: steady 141, peak 156, emitters 8, fill 3545 stud^2, lights 5 -> within
- pc cruise: steady 83, peak 83, emitters 3, fill 4762 stud^2, lights 3 -> within
- pc crisis_stack: steady 242, peak 262, emitters 10, fill 5156 stud^2, lights 7 -> within
- pc night_tunnel: steady 155, peak 155, emitters 5, fill 4793 stud^2, lights 5 -> within
- pc storm_crisis: steady 665, peak 665, emitters 6, fill 5215 stud^2, lights 5 -> within
- pc boiler_fail: steady 26, peak 80, emitters 5, fill 3294 stud^2, lights 4 -> within
- pc derail: steady 83, peak 151, emitters 7, fill 6653 stud^2, lights 4 -> within
- pc windows: steady 119, peak 142, emitters 6, fill 5101 stud^2, lights 3 -> within
- pc arrival_brake: steady 155, peak 155, emitters 5, fill 4793 stud^2, lights 4 -> within
- pc pressure_brake: steady 191, peak 211, emitters 8, fill 5144 stud^2, lights 5 -> within

Limits: Effects are simulated from the preset data with Roblox ParticleEmitter rules; textures are procedural stand-ins for the built-ins; particles are not lit by the scene beyond a LightInfluence factor; lights show as glow dots only; drift = Workspace.GlobalWind at train speed. Studio test pending (owner).
