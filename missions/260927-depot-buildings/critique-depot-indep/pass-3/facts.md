## Depot (measured fresh from src/depot/depot.blend, 2026-09-27, pass 3)
- parts (separate named Depot_* mesh objects): 389 (was 341); materials: 1 (palette atlas, 24 cells)
- tris: ~4,980 total (budget 10k/part, 20k/building); largest parts 36 tris (vents, drums, cart wheels)
- backfaces from POV 3P and game cams: 0 px
- world bbox (studs, incl. ground slab + dressing): x 10..50 (40), plan y 60..94 (34), z -0.5..31.3 (bell cote apex)
- wall footprint 24x14, eave 14; matches blueprint
- doorway clear 8.2 w x 10.0 h; hazard step nosing 1.5x1.5x11; name board 2.8 tall (frame 3.4)
- no orange on roofline (bargeboards ink); yard rail hazard-yellow with 10-stud gap on door axis
- renders: depot_pov3p (stand (30,-58), eye 9.5, FOV70) and depot_pov1p (eye 5) at 400x225; depot_game 400x225 from fixed game cam; construction views 34/side/back/door 1280x720 from fixed build cameras
