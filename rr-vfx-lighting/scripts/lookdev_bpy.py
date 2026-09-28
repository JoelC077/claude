#!/usr/bin/env python3
"""lookdev_bpy.py: lighting-look previews for rr-vfx-lighting in headless Blender (bpy 4.x/5.x, Cycles).

  python3 lookdev_bpy.py --looks "grassland.day,cutting.day+tunnel_under@door1p" --out DIR
                         [--phone grassland.day] [--res 768x432] [--samples 16] [--quick]

A look is biome.time[+override][@camera]; cameras (CAMERAS): roof3p (player on coach B's roof, third-person
eye), door1p (leaning out of coach A's doorway), cab1p (loco cab, tech.camera.cab_view, sees the firebox) and
coach1p (inside coach A, facing the power box end). Eye heights, FOV, gauge and the rolling-stock envelope come
from rr-bible. Per look it writes <slug>.png, <slug>.facts.json, view_<slug>.json + <slug>.depth.png (for
fxsim.py pov), and for looks named in --phone <slug>.phone.png at the phone resolution (tech.ui_platform.phone)
with its own view_<slug>.phone.json (no shadows, no Bloom or SunRays: tech.lighting.post_low_quality).
Presets: --presets DIR, else $RR_VFX_PRESETS, else the shipped library.

This is an approximation, not Roblox: Cycles renders the lit scene; numpy then applies exposure, bloom,
a filmic tone curve, sky and Atmosphere fog from depth, sun rays and ColorCorrection. Every mapping and
its caveat: references/fidelity.md. Needs bpy and numpy (numpy ships with bpy).
"""
import sys
sys.dont_write_bytecode = True  # never leave __pycache__ inside the skill
import argparse, json, math, os, random, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import vfx  # noqa: E402

try:
    import bpy
    import numpy as np
    from mathutils import Vector
except ImportError:
    bpy = None

# calibration constants of the preview (not Roblox numbers): see references/fidelity.md
SUN_K = 1.0        # Blender sun strength per unit of Lighting.Brightness
MOON_K = 0.16      # moon strength per unit of Brightness when the sun is below the horizon
OA_K = 2.2         # world light per unit of OutdoorAmbient (linear)
ENV_K = 0.6        # world light per unit of EnvironmentDiffuseScale x sky
AMB_K = 2.5        # unoccluded Ambient term (material emission) per unit of Ambient (linear)
CST_K = 1.5        # ColorShift_Top added to the sun colour
EXPO_K = 1.0       # overall exposure into the tone curve
FOG_K = 0.0049     # Atmosphere: optical depth per stud per unit Density (0.3 -> ~95% at 2048 studs)
HAZE_K = 0.00012   # extra far haze per unit Haze
LIGHT_K = 0.9      # Blender watts per Roblox Brightness x Range^2 for local lights
DEFAULT_SKY = (0.435, 0.639, 0.851)  # Roblox's default blue skybox zenith, approximated (sRGB)
CLASSES = {"sky": 0, "ground": 1, "track": 2, "train": 3, "trim": 4, "scenery": 5, "structure": 6, "hazard": 7}


def B(v):
    """Roblox (x, y up, z) -> Blender (x, -z, y up)."""
    return (v[0], -v[2], v[1])


def srgb_lin(c):
    c = c / 255.0 if c > 1 else c
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_lin(hx):
    hx = hx.lstrip("#")
    return [srgb_lin(int(hx[i:i + 2], 16)) for i in (0, 2, 4)]


def tv_lin(tv):
    """typed colour/light -> linear rgb 0..1."""
    if tv is None:
        return [0, 0, 0]
    if tv[0] == "light":
        return [srgb_lin(c) for c in tv[1]]
    return hex_lin(tv[1])


def tv_srgb(tv):
    if tv[0] == "light":
        return [c / 255 for c in tv[1]]
    hx = tv[1].lstrip("#")
    return [int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4)]


# ------------------------------------------------------------------ canon-driven dimensions
class Canon:
    def __init__(self, model):
        b = model.bible
        n = (lambda k, d: b.number(k, d)) if b.ok() else (lambda k, d: d)
        self.eye_3p = n("tech.camera.eye_3p", 9.5)
        self.eye_1p = n("tech.camera.eye_1p", 4.5)
        self.fov = n("tech.camera.fov_v", 70)
        self.segment = n("tech.units.segment_len", 512)
        self.poles = n("tech.units.pole_spacing", 128)
        self.ballast_w = n("tech.units.ballast_w", 24)
        self.train_len = n("tech.units.train_len", 165)
        self.ahead = n("tech.streaming.window", 4)
        self.cab_eye = n("tech.camera.cab_view", 12)
        d = model.dims   # tech.units.gauge, stock_width, stock_roof, stock_floor (proposed, OQ-030)
        self.gauge, self.half_w, self.roof, self.floor = d["gauge"], d["width"] / 2, d["roof"], d["floor"]
        import re
        bore = b.value("world.prefabs.10", "") if b.ok() else ""
        m = re.search(r"bore (\d+) h x (\d+) w", bore or "")
        self.bore_h, self.bore_w = (float(m.group(1)), float(m.group(2))) if m else (18.0, 30.0)
        ph = re.findall(r"\d+", (b.value("tech.ui_platform.phone", "") if b.ok() else "") or "")
        self.phone_res = (int(ph[0]), int(ph[1])) if len(ph) >= 2 else (844, 390)
        self.used = ["tech.camera.eye_3p", "tech.camera.eye_1p", "tech.camera.fov_v", "tech.camera.cab_view",
                     "tech.units.segment_len", "tech.units.pole_spacing", "tech.units.ballast_w", "tech.units.train_len",
                     "tech.units.gauge", "tech.units.stock_width", "tech.units.stock_roof", "tech.units.stock_floor",
                     "tech.streaming.window", "tech.ui_platform.phone", "world.prefabs.10"]


# ------------------------------------------------------------------ scene building
class Scene:
    def __init__(self, model, canon, kind):
        self.model, self.c, self.kind = model, canon, kind
        self.mats, self.objs = {}, []
        self.rnd = random.Random(11)

    def colour(self, ref):
        c = self.model.ctx.colour(ref, "lookdev")
        return c[0] if c else "#808080"

    def mat(self, ref, metal=0.0, rough=0.85, emit=None):
        key = (ref, metal, rough, emit)
        if key in self.mats:
            return self.mats[key]
        m = bpy.data.materials.new(f"M_{ref.strip('@$').replace('.', '_')}_{len(self.mats)}")
        m.use_nodes = True
        bsdf = m.node_tree.nodes["Principled BSDF"]
        lin = hex_lin(self.colour(ref))
        bsdf.inputs["Base Color"].default_value = (*lin, 1)
        bsdf.inputs["Metallic"].default_value = metal
        bsdf.inputs["Roughness"].default_value = rough
        m["base_lin"] = lin
        m["self_emit"] = 0.0
        if emit:
            m["self_emit"] = emit
        self.mats[key] = m
        return m

    def _obj(self, name, verts, faces, mat, cls):
        me = bpy.data.meshes.new(name)
        me.from_pydata([B(v) for v in verts], [], faces)
        me.update()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(mat)
        ob.pass_index = CLASSES[cls]
        self.objs.append(ob)
        return ob

    def box(self, name, x0, x1, y0, y1, z0, z1, ref, cls, **mk):
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        # faces wound outward in Roblox axes; B() is a proper rotation so winding survives
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)]
        return self._obj(name, v, f, self.mat(ref, **mk), cls)

    def cyl_x(self, name, x0, x1, cy, cz, r, ref, cls, n=16, **mk):
        v, f = [], []
        for i in range(n):
            a = 2 * math.pi * i / n
            v += [(x0, cy + r * math.cos(a), cz + r * math.sin(a)), (x1, cy + r * math.cos(a), cz + r * math.sin(a))]
        for i in range(n):
            j = (i + 1) % n
            f.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
        f.append(tuple(2 * i for i in range(n))[::-1])
        f.append(tuple(2 * i + 1 for i in range(n)))
        return self._obj(name, v, f, self.mat(ref, **mk), cls)

    def cyl_y(self, name, cx, cz, y0, y1, r, ref, cls, n=12, **mk):
        v, f = [], []
        for i in range(n):
            a = 2 * math.pi * i / n
            v += [(cx + r * math.cos(a), y0, cz + r * math.sin(a)), (cx + r * math.cos(a), y1, cz + r * math.sin(a))]
        for i in range(n):
            j = (i + 1) % n
            f.append((2 * i, 2 * i + 1, 2 * j + 1, 2 * j))
        f.append(tuple(2 * i for i in range(n)))
        f.append(tuple(2 * i + 1 for i in range(n))[::-1])
        return self._obj(name, v, f, self.mat(ref, **mk), cls)

    # -------------------------------------------------------------- parts
    def ground(self, y=-0.8, extent=6000):
        self.box("Ground", -extent, extent, y - 1, y, -extent, extent, "@style.ground.pasture", "ground")
        for i in range(60):   # patches: vary value more than hue (style.material.ground_value)
            ref = self.rnd.choice(["@style.ground.damp_hollow", "@style.ground.dry_ridge", "@style.ground.straw", "@style.ground.pasture"])
            x = self.rnd.uniform(-1200, 2400)
            z = self.rnd.choice([-1, 1]) * self.rnd.uniform(20, 700)
            s = self.rnd.uniform(15, 70)
            self.box(f"Patch{i}", x - s, x + s * 1.6, y, y + 0.05 + i * 0.001, z - s * 0.6, z + s * 0.6, ref, "ground")

    def track(self, z=0.0, y=-0.8, x0=-1500, x1=3200, tag=""):
        w = self.c.ballast_w
        self.box(f"Ballast{tag}", x0, x1, y, -0.25, z - w / 2, z + w / 2, "@style.ground.ballast", "track")
        g = self.c.gauge / 2   # rail centres from canon (tech.units.gauge)
        for s in (-g, g):
            self.box(f"Rail{tag}{s}", x0, x1, -0.25, 0.25, z + s - 0.2, z + s + 0.2, "@style.ground.rail", "track", metal=0.4, rough=0.5)

    def lineside(self, x0=-1500, x1=3200):
        x = x0
        i = 0
        while x < x1:   # telegraph poles every tech.units.pole_spacing, the speedometer (av.feel.poles)
            # weathered grey-brown, not walnut: a red-brown pole read as red decoration (style.dont.red_decoration)
            self.box(f"Pole{i}", x - 0.4, x + 0.4, -0.8, 14, 15.6, 16.4, "@style.ground.bare_earth", "scenery")
            self.box(f"PoleArm{i}", x - 0.3, x + 0.3, 12.6, 13.1, 14, 18, "@style.ground.bare_earth", "scenery")
            x += self.c.poles
            i += 1
        for side in (-1, 1):
            x = x0
            k = 0
            while x < x1:
                ln = self.rnd.uniform(25, 70)
                h = self.rnd.uniform(4.5, 8)
                z = side * self.rnd.uniform(45, 60)
                self.box(f"Hedge{side}_{k}", x, x + ln, -0.8, h, z - 3, z + 3, "@style.ground.hedgerow", "scenery")
                x += ln + self.rnd.uniform(10, 40)
                k += 1
        for i in range(70):
            x = self.rnd.uniform(-900, 2600)
            z = self.rnd.choice([-1, 1]) * self.rnd.uniform(150, 600)
            h = self.rnd.uniform(14, 26)
            self.cyl_y(f"Trunk{i}", x, z, -0.8, h * 0.45, 1.0, "@style.world.walnut", "scenery", n=6)
            r = h * 0.35
            self.box(f"Crown{i}", x - r, x + r, h * 0.4, h, z - r, z + r, "@style.ground.hedgerow", "scenery")
        for i in range(10):   # far low hills so the fog has layers to eat
            x = self.rnd.uniform(-500, 3500)
            z = self.rnd.choice([-1, 1]) * self.rnd.uniform(900, 2200)
            w = self.rnd.uniform(300, 700)
            self.box(f"Hill{i}", x - w, x + w, -0.8, self.rnd.uniform(30, 90), z - w * 0.4, z + w * 0.4,
                     self.rnd.choice(["@style.ground.dry_ridge", "@style.ground.pasture"]), "scenery")

    def train(self, headlamp=False):
        """Stand-in train (livery open, OQ-025): navy bodies with a cream band and cream interiors (style.world.cream,
        coach walls), hazard-yellow capped-post roof rails (style.form.rails), red buffer beam. Envelope from canon."""
        navy, iron, cream, brass, soot = "@style.world.navy", "@style.world.ironwork", "@style.world.cream", "@style.world.brass", "@style.world.soot_black"
        W, fl, rf = self.c.half_w, self.c.floor, self.c.roof
        for tag, x0, x1 in (("B", -97.5, -45.5), ("A", -43.5, 8.5)):   # two coaches, doorway in A's right side
            self.box(f"Coach{tag}_Frame", x0 + 3, x1 - 3, 0.3, fl - 0.8, -W + 1.5, W - 1.5, soot, "train")
            self.box(f"Coach{tag}_Floor", x0, x1, fl - 0.8, fl, -W, W, "@style.world.walnut", "train")
            self.box(f"Coach{tag}_Roof", x0 - 0.2, x1 + 0.2, rf - 0.6, rf, -W - 0.3, W + 0.3, iron, "train")
            self.box(f"Coach{tag}_WallL", x0, x1, fl, rf - 0.6, -W, -W + 0.5, navy, "train")
            self.box(f"Coach{tag}_LineL", x0 + 0.5, x1 - 0.5, fl, rf - 0.6, -W + 0.5, -W + 0.6, cream, "train")
            if tag == "A":
                dh = fl + 7   # doorway 7 tall (tech.units.train_doorway)
                self.box("CoachA_WallR1", x0, -24, fl, rf - 0.6, W - 0.5, W, navy, "train")
                self.box("CoachA_WallR2", -16, x1, fl, rf - 0.6, W - 0.5, W, navy, "train")
                self.box("CoachA_DoorHead", -24, -16, dh, rf - 0.6, W - 0.5, W, navy, "train")
                self.box("CoachA_LineR1", x0 + 0.5, -24, fl, rf - 0.6, W - 0.6, W - 0.5, cream, "train")
                self.box("CoachA_LineR2", -16, x1 - 0.5, fl, rf - 0.6, W - 0.6, W - 0.5, cream, "train")
                self.box("PowerBoxCase", 3.5, 6.5, fl + 1.5, fl + 5.5, W - 1.4, W - 0.6, navy, "train")
            else:
                self.box(f"Coach{tag}_WallR", x0, x1, fl, rf - 0.6, W - 0.5, W, navy, "train")
                self.box(f"Coach{tag}_LineR", x0 + 0.5, x1 - 0.5, fl, rf - 0.6, W - 0.6, W - 0.5, cream, "train")
            for z0, z1 in ((-W - 0.1, -W), (W, W + 0.1)):
                self.box(f"Coach{tag}_Band{z0}", x0, x1, fl + 4.6, fl + 6.2, z0, z1, cream, "trim")
            self.box(f"Coach{tag}_EndF", x1 - 0.5, x1, fl, rf - 0.6, -W, W, navy, "train")
            self.box(f"Coach{tag}_EndR", x0, x0 + 0.5, fl, rf - 0.6, -W, W, navy, "train")
            for side in (-1, 1):   # capped-post hazard-yellow roof rails (style.form.rails): the players' edge
                zr = side * (W - 0.4)
                self.box(f"Coach{tag}_Rail{side}", x0 + 1, x1 - 1, rf + 1.3, rf + 1.6, zr - 0.15, zr + 0.15, "@style.world.hazard", "hazard")
                x = x0 + 1
                while x <= x1 - 1 + 1e-6:
                    self.box(f"Coach{tag}_Post{side}_{x:.0f}", x - 0.2, x + 0.2, rf, rf + 1.6, zr - 0.2, zr + 0.2, "@style.world.hazard", "hazard")
                    self.box(f"Coach{tag}_Cap{side}_{x:.0f}", x - 0.32, x + 0.32, rf + 1.6, rf + 1.85, zr - 0.32, zr + 0.32, "@style.world.hazard", "hazard")
                    x += (x1 - x0 - 2) / 6
        self.box("Tender", 10.5, 25.5, 1, 10, -W + 0.5, W - 0.5, navy, "train")
        self.box("TenderCoal", 11, 25, 10, 11, -W + 1, W - 1, "@style.cab.coal", "train")
        self.box("LocoFrame", 27.5, 67.5, 1, 4.5, -W + 1, W - 1, soot, "train")
        # cab: open-backed shell so the cab camera sees the backhead and firebox door (tech.camera.cab_view)
        self.box("CabWallL", 27.5, 36, 4.5, 8.5, -W, -W + 0.5, navy, "train")
        self.box("CabWallR", 27.5, 36, 4.5, 8.5, W - 0.5, W, navy, "train")
        for side in (-1, 1):   # interior trim (style.world.cream) and a walked floor (style.world.diamond_plate)
            self.box(f"CabLine{side}", 27.6, 35.5, 4.5, 8.4, min(side * (W - 0.6), side * (W - 0.5)), max(side * (W - 0.6), side * (W - 0.5)), cream, "train")
        self.box("CabFloor", 27.5, 35.5, 4.5, 4.6, -W + 0.5, W - 0.5, "@style.world.diamond_plate", "train")
        for side in (-1, 1):
            self.box(f"CabPostF{side}", 35.3, 36, 8.5, 13.5, min(side * W, side * (W - 0.5)), max(side * W, side * (W - 0.5)), navy, "train")
        self.box("Backhead", 35.5, 36, 4.5, 13.5, -W + 0.5, W - 0.5, soot, "train")
        for i, ref in enumerate(("@style.light.firebox_deep", "@style.light.firebox", "@style.light.firebox_hot")):
            self.box(f"FireboxNeon{i}", 35.3, 35.5, 5.6 + i * 0.5, 5.9 + i * 0.5, -1.1, 1.1, ref, "trim", emit=3.0)
        self.box("CabRoof", 27, 36.5, 13.5, 14.2, -W - 0.3, W + 0.3, iron, "train")
        self.cyl_x("Boiler", 36, 62, 9, 0, 4, iron, "train")
        for bx in (42, 52):
            self.cyl_x(f"BoilerBand{bx}", bx, bx + 0.6, 9, 0, 4.12, brass, "trim", metal=0.6, rough=0.35)
        self.cyl_x("Smokebox", 62, 66, 9, 0, 4.2, soot, "train")
        self.cyl_y("Chimney", 58, 0, 12.5, 17, 1.2, soot, "train")
        self.cyl_y("ChimneyRim", 58, 0, 16.4, 17, 1.45, brass, "trim", metal=0.6, rough=0.35)
        self.cyl_y("SafetyValve", 40, 0, 12.6, 14.2, 0.6, brass, "trim", metal=0.6, rough=0.35)
        self.box("BufferBeam", 66, 67.5, 1.5, 4, -W + 1, W - 1, "@style.brand.buffer_red", "trim")
        lamp = self.box("HeadlampLens", 66.8, 67.6, 8.3, 9.7, -0.7, 0.7, "@style.thumb.glow", "trim",
                        emit=(4.0 if headlamp else 0.0))
        return lamp

    def cab_lights(self, phone=False):
        """Canon baseline lights (budgets.json baseline): cab lamp and firebox light, as point lights."""
        for name, ref, pos, key in (("CabLamp", "@style.light.cab_lamp", (31.5, 13, 0), "style.light.cab_lamp"),
                                    ("FireboxLight", "@style.light.firebox", (34.8, 6.5, 0), "style.light.firebox")):
            b = self.model.bible
            txt = f"{b.value(key, '')} {(b.fact(key) or {}).get('note', '')}" if b.ok() else ""
            import re
            br = re.search(r"Brightness ([\d.]+)", txt)
            rg = re.search(r"Range ([\d.]+)", txt)
            L = bpy.data.lights.new(name, "POINT")
            L.color = hex_lin(self.colour(ref))
            L.energy = (float(br.group(1)) if br else 1.4) * LIGHT_K * (float(rg.group(1)) if rg else 12) ** 2
            L.shadow_soft_size = 0.5
            L.use_shadow = not phone
            ob = bpy.data.objects.new(name, L)
            bpy.context.scene.collection.objects.link(ob)
            ob.location = B(pos)

    def build(self):
        k = self.kind
        if k == "viaduct":
            self.ground(y=-90)
            self.box("Deck", -1500, 3200, -6, -0.8, -9, 9, "@style.world.ironwork", "structure")
            for s in (-1, 1):
                self.box(f"Parapet{s}", -1500, 3200, -0.8, 2.6, s * 9 - 0.8, s * 9 + 0.8, "@style.ground.ballast", "structure")
            x = -1500
            while x < 3200:
                self.box(f"Pier{x}", x - 4, x + 4, -90, -6, -7, 7, "@style.ground.ballast", "structure")
                x += 64
            self.track()
            for i in range(40):
                x = self.rnd.uniform(-900, 2600)
                z = self.rnd.choice([-1, 1]) * self.rnd.uniform(60, 700)
                self.box(f"ValleyTree{i}", x - 8, x + 8, -90, -90 + self.rnd.uniform(15, 30), z - 8, z + 8, "@style.ground.hedgerow", "scenery")
        else:
            self.ground()
            self.track()
            if k in ("grassland", "yard", "cutting"):
                self.lineside()
        if k == "yard":
            for zt in (-20, 20, -38, 38):
                self.track(z=zt, tag=f"Y{zt}")
            for i in range(10):
                zt = self.rnd.choice([-20, 20, -38, 38])
                x = self.rnd.uniform(-400, 900)
                self.box(f"Wagon{i}", x, x + 30, 1, 11, zt - 4.5, zt + 4.5,
                         self.rnd.choice(["@style.world.ironwork", "@style.world.walnut", "@style.world.diamond_plate"]), "structure")
            self.box("Shed", -200, 120, -0.8, 34, -110, -70, "@style.world.ironwork", "structure")
            self.box("ShedRoof", -205, 125, 34, 38, -114, -66, "@style.world.soot_black", "structure")
        if k == "cutting":
            for s in (-1, 1):
                for i, (a, b, h) in enumerate(((16, 24, 12), (24, 32, 24), (32, 44, 38))):
                    ref = "@style.ground.bare_earth" if i < 2 else "@style.ground.cinder_verge"
                    self.box(f"Cut{s}_{i}", -900, 300, -0.8, h, min(s * a, s * b), max(s * a, s * b), ref, "structure")
                    self.box(f"CutTop{s}_{i}", -900, 300, h, h + 0.6, min(s * a, s * b), max(s * a, s * b), "@style.ground.hedgerow", "structure")
            bw, bh = self.c.bore_w, self.c.bore_h
            self.box("PortalL", 300, 320, -0.8, 44, -44, -bw / 2, "@style.ground.ballast", "structure")
            self.box("PortalR", 300, 320, -0.8, 44, bw / 2, 44, "@style.ground.ballast", "structure")
            self.box("PortalHead", 300, 320, bh, 44, -bw / 2, bw / 2, "@style.ground.ballast", "structure")
            self.box("TunnelIn", 320, 900, bh, bh + 3, -bw / 2 - 3, bw / 2 + 3, "@style.world.soot_black", "structure")
        if k == "tunnel":   # the camera is inside: shell around the train, open portals at both ends
            bw, bh = self.c.bore_w, self.c.bore_h
            self.box("TunnelL", -300, 700, -0.8, bh, -bw / 2 - 3, -bw / 2, "@style.ground.ballast", "structure")
            self.box("TunnelR", -300, 700, -0.8, bh, bw / 2, bw / 2 + 3, "@style.ground.ballast", "structure")
            self.box("TunnelRoof", -300, 700, bh, bh + 3, -bw / 2 - 3, bw / 2 + 3, "@style.ground.ballast", "structure")
            for x in range(-280, 700, 40):   # refuge niches: something to read in the dark
                self.box(f"Niche{x}", x, x + 4, 0, 7, bw / 2 - 0.3, bw / 2 - 0.05, "@style.world.soot_black", "structure")
        return self


# ------------------------------------------------------------------ lighting
def sun_direction(clock, lat, east_axis):
    """Unit vector toward the sun in Roblox axes, equinox declination 0 (fidelity.md)."""
    h = math.radians((clock - 12) * 15)
    phi = math.radians(lat)
    e, n, up = -math.sin(h), -math.sin(phi) * math.cos(h), math.cos(phi) * math.cos(h)  # (east, north, up)
    axes = {"+X": (1, 0, 0), "-X": (-1, 0, 0), "+Z": (0, 0, 1), "-Z": (0, 0, -1)}
    E = axes.get(east_axis, (0, 0, 1))
    U = (0, 1, 0)
    N = (U[1] * E[2] - U[2] * E[1], U[2] * E[0] - U[0] * E[2], U[0] * E[1] - U[1] * E[0])  # N = Up x E
    v = [e * E[i] + n * N[i] + up * U[i] for i in range(3)]
    ln = math.sqrt(sum(x * x for x in v)) or 1
    return [x / ln for x in v]


def sun_colour(elev):
    """Sun tint by elevation: white overhead, warm near the horizon (Roblox shifts it too; approximated)."""
    t = max(0.0, min(1.0, (math.degrees(elev) - 2) / 28))
    warm = (1.0, 0.62, 0.36)
    return [warm[i] + (1 - warm[i]) * t for i in range(3)]


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


class Look:
    def __init__(self, model, name, east_axis):
        self.name = name
        cam = "roof3p"
        if "@" in name:
            name, cam = name.split("@", 1)
        self.look = model.resolve_look(name)
        if cam not in CAMERAS:
            raise KeyError(f"unknown camera {cam!r} in {self.name!r}; cameras: {', '.join(CAMERAS)}")
        self.camera = cam
        C = self.look["classes"]
        Lt = C.get("Lighting", {})
        g = lambda cls, p, d: C.get(cls, {}).get(p, ("num", d))[1] if C.get(cls, {}).get(p, ("num", d))[0] == "num" else d
        self.g, self.C = g, C
        self.clock, self.lat = g("Lighting", "ClockTime", 14), g("Lighting", "GeographicLatitude", 41.7)
        self.brightness, self.ec = g("Lighting", "Brightness", 2), g("Lighting", "ExposureCompensation", 0)
        self.sun_dir = sun_direction(self.clock, self.lat, east_axis)
        self.elev = math.asin(max(-1, min(1, self.sun_dir[1])))
        self.day = smoothstep(-0.05, 0.35, math.sin(self.elev))
        self.scene = "tunnel" if "tunnel_under" in self.look["overrides"] else self.look["scene"]
        self.slug = self.name.replace("+", "_").replace("@", "_")


def apply_lighting(scn, lk, phone=False, headlamp_lamp=None, model=None):
    """Sun or moon, ColorShift_Bottom fill, world ambient, Ambient emission, headlamp spot."""
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    C, g = lk.C, lk.g
    Lt = C.get("Lighting", {})
    moon = lk.elev < math.radians(-2)
    d = [-x for x in lk.sun_dir] if moon else lk.sun_dir
    col = [0.72, 0.8, 1.0] if moon else sun_colour(lk.elev)
    cst = tv_lin(Lt.get("ColorShift_Top"))
    col = [col[i] + cst[i] * CST_K for i in range(3)]
    mx = max(col)
    strength = lk.brightness * (MOON_K if moon else SUN_K) * max(0.0, math.sin(max(0.02, math.asin(d[1])))) ** 0.25 * mx
    soft = g("Lighting", "ShadowSoftness", 0.2)

    def lamp(name, direction, colour, energy, shadow):
        L = bpy.data.lights.new(name, "SUN")
        L.color = colour
        L.energy = energy
        L.angle = math.radians(0.5 + 12 * soft)
        L.use_shadow = shadow and not phone
        ob = bpy.data.objects.new(name, L)
        bpy.context.scene.collection.objects.link(ob)
        ob.rotation_euler = Vector(B([-x for x in direction])).to_track_quat("-Z", "Y").to_euler()
        return ob

    lamp("Key", d, [c / mx for c in col], strength, Lt.get("GlobalShadows", ("bool", True))[1])
    csb = tv_lin(Lt.get("ColorShift_Bottom"))
    if max(csb) > 0:
        lamp("Fill", [-x for x in d], [c / max(csb) for c in csb], lk.brightness * max(csb) * CST_K, False)
    # world: OutdoorAmbient + sky x EnvironmentDiffuseScale (lighting only; sky pixels are drawn in post)
    oa = tv_lin(Lt.get("OutdoorAmbient"))
    sky = sky_colours(lk)[0]
    env = g("Lighting", "EnvironmentDiffuseScale", 0)
    amb_world = [oa[i] * OA_K + srgb_lin(sky[i]) * env * ENV_K * (0.25 + 0.75 * lk.day) for i in range(3)]
    w = bpy.context.scene.world
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (*amb_world, 1)
    bg.inputs[1].default_value = 1.0
    amb = tv_lin(Lt.get("Ambient"))
    for m in bpy.data.materials:
        if "base_lin" not in m:
            continue
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        base = list(m["base_lin"])
        e = [base[i] * amb[i] * AMB_K for i in range(3)]
        se = m["self_emit"]
        if se:
            e = [base[i] * se for i in range(3)]
        bsdf.inputs["Emission Color"].default_value = (*e, 1)
        bsdf.inputs["Emission Strength"].default_value = 1.0
    scn.cab_lights(phone)
    if headlamp_lamp is not None:
        on = "headlamp" in lk.look["fx_on"]
        lens = headlamp_lamp.data.materials[0]
        lens.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 4.0 if on else 0.0
        if on and model and "headlamp" in model.presets:
            for Lr in model.presets["headlamp"]["layers"]:
                if Lr["class"] != "SpotLight":
                    continue
                pr = Lr["props"]
                anchor = model.anchors.get(model.presets["headlamp"]["anchor"], [67.5, 9, 0])
                S = bpy.data.lights.new("Headlamp", "SPOT")
                S.color = hex_lin(pr["Color"][1])
                S.energy = pr["Brightness"][1] * LIGHT_K * pr["Range"][1] ** 2
                S.spot_size = math.radians(pr.get("Angle", ("num", 45))[1])
                S.spot_blend = 0.35
                S.use_shadow = pr.get("Shadows", ("bool", False))[1] and not phone
                ob = bpy.data.objects.new("Headlamp", S)
                bpy.context.scene.collection.objects.link(ob)
                ob.location = B(vfx_add(anchor, Lr["offset"]))
                ob.rotation_euler = Vector(B(Lr.get("dir", [1, 0, 0]))).to_track_quat("-Z", "Y").to_euler()


def vfx_add(a, b):
    return [a[i] + b[i] for i in range(3)]


def sky_colours(lk):
    """(horizon, zenith) display sRGB 0..1: the horizon is Atmosphere.Color; the zenith blends Roblox's default
    blue toward Decay by density and haze (the skybox itself is not modelled)."""
    A = lk.C.get("Atmosphere", {})
    col = tv_srgb(A["Color"]) if "Color" in A else [0.75, 0.8, 0.85]
    dec = tv_srgb(A["Decay"]) if "Decay" in A else col
    dens = lk.g("Atmosphere", "Density", 0)
    haze = lk.g("Atmosphere", "Haze", 0)
    w = max(0.0, min(1.0, dens * 1.6 + haze * 0.12))
    zen = [DEFAULT_SKY[i] + (dec[i] - DEFAULT_SKY[i]) * w for i in range(3)]
    light = 0.6 + 0.4 * lk.day
    if lk.elev < 0:   # night sky: the authored colours carry it; the default blue drops out
        zen = dec
    return [c * light for c in col], [c * light for c in zen]


# ------------------------------------------------------------------ rendering and passes
def setup_render(res, samples, quick):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    try:
        sc.cycles.use_denoising = True
    except (AttributeError, TypeError):
        pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "32"
    sc.cycles.max_bounces = 3 if quick else 6
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("World")


# name -> (stand point, look-at point, eye height above the stand) from the canon stand dims
CAMERAS = {
    "roof3p": lambda c: ((-70, c.roof, 0), (160, 4, 110), c.eye_3p),                      # on coach B's roof
    "door1p": lambda c: ((-20, c.floor, c.half_w + 1.2), (160, 2, c.half_w + 16), c.eye_1p),  # leaning out of A's door,
                                                                                               # looking along the train
    "cab1p": lambda c: ((29, 0, -1.5), (36, 6.5, 0.3), c.cab_eye),                         # loco cab, facing the firebox
    "coach1p": lambda c: ((-26, c.floor, -2), (8, c.floor + 3, c.half_w - 1), c.eye_1p),  # inside A, power box end
}


def camera(canon, name):
    if name not in CAMERAS:
        raise KeyError(f"unknown camera {name!r}; cameras: {', '.join(CAMERAS)}")
    stand, look, eye = CAMERAS[name](canon)
    e = [stand[0], stand[1] + eye, stand[2]]
    cam = bpy.data.objects.get("Cam")
    if cam is None:
        cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
        bpy.context.scene.collection.objects.link(cam)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle_y = math.radians(canon.fov)
    cam.data.clip_start, cam.data.clip_end = 0.1, 20000
    cam.location = B(e)
    fwd = [look[i] - e[i] for i in range(3)]
    ln = math.sqrt(sum(x * x for x in fwd))
    fwd = [x / ln for x in fwd]
    cam.rotation_euler = Vector(B(fwd)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    up0 = [0, 1, 0]
    right = [fwd[1] * up0[2] - fwd[2] * up0[1], fwd[2] * up0[0] - fwd[0] * up0[2], fwd[0] * up0[1] - fwd[1] * up0[0]]
    rl = math.sqrt(sum(x * x for x in right))
    right = [x / rl for x in right]
    up = [right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2], right[0] * fwd[1] - right[1] * fwd[0]]
    return {"camera": name, "eye": e, "forward": fwd, "right": right, "up": up, "fov_v": canon.fov, "stand": list(stand),
            "look_at": list(look), "eye_height": eye}


def render_exr(path, samples=None, data=False):
    sc = bpy.context.scene
    vl = sc.view_layers[0]
    keep = (sc.cycles.samples, sc.cycles.filter_width, getattr(sc.cycles, "use_denoising", False))
    if data:
        mat = bpy.data.materials.get("RR_Data") or data_material()
        vl.material_override = mat
        sc.cycles.samples, sc.cycles.filter_width = 1, 0.01
        try:
            sc.cycles.use_denoising = False
        except (AttributeError, TypeError):
            pass
        w = sc.world.node_tree.nodes.get("Background")
        wk = tuple(w.inputs[0].default_value)
        w.inputs[0].default_value = (0, 0, 0, 1)
    sc.render.filepath = path
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        if data:
            vl.material_override = None
            w.inputs[0].default_value = wk
            sc.cycles.samples, sc.cycles.filter_width = keep[0], keep[1]
            try:
                sc.cycles.use_denoising = keep[2]
            except (AttributeError, TypeError):
                pass
    img = bpy.data.images.load(path)
    W, H = img.size
    a = np.empty(W * H * 4, np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(H, W, 4)[::-1, :, :3].copy()


def data_material():
    """Emission = (object class / 8, camera distance / 4096, 0) for the data pass."""
    m = bpy.data.materials.new("RR_Data")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    info = nt.nodes.new("ShaderNodeObjectInfo")
    camd = nt.nodes.new("ShaderNodeCameraData")
    div1 = nt.nodes.new("ShaderNodeMath")
    div1.operation, div1.inputs[1].default_value = "DIVIDE", 8.0
    div2 = nt.nodes.new("ShaderNodeMath")
    div2.operation, div2.inputs[1].default_value = "DIVIDE", 4096.0
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(info.outputs["Object Index"], div1.inputs[0])
    nt.links.new(camd.outputs["View Distance"], div2.inputs[0])
    nt.links.new(div1.outputs[0], comb.inputs[0])
    nt.links.new(div2.outputs[0], comb.inputs[1])
    nt.links.new(comb.outputs[0], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


# ------------------------------------------------------------------ post (numpy)
def blur(img, r):
    """Separable box blur x3 (close to Gaussian), r in px."""
    r = max(1, int(r))
    out = img
    for _ in range(3):
        for axis in (0, 1):
            c = np.cumsum(np.pad(out, [(r + 1, r) if a == axis else (0, 0) for a in range(out.ndim)], mode="edge"), axis=axis)
            hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
            lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
            out = (hi - lo) / (2 * r + 1)
    return out


def aces(x):
    return np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0, 1)


def lin_to_srgb(x):
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(np.clip(x, 0, None), 1 / 2.4) - 0.055)


def post(lk, beauty, data, view, phone=False):
    H, W, _ = beauty.shape
    cls = np.rint(data[:, :, 0] * 8).astype(int)
    dist = data[:, :, 1] * 4096
    sky = cls == 0
    C, g = lk.C, lk.g
    hdr = beauty * (2 ** lk.ec) * EXPO_K
    bloom_on = C.get("BloomEffect", {}).get("Enabled", ("bool", True))[1] and not phone
    if bloom_on and g("BloomEffect", "Intensity", 0) > 0:
        lum = hdr @ np.array([0.2126, 0.7152, 0.0722])
        thr = g("BloomEffect", "Threshold", 1.0)
        bright = hdr * (np.clip(lum - thr * 0.5, 0, None) / np.maximum(lum, 1e-6))[:, :, None]
        hdr = hdr + blur(bright, g("BloomEffect", "Size", 24) * H / 1080 + 1) * g("BloomEffect", "Intensity", 0)
    disp = lin_to_srgb(aces(hdr))
    # sky: gradient by ray elevation, horizon = Atmosphere.Color, zenith toward Decay
    hor, zen = (np.array(c) for c in sky_colours(lk))
    ys = (np.arange(H) - H / 2)[:, None]
    xs = (np.arange(W) - W / 2)[None, :]
    fp = (H / 2) / math.tan(math.radians(view["fov_v"]) / 2)
    fwd, up, right = (np.array(view[k]) for k in ("forward", "up", "right"))
    rays = fwd[None, None, :] * fp + right[None, None, :] * xs[:, :, None] - up[None, None, :] * ys[:, :, None]
    rays /= np.linalg.norm(rays, axis=2, keepdims=True)
    el = np.clip(rays[:, :, 1], 0, 1)
    t = np.power(el, 0.55)[:, :, None]
    skyc = hor[None, None, :] * (1 - t) + zen[None, None, :] * t
    sd = np.array([-x for x in lk.sun_dir]) if lk.elev < math.radians(-2) else np.array(lk.sun_dir)
    cosang = np.clip(rays @ sd, -1, 1)
    glare = g("Atmosphere", "Glare", 0)
    if glare > 0 and lk.elev > 0:
        skyc = skyc + (np.exp((cosang - 1) * 40) * glare * 0.08)[:, :, None]
    disp = np.where(sky[:, :, None], skyc, disp)
    # fog on geometry: optical depth from Atmosphere Density and Haze; brightness follows daylight
    A = C.get("Atmosphere", {})
    dens, haze = g("Atmosphere", "Density", 0), g("Atmosphere", "Haze", 0)
    fogc = np.array(tv_srgb(A["Color"]) if "Color" in A else [0.8, 0.8, 0.8]) * (0.6 + 0.4 * lk.day)
    f = 1 - np.exp(-(FOG_K * dens * dist + HAZE_K * haze * dist * dens))
    f = np.where(sky, 0, f)[:, :, None]
    disp = disp * (1 - f) + fogc[None, None, :] * f
    # sun rays: radial blur of bright sky toward the sun's screen position
    sr_on = C.get("SunRaysEffect", {}).get("Enabled", ("bool", True))[1] and not phone
    sri = g("SunRaysEffect", "Intensity", 0)
    rel = [float(np.dot(sd, fwd)), float(np.dot(sd, right)), float(np.dot(sd, up))]
    if sr_on and sri > 0 and lk.elev > 0 and rel[0] > 0.1:
        sx, sy = W / 2 + rel[1] / rel[0] * fp, H / 2 - rel[2] / rel[0] * fp
        src = np.where(sky[:, :, None], disp, 0) * np.clip((cosang[:, :, None] + 1) / 2, 0, 1) ** 8
        acc = np.zeros_like(disp)
        spread = g("SunRaysEffect", "Spread", 0.5)
        n = 24
        yy, xx = np.mgrid[0:H, 0:W]
        for i in range(n):
            s = 1 - spread * 0.6 * i / n
            px = np.clip((sx + (xx - sx) * s).astype(int), 0, W - 1)
            py = np.clip((sy + (yy - sy) * s).astype(int), 0, H - 1)
            acc += src[py, px]
        disp = disp + acc / n * sri * 4
    # ColorCorrection (display space)
    cc = C.get("ColorCorrectionEffect", {})
    if cc.get("Enabled", ("bool", True))[1]:
        disp = disp + g("ColorCorrectionEffect", "Brightness", 0)
        disp = (disp - 0.5) * (1 + g("ColorCorrectionEffect", "Contrast", 0)) + 0.5
        lum = (disp @ np.array([0.2126, 0.7152, 0.0722]))[:, :, None]
        disp = lum + (disp - lum) * (1 + g("ColorCorrectionEffect", "Saturation", 0))
        if "TintColor" in cc:
            disp = disp * np.array(tv_srgb(cc["TintColor"]))[None, None, :]
    disp = np.clip(disp, 0, 1)
    return disp, cls, dist, float(f.max() if f.size else 0), fogc


def hexof(rgb01):
    return "#%02X%02X%02X" % tuple(int(round(max(0, min(1, c)) * 255)) for c in rgb01)


def rel_lum(rgb01):
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb01]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def hsl_sat(rgb01):
    mx, mn = max(rgb01), min(rgb01)
    l = (mx + mn) / 2
    if mx == mn:
        return 0.0
    d = mx - mn
    return d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)


def measure(lk, disp, cls, dist, canon, model):
    def mean_of(mask):
        return disp[mask].mean(axis=0).tolist() if mask.any() else None
    train = (cls == 3) | (cls == 4) | (cls == 7)
    around = (cls == 1) | (cls == 5) | (cls == 6) | (cls == 2)
    hz = cls == 7
    ground = cls == 1
    skym = cls == 0
    t_rgb, a_rgb, g_rgb, s_rgb = mean_of(train), mean_of(around), mean_of(ground), mean_of(skym)
    frame = disp.reshape(-1, 3).mean(axis=0).tolist()
    contrast = None
    if t_rgb and a_rgb:
        l1, l2 = rel_lum(t_rgb), rel_lum(a_rgb)
        contrast = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
    dens, haze = lk.g("Atmosphere", "Density", 0), lk.g("Atmosphere", "Haze", 0)
    spawn = canon.ahead * canon.segment
    spawn_fog = 1 - math.exp(-(FOG_K * dens * spawn + HAZE_K * haze * spawn * dens))
    lum8 = disp @ np.array([0.2126, 0.7152, 0.0722]) * 255
    out = {
        "look": lk.name, "camera": lk.camera, "scene": lk.scene,
        "sun": {"clock": lk.clock, "elevation_deg": round(math.degrees(lk.elev), 1),
                "dir_roblox": [round(x, 3) for x in lk.sun_dir], "moon": lk.elev < math.radians(-2)},
        "mean_luma": round(float(lum8.mean()), 1),
        "clipped_pct": round(float((disp.max(axis=2) >= 0.98).mean() * 100), 2),
        "crushed_pct": round(float((disp.max(axis=2) <= 0.03).mean() * 100), 2),
        "frame_mean": hexof(frame),
        "sky_mean": hexof(s_rgb) if s_rgb else None,
        "ground_mean": hexof(g_rgb) if g_rgb else None,
        "ground_sat_hsl": round(hsl_sat(g_rgb), 2) if g_rgb else None,
        "train_mean": hexof(t_rgb) if t_rgb else None,
        "train_vs_world_contrast": round(contrast, 2) if contrast else None,
        "crushed_train_pct": round(float((disp[train].max(axis=1) <= 0.03).mean() * 100), 2) if train.any() else None,
        "hazard_vs_world": (lambda h: round((max(rel_lum(h), rel_lum(a_rgb)) + 0.05) / (min(rel_lum(h), rel_lum(a_rgb)) + 0.05), 2)
                            if h and a_rgb else None)(mean_of(hz)),
        "hazard_mean": hexof(mean_of(hz)) if hz.any() else None,
        "spawn_edge_fog": round(spawn_fog, 3), "spawn_edge_studs": spawn,
        "fx_on": lk.look["fx_on"],
    }
    bands = []
    if model.bible.ok():
        hexes = [out["frame_mean"]] + ([out["sky_mean"]] if out["sky_mean"] else [])
        for where, msg in vfx.band_check(model, hexes, {out["frame_mean"]: "frame mean", out.get("sky_mean") or "": "sky mean"}):
            bands.append(f"{where}: {msg}")
    out["bands"] = bands
    return out


def save_png(disp, path):
    from PIL import Image
    Image.fromarray((np.clip(disp, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def save_depth(dist, cls, path):
    from PIL import Image
    d = np.where(cls == 0, 0, np.clip(dist * 16, 0, 65535)).astype(np.uint16)
    Image.fromarray(d).save(path)


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--looks", required=True, help=f"comma-separated biome.time[+override][@{'|'.join(CAMERAS)}]")
    ap.add_argument("--out", required=True)
    ap.add_argument("--phone", default="", help="comma-separated looks (as named in --looks) to also render as the phone "
                    "fallback at tech.ui_platform.phone resolution")
    ap.add_argument("--res", default="768x432")
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--quick", action="store_true", help="192x108, 4 samples: smoke test only")
    ap.add_argument("--presets", help="preset folder (default $RR_VFX_PRESETS, else the shipped library)")
    a = ap.parse_args(argv)
    if bpy is None:
        print("lookdev_bpy needs bpy (pip bpy, Blender 4.x/5.x) and numpy; no lighting preview possible here", file=sys.stderr)
        return 3
    vfx.PRESETS_ARG = a.presets
    model = vfx.Model()
    canon = Canon(model)
    east = model.light_raw.get("preview", {}).get("east_axis", "+Z")
    res = (192, 108) if a.quick else tuple(int(v) for v in a.res.lower().split("x"))
    res_phone = (res[0] * canon.phone_res[0] // 768 // 2 * 2, res[0] * canon.phone_res[1] // 768 // 2 * 2) if a.quick else canon.phone_res
    samples = 4 if a.quick else a.samples
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    names = [n.strip() for n in a.looks.split(",") if n.strip()]
    phone = {n.strip() for n in a.phone.split(",") if n.strip()}
    looks = []
    for n in names:
        try:
            looks.append(Look(model, n, east))
        except KeyError as e:
            print(f"skip {n}: {e}", file=sys.stderr)
            return 2
    by_scene = {}
    for lk in looks:
        by_scene.setdefault(lk.scene, []).append(lk)
    results = []
    tmp = tempfile.mkdtemp(prefix="rr_lookdev_")
    for scene_kind, group in by_scene.items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        setup_render(res, samples, a.quick)
        scn = Scene(model, canon, scene_kind).build()
        lamp = scn.train(headlamp=False)
        data_cache = {}
        for lk in group:
            for ph in ([False, True] if lk.name in phone else [False]):
                r = res_phone if ph else res
                sc = bpy.context.scene
                sc.render.resolution_x, sc.render.resolution_y = r
                view = camera(canon, lk.camera)
                view["res"] = list(r)
                key = (lk.camera, r)
                if key not in data_cache:
                    data_cache[key] = render_exr(os.path.join(tmp, f"data_{scene_kind}_{lk.camera}_{r[0]}.exr"), data=True)
                data = data_cache[key]
                apply_lighting(scn, lk, phone=ph, headlamp_lamp=lamp, model=model)
                beauty = render_exr(os.path.join(tmp, f"b_{lk.slug}_{int(ph)}.exr"))
                disp, cls, dist, _, fogc = post(lk, beauty, data, view, phone=ph)
                sfx = ".phone" if ph else ""
                png = out / f"{lk.slug}{sfx}.png"
                save_png(disp, png)
                facts = measure(lk, disp, cls, dist, canon, model)
                facts["phone"] = ph
                facts["png"] = png.name
                facts["res"] = list(r)
                save_depth(dist, cls, out / f"{lk.slug}{sfx}.depth.png")
                pl = [max(0.15, min(1.6, (lk.brightness / 2.4) * (0.2 + 0.8 * lk.day) * (2 ** lk.ec)))] * 3
                vj = {**view, "look": lk.name, "plate": png.name, "depth": f"{lk.slug}{sfx}.depth.png", "depth_scale": 16,
                      "particle_light": [round(x, 3) for x in pl], "phone": ph,
                      "fog": {"k": FOG_K * lk.g("Atmosphere", "Density", 0), "colour": [int(c * 255) for c in fogc]}}
                (out / f"view_{lk.slug}{sfx}.json").write_text(json.dumps(vj, indent=1))
                (out / f"{lk.slug}{sfx}.facts.json").write_text(json.dumps(facts, indent=1))
                results.append(facts)
                print(json.dumps({"png": str(png), "contrast": facts["train_vs_world_contrast"], "luma": facts["mean_luma"],
                                  "spawn_fog": facts["spawn_edge_fog"], "bands": facts["bands"]}))
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)   # EXR passes
    (out / "canon_used.json").write_text(json.dumps({"keys": canon.used, "eye_3p": canon.eye_3p, "eye_1p": canon.eye_1p,
                                                     "cab_eye": canon.cab_eye, "fov": canon.fov, "phone_res": list(canon.phone_res),
                                                     "stand": model.dims, "cameras": list(CAMERAS),
                                                     "calibration": {k: v for k, v in globals().items()
                                                                     if k.endswith("_K") and isinstance(v, float)}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
