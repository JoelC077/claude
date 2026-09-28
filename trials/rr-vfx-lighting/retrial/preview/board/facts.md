# Look-dev board: steam_chimney, smoke_chimney, sparks_brake, coal_dust, grassland.day, grassland.dusk, grassland.night (2026-09-28)

Presets from /home/user/claude/trials/rr-vfx-lighting/retrial/fx. Tiles show the player's views (POV composites: particles over the lit plate); strips on closeups.png are construction views for shape and timing only.

## Looks

Cameras: roof3p = coach B roof, eye 9.5 (tech.camera.eye_3p); door1p = leaning out of coach A's doorway, eye 4.5 (tech.camera.eye_1p); cab1p = loco cab facing the firebox, eye 12.0 above rail (tech.camera.cab_view); coach1p = inside coach A facing the power box. FOV 70.0; phone renders at 844x390 (tech.ui_platform.phone). Stand envelope: gauge 8, body 17.4 wide, floor 5, roof 14 (tech.units.*, OQ-030); stand-in train: navy, cream band and interiors, hazard-yellow roof rails (style.form.rails); livery open (OQ-025).

| look | cam | sun elev | luma | clip/crush % (train) | train vs world | hazard vs world | ground (sat) | sky | spawn-edge fog | bands |
|---|---|---|---|---|---|---|---|---|---|---|
| grassland.day | roof3p | 38.8 | 149.4 | 0.0/0.0 (0.0) | 3.25:1 | 1.26:1 | #93A660 (0.28) | #ACBEAE | 0.956 at 2048 | none |
| grassland.day phone | roof3p | 38.8 | 152.9 | 0.0/0.0 (0.0) | 3.18:1 | 1.24:1 | #94A761 (0.28) | #ADBEAE | 0.956 at 2048 | none |
| grassland.day@door1p | door1p | 38.8 | 114.3 | 0.0/4.58 (10.5) | 2.04:1 | None:1 | #728942 (0.35) | #AABDAF | 0.956 at 2048 | none |
| grassland.dusk | roof3p | 1.7 | 84.5 | 0.0/0.0 (0.0) | 2.28:1 | 1.98:1 | #6C6849 (0.2) | #685A60 | 0.968 at 2048 | none |
| grassland.dusk phone | roof3p | 1.7 | 88.2 | 0.0/0.0 (0.0) | 2.37:1 | 1.87:1 | #6F6A49 (0.2) | #685B60 | 0.968 at 2048 | none |
| grassland.dusk@door1p | door1p | 1.7 | 85.1 | 0.0/0.02 (0.04) | 1.11:1 | None:1 | #62613C (0.24) | #66595F | 0.968 at 2048 | none |
| grassland.night | roof3p | -47.8 (moon) | 26.6 | 0.0/0.56 (0.42) | 1.51:1 | 1.86:1 | #2F4437 (0.18) | #01030F | 0.969 at 2048 | none |
| grassland.night phone | roof3p | -47.8 (moon) | 28.0 | 0.0/0.45 (0.34) | 1.49:1 | 1.91:1 | #2F4437 (0.18) | #010410 | 0.969 at 2048 | none |
| grassland.night@door1p | door1p | -47.8 (moon) | 42.7 | 0.0/6.38 (11.47) | 1.1:1 | None:1 | #344B38 (0.18) | #00030E | 0.969 at 2048 | none |
| grassland.day@cab1p | cab1p | 38.8 | 65.5 | 0.95/27.16 (27.99) | 3.45:1 | None:1 | #8CA158 (0.3) | None | 0.956 at 2048 | none |

Checks against canon: spawn-edge fog >= 0.9 hides the streamer's spawn edge (tech.lighting.atmosphere, tech.streaming.window); ground saturation <= 0.45 (style.material.ground_value); bands = frame and sky means tested against the Dead Rails sepia and Land or Die blue-sky bands (style.dont.*); contrast = relative luminance ratio in the same frame.

Flags (maker heuristics, not canon: train vs world under 2:1 fades on a dim phone; crush over 5% loses shape):
- grassland.dusk@door1p (door1p): train vs world 1.11:1 < 2:1
- grassland.night (roof3p): train vs world 1.51:1 < 2:1
- grassland.night phone (roof3p): train vs world 1.49:1 < 2:1
- grassland.night@door1p (door1p): train vs world 1.1:1 < 2:1; crush 6.38% > 5% (train 11.47%)
- grassland.day@cab1p (cab1p): crush 27.16% > 5% (train 27.99%)

Limits: Previews are approximations, not Roblox: Cycles + a numpy post (filmic curve, Atmosphere fog from depth, bloom, sun rays, ColorCorrection). Skybox, Future light falloff and Roblox tone mapping are not modelled; phone variants assume no shadows and no Bloom/SunRays (tech.lighting.post_low_quality). The train is a stand-in (livery open, OQ-025). Studio test pending (owner).

## Effects

Side strips: steady state at Speed 35.0 (gameplay.speed.normal) on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar (tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.

| preset | kind | priority | anchor | start | live phone / pc (budget formula, full rate) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|---|
| steam_chimney | loop | 2 | Chimney | on | 40 / 58 | 38/38/38 | 3.66 | av.vfx.speed_link, gameplay.speed.drives |
| smoke_chimney | loop | 3 | Chimney | on | 10 / 21 | 15/15/15 | 2.61 | av.vfx.speed_link |
| sparks_brake | loop | 2 | BrakeShoe | off | 90 / 128 | 68/68/68 | 16.0 | gameplay.run.brake_formula, gameplay.crisis.pressure |
| coal_dust | burst | 2 | Firebox | event | 15 / 20 | 20/20/11/20 | 17.78 | gameplay.crisis.firebox, gameplay.fuel.shovel_pct |

POV composites (particles over the lookdev plate from the same camera; loops at steady state, Speed = gameplay.speed.fast; bursts fire after the loops warm up). Per preset: visible / live, hidden by the train or ground, off-screen, share of the screen, mean and peak (90th percentile) luma change over its own pixels:

| POV | look | cam | tier | res | t s | overdraw max/p95 | screen | per preset |
|---|---|---|---|---|---|---|---|---|
| pov_grassland.day_roof3p | grassland.day | roof3p | pc | 768x432 | 6.8 | 30/19 | 3.7% | steam_chimney 50/50, hid 0, off 0, 1.74%, Δluma +3.2 peak 16; smoke_chimney 16/16, hid 0, off 0, 3.25%, Δluma -5.5 peak 15; sparks_brake 3/92, hid 89, off 0, 0.00%, Δluma +9.0 peak 9 |
| pov_grassland.day_roof3p.phone | grassland.day | roof3p | phone | 844x390 | 6.8 | 21/14 | 1.8% | steam_chimney 34/34, hid 0, off 0, 1.22%, Δluma +3.0 peak 24; smoke_chimney 9/10, hid 0, off 1, 1.36%, Δluma -5.9 peak 20; sparks_brake 1/61, hid 60, off 0, 0.00%, Δluma +9.5 peak 13 |
| pov_grassland.day_door1p | grassland.day | door1p | pc | 768x432 | 6.8 | 4/3 | 1.0% | steam_chimney 0/50, hid 34, off 16, 0.90%, Δluma +32.7 peak 85; smoke_chimney 0/16, hid 10, off 6, 0.00%; sparks_brake 28/92, hid 64, off 0, 0.09%, Δluma +27.4 peak 48 |
| pov_grassland.dusk_roof3p | grassland.dusk | roof3p | pc | 768x432 | 6.8 | 30/19 | 3.7% | steam_chimney 50/50, hid 0, off 0, 1.74%, Δluma -12.9 peak 27; smoke_chimney 16/16, hid 0, off 0, 3.25%, Δluma -10.2 peak 21; sparks_brake 3/92, hid 89, off 0, 0.00%, Δluma +8.3 peak 9; headlamp (light/beam) |
| pov_grassland.dusk_roof3p.phone | grassland.dusk | roof3p | phone | 844x390 | 6.8 | 21/14 | 1.8% | steam_chimney 34/34, hid 0, off 0, 1.22%, Δluma -11.2 peak 19; smoke_chimney 9/10, hid 0, off 1, 1.36%, Δluma -12.4 peak 19; sparks_brake 1/61, hid 60, off 0, 0.00%, Δluma +9.5 peak 13; headlamp (light/beam) |
| pov_grassland.dusk_door1p | grassland.dusk | door1p | pc | 768x432 | 6.8 | 4/3 | 1.0% | steam_chimney 0/50, hid 34, off 16, 0.90%, Δluma +5.4 peak 34; smoke_chimney 0/16, hid 10, off 6, 0.00%; sparks_brake 28/92, hid 64, off 0, 0.09%, Δluma +27.4 peak 48; headlamp (light/beam) |
| pov_grassland.night_roof3p | grassland.night | roof3p | pc | 768x432 | 6.8 | 30/19 | 3.7% | steam_chimney 50/50, hid 0, off 0, 1.74%, Δluma +18.9 peak 37; smoke_chimney 16/16, hid 0, off 0, 3.25%, Δluma +9.3 peak 34; sparks_brake 3/92, hid 89, off 0, 0.00%, Δluma +8.0 peak 9; headlamp (light/beam) |
| pov_grassland.night_roof3p.phone | grassland.night | roof3p | phone | 844x390 | 6.8 | 21/14 | 1.8% | steam_chimney 34/34, hid 0, off 0, 1.22%, Δluma +17.5 peak 40; smoke_chimney 9/10, hid 0, off 1, 1.36%, Δluma +12.5 peak 38; sparks_brake 1/61, hid 60, off 0, 0.00%, Δluma +10.0 peak 13; headlamp (light/beam) |
| pov_grassland.night_door1p | grassland.night | door1p | pc | 768x432 | 6.8 | 4/3 | 1.0% | steam_chimney 0/50, hid 34, off 16, 0.90%, Δluma +2.7 peak 24; smoke_chimney 0/16, hid 10, off 6, 0.00%; sparks_brake 28/92, hid 64, off 0, 0.09%, Δluma +27.5 peak 49; headlamp (light/beam) |
| pov_coal_dust | grassland.day | cab1p | pc | 768x432 | 0.4 | 10/7 | 1.6% | coal_dust 20/20, hid 0, off 0, 1.64%, Δluma -22.7 peak 112 |

Visibility (warnings are for the maker to fix before the critic; hidden counts are facts):
- steam_chimney: mostly hidden by the train or ground from door1p
- steam_chimney: faint in grassland.day_roof3p, grassland.day_roof3p.phone, grassland.dusk_roof3p.phone, grassland.night_door1p (peak luma change under 25: its core barely differs from what is behind it; heuristic)
- smoke_chimney: mostly hidden by the train or ground from door1p
- smoke_chimney: faint in grassland.day_roof3p, grassland.day_roof3p.phone, grassland.dusk_roof3p, grassland.dusk_roof3p.phone (peak luma change under 25: its core barely differs from what is behind it; heuristic)
- WARN sparks_brake: under 0.1% of the screen in every POV (best pov_grassland.day_door1p: 28 of 92 visible, 0.09%): players may never see it (references/presets.md, Visible from the players' views)
- sparks_brake: mostly hidden by the train or ground from door1p, roof3p, roof3p phone

Budgets (assumed (OQ-029 default A): not canon until the owner decides; re-measure at the alpha live check (tech.streaming.live_check)); sets holding a pack preset:
- phone cruise: steady 54, peak 54, emitters 3, fill 3183 stud^2, lights 3 -> within
- phone crisis_stack: steady 230, peak 245, emitters 10, fill 3644 stud^2, lights 7 -> within
- phone night_tunnel: steady 144, peak 144, emitters 5, fill 3291 stud^2, lights 5 -> within
- phone storm_crisis: steady 384, peak 384, emitters 6, fill 3573 stud^2, lights 5 -> within
- phone boiler_fail: steady 14, peak 68, emitters 5, fill 2916 stud^2, lights 4 -> within
- phone derail: steady 54, peak 122, emitters 7, fill 5073 stud^2, lights 4 -> within
- phone windows: steady 90, peak 113, emitters 6, fill 3521 stud^2, lights 3 -> within
- phone arrival_brake: steady 144, peak 144, emitters 5, fill 3291 stud^2, lights 4 -> within
- phone pressure_brake: steady 180, peak 195, emitters 8, fill 3632 stud^2, lights 5 -> within
- pc cruise: steady 83, peak 83, emitters 3, fill 4762 stud^2, lights 3 -> within
- pc crisis_stack: steady 298, peak 318, emitters 10, fill 5281 stud^2, lights 7 -> within
- pc night_tunnel: steady 211, peak 211, emitters 5, fill 4917 stud^2, lights 5 -> within
- pc storm_crisis: steady 665, peak 665, emitters 6, fill 5215 stud^2, lights 5 -> within
- pc boiler_fail: steady 26, peak 80, emitters 5, fill 3294 stud^2, lights 4 -> within
- pc derail: steady 83, peak 151, emitters 7, fill 6653 stud^2, lights 4 -> within
- pc windows: steady 119, peak 142, emitters 6, fill 5101 stud^2, lights 3 -> within
- pc arrival_brake: steady 211, peak 211, emitters 5, fill 4917 stud^2, lights 4 -> within
- pc pressure_brake: steady 247, peak 267, emitters 8, fill 5269 stud^2, lights 5 -> within

Limits: Effects are simulated from the preset data with Roblox ParticleEmitter rules; textures are procedural stand-ins for the built-ins; particles are not lit by the scene beyond a LightInfluence factor; lights show as glow dots only; drift = Workspace.GlobalWind at train speed. Studio test pending (owner).
