---
name: rr-vfx-lighting
description: "Risky Rails (Roblox) look-dev for effects and lighting. Keeps particle, beam, trail and light presets (chimney steam and smoke that follow Speed, valve jet, power-box, axle and brake sparks, coal dust, firebox glow, headlamp, glass, boiler burst, derail explosion, rain) and Lighting, Atmosphere, ColorCorrection, Bloom and SunRays looks per biome and time of day (day, golden, dusk, night, storm, tunnel, overbridge) as JSON; exports Luau modules; previews a pack as one board from the players' roof, door and cab views on PC and phone (Cycles plus a particle simulator, per-effect visibility facts); checks phone budgets, canon values, colours and Roblox ranges; hands judgement to multiuse-critic. Use whenever Risky Rails work touches VFX, particles, steam, smoke, sparks, explosions, weather, fog, haze, sky, time of day, dusk, night, tunnels, bloom, colour grading or lighting mood, or asks if effects run or read on phones; also for effects or lighting in rr-mission-control missions. Not for UI screens or 3D models."
---

# RR VFX and Lighting

Effects and lighting for Risky Rails as data: presets in JSON, Luau generated from them, previews and budgets
measured by scripts, quality judged by an independent critic. Precise, proactive, no fluff.

Paths (find by glob, never hard-code): `<fx>` = this folder. `vfx` below = `python3 <fx>/scripts/vfx.py`. The
scripts find rr-bible and multiuse-critic themselves (sibling folder first, then `~/.claude/skills`, then
`/home/user`; env `RR_BIBLE_SKILL`, `RR_CRITIC_SKILL` override) and print the critic folder they use.
For a shell recipe use the same order: `ls -d <fx>/../rr-bible 2>/dev/null || find ~/.claude/skills /home/user -maxdepth 5 -path '*rr-bible/SKILL.md'`.

## Canon first
Read the slice you need through rr-bible, never from memory, never copied into presets as prose:
`python3 <bible>/scripts/bible.py get av.vfx --values` (effects), `get tech.lighting`, `get style.dont`,
`get style.light`, `get gameplay.speed`, `get tech.camera`, `get tech.units`, `get questions`.
Presets cite canon by key (`{"v": 0.3, "canon": "tech.lighting.atmosphere"}`, `"@style.world.brass"`); validate
compares the value with the number canon gives for that property (`Saturation +0.12`, `Range 9`; hex digits never
count; add `"match": "regex"` when the canon text names the number differently). Missing canon: record it with
`bible.py add-question` (options + default) and label the work "assumed (OQ-nnn default)". In a trial or a
read-only run use `add-question --dry-run`, leave `oq` out and write `none: ... proposed` (an `oq` must be a real
OQ id). The owner's new words beat canon: do the work, then record it.

## Workflow
1. **Work copy, always:** `vfx init <W>` copies the shipped presets to a work folder (a mission's `src/fx`, a trial
   folder); pass `--presets <W>` to every command after it. Every command prints the folder it used; "shipped
   library" means you are reading the skill's own copy, which you never edit. Then pick or edit presets in
   `<W>` (`vfx.json` effects, `lighting.json` looks, `budgets.json`) after reading `references/presets.md`.
   `vfx list`, `vfx show NAME` (a preset, trail or look such as `grassland.night` or `cutting.day+tunnel_under`).
   **A named effect or look the pack lacks: author it** (presets.md, Adding an effect or a look: anchor, time,
   budget sets, near camera). Never silently substitute the nearest preset (golden is not dusk).
2. **Gate:** `vfx validate --strict --presets <W>` (schema and ranges, canon values, colour tokens and bands, OQ
   refs, every look alone and with every override, every preset in a budget set, flash safety) and
   `vfx budget --presets <W>`. Both must pass.
3. **Preview the pack as one board:** `vfx preview all NAMES --presets <W> --out <P> [--gif]`, NAMES = the
   requested effects and looks (about 1 to 2 minutes; `--quick` only for smoke tests). It renders each look from
   the roof (roof3p) and doorway (door1p), the camera nearest each effect's anchor (cab1p, coach1p), and a phone
   fallback at the phone resolution; composites the effects over those plates at PC and phone rates; and writes
   `<P>/board/`: `contact.png` (phone POV at 1:1 + player views), `closeups.png` (effect strips at 1:1),
   `facts.md` (looks, per-effect visible / hidden / off-screen / share of screen / luma change per POV,
   budgets, limits) and `manifest.json`. Tuning an effect afterwards: `vfx preview vfx NAMES ...` reuses the
   plates and rebuilds the board in seconds. No NAMES = the default sets (library upkeep).
4. **Maker check before any critic (cheap, required):** open `board/contact.png` once and read the facts
   Visibility lines. Fix every `WARN` (an effect under 0.1% of the screen in every POV: players may never see it;
   presets.md, Visible from the players' views) and blank or broken views, or say in the brief why not. Flags on
   looks (train vs world under 2:1, crush over 5%) are heuristics to weigh, not canon. Say "preview", never
   "in game"; `references/fidelity.md` lists what is approximated.
5. **Judge (never self-score): one critic, one board.** `vfx crit <CRIT> --pass N --from <P> --presets <W>`
   writes `CRIT/rubric.md` (multiuse-critic rubric + Profile F: signal, form and motion, colour and value, phone
   read, style match, polish), the pass files and a brief built from the manifest (the pack's purposes and only
   the OQs it depends on), then prints the `critic_kit.py build ... --profile F` command with absolute paths.
   A preview board is judged with Profile F; Profile B is for UI screens (pass `--profile` only if the owner
   asks). Continue with `<critic>/SKILL.md` steps 4-9 (fresh critic, delta passes, bar 8 unless the owner said
   otherwise). No Agent tool: follow rr-mission-control's critic route (remote session, handoff to the caller, or
   a labelled UNCERTIFIED self-review capped at bar-1).
6. **Fix** in the JSON only, re-run 2-5. Keep the earlier round's JSON in `CRIT/round-N/` before editing. Turn
   each critic finding into a preset or look change with its done-when number from facts.md.
7. **Export:** `vfx build --presets <W> --out <E> [--only NAMES]` writes `RR_FXPresets.lua` and
   `RR_LightingPresets.lua` (generated; `--only` = the pack plus its looks' `fx_on`), `RR_VFX.lua`,
   `RR_Lighting.lua`, `RR_FXDemo.client.lua`, `studio_lighting_setup.lua` and a README with a wiring row per
   preset; then runs luaparse (install once: `npm i --prefix ~/.cache/rr-tools luaparse`; else a balance check,
   named in the output) and `bible check` on every file. Build PASS is required before handover. Handover says:
   "Studio test pending (owner)".
8. **Record** what the owner decides (`bible.py decide OQ-nnn X --by owner`, then update the preset and the
   affected facts). Presets never become canon by themselves.

## Inside a mission (rr-mission-control)
Effects and lighting are a deliverable of kind `mixed`: `vfx init <M>/src/fx`, previews in `<M>/src/fx/preview/`,
one critic in `<M>/critique-fx-*` on the board, export in `<M>/export/fx/` (`--only` the pack). The maker's order
file points at this SKILL.md steps 1-7; pre-flight = step 2 plus `vfx build --no-check` succeeding.

## Runtime (what the owner wires in Studio)
- `VFX.attach(anchor, "steam_chimney")`, `VFX.burst(anchor, "coal_dust")`, `VFX.setActive(name, on)`,
  `VFX.setSpeed(speed, forward)` on every throttle change, `VFX.budget()`.
- Loops start ON except priority-1 crisis loops and presets marked `"start": "off"` (brake sparks): attach them at
  spawn and `setActive` on the event. Presets a look switches (headlamp, rain) follow the current look even when
  attached after `Lighting.apply`. `attach(anchor, name, {enabled = true/false})` overrides both.
- `Lighting.apply("grassland.day")`, `Lighting.push("tunnel_under")`/`pop` from the streamer,
  `Lighting.push("overbridge_flash")` (pops itself).
- Flashes setting (av.feel.flash_limit, OQ-032): `VFX.setFlashes(on)` and `Lighting.setFlashes(on)` from the same
  player setting rr-game-feel uses: pulses soften, flicker freezes, flash overrides are skipped.
- `studio_lighting_setup.lua` once in the command bar; `RR_FXDemo.client.lua` for a quick Studio look (remove
  before publishing). `scripts/luatest.py` runs this logic in a Lua VM against stubs.

## Design rules (why the presets look like this)
- **The train never moves** (identity.pillars.stable_train): drift comes from `Workspace.GlobalWind = -forward x
  Speed`; particles need `WindAffectsDrag` and `Drag > 0`. Trails need motion: debris only, never the train body.
- **Signal over ambience:** priority 1 crisis effects keep full rate on phones; ambience (3) is cut first by the
  runtime budget guard. A crisis effect must be the loudest thing in frame from a player's view (facts.md).
- **Seen from where players stand:** the train body hides anything at rail level from the roof. Rail-level and
  interior effects throw past the body side and carry a light, and are judged from the door or near camera.
- **Readable, never horror** (identity.tone.*): tunnels and night stay readable (train-vs-world contrast in
  facts.md); haze stays because it hides the streamer's spawn edge (spawn-edge fog in facts.md).
- **Palette:** tokens or declared effect colours only; lighting intensities are light levels, band-checked
  against the Dead Rails sepia and Land or Die blue-sky looks (style.dont.*). Red stays the one 2D danger signal.
- **Phones first** (identity.audience.devices): the board's hero is the phone POV at 1:1; phone fallback = no
  shadows, Bloom or SunRays, rates scaled by priority; additive glows wash out on bright skies, lit smoke goes
  dark at night: both show in previews.
- Lighting.Technology is deprecated and not scriptable; the setup script sets LightingStyle and
  PrioritizeLightingQuality (tech.lighting.technology_api).

## Open decisions (defaults in use; the owner decides)
OQ-026 time of day (default: looks change only with biome or fork modifier; golden for lobby and results; dusk
has no slot), OQ-027 weather (default: rain and storm shelved), OQ-028 derail explosion (default: derailment stays
a breakdown), OQ-029 phone budget (default: `budgets.json`), OQ-025 train livery (previews use a stand-in train),
OQ-030 rolling-stock envelope (the preview stand uses its proposed numbers). Brake sparks are proposed (canon has
the brake, not the effect): ask the owner whether roof players must see them. Label outputs that depend on these
"assumed (OQ-nnn default)". `bible.py get OQ-026` shows the options.

## Honest limits
- Cloud: headless bpy (Cycles only), Pillow, luaparse if installed, lupa for luatest; no Roblox Studio or Studio
  MCP. Nothing here has run in Roblox: textures, light falloff, tone mapping, sun heading, lights on surfaces from
  effects and phone cost need the owner's Studio test (`references/fidelity.md`, last section).
- Built-in textures stand in for custom flipbooks; uploading assets, publishing and spending are the owner's gate.
- Never change the owner's Claude config, message players or publish; prepare, dry-run, hand over.

## Maintain
`python3 <fx>/scripts/selftest.py` exercises every command on temp copies (must print all passed; `--no-render`
skips Blender); `python3 <fx>/scripts/luatest.py` runs the Luau runtime in Lua 5.1 (selftest calls it). Scripts
never write `__pycache__`; remove any you find.
