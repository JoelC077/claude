import bpy
E="/home/user/claude/missions/260927-depot-buildings/export"
bpy.ops.wm.open_mainfile(filepath=f"{E}/depot/Depot.blend")
with bpy.data.libraries.load(f"{E}/hall/Hall.blend") as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith("Hall_")]
c = bpy.data.collections.new("Hall"); bpy.context.scene.collection.children.link(c)
for o in dst.objects: c.objects.link(o)
bpy.ops.wm.save_as_mainfile(filepath=f"{E}/DepotLobby_buildings.blend")
print("COMBINED", len([o for o in bpy.data.objects if o.type=="MESH"]))
