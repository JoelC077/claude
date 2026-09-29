# Effects: measured on the simulation (2026-09-29)

Not on the sheets (too many for one contact + one close-up sheet): torn_edge_smoke (loop p2): side strip, Speed 35, 8.22 px/stud, construction view.
Side strips: steady state at Speed 35.0 (gameplay.speed.normal) on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar (tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.

| preset | kind | priority | anchor | start | live phone / pc (budget formula, full rate) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|---|
| split_explosion | burst | 1 | SplitCore | event | 18 / 18 | 18/18/6/18 | 1.89 | none: owner decision 2026-09-29 (C10 'I want a big explosion aswell') overrides the OQ-028 default for the carriage split only; proposed · OQ-028 |
| torn_edge_smoke | loop | 2 | TornEdge | on | 17 / 24 | 21/21/21 | 8.22 | none: mission 260929-train-splits R3 (torn ends read as torn); proposed |
| topple_dust | burst | 1 | WreckDust | event | 14 / 14 | 14/14/14/14 | 2.54 | none: owner C11 topple (mission 260929-train-splits R12); proposed |
| split_glass | burst | 1 | WindowPane | event | 23 / 23 | 23/23/23/23 | 11.64 | none: mission variant of glass_burst (av.vfx.glass) for the carriage split; proposed |
| derail_explosion | burst | 1 | Bogie | event | 68 / 68 | 68/66/28/66 | 5.73 | none: OQ-028 default A keeps derailment a breakdown task; this preset is unassigned · OQ-028 |
| boiler_burst | burst | 1 | Boiler | event | 54 / 54 | 54/54/34/54 | 5.56 | av.vfx.boiler_fail, gameplay.crisis.fail_states, gameplay.crisis.fail_cinematic |
| split_explosion_in | burst | 1 | SplitCoreInside | event | 18 / 18 | 18/18/6/18 | 1.89 | none: owner decision 2026-09-29 (C10 'I want a big explosion aswell') overrides the OQ-028 default for the carriage split only; proposed · OQ-028 |

POV composites: particles over the lookdev plate from the same camera (PC 768x432, phone 844x390 at phone rates); loops at steady state at Speed gameplay.speed.fast, bursts shown t s after they fire. Per preset: visible/live, h = hidden by the train or ground, o = off-screen, share of the screen, then drawn alone over the plate: mean luma change / 90th-percentile luma change.

| POV | look | cam | tier | overdraw max/p95 | screen | per preset |
|---|---|---|---|---|---|---|
| grassland.day_roof3p | grassland.day | roof3p | pc | 2/2 | 6.7% | torn 17/21 h2 o2 6.66% -9/31 |
| grassland.day_roof3p.phone | grassland.day | roof3p | phone | 3/2 | 2.7% | torn 13/14 h0 o1 2.66% -3/29 |
| grassland.day_door1p | grassland.day | door1p | pc | 0/0 | 0.0% | torn 0/21 h0 o21 0.00% |
| split_explosion | grassland.day | roof3p | pc | 12/8 | 73.3% | torn 21/21 h0 o0 11.24% -4/23; split 10/18 h4 o4 69.97% +46/104 |
| topple_dust | grassland.day | door1p | pc | 7/4 | 6.9% | torn 0/21 h0 o21 0.00%; topple 11/14 h0 o3 6.90% +66/105 |
| split_glass | grassland.day | door1p | pc | 2/1 | 0.7% | torn 0/21 h0 o21 0.00%; split 23/23 h0 o0 0.65% +29/64 |
| derail_explosion | grassland.day | roof3p | pc | 2/1 | 8.9% | torn 20/21 h0 o1 8.87% -4/24; derail 0/67 h67 o0 0.00% |
| boiler_burst | grassland.day | roof3p | pc | 10/2 | 9.3% | torn 20/21 h0 o1 8.72% -4/24; boiler 51/54 h3 o0 0.65% +45/84 |
| split_explosion_in | grassland.day | coach1p | pc | 9/6 | 54.9% | split 5/18 h2 o11 54.90% +91/166 |

Visibility (warnings are for the maker to fix before the critic; hidden counts are facts):
- torn_edge_smoke: faint in split_explosion, derail_explosion, boiler_burst (drawn alone, 90% of its pixels change luma by under 25: it barely differs from what is behind it; heuristic)
- WARN derail_explosion: under 0.1% of the screen in every POV (best pov_derail_explosion: 0 of 67 visible, 0.00%): players may never see it (references/presets.md, Visible from the players' views)
- derail_explosion: mostly hidden by the train or ground from roof3p
