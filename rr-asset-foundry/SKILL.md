---
name: rr-asset-foundry
description: "Parametric Blender generators for recurring Risky Rails (Roblox) asset families: passenger coaches, freight wagons (flat, open coal, box van, tank), small railway buildings (hut, signal box, platform shelter), yard props (supply crates, oil drums, taped barriers) and tiling track (straight, buffer stop). Change a number or preset and get a Roblox-ready variant: rr-bible palette atlas, separate named recolour-group parts, invisible box collision proxies, optional LOD1, plain and atlas FBX, Studio setup script and measured facts; or batch N variants overnight into variant sheets. Use whenever the owner wants another carriage, wagon, hut, crate or track piece, a variation of one ('a longer coach', 'same shed but taller', '12 wagon variants overnight'), when a mission deliverable matches a family, or to add a new family. Canon comes from rr-bible; looks are judged by multiuse-critic. Not for one-off hero assets with no family (rr-mission-control builds those) or UI."
---

# RR Asset Foundry

A family is one Python file with named parameters, presets and recolour groups. The foundry turns family + numbers into a finished Roblox variant, measures it with scripts, and hands visual judgement to multiuse-critic. It never states canon (rr-bible does) and never scores looks. Be precise and proactive; no butler voice.

Paths: `<me>` = this skill's folder; `fdy` below = `python3 <me>/scripts/foundry.py`. It finds rr-bible and multiuse-critic itself (sibling folder, `~/.claude/skills`, `/home/user`; override with `RR_BIBLE=<bible.py>`, `RR_CRITIC=<folder>`). Blender work needs `import bpy` (cloud: pip bpy 5.0) or `--blender <exe>` / `RR_BLENDER`; `list`, `show`, `plan` and batch dry runs need no Blender. Output root: `--out`, else `RR_FOUNDRY_OUT`, else `~/.rr-foundry`; in a mission `<M>/src/<deliverable>`; never the session scratchpad for anything the owner keeps.

Read a reference only at the step that names it.

## Families

| family | presets | reads canon |
|---|---|---|
| carriage | coach_works, coach_brand, coach_short, coach_long | stock width/floor/roof, gauge, train doorway |
| wagon | open_coal, open_bogie, flat_crates, box_van, tank_long | stock width/floor/roof, gauge, siding spacing (POV) |
| building | hut_stone, hut_taped, signal_box, shelter | building door |
| prop | crate_single, crate_stack, crate_hazard, drum_cluster, barrier_taped | - |
| track | straight, straight_long, buffer_stop | track piece, ballast width, gauge, stock floor/width |

`fdy list --match "<words from the request>"` ranks families (best first); `fdy show <family>` prints every param (type, range, default, canon key), group, preset, player-view premise and the open questions labelling its outputs. Presets are starting points; any param can be set.

## One variant

1. `fdy plan <family> --preset <p> [--set k=v ...] [--group Group=bible.token.key] [--pov <premise>]`: resolves canon and prints params (with their bible key and status), groups and hexes, the player-view premise, open questions and warnings. Fix warnings before building.
2. `fdy make <same args> --out <dir> [--name AssetName] [--lod] [--renders full|thumb|none]` (default full). About 5 s plus renders (full set about 20-30 s on 4 CPU cores). Prints at most 10 lines; exit 1 = an objective check failed (files are still written and labelled FAIL).
3. Read `<dir>/<Asset>/facts.md` (measured, about 25 lines). Open `forge.log` only on FORGE ERROR. On a FAIL read `references/checks.md`.
4. Look at one image yourself before showing anyone: `renders/34.png` (or the crit contact sheet). Never describe renders you did not open.
5. Variations: `fdy make <family> --params <dir>/<Asset>/plan.json --set k=v --name NewName` (plan.json freezes every number, token and seed). Same plan again = "up to date" at no cost; the same plan after a family, helper, kit or canon change is rebuilt; a different plan in the same folder is refused unless `--name` or `--force`.
6. Several one-by-one variants side by side: `fdy sheet <dir>/<A> <dir>/<B> ... --out <file>.png` (thumbnails, avatar for scale).

Player view: families seen in more than one place have premises (`fdy show`; wagon: `siding` default, `lobby`, `coupled`). `--pov` picks one for the POV renders only; it never rebuilds geometry. Each premise renders 2-3 POV stands (the world scrolls, D-002).

Studio import for the owner is in each variant's README.md: import `<Asset>.fbx` (keep hierarchy, do not merge), select it, run `studio_setup.lua` in the command bar.

## Batch overnight

`fdy batch <family> --preset <p> --vary length=24:48:8 --vary kind=open,box [--mode random --n 40 --seed 7] --out <dir> --jobs 2`
- `a:b:step` or `a,b,c` (grid, the default: every combination; `--n N` caps it to a seeded subset); `a:b` with `--mode random --n N` samples the range; `--vary preset=x,y` varies presets.
- `a:b:step` needs lo <= hi and step > 0; grids over 400 variants need `--n`. `--same-seed` gives every variant the same seed (default: seed + i).
- Always `--dry-run` first: it prints the variant list and a time estimate. Tell the owner the count, time and output folder before starting.
- Start overnight batches from the main session (`nohup ... &` or Bash `run_in_background`): a background job started by a subagent or workflow step dies when that step returns. Re-running the same command resumes: finished variants are skipped; errored ones, and any made before a family, helper, kit or canon change, are rebuilt; a crash stays with its variant. Exit 1 when any variant failed or errored.
- Output `<dir>/batch-<Base>/`: `batch.md` (params, status, parts, tris, size, first fail), `sheet-N.png` (16 thumbnails per sheet, under 1.15 MP, labelled with the varied values; the 5-stud avatar is the scale), `vNNN/` variant folders.
- Report from batch.md plus one look at each sheet. Checks are objective only: picking is the owner's or a critic's call. Full critic renders for picks: `fdy crit <dir>/batch-<Base>/vNNN ...` (renders in place).

## Critic hand-off (visual judgement)

`fdy crit <variant_dir> [<variant_dir> ...] --crit <CRIT> --pass N [--pov <premise>]` renders the Profile A set if missing or if the premise changed (POV 3P at 2-3 stands and 1P, at canon eye heights and FOV, 400 px game view, 3/4, side, end, top for track), builds `contact.png` (plus `closeups.png`), concatenates facts.md and writes a `brief.md` skeleton if none exists. It works on copies (renders land in the folder given) and refuses a variant whose checks failed (`--allow-fail` to override).
- The skeleton has TODO lines: Purpose (one job per variant) and step 2. Answer them with the owner. If the owner cannot be asked (subagent, overnight), replace each TODO with an `ASSUMPTION:` line citing canon keys, and repeat the assumptions when presenting. crit prints the TODO count; never run `critic_kit.py build` with TODO lines left.
- Then follow multiuse-critic from its step 2 (its questions are the TODO lines; read its SKILL.md; the script prints the `critic_kit.py build` command). A fix is a param change or a family-code change; copy the variant to `CRIT/round-N/` first, then `make` into the same folder (a family change rebuilds by itself). Never self-score toward a bar.

## Inside a mission (rr-mission-control)

- Step 3/4: `fdy list --match` on each 3D deliverable. A match means the maker's order is `fdy make ...` with the preset and params in the order file, not a hand-written build.py: `plan.json` plus `families/<family>.py` stand in for build.py (they rebuild everything).
- Step 5: `fdy make ... --out <M>/src/<deliverable> --renders full`. Step 6 pre-flight is the variant's own checks; a FAIL blocks the critic.
- Step 7: `fdy crit` into `<M>/critique-<group>/` (one CRIT for up to 3 variants).
- Step 9: the variant folder is the export. `fdy verify <variant>` (files, Lua syntax, canon gate), then copy it to `<M>/export/<asset>/` with `families/<family>.py` beside plan.json in place of build.py.
- rr-mission-control does not mention the foundry yet; the owner-gated patch for its steps 4, 5 and 9 is in `design-notes.md`. Say so in the readback.
- A one-off build that will recur becomes a family: `references/families.md`, section "Promote a mission build".

## Canon (rr-bible)

- Every recolour group is a bible colour token, resolved at plan time. Recolour with another token: `--group Body=style.brand.teal`. Hex values and superseded tokens are refused; a new colour is first proposed in the bible (`bible.py add-fact ... --status proposed`).
- Numbers the bible holds are `@key` defaults in the family (`@tech.units.stock_width`, `@tech.units.building_door#0`). Tris target and cap, eye heights, FOV, avatar height and minimum feature pixels are read from the bible too. Nothing in this skill restates a canon value.
- Open questions label outputs, and plan/facts/README list them: OQ-025 (train exterior livery) on carriages and wagons; OQ-030 (gauge and rolling-stock envelope, proposed values) on rolling stock and track. Present those values as "assumed (OQ-nnn default)". Only the owner decides (`bible.py decide`).
- Canon a new family needs but the bible lacks: `bible.py add-question` with a default (a question, not a decision), then reference the new key. Never hard-code it. Where wagons appear is not canon: the wagon premises say ASSUMED, and the question is drafted in `design-notes.md` to record when the session may write to rr-bible.
- Canon numbers a POV needs come through `VIEW["nums"]` (`@key#i`; a value with no number reads its note, e.g. world.prefabs.15 siding spacing).
- Every `studio_setup.lua` passes `bible check` or the variant fails.

## What a variant contains

`<Asset>.fbx` (a plain material per group: Color recolours in Studio), `<Asset>_atlas.fbx` + `palette.png` (256 px atlas, 32 px cells), `<Asset>_LOD1.fbx` with `--lod` (details dropped, one MeshPart per group, no collision: for manual far-ground swaps; Roblox makes its own render LODs), `<Asset>.blend`, `parts.csv` (part, group, token, hex, material, tris, collide), `studio_setup.lua` (anchoring, invisible Box proxies, climbable ladder rungs, one GROUPS line per group the variant uses), `renders/`, `facts.md`, `README.md`, `plan.json`, `manifest.json`. Part names follow canon `tech.mesh.naming`: `<Asset>_<Part>_<Group>_<nn>`.

## Checks (per variant, by script)

Fail: part names, a MeshPart over the tris cap, palette atlas (`verify_palette`), back faces from every POV and construction camera, coplanar overlapping faces (black in Cycles, z-fighting in Roblox), floating parts, FBX reimport size (the 3.57x unit bug), Lua syntax (luaparse if present, else block balance), canon gate. Warn: over the tris target, a key feature whose smallest single piece is under `style.line.min_feature_px` on the 400 px game view (multiuse-critic A5; facts.md also gives the POV 3P sizes), family warnings. Causes and fixes: `references/checks.md`.

## New family

`fdy new-family <name>` writes `families/<name>.py` from the template. Read `references/families.md` (kit API, geometry rules that pass the checks, canon rules), then iterate `fdy plan <name>` and `fdy make <name> --renders thumb` until the checks pass, then run `crit`. Rolling stock shares `families/_rolling.py` (underframe, bogies, buffers, ladders).

## Honest limits

- Cloud sessions: headless bpy 5.0, Cycles on CPU, no Studio. The Studio import, setup script and ladder climbing are "Studio test pending (owner)"; say so. The `--blender <exe>` route (a desktop Blender) is written but untested here.
- Straight track only (no curves or points yet). Flat palette colours only: no textures or decals, and no text (canon `style.dont.invented_text`: boards are blank).
- The A5 measure ignores occlusion (hidden far-side pieces count) and the 400 px view is framed to the asset, so long vehicles (45+ studs) measure about 20% smaller than 30-stud ones.
- Wagon bodies use the coach envelope (OQ-030: width 17.4 on gauge 8); outside frames make the running gear show, but whether yard wagons should be narrower is the owner's call.
- Looks are unscored until a fresh multiuse-critic scores them.
- Never publish, upload, spend or change the owner's config. The owner imports and publishes.

## Maintain

`python3 <me>/scripts/selftest.py` exercises every command on a temp copy (`--quick` skips Blender) and must print all passed. Remove `__pycache__` after running scripts.
