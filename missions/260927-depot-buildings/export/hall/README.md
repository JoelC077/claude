# Hall for Roblox
1. Studio > 3D Importer: import `Hall.fbx` (plain, recolourable). Keep hierarchy; do NOT merge meshes. Expected size 46 x 40 x 32 studs (X, height, depth); if it is 3.57x bigger/smaller, fix the importer scale.
2. Select the imported model and paste `studio_setup.lua` into the command bar: anchors, sets collision, applies the recolour groups.
3. Recolour later: edit the GROUPS line for that group (e.g. Stone) and re-run, or recolour single parts in Properties.
4. `Hall_atlas.fbx` + `palette.png` = the palette-atlas version (one texture, 32px cells) if you prefer texture colours; its TextureID hides Color.
5. `build.py` + `kit.py` rebuild everything in Blender; `parts.csv` lists every part, its group, colour, tris and CanCollide.
