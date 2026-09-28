# Look-dev board facts: pack = steam_chimney, smoke_chimney, sparks_brake, coal_dust; looks grassland.day, .dusk, .night

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


## Effects (side strips at Speed 35; phone live uses the budget formula at full rate)

| preset | kind | priority | anchor | phone live (budget formula) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|
| steam_chimney | loop | 2 | Chimney | 40 | 38/38/38 | 3.66 | av.vfx.speed_link, gameplay.speed.drives |
| smoke_chimney | loop | 3 | Chimney | 10 | 15/15/15 | 2.61 | av.vfx.speed_link |
| sparks_brake | loop | 2 | BrakeShoe | 42 | 29/29/29 | 23.7 | gameplay.run.brake_formula, gameplay.crisis.pressure |
| coal_dust | burst | 2 | Firebox | 15 | 20/20/11/20 | 23.7 | gameplay.crisis.firebox, gameplay.fuel.shovel_pct |

## Pack POV composites (Speed = gameplay.speed.fast 50; loops at steady state; the look's fx_on presets added)

| composite | tier | live | hidden by geometry | overdraw max | screen covered |
|---|---|---|---|---|---|
| pov_grassland.day | pc | 111 | 44 | 27 | 4.9% |
| pov_grassland.day_door1p | pc | 111 | 69 | 4 | 0.4% |
| pov_grassland.day.phone | phone | 75 | 31 | 19 | 2.0% |
| pov_grassland.dusk | pc | 111 | 44 | 27 | 4.9% |
| pov_grassland.dusk_door1p | pc | 111 | 69 | 4 | 0.4% |
| pov_grassland.dusk.phone | phone | 75 | 31 | 19 | 2.0% |
| pov_grassland.night | pc | 111 | 44 | 27 | 4.9% |
| pov_grassland.night_door1p | pc | 111 | 69 | 4 | 0.4% |
| pov_grassland.night.phone | phone | 75 | 31 | 19 | 2.0% |

- coal_dust fires inside the cab (anchor Firebox): no preview camera is in the cab, so it appears only in its time strip.
- sparks_brake sits at the loco wheels at rail level: from coach B's roof (roof3p) the train body hides it; door1p sees about half.

## Phone budget, pack-relevant sets (all PC sets within)

- phone cruise: steady 54, peak 54, fill 3183 stud^2, lights 3 -> within
- phone arrival_brake: steady 96, peak 96, fill 3200 stud^2, lights 3 -> within
- phone pressure_brake: steady 132, peak 147, fill 3541 stud^2, lights 4 -> within
- phone night_brake: steady 96, peak 111, fill 3226 stud^2, lights 5 -> within
- phone crisis_stack_brake: steady 182, peak 197, fill 3546 stud^2, lights 6 -> within

Limits: Previews are approximations, not Roblox: Cycles + a numpy post (filmic curve, Atmosphere fog from depth, bloom, sun rays, ColorCorrection). Skybox, Future light falloff and Roblox tone mapping are not modelled; phone variants assume no shadows and no Bloom/SunRays (tech.lighting.post_low_quality). Studio test pending (owner).
Limits: Effects are simulated from the preset data with Roblox ParticleEmitter rules; textures are procedural stand-ins for the built-ins; particles are not lit by the scene beyond a LightInfluence factor; lights show as glow dots only; drift = Workspace.GlobalWind at train speed. Studio test pending (owner).
