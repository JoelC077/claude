#!/usr/bin/env python3
"""rr-mission-control intake: split a raw owner prompt into tagged lines, then
check that every non-noise line is covered by the mission's requirement table.

  intake.py split  MISSION_DIR (--file prompt.raw | --text "...") [--clarify-file c.raw | --clarify "..."]...
  intake.py cover  MISSION_DIR [--final]
  intake.py show   MISSION_DIR

split  writes MISSION_DIR/prompt.txt (verbatim) and MISSION_DIR/lines.md:
       one line per clause:  L3 [quality-bar,process] run through the critic ...
       Clarifications become C1, C2 ... and are tagged `clarify` as well.
cover  reads MISSION_DIR/mission.md. Every non-noise L/C id must be cited in the
       R-table's "source" column (e.g. `L3` or `L3,C1`; no ranges). Prose mentions do not count.
       Every R-row needs a done-when. --final also requires every R status to be
       final (done|verified|fallback|waived|blocked|superseded|noise).
Exit code 0 = OK, 1 = orphans/gaps (listed), 2 = usage/missing files.
Stdlib only.
"""
import argparse, os, re, sys

NOISE = [r"^(hi|hey|hello)\b[^.]*$", r"\bthank(s| you)\b", r"\bhave fun\b", r"^cheers\b",
         r"^please\.?$", r"^(ok|okay)\.?$"]
TAGS = [  # (tag, regex) - guesses only; the orchestrator writes the real R-table
    ("reference", r"https?://|\bthis\b|\bprototype\b|\bblueprint\b|\bartifact\b|\bdesign\b.*created|\bcan'?t find\b|\bcant find\b"),
    ("deliverable", r"\bmake\b|\bbuild\b|\bremake\b|\bcreate\b|\bbuildings?\b|\bhud\b|\bui\b|\bmodel\b|\bnotification system\b|\bscreen\b|\bmenu\b|\b(hall|depot|station|building|tower|house|shed|platform|bridge|prop)s?\b"),
    ("quality-bar", r"\b\d{1,2}\s*/\s*10\b|\bscore\b|\brating\b"),
    ("process", r"\bcritic\b|\brun (through|until)\b|\bloop\b|\breview\b"),
    ("tool", r"\bblender\b|\bstudio\b|\bclaude design\b|\bfigma\b"),
    ("comms", r"\bprogress\b|\bupdates?\b|\bwatch\b|\breal ?time\b|\blive\b|\bsteps?\b"),
    ("export", r"\bexport\b|\bready for roblox\b|\bfbx\b|\brbxm"),
    ("editability", r"\bseparate\b|\bedit\b|\brecolou?r|\bparts?\b"),
    ("style", r"\bstyle\b|\bi like\b|\blooks? like\b|\blook and feel\b|\bfitting\b|\btheme\b"),
    ("context", r"\bworking on\b|\bi am\b|\bi'm\b|\bit will be\b"),
]
FINAL = {"done", "verified", "fallback", "waived", "blocked", "superseded", "noise"}


def split_clauses(text):
    urls = []
    def keep(m):
        urls.append(m.group(0)); return f"\x00{len(urls)-1}\x00"
    t = re.sub(r"https?://\S+", keep, text)
    t = re.sub(r"\s*(\.{2,}|\u2026)\s*", " ", t)  # "1,2... up to 10"
    parts = re.split(r"(?<=[.!?])\s+|\n+|;\s*|,\s+and (?:then )?", t)
    out = []
    for p in parts:
        p = re.sub(r"\x00(\d+)\x00", lambda m: urls[int(m.group(1))], p).strip(" \t,")
        if p and re.search(r"\w", p):
            out.append(p)
    return out


def tag(clause):
    low = clause.lower()
    stripped = re.sub(r"https?://\S+", "", low).strip()
    if any(re.search(n, stripped) for n in NOISE) and len(stripped.split()) <= 6:
        return ["noise"]
    tags = [t for t, rx in TAGS if re.search(rx, low)]
    return tags or ["untagged"]


def cmd_split(a):
    if a.text is None and a.file is None:
        sys.exit("split: give --text or --file")
    text = a.text if a.text is not None else open(a.file, encoding="utf-8").read()
    clar = list(a.clarify or []) + [open(f, encoding="utf-8").read() for f in (a.clarify_file or [])]
    a.clarify = clar
    if not split_clauses(text):
        print("empty prompt: nothing to split"); sys.exit(2)
    os.makedirs(a.mission, exist_ok=True)
    with open(os.path.join(a.mission, "prompt.txt"), "w", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")
        for i, c in enumerate(a.clarify or [], 1):
            f.write(f"\n--- clarification C{i} ---\n{c.rstrip()}\n")
    rows = [(f"L{i}", tag(c), c) for i, c in enumerate(split_clauses(text), 1)]
    n = 0
    for c in a.clarify or []:
        for cl in split_clauses(c):
            n += 1
            rows.append((f"C{n}", ["clarify"] + [t for t in tag(cl) if t != "untagged"], cl))
    with open(os.path.join(a.mission, "lines.md"), "w", encoding="utf-8") as f:
        f.write("# Prompt lines (cite these ids in the mission.md R-table source column)\n")
        for lid, tags, c in rows:
            f.write(f"{lid} [{','.join(tags)}] {c}\n")
    noise = sum(1 for r in rows if r[1] == ["noise"])
    untagged = [r[0] for r in rows if r[1] == ["untagged"]]
    print(f"-- {len(rows)} lines, {noise} noise, {len(rows)-noise} to cover -> {a.mission}/lines.md"
          + (f"; untagged: {','.join(untagged)}" if untagged else ""))


def read_lines(mission):
    p = os.path.join(mission, "lines.md")
    if not os.path.exists(p):
        sys.exit(f"missing {p}: run split first")
    rows = []
    for ln in open(p, encoding="utf-8"):
        m = re.match(r"^([LC]\d+) \[([^\]]*)\] (.*)$", ln.rstrip("\n"))
        if m:
            rows.append((m.group(1), m.group(2).split(","), m.group(3)))
    return rows


def r_rows(md):
    """R-table rows: markdown table lines whose first cell is R<n> or R*<n>."""
    rows = []
    for ln in md.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if ln.strip().startswith("|") and cells and re.fullmatch(r"R\*?\d+", cells[0]):
            rows.append(cells)
    return rows


def cmd_cover(a):
    mp = os.path.join(a.mission, "mission.md")
    if not os.path.exists(mp):
        print(f"missing {mp}"); sys.exit(2)
    md = open(mp, encoding="utf-8").read()
    lines = read_lines(a.mission)
    rows = r_rows(md)
    hdr = None
    for ln in md.splitlines():
        cells = [c.strip().lower() for c in ln.strip().strip("|").split("|")]
        if ln.strip().startswith("|") and cells and cells[0] == "id" and "status" in cells:
            hdr = cells; break
    problems = []
    live = [(l, c) for l, t, c in lines if t != ["noise"]]
    if not live:
        problems.append("lines.md has 0 non-noise lines (empty prompt?)")
    cited = set()
    srci = next((i for i, h in enumerate(hdr or []) if "source" in h), None)
    if hdr and srci is None:
        problems.append("R-table needs a 'source' column (L/C ids are only counted there)")
    for r in rows:
        if srci is not None and srci < len(r):
            cell = r[srci]
            if re.search(r"[LC]\d+\s*[-\u2013]\s*[LC]?\d+", cell):
                problems.append(f"{r[0]}: range in source '{cell}' (list ids one by one)")
            cited |= set(re.findall(r"\b([LC]\d+)\b", cell))
    prose = set(re.findall(r"\b([LC]\d+)\b", md)) - cited
    orphans = [(l, c) for l, c in live if l not in cited]
    if not rows:
        problems.append("no R-table rows found (| R1 | ... |)")
    for l, c in orphans:
        print(f"ORPHAN {l}: {c}" + ("  (cited only in prose)" if l in prose else ""))
    for p in problems:
        print(f"GAP    {p}")
    covered = len(live) - len(orphans)
    print(f"-- lines covered {covered}/{covered+len(orphans)}, R rows {len(rows)}")
    if orphans or problems:
        print("COVERAGE FAIL"); sys.exit(1)
    print("COVERAGE OK" + (" (final)" if a.final else ""))


def cmd_show(a):
    for l, t, c in read_lines(a.mission):
        print(f"{l:4} [{','.join(t)}] {c}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split", help="save prompt verbatim and split into tagged lines")
    s.add_argument("mission"); s.add_argument("--text"); s.add_argument("--file")
    s.add_argument("--clarify", action="append", help="later owner clarification (repeatable)")
    s.add_argument("--clarify-file", action="append", help="clarification read from a file (repeatable; safer than --clarify)")
    c = sub.add_parser("cover", help="check every non-noise line is cited in mission.md")
    c.add_argument("mission"); c.add_argument("--final", action="store_true")
    sh = sub.add_parser("show", help="print lines.md")
    sh.add_argument("mission")
    a = ap.parse_args()
    {"split": cmd_split, "cover": cmd_cover, "show": cmd_show}[a.cmd](a)


if __name__ == "__main__":
    main()
