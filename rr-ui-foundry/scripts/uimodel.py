#!/usr/bin/env python3
"""rr-ui-foundry shared model: canon via rr-bible, kit data (roles, templates), spec expansion, the layout
resolver, the HUD stack policy, the gamepad nav graph and every check. ui.py (boards, export) and luatest.py
(parity) both import it, so the HTML boards and the Luau package come from the same numbers.

Not a CLI; run `python3 uimodel.py --help` for this text. Standard library only.
"""
import copy, json, math, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
KIT_DIR = SKILL / "kit"
NUM = re.compile(r"-?\d+(?:\.\d+)?")
EXPR = re.compile(r"^\s*(-?\d+(?:\.\d+)?)%\s*(?:([+-])\s*(\d+(?:\.\d+)?))?\s*$")
SLOT = re.compile(r"\{([a-zA-Z_][\w]*)(?:\|(lower|upper))?\}")
PINS = {"tl": (0, 0), "tc": (0.5, 0), "tr": (1, 0), "cl": (0, 0.5), "cc": (0.5, 0.5), "cr": (1, 0.5),
        "bl": (0, 1), "bc": (0.5, 1), "br": (1, 1)}
TYPES = ("frame", "text", "image", "hit", "stack")
NODE_KEYS = {"id", "type", "use", "variant", "slots", "rect", "pin", "stretch", "layer", "z", "visible", "if", "unless",
             "rot", "alpha", "fill", "gradient", "stroke", "radius", "clip", "pattern", "text", "style", "color",
             "align", "valign", "wrap", "truncate", "image", "tint", "gamepad_only", "feel", "comp", "action", "hint",
             "bar", "children", "states", "content", "repeat", "on", "avoid", "stack", "note", "canon_text"}
INSET_MODES = ("CoreUISafeInsets", "DeviceSafeInsets", "None")
WEIGHTS = {100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold",
           700: "Bold", 800: "ExtraBold", 900: "Heavy"}


def _walk_find(root, name, maxdepth=5):
    out, root = [], Path(root)
    if not root.is_dir():
        return out
    base = len(root.parts)
    for dirpath, dirs, files in os.walk(root):
        p = Path(dirpath)
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


class SpecError(Exception):
    """A spec that cannot be read: the CLI prints it as one line."""


class Bible:
    """Canon through rr-bible's CLI (its stable interface): one call per domain file, cached."""

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

    def fact(self, key):
        stem = key.split(".")[0]
        if stem not in self._files:
            code, out = self.run("get", stem, "--json")
            try:
                self._files[stem] = {f["key"]: f for f in json.loads(out)} if code == 0 else {}
            except ValueError:
                self._files[stem] = {}
        return self._files[stem].get(key)

    def value(self, key, default=None):
        f = self.fact(key)
        return f["value"] if f else default

    def oq(self, oid):
        """An open question as rr-bible's JSON; a decided one follows its D-nnn and gets status 'decided',
        'decided' (the D id) and 'choice' (the option letter), so a spec citing it stays valid."""
        if oid not in self._oq:
            code, out = self.run("get", oid, "--json")
            q, m = None, re.match(r"\s*(OQ-\d+) was decided: see (D-\d+)", out)
            if code == 0 and m:
                d = self._json(*self.run("get", m[2], "--json"))
                if d:
                    dec = str(d.get("fields", {}).get("decision", ""))
                    c = re.match(r"\s*([A-Za-z0-9]+)\s*:", dec)
                    q = {"id": oid, "title": d.get("title", ""), "options": [], "decided": m[2], "choice": c[1] if c else None,
                         "fields": dict(d.get("fields", {}), status="decided", default=dec)}
            elif code == 0:
                q = self._json(code, out)
            self._oq[oid] = q
        return self._oq[oid]

    @staticmethod
    def _json(code, out):
        try:
            return json.loads(out) if code == 0 else None
        except ValueError:
            return None


# ------------------------------------------------------------------ small helpers
def ev(v, size):
    """A rect component: a number (px) or "P%", "P%+N", "P%-N" of the parent size."""
    if isinstance(v, (int, float)):
        return float(v)
    m = EXPR.match(str(v))
    if not m:
        raise ValueError(f"bad rect value {v!r} (use px or 'P%[+-N]')")
    off = float(m[3] or 0) * (-1 if m[2] == "-" else 1)
    return float(m[1]) / 100.0 * size + off


def fill_slots(s, slots, keep_unknown=True):
    if not isinstance(s, str):
        return s

    def rep(m):
        if m[1] not in slots or slots[m[1]] is None:
            return m[0] if keep_unknown else ""
        v = slots[m[1]]
        v = ("" if v is False else str(v)) if not isinstance(v, (int, float)) or isinstance(v, bool) else \
            (str(int(v)) if float(v).is_integer() else str(v))
        return v.lower() if m[2] == "lower" else v.upper() if m[2] == "upper" else v
    return SLOT.sub(rep, s)


def has_slots(s):
    return isinstance(s, str) and bool(SLOT.search(s))


def cond_ok(expr, slots):
    if expr is None:
        return True
    if "=" in expr:
        k, v = expr.split("=", 1)
        return str(slots.get(k.strip(), "")).lower() == v.strip().lower()
    v = slots.get(expr.strip())
    return bool(v) and v not in ("0", 0, "false")


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(rgb):
    c = [v / 255 for v in rgb]
    c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    x, y = lum(hex_rgb(a)), lum(hex_rgb(b))
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


def blend(fg, bg, alpha):
    f, b = hex_rgb(fg), hex_rgb(bg)
    return "#%02X%02X%02X" % tuple(round(f[i] * alpha + b[i] * (1 - alpha)) for i in range(3))


def lab(h):
    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    r, g, b = [((v / 255 + 0.055) / 1.055) ** 2.4 if v / 255 > 0.04045 else v / 255 / 12.92 for v in hex_rgb(h)]
    x, y, z = (r * .4124 + g * .3576 + b * .1805) / .95047, r * .2126 + g * .7152 + b * .0722, (r * .0193 + g * .1192 + b * .9505) / 1.08883
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def delta_e(a, b):
    return math.dist(lab(a), lab(b))


def inter(a, b):
    """Overlap box of two (x, y, w, h) rects, or None."""
    x, y = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[0] + a[2], b[0] + b[2]), min(a[1] + a[3], b[1] + b[3])
    return (x, y, x2 - x, y2 - y) if x2 - x > 0.01 and y2 - y > 0.01 else None


def wh(value):
    m = re.search(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)", str(value or ""))
    return (float(m[1]), float(m[2])) if m else None


# ------------------------------------------------------------------ devices
class Device:
    def __init__(self, name, screen, insets, display, inp, design=False):
        self.name, self.screen, self.insets, self.display, self.input, self.design = name, screen, insets, display, inp, design

    def area(self, mode):
        W, H = self.screen
        t, l, r, b = (self.insets.get(k, 0) for k in ("top", "left", "right", "bottom"))
        if mode == "None":
            return (0.0, 0.0, W, H)
        if mode == "DeviceSafeInsets":
            return (l, 0.0, W - l - r, H - b)
        return (l, t, W - l - r, H - t - b)

    @property
    def touch(self):
        return self.input == "Touch"


# ------------------------------------------------------------------ kit (canon-resolved)
class Kit:
    """roles.json + components.json resolved against rr-bible. Problems land in .errors / .warnings."""

    def __init__(self, bible=None, kit_dir=None):
        self.b = bible or Bible()
        d = Path(kit_dir or os.environ.get("RR_UI_KIT") or KIT_DIR)
        self.dir = d
        self.roles = json.loads((d / "roles.json").read_text(encoding="utf-8"))
        self.comps = {k: v for k, v in json.loads((d / "components.json").read_text(encoding="utf-8")).items()
                      if not k.startswith("_")}
        self.errors, self.warnings, self.cites = [], [], set()
        if not self.b.ok():
            self.errors.append("rr-bible not found: canon cannot be read (set RR_BIBLE_SKILL)")
            return
        R = self.roles
        self.skins = list(R["skins"])
        self.default_skin, self.skin_oq = R["default_skin"], R.get("skin_oq")
        q = self.b.oq(self.skin_oq) if self.skin_oq else None
        self.skin_decided = q.get("decided") if q and q.get("choice") in self.skins else None
        if self.skin_decided:
            self.default_skin = q["choice"]
        self.skin_status = (f"decided: {self.default_skin} ({self.skin_decided})" if self.skin_decided
                            else f"assumed ({self.skin_oq} default)")
        self.colors = {s: {} for s in self.skins}
        for role, m in R["roles"].items():
            for s in self.skins:
                key = m.get(s)
                f = self.b.fact(key) if key else None
                if not f or not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(f["value"])):
                    self.errors.append(f"role {role} skin {s}: {key} is not a colour token in rr-bible")
                    continue
                if f["status"] == "superseded":
                    self.errors.append(f"role {role} skin {s}: {key} is superseded")
                self.colors[s][role] = {"hex": f["value"].upper(), "key": key, "status": f["status"]}
        self.fonts = {}
        for fam_role, key in R["fonts"].items():
            v = self.b.value(key)
            if not v:
                self.errors.append(f"font {fam_role}: {key} missing in rr-bible")
            self.fonts[fam_role] = {"name": v or "?", "key": key, "roblox": self._roblox_font(v or "")}
        self.types = {}
        for name, t in R["type"].items():
            self.types[name] = dict(t, size=self.num(t["size"], f"type {name}"), weight=int(t.get("weight", 400)))
        mt = R["min_text"]
        v = self.b.value(mt["canon"]) or ""
        self.min_text = {}
        for fam, rx in mt["parse"].items():
            m = re.search(rx, v)
            if not m:
                self.errors.append(f"min text: '{rx}' not found in {mt['canon']} ({v!r})")
            self.min_text[fam] = float(m[1]) if m else 12.0
        self.cites.add(mt["canon"])
        self.devices = {}
        for name, dv in R["devices"].items():
            scr = wh(self.b.value(dv["screen"]))
            if not scr:
                self.errors.append(f"device {name}: {dv['screen']} has no 'W x H' in rr-bible")
                scr = (844.0, 390.0)
            ins = {}
            for side, key in dv.get("insets", {}).items():
                m = NUM.search(str(self.b.value(key) or ""))
                if not m:
                    self.errors.append(f"device {name}: inset {key} missing in rr-bible")
                ins[side] = float(m[0]) if m else 0.0
                self.cites.add(key)
            self.cites.add(dv["screen"])
            self.devices[name] = Device(name, scr, ins, dv["display"], dv["input"], dv.get("design", False))
        self.design_device = next((d for d in self.devices.values() if d.design), self.devices.get("phone"))
        self.density = {}
        for disp, dn in R["density"].items():
            if "canon" in dn:
                m = re.search(dn["parse"], str(self.b.value(dn["canon"]) or ""))
                if not m:
                    self.errors.append(f"density {disp}: '{dn['parse']}' not found in {dn['canon']}")
                    self.density[disp] = 1.0
                    continue
                self.cites.add(dn["canon"])
                self.density[disp] = round(float(m[1]) / self.fit(self.devices[dn["device"]], "CoreUISafeInsets"), 4)
            else:
                self.density[disp] = float(dn.get("fit", 1.0))
        Z = R["zones"]
        self.zone = {"small_screen": float(NUM.search(str(self.b.value(Z["small_screen"]) or "500"))[0])}
        for z in ("jump", "stick"):
            self.zone[z] = {k: wh(self.b.value(Z[z][k])) for k in ("small", "large")}
            self.zone[z]["corner"] = Z[z]["corner"]
            for k in ("small", "large"):
                if not self.zone[z][k]:
                    self.errors.append(f"zone {z}.{k}: {Z[z][k]} missing in rr-bible")
                    self.zone[z][k] = (140.0, 140.0)
        m = re.search(r"left (\d+)% x bottom (\d+)/(\d+)", str(self.b.value(Z["stick_area"]) or ""))
        self.zone["stick_area"] = (int(m[1]) / 100, int(m[2]) / int(m[3])) if m else (0.4, 2 / 3)
        self.touch_target = float(NUM.search(str(self.b.value(Z["touch_target"]) or "44"))[0])
        self.cites.update([Z["small_screen"], Z["stick_area"], Z["touch_target"]])

    # canon numbers: {"v": n, "canon": key, "scale": k} -> n * k, after proving n appears in the fact
    def num(self, node, where):
        if isinstance(node, (int, float)):
            return float(node)
        if isinstance(node, dict) and "v" in node and "canon" in node:
            f = self.b.fact(node["canon"])
            self.cites.add(node["canon"])
            if not f:
                self.errors.append(f"{where}: canon key {node['canon']} not in rr-bible")
            elif not any(abs(float(x) - float(node["v"])) < 1e-9 for x in NUM.findall(str(f["value"]))):
                self.errors.append(f"{where}: {node['v']} does not appear in {node['canon']} = {f['value']!r}")
            return float(node["v"]) * float(node.get("scale", 1))
        self.errors.append(f"{where}: expected a number or {{v, canon}}, got {node!r}")
        return 0.0

    def _roblox_font(self, name):
        expr = str(self.b.value("tech.ui_platform.fonts") or "")
        squash = re.sub(r"\s+", "", name)
        m = re.search(r"Enum\.Font\.(%s)\b" % re.escape(squash), expr)
        if m:
            return {"enum": m[1]}
        m = re.search(r'Font\.new\("([^"]*%s[^"]*\.json)"' % re.escape(squash), expr)
        if m:
            return {"family": m[1]}
        self.warnings.append(f"font {name}: no Roblox expression in tech.ui_platform.fonts; guessing the family path")
        return {"family": f"rbxasset://fonts/families/{squash}.json", "guess": True}

    def fit(self, dev, mode, design_mode=None):
        ax, ay, aw, ah = dev.area(mode)
        _, _, dw, dh = self.design_device.area(design_mode or mode)
        return min(aw / dw, ah / dh)

    def skin_label(self, skin):
        """'decided: A (D-023)', 'assumed (OQ-001 default)' or 'option B (OQ-001 open)' / '(not chosen)'."""
        if skin == self.default_skin:
            return self.skin_status
        return f"option {skin} ({'not chosen, ' + self.skin_decided if self.skin_decided else self.skin_oq + ' open'})"

    def color(self, skin, role):
        c = self.colors.get(skin, {}).get(role)
        return c["hex"] if c else None

    def zones_for(self, dev):
        """Touch zones in screen px for a touch device: jump, stick ring, stick area (all in the core area)."""
        if not dev.touch:
            return {}
        ax, ay, aw, ah = dev.area("CoreUISafeInsets")
        size = "small" if min(aw, ah) <= self.zone["small_screen"] else "large"
        out = {}
        for z in ("jump", "stick"):
            zw, zh = self.zone[z][size]
            x = ax + aw - zw if self.zone[z]["corner"] == "br" else ax
            out[z] = (x, ay + ah - zh, zw, zh)
        fw, fh = self.zone["stick_area"]
        out["stick_area"] = (ax, ay + ah * (1 - fh), aw * fw, ah * fh)
        out["_size"] = size
        return out


# ------------------------------------------------------------------ template expansion
def _qualify(inst, pid):
    return f"{inst}.{pid}" if inst else pid


def expand_parts(kit, parts, pw, ph, slots, inst, static, errs, where):
    out = []
    for p in parts:
        if static and not (cond_ok(p.get("if"), slots) and not (p.get("unless") and cond_ok(p["unless"], slots))):
            continue
        reps = dict(p.get("repeat") or {"n": 1})
        try:
            x, y, w, h = (ev(v, s) for v, s in zip(p.get("rect", [0, 0, "100%", "100%"]), (pw, ph, pw, ph)))
        except ValueError as e:
            errs.append(f"{where}.{p.get('id')}: {e}")
            x = y = 0.0
            w, h = pw, ph
        if reps.get("n") == "fit":  # as many as fit between the same margins (a perforation across any width)
            dx, dy = reps.get("dx", 0), reps.get("dy", 0)
            reps["n"] = max(1, int((pw - 2 * x - w) // dx) + 1 if dx else int((ph - 2 * y - h) // dy) + 1 if dy else 1)
        for i in range(int(reps.get("n", 1))):
            q = {k: copy.deepcopy(v) for k, v in p.items() if k not in ("children", "repeat")}
            pid = p.get("id", "part") + (str(i + 1) if reps.get("n", 1) > 1 else "")
            q["rect"] = [x + i * reps.get("dx", 0), y + i * reps.get("dy", 0), w, h]
            if "use" in p:
                node = expand_use(kit, p, _qualify(inst, pid), q["rect"], slots, static, errs, where)
                if node:
                    out.append(node)
                continue
            q["id"] = _qualify(inst, pid)
            if static:
                for k in ("fill", "text", "style", "color", "image", "tint", "bar", "hint"):
                    if k in q:
                        q[k] = fill_slots(q[k], slots)
                if "gradient" in q:
                    q["gradient"] = [fill_slots(g, slots) for g in q["gradient"]]
                if "stroke" in q:
                    q["stroke"] = [fill_slots(q["stroke"][0], slots), q["stroke"][1]]
                q.pop("if", None)
                q.pop("unless", None)
            kids = expand_parts(kit, p.get("children", []), w, h, slots, inst, static, errs, where)
            if kids:
                q["children"] = kids
            out.append(q)
    return out


def expand_use(kit, node, inst_id, rect, outer_slots, static, errs, where):
    """Instantiate template node['use'] at rect with its slots (+ variant preset); returns the root node."""
    name = node["use"]
    tpl = kit.comps.get(name)
    if not tpl:
        errs.append(f"{where}: unknown template {name!r}")
        return None
    slots = {}
    var = node.get("variant") or tpl.get("default_variant")
    if tpl.get("variants") and var:
        preset = tpl["variants"].get(var)
        if isinstance(preset, dict):
            slots.update(preset)
        elif preset is None:
            errs.append(f"{where}: template {name} has no variant {var!r}")
    slots.update({k: fill_slots(v, outer_slots) for k, v in (node.get("slots") or {}).items()})
    if static and not (cond_ok(node.get("if"), outer_slots) and not (node.get("unless") and cond_ok(node["unless"], outer_slots))):
        return None
    root = dict(tpl.get("root") or {"type": "frame"})
    root.update({k: copy.deepcopy(v) for k, v in node.items() if k not in ("use", "slots", "variant", "children", "if", "unless", "rect")})
    root["id"], root["rect"], root["template"] = inst_id, list(rect), name
    if var:
        root["variant"] = var
    if slots.get("hint"):
        root["hint"] = slots["hint"]
    w, h = rect[2], rect[3]
    kids = expand_parts(kit, tpl.get("parts", []), w, h, slots, inst_id, static, errs, f"{where}:{name}")
    if tpl.get("states"):
        st = {}
        for sname, over in tpl["states"].items():
            st[sname] = {}
            for pid, props in over.items():
                tgt = inst_id if pid == "root" else _qualify(inst_id, pid)
                pr = {}
                for k, v in props.items():
                    pr[k] = [fill_slots(v[0], slots), v[1]] if k == "stroke" else fill_slots(v, slots)
                st[sname][tgt] = pr
        root["states"] = st
    content = _find(kids, lambda n: n.get("content"))
    if node.get("children"):
        host = content or {"children": kids, "rect": [0, 0, w, h]}
        ox, oy = _offset_of(kids, host) if content else (0.0, 0.0)
        for ch in node["children"]:
            sub = expand_node(kit, ch, static, errs, where)
            if sub:
                sub["rect"][0] -= ox
                sub["rect"][1] -= oy
                host.setdefault("children", []).append(sub)
    root["children"] = kids
    return root


def _find(nodes, pred):
    for n in nodes:
        if pred(n):
            return n
        f = _find(n.get("children", []), pred)
        if f:
            return f
    return None


def _offset_of(nodes, target, ox=0.0, oy=0.0):
    for n in nodes:
        x, y = ox + n["rect"][0], oy + n["rect"][1]
        if n is target:
            return x, y
        r = _offset_of(n.get("children", []), target, x, y)
        if r:
            return r
    return None


def expand_node(kit, node, static, errs, where):
    rect = [float(v) if isinstance(v, (int, float)) else v for v in node.get("rect", [0, 0, 10, 10])]
    if any(not isinstance(v, float) for v in rect):
        errs.append(f"{where}.{node.get('id')}: screen rects are px numbers")
        return None
    for k in node:
        if k not in NODE_KEYS:
            errs.append(f"{where}.{node.get('id')}: unknown key {k!r}")
    if "use" in node:
        return expand_use(kit, node, node["id"], rect, {}, static, errs, where)
    if node.get("type") not in TYPES:
        errs.append(f"{where}.{node.get('id')}: type must be one of {TYPES}")
        return None
    q = {k: copy.deepcopy(v) for k, v in node.items() if k != "children"}
    q["rect"] = rect
    if isinstance(q.get("text"), dict):
        key, part = q["text"].get("canon"), int(q["text"].get("part", 0))
        v = kit.b.value(key) if key else None
        if v is None:
            errs.append(f"{where}.{node.get('id')}: text canon {key!r} not in rr-bible")
            q["text"] = "?"
        else:
            kit.cites.add(key)
            parts = [s.strip() for s in str(v).split(" / ")]
            q["text"] = parts[part] if part < len(parts) else parts[-1]
            q["canon_text"] = key
    kids = [expand_node(kit, c, static, errs, where) for c in node.get("children", [])]
    if any(kids):
        q["children"] = [k for k in kids if k]
    return q


def walk(nodes, fn, parent=None):
    for n in nodes:
        fn(n, parent)
        walk(n.get("children", []), fn, n)


def expand_runtime(kit, name, errs):
    """A runtime template ready for Luau: rects evaluated, repeats unrolled, slots and if/unless kept."""
    tpl = kit.comps[name]
    w, h = tpl["size"]
    return {"name": name, "size": [w, h], "slots": tpl.get("slots", {}), "variants": tpl.get("variants", {}),
            "parts": expand_parts(kit, tpl["parts"], w, h, {}, "", False, errs, name)}


# ------------------------------------------------------------------ screen
class Screen:
    def __init__(self, kit, path):
        self.kit, self.path = kit, Path(path)
        self.errors, self.warnings, self.info = [], [], []
        try:
            self.raw = json.loads(self.path.read_text(encoding="utf-8"))
        except ValueError as e:
            raise SpecError(f"{self.path}: not valid JSON ({e})") from None
        except OSError as e:
            raise SpecError(f"{self.path}: {e.strerror}") from None
        S = self.raw
        self.name = S.get("screen") or self.path.stem
        for k in ("screen", "nodes"):
            if k not in S:
                self.errors.append(f"spec: missing {k!r}")
        dname = (S.get("design") or {}).get("device", "phone")
        self.design = kit.devices.get(dname)
        if not self.design or not self.design.design:
            self.errors.append(f"design.device {dname!r} must be the kit's design device ({kit.design_device.name})")
            self.design = kit.design_device
        gui = S.get("gui") or {}
        self.insets = gui.get("insets", "CoreUISafeInsets")
        if self.insets not in INSET_MODES:
            self.errors.append(f"gui.insets must be one of {INSET_MODES}")
        self.gui = gui
        self.data = {}
        for k, dv in (S.get("data") or {}).items():
            vals = dv.get("values", [])
            if isinstance(vals, dict):
                v = kit.b.value(vals.get("canon", ""))
                if v is None:
                    self.errors.append(f"data.{k}: canon {vals.get('canon')} missing")
                    v = ""
                vals = [x.strip().upper() if vals.get("upper") else x.strip() for x in str(v).split(",") if x.strip()]
            self.data[k] = {"values": vals, "default": dv.get("default", vals[0] if vals else None)}
        self.types = {}
        for tname, t in (S.get("types") or {}).items():
            txt = t.get("text", {})
            parts = []
            if isinstance(txt, dict) and "canon" in txt:
                v = kit.b.value(txt["canon"])
                kit.cites.add(txt["canon"])
                if v is None:
                    self.errors.append(f"types.{tname}: canon {txt['canon']} missing")
                parts = [p.strip() for p in str(v or "?").split(" / ")]
            elif isinstance(txt, list):
                parts = txt
                self.info.append(f"types.{tname}: literal texts (not canon): {' / '.join(txt)}")
            self.types[tname] = {"kind": t.get("kind"), "icon": t.get("icon"), "title": parts[0] if parts else "",
                                 "body": parts[1] if len(parts) > 1 else "", "stamp": parts[2] if len(parts) > 2 else None,
                                 "canon": txt.get("canon") if isinstance(txt, dict) else None}
        errs = []
        self.nodes = [n for n in (expand_node(kit, n, True, errs, self.name) for n in S.get("nodes", [])) if n]
        self.errors += errs
        self.index = {}
        walk(self.nodes, lambda n, p: self._index(n, p))
        for n in self.nodes:
            n["layer"] = n.get("layer", "core")
            if n["layer"] not in ("core", "backdrop"):
                self.errors.append(f"{n['id']}: layer must be core or backdrop")
            if n.get("stack"):
                n["stack"] = self._stack(n)
        # icons: the spec's own folder first (relative to the spec), then the skill's shared set
        self.icon_dirs = ([(self.path.parent / S["icons"]).resolve()] if S.get("icons") else []) + [SKILL / "assets" / "icons"]
        self.icons_dir = self.icon_dirs[0]
        self.nav = self._nav(S.get("nav") or {})
        self.machine = self._machine(S.get("machine") or {})
        self.boards = S.get("boards") or [{"name": "default"}]

    def icon_file(self, name):
        for d in self.icon_dirs:
            for ext in (".svg", ".png"):
                if (d / f"{name}{ext}").is_file():
                    return d / f"{name}{ext}"
        return None

    def icon_refs(self):
        """Every icon name this screen can draw: alert types plus icon.<name> images and icon slots."""
        out = {t["icon"] for t in self.types.values() if t.get("icon")}
        for n in self.index.values():
            img = n.get("image")
            if isinstance(img, str) and img.startswith("icon.") and not has_slots(img):
                out.add(img[5:])
        return out

    def _index(self, n, parent):
        if n["id"] in self.index:
            self.errors.append(f"duplicate id {n['id']}")
        self.index[n["id"]] = n
        n["_parent"] = parent["id"] if parent else None

    def ref(self, rid):
        """Exact id, else a unique '.suffix' match (so nav can say 'close' for 'panel.close')."""
        if rid in self.index:
            return rid
        hits = [k for k in self.index if k.endswith("." + rid)]
        return hits[0] if len(hits) == 1 else None

    def _stack(self, n):
        st = dict(n["stack"])
        k = self.kit
        for key in ("gap", "max"):
            st[key] = k.num(st.get(key, 8 if key == "gap" else 4), f"{n['id']}.stack.{key}")
        st["life_s"] = {kind: k.num(v, f"{n['id']}.stack.life_s.{kind}") for kind, v in st.get("life_s", {}).items()}
        for t in ("template", "compact", "overflow"):
            if st.get(t) and st[t] not in k.comps:
                self.errors.append(f"{n['id']}.stack.{t}: unknown template {st[t]}")
        return st

    def _nav(self, nav):
        hits = [i for i, n in self.index.items() if n.get("type") == "hit"]
        edges = {h: {} for h in hits}
        rows = []
        for row in nav.get("grid", []):
            rr = []
            for rid in row:
                r = self.ref(rid)
                if not r:
                    self.errors.append(f"nav.grid: unknown id {rid}")
                elif self.index[r].get("type") != "hit":
                    self.errors.append(f"nav.grid: {rid} is not interactive")
                else:
                    rr.append(r)
            if rr:
                rows.append(rr)
        centers = self._design_centers()
        for i, row in enumerate(rows):
            for j, a in enumerate(row):
                if j > 0:
                    edges[a]["left"] = row[j - 1]
                if j < len(row) - 1:
                    edges[a]["right"] = row[j + 1]
                for d, di in (("up", i - 1), ("down", i + 1)):
                    if 0 <= di < len(rows):
                        cx = centers.get(a, (0, 0))[0]
                        edges[a][d] = min(rows[di], key=lambda b: abs(centers.get(b, (0, 0))[0] - cx))
        for a, m in (nav.get("edges") or {}).items():
            ra = self.ref(a)
            if ra:
                edges.setdefault(ra, {}).update({d: self.ref(b) for d, b in m.items()})
        out = {"edges": edges, "rows": rows}
        for k in ("default", "back", "modal"):
            if nav.get(k):
                r = self.ref(nav[k])
                if not r:
                    self.errors.append(f"nav.{k}: unknown id {nav[k]}")
                out[k] = r
        if hits and not rows:
            self.warnings.append("nav: interactive nodes but no nav.grid; gamepad players cannot reach them")
        return out

    def _design_centers(self):
        out = {}

        def rec(nodes, ox, oy):
            for n in nodes:
                x, y = ox + n["rect"][0], oy + n["rect"][1]
                out[n["id"]] = (x + n["rect"][2] / 2, y + n["rect"][3] / 2)
                rec(n.get("children", []), x, y)
        rec(self.nodes, 0, 0)
        return out

    def _machine(self, m):
        if not m:
            return None
        states = m.get("states", {})
        if m.get("initial") not in states:
            self.errors.append(f"machine.initial {m.get('initial')!r} is not a state")
        for sname, look in states.items():
            for k in ("hide", "show", "disable"):
                for rid in look.get(k, []):
                    if not self.ref(rid):
                        self.errors.append(f"machine.states.{sname}.{k}: unknown id {rid}")
            for rid in (look.get("text") or {}):
                if not self.ref(rid):
                    self.errors.append(f"machine.states.{sname}.text: unknown id {rid}")
        seen, trans = set(), []
        for t in m.get("transitions", []):
            if len(t) < 3:
                self.errors.append(f"machine.transitions: {t} needs [from, event, to, feel?]")
                continue
            fr, evn, to = t[0], t[1], t[2]
            feel = t[3] if len(t) > 3 else None
            for s in (fr, to):
                if s not in states and s != "*":
                    self.errors.append(f"machine.transitions: unknown state {s}")
            if (fr, evn) in seen:
                self.errors.append(f"machine.transitions: {fr} + {evn} defined twice")
            seen.add((fr, evn))
            trans.append({"from": fr, "event": evn, "to": to, "feel": feel})
        reach, todo = {m.get("initial")}, [m.get("initial")]
        while todo:
            s = todo.pop()
            for t in trans:
                if t["from"] in (s, "*") and t["to"] not in reach:
                    reach.add(t["to"])
                    todo.append(t["to"])
        for s in states:
            if s not in reach:
                self.warnings.append(f"machine: state {s} is unreachable from {m.get('initial')}")
        return {"initial": m.get("initial"), "states": states, "transitions": trans}


# ------------------------------------------------------------------ HUD stack policy (mirrored in RR_UIKit.lua)
def stack_sim(screen, st, pushes, lives=None):
    """Apply the stack policy to a push sequence; returns (visible items oldest->newest, hidden count)."""
    live, seq = [], 0
    for i, p in enumerate(pushes):
        tname, extra = p[0], (p[1] if len(p) > 1 else {})
        t = screen.types.get(tname)
        if not t:
            screen.errors.append(f"board push: unknown type {tname}")
            continue
        seq += 1
        life = (lives[i] if lives and i < len(lives) else 1.0)
        if st.get("merge") == "type":
            same = next((it for it in live if it["type"] == tname), None)
            if same:
                same["count"] += 1
                same["life"] = life
                same["seq_touch"] = seq
                continue
        slots = {"kind": t["kind"], "title": t["title"], "body": fill_slots(t["body"], extra), "stamp": t["stamp"],
                 "icon": t["icon"]}
        live.append({"type": tname, "seq": seq, "slots": slots, "count": 1, "life": life,
                     "sticky": cond_ok(st.get("sticky"), slots), "crisis": cond_ok(st.get("crisis"), slots)})
    return stack_visible(st, live)


def stack_visible(st, live):
    mx = int(st.get("max", 4))
    ranked = sorted(live, key=lambda it: (not it["sticky"], -it["seq"]))
    vis = sorted(ranked[:mx], key=lambda it: it["seq"])
    newest = vis[-1] if vis else None
    crises = [it for it in vis if it["crisis"]]
    newest_crisis = crises[-1] if crises else None
    full = set()
    if "newest" in st.get("full", []) and newest:
        full.add(id(newest))
    if "newest_crisis" in st.get("full", []) and newest_crisis:
        full.add(id(newest_crisis))
    for it in vis:
        it["compact"] = bool(st.get("compact")) and id(it) not in full
        it["halo"] = it is newest_crisis
    return vis, len(live) - len(vis)


def stack_layout(st, kit, items, stack_w, stack_h):
    """Design-px rects of the stacked items (newest at the bottom for dir up) and the more chip."""
    gap = st.get("gap", 8)
    y = stack_h
    rects = []
    for it in reversed(items):
        tpl = kit.comps[st["compact"] if it.get("compact") else st["template"]]
        h = tpl["size"][1]
        y -= h
        rects.append((it, [stack_w - tpl["size"][0], y, tpl["size"][0], h]))
        y -= gap
    rects.reverse()
    return rects


def more_rect(kit, st, rects):
    tpl = kit.comps[st["overflow"]]
    w, h = tpl["size"]
    top = rects[0] if rects else [0, 0, 0, 0]
    return [top[0] - w - st.get("gap", 8), top[1] + 4, w, h]


# ------------------------------------------------------------------ layout resolver (mirrored in RR_UIKit.lua)
def pin_of(node, pw, ph):
    if node.get("pin"):
        return PINS[node["pin"]]
    x, y, w, h = node["rect"]
    cx, cy = x + w / 2, y + h / 2
    f = lambda c, s: 0 if c < s / 3 else (1 if c > 2 * s / 3 else 0.5)  # noqa: E731
    return (f(cx, pw), f(cy, ph))


def _extent(p, a, size, full):
    """Design px a pinned group needs along one axis: its margin from the pinned edge plus its size
    (centred: its size plus twice its offset from the centre)."""
    return a + size if p == 0 else full - a if p == 1 else size + 2 * abs(a + size / 2 - full / 2)


def group_fit(s, d, node, x, y, w, h, dw, dh, aw, ah):
    """Own fit (mirrored in RR_UIKit.lua): an area smaller than the design area shrinks a pinned group only as
    much as that group needs to stay inside it (a notched phone keeps a corner HUD and a centred panel at full
    size); bigger areas scale every group by the same s. Stretch groups always use s."""
    if s >= 1 or node.get("stretch"):
        return s
    px, py = pin_of(dict(node, rect=[x, y, w, h]), dw, dh)
    ex, ey = max(_extent(px, x, w, dw), 1e-6), max(_extent(py, y, h, dh), 1e-6)
    return max(s, min(1.0, aw / (ex * d), ah / (ey * d)))


def place_top(kit, dev, node, mode):
    """Absolute box of a top-level node: pin + scale. Returns (box, k) where k = px per design px."""
    ax, ay, aw, ah = dev.area(mode)
    dax, day, dw, dh = kit.design_device.area(mode)
    s = min(aw / dw, ah / dh)
    d = kit.density.get(dev.display, 1.0)
    x, y, w, h = node["rect"]
    x, y = x - dax, y - day
    st = node.get("stretch")
    k = group_fit(s, d, node, x, y, w, h, dw, dh, aw, ah) * d
    if st:
        mL, mR, mT, mB = x, dw - x - w, y, dh - y - h
        bw = aw - (mL + mR) * k if "x" in st else w * k
        bh = ah - (mT + mB) * k if "y" in st else h * k
        px, py = pin_of(dict(node, rect=[x, y, w, h]), dw, dh)
        bx = ax + mL * k if "x" in st else ax + px * aw + (x + px * w - px * dw) * k - px * bw
        by = ay + mT * k if "y" in st else ay + py * ah + (y + py * h - py * dh) * k - py * bh
        return (bx, by, bw, bh), k
    px, py = pin_of(dict(node, rect=[x, y, w, h]), dw, dh)
    mx, my = x + px * w - px * dw, y + py * h - py * dh
    bw, bh = w * k, h * k
    anchor_x, anchor_y = ax + px * aw + mx * k, ay + py * ah + my * k
    return (anchor_x - px * bw, anchor_y - py * bh, bw, bh), k


def place_child(node, parent_box, pdw, pdh, keep):
    x, y, w, h = node["rect"]
    qx, qy = pin_of(node, pdw, pdh)
    bw, bh = w / pdw * parent_box[2], h / pdh * parent_box[3]
    if keep and h > 0 and w > 0:
        ar = w / h
        if bw / max(bh, 1e-9) > ar:
            bw = bh * ar
        else:
            bh = bw / ar
    axp = parent_box[0] + (x + qx * w) / pdw * parent_box[2]
    ayp = parent_box[1] + (y + qy * h) / pdh * parent_box[3]
    return (axp - qx * bw, ayp - qy * bh, bw, bh)


class Look:
    """Per-board state: machine look, data slots, component states, selection."""

    def __init__(self, screen, board):
        self.board = board or {}
        m = screen.machine
        self.state = self.board.get("state") or (m["initial"] if m else None)
        look = (m["states"].get(self.state, {}) if m else {}) or {}
        self.hidden = {screen.ref(r) for r in look.get("hide", [])}
        self.shown = {screen.ref(r) for r in look.get("show", [])}
        self.disabled = {screen.ref(r) for r in look.get("disable", [])}
        self.text = {screen.ref(r): v for r, v in (look.get("text") or {}).items()}
        self.data = {k: v["default"] for k, v in screen.data.items()}
        self.data.update(self.board.get("data") or {})
        self.comp = {screen.ref(k): v for k, v in (self.board.get("comp_states") or {}).items()}
        self.select = screen.ref(self.board["select"]) if self.board.get("select") else None


def comp_flags(node, look, slots):
    flags = []
    if node.get("on") and cond_ok(node["on"], slots):
        flags.append("on")
    extra = look.comp.get(node["id"])
    if extra in ("hover", "pressed"):
        flags.append(extra)
    if node["id"] in look.disabled:
        flags.append("disabled")
    return flags


STATE_ORDER = ("on", "hover", "pressed", "disabled")


def resolve(screen, dev, skin, board=None, text_scale=1.0):
    """The drawn tree for one board: nested dicts with absolute boxes and resolved styles, plus facts for checks."""
    kit = screen.kit
    look = Look(screen, board)
    slots = dict(look.data)
    out = {"device": dev, "skin": skin, "layers": {}, "texts": [], "hits": [], "boxes": [], "problems": [],
           "look": look, "k": {}}
    overrides = {}
    for n in screen.index.values():
        if n.get("comp") and n.get("states"):
            for f in sorted(comp_flags(n, look, slots), key=STATE_ORDER.index):
                for tgt, props in n["states"].get(f, {}).items():
                    overrides.setdefault(tgt, {}).update(props)

    def draw(node, box, k, clip, inherited_alpha, depth):
        nid = node["id"]
        o = dict(node)
        o.update(overrides.get(nid, {}))
        visible = o.get("visible", True)
        if nid in look.hidden:
            visible = False
        if nid in look.shown:
            visible = True
        if not visible:
            return None
        if o.get("dy"):
            box = (box[0], box[1] + o["dy"] * k, box[2], box[3])
        alpha = inherited_alpha * (o.get("alpha", 1.0) if o.get("comp") or o.get("type") == "hit" else 1.0)
        item = {"id": nid, "type": o.get("type", "frame"), "box": box, "rot": o.get("rot", 0), "k": k,
                "clip": o.get("clip", False), "group_alpha": alpha if (o.get("comp")) else None, "children": []}
        fill_a = o.get("alpha", 1.0) if not o.get("comp") else 1.0

        def col(role, what):
            r = fill_slots(role, slots, keep_unknown=False) if role else None
            if not r:
                return None
            if r.startswith("@"):
                f = kit.b.fact(r[1:])
                return f["value"] if f else None
            c = kit.color(skin, r)
            if not c:
                out["problems"].append(f"{nid}.{what}: role {r!r} does not resolve in skin {skin}")
            return c
        if o.get("fill"):
            item["fill"], item["alpha"] = col(o["fill"], "fill"), fill_a
        if o.get("gradient"):
            item["gradient"] = [col(g, "gradient") for g in o["gradient"]]
            item["alpha"] = fill_a
        if o.get("stroke"):
            item["stroke"] = (col(o["stroke"][0], "stroke"), float(o["stroke"][1]) * k)
        if "radius" in o:
            item["radius"] = "circle" if o["radius"] == "circle" else float(o["radius"]) * k
        if o.get("pattern"):
            item["pattern"] = (o["pattern"], kit.color(skin, "hazard"), kit.color(skin, "hazard_ink"), 16 * k)
        if o.get("bar"):
            v = slots.get(o["bar"], 1.0)
            v = max(0.0, min(1.0, float(v if v not in (None, "") else 1.0)))
            item["box"] = box = (box[0], box[1], box[2] * v, box[3])
        pushed = item.get("gradient") or ([item["fill"]] if item.get("fill") else None)
        if pushed:
            chain_fill.append((pushed, item.get("alpha", 1.0)))
        if item["type"] == "text":
            t = look.text.get(nid, o.get("text", ""))
            t = fill_slots(str(t), slots, keep_unknown=False)
            sty = kit.types.get(fill_slots(o.get("style", ""), slots))
            if not sty:
                out["problems"].append(f"{nid}: unknown type style {o.get('style')!r}")
                sty = {"font": "body", "size": 14, "weight": 700, "line": 17}
            item.update(text=t, font=kit.fonts[sty["font"]]["name"], fam=sty["font"], weight=sty["weight"],
                        size=sty["size"] * k * text_scale, line=sty.get("line", sty["size"] * 1.2) * k * text_scale,
                        color=col(o.get("color", "ink"), "color"), align=o.get("align", "left"),
                        valign=o.get("valign", "center"), wrap=o.get("wrap", False), truncate=o.get("truncate", False))
            if t:
                out["texts"].append(dict(item, parent_chain=list(chain_fill)))
        if item["type"] == "image":
            item["image"] = fill_slots(o.get("image", ""), slots, keep_unknown=False)
            item["tint"] = col(o.get("tint"), "tint") if o.get("tint") else None
            if o.get("gamepad_only") and dev.input != "Gamepad":
                return None
        if item["type"] == "hit":
            out["hits"].append({"id": nid, "box": box, "disabled": nid in look.disabled})
            if look.select == nid:
                item["focus"] = True
        out["boxes"].append({"id": nid, "box": box, "top": depth == 0, "type": item["type"], "clip": clip,
                             "layer": cur[0]})
        _, _, pdw, pdh = node["rect"]
        for ch in node.get("children", []):
            cb = place_child(ch, box, pdw, pdh, keep=bool(node.get("stretch")))
            c = draw(ch, cb, k, clip or item["clip"], alpha, depth + 1)
            if c:
                item["children"].append(c)
        if node.get("stack"):
            item["children"] += draw_stack(node, box, k)
        if pushed:
            chain_fill.pop()
        return item

    def draw_stack(node, box, k):
        st = node["stack"]
        pushes = look.board.get("push", [])
        if cur[-1] and st.get("max_lifted"):
            st = dict(st, max=st["max_lifted"])
        vis, hidden = stack_sim(screen, st, pushes, look.board.get("life"))
        out["stack"] = {"visible": len(vis), "hidden": hidden, "items": vis}
        rects = stack_layout(st, kit, vis, node["rect"][2], node["rect"][3])
        drawn = []
        for it, r in rects:
            tpl = st["compact"] if it["compact"] else st["template"]
            sl = dict(it["slots"], count=it["count"] if it["count"] > 1 else None, life=it["life"],
                      halo=it["halo"], sticky=it["sticky"])
            errs = []
            inst = expand_use(kit, {"use": tpl, "slots": sl, "pin": "tl"}, f"{node['id']}.t{it['seq']}", r, {}, True, errs, "stack")
            screen.errors += errs
            saved = dict(slots)
            slots.update({kk: v for kk, v in sl.items()})
            cb = place_child(inst, box, node["rect"][2], node["rect"][3], keep=False)
            c = draw(inst, cb, k, False, 1.0, 1)
            slots.clear()
            slots.update(saved)
            if c:
                drawn.append(c)
        if hidden and st.get("overflow"):
            r = more_rect(kit, st, [r for _, r in rects])
            inst = expand_use(kit, {"use": st["overflow"], "slots": {"n": hidden}, "pin": "tl"}, f"{node['id']}.more", r, {}, True, [], "stack")
            cb = place_child(inst, box, node["rect"][2], node["rect"][3], keep=False)
            c = draw(inst, cb, k, False, 1.0, 1)
            if c:
                drawn.append(c)
        return drawn

    chain_fill, cur = [], [None]
    for n in screen.nodes:
        cur[0] = n["layer"]
        mode = "None" if n["layer"] == "backdrop" else screen.insets
        box, k = place_top(kit, dev, n, mode)
        lifted = avoid_lift(kit, dev, n, box)
        cur.append(lifted[1] != box[1])
        box = lifted
        out["k"][n["id"]] = k
        it = draw(n, box, k, False, 1.0, 0)
        if it:
            out["layers"].setdefault(n["layer"], []).append(it)
    return out


def avoid_lift(kit, dev, node, box):
    """Runtime avoid rule (mirrored in the kit): lift a group above an overlapped touch zone."""
    if not node.get("avoid") or not dev.touch:
        return box
    zones = kit.zones_for(dev)
    lift = 0.0
    for z in node["avoid"]:
        r = zones.get(z)
        if r and inter(box, r):
            lift = max(lift, box[1] + box[3] - r[1])
    return (box[0], box[1] - lift, box[2], box[3]) if lift > 0 else box


# ------------------------------------------------------------------ checks
SPECIAL_ROLES = ("diff.", "on_diff.", "kind.")


def role_checks(screen):
    """What a role is for (kit/roles.json 'use', canon ui.rules.*), on spec nodes (templates are the kit's job):
    diff.* only as difficulty marks, never chrome-sized fills; danger / kind.* only through the ticket kinds;
    accent only on something active, current or primary (a data-bound node or its control)."""
    E, W = [], []
    ids = {n["id"] for n in _spec_nodes(screen)}

    def roles_of(n):
        out = []
        for k in ("fill", "color", "tint"):
            if isinstance(n.get(k), str):
                out.append((k, n[k]))
        for g in n.get("gradient") or []:
            out.append(("gradient", g))
        if isinstance(n.get("stroke"), list):
            out.append(("stroke", n["stroke"][0]))
        return out

    def bound(n):
        return any(has_slots(v) for _, v in roles_of(n)) or has_slots(n.get("text")) or \
            any(has_slots(c.get("text")) or any(has_slots(v) for _, v in roles_of(c)) for c in n.get("children", []))
    for n in _spec_nodes(screen):
        par = screen.index.get(n.get("_parent")) if n.get("_parent") else None
        for k, r in roles_of(n):
            r = str(r)
            if r.startswith("diff.") and k in ("fill", "gradient") and min(n["rect"][2], n["rect"][3]) > 24:
                E.append(f"{n['id']}.{k}: {r} on a {n['rect'][2]:g}x{n['rect'][3]:g} box; difficulty colours only as "
                         "difficulty marks (pip, strip; min side <= 24 design px), never chrome (ui.rules.difficulty_never_chrome); "
                         "the current value takes the accent (ui.rules.one_accent)")
            if (r == "danger" or r.startswith("kind.")) and not has_slots(r):
                W.append(f"{n['id']}.{k}: {r} outside the ticket kinds; danger red is the one danger signal (ui.hud.crisis_extra)")
            if r in ("accent", "accent_dark") and not (bound(n) or (par and par["id"] in ids and bound(par))):
                W.append(f"{n['id']}.{k}: accent on a node that shows nothing active, current or primary "
                         "(ui.rules.one_accent); use a template state (chip on, button primary/cta) or bind it to data")
    return E, W


def _spec_nodes(screen):
    """Nodes the spec itself drew: not template parts ('inst.part' ids) and not template instance roots."""
    return [n for n in screen.index.values() if "." not in n["id"] and not n.get("template")]


def check(screen, devices=None, skins=None, text_scale=1.0):
    """All objective checks for one spec; returns (errors, warnings, info, facts dict)."""
    kit = screen.kit
    E, W, I = list(screen.errors) + list(kit.errors), list(screen.warnings) + list(kit.warnings), list(screen.info)
    facts = {"devices": {}, "contrast": {}, "literals": []}
    devices = devices or list(kit.devices.values())
    skins = skins or kit.skins
    literal = []

    def lit(n, parent):
        t = n.get("text")
        if isinstance(t, str) and t and not n.get("canon_text") and not has_slots(t) and not re.fullmatch(r"[\W\d]+|[A-Z]", t):
            literal.append(f"{n['id']}: {t!r}")
    walk(screen.nodes, lit)
    for s in (screen.machine or {}).get("states", {}).values():
        for rid, t in (s.get("text") or {}).items():
            literal.append(f"{rid}: {t!r}")
    facts["literals"] = literal

    def hexes(n, parent):
        for k in ("fill", "color", "tint"):
            if isinstance(n.get(k), str) and re.match(r"^#[0-9A-Fa-f]{3,8}$", n[k]):
                E.append(f"{n['id']}.{k}: hex colour {n[k]} in a spec; use a role (kit/roles.json) or @bible.key")
        for k in ("gradient",):
            for v in n.get(k) or []:
                if isinstance(v, str) and v.startswith("#"):
                    E.append(f"{n['id']}.{k}: hex colour {v} in a spec; use a role")
        if isinstance(n.get("stroke"), list) and str(n["stroke"][0]).startswith("#"):
            E.append(f"{n['id']}.stroke: hex colour {n['stroke'][0]} in a spec; use a role")
    walk(screen.nodes, hexes)
    if literal:
        I.append("literal copy (not from canon; owner confirms): " + "; ".join(literal))
    fe = feel_events()
    if screen.machine:
        for t in screen.machine["transitions"]:
            if t["feel"] and fe is not None and t["feel"] not in fe:
                E.append(f"machine: feel event {t['feel']!r} is not in rr-game-feel's presets")
    for n in screen.index.values():
        if n.get("stack") and fe is not None:
            for key, evn in (n["stack"].get("feel") or {}).items():
                if evn not in fe:
                    E.append(f"{n['id']}.stack.feel.{key}: {evn!r} is not in rr-game-feel's presets")
    if fe is None:
        W.append("rr-game-feel not found: feel event names are unchecked")
    for oid in screen.raw.get("oq", []):
        q = kit.b.oq(oid)
        if not q:
            E.append(f"oq {oid} not found in rr-bible")
        elif q.get("decided"):
            I.append(f"{oid} decided: {q['fields'].get('default', '?')} ({q['decided']}); drop it from the spec's oq "
                     "list once the work follows the decision")
    re_, rw = role_checks(screen)
    E += re_
    W += rw
    for key in screen.raw.get("canon", []):
        if not kit.b.fact(key):
            E.append(f"canon {key} not found in rr-bible")
        kit.cites.add(key)
    for name in sorted(screen.icon_refs()):
        if not screen.icon_file(name):
            E.append(f"icon {name} has no file in {' or '.join(str(d) for d in screen.icon_dirs)} (kinds need their "
                     "icon: ui.rules.colourblind)")
    boards = screen.boards
    for skin in skins:
        worst = None
        for b in boards:
            sc = resolve(screen, kit.design_device, skin, b)
            for p in sc["problems"]:
                E.append(f"[{skin}] {p}")
            for t in sc["texts"]:
                if not t["color"]:
                    continue
                for bg in bg_candidates(t["parent_chain"]):
                    r = contrast(t["color"], bg)
                    large = t["size"] >= 24 or (t["size"] >= 18.66 and (t["weight"] >= 700 or t["fam"] == "display"))
                    need = 3.0 if large else 4.5
                    if worst is None or r < worst[0]:
                        worst = (round(r, 2), t["id"], b.get("name"), need)
                    if r < need - 1e-6:
                        E.append(f"[{skin}] contrast {r:.2f}:1 < {need} for {t['id']} {t['text']!r} ({t['color']} on {bg}, board {b.get('name')})")
                        break
        facts["contrast"][skin] = worst
    design_pairs = {}
    for b in boards:
        sc = resolve(screen, kit.design_device, kit.default_skin, b)
        design_pairs[b.get("name")] = _group_overlaps(sc)
    for dev in devices:
        dfacts = {"min_text": None, "min_target": None, "k": None, "zones": {}}
        hard = dev.design or dev.touch  # every phone and tablet is a main device (identity.audience.devices)
        for b in boards:
            sc = resolve(screen, dev, kit.default_skin, b, text_scale=text_scale)
            for a_, b_ in sorted(_group_overlaps(sc) - design_pairs.get(b.get("name"), set())):
                E.append(f"[{dev.name}] groups {a_} and {b_} overlap here but not on the design board (each group keeps "
                         f"its own fit on a small area): make them one group or smaller (board {b.get('name')})")
            dfacts["k"] = sc["k"]
            for t in sc["texts"]:
                need = kit.min_text["display" if t["fam"] == "display" else "body"]
                if dfacts["min_text"] is None or t["size"] < dfacts["min_text"][0]:
                    dfacts["min_text"] = (round(t["size"], 1), t["id"])
                if t["size"] < need - 0.05:
                    (E if hard else W).append(f"[{dev.name}] text {t['id']} {t['size']:.1f} px < {need:g} px (board {b.get('name')})")
            for h in sc["hits"]:
                m = min(h["box"][2], h["box"][3])
                if dfacts["min_target"] is None or m < dfacts["min_target"][0]:
                    dfacts["min_target"] = (round(m, 1), h["id"])
                if dev.touch and m < kit.touch_target - 0.05:
                    (E if hard else W).append(f"[{dev.name}] target {h['id']} {m:.1f} px < {kit.touch_target:g} px")
            W_, H_ = dev.screen
            for bx in sc["boxes"]:
                x, y, w, h = bx["box"]
                if bx["clip"]:
                    continue
                if x < -0.5 or y < -0.5 or x + w > W_ + 0.5 or y + h > H_ + 0.5:
                    E.append(f"[{dev.name}] {bx['id']} is off screen ({x:.0f},{y:.0f},{w:.0f},{h:.0f}) board {b.get('name')}")
            ax, ay, aw, ah = dev.area(screen.insets)
            for bx in sc["boxes"]:
                if bx["layer"] == "core" and bx["type"] in ("text", "hit", "image") and bx["box"][1] < ay - 0.5:
                    E.append(f"[{dev.name}] {bx['id']} enters the top bar strip by {ay - bx['box'][1]:.0f} px (board {b.get('name')})")
            zones = kit.zones_for(dev)
            if zones:
                dfacts["zones"]["size"] = zones["_size"]
                for bx in sc["boxes"]:
                    if bx["type"] not in ("text", "hit", "image"):
                        continue
                    for z in ("jump", "stick"):
                        ov = inter(bx["box"], zones[z])
                        if ov:
                            E.append(f"[{dev.name}] {bx['id']} overlaps the {z} zone by {ov[2]:.0f}x{ov[3]:.0f} px (board {b.get('name')})")
                for h in sc["hits"] if not screen.gui.get("modal") else []:
                    if inter(h["box"], zones["stick_area"]):
                        W.append(f"[{dev.name}] {h['id']} sits in the thumbstick touch area (it takes the walk touch)")
                for n in screen.nodes:
                    if n.get("avoid"):
                        mode = screen.insets
                        base, _ = place_top(kit, dev, n, mode)
                        lifted = avoid_lift(kit, dev, n, base)
                        if lifted[1] != base[1]:
                            I.append(f"[{dev.name}] {n['id']} is lifted {base[1] - lifted[1]:.0f} px above the {zones['_size']} jump zone at run time")
            if "stack" in sc:
                dfacts.setdefault("stack", {})[b.get("name")] = f"{sc['stack']['visible']} visible, +{sc['stack']['hidden']} more"
        facts["devices"][dev.name] = dfacts
    nav = screen.nav
    hits = [i for i, n in screen.index.items() if n.get("type") == "hit"]
    if hits:
        start = nav.get("default") or (nav["rows"][0][0] if nav["rows"] else None)
        seen, todo = {start}, [start]
        while todo:
            a = todo.pop()
            for b_ in nav["edges"].get(a, {}).values():
                if b_ and b_ not in seen:
                    seen.add(b_)
                    todo.append(b_)
        for h in hits:
            if h not in seen:
                E.append(f"nav: {h} is unreachable by gamepad from {start}")
            if len(hits) > 1 and not nav["edges"].get(h):
                E.append(f"nav: {h} has no neighbours (dead end)")
        opp = {"left": "right", "right": "left", "up": "down", "down": "up"}
        row_of = {h: i for i, r in enumerate(nav["rows"]) for h in r}
        for a, m in nav["edges"].items():
            for d, b_ in m.items():
                back = nav["edges"].get(b_, {}).get(opp[d]) if b_ else None
                if d in ("up", "down") and back and back in row_of and row_of.get(back) == row_of.get(a):
                    continue  # rows of different lengths: several items share a neighbour (inherent, not a trap)
                if b_ and back != a:
                    (W if d in ("left", "right") else I).append(f"nav: {a}.{d} = {b_} but {b_}.{opp[d]} = {nav['edges'].get(b_, {}).get(opp[d])}")
        if screen.gui.get("modal") and not nav.get("modal"):
            W.append("nav: modal screen without nav.modal (focus can leave the panel)")
        if not nav.get("back") and screen.gui.get("modal"):
            W.append("nav: modal screen without nav.back (ButtonB does nothing)")
    facts["density"] = kit.density
    return list(dict.fromkeys(E)), list(dict.fromkeys(W)), list(dict.fromkeys(I)), facts


def _group_overlaps(scene):
    tops = [(bx["id"], bx["box"]) for bx in scene["boxes"] if bx["top"] and bx["layer"] == "core"]
    return {(a[0], b[0]) for i, a in enumerate(tops) for b in tops[i + 1:] if inter(a[1], b[1])}


def bg_candidates(chain):
    """Colours a text actually sits on: the nearest opaque fill (each gradient stop) with translucent fills above
    it blended in. Nothing opaque behind = the game world: unknown, so no contrast claim is made."""
    idx = max((i for i, (_, a) in enumerate(chain) if a >= 0.99), default=None)
    if idx is None:
        return []
    out = []
    for base in chain[idx][0]:
        c = base
        for stops, a in chain[idx + 1:]:
            c = blend(stops[0], c, a)
        out.append(c)
    return out


def feel_events():
    feel = find_sibling("rr-game-feel", "RR_FEEL_SKILL")
    p = Path(os.environ.get("RR_FEEL_PRESETS") or (feel / "presets" / "feel.json" if feel else ""))
    if p.is_dir():
        p = p / "feel.json"
    if not str(p) or not p.is_file():
        return None
    try:
        return set(json.loads(p.read_text(encoding="utf-8")).get("events", {}))
    except ValueError:
        return None


# ------------------------------------------------------------------ Lua literal emitter
LUA_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
LUA_KEYWORDS = {"and", "break", "do", "else", "elseif", "end", "false", "for", "function", "if", "in", "local", "nil",
                "not", "or", "repeat", "return", "then", "true", "until", "while", "goto", "continue", "type"}


def lua(v, ind=0, strip=("_parent", "note")):
    pad, pad1 = "\t" * ind, "\t" * (ind + 1)
    if v is None:
        return "nil"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(int(v)) if float(v).is_integer() else repr(round(float(v), 6))
    if isinstance(v, str):
        if v.startswith("\0raw:"):
            return v[5:]
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(v, (list, tuple)):
        if not v:
            return "{}"
        simple = all(not isinstance(x, (dict, list, tuple)) for x in v)
        if simple:
            return "{ " + ", ".join(lua(x) for x in v) + " }"
        return "{\n" + "".join(f"{pad1}{lua(x, ind + 1, strip)},\n" for x in v) + pad + "}"
    if isinstance(v, dict):
        items = [(k, x) for k, x in v.items() if k not in strip]
        if not items:
            return "{}"
        out = []
        for k, x in items:
            key = k if (isinstance(k, str) and LUA_IDENT.match(k) and k not in LUA_KEYWORDS) else f"[{lua(k)}]"
            out.append(f"{pad1}{key} = {lua(x, ind + 1, strip)},\n")
        return "{\n" + "".join(out) + pad + "}"
    return lua(str(v))


def raw(expr):
    return "\0raw:" + expr


if __name__ == "__main__":
    print(__doc__)
