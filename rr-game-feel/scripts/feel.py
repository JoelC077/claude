#!/usr/bin/env python3
"""rr-game-feel: Risky Rails juice presets as data -> Luau runtime, feel specs, plots, previews, critic hand-off.

  feel.py list [--group G]                       events with group, tier, who, channels, loudness
  feel.py show EVENT [--json] [--rm]             one event: channels, measured metrics, hierarchy pairs
  feel.py validate [--strict] [--json]           schema, Roblox enums, canon agreement, colours, OQs, comfort
                                                 limits, visibility, reduce motion, loudness hierarchy, cues
  feel.py spec [EVENT|all] [--out FILE]          feel spec per event (markdown) from the presets
  feel.py tune [SEL] --out DIR                   tuning table: TUNING.md + tuning.csv (knobs, safe ranges,
                                                 measured result per event)
  feel.py set 'PATH=VALUE' ... [--dry-run]       edit feel.json by path (events.x.channels[0].amp=5), keeps
                                                 the house layout; feel.py fmt [--check] reformats it
  feel.py changed --since OLD.json               changed events and the groups to re-preview / re-critique
  feel.py plot curves|lever|sustain|EVENT|all --out DIR [--compare DUMP]
                                                 PNG plots (Pillow); --compare overlays a Studio curve dump
  feel.py preview GROUP|EVENT|E1,E2,..|all --out DIR [--name N] [--gif] [--rm]
                                                 mock phone frames, filmstrips, feel matrix, contact.png,
                                                 closeups.png, facts.md (multiuse-critic layout); an EVENT
                                                 goes to DIR/ev_<event>, a list to DIR/<N or set_<first>>
  feel.py crit CRIT --pass N --from DIR          CRIT/rubric.md with Profile G, pass files, brief from canon
  feel.py build --out DIR [--no-check]           RR_FeelPresets.lua, RR_FeelTyped.luau (strict types), runtime
                                                 modules, FEEL_SPEC.md, README; then the Luau syntax gate
                                                 (luau-compile, else luaparse, else SKIP), strict typecheck
                                                 when luau-lsp is installed, and bible check

Presets: --presets FILE, else $RR_FEEL_PRESETS (a file or a folder holding feel.json), else the skill's own
copy (read-only: copy it into the project first). Every command prints which file it used. Canon: the
rr-bible skill (found by glob or $RR_BIBLE_SKILL). Critic scripts: multiuse-critic ($RR_CRITIC_SKILL); cue
names: rr-vfx-lighting ($RR_VFX_SKILL), rr-soundsmith ($RR_SOUND_SKILL). Standard library only; plot and
preview need Pillow. Exit codes: 0 ok, 1 check failed, 2 usage or missing input.
"""
import argparse, colorsys, copy, datetime as _dt, json, math, os, re, shutil, statistics, subprocess, sys
from pathlib import Path

sys.dont_write_bytecode = True   # never leave __pycache__ in the skill folder
HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
import feelmath as fm  # noqa: E402

TODAY = _dt.date.today().isoformat()
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")
NEUTRALS = {"#FFFFFF", "#000000"}
HAPTIC_TYPES = ("Custom", "UIHover", "UIClick", "UINotification", "GameplayExplosion", "GameplayCollision")
PROPS = {"tween": ("scale", "x", "y", "x_px", "y_px", "rot", "alpha", "count"),
         "punch": ("scale", "rot", "x_px", "y_px"), "pulse": ("alpha", "scale")}
REQUIRED = {"tween": ("target", "prop", "from", "to", "dur"), "punch": ("target", "prop", "amp", "freq_hz", "dur"),
            "camkick": ("angles_deg", "freq_hz", "dur"), "shake": ("trauma",), "hitstop": ("ms",),
            "flash": ("scope", "color", "peak", "in", "out"), "fovkick": ("delta_deg", "in", "out"),
            "haptic": ("effect", "keys"), "pulse": ("target", "prop", "min", "max", "period"), "cue": ()}
LUA_KEYWORDS = {"and", "break", "do", "else", "elseif", "end", "false", "for", "function", "if", "in", "local", "nil",
                "not", "or", "repeat", "return", "then", "true", "until", "while", "continue", "export", "type"}
EVENT_FIELDS = ("group", "priority", "who", "trigger", "intent")
WHO = ("local", "actor", "crew", "all")


def presets_path(explicit=None):
    """(path, how): --presets, then $RR_FEEL_PRESETS, then the skill's own copy (read-only default)."""
    if explicit:
        p, how = Path(explicit), "--presets"
    elif os.environ.get("RR_FEEL_PRESETS"):
        p, how = Path(os.environ["RR_FEEL_PRESETS"]), "$RR_FEEL_PRESETS"
    else:
        p, how = SKILL / "presets" / "feel.json", "skill default copy: read-only, copy it into the project to edit"
    return (p / "feel.json" if p.is_dir() else p), how


def die(msg, code=2):
    print(msg)
    sys.exit(code)


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

    def value(self, key, default="?"):
        f = self.fact(key)
        return f["value"] if f else default

    def oq(self, oid):
        if oid not in self._oq:
            code, out = self.run("get", oid, "--json")
            try:
                self._oq[oid] = json.loads(out) if code == 0 else None
            except ValueError:
                self._oq[oid] = None
        return self._oq[oid]


# ------------------------------------------------------------------ model
class Model:
    """Raw presets + a resolved copy (numbers and hex only) that feelmath and the Luau generator use."""

    def __init__(self, path=None, bible=None):
        self.path, self.how = presets_path(path)
        if not self.path.is_file():
            die(f"presets not found: {self.path} ({self.how})")
        try:
            self.raw = json.loads(self.path.read_text(encoding="utf-8"))
        except ValueError as e:
            die(f"presets {self.path} are not valid JSON: {e}")
        self.bible = bible or Bible()
        self.refs, self.colours, self.problems, self.notes = [], [], [], []
        self.r = self._resolve(copy.deepcopy(self.raw), "")
        self.events = self.r["events"]

    def _resolve(self, node, where):
        if isinstance(node, dict):
            if "v" in node and "canon" in node and set(node) <= {"v", "canon", "scale", "note", "match"}:
                self.refs.append((where, node))
                return node["v"]
            return {k: self._resolve(v, f"{where}.{k}" if where else k) for k, v in node.items()}
        if isinstance(node, list):
            return [self._resolve(v, f"{where}[{i}]") for i, v in enumerate(node)]
        if isinstance(node, str) and node.startswith("@"):
            f = self.bible.fact(node[1:]) if self.bible.ok() else None
            self.colours.append((where, node, f))
            if f and HEX_RE.match(str(f["value"])):
                return f["value"].upper()
            self.problems.append(f"{where}: colour {node} is not a hex token in rr-bible")
            return "#FF00FF"
        return node

    def phone(self):
        w, h = (int(x) for x in NUM_RE.findall(str(self.r["meta"]["phone"]))[:2])
        return fm.PhoneView(w, h, float(self.r["meta"]["fov_deg"]))

    def names(self, sel="all"):
        ev = self.events
        if sel in (None, "", "all"):
            return list(ev)
        if sel in ev:
            return [sel]
        if "," in sel:
            bad = [n for n in sel.split(",") if n not in ev]
            if bad:
                die(f"unknown events: {', '.join(bad)}")
            return sel.split(",")
        g = [n for n, e in ev.items() if e.get("group") == sel]
        if not g:
            die(f"no event or group {sel!r}; groups: {', '.join(sorted({e['group'] for e in ev.values()}))}")
        return g

    def source(self, full=True):
        """Presets file: the full path and how it was chosen (commands), or the last three parts (exports)."""
        return f"{self.path} ({self.how})" if full else "/".join(self.path.parts[-3:])


# ------------------------------------------------------------------ metrics
def is_red(hexcol):
    r, g, b = (int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return s > 0.45 and 0.2 < l < 0.8 and (h < 0.04 or h > 0.96)


def metrics(model, name, reduce_motion=False, profile="default", sample=None):
    """Measured peaks for one event (phone pixels from the canon phone size and FOV); cached per model."""
    key = (name, reduce_motion, profile)
    cache = model.__dict__.setdefault("_mcache", {})
    if sample is None and key in cache:
        return dict(cache[key])
    m = _metrics(model, name, reduce_motion, profile, sample)
    if sample is None:
        cache[key] = dict(m)
    return m


def _metrics(model, name, reduce_motion, profile, sample):
    r = model.r
    s = sample or fm.sample_event(r, name, reduce_motion=reduce_motion, profile=profile)
    L, pv, lim = s["lanes"], model.phone(), r["limits"]
    near = float(r["meta"]["near_depth_studs"])

    def peak(pred):
        vals = [abs(v) for k, lane in L.items() if pred(k) for v in lane]
        return max(vals) if vals else 0.0

    def axis_peak(axis):
        return peak(lambda k: k.startswith("cam:" + axis)) + peak(lambda k: ":camkick:" in k and k.endswith(":" + axis))

    m = {"event": name, "tier": model.events[name]["priority"], "rm": reduce_motion, "profile": profile}
    m["trauma"] = peak(lambda k: k == "cam:trauma")
    m["shake"] = peak(lambda k: k == "cam:shake")
    rot = math.hypot(axis_peak("pitch"), axis_peak("yaw"))
    trans = math.hypot(peak(lambda k: k == "cam:x"), peak(lambda k: k == "cam:y"))
    m["cam_deg"] = round(rot, 3)
    m["roll_deg"] = round(axis_peak("roll"), 3)
    m["cam_px"] = round(pv.deg_px(rot) + pv.studs_px(trans, near) + pv.roll_edge_px(m["roll_deg"]) * 0.5, 1)
    m["kick_deg"] = round(max(peak(lambda k: ":camkick:" in k and k.endswith(a)) for a in (":pitch", ":yaw", ":roll")), 3)
    m["fov_deg"] = round(peak(lambda k: k.endswith(":fovkick")), 2)
    m["hitstop_ms"] = round(sum(b - a for a, b in s["meta"]["hitstop"]) * 1000)
    fl_screen, fl_count, fl_red = 0.0, 0, False
    for ch, d in s["meta"]["channels"]:
        if ch["type"] == "flash" and ch["scope"] in ("screen", "vignette"):
            fl_count += 1
            if is_red(ch["color"]):
                fl_red = True
    for k, lane in L.items():
        if ":flash:" in k and not k.endswith(":element"):
            fl_screen = max(fl_screen, max(lane))
    m["flash_peak"] = round(fl_screen, 3)
    m["flash_count"] = fl_count
    m["flash_red"] = fl_red
    m["punch_scale"] = round(peak(lambda k: ":punch:" in k and k.endswith(":scale")), 3)
    m["punch_px"] = round(peak(lambda k: ":punch:" in k and (k.endswith(":x_px") or k.endswith(":y_px"))), 2)
    m["fov_signed"] = 0.0
    fl = [v for k, lane in L.items() if k.endswith(":fovkick") for v in lane]
    if fl:
        m["fov_signed"] = round(max(fl, key=abs), 2)
    pulses = [ch for ch, _ in s["meta"]["channels"] if ch["type"] == "pulse"]
    m["pulse_depth"] = round(max([abs(ch["max"] - ch["min"]) for ch in pulses] + [0.0]), 3)
    hap = [v for k, lane in L.items() if k.endswith(":haptic") for v in lane]
    m["haptic_peak"] = round(max(hap) if hap else 0.0, 3)
    m["haptic_ms"] = round(sum(1 for v in hap if v > 0.01) * 1000 / 60)
    loops = [ch for ch, _ in s["meta"]["channels"] if ch["type"] == "pulse" and not ch.get("dur")]
    finite = [d + fm.channel_len(r, ch) for ch, d in s["meta"]["channels"] if ch not in loops]
    m["total_s"] = round(max(finite + [0.0]) + m["hitstop_ms"] / 1000, 3)
    m["loops"] = len(loops)
    # what still carries the event (canon av.feel.reduce_motion: colour, haptics or sound); "visible" needs a
    # change a player can see on a phone (limits.visible_scale_min, limits.punch_px_min)
    vis_scale, vis_px = lim.get("visible_scale_min", 0.03), lim.get("punch_px_min", 1.5)
    comm = []
    if any((":tween:" in k and k.endswith((":alpha", ":fadealpha")) and max(v) - min(v) > 0.05) or
           (":pulse:" in k and max(v) - min(v) > 0.05) for k, v in L.items()):
        comm.append("alpha")
    if m["flash_peak"] > 0 or any(":flash:" in k and max(v) > 0.05 for k, v in L.items()):
        comm.append("flash")
    if any(":tween:" in k and k.endswith((":scale", ":rot", ":count")) and
           max(v) - min(v) > (vis_scale if k.endswith(":scale") else 0.01) for k, v in L.items()):
        comm.append("tween")
    if m["punch_scale"] >= vis_scale or m["punch_px"] >= vis_px:
        comm.append("punch")
    if m["cam_px"] > lim.get("kick_px_min", 1.5) or abs(m["fov_signed"]) > 0.5:
        comm.append("camera")
    cues = [ch for ch, _ in s["meta"]["channels"] if ch["type"] == "cue"]
    if any(ch.get("vfx") for ch in cues):
        comm.append("vfx")
    if any(ch.get("sfx") for ch in cues):
        comm.append("sound")
    if m["haptic_peak"] > 0:
        comm.append("haptic")
    m["communicates"] = comm
    m["reaches_all"] = [c for c in comm if c != "haptic"]   # PC and most tablets have no haptic motor
    w = lim["loudness_weights"]
    tw = [abs(ch["to"] - ch["from"]) for ch, _ in s["meta"]["channels"] if ch["type"] == "tween" and ch.get("prop") == "scale"]
    m["scale_travel"] = round(max(tw + [0.0]) * (0 if reduce_motion else 1), 3)
    hud = max(min(1, m["punch_px"] / lim.get("hud_px_ref", 5)), m["pulse_depth"], min(1, m["scale_travel"]))
    parts = {"shake": m["shake"], "camkick": min(1, m["kick_deg"] / lim["kick_deg_max"]),
             "hitstop": min(1, m["hitstop_ms"] / lim["hitstop_ms_max"]),
             "flash": min(1, m["flash_peak"] / r["a11y"]["flash"]["screen_peak_max"]),
             "fovkick": min(1, m["fov_deg"] / lim["fov_delta_max"]), "haptic": m["haptic_peak"] * min(1, m["haptic_ms"] / 300),
             "punch": min(1, m["punch_scale"] / lim["punch_scale_amp_max"]), "hud": hud}
    m["loudness"] = round(sum(w.get(k, 0) * v for k, v in parts.items()) / sum(w.values()), 3)
    return m


def sustain_metrics(model):
    r, pv = model.r, model.phone()
    sh, near = r["shake"], float(r["meta"]["near_depth_studs"])
    out = {}
    for src, floor in (("speed", r["sustain"]["speed"]["gain"]), ("pressure", r["sustain"]["pressure"]["gain"]),
                       ("both", min(sh["sustain_cap"], r["sustain"]["speed"]["gain"] + r["sustain"]["pressure"]["gain"]))):
        floor = min(floor, sh["sustain_cap"])
        s = floor ** sh["power"]
        px = pv.deg_px(math.hypot(sh["max_angle_deg"][0], sh["max_angle_deg"][1]) * s) + \
            pv.studs_px(math.hypot(*sh["max_offset_studs"][:2]) * s, near) + pv.roll_edge_px(sh["max_angle_deg"][2] * s) * 0.5
        out[src] = {"floor": round(floor, 3), "shake": round(s, 4), "px_max": round(px, 2)}
    return out


# ------------------------------------------------------------------ validate
UNIT_RE = re.compile(r"(?:\+-|±)?\s*-?\d+(?:\.\d+)?(?:\s*(?:(?:px|ms|s|deg|studs|x)\b|%))?")
FWD_RE = re.compile(r"\b(?:leans?|lurch(?:es)?|pitch(?:es)?|tips?|thrown|jolts?|dips?)\s+forward\b|\bnods?\b|\bdips?\b")
BACK_RE = re.compile(r"\b(?:leans?|lurch(?:es)?|pitch(?:es)?|tips?|thrown|pushed|rocks?)\s+back(?:ward)?\b")
STOP = {"with", "from", "that", "this", "when", "what", "where", "which", "does", "into", "only", "their", "there",
        "they", "them", "then", "than", "each", "every", "missing", "canon", "event", "events", "default", "before",
        "after", "about", "over", "under", "once", "just", "plays", "play", "same", "more", "most", "some", "your"}


def first_num(text):
    m = NUM_RE.search(str(text).replace("+-", " ").replace("±", " "))
    return float(m.group()) if m else None


def canon_phrase(fact, want):
    """The unit-tagged phrase in a fact whose number is `want` (suggested as a ref's "match")."""
    fact = str(fact)
    for m in UNIT_RE.finditer(fact):
        n = first_num(m.group())
        if n is not None and abs(abs(n) - abs(want)) < 1e-6:
            ph = m.group().strip()
            return ph[1:] if ph.startswith("-") and m.start() > 0 and fact[m.start() - 1].isdigit() else ph
    return None


def words(text):
    return {w.rstrip("s") for w in re.findall(r"[a-z]{4,}", str(text).lower().replace("_", " ")) if w not in STOP}


def hierarchy(model, loud=None):
    """{event: [(higher-tier event, its loudness), ...]} for every higher-tier event this one outshouts."""
    loud = loud or {n: (int(e["priority"]), metrics(model, n)["loudness"]) for n, e in model.events.items()}
    out = {}
    for n, (t, l) in loud.items():
        out[n] = sorted([(o, lo) for o, (to, lo) in loud.items() if to < t and l > lo + 1e-9], key=lambda x: x[1])
    return out, loud


def shake_px(model, trauma):
    """Upper bound of the camera motion one shake channel adds on the phone (trauma -> shake = trauma^power)."""
    r, pv = model.r, model.phone()
    sh, near = r["shake"], float(r["meta"]["near_depth_studs"])
    s = min(1.0, trauma) ** sh["power"]
    return pv.deg_px(math.hypot(*sh["max_angle_deg"][:2]) * s) + pv.studs_px(math.hypot(*sh["max_offset_studs"][:2]) * s, near) \
        + pv.roll_edge_px(sh["max_angle_deg"][2] * s) * 0.5


def oq_ids(model):
    """(where, OQ id, context words) for every OQ cited by an event or a global section."""
    r, out = model.r, []
    for name, ev in r["events"].items():
        ctx = words(" ".join([name, ev.get("group", ""), ev.get("trigger", ""), ev.get("intent", "")] + list(ev.get("canon", []))))
        out += [(f"events.{name}", o, ctx) for o in ev.get("oq", [])]
    out += [("lever", o, words("lever pull junction fork drag console input " + json.dumps(r["lever"]))) for o in r["lever"].get("oq", [])]
    out += [("a11y", o, words("feel accessibility settings reduce motion shake flashes haptics")) for o in r["a11y"].get("oq", [])]
    po = r["sustain"]["pressure"].get("oq")
    if po:
        out.append(("sustain.pressure", po, words("boiler pressure gauge redline rumble")))
    return out


def validate(model, strict=False):
    r, raw, b, notes = model.r, model.raw, model.bible, model.notes
    for name, ev in raw.get("events", {}).items():
        for i, ch in enumerate(ev.get("channels", [])):
            col = ch.get("color")
            if isinstance(col, str) and not col.startswith("@") and col.upper() not in NEUTRALS:
                model.problems.append(f"events.{name}.channels[{i}]: colour {col} is not a token: use @key "
                                      "(or #FFFFFF / #000000)")
    errs, warns = list(dict.fromkeys(model.problems)), []
    if not b.ok():
        errs.append("rr-bible not found: canon cannot be checked (set RR_BIBLE_SKILL)")
    for key in ("meta", "roles", "shake", "sustain", "lever", "a11y", "profiles", "limits", "events"):
        if key not in r:
            errs.append(f"missing top-level section {key!r}")
    if errs:
        return errs, warns
    # canon agreement: strings equal the fact; numbers are bound to a phrase of the fact ("match") whose first
    # number is v x scale (sign ignored); without match the number must appear, and must be unambiguous
    for where, ref in model.refs:
        f = b.fact(ref["canon"]) if b.ok() else None
        if not f:
            errs.append(f"{where}: canon key {ref['canon']} not in rr-bible")
            continue
        if f["status"] == "superseded":
            errs.append(f"{where}: {ref['canon']} is superseded")
        elif f["status"] == "conflict":
            warns.append(f"{where}: {ref['canon']} is a conflict: label output 'assumed (OQ default)'")
        v, fact = ref["v"], str(f["value"])
        full = fact + " | " + str(f.get("note") or "")
        if isinstance(v, str):
            if v.strip().lower() != fact.strip().lower():
                errs.append(f"{where}: {v!r} contradicts canon {ref['canon']} = {fact!r}")
            continue
        want = v * ref.get("scale", 1)
        if "match" in ref:
            mt = str(ref["match"])
            n = first_num(mt)
            if mt.lower() not in full.lower():
                errs.append(f"{where}: match {mt!r} is not in canon {ref['canon']} = {full!r}")
            elif n is None or abs(abs(n) - abs(want)) > 1e-6:
                errs.append(f"{where}: {v} disagrees with canon {ref['canon']}: {mt!r} says {n}")
            continue
        nums = {abs(float(x)) for x in NUM_RE.findall(fact.replace("+-", " "))}
        if not any(abs(n - abs(want)) < 1e-6 for n in nums):
            errs.append(f"{where}: {v} not found in canon {ref['canon']} = {fact!r}")
        elif len(nums) > 1:
            warns.append(f"{where}: canon {ref['canon']} holds several numbers; bind the value with \"match\": "
                         f"{json.dumps(canon_phrase(fact, want) or str(want))}")
    # colours
    for where, tok, f in model.colours:
        if f and f["status"] == "superseded":
            errs.append(f"{where}: colour {tok} is superseded")
        elif f and f["status"] in ("conflict",):
            warns.append(f"{where}: colour {tok} is undecided ({f['status']})")
    # roles, events, channels
    roles = set(r["roles"])
    groups = {}
    for name, ev in r["events"].items():
        where = f"events.{name}"
        for fld in EVENT_FIELDS:
            if fld not in ev:
                errs.append(f"{where}: missing {fld}")
        if ev.get("who") not in WHO:
            errs.append(f"{where}: who must be one of {WHO}")
        if str(ev.get("priority")) not in r["limits"]["tiers"]:
            errs.append(f"{where}: priority must be 1-5")
        groups.setdefault(ev.get("group"), []).append(name)
        for k in ev.get("canon", []):
            if b.ok() and not b.fact(k):
                errs.append(f"{where}: cites unknown canon {k}")
        if ev.get("alert") and b.ok() and not b.fact(ev["alert"]):
            errs.append(f"{where}: alert {ev['alert']} not in gameplay.alerts")
        for inc in ev.get("include", []):
            if inc.get("event") not in r["events"]:
                errs.append(f"{where}: include {inc.get('event')!r} is not an event")
        try:
            fm.expand(r, name)
        except (ValueError, RecursionError, KeyError) as e:
            errs.append(f"{where}: {e}")
            continue
        for i, ch in enumerate(ev.get("channels", [])):
            errs += check_channel(r, f"{where}.channels[{i}]", ch, roles, ev)
    for g, names in groups.items():
        if len(names) > 7:
            warns.append(f"group {g}: {len(names)} events (keep <= 7: two images per critic)")
    # open questions: exist, still open, and about this event (OQ numbers race between parallel skills)
    for where, oid, ctx in oq_ids(model):
        if re.match(r"^OQ-TBD", oid):
            notes.append(f"{where}: {oid} is an unrecorded question: the owner records it (bible.py add-question "
                         "TITLE --option 'A: ..' --option 'B: ..' --default 'A (why)' --src IDS --affects KEYS), "
                         "then the preset cites the new number")
            continue
        o = b.oq(oid) if b.ok() else {}
        if o is None:
            errs.append(f"{where}: {oid} not found in rr-bible")
            continue
        if not o:
            continue
        if o.get("fields", {}).get("status", "open") != "open":
            warns.append(f"{where}: {oid} is no longer open: update the preset to the decision")
        title = o.get("title", "")
        if ctx and not (words(title) & ctx):
            warns.append(f"{where}: {oid} is {title!r}, which shares no word with what cites it: wrong number? "
                         "(cite OQ-TBD-<slug> until the owner records it)")
    if errs:
        return errs, warns
    # alert coverage
    if b.ok():
        alert_ids = [k for k in (b._files.get("gameplay") or {}) if k.startswith("gameplay.alerts.")
                     and not re.search(r"\.(life_\w+|transport|first_hints)$", k)]
        covered = {ev.get("alert") for ev in r["events"].values()}
        for k in alert_ids:
            if k not in covered:
                warns.append(f"alert {k} has no feel event")
    # comfort limits, visibility, reduce motion, direction
    lim, a11y, pv = r["limits"], r["a11y"]["flash"], model.phone()
    loud = {}
    for name, ev in r["events"].items():
        tier = str(ev["priority"])
        m = metrics(model, name)
        loud[name] = (int(tier), m["loudness"])
        where = f"events.{name}"
        if m["cam_px"] > lim["tier_shake_px"][tier]:
            errs.append(f"{where}: camera moves {m['cam_px']} px on a phone; tier {tier} limit {lim['tier_shake_px'][tier]}")
        if m["roll_deg"] > lim["roll_deg_max"]:
            errs.append(f"{where}: roll {m['roll_deg']} deg > {lim['roll_deg_max']}")
        if m["kick_deg"] > lim["kick_deg_max"]:
            errs.append(f"{where}: camera kick {m['kick_deg']} deg > {lim['kick_deg_max']}")
        kick_px = pv.deg_px(m["kick_deg"])
        if 0 < kick_px < lim.get("kick_px_min", 0):
            warns.append(f"{where}: camera kick peaks at {kick_px:.1f} px on a phone, under {lim['kick_px_min']} px: "
                         "nobody will see it (raise it or drop it)")
        for i, ch in enumerate(ev.get("channels", [])):
            if ch["type"] == "shake":
                px = shake_px(model, ch["trauma"])
                if px < lim.get("kick_px_min", 0):
                    warns.append(f"{where}.channels[{i}]: shake trauma {ch['trauma']} peaks at {px:.1f} px on a phone "
                                 f"(shake = trauma^{r['shake']['power']}): invisible; raise it or use a camkick")
            if ch["type"] == "punch" and ch["prop"] in ("x_px", "y_px") and abs(ch["amp"]) < lim.get("punch_px_min", 0):
                warns.append(f"{where}.channels[{i}]: punch of {abs(ch['amp'])} px is under {lim['punch_px_min']} px: invisible")
            if ch["type"] == "camkick" and ch["angles_deg"][0]:
                txt = f"{ev.get('intent', '')} {ev.get('trigger', '')}".lower()
                p = ch["angles_deg"][0]
                if p > 0 and FWD_RE.search(txt):
                    warns.append(f"{where}.channels[{i}]: pitch {p:+g} tips the view UP (Roblox: + looks up), but the "
                                 "intent says forward/nod/dip: use a negative pitch")
                elif p < 0 and BACK_RE.search(txt):
                    warns.append(f"{where}.channels[{i}]: pitch {p:+g} tips the view DOWN, but the intent says "
                                 "back: use a positive pitch (Roblox: + looks up)")
        if m["fov_deg"] > lim["fov_delta_max"]:
            errs.append(f"{where}: FOV kick {m['fov_deg']} > {lim['fov_delta_max']}")
        if m["hitstop_ms"] > lim["hitstop_ms_max"]:
            errs.append(f"{where}: hit-stop {m['hitstop_ms']} ms > {lim['hitstop_ms_max']}")
        cap = lim["fail_s_max"] if tier == "1" else lim["event_s_max"]
        if m["total_s"] > cap:
            errs.append(f"{where}: lasts {m['total_s']} s > {cap}")
        if m["flash_count"] > a11y["per_second_max"]:
            errs.append(f"{where}: {m['flash_count']} screen flashes > {a11y['per_second_max']} per second")
        if ev["priority"] > 2 and any(ch["type"] == "flash" and is_red(ch["color"]) for ch, _ in fm.expand(r, name)):
            errs.append(f"{where}: red flash on a tier {tier} event; red is only the danger signal (style.dont.red_decoration)")
        rmm = metrics(model, name, reduce_motion=True)
        if not rmm["reaches_all"] and not ev.get("rm_reads"):
            left = ", ".join(rmm["communicates"]) or "nothing"
            errs.append(f"{where}: with Reduce Motion on only {left} is left (av.feel.reduce_motion): keep a visible "
                        "channel (alpha, colour flash, scale >= limits.visible_scale_min) or a sound cue, or say in "
                        "rm_reads what still shows it (a haptic alone misses PC and most tablets)")
        lm = metrics(model, name, profile="loud")
        if lm["cam_px"] > lim["tier_shake_px"][tier] * 1.25:
            warns.append(f"{where}: loud profile moves the camera {lm['cam_px']} px (tier {tier} limit x1.25)")
    # hierarchy: a lower tier may beat single events of a higher tier, never most of it (median); pairs are noted
    pairs, _ = hierarchy(model, loud)
    for hi in sorted({t for t, _ in loud.values()}):
        med = statistics.median(l for t, l in loud.values() if t == hi)
        for name, (t, l) in loud.items():
            if t > hi and l > med + 1e-9:
                warns.append(f"hierarchy: {name} (tier {t}, loudness {l}) is louder than most tier {hi} events "
                             f"(median {med:.3f})")
    n_pairs = sum(len(v) for v in pairs.values())
    if n_pairs:
        notes.append(f"hierarchy: {n_pairs} single pairs where a lower tier outshouts a higher-tier event "
                     "(feel.py show EVENT lists them; never claim 'quieter than every X' without checking)")
    for src in ("speed", "pressure"):
        if r["sustain"][src]["gain"] > r["shake"]["sustain_cap"]:
            errs.append(f"sustain {src}: gain {r['sustain'][src]['gain']} > sustain_cap {r['shake']['sustain_cap']} "
                        "(the rumble would flatten before its maximum)")
    for src, sm in sustain_metrics(model).items():
        if sm["px_max"] > lim["sustain_px_max"]:
            errs.append(f"sustain {src}: {sm['px_max']} px of constant camera motion > {lim['sustain_px_max']} (stable_train)")
    # lever
    lv = r["lever"]
    if not 0.3 <= lv["detent"] <= 0.95:
        errs.append("lever.detent must be 0.3-0.95")
    if "notch" in lv and not 0.2 <= lv["notch"] < lv["detent"]:
        errs.append("lever.notch must be 0.2 or more and below lever.detent (the tick is felt before the commit)")
    for k in ("detent_event", "commit_event", "snapback_event"):
        if lv.get(k) not in r["events"]:
            errs.append(f"lever.{k}: {lv.get(k)!r} is not an event")
    for k in ("snap", "snapback"):
        errs += check_ease(f"lever.{k}", lv[k])
    # profiles
    for p, d in r["profiles"].items():
        if p == "about":
            continue
        for k, v in d.items():
            if k in ("flash", "hitstop") and v > 1:
                errs.append(f"profiles.{p}.{k} = {v}: flashes and hit-stop never go above default")
    # cue names against the sibling skills (a missing sibling is a note, not a failure)
    for label, skill, env, rel, key, field in (("rr-vfx-lighting preset", "rr-vfx-lighting", "RR_VFX_SKILL", "presets/vfx.json", "presets", "vfx"),
                                               ("rr-soundsmith sound", "rr-soundsmith", "RR_SOUND_SKILL", "presets/soundmap.json", "sounds", "sfx")):
        sib = find_sibling(skill, env)
        known = set()
        if sib and (sib / rel).is_file():
            try:
                known = set(json.loads((sib / rel).read_text(encoding="utf-8")).get(key, {}))
            except ValueError:
                known = set()
        used = sorted({(n, ch[field]) for n, ev in r["events"].items() for ch in ev.get("channels", [])
                       if ch["type"] == "cue" and ch.get(field)})
        if not known and used:
            notes.append(f"{field} cue names unchecked: {skill} not found (set {env})")
        for n, c in used:
            if known and c not in known:
                errs.append(f"events.{n}: {field} cue {c} is not an {label}")
    if strict and warns:
        errs += [f"(strict) {w}" for w in warns]
    return errs, warns


def check_ease(where, ch):
    out = []
    if ch.get("style", "Quad") not in fm.STYLES:
        out.append(f"{where}: style {ch.get('style')!r} is not an Enum.EasingStyle")
    if ch.get("dir", "Out") not in fm.DIRECTIONS:
        out.append(f"{where}: dir {ch.get('dir')!r} is not an Enum.EasingDirection")
    return out


def check_channel(r, where, ch, roles, ev):
    lim, out = r["limits"], []
    t = ch.get("type")
    if t not in REQUIRED:
        return [f"{where}: unknown channel type {t!r}"]
    for k in REQUIRED[t]:
        if k not in ch:
            out.append(f"{where}: {t} needs {k}")
    if out:
        return out
    if "target" in ch and ch["target"] not in roles:
        out.append(f"{where}: target {ch['target']!r} is not a role (roles: {', '.join(sorted(roles))})")
    if t in PROPS and ch.get("prop") not in PROPS[t]:
        out.append(f"{where}: {t} prop must be one of {PROPS[t]}")
    rm = ch.get("rm")
    if rm is not None and not (isinstance(rm, (int, float)) and 0 <= rm <= 1) and rm not in ("fade", "snap", "skip", "keep"):
        out.append(f"{where}: rm must be 0..1 or fade|snap|skip|keep")
    for k in ("dur", "in", "out", "hold", "delay", "period"):
        if k in ch and not (isinstance(ch[k], (int, float)) and ch[k] >= 0):
            out.append(f"{where}: {k} must be a number >= 0")
    if t == "tween":
        out += check_ease(where, ch)
        if ch.get("before", "from") not in ("from", "rest", "hidden"):
            out.append(f"{where}: before must be from, rest or hidden")
        if ch["dur"] <= 0:
            out.append(f"{where}: dur must be > 0")
    if t == "punch":
        lo, hi = lim["punch_freq_hz"]
        if not lo <= ch["freq_hz"] <= hi:
            out.append(f"{where}: freq_hz {ch['freq_hz']} outside {lo}-{hi}")
        if ch.get("shape", "sin") not in ("sin", "cos", "noise"):
            out.append(f"{where}: shape must be sin, cos or noise")
        if ch.get("shape") != "noise":
            dlo, dhi = lim["damping"]
            if not dlo <= ch.get("damping", 0.3) <= dhi:
                out.append(f"{where}: damping outside {dlo}-{dhi}")
            z, shape = ch.get("damping", 0.3), ch.get("shape", "sin")
            resid = abs(fm.spring(ch["dur"] - 1e-3, 1, ch["freq_hz"], z, shape)) / fm.peak_gain(ch["freq_hz"], z, shape, ch["dur"])
            if resid > 0.05:
                out.append(f"{where}: spring still at {resid:.0%} of its peak when it ends: raise dur or damping (visible snap)")
        if ch["prop"] == "scale" and ch["amp"] > lim["punch_scale_amp_max"]:
            out.append(f"{where}: scale punch {ch['amp']} > {lim['punch_scale_amp_max']}")
    if t == "camkick":
        if len(ch["angles_deg"]) != 3:
            out.append(f"{where}: angles_deg is [pitch, yaw, roll]")
        dlo, dhi = lim["damping"]
        if not dlo <= ch.get("damping", 0.4) <= dhi:
            out.append(f"{where}: damping outside {dlo}-{dhi}")
        flo, fhi = lim.get("camkick_freq_hz", [0.5, 14])
        if not flo <= ch["freq_hz"] <= fhi:
            out.append(f"{where}: camkick freq_hz {ch['freq_hz']} outside {flo}-{fhi}")
    if t == "shake" and not 0 < ch["trauma"] <= 1:
        out.append(f"{where}: trauma must be in (0, 1]")
    if t == "hitstop" and ev.get("who") == "crew":
        out.append(f"{where}: hit-stop on a crew event; it belongs to the actor's client (av.feel.hitstop_local)")
    if t == "flash":
        if ch["scope"] not in ("screen", "vignette", "element"):
            out.append(f"{where}: scope must be screen, vignette or element")
        if ch["scope"] == "element" and "target" not in ch:
            out.append(f"{where}: element flash needs a target")
        if not HEX_RE.match(str(ch["color"])):
            out.append(f"{where}: color must be @token or #hex")
        elif ch["scope"] != "element":
            cap = r["a11y"]["flash"]["red_peak_max"] if is_red(ch["color"]) else r["a11y"]["flash"]["screen_peak_max"]
            if ch["peak"] > cap:
                out.append(f"{where}: flash peak {ch['peak']} > {cap} (photosensitivity cap)")
            if ch["in"] < 0.02:
                out.append(f"{where}: flash in < 0.02 s (a one-frame strobe)")
    if t == "fovkick" and abs(ch["delta_deg"]) > lim["fov_delta_max"]:
        out.append(f"{where}: FOV delta {ch['delta_deg']} > {lim['fov_delta_max']}")
    if t == "haptic":
        if ch["effect"] not in HAPTIC_TYPES:
            out.append(f"{where}: effect must be an Enum.HapticEffectType ({', '.join(HAPTIC_TYPES)})")
        ks = ch["keys"]
        if not ks or any(len(k) != 2 or not 0 <= k[1] <= 1 for k in ks):
            out.append(f"{where}: keys are [[ms, 0..1], ...]")
        elif [k[0] for k in ks] != sorted(k[0] for k in ks):
            out.append(f"{where}: keys must be sorted by ms")
        elif ks[-1][0] - ks[0][0] > lim["haptic_ms_max"]:
            out.append(f"{where}: haptic lasts {ks[-1][0] - ks[0][0]} ms > {lim['haptic_ms_max']}")
        elif ks[-1][1] != 0:
            out.append(f"{where}: last key must be 0 (a motor left running)")
    if t == "pulse" and ch["period"] < 0.5:
        out.append(f"{where}: pulse period {ch['period']} < 0.5 s flickers (photosensitivity)")
    if t == "pulse" and not ch["min"] < ch["max"]:
        out.append(f"{where}: pulse min {ch['min']} must be below max {ch['max']} (swapped range)")
    if t == "cue" and not (ch.get("sfx") or ch.get("vfx")):
        out.append(f"{where}: cue needs sfx or vfx")
    return out


# ------------------------------------------------------------------ spec
def fmt(x):
    return f"{x:g}" if isinstance(x, (int, float)) else str(x)


def channel_line(ch, d, pv):
    t = ch["type"]
    tgt = ch.get("target", "camera" if t in ("shake", "camkick", "fovkick") else "screen" if t == "flash" else "-")
    if t == "tween":
        what = f"{ch['prop']} {fmt(ch['from'])} -> {fmt(ch['to'])}, {ch.get('style', 'Quad')} {ch.get('dir', 'Out')}"
        span = ch["dur"]
    elif t == "punch":
        what = f"{ch['prop']} punch peak {fmt(ch['amp'])} ({ch.get('shape', 'sin')}, {fmt(ch['freq_hz'])} Hz, damping {fmt(ch.get('damping', 0.3))})"
        span = ch["dur"]
    elif t == "camkick":
        p, y, rr = ch["angles_deg"]
        what = (f"kick peak pitch {fmt(p)} ({'view up' if p > 0 else 'view down' if p < 0 else '-'}) yaw {fmt(y)} roll {fmt(rr)} deg"
                f"{' toward the pulled side' if ch.get('side_sign') else ''}, {fmt(ch['freq_hz'])} Hz")
        span = ch["dur"]
    elif t == "shake":
        what = f"add trauma {fmt(ch['trauma'])}"
        span = None
    elif t == "hitstop":
        what = f"freeze own effects {ch['ms']} ms"
        span = ch["ms"] / 1000
    elif t == "flash":
        what = f"{ch['scope']} flash {ch['color']} to {fmt(ch['peak'])} (in {fmt(ch['in'])}, hold {fmt(ch.get('hold', 0))}, out {fmt(ch['out'])})"
        span = ch["in"] + ch.get("hold", 0) + ch["out"]
    elif t == "fovkick":
        what = f"FOV {ch['delta_deg']:+g} deg (in {fmt(ch['in'])}, hold {fmt(ch.get('hold', 0))}, out {fmt(ch['out'])})"
        span = ch["in"] + ch.get("hold", 0) + ch["out"]
    elif t == "haptic":
        what = f"haptic {ch['effect']}: " + ", ".join(f"{k[0]}ms {fmt(k[1])}" for k in ch["keys"])
        span = ch["keys"][-1][0] / 1000
    elif t == "pulse":
        what = f"{ch['prop']} pulse {fmt(ch['min'])}-{fmt(ch['max'])} every {fmt(ch['period'])} s"
        span = ch.get("dur") or "loop"
    else:
        what = "cue " + ", ".join(f"{k} {ch[k]}" for k in ("sfx", "vfx") if ch.get(k))
        span = None
    end = f"{d + span:.2f}" if isinstance(span, (int, float)) else (span or "")
    return f"| {d:.2f} | {end} | {t} | {tgt} | {what} |"


def spec_event(model, name):
    ev, r, pv = model.events[name], model.r, model.phone()
    raw = model.raw["events"][name]
    m, rm = metrics(model, name), metrics(model, name, reduce_motion=True)
    tier = r["limits"]["tiers"][str(ev["priority"])]
    out = [f"## {name}", f"*{ev['group']} · tier {ev['priority']} ({tier}) · plays for: {ev['who']}*", "",
           f"- **Intent:** {ev['intent']}", f"- **Trigger:** {ev['trigger']}"]
    if ev.get("alert"):
        out.append(f"- **Alert text (verbatim):** {model.bible.value(ev['alert'])}  (`{ev['alert']}`)")
    if ev.get("include"):
        out.append("- **Includes:** " + ", ".join(f"{i['event']} (+{i.get('delay', 0)} s)" for i in ev["include"]))
    cites = list(ev.get("canon", [])) + [ref["canon"] for w, ref in model.refs if w.startswith(f"events.{name}.")]
    if cites:
        out.append("- **Canon:** " + "; ".join(f"`{k}` = {model.bible.value(k)}" for k in dict.fromkeys(cites)))
    if ev.get("oq"):
        out.append("- **Open:** " + "; ".join(f"{o} (unrecorded: owner gate)" if o.startswith("OQ-TBD") else
                                              f"{o} (default in use; label 'assumed ({o} default)')" for o in ev["oq"]))
    out += ["", "| start s | end s | channel | target | what |", "|---|---|---|---|---|"]
    out += [channel_line(ch, d, pv) for ch, d in fm.expand(r, name)]
    out += ["", f"- **Measured (phone {r['meta']['phone']}, FOV {r['meta']['fov_deg']}):** camera {m['cam_px']} px "
            f"(roll {m['roll_deg']} deg), kick {m['kick_deg']} deg, FOV {m['fov_deg']} deg, hit-stop {m['hitstop_ms']} ms, "
            f"screen flash {m['flash_peak']}, haptic {m['haptic_peak']} for {m['haptic_ms']} ms, lasts {m['total_s']} s"
            f"{' + loop' if m['loops'] else ''}, loudness {m['loudness']}.",
            f"- **Reduce motion:** camera {rm['cam_px']} px, FOV {rm['fov_deg']}; still reads through: "
            f"{', '.join(rm['communicates']) or 'nothing in the feel channels'}"
            f"{'; outside feel: ' + ev['rm_reads'] if ev.get('rm_reads') else ''}.",
            "- **Hierarchy:** " + hier_line(model, name),
            f"- **Studio check (owner):** trigger it from RR_FeelDemo; it should read as: {ev['intent']}.", ""]
    notes = [c.get("note") for c in raw.get("channels", []) if c.get("note")]
    if notes:
        out.insert(-1, "- **Notes:** " + " ".join(notes))
    return "\n".join(out)


def hier_line(model, name, pairs=None):
    pairs = pairs or hierarchy(model)[0]
    beats = pairs.get(name, [])
    if not beats:
        return "quieter than every event of a higher tier."
    return ("louder than " + ", ".join(f"{o} (tier {model.events[o]['priority']}, {lo:.2f})" for o, lo in beats)
            + f" at {metrics(model, name)['loudness']:.2f}; quieter than the rest of the higher tiers.")


def spec(model, sel="all"):
    names = model.names(sel)
    r = model.r
    head = [f"# Risky Rails feel spec ({TODAY})", "",
            f"Generated by rr-game-feel from `{model.source(full=False)}`; do not edit, regenerate (`feel.py spec`). "
            "Times are seconds from the event; motion channels run on the feel clock and hold during hit-stop; "
            "flashes, haptics, hit-stop and cues run on real time. Phone pixels use "
            f"`tech.ui_platform.phone` {r['meta']['phone']} and `tech.camera.fov_v` {r['meta']['fov_deg']}.", "",
            "Tiers: " + ", ".join(f"{k} {v}" for k, v in r["limits"]["tiers"].items()) +
            ". A lower tier is never louder than most of a higher tier (validate checks the median); single pairs "
            "where it is are listed per event under Hierarchy. Punch amps and kick angles are the delivered peaks; "
            "a positive pitch tips the view up.", ""]
    if sel in (None, "", "all"):
        sm = sustain_metrics(model)
        head += ["## Sustained shake (trauma floor)",
                 f"- Speed: floor = {r['sustain']['speed']['gain']} x Speed / {r['sustain']['speed']['ref']} "
                 f"(`av.vfx.speed_link`); at top speed {sm['speed']['px_max']} px.",
                 f"- Pressure: floor = {r['sustain']['pressure']['gain']} x clamp((p - {r['sustain']['pressure']['threshold']}) / "
                 f"{1 - r['sustain']['pressure']['threshold']:.2f}); at redline {sm['pressure']['px_max']} px (numbers: OQ-013 default).",
                 f"- Cap {r['shake']['sustain_cap']}: both at once {sm['both']['px_max']} px; reduce motion: 0.", "",
                 "## Lever drag", f"- Two-way (gameplay.fork.lever): the finger's travel u is signed, - left, + right. "
                 f"Knob = detent x (|u| / detent)^{r['lever']['resist']} (heavy); {r['lever']['detent_event']} ticks at "
                 f"{r['lever'].get('notch', r['lever']['detent']):.0%}, {r['lever']['commit_event']} fires once at "
                 f"{r['lever']['detent']:.0%} and the lever stays committed until the next junction (ctx.fork); the knob snaps home "
                 f"{r['lever']['snap']['style']} {r['lever']['snap']['dir']} {r['lever']['snap']['dur']} s. Released early: "
                 f"{r['lever']['snapback_event']} and a {r['lever']['snapback']['style']} {r['lever']['snapback']['dir']} "
                 f"{r['lever']['snapback']['dur']} s return. World handle throw +-{r['lever']['throw_deg']} deg. Input method: "
                 "OQ-031 (default A, drag).", ""]
    return "\n".join(head + [spec_event(model, n) for n in names]) + "\n"


# ------------------------------------------------------------------ Luau generation
def lua_val(v, ind=1):
    pad = "\t" * ind
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(float(v)) if isinstance(v, float) else str(v)
    if isinstance(v, str):
        if HEX_RE.match(v):
            r, g, b = (int(v[i:i + 2], 16) for i in (1, 3, 5))
            return f"Color3.fromRGB({r}, {g}, {b})"
        return json.dumps(v)
    if isinstance(v, list):
        return "{ " + ", ".join(lua_val(x, ind + 1) for x in v) + " }"
    if isinstance(v, dict):
        items = []
        for k, x in v.items():
            if k in ("about", "note", "intent", "trigger", "canon_link") and ind > 1:
                continue
            key = k if (re.match(r"^[A-Za-z_]\w*$", k) and k not in LUA_KEYWORDS) else f"[{json.dumps(k)}]"
            items.append(f"{pad}{key} = {lua_val(x, ind + 1)},")
        return "{\n" + "\n".join(items) + "\n" + "\t" * (ind - 1) + "}"
    return "nil"


def gen_presets_lua(model):
    r = copy.deepcopy(model.r)
    r.pop("preview", None)
    r.pop("roles", None)
    for ev in r["events"].values():
        ev.pop("intent", None)
        ev.pop("trigger", None)
        ev.pop("rm_reads", None)
        ev["priority"] = int(ev["priority"])
    body = lua_val(r, 1)
    return ("-- RR_FeelPresets (ModuleScript) - GENERATED by rr-game-feel feel.py build on " + TODAY + "\n"
            f"-- from {model.source(full=False)}. Do not edit: change that feel.json and rebuild (live tuning in Studio:\n"
            "-- Feel.Presets.events.<name>.channels[i].<knob> = value, then copy the numbers back into feel.json).\n"
            "-- Colours are rr-bible tokens; numbers marked canon in feel.json were checked against rr-bible.\n"
            "return " + body + "\n")


def luau_str_union(names):
    return "\n\t| ".join(json.dumps(n) for n in names)


def gen_typed_luau(model):
    """RR_FeelTyped.luau: the same RR_Feel module, cast once to a strict interface (event names, roles, settings)."""
    r = model.r
    roles = sorted(k for k in r["roles"] if k not in ("camera", "screen"))
    events = list(r["events"])
    profiles = [p for p in r["profiles"] if p != "about"]
    tgt = "\n".join(f"\t{k}: GuiObject?," for k in roles)
    return f"""--!strict
-- RR_FeelTyped (ModuleScript) - GENERATED by rr-game-feel feel.py build on {TODAY} from {model.source(full=False)}.
-- The RR_Feel runtime (untyped, Lua 5.1-compatible so the cloud tests can run it) cast once to a strict
-- interface: event names, target roles, settings and lever results are checked by the type checker.
-- Use it from --!strict code: local Feel = require(ReplicatedStorage.RRFeel.RR_FeelTyped)

local RR_Feel = require(script.Parent:WaitForChild("RR_Feel")) :: any

export type EventName =
\t| {luau_str_union(events)}

export type Targets = {{
{tgt}
}}

export type Ctx = {{
\ttargets: Targets?,
\tside: number?, -- -1 left branch, 1 right branch (camera yaw and roll follow it)
\tgain: number?,
\tcount: {{ amount: number, format: ((number) -> string)? }}?, -- pass the HUD's own money formatter
\tfork: any?, -- lever: the junction id; a new id re-arms the lever
}}

export type Handle = {{ Stop: (self: Handle) -> () }}
export type Setting = "reduceMotion" | "shake" | "flashes" | "haptics" | "profile"
export type Profile = {' | '.join(json.dumps(p) for p in profiles)}
export type LeverRelease = "committed" | "snapback"

export type Feel = {{
\tplay: (name: EventName, ctx: Ctx?) -> Handle,
\tplayFor: (name: EventName, actorUserId: number?, ctx: Ctx?) -> Handle?,
\taddTrauma: (amount: number) -> (),
\tsetSpeed: (speed: number) -> (),
\tsetPressure: (p01: number) -> (),
\thitStop: (ms: number) -> boolean,
\tleverDrag: (u: number, ctx: Ctx?) -> number, -- u signed -1..1; returns the knob position to draw
\tleverRelease: (ctx: Ctx?) -> LeverRelease,
\tleverReset: () -> (),
\tanimateValue: (from: number, to: number, spec: {{ style: string, dir: string, dur: number }}, onStep: (number) -> ()) -> {{ Stop: () -> () }},
\tfreezable: (emitter: ParticleEmitter) -> (),
\treset: (obj: GuiObject) -> (),
\tsetSetting: (key: Setting, value: any) -> (),
\tcurveDump: (n: number?) -> string,
\tsettings: {{ reduceMotion: boolean, shake: number, flashes: boolean, haptics: boolean, profile: Profile }},
\tCue: BindableEvent,
\tChanged: BindableEvent,
\tPresets: any,
}}

local Feel: Feel = RR_Feel
return Feel
"""


def syntax_gate(path):
    """(state, message): luau-compile (real Luau) if installed, else luaparse (Lua 5.1 grammar, .lua only), else SKIP."""
    import luau_check
    st, msg = luau_check.compile_check(path)
    if st != "SKIP":
        return st, msg
    lp = Path.home() / ".cache" / "rr-tools" / "node_modules" / "luaparse"
    node = shutil.which("node")
    if lp.is_dir() and node and path.suffix == ".lua":
        js = ("const lp=require(process.argv[1]);const fs=require('fs');"
              "try{lp.parse(fs.readFileSync(process.argv[2],'utf8'),{luaVersion:'5.1'});console.log('ok')}"
              "catch(e){console.log('ERR '+e.message);process.exit(1)}")
        r = subprocess.run([node, "-e", js, str(lp), str(path)], capture_output=True, text=True)
        return ("PASS" if r.returncode == 0 else "FAIL"), "luaparse (Lua 5.1 grammar): " + (r.stdout.strip() or r.stderr.strip()[-200:])
    return "SKIP", "syntax unchecked: no luau-compile or luaparse (python3 scripts/luau_check.py --install)"


def build(model, out, check=True):
    errs, warns = validate(model)
    print(f"presets: {model.source()}")
    if errs:
        print("build refused: validate failed\n  " + "\n  ".join(errs))
        return 1
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "RR_FeelPresets.lua").write_text(gen_presets_lua(model), encoding="utf-8")
    (out / "RR_FeelTyped.luau").write_text(gen_typed_luau(model), encoding="utf-8")
    for f in ("RR_Feel.lua", "RR_FeelMath.lua", "RR_FeelDemo.client.lua"):
        shutil.copy2(SKILL / "assets" / "luau" / f, out / f)
    (out / "FEEL_SPEC.md").write_text(spec(model), encoding="utf-8")
    (out / "README.md").write_text(readme(model), encoding="utf-8")
    print(f"wrote {out}: RR_FeelPresets.lua (generated), RR_FeelTyped.luau (generated, --!strict), RR_Feel.lua, "
          "RR_FeelMath.lua, RR_FeelDemo.client.lua, FEEL_SPEC.md, README.md")
    if not check:
        return 0
    ok, skipped = True, False
    code_files = sorted(list(out.glob("*.lua")) + list(out.glob("*.luau")))
    for f in code_files:
        st, msg = syntax_gate(f)
        ok &= st != "FAIL"
        skipped |= st == "SKIP"
        print(f"  {st} {f.name}: {msg}")
    import luau_check
    code, lines = luau_check.check([str(f) for f in code_files], strict=[str(out / "RR_FeelTyped.luau")], quiet=True)
    for ln in lines:
        if "typecheck" in ln:
            print(ln)
    ok &= code != 1
    b = model.bible
    if b.ok():
        for f in code_files + [out / "README.md"]:
            c, txt = b.run("check", str(f))
            ok &= c == 0
            print(f"  {'PASS' if c == 0 else 'FAIL'} bible check {f.name}" + ("" if c == 0 else "\n" + txt.strip()))
    else:
        print("  SKIP bible check: rr-bible not found")
        ok = False
    if not ok:
        print("build FAIL")
    else:
        print("build PASS" + (" (syntax unchecked: see SKIP lines)" if skipped else "") + ": Studio test pending (owner)")
    return 0 if ok else 1


def readme(model):
    r = model.r
    ev = ", ".join(f"`{n}`" for n in r["events"])
    lv = r["lever"]
    return f"""# RR Feel runtime (generated {TODAY} by rr-game-feel)

Client-only juice for Risky Rails. Nothing here has run in Roblox yet: **Studio test pending (owner)**.
Presets: `{model.source(full=False)}` (the only place to change numbers; rebuild after).

## Install (Studio)
1. ReplicatedStorage > Folder `RRFeel` with four ModuleScripts: `RR_Feel`, `RR_FeelMath`, `RR_FeelPresets`,
   `RR_FeelTyped` (paste each file; names must match).
2. Optional demo: `RR_FeelDemo.client.lua` as a LocalScript in StarterPlayerScripts. Play Solo: buttons fire every
   event, a toggle flips reduce motion, a two-way lever console shows the drag feel, `DUMP` prints easing curves.
3. With rr-ui-foundry's kit: `Kit.useFeel(require(ReplicatedStorage.RRFeel.RR_Feel))` once, or UI transitions fall
   back to plain fades.

## Use (LocalScripts only)
```lua
local Feel = require(game.ReplicatedStorage.RRFeel.RR_FeelTyped)   -- typed; RR_Feel is the same module untyped
Feel.play("lever_commit", {{ side = -1, targets = {{ lever_panel = panel, lamp = lamp }} }})
Feel.playFor("shovel_coal", actorUserId, ctx)   -- server events carry the actor's UserId; `who` decides who feels it
Feel.play("alert_fare_banked", {{ targets = {{ ticket = parts.mover, stamp = parts.stamp, cash = label }},
    count = {{ amount = 12500, format = Hud.formatCash }} }})   -- the HUD's own formatter: the count ends on its stamp
Feel.setSpeed(speed)          -- every throttle change: rumble floor follows Speed (av.vfx.speed_link)
Feel.setPressure(p01)         -- 0..1 of the gauge; floor rises past the threshold (OQ-013 numbers)
Feel.Cue.Event:Connect(function(event, cue) end)   -- sound and VFX modules subscribe here
Feel.setSetting("reduceMotion", true)  -- also: shake (0..1), flashes, haptics, profile subtle|default|loud
```
Events: {ev}.

## Lever (two-way, gameplay.fork.lever)
```lua
-- u is signed: - left, + right (the sign picks the branch); fork = the junction id re-arms the lever per junction
local startX, travel = 0, knobTravelPx
knob.InputBegan:Connect(function(input) startX = input.Position.X end)
UserInputService.InputChanged:Connect(function(input)   -- global tracking: the finger leaves the 64 px knob
    if not dragging then return end
    local shown = Feel.leverDrag((input.Position.X - startX) / travel, {{ targets = t, fork = junctionId }})
    knob.Position = UDim2.new(0.5, shown * travel, 0.5, 0)   -- |shown| == 1: committed (animate lever.snap)
end)
-- on release: if Feel.leverRelease({{ targets = t }}) == "snapback" then animate the knob home (lever.snapback)
```
The detent tick fires at {lv.get('notch', lv['detent']):.0%} of the travel, the commit once at {lv['detent']:.0%}; the lever stays
committed until a new `fork` id (or `Feel.leverReset()`). `RR_FeelDemo` has the full wiring; a UIDragDetector works too.

## HUD wiring (NotificationController): one writer per property
The shipped HUD animates the same objects itself (ticket slide in, crisis shake, halo pulse on RenderStepped).
Two writers fight, and RR_Feel restores the position it captured when an event starts, so a ticket captured
mid-slide ends parked off-screen. Before passing `ticket`/`halo` targets:
1. Delete the controller's own motion for those objects: the `mover.Position = UDim2.fromScale(1.25, 0)` + slide
   tween, the crisis `{{ -5, 5, -4, 3, 0 }}` shake loop, and the `haloRed` pulse in its RenderStepped callback.
2. Call Feel after the ticket is built at its rest position (mover at 0,0): `hud_ticket_enter`, `hud_ticket_leave`,
   `hud_merge_bump`, `hud_crisis_arrival` (targets: ticket = parts.mover, stamp = parts.stamp, halo = parts.haloRed).
3. Set `haloRed.BackgroundTransparency = 0`: the pulse multiplies the designed opacity (at 0.1 it would reach
   0.27-0.855 instead of canon's 0.3-0.95).
Or keep the controller's motion and pass only the other roles (gauge, stamp, cash): camera, haptics and cues still play.

## Rules baked in
- Reduce motion starts from `GuiService.ReducedMotionEnabled` (tech.feel.reduced_motion) and follows its changes.
- Screen flashes: at most {r['a11y']['flash']['per_second_max']} per second across all events, peaks capped (av.feel.flash_limit).
- Hit-stop freezes only this client's Feel effects, its character's animation tracks and emitters registered with
  `Feel.freezable(emitter)`; the server-driven world scroll never pauses (av.feel.hitstop_local).
- Haptics use HapticEffect (phones, gamepads, Quest) and fall back to HapticService:SetMotor on gamepads.
- Camera effects run after the camera scripts (BindToRenderStep, Camera + 1) and never accumulate; FOV kicks
  are applied as a delta, so a fail camera that sets its own FOV mid-kick keeps it.
- Camera pitch: + tips the view up, - down (a lurch forward or a nod is negative).
- Open decisions in use: OQ-031 lever input (default drag console), OQ-032 feel settings (default: Roblox's own
  Reduce Motion for the alpha), OQ-013 pressure numbers, OQ-006 who may pull.
"""


# ------------------------------------------------------------------ critic hand-off
def merged_rubric(critic):
    base = (critic / "references" / "rubric.md").read_text(encoding="utf-8")
    if "## Profile G" in base:
        return base
    g = (SKILL / "references" / "rubric-feel.md").read_text(encoding="utf-8")
    prof = g[g.index("## Profile G"):].rstrip() + "\n\n"
    i = base.index("## Shared blocks")
    text = base[:i] + prof + base[i:]
    return re.sub(r"(<!--\s*include-with:\s*A6, B5[^>]*?)(\s*-->)", r"\1, G5\2", text)


def brief(model, group, events=None):
    b, r = model.bible, model.r
    v = lambda k, d="?": b.value(k, d) if b.ok() else d  # noqa: E731
    return "\n".join([
        f"# Risky Rails feel presets: {group} (rr-game-feel)",
        "- Purpose: game feel (juice) per event: camera shake and kicks, hit-stop, UI punch, flashes, FOV kicks and "
        "haptics that say what happened and how big, on a phone, without hurting play.",
        f"- Audience: {v('identity.audience.launch')}; {v('identity.audience.devices')} (phone {r['meta']['phone']} landscape).",
        f"- Player view: players stay on the train; third-person eye {v('tech.camera.eye_3p')} studs, first-person "
        f"{v('tech.camera.eye_1p')}, vertical FOV {r['meta']['fov_deg']}. Stable train: {v('identity.pillars.stable_train')}. "
        "The images are curve plots, a feel matrix and mock phone frames at the peak of each event: judge timing, "
        "curve shape, magnitude and hierarchy as intent, not engine pixels. Camera pitch: + tips the view up. "
        "Facts list, per event, any higher-tier event it outshouts.",
        "- Stage: feel presets before any Studio playtest; the runtime uses the same formulas (Limits in Facts).",
        f"- Fixed constraints: tone {v('identity.tone.company')}; {v('identity.tone.not')}; "
        f"{v('identity.pillars.physical_loud')}; {v('identity.pillars.funny_failure')}. Red only for the danger "
        f"signal. Flashes: {v('av.feel.flash_limit')} ({b.fact('av.feel.flash_limit')['note'] if b.ok() and b.fact('av.feel.flash_limit') else ''}). "
        f"Reduce motion: {v('av.feel.reduce_motion')}. Hit-stop: {v('av.feel.hitstop_local')}.",
        "- Owner worries / already decided: feel must scale by tier (fail > crisis > commit > reward > UI); the lever "
        "is the signature moment (identity.pillars.fork_bet). Open, on defaults: OQ-031 lever input (drag console), "
        "OQ-032 feel settings (Roblox Reduce Motion only for the alpha), OQ-013 pressure numbers. Sound is not in "
        "these images (cues name sounds for a later skill); judge the visual and haptic channels only.",
        *([f"- Events in this pass: {', '.join(events)}."] if events else []),
        "step 2: pre-answered (canon via rr-bible; owner away)"]) + "\n"


def crit(model, a):
    critic = find_sibling("multiuse-critic", "RR_CRITIC_SKILL")
    if not critic:
        print("multiuse-critic not found: set RR_CRITIC_SKILL")
        return 2
    src = Path(a.src)
    if not (src / "contact.png").is_file():
        print(f"{src}/contact.png missing: run feel.py preview first")
        return 2
    C = Path(a.crit)
    pdir = C / f"pass-{a.pass_}"
    pdir.mkdir(parents=True, exist_ok=True)
    (C / "rubric.md").write_text(merged_rubric(critic), encoding="utf-8")
    for n in ("contact.png", "contact.json", "closeups.png", "closeups.json", "facts.md"):
        if (src / n).is_file():
            shutil.copy2(src / n, pdir / n)
    if not (C / "brief.md").is_file():
        pj = json.loads((src / "preview.json").read_text()) if (src / "preview.json").is_file() else {}
        (C / "brief.md").write_text(brief(model, pj.get("group", src.name), pj.get("events")), encoding="utf-8")
        print(f"wrote {C / 'brief.md'} (edit the Owner worries line if the owner said more)")
    extra = " --images closeups.png" if (pdir / "closeups.png").is_file() else ""
    print(f"wrote {C / 'rubric.md'} (multiuse-critic rubric + Profile G) and pass-{a.pass_}/ files")
    print(f"next: python3 {critic / 'scripts' / 'critic_kit.py'} build {C} --pass {a.pass_} --kind full --profile G "
          f"--role \"senior game-feel designer\"{extra}")
    print("then spawn a fresh critic on the printed prompt (multiuse-critic step 5); never score it yourself")
    return 0


# ------------------------------------------------------------------ editing: house layout, set, changed
WIDTH = 118


def _inline(v):
    return json.dumps(v, ensure_ascii=False)


def _fill(items, ind, open_, close):
    """Items written inline, wrapped at WIDTH; continuation lines one space inside the bracket."""
    lines, cur = [], open_
    for i, it in enumerate(items):
        piece = it + ("," if i < len(items) - 1 else close)
        if len(cur) > len(open_) and ind + len(cur) + 1 + len(piece) > WIDTH:
            lines.append(cur.rstrip())
            cur = " " * len(open_) + piece
        else:
            cur += ("" if cur == open_ else " ") + piece
    lines.append(cur)
    return ("\n" + " " * ind).join(lines)


def _fmt(v, ind, key=None, depth=0):
    """House layout of feel.json: sections and events one key per line, channels one per line (wrapped), leaves
    inline. json.loads(dump(x)) == x always."""
    pad = " " * (ind + 2)
    if isinstance(v, dict) and (depth <= 1 or (depth == 2 and key is not None and v and "channels" in v)):
        if depth == 2 and "channels" in v:   # an event: scalar fields filled, then channels one per line
            head = [f"{_inline(k)}: {_inline(x)}" for k, x in v.items() if k not in ("channels",)]
            out = "{\n" + pad + _fill(head, ind + 2, "", ",")
            chans = v.get("channels", [])
            if chans:
                out += "\n" + pad + '"channels": [\n' + ",\n".join(
                    pad + "  " + _fill([f"{_inline(k)}: {_inline(x)}" for k, x in c.items()], ind + 4, "{", "}") for c in chans
                ) + "\n" + pad + "]"
            else:
                out += "\n" + pad + '"channels": []'
            return out + "\n" + " " * ind + "}"
        items = [pad + f"{_inline(k)}: " + _fmt(x, ind + 2, k, depth + 1) for k, x in v.items()]
        return "{\n" + ",\n".join(items) + "\n" + " " * ind + "}"
    s = _inline(v)
    if len(s) + ind + (len(key) + 4 if key else 0) <= WIDTH or not isinstance(v, (dict, list)):
        return s
    if isinstance(v, dict):
        return _fill([f"{_inline(k)}: {_inline(x)}" for k, x in v.items()], ind + (len(key) + 4 if key else 0), "{", "}")
    return _fill([_inline(x) for x in v], ind + (len(key) + 4 if key else 0), "[", "]")


def dump_presets(data):
    text = _fmt(data, 0) + "\n"
    if json.loads(text) != data:
        raise ValueError("formatter round trip failed")
    return text


PATH_RE = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


def set_path(data, path, value):
    keys = [m.group(1) if m.group(1) is not None else int(m.group(2)) for m in PATH_RE.finditer(path)]
    node = data
    for k in keys[:-1]:
        node = node[k]
    last = keys[-1]
    old = node[last] if (isinstance(node, list) and last < len(node)) or (isinstance(node, dict) and last in node) else None
    if isinstance(old, dict) and "canon" in old and "v" in old and not isinstance(value, dict):
        old = dict(old)
        before, old["v"] = old["v"], value   # keep the canon binding; validate re-checks it
        node[last] = old
        return before, value
    node[last] = value
    return old, value


def cmd_set(model, a):
    data = copy.deepcopy(model.raw)
    for item in a.assign:
        if "=" not in item:
            die(f"set needs PATH=VALUE, got {item!r}")
        path, raw = item.split("=", 1)
        try:
            val = json.loads(raw)
        except ValueError:
            val = raw
        try:
            before, after = set_path(data, path.strip(), val)
        except (KeyError, IndexError, TypeError) as e:
            die(f"set: no such path {path!r} ({e})")
        print(f"set {path.strip()}: {json.dumps(before)} -> {json.dumps(after)}")
    if a.dry_run:
        print("dry run: nothing written")
        return 0
    model.path.write_text(dump_presets(data), encoding="utf-8")
    print(f"wrote {model.source()}; next: feel.py validate --strict")
    return 0


def cmd_fmt(model, a):
    text = dump_presets(model.raw)
    same = text == model.path.read_text(encoding="utf-8")
    if a.check:
        print(f"fmt: {model.path} is {'in' if same else 'NOT in'} the house layout")
        return 0 if same else 1
    if not same:
        model.path.write_text(text, encoding="utf-8")
    print(f"fmt: {model.source()} {'unchanged' if same else 'rewritten in the house layout'}")
    return 0


def cmd_changed(model, a):
    old = Path(a.since)
    if not old.is_file():
        die(f"--since {old}: not a file")
    was = json.loads(old.read_text(encoding="utf-8"))
    now = model.raw
    glob_changed = [k for k in now if k not in ("events", "preview", "about", "version") and now.get(k) != was.get(k)]
    changed = sorted(n for n in now["events"] if now["events"][n] != was.get("events", {}).get(n))
    removed = sorted(n for n in was.get("events", {}) if n not in now["events"])
    hit = set(changed)
    grew = True
    while grew:   # an event that includes a changed event changed too
        more = {n for n, e in now["events"].items() if any(i.get("event") in hit for i in e.get("include", []))} - hit
        hit |= more
        grew = bool(more)
    groups = sorted({now["events"][n]["group"] for n in hit})
    if glob_changed:
        groups = sorted({e["group"] for e in now["events"].values()})
    print(f"changed events: {', '.join(changed) or 'none'}" + (f"; removed: {', '.join(removed)}" if removed else ""))
    print(f"affected (with includers): {', '.join(sorted(hit)) or 'none'}")
    if glob_changed:
        print(f"global sections changed ({', '.join(glob_changed)}): every group is affected")
    print(f"re-preview and re-critique only: {', '.join(groups) or 'nothing'}")
    return 0


# ------------------------------------------------------------------ tuning table
def knob_range(r, ch, key, tier):
    lim, fl = r["limits"], r["a11y"]["flash"]
    t = ch["type"]
    table = {
        ("camkick", "angles_deg"): f"delivered peak deg: kick <= {lim['kick_deg_max']}, roll <= {lim['roll_deg_max']}, "
                                   f">= {lim['kick_px_min']} px on the phone; + pitch = view up",
        ("camkick", "freq_hz"): "{}-{} Hz".format(*lim.get("camkick_freq_hz", [0.5, 14])),
        ("camkick", "damping"): "{}-{}".format(*lim["damping"]),
        ("punch", "freq_hz"): "{}-{} Hz".format(*lim["punch_freq_hz"]),
        ("punch", "damping"): "{}-{} (spring ends under 5% of its peak)".format(*lim["damping"]),
        ("punch", "amp"): (f"delivered peak, <= {lim['punch_scale_amp_max']}" if ch.get("prop") in ("scale", "rot")
                           else f"delivered px, >= {lim.get('punch_px_min', 1.5)}"),
        ("shake", "trauma"): f"0-1; camera <= {lim['tier_shake_px'][str(tier)]} px (tier {tier}); visible from about 0.3",
        ("fovkick", "delta_deg"): f"|delta| <= {lim['fov_delta_max']} deg (- zooms in)",
        ("hitstop", "ms"): f"<= {lim['hitstop_ms_max']} ms, cooldown {lim['hitstop_cooldown_s']} s; not on crew events",
        ("flash", "peak"): f"screen/vignette <= {fl['screen_peak_max']} (red {fl['red_peak_max']}); element exempt",
        ("haptic", "keys"): f"[ms, 0..1], end at 0, <= {lim['haptic_ms_max']} ms",
        ("pulse", "period"): ">= 0.5 s", ("tween", "dur"): "> 0 s", ("tween", "style"): "Enum.EasingStyle",
    }
    return table.get((t, key), "")


def cmd_tune(model, a):
    names = model.names(a.sel)
    r, raw = model.r, model.raw
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    md = ["# Feel tuning table", "", f"Generated {TODAY} from `{model.source(full=False)}` by `feel.py tune`. Change numbers "
          "with `feel.py set 'events.E.channels[i].KNOB=VALUE'` (or edit feel.json), then `validate --strict` and "
          "`build`; never edit RR_FeelPresets.lua. `canon` knobs keep their rr-bible value; the rest are free within "
          "the range. Punch amps and kick angles are the delivered peaks.", ""]
    rows = []
    md += ["| event | tier / who | ch | channel | knobs | safe range | canon-locked |", "|---|---|---|---|---|---|---|"]
    for n in names:
        e = raw["events"][n]
        tier = e["priority"]
        for i, ch in enumerate(e.get("channels", [])):
            label = ch["type"] + (f" {ch['target']}.{ch.get('prop', '')}".rstrip(".") if ch.get("target") else "")
            knobs, rng, locked = [], [], []
            for k, v in ch.items():
                if k in ("type", "target", "prop", "note", "before"):
                    continue
                vv = v["v"] if isinstance(v, dict) and "v" in v else v
                rg = knob_range(r, ch, k, tier)
                src = f"canon {v['canon']}" if isinstance(v, dict) and "canon" in v else "knob"
                rows.append([n, f"t{tier} {e['who']}", i, label, k, json.dumps(vv), rg, src])
                knobs.append(f"{k} {json.dumps(vv)}")
                if rg:
                    rng.append(f"{k}: {rg}")
                if src != "knob":
                    locked.append(f"{k} ({v['canon']})")
            md.append(f"| {n} | t{tier} {e['who']} | {i} | {label} | {' · '.join(knobs)} | {'; '.join(rng)} | {', '.join(locked) or '-'} |")
        for inc in e.get("include", []):
            md.append(f"| {n} | t{tier} {e['who']} | - | include | {inc['event']} at +{inc.get('delay', 0)} s | | - |")
    pairs, _ = hierarchy(model)
    md += ["", "| event | camera px (RM) | kick deg | FOV deg | hit-stop ms | flash | haptic | secs | loudness | "
           "outshouts (higher tier) | RM still reads via |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for n in names:
        m, rm = metrics(model, n), metrics(model, n, reduce_motion=True)
        beats = ", ".join(o for o, _ in pairs.get(n, [])) or "-"
        via = ", ".join(rm["communicates"]) + (f"; {r['events'][n]['rm_reads']}" if r["events"][n].get("rm_reads") else "")
        md.append(f"| {n} | {m['cam_px']} ({rm['cam_px']}) | {m['kick_deg']} | {m['fov_signed']:+g} | {m['hitstop_ms']} | "
                  f"{m['flash_peak']} | {m['haptic_peak']} / {m['haptic_ms']} ms | {m['total_s']}{' + loop' if m['loops'] else ''} | "
                  f"{m['loudness']} | {beats} | {via} |")
    lv = r["lever"]
    md += ["", "## Lever drag (`lever` section)", "", "| knob | value | meaning |", "|---|---|---|",
           f"| notch | {lv.get('notch', '-')} | finger travel where the detent tick fires (felt before the commit) |",
           f"| detent | {lv['detent']} | finger travel where the commit fires (once per junction) |",
           f"| resist | {lv['resist']} | knob = detent x (finger/detent)^resist: higher feels heavier |",
           f"| snap | {lv['snap']['style']} {lv['snap']['dir']} {lv['snap']['dur']} s | knob home after the commit |",
           f"| snapback | {lv['snapback']['style']} {lv['snapback']['dir']} {lv['snapback']['dur']} s | knob home when released early |",
           f"| throw_deg | {lv['throw_deg']} | in-world handle throw |", ""]
    for k in ("notch", "detent", "resist", "throw_deg"):
        if k in lv:
            rows.append(["lever", "", "", "drag", k, json.dumps(lv[k]), "", "knob"])
    (out / "TUNING.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    import csv
    with open(out / "tuning.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["event", "tier_who", "channel_index", "channel", "knob", "value", "safe_range", "source"])
        w.writerows(rows)
    print(f"wrote {out / 'TUNING.md'} and tuning.csv ({len(rows)} knobs, {len(names)} events; presets: {model.source()})")
    return 0


# ------------------------------------------------------------------ CLI
def cmd_list(model, a):
    names = model.names(a.group or "all")
    print(f"{len(names)} events  (presets: {model.source()})")
    for n in names:
        e, m = model.events[n], metrics(model, n)
        kinds = sorted({ch["type"] for ch, _ in fm.expand(model.r, n)})
        print(f"  {n:24} {e['group']:8} t{e['priority']} {e['who']:6} loud {m['loudness']:.2f}  {','.join(kinds)}")
    return 0


def cmd_show(model, a):
    if a.event not in model.events:
        print(f"no event {a.event!r}")
        return 2
    m = metrics(model, a.event, reduce_motion=a.rm)
    if a.json:
        pairs, _ = hierarchy(model)
        print(json.dumps({"event": model.events[a.event], "expanded": [[c, d] for c, d in fm.expand(model.r, a.event)],
                          "metrics": m, "outshouts": pairs.get(a.event, []), "presets": str(model.path)}, indent=1))
    else:
        print(spec_event(model, a.event))
    return 0


def cmd_validate(model, a):
    errs, warns = validate(model, a.strict)
    if a.json:
        print(json.dumps({"ok": not errs, "errors": errs, "warnings": warns, "notes": model.notes,
                          "presets": str(model.path)}, indent=1))
    else:
        print(f"presets: {model.source()}")
        for n in model.notes:
            print("NOTE " + n)
        for w in warns:
            print("WARN " + w)
        for e in errs:
            print("FAIL " + e)
        print(f"validate {'PASS' if not errs else 'FAIL'}: {len(model.events)} events, {len(errs)} errors, {len(warns)} warnings")
    return 0 if not errs else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--presets", help="feel.json to use (default: $RR_FEEL_PRESETS, else the skill's read-only copy)")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--presets", default=argparse.SUPPRESS, help="feel.json to use (also accepted before the command)")
    sp = ap.add_subparsers(dest="cmd", required=True)
    _add = sp.add_parser
    sp.add_parser = lambda *x, **k: _add(*x, parents=[common], **k)
    p = sp.add_parser("list"); p.add_argument("--group")
    p = sp.add_parser("show"); p.add_argument("event"); p.add_argument("--json", action="store_true"); p.add_argument("--rm", action="store_true")
    p = sp.add_parser("validate"); p.add_argument("--strict", action="store_true"); p.add_argument("--json", action="store_true")
    p = sp.add_parser("spec"); p.add_argument("sel", nargs="?", default="all"); p.add_argument("--out")
    p = sp.add_parser("tune"); p.add_argument("sel", nargs="?", default="all"); p.add_argument("--out", required=True)
    p = sp.add_parser("set"); p.add_argument("assign", nargs="+"); p.add_argument("--dry-run", action="store_true")
    p = sp.add_parser("fmt"); p.add_argument("--check", action="store_true")
    p = sp.add_parser("changed"); p.add_argument("--since", required=True)
    p = sp.add_parser("plot"); p.add_argument("what"); p.add_argument("--out", required=True); p.add_argument("--compare")
    p = sp.add_parser("preview"); p.add_argument("sel"); p.add_argument("--out", required=True); p.add_argument("--name")
    p.add_argument("--gif", action="store_true"); p.add_argument("--rm", action="store_true", help="preview with reduce motion on")
    p = sp.add_parser("crit"); p.add_argument("crit"); p.add_argument("--pass", dest="pass_", type=int, required=True)
    p.add_argument("--from", dest="src", required=True)
    p = sp.add_parser("build"); p.add_argument("--out", required=True); p.add_argument("--no-check", action="store_true")
    a = ap.parse_args(argv)
    model = Model(a.presets)
    if a.cmd == "list":
        return cmd_list(model, a)
    if a.cmd == "show":
        return cmd_show(model, a)
    if a.cmd == "validate":
        return cmd_validate(model, a)
    if a.cmd == "spec":
        text = spec(model, a.sel)
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(text, encoding="utf-8")
            print(f"wrote {a.out} ({len(model.names(a.sel))} events)")
        else:
            print(text)
        return 0
    if a.cmd in ("plot", "preview"):
        try:
            import feelplot
        except ImportError as e:
            print(f"{a.cmd} needs Pillow: {e}")
            return 2
        return feelplot.plot(model, a) if a.cmd == "plot" else feelplot.preview(model, a)
    if a.cmd == "crit":
        return crit(model, a)
    if a.cmd in ("tune", "set", "fmt", "changed"):
        return {"tune": cmd_tune, "set": cmd_set, "fmt": cmd_fmt, "changed": cmd_changed}[a.cmd](model, a)
    if a.cmd == "build":
        return build(model, a.out, check=not a.no_check)
    return 2


if __name__ == "__main__":
    sys.exit(main())
