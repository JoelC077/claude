# Look-dev board: split_explosion, torn_edge_smoke, topple_dust, glass_split, boiler_burst, interior_split (2026-09-29)

Presets from /home/user/claude/missions/260929-train-splits/src/fx. Tiles show the player's views (POV composites: particles over the lit plate); strips on closeups.png are construction views for shape and timing only.

## Looks

Cameras: roof3p = coach B roof, eye 9.5 (tech.camera.eye_3p); door1p = leaning out of coach A's doorway, eye 4.5 (tech.camera.eye_1p); cab1p = loco cab facing the firebox, eye 12.0 above rail (tech.camera.cab_view); coach1p = inside coach A facing the power box. FOV 70.0; phone renders at 844x390 (tech.ui_platform.phone). Stand envelope: gauge 8, body 17.4 wide, floor 5, roof 14 (tech.units.*, OQ-030); stand-in train: navy, cream band and interiors, hazard-yellow roof rails (style.form.rails); livery open (OQ-025).

| look | cam | sun elev | luma | clip/crush % (train) | train vs world | hazard vs world | ground (sat) | sky | spawn-edge fog | bands |
|---|---|---|---|---|---|---|---|---|---|---|
| grassland.day | roof3p | 38.8 | 149.4 | 0.0/0.0 (0.0) | 3.25:1 | 1.26:1 | #93A660 (0.28) | #ACBEAE | 0.956 at 2048 | none |
| grassland.day phone | roof3p | 38.8 | 152.9 | 0.0/0.0 (0.0) | 3.18:1 | 1.24:1 | #94A761 (0.28) | #ADBEAE | 0.956 at 2048 | none |
| grassland.day@door1p | door1p | 38.8 | 114.3 | 0.0/4.58 (10.5) | 2.04:1 | None:1 | #728942 (0.35) | #AABDAF | 0.956 at 2048 | none |
| grassland.day@coach1p | coach1p | 38.8 | 33.0 | 0.0/32.83 (32.83) | None:1 | None:1 | None (None) | None | 0.956 at 2048 | none |

Checks against canon: spawn-edge fog >= 0.9 hides the streamer's spawn edge (tech.lighting.atmosphere, tech.streaming.window); ground saturation <= 0.45 (style.material.ground_value); bands = frame and sky means tested against the Dead Rails sepia and Land or Die blue-sky bands (style.dont.*); contrast = relative luminance ratio in the same frame.

Flags (maker heuristics, not canon: train vs world under 2:1 fades on a dim phone; crush over 5% loses shape):
- grassland.day@coach1p (coach1p): crush 32.83% > 5% (train 32.83%)

Limits: Previews are approximations, not Roblox: Cycles + a numpy post (filmic curve, Atmosphere fog from depth, bloom, sun rays, ColorCorrection). Skybox, Future light falloff and Roblox tone mapping are not modelled; phone variants assume no shadows and no Bloom/SunRays (tech.lighting.post_low_quality). The train is a stand-in (livery open, OQ-025). Studio test pending (owner).

## Effects

Side strips: steady state at Speed 35.0 (gameplay.speed.normal) on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar (tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.

| preset | kind | priority | anchor | start | live phone / pc (budget formula, full rate) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|---|
| split_explosion | burst | 1 | SplitCore | event | 18 / 18 | 18/18/5/18 | 2.78 | none: owner decision 2026-09-29 (C10 'I want a big explosion aswell') overrides the OQ-028 default for the carriage split only; proposed · OQ-028 |
| torn_edge_smoke | loop | 2 | TornEdge | on | 19 / 28 | 22/22/22 | 8.24 | none: mission 260929-train-splits R3 (torn ends read as torn); proposed |
| topple_dust | burst | 1 | WreckDust | event | 16 / 16 | 16/16/16/16 | 2.54 | none: owner C11 topple (mission 260929-train-splits R12); proposed |
| glass_split | burst | 1 | WindowPane | event | 23 / 23 | 23/23/23/23 | 6.35 | none: mission variant of glass_burst (av.vfx.glass) for the carriage split; proposed |
| boiler_burst | burst | 1 | Boiler | event | 54 / 54 | 54/54/34/54 | 5.56 | av.vfx.boiler_fail, gameplay.crisis.fail_states, gameplay.crisis.fail_cinematic |
| interior_split | burst | 1 | SplitCoreInside | event | 18 / 18 | 18/18/5/18 | 2.78 | none: owner decision 2026-09-29 (C10 'I want a big explosion aswell') overrides the OQ-028 default for the carriage split only; proposed · OQ-028 |

POV composites: particles over the lookdev plate from the same camera (PC 768x432, phone 844x390 at phone rates); loops at steady state at Speed gameplay.speed.fast, bursts shown t s after they fire. Per preset: visible/live, h = hidden by the train or ground, o = off-screen, share of the screen, then drawn alone over the plate: mean luma change / 90th-percentile luma change.

| POV | look | cam | tier | overdraw max/p95 | screen | per preset |
|---|---|---|---|---|---|---|
| grassland.day_roof3p | grassland.day | roof3p | pc | 2/2 | 9.8% | torn 20/22 h1 o1 9.77% -9/33 |
| grassland.day_roof3p.phone | grassland.day | roof3p | phone | 2/2 | 6.8% | torn 15/16 h0 o1 6.81% -14/40 |
| grassland.day_door1p | grassland.day | door1p | pc | 0/0 | 0.0% | torn 0/22 h0 o22 0.00% |
| split_explosion | grassland.day | roof3p | pc | 9/4 | 61.8% | torn 21/24 h1 o2 9.81% -12/37; split 10/18 h2 o6 61.39% +58/107 |
| topple_dust | grassland.day | door1p | pc | 9/6 | 13.3% | torn 0/25 h0 o25 0.00%; topple 11/16 h2 o3 13.34% +67/118 |
| glass_split | grassland.day | door1p | pc | 3/2 | 0.6% | torn 0/24 h0 o24 0.00%; glass 23/23 h0 o0 0.62% +31/65 |
| boiler_burst | grassland.day | roof3p | pc | 10/2 | 10.9% | torn 22/24 h1 o1 10.26% -11/35; boiler 50/54 h4 o0 0.64% +43/85 |
| interior_split | grassland.day | coach1p | pc | 3/2 | 38.2% | interior 2/18 h12 o4 38.25% +68/166 |

Visibility (warnings are for the maker to fix before the critic; hidden counts are facts):
- interior_split: mostly hidden by the train or ground from coach1p

Budgets (assumed (OQ-029 default A): not canon until the owner decides; re-measure at the alpha live check (tech.streaming.live_check)); 3 sets holding a pack preset:
- phone: 3 of 3 sets within; tightest carriage_split_inside: steady 74 of 400, peak 154 of 800, emitters 11 of 12, lights 5 of 8
- pc: 3 of 3 sets within; tightest carriage_split_inside: steady 111 of 1500, peak 191 of 2500, emitters 11 of 24, lights 5 of 16

Limits: Effects are simulated from the preset data with Roblox ParticleEmitter rules; textures are procedural stand-ins for the built-ins; particles are not lit by the scene beyond a LightInfluence factor; lights show as glow dots only; drift = Workspace.GlobalWind at train speed. Studio test pending (owner).
