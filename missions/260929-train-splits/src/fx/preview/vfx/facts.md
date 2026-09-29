# Effects: measured on the simulation (2026-09-29)

Side strips: steady state at Speed 35.0 (gameplay.speed.normal) on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar (tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.

| preset | kind | priority | anchor | start | live phone / pc (budget formula, full rate) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|---|
| split_explosion | burst | 1 | SplitCore | event | 18 / 18 | 18/18/5/18 | 2.78 | none: owner decision 2026-09-29 (C10 'I want a big explosion aswell') overrides the OQ-028 default for the carriage split only; proposed · OQ-028 |
| torn_edge_smoke | loop | 2 | TornEdge | on | 19 / 28 | 22/22/22 | 11.39 | none: mission 260929-train-splits R3 (torn ends read as torn); proposed |
| topple_dust | burst | 1 | WreckDust | event | 14 / 14 | 14/14/14/14 | 2.54 | none: owner C11 topple (mission 260929-train-splits R12); proposed |
| glass_split | burst | 1 | WindowPane | event | 23 / 23 | 23/23/23/23 | 6.35 | none: mission variant of glass_burst (av.vfx.glass) for the carriage split; proposed |
| boiler_burst | burst | 1 | Boiler | event | 54 / 54 | 54/54/34/54 | 5.56 | av.vfx.boiler_fail, gameplay.crisis.fail_states, gameplay.crisis.fail_cinematic |
| interior_split | burst | 1 | SplitCoreInside | event | 18 / 18 | 18/18/5/18 | 2.78 | none: owner decision 2026-09-29 (C10 'I want a big explosion aswell') overrides the OQ-028 default for the carriage split only; proposed · OQ-028 |

POV composites: particles over the lookdev plate from the same camera (PC 768x432, phone 844x390 at phone rates); loops at steady state at Speed gameplay.speed.fast, bursts shown t s after they fire. Per preset: visible/live, h = hidden by the train or ground, o = off-screen, share of the screen, then drawn alone over the plate: mean luma change / 90th-percentile luma change.

| POV | look | cam | tier | overdraw max/p95 | screen | per preset |
|---|---|---|---|---|---|---|
| grassland.day_roof3p | grassland.day | roof3p | pc | 3/2 | 11.7% | torn 19/22 h1 o2 11.67% +0/30 |
| grassland.day_roof3p.phone | grassland.day | roof3p | phone | 2/1 | 17.1% | torn 16/16 h0 o0 17.05% -4/28 |
| grassland.day_door1p | grassland.day | door1p | pc | 0/0 | 0.0% | torn 0/22 h0 o22 0.00% |
| split_explosion | grassland.day | roof3p | pc | 10/5 | 55.0% | torn 21/24 h1 o2 12.02% -1/30; split 10/18 h2 o6 54.98% +61/108 |
| topple_dust | grassland.day | door1p | pc | 10/7 | 12.7% | torn 0/25 h0 o25 0.00%; topple 12/14 h0 o2 12.66% +79/119 |
| glass_split | grassland.day | door1p | pc | 3/2 | 0.6% | torn 0/24 h0 o24 0.00%; glass 23/23 h0 o0 0.62% +31/65 |
| boiler_burst | grassland.day | roof3p | pc | 11/2 | 13.1% | torn 22/24 h1 o1 12.90% -2/29; boiler 50/54 h4 o0 0.64% +43/85 |
| interior_split | grassland.day | coach1p | pc | 3/2 | 42.3% | interior 3/18 h12 o3 42.28% +74/166 |

Visibility (warnings are for the maker to fix before the critic; hidden counts are facts):
- interior_split: mostly hidden by the train or ground from coach1p
