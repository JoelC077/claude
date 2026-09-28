#!/usr/bin/env python3
"""Shared helpers for rr-data-and-money: sibling lookup, rr-bible canon, canon-referenced presets, IO, numbers.

Not a CLI: `python3 rrlib.py --help` prints this text. Stdlib only.
Canon refs in presets:  {"v": 40, "canon": "economy.supplies.coal"}  -> number must appear in that canon VALUE
                        {"v": 10, "canon": "k", "in": "note"}         -> ... or in its note (caps stated there)
                        {"v": 0.6, "assumed": "why"}                   -> no canon; listed in every report
A path that is canon in the skill's preset but 'assumed' in a mission copy is reported as an override of canon.
Presets: rrlib.preset(name) = --flag, $ENV, <data root>/presets/NAME (mission copy), else the skill's preset.
"""
import copy, json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PRESETS = SKILL / "presets"
NUM_RE = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?%?")
CMP_RE = re.compile(r"(>=|<=|≥|≤|<|>)\s*(-?\d[\d,]*(?:\.\d+)?)\s*(%?)")


def project_root(start=None):
    """The git repo holding the current directory (the owner's project), else None."""
    cur = Path(start or os.getcwd()).resolve()
    for d in [cur, *cur.parents]:
        if (d / ".git").exists():
            return d
    return None


def data_root():
    """$RR_DATA_ROOT, else <project>/.rr-data when a git project is open (survives a fresh cloud machine once
    committed), else ~/.rr-data. Never a session scratchpad: a new session must find plans, history and memos."""
    if os.environ.get("RR_DATA_ROOT"):
        return Path(os.environ["RR_DATA_ROOT"]).expanduser()
    proj = project_root()
    return proj / ".rr-data" if proj and proj != Path.home() else Path.home() / ".rr-data"


def preset(name, given=None, env=None):
    """Preset to use: --flag, else $ENV, else <R>/presets/NAME (a mission's own copy), else the skill's preset.
    Missions copy presets to <R>/presets/ and edit them there; the skill's own presets stay the canon baseline."""
    if given:
        return Path(given)
    if env and os.environ.get(env):
        return Path(os.environ[env])
    own = data_root() / "presets" / name
    return own if own.is_file() else PRESETS / name


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
        self._files, self._ids = {}, {}

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

    def get_id(self, oid):
        """OQ-nnn / D-nnn block as text (None when missing)."""
        if oid not in self._ids:
            code, out = self.run("get", oid)
            self._ids[oid] = out.strip() if code == 0 else None
        return self._ids[oid]


WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
         "ten": 10, "once": 1, "twice": 2}
RANGE_PCT = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*[-–]\s*\d[\d,]*(?:\.\d+)?%")


def numbers_in(text):
    """All numbers in a canon string; '10%' yields 10 and 0.10, '30-60%' also 0.30, '2,500' 2500, 'two' 2."""
    text = text or ""
    out = []
    for m in NUM_RE.findall(text):
        pct = m.endswith("%")
        x = float(m.rstrip("%").replace(",", ""))
        out.append(x)
        if pct:
            out.append(x / 100)
    out += [float(m.replace(",", "")) / 100 for m in RANGE_PCT.findall(text)]
    out += [float(v) for w, v in WORDS.items() if re.search(rf"\b{w}\b", text, re.I)]
    return out


def comparisons(text):
    """[(op, number, is_pct)] in reading order: '>= 10% soft; >= 13%' -> [('>=', .10, True), ('>=', .13, True)]."""
    res = []
    for op, n, is_pct in CMP_RE.findall(text or ""):
        x = float(n.replace(",", ""))
        res.append(({"≥": ">=", "≤": "<="}.get(op, op), x / 100 if is_pct else x, bool(is_pct)))
    return res


def close(a, b, rel=1e-6):
    return abs(a - b) <= rel * max(1.0, abs(a), abs(b))


def canon_paths(node, where="", field="canon"):
    """{path: canon key} for every {v, canon} node (paths as Refs prints them); field="in" gives {path: "note"}."""
    out = {}
    if isinstance(node, dict) and "v" in node and "canon" in node:
        if field in node:
            out[where] = node[field]
    elif isinstance(node, dict):
        for k, v in node.items():
            if not k.startswith("_"):
                out.update(canon_paths(v, f"{where}.{k}" if where else k, field))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.update(canon_paths(v, f"{where}[{_tag(v, i)}]", field))
    return out


def base_refs(preset_file):
    """(canon keys, 'in' flags) of the skill's own preset: the reference for mission copies."""
    raw = load_json(preset_file)
    return canon_paths(raw), canon_paths(raw, field="in")


def _tag(v, i):
    """List items with an id/sku are addressed by it (products[toolbelt]) so reordering cannot hide a change."""
    return v.get("id") or v.get("sku") or i if isinstance(v, dict) else i


class Refs:
    """Resolve {"v", "canon"|"assumed"} nodes in a preset; collect canon problems and the assumed list.
    base = {path: canon key} of the skill's own preset: a path that was canon there and is 'assumed' here is an
    override of canon and is reported (self.overrides + a warning), never silent."""

    def __init__(self, bible=None, base=None, base_in=None):
        self.bible = bible or Bible()
        self.base = base or {}
        self.base_in = base_in or {}  # where the skill's preset says a number lives ("note"); copies inherit it
        self.errors, self.warnings, self.assumed, self.canon, self.overrides = [], [], [], [], []

    def is_ref(self, node):
        return isinstance(node, dict) and "v" in node and ("canon" in node or "assumed" in node)

    def resolve(self, node, where=""):
        if self.is_ref(node):
            self._check(node, where)
            return node["v"]
        if isinstance(node, dict):
            return {k: self.resolve(v, f"{where}.{k}" if where else k) for k, v in node.items() if not k.startswith("_")}
        if isinstance(node, list):
            return [self.resolve(v, f"{where}[{_tag(v, i)}]") for i, v in enumerate(node)]
        return node

    def _check(self, node, where):
        if "assumed" in node:
            self.assumed.append((where, node["v"], node["assumed"]))
            key = self.base.get(where)
            if key:
                f = self.bible.fact(key) if self.bible.ok() else None
                cv = f.get("value") if f else "?"
                self.overrides.append((where, node["v"], key, cv))
                self.warnings.append(f"{where} = {node['v']} overrides canon {key} = \"{cv}\" (labelled assumed)")
            return
        key = node["canon"]
        if not self.bible.ok():
            self.warnings.append(f"{where}: rr-bible not found, {key} unchecked")
            return
        f = self.bible.fact(key)
        if not f:
            self.errors.append(f"{where}: canon key {key} not in rr-bible")
            return
        self.canon.append((where, node["v"], key, f.get("status", "?")))
        st = f.get("status")
        if st == "superseded":
            self.errors.append(f"{where}: {key} is superseded in canon")
        elif st == "conflict":
            self.warnings.append(f"{where}: {key} is a canon conflict; label output 'assumed (OQ default)'")
        vals = node["v"] if isinstance(node["v"], list) else [node["v"]]
        # numbers must come from the canon value itself; "in": "note" opts into the note (e.g. a cap stated there).
        # Matching the whole text let placeholders in a note ("10 R$ placeholder") pass for a coin price.
        where_in = node.get("in") or self.base_in.get(where)
        text = f.get("note") or "" if where_in == "note" else f.get("value", "")
        have = numbers_in(text)
        for v in vals:
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            if not any(close(v, h) for h in have):
                self.errors.append(f"{where}: {v} not found in canon {key} {'note' if where_in == 'note' else 'value'}"
                                   f" = \"{text}\"")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=1, sort_keys=False) + "\n", encoding="utf-8")


class PathError(ValueError):
    pass


def _has(cur, p):
    try:
        _step(cur, p, "")
        return True
    except PathError:
        return False


def _step(cur, p, dotted):
    if isinstance(cur, list):
        if p.isdigit() and int(p) < len(cur):
            return int(p)
        ids = [_tag(x, i) for i, x in enumerate(cur)]
        if p in ids:
            return ids.index(p)
        raise PathError(f"--set/--sweep path {dotted}: no list item '{p}' (have {ids})")
    if isinstance(cur, dict) and p in cur:
        return p
    keys = sorted(k for k in cur if not str(k).startswith("_")) if isinstance(cur, dict) else []
    raise PathError(f"--set/--sweep path {dotted}: no key '{p}'" + (f" (have {', '.join(keys)})" if keys else ""))


def set_path(obj, dotted, value, template=None):
    """--set a.b.0.c=value on a nested dict/list (list items also by id: unlocks.loco_2.price); value parsed as
    JSON when possible. Every key must already exist, or exist in `template` (the skill's preset: an older copy
    may lack a newer key); a typo raises PathError instead of adding an unused key.
    A canon ref keeps its node and becomes {v, assumed: override ...}."""
    parts = dotted.split(".")
    cur, tpl = obj, template
    for i, p in enumerate(parts):
        try:
            k = _step(cur, p, dotted)
        except PathError:
            if not (isinstance(cur, dict) and isinstance(tpl, dict) and p in tpl):
                raise
            cur[p], k = copy.deepcopy(tpl[p]), p
        if i == len(parts) - 1:
            break
        tpl = tpl[_step(tpl, p, dotted)] if isinstance(tpl, (dict, list)) and _has(tpl, p) else None
        cur = cur[k]
    try:
        val = json.loads(value)
    except ValueError:
        val = value
    tgt = cur[k]
    if isinstance(tgt, dict) and "v" in tgt and not isinstance(val, dict):
        new = dict(tgt, v=val)
        new.pop("canon", None)
        new["assumed"] = f"override --set {dotted}={value}"
        val = new
    cur[k] = val


def pct(x, d=1):
    return "n/a" if x is None else f"{x * 100:.{d}f}%"


def fmt_num(x, d=0):
    if x is None:
        return "n/a"
    if abs(x) >= 1e6:
        return f"{x / 1e6:.1f}M"
    if abs(x) >= 1e4:
        return f"{x / 1e3:.1f}K"
    return f"{x:,.{d}f}"


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


if __name__ == "__main__":
    print(__doc__)
