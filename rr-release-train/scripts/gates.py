#!/usr/bin/env python3
"""gates.py - rr-release-train pre-release gates G1-G10 and the patch-notes check (library for release.py).

  gates.py --help        this text; gates run through `release.py gate` and `release.py notes-check`

G1 version · G2 changes · G3 patch notes · G4 canon · G5 security (rr-exploit-guard SECURITY_GATE.json) ·
G6 tests · G7 performance · G8 visuals (multiuse-critic ledgers) · G9 hygiene · G10 open questions.
Statuses: PASS, WARN, FAIL, PENDING (evidence missing), WAIVED (owner), N/A. Verdict: NO-GO on any FAIL or a
PENDING blocking gate (presets/gates.json `blocking` per channel); GO-WITH-WARNINGS on WARN or a pending
advisory gate; else GO. Rules and thresholds: presets/gates.json; game facts: rr-bible at run time.
"""
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rtlib import (LEVELS, core, effective_level, find_sibling, level_between, live_release,  # noqa: E402
                   load_json, now, parse_ver, released_versions, save_json, sha256_text, ver_key)

TAG = re.compile(r"\[((?:C-\d+)(?:[,\s]+C-\d+)*)\]")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]")


def _ts(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def changes_hash(ctx):
    inc = [(c["id"], c["audience"], c["title"], c.get("note", "")) for c in ctx.included()]
    return sha256_text(json.dumps([ctx.rel.get("version"), inc]))


def sidings(bible):
    v = bible.value("release.alpha.sidings") or ""
    terms = [t.replace('"', "").strip(" ()").lower() for t in re.split(r"[,()]", v)]
    return [t for t in terms if t and "parking lot" not in t]


# ---------------------------------------------------------------- routes (API vs Studio)
OC_FALLBACK = {"EditableImage", "EditableMesh", "PartOperation", "UnionOperation", "NegateOperation",
               "IntersectOperation", "SurfaceAppearance", "BaseWrap", "WrapLayer", "WrapTarget", "WrapDeformer"}


def canon_limit(ctx):
    v = ctx.bible.value("tech.publish.oc_size_limit")
    return int(v) if v and str(v).isdigit() else 10485760


def canon_unsupported(ctx):
    v = ctx.bible.value("tech.publish.oc_unsupported")
    base = {s.strip() for s in v.split(",")} if v else set()
    return base | ({"UnionOperation", "NegateOperation", "IntersectOperation"} if "PartOperation" in base else set()) \
        | ({"WrapLayer", "WrapTarget", "WrapDeformer"} if "BaseWrap" in base else set()) or OC_FALLBACK


def place_route(ctx, name, info):
    """('api'|'studio', blockers). Unsupported classes force Studio unless the owner set `config --route api`
    for that place after confirming none of them changed since the last Studio publish (the API would not
    update them; unchanged ones are kept)."""
    reasons, pc = [], ctx.place_cfg(name) or {}
    if not pc.get("universe_id") or not pc.get("place_id"):
        reasons.append(f"no Open Cloud IDs (config --place {name} --universe U --place-id P)")
    if info.get("bytes", 0) > canon_limit(ctx):
        reasons.append(f"{info['bytes']} bytes > API limit {canon_limit(ctx)} (tech.publish.oc_size_limit)")
    audit = load_json(ctx.dir / info["audit"], {}) if info.get("audit") else {}
    bad = {c: n for c, n in (audit.get("classes") or {}).items() if c in canon_unsupported(ctx)}
    if bad and pc.get("route") != "api":
        reasons.append("API does not update " + ", ".join(f"{c} x{n}" for c, n in sorted(bad.items()))
                       + " (tech.publish.oc_unsupported; if none changed since the last Studio publish: "
                       f"config --place {name} --route api)")
    if pc.get("route") == "studio":
        reasons.append("owner set route studio")
    return ("studio" if any("IDs" not in r for r in reasons) else "api"), reasons


def release_route(ctx):
    """One route for the whole release, so every place goes live together: ('api'|'studio', reasons)."""
    routes = {n: place_route(ctx, n, i) for n, i in ctx.rel["places"].items()}
    studio = [f"{n}: {'; '.join(w)}" for n, (r, w) in routes.items() if r == "studio"]
    if studio:
        return "studio", studio
    return "api", [f"{n}: {'; '.join(w)}" for n, (r, w) in routes.items() if w]


# ---------------------------------------------------------------- notes-check
def lexicon(bible):
    return [f["value"].strip() for f in bible.facts("world.lexicon") if f.get("value")]


def notes_check(ctx):
    """Trace every line of the .src files; outputs are written only on PASS (a FAIL removes stale ones)."""
    n, rel, bible = ctx.presets["notes"], ctx.rel, ctx.bible
    by_id = {c["id"]: c for c in rel["changes"]}
    player = {c["id"] for c in ctx.included() if c["audience"] == "player"}
    errors, warnings, texts, tagged = [], [], {}, set()
    odds, buy = re.compile(n["odds_words"], re.I), re.compile(n["buy_words"], re.I)
    promise = re.compile(n.get("promise_words", r"$^"), re.I)
    siding_terms, lex = sidings(bible), lexicon(bible)
    lex_low = [x.lower().rstrip(".!") for x in lex]
    all_text = " ".join(by_id[c]["title"] + " " + by_id[c].get("note", "") for c in player)
    VER = re.compile(r"\bv?\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?")

    def scan(text, fname, store=False):
        out = []
        for i, line in enumerate(text.splitlines(), 1):
            ids = [x for grp in TAG.findall(line) for x in re.findall(r"C-\d+", grp)]
            bullet = bool(re.match(r"^\s*[-*]\s+", line))
            head = line.lstrip().startswith("#")
            clean = re.sub(r"\s*" + TAG.pattern, "", line).rstrip()
            body = re.sub(r"^\s*(#+|[-*])\s*", "", clean).strip()
            where = f"{fname}:{i}"
            if bullet and not ids and not store:
                errors.append(f"{where}: bullet has no [C-n] tag (every claim must trace to a change)")
            for cid in ids:
                c = by_id.get(cid)
                if not c:
                    errors.append(f"{where}: {cid} is not a change in this release")
                elif c.get("in_build") != "yes":
                    errors.append(f"{where}: {cid} is not confirmed in the build (mark it or drop the line)")
                elif c["audience"] != "player":
                    errors.append(f"{where}: {cid} is internal; players do not get internal work")
                tagged.add(cid)
            src_text = " ".join(by_id[x]["title"] + " " + by_id[x].get("note", "") for x in ids if x in by_id)
            is_lex = body.lower().rstrip(".!") in lex_low
            free = body and not bullet and not ids and not store and not head
            if free and not is_lex and not body.upper().startswith("TITLE:"):
                errors.append(f"{where}: untraced line '{body[:60]}': a notice or sign-off is a world.lexicon string "
                              "verbatim, or carries the [C-n] tag of the change it describes")
            if odds.search(clean) and buy.search(clean):
                errors.append(f"{where}: sells or implies odds/luck for money (D-007 never sell odds): {clean[:80]}")
            if promise.search(clean):
                errors.append(f"{where}: promises future content ('{promise.search(clean).group(0)}'): notes say what "
                              "shipped; plans are the owner's to announce")
            for j in n["jargon"]:
                if re.search(re.escape(j) if not j[0].isalpha() else rf"\b{re.escape(j)}", clean, re.I):
                    warnings.append(f"{where}: internal jargon '{j}' in player text")
            for t in siding_terms:
                if t in clean.lower() and not (ids and t in src_text.lower()):
                    errors.append(f"{where}: names parked siding '{t}' (release.alpha.sidings): only a tagged line "
                                  "whose change ships it may name it")
            nums = re.findall(r"\d+(?:\.\d+)?%?", VER.sub("", clean))
            lex_hit = " ".join(x for x in lex if x.lower() in clean.lower())
            for num in nums:
                bare = num.rstrip("%")
                if bullet and ids and bare not in src_text:
                    warnings.append(f"{where}: number {num} is not in {', '.join(ids)}; confirm it against canon")
                elif not bullet and bare not in (src_text if ids else all_text) and bare not in lex_hit:
                    errors.append(f"{where}: number {num} in a headline/notice/sign-off traces to no change "
                                  "(tag the line, or drop the number)")
            out.append(clean)
        return "\n".join(out).strip() + "\n"

    src = ctx.dir / "PATCH_NOTES.src.md"
    if not src.is_file():
        errors.append("PATCH_NOTES.src.md missing: `release.py notes` writes the brief; write the notes from it")
    else:
        text = scan(src.read_text(), src.name)
        texts["PATCH_NOTES.md"] = text
        if len(text) > n["discord_max"]:
            errors.append(f"PATCH_NOTES.md is {len(text)} characters (limit {n['discord_max']}, one Discord post)")
        if len(EMOJI.findall(text)) > n["max_emoji"]:
            warnings.append(f"PATCH_NOTES.md has {len(EMOJI.findall(text))} emoji (house max {n['max_emoji']})")
    st = ctx.dir / "STORE_UPDATE.src.txt"
    if not st.is_file():
        warnings.append("STORE_UPDATE.src.txt missing (one line for the store description)")
    else:
        text = scan(st.read_text(), st.name, store=True)
        lines = [x for x in text.splitlines() if x.strip()]
        title = next((x.split(":", 1)[1].strip() for x in lines if x.upper().startswith("TITLE:")), None)
        blurb = "\n".join(x for x in lines if not x.upper().startswith("TITLE:"))
        texts["STORE_UPDATE.txt"] = text
        if len(blurb) > n["store_max"]:
            errors.append(f"store line is {len(blurb)} characters (limit {n['store_max']})")
        for rx in n["store_banned"]:
            if re.search(rx, text, re.I):
                errors.append(f"store text matches {rx} (release.store.metadata_rules: "
                              f"{bible.value('release.store.metadata_rules') or 'no free, no giveaway'})")
        if title is not None:
            if len(title) > n["title_max"]:
                errors.append(f"title is {len(title)} characters (max {n['title_max']}; recheck in Creator Hub)")
            if len(EMOJI.findall(title)) > 1:
                errors.append("title has more than one emoji (release.store.title: one emoji max)")
            if not title.lower().startswith("risky rails"):
                warnings.append(f"title does not follow release.store.title: {bible.value('release.store.title')}")
    for cid in sorted(player - tagged, key=lambda x: int(x[2:])):
        errors.append(f"{cid} ({by_id[cid]['title'][:60]}) is a player change the notes do not cover "
                      "(cover it, or `mark --audience internal`)")
    tmp = ctx.dir / ".notes-check"
    tmp.mkdir(exist_ok=True)
    if not bible.ok:
        errors.append("rr-bible not found (RR_BIBLE_SKILL): canon check impossible")
    else:
        for o, text in texts.items():
            (tmp / o).write_text(text)
            code, findings, _ = bible.check(tmp / o, skip="hex,fonts")
            for f in findings:
                (errors if f.get("level") == "ERROR" else warnings).append(f"{o}:{f.get('line')}: {f.get('msg')}")
    shutil.rmtree(tmp, ignore_errors=True)
    outputs = []
    for o, text in texts.items():
        if not errors:
            (ctx.dir / o).write_text(text)
            outputs.append(o)
        elif (ctx.dir / o).is_file():
            (ctx.dir / o).unlink()  # a stale "clean" file must not be posted
    res = {"ok": not errors, "errors": errors, "warnings": sorted(set(warnings), key=warnings.index),
           "outputs": outputs, "changes_hash": changes_hash(ctx), "at": now()}
    save_json(ctx.dir / "notes-check.json", res)
    return res


# ---------------------------------------------------------------- missions (rr-mission-control folders)
def mission_notes(mdir):
    """Owner-facing notes a mission's export left: 'Watch:' checks, scripts marked 'delete for release'."""
    out = {"watch": [], "delete": []}
    d = Path(mdir) / "export"
    for f in sorted(d.rglob("*.md"))[:20] if d.is_dir() else []:
        for line in f.read_text(errors="replace").splitlines():
            m = re.search(r"\bWatch:\s*(.+)", line)
            if m:
                out["watch"].append(m.group(1).strip()[:200])
            if re.search(r"delete (it )?(for|before) release", line, re.I):
                for tok in re.findall(r"[\w/.-]+\.lua\b", line):
                    out["delete"].append(re.sub(r"(\.(client|server))?\.lua$", "", tok.split("/")[-1]))
    out["delete"] = sorted(set(out["delete"]))
    return out


def ledger_standing(crit_dir, bar):
    """multiuse-critic standing rule, read fresh: latest score per criterion, overall = lowest. Certified =
    every standing score from a recorded non-self agent, overall >= bar, and an independent --kind final pass
    that agrees (all its scores at the bar)."""
    rows = load_json(Path(crit_dir) / "ledger.json", []) or []
    if not rows:
        return None
    stand, agents = {}, {}
    for r in rows:
        for c, sc in (r.get("scores") or {}).items():
            stand[c], agents[c] = sc, (r.get("agent") or "").strip()
    overall = min(stand.values()) if stand else None
    indep = bool(agents) and all(w and "self" not in w.lower() for w in agents.values())
    finals = [r for r in rows if r.get("kind") == "final" and "self" not in (r.get("agent") or "self").lower()]
    final_ok = bool(finals) and all(v >= bar for v in (finals[-1].get("scores") or {}).values())
    return {"dir": str(crit_dir), "overall": overall, "bar": bar, "passes": len(rows), "independent": indep,
            "final": final_ok, "certified": indep and final_ok and overall is not None and overall >= bar,
            "agents": sorted({w or "(unrecorded)" for w in agents.values()})}


def mission_terms(c):
    """Distinctive words of an in-build mission (slug words, capitalised terms of its objective and title)."""
    m = c.get("mission") or {}
    slug = Path(m.get("dir", "")).name
    stop = {"risky rails", "roblox", "blender", "studio", "claude", "fbx", "build", "remake", "objective", "the", "and",
            "for", "new", "mission", "each", "every", "exported", "ready", "alerts", "every alert"}
    t = {w for w in re.sub(r"^\d{6}-", "", slug).split("-") if len(w) >= 3}
    obj = ""
    mm = Path(m.get("dir", "")) / "mission.md"
    if mm.is_file():
        x = re.search(r"^Objective:\s*(.+)$", mm.read_text(errors="replace"), re.M)
        obj = x.group(1) if x else ""
    t |= {w.lower() for w in re.findall(r"\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*", obj + " " + c.get("title", ""))}
    return {x for x in t if x not in stop and len(x) >= 3}


# ---------------------------------------------------------------- gates
def G(gid, ctx, status, summary, details=None, fix=None):
    return {"id": gid, "name": ctx.presets["gate_names"][gid], "status": status, "summary": summary,
            "details": details or [], "fix": fix or []}


def soft(ctx):
    """Status for problems that block only strict channels."""
    return "FAIL" if ctx.presets["channels"][ctx.rel["channel"]]["strict"] else "WARN"


def worse(a, b):
    order = ["N/A", "PASS", "WARN", "PENDING", "FAIL"]
    return a if order.index(a) >= order.index(b) else b


def audit_of(ctx, name):
    info = ctx.rel["places"][name]
    return load_json(ctx.dir / info["audit"], {}) or {}


def baseline_dir(ctx, name):
    """Audit folder of the release that is live now (rtlib.live_release), or None."""
    live = live_release(ctx.root)
    d = ctx.root / live["version"] / "places" / name / "audit" if live else None
    return d if d and d.is_dir() else None


def g1(ctx):
    rel, v = ctx.rel, ctx.rel.get("version")
    if not v:
        return G("G1", ctx, "PENDING", "no version", fix=["release.py version --apply"])
    if not parse_ver(v):
        return G("G1", ctx, "FAIL", f"{v} is not semver", fix=["release.py version --set X.Y.Z-alpha.N"])
    hist = released_versions(ctx.root)
    if hist and ver_key(v) <= max(ver_key(h) for h in hist):
        return G("G1", ctx, "FAIL", f"{v} is not above released {max(hist, key=ver_key)}",
                 fix=["release.py version --apply"])
    status, det, fix = "PASS", [], []
    pre = parse_ver(v)[3].split(".")[0]
    if pre != ctx.channel_pre():
        status = soft(ctx)
        det.append(f"{v} does not carry channel {rel['channel']}'s tag '{ctx.channel_pre()}'")
    if not rel["places"]:
        return G("G1", ctx, "PENDING", f"{v}; no place attached", det, ["release.py attach NAME FILE"])
    for n, i in rel["places"].items():
        if i.get("stamp") is None:
            status = "FAIL"
            det.append(f"{n}: no RR_Version stamp in the file (the Luau release tests and smoke S1 need it)")
            fix.append("release.py stamp; owner places RR_Version in ReplicatedStorage, saves, re-attaches")
        elif i["stamp"] != v:
            status = "FAIL"
            det.append(f"{n}: stamp says {i['stamp']}, release is {v} (wrong file or stale stamp)")
            fix.append("release.py stamp; update RR_Version in Studio; re-attach")
    return G("G1", ctx, status, f"{v}" + (f" · {det[0]}" if det else " · stamps match"), det, sorted(set(fix)))


def g2(ctx):
    rel, inc = ctx.rel, ctx.included()
    unknown = [c["id"] for c in rel["changes"] if c.get("in_build") == "unknown"]
    if not inc:
        return G("G2", ctx, "FAIL" if not unknown else "PENDING", "no confirmed in-build change",
                 fix=["release.py collect / add / mark --in-build yes --via ..."])
    if unknown:
        return G("G2", ctx, "PENDING", f"{len(unknown)} changes not confirmed in the build: {', '.join(unknown)}",
                 fix=[f"ask the owner, then release.py mark {' '.join(unknown)} --in-build yes|no --via \"chat DATE\""])
    need = max((c["bump"] for c in inc), key=lambda b: LEVELS[b])
    v = rel.get("version")
    det, status, fix = [], "PASS", []
    if v and parse_ver(v):
        lives = [h for h in released_versions(ctx.root) if not parse_ver(h)[3]]
        base = max(lives, key=ver_key) if lives else "0.0.0"
        have = level_between(base, core(v))
        if LEVELS[have] < LEVELS[effective_level(need, base)]:
            status = "FAIL"
            det.append(f"{v} is a {have} step from {base}, changes need {effective_level(need, base)}")
            fix.append("release.py version --apply")
    owner_word = [c for c in inc if not c["src"].startswith(("git:", "place:"))]
    agent_word = [c["id"] for c in owner_word if not c.get("via")]
    for c in owner_word:
        if c.get("via"):
            det.append(f"{c['id']} in build per the owner ({c['via']})")
    if agent_word:
        status = worse(status, soft(ctx))
        det.insert(0, f"in build on the agent's word, no owner citation: {', '.join(agent_word)}")
        fix.append(f"ask the owner what is in Studio, then release.py mark {' '.join(agent_word)} --in-build yes "
                   "--via \"chat DATE\"")
    players = [c for c in inc if c["audience"] == "player"]
    diffs = [c for c in inc if c["src"].startswith("place:")]
    if diffs and not players:
        status = worse(status, "WARN")
        det.append("scripts changed but no player-facing change describes them")
    tele = [p for c in diffs for p in (c.get("scripts") or {}).get("teleport", [])]
    if tele:
        status = worse(status, "WARN")
        det.append(f"cross-place contract changed ({', '.join(tele[:4])}): during the bleed-off old Lobby servers "
                   "still send players to the new Trip (and back); the new side must accept the old TeleportData")
    return G("G2", ctx, status, f"{len(inc)} in build ({len(players)} player) · bump {need}" +
             (f" · {det[0]}" if det else ""), det, fix)


def g3(ctx):
    if not [c for c in ctx.included() if c["audience"] == "player"]:
        return G("G3", ctx, "N/A", "no player-facing change")
    nc = load_json(ctx.dir / "notes-check.json")
    if not nc:
        return G("G3", ctx, "PENDING", "notes not checked", fix=["release.py notes; write the .src files; notes-check"])
    if nc.get("changes_hash") != changes_hash(ctx):
        return G("G3", ctx, "PENDING", "changes or version moved since notes-check", fix=["release.py notes-check"])
    if not nc["ok"]:
        return G("G3", ctx, "FAIL", f"{len(nc['errors'])} errors", nc["errors"][:10], ["fix the .src files; notes-check"])
    return G("G3", ctx, "WARN" if nc["warnings"] else "PASS", f"every line traced · {len(nc['warnings'])} warnings",
             nc["warnings"][:10])


def script_files(ctx, name):
    """[(instance path, class, text)] of one attached place's extracted scripts."""
    info = ctx.rel["places"][name]
    sdir = ctx.dir / Path(info["audit"]).parent / "scripts"
    out = []
    for e in load_json(sdir / "index.json", []) or []:
        f = sdir / e["file"]
        if f.is_file():
            out.append((e["path"], e.get("class", ""), f.read_text(errors="replace")))
    return out


def combined_scripts(ctx, name):
    lines, where = [], []
    for path, _, txt in script_files(ctx, name):
        for k, ln in enumerate(txt.splitlines(), 1):
            lines.append(ln)
            where.append(f"{path}:{k}")
    out = ctx.dir / Path(ctx.rel["places"][name]["audit"]).parent / "all_scripts.lua"
    out.write_text("\n".join(lines) + "\n")
    return out, where


def number_drift(ctx):
    """Heuristic: `name = number` in scripts vs single-number canon facts whose last key segment names it."""
    d = ctx.presets.get("drift") or {}
    facts = []
    for pre in d.get("prefixes", []):
        for f in ctx.bible.facts(pre):
            if re.fullmatch(r"-?\d+(?:\.\d+)?", str(f.get("value", "")).strip()):
                seg, parent = f["key"].split(".")[-1], f["key"].split(".")[-2]
                for u in d.get("units", []):
                    if seg.endswith(u):
                        seg = seg[: -len(u)]
                        break
                facts.append((seg.replace("_", "").lower(), "_" in seg, parent.lower(), f))
    out = []
    for n in ctx.rel["places"]:
        for path, _, txt in script_files(ctx, n):
            low_path = path.lower()
            for k, ln in enumerate(txt.splitlines(), 1):
                if ln.lstrip().startswith("--"):
                    continue
                for m in re.finditer(r"\b([A-Za-z_]\w*)\s*=\s*(-?\d+(?:\.\d+)?)\b", ln):
                    ident = m.group(1).replace("_", "").lower()
                    for seg, multi, parent, f in facts:
                        if ident == seg and (multi or parent in low_path) and float(m.group(2)) != float(f["value"]):
                            out.append(f"{n} {path.split('.')[-1]}:{k} {m.group(1)} = {m.group(2)}; canon "
                                       f"{f['key']} = {f['value']} ({(f.get('note') or '')[:60]})")
    return sorted(set(out))


def g4(ctx):
    b = ctx.bible
    if not b.ok:
        return G("G4", ctx, "FAIL", "rr-bible not found", fix=["set RR_BIBLE_SKILL to the rr-bible folder"])
    if not ctx.rel["places"]:
        return G("G4", ctx, "PENDING", "no place attached", fix=["release.py attach NAME FILE"])
    status, det, off = "PASS", [], 0
    for n in ctx.rel["places"]:
        props = ctx.dir / Path(ctx.rel["places"][n]["audit"]).parent / "props.lua"
        if props.is_file():
            _, finds, _ = b.check(props, skip="names,numbers")
            errs = [f for f in finds if f.get("level") == "ERROR"]
            off += len(errs)
            det += [f"{n} colour/font: {f['msg']}" for f in errs[:4]]
        allf, where = combined_scripts(ctx, n)
        _, finds, _ = b.check(allf, skip="hex,fonts")
        for f in finds:
            loc = where[f["line"] - 1] if f.get("line") and f["line"] <= len(where) else "?"
            if f.get("level") == "ERROR":
                status = "FAIL"
            det.insert(0, f"{n} {loc}: {f['msg']}")
    if off:
        status = worse(status, "WARN")
    drift = number_drift(ctx)
    if drift:
        status = worse(status, "WARN")
        det += [f"possible number drift: {x}" for x in drift[:6]]
    summ = (f"{off} off-palette colours/fonts" if off else "colours/fonts on canon") + \
        (" · scripts: banned name or contradicting number" if status == "FAIL" else
         " · scripts: no banned name; numbers compared only where canon has a check pattern") + \
        (f" · {len(drift)} possible number drifts (heuristic)" if drift else "")
    fix = ["fix the script to canon, or record the change with bible add-fact / decide (owner)"] if status != "PASS" \
        and (status == "FAIL" or drift) else []
    return G("G4", ctx, status, summ, det[:14], fix)


def security_file_problems(data):
    """Why a SECURITY_GATE.json is not an rr-exploit-guard verdict ([] when it is)."""
    if not isinstance(data, dict):
        return ["not a JSON object"]
    p = []
    if data.get("skill") != "rr-exploit-guard":
        p.append("skill is not rr-exploit-guard")
    if str(data.get("verdict", "")).upper() not in ("PASS", "HOLD", "FAIL"):
        p.append("verdict is not PASS/HOLD/FAIL")
    if not _ts(data.get("scanned_at")):
        p.append("no scanned_at")
    if not isinstance(data.get("places"), dict):
        p.append("no places map (sha256 of what was scanned)")
    return p


def g5(ctx):
    ev = ctx.rel["evidence"].get("security") or {}
    guard = find_sibling("rr-exploit-guard", "RR_EXPLOIT_GUARD_SKILL")
    scan_dirs = " ".join(str(ctx.dir / Path(i["audit"]).parent / "scripts") for i in ctx.rel["places"].values())
    how = (f"rr-exploit-guard ({guard or 'not installed yet'}): scan {scan_dirs or '<attach places first>'}, gate "
           f"--stage {ctx.rel['channel']} --out {ctx.dir / 'security'}")
    if ev.get("by") == "owner" and not ev.get("file"):
        st = {"pass": "PASS", "hold": soft(ctx), "fail": "FAIL"}[ev["result"]]
        return G("G5", ctx, st, f"owner-attested {ev['result']} without an rr-exploit-guard verdict "
                 f"({ev.get('note', '')[:80]})", fix=[how] if st != "PASS" else [])
    f = Path(ev["file"]) if ev.get("file") else ctx.dir / "security" / "SECURITY_GATE.json"
    if not f.is_file():
        return G("G5", ctx, "PENDING", "no security verdict", fix=[how])
    try:
        data = load_json(f, {})
    except ValueError:
        data = None
    bad = security_file_problems(data)
    if bad:
        return G("G5", ctx, "FAIL", f"{f.name} is not an rr-exploit-guard verdict: {'; '.join(bad)}", fix=[how])
    verdict = str(data["verdict"]).upper()
    pinned = {str(v) for v in data["places"].values()}
    unbound = [n for n, i in ctx.rel["places"].items() if i["sha256"] not in pinned]
    if unbound:
        return G("G5", ctx, "PENDING", f"verdict {verdict} was not made on the attached {', '.join(unbound)} "
                 "(file changed since the scan, or the scan did not pin it)", fix=[how])
    if data.get("stage") != ctx.rel["channel"]:
        return G("G5", ctx, "PENDING", f"verdict {verdict} is for stage {data.get('stage')}, release channel is "
                 f"{ctx.rel['channel']}", fix=[how])
    counts = f"blocking {len(data.get('blocking') or [])}, hold {len(data.get('hold') or [])}"
    st = {"PASS": "PASS", "HOLD": soft(ctx), "FAIL": "FAIL"}[verdict]
    det = [str(x)[:160] for x in (data.get("blocking") or [])[:5] + (data.get("hold") or [])[:5]]
    return G("G5", ctx, st, f"rr-exploit-guard {verdict} ({counts}, stage {data['stage']}, bound to the attached "
             "files)", det, [how] if st != "PASS" else [])


def need_kind(ctx, kind):
    spec = ctx.presets["evidence"][kind]
    if ctx.rel["channel"] not in spec["channels"]:
        return False
    return LEVELS.get(ctx.rel.get("bump", "patch"), 1) >= LEVELS[spec.get("min_bump", "none")]


def g6(ctx):
    ev, cfg, det, fix = ctx.rel["evidence"], ctx.cfg, [], []
    status = "PASS"
    data_rx = re.compile(ctx.presets.get("specs_data", r"$^"))
    risky = [f"{n} {p}" for n in ctx.rel["places"] for p, _, txt in script_files(ctx, n)
             if p.endswith(".spec") and data_rx.search(txt)]
    if risky:
        status = "FAIL"
        det.append("specs touch live data services (the release tests run on the production universe): "
                   + ", ".join(risky[:4]))
        fix.append("keep specs off DataStore/ProfileStore/Messaging/MemoryStore; data modules check "
                   "_G.RR_RELEASE_TEST and stub themselves (references/gates.md)")
    t = ev.get("tests")
    route, why = release_route(ctx) if ctx.rel["places"] else ("studio", ["no places"])
    deferred = cfg.get("luau_tests") and route == "api" and not why
    if t and t.get("by") == "opencloud" and deferred:
        det.append(f"tests deferred (publish re-runs them); last Open Cloud run {t['result']}")
    elif t:
        if t["result"] != "pass":
            status = "FAIL"
        det.append(f"tests {t['result']} ({t['by']}) {t.get('note', '')[:120]}")
    elif need_kind(ctx, "tests"):
        if deferred:
            det.append("tests deferred: run_tests.lua runs on each saved version before publish; publish stops on a fail")
        else:
            status = worse(status, "PENDING")
            det.append("no test result")
            fix.append("owner runs assets/luau/run_tests.lua in Studio (command bar, server) and records "
                       "`evidence tests --result pass --by owner --note \"N specs\"`")
    b = ev.get("bugbash")
    if b:
        status = "FAIL" if b["result"] != "pass" else status
        det.append(f"bug bash {b['result']} ({b['by']}) {b.get('note', '')[:80]}")
    elif need_kind(ctx, "bugbash"):
        status = worse(status, "PENDING")
        det.append("bug bash needed (minor or bigger release): " + (ctx.bible.value("release.alpha.bug_bash") or ""))
        fix.append("owner runs the bug bash and records `evidence bugbash --result pass --by owner --note ...`")
    summ = " · ".join(d.split(":")[0] for d in det) or "no tests required"
    return G("G6", ctx, status, summ[:120], det, fix)


def run_extra(ctx, gid):
    """Sibling checks from presets. Advisory unless the cmd takes {audits} (then it judges this build)."""
    cache = ctx.__dict__.setdefault("_extra", {})
    if gid in cache:
        return cache[gid]
    out = cache[gid] = []
    audits = [str(ctx.dir / Path(i["audit"]).parent) for i in ctx.rel["places"].values()]
    for x in ctx.presets.get("extra_checks", []):
        if x["gate"] != gid:
            continue
        bound = any("{audits}" in c for c in x["cmd"])
        sk = find_sibling(x["skill"])
        if not sk:
            out.append((x["name"], None, f"skipped: {x['skill']} not installed", bound))
            continue
        cmd = []
        for c in x["cmd"]:
            cmd += audits if c == "{audits}" else [c.replace("{python}", sys.executable).replace("{skill}", str(sk))]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            lines = [ln.strip() for ln in (r.stdout + r.stderr).strip().splitlines() if ln.strip()]
            keep = [ln for ln in lines if re.search(r"\b(FAIL|ERROR|over|missing|placeholder)\b", ln, re.I)] or lines[-1:]
            out.append((x["name"], r.returncode, " | ".join(keep[:3])[:600], bound))
        except (OSError, subprocess.TimeoutExpired) as e:
            out.append((x["name"], 1, f"could not run: {e}", bound))
    return out


def extra_lines(ctx, gid):
    """(status change for build-bound checks, detail lines bound to the build, advisory lines)."""
    st, det, adv = "PASS", [], []
    for name, code, tail, bound in run_extra(ctx, gid):
        line = f"{name}: {'skipped' if code is None else ('ok' if code == 0 else 'FAILED')} {tail}"
        if bound:
            det.append(line)
            if code:
                st = soft(ctx)
        else:
            adv.append(f"{gid} (library, not this build) {line}")
    return st, det, adv


def audit_metrics(a):
    c = a.get("counts", {})
    return {"instances": a.get("instances", 0), "parts": c.get("parts", 0), "meshparts": c.get("meshparts", 0),
            "unanchored_parts": c.get("unanchored_parts", 0), "scripts": c.get("scripts", 0),
            "script_bytes": c.get("script_bytes", 0), "effects": sum((c.get("effects") or {}).values()),
            "bytes": a.get("bytes", 0)}


def g7(ctx):
    p, status, det, fix = ctx.presets["perf"], "PASS", [], []
    live = live_release(ctx.root)
    ev = ctx.rel["evidence"]
    fresh = []
    for n in ctx.rel["places"]:
        cur = audit_metrics(audit_of(ctx, n))
        bd = baseline_dir(ctx, n)
        prev_a = load_json(bd / "audit.json") if bd else None
        if not prev_a:
            fresh.append(n)
            det.append(f"{n}: no baseline to compare (first audited release): {cur['instances']} instances, "
                       f"{cur['parts']} parts ({cur['meshparts']} MeshParts, {cur['unanchored_parts']} unanchored), "
                       f"{cur['scripts']} scripts, {cur['effects']} effects, {cur['bytes'] // 1024} KB file")
            continue
        old = audit_metrics(prev_a)
        grew = [f"{m} {old[m]}->{cur[m]} (+{(cur[m] - old[m]) * 100 // max(old[m], 1)}%)" for m in p["metrics"]
                if cur[m] > old[m] and (cur[m] - old[m]) * 100 > p["warn_growth_pct"] * max(old[m], 1)]
        if grew:
            status = worse(status, "WARN")
            det.append(f"{n} vs {live['version']}: " + ", ".join(grew))
            fix.append("owner: confirm on a phone (F9 memory, FPS) that the growth is fine; record `evidence perf`")
        else:
            det.append(f"{n}: no metric grew over {p['warn_growth_pct']}% vs {live['version']}")
    if fresh and not ev.get("perf"):
        status = worse(status, soft(ctx))
        fix.append("owner: play the new content on a phone (F9 memory, FPS) and record "
                   "`evidence perf --result pass --by owner --note \"phone, FPS, MB\"`")
    xs, xdet, _ = extra_lines(ctx, "G7")
    status, det = worse(status, xs), det + xdet
    for kind in ("perf", "livecheck"):
        e = ev.get(kind)
        if e and e["result"] != "pass":
            status = "FAIL"
            det.append(f"{kind} {e['result']} ({e['by']}): {e.get('note', '')}")
        elif e:
            det.append(f"{kind} pass ({e['by']}): {e.get('note', '')[:80]}")
    if not ev.get("livecheck") and need_kind(ctx, "livecheck"):
        status = worse(status, "PENDING")
        det.append("live check needed: " + (ctx.bible.value("tech.streaming.live_check") or ""))
        fix.append("owner runs the live check and records `evidence livecheck --result pass --by owner --note ...`")
    summ = ("no baseline: owner phone evidence needed · " if fresh and not ev.get("perf") else "") + \
        (det[0] if det else "no places")
    return G("G7", ctx, status, summ[:140] + " (budgets: OQ-039 default A)", det, fix)


def g8(ctx):
    kinds = set(ctx.presets["visual_kinds"])
    vis = [c for c in ctx.included() if (c.get("mission") or {}).get("kind") in kinds]
    if not vis:
        return G("G8", ctx, "N/A", "no visual work from missions in this build")
    det, fix, bad = [], [], 0
    for c in vis:
        m = c["mission"]
        bar = m.get("bar") or 8
        crit = [x for x in (ledger_standing(d, bar) for d in sorted(Path(m["dir"]).glob("critique*")) if d.is_dir()) if x]
        ok = [x for x in crit if x["certified"]]
        if ok:
            det.append(f"{c['id']}: certified {ok[0]['overall']}/{bar} by {', '.join(ok[0]['agents'])} (final pass agrees)")
            continue
        bad += 1
        led = "; ".join(f"{Path(x['dir']).name} {x['overall']}/{bar} by {', '.join(x['agents'])}"
                        + ("" if x["final"] else ", no independent final pass") for x in crit)
        det.append(f"{c['id']} {c['title'][:50]}: uncertified ({led or 'no critic ledger'})")
        best = max(crit, key=lambda x: (x["overall"] or 0), default=None)
        if not best:
            fix.append(f"{c['id']}: no critic ledger: score it with multiuse-critic ({m['dir']})")
        elif (best["overall"] or 0) < bar:
            fix.append(f"{c['id']}: standing {best['overall']}/{bar}: finish the fix loop in rr-mission-control "
                       f"(fix the open blocks-{bar} issues), then one independent --kind final pass ({best['dir']})")
        elif not best["independent"]:
            fix.append(f"{c['id']}: at the bar on self-review only: one independent --kind final multiuse-critic "
                       f"pass ({best['dir']})")
        else:
            fix.append(f"{c['id']}: independent and at the bar: one --kind final pass must agree ({best['dir']})")
    st = "PASS" if not bad else soft(ctx)
    return G("G8", ctx, st, f"{len(vis) - bad}/{len(vis)} visual changes certified (independent, at the bar, final "
             "pass agrees)", det, fix)


def words_of(name):
    return {w.lower() for w in re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+", name)}


def g9(ctx):
    h, status, det, fix = ctx.presets["hygiene"], "PASS", [], []
    assign, dname = re.compile(h["debug_assign"]), re.compile(h["debug_name"])
    dex, blank = re.compile(h["debug_name_exclude"]), re.compile(h["blank_asset_in_script"], re.I)
    demo_words = set(h["demo_words"])
    canon_store = ctx.bible.value("tech.data.store_name")
    marked = {x for c in ctx.included() if c.get("mission") for x in mission_notes(c["mission"]["dir"])["delete"]}
    for n in ctx.rel["places"]:
        a = audit_of(ctx, n)
        files = script_files(ctx, n)
        bd = baseline_dir(ctx, n)
        old = {e["path"] for e in (load_json(bd / "scripts" / "index.json", []) if bd else [])} if bd else set()
        stores, demos = set(), []
        for path, cls, txt in files:
            name = path.split(".")[-1] if not path.endswith(".spec") else path.rsplit(".", 2)[-2] + ".spec"
            if not path.endswith(".spec") and ((words_of(name) & demo_words) or name in marked):
                demos.append(name)
                status = worse(status, soft(ctx))
                det.append(f"{n} {path}: {'marked delete-for-release by its mission' if name in marked else 'demo/test script'}"
                           f" ({cls}) ships in the build")
            for k, ln in enumerate(txt.splitlines(), 1):
                if ln.lstrip().startswith("--"):
                    continue
                for m in assign.finditer(ln):
                    ident = m.group(1).replace("_", "").lower()
                    if dname.search(ident) and not dex.search(ident):
                        status = worse(status, soft(ctx))
                        det.append(f"{n} {path}:{k}: debug flag {m.group(1)} = true")
                if blank.search(ln):
                    status = worse(status, soft(ctx))
                    det.append(f"{n} {path}:{k}: blank asset id {blank.search(ln).group(1)} (upload the asset, set the id)")
            for rx in h["store_calls"]:
                stores |= set(re.findall(rx, txt))
        mods = [(p, t) for p, cls, t in files if cls == "ModuleScript" and not p.endswith(".spec")
                and p.split(".")[-1] not in h.get("no_caller_skip", []) and (not old or p not in old)]
        lonely, demo_only = [], []
        for p, _ in mods:
            mname = p.split(".")[-1]
            rx = re.compile(rf"\b{re.escape(mname)}\b")
            callers = [q.split(".")[-1] for q, _, t in files if q != p and rx.search(t)]
            if not callers:
                lonely.append(mname)
            elif all(cl in demos for cl in callers):
                demo_only.append(f"{mname} (only {', '.join(callers)})")
        if lonely:
            status = worse(status, "WARN")
            det.append(f"{n}: {'new ' if old else ''}modules nothing in this place requires: {', '.join(lonely[:8])} "
                       "(dead code, or the feature is not wired up here)")
        if demo_only:
            status = worse(status, "WARN")
            det.append(f"{n}: modules only a demo script requires: {', '.join(demo_only[:4])} (delete the demo and "
                       "nothing calls them)")
        if stores and canon_store and canon_store not in stores:
            status = worse(status, "WARN")
            det.append(f"{n}: data stores {sorted(stores)}; canon tech.data.store_name is {canon_store}")
        test_stores = [s for s in stores if re.search(r"test|dev|debug|tmp|temp", s, re.I)]
        if test_stores:
            status = worse(status, soft(ctx))
            det.append(f"{n}: test-looking data store {test_stores}")
        if a.get("placeholders"):
            status = worse(status, soft(ctx))
            det.append(f"{n}: placeholder instances {a['placeholders'][:5]}")
        if a.get("blank_assets"):
            status = worse(status, soft(ctx))
            det.append(f"{n}: blank asset ids in properties {a['blank_assets'][:5]}")
    if any("debug flag" in d for d in det):
        fix.append("turn debug flags off before a live release (tech.security.admin); alpha may keep owner-only admin")
    if any("blank asset" in d for d in det):
        fix.append("owner uploads the assets (Asset Manager) and sets the ids, then re-attach")
    if any("ships in the build" in d for d in det):
        fix.append("owner deletes demo/test scripts from the place, saves, re-attaches")
    xs, xdet, _ = extra_lines(ctx, "G9")
    status, det = worse(status, xs), det + xdet
    return G("G9", ctx, status, (f"{len(det)} findings · " + det[0] if det
                                 else "no debug flags, demo scripts, blank assets or store-name drift")[:140], det, fix)


def g10(ctx):
    b, ch = ctx.bible, ctx.rel["channel"]
    if not b.ok:
        return G("G10", ctx, "WARN", "rr-bible not found: open questions unknown")
    words = ("release", "launch", "publish", "monetis")
    missions = [(c, mission_terms(c), b.mission_src(Path(c["mission"]["dir"]).name))
                for c in ctx.included() if c.get("mission")]
    status, det, block, touch = "PASS", [], [], []
    for q in b.open_questions():
        f = q.get("fields") or {}
        blocks, title = f.get("blocks", "").lower(), q.get("title", "")
        text = re.sub(r"[._]", " ", f"{title} {f.get('affects', '')} {blocks}".lower())
        srcs = [x.strip() for x in f.get("src", "").split(",")]
        why = [c["id"] for c, terms, sid in missions
               if (sid and sid in srcs) or any(re.search(rf"\b{re.escape(t)}\b", text) for t in terms)]
        line = f"{q['id']} {title}: default {f.get('default', '?')[:90]} (assumed)"
        if re.search(rf"\b{ch}\b", blocks) and re.search(r"release-train|channel|publish", blocks):
            block.append(q["id"])
            status = "FAIL"
            det.insert(0, f"BLOCKS the {ch} channel: {line} (blocks: {f.get('blocks')})")
        elif why:
            touch.append(q["id"])
            status = worse(status, soft(ctx))
            det.append(f"touches {', '.join(why)}: {line}" + (f" (blocks: {f['blocks']})" if f.get("blocks") else ""))
        elif any(w in f"{title} {blocks}".lower() for w in words):
            status = worse(status, "WARN")
            det.append(line)
    if status == "PASS":
        return G("G10", ctx, "PASS", "no open question blocks this channel or touches what ships")
    summ = (f"{len(block)} block the {ch} channel · " if block else "") + \
        (f"{len(touch)} touch in-build changes · " if touch else "") + f"{len(det)} open questions in play"
    return G("G10", ctx, status, summ, det[:14], ["owner: `bible decide OQ-nnn X --by owner` (or waive G10 with a "
                                                  "reason) when ready"])


def run(ctx):
    rel = ctx.rel
    gates = [fn(ctx) for fn in (g1, g2, g3, g4, g5, g6, g7, g8, g9, g10)]
    advisory = extra_lines(ctx, "G7")[2] + extra_lines(ctx, "G9")[2]
    blocking = set(ctx.presets["blocking"][rel["channel"]])
    for g in gates:
        w = rel["waivers"].get(g["id"])
        if w and g["status"] in ("FAIL", "PENDING", "WARN"):
            g["summary"] = f"waived by owner ({w['reason']}); was {g['status']}: {g['summary']}"
            g["status"] = "WAIVED"
    fail = [g for g in gates if g["status"] == "FAIL" or (g["status"] == "PENDING" and g["id"] in blocking)]
    warn = [g for g in gates if g["status"] in ("WARN", "PENDING")]
    verdict = "NO-GO" if fail else ("GO-WITH-WARNINGS" if warn else "GO")
    core_ = [(g["id"], g["status"], g["summary"], g["details"]) for g in gates]
    h = sha256_text(json.dumps([rel.get("version"), rel["channel"], core_]))
    fixes = [f"{g['id']}: {x}" for g in gates if g["status"] in ("FAIL", "PENDING", "WARN") for x in g["fix"]]
    rep = {"version": rel.get("version"), "channel": rel["channel"], "verdict": verdict, "at": now(), "hash": h,
           "gates": gates, "fixes": fixes, "advisory": advisory,
           "blockers": [g["id"] for g in fail]}
    save_json(ctx.dir / "gates.json", rep)
    L = [f"# Gates · {rel.get('version')} ({rel['channel']}) · {verdict}", "",
         f"Run {rep['at']}. Blocking in {rel['channel']}: {', '.join(sorted(blocking, key=lambda x: int(x[1:])))}. "
         "Visual judgement: multiuse-critic; security: rr-exploit-guard; approval: the owner.", "",
         "| gate | status | summary |", "|---|---|---|"]
    L += [f"| {g['id']} {g['name']} | {g['status']} | {g['summary'].replace('|', '/')} |" for g in gates]
    for g in gates:
        if g["details"] or g["fix"]:
            L += ["", f"## {g['id']} {g['name']} · {g['status']}"] + [f"- {d}" for d in g["details"]] + \
                 [f"- fix: {x}" for x in g["fix"]]
    if advisory:
        L += ["", "## Advisory: sibling library checks (not about this build; not in the verdict or approval)"] + \
             [f"- {x}" for x in advisory]
    (ctx.dir / "GATES.md").write_text("\n".join(L) + "\n")
    rel["gate"] = {"verdict": verdict, "at": rep["at"], "hash": h, "blockers": rep["blockers"]}
    ctx.save()
    return rep


if __name__ == "__main__":
    print(__doc__)
