import bpy, sys
sys.path.insert(0, "/home/user/claude/missions/260927-depot-buildings/src"); import kit
bpy.ops.wm.read_factory_settings(use_empty=True)
for f in sys.argv[sys.argv.index("--")+1:]:
    print("REIMPORT", f); r = kit.bk.reimport(f); print("RESULT", r)
