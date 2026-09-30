import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import bpy
from scene import *
out = sys.argv[1]; only = sys.argv[2:] 
reset(); objs = import_train(); world(); ground()
print('objects', len(objs))
J = r2b((-58.1, 16.0, 116.6))
views = {
 'orig_overview': cam('ov', (-2, -30, 40), (-58, -118, 15), lens=24),
 'orig_join_34': cam('j34', (-28, -96, 30), J, lens=32),
 'orig_join_side': cam('js', (0, -116.6, 17), r2b((-58.1, 17.0, 116.6)), ortho=26),
 'orig_join_top': cam('jt', (-58.1, -116.6, 70), (-58.1, -116.61, 13), ortho=30),
}
for k, c in views.items():
    if only and k not in only: continue
    render(c, os.path.join(out, k + '.png'), res=(1400, 800), samples=16)
