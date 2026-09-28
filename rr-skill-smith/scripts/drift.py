#!/usr/bin/env python3
"""rr-skill-smith drift: cross-skill contract drift across the JARVIS web.

Usage:
  drift.py [--root R] [--home H] [SKILL ...] [--kinds K,K] [--level ERROR|WARN|INFO] [--json] [--save]
           [--dir PATH]   (check a staged copy of one skill instead of the live folder)

Kinds (all by default):
  hex     colours restated from rr-bible (exact copy of a token), near-copies (drifted), superseded tokens
  numbers values contradicting a bible fact that carries a check: regex (crew max, stud size, FOV, ...)
  studs   "N studs" next to a canon concept (gauge, avatar, segment, poles, ...) that differs from rr-bible
  oq      OQ ids unknown to the bible, decided, cited for a different topic, OQ-TBD placeholders, hard-coded lists
  keys    cited canon keys (`gameplay.crew.max`) that do not exist in rr-bible
  refs    unknown skill names, broken paths into other skills (<critic>/scripts/x.py) or inside a skill
  flags   documented script calls (`bible add-question --dry-run`) whose subcommand or --flag the script lacks
Levels: ERROR = broken contract (fix before shipping); WARN = likely drift, look; INFO = counted only.
Exit 1 when any ERROR is reported. --save writes <home>/drift.json (health.py and evals.py read it).
rr-bible is the canon: its own files are only checked for refs and flags.
"""
import sys

sys.dont_write_bytecode = True
import argparse
import difflib
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smithlib as L  # noqa: E402

KINDS = ["hex", "numbers", "studs", "oq", "keys", "refs", "flags"]
LEVELS = {"ERROR": 0, "WARN": 1, "INFO": 2}
DOC_DIRS = ("references", "agents")
CODE_EXT = {".py", ".lua", ".luau", ".json", ".js", ".sh"}
FILE_EXT = ("py", "lua", "luau", "json", "md", "html", "png", "csv", "fbx", "txt", "js", "css", "rbxl", "rbxlx", "skill",
            "sh", "svg", "jpg", "gif", "mp4", "wav", "ogg", "blend", "obj", "yaml", "yml", "toml", "zip", "tmp")
SUBDIRS = "scripts|references|assets|agents|presets|kit|specs|families|canon|evals|templates|examples"
GENERIC_KEY_TOKENS = {"len", "h", "max", "min", "spacing", "piece", "clear", "m", "studs", "stud", "3p", "1p", "v", "ds",
                      "value", "size", "px"}
QUALIFIER = {"len": r"long|length", "h": r"tall|high|height", "spacing": r"every|apart|spacing|spaced",
             "clear": r"clear|within|keep", "max": r"max|clamp|up to|at most|range", "piece": r"piece|straight"}
NOT_SKILL_RR = {"rr-missions", "rr-tools", "rr-profile", "rr-releases"}


def is_doc(relp):
    return relp.name == "SKILL.md" or (relp.parts and relp.parts[0] in DOC_DIRS)


def line_at(text, pos):
    return text.count("\n", 0, pos) + 1


class Ctx:
    def __init__(self, root, skills):
        self.root, self.skills = root, skills
        self.mod, self.b = L.bible(root)
        self.findings = []
        self.aliases = {}
        self.scripts = {}  # basename -> [paths]
        for name, s in skills.items():
            for p in (Path(s["dir"]) / "scripts").glob("*.py") if (Path(s["dir"]) / "scripts").exists() else []:
                self.scripts.setdefault(p.name, []).append(p)
        for name, s in skills.items():
            t = L.read(Path(s["dir"]) / "SKILL.md")
            for al, script in re.findall(r"`(\w+)`(?: below)?\s*=\s*`python3 <\w+>/scripts/(\w+\.py)`", t):
                self.aliases.setdefault(name, {})[al] = self._script(name, script)
            for script, al in re.findall(r"`python3 <\w+>/scripts/(\w+\.py)`\s*\(below:?\s*`(\w+)`\)", t):
                self.aliases.setdefault(name, {})[al] = self._script(name, script)
        self.global_alias = {}
        for name, m in self.aliases.items():
            for al, p in m.items():
                if p:
                    self.global_alias.setdefault(al, p)
        self.placeholder = {}
        for name, s in skills.items():
            t = L.read(Path(s["dir"]) / "SKILL.md")
            for ph, rest in re.findall(r"`<(\w+)>`\s*=\s*([^;\n]{0,200})", t):
                rest = rest.split("`<")[0]
                if re.match(r"(this|the) (skill'?s )?folder", rest) and "multiuse" not in rest:
                    self.placeholder.setdefault(name, {})[ph] = name
                    continue
                m = re.search(r"(rr-[a-z-]+[a-z]|multiuse-critic|risky-rails-[a-z-]+[a-z])", rest)
                if m and m.group(1) in skills:
                    self.placeholder.setdefault(name, {})[ph] = m.group(1)
        self.default_ph = {"bible": "rr-bible", "critic": "multiuse-critic"}

    def _script(self, skill, script):
        p = Path(self.skills[skill]["dir"]) / "scripts" / script
        if p.exists():
            return p
        cands = self.scripts.get(script, [])
        return cands[0] if len(cands) == 1 else None

    def add(self, skill, relp, line, kind, level, msg, fix=""):
        self.findings.append({"skill": skill, "file": str(relp), "line": line, "kind": kind, "level": level,
                              "msg": msg, "fix": fix})


# ---------------------------------------------------------------- hex + numbers
def check_hex(c, skill, relp, text):
    if not c.b:
        return
    canon = c.b.canon_hexes()
    doc = is_doc(relp)
    seen, restated = {}, []
    for h, pos in c.mod.find_colours(text):
        seen.setdefault(h, pos)
    for h, pos in seen.items():
        if h in c.mod.NEUTRALS:
            continue
        ln = line_at(text, pos)
        lab = c.mod.lab(c.mod.hex_rgb(h))
        near_neutral = abs(lab[1]) < 5 and abs(lab[2]) < 5 and (lab[0] < 12 or lab[0] > 94)
        if h in canon:
            f = min(canon[h], key=lambda f: c.mod.STATUSES.index(f["status"]))
            if f["status"] == "superseded":
                c.add(skill, relp, ln, "hex", "ERROR", f"{h} is superseded token {f['key']}", "use the current token")
            elif f["status"] == "conflict":
                c.add(skill, relp, ln, "hex", "WARN", f"{h} = {f['key']} is undecided (conflict)", "use the OQ default")
            elif doc:
                restated.append((ln, h, f["key"]))
            else:
                c.add(skill, relp, ln, "hex", "INFO", f"{h} hard-coded copy of {f['key']}")
            continue
        best = min(canon, key=lambda x: c.mod.delta_e(h, x))
        de = c.mod.delta_e(h, best)
        k = canon[best][0]["key"]
        if de <= (2.5 if doc else 1.2) and not near_neutral:
            c.add(skill, relp, ln, "hex", "ERROR" if doc else "WARN",
                  f"{h} is a near-copy of {k} {best} (dE {de:.1f}): drifted?", f"use {k} from rr-bible")
        elif doc:
            c.add(skill, relp, ln, "hex", "WARN", f"{h} off-palette in instructions (nearest {k}, dE {de:.0f})",
                  "cite a token or record a proposed fact")
        else:
            c.add(skill, relp, ln, "hex", "INFO", f"{h} off-palette (nearest {k}, dE {de:.0f})")
    if restated:
        keys = ", ".join(f"{h}={k}" for _, h, k in restated[:4]) + (f" +{len(restated) - 4}" if len(restated) > 4 else "")
        c.add(skill, relp, restated[0][0], "hex", "WARN", f"{len(restated)} canon colour(s) restated in instructions: {keys}",
              "cite the keys (or a palette name) and read values with bible get/tokens")


def check_numbers(c, skill, relp, text):
    if not c.b:
        return
    for f in c.b.facts:
        if not f["check"]:
            continue
        try:
            cv = float(f["value"])
        except ValueError:
            continue
        for m in re.finditer(f["check"], text, re.I):
            got = next((g for g in m.groups() if g is not None), None)
            try:
                v = float(str(got).replace(",", ""))
            except ValueError:
                continue
            if abs(v - cv) > 1e-9:
                c.add(skill, relp, line_at(text, m.start()), "numbers", "WARN" if f["status"] == "conflict" else "ERROR",
                      f"'{m.group(0).strip()}' contradicts {f['key']} = {f['value']}", f"read {f['key']} from rr-bible")


def stud_concepts(c):
    if hasattr(c, "_studs"):
        return c._studs
    out = []
    for f in c.b.facts if c.b else []:
        if f["status"] == "superseded":
            continue
        try:
            v = float(f["value"])
        except ValueError:
            continue
        if not (f["key"].startswith("tech.units.") or "stud" in (f["note"] + f["key"]).lower()) or \
                re.search(r"_m(_|$)|_ds$", f["key"]):
            continue
        last = f["key"].split(".")[-1].split("_")
        prim = [t for t in last if t not in GENERIC_KEY_TOKENS and len(t) >= 3 and not t.isdigit()]
        qual = [QUALIFIER[t] for t in last if t in QUALIFIER]
        if prim:
            out.append((f, prim, qual, v))
    c._studs = out
    return out


def check_studs(c, skill, relp, text):
    for m in re.finditer(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(?:-\s*)?studs?\b(?!\s*/\s*s|\s*per\s*s)", text):
        v = float(m.group(1))
        pre = re.split(r"[;|\n()]|\.\s|,\s", text[max(0, m.start() - 60): m.start()])[-1]
        post = re.split(r"[;|\n()]|\.\s|,\s", text[m.end(): m.end() + 30])[0]
        win = (pre + m.group(0) + post).lower()
        pos0 = len(pre)
        best = None
        for f, prim, qual, cv in stud_concepts(c):
            hits = [x.start() for p in prim for x in re.finditer(r"\b" + re.escape(p), win)]
            if not hits or not all(re.search(r"\b" + re.escape(p), win) for p in prim):
                continue
            if qual and not any(re.search(q, win) for q in qual):
                continue
            dist = min(abs(h - pos0) for h in hits) - 5 * len(prim)
            if best is None or dist < best[0]:
                best = (dist, f, prim, cv)
        if best:
            _, f, prim, cv = best
            ln = line_at(text, m.start())
            if abs(v - cv) < 1e-9:
                if is_doc(relp):
                    c.add(skill, relp, ln, "studs", "WARN", f"'{m.group(0)}' restates {f['key']} = {f['value']}",
                          f"cite `{f['key']}` instead of the number")
            else:
                c.add(skill, relp, ln, "studs", "WARN", f"'{m.group(0)}' near '{' '.join(prim)}' but {f['key']} = "
                      f"{f['value']} ({f['status']})", f"read {f['key']}; or record a new fact if it is a different measure")


# ---------------------------------------------------------------- OQ ids
def oq_index(c):
    if hasattr(c, "_oq"):
        return c._oq
    opens, decided = {}, {}
    if c.b:
        for q in c.b.oqs:
            words = L.content_words(q["title"] + " " + " ".join(t for _, t in q["options"]) + " "
                                    + " ".join(q["fields"].values()).replace(".", " ").replace("_", " "))
            opens[q["id"]] = (q["title"], words)
        for d in c.b.decisions:
            for oq in re.findall(r"OQ-\d{3}", "\n".join(d["raw"])):
                decided.setdefault(oq, d["id"])
    c._oq = (opens, decided)
    return c._oq


def check_oq(c, skill, relp, text):
    opens, decided = oq_index(c)
    ids = list(re.finditer(r"\bOQ-(\d{3}|TBD[-\w]*)\b", text))
    for k, m in enumerate(ids):
        oq = m.group(0)
        ln = line_at(text, m.start())
        if oq.startswith("OQ-TBD"):
            c.add(skill, relp, ln, "oq", "WARN", f"{oq} placeholder not reconciled", "record it with bible add-question; cite the id it gets")
            continue
        if oq not in opens:
            if oq in decided:
                c.add(skill, relp, ln, "oq", "WARN", f"{oq} is decided ({decided[oq]})", f"use {decided[oq]} and its facts")
            else:
                c.add(skill, relp, ln, "oq", "ERROR", f"{oq} is not in rr-bible", "cite a real OQ or record the question")
            continue
        lstart, nl = text.rfind("\n", 0, m.start()) + 1, text.find("\n", m.end())
        crowded = sum(1 for x in ids if lstart <= x.start() <= (nl if nl > 0 else len(text))) >= 3
        lo = max(ids[k - 1].end() if (k and crowded) else 0, m.start() - 160, lstart)
        hi = min(ids[k + 1].start() if (k + 1 < len(ids) and crowded) else len(text), m.end() + 200,
                 nl if nl > 0 else len(text))
        ctx = text[lo:hi]
        cw = L.content_words(re.sub(r"OQ-\d{3}", " ", ctx))
        title, words = opens[oq]
        if len(cw) >= 3 and not (cw & words):
            c.add(skill, relp, ln, "oq", "WARN", f"{oq} cited for '{ctx.strip()[:70]}' but it is '{title[:60]}'",
                  "check the id (parallel lanes collided on OQ numbers)")
    if relp.suffix in CODE_EXT and len(ids) >= 4:
        lines = text.splitlines()
        for i in range(len(lines)):
            win = set(re.findall(r"OQ-\d{3}", "\n".join(lines[i:i + 8])))
            if len(win) >= 4:
                c.add(skill, relp, i + 1, "oq", "WARN", f"hard-coded OQ list ({len(win)} ids)",
                      "read `bible get questions --json` at run time")
                break


# ---------------------------------------------------------------- canon keys
def check_keys(c, skill, relp, text):
    if not c.b:
        return
    files = set(c.b.domain_files)
    if relp.suffix == ".md":
        cands = [(m.group(1), m.start()) for m in re.finditer(r"`([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)`", text)]
    else:
        cands = [(m.group(1), m.start()) for m in re.finditer(r"[\"']([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)[\"']", text)]
    keys = c.b.by_key
    sections = {(f, s) for f, secs in c.b.sections.items() for s, _ in secs}
    seen = set()
    for key, pos in cands:
        parts = key.split(".")
        if parts[0] not in files or parts[-1] in FILE_EXT or key in seen:
            continue
        seen.add(key)
        if key in keys:
            if keys[key]["status"] == "superseded":
                c.add(skill, relp, line_at(text, pos), "keys", "WARN", f"`{key}` is superseded", "cite the current key")
            continue
        if len(parts) == 2 and (parts[0], parts[1]) in sections:
            continue
        if any(k.startswith(key + ".") for k in keys):
            continue
        close = difflib.get_close_matches(key, keys.keys(), n=1, cutoff=0.75)
        c.add(skill, relp, line_at(text, pos), "keys", "ERROR" if is_doc(relp) or relp.suffix in CODE_EXT else "WARN",
              f"`{key}` is not in rr-bible" + (f" (closest `{close[0]}`)" if close else ""),
              "fix the key or add the fact with bible add-fact")


# ---------------------------------------------------------------- refs
def check_refs(c, skill, relp, text, skill_dir):
    names = set(c.skills)
    for m in re.finditer(r"(?<![\w./~-])(rr-[a-z0-9]+(?:-[a-z0-9]+)*)(?![\w-])", text):
        n = m.group(1)
        if n in names or n in NOT_SKILL_RR or n.endswith("-") or re.fullmatch(r"rr-\d+", n):
            continue
        after = text[m.end(): m.end() + 12]
        near = text[max(0, m.start() - 30): m.end() + 30].lower()
        typo = difflib.get_close_matches(n, [x for x in names if x.startswith("rr-")], n=1, cutoff=0.85)
        if re.match(r"/(" + SUBDIRS + r"|SKILL\.md)", after):
            c.add(skill, relp, line_at(text, m.start()), "refs", "ERROR", f"unknown skill '{n}' in a path",
                  "fix the name or build the skill")
        elif typo or re.search(r"\bskills?\b", near):
            c.add(skill, relp, line_at(text, m.start()), "refs", "WARN", f"unknown skill '{n}'"
                  + (f" (did you mean {typo[0]}?)" if typo else ""), "fix the name or build the skill")
    ph_map = dict(c.default_ph, **c.placeholder.get(skill, {}))
    for m in re.finditer(r"(?:<(\w+)>|(?<![\w-])(rr-[a-z0-9-]+[a-z0-9]|multiuse-critic|risky-rails-[a-z-]+[a-z]))/"
                         r"((?:" + SUBDIRS + r"|SKILL\.md)(?:/[\w.-]+)*)", text):
        target = ph_map.get(m.group(1)) if m.group(1) else m.group(2)
        path = m.group(3).rstrip(".,:;)")
        if not target or target not in c.skills or "*" in path:
            continue
        if not (Path(c.skills[target]["dir"]) / path).exists():
            c.add(skill, relp, line_at(text, m.start()), "refs", "ERROR", f"{target}/{path} does not exist",
                  "fix the path (renamed or removed file)")
    if relp.suffix == ".md":
        for m in re.finditer(r"(?<![\w/<>.$-])((?:" + SUBDIRS + r")/[\w.-]+(?:/[\w.-]+)*)", text):
            path = m.group(1).rstrip(".,:;)")
            if "." not in Path(path).name and not (skill_dir / path).exists():
                continue  # a bare folder word like assets/icons is checked only when it exists as a file path
            if (skill_dir / path).exists() or (skill_dir / relp.parent / path).exists():
                continue
            lstart = text.rfind("\n", 0, m.start()) + 1
            line_txt = text[lstart: text.find("\n", m.end()) if text.find("\n", m.end()) > 0 else len(text)]
            others = [n for n in re.findall(r"(rr-[a-z0-9-]+[a-z0-9]|multiuse-critic)", text[lstart:m.start()]) if n in c.skills]
            if others:
                if not (Path(c.skills[others[-1]]["dir"]) / path).exists() and not re.search(r"(?i)propos", line_txt):
                    c.add(skill, relp, line_at(text, m.start()), "refs", "WARN", f"{others[-1]}/{path} does not exist",
                          "fix the path")
                continue
            if re.search(r"(?i)propos|planned|future|would", line_txt):
                continue
            prev = text[max(0, m.start() - 40): m.start()]
            if re.search(r"(<\w+>|\$\w+|~|[\w-]+)/$", prev) or re.search(r"(mission|<M>|<R>|trial|out|export)\b[^`\n]{0,20}$", prev):
                continue
            c.add(skill, relp, line_at(text, m.start()), "refs", "ERROR", f"{path} does not exist in {skill}",
                  "fix the path or drop the reference")


# ---------------------------------------------------------------- script flags
def script_text(p):
    txt = L.read(p)
    for q in p.parent.glob("*.py"):
        if q != p:
            txt += "\n" + L.read(q)
    return txt


def check_flags(c, skill, relp, text, cache):
    if relp.suffix != ".md":
        return
    spans = re.findall(r"`([^`\n]{3,300})`", text)
    spans += [ln for blk in re.findall(r"```[a-z]*\n(.*?)```", text, re.S) for ln in blk.splitlines()]
    my_alias = c.aliases.get(skill, {})
    for span in spans:
        for part in re.split(r"\s*(?:&&|\|\||;|\|(?!\S*\|))\s*", span):
            toks = part.split()
            if not toks:
                continue
            script, rest = None, []
            for i, t in enumerate(toks):
                mm = re.search(r"(?:^|/)(\w+\.py)$", t)
                if mm:
                    script = c._script(skill, mm.group(1)) if mm.group(1) in [p.name for p in
                                                                             (Path(c.skills[skill]["dir"]) / "scripts").glob("*.py")] else \
                        (c.scripts.get(mm.group(1), [None])[0] if len(c.scripts.get(mm.group(1), [])) == 1 else None)
                    rest = toks[i + 1:]
                    break
            if not script and toks[0] in my_alias:
                script, rest = my_alias[toks[0]], toks[1:]
            elif not script and toks[0] in c.global_alias and toks[0] not in c.skills:
                script, rest = c.global_alias[toks[0]], toks[1:]
            if not script:
                continue
            key = str(script)
            if key not in cache:
                st = script_text(script)
                cache[key] = (st, bool(re.search(r"add_subparsers|add_parser\(", st)))
            st, has_sub = cache[key]
            if has_sub and rest and re.fullmatch(r"[a-z][a-z0-9-]{1,30}", rest[0]) and not re.search(
                    r"[\"']" + re.escape(rest[0]) + r"[\"']", st):
                c.add(skill, relp, line_at(text, text.find(span)), "flags", "WARN",
                      f"`{script.name} {rest[0]}`: no such subcommand in {L.rel(script, c.root)}",
                      "fix the call or the docs")
            for t in rest:
                fm = re.match(r"^(--[a-z][a-z0-9-]*)", t)
                if fm and not re.search(r"[\"']" + re.escape(fm.group(1)) + r"[\"'=]", st):
                    c.add(skill, relp, line_at(text, text.find(span)), "flags", "WARN",
                          f"`{script.name} ... {fm.group(1)}`: flag not defined in {L.rel(script, c.root)}",
                          "fix the call or add the flag")


# ---------------------------------------------------------------- driver
def run(root, skills, only=None, kinds=None, dirs=None):
    c = Ctx(root, skills)
    kinds = kinds or KINDS
    cache = {}
    for name, s in sorted(skills.items()):
        if only and name not in only:
            continue
        d = Path((dirs or {}).get(name) or s["dir"])
        for p in L.skill_files(d):
            relp = p.relative_to(d)
            if relp.parts[0] == "evals" or (name == "rr-skill-smith" and relp.parts[0] == "assets"):
                continue
            text = L.read(p)
            canon_skill = name == "rr-bible"
            notes = relp.name in ("design-notes.md", "CHANGELOG.md")
            before = len(c.findings)
            if not canon_skill and not notes:
                if "hex" in kinds:
                    check_hex(c, name, relp, text)
                if "numbers" in kinds:
                    check_numbers(c, name, relp, text)
                if "studs" in kinds:
                    check_studs(c, name, relp, text)
                if "oq" in kinds:
                    check_oq(c, name, relp, text)
                if "keys" in kinds:
                    check_keys(c, name, relp, text)
            if "refs" in kinds and not notes and not (canon_skill and relp.parts[0] == "canon"):
                check_refs(c, name, relp, text, d)
            if "flags" in kinds and not notes:
                check_flags(c, name, relp, text, cache)
            if notes:
                continue
            for f in c.findings[before:]:
                if relp.parts[0] in ("tests", "fixtures") or "corpus" in relp.parts or \
                        re.match(r"(selftest|luatest|test_)", relp.name):
                    f["level"] = "INFO"
    return c.findings


def summary(findings):
    out = {}
    for f in findings:
        s = out.setdefault(f["skill"], {"ERROR": 0, "WARN": 0, "INFO": 0, "kinds": {}})
        s[f["level"]] += 1
        k = s["kinds"].setdefault(f["kind"], {"ERROR": 0, "WARN": 0, "INFO": 0})
        k[f["level"]] += 1
    return out


def main(argv=None):
    ap = L.common_args(argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter))
    ap.add_argument("skills", nargs="*", help="skills to check (default: the whole web)")
    ap.add_argument("--kinds", help="comma list of " + ",".join(KINDS))
    ap.add_argument("--level", default="WARN", choices=list(LEVELS), help="lowest level to print (default WARN)")
    ap.add_argument("--dir", help="check this folder as the (single) named skill, e.g. a staged copy")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--save", action="store_true", help="write <home>/drift.json")
    ap.add_argument("--limit", type=int, default=60, help="max findings printed per skill (default 60)")
    a = ap.parse_args(argv)
    root = L.find_root(a.root)
    skills = L.web(root)
    kinds = [k.strip() for k in a.kinds.split(",")] if a.kinds else None
    if kinds and set(kinds) - set(KINDS):
        L.die(f"unknown kind(s): {set(kinds) - set(KINDS)}")
    for s in a.skills:
        if s not in skills:
            L.die(f"unknown skill {s}; known: {', '.join(sorted(skills))}")
    dirs = None
    if a.dir:
        if len(a.skills) != 1:
            L.die("--dir needs exactly one skill name")
        dirs = {a.skills[0]: a.dir}
    findings = run(root, skills, set(a.skills) or None, kinds, dirs)
    summ = summary(findings)
    if a.save:
        home = L.ensure_home(L.smith_home(root, a.home))
        L.save_json(home / "drift.json", {"checked": L.now(), "summary": summ, "findings": findings})
    shown = [f for f in findings if LEVELS[f["level"]] <= LEVELS[a.level]]
    if a.json:
        print(json.dumps({"summary": summ, "findings": shown}, indent=1, ensure_ascii=False))
    else:
        per = {}
        for f in sorted(shown, key=lambda f: (f["skill"], LEVELS[f["level"]], f["file"], f["line"])):
            per.setdefault(f["skill"], []).append(f)
        for sk, fs in per.items():
            print(f"== {sk}")
            for f in fs[: a.limit]:
                print(f"  {f['level']} {f['kind']} {f['file']}:{f['line']}: {f['msg']}")
            if len(fs) > a.limit:
                print(f"  ... {len(fs) - a.limit} more (--json or --limit)")
        rows = [[sk, v["ERROR"], v["WARN"], v["INFO"], ", ".join(f"{k} {x['ERROR']}/{x['WARN']}" for k, x in
                                                                 sorted(v["kinds"].items()) if x["ERROR"] or x["WARN"])]
                for sk, v in sorted(summ.items())]
        print(L.md_table(["skill", "ERROR", "WARN", "INFO", "kinds (E/W)"], rows))
    return 1 if any(f["level"] == "ERROR" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
