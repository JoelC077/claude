# train.facts.md: Joel's train (Studio OBJ export temp2.obj, 2026-09-29)

Source: `8ada0157-Archive.zip` -> temp2.obj (957 groups, 191,938 verts, 113,588 faces), temp2.mtl, 55 textures.
Raw copy lives outside git (scratchpad `train/`). Parsed tables: `src/analysis/groups.json` (per-group bbox), `src/analysis/Union22.boxes.json`.
Units: studs, Roblox world coordinates (Y up). Studio names are generic ("Part", "Union", ...); OBJ numbering (Part1..N, Union1..N) is
the exporter's, so Studio code must find parts by geometry, never by these names.
Colours: MTL Kd = (RGB/255)^2.2, so RGB = round(255 * Kd^(1/2.2)) (verified: Part15Mtl -> 163,162,165 Medium stone grey).

## Layout (train along world Z, front = low Z)
| item | z range | notes |
|---|---|---|
| front walkway stub (Carriage 1) | 46.28 - 52.98 | plate 9.7 x 0.2 x 6.7 + 4 posts/side + top rails (loose Parts, same design as the gangway) |
| Carriage 1 (front, green body RGB 89,111,93) | 51.72 - 114.19 | roof union 19.48 x 3.59 x 62.34; bogie unions to 114.19 (wheel rim) |
| join J1 gap between end walls | 113.68 - 120.08 | C1 rear wall face 113.68 (door + glass); C2 front wall face 120.08 |
| Carriage 2 (rear, blue-grey body) | 119.12 - 181.59 | identical carriage, pitch +67.40 z |
| rear observation platform (Carriage 2) | 180.98 - 185.48 | full-width floor + baluster fence |
Body x -67.79..-48.31 (centre -58.05); floor top y 13.927; roof top y 27.98; wheel bottoms (rail) y 5.33.
Each carriage: side door + yellow steps (Part22Mtl) at its FRONT end only; double end door at its REAR end opening onto the gangway.
Under the gangway: empty between z 114.19 (C1 bogie wheel) and 120.77 (C2 bogie); bogie frame top y 12.59; no coupler, buffers or hoses exist.

## The only part crossing the join: Union22 (Studio: a UnionOperation)
bbox x[-62.964, -53.264] y[13.727, 18.127] z[113.576, 120.876]; size 9.7 x 4.4 x 7.3; centre (-58.114, 15.927, 117.226).
Material DiamondPlate, colour Medium stone grey 163,162,165. Exact decomposition (15 original Parts):
| piece | x | y | z |
|---|---|---|---|
| plate | -62.964..-53.264 | 13.727..13.927 | 113.576..120.276 |
| posts 0.2x4.2x0.2, W and E | centres -62.464 / -53.764 | 13.927..18.127 | centres 114.376 + n (n=0..5) |
| top rail W | -62.564..-62.364 | 17.927..18.127 | 113.676..120.876 (last 0.8 buried in C2 wall Part374) |
| top rail E | -53.864..-53.664 | 17.927..18.127 | 113.676..120.176 |
Every other part lies wholly on one side of z = 116.876 (checked: no other bbox crosses 113.7..120.0 except C1/C2 own pieces).

## Coupling plane
z_c = 116.876 = midpoint of the end-wall faces (116.88) = midpoint between posts 3 and 4 (116.376 / 117.376): the cut crosses no post.
Join frame J: origin = Union22 bbox centre (-58.114, 15.927, 117.226), axes = train axes, +Z toward the rear carriage.
In J: floor top y = -2.0; plate y -2.2..-2.0, z -3.65..3.05; posts x +-4.35, y -2.0..2.2, z centres -2.85 + n; rails y 2.0..2.2; z_c = -0.35.
C1 wall face J z -3.546; C2 wall face J z 2.854; C1 bogie end J z -3.036; C2 bogie start J z 3.544.

## Canon used
gameplay.crisis.coupling (proposed): "coupling snaps: lose the carriage and its passengers"; gameplay.crisis.breakdowns: "coupling strain".
World scrolls past a static train (rr-profile). gameplay.speed.normal 35 studs/s, slow 20; gameplay.run.brake_const 5; OQ-043 default hard brake ~2x.
Tokens: style.world.ironwork #363A42, style.world.soot_black #15181B, style.world.brass #C9953A (Reflectance 0.12-0.15), style.brand.hazard_yellow #F2C230.
