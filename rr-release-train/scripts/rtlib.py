#!/usr/bin/env python3
"""rtlib.py - shared helpers for rr-release-train (paths, canon client, semver, state files).

Library module; `python3 rtlib.py --help` prints this. `python3 rtlib.py where` prints the resolved sibling skills
and releases root (useful when a run cannot find rr-bible or the releases).
"""
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$")
LEVELS = {"none": 0, "patch": 1, "minor": 2, "major": 3}


def die(msg, code=2):
    print(msg)
    sys.exit(code)


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def today():
    return dt.date.today().isoformat()


def load_json(p, default=None):
    p = Path(p)
    if not p.is_file():
        return default
    return json.loads(p.read_text())


def save_json(p, data):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    os.replace(tmp, p)


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_tree(d):
    h = hashlib.sha256()
    for f in sorted(Path(d).rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts and not f.name.startswith("."):
            h.update(str(f.relative_to(d)).encode() + b"\0" + sha256_file(f).encode())
    return h.hexdigest()


def sha256_text(s):
    return hashlib.sha256(s.encode()).hexdigest()


# ---------------------------------------------------------------- siblings
def _walk_find(root, name, depth=5):
    root = Path(root).expanduser()
    out = []
    if not root.is_dir():
        return out
    base = len(root.parts)
    for dirpath, dirnames, _ in os.walk(root):
        p = Path(dirpath)
        if len(p.parts) - base >= depth:
            dirnames[:] = []
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("node_modules", "__pycache__")]
        if p.name == name:
            out.append(p)
    return out


def find_sibling(name, env=None):
    """Env var, then a sibling folder of this skill, then ~/.claude/skills and /home/user (depth 5)."""
    if env and os.environ.get(env):
        p = Path(os.environ[env]).expanduser()
        return p if (p / "SKILL.md").is_file() else None
    cands = [SKILL.parent / name] + _walk_find(Path.home() / ".claude" / "skills", name) + _walk_find("/home/user", name)
    return next((c for c in cands if (c / "SKILL.md").is_file()), None)


class Bible:
    """Canon through rr-bible's CLI (its stable interface), cached per query."""

    def __init__(self):
        self.dir = find_sibling("rr-bible", "RR_BIBLE_SKILL")
        self.script = self.dir / "scripts" / "bible.py" if self.dir else None
        self._cache = {}

    @property
    def ok(self):
        return bool(self.script and self.script.is_file())

    def run(self, *args):
        if not self.ok:
            return 2, "rr-bible not found: set RR_BIBLE_SKILL to its folder"
        r = subprocess.run([sys.executable, str(self.script), *args], capture_output=True, text=True)
        return r.returncode, (r.stdout + r.stderr).strip()

    def get(self, query):
        """List of fact dicts ({key, value, note, src, status}) or one OQ/D dict; None on a miss."""
        if query in self._cache:
            return self._cache[query]
        code, out = self.run("get", query, "--json")
        val = None
        if code == 0:
            try:
                val = json.loads(out)
            except json.JSONDecodeError:
                val = None
        self._cache[query] = val
        return val

    def value(self, key, default=None):
        v = self.get(key)
        if isinstance(v, list):
            for f in v:
                if f.get("key") == key:
                    return f.get("value", default)
        return default

    def facts(self, prefix):
        v = self.get(prefix)
        return v if isinstance(v, list) else []

    def text(self, query):
        code, out = self.run("get", query)
        return out if code == 0 else ""

    def decisions(self):
        """[(id, date, title)] from `get decisions`."""
        out = []
        for line in self.text("decisions").splitlines():
            m = re.match(r"^(D-\d+)\s+·\s+(\d{4}-\d{2}-\d{2})\s+·\s+(.+)$", line.strip())
            if m:
                out.append(m.groups())
        return out

    def questions_about(self, words=("release", "launch", "publish")):
        """Open questions whose text mentions any word, as get-OQ dicts."""
        ids = set()
        for w in words:
            code, out = self.run("search", w, "--limit", "300")
            ids |= set(re.findall(r"\b(OQ-\d+)\b", out if code == 0 else ""))
        res = []
        for q in sorted(ids):
            d = self.get(q)
            if isinstance(d, dict) and d.get("fields", {}).get("status", "open") == "open":
                res.append(d)
        return res

    def check(self, path, skip=None):
        """(exit code, findings list) of `bible check FILE --json`."""
        args = ["check", str(path), "--json"] + (["--skip", skip] if skip else [])
        code, out = self.run(*args)
        try:
            data = json.loads(out[out.index("{"):]) if "{" in out else {}
        except json.JSONDecodeError:
            data = {}
        return code, data.get("findings", []), out


# ---------------------------------------------------------------- semver
def parse_ver(v):
    m = SEMVER.match(v or "")
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4) or ""


def _pre_key(pre):
    if not pre:
        return (1,)
    out = []
    for part in pre.split("."):
        out.append((0, int(part), "") if part.isdigit() else (1, 0, part))
    return (0, tuple(out))


def ver_key(v):
    p = parse_ver(v)
    if not p:
        raise ValueError(f"not a semver: {v}")
    return p[0], p[1], p[2], _pre_key(p[3])


def core(v):
    p = parse_ver(v)
    return f"{p[0]}.{p[1]}.{p[2]}"


def bump_core(v, level):
    ma, mi, pa, _ = parse_ver(v)
    if level == "major":
        return f"{ma + 1}.0.0"
    if level == "minor":
        return f"{ma}.{mi + 1}.0"
    if level == "patch":
        return f"{ma}.{mi}.{pa + 1}"
    return f"{ma}.{mi}.{pa}"


def level_between(a, b):
    """Bump level that takes core a to core b."""
    pa, pb = parse_ver(a), parse_ver(b)
    if pb[0] > pa[0]:
        return "major"
    if pb[1] > pa[1]:
        return "minor"
    if pb[2] > pa[2]:
        return "patch"
    return "none"


def effective_level(level, base):
    """0.x rule: a breaking change bumps minor while major is 0 (1.0.0 is set explicitly)."""
    if level == "major" and parse_ver(base)[0] == 0:
        return "minor"
    return level


def next_version(history_versions, level, channel_pre):
    """history_versions: released versions (any channel). channel_pre: 'alpha', 'beta' or '' (live)."""
    vers = sorted((v for v in history_versions if parse_ver(v)), key=ver_key)
    if level == "none":
        level = "patch"
    if not vers:
        base_live = "0.0.0"
        new_core = bump_core(base_live, effective_level(level, base_live))
        if new_core == "0.0.1" and level != "patch":
            new_core = "0.1.0"
        return new_core + (f"-{channel_pre}.1" if channel_pre else "")
    last = vers[-1]
    lives = [v for v in vers if not parse_ver(v)[3]]
    last_live = lives[-1] if lives else "0.0.0"
    lvl = effective_level(level, last_live)
    last_pre = parse_ver(last)[3]
    if last_pre:
        pending = level_between(last_live, core(last))
        if LEVELS[lvl] <= LEVELS[pending]:
            c = core(last)
            if not channel_pre:
                return c
            tag = last_pre.split(".")[0]
            if tag == channel_pre:
                nums = [int(x) for x in last_pre.split(".")[1:] if x.isdigit()]
                return f"{c}-{channel_pre}.{(nums[0] if nums else 0) + 1}"
            same = [v for v in vers if core(v) == c and parse_ver(v)[3].split(".")[0] == channel_pre]
            n = max([int(parse_ver(v)[3].split(".")[1]) for v in same if parse_ver(v)[3].split(".")[1:2] and
                     parse_ver(v)[3].split(".")[1].isdigit()] or [0]) + 1
            return f"{c}-{channel_pre}.{n}"
        new_core = bump_core(last_live, lvl)
    else:
        new_core = bump_core(last, lvl)
    return new_core + (f"-{channel_pre}.1" if channel_pre else "")


# ---------------------------------------------------------------- roots and state
def git_top(path="."):
    try:
        r = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        return Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    except OSError:
        return None


def releases_root(arg=None):
    if arg:
        return Path(arg).expanduser().resolve()
    if os.environ.get("RR_RELEASES_ROOT"):
        return Path(os.environ["RR_RELEASES_ROOT"]).expanduser().resolve()
    top = git_top()
    return (top / ".rr-releases") if top else (Path.home() / ".rr-releases")


def history(root):
    return load_json(Path(root) / "history.json", [])


def released_versions(root):
    return [h["version"] for h in history(root) if h.get("status") in ("published", "rolled_back", "recorded")]


def last_release(root):
    rows = [h for h in history(root) if h.get("status") in ("published", "recorded", "rolled_back")]
    rows.sort(key=lambda h: ver_key(h["version"]))
    return rows[-1] if rows else None


def luaparse_check(path):
    """luaparse (npm, Lua 5.1 grammar) if installed under ~/.cache/rr-tools, else a block-balance check."""
    lp = Path.home() / ".cache" / "rr-tools" / "node_modules" / "luaparse"
    node = shutil.which("node")
    if lp.is_dir() and node:
        js = ("const lp=require(process.argv[1]);const fs=require('fs');"
              "try{lp.parse(fs.readFileSync(process.argv[2],'utf8'),{luaVersion:'5.1'});console.log('ok')}"
              "catch(e){console.log('ERR '+e.message);process.exit(1)}")
        r = subprocess.run([node, "-e", js, str(lp), str(path)], capture_output=True, text=True)
        return r.returncode == 0, "luaparse: " + (r.stdout.strip() or r.stderr.strip()[-200:])
    src = re.sub(r"--\[\[.*?\]\]|--[^\n]*|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", "", Path(path).read_text(), flags=re.S)
    opens = len(re.findall(r"\b(function|do|then)\b", src)) - len(re.findall(r"\belseif\b", src))
    opens -= len(re.findall(r"\bwhile\b[^\n]*\bdo\b|\bfor\b[^\n]*\bdo\b", src))
    ends = len(re.findall(r"\bend\b", src))
    return opens == ends, f"balance check (install luaparse for a real parse): {opens} openers vs {ends} ends"


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "where":
        b = Bible()
        print(f"skill: {SKILL}\nrr-bible: {b.dir or 'NOT FOUND'}\nreleases root: {releases_root()}")
        for n in ("multiuse-critic", "rr-mission-control", "rr-exploit-guard"):
            print(f"{n}: {find_sibling(n) or 'not found'}")
    else:
        print(__doc__)
