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
| grassland.night | roof3p | -47.8 (moon) | 28.6 | 0.0/0.55 (0.4) | 1.57:1 | 1.99:1 | #33483B (0.17) | #01030F | 0.969 at 2048 | none |
| grassland.night phone | roof3p | -47.8 (moon) | 30.1 | 0.0/0.44 (0.3) | 1.55:1 | 2.04:1 | #33493B (0.17) | #010410 | 0.969 at 2048 | none |
| grassland.night@door1p | door1p | -47.8 (moon) | 48.2 | 0.0/6.18 (11.0) | 1.05:1 | None:1 | #39513C (0.17) | #00030E | 0.969 at 2048 | none |
| grassland.day@cab1p | cab1p | 38.8 | 65.5 | 0.95/27.16 (27.99) | 3.45:1 | None:1 | #8CA158 (0.3) | None | 0.956 at 2048 | none |

Checks against canon: spawn-edge fog >= 0.9 hides the streamer's spawn edge (tech.lighting.atmosphere, tech.streaming.window); ground saturation <= 0.45 (style.material.ground_value); bands = frame and sky means tested against the Dead Rails sepia and Land or Die blue-sky bands (style.dont.*); contrast = relative luminance ratio in the same frame.

Flags (maker heuristics, not canon: train vs world under 2:1 fades on a dim phone; crush over 5% loses shape):
- grassland.dusk@door1p (door1p): train vs world 1.11:1 < 2:1
- grassland.night (roof3p): train vs world 1.57:1 < 2:1
- grassland.night phone (roof3p): train vs world 1.55:1 < 2:1
- grassland.night@door1p (door1p): train vs world 1.05:1 < 2:1; crush 6.18% > 5% (train 11.0%)
- grassland.day@cab1p (cab1p): crush 27.16% > 5% (train 27.99%)

Limits: Previews are approximations, not Roblox: Cycles + a numpy post (filmic curve, Atmosphere fog from depth, bloom, sun rays, ColorCorrection). Skybox, Future light falloff and Roblox tone mapping are not modelled; phone variants assume no shadows and no Bloom/SunRays (tech.lighting.post_low_quality). The train is a stand-in (livery open, OQ-025). Studio test pending (owner).

## Effects

Side strips: steady state at Speed 35.0 (gameplay.speed.normal) on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar (tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.

| preset | kind | priority | anchor | start | live phone / pc (budget formula, full rate) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|---|
| steam_chimney | loop | 2 | Chimney | on | 40 / 58 | 38/38/38 | 3.66 | av.vfx.speed_link, gameplay.speed.drives |
| smoke_chimney | loop | 3 | Chimney | on | 10 / 21 | 15/15/15 | 2.61 | av.vfx.speed_link |
| sparks_brake | loop | 2 | BrakeShoe | off | 90 / 128 | 68/68/68 | 15.84 | gameplay.run.brake_formula, gameplay.crisis.pressure |
| coal_dust | burst | 2 | Firebox | event | 15 / 20 | 20/20/11/20 | 17.78 | gameplay.crisis.firebox, gameplay.fuel.shovel_pct |

POV composites: particles over the lookdev plate from the same camera (PC 768x432, phone 844x390 at phone rates); loops at steady state at Speed gameplay.speed.fast, bursts shown t s after they fire. Per preset: visible/live, h = hidden by the train or ground, o = off-screen, share of the screen, then drawn alone over the plate: mean luma change / 90th-percentile luma change.

| POV | look | cam | tier | overdraw max/p95 | screen | per preset |
|---|---|---|---|---|---|---|
| grassland.day_roof3p | grassland.day | roof3p | pc | 30/19 | 3.7% | steam 50/50 h0 o0 1.74% +20/39; smoke 16/16 h0 o0 3.25% -17/34; sparks 3/92 h89 o0 0.00% +9/11 |
| grassland.day_roof3p.phone | grassland.day | roof3p | phone | 21/14 | 1.8% | steam 34/34 h0 o0 1.22% +17/40; smoke 9/10 h0 o1 1.36% -20/33; sparks 1/61 h60 o0 0.00% +12/16 |
| grassland.day_door1p | grassland.day | door1p | pc | 4/3 | 1.1% | steam 0/50 h34 o16 0.90% +33/85; smoke 0/16 h10 o6 0.00%; sparks 28/92 h64 o0 0.16% +29/73 |
| grassland.dusk_roof3p | grassland.dusk | roof3p | pc | 30/19 | 3.7% | steam 50/50 h0 o0 1.74% -4/9; smoke 16/16 h0 o0 3.25% -11/23; sparks 3/92 h89 o0 0.00% +9/10; headlamp light |
| grassland.dusk_roof3p.phone | grassland.dusk | roof3p | phone | 21/14 | 1.8% | steam 34/34 h0 o0 1.22% -4/7; smoke 9/10 h0 o1 1.36% -13/22; sparks 1/61 h60 o0 0.00% +12/16; headlamp light |
| grassland.dusk_door1p | grassland.dusk | door1p | pc | 4/3 | 1.1% | steam 0/50 h34 o16 0.90% +5/34; smoke 0/16 h10 o6 0.00%; sparks 28/92 h64 o0 0.16% +29/73; headlamp light |
| grassland.night_roof3p | grassland.night | roof3p | pc | 30/19 | 3.7% | steam 50/50 h0 o0 1.74% +23/49; smoke 16/16 h0 o0 3.25% -0/2; sparks 3/92 h89 o0 0.00% +8/10; headlamp light |
| grassland.night_roof3p.phone | grassland.night | roof3p | phone | 21/14 | 1.8% | steam 34/34 h0 o0 1.22% +20/49; smoke 9/10 h0 o1 1.36% +0/2; sparks 1/61 h60 o0 0.00% +12/15; headlamp light |
| grassland.night_door1p | grassland.night | door1p | pc | 4/3 | 1.1% | steam 0/50 h34 o16 0.90% +2/25; smoke 0/16 h10 o6 0.00%; sparks 28/92 h64 o0 0.16% +29/73; headlamp light |
| coal_dust | grassland.day | cab1p | pc | 10/7 | 1.6% | coal 20/20 h0 o0 1.64% -26/117 |

Visibility (warnings are for the maker to fix before the critic; hidden counts are facts):
- steam_chimney: mostly hidden by the train or ground from door1p
- steam_chimney: faint in grassland.dusk_roof3p, grassland.dusk_roof3p.phone (drawn alone, 90% of its pixels change luma by under 25: it barely differs from what is behind it; heuristic)
- smoke_chimney: mostly hidden by the train or ground from door1p
- smoke_chimney: faint in grassland.dusk_roof3p, grassland.dusk_roof3p.phone, grassland.night_roof3p, grassland.night_roof3p.phone (drawn alone, 90% of its pixels change luma by under 25: it barely differs from what is behind it; heuristic)
- sparks_brake: mostly hidden by the train or ground from door1p, roof3p, roof3p phone

Budgets (assumed (OQ-029 default A): not canon until the owner decides; re-measure at the alpha live check (tech.streaming.live_check)); 9 sets holding a pack preset:
- phone: 9 of 9 sets within; tightest storm_crisis: steady 390 of 400, peak 390 of 800, emitters 6 of 12, lights 5 of 8
- pc: 9 of 9 sets within; tightest storm_crisis: steady 671 of 1500, peak 671 of 2500, emitters 6 of 24, lights 5 of 16

Limits: Effects are simulated from the preset data with Roblox ParticleEmitter rules; textures are procedural stand-ins for the built-ins; particles are not lit by the scene beyond a LightInfluence factor; lights show as glow dots only; drift = Workspace.GlobalWind at train speed. Studio test pending (owner).
