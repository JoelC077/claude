---
name: rr-vfx-lighting
description: "Risky Rails (Roblox) look-dev for effects and lighting. Keeps ParticleEmitter, Beam, Trail and light presets (chimney steam and coal smoke that follow Speed, safety-valve jet, power-box and axle sparks, coal dust, firebox glow, headlamp, glass, boiler burst, derail explosion, rain) and Lighting, Atmosphere, ColorCorrection, Bloom and SunRays looks per biome and time of day (day, golden, night, storm, tunnel and overbridge overrides) as JSON, exports Luau apply-modules plus a Studio setup script, previews them in the cloud (Blender Cycles and a particle simulator, with honest caveats), checks phone budgets, canon colours and Roblox ranges, and hands judgement to multiuse-critic. Use whenever Risky Rails work touches VFX, particles, steam, smoke, sparks, explosions, weather, fog, haze, sky, time of day, night, tunnel darkness, bloom, colour grading or lighting mood, or asks if effects will run on phones; also for effects or lighting deliverables in rr-mission-control missions. Not for UI screens or 3D models."
---

# RR VFX and Lighting

Effects and lighting for Risky Rails as data: presets in JSON, Luau generated from them, previews and budgets
measured by scripts, quality judged by an independent critic. Precise, proactive, no fluff.

Paths (find by glob, never hard-code): `<fx>` = this folder;
`<bible>` = `dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path '*rr-bible/SKILL.md' 2>/dev/null | head -1)"`;
`<critic>` = same with `*multiuse-critic/SKILL.md`. The scripts find both themselves (env overrides
`RR_BIBLE_SKILL`, `RR_CRITIC_SKILL`, `RR_VFX_PRESETS`). `vfx` below = `python3 <fx>/scripts/vfx.py`.

## Canon first
Read the slice you need through rr-bible, never from memory, never copied into presets as prose:
`python3 <bible>/scripts/bible.py get av.vfx --values` (effects), `get tech.lighting` (lighting, platform facts),
`get style.dont`, `get style.light`, `get gameplay.speed`, `get tech.camera`, `get questions`.
Presets cite canon by key (`{"v": 0.3, "canon": "tech.lighting.atmosphere"}`, `"@style.world.brass"`) and
`vfx validate` proves they agree. Missing canon: record it with `bible.py add-question` (options + default) and
label the work "assumed (OQ-nnn default)". The owner's new words beat canon: do the work, then record it.

## Workflow
1. **Pick or edit presets** in `<fx>/presets/` (`vfx.json` effects, `lighting.json` looks, `budgets.json`).
   Read `references/presets.md` before editing: value forms, ops, colours, Roblox limits. `vfx list` shows
   everything; `vfx show NAME` one preset, trail or look (`grassland.night`, `cutting.day+tunnel_under`).
2. **Gate:** `vfx validate --strict` (schema and ranges, canon agreement, colour tokens and bands, OQ refs,
   single-preset phone budget) and `vfx budget` (concurrency sets on phone and PC). Both must pass.
3. **Preview:** `vfx preview all --out <dir> [--gif]` (about 1 minute; `--quick` only for smoke tests).
   Writes `<dir>/lighting/` (lookdev renders from the player's roof and doorway views, phone fallbacks,
   `contact.png`, `closeups.png`, `facts.md`) and `<dir>/vfx/` (side strips per preset, POV composites over the
   lookdev plates, GIFs for the owner, sheets, `facts.md` with budgets and overdraw). Look at each `contact.png`
   yourself once; fix blank or broken views before any critic sees them. Say "preview", never "in game";
   `references/fidelity.md` lists what is approximated.
4. **Judge (never self-score):** `vfx crit <CRIT> --pass N --from <dir>/lighting` (and a second CRIT for
   `<dir>/vfx`). It writes `CRIT/rubric.md` (multiuse-critic rubric + Profile F: signal, form and motion,
   colour and value, phone read, style match, polish), the pass files and a brief built from canon, then prints
   the `critic_kit.py build ... --profile F` command. Continue with `<critic>/SKILL.md` steps 4-9 (fresh critic,
   delta passes, bar 8 unless the owner said otherwise). No Agent tool: follow rr-mission-control's critic route
   (remote session, handoff to the caller, or a labelled UNCERTIFIED self-review capped at bar-1).
5. **Fix** in the JSON only, re-run 2-4. Keep the earlier round's JSON in `CRIT/round-N/` before editing.
6. **Export:** `vfx build --out <dir>/export` writes `RR_FXPresets.lua` and `RR_LightingPresets.lua`
   (generated), `RR_VFX.lua`, `RR_Lighting.lua`, `RR_FXDemo.client.lua`, `studio_lighting_setup.lua` and a
   README; then runs luaparse (install once: `npm i --prefix ~/.cache/rr-tools luaparse`; else a balance check,
   named in the output) and `bible check` on every file.
   Build PASS is required before handover. Handover says: "Studio test pending (owner)".
7. **Record** what the owner decides (`bible.py decide OQ-nnn X --by owner`, then update the preset and the
   affected facts). Presets never become canon by themselves.

## Inside a mission (rr-mission-control)
Treat effects and lighting as a deliverable of kind `mixed`: presets live in `<M>/src/fx/` (copy `presets/` there
and set `RR_VFX_PRESETS=<M>/src/fx`), previews in `<M>/src/fx/preview/`, the critic in `<M>/critique-fx-*`,
export in `<M>/export/fx/`. The maker's order file points at this SKILL.md steps 1-6; pre-flight = step 2 plus
`vfx build --no-check` succeeding. Contact sheets and facts.md already have the critic's layout.

## Runtime (what the owner wires in Studio)
- `VFX.attach(anchor, "steam_chimney")`, `VFX.burst(anchor, "coal_dust")`, `VFX.setActive(name, on)`,
  `VFX.setSpeed(speed, forward)` on every throttle change, `VFX.budget()`.
- `Lighting.apply("grassland.day")`, `Lighting.push("tunnel_under")`/`pop` from the streamer,
  `Lighting.push("overbridge_flash")` (pops itself). Looks switch the headlamp and rain presets via `fx_on`.
- `studio_lighting_setup.lua` once in the command bar; `RR_FXDemo.client.lua` for a quick Studio look.

## Design rules (why the presets look like this)
- **The train never moves** (identity.pillars.stable_train): drift comes from `Workspace.GlobalWind = -forward x
  Speed`; particles need `WindAffectsDrag` and `Drag > 0`. Trails need motion: debris only, never the train body.
- **Signal over ambience:** priority 1 crisis effects keep full rate on phones; ambience (3) is cut first by the
  runtime budget guard. A crisis effect must be the loudest thing in frame.
- **Readable, never horror** (identity.tone.*): tunnels and night stay readable (train-vs-world contrast in
  facts.md); haze stays because it hides the streamer's spawn edge (spawn-edge fog in facts.md).
- **Palette:** tokens or declared effect colours only; lighting intensities are light levels, band-checked
  against the Dead Rails sepia and Land or Die blue-sky looks (style.dont.*). Red stays the one 2D danger signal.
- **Phones first** (identity.audience.devices): judge the phone fallback (no shadows, Bloom or SunRays) and
  the budget sets; additive glows on bright skies wash out, lit smoke goes dark at night: both show in previews.
- Lighting.Technology is deprecated and not scriptable; the setup script sets LightingStyle and
  PrioritizeLightingQuality (tech.lighting.technology_api).

## Open decisions (defaults in use; the owner decides)
OQ-026 time of day (default: looks change only with biome or fork modifier; golden for lobby and results),
OQ-027 weather (default: rain and storm shelved), OQ-028 derail explosion (default: derailment stays a
breakdown; `derail_explosion` unassigned), OQ-029 phone budget (default: `budgets.json`). Label outputs that
depend on them "assumed (OQ-nnn default)". `bible.py get OQ-026` shows the options.

## Honest limits
- Cloud: headless bpy (Cycles only), Pillow, luaparse if installed; no Roblox Studio or Studio MCP. Nothing here
  has run in Roblox: textures, light falloff, tone mapping, sun heading and phone cost need the owner's Studio
  test (`references/fidelity.md`, last section).
- Built-in textures stand in for custom flipbooks; uploading assets, publishing and spending are the owner's gate.
- Never change the owner's Claude config, message players or publish; prepare, dry-run, hand over.

## Maintain
`python3 <fx>/scripts/selftest.py` exercises every command on temp copies (must print all passed; add
`--no-render` to skip Blender). Remove `__pycache__` after running scripts.
