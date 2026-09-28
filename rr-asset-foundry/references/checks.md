# Checks: what failed and how to fix it (read on a FAIL)

Every check runs on every variant; the numbers are in `facts.md`, raw data in `result.json` (names of the parts involved). Fix the family code or the params, then `fdy make ... --force`. Never loosen a check to pass.

| check | fails when | usual cause | fix |
|---|---|---|---|
| names | a part is not `<Asset>_<Part>_<Group>_<nn>` | asset or part name with `_` or lower-case start | CamelCase names; `--name` letters and digits only |
| tris cap | a MeshPart over `tech.mesh.tris_cap` (warning over `tris_target`) | high `segs`, or a merged group (track, LOD1) that is too big | fewer segments; split the group; shorter pieces |
| palette | `verify_palette` not ok: a cell off its hex, a face spanning cells or near a cell edge | a part created outside `k.*`, or a colour edited after the atlas | build every part through the kit |
| back faces | a camera (3/4 or POV 3P, 200 px ray grid, each hit confirmed by 4 sub-pixel rays) sees faces from behind; Roblox culls them | an open mesh (a lone quad, a prism profile wound oddly), a part edited after the kit made it, or a camera inside a part | closed meshes only; the kit recalculates normals, so look for open or hand-edited geometry |
| coplanar | two parts have same-facing faces in one plane that overlap | flush details, frames on jambs, parts ending on the same plane | overlap or stagger by 0.02+ (see families.md geometry rules); `result.json` lists the pairs |
| floating | a part's bounding box touches nothing connected to the ground | a detail placed a gap away from its support, a proud plate at the wrong depth | move it to touch or overlap its support within 0.05 |
| reimport | the FBX re-imports at the wrong size (about 3.57x or 0.28x is the metre/stud bug) | scene units or export scale changed | leave forge's export settings alone; the unit system must stay NONE |
| Lua syntax | `studio_setup.lua` does not parse (luaparse, or block balance without it) | a family RULES value that is not valid Lua | values like `"Enum.CollisionFidelity.Box"` are written raw; plain strings are quoted |
| canon gate | `bible check studio_setup.lua` fails | a group token resolved to an off-canon hex (bible changed), or the file was edited by hand | re-plan and rebuild; never hand-edit the generated script |
| forge error | the build crashed (exit code in manifest, last log lines printed) | a family bug or a param combination the family cannot build | read `forge.log`, fix the family, and make `validate()` refuse the bad range (`ERROR:`; batches mark it `refused` and carry on) |

Warnings (never block): a key feature under `style.line.min_feature_px` at the 400 px game view (make it chunkier or drop it from VIEW features), family `validate()` messages, over the tris target.

## What "ok" does not mean

The checks are objective and geometric. They do not judge silhouette, proportion, style or whether the variant reads at a glance; that is the critic's job (`fdy crit`). They also do not test Studio: import, collision behaviour, ladder climbing and the setup script are owner tests.

## Output layout

```
<out>/<Asset>/        plan.json  manifest.json  result.json  facts.md  README.md  forge.log
                      <Asset>.fbx  <Asset>_atlas.fbx  palette.png  [<Asset>_LOD1.fbx]  <Asset>.blend
                      parts.csv  studio_setup.lua  renders/{thumb,game,pov3p,pov1p,34,side,end[,top]}.png
<out>/batch-<Base>/   batch.json  batch.md  sheet-N.png (+ .json)  vNNN/ (one variant folder each)
<CRIT>/               brief.md  pass-N/{contact.png, closeups.png, facts.md, renders}   (then critic_kit.py)
```

`manifest.json` status: `ok`, `fail` (checks failed, files written) or `error` (forge crashed); batch rows can also be `refused` (the family's `validate()` rejected the combination at plan time, nothing built). Batches resume by the plan hash (family file + params + seed + groups + options; renders are not part of it, so adding renders to a variant rebuilds nothing).
