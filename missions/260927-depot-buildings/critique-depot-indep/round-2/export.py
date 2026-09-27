"""Roblox export per building: python3 export.py depot|hall
Writes export/<b>/: <B>.fbx (plain material per recolour group, no texture -> Color3 recolours),
<B>_atlas.fbx (palette-atlas UVs + palette.png), <B>.blend, build.py, parts.csv, studio_setup.lua, README.md."""
import bpy, sys, os, csv, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit

b = sys.argv[-1]
B = b.capitalize()
SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(kit.M, "export", b)
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(SRC, b, f"{b}.blend"))
for o in list(bpy.data.objects):
    if o.type != "MESH" or not o.name.startswith(B + "_"):
        bpy.data.objects.remove(o)
parts = kit.parts_of(B)
HEX = {name: kit.PALETTE[i] for name, i in kit.C.items()}
ROBLOX_MAT = {"stone": "Slate", "stonedark": "Slate", "stonelt": "Slate", "mortar": "Concrete", "timber": "Wood",
              "timberlt": "WoodPlanks", "slate": "Slate", "soot": "Slate", "iron": "Metal", "brass": "Metal",
              "moss": "Grass", "dark": "SmoothPlastic", "glow": "Neon", "paving": "Concrete", "door": "Wood",
              "gravel": "Pebble", "brick": "Brick", "hazard": "SmoothPlastic", "ink": "SmoothPlastic",
              "teal": "Wood", "cream": "SmoothPlastic", "slatedk": "Slate", "red": "SmoothPlastic"}
NOCOLLIDE = ("Gutter", "Downpipe", "Ivy", "Moss", "Barge", "Finial", "Vent", "Soot", "Ashlar", "Quoin", "StepNosing",
             "Win", "Roundel", "Keystone", "Cupola", "Canopy", "NameBoard", "Interior", "Lamp", "Ridge", "String", "BellCote", "Notice")


def group(o):
    return o.name.split("_")[2].lower()          # <Bldg>_<Part>_<Mat>_<nn>


rows = []
dg = bpy.context.evaluated_depsgraph_get()
for o in parts:
    me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); t = len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
    g = group(o)
    rows.append(dict(name=o.name, group=g.capitalize(), material=ROBLOX_MAT[g], palette_cell=kit.C[g], hex=HEX[g], tris=t,
                     cancollide=str(not any(k in o.name for k in NOCOLLIDE)).lower()))
with open(os.path.join(OUT, "parts.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)

# apply transforms so Studio pivots are clean at the part centre after import
bpy.ops.object.select_all(action="DESELECT")
for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]

# atlas FBX (the palette atlas route; textures embedded)
shutil.copy(os.path.join(SRC, "palette.png"), os.path.join(OUT, "palette.png"))
atlas = os.path.join(OUT, f"{B}_atlas.fbx")
bpy.ops.export_scene.fbx(filepath=atlas, use_selection=True, apply_scale_options="FBX_SCALE_UNITS",
                         path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE", bake_space_transform=True)

# plain FBX: one untextured material per recolour group
mats = {}
for o in parts:
    g = group(o)
    if g not in mats:
        m = bpy.data.materials.new(g.capitalize())
        r, gg, bb = (int(HEX[g][i:i + 2], 16) / 255 for i in (1, 3, 5))
        m.diffuse_color = (r, gg, bb, 1)
        mats[g] = m
    o.data.materials.clear(); o.data.materials.append(mats[g])
plain = os.path.join(OUT, f"{B}.fbx")
bpy.ops.export_scene.fbx(filepath=plain, use_selection=True, apply_scale_options="FBX_SCALE_UNITS",
                         path_mode="STRIP", mesh_smooth_type="FACE", bake_space_transform=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"{B}.blend"), copy=True)
shutil.copy(os.path.join(SRC, b, "build.py"), os.path.join(OUT, "build.py"))
shutil.copy(os.path.join(SRC, "kit.py"), os.path.join(OUT, "kit.py"))

# Studio command-bar script: anchoring/collision + recolour table
lua = kit.bk.studio_setup_lua(B, {"Anchored": True, "CanCollide": True, "CastShadow": True},
                              [(f"^{B}_[^_]*{k}", {"CanCollide": False, "CollisionFidelity": "Enum.CollisionFidelity.Box"}) for k in NOCOLLIDE])
grp = {}
for r in rows:
    grp.setdefault(r["group"], r)
lines = ["", "-- RECOLOUR: edit one line per group (TextureID is cleared so Color shows).",
         "local GROUPS = {"]
for g, r in sorted(grp.items()):
    lines.append(f'  {g} = {{color = Color3.fromHex("{r["hex"][1:]}"), material = Enum.Material.{r["material"]}}},')
lines += ["}",
          "for _, p in ipairs(root:GetDescendants()) do",
          '  if p:IsA("BasePart") then',
          '    local g = GROUPS[(p.Name:split("_")[3] or "")]',
          "    if g then",
          '      if p:IsA("MeshPart") then p.TextureID = "" end',
          "      p.Color = g.color; p.Material = g.material",
          "    end",
          "  end",
          "end",
          'print("recolour groups applied")']
open(os.path.join(OUT, "studio_setup.lua"), "w").write(lua + "\n" + "\n".join(lines) + "\n")

size = kit.bk._bbox(parts)
open(os.path.join(OUT, "README.md"), "w").write(
    f"# {B} for Roblox\n"
    f"1. Studio > 3D Importer: import `{B}.fbx` (plain, recolourable). Keep hierarchy; do NOT merge meshes. Expected size {size.x:.0f} x {size.z:.0f} x {size.y:.0f} studs (X, height, depth); if it is 3.57x bigger/smaller, fix the importer scale.\n"
    f"2. Select the imported model and paste `studio_setup.lua` into the command bar: anchors, sets collision, applies the recolour groups.\n"
    f"3. Recolour later: edit the GROUPS line for that group (e.g. Stone) and re-run, or recolour single parts in Properties.\n"
    f"4. `{B}_atlas.fbx` + `palette.png` = the palette-atlas version (one texture, 32px cells) if you prefer texture colours; its TextureID hides Color.\n"
    f"5. `build.py` + `kit.py` rebuild everything in Blender; `parts.csv` lists every part, its group, colour, tris and CanCollide.\n")
print("EXPORT", B, len(parts), "parts", f"{size.x:.1f}x{size.y:.1f}x{size.z:.1f}")
