#!/usr/bin/env python3
"""Shared helpers for rr-data-and-money: sibling lookup, rr-bible canon, canon-referenced presets, IO, numbers.

Not a CLI: `python3 rrlib.py --help` prints this text. Stdlib only.
Canon refs in presets:  {"v": 40, "canon": "economy.supplies.coal"}  -> value checked against rr-bible text
                        {"v": 0.6, "assumed": "why"}                   -> no canon; listed in every report
"""
import json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PRESETS = SKILL / "presets"
NUM_RE = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?%?")
CMP_RE = re.compile(r"(>=|<=|≥|≤|<|>)\s*(-?\d[\d,]*(?:\.\d+)?)\s*(%?)")


def data_root():
    """$RR_DATA_ROOT, else ~/.rr-data (never a session scratchpad: a new session must find it)."""
    return Path(os.environ.get("RR_DATA_ROOT", Path.home() / ".rr-data")).expanduser()


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


class Refs:
    """Resolve {"v", "canon"|"assumed"} nodes in a preset; collect canon problems and the assumed list."""

    def __init__(self, bible=None):
        self.bible = bible or Bible()
        self.errors, self.warnings, self.assumed, self.canon = [], [], [], []

    def is_ref(self, node):
        return isinstance(node, dict) and "v" in node and ("canon" in node or "assumed" in node)

    def resolve(self, node, where=""):
        if self.is_ref(node):
            self._check(node, where)
            return node["v"]
        if isinstance(node, dict):
            return {k: self.resolve(v, f"{where}.{k}" if where else k) for k, v in node.items() if not k.startswith("_")}
        if isinstance(node, list):
            return [self.resolve(v, f"{where}[{i}]") for i, v in enumerate(node)]
        return node

    def _check(self, node, where):
        if "assumed" in node:
            self.assumed.append((where, node["v"], node["assumed"]))
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
        have = numbers_in(f.get("value", "") + " | " + (f.get("note") or ""))
        for v in vals:
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            if not any(close(v, h) for h in have):
                self.errors.append(f"{where}: {v} not found in canon {key} = \"{f.get('value')}\"")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=1, sort_keys=False) + "\n", encoding="utf-8")


def set_path(obj, dotted, value):
    """--set a.b.0.c=value on a nested dict/list; value parsed as JSON when possible. Canon refs keep their tag."""
    parts = dotted.split(".")
    cur = obj
    for p in parts[:-1]:
        cur = cur[int(p)] if isinstance(cur, list) else cur[p]
    last = parts[-1]
    try:
        val = json.loads(value)
    except ValueError:
        val = value
    tgt = cur[int(last)] if isinstance(cur, list) else cur.get(last)
    if isinstance(tgt, dict) and "v" in tgt and not isinstance(val, dict):
        new = dict(tgt, v=val)
        new.pop("canon", None)
        new["assumed"] = f"override --set {dotted}={value}"
        val = new
    if isinstance(cur, list):
        cur[int(last)] = val
    else:
        cur[last] = val


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
