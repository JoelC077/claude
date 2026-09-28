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

    def open_questions(self):
        """Every open OQ as a get-OQ dict ({id, title, fields, options})."""
        if "__oqs" not in self._cache:
            ids = re.findall(r"^(OQ-\d+)\b", self.text("open-questions"), re.M)
            res = [self.get(q) for q in ids]
            self._cache["__oqs"] = [d for d in res if isinstance(d, dict)
                                    and (d.get("fields") or {}).get("status", "open") == "open"]
        return self._cache["__oqs"]

    def mission_src(self, slug):
        """Source ID that rr-bible's source list gives a mission folder (e.g. HUDM for 260927-ticket-hud), or ''."""
        f = self.dir / "canon" / "sources.md" if self.dir else None
        if not f or not f.is_file():
            return ""
        m = re.search(r"^- `([A-Z0-9_]+)`[^\n]*\bmission " + re.escape(slug) + r"\b", f.read_text(errors="replace"), re.M)
        return m.group(1) if m else ""

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
    """history_versions: released versions (any channel). channel_pre: 'alpha', 'beta' or '' (live).
    First release is 0.1.0 (OQ-037 default); the result always sorts above every released version."""
    vers = sorted((v for v in history_versions if parse_ver(v)), key=ver_key)
    tag = lambda c, n=1: c + (f"-{channel_pre}.{n}" if channel_pre else "")
    if level == "none":
        level = "patch"
    if not vers:
        return tag("0.1.0" if effective_level(level, "0.0.0") != "major" else "1.0.0")
    last = vers[-1]
    lives = [v for v in vers if not parse_ver(v)[3]]
    last_live = lives[-1] if lives else "0.0.0"
    lvl = effective_level(level, last_live)
    cand = None
    if parse_ver(last)[3]:
        pending = level_between(last_live, core(last))
        if LEVELS[lvl] <= LEVELS[pending]:
            c = core(last)
            if not channel_pre:
                cand = c
            else:
                nums = [int(parse_ver(v)[3].split(".")[1]) for v in vers if core(v) == c
                        and parse_ver(v)[3].split(".")[0] == channel_pre
                        and parse_ver(v)[3].split(".")[1:2] and parse_ver(v)[3].split(".")[1].isdigit()]
                cand = tag(c, max(nums or [0]) + 1)
        else:
            cand = tag(bump_core(last_live, lvl))
    else:
        cand = tag(bump_core(last, lvl))
    while ver_key(cand) <= ver_key(last):
        cand = tag(bump_core(core(cand), "patch"))
    return cand


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
    return (top / "releases") if top else (Path.home() / "rr-releases")


def missions_roots(extra=None):
    """Mission folders (rr-mission-control): configured ones, $RR_MISSIONS_ROOT, ~/.rr-missions and
    <git top>/.rr-missions (mission-control's own defaults); only when none of those holds a mission, the legacy
    <git top>/missions and /home/user/*/missions."""
    top = git_top()
    cands = [Path(x).expanduser() for x in (extra or [])]
    if os.environ.get("RR_MISSIONS_ROOT"):
        cands.append(Path(os.environ["RR_MISSIONS_ROOT"]).expanduser())
    cands += [Path.home() / ".rr-missions"] + ([top / ".rr-missions"] if top else [])

    def keep(cs):
        out = []
        for c in cs:
            c = c.resolve()
            if c.is_dir() and c not in out and any(c.glob("*/state.json")):
                out.append(c)
        return out
    out = keep(cands)
    if not out and not extra and not os.environ.get("RR_MISSIONS_ROOT"):
        out = keep(([top / "missions"] if top else []) + _walk_find("/home/user", "missions", depth=3))
    return out


def scratch_warning(root):
    """A releases root that will not survive the session (history and the rollback archive live there)."""
    s = str(Path(root).resolve())
    if s.startswith(("/tmp", "/var/tmp")) or "scratchpad" in s or "/claude-0/" in s:
        return (f"releases root {s} is a scratch/temp path: history.json and the rollback archive would be lost "
                "(set $RR_RELEASES_ROOT to a persistent folder the owner names)")
    return ""


def load_presets():
    return load_json(SKILL / "presets" / "gates.json", {})


def history(root):
    return load_json(Path(root) / "history.json", [])


def released_versions(root):
    """Every version ever used (never reuse one): published, recorded, rolled back, or seeded by the owner."""
    return [h["version"] for h in history(root) if h.get("status") in ("published", "rolled_back", "recorded", "seed")]


def _ordered(root, statuses):
    rows = [h for h in history(root) if h.get("status") in statuses and parse_ver(h.get("version"))]
    return sorted(rows, key=lambda h: ver_key(h["version"]))


def latest_release(root):
    """The newest release this train published (any outcome, seeds excluded): smoke and rollback act on it."""
    rows = _ordered(root, ("published", "recorded", "rolled_back"))
    return rows[-1] if rows else None


def live_release(root):
    """The release whose content is live now: the newest published one, or, when that was rolled back, the release
    it was rolled back to (with the rollback's new place version numbers). Seeds count when nothing newer exists.
    Collect, the script diff, G7 and ROLLBACK.md compare against this."""
    rows = _ordered(root, ("published", "recorded", "rolled_back", "seed"))
    if not rows:
        return None
    cur, nums = rows[-1], None
    seen = set()
    while cur.get("status") == "rolled_back" and cur["version"] not in seen:
        seen.add(cur["version"])
        rb = cur.get("rollback") or {}
        nums = rb.get("places") or {}
        nxt = next((h for h in rows if h["version"] == rb.get("to")), None)
        if not nxt:
            return None
        via, cur = cur["version"], nxt
    if nums is None:
        return cur
    live = dict(cur, via_rollback=via)
    live["places"] = {n: dict(p, version_number=nums.get(n, p.get("version_number")))
                      for n, p in (cur.get("places") or {}).items()}
    return live


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "where":
        b = Bible()
        print(f"skill: {SKILL}\nrr-bible: {b.dir or 'NOT FOUND'}\nreleases root: {releases_root()}")
        for n in ("multiuse-critic", "rr-mission-control", "rr-exploit-guard", "rr-soundsmith", "rr-vfx-lighting"):
            print(f"{n}: {find_sibling(n) or 'not found'}")
        print("missions:", ", ".join(map(str, missions_roots())) or "none found")
        w = scratch_warning(releases_root())
        if w:
            print("warning: " + w)
    else:
        print(__doc__)
