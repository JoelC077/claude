## Main Hall - measured (fresh render of src/hall/hall.blend, 2026-09-27, pass 2)
- parts: 404 separate named Hall_* mesh objects (was 347); materials: 1 (palette atlas)
- tris total 5,068 (was 4,340; budget 20k); largest part 60 tris (Hall_RoundelFace_Cream_01 / RoundelRim_Brass_01; target 10k/part)
- backface pixels (Roblox-culled): 0 on all 7 rendered views (Crit_POV3P, Crit_POV1P, Hall_Cam_Game/34/Side/Back/Door)
- wall footprint 34.0 x 14.0 studs, plan x 13..47, y -16..-2; eaves 16
- overall bbox incl. slab/lamps/rails: 46.0 x 32.0 x 36.6 (cupola vane apex ~36.1 above ground; was 34.5)
- doorway clear 7.9 wide x 10.0 tall (front); rear service door 7 x 9; avatar stand-in 5 studs
- verify_palette (maker build log): ok, 2479 faces, 0 spanning, 0 off-palette
- renders: POV 3P (30 studs out, eye 9.5, FOV 70 vertical) and POV 1P (18 studs out, eye 5); game view 400x225 at 1:1 from fixed game cam; 3/4, side, back, door construction views 800x450 from fixed build cameras
