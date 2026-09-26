# 3D pipeline (Profile A)

Read this at step 3 when the work is a 3D model. The pipeline below is the one that took the station canopy to 8/10 on every criterion; treat it as standard. `scripts/blender_kit.py` holds the tested helpers.

## Set-up, once per critique

- **Folder access.** If the renders or the .blend live in the owner's project folder, request access to that folder once, at the start, not per pass. Keep `CRIT/` inside it, or copy each pass's renders across in one batch.
- **Helper library in the .blend.**
  - Copy `scripts/blender_kit.py` into the project folder. A file copy costs no tokens.
  - In Blender, run `bpy.data.texts.load("<project>/blender_kit.py")` once. The text block is saved with the .blend.
  - Every round then starts with `kit = bpy.data.texts["blender_kit.py"].as_module()`.
  - Only if Blender can't see any folder you can write to, send the file's text once with `bpy.data.texts.new("blender_kit.py").from_string(...)`.
- **Build from one script.** The model is built by a script that deletes and rebuilds everything each round. No hand edits in the .blend, so a render always matches a script. Before each round, save the script as `CRIT/round-N/build.py`: rolling back is re-running the old script.

## Cameras

Name them once and never move them between passes. If a geometry change puts a wall in front of a fixed camera, add a camera; don't move the old one.

**Player's view (primary).** Where players really are, at the real Roblox eye heights, with Roblox's vertical FOV of 70:
- `kit.pov_camera("Cam_POV_3P", stand=(x, y, floor_z), look_at=target, eye_height=9.5)` for the third-person camera. It sits about 9.5 studs above the floor the player stands on.
- `kit.pov_camera("Cam_POV_1P", ..., eye_height=5)` for first-person.
- Put `stand` where the owner said players are. For example, when players never leave the train, stand them on the carriage floor, not on the platform.
- If the camera or the world moves (a scrolling world, a moving train), render 2–3 POV positions along the path.

**Game distance.** The 3/4 view rendered at 400×225. A5 is judged on it: key features must span at least 5 px.

**Construction views (secondary).** These are the 3/4, side elevation, both ends, a close-up of every interaction point, the interior if there is one, and top-down if players walk on it. Add 5-stud stand-in avatars for scale. If the project already has cameras (Risky Rails: `scene_build.py`'s `Cam_*`), reuse them.

## Render

- `kit.render(cam, path)` renders 1600×900 in Cycles at 16 samples, on the GPU if Blender has one. Render POV views with `res=(768, 432)` and the game-distance view with `res=(400, 225)`.
- **Contact sheet** (`scripts/contact_sheet.py`, keeps it under 1.15 MP):
  - The top band holds the third-person POV (768×432) and the 400 px game-distance render, both true size (`@1`).
  - The grid below holds up to 6 fitted views: the first-person POV, then 3/4, side and ends. Use `--tile 320x180`: that layout measures 1.03 MP.
  - Everything else goes on `closeups.png`, the one optional second image.
- **Look at the contact sheet yourself, every pass.** A black face, a missing part or a camera inside a wall costs a whole pass if the critic finds it instead of you. Open a full-size render only when the sheet shows something off.

## facts.md (measured by script, every pass)

- `kit.tris(objs)`: triangles per mesh. The 20,000 cap is hard. In a moving or scrolling world, aim for 10,000 or fewer per MeshPart and fewer MeshParts overall.
- Part and collision-proxy counts. Mark which parts are `CanCollide=false`.
- The avatar dimensions that matter: openings, step risers, rail heights, floor heights, and gaps between vehicles or to the platform edge.
- A5 pixel sizes: for each key feature, its smallest size in px on the 400 px render.
- The results of every check below.

## Checks before handover (and whenever a critic doubts something)

- **Palette atlas.**
  - Build it: one 256 px texture with 32 px cells, one flat colour per cell, `Closest` sampling, one material. Use `kit.palette_image(hexes, path=...)` and `kit.palette_material(img)`.
  - Map it: `kit.map_faces(obj, index)` puts each face's UVs inside its cell, 4 px clear of the edges so mipmaps don't bleed.
  - Verify it with `kit.verify_palette(objs, img, hexes)`. Every cell must equal its hex exactly, and every exported face must sample a palette colour with no face spanning two cells. Put the one-line result in facts.md.
- **Diagnostic renders settle doubts.** Don't argue with the critic; render the answer. `kit.render(cam, path, diag="no_shadows")` once proved a "smear" was a shadow edge. `diag="flat"` renders unlit texture colours, so the pixels equal the palette hexes.
- **Normals.** Roblox culls back faces. `kit.backfaces(cam, res=(400, 225), mask_path=...)` ray-casts every pixel of a view and counts the pixels that would vanish in Roblox, per object. It gives the same answer as a back-face-culled render diff. Run it on every POV and construction camera, and fix the flagged objects (flip their faces) until each view reports none.
- **Round-trip the export.** `kit.reimport("x.fbx", expect=(x, y, z))`, and the same for the OBJ. This re-imports the export and reports the size in studs, triangles, UV maps and materials, then removes it again. A 3.57× or 0.28× size means a metre/stud mix-up (1 stud = 0.28 m).
- **Studio setup script.** Ship `kit.studio_setup_lua(model, default, rules)` output as `CRIT/studio_setup.lua`. The owner pastes it into Studio's command bar with the model selected. Generate it from the build script, so part names, `Anchored`, `CanCollide`, `CastShadow` and collision fidelity always match the build.

## Roblox facts (bake these into fixes and briefs)

- **Studio's OBJ export renumbers parts** (Part1, Part2…), but in Studio they're all just "Part". Never map anything by exported names; classify by size or shape (`kit.dims(o)`).
- **Studio's OBJ imports into Blender rotated 90° about X.** Bake the rotation before measuring: `kit.import_studio_obj(path)` does it.
- **`CanCollide=false` parts don't block the Roblox camera**: the Popper camera ignores them. Overhead decoration a third-person camera would bump into can be `CanCollide=false`.
- **Moving or scrolling worlds** want fewer MeshParts, each 10,000 triangles or fewer (cap 20,000).
- **FBX unit scale can come in about 3.57× off.** When handing over, tell the owner the expected size in studs, for example "should import as 48 × 14 × 12 studs", to check in Studio's importer.
