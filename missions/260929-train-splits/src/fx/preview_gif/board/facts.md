# Look-dev board: split_explosion, torn_edge_smoke, topple_dust, glass_burst (2026-09-29)

Presets from /home/user/claude/missions/260929-train-splits/src/fx. Tiles show the player's views (POV composites: particles over the lit plate); strips on closeups.png are construction views for shape and timing only.

## Looks

Cameras: roof3p = coach B roof, eye 9.5 (tech.camera.eye_3p); door1p = leaning out of coach A's doorway, eye 4.5 (tech.camera.eye_1p); cab1p = loco cab facing the firebox, eye 12.0 above rail (tech.camera.cab_view); coach1p = inside coach A facing the power box. FOV 70.0; phone renders at 844x390 (tech.ui_platform.phone). Stand envelope: gauge 8, body 17.4 wide, floor 5, roof 14 (tech.units.*, OQ-030); stand-in train: navy, cream band and interiors, hazard-yellow roof rails (style.form.rails); livery open (OQ-025).

| look | cam | sun elev | luma | clip/crush % (train) | train vs world | hazard vs world | ground (sat) | sky | spawn-edge fog | bands |
|---|---|---|---|---|---|---|---|---|---|---|
| grassland.day | roof3p | 38.8 | 149.4 | 0.0/0.0 (0.0) | 3.25:1 | 1.26:1 | #93A660 (0.28) | #ACBEAE | 0.956 at 2048 | none |
| grassland.day phone | roof3p | 38.8 | 152.9 | 0.0/0.0 (0.0) | 3.18:1 | 1.24:1 | #94A761 (0.28) | #ADBEAE | 0.956 at 2048 | none |
| grassland.day@door1p | door1p | 38.8 | 114.3 | 0.0/4.58 (10.5) | 2.04:1 | None:1 | #728942 (0.35) | #AABDAF | 0.956 at 2048 | none |

Checks against canon: spawn-edge fog >= 0.9 hides the streamer's spawn edge (tech.lighting.atmosphere, tech.streaming.window); ground saturation <= 0.45 (style.material.ground_value); bands = frame and sky means tested against the Dead Rails sepia and Land or Die blue-sky bands (style.dont.*); contrast = relative luminance ratio in the same frame.

Limits: Previews are approximations, not Roblox: Cycles + a numpy post (filmic curve, Atmosphere fog from depth, bloom, sun rays, ColorCorrection). Skybox, Future light falloff and Roblox tone mapping are not modelled; phone variants assume no shadows and no Bloom/SunRays (tech.lighting.post_low_quality). The train is a stand-in (livery open, OQ-025). Studio test pending (owner).

## Effects

Side strips: steady state at Speed 35.0 (gameplay.speed.normal) on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar (tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.

| preset | kind | priority | anchor | start | live phone / pc (budget formula, full rate) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|---|
| split_explosion | burst | 1 | SplitCore | event | 20 / 20 | 20/20/16/20 | 2.07 | none: owner decision 2026-09-29 (C10 'I want a big explosion aswell') overrides the OQ-028 default for the carriage split only; proposed · OQ-028 |
| torn_edge_smoke | loop | 2 | TornEdge | on | 20 / 28 | 24/24/24 | 5.03 | none: mission 260929-train-splits R3 (torn ends read as torn); proposed |
| topple_dust | burst | 1 | WreckDust | event | 10 / 10 | 10/10/10/10 | 2.54 | none: owner C11 topple (mission 260929-train-splits R12); proposed |
| glass_burst | burst | 1 | WindowPane | event | 23 / 23 | 23/23/1/23 | 17.78 | av.vfx.glass, gameplay.crisis.windows |

POV composites: particles over the lookdev plate from the same camera (PC 768x432, phone 844x390 at phone rates); loops at steady state at Speed gameplay.speed.fast, bursts shown t s after they fire. Per preset: visible/live, h = hidden by the train or ground, o = off-screen, share of the screen, then drawn alone over the plate: mean luma change / 90th-percentile luma change.

| POV | look | cam | tier | overdraw max/p95 | screen | per preset |
|---|---|---|---|---|---|---|
| grassland.day_roof3p | grassland.day | roof3p | pc | 2/2 | 9.1% | torn 9/24 h2 o13 9.06% -10/30 |
| grassland.day_roof3p.phone | grassland.day | roof3p | phone | 1/1 | 3.8% | torn 9/18 h0 o9 3.78% -15/33 |
| grassland.day_door1p | grassland.day | door1p | pc | 0/0 | 0.0% | torn 0/24 h0 o24 0.00% |
| split_explosion | grassland.day | roof3p | pc | 8/6 | 20.9% | torn 12/24 h1 o11 6.90% -7/28; split 7/20 h6 o7 18.89% +33/104 |
| topple_dust | grassland.day | door1p | pc | 4/3 | 8.6% | torn 0/24 h0 o24 0.00%; topple 8/10 h1 o1 8.59% +55/89 |
| glass_burst | grassland.day | door1p | pc | 3/3 | 2.0% | torn 0/24 h0 o24 0.00%; glass 21/21 h0 o0 2.01% +9/16 |

Visibility (warnings are for the maker to fix before the critic; hidden counts are facts):
- glass_burst: faint in glass_burst (drawn alone, 90% of its pixels change luma by under 25: it barely differs from what is behind it; heuristic)

Budgets (assumed (OQ-029 default A): not canon until the owner decides; re-measure at the alpha live check (tech.streaming.live_check)); 2 sets holding a pack preset:
- phone: 2 of 2 sets within; tightest windows: steady 90 of 400, peak 113 of 800, emitters 6 of 12, lights 3 of 8
- pc: 2 of 2 sets within; tightest windows: steady 119 of 1500, peak 142 of 2500, emitters 6 of 24, lights 3 of 16

Limits: Effects are simulated from the preset data with Roblox ParticleEmitter rules; textures are procedural stand-ins for the built-ins; particles are not lit by the scene beyond a LightInfluence factor; lights show as glow dots only; drift = Workspace.GlobalWind at train speed. Studio test pending (owner).
