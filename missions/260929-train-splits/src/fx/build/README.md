# rr-vfx-lighting export (2026-09-29) (pack: split_explosion, torn_edge_smoke, topple_dust, glass_burst)
Studio test pending (owner). Nothing here has run in Roblox Studio. Presets from /home/user/claude/missions/260929-train-splits/src/fx.
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
| split_explosion | burst p1 | SplitCore | `VFX.burst(anchor, "split_explosion")` on the event |
| torn_edge_smoke | loop p2 | TornEdge | `VFX.attach(anchor, "torn_edge_smoke")` runs from spawn |
| topple_dust | burst p1 | WreckDust | `VFX.burst(anchor, "topple_dust")` on the event |
| glass_burst | burst p1 | WindowPane | `VFX.burst(anchor, "glass_burst")` on the event |
| headlamp | loop p2 | Headlamp | `VFX.attach(anchor, "headlamp")`; the current look switches it (Lighting.apply) |
