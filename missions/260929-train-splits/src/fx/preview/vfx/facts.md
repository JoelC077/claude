# Effects: measured on the simulation (2026-09-29)

Not on the sheets (too many for one contact + one close-up sheet): torn_edge_smoke (loop p2): side strip, Speed 35, 9.85 px/stud, construction view.
Side strips: steady state at Speed 35.0 (gameplay.speed.normal) on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar (tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.

| preset | kind | priority | anchor | start | live phone / pc (budget formula, full rate) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|---|
| split_explosion | burst | 1 | SplitCore | event | 18 / 18 | 18/18/6/18 | 2.78 | none: owner decision 2026-09-29 (C10 'I want a big explosion aswell') overrides the OQ-028 default for the carriage split only; proposed · OQ-028 |
| torn_edge_smoke | loop | 2 | TornEdge | on | 19 / 28 | 22/22/22 | 9.85 | none: mission 260929-train-splits R3 (torn ends read as torn); proposed |
| topple_dust | burst | 1 | WreckDust | event | 14 / 14 | 14/14/14/14 | 2.54 | none: owner C11 topple (mission 260929-train-splits R12); proposed |
| glass_split | burst | 1 | WindowPane | event | 23 / 23 | 23/23/23/23 | 11.64 | none: mission variant of glass_burst (av.vfx.glass) for the carriage split; proposed |
| derail_explosion | burst | 1 | Bogie | event | 68 / 68 | 68/66/28/66 | 5.73 | none: OQ-028 default A keeps derailment a breakdown task; this preset is unassigned · OQ-028 |
| boiler_burst | burst | 1 | Boiler | event | 54 / 54 | 54/54/34/54 | 5.56 | av.vfx.boiler_fail, gameplay.crisis.fail_states, gameplay.crisis.fail_cinematic |
| interior_split | burst | 1 | SplitCoreInside | event | 18 / 18 | 18/18/6/18 | 2.78 | none: owner decision 2026-09-29 (C10 'I want a big explosion aswell') overrides the OQ-028 default for the carriage split only; proposed · OQ-028 |

POV composites: particles over the lookdev plate from the same camera (PC 768x432, phone 844x390 at phone rates); loops at steady state at Speed gameplay.speed.fast, bursts shown t s after they fire. Per preset: visible/live, h = hidden by the train or ground, o = off-screen, share of the screen, then drawn alone over the plate: mean luma change / 90th-percentile luma change.

| POV | look | cam | tier | overdraw max/p95 | screen | per preset |
|---|---|---|---|---|---|---|
| grassland.day_roof3p | grassland.day | roof3p | pc | 2/1 | 9.7% | torn 19/22 h1 o2 9.72% -5/30 |
| grassland.day_roof3p.phone | grassland.day | roof3p | phone | 2/1 | 6.3% | torn 15/16 h0 o1 6.28% -7/33 |
| grassland.day_door1p | grassland.day | door1p | pc | 0/0 | 0.0% | torn 0/22 h0 o22 0.00% |
| split_explosion | grassland.day | roof3p | pc | 10/6 | 91.2% | torn 22/25 h0 o3 9.33% -7/31; split 11/18 h3 o4 91.19% +41/77 |
| topple_dust | grassland.day | door1p | pc | 6/4 | 8.5% | torn 0/25 h0 o25 0.00%; topple 12/14 h0 o2 8.47% +62/100 |
| glass_split | grassland.day | door1p | pc | 3/2 | 0.6% | torn 0/24 h0 o24 0.00%; glass 23/23 h0 o0 0.62% +31/65 |
| derail_explosion | grassland.day | roof3p | pc | 2/2 | 9.3% | torn 22/24 h0 o2 9.27% -6/33; derail 0/68 h68 o0 0.00% |
| boiler_burst | grassland.day | roof3p | pc | 11/2 | 9.4% | torn 21/24 h1 o2 9.01% -7/33; boiler 50/54 h4 o0 0.64% +43/85 |
| interior_split | grassland.day | coach1p | pc | 7/5 | 44.6% | interior 3/18 h3 o12 44.57% +72/151 |

Visibility (warnings are for the maker to fix before the critic; hidden counts are facts):
- WARN derail_explosion: under 0.1% of the screen in every POV (best pov_derail_explosion: 0 of 68 visible, 0.00%): players may never see it (references/presets.md, Visible from the players' views)
- derail_explosion: mostly hidden by the train or ground from roof3p
