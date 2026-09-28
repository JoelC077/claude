# Lighting looks: measured on the preview renders (2026-09-28)

Cameras: roof3p = coach B roof, eye 9.5 (tech.camera.eye_3p); door1p = leaning out of coach A's doorway, eye 4.5 (tech.camera.eye_1p); cab1p = loco cab facing the firebox, eye 12.0 above rail (tech.camera.cab_view); coach1p = inside coach A facing the power box. FOV 70.0; phone renders at 844x390 (tech.ui_platform.phone). Stand envelope: gauge 8, body 17.4 wide, floor 5, roof 14 (tech.units.*, OQ-030); stand-in train: navy, cream band and interiors, hazard-yellow roof rails (style.form.rails); livery open (OQ-025).

| look | cam | sun elev | luma | clip/crush % (train) | train vs world | hazard vs world | ground (sat) | sky | spawn-edge fog | bands |
|---|---|---|---|---|---|---|---|---|---|---|
| grassland.day | roof3p | 38.8 | 149.4 | 0.0/0.0 (0.0) | 3.12:1 | 1.26:1 | #93A660 (0.28) | #ACBEAE | 0.956 at 2048 | none |
| grassland.day phone | roof3p | 38.8 | 153.0 | 0.0/0.0 (0.0) | 3.02:1 | 1.24:1 | #94A762 (0.28) | #ADBEAE | 0.956 at 2048 | none |
| grassland.day@door1p | door1p | 38.8 | 116.1 | 0.0/6.01 (13.75) | 2.08:1 | None:1 | #738A44 (0.34) | #A9BDAF | 0.956 at 2048 | none |
| grassland.dusk | roof3p | 1.7 | 77.4 | 0.0/0.0 (0.0) | 2.02:1 | 1.86:1 | #5C583E (0.19) | #675A60 | 0.968 at 2048 | none |
| grassland.dusk phone | roof3p | 1.7 | 80.8 | 0.0/0.0 (0.0) | 2.08:1 | 1.79:1 | #5F5A3F (0.2) | #685B60 | 0.968 at 2048 | none |
| grassland.dusk@door1p | door1p | 1.7 | 75.2 | 0.0/5.37 (12.28) | 1.04:1 | None:1 | #4F4F31 (0.24) | #65585F | 0.968 at 2048 | none |
| grassland.night | roof3p | -47.8 (moon) | 26.7 | 0.0/0.56 (0.43) | 1.48:1 | 1.86:1 | #2F4437 (0.18) | #01030F | 0.969 at 2048 | none |
| grassland.night phone | roof3p | -47.8 (moon) | 28.2 | 0.0/0.45 (0.36) | 1.45:1 | 1.92:1 | #2F4437 (0.18) | #010410 | 0.969 at 2048 | none |
| grassland.night@door1p | door1p | -47.8 (moon) | 42.9 | 0.0/8.61 (14.62) | 1.08:1 | None:1 | #344B38 (0.18) | #00030E | 0.969 at 2048 | none |
| grassland.day@cab1p | cab1p | 38.8 | 16.6 | 0.95/49.22 (51.52) | 5.4:1 | None:1 | #7B914A (0.32) | None | 0.956 at 2048 | none |

Checks against canon: spawn-edge fog >= 0.9 hides the streamer's spawn edge (tech.lighting.atmosphere, tech.streaming.window); ground saturation <= 0.45 (style.material.ground_value); bands = frame and sky means tested against the Dead Rails sepia and Land or Die blue-sky bands (style.dont.*); contrast = relative luminance ratio in the same frame.

Flags (maker heuristics, not canon: train vs world under 2:1 fades on a dim phone; crush over 5% loses shape):
- grassland.day@door1p (door1p): crush 6.01% > 5% (train 13.75%)
- grassland.dusk@door1p (door1p): train vs world 1.04:1 < 2:1; crush 5.37% > 5% (train 12.28%)
- grassland.night (roof3p): train vs world 1.48:1 < 2:1
- grassland.night phone (roof3p): train vs world 1.45:1 < 2:1
- grassland.night@door1p (door1p): train vs world 1.08:1 < 2:1; crush 8.61% > 5% (train 14.62%)
- grassland.day@cab1p (cab1p): crush 49.22% > 5% (train 51.52%)

Limits: Previews are approximations, not Roblox: Cycles + a numpy post (filmic curve, Atmosphere fog from depth, bloom, sun rays, ColorCorrection). Skybox, Future light falloff and Roblox tone mapping are not modelled; phone variants assume no shadows and no Bloom/SunRays (tech.lighting.post_low_quality). The train is a stand-in (livery open, OQ-025). Studio test pending (owner).
