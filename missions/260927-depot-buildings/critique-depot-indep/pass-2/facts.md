## Depot (measured fresh from src/depot/depot.blend, 2026-09-27, pass 2)
- parts (separate named Depot_* mesh objects): 341 (was 290); materials: 1 (palette atlas, 22 cells)
- tris: total 4,404 (budget 10k/part, 20k/building); largest part Depot_Bay1Vent_Dark_01 36 tris
- backfaces from POV 3P and game cams: 0 px
- world bbox (studs, incl. ground slab + dressing): x 10..50 (40), plan y 60..94 (34), z -0.5..31.3 (bell cote apex; was 27.0)
- wall footprint (build facts): x 18..42 (24), plan y 76..90 (14), eave 14; matches blueprint
- doorway clear 8.2 w x 10.0 h (was 7.7); avatar stand-in 5 studs
- verify_palette (maker build log): ok, 0 spanning/off faces
- renders: depot_pov3p (stand plan (30,50), eye 9.5, FOV70), depot_pov1p (eye 5), depot_game 400x225 from fixed game cam; construction views 34/side/back/door from fixed build cameras
