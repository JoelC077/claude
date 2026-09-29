# Effects: measured on the simulation (2026-09-29)

Side strips: steady state at Speed 35.0 (gameplay.speed.normal) on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar (tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.

| preset | kind | priority | anchor | start | live phone / pc (budget formula, full rate) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|---|
| torn_edge_smoke | loop | 2 | TornEdge | on | 19 / 28 | 22/22/22 | 8.24 | none: mission 260929-train-splits R3 (torn ends read as torn); proposed |
| topple_dust | burst | 1 | WreckDust | event | 16 / 16 | 16/16/16/16 | 2.54 | none: owner C11 topple (mission 260929-train-splits R12); proposed |

POV composites: particles over the lookdev plate from the same camera (PC 768x432, phone 844x390 at phone rates); loops at steady state at Speed gameplay.speed.fast, bursts shown t s after they fire. Per preset: visible/live, h = hidden by the train or ground, o = off-screen, share of the screen, then drawn alone over the plate: mean luma change / 90th-percentile luma change.

| POV | look | cam | tier | overdraw max/p95 | screen | per preset |
|---|---|---|---|---|---|---|
| grassland.day_roof3p | grassland.day | roof3p | pc | 2/2 | 9.8% | torn 20/22 h1 o1 9.77% -9/33 |
| grassland.day_roof3p.phone | grassland.day | roof3p | phone | 2/2 | 6.8% | torn 15/16 h0 o1 6.81% -14/40 |
| grassland.day_door1p | grassland.day | door1p | pc | 0/0 | 0.0% | torn 0/22 h0 o22 0.00% |
| topple_dust | grassland.day | door1p | pc | 9/5 | 11.9% | torn 0/25 h0 o25 0.00%; topple 11/16 h2 o3 11.87% +67/116 |
