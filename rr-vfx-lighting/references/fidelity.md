# Preview fidelity (read when presenting previews or when a critic doubts one)

Previews exist to compare presets and catch bad ideas cheaply. They are not Roblox. Say "preview", never
"in game"; every runtime claim stays "Studio test pending (owner)".

## Lighting (`lookdev_bpy.py`: Cycles + numpy post)
| Roblox | preview | trust |
|---|---|---|
| ClockTime, GeographicLatitude | sun from hour angle and latitude, declination 0 (equinox); east = `preview.east_axis` (default +Z, train heading north) | direction approximate; print Lighting:GetSunDirection() in Studio (demo key U) and compare with facts sun.dir_roblox |
| Brightness, ColorShift_Top | sun strength = Brightness x SUN_K; colour warms near the horizon, plus ColorShift_Top | relative only |
| night | moon opposite the sun at MOON_K strength, cool tint | weakest mapping |
| ColorShift_Bottom | shadowless fill from the opposite side | rough |
| OutdoorAmbient, EnvironmentDiffuseScale | world light (occluded by geometry) | relative |
| Ambient | unoccluded emission term on every surface | rough |
| Atmosphere Density, Haze | fog = 1 - exp(-(FOG_K x Density + HAZE_K x Haze x Density) x distance); FOG_K puts Density 0.3 at ~95% by 2048 studs | calibrated to canon intent (haze hides the spawn edge), not measured in Roblox |
| Atmosphere Color, Decay, Glare | horizon = Color, zenith blends Roblox's default blue toward Decay by density and haze; glare glow near the sun | skybox not modelled: thin haze can look bluer in Studio |
| ExposureCompensation, tone mapping | 2^EC x EXPO_K into an ACES-fit curve | Roblox's curve differs |
| Bloom, SunRays | bright-pass blur; radial blur from the sun | shape only |
| ColorCorrection | brightness, contrast, saturation, tint in display space | close |
| phone fallback | no shadows, no Bloom or SunRays | assumed from tech.lighting.post_low_quality |
| local lights | spot/point lights at Brightness x LIGHT_K x Range^2 W, no Range cutoff | rough |
Calibration constants print in `canon_used.json`. Cameras (lookdev_bpy.py `CAMERAS`; an unknown name is an error):
roof3p (coach B roof, eye tech.camera.eye_3p), door1p (leaning out of coach A's doorway, eye tech.camera.eye_1p,
looking along the train), cab1p (loco cab facing the firebox, eye tech.camera.cab_view above rail), coach1p (inside
coach A facing the power-box end); FOV tech.camera.fov_v. Phone fallbacks render at tech.ui_platform.phone
(844 x 390) with their own view and depth, so phone POVs are true phone framing. The stand is a blockout built
from canon's proposed envelope (tech.units.gauge, stock_width, stock_roof, stock_floor; OQ-030): two coaches with
cream interiors and a doorway (tech.units.train_doorway), hazard-yellow capped-post roof rails (style.form.rails),
an open cab shell with backhead, firebox neon and the canon cab lamp and firebox lights; poles every 128, ballast
24, tunnel bore from world.prefabs.10. The train paint is a stand-in (navy, cream band): livery is open (OQ-025).

## Effects (`fxsim.py`: Pillow)
Faithful to the data: rates, bursts, ranges, spread, acceleration, drag half-life, GlobalWind drift at train
speed, sequences with envelopes, LightEmission blend, LightInfluence/Brightness, VelocityParallel streaks, box
emitters, debris under Roblox gravity 196.2 x gravity_scale. Approximate: textures (procedural stand-ins),
Squash shape, particles lit only by a scene factor, fog on particles, depth test at particle centres, lights shown
as glow dots (effect lights do not light the stand's surfaces), no ground collision. Overdraw is measured on the POV
frame (layers per pixel), a proxy for phone cost. Per preset and POV: visible = particle centres in frame and in
front of the depth plate; hidden = behind the train or ground; off-screen; share of the screen its sprites cover;
mean and 90th-percentile luma change over those pixels. Loops run at steady state (Speed gameplay.speed.fast);
bursts fire after the loops warm up. Phone POVs use the phone tier's rate scale.

## What only Studio can settle (hand to the owner)
Real texture look, Future/Realistic light falloff, the sun's real heading, post effects on a phone, particle
cost on a phone (F9 / MicroProfiler during tech.streaming.live_check), GlobalWind side effects on Terrain grass
and clouds (lower `meta.wind_scale` if clouds race).
