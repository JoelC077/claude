## Depot (measured fresh from src/depot/depot.blend, 2026-09-27, pass 4)
- parts (separate named Depot_* mesh objects): 387 (was 389); materials: 1 (palette atlas)
- tris: 4,956 total (budget 10k/part, 20k/building); largest part 36 tris
- backfaces from POV 3P cam: 0 px
- world bbox (studs, incl. ground slab + dressing): x 10..50 (40), y -94..-60 (34), z -0.5..31.3 (bell cote apex)
- wall footprint 24x14, eave 14 (unchanged per maker rebuild)
- yard rail Depot_YardRail_Hazard_01/02: 11 x 1.0 x 1.2 studs each (was 0.4x0.4); mid rails removed
- renders: depot_pov3p (stand (30,-58), eye 9.5, FOV70) and depot_pov1p (eye 5) at 400x225; depot_game 400x225 from fixed Depot_Cam_Game; construction views 34/side/back/door 1280x720 from fixed build cameras
