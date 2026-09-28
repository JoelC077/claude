# Roblox export (step 9)

Runs after the bar is met or a stop rule fired. multiuse-critic covers 3D handover helpers (`blender_kit.reimport`, `studio_setup_lua`); it has no UI export, so the UI half is owned here.

## 3D (per building)
Output `<M>/export/<building>/`:
- `<Building>.fbx` (always) - Apply transforms; one object per editable part, never joined; names `<Bldg>_<Part>_<Mat>_<nn>` (e.g. `Depot_WallN_Stone_01`, `Depot_Roof_Slate_02`); exported **without** the atlas texture (plain material per group), because a MeshPart with a TextureID or SurfaceAppearance hides its Color and recolouring would then need a texture edit.
- `<Building>_atlas.fbx` (only if the owner asked for the palette atlas) - same parts with the atlas texture; README says it cannot be recoloured by Color in Studio.
- `<Building>.blend` + `build.py` (final round) - the source of truth; rebuilding is re-running the script.
- `parts.csv` - `name,group,material,palette_cell,tris,cancollide`. The recolour groups are what the owner edits.
- `studio_setup.lua` from `kit.studio_setup_lua(model, default, rules)`: Anchored, CanCollide per rules (trims, gutters, ivy = false), CollisionFidelity Box for small parts, and a recolour table: `local GROUPS = { Stone = {color=Color3.fromHex("<style.depot_kit.stone>"), material=Enum.Material.Slate, parts={...}}, ... }` (colours from parts.csv palette_cell) + a loop that sets `TextureID = ""`, Color and Material per group, so recolouring = editing one line. Check: changing one GROUPS colour visibly recolours those parts (TextureID empty).
- Optional `<Building>.obj` fallback.
Verify (report in the step line):
- `kit.reimport(path, expect=(w, d, h))` in studs; a 3.57x factor means the unit bug (fix scale, re-export).
- `kit.tris` per object <= 10k (cap 20k); part count; `verify_palette`.
Import note for the owner (README.md, 5 lines): Studio > Avatar/3D Importer, keep hierarchy, do not merge meshes, then run studio_setup.lua in the command bar.
Live-Blender case: if built via Blender MCP on the owner's machine, export there too into a new dated folder `rr-export-<YYMMDD-HHMM>/` next to the new .blend; never replace existing files; list the paths on his machine.

## UI (ScreenGui package)
Output `<M>/export/roblox/` (Rojo-friendly):
- `NotificationHud.lua` (ModuleScript) - builds the ScreenGui in code: Frames/ImageLabels/TextLabels sized with Scale + `UIAspectRatioConstraint`, `UIScale` (1.0 phone, 1.16 PC from the design), `UICorner`, `UIStroke`, `UIGradient` mirroring the tokens, `UIListLayout` bottom-right stack; fonts via `Font.fromEnum(Enum.Font.LuckiestGuy)` and `Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Bold)`.
- `NotificationController.lua` - public `Notify(kind, data)`; kinds table (colours, lifetimes, stamp), exact texts, merge + count badge, cap 4 with "+N MORE", compact older, sticky crisis, TweenService enter/leave/shake/pulse.
- `NotificationDemo.client.lua` - fires every type once, for a quick Studio test.
- `icons/` - PNG sprite sheet rendered at 2x via Playwright + `icons.json` (ImageRectOffset/Size per icon).
- `ASSETS.md` - upload order, where each `rbxassetid://` placeholder goes.
Verify:
- Syntax: `luau-analyze` or `selene` if installed; else `luac -p` (Lua 5.1 subset; ignore Luau type annotations by not using them); else npm `luaparse` (`npm i luaparse`, works in the cloud image; no Luau types or `+=`); else a bracket/`end` balance check. Report which ran.
- Layout parity: render the Lua layout numbers as HTML (same tokens) with `render_design.py` and put it side by side with the final board in one contact sheet; you look at it once. (rr-ui-foundry deliverables: skip this; `ui build` BUILD PASS is the check.)
- Text diff: every notification text in the Lua equals the facts file.

## Environments
- Cloud: pip `bpy` 5.0 headless (Cycles only, no viewport), Playwright + Chromium for UI renders. No Roblox Studio: never claim an in-Studio test; say "Studio test pending (owner)".
- Cowork: same scripts if Python is available; otherwise deliver files + README and mark verification steps not run.
