# rr-vfx-lighting · design notes (2026-09-28)

## Job
Roblox-native look-dev for Risky Rails: particle, beam, trail and light presets and per-biome, per-time-of-day
lighting looks, kept as JSON data, turned into Luau apply-modules, previewed in the cloud with honest caveats,
budgeted for phones, judged by multiuse-critic.

## Pipeline
```
bible get (canon slice) -> vfx init WORK (copy of presets/, the source of truth for this run; --presets WORK after)
  -> vfx.py validate   schema + Roblox ranges, canon values (number next to the property), colour gate, OQ refs,
                       every look x override, budget-set membership, flash safety
  -> vfx.py budget     concurrency sets (worst crisis at once) vs phone/PC tiers
  -> vfx.py preview all NAMES   lookdev_bpy.py plates per look x camera (roof3p, door1p, near: cab1p, coach1p) + phone
                       plates at 844x390; fxsim.py strips + POV composites (PC and phone rates) with per-preset
                       visibility; ONE board: contact.png (phone POV 1:1 + views), closeups.png (strips 1:1),
                       facts.md, manifest.json. `preview vfx NAMES` rebuilds POVs + board over existing plates.
  -> vfx.py crit --from PREVIEW   CRIT/rubric.md = critic rubric + Profile F; brief from the manifest (one critic)
  -> critic_kit.py build --profile F -> independent critic (never self-scored)
  -> vfx.py build [--only NAMES]  RR_FXPresets.lua + RR_LightingPresets.lua (generated) + RR_VFX.lua, RR_Lighting.lua,
                       RR_FXDemo.client.lua, studio_lighting_setup.lua, README with wiring; luaparse + bible check
  -> luatest.py        runtime logic in Lua 5.1 (lupa) against Roblox stubs
```

## Files
- `presets/vfx.json` 13 presets (steam x2, smoke, sparks x3 incl. brake, coal dust, firebox glow, headlamp, glass,
  derail explosion, boiler burst, rain) + 2 trails + declared effect colours + the preview stand (anchors as canon
  envelope expressions, near cameras).
- `presets/lighting.json` base + 5 times (day, golden, dusk on grassland only, night, storm) + 5 biomes + 2 overrides
  (tunnel_under canon, overbridge_flash proposed, marked flash) + preview sets (default looks, POV sets).
- `presets/budgets.json` phone and PC tiers, per-priority rate scale, concurrency sets. Default of OQ-029.
- `scripts/vfx.py` (stdlib CLI), `preview.py` (plan, board, crit), `fxsim.py` (Pillow), `lookdev_bpy.py` (bpy + numpy),
  `luatest.py` (lupa), `selftest.py`.
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
   merged into CRIT/rubric.md so critic_kit.py works unchanged. One board and one critic per pack
   (rr-mission-control: one critic per mission).
9. **Visibility is measured, not eyeballed** (trial 2026-09-28: brake sparks were invisible from every roof view and
   nothing said so): per-preset visible / hidden / covered per POV, a WARN under 0.1% of the screen, cameras near
   each anchor (cab, coach, door) so every crisis signal has a player view.
10. **Work copy always**: runs never edit the shipped library; every command prints the folder it read.
11. **Runtime start rules**: crisis and event loops start off; look-driven presets follow the look even when
    attached late; burst lights are owned by the burst (a refresh used to switch flashes off mid-burst).
12. **Flash safety**: one flashes setting softens pulses, freezes flicker and skips flash overrides
    (av.feel.flash_limit, OQ-032), matching rr-game-feel.

## Canon plugged in (read at run time, never copied)
tech.camera.* (eyes, FOV, cab_view), tech.units.* (segment, poles, train length, ballast, gauge, stock_width,
stock_roof, stock_floor, train_doorway), tech.ui_platform.phone, tech.streaming.window, gameplay.speed.*,
tech.lighting.*, style.* tokens (incl. style.form.rails, style.thumb.glow), style.dont.*, av.vfx.*, world.prefabs.10.

## Open decisions recorded in the bible
OQ-026 time of day (default C: looks change only with biome or fork modifier), OQ-027 weather (default A:
rain shelved), OQ-028 derail explosion (default A: derail stays a breakdown; preset unassigned),
OQ-029 phone budget (default A: this skill's numbers). Platform facts added: technology_api,
light_range_max 120, post_low_quality. Drift noted: tech.lighting.technology still says "Future".

## Limits
No Studio: every runtime claim is "Studio test pending (owner)". Skybox, Future light falloff, Roblox tone
mapping and particle textures are approximated. Custom textures and publishing are the owner's gate.
