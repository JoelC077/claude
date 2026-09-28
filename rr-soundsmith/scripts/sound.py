#!/usr/bin/env python3
"""rr-soundsmith: Risky Rails audio as data -> checks, measurements, placeholders, briefs, Luau runtime, critic hand-off.

  sound.py list [--group G] [--tier N]           every sound by phase: tier, group, class, space, level, Volume, state
  sound.py show ID|EVENT [--json]                 one sound (mix math, events, brief) or one event's actions
  sound.py validate [--strict] [--release]        schema, canon agreement, cited OQs, rr-game-feel cue parity, ladder,
                                                  ducking, voices, Roblox ranges, licences (--release: ship gate)
  sound.py oq                                     cited open questions (status, default) + add-question commands for
                                                  pending ones (never writes the bible)
  sound.py analyze PATH... [--as ID|--class C] [--json] [--fix-out DIR [--mono]]
                                                  measure dropped files against the class standard and Roblox limits
  sound.py synth [ID...|all] --out DIR            PLACEHOLDER_<id>.wav + PLACEHOLDERS.md (needs numpy)
  sound.py register ID --file F [--file F2] --id N [--id N2] --source owner_upload|roblox_licensed|placeholder
                    [--origin O] [--licence L] [--proof P] [--credit C] [--creator C] [--community] [--dry-run]
  sound.py brief [ID...|all] [--out FILE]         audio sourcing briefs (build writes them all; use this for subsets)
  sound.py sheet --from DIR --out DIR             tiles, mix ladder, timelines, contact.png, closeups.png, facts.md
  sound.py crit CRIT --pass N --from DIR [--owner-away]   CRIT/rubric.md with Profile S, pass files, brief from canon
  sound.py build --out DIR [--no-check]           RR_SoundMap.lua (generated), RR_Sound.lua, demo, Studio setup,
                                                  SOUND_SPEC.md, AUDIO_BRIEFS.md, LICENCES.md, README; luaparse + bible check
  sound.py where                                  which soundmap/register is in use and why
  sound.py promote --from DIR [--to HOME] [--dry-run]    copy a mission's soundmap.json, assets.json (merged) and
                                                  recipes.py to the project home so every later run reads them

Presets: $RR_SOUND_PRESETS (folder or soundmap.json), else the project home ($RR_SOUND_HOME, else ~/.rr-sound) when it
holds a soundmap.json, else <skill>/presets (read-only defaults: register refuses to write there). Canon through
rr-bible's CLI (found by glob or $RR_BIBLE_SKILL); cue names from rr-game-feel ($RR_FEEL_PRESETS or its
presets/feel.json); critic scripts from multiuse-critic ($RR_CRITIC_SKILL). Standard library, plus numpy for
synth/sheet and fast analysis, Pillow for sheet (also found in ~/.cache/rr-tools/py).
Exit codes: 0 pass, 1 fail, 2 usage or missing dependency.
"""
import argparse, copy, datetime, hashlib, json, math, os, re, shlex, shutil, struct, subprocess, sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
import audiolib as al  # noqa: E402

TODAY = datetime.date.today().isoformat()
AUDIO_EXT = {".wav", ".ogg", ".mp3", ".flac", ".opus"}
ROLLOFF = {"Inverse", "Linear", "LinearSquare", "InverseTapered"}
SOURCES = {"owner_upload", "roblox_licensed", "placeholder"}
ORIGINS = {"self-made", "commissioned", "cc0", "purchased", "rr-soundsmith synth"}  # av.audio.licence (no CC-BY)
REFUSED = [r"\bnc\b", r"non-?commercial", r"\bnd\b", r"no-?deriv", r"\bsa\b", r"share-?alike", r"youtube",
           r"\brip(s|ped|ping)?\b",
           r"unknown", r"not sure", r"free download", r"copyright(ed)? (song|track)", r"tiktok"]
NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")
GROUP_TIERS = {"Alarms": (1, 2), "Actions": (3, 4), "UI": (5, 5), "Ambient": (6, 6), "Music": (7, 7)}
PHASES = ["lobby", "depart", "run", "fork", "crisis", "arrive", "results", "any"]
SPEC_LAYERS = {"tone", "noise", "bell", "click", "modes"}


def home_dir():
    return Path(os.environ.get("RR_SOUND_HOME") or Path.home() / ".rr-sound")


def presets_source():
    """(folder, how): $RR_SOUND_PRESETS, else the project home when it holds a soundmap, else the skill defaults."""
    if os.environ.get("RR_SOUND_PRESETS"):
        p = Path(os.environ["RR_SOUND_PRESETS"])
        return (p.parent if p.is_file() else p), "RR_SOUND_PRESETS"
    if (home_dir() / "soundmap.json").is_file():
        return home_dir(), "project home ($RR_SOUND_HOME or ~/.rr-sound)"
    return SKILL / "presets", "skill defaults (read-only: register refuses to write here)"


def presets_dir():
    return presets_source()[0]


def inside_skill(p):
    try:
        Path(p).resolve().relative_to(SKILL.resolve())
        return True
    except ValueError:
        return False


def recipe_names(pdir):
    """Recipe names without importing numpy: built-ins in synth.py and r_<name> in <presets>/recipes.py."""
    names = set(re.findall(r"^def r_(\w+)\(", (HERE / "synth.py").read_text(encoding="utf-8"), re.M))
    extra = Path(pdir) / "recipes.py"
    if extra.is_file():
        names |= set(re.findall(r"^def r_(\w+)\(", extra.read_text(encoding="utf-8"), re.M))
    return names


def spec_problems(spec, length_range):
    """Errors in a soundmap "synth" layer spec (checked without numpy)."""
    out = []
    if not isinstance(spec.get("len"), (int, float)) or not 0 < spec["len"] <= 60:
        return ["synth.len must be 0-60 s"]
    if not isinstance(spec.get("layers"), list) or not spec["layers"]:
        return ["synth.layers must be a non-empty list"]
    for i, ly in enumerate(spec["layers"]):
        kind = SPEC_LAYERS & set(ly)
        if len(kind) != 1:
            out.append(f"synth.layers[{i}] needs exactly one of {sorted(SPEC_LAYERS)}")
            continue
        if ly.get("wave", "sine") not in ("sine", "square", "saw") or ly.get("color", "white") not in ("white", "pink", "brown"):
            out.append(f"synth.layers[{i}]: wave sine|square|saw, color white|pink|brown")
        if not 0 <= ly.get("at", 0) < spec["len"]:
            out.append(f"synth.layers[{i}].at must be inside 0..len")
        if "noise" in ly and not (isinstance(ly["noise"], list) and len(ly["noise"]) == 2):
            out.append(f"synth.layers[{i}].noise must be [lo, hi] Hz (null for open)")
        if "modes" in ly and not all(isinstance(m_, list) and len(m_) == 3 for m_ in ly["modes"]):
            out.append(f"synth.layers[{i}].modes must be [[freq, tau, amp], ...]")
    if not length_range[0] <= spec["len"] <= length_range[1]:
        out.append(f"synth.len {spec['len']} outside the class length {length_range}")
    return out


# ------------------------------------------------------------------ siblings and canon
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


def feel_presets():
    if os.environ.get("RR_FEEL_PRESETS"):
        p = Path(os.environ["RR_FEEL_PRESETS"])
        p = p / "feel.json" if p.is_dir() else p
        return p if p.is_file() else None
    fs = find_sibling("rr-game-feel", "RR_FEEL_SKILL")
    p = fs / "presets" / "feel.json" if fs else None
    return p if p and p.is_file() else None


# ------------------------------------------------------------------ model
class Model:
    def __init__(self, bible=None):
        self.dir = presets_dir()
        self.path = self.dir / "soundmap.json"
        if not self.path.is_file():
            sys.exit(f"soundmap not found: {self.path}")
        self.raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.assets_path = self.dir / "assets.json"
        self.assets = json.loads(self.assets_path.read_text(encoding="utf-8")) if self.assets_path.is_file() else {}
        self.assets.pop("_about", None)
        self.bible = bible or Bible()
        self.refs = []
        self.r = self._resolve(copy.deepcopy(self.raw), "")
        self.sounds, self.events, self.std, self.ladder = self.r["sounds"], self.r["events"], self.r["standards"], self.r["ladder"]

    def _resolve(self, node, where):
        if isinstance(node, dict):
            if "v" in node and "canon" in node and set(node) <= {"v", "canon", "note"}:
                self.refs.append((where, node))
                return node["v"]
            return {k: self._resolve(v, f"{where}.{k}" if where else k) for k, v in node.items()}
        if isinstance(node, list):
            return [self._resolve(v, f"{where}[{i}]") for i, v in enumerate(node)]
        return node

    # mix math -------------------------------------------------------
    def ladder_key(self, sid):
        s = self.sounds[sid]
        return {"loop": "ambient", "music": "music"}.get(s["class"], f"t{s['tier']}")

    def metric(self, sid):
        return self.std[self.sounds[sid]["class"]]["metric"]

    def file_level(self, sid):
        """(level, how): measured mean of registered files, else the class target (assumed)."""
        a = self.assets.get(sid) or {}
        vals = [m.get(self.metric(sid)) for m in a.get("measured", []) if m.get(self.metric(sid)) is not None]
        if vals:
            return round(sum(vals) / len(vals), 2), "measured"
        return float(self.std[self.sounds[sid]["class"]]["target"]), "standard"

    def mix(self, sid):
        s = self.sounds[sid]
        lvl, how = self.file_level(sid)
        target = self.ladder[self.ladder_key(sid)] + s.get("trim_db", 0)
        gain = target - lvl
        vol = self.r["meta"]["ref_volume"] * 10 ** (gain / 20)
        clamped = min(vol, 10.0)
        eff = lvl + 20 * math.log10(clamped / self.r["meta"]["ref_volume"])
        return {"file_level": lvl, "level_from": how, "target": round(target, 2), "gain_db": round(gain, 2),
                "volume": round(clamped, 4), "volume_raw": round(vol, 4), "effective": round(eff, 2)}

    def asset_state(self, sid):
        a = self.assets.get(sid)
        if not a or not a.get("ids"):
            return "unassigned" if not a else f"{a.get('source')}, no id"
        return "placeholder" if a.get("source") == "placeholder" else "final"

    def group_chain(self, g):
        out = []
        while g:
            out.append(g)
            g = self.r["groups"].get(g, {}).get("parent")
        return out

    def events_for(self, sid):
        out = []
        for e, ev in self.events.items():
            ids = [ev.get("play"), ev.get("toggle")] + ev.get("start", []) + ev.get("stop", [])
            if sid in ids:
                out.append(e)
        return out

    def event_phase(self, e):
        return self.events[e].get("phase", "any")

    def sound_phase(self, sid):
        ph = [self.event_phase(e) for e in self.events_for(sid)]
        return min(ph, key=pidx) if ph else "any"

    def by_phase(self, ids=None):
        return sorted(ids if ids is not None else self.sounds, key=lambda s: (pidx(self.sound_phase(s)), self.sounds[s]["tier"], s))

    def events_by_phase(self):
        order = list(self.events)
        return sorted(order, key=lambda e: (pidx(self.event_phase(e)), order.index(e)))


def pidx(p):
    return PHASES.index(p) if p in PHASES else len(PHASES)


# ------------------------------------------------------------------ open questions
def add_question_cmd(m, p, portable=False):
    b = "<bible>/scripts/bible.py" if portable or not m.bible.script else str(m.bible.script)
    parts = ["python3", b, "add-question", p.get("title", "?")]
    for o in p.get("options", []):
        parts += ["--option", o]
    parts += ["--default", p.get("default", "?"), "--src", "SND"]
    for k in ("context", "affects", "blocks"):
        if p.get(k):
            parts += [f"--{k}", p[k]]
    return " ".join(shlex.quote(x) for x in parts)


def oq_relevant(m, q, cited):
    f = q.get("fields", {})
    text = " ".join(str(x or "") for x in (q.get("title"), f.get("context"), f.get("affects"), f.get("blocks"))).lower()
    if re.search(r"rr-soundsmith|\baudio\b|\bsounds?\b|av\.audio", text):
        return True
    keys = set(m.r["meta"].get("canon", [])) if "meta" in cited else set()
    for sid in cited:
        if sid in m.sounds:
            if sid.lower() in text:
                return True
            keys |= set(m.sounds[sid].get("canon", []))
    return any(k.lower() in text for k in keys)


def oq_rows(m):
    """Every cited open question (meta.oq, then sounds): id, title, status, default text, who cites it, relevance."""
    cites = {}
    for o in m.r["meta"].get("oq", []):
        cites.setdefault(o, []).append("meta")
    for sid in m.by_phase():
        for o in m.sounds[sid].get("oq", []):
            cites.setdefault(o, []).append(sid)
    pend = m.r["meta"].get("pending_oq", {})
    rows = []
    for o, who in cites.items():
        row = {"id": o, "cited": who, "pending": o.startswith("pending:"), "known": False, "relevant": True,
               "title": "?", "status": "?", "default": "?", "cmd": None}
        if row["pending"]:
            p = pend.get(o.split(":", 1)[1])
            if p:
                row.update(known=True, title=p.get("title", "?"), status="not yet in rr-bible", cmd=add_question_cmd(m, p),
                           cmd_portable=add_question_cmd(m, p, True),
                           default=default_text(p.get("default", "?"), [o_.split(": ", 1) for o_ in p.get("options", [])]))
        elif m.bible.ok():
            q = m.bible.oq(o)
            if q:
                f = q.get("fields", {})
                row.update(known=True, title=q.get("title", "?"), status=f.get("status", "?"),
                           default=default_text(f.get("default", "?"), q.get("options", [])), relevant=oq_relevant(m, q, who))
        rows.append(row)
    return rows


def default_text(default, options):
    """'A: <option text>' for a default like 'A (why)'; the raw default when it names no option."""
    letter = str(default).strip()[:1]
    opt = dict((o[0], o[1]) for o in options if len(o) == 2)
    return f"{letter}: {opt[letter]}" if letter in opt else str(default)


def cmd_oq(m, a):
    rows = oq_rows(m)
    if not m.bible.ok():
        print("rr-bible not found: titles and defaults unknown (set RR_BIBLE_SKILL)")
    for r_ in rows:
        flag = "" if r_["relevant"] else "  [WARN: does not mention audio, rr-soundsmith or the citing sound: wrong number?]"
        print(f"{r_['id']} ({r_['status']}) {r_['title']}{flag}\n   default {r_['default'][:160]}\n   cited by {', '.join(r_['cited'])}")
        if r_["cmd"]:
            print(f"   record it (owner or mission-control; then cite the number it prints):\n   {r_['cmd']}")
    print(f"oq: {len(rows)} cited, {sum(r_['pending'] for r_ in rows)} pending, {sum(not r_['relevant'] for r_ in rows)} suspect")
    return 0


# ------------------------------------------------------------------ validate
def numbers_in(text):
    return [float(x) for x in NUM_RE.findall(str(text).replace(",", ""))]


def canon_agrees(v, fact_value):
    vals = v if isinstance(v, list) else [v]
    have = numbers_in(fact_value)
    return all(any(abs(float(x) - h) < 1e-9 for h in have) for x in vals if isinstance(x, (int, float)))


def licence_problems(sid, a, stage="alpha"):
    """(errors, warns) for one register entry."""
    errs, warns = [], []
    src = a.get("source")
    if src not in SOURCES:
        return [f"assets.{sid}: source {src!r} is not one of {sorted(SOURCES)} (av.audio.licence)"], []
    for i in a.get("ids", []):
        if not re.fullmatch(r"(rbxassetid://)?\d+", str(i)):
            errs.append(f"assets.{sid}: asset id {i!r} is not a number or rbxassetid://N")
    if src != "placeholder" and not a.get("ids"):
        errs.append(f"assets.{sid}: {src} needs --id (the Roblox asset id the audio plays from)")
    text = " ".join(str(a.get(k, "")) for k in ("origin", "licence", "proof", "note")).lower()
    for pat in REFUSED:
        if re.search(pat, text):
            errs.append(f"assets.{sid}: licence text matches refused term /{pat}/ (NC, ND, SA, rips and unknown terms "
                        f"are refused: av.audio.licence)")
            break
    files = a.get("files", [])
    if src == "placeholder":
        bad = [f for f in files if not Path(f).name.startswith("PLACEHOLDER_")]
        if bad:
            errs.append(f"assets.{sid}: placeholder files must be named PLACEHOLDER_*: {', '.join(bad)}")
    elif src == "owner_upload":
        if a.get("origin") not in ORIGINS - {"rr-soundsmith synth"}:
            errs.append(f"assets.{sid}: owner_upload needs --origin one of self-made, commissioned, cc0, purchased "
                        f"(av.audio.licence; CC-BY is not admitted until the owner extends it)")
        if not a.get("proof"):
            errs.append(f"assets.{sid}: owner_upload needs --proof (receipt, licence URL, project file or 'made by owner <date>')")
        if a.get("origin") == "cc0" and re.search(r"\bcc[ -]?by\b|/licenses/by\b|attribution", text):
            errs.append(f"assets.{sid}: origin cc0 but the licence text names attribution (CC BY is not CC0 and is not "
                        f"admitted by av.audio.licence)")
        if any(Path(f).name.startswith("PLACEHOLDER_") for f in files):
            errs.append(f"assets.{sid}: a PLACEHOLDER_ file registered as owner_upload; register it as placeholder")
    elif src == "roblox_licensed":
        if a.get("community"):
            errs.append(f"assets.{sid}: community-uploaded Creator Store audio is refused (OQ-036 default A)")
        if not a.get("creator"):
            errs.append(f"assets.{sid}: roblox_licensed needs --creator (Roblox or the partner label shown on the Creator Store)")
        elif a.get("creator", "").strip().lower() != "roblox":
            warns.append(f"assets.{sid}: creator {a['creator']!r}: confirm it is a Roblox audio partner, not a community "
                         f"upload (OQ-036); Roblox-licensed audio is for use inside Roblox only (not trailers)")
        if not a.get("proof"):
            errs.append(f"assets.{sid}: roblox_licensed needs --proof (the Creator Store URL)")
    return errs, warns


def validate(m, strict=False, release=False, quiet=False):
    E, W, N = [], [], []
    r, b = m.r, m.bible
    for k in ("meta", "platform", "standards", "ladder", "groups", "settings", "voices", "ducking", "spatial",
              "emitters", "speed_link", "sounds", "events"):
        if k not in r:
            E.append(f"missing top-level '{k}'")
    if E:
        return report(E, W, strict, quiet, N)
    # canon refs
    if not b.ok():
        W.append("rr-bible not found: canon agreement unchecked (set RR_BIBLE_SKILL)")
    else:
        for where, node in m.refs:
            keys = node["canon"] if isinstance(node["canon"], list) else [node["canon"]]
            vals = node["v"] if isinstance(node["canon"], list) else [node["v"]]
            for k, v in zip(keys, vals):
                f = b.fact(k)
                if not f:
                    E.append(f"{where}: canon key {k} not in rr-bible")
                elif not canon_agrees(v, f["value"]):
                    E.append(f"{where}: {v} disagrees with canon {k} = {f['value']!r}")
                elif f["status"] in ("superseded",):
                    E.append(f"{where}: canon {k} is superseded")
        keys = set(r["meta"].get("canon", []))
        for s in r["sounds"].values():
            keys |= set(s.get("canon", []))
        for sl in r["speed_link"]:
            keys |= set(sl.get("canon", []))
        for k in sorted(keys):
            f = b.fact(k)
            if not f:
                E.append(f"canon key {k} cited but not in rr-bible")
            elif f["status"] == "superseded":
                E.append(f"canon key {k} is superseded")
    pend = r["meta"].get("pending_oq", {})
    for row in oq_rows(m):
        if row["pending"]:
            if not row["known"]:
                E.append(f"{row['id']} cited by {', '.join(row['cited'])} but meta.pending_oq has no such key")
            else:
                N.append(f"{row['id']} ({row['title']}) is not in rr-bible yet: `sound.py oq` prints the add-question "
                         f"command; then cite the number it prints")
            continue
        if b.ok() and not row["known"]:
            E.append(f"{row['id']} cited but not found in rr-bible")
        elif not row["relevant"]:
            W.append(f"{row['id']} ({row['title']}) cited by {', '.join(row['cited'])} never mentions audio, rr-soundsmith, "
                     f"the sound or its canon keys: wrong number? (`sound.py oq`)")
    for k, p in pend.items():
        miss = [f for f in ("title", "options", "default") if not p.get(f)]
        if miss:
            E.append(f"meta.pending_oq.{k}: missing {', '.join(miss)}")
    # groups
    G = r["groups"]
    roots = [g for g, v in G.items() if v.get("parent") is None]
    if roots != ["Master"]:
        E.append(f"groups: exactly one root 'Master' expected, found {roots}")
    for g, v in G.items():
        seen, p = set(), g
        while p:
            if p in seen:
                E.append(f"groups: cycle at {g}")
                break
            seen.add(p)
            p = G.get(p, {}).get("parent")
            if p and p not in G:
                E.append(f"groups.{g}: parent {p} missing")
                break
        if v.get("setting") and v["setting"] not in r["settings"]:
            E.append(f"groups.{g}: setting {v['setting']} not in settings")
    for k, v in r["settings"].items():
        if not 0 <= v <= 1:
            E.append(f"settings.{k}: {v} outside 0..1")
    # ladder
    L = r["ladder"]
    order = ["t1", "t2", "t3", "t4", "t5", "ambient"]
    for k in order + ["music"]:
        if not isinstance(L.get(k), (int, float)):
            E.append(f"ladder.{k} missing")
    if not E:
        for a_, b_ in zip(order, order[1:]):
            if L[a_] < L[b_]:
                E.append(f"ladder: {a_} ({L[a_]}) is quieter than {b_} ({L[b_]}); fail > crisis > commit > reward > UI > loops")
    # spatial, emitters
    for k, v in r["spatial"].items():
        if v.get("mode") not in ROLLOFF:
            E.append(f"spatial.{k}: mode {v.get('mode')} is not an Enum.RollOffMode")
        if not 0 < v.get("min", 0) < v.get("max", 0):
            E.append(f"spatial.{k}: need 0 < min < max studs")
        if v.get("max", 0) > 2 * r["meta"]["train_len"] + 200:
            W.append(f"spatial.{k}: max {v['max']} studs reaches far beyond the {r['meta']['train_len']}-stud train")
    # sounds
    S = r["sounds"]
    tmax = L.get("trim_max_db", 3)
    recipes = recipe_names(m.dir)
    for sid, s in S.items():
        w = f"sounds.{sid}"
        for f in ("tier", "group", "class", "space", "stage", "brief"):
            if f not in s:
                E.append(f"{w}: missing {f}")
        if any(f not in s for f in ("tier", "group", "class", "space")):
            continue
        if s["group"] not in G:
            E.append(f"{w}: group {s['group']} not in groups")
        if s["class"] not in r["standards"]:
            E.append(f"{w}: class {s['class']} not in standards")
            continue
        if not isinstance(s["tier"], int) or not 1 <= s["tier"] <= 7:
            E.append(f"{w}: tier must be 1..7")
        lo_hi = GROUP_TIERS.get(s["group"])
        if lo_hi and not lo_hi[0] <= s["tier"] <= lo_hi[1]:
            W.append(f"{w}: tier {s['tier']} in group {s['group']} (expected {lo_hi[0]}-{lo_hi[1]})")
        looped = s.get("looped", False)
        if (s["class"] in ("loop", "music")) != looped:
            E.append(f"{w}: class {s['class']} and looped={looped} disagree")
        if s["class"] == "loop" and s["tier"] != 6 or s["class"] == "music" and s["tier"] != 7:
            E.append(f"{w}: loops are tier 6, music tier 7")
        if s["space"] not in ("2d", "3d"):
            E.append(f"{w}: space must be 2d or 3d")
        if s["space"] == "3d":
            if s.get("emitter") not in r["emitters"]:
                E.append(f"{w}: 3d sound needs an emitter role from emitters")
            if s.get("spatial", "coach") not in r["spatial"]:
                E.append(f"{w}: spatial preset {s.get('spatial')} missing")
        if s.get("layer3d"):
            ly = s["layer3d"]
            if s["space"] != "2d":
                E.append(f"{w}: layer3d only on 2d sounds")
            if ly.get("emitter") not in r["emitters"]:
                E.append(f"{w}: layer3d emitter {ly.get('emitter')} not in emitters")
            if not -24 <= ly.get("gain_db", 0) <= 0:
                E.append(f"{w}: layer3d gain_db must be -24..0")
        if s["stage"] not in ("alpha", "siding"):
            E.append(f"{w}: stage must be alpha or siding")
        if not looped:
            if not isinstance(s.get("voices"), int) or s["voices"] < 1:
                E.append(f"{w}: voices must be an int >= 1")
            if not 0 <= s.get("cooldown", -1) <= 10:
                E.append(f"{w}: cooldown must be 0..10 s")
            p = s.get("pitch", [1, 1])
            if len(p) != 2 or not 0.5 <= p[0] <= p[1] <= 2:
                E.append(f"{w}: pitch must be [lo, hi] within 0.5..2")
            cap = r["voices"]["per_group"].get(s["group"])
            if cap and s.get("voices", 1) > cap:
                W.append(f"{w}: voices {s['voices']} above the {s['group']} cap {cap}")
            elif cap and s.get("voices", 1) * 2 > cap:
                W.append(f"{w}: voices {s['voices']} can fill over half the {s['group']} cap {cap} (it would push out "
                         f"other sounds of its tier)")
        if abs(s.get("trim_db", 0)) > tmax:
            E.append(f"{w}: trim_db {s['trim_db']} beyond +-{tmax} (move the ladder instead)")
        br = s.get("brief", {})
        for f in ("moment", "must_say", "sounds_like", "avoid", "len"):
            if not br.get(f):
                E.append(f"{w}: brief.{f} missing")
        blen, clen = br.get("len", [0, 0]), r["standards"][s["class"]]["len"]
        if len(blen) == 2 and not (clen[0] <= blen[0] <= blen[1] <= clen[1]):
            W.append(f"{w}: brief length {blen} outside the {s['class']} standard {clen}")
        if s["class"] == "alarm" and len(blen) == 2 and blen[1] * 1000 > r["meta"].get("danger_life_ms", 1e9):
            W.append(f"{w}: alarm longer than the danger ticket life ({r['meta']['danger_life_ms']} ms)")
        sy = s.get("synth")
        if isinstance(sy, dict):
            E += [f"{w}: {x}" for x in spec_problems(sy, r["standards"][s["class"]]["len"])]
        elif sy is not None and sy not in recipes:
            E.append(f"{w}: synth recipe {sy!r} not found (synth.py --list, or r_{sy} in <presets>/recipes.py)")
        elif sy is None and sid not in recipes:
            N.append(f"{w}: no placeholder recipe (synth skips it): add \"synth\": a recipe name or a layer spec "
                     f"(references/schema.md), or r_{sid} in <presets>/recipes.py")
        if not m.events_for(sid):
            W.append(f"{w}: no event plays it")
        mx = m.mix(sid)
        if mx["volume_raw"] > 10:
            E.append(f"{w}: needs Volume {mx['volume_raw']} (> 10): file too quiet for ladder {mx['target']}")
        elif mx["volume"] < 0.01:
            W.append(f"{w}: Volume {mx['volume']} is nearly silent")
    # hierarchy with trims and clamps (one-shots)
    shots = [(sid, S[sid]["tier"], m.mix(sid)["effective"]) for sid in S if not S[sid].get("looped")]
    ov = L.get("overlap_lu", 1)
    for a_sid, a_t, a_e in shots:
        for b_sid, b_t, b_e in shots:
            if a_t < b_t and b_e > a_e + ov:
                E.append(f"hierarchy: {b_sid} (tier {b_t}, {b_e} LUFS) louder than {a_sid} (tier {a_t}, {a_e}) by > {ov} LU")
    # voices, ducking
    for g in r["voices"]["per_group"]:
        if g not in G:
            E.append(f"voices.per_group: {g} not a group")
    names = set()
    for i, d in enumerate(r["ducking"]):
        w = f"ducking[{i}] {d.get('name')}"
        if d.get("name") in names:
            E.append(f"{w}: duplicate name")
        names.add(d.get("name"))
        trig = d.get("when", {})
        tsounds = list(trig.get("sounds", []))
        for x in tsounds:
            if x not in S:
                E.append(f"{w}: trigger sound {x} missing")
        for g in trig.get("groups", []):
            if g not in G:
                E.append(f"{w}: trigger group {g} missing")
            tsounds += [sid for sid, s in S.items() if g in m.group_chain(s["group"])]
        if not tsounds:
            E.append(f"{w}: no trigger")
        for g, dbv in d.get("duck", {}).items():
            if g not in G:
                E.append(f"{w}: ducks unknown group {g}")
                continue
            if not -40 <= dbv < 0:
                E.append(f"{w}: duck {g} {dbv} dB outside -40..0")
            selfhit = [x for x in tsounds if x in S and g in m.group_chain(S[x]["group"])]
            if selfhit:
                E.append(f"{w}: ducks {g}, which contains its own trigger {selfhit[0]} (self-ducking)")
        for k, lo, hi in (("attack", 0.005, 1.0), ("hold", 0.0, 5.0), ("release", 0.05, 5.0)):
            if not lo <= d.get(k, -1) <= hi:
                E.append(f"{w}: {k} must be {lo}..{hi} s")
        for x in [t for t in tsounds if t in S and not S[t].get("looped")]:
            te = m.mix(x)["effective"]
            for g, dbv in d.get("duck", {}).items():
                for y, s in S.items():
                    if g in m.group_chain(s["group"]) and not s.get("looped") and te - (m.mix(y)["effective"] + dbv) < 3:
                        W.append(f"{w}: {x} clears ducked {y} by under 3 LU")
    # speed link
    for i, sl in enumerate(r["speed_link"]):
        if sl.get("sound") not in S or not S[sl["sound"]].get("looped"):
            E.append(f"speed_link[{i}]: sound must be a looped sound")
        lo, hi = sl.get("rate", [1, 1])
        if not 0.5 <= lo < hi <= 2:
            E.append(f"speed_link[{i}]: rate must be lo < hi within 0.5..2 (PlaybackSpeed)")
        sp = sl.get("speeds", [])
        if sp and sl.get("ref") not in sp:
            E.append(f"speed_link[{i}]: ref {sl.get('ref')} is not one of the notch speeds {sp}")
    # events + rr-game-feel parity
    for e, ev in r["events"].items():
        acts = [k for k in ("play", "start", "stop", "toggle") if k in ev]
        if ev.get("via") not in ("feel", "direct"):
            E.append(f"events.{e}: via must be feel or direct")
        if ev.get("phase", "any") not in PHASES:
            E.append(f"events.{e}: phase {ev.get('phase')!r} not one of {', '.join(PHASES)}")
        if len(acts) != 1:
            E.append(f"events.{e}: exactly one of play, start, stop, toggle")
        for x in [ev.get("play"), ev.get("toggle")] + ev.get("start", []) + ev.get("stop", []):
            if x and x not in S:
                E.append(f"events.{e}: sound {x} missing")
        if ev.get("toggle") and not S.get(ev["toggle"], {}).get("looped"):
            E.append(f"events.{e}: toggle needs a looped sound")
        for x in ev.get("start", []):
            if x in S and not S[x].get("looped"):
                E.append(f"events.{e}: start needs looped sounds ({x})")
    fp = feel_presets()
    if not fp:
        W.append("rr-game-feel not found: cue parity unchecked (set RR_FEEL_PRESETS)")
    else:
        fev = json.loads(fp.read_text(encoding="utf-8")).get("events", {})
        for fe, fv in fev.items():
            cues = [c.get("sfx") for c in fv.get("channels", []) if c.get("type") == "cue" and c.get("sfx")]
            ev = r["events"].get(fe)
            for sfx in cues:
                if not ev or ev.get("via") != "feel" or ev.get("play") != sfx:
                    E.append(f"feel parity: rr-game-feel event {fe} cues sfx {sfx}; map it here as "
                             f'"{fe}": {{"via": "feel", "play": "{sfx}"}}')
                elif sfx in S and S[sfx]["tier"] != fv.get("priority"):
                    lowest = min(v.get("priority", 9) for n, v in fev.items() if any(
                        c.get("sfx") == sfx for c in v.get("channels", []) if c.get("type") == "cue"))
                    if S[sfx]["tier"] != lowest:
                        W.append(f"feel parity: {sfx} tier {S[sfx]['tier']} but its most important feel event is priority {lowest}")
            if not cues and ev and ev.get("via") == "direct" and ev.get("play"):
                N.append(f"feel parity: {fe} exists in rr-game-feel without a cue; add {{\"type\": \"cue\", \"sfx\": "
                         f"\"{ev['play']}\"}} there to route it through Feel (then set via feel here)")
        for e, ev in r["events"].items():
            if ev.get("via") == "feel":
                fv = fev.get(e)
                cues = [c.get("sfx") for c in (fv or {}).get("channels", []) if c.get("type") == "cue"]
                if not fv:
                    E.append(f"feel parity: events.{e} is via feel but rr-game-feel has no such event")
                elif ev.get("play") not in cues:
                    E.append(f"feel parity: events.{e} plays {ev.get('play')} but rr-game-feel cues {cues or 'nothing'}")
    # platform, licences
    pf = r["platform"]
    if pf.get("max_khz", 0) * 1000 < r["meta"]["sample_rate"]:
        E.append(f"meta.sample_rate {r['meta']['sample_rate']} above the platform limit {pf['max_khz']} kHz")
    for sid, a in m.assets.items():
        if sid not in S:
            E.append(f"assets.{sid}: no such sound in soundmap")
            continue
        e2, w2 = licence_problems(sid, a, S[sid]["stage"])
        E += e2
        W += w2
    state = {sid: m.asset_state(sid) for sid in S}
    alpha = [sid for sid in S if S[sid]["stage"] == "alpha"]
    heard = [sid for sid in alpha if state[sid] != "unassigned"]
    if release:
        for sid in S:
            if state[sid] not in ("final", "unassigned"):
                E.append(f"release: {sid} is {state[sid]}: placeholders never ship (av.audio.placeholder)")
        if not heard:
            N.append("release: no alpha sound has audio yet: this build ships silent, which the plan allows "
                     "(av.audio.priority_in_plan: sound is a COULD for the alpha)")
        else:
            for sid in alpha:
                if state[sid] == "unassigned":
                    E.append(f"release: {sid} is unassigned while {len(heard)} alpha sounds have audio: every alpha sound "
                             f"needs final licensed audio (av.audio.placeholder), or set its stage to siding")
    elif [sid for sid in alpha if state[sid] != "final"]:
        N.append(f"{sum(state[s_] != 'final' for s_ in alpha)} alpha sounds not final yet (placeholder or unassigned); "
                 "--release gates them")
    return report(E, W, strict, quiet, N)


def report(E, W, strict, quiet=False, N=()):
    ok = not E and not (strict and W)
    if not quiet:
        print(f"validate {'PASS' if ok else 'FAIL'}: {len(E)} errors, {len(W)} warnings, {len(N)} notes")
        for e in E:
            print("  ERROR " + e)
        for w in W:
            print("  warn  " + w)
        for n in N:
            print("  note  " + n)
    return 0 if ok else 1


# ------------------------------------------------------------------ analyze
def sid_from_name(m, path):
    """PLACEHOLDER_<id>, <id>, <id>_v2, <id>_std or <id>_<anything>: the longest sound id the name starts with."""
    stem = re.sub(r"^PLACEHOLDER_", "", Path(path).stem)
    hits = [s for s in m.sounds if stem == s or stem.startswith(s + "_")]
    return max(hits, key=len) if hits else None


def audio_files(paths):
    out = []
    for p in map(Path, paths):
        if p.is_dir():
            out += sorted(x for x in p.iterdir() if x.suffix.lower() in AUDIO_EXT)
        else:
            out.append(p)
    return out


def check_file(m, rep, sid=None, cls=None):
    """[(level, message)] for one measured file. level: FAIL, WARN, ok."""
    r = m.r
    cls = cls or (m.sounds[sid]["class"] if sid else "oneshot")
    std, pf = r["standards"][cls], r["platform"]
    out = []
    add = lambda lvl, msg: out.append((lvl, msg))  # noqa: E731
    ext = Path(rep["file"]).suffix.lower().lstrip(".")
    if ext not in pf["formats"]:
        add("FAIL", f"format .{ext} is not importable (tech.audio.import_formats: {', '.join(pf['formats'])})"
                    + ("; transcode to .ogg Vorbis or .wav" if ext == "opus" else ""))
    if not rep.get("duration"):
        add("FAIL", "empty audio (0 samples): re-export the sound")
        return out
    if rep.get("bytes", 0) > pf["max_mb"] * 1024 * 1024:
        add("FAIL", f"{rep['bytes'] / 1048576:.1f} MB is over the {pf['max_mb']} MB import limit")
    if rep.get("duration", 0) > pf["max_min"] * 60:
        add("FAIL", f"{rep['duration']:.0f} s is over the {pf['max_min']}-minute import limit")
    if rep.get("rate", 0) > pf["max_khz"] * 1000:
        add("FAIL", f"sample rate {rep['rate']} Hz is over {pf['max_khz']} kHz (Studio rejects it); resample to 48 kHz")
    elif rep.get("rate", 48000) < 44100:
        add("WARN", f"sample rate {rep['rate']} Hz sounds dull; deliver 44.1 or 48 kHz")
    if rep.get("nch") not in pf["channels"]:
        add("FAIL", f"{rep.get('nch')} channels: Roblox takes mono, stereo, 3.0 or 5.1")
    if rep.get("bits") == 8:
        add("WARN", "8-bit audio is noisy; deliver 16 or 24-bit")
    lo, hi = std["len"]
    if rep["duration"] < lo / 2:
        add("FAIL", f"length {rep['duration']} s is under half the {cls} minimum {lo} s: truncated export?")
    elif not lo <= rep["duration"] <= hi:
        add("WARN", f"length {rep.get('duration')} s outside the {cls} standard {lo}-{hi} s")
    if not rep.get("decoded"):
        add("WARN", "not decoded (no ffmpeg): loudness, peaks and silence unmeasured; export WAV or install ffmpeg")
        return out
    if rep.get("clip_runs"):
        add("FAIL", f"{rep['clip_runs']} clipped runs (3+ samples at full scale): re-export without clipping")
    tp = rep.get("true_peak")
    pk = tp if tp is not None else rep.get("sample_peak")
    if pk is not None and pk > 0:
        add("FAIL", f"peak {pk} dB{'TP' if tp is not None else 'FS'} is over full scale")
    elif pk is not None and pk > std["tp_max"]:
        add("WARN", f"peak {pk} dB{'TP' if tp is not None else 'FS (sample; no numpy)'} above {std['tp_max']}")
    lvl = rep.get(std["metric"])
    if lvl is None or lvl < -70:
        add("FAIL", f"silent: {std['metric']} {lvl if lvl is not None else 'unmeasurable'} (under -70 LUFS): export the actual sound")
    else:
        need = std["target"] - lvl
        head = std["tp_max"] - 0.1 - (pk if pk is not None else std["tp_max"])
        if abs(need) > std["tol"]:
            gain = min(need, head, 30.0) if need > 0 else need
            add("WARN", f"{std['metric']} {lvl} vs standard {std['target']} (gain {need:+.1f} dB; peak allows "
                        f"{head:+.1f}); --fix-out applies {gain:+.1f} dB" + (" (capped at +30: re-export louder)" if need > 30 else "")
                + ", or register it as is and the mix compensates")
    if std.get("lead_max_ms") is not None and rep.get("lead_ms") is not None:
        if rep["lead_ms"] > 50:
            add("FAIL", f"{rep['lead_ms']} ms of silence before the sound: it will feel late; trim the start")
        elif rep["lead_ms"] > std["lead_max_ms"]:
            add("WARN", f"{rep['lead_ms']} ms lead silence (max {std['lead_max_ms']})")
    if std.get("tail_max_ms") is not None and (rep.get("tail_ms") or 0) > std["tail_max_ms"]:
        add("WARN", f"{rep['tail_ms']} ms trailing silence (max {std['tail_max_ms']}): trim it, it holds a voice")
    if rep.get("dc", 0) > 0.005:
        add("WARN", f"DC offset {rep['dc']}: high-pass or remove DC")
    if std.get("seam") and rep.get("seam"):
        sm = rep["seam"]
        if sm["ratio"] > 2 and sm["jump"] > 0.01:
            add("FAIL", f"loop seam clicks (wrap step {sm['jump']}, {sm['ratio']}x the steps around it): crossfade the ends")
    if rep.get("phone_loss_db") is not None and rep["phone_loss_db"] > std.get("phone_loss_max", 99):
        add("WARN", f"loses {rep['phone_loss_db']} dB on phone speakers (max {std['phone_loss_max']}): add 0.5-4 kHz content")
    if sid and m.sounds[sid]["space"] == "3d" and rep.get("nch", 1) > 1:
        add("WARN", "stereo file on a positional (3d) sound: deliver mono (--fix-out --mono)")
    if rep.get("corr") is not None and rep["corr"] < 0:
        add("WARN", f"left/right correlation {rep['corr']}: phasey, collapses badly to mono")
    is_ph = "PLACEHOLDER" in rep.get("info", {}).get("ICMT", "") or Path(rep["file"]).name.startswith("PLACEHOLDER_")
    if is_ph:
        add("ok", "placeholder (never ships)")
    return out


def cmd_analyze(m, a):
    files = audio_files(a.paths)
    if not files:
        print("no audio files found")
        return 2
    rows, worst = [], 0
    for f in files:
        sid = a.as_ or sid_from_name(m, f)
        if a.as_ and a.as_ not in m.sounds:
            print(f"unknown sound {a.as_}")
            return 2
        cls = a.cls or (m.sounds[sid]["class"] if sid else "oneshot")
        try:
            rep = al.measure(f, loop=m.r["standards"][cls].get("seam", False))
        except (al.AudioError, OSError, struct.error) as e:
            rows.append({"file": str(f), "status": "FAIL", "checks": [("FAIL", f"unreadable: {e}")]})
            worst = 1
            continue
        checks = check_file(m, rep, sid, cls)
        status = "FAIL" if any(c[0] == "FAIL" for c in checks) else "WARN" if any(c[0] == "WARN" for c in checks) else "PASS"
        worst = max(worst, 1 if status == "FAIL" else 0)
        row = {"file": str(f), "sound": sid, "class": cls, "status": status, "measured": rep, "checks": checks}
        if a.fix_out and rep.get("decoded"):
            row["fixed"] = fix_file(m, f, rep, cls, a.fix_out, a.mono)
        rows.append(row)
    if a.json:
        print(json.dumps(rows, indent=1, default=str))
        return worst
    for row in rows:
        rep = row.get("measured", {})
        std = m.r["standards"][row.get("class", "oneshot")]
        lvl = rep.get(std["metric"])
        print(f"{row['status']:4} {Path(row['file']).name}  [{row.get('sound') or '?'}; {row.get('class')}]  "
              f"{rep.get('duration', '?')} s {rep.get('rate', '?')} Hz {rep.get('nch', '?')}ch  "
              f"{std['metric']} {lvl}  TP {rep.get('true_peak')}  phone loss {rep.get('phone_loss_db', '-')} dB")
        for lvl_, msg in row["checks"]:
            if lvl_ != "ok" or a.verbose:
                print(f"     {lvl_:4} {msg}")
        if row.get("fixed"):
            print(f"     {'' if row['fixed'].startswith('(') else 'wrote '}{row['fixed']}")
    n = {s: sum(r_["status"] == s for r_ in rows) for s in ("PASS", "WARN", "FAIL")}
    print(f"analyze: {n['PASS']} pass, {n['WARN']} warn, {n['FAIL']} fail ({len(rows)} files)")
    return worst


def fix_file(m, path, rep, cls, out_dir, mono=False):
    """A new file toward the class standard: trims lead/tail silence of one-shots, optional mono, then gain only (never
    above the peak ceiling, at most +30 dB). Never touches the source; cannot repair clipping or resample."""
    std, pf = m.r["standards"][cls], m.r["platform"]
    if rep.get("clip_runs") or rep.get("rate", 0) > pf["max_khz"] * 1000:
        return "(not fixed: clipping and sample rate need a re-export from the source)"
    d = al.load(path)
    chans, rate, notes = d["channels"], d["rate"], []
    if mono and len(chans) > 1 and al.np is None:
        notes.append("mono skipped: needs numpy")
    if mono and len(chans) > 1 and al.np is not None:
        mix = sum(chans) / len(chans)
        if al.loudness([mix], rate)["m_max"] < al.loudness(chans, rate)["m_max"] - 6:
            loudest = max(chans, key=lambda c: float(al.np.mean(c ** 2)))
            mix, _ = loudest, notes.append("channels cancel when summed: kept the louder channel")
        chans = [mix]
        notes.append("mono")
    if not std.get("seam") and al.np is not None:
        lead, tail = rep.get("lead_ms") or 0, rep.get("tail_ms") or 0
        a0 = int(max(0.0, lead - 2) / 1000 * rate) if lead > std.get("lead_max_ms", 10) else 0
        cut = int(max(0.0, tail - std.get("tail_max_ms", 300) / 2) / 1000 * rate) if tail > std.get("tail_max_ms", 300) else 0
        if a0 or cut:
            n = len(chans[0])
            chans = [c[a0:n - cut].copy() for c in chans]
            f = min(len(chans[0]), int(0.005 * rate))
            for c in chans:
                c[len(c) - f:] *= al.np.linspace(1, 0, f)
            notes.append(f"trimmed {a0 / rate * 1000:.0f} ms lead, {cut / rate * 1000:.0f} ms tail")
    lv = al.loudness(chans, rate)
    lvl = lv.get(std["metric"])
    pk = al.true_peak(chans)
    pk = pk if pk is not None else al.db(al.sample_peak(chans))
    if lvl is None or lvl < -70:
        return "(not fixed: silent)"
    gain = min(std["target"] - lvl, std["tp_max"] - 0.1 - pk, 30.0)
    g = 10 ** (gain / 20)
    chans = [[v * g for v in c] if al.np is None else c * g for c in chans]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out = Path(out_dir) / (Path(path).stem + "_std.wav")
    if out.resolve() == Path(path).resolve() or out.exists():
        return f"(skipped: {out} exists)"
    info = dict(d.get("info") or {})
    info["ICMT"] = (info.get("ICMT", "") + f" | rr-soundsmith --fix-out gain {gain:+.2f} dB from {Path(path).name}").strip(" |")
    al.write_wav(out, rate, chans, bits=24, info=info)
    return f"{out} (gain {gain:+.2f} dB{'; ' + '; '.join(notes) if notes else ''})"


# ------------------------------------------------------------------ synth, register
def cmd_synth(m, a):
    try:
        import synth as sy
    except ImportError as e:
        print(f"synth needs numpy ({e}); pip install numpy")
        return 2
    ids = list(m.sounds) if not a.ids or a.ids == ["all"] else a.ids
    bad = [i for i in ids if i not in m.sounds]
    if bad:
        print(f"unknown sounds: {', '.join(bad)}")
        return 2
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for sid in ids:
        name, fn = sy.resolve(sid, m.sounds[sid], m.dir)
        if fn is None:
            print(f"skip {sid}: no recipe (add \"synth\" in the soundmap or r_{sid} in {m.dir / 'recipes.py'})")
            continue
        std = m.r["standards"][m.sounds[sid]["class"]]
        row = sy.render(sid, name, std, out, seed=a.seed, fn=fn)
        chk = check_file(m, row["measured"], sid)
        row["status"] = "FAIL" if any(c[0] == "FAIL" for c in chk) else "WARN" if any(c[0] == "WARN" for c in chk) else "PASS"
        row["checks"] = [c[1] for c in chk if c[0] != "ok"]
        rows.append(row)
        me = row["measured"]
        print(f"{row['status']:4} {row['file']:34} {me['duration']:5.2f} s  {std['metric']} {me.get(std['metric'])}  "
              f"TP {me.get('true_peak')}  phone -{me.get('phone_loss_db')} dB")
    lines = ["# PLACEHOLDER SFX (rr-soundsmith)", "",
             f"Synthesised {TODAY} from code only (no samples, so no third-party rights). For prototyping timing and mix "
             "in Studio. Never ship: `sound.py validate --release` fails while an alpha sound uses one.", "",
             "Owner, to hear them in Studio: import in Asset Manager (name them `PLACEHOLDER <id>`), then "
             "`sound.py register <id> --file <this folder>/PLACEHOLDER_<id>.wav --id <asset id> --source placeholder "
             "--origin \"rr-soundsmith synth\"` and `sound.py build`.", "",
             "| id | file | s | level | TP | phone loss | check | sha1 |", "|---|---|---|---|---|---|---|---|"]
    for row in rows:
        me, std = row["measured"], m.r["standards"][m.sounds[row["id"]]["class"]]
        lines.append(f"| {row['id']} | {row['file']} | {me['duration']:.2f} | {me.get(std['metric'])} {std['metric']} | "
                     f"{me.get('true_peak')} | {me.get('phone_loss_db')} dB | {row['status']} | {row['sha1']} |")
    (out / "PLACEHOLDERS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    fails = sum(r_["status"] == "FAIL" for r_ in rows)
    print(f"synth: {len(rows)} placeholders in {out} ({fails} fail); manifest PLACEHOLDERS.md")
    return 1 if fails else 0


def cmd_register(m, a):
    if a.sid not in m.sounds:
        print(f"unknown sound {a.sid}")
        return 2
    s = m.sounds[a.sid]
    if a.source != "placeholder" and not a.id:
        print(f"register needs --id N: the Roblox asset id of the uploaded audio ({a.source})")
        return 2
    if inside_skill(m.assets_path) and not a.dry_run:
        print(f"register refused: the register would be written inside the skill folder ({m.assets_path}), which a "
              "re-sync overwrites. Use a mission copy (RR_SOUND_PRESETS=<M>/src/sound) or the project home "
              f"(`sound.py promote --from {SKILL / 'presets'}` creates {home_dir()}); `sound.py where` shows which is in use")
        return 2
    entry = {"ids": [str(i) if str(i).startswith("rbxassetid://") else f"rbxassetid://{i}" for i in a.id],
             "source": a.source, "origin": a.origin or ("rr-soundsmith synth" if a.source == "placeholder" else ""),
             "licence": a.licence or "", "proof": a.proof or "", "credit": a.credit or "", "creator": a.creator or "",
             "community": bool(a.community), "files": [], "sha1": [], "measured": [], "registered": TODAY}
    for f in a.file:
        std = m.r["standards"][s["class"]]
        rep = al.measure(f, loop=std.get("seam", False))
        chk = check_file(m, rep, a.sid)
        tagged = "placeholder" in " ".join(str(v) for v in rep.get("info", {}).values()).lower()
        if tagged and a.source != "placeholder":
            print(f"register refused: {Path(f).name} carries the PLACEHOLDER tag in its INFO chunk; register it with "
                  "--source placeholder, or register the final file")
            return 1
        for lvl, msg in chk:
            if lvl != "ok":
                print(f"  {lvl} {Path(f).name}: {msg}")
        if any(c[0] == "FAIL" for c in chk):
            print(f"register refused: {Path(f).name} fails analysis (fix it, then register)")
            return 1
        entry["files"].append(Path(f).name)
        entry["sha1"].append(hashlib.sha1(Path(f).read_bytes()).hexdigest()[:12])
        entry["measured"].append({k: rep.get(k) for k in ("m_max", "integrated", "true_peak", "duration", "phone_loss_db")})
    if not a.file and a.source != "roblox_licensed":
        print("register needs --file (the file that was uploaded) unless the source is roblox_licensed")
        return 2
    lv = [x.get(m.metric(a.sid)) for x in entry["measured"] if x.get(m.metric(a.sid)) is not None]
    if len(lv) > 1 and max(lv) - min(lv) > 2:
        print(f"  WARN variations differ by {max(lv) - min(lv):.1f} LU: match them within 2 LU")
    errs, warns = licence_problems(a.sid, entry, s["stage"])
    for w in warns:
        print("  warn  " + w)
    if errs:
        for e in errs:
            print("  ERROR " + e)
        print("register refused (licence gate): nothing written")
        return 1
    if a.dry_run:
        print(json.dumps(entry, indent=1))
        print("dry run: nothing written")
        return 0
    data = json.loads(m.assets_path.read_text(encoding="utf-8")) if m.assets_path.is_file() else {}
    data.setdefault("_about", "rr-soundsmith asset register, written by sound.py register; licence proof per sound")
    data[a.sid] = entry
    m.assets_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    m.assets[a.sid] = entry
    mx = m.mix(a.sid)
    print(f"registered {a.sid}: {a.source}, {len(entry['ids'])} id(s); file level {mx['file_level']} ({mx['level_from']}) "
          f"-> Volume {mx['volume']}; now run sound.py build")
    return 0


# ------------------------------------------------------------------ brief
def route(s):
    """Where to get a sound: brief.route, else by class (alarms must be distinct, loops seamless)."""
    if s["brief"].get("route"):
        return s["brief"]["route"]
    if s["class"] == "alarm" or s["tier"] == 1:
        return "commission / self-made (distinct)"
    return "self-made loop / store" if s.get("looped") else "store / self-made"


def space_text(m, s):
    r = m.r
    if s["space"] == "3d":
        txt = f"3D at the {s.get('emitter')} ({r['emitters'].get(s.get('emitter'), '')})"
    else:
        txt = "2D (global: same level everywhere)"
    if s.get("layer3d"):
        txt += f", plus a positional layer at the {s['layer3d']['emitter']} (OQ-035 default)"
    return txt


def brief_md(m, sid, oqs=None):
    s, r = m.sounds[sid], m.r
    br, std, mx = s["brief"], r["standards"][s["class"]], m.mix(sid)
    evs = m.events_for(sid)
    fp = feel_presets()
    fev = json.loads(fp.read_text(encoding="utf-8")).get("events", {}) if fp else {}
    beats = []
    for e in evs:
        if e in fev and m.events[e]["via"] == "feel":
            chans = fev[e].get("channels", [])
            hs = [c for c in chans if c.get("type") == "hitstop"]
            beats.append(f"{e}" + (f" (lands with a {hs[0]['ms']} ms hit-stop at 0 ms)" if hs else ""))
        else:
            beats.append(f"{e} (Sound.event)")
    chan = "mono" if s["space"] == "3d" or s.get("layer3d") else "mono or stereo"
    canon = []
    for k in s.get("canon", [])[:4]:
        v = m.bible.value(k, None) if m.bible.ok() else None
        if v:
            canon.append(f"`{k}`: {v}")
    lines = [f"## {sid} · {m.sound_phase(sid)} · tier {s['tier']} · {s['group']} · {s['class']} · {m.asset_state(sid)}", "",
             f"- **Moment:** {br['moment']}. Events: {', '.join(beats) or 'none'}.",
             f"- **Must say:** {br['must_say']}",
             f"- **Sounds like:** {br['sounds_like']}"]
    if br.get("layers"):
        lines.append(f"- **Layers:** {'; '.join(br['layers'])}")
    lines += [f"- **Length:** {br['len'][0]}-{br['len'][1]} s" + ("; seamless loop, no fade in or out" if s.get("looped") else
              f"; sound starts within {std.get('lead_max_ms', 10)} ms, tail silence under {std.get('tail_max_ms', 300)} ms"),
              f"- **Variations:** {br.get('variations', 1)}" + ("" if s.get("looped") or s.get("pitch", [1, 1])[0] == s.get("pitch", [1, 1])[1]
                                                                 else f" (runtime pitch spread {s['pitch'][0]}-{s['pitch'][1]})"),
              f"- **Space:** {space_text(m, s)}; deliver {chan}.",
              f"- **Level:** {s['class']} standard {std['metric']} {std['target']} LUFS, at most {std['tp_max']} dBTP; "
              f"the mix sets {mx['target']} LUFS in game (ladder {m.ladder_key(sid)}).",
              f"- **Phones:** loses at most {std.get('phone_loss_max', 6)} dB on a phone speaker: keep energy in 0.5-4 kHz.",
              f"- **Avoid:** {br['avoid']}."]
    if canon:
        lines.append(f"- **Canon:** {' · '.join(canon)}")
    if s.get("oq"):
        oqs = oqs if oqs is not None else {row["id"]: row for row in oq_rows(m)}
        lines.append("- **Open:** " + "; ".join(f"{o} ({oqs[o]['title']}) default {oqs[o]['default'][:90]}" if o in oqs
                                                   else o for o in s["oq"]))
    return "\n".join(lines) + "\n"


def briefs_text(m, ids):
    b = m.bible
    v = lambda k, d: b.value(k, d) if b.ok() else d  # noqa: E731
    ids = m.by_phase(ids)
    oqs = {row["id"]: row for row in oq_rows(m)}
    head = ["# Risky Rails audio briefs (rr-soundsmith)", "",
            f"Generated {TODAY} from soundmap.json and canon; {len(ids)} sounds in phase order; format in "
            "references/brief-format.md. Edit the soundmap, not this file.", "",
            f"- **Licence** (av.audio.licence): {v('av.audio.licence', 'owner uploads or Roblox-licensed only')}. Record "
            "proof with `sound.py register`. Uploaded audio stays private to the game: never distribute it on the Creator Store.",
            f"- **Tone** (identity.tone): {v('identity.tone.company', 'an incompetent train company')}; "
            f"{v('identity.tone.not', 'never horror')}.",
            "- **Delivery:** dry (no reverb baked in), WAV 48 or 44.1 kHz, 16 or 24-bit; mono for anything positional.",
            "- **Meter:** levels are ITU BS.1770 with mono counted as dual mono (+3 dB, as heard on two speakers). On a "
            "meter that reads mono as one channel, aim 3 dB lower (m_max -14 reads -17 there).",
            "- **Done when:** `sound.py analyze <file> --as <id>` shows no FAIL, then register and build.",
            "- **Route:** store = Roblox-licensed Creator Store search using Sounds like; self-made = record or perform "
            "it; commission = a sound designer with a written rights grant.", "",
            "| phase | id | tier | class | takes | length s | space | state | route |", "|---|---|---|---|---|---|---|---|---|"]
    for sid in ids:
        s = m.sounds[sid]
        sp = s["space"] + (f" @{s['emitter']}" if s.get("emitter") else "") + (" +3d" if s.get("layer3d") else "")
        head.append(f"| {m.sound_phase(sid)} | {sid} | {s['tier']} | {s['class']} | {s['brief'].get('variations', 1)} | "
                    f"{s['brief']['len'][0]}-{s['brief']['len'][1]} | {sp} | {m.asset_state(sid)} | {route(s)} |")
    return "\n".join(head) + "\n\n" + "\n".join(brief_md(m, sid, oqs) for sid in ids)


def cmd_brief(m, a):
    ids = list(m.sounds) if not a.ids or a.ids == ["all"] else a.ids
    bad = [i for i in ids if i not in m.sounds]
    if bad:
        print(f"unknown sounds: {', '.join(bad)}")
        return 2
    text = briefs_text(m, ids)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out} ({len(ids)} briefs)")
    else:
        print(text)
    return 0


# ------------------------------------------------------------------ list, show
def cmd_list(m, a):
    ids = [s for s in m.by_phase() if (not a.group or m.sounds[s]["group"] == a.group) and (not a.tier or m.sounds[s]["tier"] == a.tier)]
    print(f"{len(ids)} sounds (presets: {m.dir})")
    for sid in ids:
        s, mx = m.sounds[sid], m.mix(sid)
        print(f"  {m.sound_phase(sid):7} {sid:18} t{s['tier']} {s['group']:7} {s['class']:7} {s['space']}{'+3d' if s.get('layer3d') else '   '} "
              f"{s['stage']:6} target {mx['target']:6.1f}  Volume {mx['volume']:.3f}  {m.asset_state(sid)}")
    return 0


def cmd_show(m, a):
    if a.name in m.events:
        ev = m.events[a.name]
        print(json.dumps({a.name: ev}, indent=1) if a.json else f"event {a.name}: {json.dumps(ev)}")
        return 0
    if a.name not in m.sounds:
        print(f"no sound or event {a.name!r}")
        return 1
    s = dict(m.sounds[a.name])
    s["mix"] = m.mix(a.name)
    s["events"] = m.events_for(a.name)
    s["asset"] = m.assets.get(a.name, "unassigned")
    s["groups"] = m.group_chain(s["group"])
    if a.json:
        print(json.dumps(s, indent=1))
    else:
        print(brief_md(m, a.name))
        print(f"mix: {json.dumps(s['mix'])}\ngroups: {' < '.join(s['groups'])}\nasset: {json.dumps(s['asset'])}")
    return 0


# ------------------------------------------------------------------ Lua generation
def lua(v, ind=0):
    pad = "\t" * ind
    if v is None:
        return "nil"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(round(v, 6)) if isinstance(v, float) else str(v)
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(v, list):
        if all(not isinstance(x, (dict, list)) for x in v):
            return "{" + ", ".join(lua(x) for x in v) + "}"
        return "{\n" + "".join(f"{pad}\t{lua(x, ind + 1)},\n" for x in v) + pad + "}"
    items = []
    for k, x in v.items():
        key = k if re.fullmatch(r"[A-Za-z_]\w*", k) and k not in LUA_KW else f'["{k}"]'
        items.append(f"{pad}\t{key} = {lua(x, ind + 1)},\n")
    return "{\n" + "".join(items) + pad + "}"


LUA_KW = {"and", "break", "do", "else", "elseif", "end", "false", "for", "function", "if", "in", "local", "nil", "not",
          "or", "repeat", "return", "then", "true", "until", "while", "continue", "type", "export"}


def runtime_map(m):
    r = m.r
    order, seen = [], set()

    def add(g):
        if g in seen:
            return
        p = r["groups"][g].get("parent")
        if p:
            add(p)
        seen.add(g)
        order.append({"name": g, "parent": p, "setting": r["groups"][g].get("setting", "master" if g == "Master" else None)})
    for g in r["groups"]:
        add(g)
    sounds = {}
    for sid, s in r["sounds"].items():
        a, mx = m.assets.get(sid) or {}, m.mix(sid)
        sp = r["spatial"].get(s.get("spatial", "coach"))
        ent = {"group": s["group"], "tier": s["tier"], "volume": mx["volume"], "gainDb": mx["gain_db"],
               "looped": bool(s.get("looped")), "space": s["space"], "emitter": s.get("emitter"),
               "rolloff": {"mode": sp["mode"], "min": sp["min"], "max": sp["max"]} if s["space"] == "3d" else None,
               "voices": 1 if s.get("looped") else s.get("voices", 1), "cooldown": s.get("cooldown", 0),
               "pitch": s.get("pitch", [1, 1]), "ids": a.get("ids", []), "placeholder": a.get("source") == "placeholder",
               "keep": s["class"] == "alarm",
               "length": (a.get("measured") or [{}])[0].get("duration") or s["brief"]["len"][1], "stage": s["stage"]}
        if s.get("layer3d"):
            ly = s["layer3d"]
            lsp = r["spatial"].get(ly.get("spatial", "coach"))
            ent["layer3d"] = {"emitter": ly["emitter"], "gainDb": ly.get("gain_db", -4),
                              "rolloff": {"mode": lsp["mode"], "min": lsp["min"], "max": lsp["max"]}}
        sounds[sid] = ent
    duck = []
    for d in r["ducking"]:
        duck.append({"name": d["name"], "sounds": {x: True for x in d["when"].get("sounds", [])},
                     "groups": {g: True for g in d["when"].get("groups", [])}, "duck": d["duck"],
                     "attack": d["attack"], "hold": d["hold"], "release": d["release"]})
    events = {}
    for e, ev in r["events"].items():
        x = {"via": ev["via"]}
        for k in ("play", "toggle", "pitch"):
            if k in ev:
                x[k] = ev[k]
        for k in ("start", "stop"):
            if k in ev:
                x[k] = ev[k]
        if "pitch_step" in ev:
            x["pitchStep"] = ev["pitch_step"]
        events[e] = x
    speed = [{"sound": sl["sound"], "ref": sl["ref"], "rate": sl["rate"], "slope": sl.get("gain_slope", 0),
              "silentBelow": sl.get("silent_below", 0)} for sl in r["speed_link"]]
    return {"version": r["version"], "generated": TODAY, "refVolume": r["meta"]["ref_volume"],
            "placeholders": sum(1 for s in sounds.values() if s["placeholder"]),
            "unassigned": sum(1 for s in sounds.values() if not s["ids"]),
            "groups": order, "settings": r["settings"],
            "voices": {"max": r["voices"]["max"], "perGroup": r["voices"]["per_group"], "protectTier": r["voices"]["protect_tier"]},
            "ducking": duck, "sounds": sounds, "events": events, "speed": speed}


def setup_lua(m, rm):
    stud = m.r["meta"]["stud_m"]
    lines = ["-- studio_sound_setup.lua (GENERATED by rr-soundsmith build). Run once in the Studio command bar.",
             "-- Creates SoundService.RR_Mix with the SoundGroup tree. RR_Sound reuses these groups by name and keeps the",
             "-- Volume you set on each group here as its base; player settings and ducking multiply on top at run time.",
             "-- Safe to re-run: existing groups (and their volumes) are kept, never deleted.",
             'local SoundService = game:GetService("SoundService")',
             'local mix = SoundService:FindFirstChild("RR_Mix")',
             'if not mix then mix = Instance.new("Folder"); mix.Name = "RR_Mix"; mix.Parent = SoundService end',
             "local made = {}"]
    for g in rm["groups"]:
        parent = f'made["{g["parent"]}"]' if g["parent"] else "mix"
        lines += [f'do local g = {parent}:FindFirstChild("{g["name"]}")',
                  f'\tif not g then g = Instance.new("SoundGroup"); g.Name = "{g["name"]}"; g.Volume = 1; g.Parent = {parent} end',
                  f'\tmade["{g["name"]}"] = g end']
    lines += ["SoundService.RespectFilteringEnabled = true -- client sounds stay local (tech.audio.local_playback)",
              f"SoundService.DistanceFactor = {round(1 / stud, 3)} -- 1 / tech.units.stud_m; Doppler only",
              'print("RR_Mix ready: " .. #mix:GetDescendants() .. " SoundGroups")']
    return "\n".join(lines) + "\n"


def open_decisions_md(m):
    rows = oq_rows(m)
    out = []
    for r_ in rows:
        tail = f"; record: `{r_['cmd_portable']}`" if r_["cmd"] else ""
        warn = " **(check: this OQ never mentions audio; wrong number?)**" if not r_["relevant"] else ""
        out.append(f"- {r_['id']} ({r_['status']}) {r_['title']}: default {r_['default'].rstrip('.')}. Cited by "
                   f"{', '.join(r_['cited'])}{warn}{tail}")
    return out or ["none cited"]


def spec_md(m, rm):
    r = m.r
    L = r["ladder"]
    lines = ["# SOUND_SPEC (generated by rr-soundsmith build; not canon)", "",
             f"{len(r['sounds'])} sounds, {len(r['events'])} events, {rm['placeholders']} placeholders, "
             f"{rm['unassigned']} unassigned. Presets: soundmap.json {TODAY}. Runtime: legacy Sound + SoundGroup "
             "(tech.audio.soundgroup_status: supported; Roblox now recommends the Audio API; port later if needed).", "",
             "## Mix ladder (in-game level, LUFS)", "",
             f"fail t1 {L['t1']} > crisis t2 {L['t2']} > commit t3 {L['t3']} > reward t4 {L['t4']} > UI t5 {L['t5']} > "
             f"ambient loops {L['ambient']} (integrated); music {L['music']}. Trims within +-{L['trim_max_db']} dB.", "",
             "## Event -> sound (phase order)", "",
             "| phase | event | via | action | sound | tier | group | space | target | Volume | asset |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in m.events_by_phase():
        ev = r["events"][e]
        for act in ("play", "toggle", "start", "stop"):
            if act not in ev:
                continue
            for sid in ev[act] if isinstance(ev[act], list) else [ev[act]]:
                s, mx = r["sounds"][sid], m.mix(sid)
                sp = s["space"] + (f" @{s.get('emitter')}" if s.get("emitter") else "") + (f" +3d @{s['layer3d']['emitter']}" if s.get("layer3d") else "")
                lines.append(f"| {m.event_phase(e)} | {e} | {ev['via']} | {act} | {sid} | {s['tier']} | {s['group']} | {sp} | "
                             f"{mx['target']} | {mx['volume']} | {m.asset_state(sid)} |")
    lines += ["", "## Ducking", ""]
    for d in r["ducking"]:
        trig = ", ".join(d["when"].get("sounds", []) + [f"group {g}" for g in d["when"].get("groups", [])])
        duck = ", ".join(f"{g} {v} dB" for g, v in d["duck"].items())
        lines.append(f"- **{d['name']}**: while {trig} plays: {duck}; attack {d['attack']} s, hold {d['hold']} s, release {d['release']} s")
    v = r["voices"]
    lines += ["", "## Voices and priority", "",
              f"At most {v['max']} one-shots at once; per group {json.dumps(v['per_group'])}. When full, a new sound takes "
              f"the least important voice (highest tier number), oldest first. New tier 1-{v['protect_tier']} sounds always "
              "get a voice, but a crisis alarm that is playing (class alarm) is cut only by the fail or by another alarm: "
              "crisis impacts (glass, coupling) yield to it and are dropped instead. A stolen voice stops its positional "
              "layer too. Loops are keyed and never stolen. Per-sound cooldowns and voice counts are in RR_SoundMap.", "",
              "## Speed link", ""]
    for sl in r["speed_link"]:
        lines.append(f"- {sl['sound']}: PlaybackSpeed = Speed / {sl['ref']} clamped {sl['rate']}; level "
                     f"{sl.get('gain_slope')} x 20log10(Speed/{sl['ref']}) dB; silent below {sl.get('silent_below')} "
                     "(av.audio.speed_link). Call Sound.setSpeed whenever Speed changes (each Heartbeat or the train's "
                     "Speed value Changed), including the departure ramp and arrival braking, so the wheels fade to "
                     "silence at the StopMarker.")
    lines += ["", "## Open decisions (defaults in use; the owner decides)", ""] + open_decisions_md(m)
    return "\n".join(lines) + "\n"


def licences_md(m):
    lines = ["# LICENCES (generated by rr-soundsmith build from assets.json)", "",
             f"Rule (av.audio.licence): {m.bible.value('av.audio.licence', 'owner uploads or Roblox-licensed only') if m.bible.ok() else 'owner uploads or Roblox-licensed only'}.", "",
             "| sound | stage | state | source | origin | creator | licence | proof | credit | ids | registered |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for sid, s in m.sounds.items():
        a = m.assets.get(sid) or {}
        lines.append(f"| {sid} | {s['stage']} | {m.asset_state(sid)} | {a.get('source', '-')} | {a.get('origin', '-')} | "
                     f"{a.get('creator', '') or '-'} | {a.get('licence', '') or '-'} | {a.get('proof', '') or '-'} | "
                     f"{a.get('credit', '') or '-'} | {' '.join(a.get('ids', [])) or '-'} | {a.get('registered', '-')} |")
    credits = [f"- {a['credit']}" for a in m.assets.values() if a.get("credit")]
    lines += ["", "## Credits for the game description", ""] + (credits or ["none required"])
    return "\n".join(lines) + "\n"


def luaparse_check(files):
    node = shutil.which("node")
    lp = Path.home() / ".cache" / "rr-tools" / "node_modules" / "luaparse"
    if node and lp.is_dir():
        js = ("const lp=require(process.argv[1]);const fs=require('fs');let bad=0;"
              "for(const f of process.argv.slice(2)){try{lp.parse(fs.readFileSync(f,'utf8'),{luaVersion:'5.3'})}"
              "catch(e){bad++;console.log(f+': '+e.message)}}process.exit(bad?1:0)")
        r = subprocess.run([node, "-e", js, str(lp), *map(str, files)], capture_output=True, text=True)
        return r.returncode == 0, "luaparse", r.stdout.strip()
    bad = []
    for f in files:
        t = re.sub(r"--\[\[.*?\]\]|--[^\n]*|\"(\\.|[^\"\\])*\"|'(\\.|[^'\\])*'", "", Path(f).read_text(encoding="utf-8"), flags=re.S)
        opens = len(re.findall(r"\b(function|do|then|repeat)\b", t)) - len(re.findall(r"\belseif\b", t))
        closes = len(re.findall(r"\b(end|until)\b", t))
        if opens != closes or t.count("{") != t.count("}") or t.count("(") != t.count(")"):
            bad.append(f"{f}: block/bracket balance off")
    return not bad, "balance check (install luaparse: npm i --prefix ~/.cache/rr-tools luaparse)", "\n".join(bad)


def cmd_build(m, a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if validate(m, quiet=True) != 0:
        validate(m)
        print("build refused: validate fails")
        return 1
    rm = runtime_map(m)
    head = ("-- RR_SoundMap (GENERATED by rr-soundsmith build from soundmap.json + assets.json; do not edit, regenerate)\n"
            f"-- {rm['placeholders']} placeholder and {rm['unassigned']} unassigned sounds: placeholders never ship.\n")
    (out / "RR_SoundMap.lua").write_text(head + "return " + lua(rm) + "\n", encoding="utf-8")
    for f in ("RR_Sound.lua", "RR_SoundDemo.client.lua"):
        shutil.copy2(SKILL / "assets" / "luau" / f, out / f)
    (out / "studio_sound_setup.lua").write_text(setup_lua(m, rm), encoding="utf-8")
    (out / "SOUND_SPEC.md").write_text(spec_md(m, rm), encoding="utf-8")
    (out / "AUDIO_BRIEFS.md").write_text(briefs_text(m, list(m.sounds)), encoding="utf-8")
    (out / "LICENCES.md").write_text(licences_md(m), encoding="utf-8")
    (out / "README.md").write_text(README.format(date=TODAY, ph=rm["placeholders"], un=rm["unassigned"]), encoding="utf-8")
    lua_files = sorted(out.glob("*.lua"))
    ok, how, msg = luaparse_check(lua_files)
    print(f"{'PASS' if ok else 'FAIL'} syntax ({how}) on {len(lua_files)} Lua files" + (f"\n{msg}" if msg else ""))
    status = 0 if ok else 1
    if not a.no_check:
        if m.bible.ok():
            files = lua_files + sorted(out.glob("*.md"))
            bad = []
            for f in files:
                code, txt = m.bible.run("check", str(f))
                if code != 0:
                    bad.append(f"{f.name}:\n{txt.strip()[-1200:]}")
            print(f"{'PASS' if not bad else 'FAIL'} bible check on {len(files)} files")
            for x in bad:
                print(x)
            status = 1 if bad else status
        else:
            print("bible check skipped: rr-bible not found")
    print(f"build {'PASS' if status == 0 else 'FAIL'}: {out} ({rm['placeholders']} placeholders, {rm['unassigned']} "
          "unassigned). Handover: Studio listening test pending (owner).")
    return status


README = """# Risky Rails sound package (rr-soundsmith, {date})

Files
- `RR_SoundMap.lua` ModuleScript, GENERATED data (sounds, groups, ducking, events, voices). Regenerate, never edit.
- `RR_Sound.lua` ModuleScript, the client runtime. `RR_SoundDemo.client.lua` LocalScript listening test.
- `studio_sound_setup.lua` run once in the command bar: SoundService.RR_Mix SoundGroup tree. A group Volume you set
  there is kept as its base; player settings and ducking multiply on top.
- `SOUND_SPEC.md` event -> sound table by phase, ladder, ducking, voices, open decisions. `AUDIO_BRIEFS.md` sourcing
  briefs (summary table first). `LICENCES.md` register.

Wire it (client only)
1. ReplicatedStorage: RR_SoundMap, RR_Sound (and RR_Feel from rr-game-feel if you use it).
2. In one LocalScript: `local Sound = require(RS.RR_Sound); Sound.init(require(RS.RR_SoundMap), {{feel = Feel}})`.
3. Emitters: `Sound.setEmitter("lever", leverAttachment)` for each role in SOUND_SPEC (missing roles play 2D).
4. Game code: `Sound.event("trip_start")`, `Sound.event("ui_button_press")`, and `Sound.setSpeed(speed)` whenever Speed
   changes: each Heartbeat or on the train's replicated Speed value Changed, including the ~5 s departure ramp and the
   arrival braking (the wheels then fade to silence at the StopMarker). Calling it only on throttle notches makes the
   wheel loop jump between notches and never fade.
5. Lobby place: `Sound.event("lobby_enter")` on join, queue events from the queue pad script, `lobby_leave` before
   the teleport.
   Events marked `via feel` play when RR_Feel plays that event; do not call them twice.

Runtime choice: legacy Sound + SoundGroup (still supported; Roblox now recommends the Audio API, see
tech.audio.soundgroup_status). Chosen for SoundGroup nesting and scripted ducking that is tested in a Lua VM; a port to
AudioPlayer/AudioEmitter/AudioFader keeps RR_SoundMap unchanged.

State: {ph} placeholder and {un} unassigned sounds. Placeholders never ship (`sound.py validate --release`).
Studio listening test pending (owner): see rr-soundsmith references/fidelity.md.
"""


# ------------------------------------------------------------------ sheet and critic
def cmd_sheet(m, a):
    try:
        import sheet
    except ImportError as e:
        print(f"sheet needs numpy and Pillow ({e})")
        return 2
    return sheet.make(m, Path(a.src), Path(a.out), feel_presets(), find_sibling("multiuse-critic", "RR_CRITIC_SKILL"))


def merged_rubric(critic):
    base = (critic / "references" / "rubric.md").read_text(encoding="utf-8")
    if "## Profile S" in base:
        return base
    g = (SKILL / "references" / "rubric-sound.md").read_text(encoding="utf-8")
    prof = g[g.index("## Profile S"):].rstrip() + "\n\n"
    i = base.index("## Shared blocks")
    text = base[:i] + prof + base[i:]
    return re.sub(r"(<!--\s*include-with:\s*A6, B5[^>]*?)(\s*-->)", r"\1, S5\2", text)


def crit_brief(m, src=None, owner_away=False):
    b = m.bible
    v = lambda k, d="?": b.value(k, d) if b.ok() else d  # noqa: E731
    files = {}
    pv = Path(src) / "preview.json" if src else None
    if pv and pv.is_file():
        files = json.loads(pv.read_text(encoding="utf-8")).get("files", {})
    ph = sum(Path(f).name.startswith("PLACEHOLDER_") for f in files.values())
    st = [m.asset_state(s) for s in m.sounds]
    stage = (f"{len(files)} of {len(m.sounds)} sounds have a file in this pass ({ph} synthesised PLACEHOLDERs, "
             f"{len(files) - ph} owner files); register: {st.count('final')} final, {st.count('placeholder')} placeholder, "
             f"{st.count('unassigned')} unassigned. Sounds without a file are judged on the event and brief table.")
    oqs = "; ".join(f"{r_['id']} {r_['title']} (default {r_['default'][:80]})" for r_ in oq_rows(m)) or "none"
    step2 = ("step 2: pre-answered (canon via rr-bible; owner away; assumptions are the defaults above)" if owner_away else
             "step 2: ask the owner at most 3 questions the canon above leaves open (multiuse-critic step 2), then write "
             "the answers here")
    return "\n".join([
        "# Risky Rails sound plan (rr-soundsmith)",
        "- Purpose: the event -> sound plan and mix: each sound says what happened and how urgent, alarms reach the "
        "other carriage, the hierarchy holds on a phone, placeholders mark timing until final audio arrives.",
        f"- Audience: {v('identity.audience.launch')}; {v('identity.audience.devices')}.",
        "- Player view: you cannot hear anything. The images are waveforms, spectrograms, a loudness ladder, "
        "phone-speaker loss and event timelines against rr-game-feel's channels; Facts has the measurements and the "
        "event and brief table (phase, events, space, must say, sounds like, avoid). Judge the plan and the numbers, "
        "never 'how it sounds'; the owner's ears are the final check.",
        f"- Stage: {stage}",
        f"- Fixed constraints: {v('av.audio.priority')}; {v('av.audio.slapstick')}; {v('av.audio.speed_link')}; "
        f"tone {v('identity.tone.company')}; {v('identity.tone.not')}. Licences: {v('av.audio.licence')}.",
        f"- Owner worries / already decided: alarms first (canon). Open decisions, defaults in use: {oqs}. Placeholder "
        "timbre is not the brief: judge the plan, levels, timing and distinctness, and the brief text for style.",
        step2]) + "\n"


def cmd_crit(m, a):
    critic = find_sibling("multiuse-critic", "RR_CRITIC_SKILL")
    if not critic:
        print("multiuse-critic not found: set RR_CRITIC_SKILL")
        return 2
    src = Path(a.src)
    if not (src / "contact.png").is_file():
        print(f"{src}/contact.png missing: run sound.py sheet first")
        return 2
    C = Path(a.crit)
    pdir = C / f"pass-{a.pass_}"
    pdir.mkdir(parents=True, exist_ok=True)
    (C / "rubric.md").write_text(merged_rubric(critic), encoding="utf-8")
    for n in ("contact.png", "contact.json", "closeups.png", "closeups.json", "facts.md"):
        if (src / n).is_file():
            shutil.copy2(src / n, pdir / n)
    if not (C / "brief.md").is_file():
        (C / "brief.md").write_text(crit_brief(m, src, a.owner_away), encoding="utf-8")
        print(f"wrote {C / 'brief.md'} (edit the Owner worries line if the owner said more)")
    extra = " --images closeups.png" if (pdir / "closeups.png").is_file() else ""
    print(f"wrote {C / 'rubric.md'} (multiuse-critic rubric + Profile S) and pass-{a.pass_}/ files")
    print(f"critic skill: {critic} (use this path, not your own glob)")
    print(f"next: python3 {critic / 'scripts' / 'critic_kit.py'} build {C} --pass {a.pass_} --kind full --profile S "
          f"--role \"senior game audio designer\"{extra}")
    print("then spawn a fresh critic on the printed prompt (multiuse-critic step 5); never score it yourself")
    return 0


# ------------------------------------------------------------------ where, promote
def cmd_where(m, a):
    p, how = presets_source()
    n_assets = len([k for k in m.assets])
    print(f"presets: {p} ({how})\n  soundmap.json: {len(m.sounds)} sounds, {len(m.events)} events; assets.json: "
          f"{n_assets} registered; recipes.py: {'yes' if (p / 'recipes.py').is_file() else 'no'}")
    print(f"  project home: {home_dir()} ({'present' if (home_dir() / 'soundmap.json').is_file() else 'absent'})")
    if inside_skill(p):
        print("  read-only: register refuses to write into the skill folder; use a mission copy or `sound.py promote`")
    return 0


def cmd_promote(m, a):
    src = Path(a.src)
    src = src.parent if src.is_file() else src
    dst = Path(a.to) if a.to else home_dir()
    if not (src / "soundmap.json").is_file():
        print(f"{src}/soundmap.json not found")
        return 2
    if inside_skill(dst):
        print(f"promote refused: {dst} is inside the skill folder (a re-sync overwrites it)")
        return 2
    load = lambda p: json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}  # noqa: E731
    new_map, old_map = load(src / "soundmap.json"), load(dst / "soundmap.json")
    new_a, old_a = load(src / "assets.json"), load(dst / "assets.json")
    diff = lambda new, old: ([k for k in new if k not in old], [k for k in old if k not in new],  # noqa: E731
                             [k for k in new if k in old and new[k] != old[k]])
    add, rem, chg = diff(new_map.get("sounds", {}), old_map.get("sounds", {}))
    eadd, erem, _ = diff(new_map.get("events", {}), old_map.get("events", {}))
    merged = dict(old_a)
    merged.update({k: v for k, v in new_a.items() if k != "_about"})
    reg = [k for k in new_a if k != "_about" and old_a.get(k) != new_a[k]]
    kept = [k for k in old_a if k != "_about" and k not in new_a]
    if old_map:
        print(f"promote {src} -> {dst}\n  sounds: +{add or '-'} -{rem or '-'} changed {chg or '-'}\n  events: +{eadd or '-'} "
              f"-{erem or '-'}\n  registrations new or changed: {reg or '-'}; kept from the home: {kept or '-'}")
    else:
        print(f"promote {src} -> {dst} (new home): {len(new_map.get('sounds', {}))} sounds, "
              f"{len(new_map.get('events', {}))} events, {len(reg)} registrations")
    if a.dry_run:
        print("dry run: nothing written")
        return 0
    dst.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    for n in ("soundmap.json", "assets.json", "recipes.py"):
        if (dst / n).is_file():
            shutil.copy2(dst / n, dst / f"{n}.bak-{stamp}")
    shutil.copy2(src / "soundmap.json", dst / "soundmap.json")
    if merged:
        merged.setdefault("_about", "rr-soundsmith asset register, written by sound.py register; licence proof per sound")
        (dst / "assets.json").write_text(json.dumps(merged, indent=1) + "\n", encoding="utf-8")
    if (src / "recipes.py").is_file():
        shutil.copy2(src / "recipes.py", dst / "recipes.py")
    print(f"promoted (backups *.bak-{stamp}); every run without RR_SOUND_PRESETS now reads {dst}; run sound.py validate")
    return 0


# ------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("list"); p.add_argument("--group"); p.add_argument("--tier", type=int)
    p = sp.add_parser("show"); p.add_argument("name"); p.add_argument("--json", action="store_true")
    p = sp.add_parser("validate"); p.add_argument("--strict", action="store_true"); p.add_argument("--release", action="store_true")
    sp.add_parser("oq"); sp.add_parser("where")
    p = sp.add_parser("promote"); p.add_argument("--from", dest="src", required=True); p.add_argument("--to")
    p.add_argument("--dry-run", action="store_true")
    p = sp.add_parser("analyze"); p.add_argument("paths", nargs="+"); p.add_argument("--as", dest="as_")
    p.add_argument("--class", dest="cls", choices=["oneshot", "ui", "alarm", "impact", "loop", "music"])
    p.add_argument("--json", action="store_true"); p.add_argument("--fix-out"); p.add_argument("--mono", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    p = sp.add_parser("synth"); p.add_argument("ids", nargs="*"); p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=7)
    p = sp.add_parser("register"); p.add_argument("sid"); p.add_argument("--file", action="append", default=[])
    p.add_argument("--id", action="append", default=[]); p.add_argument("--source", required=True, choices=sorted(SOURCES))
    for k in ("origin", "licence", "proof", "credit", "creator"):
        p.add_argument(f"--{k}")
    p.add_argument("--community", action="store_true", help="the Creator Store asset was uploaded by a community member")
    p.add_argument("--dry-run", action="store_true")
    p = sp.add_parser("brief"); p.add_argument("ids", nargs="*"); p.add_argument("--out")
    p = sp.add_parser("sheet"); p.add_argument("--from", dest="src", required=True); p.add_argument("--out", required=True)
    p = sp.add_parser("crit"); p.add_argument("crit"); p.add_argument("--pass", dest="pass_", type=int, required=True)
    p.add_argument("--from", dest="src", required=True)
    p.add_argument("--owner-away", action="store_true", help="pre-answer multiuse-critic step 2 from canon defaults")
    p = sp.add_parser("build"); p.add_argument("--out", required=True); p.add_argument("--no-check", action="store_true")
    a = ap.parse_args(argv)
    m = Model()
    return {"list": cmd_list, "show": cmd_show, "analyze": cmd_analyze, "synth": cmd_synth, "register": cmd_register,
            "brief": cmd_brief, "sheet": cmd_sheet, "crit": cmd_crit, "build": cmd_build, "oq": cmd_oq,
            "where": cmd_where, "promote": cmd_promote,
            "validate": lambda m_, a_: validate(m_, a_.strict, a_.release)}[a.cmd](m, a)


if __name__ == "__main__":
    sys.exit(main())
