# rr-vfx-lighting export (2026-09-28)
Studio test pending (owner). Nothing here has run in Roblox Studio.
1. ReplicatedStorage > folder `RRFX`: add RR_FXPresets, RR_LightingPresets, RR_VFX, RR_Lighting as ModuleScripts (Rojo: this folder as-is).
2. Command bar, once: paste studio_lighting_setup.lua (sets LightingStyle, PrioritizeLightingQuality, Use2022Materials; lists effects that would stack).
3. StarterPlayerScripts: RR_FXDemo.client.lua as a LocalScript for a quick look (L next look, T tunnel, B next burst, 1/2/3 speed notch).
4. In game code (client): `VFX.attach(trainAnchor, "steam_chimney")`, `VFX.setSpeed(speed, forward)` every notch change, `Lighting.apply("grassland.day")`, `Lighting.push("tunnel_under")` / `pop` from the streamer.
5. Budgets are assumed (OQ-029 default A): not canon until the owner decides; re-measure at the alpha live check (tech.streaming.live_check). Textures are Roblox built-ins as placeholders; custom flipbooks need an asset upload (owner).
