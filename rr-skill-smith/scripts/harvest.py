#!/usr/bin/env python3
"""rr-skill-smith harvest: collect friction logs, critic ledgers, verdicts and cost ledgers across the
JARVIS web, attribute each item to a skill, cluster recurring problems and draft minimal-patch briefs.

Usage:
  harvest.py [--root R] [--home H] scan [--json]
  harvest.py list [--skill S] [--status open|claimed|partial|fixed|env|all] [--sev H|M|L] [--limit N] [--json]
  harvest.py clusters [--skill S] [--min N] [--json]
  harvest.py patch SKILL [--cluster ID ...] [--top N] [--out FILE]
  harvest.py close ID [ID ...] --by EVIDENCE [--status fixed|wontfix|dup]

Sources (read-only): <root>/missions/**, <root>/.rr-missions/**, ~/.rr-missions/**, <root>/trials/**:
  *FRICTION*.md (any format: numbered, F-ids, tables, [H] bullets, ## F-headings), ledger.json,
  pass-*/verdict.md, review/verdict.md, trials/<skill>/REPORT.md (fix claims, review scores), state.json (tokens).
Writes <home>/frictions.json, scores.json, clusters.json (scan) and <home>/proposals/<skill>/ (patch).
Status: open (no fix claimed), claimed (a lane REPORT says fixed; unverified), partial (listed as rejected or
partial), fixed/wontfix/dup (closed with evidence via `close` or ship.py apply --fixes), env (environment, not skill).
"""
import sys

sys.dont_write_bytecode = True
import argparse
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smithlib as L  # noqa: E402

FRICTION_RE = re.compile(r"(?i)^(skill-)?friction.*\.md$")
SEV_WORD = {"h": "H", "high": "H", "m": "M", "med": "M", "medium": "M", "l": "L", "low": "L", "blocker": "H"}
SKIP_SEC = re.compile(r"(?i)\b(what worked|worked|run log|results?|went well|for balance|no friction)\b")
ENV_SEC = re.compile(r"(?i)environment")
SEV_SEC = re.compile(r"(?i)^(high|med|medium|low)\b")


# ---------------------------------------------------------------- sources
def mission_roots(root):
    out = []
    for p in (Path(root) / "missions", Path(root) / ".rr-missions", Path.home() / ".rr-missions"):
        if p.exists() and p.resolve() not in [x.resolve() for x in out]:
            out.append(p)
    return out


def all_bases(root):
    bases = mission_roots(root)
    if (Path(root) / "trials").exists():
        bases.append(Path(root) / "trials")
    return bases


def rglob(base, pred):
    for p in sorted(base.rglob("*")):
        if p.is_file() and not any(s in p.parts for s in L.SKIP_DIRS) and pred(p):
            yield p


def context_of(path, root, skills):
    """(kind, tag, [candidate skills], date) for a file under trials/<skill>/ or a mission folder."""
    path = Path(path).resolve()
    trials = (Path(root) / "trials").resolve()
    if trials in path.parents:
        skill = path.relative_to(trials).parts[0]
        return "trial", "t:" + skill, [skill], L._dt.date.fromtimestamp(path.stat().st_mtime).isoformat()
    for mr in mission_roots(root):
        mr = mr.resolve()
        if mr in path.parents:
            parts = path.relative_to(mr).parts
            slug = parts[0]
            mdir = mr / slug
            cands = []
            st = L.load_json(mdir / "state.json", {}) or {}
            for k in ("skills", "skill"):
                v = st.get(k)
                cands += v if isinstance(v, list) else ([v] if v else [])
            for fr in mdir.glob("*FRICTION*.md"):
                head = "\n".join(L.read(fr).splitlines()[:3])
                cands += [n for n in re.findall(r"\b(rr-[a-z-]+[a-z]|multiuse-critic|risky-rails-[a-z-]+[a-z])\b", head)]
            cands = [c for i, c in enumerate(cands) if c in skills and c not in cands[:i]] or ["rr-mission-control"]
            m = re.match(r"(\d{2})(\d{2})(\d{2})-", slug)
            date = f"20{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else \
                L._dt.date.fromtimestamp(path.stat().st_mtime).isoformat()
            return "mission", "m:" + slug, cands, date
    return "other", "x:" + path.parent.name, ["rr-mission-control"], \
        L._dt.date.fromtimestamp(path.stat().st_mtime).isoformat()


# ---------------------------------------------------------------- friction parsing
def sev_of(text, default):
    t = text[:220]
    pats = [r"\*\*\s*(H|M|L|High|Med|Medium|Low)\s*[:·]", r"^\s*\[\s*(H|M|L)\b", r"\[(H|M|L)(?:[,\] ])",
            r"\((H|M|L)(?:-(H|M|L))?\)\s*$", r"(?i)\b(BLOCKER)\b", r"^\*\*(H|M|L)\*\*"]
    found = []
    for p in pats:
        for m in re.finditer(p, t, re.M):
            found += [SEV_WORD.get(g.lower()) for g in m.groups() if g]
    found = [f for f in found if f]
    if not found:
        return default
    return max(found, key=lambda s: L.SEV_W[s])


def title_of(text):
    t = text.strip()
    m = re.search(r"\*\*(.+?)\*\*", t)
    if m and m.start() < 40:
        ttl = m.group(1)
    else:
        t = re.sub(r"^\s*\[[^\]]*\]\s*", "", t)
        sm = re.match(r"^([\w-]{2,20}) / (.+)$", t) or re.match(r"^(.{1,44}?)\s—\s(.+)$", t)
        head, tail = (sm.group(1), sm.group(2)) if sm else (t, "")
        if tail and len(head) < 45:  # "engine — two roots ..." / "scripts/x.py f() — the check ...": lead with the problem
            t = tail + f" ({head.strip()})"
        ttl = re.split(r"(?<=[a-z0-9)`'\"])\.\s|\s—\s|\s-\s(?=[A-Z])", t, maxsplit=1)[0]
    ttl = re.sub(r"^\s*(\[[^\]]*\]\s*)?((H|M|L|High|Med|Medium|Low)\s*[:·]\s*)?", "", ttl)
    ttl = re.sub(r"^\s*(H|M|L)\s*(\(|·)", "", ttl).strip(" .*:")
    return ttl[:140]


def parse_friction(text):
    items, cur = [], None
    sec_sev, skip, env, table_cols, bullet_n = None, False, False, None, 0
    lines = text.splitlines()

    def start(n, first, sev_default, lineno, extra=None):
        nonlocal cur
        cur = {"n": n, "first": first, "body": [first], "line": lineno, "sev_default": sev_default,
               "env": env, **(extra or {})}
        items.append(cur)

    for i, raw in enumerate(lines, 1):
        line = raw.rstrip()
        hm = re.match(r"^(#{1,4})\s+(.*)$", line)
        if hm:
            htxt = hm.group(2).strip()
            fm = re.match(r"^(F\d+)\s*[·:.\-—]\s*(.+?)\s*$", htxt)
            if fm:
                skip = False
                start(fm.group(1), fm.group(2), sec_sev or "M", i)
                continue
            cur = None
            table_cols = None
            if len(hm.group(1)) == 1:
                sec_sev, skip, env = None, False, False
            if SEV_SEC.match(htxt):
                sec_sev, skip = SEV_WORD[SEV_SEC.match(htxt).group(1).lower()], False
            elif SKIP_SEC.search(htxt) and not re.search(r"(?i)friction", htxt):
                skip = True
            elif ENV_SEC.search(htxt):
                env, skip = True, False
            elif re.search(r"(?i)friction", htxt):
                skip = False
            continue
        if skip:
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            nxt = lines[i] if i < len(lines) else ""
            if table_cols is None and re.match(r"^\|[\s:|-]+\|?\s*$", nxt) and any(re.fullmatch(r"(?i)sev(erity)?", c)
                                                                                 for c in cells):
                table_cols = {c.lower(): k for k, c in enumerate(cells)}
                continue
            if table_cols and not re.match(r"^\|[\s:|-]+\|?\s*$", line) and len(cells) >= len(table_cols) - 1:
                g = lambda *names: next((cells[table_cols[n]] for n in names if n in table_cols
                                         and table_cols[n] < len(cells)), "")
                n = g("#", "id", "n") or str(len(items) + 1)
                what = g("friction", "problem", "issue", "what") or max(cells, key=len)
                where = g("where", "file")
                sevs = [SEV_WORD[x] for x in re.findall(r"[hml]", g("sev", "severity").lower()) if x in SEV_WORD]
                start(n, what, max(sevs, key=lambda s: L.SEV_W[s]) if sevs else (sec_sev or "M"), i, {"where": where})
                cur = None
            continue
        table_cols = None
        m = re.match(r"^(F\d+)\s*(\[[^\]]+\])\s*(.*)$", line)
        if m:
            start(m.group(1), m.group(2) + " " + m.group(3), sec_sev or "M", i)
            continue
        m = re.match(r"^(\d{1,3})\.\s+(.*)$", line)
        if m:
            start(m.group(1), m.group(2), sec_sev or "M", i)
            continue
        m = re.match(r"^- \[(?=[^\]]*\b(?:H|M|L)\b)([^\]]+)\]\s*(.*)$", line)
        if m:
            bullet_n += 1
            start(f"b{bullet_n}", f"[{m.group(1)}] {m.group(2)}", sec_sev or "M", i)
            continue
        if cur is not None and line.strip():
            cur["body"].append(line.strip())
    out = []
    for it in items:
        first = it["first"]
        body = " ".join(it["body"])
        hint = ""
        hm2 = re.search(r"\[(?:[HML](?:-[HML])?\s*,\s*)?(fixed|open)\]", first, re.I)
        if hm2:
            hint = hm2.group(1).lower()
        sev = sev_of(first, it["sev_default"])
        out.append({"n": str(it["n"]), "sev": sev, "title": title_of(first), "text": body[:1500], "line": it["line"],
                    "hint": hint, "env": it["env"], "where": it.get("where", "")})
    return out


# ---------------------------------------------------------------- attribution, themes
def skill_mentions(text, skills, index):
    hits = []
    low = text
    for name in skills:
        for m in re.finditer(r"(?<![\w.-])" + re.escape(name) + r"(?![\w-])", low):
            hits.append((m.start(), name))
    alias = {"mission-control": "rr-mission-control", "critic_kit": "multiuse-critic", "multiuse critic": "multiuse-critic",
             "bible.py": "rr-bible"}
    for a, name in alias.items():
        if name in skills:
            for m in re.finditer(re.escape(a), low):
                hits.append((m.start(), name))
    for m in re.finditer(r"[\w-]+\.(?:py|md|lua|luau|json)\b|\b[a-z]+_[a-z_]+\b", low):
        name = index.get(m.group(0))
        if name:
            hits.append((m.start(), name))
    hits.sort()
    seen = []
    for _, n in hits:
        if n not in seen:
            seen.append(n)
    return seen


def load_themes():
    data = L.load_json(L.SMITH_DIR / "assets" / "themes.json", {"themes": []})
    for t in data["themes"]:
        t["_re"] = [re.compile(p, re.I) for p in t["any"]]
    return data["themes"]


def theme_of(title, text, themes):
    best, score = None, 0
    for t in themes:
        s = sum(2 * bool(r.search(title)) + bool(r.search(text)) for r in t["_re"])
        if s > score:
            best, score = t["id"], s
    return best


WHERE_RE = re.compile(r"([\w./<>-]*[\w-]+\.(?:py|lua|luau|md|json|html))(?:\s*\(?\s*(?:l\.|line\s*|:L?)(\d+))?")


def where_refs(text):
    out = []
    for m in WHERE_RE.finditer(text):
        f = m.group(1)
        if f.endswith(("FRICTION.md", "REPORT.md")):
            continue
        ref = f + (f":{m.group(2)}" if m.group(2) else "")
        if ref not in out:
            out.append(ref)
    return out[:8]


# ---------------------------------------------------------------- report claims
def report_claims(report_text):
    t = report_text
    blanket = set()
    if re.search(r"(?i)all \d* ?friction items (are|were) (fixed|addressed)|every friction item", t):
        blanket |= {"H", "M", "L"}
    if re.search(r"(?i)(all|every) (the )?(\d+ )?high(s)? and (the )?(\d+ )?med(ium)?|every high and medium|"
                 r"all high and medium|every HIGH and MED", t):
        blanket |= {"H", "M"}
    if re.search(r"(?i)(and|plus|along with) (every |all )?(the )?cheap (low|LOW)", t):
        blanket.add("L-cheap")
    partial_lines = []
    in_rej = False
    for line in t.splitlines():
        if line.startswith("#"):
            in_rej = bool(re.search(r"(?i)reject|partial|declin|not (done|fixed)|open", line))
            continue
        if in_rej or re.search(r"(?i)\b(rejected|declined|partly|partial)\b", line):
            partial_lines.append(line)
    return blanket, t, "\n".join(partial_lines)


def claim_status(item, claims):
    if not claims:
        return "open"
    blanket, text, partial = claims
    ids = [item["n"]] + ([f"F{item['n']}"] if item["n"].isdigit() else [])
    pat = r"\b(" + "|".join(re.escape(x) for x in ids if not x.isdigit()) + r")\b" if any(
        not x.isdigit() for x in ids) else None
    if pat and re.search(pat, partial):
        return "partial"
    if item["sev"] in blanket or (pat and re.search(pat, text)):
        return "claimed"
    return "open"


# ---------------------------------------------------------------- scan
def scan(root, home, skills):
    index = L.file_index(skills)
    themes = load_themes()
    old = L.load_json(home / "frictions.json", {}) or {}
    manual = old.get("manual", {})
    items, sources = [], []
    bases = all_bases(root)
    for base in bases:
        for f in rglob(base, lambda p: bool(FRICTION_RE.match(p.name))):
            kind, tag, cands, date = context_of(f, root, skills)
            rep = f.parent / "REPORT.md" if kind == "trial" else None
            ftext = L.read(f)
            fixsec = "\n".join(re.findall(r"(?ims)^#{1,3} [^\n]*\bfix (?:pass|round|report)[^\n]*\n(.*?)(?=^#{1,3} |\Z)", ftext))
            rtext = (L.read(rep) if rep and rep.exists() else "") + "\n" + fixsec
            claims = report_claims(rtext) if rtext.strip() else None
            parsed = parse_friction(ftext)
            sources.append({"path": L.rel(f, root), "kind": kind, "tag": tag, "skills": cands, "items": len(parsed),
                            "date": date})
            for it in parsed:
                full = it["title"] + " " + it["text"] + " " + it["where"]
                ment = skill_mentions(full, skills, index)
                if kind == "trial":
                    primary = cands[0]
                else:
                    primary = next((m for m in ment if m in cands), cands[0])
                if it["env"]:
                    status = "env"
                elif it["hint"]:
                    status = "claimed" if it["hint"] == "fixed" else "open"
                else:
                    status = claim_status(it, claims)
                key = L.fp(tag, L.norm_words(it["title"])[:80])
                rec = {"id": f"{tag}#{it['n']}", "fp": key, "skill": primary,
                       "also": [m for m in ment if m != primary][:4], "sev": it["sev"], "title": it["title"],
                       "text": it["text"], "source": L.rel(f, root), "line": it["line"], "date": date,
                       "status": status, "theme": theme_of(it["title"], full, themes), "where": where_refs(full)}
                if key in manual:
                    rec["status"] = manual[key]["status"]
                    rec["closed_by"] = manual[key].get("by", "")
                items.append(rec)
    L.save_json(home / "frictions.json", {"scanned": L.now(), "root": str(root), "sources": sources,
                                          "items": items, "manual": manual})
    scores, costs = scan_scores(root, skills)
    L.save_json(home / "scores.json", {"scanned": L.now(), "scores": scores, "costs": costs})
    clusters = make_clusters(items, themes)
    L.save_json(home / "clusters.json", {"scanned": L.now(), "clusters": clusters})
    return items, sources, scores, costs, clusters


def _date(p, root):
    ctx = context_of(p, root, {})
    return ctx[3]


def attribute(p, root, skills):
    kind, tag, cands, date = context_of(p, root, skills)
    return kind, tag, cands, date


def scan_scores(root, skills):
    scores, costs, seen_passes = [], [], set()
    for base in all_bases(root):
        for v in rglob(base, lambda p: p.name == "verdict.md"):
            kind, tag, cands, date = attribute(v, root, skills)
            t = L.read(v)
            skill = cands[0]
            pm = re.search(r"pass-(\d+)", str(v))
            crit = str(v.parent.parent) if pm else str(v.parent)
            indep = not re.search(r"(?i)self-assess|self-review|not an independent", t[:600])
            if re.search(r"(?m)^R\d+\s*\|\s*(SAFE|VULN|UNSURE)", t):
                vuln = len(re.findall(r"(?m)^R\d+\s*\|\s*VULN", t))
                new = len(re.findall(r"(?m)^NEW:", t))
                safe = len(re.findall(r"(?m)^R\d+\s*\|\s*SAFE", t))
                indep = bool(re.search(r"(?mi)^independent:\s*yes", t))
                scores.append({"skill": skill, "kind": "security", "vuln": vuln, "new": new, "safe": safe,
                               "independent": indep, "source": L.rel(v, root), "date": date, "tag": tag})
                continue
            crits = {}
            for block in re.findall(r"(?ms)^SCORES[^\n]*:(.*?)(?=^\S[^\n]*:\s*$|^ISSUES|^OVERALL|^Evidence|\Z)", t):
                for m in re.finditer(r"(?m)^\s*([A-Z]\d{1,2})\b[^:\n]{0,40}:\s*(\d+(?:\.\d)?)\s*/\s*10", block):
                    crits[m.group(1)] = float(m.group(2))
            for m in re.finditer(r"(?m)^SCORES[^:\n]*:(.+)$", t):
                for c, s in re.findall(r"\b([A-Z]\d{1,2})\s+(\d+(?:\.\d)?)\b", m.group(1)):
                    crits.setdefault(c, float(s))
            om = re.search(r"(?mi)^OVERALL:\s*(\d+(?:\.\d)?)", t)
            overall = float(om.group(1)) if om else (min(crits.values()) if crits else None)
            if overall is None:
                continue
            passno = int(pm.group(1)) if pm else 1
            seen_passes.add((crit, passno))
            scores.append({"skill": skill, "kind": "critic", "overall": overall, "scores": crits, "independent": indep,
                           "pass": passno, "source": L.rel(v, root), "date": date, "tag": tag})
        for lg in rglob(base, lambda p: p.name.startswith("ledger") and p.suffix == ".json"):
            kind, tag, cands, date = attribute(lg, root, skills)
            data = L.load_json(lg, [])
            if not isinstance(data, list):
                continue
            crit = str(lg.parent)
            new_total = 0
            for e in data:
                if not isinstance(e, dict):
                    continue
                new_total += int(e.get("new") or 0)
                sc = {k: float(v) for k, v in (e.get("scores") or {}).items() if isinstance(v, (int, float))}
                if not sc or (crit, e.get("pass")) in seen_passes:
                    continue
                agent = str(e.get("agent", ""))
                scores.append({"skill": cands[0], "kind": "critic", "overall": min(sc.values()), "scores": sc,
                               "independent": "self" not in agent.lower() and "self" not in lg.name,
                               "pass": e.get("pass"), "source": L.rel(lg, root), "date": date, "tag": tag,
                               "partial": len(sc) < 3})
            costs.append({"skill": cands[0], "kind": "critic", "tokens": new_total, "passes": len(data),
                          "estimated": any("est" in str(e.get("note", "")).lower() for e in data if isinstance(e, dict))
                          or new_total == 0, "source": L.rel(lg, root), "date": date, "tag": tag})
        for st in rglob(base, lambda p: p.name == "state.json"):
            s = L.load_json(st, {}) or {}
            if "tokens" in s and isinstance(s.get("tokens"), (int, float)):
                kind, tag, cands, date = attribute(st, root, skills)
                costs.append({"skill": "rr-mission-control", "kind": "mission", "tokens": int(s["tokens"]),
                              "status": s.get("status", ""), "source": L.rel(st, root), "date": date, "tag": tag,
                              "estimated": True})
    trials = Path(root) / "trials"
    for rep in sorted(trials.glob("*/REPORT.md")) if trials.exists() else []:
        t = L.read(rep)
        skill = rep.parent.name
        date = L._dt.date.fromtimestamp(rep.stat().st_mtime).isoformat()
        m = re.search(r"(?i)review scores?[^\[\n]*\[([\d.,\s]+)\]", t) or \
            re.search(r"(?i)(?:scored|scores)\s+(\d+(?:\.\d)?)\s+and\s+(\d+(?:\.\d)?)", t)
        if m:
            vals = [float(x) for x in re.findall(r"\d+(?:\.\d)?", " ".join(g for g in m.groups() if g))]
            if vals:
                scores.append({"skill": skill, "kind": "review", "overall": min(vals), "values": vals,
                               "independent": True, "source": L.rel(rep, root), "date": date, "tag": "t:" + skill})
        for fm in re.finditer(r"(?m)^Fresh critic on[^:]*: overall (\d+(?:\.\d)?).*?Verdict saved at (\S+?)\.?$", t):
            if not Path(fm.group(2)).exists():
                scores.append({"skill": skill, "kind": "critic", "overall": float(fm.group(1)), "scores": {},
                               "independent": True, "source": L.rel(rep, root), "date": date, "tag": "t:" + skill})
    return scores, costs


# ---------------------------------------------------------------- clusters
def make_clusters(items, themes):
    tmap = {t["id"]: t for t in themes}
    live = [i for i in items if i["status"] in ("open", "claimed", "partial")]
    groups = {}
    for it in live:
        if it["theme"]:
            groups.setdefault((it["skill"], it["theme"]), []).append(it)
    rest = [i for i in live if not i["theme"]]
    sim_n = 0
    used = set()
    for a in rest:
        if a["fp"] in used:
            continue
        wa = L.content_words(a["title"] + " " + a["text"][:300])
        grp = [a]
        for b in rest:
            if b is a or b["fp"] in used or b["skill"] != a["skill"]:
                continue
            wb = L.content_words(b["title"] + " " + b["text"][:300])
            if wa and wb and len(wa & wb) / len(wa | wb) >= 0.25:
                grp.append(b)
        if len(grp) > 1:
            sim_n += 1
            for g in grp:
                used.add(g["fp"])
            groups[(a["skill"], f"sim-{sim_n}")] = grp
    out = []
    web_themes = {}
    for (skill, theme), grp in groups.items():
        if theme in tmap:
            web_themes.setdefault(theme, set()).add(skill)
    for (skill, theme), grp in groups.items():
        t = tmap.get(theme, {})
        sev = max((g["sev"] for g in grp), key=lambda s: L.SEV_W[s])
        srcs = sorted({g["source"] for g in grp})
        n_open = sum(1 for g in grp if g["status"] == "open")
        score = sum(L.SEV_W[g["sev"]] * (1.0 if g["status"] == "open" else 0.5) for g in grp) * (
            1 + 0.5 * (len(srcs) - 1)) * (1.5 if len(web_themes.get(theme, ())) > 1 else 1)
        out.append({"id": f"{skill}/{theme}", "skill": skill, "theme": theme,
                    "title": t.get("title") or grp[0]["title"], "fix": t.get("fix", ""), "n": len(grp),
                    "open": n_open, "sev": sev, "score": round(score, 1), "sources": srcs,
                    "items": [g["id"] for g in grp], "web_skills": sorted(web_themes.get(theme, {skill})),
                    "recurring": len(grp) > 1 or len(web_themes.get(theme, ())) > 1})
    out.sort(key=lambda c: -c["score"])
    return out


# ---------------------------------------------------------------- commands
def cmd_scan(a, root, home, skills):
    items, sources, scores, costs, clusters = scan(root, home, skills)
    if a.json:
        print(json.dumps({"sources": len(sources), "items": len(items), "clusters": len(clusters)}))
        return 0
    print(f"harvest: {len(sources)} friction logs, {len(items)} items, {len(scores)} score records, "
          f"{len(costs)} cost records -> {home}")
    rows = []
    for name in sorted({i["skill"] for i in items} | {s["skill"] for s in scores}):
        its = [i for i in items if i["skill"] == name]
        st = {k: sum(1 for i in its if i["status"] == k) for k in ("open", "claimed", "partial")}
        hopen = sum(1 for i in its if i["status"] == "open" and i["sev"] == "H")
        cl = [c for c in clusters if c["skill"] == name and c["recurring"]][:2]
        last = [s for s in scores if s["skill"] == name and s["kind"] == "critic"]
        last.sort(key=lambda s: (s["date"], s.get("pass") or 0))
        ls = f"{last[-1]['overall']:g}{'' if last[-1]['independent'] else ' self'}" if last else "-"
        rows.append([name, st["open"], hopen, st["claimed"], st["partial"], ls,
                     "; ".join(f"{c['theme']} x{c['n']}" for c in cl) or "-"])
    print(L.md_table(["skill", "open", "open H", "claimed", "partial", "last critic", "top recurring"], rows))
    web = [c for c in clusters if len(c["web_skills"]) > 1]
    seen = []
    for c in web:
        if c["theme"] not in seen:
            seen.append(c["theme"])
    if seen:
        print("web-wide themes: " + ", ".join(f"{t} ({len(next(c for c in web if c['theme'] == t)['web_skills'])} skills)"
                                              for t in seen[:8]))
    print("next: harvest.py clusters --skill S | harvest.py patch S | drift.py | health.py")
    return 0


def load_state(home):
    fr = L.load_json(home / "frictions.json")
    if not fr:
        L.die("no harvest yet: run harvest.py scan first", 1)
    return fr


def cmd_list(a, root, home, skills):
    fr = load_state(home)
    its = [i for i in fr["items"] if (not a.skill or i["skill"] == a.skill or a.skill in i["also"])
           and (a.status == "all" or i["status"] == a.status) and (not a.sev or i["sev"] == a.sev)]
    its.sort(key=lambda i: (-L.SEV_W[i["sev"]], i["skill"], i["id"]))
    its = its[: a.limit] if a.limit else its
    if a.json:
        print(json.dumps(its, indent=1, ensure_ascii=False))
        return 0
    for i in its:
        also = f" (+{','.join(i['also'])})" if i["also"] else ""
        print(f"[{i['sev']}] {i['id']} {i['status']} {i['skill']}{also} [{i['theme'] or '-'}]: {i['title'][:110]}")
    print(f"{len(its)} items")
    return 0


def cmd_clusters(a, root, home, skills):
    cl = (L.load_json(home / "clusters.json") or {}).get("clusters")
    if cl is None:
        L.die("no harvest yet: run harvest.py scan first", 1)
    cl = [c for c in cl if (not a.skill or c["skill"] == a.skill) and c["n"] >= a.min]
    if a.json:
        print(json.dumps(cl, indent=1))
        return 0
    for c in cl:
        web = f" web:{len(c['web_skills'])} skills" if len(c["web_skills"]) > 1 else ""
        print(f"{c['id']}  score {c['score']}  n={c['n']} open={c['open']} sev {c['sev']}{web}\n  {c['title']}\n"
              f"  items: {', '.join(c['items'][:6])}{' ...' if len(c['items']) > 6 else ''}")
    print(f"{len(cl)} clusters")
    return 0


def cmd_patch(a, root, home, skills):
    fr = load_state(home)
    cl = (L.load_json(home / "clusters.json") or {}).get("clusters", [])
    if a.skill not in skills:
        L.die(f"unknown skill {a.skill}; known: {', '.join(sorted(skills))}")
    mine = [c for c in cl if c["skill"] == a.skill and (not a.cluster or c["id"] in a.cluster or c["theme"] in a.cluster)]
    mine = mine[: a.top] if not a.cluster else mine
    byid = {i["id"]: i for i in fr["items"]}
    loose = [i for i in fr["items"] if i["skill"] == a.skill and i["status"] == "open" and i["sev"] == "H"
             and not any(i["id"] in c["items"] for c in cl)]
    ver, _ = L.version_of(skills[a.skill]["dir"])
    files = {p.name: p for p in L.skill_files(skills[a.skill]["dir"])}
    out = [f"# Patch brief: {a.skill} {ver} ({L.today()})", "",
           "Rules: stage first (`ship.py stage SKILL`), edit only the staged copy; one cluster per change; write the "
           "regression check first and see it fail (or, for a claimed fix, pass), then make the smallest fix; no new "
           "features; SKILL.md may grow by 5 lines at most; then `ship.py propose`. Owner approves before anything ships.",
           ""]
    for k, c in enumerate(mine, 1):
        out += [f"## P{k} {c['title']} ({c['id']}, n={c['n']}, open {c['open']}, sev {c['sev']})",
                f"Fix hint: {c['fix'] or 'derive from the evidence; keep it minimal'}"]
        if len(c["web_skills"]) > 1:
            out.append(f"Web-wide: also in {', '.join(s for s in c['web_skills'] if s != a.skill)}; "
                       "prefer one shared fix (in the owning skill) over copies.")
        out.append("Evidence:")
        refs = []
        for iid in c["items"]:
            i = byid.get(iid)
            if not i:
                continue
            out.append(f"- [{i['sev']}] {iid} ({i['status']}): {i['title'][:120]} :: {i['text'][len(i['title']):][:220].strip()}")
            refs += i["where"]
        named = []
        for r in refs:
            base = Path(r.split(":")[0]).name
            if base in files and r not in named:
                named.append(f"{L.rel(files[base], skills[a.skill]['dir'])}{':' + r.split(':')[1] if ':' in r else ''}")
        if named:
            out.append("Files: " + ", ".join(dict.fromkeys(named)))
        out.append('Check to add (evals/evals.json "checks"): '
                   + json.dumps({"id": f"fr-{c['theme']}", "run": "TODO: command that exposes the problem",
                                 "exit": 0, "stdout_has": ["TODO"], "covers": c["items"][:6]}))
        out.append("")
    if loose:
        out.append("## Open H items outside clusters")
        for i in loose[:6]:
            out.append(f"- {i['id']}: {i['title'][:140]}")
    text = "\n".join(out) + "\n"
    dest = Path(a.out) if a.out else home / "proposals" / a.skill / f"patch-brief-{L.today()}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"patch brief: {dest} ({len(mine)} clusters, ~{L.toks(len(text))} tokens)")
    return 0


def cmd_close(a, root, home, skills):
    fr = load_state(home)
    manual = fr.setdefault("manual", {})
    byid = {i["id"]: i for i in fr["items"]}
    n = 0
    for iid in a.ids:
        i = byid.get(iid)
        if not i:
            print(f"unknown id {iid}", file=sys.stderr)
            continue
        manual[i["fp"]] = {"status": a.status, "by": a.by, "date": L.today(), "id": iid}
        i["status"], i["closed_by"] = a.status, a.by
        n += 1
    L.save_json(home / "frictions.json", fr)
    print(f"closed {n} item(s) as {a.status}; rescan keeps it (keyed by source and title)")
    return 0 if n else 1


def main(argv=None):
    ap = L.common_args(argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter))
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("scan", help="harvest every source and rebuild frictions, scores and clusters")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("list", help="friction items")
    p.add_argument("--skill")
    p.add_argument("--status", default="open", choices=["open", "claimed", "partial", "fixed", "wontfix", "dup", "env", "all"])
    p.add_argument("--sev", choices=["H", "M", "L"])
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("clusters", help="recurring problems per skill (web-wide themes weigh more)")
    p.add_argument("--skill")
    p.add_argument("--min", type=int, default=1)
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("patch", help="draft a minimal-patch brief for a skill's top clusters")
    p.add_argument("skill")
    p.add_argument("--cluster", nargs="*", help="cluster ids or themes (default: top N)")
    p.add_argument("--top", type=int, default=3)
    p.add_argument("--out")
    p = sp.add_parser("close", help="close items with evidence (kept across rescans)")
    p.add_argument("ids", nargs="+")
    p.add_argument("--by", required=True, help="evidence, e.g. 'eval fr-pycache passes (rr-ui-foundry 1.1.0)'")
    p.add_argument("--status", default="fixed", choices=["fixed", "wontfix", "dup", "open"])
    a = ap.parse_args(argv)
    root = L.find_root(a.root)
    home = L.ensure_home(L.smith_home(root, a.home))
    skills = L.web(root)
    return {"scan": cmd_scan, "list": cmd_list, "clusters": cmd_clusters, "patch": cmd_patch,
            "close": cmd_close}[a.cmd](a, root, home, skills)


if __name__ == "__main__":
    sys.exit(main())
