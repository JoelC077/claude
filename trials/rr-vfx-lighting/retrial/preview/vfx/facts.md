# Effects: measured on the simulation (2026-09-28)

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
