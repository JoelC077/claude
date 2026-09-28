# Effects: measured on the simulation (2026-09-28)

Side strips: steady state at Speed 35.0 (gameplay.speed.normal) on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar (tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.

| preset | kind | priority | anchor | start | live phone / pc (budget formula, full rate) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|---|
| steam_chimney | loop | 2 | Chimney | on | 40 / 58 | 38/38/38 | 3.66 | av.vfx.speed_link, gameplay.speed.drives |
| smoke_chimney | loop | 3 | Chimney | on | 10 / 21 | 15/15/15 | 2.61 | av.vfx.speed_link |
| sparks_brake | loop | 2 | BrakeShoe | off | 90 / 128 | 68/68/68 | 15.84 | gameplay.run.brake_formula, gameplay.crisis.pressure |
| coal_dust | burst | 2 | Firebox | event | 15 / 20 | 20/20/11/20 | 17.78 | gameplay.crisis.firebox, gameplay.fuel.shovel_pct |

POV composites (particles over the lookdev plate from the same camera; loops at steady state, Speed = gameplay.speed.fast; bursts fire after the loops warm up). Per preset: visible / live, hidden by the train or ground, off-screen, share of the screen, mean and peak (90th percentile) luma change over its own pixels:

| POV | look | cam | tier | res | t s | overdraw max/p95 | screen | per preset |
|---|---|---|---|---|---|---|---|---|
| pov_grassland.day_roof3p | grassland.day | roof3p | pc | 768x432 | 6.8 | 30/19 | 3.7% | steam_chimney 50/50, hid 0, off 0, 1.74%, Δluma +3.2 peak 16; smoke_chimney 16/16, hid 0, off 0, 3.25%, Δluma -5.5 peak 15; sparks_brake 3/92, hid 89, off 0, 0.00%, Δluma +9.0 peak 11 |
| pov_grassland.day_roof3p.phone | grassland.day | roof3p | phone | 844x390 | 6.8 | 21/14 | 1.8% | steam_chimney 34/34, hid 0, off 0, 1.22%, Δluma +3.0 peak 24; smoke_chimney 9/10, hid 0, off 1, 1.36%, Δluma -5.9 peak 20; sparks_brake 1/61, hid 60, off 0, 0.00%, Δluma +12.0 peak 16 |
| pov_grassland.day_door1p | grassland.day | door1p | pc | 768x432 | 6.8 | 4/3 | 1.1% | steam_chimney 0/50, hid 34, off 16, 0.90%, Δluma +32.7 peak 85; smoke_chimney 0/16, hid 10, off 6, 0.00%; sparks_brake 28/92, hid 64, off 0, 0.16%, Δluma +29.0 peak 73 |
| pov_grassland.dusk_roof3p | grassland.dusk | roof3p | pc | 768x432 | 6.8 | 30/19 | 3.7% | steam_chimney 50/50, hid 0, off 0, 1.74%, Δluma -12.9 peak 27; smoke_chimney 16/16, hid 0, off 0, 3.25%, Δluma -10.2 peak 21; sparks_brake 3/92, hid 89, off 0, 0.00%, Δluma +9.0 peak 10; headlamp (light/beam) |
| pov_grassland.dusk_roof3p.phone | grassland.dusk | roof3p | phone | 844x390 | 6.8 | 21/14 | 1.8% | steam_chimney 34/34, hid 0, off 0, 1.22%, Δluma -11.2 peak 19; smoke_chimney 9/10, hid 0, off 1, 1.36%, Δluma -12.4 peak 19; sparks_brake 1/61, hid 60, off 0, 0.00%, Δluma +12.2 peak 16; headlamp (light/beam) |
| pov_grassland.dusk_door1p | grassland.dusk | door1p | pc | 768x432 | 6.8 | 4/3 | 1.1% | steam_chimney 0/50, hid 34, off 16, 0.90%, Δluma +5.4 peak 34; smoke_chimney 0/16, hid 10, off 6, 0.00%; sparks_brake 28/92, hid 64, off 0, 0.16%, Δluma +29.4 peak 73; headlamp (light/beam) |
| pov_grassland.night_roof3p | grassland.night | roof3p | pc | 768x432 | 6.8 | 30/19 | 3.7% | steam_chimney 50/50, hid 0, off 0, 1.74%, Δluma +18.9 peak 37; smoke_chimney 16/16, hid 0, off 0, 3.25%, Δluma +9.3 peak 34; sparks_brake 3/92, hid 89, off 0, 0.00%, Δluma +8.0 peak 10; headlamp (light/beam) |
| pov_grassland.night_roof3p.phone | grassland.night | roof3p | phone | 844x390 | 6.8 | 21/14 | 1.8% | steam_chimney 34/34, hid 0, off 0, 1.22%, Δluma +17.5 peak 40; smoke_chimney 9/10, hid 0, off 1, 1.36%, Δluma +12.5 peak 38; sparks_brake 1/61, hid 60, off 0, 0.00%, Δluma +12.5 peak 16; headlamp (light/beam) |
| pov_grassland.night_door1p | grassland.night | door1p | pc | 768x432 | 6.8 | 4/3 | 1.1% | steam_chimney 0/50, hid 34, off 16, 0.90%, Δluma +2.7 peak 24; smoke_chimney 0/16, hid 10, off 6, 0.00%; sparks_brake 28/92, hid 64, off 0, 0.16%, Δluma +29.6 peak 74; headlamp (light/beam) |
| pov_coal_dust | grassland.day | cab1p | pc | 768x432 | 0.4 | 10/7 | 1.6% | coal_dust 20/20, hid 0, off 0, 1.64%, Δluma -22.7 peak 112 |

Visibility (warnings are for the maker to fix before the critic; hidden counts are facts):
- steam_chimney: mostly hidden by the train or ground from door1p
- steam_chimney: faint in grassland.day_roof3p, grassland.day_roof3p.phone, grassland.dusk_roof3p.phone, grassland.night_door1p (peak luma change under 25: its core barely differs from what is behind it; heuristic)
- smoke_chimney: mostly hidden by the train or ground from door1p
- smoke_chimney: faint in grassland.day_roof3p, grassland.day_roof3p.phone, grassland.dusk_roof3p, grassland.dusk_roof3p.phone (peak luma change under 25: its core barely differs from what is behind it; heuristic)
- sparks_brake: mostly hidden by the train or ground from door1p, roof3p, roof3p phone
