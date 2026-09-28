#!/usr/bin/env python3
"""rr-bible: the Risky Rails source of truth. Read slices, export tokens, check files, record canon.

Usage:
  bible.py [--canon DIR] <command> [args]

Read (token-cheap):
  list [FILE]                     domain files and their sections with fact counts
  get QUERY [--values] [--json]   one key, a key prefix (topic), a file stem, OQ-nnn or D-nnn
  search TEXT [--regex] [--limit N] [--json]
  stats [--json]                  counts of facts by file and status, questions, decisions

Use:
  tokens --format json|luau|css [--prefix P ...] [--canon-only] [--out FILE]
  check FILE [--near DE] [--allow HEX,..] [--skip hex,fonts,names,numbers] [--all-fonts] [--json]
                                  canon gate: exit 1 when the file contradicts canon

Write (the owner decides; skills record):
  add-fact KEY VALUE --src IDS [--note N] [--status S] [--check REGEX] [--replace] [--title T] [--dry-run]
  add-question TITLE --option "A: .." --option "B: .." --default "A (why)" --src IDS
               [--context C] [--affects k1,k2] [--blocks B] [--dry-run]
  decide OQ-nnn OPTION --by owner [--via WHERE] [--note N] [--date YYYY-MM-DD] [--dry-run]
  lint                            integrity check of the whole bible (run after every write)

Canon dir: --canon, else $RR_BIBLE_DIR, else ../canon next to this script.
Fact line grammar (one fact per line, in canon/<file>.md under "## <section> · Title"):
  - `file.section.name` = `value` | note | src: ID, ID | status [| check: REGEX]
Statuses: canon measured platform proposed assumed conflict superseded.
"""
import argparse
import datetime as _dt
import difflib
import html
import json
import math
import os
import re
import signal
import sys
from pathlib import Path

STATUSES = ["canon", "measured", "platform", "proposed", "assumed", "conflict", "superseded"]
FIRM = {"canon", "measured", "platform"}
META_FILES = {"sources", "decisions", "open-questions"}
FACT_RE = re.compile(
    r"^- `(?P<key>[a-z0-9_]+(?:\.[a-z0-9_]+)+)` = `(?P<value>[^`]*)`"
    r"(?: \| (?P<note>.*?))? \| src: (?P<src>[^|]+?) \| (?P<status>[a-z]+)"
    r"(?: \| check: (?P<check>.+?))?\s*$"
)
SECTION_RE = re.compile(r"^## (?P<id>[a-z0-9_]+) · (?P<title>.+?)\s*$")
SOURCE_RE = re.compile(r"^- `(?P<id>[A-Z][A-Z0-9]*)` — (?P<rest>.*)$")
OQ_HEAD_RE = re.compile(r"^### (?P<id>OQ-\d{3}) · (?P<title>.+?)\s*$")
D_HEAD_RE = re.compile(r"^### (?P<id>D-\d{3}) · (?P<date>\d{4}-\d{2}-\d{2}) · (?P<title>.+?)\s*$")
FIELD_RE = re.compile(r"^- (?P<k>[a-z_]+):\s?(?P<v>.*)$")
OPTION_RE = re.compile(r"^  - (?P<letter>[A-Z]): (?P<text>.+)$")
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
REF_RE = re.compile(r"\b(OQ-\d{3}|D-\d{3})\b")
NEUTRALS = {"#FFFFFF", "#000000"}
GENERIC_FONTS = {"serif", "sansserif", "monospace", "cursive", "fantasy", "systemui", "uisansserif",
                 "uiserif", "uimonospace", "applesystem", "blinkmacsystemfont", "inherit", "initial",
                 "unset", "emoji", "math"}


def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def canon_dir(arg):
    d = arg or os.environ.get("RR_BIBLE_DIR") or str(Path(__file__).resolve().parent.parent / "canon")
    p = Path(d).expanduser().resolve()
    if not (p / "sources.md").exists():
        die(f"canon not found at {p} (need sources.md); pass --canon or set RR_BIBLE_DIR")
    return p


def read(p):
    return Path(p).read_text(encoding="utf-8")


def write(p, text):
    Path(p).write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- parsing
class Bible:
    def __init__(self, root):
        self.root = root
        self.facts, self.sections, self.bad_lines = [], {}, []
        self.domain_files = sorted(p.stem for p in root.glob("*.md") if p.stem not in META_FILES)
        for stem in self.domain_files:
            sec = None
            self.sections[stem] = []
            for i, line in enumerate(read(root / f"{stem}.md").splitlines(), 1):
                m = SECTION_RE.match(line)
                if m:
                    sec = m.group("id")
                    self.sections[stem].append((sec, m.group("title")))
                    continue
                if line.startswith("- `"):
                    f = FACT_RE.match(line)
                    if not f:
                        self.bad_lines.append((stem, i, line))
                        continue
                    d = f.groupdict()
                    d.update(file=stem, line=i, section=sec, note=d["note"] or "", check=d["check"] or "")
                    self.facts.append(d)
        self.by_key = {}
        for f in self.facts:
            self.by_key.setdefault(f["key"], f)
        self.sources = {}
        for line in read(root / "sources.md").splitlines():
            m = SOURCE_RE.match(line)
            if m:
                self.sources[m.group("id")] = m.group("rest")
        self.oqs = parse_blocks(read(root / "open-questions.md"), OQ_HEAD_RE)
        self.decisions = parse_blocks(read(root / "decisions.md"), D_HEAD_RE)

    def canon_hexes(self):
        out = {}
        for f in self.facts:
            if HEX_RE.match(f["value"]):
                out.setdefault(f["value"].upper(), []).append(f)
        return out

    def fonts(self):
        out = {}
        for f in self.facts:
            if f["key"].startswith("style.type.") and re.fullmatch(r"[A-Za-z][A-Za-z0-9 ]{1,39}", f["value"]):
                out[norm_font(f["value"])] = f
        return out


def parse_blocks(text, head_re):
    blocks, cur = [], None
    for line in text.splitlines():
        m = head_re.match(line)
        if m:
            cur = dict(m.groupdict(), fields={}, options=[], raw=[line])
            blocks.append(cur)
            continue
        if line.startswith("### ") or line.startswith("# "):
            cur = None
            continue
        if cur is None:
            continue
        cur["raw"].append(line)
        o = OPTION_RE.match(line)
        if o:
            cur["options"].append((o.group("letter"), o.group("text")))
            continue
        fm = FIELD_RE.match(line)
        if fm:
            cur["fields"][fm.group("k")] = fm.group("v")
    for b in blocks:
        while b["raw"] and not b["raw"][-1].strip():
            b["raw"].pop()
    return blocks


def fact_line(f):
    note = f" | {f['note']}" if f.get("note") else ""
    check = f" | check: {f['check']}" if f.get("check") else ""
    return f"- `{f['key']}` = `{f['value']}`{note} | src: {f['src']} | {f['status']}{check}"


def compact(f, values_only=False):
    if values_only:
        return f"{f['key']} = {f['value']}"
    note = f" | {f['note']}" if f["note"] else ""
    return f"{f['key']} = {f['value']}{note} | {f['status']} [{f['src']}]"


def src_tokens(src):
    toks = []
    for part in src.split(","):
        part = part.strip()
        if part:
            toks.append(part.split()[0])
    return toks


# ---------------------------------------------------------------- colour maths
def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(r, g, b):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(v)))) for v in (r, g, b))


def lab(rgb):
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(a, b):
    return math.dist(lab(hex_rgb(a)), lab(hex_rgb(b)))


def hsl(h):
    r, g, b = (c / 255 for c in hex_rgb(h))
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        return 0.0, 0.0, l
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        hue = ((g - b) / d) % 6
    elif mx == g:
        hue = (b - r) / d + 2
    else:
        hue = (r - g) / d + 4
    return hue * 60, s, l


def look_warning(h):
    hue, s, l = hsl(h)
    if 20 <= hue <= 45 and 0.2 <= s <= 0.75 and 0.3 <= l <= 0.75:
        return "sepia/desert band (Dead Rails distance)"
    if 190 <= hue <= 215 and s >= 0.35 and l >= 0.6:
        return "blue-sky band (Land or Die distance)"
    return ""


# ---------------------------------------------------------------- font helpers
def norm_font(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def split_camel(s):
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)


# ---------------------------------------------------------------- commands
def cmd_list(b, a):
    if a.file:
        if a.file not in b.sections:
            die(f"no domain file '{a.file}'; files: {', '.join(b.domain_files)}", 1)
        for sec, title in b.sections[a.file]:
            keys = [f["key"] for f in b.facts if f["file"] == a.file and f["section"] == sec]
            print(f"{a.file}.{sec} ({len(keys)}) {title}")
            print("  " + " ".join(k.split(".", 2)[2] for k in keys))
        return 0
    print(f"canon: {b.root}")
    for stem in b.domain_files:
        parts = []
        for sec, _ in b.sections[stem]:
            n = sum(1 for f in b.facts if f["file"] == stem and f["section"] == sec)
            parts.append(f"{sec}({n})")
        print(f"{stem}: {' '.join(parts)}")
    print(f"open questions: {len(b.oqs)}  decisions: {len(b.decisions)}  sources: {len(b.sources)}")
    return 0


def block_text(block):
    return "\n".join(block["raw"])


def cmd_get(b, a):
    q = a.query.strip()
    if re.fullmatch(r"OQ-\d{3}", q) or re.fullmatch(r"D-\d{3}", q):
        pool = b.oqs if q.startswith("OQ") else b.decisions
        for blk in pool:
            if blk["id"] == q:
                if a.json:
                    print(json.dumps({"id": q, "title": blk["title"], "fields": blk["fields"],
                                      "options": blk["options"]}, ensure_ascii=False, indent=1))
                else:
                    print(block_text(blk))
                return 0
        if q.startswith("OQ"):
            for d in b.decisions:
                if d["fields"].get("from") == q:
                    print(f"{q} was decided: see {d['id']}\n" + block_text(d))
                    return 0
        die(f"{q} not found", 1)
    if q in ("OQ", "open-questions", "questions"):
        for blk in b.oqs:
            print(f"{blk['id']} · {blk['title']} | default: {blk['fields'].get('default', '?')}")
        return 0
    if q in ("D", "decisions"):
        for blk in b.decisions:
            print(f"{blk['id']} · {blk['date']} · {blk['title']}")
        return 0
    if q in ("palette", "palettes", "colours", "colors"):
        secs = {}
        for f in b.facts:
            if HEX_RE.match(f["value"]) and f["status"] != "superseded":
                sec = ".".join(f["key"].split(".")[:2])
                secs[sec] = secs.get(sec, 0) + 1
        print("colour sections (get one, e.g. bible.py get style.brand): "
              + ", ".join(f"{k} ({v})" for k, v in secs.items()))
        return 0
    if q in b.by_key:
        hits = [b.by_key[q]]
    elif q in b.sections:
        hits = [f for f in b.facts if f["file"] == q]
    elif "." not in q and any(f["section"] == q for f in b.facts):
        hits = [f for f in b.facts if f["section"] == q]  # bare section id, e.g. "fuel", "lever"
    else:
        hits = [f for f in b.facts if f["key"].startswith(q + ".")]
    if not hits:
        near = difflib.get_close_matches(q, list(b.by_key) + list(b.sections), n=5, cutoff=0.5)
        print(f"no key or topic '{q}'." + (f" close keys: {', '.join(near)}" if near else ""))
        words = q.replace(".", " ").replace("_", " ")
        pat = re.compile(re.escape(words), re.I)
        found = [f for f in b.facts if pat.search(f["key"].replace(".", " ").replace("_", " "))
                 or pat.search(f["value"]) or pat.search(f["note"])][:8]
        for f in found:
            print("  " + compact(f, a.values))
        if not found:
            print("no canon found. If it should exist, record the gap: bible.py add-question.")
        return 1
    if a.json:
        print(json.dumps([{k: f[k] for k in ("key", "value", "note", "src", "status")} for f in hits],
                         ensure_ascii=False, indent=1))
    else:
        for f in hits:
            print(compact(f, a.values))
    return 0


def cmd_search(b, a):
    flags = re.I
    pat = re.compile(a.text if a.regex else re.escape(a.text), flags)
    out = []
    for f in b.facts:
        if pat.search(f["key"]) or pat.search(f["value"]) or pat.search(f["note"]):
            out.append(("fact", compact(f), f))
    for blk in b.oqs + b.decisions:
        body = block_text(blk)
        if pat.search(body):
            out.append(("block", f"{blk['id']} · {blk['title']}", blk))
    if a.json:
        print(json.dumps([o[1] for o in out[:a.limit]], ensure_ascii=False, indent=1))
    else:
        for o in out[:a.limit]:
            print(o[1])
        if len(out) > a.limit:
            print(f"... {len(out) - a.limit} more (use --limit)")
    if not out:
        print(f"nothing matches '{a.text}'. If this is missing canon, record it with add-question.")
        return 1
    return 0


def cmd_stats(b, a):
    by_file = {s: sum(1 for f in b.facts if f["file"] == s) for s in b.domain_files}
    by_status = {s: sum(1 for f in b.facts if f["status"] == s) for s in STATUSES}
    data = {"facts": len(b.facts), "by_file": by_file, "by_status": by_status,
            "open_questions": len(b.oqs), "decisions": len(b.decisions), "sources": len(b.sources),
            "hex_tokens": sum(len(v) for v in b.canon_hexes().values())}
    if a.json:
        print(json.dumps(data, indent=1))
    else:
        print(f"facts {data['facts']} | open questions {data['open_questions']} | decisions {data['decisions']}"
              f" | sources {data['sources']} | colour tokens {data['hex_tokens']}")
        print("by file: " + ", ".join(f"{k} {v}" for k, v in by_file.items()))
        print("by status: " + ", ".join(f"{k} {v}" for k, v in by_status.items() if v))
    return 0


def token_facts(b, a):
    statuses = FIRM if a.canon_only else set(STATUSES) - {"superseded"}
    prefixes = a.prefix or ["style.", "ui."]
    cols = [f for f in b.facts if HEX_RE.match(f["value"]) and f["status"] in statuses
            and any(f["key"].startswith(p) for p in prefixes)]
    fonts = [f for f in b.fonts().values() if f["status"] in statuses]
    return cols, fonts


def luau_key(k):
    return k if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k) else f'["{k}"]'


def cmd_tokens(b, a):
    cols, fonts = token_facts(b, a)
    today = _dt.date.today().isoformat()
    if a.format == "json":
        text = json.dumps({
            "generated": today, "source": "rr-bible canon",
            "colors": {f["key"]: f["value"].upper() for f in cols},
            "fonts": {f["key"].split(".")[-1]: f["value"] for f in fonts},
            "status": {f["key"]: f["status"] for f in cols + fonts},
        }, ensure_ascii=False, indent=1)
    elif a.format == "css":
        lines = [f"/* rr-bible tokens {today}; generated, do not edit: change canon and regenerate */", ":root {"]
        for f in cols:
            flag = "" if f["status"] in FIRM else f" /* {f['status']} */"
            lines.append(f"  --rr-{f['key'].replace('.', '-').replace('_', '-')}: {f['value'].upper()};{flag}")
        for f in fonts:
            lines.append(f"  --rr-font-{f['key'].split('.')[-1].replace('_', '-')}: \"{f['value']}\";")
        lines.append("}")
        text = "\n".join(lines)
    else:
        tree = {}
        for f in cols:
            node = tree
            parts = f["key"].split(".")
            for p in parts[:-1]:
                node = node.setdefault(p, {})
            node[parts[-1]] = f
        lines = [f"-- rr-bible tokens {today}. Generated: change canon and rerun bible.py tokens --format luau.",
                 "local T = {}"]

        def emit(node, depth):
            pad = "\t" * depth
            for k, v in node.items():
                if isinstance(v, dict) and "key" not in v:
                    lines.append(f"{pad}{luau_key(k)} = {{")
                    emit(v, depth + 1)
                    lines.append(f"{pad}}},")
                else:
                    flag = "" if v["status"] in FIRM else f" -- {v['status']}"
                    lines.append(f'{pad}{luau_key(k)} = Color3.fromHex("{v["value"].upper().lstrip("#")}"),{flag}')
        for top, sub in tree.items():
            lines.append(f"T.{top} = {{")
            emit(sub, 1)
            lines.append("}")
        lines.append("T.fonts = {")
        for f in fonts:
            lines.append(f'\t{luau_key(f["key"].split(".")[-1])} = "{f["value"]}",')
        lines.append("}")
        lines.append("return T")
        text = "\n".join(lines)
    if a.out:
        write(a.out, text + "\n")
        print(f"wrote {len(cols)} colours + {len(fonts)} fonts to {a.out}")
    else:
        print(text)
    return 0


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def find_colours(text):
    found = []
    for m in re.finditer(r"(?<![&\w])#([0-9A-Fa-f]{8}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b", text):
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        found.append(("#" + h[:6].upper(), m.start()))
    for m in re.finditer(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})", text):
        found.append((rgb_hex(*map(int, m.groups())), m.start()))
    for m in re.finditer(r"Color3\.fromRGB\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)", text):
        found.append((rgb_hex(*map(int, m.groups())), m.start()))
    for m in re.finditer(r"(?i)\b\w*hex\(\s*[\"']([0-9A-Fa-f]{6})[\"']\s*\)", text):
        found.append(("#" + m.group(1).upper(), m.start()))  # Color3.fromHex("..") or a local hex("..") helper
    for m in re.finditer(r"Color3\.new\(\s*([01](?:\.\d+)?)\s*,\s*([01](?:\.\d+)?)\s*,\s*([01](?:\.\d+)?)\s*\)", text):
        found.append((rgb_hex(*(float(v) * 255 for v in m.groups())), m.start()))
    return found


def find_fonts(text, all_fonts):
    found = []
    for m in re.finditer(r"font-family\s*(?::\s*([^;}\n>]+)|=\s*\"([^\"]*)\"|=\s*'([^']*)')", text, re.I):
        val = next(g for g in m.groups() if g is not None)
        val = re.split(r"\"\s+[\w:-]+=|\"\s*/?>|\"\s*$", val)[0]  # stop at the end of a style="" attribute
        fams = [x.strip().strip("\"'").strip() for x in val.split(",")]
        fams = [x for x in fams if x and not re.search(r"[{}$%<>]", x) and norm_font(x) not in GENERIC_FONTS]
        for x in (fams if all_fonts else fams[:1]):
            found.append((x, m.start()))
    for m in re.finditer(r"fonts\.googleapis\.com/css2?\?([^\"'\s>]+)", text):
        for fam in re.findall(r"family=([A-Za-z0-9+]+)", m.group(1)):
            found.append((fam.replace("+", " "), m.start()))
    for m in re.finditer(r"Enum\.Font\.(\w+)", text):
        found.append((split_camel(m.group(1)), m.start()))
    for m in re.finditer(r"rbxasset://fonts/families/(\w+)\.json", text):
        found.append((split_camel(m.group(1)), m.start()))
    for m in re.finditer(r"@fontsource/([a-z0-9-]+)", text):
        found.append((m.group(1).replace("-", " ").title(), m.start()))
    return found


def cmd_check(b, a):
    path = Path(a.file)
    if not path.exists():
        die(f"no such file: {path}")
    text = read(path)
    skip = set(filter(None, (a.skip or "").split(",")))
    allow = {("#" + h.strip().lstrip("#")).upper() for h in (a.allow or "").split(",") if h.strip()}
    findings, ok = [], {"colours": 0, "fonts": 0}

    def add(level, kind, msg, pos, src=None):
        findings.append({"level": level, "kind": kind, "line": line_of(src or text, pos), "msg": msg})

    if "hex" not in skip:
        canon = b.canon_hexes()
        seen = {}
        for h, pos in find_colours(text):
            seen.setdefault(h, []).append(pos)
        for h, poses in seen.items():
            n = f" x{len(poses)}" if len(poses) > 1 else ""
            if h in allow or h in NEUTRALS:
                ok["colours"] += 1
                continue
            if h in canon:
                facts = canon[h]
                firmest = min(facts, key=lambda f: STATUSES.index(f["status"]))
                if firmest["status"] == "superseded":
                    add("WARN", "hex", f"{h}{n}: superseded token {firmest['key']} ({firmest['note'][:60]})", poses[0])
                elif firmest["status"] == "conflict":
                    add("WARN", "hex", f"{h}{n}: token {firmest['key']} is undecided; {refs_in(firmest)}", poses[0])
                else:
                    ok["colours"] += 1
                continue
            best = min(canon, key=lambda c: delta_e(h, c))
            de = delta_e(h, best)
            if de <= a.near:
                ok["colours"] += 1
                continue
            warn = look_warning(h)
            add("ERROR", "hex", f"{h}{n}: off-palette; nearest {canon[best][0]['key']} {best} (dE {de:.1f})"
                + (f"; {warn}" if warn else ""), poses[0])
    if "fonts" not in skip:
        fonts = b.fonts()
        seen = {}
        plain = html.unescape(text)
        for name, pos in find_fonts(plain, a.all_fonts):
            seen.setdefault(norm_font(name), (name, pos))
        for key, (name, pos) in seen.items():
            f = fonts.get(key)
            if not f:
                add("ERROR", "font", f"font '{name}' is not in canon (style.type.*)", pos, plain)
            elif f["status"] == "superseded":
                add("WARN", "font", f"font '{name}' is superseded ({f['key']})", pos, plain)
            else:
                ok["fonts"] += 1
    if "names" not in skip:
        for f in b.facts:
            if ".banned." not in f["key"]:
                continue
            for m in re.finditer(r"(?<!\w)" + re.escape(f["value"]) + r"(?!\w)", text, re.I):
                level = "WARN" if f["status"] == "conflict" else "ERROR"
                add(level, "name", f"'{m.group(0)}' is banned ({f['key']}): {f['note']}", m.start())
                break
    if "numbers" not in skip:
        for f in b.facts:
            if not f["check"]:
                continue
            try:
                canon_v = float(f["value"])
            except ValueError:
                continue
            for m in re.finditer(f["check"], text, re.I):
                got = next((g for g in m.groups() if g is not None), None)
                if got is None:
                    continue
                try:
                    v = float(got.replace(",", ""))
                except ValueError:
                    continue
                if abs(v - canon_v) > 1e-9:
                    level = "WARN" if f["status"] == "conflict" else "ERROR"
                    add(level, "number", f"'{m.group(0).strip()}' contradicts {f['key']} = {f['value']}", m.start())
    findings.sort(key=lambda x: (x["level"] != "ERROR", x["line"]))
    errors = sum(1 for x in findings if x["level"] == "ERROR")
    warns = len(findings) - errors
    if a.json:
        print(json.dumps({"file": str(path), "errors": errors, "warnings": warns, "ok": ok,
                          "findings": findings}, ensure_ascii=False, indent=1))
    else:
        for x in findings:
            print(f"{x['level']} {x['kind']} L{x['line']}: {x['msg']}")
        verdict = "FAIL" if errors else "PASS"
        print(f"check {verdict}: {path.name}: {errors} errors, {warns} warnings, "
              f"{ok['colours']} colours and {ok['fonts']} fonts on canon")
    return 1 if errors else 0


def refs_in(f):
    r = REF_RE.findall(f["note"])
    return "see " + ", ".join(r) if r else "see open-questions.md"


def check_srcs(b, src):
    bad = [t for t in src_tokens(src) if t not in b.sources and t != "owner"]
    return bad


def synced_warning(b):
    if "/skills/synced/" in str(b.root):
        print(f"note: writing to a synced skill copy ({b.root}); also land the change in the repo copy", file=sys.stderr)


def cmd_add_fact(b, a):
    key = a.key.strip()
    if not re.fullmatch(r"[a-z0-9_]+(?:\.[a-z0-9_]+){2,}", key):
        die("key must be file.section.name (lowercase, digits, underscores), e.g. gameplay.fuel.shovel_pct")
    stem, sec = key.split(".")[:2]
    if stem not in b.domain_files:
        die(f"no domain file '{stem}'; files: {', '.join(b.domain_files)}")
    if a.status not in STATUSES:
        die(f"status must be one of {', '.join(STATUSES)}")
    for s, name in ((a.value, "value"), (a.note or "", "note")):
        if "`" in s or " | " in s or "\n" in s:
            die(f"{name} may not contain backticks, ' | ' or newlines")
    bad = check_srcs(b, a.src)
    if bad:
        die(f"unknown source id(s): {', '.join(bad)}; add them to canon/sources.md or use 'owner YYYY-MM-DD'")
    if a.check:
        try:
            if re.compile(a.check).groups < 1:
                die("check regex needs a capture group for the number")
        except re.error as e:
            die(f"bad check regex: {e}")
    new = {"key": key, "value": a.value, "note": a.note or "", "src": a.src.strip(), "status": a.status,
           "check": a.check or ""}
    line = fact_line(new)
    path = b.root / f"{stem}.md"
    lines = read(path).splitlines()
    old = b.by_key.get(key)
    if old and not a.replace:
        print("exists: " + compact(old))
        die("key exists; pass --replace to overwrite it", 1)
    if old:
        lines[old["line"] - 1] = line
        action = "replaced"
    else:
        idx = None
        for i, ln in enumerate(lines):
            m = SECTION_RE.match(ln)
            if m and m.group("id") == sec:
                idx = i
                j = i + 1
                while j < len(lines) and not lines[j].startswith("## "):
                    if lines[j].startswith("- `"):
                        idx = j
                    j += 1
                break
        if idx is None:
            while lines and not lines[-1].strip():
                lines.pop()
            lines += ["", f"## {sec} · {a.title or sec.replace('_', ' ').capitalize()}", line]
        else:
            lines.insert(idx + 1, line)
        action = "added"
    if a.dry_run:
        print(f"(dry run) would have {action}: {line}")
        return 0
    synced_warning(b)
    write(path, "\n".join(lines) + "\n")
    print(f"{action} in {stem}.md: {line}")
    return 0


def next_id(b, prefix):
    nums = [int(x["id"].split("-")[1]) for x in (b.oqs if prefix == "OQ" else b.decisions)]
    if prefix == "OQ":
        nums += [int(d["fields"]["from"].split("-")[1]) for d in b.decisions
                 if re.fullmatch(r"OQ-\d{3}", d["fields"].get("from", ""))]
    return f"{prefix}-{(max(nums) if nums else 0) + 1:03d}"


def cmd_add_question(b, a):
    if len(a.option) < 2:
        die("give at least two --option values")
    bad = check_srcs(b, a.src)
    if bad:
        die(f"unknown source id(s): {', '.join(bad)}")
    opts = []
    for i, o in enumerate(a.option):
        m = re.match(r"^([A-Z]):\s*(.+)$", o.strip())
        opts.append((m.group(1), m.group(2)) if m else (chr(65 + i), o.strip()))
    letters = [l for l, _ in opts]
    if len(set(letters)) != len(letters):
        die("option letters must be unique")
    if a.default.strip()[:1] not in letters:
        die(f"--default must start with an option letter ({', '.join(letters)})")
    for k in filter(None, (a.affects or "").split(",")):
        if k.strip() not in b.by_key:
            die(f"--affects key not in canon: {k.strip()}")
    oid = next_id(b, "OQ")
    today = _dt.date.today().isoformat()
    block = [f"### {oid} · {a.title.strip()}", "- status: open", f"- raised: {today}", f"- src: {a.src.strip()}"]
    if a.context:
        block.append(f"- context: {a.context.strip()}")
    block.append("- options:")
    block += [f"  - {l}: {t}" for l, t in opts]
    block.append(f"- default: {a.default.strip()}")
    if a.affects:
        block.append(f"- affects: {', '.join(k.strip() for k in a.affects.split(','))}")
    block.append(f"- blocks: {a.blocks.strip() if a.blocks else 'none'}")
    text = "\n".join(block)
    if a.dry_run:
        print(f"(dry run: {oid} is provisional; parallel writers may take it first. Cite a placeholder such as "
              "OQ-TBD-<slug> until it is recorded, then cite the number the real run prints)\n" + text)
        return 0
    synced_warning(b)
    p = b.root / "open-questions.md"
    write(p, read(p).rstrip("\n") + "\n\n" + text + "\n")
    print(f"added {oid}\n{text}")
    return 0


def cmd_decide(b, a):
    q = a.question.upper()
    blk = next((x for x in b.oqs if x["id"] == q), None)
    if not blk:
        done = next((d for d in b.decisions if d["fields"].get("from") == q), None)
        die(f"{q} is already decided ({done['id']})" if done else f"{q} not found in open-questions.md", 1)
    letter = a.option.strip().upper()[:1]
    opt = dict(blk["options"]).get(letter)
    if not opt:
        die(f"{q} has no option {letter}; options: {', '.join(l for l, _ in blk['options'])}", 1)
    if a.by.strip().lower() != "owner":
        die("only the owner decides (--by owner). Until he does, proceed on the question's default "
            "and mark the output 'assumed (" + q + " default)'.", 1)
    date = a.date or _dt.date.today().isoformat()
    did = next_id(b, "D")
    by_line = "owner" + (f" ({a.via.strip()})" if a.via else "")
    src = f"owner {date}"
    osrc = blk["fields"].get("src", "")
    title = blk["title"].rstrip("?").strip()
    decision = f"{letter}: {opt}" + (f" Note: {a.note.strip()}" if a.note else "")
    block = [f"### {did} · {date} · {title}", f"- decision: {decision}", f"- by: {by_line}",
             f"- src: {src}" + (f", {osrc}" if osrc else ""), f"- from: {q}"]
    if blk["fields"].get("affects"):
        block.append(f"- affects: {blk['fields']['affects']}")
    text = "\n".join(block)
    affected = [k.strip() for k in blk["fields"].get("affects", "").split(",") if k.strip()]
    linked = sorted({f["key"] for f in b.facts if q in f["note"]} | set(affected))
    if a.dry_run:
        print("(dry run)\n" + text)
        return 0
    synced_warning(b)
    oq_path = b.root / "open-questions.md"
    lines = read(oq_path).splitlines()
    start = lines.index(blk["raw"][0])
    end = start + 1
    while end < len(lines) and not lines[end].startswith("### "):
        end += 1
    del lines[start:end]
    write(oq_path, "\n".join(lines).rstrip("\n") + "\n")
    d_path = b.root / "decisions.md"
    write(d_path, read(d_path).rstrip("\n") + "\n\n" + text + "\n")
    print(f"decided {q} -> {did}\n{text}")
    if linked:
        print("now update these facts to match (add-fact KEY VALUE --src 'owner " + date + "' --status canon --replace):")
        for k in linked:
            f = b.by_key.get(k)
            print("  " + (compact(f) if f else k))
    return 0


def cmd_lint(b, a):
    problems = []
    for stem, i, line in b.bad_lines:
        problems.append(f"{stem}.md:{i}: malformed fact line: {line[:90]}")
    seen = {}
    oq_ids = {x["id"] for x in b.oqs} | {d["fields"].get("from") for d in b.decisions}
    d_ids = {d["id"] for d in b.decisions}
    for f in b.facts:
        loc = f"{f['file']}.md:{f['line']}"
        if f["key"] in seen:
            problems.append(f"{loc}: duplicate key {f['key']} (first at line {seen[f['key']]})")
        seen.setdefault(f["key"], f["line"])
        parts = f["key"].split(".")
        if parts[0] != f["file"]:
            problems.append(f"{loc}: key {f['key']} is in {f['file']}.md")
        if f["section"] is None or parts[1] != f["section"]:
            problems.append(f"{loc}: key {f['key']} is under section '{f['section']}'")
        if f["status"] not in STATUSES:
            problems.append(f"{loc}: bad status '{f['status']}'")
        for t in check_srcs(b, f["src"]):
            problems.append(f"{loc}: unknown source '{t}'")
        for r in REF_RE.findall(f["note"]):
            if r not in oq_ids and r not in d_ids:
                problems.append(f"{loc}: reference {r} not found")
        if f["status"] == "conflict" and not REF_RE.search(f["note"]):
            problems.append(f"{loc}: conflict fact without an OQ reference")
        if f["check"]:
            try:
                if re.compile(f["check"]).groups < 1:
                    problems.append(f"{loc}: check regex has no capture group")
            except re.error as e:
                problems.append(f"{loc}: bad check regex ({e})")
    for x in b.oqs:
        for need in ("status", "raised", "src", "default"):
            if need not in x["fields"]:
                problems.append(f"{x['id']}: missing '{need}'")
        if len(x["options"]) < 2:
            problems.append(f"{x['id']}: needs at least two options")
        if x["fields"].get("default", "")[:1] not in dict(x["options"]):
            problems.append(f"{x['id']}: default does not start with an option letter")
        for t in check_srcs(b, x["fields"].get("src", "")):
            problems.append(f"{x['id']}: unknown source '{t}'")
        for k in filter(None, (s.strip() for s in x["fields"].get("affects", "").split(","))):
            if k not in b.by_key:
                problems.append(f"{x['id']}: affects unknown key {k}")
    ids = [x["id"] for x in b.oqs]
    if len(ids) != len(set(ids)):
        problems.append("duplicate OQ ids")
    dids = [d["id"] for d in b.decisions]
    if len(dids) != len(set(dids)):
        problems.append("duplicate decision ids")
    for d in b.decisions:
        for need in ("decision", "by", "src"):
            if need not in d["fields"]:
                problems.append(f"{d['id']}: missing '{need}'")
    for p in problems:
        print(p)
    if problems:
        print(f"lint FAIL: {len(problems)} problems")
        return 1
    print(f"lint OK: {len(b.facts)} facts, {len(b.oqs)} open questions, {len(b.decisions)} decisions, "
          f"{len(b.sources)} sources")
    return 0


def main(argv=None):
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped into head
    ap = argparse.ArgumentParser(prog="bible.py", description=__doc__,
                                 epilog="Run 'bible.py COMMAND --help' for command options.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--canon", help="canon directory (default: $RR_BIBLE_DIR or ../canon)")
    sp = ap.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    p = sp.add_parser("list", help="files, sections and fact counts")
    p.add_argument("file", nargs="?", help="a domain file stem, e.g. style")
    p = sp.add_parser("get", help="print one key, a topic prefix, a file, OQ-nnn or D-nnn")
    p.add_argument("query")
    p.add_argument("--values", action="store_true", help="key = value only (cheapest)")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("search", help="find facts, questions and decisions by text")
    p.add_argument("text")
    p.add_argument("--regex", action="store_true")
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("stats", help="counts")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("tokens", help="export colour and font tokens")
    p.add_argument("--format", choices=["json", "luau", "css"], default="json")
    p.add_argument("--prefix", action="append", help="key prefix to include (repeatable; default style. and ui.)")
    p.add_argument("--canon-only", action="store_true", help="only canon/measured/platform tokens")
    p.add_argument("--out", help="write to this file instead of stdout")
    p = sp.add_parser("check", help="canon gate for a file (html, css, lua, md, svg, py...)")
    p.add_argument("file")
    p.add_argument("--near", type=float, default=2.0, help="accept colours within this CIE76 dE of a token (default 2)")
    p.add_argument("--allow", help="comma-separated extra hexes allowed in this file")
    p.add_argument("--skip", help="comma-separated: hex,fonts,names,numbers")
    p.add_argument("--all-fonts", action="store_true", help="check fallback families too, not only the first")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("add-fact", help="add or replace one fact")
    p.add_argument("key")
    p.add_argument("value")
    p.add_argument("--src", required=True, help="source ids, comma-separated, or 'owner YYYY-MM-DD'")
    p.add_argument("--note")
    p.add_argument("--status", default="proposed", help=f"one of {', '.join(STATUSES)} (default proposed)")
    p.add_argument("--check", help="regex with one capture group; check flags files whose number differs")
    p.add_argument("--replace", action="store_true")
    p.add_argument("--title", help="section title if the section is new")
    p.add_argument("--dry-run", action="store_true")
    p = sp.add_parser("add-question", help="record missing or undecided canon as an open question")
    p.add_argument("title")
    p.add_argument("--option", action="append", default=[], help='"A: text" (repeat, at least two)')
    p.add_argument("--default", required=True, help='recommended default, starting with its letter: "A (why)"')
    p.add_argument("--src", required=True)
    p.add_argument("--context")
    p.add_argument("--affects", help="comma-separated fact keys this question governs")
    p.add_argument("--blocks")
    p.add_argument("--dry-run", action="store_true")
    p = sp.add_parser("decide", help="move an open question to decisions (owner's call)")
    p.add_argument("question", help="OQ-nnn")
    p.add_argument("option", help="option letter")
    p.add_argument("--by", required=True, help="must be 'owner': only the owner decides")
    p.add_argument("--via", help="where the owner said it, e.g. 'chat 2026-09-28' or 'artifact comment'")
    p.add_argument("--note")
    p.add_argument("--date")
    p.add_argument("--dry-run", action="store_true")
    sp.add_parser("lint", help="integrity check")

    a = ap.parse_args(argv)
    b = Bible(canon_dir(a.canon))
    cmd = {"list": cmd_list, "get": cmd_get, "search": cmd_search, "stats": cmd_stats, "tokens": cmd_tokens,
           "check": cmd_check, "add-fact": cmd_add_fact, "add-question": cmd_add_question,
           "decide": cmd_decide, "lint": cmd_lint}[a.cmd]
    return cmd(b, a)


if __name__ == "__main__":
    sys.exit(main())
