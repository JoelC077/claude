## Main Hall - measured (fresh render of src/hall/hall.blend, 2026-09-27, pass 3)
- parts: 414 separate named Hall_* mesh objects (was 404); materials: 1 (Palette atlas)
- tris: 5,188 total per maker build log (was 5,068; budget 20k); largest part 60 tris (target 10k/part)
- backface pixels (Roblox-culled): 0 on all 7 rendered views (Crit_POV3P, Crit_POV1P, Hall_Cam_Game/34/Side/Back/Door)
- wall footprint 34.0 x 14.0 studs, plan x 13..47, y -16..-2; eaves 16
- overall bbox incl. slab/lamps/rails: 46.0 x 32.0 x 38.6 (was 36.6; cupola raised 2)
- doorway clear 7.9 wide x 10.0 tall (front); rear service door 7 x 9; avatar stand-in 5 studs
- verify_palette (maker log): ok, 0 off-palette; reimport: 414 meshes, no missing UVs
- renders: POV 3P (30 studs out, eye 9.5, FOV 70 vertical) and POV 1P (18 studs out, eye 5); game view 400x225 at 1:1 from fixed game cam; 3/4, side, back, door construction views 800x450
