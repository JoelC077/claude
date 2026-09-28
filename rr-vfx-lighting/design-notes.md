# rr-vfx-lighting · design notes (2026-09-28)

## Job
Roblox-native look-dev for Risky Rails: particle, beam, trail and light presets and per-biome, per-time-of-day
lighting looks, kept as JSON data, turned into Luau apply-modules, previewed in the cloud with honest caveats,
budgeted for phones, judged by multiuse-critic.

## Pipeline
```
bible get (canon slice) -> presets/*.json (source of truth)
  -> vfx.py validate   schema + Roblox ranges, canon refs, colour gate, OQ refs, per-preset budget
  -> vfx.py budget     concurrency sets (worst crisis at once) vs phone/PC tiers
  -> vfx.py preview    lighting: lookdev_bpy.py (Cycles + numpy post: fog, bloom, sun rays, colour correction)
                       vfx: fxsim.py (Roblox particle semantics re-implemented, Pillow) -> strips + POV composite
                       -> contact sheets via multiuse-critic/contact_sheet.py + facts.md (measured)
  -> vfx.py crit       CRIT/rubric.md = critic rubric + Profile F (effects and lighting); brief from canon
  -> critic_kit.py build --profile F -> independent critic (never self-scored)
  -> vfx.py build      RR_FXPresets.lua + RR_LightingPresets.lua (generated) + RR_VFX.lua, RR_Lighting.lua,
                       RR_FXDemo.client.lua, studio_lighting_setup.lua; luaparse + bible check gates
```

## Files
- `presets/vfx.json` 12 presets (steam x2, smoke, sparks x2, coal dust, firebox glow, headlamp, glass,
  derail explosion, boiler burst, rain) + 2 trails + declared effect colours.
- `presets/lighting.json` base + 4 times (day, golden, night, storm) + 5 biomes (grassland, cutting, viaduct,
  yard, depot) + 2 overrides (tunnel_under canon, overbridge_flash proposed).
- `presets/budgets.json` phone and PC tiers, per-priority rate scale, concurrency sets. Default of OQ-029.
- `scripts/vfx.py` (stdlib), `fxsim.py` (Pillow), `lookdev_bpy.py` (bpy + numpy), `selftest.py`.
- `assets/luau/` hand-written runtime modules; `references/` presets.md, fidelity.md, rubric-fx.md.

## Decisions (with why)
1. **Data first.** JSON holds Roblox property names and typed values; Luau is generated, so previews,
   budgets and the game read one source. Colours are `@bible.key` tokens where one fits, else a declared
   `$effect` colour with a reason; lighting intensities (Ambient, OutdoorAmbient, ColorShift, Tint) are
   light levels, not palette colours: exempt from the palette gate, still band-checked (sepia, blue sky).
2. **The train never moves.** Particles drift back through `Workspace.GlobalWind = -forward * Speed`
   (documented: particles with WindAffectsDrag and Drag > 0 follow it), so steam streams like a moving train.
   Trails need moving attachments: never on the train body, only on flung debris.
3. **Signal over ambience.** Every preset has a priority (1 crisis signal, 2 feedback, 3 ambience); phones
   scale rate by priority (1.0 / 0.7 / 0.5), so the valve jet still reads when rain is cut.
4. **Speed link is canon** (av.vfx.speed_link): chimney rates lerp idle..max over 0..gameplay.speed.fast.
5. **Lighting.Technology is deprecated and not scriptable** (RBXD, recorded as tech.lighting.technology_api):
   canon "Future" maps to LightingStyle Realistic + PrioritizeLightingQuality, set by the Studio setup script.
6. **Looks are resolved in Python** for every allowed biome.time; only overrides (tunnel, overbridge) apply
   at runtime as add/mul/lerp ops, so Luau stays small and matches the previews exactly.
7. **Previews are approximations with measured facts**, not claims about Roblox: fog opacity at the
   streamer spawn edge, train-vs-world value contrast, ground saturation vs canon, frame-mean band check,
   particle overdraw on the POV. `references/fidelity.md` lists every mapping and what to verify in Studio.
8. **Critic Profile F** (signal, form and motion, colour and value, phone read, style match, polish) is
   merged into CRIT/rubric.md so critic_kit.py works unchanged.

## Canon plugged in (read at run time, never copied)
tech.camera.* (eyes, FOV), tech.units.* (segment, poles, train length, ballast), tech.streaming.window,
gameplay.speed.*, tech.lighting.*, style.* tokens, style.dont.*, av.vfx.*, world.prefabs.10 (tunnel bore).

## Open decisions recorded in the bible
OQ-026 time of day (default C: looks change only with biome or fork modifier), OQ-027 weather (default A:
rain shelved), OQ-028 derail explosion (default A: derail stays a breakdown; preset unassigned),
OQ-029 phone budget (default A: this skill's numbers). Platform facts added: technology_api,
light_range_max 120, post_low_quality. Drift noted: tech.lighting.technology still says "Future".

## Limits
No Studio: every runtime claim is "Studio test pending (owner)". Skybox, Future light falloff, Roblox tone
mapping and particle textures are approximated. Custom textures and publishing are the owner's gate.
