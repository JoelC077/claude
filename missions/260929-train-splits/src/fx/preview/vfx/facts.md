# Effects: measured on the simulation (2026-09-29)

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
