"""Shared scene setup: import Joel's Studio OBJ into Blender (Z-up), lights, world, cameras.
Blender coords from a Studio OBJ (Y-up): bx = rx, by = -rz, bz = ry. Front of train = +by (rz small)."""
import bpy, math, os, sys
from mathutils import Vector
OBJ = os.environ.get('RR_TRAIN_OBJ', '/tmp/claude-0/-home-user-claude/7feb16c0-5cf3-5a92-a257-eb9720cba30b/scratchpad/train/temp2.obj')

def r2b(p):
    """Roblox world (x, y, z) -> Blender (x, -z, y)."""
    return Vector((p[0], -p[2], p[1]))

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def roblox_look(mats):
    """Roblox tints the material texture by the part Color: base = Kd x texture (OBJ importer drops Kd)."""
    for m in mats:
        if not m.use_nodes: continue
        nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not bsdf: continue
        kd = tuple(bsdf.inputs['Base Color'].default_value)
        # detach alpha map (Roblox writes map_d = diffuse, which would make parts see-through)
        for l in list(bsdf.inputs['Alpha'].links): nt.links.remove(l)
        bsdf.inputs['Alpha'].default_value = 1.0 if 'Glass' not in m.name else 0.35
        bsdf.inputs['Roughness'].default_value = 0.7
        links = list(bsdf.inputs['Base Color'].links)
        if links:
            src = links[0].from_socket
            mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 1.0
            nt.links.new(src, mix.inputs[6]); mix.inputs[7].default_value = kd
            nt.links.new(mix.outputs[2], bsdf.inputs['Base Color'])
        # normal maps from Roblox are subtle; drop bump to keep reads clean
        for l in list(bsdf.inputs['Normal'].links): nt.links.remove(l)

def import_train(path=OBJ, split=True):
    before = set(bpy.data.objects); mb = set(bpy.data.materials)
    bpy.ops.wm.obj_import(filepath=path, forward_axis='NEGATIVE_Z', up_axis='Y', use_split_groups=split)
    objs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    roblox_look([m for m in bpy.data.materials if m not in mb])
    return objs

def world(strength=0.9, sun=3.2):
    w = bpy.data.worlds.new('W'); bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.62, 0.72, 0.86, 1); bg.inputs[1].default_value = strength
    s = bpy.data.lights.new('Sun', 'SUN'); s.energy = sun; s.angle = math.radians(8)
    so = bpy.data.objects.new('Sun', s); bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), math.radians(12), math.radians(35))
    sc = bpy.context.scene
    sc.view_settings.view_transform = 'AgX' if 'AgX' in [i.identifier for i in sc.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Filmic'
    sc.cycles.use_denoising = True

def ground(z=5.33, size=600, color=(0.33, 0.30, 0.26)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(-58, -116, z - 0.01))
    g = bpy.context.active_object; g.name = 'Ground'
    m = bpy.data.materials.new('GroundMat'); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*color, 1)
    g.data.materials.append(m)
    return g

def cam(name, loc, look, lens=35, ortho=None):
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.context.scene.collection.objects.link(c)
    c.location = Vector(loc)
    c.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.data.lens = lens; c.data.clip_start = 0.05; c.data.clip_end = 5000
    if ortho:
        c.data.type = 'ORTHO'; c.data.ortho_scale = ortho
    return c

def render(c, path, res=(1600, 900), samples=24):
    sc = bpy.context.scene
    sc.camera = c; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path
