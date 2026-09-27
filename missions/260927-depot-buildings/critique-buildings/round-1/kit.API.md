reset() -> scene (empty, palette material, sun, world); coll(name)
box(name, center, size, cell, coll, rot=(deg x,y,z)); prism(name, profile[(a,z)], depth, loc, cell, coll, axis="Y"|"X", rot_z)
cyl(name, center, r, h, cell, coll, segs=8, axis, r2); gable_roof(prefix, x0,x1, ycen, depth, eave_z, ridge_z, coll, overhang, thick, axis, nn, tag)
avatar(name, loc, coll); cam(name, loc, look, fov); milestone(prefix,k,stage,[(tag,cam)]); parts_of(prefix)
C = {stone,stonedark,mortar,timber,timberlt,slate,iron,moss,dark,glow,brass,paving,soot,door,gravel,brick}; bk = blender_kit
