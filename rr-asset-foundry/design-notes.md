# rr-asset-foundry: design notes (2026-09-28)

## Job
Recurring Risky Rails asset families (carriages, wagons, buildings, props, track) as parametric generators: change a number, get a Roblox-ready variant; run N overnight and pick from a variant sheet. The foundry makes and measures; it never judges looks (multiuse-critic does) and never states canon (rr-bible does).

## Pipeline (one variant)
`plan` (stdlib, no Blender) -> `forge` (bpy) -> post-checks (stdlib) -> files.
1. **plan**: family defaults < preset < `--params` JSON < `--set`. Defaults written `@key` are read from rr-bible at plan time (`@tech.units.track_piece`, `@tech.units.building_door#0`), so no canon number is restated in code. Group colours are bible token keys, resolved through `bible.py tokens --format json` (superseded refused, conflict labelled). Everything resolved is frozen into `plan.json`, so a forge run never needs the bible and a variant is reproducible.
2. **forge** (`python3 forge.py plan.json` with pip bpy, or `blender -b -P forge.py -- plan.json`): empty scene -> `family.build(k, p)` through the foundry kit (`fkit.py`: box, boxes, cyl, prism, wall with holes, proxies, detail levels, seeded rng) -> palette atlas + face mapping via multiuse-critic `blender_kit.py` (reused, not copied) -> checks -> renders -> exports.
3. **post**: `bible check studio_setup.lua` (canon gate), Lua syntax (luaparse if present, else block balance), manifest, facts.md, README.

## Decisions
- **Family = one pure-Python file** (`families/<name>.py`: PARAMS, GROUPS, PRESETS, VIEW, build). Importable without bpy, so `plan`/`list`/`show` and batch planning cost no Blender time. New family = `foundry.py new-family` from `_template.py`.
- **Recolour groups are semantic** (Body, Trim, Timber, Iron...), named in the part name `<Asset>_<Part>_<Group>_<nn>` (canon tech.mesh.naming). `studio_setup.lua` carries one GROUPS line per group (token hex + Roblox material), so a recolour is one edited line.
- **Two FBX always**: plain (a material per group, no texture: Color recolours in Studio) and `_atlas` (256 px palette atlas, 32 px cells); canon tech.mesh.recolour and the depot mission's friction #16.
- **Collision proxies** are box meshes named `<Asset>_Collider_Proxy_nn` inside the FBX (placement survives any importer axis convention); the setup script makes them invisible Box colliders and turns visual CanCollide off. Families with no collision (scrolling track) switch everything off.
- **LOD option** = a second build at detail level 1 (small parts dropped, fewer segments) merged to one MeshPart per group: `<Asset>_LOD1.fbx` for far-ground bands. Roblox makes its own render LODs; this file is for manual far-band swaps and scatter (said honestly).
- **Merge option** (`--merge group`): one MeshPart per group, default for track (streamed segments want few MeshParts).
- **Objective checks per variant** (hard fail = exit 1, outputs still written and labelled): names, tris vs tech.mesh target/cap, verify_palette, back faces from POV + 3/4, coplanar overlaps (lesson: black Cycles faces, depot mission), floating parts (friction #17), FBX reimport size (3.57x unit bug), key-feature pixel span on the 400 px game view vs style.line.min_feature_px, Lua syntax, bible check.
- **Batch**: grid or seeded random sweep over params (and presets), one subprocess per variant (a crash never kills the run), resumable by plan hash, thumbnails only by default, variant sheets via multiuse-critic `contact_sheet.py` (16 per sheet, under 1.15 MP), `batch.md` table with check status. Picking stays with the owner or a critic; the foundry never ranks looks.
- **Critic hand-off**: `crit` renders the Profile A set (POV 3P/1P at canon eye heights, 400 px game view, 3/4, side, end) into `CRIT/pass-N/`, builds `contact.png` + `facts.md`, writes a brief skeleton (never claims step 2 answered) and prints the `critic_kit.py build` command.

## Plugs
- rr-bible: tokens, `@key` params, tris/camera/avatar numbers, `check` gate; missing canon recorded with `add-question` / proposed `add-fact` (OQ-030: gauge and rolling-stock envelope). OQ-025 (livery) labels every carriage/wagon livery as assumed.
- rr-mission-control: step 4 `list --match` finds a family; step 5 maker runs `make` instead of writing build.py; step 6 = the variant's checks; step 7 `crit`; step 9 the variant folder is the export (`verify`).
- multiuse-critic: `blender_kit.py`, `contact_sheet.py`, `critic_kit.py` found by glob, never copied.

## Limits
Cloud: headless bpy 5.0, Cycles CPU only (renders are the slow part), no Studio: import and setup script are "Studio test pending (owner)". Curved track, animated parts and textures beyond the flat atlas are out of scope.

## Fix round 1 (2026-09-28, trial FRICTION F1-F12 + two independent reviews)
- **A5 measured per piece.** `fkit.feature_px` projects every mesh island of a key's parts (exact `<Part>` token) and takes its thinnest on-screen width (convex hull, rotating calipers), on the 400 px game view (warns) and the POV 3P (facts). The old whole-part longest side could never warn (trial: "Strap 102 px" where the piece was 2.7 px).
- **Player-view premises.** `VIEW["premises"]` + `stands()` give 1-3 POV stands per premise; `--pov` switches premise with a render-only pass (no rebuild). Wagon default `siding` (seen from the coach at world.prefabs.15 spacing) replaces the canon-contradicting "next vehicle" view (kept as `coupled`, labelled CONTRADICTS canon).
- **Identity split.** `vkey` (the variant) vs `hash` (vkey + family, imported helpers, fkit, forge, canon/stage/view). Stale or errored = rebuilt; different variant = refused. Batch variants catch their own refusals and crashes.
- **Copies are first-class.** Render-only writes a temporary plan with the folder given, current sibling paths and family file, and re-points the palette image; crit, sheet and make all use it.
- **Critic lessons in the wagon family**: straps 1.3 x 0.3 and end straps 1.5 x 0.3 (foreshortened 3/4 view), two-peak heightfield coal 2.75 above the sides with bigger lumps, light cap rails, whole replaced planks instead of red-oxide patches, gap-free deck, outside-frame running gear with wheel_r 2.0.

## Pending, owner-gated (not done from this session: it may write only its own folder)
**rr-bible question** (a question, not a decision; the family labels the premise ASSUMED until it exists). Dry-run OK (would be OQ-042 today):
```
python3 <rr-bible>/scripts/bible.py add-question "Where do freight wagons appear, and how does the player see them?" \
  --option "A: yard dressing on the marshalling-yard sidings (world.prefabs.15), seen from the coach at the siding spacing while the world scrolls" \
  --option "B: Depot Lobby yard dressing, seen on foot and close" \
  --option "C: coupled into the crew's train (would change gameplay.train.layout; conflicts with D-013 no tender)" \
  --default "A (the only canon place for sidings; the train is cab + coach)" --src FDY --affects world.prefabs.15 \
  --blocks "rr-asset-foundry wagon POV premise and critic brief"
```
Then add the new OQ id to wagon.py `OPEN`. Related: OQ-030 option on whether yard wagons use the coach width (17.4 on gauge 8).

**rr-mission-control patch** (its SKILL.md; the link is one-sided today):
- Step 4: "For each 3D deliverable run `<foundry> list --match`; a match makes the maker's order `foundry.py make <family> --preset .. --set ..` (params in the order file)."
- Step 5: after "3D: one `build.py` that rebuilds everything" add "(or, for a foundry family, the variant's `plan.json` + `families/<family>.py`, rebuilt by `foundry.py make --params plan.json`)".
- Step 9: export list "`.blend` + `build.py`" becomes "`.blend` + `build.py` (foundry: `plan.json` + the family file; `foundry.py verify` is the pre-export check)".
