# WagonOpenCoal (wagon, preset open_coal)
1. Studio > 3D Importer: import `WagonOpenCoal.fbx` (recolourable). Keep hierarchy; do NOT merge meshes. Expected size X 32.8 x Y(up) 10.54 x Z 18.04 studs; about 3.57x off = unit bug, fix the importer scale.
2. Select the imported model, paste `studio_setup.lua` into the command bar: anchors, collision (invisible Collider_Proxy boxes), recolour groups.
3. Recolour: edit one GROUPS line (a group per material, e.g. Chassis) and re-run. `WagonOpenCoal_atlas.fbx` + `palette.png` = palette-atlas look (set KEEP_ATLAS = true; Color is then hidden).
4. No LOD1 file (make with --lod for a far-ground version).
5. Vary it: `python3 <rr-asset-foundry>/scripts/foundry.py make wagon --params plan.json --set KEY=VALUE --name NewName` (families/wagon.py lists every param).
Studio test pending (owner): nothing here was run in Studio.
Open: OQ-025, OQ-030; colours/dimensions tied to them are assumptions.
