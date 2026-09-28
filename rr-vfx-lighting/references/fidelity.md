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
Calibration constants print in `canon_used.json`. Cameras: roof3p (coach B roof, eye tech.camera.eye_3p) and
door1p (leaning out of coach A's doorway, eye tech.camera.eye_1p), FOV tech.camera.fov_v. The stand is a
blockout (train 165 studs, poles every 128, ballast 24, tunnel bore from world.prefabs.10); livery colours are
test-stand choices (OQ-025 open), not canon.

## Effects (`fxsim.py`: Pillow)
Faithful to the data: rates, bursts, ranges, spread, acceleration, drag half-life, GlobalWind drift at train
speed, sequences with envelopes, LightEmission blend, LightInfluence/Brightness, VelocityParallel streaks, box
emitters, debris under Roblox gravity 196.2 x gravity_scale. Approximate: textures (procedural stand-ins),
Squash shape, particles lit only by a scene factor, fog on particles, depth test at particle centres, lights shown
as glow dots, no ground collision. Overdraw is measured on the POV frame (layers per pixel), a proxy for phone cost.

## What only Studio can settle (hand to the owner)
Real texture look, Future/Realistic light falloff, the sun's real heading, post effects on a phone, particle
cost on a phone (F9 / MicroProfiler during tech.streaming.live_check), GlobalWind side effects on Terrain grass
and clouds (lower `meta.wind_scale` if clouds race).
