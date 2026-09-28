# Preset data (read when adding or editing a preset)

Source of truth: `vfx.json`, `lighting.json`, `budgets.json` in your work copy (`vfx.py init DIR`, then `--presets DIR`
on every command); the skill's own `presets/` is the shipped library and is never edited in a run. Luau is generated
(`vfx.py build`); never hand-edit generated Luau. After any edit: `vfx.py validate --strict`, then `vfx.py budget`.

## Values
Property names are Roblox's. `vfx.py` has the schema (`SCHEMA`: class, property, type, range; hard ranges are
errors, soft ranges warnings); add a property there, with its documented range, before using it.

| type | JSON | Luau |
|---|---|---|
| number, bool, string | `0.35`, `true`, `"rbxasset://..."` | as is |
| enum | `"Enum.ParticleOrientation.VelocityParallel"` | as is |
| NumberRange | `[min, max]` or one number | `NumberRange.new` |
| NumberSequence | `[[0, v], [0.4, v, envelope], [1, v]]` (2..20 keypoints, times 0..1 rising) or one number | `NumberSequence.new` |
| ColorSequence | `[[0, colour], [1, colour]]` or one colour | `ColorSequence.new` |
| Vector2 / Vector3 | `[x, y]` / `[x, y, z]` | `.new` |
| colour | `"@style.world.brass"` (rr-bible token), `"$steam_grey"` (declared in `fx_colours`), `"#FFFFFF"`/`"#000000"` | `hex("...")` |
| light level | `[r, g, b]` 0..255 on Ambient, OutdoorAmbient, ColorShift_*, TintColor | `lvl(r, g, b)` |

- A raw hex anywhere else is an error: use a token, or declare an effect colour with `hex` and `why`.
  Declared colours must stay out of the sepia and blue-sky bands (validate asks rr-bible).
- `{"v": 0.3, "canon": "tech.lighting.atmosphere"}`: a value taken from canon. Validate reads the number canon gives
  right after the property's name (`Density about 0.3`, `Saturation +0.12`, `Range 9`), else the only number in the
  text (hex colours never count); lists compare as `a,b,c`. When canon names it differently, add
  `"match": "regex with one group"`. Swapped or invented values fail.
- `{"canon": "gameplay.speed.fast"}` (no `v`): read the number from canon at build time.
- `"oq": "OQ-027"` on a preset or time: the thing waits on an open question; validate warns once it is decided.

## Effect presets (`vfx.json` → `presets`)
- `kind` loop | burst; `priority` 1 crisis signal, 2 feedback, 3 ambience (phones scale rate by priority; the
  runtime guard cuts 3 before 2 and never 1); `anchor` a named attachment on the train (preview positions in
  `stand.anchors`); `use` one line; `canon` list of bible keys it implements, or `"none: why"` plus an `oq` (a real
  OQ id) or the word `proposed` in the reason.
- `start` on | off (loops): off = attached at spawn, switched by `VFX.setActive` on its event. Default: off for
  priority 1, on otherwise; presets a look lists in `fx_on` follow the look instead.
- `layers[]`: `name`, `class` (ParticleEmitter, Beam, PointLight, SpotLight, SurfaceLight, Debris), `offset`,
  `dir` (emission axis; lights use it as the look direction), `props`.
  - burst emitters: `emit` (count), optional `delay` s. Beams: `a1` (second attachment offset).
  - `parent: "part"` + `part_size`: an invisible anchored box emitter (rain).
  - lights: `pulse` {peak, duration} for bursts, `flicker` {min, max, hz} for loops.
  - Debris: `debris` {count, size, speed [min,max], spread deg, lifetime s, gravity_scale, carry, colours, trail}:
    client parts with a VectorForce for floaty slapstick arcs; `carry` 1 streams them back at train speed.
- `speed_link` {layers, rate_idle, rate_max}: rate lerps over 0..`meta.speed_max` (canon av.vfx.speed_link); a light
  layer named here dims with the same share (a brake glow fades as the train stops).
- `crackle` {every [s,s], emit [n,n], flash}: irregular bursts on a loop (power box sparks).
- `preview` {window: [x0, x1, y0, y1], t: s}: side-strip framing for big emitters and the burst POV time;
  `preview_sprite` on a layer picks the stand-in texture shape (smoke, spark, soft, streak). Preview-only.
- `stand.anchors` and layer `offset`/`a1` components may be expressions over the canon rolling-stock envelope:
  `gauge`, `width`, `roof`, `floor` (tech.units.*, OQ-030), e.g. `"gauge/2"`, `"width/2+0.1"`, `"floor+3"`.
  `stand.near_camera` maps an anchor to the preview camera that sees it best (cab1p, coach1p, door1p, roof3p).

## Adding an effect or a look the pack lacks (author it; never substitute the nearest one)
1. Effect: a preset in `vfx.json` (kind, priority, start, anchor, use, canon or `none: ... proposed`); a new anchor
   in `stand.anchors` (canon envelope expressions) and its `stand.near_camera`.
2. Look: a time under `times` (with `use`, and `oq` when canon has no slot for it) and the time in
   `biomes[b].times` for each biome that gets it; declared colours in `fx_colours` with a `why`.
3. `budgets.json`: add the preset to every set it can stack with (validate warns when a preset is in none).
4. `validate --strict`, `budget`, then `preview all` with the pack's names; fix the Visibility warnings first.

## Visible from the players' views (read when facts.md warns)
Players stand on coach roofs (roof3p), lean out of doorways (door1p), work in the cab (cab1p) and coaches
(coach1p). From a roof the train body hides everything at rail level, and the roof hides the coach's own
windows. facts.md gives, per POV and preset, visible / live, hidden by the train or ground, off-screen, share of
the screen and the peak luma change; a WARN means under 0.1% of the screen in every POV.
- Rail-level effects (wheels, axles, brakes): throw particles out past the body side, not just back: an outward
  direction component of about 0.8, Speed 30 or more, Drag 0.4 to 0.6 so the throw survives GlobalWind, Lifetime
  0.4 to 0.8, chunky Size (about 2 at birth); add a PointLight near the rail so the ballast glows (the preview does
  not light surfaces from effects: say so). Judge them from door1p; ask the owner whether roof players must see them.
- Interior effects (firebox, power box): judge from cab1p or coach1p; dark-on-dark (coal dust on a soot backhead)
  needs a lighter or warmer core or an ember layer to read.
- Faint = the peak luma change is under 25 (the effect's core barely differs from what is behind it): darken smoke
  against a pale sky, lighten steam against dusk, add emission to sparks.
- `trails`: Trail props + `width`; used by debris. Trails need moving attachments: never on the train body.

## Looks (`lighting.json`)
`base` → `times[time]` → `biomes[biome]` → `overrides[...]`, per class (Lighting, Atmosphere,
ColorCorrectionEffect, BloomEffect, SunRaysEffect, DepthOfFieldEffect). Plain values set; ops adjust:
`{"add": x}`, `{"mul": x}` (numbers, light levels, colours), `{"lerp": [colour, t]}`, `{"set": v}`.
Derived colours are emitted as Luau `:Lerp` of their sources, so the canon gate sees only token colours.
`biomes[b].times` lists the allowed times; `scene` picks the preview stand. `fx_on` names effect presets a look
switches on (headlamp at night and in tunnels, rain in storm). Overrides carry `tween_in`, `tween_out`,
optional `duration` (self-popping). `studio` holds Studio-only settings for `studio_lighting_setup.lua`.

## Roblox facts the presets rely on (RBXD, fetched 2026-09-28; recheck before launch)
- ParticleEmitter Size is the side of the square texture in studs; Drag halves speed every 1/Drag s;
  WindAffectsDrag follows Workspace.GlobalWind only when Drag > 0; LightEmission 0 normal .. 1 additive and
  does not light surfaces (use a light); LightInfluence 0..1 (Instance.new default 0, Studio insert 1);
  Brightness scales emission when LightInfluence is 0. Emission follows an Attachment's orientation.
- Light Range is clamped at `tech.lighting.light_range_max` (read from rr-bible; validate flags longer ranges).
- Lighting.Technology is deprecated and not scriptable; LightingStyle + PrioritizeLightingQuality replace it
  (tech.lighting.technology_api). Ambient must not exceed OutdoorAmbient (Roblox clamps OutdoorAmbient up).
- Post effects may not render at low quality levels (tech.lighting.post_low_quality): judge the phone fallback.
- Keypoint sequences: at most 20 keypoints, times from 0 to 1.
- Textures: presets use Roblox built-ins (`rbxasset://textures/particles/smoke_main.dds`, `sparkles_main.dds`) as
  placeholders; custom flipbooks need an asset upload, which is the owner's gate.
