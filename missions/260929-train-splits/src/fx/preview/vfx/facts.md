# Effects: measured on the simulation (2026-09-29)

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
