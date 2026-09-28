# Writing a family (read when adding or changing one)

A family is `families/<name>.py`, pure Python, importable without Blender (so `plan`, `list` and batch planning cost nothing). `fdy new-family <name>` copies `families/_template.py`. Files starting with `_` are helpers, not families.

## Module contract

| name | what |
|---|---|
| `FAMILY`, `DESC`, `TAGS` | id, one-sentence description, request words for `list --match` |
| `OPEN` | rr-bible open questions that label every output (e.g. `["OQ-025"]`); OQs in a canon key's note are added automatically |
| `PARAMS` | `name: ("float"/"int", default, min, max, help)`, `("choice", default, [..], help)`, `("bool", default, help)`. A default written `"@file.section.key"` (or `"@key#1"` for the 2nd number in a value like `7 x 9`) is read from rr-bible at plan time |
| `GROUPS` | recolour group: `(bible colour token, Roblox Material[, Reflectance])`. CamelCase names; they become the `<Group>` in part names and the GROUPS lines in the Studio script. Keep materials honest (only brass gets reflectance, canon `style.material.reflectance`) |
| `PRESETS`, `DEFAULT_PRESET` | `name: {"params": {...}, "groups": {Group: token}, "note": "..."}` |
| `VIEW` | `ground` (stage token), `features` (part-name keys measured at game distance), `player` (how it is seen: goes into the critic brief), optional `stage: "track"` (rails under rolling stock), `top: True`, `rules` (extra Studio rules `(lua_pattern, {Property: value})`) |
| `OPTIONS` | defaults for `merge` (`none`/`group`), `collide` (False = nothing collides, e.g. streamed scenery), `lod` |
| `validate(p, canon)` | optional plan-time warnings; a message starting `ERROR:` refuses the combination (exit 2); `canon("tech.units.stock_roof")` returns a bible number |
| `build(k, p)` | makes every part through `k` |
| `pov(p, lo, hi)`, `avatar(p, lo, hi)`, `tile_offsets(p)` | optional: POV stand and look-at, stand-in avatar spot, stage copies for tiling pieces |

## Kit API (`k`, see `scripts/fkit.py` docstring)

`k.box(part, group, center, size, rot=(0,0,0), detail=0)`, `k.boxes(part, group, items)` (several boxes, one part), `k.cyl(part, group, center, r, depth, axis, segs, r2, scale)`, `k.prism(part, group, profile, depth, center, axis)`, `k.wall(part, group, axis, a0, a1, at, z0, z1, thick, holes)`, `k.proxy(center, size, rot)`, `k.measure(label, text)`, `k.rng` (seeded), `k.segs(n)`. Helpers: `fkit.arc`, `fkit.arc_z`, `fkit.shell`, `fkit.frame_boxes`. Rolling stock: `_rolling.underframe`, `bogie`, `wheelset`, `ladder`, `RUNG_RULE`, `pov_next_vehicle`.

- Frame: studs, z up. Buildings and props: z = 0 ground, front faces -y (the 3/4 and POV cameras sit on the -y side). Rolling stock and track: z = 0 rail top, x along the track.
- `detail=1` parts vanish at LOD1 (rivets, springs, gutters, lumps). Everything the silhouette needs stays detail 0.
- Randomness only through `k.rng`, drawn the same way at every LOD (never branch on `k.lod` before drawing).
- One part per thing the owner might recolour or replace; many identical small things (rungs, bars, planks) go in one `boxes` part.
- Collision: a few `k.proxy` boxes for what players stand on or bump into (floors, walls with door gaps, roofs, railings, ramps for stairs). No proxies + `collide: True` means the visual parts collide; `collide: False` means nothing does.

## Geometry rules that pass the checks

- Parts meet by overlapping (0.05-0.3), never by two faces sharing a plane. Proud details stand 0.05-0.3 out (canon `style.form.relief`) and at a depth no neighbour uses: stagger 0.02+ (e.g. straps 0.22, patches 0.19, door 0.20).
- Frames lap into their opening (`fkit.frame_boxes`, lap 0.08) so no frame face lies on a jamb. Sills, lintels, stripes and gutters stop 0.1 short of the ends of what they sit on.
- Anything attached must touch or overlap its support within 0.05; bounding boxes decide `floating`.
- Chunky over fine: nothing thinner than about 0.15 on things seen in motion (canon `style.dont.hairlines`); key features at least `style.line.min_feature_px` at the 400 px game view.
- Gable ends and end walls follow the roof curve (`fkit.arc_z`) so no gap shows under a roof.
- Keep every MeshPart under the tris target (cylinders 10-24 segments).
- No text or logos (canon `style.dont.invented_text`); blank boards are fine and are listed in facts.

## Canon rules

- Colours only as bible token keys in GROUPS or presets. A missing colour: propose it in the bible first.
- Any dimension the bible holds is an `@key` default. A dimension the family needs that is shared with other families (gauge, stock envelope, doors) belongs in the bible: `bible.py add-question` with a default plus `add-fact --status proposed`, then reference it (OQ-030 is the worked example).
- Numbers that are pure art choices (plank count, bevel sizes, lump counts) stay family params.
- Plan must print no warnings for every preset; `fdy plan <family> --preset <p>` for each.

## Promote a mission build

A mission `build.py` (rr-mission-control) becomes a family when the owner will want more of it:
1. Copy the template; move each hard-coded dimension the owner might change into PARAMS, and each colour into GROUPS as its bible token (the mission's palette list maps to tokens: `bible.py check build.py` names the nearest token for each hex).
2. Replace direct bpy calls with `k.*` (one call per part; the kit does naming, atlas UVs and collections).
3. Replace the mission's cameras with VIEW/`pov()`; the forge makes the standard set.
4. `fdy make <name> --preset <p> --renders full`; iterate until the checks pass; compare with the mission's certified renders side by side (one contact sheet) before retiring the old script.

## Test loop

`fdy plan` (no warnings) -> `fdy make --renders thumb` for every preset (all ok) -> one look at `renders/thumb.png` per preset -> `fdy batch --vary` across the widest ranges with `--renders none` (catches geometry that breaks at extremes) -> `fdy crit` for the defaults. Add the family to the SKILL.md table and run `scripts/selftest.py`.
