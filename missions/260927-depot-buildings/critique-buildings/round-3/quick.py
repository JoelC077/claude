import bpy,sys
sys.path.insert(0,"/home/user/claude/missions/260927-depot-buildings/src"); import kit
from PIL import Image
blend,cams,out=sys.argv[1],sys.argv[2].split(","),sys.argv[3]
bpy.ops.wm.open_mainfile(filepath=blend)
ims=[]
for i,c in enumerate(cams):
    p=f"/tmp/claude-0/q{i}.png"; kit.bk.render(bpy.data.objects[c],p,res=(640,360),samples=8); ims.append(Image.open(p))
W=Image.new("RGB",(1280,360*((len(ims)+1)//2)))
for i,im in enumerate(ims): W.paste(im,((i%2)*640,(i//2)*360))
W.save(out)
