# Lighting looks: measured on the preview renders (2026-09-28)

Cameras: roof3p = coach B roof, eye 9.5 (tech.camera.eye_3p); door1p = leaning out of coach A's doorway, eye 4.5 (tech.camera.eye_1p); cab1p = loco cab facing the firebox, eye 12.0 above rail (tech.camera.cab_view); coach1p = inside coach A facing the power box. FOV 70.0; phone renders at 844x390 (tech.ui_platform.phone). Stand envelope: gauge 8, body 17.4 wide, floor 5, roof 14 (tech.units.*, OQ-030); stand-in train: navy, cream band and interiors, hazard-yellow roof rails (style.form.rails); livery open (OQ-025).

| look | cam | sun elev | luma | clip/crush % (train) | train vs world | hazard vs world | ground (sat) | sky | spawn-edge fog | bands |
|---|---|---|---|---|---|---|---|---|---|---|
| grassland.day | roof3p | 38.8 | 149.4 | 0.0/0.0 (0.0) | 3.25:1 | 1.26:1 | #93A660 (0.28) | #ACBEAE | 0.956 at 2048 | none |
| grassland.day phone | roof3p | 38.8 | 152.9 | 0.0/0.0 (0.0) | 3.18:1 | 1.24:1 | #94A761 (0.28) | #ADBEAE | 0.956 at 2048 | none |
| grassland.day@door1p | door1p | 38.8 | 114.3 | 0.0/4.58 (10.5) | 2.04:1 | None:1 | #728942 (0.35) | #AABDAF | 0.956 at 2048 | none |
| grassland.dusk | roof3p | 1.7 | 84.5 | 0.0/0.0 (0.0) | 2.28:1 | 1.98:1 | #6C6849 (0.2) | #685A60 | 0.968 at 2048 | none |
| grassland.dusk phone | roof3p | 1.7 | 88.2 | 0.0/0.0 (0.0) | 2.37:1 | 1.87:1 | #6F6A49 (0.2) | #685B60 | 0.968 at 2048 | none |
| grassland.dusk@door1p | door1p | 1.7 | 85.1 | 0.0/0.02 (0.04) | 1.11:1 | None:1 | #62613C (0.24) | #66595F | 0.968 at 2048 | none |
| grassland.night | roof3p | -47.8 (moon) | 28.6 | 0.0/0.55 (0.4) | 1.57:1 | 1.99:1 | #33483B (0.17) | #01030F | 0.969 at 2048 | none |
| grassland.night phone | roof3p | -47.8 (moon) | 30.1 | 0.0/0.44 (0.3) | 1.55:1 | 2.04:1 | #33493B (0.17) | #010410 | 0.969 at 2048 | none |
| grassland.night@door1p | door1p | -47.8 (moon) | 48.2 | 0.0/6.18 (11.0) | 1.05:1 | None:1 | #39513C (0.17) | #00030E | 0.969 at 2048 | none |
| grassland.day@cab1p | cab1p | 38.8 | 65.5 | 0.95/27.16 (27.99) | 3.45:1 | None:1 | #8CA158 (0.3) | None | 0.956 at 2048 | none |

Checks against canon: spawn-edge fog >= 0.9 hides the streamer's spawn edge (tech.lighting.atmosphere, tech.streaming.window); ground saturation <= 0.45 (style.material.ground_value); bands = frame and sky means tested against the Dead Rails sepia and Land or Die blue-sky bands (style.dont.*); contrast = relative luminance ratio in the same frame.

Flags (maker heuristics, not canon: train vs world under 2:1 fades on a dim phone; crush over 5% loses shape):
- grassland.dusk@door1p (door1p): train vs world 1.11:1 < 2:1
- grassland.night (roof3p): train vs world 1.57:1 < 2:1
- grassland.night phone (roof3p): train vs world 1.55:1 < 2:1
- grassland.night@door1p (door1p): train vs world 1.05:1 < 2:1; crush 6.18% > 5% (train 11.0%)
- grassland.day@cab1p (cab1p): crush 27.16% > 5% (train 27.99%)

Limits: Previews are approximations, not Roblox: Cycles + a numpy post (filmic curve, Atmosphere fog from depth, bloom, sun rays, ColorCorrection). Skybox, Future light falloff and Roblox tone mapping are not modelled; phone variants assume no shadows and no Bloom/SunRays (tech.lighting.post_low_quality). The train is a stand-in (livery open, OQ-025). Studio test pending (owner).
