# Lighting looks: measured on the preview renders (2026-09-28)

Player view: roof3p = standing on a coach roof, eye 9.5 studs up (tech.camera.eye_3p); door1p = leaning out of a coach doorway, eye 4.5 (tech.camera.eye_1p); vertical FOV 70.0 (tech.camera.fov_v). The train never moves (identity.pillars.stable_train).

| look | cam | sun elev | luma | clip/crush % | train vs world | ground (HSL sat) | sky | spawn-edge fog | bands |
|---|---|---|---|---|---|---|---|---|---|
| grassland.day | roof3p | 38.8 | 155.3 | 0.0/0.0 | 3.56:1 | #8DA15B (0.28) | #ACBEAE | 0.956 at 2048 | none |
| grassland.day phone | roof3p | 38.8 | 156.7 | 0.0/0.0 | 3.69:1 | #91A55D (0.28) | #ACBEAE | 0.956 at 2048 | none |
| grassland.dusk | roof3p | 1.7 | 73.4 | 0.0/0.0 | 1.92:1 | #444937 (0.14) | #5E5A63 | 0.968 at 2048 | none |
| grassland.dusk phone | roof3p | 1.7 | 74.4 | 0.0/0.0 | 1.98:1 | #454A38 (0.14) | #5E5A63 | 0.968 at 2048 | none |
| grassland.night | roof3p | -47.8 (moon) | 30.3 | 0.0/0.49 | 1.64:1 | #304637 (0.18) | #01030F | 0.969 at 2048 | none |
| grassland.night phone | roof3p | -47.8 (moon) | 30.3 | 0.0/0.49 | 1.65:1 | #304637 (0.18) | #01030F | 0.969 at 2048 | none |
| grassland.day@door1p | door1p | 38.8 | 110.4 | 0.0/14.66 | 2.46:1 | #7B9148 (0.34) | #A9BDAF | 0.956 at 2048 | none |
| grassland.dusk@door1p | door1p | 1.7 | 59.6 | 0.0/14.99 | 1.2:1 | #38412E (0.17) | #5B5862 | 0.968 at 2048 | none |
| grassland.night@door1p | door1p | -47.8 (moon) | 39.3 | 0.0/26.17 | 1.23:1 | #354D39 (0.18) | #00030E | 0.969 at 2048 | none |

Checks against canon:
- spawn-edge fog: canon keeps haze to hide the streamer's spawn edge (tech.lighting.atmosphere, tech.streaming.window); below 0.9 the edge may show.
- ground saturation: canon says nothing above about 45% (style.material.ground_value).
- bands: frame and sky means tested against the Dead Rails sepia and Land or Die blue-sky bands (style.dont.*).
- train vs world: relative-luminance ratio of the train to everything around it in the same frame.

Limits: Previews are approximations, not Roblox: Cycles + a numpy post (filmic curve, Atmosphere fog from depth, bloom, sun rays, ColorCorrection). Skybox, Future light falloff and Roblox tone mapping are not modelled; phone variants assume no shadows and no Bloom/SunRays (tech.lighting.post_low_quality). Studio test pending (owner).
