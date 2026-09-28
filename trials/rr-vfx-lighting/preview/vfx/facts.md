# Effects: measured on the simulation (2026-09-28)

Side strips: steady state at Speed 35.0 (gameplay.speed.normal) on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar (tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.

| preset | kind | priority | anchor | phone live (budget formula) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|
| steam_chimney | loop | 2 | Chimney | 40 | 38/38/38 | 3.66 | av.vfx.speed_link, gameplay.speed.drives |
| smoke_chimney | loop | 3 | Chimney | 10 | 15/15/15 | 2.61 | av.vfx.speed_link |
| sparks_brake | loop | 2 | BrakeShoe | 42 | 29/29/29 | 23.7 | gameplay.run.brake_formula, gameplay.crisis.pressure |
| coal_dust | burst | 2 | Firebox | 15 | 20/20/11/20 | 23.7 | gameplay.crisis.firebox, gameplay.fuel.shovel_pct |

POV composites (roof3p, particles over the lookdev plate, Speed = gameplay.speed.fast):

| composite | look | presets | live | overdraw max / p95 / mean | screen covered |
|---|---|---|---|---|---|
| pov_crisis | grassland.day | steam_chimney, smoke_chimney, steam_valve | 94 | 33 / 21 / 5.75 | 2.7% |
| pov_cruise | grassland.day | steam_chimney, smoke_chimney | 66 | 30 / 16 / 3.7 | 4.0% |
| pov_boiler | grassland.day | boiler_burst, smoke_chimney | 56 | 10 / 8 / 3.45 | 0.8% |
| pov_night | grassland.night | steam_chimney, smoke_chimney, headlamp, firebox_glow | 72 | 31 / 18 / 4.47 | 3.8% |

Budgets (assumed (OQ-029 default A): not canon until the owner decides; re-measure at the alpha live check (tech.streaming.live_check)):

- phone cruise: steady 54, peak 54, fill 3183 stud^2, lights 3 -> within
- phone crisis_stack: steady 140, peak 155, fill 3528 stud^2, lights 6 -> within
- phone night_tunnel: steady 54, peak 54, fill 3183 stud^2, lights 4 -> within
- phone storm_crisis: steady 384, peak 384, fill 3565 stud^2, lights 5 -> within
- phone boiler_fail: steady 14, peak 68, fill 2916 stud^2, lights 4 -> within
- phone derail: steady 54, peak 122, fill 5073 stud^2, lights 4 -> within
- phone arrival_brake: steady 96, peak 96, fill 3200 stud^2, lights 3 -> within
- phone pressure_brake: steady 132, peak 147, fill 3541 stud^2, lights 4 -> within
- phone night_brake: steady 96, peak 111, fill 3226 stud^2, lights 5 -> within
- phone crisis_stack_brake: steady 182, peak 197, fill 3546 stud^2, lights 6 -> within
- pc cruise: steady 83, peak 83, fill 4762 stud^2, lights 3 -> within
- pc crisis_stack: steady 170, peak 190, fill 5119 stud^2, lights 6 -> within
- pc night_tunnel: steady 83, peak 83, fill 4762 stud^2, lights 4 -> within
- pc storm_crisis: steady 665, peak 665, fill 5208 stud^2, lights 5 -> within
- pc boiler_fail: steady 26, peak 80, fill 3294 stud^2, lights 4 -> within
- pc derail: steady 83, peak 151, fill 6653 stud^2, lights 4 -> within
- pc arrival_brake: steady 143, peak 143, fill 4788 stud^2, lights 3 -> within
- pc pressure_brake: steady 179, peak 199, fill 5139 stud^2, lights 4 -> within
- pc night_brake: steady 143, peak 163, fill 4824 stud^2, lights 5 -> within
- pc crisis_stack_brake: steady 230, peak 250, fill 5144 stud^2, lights 6 -> within

Limits: Effects are simulated from the preset data with Roblox ParticleEmitter rules; textures are procedural stand-ins for the built-ins; particles are not lit by the scene beyond a LightInfluence factor; lights show as glow dots only; drift = Workspace.GlobalWind at train speed. Studio test pending (owner).
