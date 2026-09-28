# Effects: measured on the simulation (2026-09-28)

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
