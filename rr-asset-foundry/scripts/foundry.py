#!/usr/bin/env python3
"""rr-asset-foundry: parametric Risky Rails asset families -> Roblox-ready variants.

  foundry.py list [--match TEXT]                  families and presets (match: words from a request)
  foundry.py show FAMILY                          params (type, range, default, canon source), groups, presets
  foundry.py plan FAMILY [VARIANT OPTIONS] [--json]   resolve canon + params, no Blender
  foundry.py make FAMILY [VARIANT OPTIONS] [--out DIR] [--renders full|thumb|none] [--force]
  foundry.py batch FAMILY [VARIANT OPTIONS] --vary K=a:b:step | K=a:b | K=x,y,z ... [--n N] [--mode grid|random]
                  [--out DIR] [--jobs J] [--timeout S] [--dry-run]      N variants + variant sheets + batch.md
  foundry.py sheet BATCH_DIR                      rebuild the variant sheets and batch.md
  foundry.py crit VARIANT_DIR [VARIANT_DIR ...] --crit CRIT [--pass N]   Profile A pass folder for multiuse-critic
  foundry.py verify VARIANT_DIR                   re-check an export folder (files, Lua syntax, canon gate)
  foundry.py new-family NAME                      scaffold families/NAME.py from the template

VARIANT OPTIONS: --preset P  --set KEY=VALUE (repeat)  --group GROUP=bible.token.key (repeat)  --params FILE.json
  (a plan.json works: rebuild or tweak an earlier variant)  --name AssetName  --seed N  --lod  --merge none|group
  --no-atlas  --blender PATH
Env: RR_BIBLE (bible.py), RR_CRITIC (multiuse-critic folder), RR_FOUNDRY_OUT (default out root, else ~/.rr-foundry),
RR_BLENDER (a blender binary when python3 has no bpy). Exit: 0 ok, 1 a check failed, 2 usage or canon error.
"""
import argparse, concurrent.futures as cf, datetime, hashlib, importlib.util, itertools, json, os, random, re
import shutil, subprocess, sys, threading, time

sys.dont_write_bytecode = True       # never leave __pycache__ in this or a sibling skill

ME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS, FAMILIES = os.path.join(ME, "scripts"), os.path.join(ME, "families")
FORGE = os.path.join(SCRIPTS, "forge.py")
NAME_RX = re.compile(r"^[A-Z][A-Za-z0-9]*$")
MATERIALS = set("""Plastic SmoothPlastic Neon Wood WoodPlanks Marble Slate Concrete Granite Brick Pebble Cobblestone
Rock Sandstone Basalt CrackedLava Limestone Pavement CorrodedMetal DiamondPlate Foil Metal Grass LeafyGrass Sand Fabric
Snow Mud Ground Asphalt Salt Ice Glacier Glass ForceField Cardboard Carpet CeramicTiles ClayRoofTiles RoofShingles
Leather Plaster Rubber""".split())
STAGE_TOKENS = {"rail": "style.ground.rail", "ballast": "style.ground.ballast",
                "dark": "style.thumb.dark", "vest": "style.brand.hazard_yellow", "skin": "style.thumb.skin"}
CANON_NUMS = {"tris_target": "tech.mesh.tris_target", "tris_cap": "tech.mesh.tris_cap", "eye_3p": "tech.camera.eye_3p",
              "eye_1p": "tech.camera.eye_1p", "fov_v": "tech.camera.fov_v", "avatar_h": "tech.units.avatar_h",
              "min_feature_px": "style.line.min_feature_px"}


def die(msg, code=2):
    print(msg, file=sys.stderr)
    e = SystemExit(code)
    e.msg = msg                      # batch catches refusals per variant instead of stopping
    raise e


# ---------- sibling skills (portable: env, sibling folder, ~/.claude/skills, /home/user) ----------

def find_skill(name, env):
    if os.environ.get(env):
        p = os.environ[env]
        return os.path.dirname(os.path.dirname(p)) if p.endswith(".py") else p
    cands = [os.path.join(os.path.dirname(ME), name)]
    for root in (os.path.expanduser("~/.claude/skills"), "/home/user"):
        for dp, dns, fns in os.walk(root):
            if dp.count(os.sep) - root.count(os.sep) >= 5:
                dns[:] = []
            dns[:] = [d for d in dns if not d.startswith(".") and d not in ("node_modules", "__pycache__")]
            if os.path.basename(dp) == name and "SKILL.md" in fns:
                cands.append(dp)
    for c in cands:
        if os.path.isfile(os.path.join(c, "SKILL.md")):
            return c
    return None


class Bible:
    """Reads rr-bible through its own script (never parses canon files itself)."""

    def __init__(self):
        root = find_skill("rr-bible", "RR_BIBLE")
        self.py = os.environ.get("RR_BIBLE") if (os.environ.get("RR_BIBLE") or "").endswith(".py") else \
            (os.path.join(root, "scripts", "bible.py") if root else None)
        if not self.py or not os.path.isfile(self.py):
            die("rr-bible not found (set RR_BIBLE=/path/to/bible.py). The foundry never guesses canon.")
        self._tok, self._files = None, {}

    def run(self, *args):
        r = subprocess.run([sys.executable, self.py, *args], capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr

    def tokens(self):
        if self._tok is None:
            code, out, err = self.run("tokens", "--format", "json")
            if code:
                die(f"bible tokens failed: {err.strip()}")
            self._tok = json.loads(out)
        return self._tok

    def fact(self, key):
        stem = key.split(".")[0]
        if stem not in self._files:
            code, out, _ = self.run("get", stem, "--json")
            self._files[stem] = {f["key"]: f for f in json.loads(out)} if code == 0 else {}
        return self._files[stem].get(key)

    def number(self, ref):
        """'@tech.units.gauge' or '@tech.units.building_door#1' -> (float, fact)."""
        key, _, idx = ref.lstrip("@").partition("#")
        f = self.fact(key)
        if not f:
            code, out, err = self.run("get", key)
            die(f"canon key {key} not found. {(out + err).strip()[:300]}\nRecord the gap: bible.py add-question ...")
        if f["status"] == "superseded":
            die(f"canon key {key} is superseded; the family must reference its replacement")
        nums = re.findall(r"-?\d+(?:\.\d+)?", f["value"])
        if not nums:
            die(f"canon key {key} = {f['value']!r} holds no number")
        return float(nums[int(idx or 0)]), f

    def colour(self, key):
        tok = self.tokens()
        if key in tok["colors"]:
            return tok["colors"][key], tok["status"].get(key, "?")
        f = self.fact(key)
        if f and f["status"] == "superseded":
            die(f"colour {key} is superseded ({f['note'][:80]}); pick its replacement")
        if f and re.match(r"^#[0-9A-Fa-f]{6}$", f["value"]):
            return f["value"].upper(), f["status"]
        die(f"colour token {key} not found in rr-bible. `bible.py search` for one, or propose it with add-fact.")


# ---------- families ----------

def family_names():
    return sorted(f[:-3] for f in os.listdir(FAMILIES) if f.endswith(".py") and not f.startswith("_"))


def load_family(name):
    path = os.path.join(FAMILIES, f"{name}.py")
    if not os.path.isfile(path):
        die(f"no family {name!r}; have: {', '.join(family_names())}")
    if FAMILIES not in sys.path:
        sys.path.insert(0, FAMILIES)
    spec = importlib.util.spec_from_file_location(f"family_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.__file_path__ = path
    for attr in ("FAMILY", "DESC", "PARAMS", "GROUPS", "PRESETS", "VIEW", "build"):
        if not hasattr(mod, attr):
            die(f"family {name} lacks {attr}")
    return mod


def spec_of(raw):
    kind = raw[0]
    if kind in ("float", "int"):
        return {"type": kind, "default": raw[1], "min": raw[2], "max": raw[3], "help": raw[4]}
    if kind == "choice":
        return {"type": kind, "default": raw[1], "choices": list(raw[2]), "help": raw[3]}
    if kind == "bool":
        return {"type": kind, "default": raw[1], "help": raw[2]}
    die(f"bad param spec {raw!r}")


def coerce(name, spec, v):
    t = spec["type"]
    try:
        if t == "float":
            v = round(float(v), 4)
        elif t == "int":
            v = int(float(v))
        elif t == "bool":
            v = v if isinstance(v, bool) else str(v).lower() in ("1", "true", "yes", "on")
        elif t == "choice":
            v = str(v)
    except ValueError:
        die(f"{name}: {v!r} is not a {t}")
    if t in ("float", "int") and not spec["min"] <= v <= spec["max"]:
        die(f"{name}={v} is outside {spec['min']}..{spec['max']} ({spec['help']})")
    if t == "choice" and v not in spec["choices"]:
        die(f"{name}={v} is not one of {', '.join(spec['choices'])}")
    return v


# ---------- plan ----------

def camel(*words):
    return "".join(w[:1].upper() + w[1:] for s in words for w in re.split(r"[^A-Za-z0-9]+", str(s)) if w)


def resolve(fam, a, bible, overrides=None, name=None, seed=None, out=None):
    """Build the frozen plan dict. overrides: extra {param: value} (batch)."""
    pfile = {}
    if getattr(a, "params", None):
        pfile = json.load(open(a.params))
    preset = (overrides or {}).get("preset") or getattr(a, "preset", None) or pfile.get("preset") \
        or getattr(fam, "DEFAULT_PRESET", None) or next(iter(fam.PRESETS))
    if preset not in fam.PRESETS:
        die(f"no preset {preset!r} in {fam.FAMILY}; have: {', '.join(fam.PRESETS)}")
    specs = {k: spec_of(v) for k, v in fam.PARAMS.items()}
    params, sources = {}, {}
    for k, s in specs.items():
        d = s["default"]
        if isinstance(d, str) and d.startswith("@"):
            val, f = bible.number(d)
            sources[k] = {"key": f["key"], "status": f["status"], "oq": re.findall(r"OQ-\d{3}", f.get("note", ""))}
            if "#" in d:
                sources[k]["index"] = int(d.split("#")[1])
            d = val
        params[k] = d
    layers = [fam.PRESETS[preset].get("params", {}), pfile.get("params", {}),
              dict(kv.split("=", 1) for kv in (getattr(a, "set", None) or [])), overrides or {}]
    for layer in layers:
        for k, v in layer.items():
            if k == "preset":
                continue
            if k not in specs:
                die(f"{fam.FAMILY} has no param {k!r}; params: {', '.join(specs)}")
            if k in sources and coerce(k, specs[k], v) != params[k]:
                sources.pop(k)             # overridden with a different value: no longer the canon value
            params[k] = v
    params = {k: coerce(k, specs[k], v) for k, v in params.items()}
    warnings = list(fam.validate(params, lambda key: bible.number("@" + key)[0])) if hasattr(fam, "validate") else []
    errors = [w for w in warnings if w.startswith("ERROR")]
    if errors:
        die(f"{fam.FAMILY}: " + "; ".join(errors))

    gtok = {g: spec[0] for g, spec in fam.GROUPS.items()}
    gtok.update(fam.PRESETS[preset].get("groups", {}))
    gtok.update({g: (v["token"] if isinstance(v, dict) else v) for g, v in pfile.get("groups", {}).items() if g in gtok})
    for kv in getattr(a, "group", None) or []:
        g, _, key = kv.partition("=")
        if g not in gtok:
            die(f"{fam.FAMILY} has no group {g!r}; groups: {', '.join(gtok)}")
        gtok[g] = key
    groups, palette = {}, []
    for g, spec in fam.GROUPS.items():
        if not NAME_RX.match(g):
            die(f"group name {g!r} must be CamelCase letters/digits")
        if spec[1] not in MATERIALS:
            die(f"group {g}: {spec[1]!r} is not a Roblox Material")
        hx, status = bible.colour(gtok[g])
        if status == "conflict":
            warnings.append(f"group {g} uses {gtok[g]} (conflict): assumed, see its OQ")
        groups[g] = {"token": gtok[g], "hex": hx, "status": status, "material": spec[1],
                     "reflectance": spec[2] if len(spec) > 2 else None}
        if hx not in palette:
            palette.append(hx)
    if len(palette) > 64:
        die(f"{len(palette)} colours; the 256 px atlas holds 64")
    cells = {g: palette.index(groups[g]["hex"]) for g in groups}

    opts = dict(getattr(fam, "OPTIONS", {}))
    opts.update({k: v for k, v in pfile.get("options", {}).items() if k in ("lod", "merge", "atlas")})
    asset = name or getattr(a, "name", None) or pfile.get("asset") or camel(fam.FAMILY, preset)
    if not NAME_RX.match(asset):
        die(f"asset name {asset!r} must be CamelCase letters and digits (it prefixes every part name)")
    view = dict(fam.VIEW)
    ground_key = view.pop("ground", "style.ground.pasture")
    stage = {k: bible.colour(v)[0] for k, v in STAGE_TOKENS.items() if k in ("rail", "ballast")}
    stage["ground"] = bible.colour(ground_key)[0]
    stage["avatar"] = {k: bible.colour(STAGE_TOKENS[k])[0] for k in ("dark", "vest", "skin")}
    amb = (bible.fact("tech.lighting.outdoor_ambient") or {}).get("value") or \
        die("canon key tech.lighting.outdoor_ambient not found (stage lighting reads it)")
    stage["ambient"] = [int(x) for x in re.findall(r"\d+", amb)[:3]]
    canon = {k: bible.number("@" + v)[0] for k, v in CANON_NUMS.items()}
    critic = find_skill("multiuse-critic", "RR_CRITIC")
    if not critic:
        die("multiuse-critic not found (set RR_CRITIC); its blender_kit.py builds the atlas and checks")
    root = out or getattr(a, "out", None) or (os.path.dirname(pfile["out"]) if pfile.get("out") else None) \
        or os.environ.get("RR_FOUNDRY_OUT") or os.path.expanduser("~/.rr-foundry")
    plan = {
        "asset": asset, "family": fam.FAMILY, "family_file": fam.__file_path__, "preset": preset,
        "preset_note": fam.PRESETS[preset].get("note", ""), "params": params, "param_sources": sources,
        "seed": int(next(v for v in (seed, getattr(a, "seed", None), pfile.get("seed"), 1) if v is not None)),
        "groups": groups, "palette": palette, "cells": cells, "view": view, "stage": stage, "canon": canon,
        "options": {"lod": bool(getattr(a, "lod", False) or opts.get("lod", False)),
                    "merge": getattr(a, "merge", None) or opts.get("merge", "none"),
                    "atlas": not getattr(a, "no_atlas", False) and opts.get("atlas", True),
                    "collide": opts.get("collide", True),
                    "renders": getattr(a, "renders", None) or "full"},
        "open": sorted(set(getattr(fam, "OPEN", [])) | {q for s in sources.values() for q in s["oq"]}),
        "warnings": warnings, "out": os.path.abspath(os.path.join(root, asset)),
        "critic_scripts": os.path.join(critic, "scripts"), "foundry_scripts": SCRIPTS,
    }
    fam_hash = hashlib.sha1(open(fam.__file_path__, "rb").read()).hexdigest()[:10]
    key = {k: plan[k] for k in ("asset", "params", "seed", "groups")}
    key["options"] = {k: v for k, v in plan["options"].items() if k != "renders"}   # renders are not identity
    plan["family_hash"] = fam_hash
    plan["hash"] = hashlib.sha1((fam_hash + json.dumps(key, sort_keys=True)).encode()).hexdigest()[:12]
    return plan


def plan_lines(plan):
    src = plan["param_sources"]
    ps = ", ".join(f"{k} {v}" + (f" [{src[k]['key']} {src[k]['status']}]" if k in src else "")
                   for k, v in plan["params"].items())
    gs = ", ".join(f"{g} {s['hex']}" for g, s in plan["groups"].items())
    lines = [f"{plan['asset']}: {plan['family']} preset {plan['preset']} seed {plan['seed']} -> {plan['out']}",
             f"params: {ps}", f"groups ({len(plan['palette'])} atlas cells): {gs}",
             f"options: {', '.join(f'{k} {v}' for k, v in plan['options'].items())}"]
    if plan["open"]:
        lines.append(f"open questions labelling this output: {', '.join(plan['open'])} (outputs are 'assumed' until decided)")
    lines += [f"WARNING: {w}" for w in plan["warnings"]]
    return lines


# ---------- forge + post checks ----------

_BPY = None


def blender_cmd(a):
    global _BPY
    exe = getattr(a, "blender", None) or os.environ.get("RR_BLENDER")
    if exe:
        return lambda plan, *x: [exe, "-b", "--factory-startup", "-P", FORGE, "--", plan, *x]
    if _BPY is None:
        _BPY = subprocess.run([sys.executable, "-c", "import bpy"], capture_output=True).returncode == 0
    if not _BPY:
        die("no Blender: `pip install bpy` (3.11) or pass --blender /path/to/blender (plan works without it)")
    return lambda plan, *x: [sys.executable, FORGE, plan, *x]


_LUAPARSE = []


def luaparse_js():
    if _LUAPARSE:
        return _LUAPARSE[0]
    _LUAPARSE.append(_find_luaparse())
    return _LUAPARSE[0]


def _find_luaparse():
    cands = [os.environ.get("LUAPARSE", "")]
    try:
        g = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, timeout=20).stdout.strip()
        cands.append(os.path.join(g, "luaparse", "luaparse.js"))
    except (OSError, subprocess.TimeoutExpired):
        pass
    for base in (os.path.expanduser("~"), "/tmp", os.path.dirname(ME)):
        for dp, dns, fns in os.walk(base):
            if dp.count(os.sep) - base.count(os.sep) >= 4:
                dns[:] = []
            if dp.endswith(os.path.join("node_modules", "luaparse")) and "luaparse.js" in fns:
                cands.append(os.path.join(dp, "luaparse.js"))
                dns[:] = []
    return next((c for c in cands if c and os.path.isfile(c)), None)


def lua_check(path):
    """(ok, tool, message). luaparse (Luau compound ops rewritten) when node + luaparse exist, else block balance."""
    src = open(path).read()
    js = shutil.which("node") and luaparse_js()
    if js:
        plain = re.sub(r"(\b[\w.]+)\s*([+\-*/])=\s*", r"\1 = \1 \2 ", src)
        code = f"const p=require({json.dumps(js)});try{{p.parse(require('fs').readFileSync(0,'utf8'));" \
               f"console.log('ok')}}catch(e){{console.log(e.message);process.exit(1)}}"
        r = subprocess.run(["node", "-e", code], input=plain, capture_output=True, text=True)
        return r.returncode == 0, "luaparse", r.stdout.strip()
    body = re.sub(r"--\[\[.*?\]\]|--[^\n]*", "", src, flags=re.S)
    body = re.sub(r'"(\\.|[^"\\])*"|\'(\\.|[^\'\\])*\'', '""', body)
    words = re.findall(r"\b(function|do|if|repeat|end|until)\b", body)
    opens = sum(w in ("function", "do", "if") for w in words)
    ok = opens == words.count("end") and words.count("repeat") == words.count("until") and \
        all(body.count(o) == body.count(c) for o, c in ("()", "[]", "{}"))
    return ok, "block-balance", f"{opens} blocks, {words.count('end')} ends"


def post(plan, res, bible):
    """Hard checks -> (fails, warns); also runs the canon gate and the Lua syntax check."""
    out, cn = plan["out"], plan["canon"]
    fails, warns = [], list(plan["warnings"])
    if res.get("names_bad"):
        fails.append(f"{len(res['names_bad'])} part names off the pattern: {res['names_bad'][:3]}")
    if res["tris"]["over_cap"]:
        fails.append(f"over the {cn['tris_cap']:.0f} tris cap: {res['tris']['over_cap']}")
    if res["tris"]["over_target"]:
        warns.append(f"over the {cn['tris_target']:.0f} tris target: {res['tris']['over_target'][:4]}")
    if not res["palette"]["ok"]:
        fails.append(f"verify_palette: {res['palette']}")
    bf = {k: v for k, v in res.get("backfaces", {}).items() if v}
    if bf:
        fails.append(f"back faces in view {bf} ({list(res.get('backface_parts', {}))[:3]})")
    if res.get("coplanar"):
        fails.append(f"{len(res['coplanar'])} coplanar overlaps (black in Cycles, z-fight in Roblox): {res['coplanar'][:3]}")
    if res.get("floating"):
        fails.append(f"{len(res['floating'])} floating parts: {res['floating'][:4]}")
    small = {k: v for k, v in res.get("features", {}).items() if v[0] < cn["min_feature_px"]}
    if small:
        warns.append(f"features under {cn['min_feature_px']:.0f} px at game distance: {small}")
    ri = res.get("reimport") or {}
    if ri.get("unit_warning"):
        fails.append(f"FBX reimport: {ri['unit_warning']} (size {ri.get('size')})")
    lod = res.get("lod1") or {}
    if lod.get("over_cap"):
        fails.append(f"LOD1 over the tris cap: {lod['over_cap']}")
    lua = os.path.join(out, "studio_setup.lua")
    checks = {}
    if os.path.isfile(lua):
        ok, tool, msg = lua_check(lua)
        checks["lua"] = f"{'ok' if ok else 'FAIL'} ({tool}: {msg})"
        if not ok:
            fails.append(f"studio_setup.lua syntax: {msg}")
        code, so, se = bible.run("check", lua, "--json")
        try:
            rep = json.loads(so)
        except ValueError:
            rep = {"raw": (so + se)[:200]}
        finds = "; ".join(f"L{f.get('line')} {f.get('msg')}" for f in rep.get("findings", [])[:2]) or json.dumps(rep)[:200]
        checks["bible_check"] = "PASS" if code == 0 else f"FAIL ({finds})"
        if code != 0:
            fails.append(f"bible check studio_setup.lua: {checks['bible_check']}")
    return fails, warns, checks


def write_reports(plan, res, fails, warns, checks, secs):
    out, a = plan["out"], plan["asset"]
    size = res["size"]
    status = "fail" if fails else "ok"
    man = {"asset": a, "family": plan["family"], "preset": plan["preset"], "hash": plan["hash"], "status": status,
           "made": datetime.datetime.now().isoformat(timespec="seconds"), "seconds": round(secs, 1),
           "params": plan["params"], "size_studs": size, "parts": res["parts"], "proxies": res["proxies"],
           "tris": res["tris"], "groups": res["groups"], "features": res.get("features", {}),
           "lod1": res.get("lod1"), "renders": res.get("renders", {}), "files": res.get("files", []),
           "checks": checks, "fails": fails, "warnings": warns, "open": plan["open"]}
    json.dump(man, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    src = plan["param_sources"]
    L = [f"# {a} (measured by rr-asset-foundry {datetime.date.today()})",
         f"- family {plan['family']}, preset {plan['preset']} ({plan['preset_note']}); seed {plan['seed']}",
         "- params: " + ", ".join(f"{k} {v}" + (f" ({src[k]['key']}, {src[k]['status']})" if k in src else "")
                                  for k, v in plan["params"].items()),
         f"- size, studs (Blender x, y, z-up): {size[0]} x {size[1]} x {size[2]}; in Studio X {size[0]}, "
         f"Y(up) {size[2]}, Z {size[1]}",
         f"- parts: {res['parts']} separate named <Asset>_<Part>_<Group>_<nn>; groups "
         + ", ".join(f"{g} {n}" for g, n in res["groups"].items()),
         f"- collision: {res['proxies']} box proxies (invisible, CanCollide true); visual parts CanCollide "
         f"{'false' if res['proxies'] or not plan['options']['collide'] else 'true'}",
         f"- tris: {res['tris']['total']:,} total; largest part {res['tris']['max_name']} {res['tris']['max_part']:,} "
         f"(target {plan['canon']['tris_target']:,.0f} / cap {plan['canon']['tris_cap']:,.0f} per MeshPart)",
         f"- palette atlas: {len(plan['palette'])} cells exact={res['palette']['cells_exact']}; {res['palette']['faces']} "
         f"faces, {res['palette']['spanning']} span cells, {res['palette']['near_edge']} near an edge, "
         f"{res['palette']['off_palette']} off-palette",
         "- colours (rr-bible tokens): " + ", ".join(f"{g} {s['token']} {s['hex']} {s['material']}"
                                                   for g, s in plan["groups"].items()),
         f"- back faces in view: {res.get('backfaces')}; coplanar overlaps: {len(res.get('coplanar', []))}; "
         f"floating parts: {len(res.get('floating', []))}",
         f"- game-distance spans (400 px view, key features >= {plan['canon']['min_feature_px']:.0f} px): "
         + (", ".join(f"{k} {v[0]} px" for k, v in res.get("features", {}).items()) or "none listed")]
    L += [f"- measured: {k}: {v}" for k, v in res.get("measures", {}).items()]
    if res.get("reimport"):
        r = res["reimport"]
        L.append(f"- FBX reimport: {r.get('meshes')} meshes, size {r.get('size')}, {r.get('tris')} tris, "
                 f"{r.get('unit_warning') or 'no unit warning'}")
    if res.get("lod1"):
        l1 = res["lod1"]
        L.append(f"- LOD1: {l1['parts']} parts (one per group), {l1['tris']:,} tris, {l1['dropped_details']} details dropped")
    L += [f"- Studio setup script: {v}" for k, v in checks.items() if k == "lua"]
    L += [f"- canon gate (bible check studio_setup.lua): {checks['bible_check']}"] if "bible_check" in checks else []
    if plan["open"]:
        L.append(f"- open questions: {', '.join(plan['open'])} (values labelled assumed/proposed until the owner decides)")
    L += [f"- FAIL: {f}" for f in fails] + [f"- warning: {w}" for w in warns]
    L.append("- not measured here: Studio import and the setup script (no Studio in the cloud; owner test)")
    open(os.path.join(out, "facts.md"), "w").write("\n".join(L) + "\n")
    fams = os.path.relpath(FAMILIES, ME)
    readme = [f"# {a} ({plan['family']}, preset {plan['preset']})",
              f"1. Studio > 3D Importer: import `{a}.fbx` (recolourable). Keep hierarchy; do NOT merge meshes. "
              f"Expected size X {size[0]} x Y(up) {size[2]} x Z {size[1]} studs; about 3.57x off = unit bug, fix the importer scale.",
              "2. Select the imported model, paste `studio_setup.lua` into the command bar: anchors, collision "
              "(invisible Collider_Proxy boxes), recolour groups.",
              f"3. Recolour: edit one GROUPS line (a group per material, e.g. {next(iter(plan['groups']))}) and re-run. "
              f"`{a}_atlas.fbx` + `palette.png` = palette-atlas look (set KEEP_ATLAS = true; Color is then hidden).",
              (f"4. `{a}_LOD1.fbx` = far-ground version (one part per group, no collision)." if res.get("lod1") else
               "4. No LOD1 file (make with --lod for a far-ground version)."),
              f"5. Vary it: `python3 <rr-asset-foundry>/scripts/foundry.py make {plan['family']} --params plan.json "
              f"--set KEY=VALUE --name NewName` ({fams}/{plan['family']}.py lists every param).",
              "Studio test pending (owner): nothing here was run in Studio."]
    if plan["open"]:
        readme.append(f"Open: {', '.join(plan['open'])}; colours/dimensions tied to them are assumptions.")
    open(os.path.join(out, "README.md"), "w").write("\n".join(readme) + "\n")
    return man


def make_one(plan, a, bible, force=False, quiet=False, timeout=None):
    out = plan["out"]
    mpath = os.path.join(out, "manifest.json")
    if os.path.isfile(mpath):
        old = json.load(open(mpath))
        if old.get("hash") == plan["hash"] and not force and old.get("status") in ("ok", "fail"):
            want = {"none": set(), "thumb": {"thumb", "game"}, "full": {"thumb", "game", "pov3p", "pov1p", "34", "side", "end"}}
            if not want[plan["options"]["renders"]] <= set(old.get("renders", {})):
                with open(os.path.join(out, "forge.log"), "a") as log:
                    subprocess.run(blender_cmd(a)(os.path.join(out, "plan.json"), "--render-only", plan["options"]["renders"]),
                                   stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
                old["renders"] = json.load(open(os.path.join(out, "result.json"))).get("renders", {})
                json.dump(old, open(mpath, "w"), indent=1)
            if not quiet:
                print(f"{plan['asset']}: up to date ({old['status']}), renders {', '.join(old.get('renders', {})) or 'none'}; {out}")
            return old
        if not force:
            die(f"{out} holds a different variant; pass --name NewName to keep both, or --force to replace it")
    if os.path.isdir(out) and force:
        shutil.rmtree(out)
    os.makedirs(out, exist_ok=True)
    ppath = os.path.join(out, "plan.json")
    json.dump(plan, open(ppath, "w"), indent=1)
    cmd = blender_cmd(a)(ppath)
    t = time.time()
    with open(os.path.join(out, "forge.log"), "w") as log:
        try:
            r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
            code = r.returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
    rpath = os.path.join(out, "result.json")
    if code != 0 or not os.path.isfile(rpath):
        tail = open(os.path.join(out, "forge.log")).read().splitlines()[-12:]
        man = {"asset": plan["asset"], "hash": plan["hash"], "status": "error", "fails": [f"forge exit {code}"],
               "log_tail": tail, "params": plan["params"]}
        json.dump(man, open(mpath, "w"), indent=1)
        if not quiet:
            print(f"{plan['asset']}: FORGE ERROR (exit {code}); last log lines:\n  " + "\n  ".join(tail))
        return man
    res = json.load(open(rpath))
    fails, warns, checks = post(plan, res, bible)
    man = write_reports(plan, res, fails, warns, checks, time.time() - t)
    if not quiet:
        print(f"{plan['asset']}: {man['status'].upper()} in {man['seconds']:.0f}s; {res['parts']} parts + "
              f"{res['proxies']} proxies, {res['tris']['total']:,} tris, size {res['size']} studs")
        for f in fails:
            print(f"  FAIL {f}")
        for w in warns[:4]:
            print(f"  warn {w}")
        print(f"  files: {out}/ (facts.md, README.md, {', '.join(res.get('files', [])[:4])} ...)")
    return man


# ---------- commands ----------

def cmd_list(a):
    words = set(re.findall(r"[a-z]+", (a.match or "").lower()))
    hits = 0
    for n in family_names():
        fam = load_family(n)
        tags = set(getattr(fam, "TAGS", [])) | {fam.FAMILY}
        if not words or words & {t for tag in tags for t in tag.split()}:
            hits += 1
            print(f"{n}: {fam.DESC}")
            print(f"  presets: {', '.join(fam.PRESETS)}")
    if not hits:
        print(f"no family matches {a.match!r} (have: {', '.join(family_names())}); a recurring asset gets one with "
              "`new-family`, a one-off goes to rr-mission-control")


def cmd_show(a):
    fam = load_family(a.family)
    print(f"{fam.FAMILY}: {fam.DESC}\nparams:")
    for k, raw in fam.PARAMS.items():
        s = spec_of(raw)
        rng = f"{s['min']}..{s['max']}" if "min" in s else ("|".join(s["choices"]) if "choices" in s else "true|false")
        print(f"  {k} ({s['type']} {rng}, default {s['default']}): {s['help']}")
    print("groups (recolour; bible token, Roblox material):")
    for g, spec in fam.GROUPS.items():
        print(f"  {g}: {spec[0]}, {spec[1]}" + (f", Reflectance {spec[2]}" if len(spec) > 2 else ""))
    print("presets:")
    for p, v in fam.PRESETS.items():
        print(f"  {p}: {v.get('note', '')} {json.dumps(v.get('params', {}))}"
              + (f" groups {json.dumps(v['groups'])}" if v.get("groups") else ""))
    if getattr(fam, "OPEN", None):
        print(f"open questions: {', '.join(fam.OPEN)}")


def cmd_plan(a):
    fam, bible = load_family(a.family), Bible()
    plan = resolve(fam, a, bible)
    if a.json:
        print(json.dumps(plan, indent=1))
    else:
        print("\n".join(plan_lines(plan)))


def cmd_make(a):
    fam, bible = load_family(a.family), Bible()
    plan = resolve(fam, a, bible)
    for line in plan_lines(plan)[3:]:
        print(line)
    man = make_one(plan, a, bible, force=a.force, timeout=a.timeout)
    sys.exit(0 if man["status"] == "ok" else 1)


def parse_vary(specs, fam):
    params = {k: spec_of(v) for k, v in fam.PARAMS.items()}
    out = {}
    for s in specs:
        k, _, rng = s.partition("=")
        if k != "preset" and k not in params:
            die(f"--vary {k}: no such param in {fam.FAMILY}")
        if k == "preset" or "," in rng or params[k]["type"] in ("choice", "bool"):
            vals = [v for v in rng.split(",") if v]
            out[k] = ("list", vals if k == "preset" else [coerce(k, params[k], v) for v in vals])
        elif ":" in rng:
            parts = [float(x) for x in rng.split(":")]
            out[k] = ("range", parts)
        else:
            out[k] = ("list", [coerce(k, params[k], rng)])
    return out, params


def expand(vary, params, mode, n, seed):
    rnd = random.Random(seed)

    def grid_values(k, v):
        if v[0] == "list":
            return v[1]
        lo, hi = v[1][0], v[1][1]
        step = v[1][2] if len(v[1]) > 2 else (hi - lo) / 3
        vals, x = [], lo
        while x <= hi + 1e-9:
            vals.append(round(x, 3))
            x += step
        return vals
    keys = list(vary)
    if mode == "grid":
        combos = [dict(zip(keys, c)) for c in itertools.product(*(grid_values(k, vary[k]) for k in keys))]
        if n and len(combos) > n:
            combos = sorted(rnd.sample(combos, n), key=lambda c: [str(c[k]) for k in keys])
        return combos
    combos = []
    for _ in range(n or 8):
        c = {}
        for k, v in vary.items():
            if v[0] == "list":
                c[k] = rnd.choice(v[1])
            else:
                x = rnd.uniform(v[1][0], v[1][1])
                c[k] = int(round(x)) if params.get(k, {}).get("type") == "int" else round(x, 1)
        combos.append(c)
    return combos


def label(i, combo):
    txt = f"v{i:03d} " + " ".join(f"{k[:10]} {v:g}" if isinstance(v, float) else f"{k[:10]} {v}" for k, v in combo.items())
    return re.sub(r"[=@]", " ", txt)[:40]


def cmd_batch(a):
    fam, bible = load_family(a.family), Bible()
    vary, pspecs = parse_vary(a.vary, fam)
    combos = expand(vary, pspecs, a.mode, a.n, a.seed or 1)
    base = a.name or camel(fam.FAMILY, a.preset or getattr(fam, "DEFAULT_PRESET", "") or "")
    root = a.out or os.environ.get("RR_FOUNDRY_OUT") or os.path.expanduser("~/.rr-foundry")
    bdir = os.path.abspath(os.path.join(root, f"batch-{base}"))
    a.renders = a.renders or "thumb"
    plans, refused = [], []
    for i, combo in enumerate(combos, 1):
        try:
            plan = resolve(fam, a, bible, overrides=combo, name=f"{base}V{i:03d}", seed=(a.seed or 1) + i, out=bdir)
        except SystemExit as e:
            if not getattr(e, "msg", None):
                raise
            refused.append({"id": f"v{i:03d}", "asset": f"{base}V{i:03d}", "vary": combo, "status": "refused",
                            "fails": [e.msg], "seconds": 0})
            continue
        plan["out"] = os.path.join(bdir, f"v{i:03d}")
        plans.append((i, combo, plan))
    if refused:
        print(f"{len(refused)} combinations refused at plan time (listed in batch.md); {len(plans)} to build")
    prior = [json.load(open(os.path.join(p[2]["out"], "manifest.json")))["seconds"] for p in plans
             if os.path.isfile(os.path.join(p[2]["out"], "manifest.json"))
             and "seconds" in json.load(open(os.path.join(p[2]["out"], "manifest.json")))]
    per = (sum(prior) / len(prior)) if prior else {"none": 4, "thumb": 8, "full": 30}[a.renders]
    print(f"batch {base}: {len(plans)} variants ({a.mode}), renders {a.renders}, about "
          f"{per * len(plans) / max(1, a.jobs) / 60:.1f} min at {per:.0f}s each, jobs {a.jobs} -> {bdir}")
    if a.dry_run:
        for i, combo, plan in plans:
            print(f"  v{i:03d} {json.dumps(combo)}")
        return
    os.makedirs(bdir, exist_ok=True)
    state = {"family": fam.FAMILY, "base": base, "vary": a.vary, "mode": a.mode, "seed": a.seed or 1,
             "preset": a.preset, "sets": a.set or [], "renders": a.renders, "variants": list(refused)}
    json.dump(state, open(os.path.join(bdir, "batch.json"), "w"), indent=1)
    lock = threading.Lock()

    def one(item):
        i, combo, plan = item
        man = make_one(plan, a, bible, force=a.force, quiet=True, timeout=a.timeout)
        with lock:
            row = {"id": f"v{i:03d}", "asset": plan["asset"], "vary": combo, "status": man["status"],
                   "fails": man.get("fails", []), "seconds": man.get("seconds")}
            state["variants"] = [r for r in state["variants"] if r["id"] != row["id"]] + [row]
            state["variants"].sort(key=lambda r: r["id"])
            json.dump(state, open(os.path.join(bdir, "batch.json"), "w"), indent=1)
            print(f"  {row['id']} {man['status']}" + (f": {row['fails'][0][:90]}" if row["fails"] else ""), flush=True)
    with cf.ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
        list(ex.map(one, plans))
    sheet(bdir)


def sheet(bdir):
    st = json.load(open(os.path.join(bdir, "batch.json")))
    critic = find_skill("multiuse-critic", "RR_CRITIC")
    cs = os.path.join(critic, "scripts", "contact_sheet.py")
    rows, items = [], []
    for r in st["variants"]:
        vdir = os.path.join(bdir, r["id"])
        mp = os.path.join(vdir, "manifest.json")
        man = json.load(open(mp)) if os.path.isfile(mp) else {"status": r["status"] if r["status"] == "refused" else "missing",
                                                               "fails": r.get("fails", [])}
        thumb = os.path.join(vdir, "renders", "thumb.png")
        lab = label(int(r["id"][1:]), r["vary"]) + (" FAIL" if man["status"] != "ok" else "")
        if os.path.isfile(thumb):
            items.append(f"{lab}={thumb}")
        t = man.get("tris", {}).get("total", "")
        rows.append(f"| {r['id']} | {', '.join(f'{k} {v}' for k, v in r['vary'].items())} | {man['status']} | "
                    f"{man.get('parts', '')} | {t} | {' x '.join(str(s) for s in man.get('size_studs', []))} | "
                    f"{(man.get('fails') or [''])[0][:70]} |")
    for old in os.listdir(bdir):
        if re.match(r"sheet-\d+\.(png|json)$", old):
            os.remove(os.path.join(bdir, old))
    sheets, queue = [], [items[i:i + 16] for i in range(0, len(items), 16)]
    while queue:                     # an oversized sheet (the packer went tall) is split in two and redone
        chunk = queue.pop(0)
        out = os.path.join(bdir, f"sheet-{len(sheets) + 1}.png")
        r = subprocess.run([sys.executable, cs, out, *chunk, "--tile", "320x180"], capture_output=True, text=True)
        if r.returncode == 2 and len(chunk) > 1:
            queue[:0] = [chunk[:(len(chunk) + 1) // 2], chunk[(len(chunk) + 1) // 2:]]
            continue
        sheets.append(f"sheet-{len(sheets) + 1}.png" + ("" if r.returncode == 0 else f" (contact_sheet exit {r.returncode})"))
    ok = sum(1 for r in st["variants"] if r["status"] == "ok")
    md = [f"# Batch {st['base']} ({st['family']}, {st['mode']}, {len(st['variants'])} variants, {ok} pass checks)",
          f"vary: {' '.join(st['vary'])}; preset {st.get('preset') or 'default'}; sets {st.get('sets') or 'none'}",
          f"sheets: {', '.join(sheets) or 'none (no thumbnails)'}. Each thumbnail is framed to its variant; the "
          "5-stud avatar is the scale reference and sizes are below. Pick by eye, or hand picks to multiuse-critic "
          "(`foundry.py crit`); the checks here are objective only, never a look score.", "",
          "| id | varied | status | parts | tris | size (x y z) | first fail |", "|---|---|---|---|---|---|---|"] + rows
    open(os.path.join(bdir, "batch.md"), "w").write("\n".join(md) + "\n")
    print(f"batch.md + {len(sheets)} sheet(s) in {bdir}: {ok}/{len(st['variants'])} pass objective checks")


def cmd_sheet(a):
    sheet(os.path.abspath(a.batch_dir))


def cmd_crit(a):
    bible = Bible()
    critic = find_skill("multiuse-critic", "RR_CRITIC")
    cs = os.path.join(critic, "scripts", "contact_sheet.py")
    crit = os.path.abspath(a.crit)
    pdir = os.path.join(crit, f"pass-{a.pass_}")
    os.makedirs(pdir, exist_ok=True)
    band, grid, close, facts, mans = [], [], [], [], []
    multi = len(a.variants) > 1
    for v in a.variants:
        v = os.path.abspath(v)
        plan, man = json.load(open(os.path.join(v, "plan.json"))), json.load(open(os.path.join(v, "manifest.json")))
        need = ["pov3p", "game", "pov1p", "34", "side", "end"] + (["top"] if plan["view"].get("top") else [])
        if any(not os.path.isfile(os.path.join(v, "renders", f"{n}.png")) for n in need):
            print(f"{plan['asset']}: rendering the full critic set ...", flush=True)
            with open(os.path.join(v, "forge.log"), "a") as log:
                r = subprocess.run(blender_cmd(a)(os.path.join(v, "plan.json"), "--render-only", "full"),
                                   stdout=log, stderr=subprocess.STDOUT)
            if r.returncode:
                die(f"render-only failed for {v}; see forge.log", 1)
        pre = f"{plan['asset']}_" if multi else ""
        for n in need:
            shutil.copy(os.path.join(v, "renders", f"{n}.png"), os.path.join(pdir, f"{pre}{n}.png"))
        tag = f"{plan['asset']} " if multi else ""
        if multi:
            band.append(f"{tag}game 400px={os.path.join(pdir, pre + 'game.png')}@1")
            close.append(f"{tag}POV 3P={os.path.join(pdir, pre + 'pov3p.png')}@1")
        else:
            band += [f"POV 3P={os.path.join(pdir, 'pov3p.png')}@1", f"game 400px={os.path.join(pdir, 'game.png')}@1"]
        grid += [f"{tag}{lab}={os.path.join(pdir, pre + n + '.png')}"
                 for n, lab in (("pov1p", "POV 1P"), ("34", "3/4"), ("side", "side"), ("end", "end"), ("top", "top"))
                 if n in need]
        facts.append(open(os.path.join(v, "facts.md")).read().strip())
        mans.append((plan, man))
    for tile in ("320x180", "288x162", "256x144"):
        r = subprocess.run([sys.executable, cs, os.path.join(pdir, "contact.png"), *band, *grid, "--tile", tile],
                           capture_output=True, text=True)
        if r.returncode == 0:
            break
    if r.returncode:
        die(f"contact sheet over budget even at 256x144: {r.stdout[-300:]}", 1)
    extra = ""
    if close:
        rc = subprocess.run([sys.executable, cs, os.path.join(pdir, "closeups.png"), *close], capture_output=True, text=True)
        extra = " --images closeups.png" if rc.returncode == 0 else ""
    open(os.path.join(pdir, "facts.md"), "w").write("\n\n".join(facts) + "\n")
    brief = os.path.join(crit, "brief.md")
    if not os.path.isfile(brief):
        plan0, _ = mans[0]
        fam = load_family(plan0["family"])
        aud = [bible.fact(k) for k in ("identity.audience.launch", "identity.audience.target")]
        cn = plan0["canon"]
        opens = sorted({q for p, _ in mans for q in p["open"]})
        names = ", ".join(p["asset"] for p, _ in mans)
        open(brief, "w").write("\n".join([
            f"# {names}",
            f"- Purpose: {fam.DESC} Variant(s): " + "; ".join(f"{p['asset']} = preset {p['preset']} ({p['preset_note']})" for p, _ in mans),
            "- Audience: " + "; ".join(f["value"] for f in aud if f),
            f"- Player view: third-person eye {cn['eye_3p']:g} studs above the floor, first-person {cn['eye_1p']:g}, "
            f"vertical FOV {cn['fov_v']:g}. {fam.VIEW.get('player', '')}",
            "- Stage: generated draft (parametric: fixes are parameter or family-code changes, then a rebuild).",
            f"- Fixed constraints: <= {cn['tris_target']:,.0f} tris per MeshPart (cap {cn['tris_cap']:,.0f}); colours only "
            "rr-bible tokens (listed in facts); separate named parts per recolour group; invisible box collision proxies.",
            f"- Owner worries / decided: open questions {', '.join(opens) or 'none'} (their values are assumptions, not "
            "style choices to critique). Step 2 NOT answered by the foundry: ask the owner or pre-answer before pass 1."]) + "\n")
    print(f"pass folder ready: {pdir} (contact.png{', closeups.png' if extra else ''}, facts.md); brief: {brief}")
    print(f"next: python3 {os.path.join(critic, 'scripts', 'critic_kit.py')} build {crit} --pass {a.pass_} --kind full "
          f"--profile A --role \"senior game artist\"{extra}")
    print("then a fresh critic per multiuse-critic steps 5-6; the foundry never scores.")


def cmd_verify(a):
    v = os.path.abspath(a.variant_dir)
    man = json.load(open(os.path.join(v, "manifest.json")))
    plan = json.load(open(os.path.join(v, "plan.json")))
    plan["out"] = v                     # check the folder given (it may be a copy), not where it was made
    missing = [f for f in man.get("files", []) + ["studio_setup.lua", "parts.csv", "facts.md", "README.md"]
               if not os.path.isfile(os.path.join(v, f))]
    res = json.load(open(os.path.join(v, "result.json")))
    fails, warns, checks = post(plan, res, Bible())
    fails += [f"missing file {f}" for f in missing]
    print(f"{man['asset']}: {'PASS' if not fails else 'FAIL'}; {len(man.get('files', [])) - len(missing)} export files present"
          f"; lua {checks.get('lua')}; canon gate {checks.get('bible_check', 'not run')[:4]}")
    for f in fails:
        print(f"  FAIL {f}")
    sys.exit(1 if fails else 0)


def cmd_new_family(a):
    name = a.name.lower()
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        die("family names are lower_case")
    dst = os.path.join(FAMILIES, f"{name}.py")
    if os.path.exists(dst):
        die(f"{dst} exists")
    src = open(os.path.join(FAMILIES, "_template.py")).read()
    open(dst, "w").write(src.replace("TEMPLATE_NAME", name).replace("TemplateName", camel(name)))
    print(f"wrote {dst}: fill PARAMS, GROUPS (bible tokens), PRESETS, VIEW and build(); then `foundry.py plan {name}` "
          f"and `make {name} --renders thumb` (references/families.md has the rules)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def variant_opts(p, renders_default=None):
        p.add_argument("family")
        p.add_argument("--preset")
        p.add_argument("--set", action="append", help="KEY=VALUE, repeatable")
        p.add_argument("--group", action="append", help="GROUP=bible.token.key, repeatable")
        p.add_argument("--params", help="JSON with params (a plan.json works)")
        p.add_argument("--name")
        p.add_argument("--seed", type=int)
        p.add_argument("--lod", action="store_true")
        p.add_argument("--merge", choices=["none", "group"])
        p.add_argument("--no-atlas", action="store_true")
        p.add_argument("--out")
        p.add_argument("--renders", choices=["full", "thumb", "none"], default=renders_default)
        p.add_argument("--blender")
        p.add_argument("--force", action="store_true")
        p.add_argument("--timeout", type=int, default=1800)
    p = sub.add_parser("list")
    p.add_argument("--match")
    p = sub.add_parser("show")
    p.add_argument("family")
    p = sub.add_parser("plan")
    variant_opts(p)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("make")
    variant_opts(p)
    p = sub.add_parser("batch")
    variant_opts(p)
    p.add_argument("--vary", action="append", required=True)
    p.add_argument("--n", type=int)
    p.add_argument("--mode", choices=["grid", "random"], default="grid")
    p.add_argument("--jobs", type=int, default=1)
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("sheet")
    p.add_argument("batch_dir")
    p = sub.add_parser("crit")
    p.add_argument("variants", nargs="+")
    p.add_argument("--crit", required=True)
    p.add_argument("--pass", dest="pass_", type=int, default=1)
    p.add_argument("--blender")
    p = sub.add_parser("verify")
    p.add_argument("variant_dir")
    p = sub.add_parser("new-family")
    p.add_argument("name")
    a = ap.parse_args()
    {"list": cmd_list, "show": cmd_show, "plan": cmd_plan, "make": cmd_make, "batch": cmd_batch, "sheet": cmd_sheet,
     "crit": cmd_crit, "verify": cmd_verify, "new-family": cmd_new_family}[a.cmd](a)


if __name__ == "__main__":
    main()
