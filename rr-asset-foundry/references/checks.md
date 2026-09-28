# Checks: what failed and how to fix it (read on a FAIL)

Every check runs on every variant; the numbers are in `facts.md`, raw data in `result.json` (names of the parts involved). Fix the family code or the params, then `fdy make ... --force`. Never loosen a check to pass.

| check | fails when | usual cause | fix |
|---|---|---|---|
| names | a part is not `<Asset>_<Part>_<Group>_<nn>` | asset or part name with `_` or lower-case start | CamelCase names; `--name` letters and digits only |
| tris cap | a MeshPart over `tech.mesh.tris_cap` (warning over `tris_target`) | high `segs`, or a merged group (track, LOD1) that is too big | fewer segments; split the group; shorter pieces |
| palette | `verify_palette` not ok: a cell off its hex, a face spanning cells or near a cell edge | a part created outside `k.*`, or a colour edited after the atlas | build every part through the kit |
| back faces | any POV (every stand, 3P and 1P) or construction camera (3/4, side, end, top) sees faces from behind (200 px ray grid, ortho rays for side/end/top, each hit confirmed by 4 sub-pixel rays); Roblox culls them | an open mesh (a lone quad, a prism profile wound oddly), a part edited after the kit made it, or a camera inside a part | closed meshes only; the kit recalculates normals, so look for open or hand-edited geometry |
| coplanar | two parts have same-facing faces in one plane that overlap | flush details, frames on jambs, parts ending on the same plane | overlap or stagger by 0.02+ (see families.md geometry rules); `result.json` lists the pairs |
| floating | a part's bounding box touches nothing connected to the ground | a detail placed a gap away from its support, a proud plate at the wrong depth | move it to touch or overlap its support within 0.05 |
| reimport | the FBX re-imports at the wrong size (about 3.57x or 0.28x is the metre/stud bug) | scene units or export scale changed | leave forge's export settings alone; the unit system must stay NONE |
| Lua syntax | `studio_setup.lua` does not parse (luaparse, or block balance without it) | a family RULES value that is not valid Lua | values like `"Enum.CollisionFidelity.Box"` are written raw; plain strings are quoted |
| canon gate | `bible check studio_setup.lua` fails | a group token resolved to an off-canon hex (bible changed), or the file was edited by hand | re-plan and rebuild; never hand-edit the generated script |
| forge error | the build crashed (exit code in manifest, last log lines printed) | a family bug or a param combination the family cannot build | read `forge.log`, fix the family, and make `validate()` refuse the bad range (`ERROR:`; batches mark it `refused` and carry on) |

Warnings (never block): a key feature under `style.line.min_feature_px` at the 400 px game view, family `validate()` messages, over the tris target.

**A5 (key features at game distance).** For each `VIEW["features"]` key (the exact `<Part>` token; the `<Group>` token for merged parts), every piece (mesh island) in frame is projected and its thinnest on-screen width taken (convex hull, rotating calipers); the smallest per key is reported with how many pieces are under the bar, on the 400 px game view (warns) and the POV 3P (facts only). Occlusion is ignored. Fix by making the piece chunkier; the 3/4 view foreshortens a side to about 0.8, so on a 30-stud vehicle a vertical strap needs about 1.3 x 0.3 studs (0.45 measured 2.7 px, 0.9 x 0.18 3.8 px) and a horizontal bar about 1.1 tall. Drop a key only if the piece is decoration that may vanish.

## What "ok" does not mean

The checks are objective and geometric. They do not judge silhouette, proportion, style or whether the variant reads at a glance; that is the critic's job (`fdy crit`). They also do not test Studio: import, collision behaviour, ladder climbing and the setup script are owner tests.

## Output layout

```
<out>/<Asset>/        plan.json  manifest.json  result.json  facts.md  README.md  forge.log
                      <Asset>.fbx  <Asset>_atlas.fbx  palette.png  [<Asset>_LOD1.fbx]  <Asset>.blend
                      parts.csv  studio_setup.lua  renders/{thumb,game,pov3p,pov3p_2[,pov3p_3],pov1p,34,side,end[,top]}.png
<out>/batch-<Base>/   batch.json  batch.md  sheet-N.png (+ .json)  vNNN/ (one variant folder each)
<CRIT>/               brief.md  pass-N/{contact.png, closeups.png, facts.md, renders}   (then critic_kit.py)
```

`manifest.json` status: `ok`, `fail` (checks failed, files written) or `error` (forge crashed or timed out, or a batch variant was refused a folder); batch rows can also be `refused` (the family's `validate()` rejected the combination at plan time, nothing built).

Identity: `vkey` = asset + params + seed + groups + build options (the variant); `hash` = vkey + the family file, the helpers it imports (`families/_*.py`), `fkit.py`, `forge.py`, and the plan's canon numbers, stage colours and view. Same hash and ok/fail: up to date (missing renders or a new `--pov` premise are rendered in place, nothing rebuilt). Same vkey, new hash or last status error: rebuilt, in `make` and on a batch resume. Different vkey in the folder: refused unless `--name` or `--force`. A multiuse-critic `blender_kit.py` update does not rebuild; use `--force`.
