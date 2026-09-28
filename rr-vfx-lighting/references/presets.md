# Preset data (read when adding or editing a preset)

Source of truth: `presets/vfx.json`, `presets/lighting.json`, `presets/budgets.json`. Luau is generated from them
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
- `{"v": 0.3, "canon": "tech.lighting.atmosphere"}`: a value taken from canon; validate checks the number (or
  list, or bool) appears in that fact's value or note, so the preset can never contradict it silently.
- `{"canon": "gameplay.speed.fast"}` (no `v`): read the number from canon at build time.
- `"oq": "OQ-027"` on a preset or time: the thing waits on an open question; validate warns once it is decided.

## Effect presets (`vfx.json` → `presets`)
- `kind` loop | burst; `priority` 1 crisis signal, 2 feedback, 3 ambience (phones scale rate by priority; the
  runtime guard cuts 3 before 2 and never 1); `anchor` a named attachment on the train (preview positions in
  `stand.anchors`); `use` one line; `canon` list of bible keys it implements, or `"none: why"` plus an `oq`.
- `layers[]`: `name`, `class` (ParticleEmitter, Beam, PointLight, SpotLight, SurfaceLight, Debris), `offset`,
  `dir` (emission axis; lights use it as the look direction), `props`.
  - burst emitters: `emit` (count), optional `delay` s. Beams: `a1` (second attachment offset).
  - `parent: "part"` + `part_size`: an invisible anchored box emitter (rain).
  - lights: `pulse` {peak, duration} for bursts, `flicker` {min, max, hz} for loops.
  - Debris: `debris` {count, size, speed [min,max], spread deg, lifetime s, gravity_scale, carry, colours, trail}:
    client parts with a VectorForce for floaty slapstick arcs; `carry` 1 streams them back at train speed.
- `speed_link` {layers, rate_idle, rate_max}: rate lerps over 0..`meta.speed_max` (canon av.vfx.speed_link).
- `crackle` {every [s,s], emit [n,n], flash}: irregular bursts on a loop (power box sparks).
- `preview` {window: [x0, x1, y0, y1]}: side-strip framing for big emitters; `preview_sprite` on a layer picks
  the stand-in texture shape (smoke, spark, soft, streak). Preview-only.
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
- Light Range is clamped to 120 studs (tech.lighting.light_range_max).
- Lighting.Technology is deprecated and not scriptable; LightingStyle + PrioritizeLightingQuality replace it
  (tech.lighting.technology_api). Ambient must not exceed OutdoorAmbient (Roblox clamps OutdoorAmbient up).
- Post effects may not render at low quality levels (tech.lighting.post_low_quality): judge the phone fallback.
- Keypoint sequences: at most 20 keypoints, times from 0 to 1.
- Textures: presets use Roblox built-ins (`rbxasset://textures/particles/smoke_main.dds`, `sparkles_main.dds`) as
  placeholders; custom flipbooks need an asset upload, which is the owner's gate.
