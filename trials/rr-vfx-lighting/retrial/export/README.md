# rr-vfx-lighting export (2026-09-28) (pack: steam_chimney, smoke_chimney, sparks_brake, coal_dust, grassland.day, grassland.dusk, grassland.night)
Studio test pending (owner). Nothing here has run in Roblox Studio. Presets from /home/user/claude/trials/rr-vfx-lighting/retrial/fx.
1. ReplicatedStorage > folder `RRFX`: RR_FXPresets, RR_LightingPresets, RR_VFX, RR_Lighting as ModuleScripts
   (Rojo: map only these four `.lua` files into the folder; the other two files are not modules).
2. Command bar, once: paste studio_lighting_setup.lua (sets LightingStyle, PrioritizeLightingQuality, Use2022Materials;
   lists effects that would stack). It is not a script to keep in the place.
3. Optional quick look: RR_FXDemo.client.lua as a LocalScript in StarterPlayerScripts (L look, T tunnel, B burst,
   1/2/3 speed notch, F flashes); remove it before publishing.
4. Game code (client): `VFX.setSpeed(speed, forward)` every notch change; `Lighting.apply(look)`;
   `Lighting.push("tunnel_under")` / `pop` from the streamer; `VFX.setFlashes(on)` + `Lighting.setFlashes(on)` from the
   players' flashes setting (av.feel.flash_limit, OQ-032). Priority-1 loops and presets marked start off begin OFF.
5. Budgets are assumed (OQ-029 default A): not canon until the owner decides; re-measure at the alpha live check (tech.streaming.live_check). Textures are Roblox built-ins as placeholders; custom flipbooks need
   an asset upload (owner).

| preset | kind | anchor | wire it |
|---|---|---|---|
| steam_chimney | loop p2 | Chimney | `VFX.attach(anchor, "steam_chimney")` runs from spawn; rate follows `VFX.setSpeed` |
| smoke_chimney | loop p3 | Chimney | `VFX.attach(anchor, "smoke_chimney")` runs from spawn; rate follows `VFX.setSpeed` |
| sparks_brake | loop p2 | BrakeShoe | `VFX.attach(anchor, "sparks_brake")` starts off; `VFX.setActive("sparks_brake", true/false)` on the event |
| coal_dust | burst p2 | Firebox | `VFX.burst(anchor, "coal_dust")` on the event |
| headlamp | loop p2 | Headlamp | `VFX.attach(anchor, "headlamp")`; the current look switches it (Lighting.apply) |
