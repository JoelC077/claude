#!/usr/bin/env python3
"""rr-vfx-lighting: Roblox effect and lighting presets as data.

  vfx.py init DIR                               copy the shipped presets to a work folder (edit that, never the skill)
  vfx.py list                                   presets, trails, looks, budget sets
  vfx.py show NAME [--json]                     one effect preset, trail, or look (biome.time[+override])
  vfx.py validate [--strict]                    schema, Roblox ranges, canon refs, colour gate, OQ refs, budgets
  vfx.py budget [SET ...] [--tier phone|pc|all] concurrency sets vs tier budgets (exit 1 when over)
  vfx.py preview lighting|vfx|all [NAMES] --out DIR [--quick] [--gif]
                                                renders + POVs + one board (OUT/board) + facts.md; NAMES = looks
                                                and/or effect presets (a pack); none = the default preview sets
  vfx.py crit CRIT --pass N --from DIR          CRIT/rubric.md (+ Profile F), pass files, brief from the previewed names
  vfx.py build --out DIR [--only NAMES] [--no-check]
                                                generated Luau data + runtime modules + Studio setup, then gates

Every command takes --presets DIR (the work copy; else $RR_VFX_PRESETS; else the shipped library, read-only)
and prints which folder it used. Canon comes from the rr-bible skill (found by glob or $RR_BIBLE_SKILL); the
critic scripts from multiuse-critic ($RR_CRITIC_SKILL). Standard library only; preview needs Pillow, lighting
preview needs bpy (see lookdev_bpy.py --help).
"""
import sys
sys.dont_write_bytecode = True  # never leave __pycache__ inside the skill
if __name__ == "__main__":
    sys.modules["vfx"] = sys.modules[__name__]   # preview.py / fxsim.py `import vfx` must see this run's --presets
import argparse, copy, datetime as _dt, json, math, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
TODAY = _dt.date.today().isoformat()
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
NEUTRALS = {"#FFFFFF", "#000000"}
LIGHT_CLASSES = ("PointLight", "SpotLight", "SurfaceLight")


PRESETS_ARG = None   # set by --presets


def presets_dir():
    return Path(PRESETS_ARG or os.environ.get("RR_VFX_PRESETS") or SKILL / "presets").resolve()


def shipped():
    return presets_dir() == (SKILL / "presets").resolve()


# preview test stand: rolling-stock envelope from canon (OQ-030 proposed); anchors and offsets may use these names
STAND_CANON = {"gauge": ("tech.units.gauge", 8.0), "width": ("tech.units.stock_width", 17.4),
               "roof": ("tech.units.stock_roof", 14.0), "floor": ("tech.units.stock_floor", 5.0)}
EXPR_RE = re.compile(r"^[\sa-z0-9_.+\-*/()]+$")


def stand_dims(bible):
    return {k: (bible.number(key, d) if bible.ok() else d) or d for k, (key, d) in STAND_CANON.items()}


def vec_eval(v, dims, where, issues):
    """[x, y, z] where a component may be an expression over the stand names ("gauge/2", "width/2+0.1")."""
    out = []
    for c in v:
        if _num(c):
            out.append(float(c))
        elif isinstance(c, str) and EXPR_RE.match(c):
            try:
                out.append(float(eval(c, {"__builtins__": {}}, dict(dims))))  # noqa: S307 (regex-limited arithmetic)
            except Exception as e:  # noqa: BLE001
                issues.err(where, f"bad expression {c!r}: {e} (names: {', '.join(dims)})")
                return None
        else:
            issues.err(where, f"3 numbers or stand expressions expected, got {c!r}")
            return None
    return out


# ------------------------------------------------------------------ siblings
def _walk_find(root, name, maxdepth=5):
    root = Path(root)
    if not root.is_dir():
        return []
    out, base = [], len(root.parts)
    for d, dirs, files in os.walk(root):
        p = Path(d)
        if len(p.parts) - base >= maxdepth:
            dirs[:] = []
        dirs[:] = [x for x in dirs if not x.startswith(".") and x not in ("node_modules", "__pycache__")]
        if p.name == name and "SKILL.md" in files:
            out.append(p)
    return out


def find_sibling(name, env):
    """Env var, then a sibling folder of this skill, then ~/.claude/skills and /home/user (depth 5)."""
    if os.environ.get(env):
        p = Path(os.environ[env])
        return p if (p / "SKILL.md").is_file() else None
    cands = [SKILL.parent / name] + _walk_find(Path.home() / ".claude" / "skills", name) + _walk_find("/home/user", name)
    return next((c for c in cands if (c / "SKILL.md").is_file()), None)


class Bible:
    """Reads canon through rr-bible's CLI (its stable interface), one call per domain file, cached."""

    def __init__(self):
        self.dir = find_sibling("rr-bible", "RR_BIBLE_SKILL")
        self.script = self.dir / "scripts" / "bible.py" if self.dir else None
        self._files, self._oq = {}, {}

    def ok(self):
        return bool(self.script and self.script.is_file())

    def run(self, *args):
        if not self.ok():
            return 2, "rr-bible not found: set RR_BIBLE_SKILL to its folder"
        r = subprocess.run([sys.executable, str(self.script), *args], capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def facts(self, stem):
        if stem not in self._files:
            code, out = self.run("get", stem, "--json")
            try:
                self._files[stem] = {f["key"]: f for f in json.loads(out)} if code == 0 else {}
            except ValueError:
                self._files[stem] = {}
        return self._files[stem]

    def fact(self, key):
        return self.facts(key.split(".")[0]).get(key)

    def value(self, key, default=None):
        f = self.fact(key)
        return f["value"] if f else default

    def number(self, key, default=None):
        v = self.value(key)
        m = re.search(r"-?\d+(?:\.\d+)?", v or "")
        return float(m.group(0)) if m else default

    def oq(self, oid):
        if oid not in self._oq:
            code, out = self.run("get", oid, "--json")
            try:
                d = json.loads(out) if code == 0 else None
            except ValueError:
                d = None
            self._oq[oid] = d[0] if isinstance(d, list) and d else d
        return self._oq[oid]

    def check(self, path, allow=(), skip=None):
        args = ["check", str(path), "--json"] + (["--allow", ",".join(allow)] if allow else []) + (["--skip", skip] if skip else [])
        code, out = self.run(*args)
        try:
            return code, json.loads(out[out.index("{"):])
        except ValueError:
            return code, {"errors": 1, "warnings": 0, "findings": [{"level": "ERROR", "kind": "run", "line": 0, "msg": out.strip()[:300]}]}


# ------------------------------------------------------------------ schema
# (type, lo, hi, hard) ; enum: ("enum", EnumType, [names]); ranges "hard" come from the docs (RBXD) or engine errors
ORIENT = ["FacingCamera", "FacingCameraWorldUp", "VelocityParallel", "VelocityPerpendicular"]
NORMAL = ["Top", "Bottom", "Front", "Back", "Left", "Right"]
_COMMON_FX = {"Color": ("cseq",), "Transparency": ("nseq", 0, 1, True), "LightEmission": ("num", 0, 1, True),
              "LightInfluence": ("num", 0, 1, True), "Brightness": ("num", 0, None, False), "Texture": ("str",),
              "Enabled": ("bool",), "ZOffset": ("num", None, None, False),
              "TextureLength": ("num", 0, None, False), "TextureMode": ("enum", "TextureMode", ["Stretch", "Wrap", "Static"])}
_LIGHT = {"Brightness": ("num", 0, None, False), "Range": ("num", 0, 120, True), "Color": ("color",),
          "Shadows": ("bool",), "Enabled": ("bool",)}
SCHEMA = {
    "ParticleEmitter": {**_COMMON_FX, "Rate": ("num", 0, None, False), "Lifetime": ("range", 0, None, False),
                        "Speed": ("range", None, None, False), "SpreadAngle": ("v2", -360, 360, False),
                        "Acceleration": ("v3",), "Drag": ("num", 0, None, False), "WindAffectsDrag": ("bool",),
                        "Size": ("nseq", 0, None, True), "Squash": ("nseq", -3, 3, False),
                        "Rotation": ("range", None, None, False), "RotSpeed": ("range", None, None, False),
                        "Orientation": ("enum", "ParticleOrientation", ORIENT), "TimeScale": ("num", 0, 1, True),
                        "VelocityInheritance": ("num", 0, 1, True), "LockedToPart": ("bool",),
                        "EmissionDirection": ("enum", "NormalId", NORMAL),
                        "Shape": ("enum", "ParticleEmitterShape", ["Box", "Sphere", "Cylinder", "Disc"]),
                        "ShapeStyle": ("enum", "ParticleEmitterShapeStyle", ["Volume", "Surface"]),
                        "ShapeInOut": ("enum", "ParticleEmitterShapeInOut", ["Outward", "Inward", "InAndOut"]),
                        "ShapePartial": ("num", 0, 1, True)},
    "Beam": {**_COMMON_FX, "Width0": ("num", 0, None, True), "Width1": ("num", 0, None, True),
             "Segments": ("num", 1, 1000, True), "FaceCamera": ("bool",), "CurveSize0": ("num", None, None, False),
             "CurveSize1": ("num", None, None, False), "TextureSpeed": ("num", None, None, False)},
    "Trail": {**_COMMON_FX, "Lifetime": ("num", 0, 20, False), "MinLength": ("num", 0, None, True),
              "MaxLength": ("num", 0, None, True), "WidthScale": ("nseq", 0, None, True), "FaceCamera": ("bool",)},
    "PointLight": dict(_LIGHT),
    "SpotLight": {**_LIGHT, "Angle": ("num", 0, 180, True), "Face": ("enum", "NormalId", NORMAL)},
    "SurfaceLight": {**_LIGHT, "Angle": ("num", 0, 180, True), "Face": ("enum", "NormalId", NORMAL)},
    "Lighting": {"ClockTime": ("num", 0, 24, True), "GeographicLatitude": ("num", -90, 90, True),
                 "Brightness": ("num", 0, 10, False), "ExposureCompensation": ("num", -5, 5, True),
                 "OutdoorAmbient": ("light",), "Ambient": ("light",), "ColorShift_Top": ("light",),
                 "ColorShift_Bottom": ("light",), "EnvironmentDiffuseScale": ("num", 0, 1, True),
                 "EnvironmentSpecularScale": ("num", 0, 1, True), "ShadowSoftness": ("num", 0, 1, True),
                 "GlobalShadows": ("bool",)},
    "Atmosphere": {"Density": ("num", 0, 1, True), "Offset": ("num", 0, 1, True), "Color": ("color",),
                   "Decay": ("color",), "Glare": ("num", 0, 10, True), "Haze": ("num", 0, 10, True)},
    "ColorCorrectionEffect": {"Enabled": ("bool",), "Brightness": ("num", -1, 1, False), "Contrast": ("num", -1, 1, False),
                              "Saturation": ("num", -1, 1, False), "TintColor": ("light",)},
    "BloomEffect": {"Enabled": ("bool",), "Intensity": ("num", 0, 1, False), "Size": ("num", 0, 56, False),
                    "Threshold": ("num", 0, 4, False)},
    "SunRaysEffect": {"Enabled": ("bool",), "Intensity": ("num", 0, 1, False), "Spread": ("num", 0, 1, True)},
    "DepthOfFieldEffect": {"Enabled": ("bool",), "FarIntensity": ("num", 0, 1, True), "NearIntensity": ("num", 0, 1, True),
                           "FocusDistance": ("num", 0, 200, False), "InFocusRadius": ("num", 0, 50, False)},
}
LOOK_CLASSES = ["Lighting", "Atmosphere", "ColorCorrectionEffect", "BloomEffect", "SunRaysEffect", "DepthOfFieldEffect"]
LAYER_CLASSES = ["ParticleEmitter", "Beam", "PointLight", "SpotLight", "SurfaceLight", "Debris"]


class Issues:
    def __init__(self):
        self.items = []

    def add(self, level, where, msg):
        self.items.append((level, where, msg))

    def err(self, where, msg):
        self.add("ERROR", where, msg)

    def warn(self, where, msg):
        self.add("WARN", where, msg)

    def count(self, level):
        return sum(1 for x in self.items if x[0] == level)


class Ctx:
    """Resolution context: fx colours, bible, issues."""

    def __init__(self, bible, fx_colours, issues):
        self.bible, self.fx, self.issues = bible, fx_colours, issues
        self.canon_refs, self.oq_refs = [], []

    def colour(self, ref, where):
        """-> (hex, kind) with kind token|fx|neutral; None on error (issue recorded)."""
        if isinstance(ref, dict) and "v" in ref:
            ref = ref["v"]
        if not isinstance(ref, str):
            self.issues.err(where, f"colour must be '@bible.key', '$fx_name' or '#FFFFFF'/'#000000', got {ref!r}")
            return None
        if ref.startswith("@"):
            key = ref[1:]
            if not self.bible.ok():
                self.issues.err(where, f"{ref}: rr-bible not found (set RR_BIBLE_SKILL)")
                return None
            f = self.bible.fact(key)
            if not f:
                self.issues.err(where, f"{ref}: no such canon key (bible get {key.rsplit('.', 1)[0]})")
                return None
            if not HEX_RE.match(f["value"]):
                self.issues.err(where, f"{ref}: canon value {f['value']!r} is not a colour")
                return None
            if f["status"] == "superseded":
                self.issues.err(where, f"{ref}: token is superseded")
            elif f["status"] == "conflict":
                self.issues.warn(where, f"{ref}: token is undecided (conflict); label output 'assumed'")
            return f["value"].upper(), "token"
        if ref.startswith("$"):
            c = self.fx.get(ref[1:])
            if not c:
                self.issues.err(where, f"{ref}: not declared in fx_colours")
                return None
            return c["hex"].upper(), "fx"
        if HEX_RE.match(ref) and ref.upper() in NEUTRALS:
            return ref.upper(), "neutral"
        self.issues.err(where, f"{ref}: raw colour; use an @bible token or declare it in fx_colours with a reason")
        return None


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _unwrap(raw, ctx, where):
    """{"v": x, "canon": key} or {"canon": key} or {"v": x, "oq": id}: record refs, return the value."""
    if isinstance(raw, dict) and ("canon" in raw or "oq" in raw) and not any(k in raw for k in ("add", "mul", "lerp", "set")):
        if "canon" in raw:
            ctx.canon_refs.append((where, raw["canon"], raw.get("v"), raw.get("match")))
            if "v" not in raw:
                v = ctx.bible.number(raw["canon"]) if ctx.bible.ok() else None
                if v is None:
                    ctx.issues.err(where, f"canon {raw['canon']} has no number to read")
                return v
        if "oq" in raw:
            ctx.oq_refs.append((where, raw["oq"]))
        return raw.get("v")
    return raw


def convert(cls, prop, raw, ctx, where):
    """Typed value: ('num', x) ('bool', b) ('str', s) ('enum', 'Enum.T.N') ('color', hex) ('light', [r,g,b])
    ('range', a, b) ('nseq', [(t, v, e)]) ('cseq', [(t, hex)]) ('v2', x, y) ('v3', x, y, z). None on error."""
    spec = SCHEMA.get(cls, {}).get(prop)
    w = f"{where}.{prop}"
    if spec is None:
        ctx.issues.err(w, f"{cls} has no property {prop} in the schema (typo, or add it to SCHEMA with its range)")
        return None
    raw = _unwrap(raw, ctx, w)
    if raw is None:
        return None
    t = spec[0]

    def rng(v, what=""):
        lo, hi, hard = (spec[1], spec[2], spec[3]) if len(spec) >= 4 else (None, None, False)
        if (lo is not None and v < lo) or (hi is not None and v > hi):
            ctx.issues.add("ERROR" if hard else "WARN", w, f"{what}{v} outside {lo}..{hi}" + ("" if hard else " (soft range; check in Studio)"))

    if t == "num":
        if not _num(raw):
            ctx.issues.err(w, f"number expected, got {raw!r}")
            return None
        rng(raw)
        return ("num", raw)
    if t == "bool":
        if not isinstance(raw, bool):
            ctx.issues.err(w, f"true/false expected, got {raw!r}")
            return None
        return ("bool", raw)
    if t == "str":
        if not isinstance(raw, str):
            ctx.issues.err(w, "string expected")
            return None
        if prop == "Texture" and raw and not re.match(r"^(rbxasset://|rbxassetid://\d+$)", raw):
            ctx.issues.err(w, f"texture must be rbxasset:// or rbxassetid://<id>, got {raw!r}")
        return ("str", raw)
    if t == "enum":
        m = re.fullmatch(r"Enum\.(\w+)\.(\w+)", raw) if isinstance(raw, str) else None
        if not m or m.group(1) != spec[1] or m.group(2) not in spec[2]:
            ctx.issues.err(w, f"expected Enum.{spec[1]}.<{'|'.join(spec[2])}>, got {raw!r}")
            return None
        return ("enum", raw)
    if t == "color":
        c = ctx.colour(raw, w)
        return ("color", c[0]) if c else None
    if t == "light":
        if isinstance(raw, list) and len(raw) == 3 and all(_num(v) and 0 <= v <= 255 for v in raw):
            return ("light", [int(round(v)) for v in raw])
        c = ctx.colour(raw, w)
        return ("color", c[0]) if c else None
    if t == "range":
        if _num(raw):
            raw = [raw, raw]
        if not (isinstance(raw, list) and len(raw) == 2 and all(_num(v) for v in raw)) or raw[0] > raw[1]:
            ctx.issues.err(w, f"NumberRange [min, max] expected (min <= max), got {raw!r}")
            return None
        rng(raw[0]), rng(raw[1])
        return ("range", raw[0], raw[1])
    if t in ("v2", "v3"):
        n = 2 if t == "v2" else 3
        if not (isinstance(raw, list) and len(raw) == n and all(_num(v) for v in raw)):
            ctx.issues.err(w, f"{n} numbers expected, got {raw!r}")
            return None
        if len(spec) >= 4:
            for v in raw:
                rng(v)
        return (t, *raw)
    if t == "nseq":
        if _num(raw):
            rng(raw)
            return ("nseq", [(0, raw, 0), (1, raw, 0)])
        kps = _keypoints(raw, w, ctx)
        if kps is None:
            return None
        out = []
        for k in kps:
            v, e = k[1], (k[2] if len(k) > 2 else 0)
            if not _num(v) or not _num(e) or e < 0:
                ctx.issues.err(w, f"keypoint {k!r}: value and envelope must be numbers, envelope >= 0")
                return None
            rng(v, f"t={k[0]}: ")
            if spec[3] and spec[1] is not None and v - e < spec[1] - 1e-9 and e:
                ctx.issues.err(w, f"t={k[0]}: value - envelope {v - e} below {spec[1]}")
            out.append((k[0], v, e))
        return ("nseq", out)
    if t == "cseq":
        if not isinstance(raw, list):
            c = ctx.colour(raw, w)
            return ("cseq", [(0, c[0]), (1, c[0])]) if c else None
        kps = _keypoints(raw, w, ctx)
        if kps is None:
            return None
        out = []
        for k in kps:
            c = ctx.colour(k[1], w)
            if not c:
                return None
            out.append((k[0], c[0]))
        return ("cseq", out)
    ctx.issues.err(w, f"unknown schema type {t}")
    return None


def _keypoints(raw, w, ctx):
    if not (isinstance(raw, list) and 2 <= len(raw) <= 20 and all(isinstance(k, list) and len(k) >= 2 for k in raw)):
        ctx.issues.err(w, "sequence must be 2..20 keypoints [time, value(, envelope)] (Roblox caps keypoints at 20)")
        return None
    times = [k[0] for k in raw]
    if not all(_num(t) for t in times) or times[0] != 0 or times[-1] != 1 or any(b <= a for a, b in zip(times, times[1:])):
        ctx.issues.err(w, f"keypoint times must start at 0, end at 1 and increase, got {times}")
        return None
    return raw


def seq_at(seq, t):
    """Evaluate an nseq (value part) at t in 0..1 (piecewise linear)."""
    for (t0, v0, *_), (t1, v1, *_) in zip(seq, seq[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * ((t - t0) / (t1 - t0) if t1 > t0 else 0)
    return seq[-1][1]


def seq_mean(seq):
    return sum((t1 - t0) * (v0 + v1) / 2 for (t0, v0, *_), (t1, v1, *_) in zip(seq, seq[1:]))


# ------------------------------------------------------------------ loading
def load_json(name):
    p = presets_dir() / name
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"missing {p}")
    except ValueError as e:
        sys.exit(f"{p}: bad JSON: {e}")


class Model:
    """Everything loaded and typed once."""

    def __init__(self, bible=None):
        self.bible = bible or Bible()
        self.issues = Issues()
        self.vfx_raw, self.light_raw, self.budget_raw = load_json("vfx.json"), load_json("lighting.json"), load_json("budgets.json")
        fx = {}
        for src in (self.vfx_raw.get("fx_colours", {}), self.light_raw.get("fx_colours", {})):
            for k, v in src.items():
                if k in fx:
                    self.issues.err(f"fx_colours.{k}", "declared twice")
                if not (isinstance(v, dict) and HEX_RE.match(v.get("hex", "")) and v.get("why")):
                    self.issues.err(f"fx_colours.{k}", "needs {hex: '#RRGGBB', why: 'reason'}")
                    continue
                fx[k] = v
        self.fx = fx
        self.ctx = Ctx(self.bible, fx, self.issues)
        self.meta = self._meta()
        self.dims = stand_dims(self.bible)
        self.presets = {n: self._preset(n, p) for n, p in self.vfx_raw.get("presets", {}).items()}
        self.trails = {n: self._trail(n, t) for n, t in self.vfx_raw.get("trails", {}).items()}
        st = self.vfx_raw.get("stand", {})
        self.anchors = {k: v for k, v in ((k, vec_eval(v, self.dims, f"stand.anchors.{k}", self.issues))
                                          for k, v in st.get("anchors", {}).items()) if v}
        self.near = st.get("near_camera", {})

    def _meta(self):
        m = self.vfx_raw.get("meta", {})
        out = {"wind_scale": m.get("wind_scale", 1.0)}
        out["speed_max"] = _unwrap(m.get("speed_max", 50), self.ctx, "meta.speed_max")
        out["speeds"] = {k: _unwrap(v, self.ctx, f"meta.speeds.{k}") for k, v in m.get("speeds", {}).items()}
        return out

    def _props(self, cls, props, where):
        out = {}
        for k, v in (props or {}).items():
            tv = convert(cls, k, v, self.ctx, where)
            if tv is not None:
                out[k] = tv
        return out

    def _trail(self, name, t):
        return {"use": t.get("use", ""), "width": t.get("width", 0.5), "props": self._props("Trail", t.get("props"), f"trails.{name}")}

    def _preset(self, name, p):
        w = f"presets.{name}"
        iss = self.issues
        out = {k: p.get(k) for k in ("kind", "priority", "anchor", "use", "canon", "oq", "speed_link", "crackle", "preview")}
        if p.get("kind") not in ("loop", "burst"):
            iss.err(w, "kind must be loop or burst")
        if p.get("start") not in (None, "on", "off"):
            iss.err(w, "start must be on or off (default: off for priority-1 loops, on otherwise)")
        out["start"] = p.get("start") or ("off" if p.get("priority") == 1 else "on")
        if p.get("priority") not in (1, 2, 3):
            iss.err(w, "priority must be 1 (crisis signal), 2 (feedback) or 3 (ambience)")
        if not p.get("use"):
            iss.err(w, "use: one line saying what it is for")
        canon = p.get("canon")
        if isinstance(canon, list):
            for k in canon:
                self.ctx.canon_refs.append((w, k, None, None))
        elif not (isinstance(canon, str) and canon.startswith("none:")):
            iss.err(w, "canon: a list of bible keys this implements, or 'none: why' (then an oq or 'proposed')")
        elif not p.get("oq") and "proposed" not in canon:
            iss.err(w, "canon 'none: ...' needs an oq (a real OQ-nnn) or the word 'proposed' in the reason")
        if p.get("oq"):
            self.ctx.oq_refs.append((w, p["oq"]))
        layers, names = [], set()
        for i, L in enumerate(p.get("layers", [])):
            lw = f"{w}.layers[{L.get('name', i)}]"
            cls = L.get("class")
            if cls not in LAYER_CLASSES:
                iss.err(lw, f"class must be one of {', '.join(LAYER_CLASSES)}")
                continue
            if L.get("name") in names or not L.get("name"):
                iss.err(lw, "every layer needs a unique name")
            names.add(L.get("name"))
            lay = {k: L.get(k) for k in ("name", "class", "emit", "delay", "pulse", "flicker", "parent", "preview_sprite")}
            for vec in ("offset", "dir", "a1", "part_size"):
                if vec in L:
                    v = L[vec]
                    if not (isinstance(v, list) and len(v) == 3):
                        iss.err(f"{lw}.{vec}", "3 numbers expected")
                        continue
                    r = vec_eval(v, self.dims, f"{lw}.{vec}", iss)   # offsets may follow the canon stand ("-gauge")
                    if r is not None:
                        lay[vec] = r
            lay.setdefault("offset", [0, 0, 0])
            if "dir" in lay and math.hypot(*lay["dir"]) < 1e-6:
                iss.err(f"{lw}.dir", "zero vector")
            if cls == "Debris":
                d = L.get("debris") or {}
                req = ("count", "size", "speed", "spread", "lifetime", "colours")
                if any(k not in d for k in req):
                    iss.err(lw, f"debris needs {', '.join(req)}")
                else:
                    cols = [c for c in (self.ctx.colour(c, f"{lw}.colours") for c in d["colours"]) if c]
                    lay["debris"] = {**d, "colours": [c[0] for c in cols]}
                    if d.get("trail") and d["trail"] not in self.vfx_raw.get("trails", {}):
                        iss.err(lw, f"trail {d['trail']!r} is not defined under trails")
            else:
                lay["props"] = self._props(cls, L.get("props"), lw)
            if cls == "Beam" and "a1" not in lay:
                iss.err(lw, "a Beam needs a1 (the second attachment's offset)")
            if L.get("parent") == "part" and "part_size" not in lay:
                iss.err(lw, "parent 'part' needs part_size")
            if p.get("kind") == "burst" and cls == "ParticleEmitter" and not L.get("emit"):
                iss.err(lw, "burst emitters need emit (particle count)")
            if cls in LIGHT_CLASSES and L.get("pulse") and not {"peak", "duration"} <= set(L["pulse"]):
                iss.err(lw, "pulse needs peak and duration")
            if cls in LIGHT_CLASSES and L.get("flicker") and not {"min", "max", "hz"} <= set(L["flicker"]):
                iss.err(lw, "flicker needs min, max and hz")
            if cls in ("ParticleEmitter", "Beam", "Trail"):
                lay["props"].setdefault("LightInfluence", ("num", 0))  # Instance.new default is 0 (RBXD); make it explicit
            layers.append(lay)
        out["layers"] = layers
        sl = p.get("speed_link")
        if sl:
            for ln in sl.get("layers", []):
                if ln not in names:
                    iss.err(f"{w}.speed_link", f"layer {ln!r} does not exist")
            if not (_num(sl.get("rate_idle")) and _num(sl.get("rate_max")) and 0 <= sl["rate_idle"] <= sl["rate_max"]):
                iss.err(f"{w}.speed_link", "rate_idle and rate_max numbers, 0 <= idle <= max")
        cr = p.get("crackle")
        if cr and not all(isinstance(cr.get(k), list) and len(cr[k]) == 2 for k in ("every", "emit")):
            iss.err(f"{w}.crackle", "every: [min_s, max_s] and emit: [min, max]")
        return out

    # ---------------- looks
    def looks(self):
        """Every allowed biome.time name."""
        L = self.light_raw
        return [f"{b}.{t}" for b, bd in L.get("biomes", {}).items() for t in bd.get("times", [])]

    def resolve_look(self, name, issues=None):
        """biome.time[+override...] -> {'classes': {cls: {prop: typed}}, 'fx_on': [...], 'parts': ...}."""
        iss = issues or self.issues
        L = self.light_raw
        name = name.split("@")[0]
        head, *ovs = name.split("+")
        if head.count(".") != 1:
            raise KeyError(f"look {name!r}: use biome.time[+override]")
        biome, time = head.split(".")
        if biome not in L.get("biomes", {}):
            raise KeyError(f"no biome {biome!r}; biomes: {', '.join(L.get('biomes', {}))}")
        bd = L["biomes"][biome]
        if time not in bd.get("times", []):
            raise KeyError(f"{biome} has no {time!r} look; times: {', '.join(bd.get('times', []))}")
        for o in ovs:
            if o not in L.get("overrides", {}):
                raise KeyError(f"no override {o!r}; overrides: {', '.join(L.get('overrides', {}))}")
        ctx = Ctx(self.bible, self.fx, iss)
        ctx.canon_refs, ctx.oq_refs = self.ctx.canon_refs, self.ctx.oq_refs  # every look's canon values get checked
        state, fx_on = {}, []
        layers = [("base", L.get("base", {})), (f"times.{time}", L["times"].get(time, {})), (f"biomes.{biome}", bd)]
        layers += [(f"overrides.{o}", L["overrides"][o]) for o in ovs]
        for where, blk in layers:
            for cls in LOOK_CLASSES:
                for prop, raw in (blk.get(cls) or {}).items():
                    cur = state.setdefault(cls, {}).get(prop)
                    val = apply_op(cls, prop, cur, raw, ctx, f"{where}.{cls}")
                    if val is not None:
                        state[cls][prop] = val
            for f in blk.get("fx_on", []) or []:
                if f not in fx_on:
                    fx_on.append(f)
        return {"name": name, "biome": biome, "time": time, "overrides": ovs, "classes": state, "fx_on": fx_on,
                "scene": bd.get("scene", biome)}


def _rgb(hx):
    hx = hx.lstrip("#")
    return [int(hx[i:i + 2], 16) for i in (0, 2, 4)]


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(v)))) for v in rgb)


def apply_op(cls, prop, cur, raw, ctx, where):
    """Plain value sets; {'add': x}, {'mul': x}, {'lerp': [colour, t]}, {'set': v} adjust the current value."""
    if isinstance(raw, dict) and any(k in raw for k in ("add", "mul", "lerp", "set")):
        op = next(k for k in ("add", "mul", "lerp", "set") if k in raw)
        if op == "set":
            return convert(cls, prop, raw["set"], ctx, where)
        if cur is None:
            ctx.issues.err(f"{where}.{prop}", f"{op} on a value nobody set before (set it in base)")
            return None
        if op in ("add", "mul"):
            x = raw[op]
            if cur[0] == "num" and _num(x):
                v = cur[1] + x if op == "add" else cur[1] * x
                return convert(cls, prop, round(v, 6), ctx, where)
            if cur[0] in ("light", "color") and op == "mul" and _num(x):
                rgb = cur[1] if cur[0] == "light" else _rgb(cur[1])
                v = [min(255, round(c * x)) for c in rgb]
                return ("light", v) if cur[0] == "light" else ("color", _hex(v), ("mul", cur, x))
            ctx.issues.err(f"{where}.{prop}", f"{op} does not apply to a {cur[0]}")
            return None
        tgt, t = (raw["lerp"] + [None])[:2]
        c = ctx.colour(tgt, f"{where}.{prop}")
        if not c or not _num(t) or cur[0] not in ("light", "color"):
            ctx.issues.err(f"{where}.{prop}", "lerp needs [colour, 0..1] on a colour or light level")
            return None
        a = cur[1] if cur[0] == "light" else _rgb(cur[1])
        b = _rgb(c[0])
        v = [a[i] + (b[i] - a[i]) * t for i in range(3)]
        return ("light", [round(x) for x in v]) if cur[0] == "light" else ("color", _hex(v), ("lerp", cur, c[0], t))
    return convert(cls, prop, raw, ctx, where)


# ------------------------------------------------------------------ budgets
def tier_cfg(model, tier):
    return model.budget_raw["tiers"][tier]


def preset_cost(model, name, tier):
    p = model.presets[name]
    cfg = tier_cfg(model, tier)
    scale = cfg["rate_scale"].get(str(p.get("priority")), 1.0)
    c = dict(steady=0.0, burst=0.0, fill=0.0, emitters=0, lights=0, shadowed=0, beams=0, debris=0)
    sl = p.get("speed_link") or {}
    for L in p["layers"]:
        cls, pr = L["class"], L.get("props", {})
        if cls == "ParticleEmitter":
            c["emitters"] += 1
            life = pr.get("Lifetime", ("range", 1, 1))[2]
            size = seq_mean(pr["Size"][1]) if "Size" in pr else 1.0
            if p.get("kind") == "loop":
                rate = pr.get("Rate", ("num", 0))[1]
                if L["name"] in sl.get("layers", []):
                    rate = sl["rate_max"]
                if p.get("crackle"):
                    cr = p["crackle"]
                    rate = (sum(cr["emit"]) / 2) / (sum(cr["every"]) / 2)
                live = rate * scale * life
                c["steady"] += live
            else:
                live = math.ceil((L.get("emit") or 0) * scale)
                c["burst"] += live
            c["fill"] += live * size * size
        elif cls == "Beam":
            c["beams"] += 1
        elif cls in LIGHT_CLASSES:
            c["lights"] += 1
            c["shadowed"] += 1 if pr.get("Shadows", ("bool", False))[1] else 0
        elif cls == "Debris":
            c["debris"] += L.get("debris", {}).get("count", 0)
    return c


def set_cost(model, names, tier):
    tot = dict(steady=0.0, burst=0.0, fill=0.0, emitters=0, lights=0, shadowed=0, beams=0, debris=0)
    for n in names:
        for k, v in preset_cost(model, n, tier).items():
            tot[k] += v
    base = model.budget_raw.get("baseline", {})
    tot["lights"] += base.get("lights", 0)
    tot["shadowed"] += base.get("lights_shadowed", 0)
    return tot


def over_budget(model, tot, tier):
    cfg = tier_cfg(model, tier)
    checks = [("steady live particles", tot["steady"], cfg["live_particles"]),
              ("peak live particles", tot["steady"] + tot["burst"], cfg["burst_peak"]),
              ("emitters", tot["emitters"], cfg["emitters"]), ("fill stud^2", tot["fill"], cfg["fill_stud2"]),
              ("lights in view", tot["lights"], cfg["lights_view"]), ("shadowed lights", tot["shadowed"], cfg["lights_shadowed"]),
              ("beams", tot["beams"], cfg["beams"]), ("debris parts", tot["debris"], cfg["debris_parts"])]
    return [(n, v, lim) for n, v, lim in checks if v > lim + 1e-9], checks


# ------------------------------------------------------------------ validate
def band_check(model, hexes, where_of):
    """Palette-exempt colours (fx colours, light levels scaled to full value) must stay out of the sepia and
    blue-sky bands (style.dont.*): rr-bible's check names the band; this reads it from its JSON."""
    out = []
    if not hexes or not model.bible.ok():
        return out
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for h in hexes:
            f.write(f"{h}\n")
        tmp = f.name
    try:
        _, res = model.bible.check(tmp, skip="fonts,names,numbers")
    finally:
        os.unlink(tmp)
    lines = {i + 1: h for i, h in enumerate(hexes)}
    for x in res.get("findings", []):
        if "band" in x.get("msg", ""):
            h = lines.get(x["line"], "?")
            out.append((where_of.get(h, h), f"{h}: {x['msg'].split(';')[-1].strip()}"))
    return out


def light_to_hex(rgb):
    """A light level's tint at a mid-high lightness (chromaticity kept), so the band test sees the hue and
    saturation the light adds, not its intensity."""
    mean = sum(rgb) / 3
    if mean <= 0:
        return "#000000"
    k = min(0.62 * 255 / mean, 255 / max(rgb))
    return _hex([c * k for c in rgb])


def look_combos(model):
    """Every biome.time, each with every override, and with all overrides stacked (validate checks them all)."""
    looks, ovs = model.looks(), list(model.light_raw.get("overrides", {}))
    out = list(looks) + [f"{l}+{o}" for l in looks for o in ovs]
    if len(ovs) > 1:
        out += [f"{l}+{'+'.join(ovs)}" for l in looks]
    return out


def validate(model, strict=False, quiet=False):
    iss = model.issues
    b = model.bible
    if not b.ok():
        iss.err("rr-bible", "not found; canon refs cannot be checked (set RR_BIBLE_SKILL)")
    anchors = model.anchors
    in_sets = {n for s in model.budget_raw.get("sets", {}).values() for n in s.get("presets", [])}
    for n, p in model.presets.items():
        if p.get("anchor") not in anchors:
            iss.warn(f"presets.{n}", f"anchor {p.get('anchor')!r} has no preview position in stand.anchors")
        if n not in in_sets:
            iss.warn(f"presets.{n}", "in no budgets.json set: add it to the sets it can stack with, or the budget never counts it")
        for L in p["layers"]:
            pr = L.get("props", {})
            if pr.get("WindAffectsDrag", ("bool", False))[1] and pr.get("Drag", ("num", 0))[1] <= 0:
                iss.warn(f"presets.{n}.{L['name']}", "WindAffectsDrag needs Drag > 0 (RBXD) or the drift does nothing")
            if L["class"] == "ParticleEmitter" and pr.get("LightEmission", ("num", 0))[1] >= 0.5 and pr.get("LightInfluence", ("num", 0))[1] > 0.5:
                iss.warn(f"presets.{n}.{L['name']}", "additive and lit at once: goes muddy in the dark; LightInfluence <= 0.5 for glows")
            fl = L.get("flicker") or {}
            if L["class"] in LIGHT_CLASSES and fl.get("hz", 0) > 3 and pr.get("Range", ("num", 0))[1] >= 20:
                iss.warn(f"presets.{n}.{L['name']}", f"flicker {fl['hz']} Hz on a Range >= 20 light is a scene flash: "
                         "keep it <= 3 Hz (av.feel.flash_limit); the runtime freezes it when flashes are off")
        if p.get("kind") == "loop" and p.get("priority") == 3 and not p.get("speed_link") and not p.get("oq"):
            iss.warn(f"presets.{n}", "ambience loop with no speed link or OQ: is it needed?")
    # looks: every biome.time, alone, with each override and with all stacked (ranges, clamps, fx_on)
    L = model.light_raw
    for bname, bd in L.get("biomes", {}).items():
        for t in bd.get("times", []):
            if t not in L.get("times", {}):
                iss.err(f"biomes.{bname}", f"time {t!r} is not defined under times")
    seen_where = {(lvl, w) for lvl, w, _ in iss.items}
    for name in look_combos(model):
        tmp = Issues()
        try:
            look = model.resolve_look(name, tmp)
        except KeyError as e:
            iss.err(f"looks.{name}", str(e))
            continue
        for f in look["fx_on"]:
            if f not in model.presets:
                tmp.err(f"looks.{name.split('+')[0]}", f"fx_on {f!r} is not an effect preset")
        lt = look["classes"].get("Lighting", {})
        if "Ambient" in lt and "OutdoorAmbient" in lt and lt["Ambient"][0] == "light" == lt["OutdoorAmbient"][0]:
            if any(a > o for a, o in zip(lt["Ambient"][1], lt["OutdoorAmbient"][1])):
                tmp.warn(f"looks.{name}", "Ambient exceeds OutdoorAmbient in a channel: Roblox clamps OutdoorAmbient up (RBXD)")
        for lvl, w, msg in tmp.items:          # report each problem once, naming the first look it breaks
            if (lvl, w) not in seen_where:
                seen_where.add((lvl, w))
                iss.add(lvl, w, msg + ("" if w.endswith(name) or "+" not in name else f" (in {name})"))
    for oname, ov in L.get("overrides", {}).items():
        for k in ov.get("canon", []) or []:
            model.ctx.canon_refs.append((f"overrides.{oname}", k, None, None))
    for oname, t in L.get("times", {}).items():
        if t.get("oq"):
            model.ctx.oq_refs.append((f"times.{oname}", t["oq"]))
    st = L.get("studio", {})
    for k in ("Use2022Materials",):
        if isinstance(st.get(k), dict):
            _unwrap(st[k], model.ctx, f"studio.{k}")
    # canon consistency: every {"v": x, "canon": key} must match the number canon gives for that property
    if b.ok():
        for where, key, v, match in dict.fromkeys((w, k, json.dumps(v), m) for w, k, v, m in model.ctx.canon_refs):
            v = json.loads(v)
            f = b.fact(key)
            if not f:
                iss.err(where, f"canon key {key} not found in rr-bible")
                continue
            if f["status"] == "superseded":
                iss.err(where, f"{key} is superseded")
            if v is None:
                continue
            ok, how = canon_agrees(v, f"{f['value']} | {f.get('note', '')}", where.rsplit(".", 1)[-1], match)
            if not ok:
                iss.err(where, f"value {v!r} {how} canon {key} = {f['value']!r}")
        seen = set()
        for where, oid in model.ctx.oq_refs:
            if oid in seen:
                continue
            seen.add(oid)
            q = b.oq(oid)
            if not q:
                iss.err(where, f"{oid} not found in rr-bible")
            elif q.get("fields", {}).get("status", "open") != "open" or q.get("id", "").startswith("D-"):
                iss.warn(where, f"{oid} is no longer open ({q.get('id')}): update the preset to the decision")
    # colour bands for palette-exempt colours
    where_of = {}
    for k, v in model.fx.items():
        where_of[v["hex"].upper()] = f"fx_colours.{k}"
    for name in model.looks():
        try:
            look = model.resolve_look(name, Issues())
        except KeyError:
            continue
        for cls, props in look["classes"].items():
            for prop, tv in props.items():
                if tv[0] == "light" and prop != "TintColor" and max(tv[1]) >= 24:
                    where_of.setdefault(light_to_hex(tv[1]), f"looks.{name}.{cls}.{prop} (light level {tv[1]})")
                elif tv[0] == "color" and len(tv) > 2:
                    where_of.setdefault(tv[1], f"looks.{name}.{cls}.{prop} (derived colour)")
    for where, msg in band_check(model, sorted(where_of), where_of):
        iss.add("ERROR" if where.startswith("fx_colours") else "WARN", where, msg + " (style.dont.*)")
    # per-preset budget sanity (a single preset over the phone budget can never fit a set)
    for n in model.presets:
        tot = set_cost(model, [n], "phone")
        bad, _ = over_budget(model, tot, "phone")
        for what, v, lim in bad:
            iss.err(f"presets.{n}", f"alone exceeds the phone {what}: {v:.0f} > {lim}")
    for sname, s in model.budget_raw.get("sets", {}).items():
        for n in s["presets"]:
            if n not in model.presets:
                iss.err(f"budgets.sets.{sname}", f"unknown preset {n!r}")
    iss.items = list(dict.fromkeys(iss.items))  # base values resolve into every look: report each issue once
    errors, warns = iss.count("ERROR"), iss.count("WARN")
    if not quiet:
        for lvl, where, msg in sorted(iss.items, key=lambda x: (x[0] != "ERROR", x[1])):
            print(f"{lvl} {where}: {msg}")
        verdict = "FAIL" if errors or (strict and warns) else "PASS"
        print(f"validate {verdict}: {len(model.presets)} presets, {len(model.trails)} trails, {len(model.looks())} looks "
              f"(+{len(look_combos(model)) - len(model.looks())} override combos), {len(L.get('overrides', {}))} overrides; "
              f"{errors} errors, {warns} warnings; {len({(r[0], r[1]) for r in model.ctx.canon_refs})} canon refs, "
              f"{len({o for _, o in model.ctx.oq_refs})} OQ refs")
    return 1 if errors or (strict and warns) else 0


HEX_TOKEN = re.compile(r"#[0-9A-Fa-f]{6}\b")
NUM_RE = r"[-+]?\d+(?:\.\d+)?"


def _same(v, s):
    if isinstance(v, bool):
        return s.lower() == str(v).lower()
    try:
        return abs(float(s) - float(v)) < 1e-9
    except ValueError:
        return False


def canon_agrees(v, text, prop=None, match=None):
    """-> (ok, how). Compares v with the number canon gives for this property: a ref's own `match` regex (group 1),
    else the number right after the property name ('Saturation +0.12', 'Range 9', 'Density about 0.3'), else
    the only number in the text. Hex colours never count as numbers; lists compare as 'a,b,c'."""
    t = HEX_TOKEN.sub(" ", text)
    if match:
        m = re.search(match, t, re.I)
        if not m:
            return False, f"has no match for {match!r} in"
        return _same(v, (m.group(1) if m.groups() else m.group(0)).replace(" ", "")), "contradicts (match)"
    if isinstance(v, list):
        return ",".join(lua_num(x) if _num(x) else str(x) for x in v) in t.replace(" ", ""), "contradicts"
    if prop:
        m = re.search(rf"\b{re.escape(prop)}\b[\s=:~]*(?:about|approx(?:imately)?|of|is|at)?[\s=:~]*({NUM_RE}|true|false)\b", t, re.I)
        if m:
            return _same(v, m.group(1)), f"contradicts {prop} {m.group(1)} in"
    if isinstance(v, bool):
        words = set(re.findall(r"\b(true|false)\b", t.lower()))
        return words == {str(v).lower()}, "is not the only true/false in"
    nums = {float(x) for x in re.findall(NUM_RE, t)}
    if len(nums) > 1:
        return False, f"is ambiguous (canon text has {len(nums)} numbers and does not name {prop}; add \"match\") against"
    return bool(nums) and _same(v, next(iter(nums))), "contradicts"


# ------------------------------------------------------------------ Luau
def lua_num(x):
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    s = repr(round(x, 6)) if isinstance(x, float) else str(x)
    return s


def lua_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def lua_val(tv):
    t = tv[0]
    if t == "num":
        return lua_num(tv[1])
    if t == "bool":
        return "true" if tv[1] else "false"
    if t == "str":
        return lua_str(tv[1])
    if t == "enum":
        return tv[1]
    if t == "color":
        if len(tv) > 2:   # derived by an op: emit the op so the canon gate sees the source colours, not a new hex
            op = tv[2]
            if op[0] == "lerp":
                return f'{lua_val(op[1])}:Lerp(hex("{op[2].lstrip("#")}"), {lua_num(op[3])})'
            return f"{lua_val(op[1])}:Lerp(Color3.new(0, 0, 0), {lua_num(round(1 - op[2], 6))})"
        return f'hex("{tv[1].lstrip("#")}")'
    if t == "light":
        return f"lvl({tv[1][0]}, {tv[1][1]}, {tv[1][2]})"
    if t == "range":
        return f"nr({lua_num(tv[1])}, {lua_num(tv[2])})"
    if t == "v2":
        return f"Vector2.new({lua_num(tv[1])}, {lua_num(tv[2])})"
    if t == "v3":
        return f"Vector3.new({lua_num(tv[1])}, {lua_num(tv[2])}, {lua_num(tv[3])})"
    if t == "nseq":
        return "ns({" + ", ".join("{" + ", ".join(lua_num(x) for x in (k if k[2] else k[:2])) + "}" for k in tv[1]) + "})"
    if t == "cseq":
        return "cs({" + ", ".join(f'{{{lua_num(k[0])}, hex("{k[1].lstrip("#")}")}}' for k in tv[1]) + "})"
    raise ValueError(t)


def lua_key(k):
    return k if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k) else f"[{lua_str(k)}]"


def v3(v):
    return f"Vector3.new({', '.join(lua_num(x) for x in v)})"


def lua_plain(x, depth=0):
    """Plain JSON data (numbers, strings, lists, dicts) as a Luau table literal."""
    if isinstance(x, bool):
        return "true" if x else "false"
    if _num(x):
        return lua_num(x)
    if isinstance(x, str):
        return lua_str(x)
    if isinstance(x, list):
        return "{" + ", ".join(lua_plain(v) for v in x) + "}"
    if isinstance(x, dict):
        return "{" + ", ".join(f"{lua_key(str(k))} = {lua_plain(v)}" for k, v in x.items()) + "}"
    return "nil"


HEADER = """-- {name}: GENERATED by rr-vfx-lighting (vfx.py build, {date}) from presets/{src}.
-- Do not edit: change the JSON and rebuild. Palette colours use hex(); light levels use lvl() (intensities, not palette).
local function hex(h) return Color3.fromHex(h) end
local function lvl(r, g, b) return Color3.fromRGB(r, g, b) end
"""
SEQ_HELPERS = """local function nr(a, b) return NumberRange.new(a, b) end
local function ns(t)
	local k = {}
	for i, p in ipairs(t) do k[i] = NumberSequenceKeypoint.new(p[1], p[2], p[3] or 0) end
	return NumberSequence.new(k)
end
local function cs(t)
	local k = {}
	for i, p in ipairs(t) do k[i] = ColorSequenceKeypoint.new(p[1], p[2]) end
	return ColorSequence.new(k)
end
"""


def gen_fx_lua(model, only=None):
    m, B = model.meta, model.budget_raw
    out = [HEADER.format(name="RR_FXPresets", date=TODAY, src="vfx.json"), SEQ_HELPERS, "local P = {}", ""]
    tiers = {t: {"rate_scale": {int(k): v for k, v in c["rate_scale"].items()}, "post_off": c["post_off"],
                 "live_particles": c["live_particles"], "burst_peak": c["burst_peak"]} for t, c in B["tiers"].items()}
    out.append("P.meta = {")
    out.append(f"\tspeed_max = {lua_num(m['speed_max'] or 50)}, -- gameplay.speed.fast (rr-bible)")
    out.append("\tspeeds = " + lua_plain(m["speeds"]) + ",")
    out.append(f"\twind_scale = {lua_num(m['wind_scale'])},")
    out.append(f"\tbudget_status = {lua_str(B.get('status', ''))},")
    out.append("\ttiers = {")
    for t, c in tiers.items():
        rs = "{" + ", ".join(f"[{k}] = {lua_num(v)}" for k, v in sorted(c["rate_scale"].items())) + "}"
        out.append(f"\t\t{t} = {{rate_scale = {rs}, post_off = {lua_plain(c['post_off'])}, "
                   f"live_particles = {c['live_particles']}, burst_peak = {c['burst_peak']}}},")
    out.append("\t},")
    out.append("}")
    out.append("")
    out.append("P.trails = {")
    for n, t in model.trails.items():
        out.append(f"\t{lua_key(n)} = {{width = {lua_num(t['width'])}, props = {{")
        for k, tv in t["props"].items():
            out.append(f"\t\t{k} = {lua_val(tv)},")
        out.append("\t}},")
    out.append("}")
    out.append("")
    out.append("P.presets = {")
    for n, p in model.presets.items():
        if only is not None and n not in only:
            continue
        out.append(f"\t{lua_key(n)} = {{")
        out.append(f"\t\tkind = {lua_str(p['kind'])}, priority = {p['priority']}, anchor = {lua_str(p['anchor'] or '')}, "
                   f"start = {lua_str(p['start'])},")
        out.append(f"\t\tuse = {lua_str(p.get('use') or '')},")
        if p.get("speed_link"):
            sl = p["speed_link"]
            out.append(f"\t\tspeed_link = {{layers = {lua_plain(sl['layers'])}, idle = {lua_num(sl['rate_idle'])}, max = {lua_num(sl['rate_max'])}}},")
        if p.get("crackle"):
            out.append(f"\t\tcrackle = {lua_plain(p['crackle'])},")
        out.append("\t\tlayers = {")
        for L in p["layers"]:
            bits = [f"name = {lua_str(L['name'])}", f"class = {lua_str(L['class'])}", f"offset = {v3(L['offset'])}"]
            for k in ("dir", "a1", "part_size"):
                if k in L:
                    bits.append(f"{k} = {v3(L[k])}")
            for k in ("emit", "delay", "parent"):
                if L.get(k) is not None:
                    bits.append(f"{k} = {lua_plain(L[k])}")
            for k in ("pulse", "flicker"):
                if L.get(k):
                    bits.append(f"{k} = {lua_plain(L[k])}")
            if L["class"] == "Debris":
                d = L["debris"]
                bits.append("debris = {" + f"count = {d['count']}, size = {v3(d['size'])}, speed = {lua_plain(d['speed'])}, "
                            f"spread = {lua_num(d['spread'])}, lifetime = {lua_num(d['lifetime'])}, "
                            f"gravity_scale = {lua_num(d.get('gravity_scale', 1))}, carry = {lua_num(d.get('carry', 0))}, "
                            f"colours = {{{', '.join(lua_val(('color', c)) for c in d['colours'])}}}, "
                            f"trail = {lua_str(d.get('trail') or '')}" + "}")
            out.append("\t\t\t{" + ", ".join(bits) + ", props = {")
            for k, tv in L.get("props", {}).items():
                out.append(f"\t\t\t\t{k} = {lua_val(tv)},")
            out.append("\t\t\t}},")
        out.append("\t\t},")
        out.append("\t},")
    out.append("}")
    out.append("")
    out.append("return P")
    return "\n".join(out) + "\n"


def gen_light_lua(model, only=None):
    L = model.light_raw
    looks = [n for n in model.looks() if only is None or n in only] or model.looks()
    hero = L.get("preview", {}).get("hero", looks[0])
    out = [HEADER.format(name="RR_LightingPresets", date=TODAY, src="lighting.json"), "local P = {}", ""]
    out.append(f"P.default = {lua_str(hero if hero in looks else looks[0])}")
    out.append("P.looks = {")
    for name in looks:
        look = model.resolve_look(name)
        out.append(f"\t[{lua_str(name)}] = {{")
        for cls in LOOK_CLASSES:
            props = look["classes"].get(cls)
            if not props:
                continue
            out.append(f"\t\t{cls} = {{" + ", ".join(f"{k} = {lua_val(tv)}" for k, tv in props.items()) + "},")
        out.append(f"\t\tfx_on = {lua_plain(look['fx_on'])},")
        out.append("\t},")
    out.append("}")
    out.append("")
    out.append("P.overrides = {")
    ctx = Ctx(model.bible, model.fx, model.issues)
    for oname, ov in L.get("overrides", {}).items():
        out.append(f"\t{lua_key(oname)} = {{")
        out.append(f"\t\ttween_in = {lua_num(ov.get('tween_in', 0.3))}, tween_out = {lua_num(ov.get('tween_out', 0.6))}, "
                   f"duration = {lua_num(ov['duration']) if 'duration' in ov else 'nil'},")
        out.append(f"\t\tfx_on = {lua_plain(ov.get('fx_on', []))}, flash = {'true' if ov.get('flash') else 'false'},")
        out.append("\t\tops = {")
        for cls in LOOK_CLASSES:
            ops = []
            for prop, raw in (ov.get(cls) or {}).items():
                if isinstance(raw, dict) and ("add" in raw or "mul" in raw):
                    k = "add" if "add" in raw else "mul"
                    ops.append(f'{prop} = {{"{k}", {lua_num(raw[k])}}}')
                elif isinstance(raw, dict) and "lerp" in raw:
                    c = ctx.colour(raw["lerp"][0], f"overrides.{oname}.{cls}.{prop}")
                    if c:
                        ops.append(f'{prop} = {{"lerp", {lua_val(("color", c[0]))}, {lua_num(raw["lerp"][1])}}}')
                else:
                    tv = convert(cls, prop, raw["set"] if isinstance(raw, dict) and "set" in raw else raw, ctx, f"overrides.{oname}.{cls}")
                    if tv:
                        ops.append(f'{prop} = {{"set", {lua_val(tv)}}}')
            if ops:
                out.append(f"\t\t\t{cls} = {{" + ", ".join(ops) + "},")
        out.append("\t\t},")
        out.append("\t},")
    out.append("}")
    out.append("")
    ph = model.budget_raw["tiers"]["phone"]
    out.append(f"P.phone_post_off = {lua_plain(ph['post_off'])} -- {model.budget_raw.get('status', '')}")
    out.append("")
    out.append("return P")
    return "\n".join(out) + "\n"


def gen_studio_lua(model):
    L = model.light_raw
    st = L.get("studio", {})
    hero = L.get("preview", {}).get("hero", model.looks()[0])
    look = model.resolve_look(hero)
    u22 = st.get("Use2022Materials")
    u22 = u22.get("v") if isinstance(u22, dict) else u22
    lines = [f"-- studio_lighting_setup.lua: GENERATED by rr-vfx-lighting (vfx.py build, {TODAY}).",
             "-- Paste into Studio's command bar once per place. It sets the Studio-level lighting options, lists effects",
             "-- that would stack with the RRFX_ ones, and applies the default look for editing. It prints every old value.",
             "local function hex(h) return Color3.fromHex(h) end",
             "local function lvl(r, g, b) return Color3.fromRGB(r, g, b) end",
             "local L = game:GetService(\"Lighting\")",
             "local function set(inst, prop, v)",
             "\tlocal ok, old = pcall(function() return inst[prop] end)",
             "\tlocal done = pcall(function() inst[prop] = v end)",
             "\tprint(string.format(\"%s.%s: %s -> %s%s\", inst.Name, prop, tostring(ok and old), tostring(v), done and \"\" or \" (FAILED: not settable here)\"))",
             "end",
             f"set(L, \"LightingStyle\", {st.get('LightingStyle', 'Enum.LightingStyle.Realistic')}) -- tech.lighting.technology_api",
             f"set(L, \"PrioritizeLightingQuality\", {'true' if st.get('PrioritizeLightingQuality', True) else 'false'})",
             f"set(game:GetService(\"MaterialService\"), \"Use2022Materials\", {'true' if u22 else 'false'}) -- tech.lighting.materials_2022 (canon)",
             "print(\"Lighting.Technology is deprecated and not scriptable (RBXD 2026-09-28): LightingStyle replaces it.\")",
             "for _, c in ipairs(L:GetChildren()) do",
             "\tif (c:IsA(\"PostEffect\") or c:IsA(\"Atmosphere\") or c:IsA(\"Sky\")) and string.sub(c.Name, 1, 5) ~= \"RRFX_\" then",
             "\t\tprint(\"existing effect (stacks with RR_Lighting; disable it if the look doubles up):\", c:GetFullName(), c.ClassName)",
             "\tend",
             "end",
             "local function ensure(cls)",
             "\tif cls == \"Lighting\" then return L end",
             "\tlocal inst = L:FindFirstChild(\"RRFX_\" .. cls)",
             "\tif not inst and cls == \"Atmosphere\" then inst = L:FindFirstChildOfClass(\"Atmosphere\") end",
             "\tif not inst then inst = Instance.new(cls); inst.Name = \"RRFX_\" .. cls; inst.Parent = L end",
             "\treturn inst",
             "end",
             f"-- default look: {hero}"]
    for cls in LOOK_CLASSES:
        props = look["classes"].get(cls)
        if not props:
            continue
        lines.append(f"do local i = ensure(\"{cls}\")")
        for k, tv in props.items():
            lines.append(f"\tset(i, \"{k}\", {lua_val(tv)})")
        lines.append("end")
    lines.append("print(\"rr-vfx-lighting: studio setup done. Studio test pending (owner): check the look in Play Solo and on a phone emulator.\")")
    return "\n".join(lines) + "\n"


def find_luaparse():
    cands = [os.environ.get("LUAPARSE_DIR", "")]
    try:
        cands.append(subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, timeout=20).stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    cands += [str(Path.home() / ".cache" / "rr-tools" / "node_modules"), str(Path.home() / "node_modules"),
              str(Path.cwd() / "node_modules")]
    for c in cands:
        if not c:
            continue
        for p in (Path(c) / "luaparse", Path(c) / "node_modules" / "luaparse"):
            if (p / "luaparse.js").is_file():
                return p
    return None


def lua_syntax(path):
    """-> (ok, tool, message). luaparse (Lua 5.3 grammar) when found, else a keyword/bracket balance check."""
    lp = find_luaparse() if shutil.which("node") else None
    if lp:
        js = ("const lp=require(process.argv[1]);const fs=require('fs');"
              "try{lp.parse(fs.readFileSync(process.argv[2],'utf8'),{luaVersion:'5.3'});console.log('ok')}"
              "catch(e){console.log('ERR '+e.message);process.exit(1)}")
        r = subprocess.run(["node", "-e", js, str(lp), str(path)], capture_output=True, text=True)
        return r.returncode == 0, "luaparse", r.stdout.strip() or r.stderr.strip()[:200]
    return balance_check(Path(path).read_text(encoding="utf-8"))


def balance_check(text):
    s = re.sub(r"--\[(=*)\[.*?\]\1\]", "", text, flags=re.S)
    s = re.sub(r"--[^\n]*", "", s)
    s = re.sub(r"\[(=*)\[.*?\]\1\]", '""', s, flags=re.S)
    s = re.sub(r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'', '""', s)
    opens = len(re.findall(r"\b(function|if|do|repeat)\b", s))
    closes = len(re.findall(r"\b(end|until)\b", s))
    # 'for ... do' and 'while ... do' contribute one 'do' each, already counted
    pairs = all(s.count(a) == s.count(b) for a, b in (("(", ")"), ("{", "}"), ("[", "]")))
    ok = opens == closes and pairs
    return ok, "balance check (luaparse not found: npm i --prefix ~/.cache/rr-tools luaparse)", \
        f"blocks {opens} open / {closes} close; brackets {'balanced' if pairs else 'UNBALANCED'}"


def pack_names(model, names):
    """-> (presets, looks) named, with the fx_on presets of named looks added; KeyError on unknown names."""
    presets, looks, bad = [], [], []
    for n in names or []:
        if n in model.presets:
            presets.append(n)
            continue
        try:
            model.resolve_look(n.split("@")[0], Issues())
            looks.append(n)
        except KeyError:
            bad.append(n)
    if bad:
        raise KeyError(f"not a preset or look: {', '.join(bad)} (presets: {', '.join(model.presets)}; looks: biome.time"
                       f"[+override][@camera], e.g. {model.looks()[0]})")
    return presets, looks


def wiring(model, n):
    p = model.presets[n]
    if p["kind"] == "burst":
        return f'`VFX.burst(anchor, "{n}")` on the event'
    driven = any(n in model.resolve_look(l, Issues())["fx_on"] for l in model.looks())
    if driven:
        return f'`VFX.attach(anchor, "{n}")`; the current look switches it (Lighting.apply)'
    if p["start"] == "off":
        return f'`VFX.attach(anchor, "{n}")` starts off; `VFX.setActive("{n}", true/false)` on the event'
    return f'`VFX.attach(anchor, "{n}")` runs from spawn' + ("; rate follows `VFX.setSpeed`" if p.get("speed_link") else "")


def cmd_build(model, a):
    rc = validate(model, quiet=True)
    if rc:
        validate(Model(model.bible))
        print("build refused: fix validate errors first")
        return 1
    only_p = only_l = None
    if a.only:
        try:
            only_p, only_l = pack_names(model, a.only)
        except KeyError as e:
            print(f"build: {e}")
            return 2
        only_l = [l.split("@")[0] for l in only_l]
        for l in only_l:
            only_p += [f for f in model.resolve_look(l, Issues())["fx_on"] if f not in only_p]
        for ov in model.light_raw.get("overrides", {}).values():
            only_p += [f for f in ov.get("fx_on", []) if f not in only_p]
        only_l = only_l or None
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    files = {"RR_FXPresets.lua": gen_fx_lua(model, only_p), "RR_LightingPresets.lua": gen_light_lua(model, only_l),
             "studio_lighting_setup.lua": gen_studio_lua(model)}
    for n, text in files.items():
        (out / n).write_text(text, encoding="utf-8")
    for src in sorted((SKILL / "assets" / "luau").glob("*.lua")):
        shutil.copy2(src, out / src.name)
    names = only_p or list(model.presets)
    rows = "\n".join(f"| {n} | {model.presets[n]['kind']} p{model.presets[n]['priority']} | {model.presets[n]['anchor']} | "
                     f"{wiring(model, n)} |" for n in names)
    readme = f"""# rr-vfx-lighting export ({TODAY}){' (pack: ' + ', '.join(a.only) + ')' if a.only else ''}
Studio test pending (owner). Nothing here has run in Roblox Studio. Presets from {presets_dir()}.
1. ReplicatedStorage > folder `RRFX`: RR_FXPresets, RR_LightingPresets, RR_VFX, RR_Lighting as ModuleScripts
   (Rojo: map only these four `.lua` files into the folder; the other two files are not modules).
2. Command bar, once: paste studio_lighting_setup.lua (sets LightingStyle, PrioritizeLightingQuality, Use2022Materials;
   lists effects that would stack). It is not a script to keep in the place.
3. Optional quick look: RR_FXDemo.client.lua as a LocalScript in StarterPlayerScripts (L look, T tunnel, B burst,
   1/2/3 speed notch, F flashes); remove it before publishing.
4. Game code (client): `VFX.setSpeed(speed, forward)` every notch change; `Lighting.apply(look)`;
   `Lighting.push("tunnel_under")` / `pop` from the streamer; `VFX.setFlashes(on)` + `Lighting.setFlashes(on)` from the
   players' flashes setting (av.feel.flash_limit, OQ-032). Priority-1 loops and presets marked start off begin OFF.
5. Budgets are {model.budget_raw.get('status', '')}. Textures are Roblox built-ins as placeholders; custom flipbooks need
   an asset upload (owner).

| preset | kind | anchor | wire it |
|---|---|---|---|
{rows}
"""
    (out / "README.md").write_text(readme, encoding="utf-8")
    print(f"wrote {len(files) + 1 + len(list((SKILL / 'assets' / 'luau').glob('*.lua')))} files to {out}")
    if a.no_check:
        print("checks skipped (--no-check)")
        return 0
    fails = 0
    for f in sorted(out.glob("*.lua")):
        ok, tool, msg = lua_syntax(f)
        fails += 0 if ok else 1
        print(f"syntax {'ok  ' if ok else 'FAIL'} {f.name} ({tool.split(' (')[0]}): {msg if not ok else ''}".rstrip(": "))
    if not find_luaparse():
        print("note: luaparse not found; ran the balance check only (npm i --prefix ~/.cache/rr-tools luaparse, or LUAPARSE_DIR)")
    allow = sorted({v["hex"].upper() for v in model.fx.values()})
    for f in sorted(out.glob("*.lua")):
        code, res = model.bible.check(f, allow=allow)
        errs = [x for x in res.get("findings", []) if x["level"] == "ERROR"]
        fails += 1 if errs else 0
        print(f"canon {'ok  ' if not errs else 'FAIL'} {f.name}: {res.get('ok', {}).get('colours', 0)} colours on canon"
              + (f"; {len(errs)} errors: " + "; ".join(x['msg'] for x in errs[:3]) if errs else ""))
    print(f"allowed effect colours (declared in fx_colours with reasons): {', '.join(allow) or 'none'}")
    print(f"build {'PASS' if not fails else 'FAIL'}: {out}")
    return 1 if fails else 0


# ------------------------------------------------------------------ commands
def fmt_typed(tv):
    t = tv[0]
    if t in ("num", "bool", "str", "enum", "color"):
        return tv[1]
    if t == "light":
        return tv[1]
    if t == "range":
        return [tv[1], tv[2]]
    if t in ("v2", "v3"):
        return list(tv[1:])
    if t == "nseq":
        return [list(k) if k[2] else list(k[:2]) for k in tv[1]]
    if t == "cseq":
        return [list(k) for k in tv[1]]
    return tv


def typed_to_plain(obj):
    if isinstance(obj, tuple) and obj and isinstance(obj[0], str) and obj[0] in ("num", "bool", "str", "enum", "color", "light", "range", "v2", "v3", "nseq", "cseq"):
        return fmt_typed(obj)
    if isinstance(obj, dict):
        return {k: typed_to_plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [typed_to_plain(v) for v in obj]
    return obj


def cmd_list(model, a):
    print(f"effects ({len(model.presets)}): priority 1 signal, 2 feedback, 3 ambience")
    for n, p in model.presets.items():
        c = preset_cost(model, n, "phone")
        tag = f" [{p['oq']}]" if p.get("oq") else ""
        live = c["steady"] or c["burst"]
        print(f"  {n:18} {p['kind']:5} p{p['priority']} @{p['anchor']:<11} phone live {live:5.0f}{tag}  {p['use'][:70]}")
    print(f"trails ({len(model.trails)}): {', '.join(model.trails)}")
    looks = model.looks()
    print(f"looks ({len(looks)}): " + ", ".join(looks))
    print(f"overrides: {', '.join(model.light_raw.get('overrides', {}))}")
    print(f"budget sets: {', '.join(model.budget_raw.get('sets', {}))}  ({model.budget_raw.get('status', '')})")
    return 0


def cmd_show(model, a):
    n = a.name
    if n in model.presets:
        obj = typed_to_plain(model.presets[n])
        obj["cost_phone"] = {k: round(v, 1) for k, v in preset_cost(model, n, "phone").items()}
    elif n in model.trails:
        obj = typed_to_plain(model.trails[n])
    else:
        try:
            obj = typed_to_plain(model.resolve_look(n))
        except KeyError as e:
            print(f"{e}; effects: {', '.join(model.presets)}; trails: {', '.join(model.trails)}", file=sys.stderr)
            return 1
    if a.json:
        print(json.dumps(obj, indent=1))
    else:
        for k, v in obj.items():
            if isinstance(v, dict):
                print(f"{k}:")
                for k2, v2 in v.items():
                    print(f"  {k2}: {json.dumps(v2)}")
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                print(f"{k}:")
                for item in v:
                    print("  - " + json.dumps(item))
            else:
                print(f"{k}: {json.dumps(v)}")
    return 0


def cmd_budget(model, a):
    sets = model.budget_raw.get("sets", {})
    names = a.sets or list(sets)
    tiers = ["phone", "pc"] if a.tier == "all" else [a.tier]
    fails = 0
    print(f"budgets: {model.budget_raw.get('status', '')}")
    for tier in tiers:
        print(f"-- {tier}")
        for s in names:
            if s not in sets:
                print(f"unknown set {s!r}; sets: {', '.join(sets)}")
                return 2
            tot = set_cost(model, sets[s]["presets"], tier)
            bad, checks = over_budget(model, tot, tier)
            fails += 1 if bad else 0
            summary = (f"steady {tot['steady']:.0f}, peak {tot['steady'] + tot['burst']:.0f}, emitters {tot['emitters']}, "
                       f"fill {tot['fill']:.0f}, lights {tot['lights']} ({tot['shadowed']} shadowed), beams {tot['beams']}, debris {tot['debris']}")
            print(f"{'OVER' if bad else 'ok  '} {s:14} {summary}")
            for what, v, lim in bad:
                print(f"     over: {what} {v:.0f} > {lim}")
    print(f"budget {'FAIL' if fails else 'PASS'}: {fails} set(s) over")
    return 1 if fails else 0


def cmd_preview(model, a):
    import preview  # local module, needs Pillow (and bpy for lighting)
    return preview.run(model, a)


def cmd_crit(model, a):
    import preview
    return preview.crit(model, a)


def cmd_init(a):
    d = Path(a.dir).resolve()
    if d == (SKILL / "presets").resolve():
        print("init: that is the shipped library; pick a work folder (a mission's src/fx, a trial folder)")
        return 2
    if any(d.glob("*.json")) and not a.force:
        print(f"init: {d} already has presets (edit them, or --force to overwrite with the shipped library)")
        return 2
    d.mkdir(parents=True, exist_ok=True)
    for f in (SKILL / "presets").glob("*.json"):
        shutil.copy2(f, d / f.name)
    print(f"work copy: {d}\nedit these, and pass --presets {d} to every vfx.py command (validate, budget, preview, crit, build)")
    return 0


def main(argv=None):
    global PRESETS_ARG
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--presets", help="preset folder to use (work copy); default $RR_VFX_PRESETS, else the shipped library")
    ap = argparse.ArgumentParser(prog="vfx.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                 parents=[common])
    sub = ap.add_subparsers(dest="cmd", metavar="COMMAND")
    s = sub.add_parser("init", help="copy the shipped presets to a work folder")
    s.add_argument("dir")
    s.add_argument("--force", action="store_true")
    sub.add_parser("list", help="presets, trails, looks, budget sets", parents=[common])
    s = sub.add_parser("show", help="one preset, trail or look", parents=[common])
    s.add_argument("name")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("validate", help="schema, ranges, canon, colours, OQs, budgets", parents=[common])
    s.add_argument("--strict", action="store_true", help="warnings fail too")
    s = sub.add_parser("budget", help="concurrency sets vs tier budgets", parents=[common])
    s.add_argument("sets", nargs="*")
    s.add_argument("--tier", choices=["phone", "pc", "all"], default="all")
    s = sub.add_parser("build", help="Luau export + gates", parents=[common])
    s.add_argument("--out", required=True)
    s.add_argument("--only", nargs="+", metavar="NAME", help="export a pack: these presets and looks (+ their fx_on)")
    s.add_argument("--no-check", action="store_true")
    s = sub.add_parser("preview", help="renders + POVs + board + facts.md", parents=[common])
    s.add_argument("what", choices=["lighting", "vfx", "all"])
    s.add_argument("names", nargs="*", help="looks (biome.time[+override][@camera]) and/or effect presets; default: the preview sets")
    s.add_argument("--out", required=True)
    s.add_argument("--quick", action="store_true", help="tiny renders for smoke tests (not for critique)")
    s.add_argument("--gif", action="store_true", help="also write motion GIFs of the effects for the owner")
    s.add_argument("--phone", default=None, help="looks to also render as the phone fallback (default: every named look, "
                   "else preview.phone_set)")
    s.add_argument("--samples", type=int, default=16)
    s = sub.add_parser("crit", help="prepare one multiuse-critic pass (Profile F)", parents=[common])
    s.add_argument("crit")
    s.add_argument("--pass", dest="pass_", type=int, default=1)
    s.add_argument("--from", dest="src", required=True, help="preview --out folder (uses its board/), or one group folder")
    s.add_argument("--group", default=None, help="pack, lighting or vfx (default: from the --from folder)")
    s.add_argument("--profile", default="F", help="rubric profile for critic_kit (F = effects and lighting; B is for UI)")
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 2
    if a.cmd == "init":
        return cmd_init(a)
    PRESETS_ARG = a.presets
    if not (presets_dir() / "vfx.json").is_file():
        print(f"no presets in {presets_dir()} (vfx.py init DIR makes a work copy)")
        return 2
    note = f"presets: {presets_dir()}" + (" (shipped library: read-only; `vfx.py init DIR` + --presets DIR before editing)"
                                          if shipped() else "")
    print(note, file=sys.stderr if getattr(a, "json", False) else sys.stdout)
    model = Model()
    return {"list": cmd_list, "show": cmd_show, "validate": lambda m, a: validate(m, a.strict), "budget": cmd_budget,
            "build": cmd_build, "preview": cmd_preview, "crit": cmd_crit}[a.cmd](model, a)


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    sys.exit(main())
