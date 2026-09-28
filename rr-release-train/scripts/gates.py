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
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rtlib import (LEVELS, core, effective_level, find_sibling, last_release, level_between,  # noqa: E402
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
    terms = [t.strip(' "()').lower() for t in re.split(r"[,()]", v)]
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
def notes_check(ctx):
    n, rel, bible = ctx.presets["notes"], ctx.rel, ctx.bible
    by_id = {c["id"]: c for c in rel["changes"]}
    player = {c["id"] for c in ctx.included() if c["audience"] == "player"}
    errors, warnings, outputs, tagged = [], [], [], set()
    odds, buy = re.compile(n["odds_words"], re.I), re.compile(n["buy_words"], re.I)
    siding_terms = sidings(bible)

    def scan(text, fname, store=False):
        out = []
        for i, line in enumerate(text.splitlines(), 1):
            ids = [x for grp in TAG.findall(line) for x in re.findall(r"C-\d+", grp)]
            bullet = bool(re.match(r"^\s*[-*]\s+", line))
            if bullet and not ids and not store:
                errors.append(f"{fname}:{i}: bullet has no [C-n] tag (every claim must trace to a change)")
            for cid in ids:
                c = by_id.get(cid)
                if not c:
                    errors.append(f"{fname}:{i}: {cid} is not a change in this release")
                elif c.get("in_build") != "yes":
                    errors.append(f"{fname}:{i}: {cid} is not confirmed in the build (mark it or drop the line)")
                elif c["audience"] != "player":
                    errors.append(f"{fname}:{i}: {cid} is internal; players do not get internal work")
                tagged.add(cid)
            clean = re.sub(r"\s*" + TAG.pattern, "", line).rstrip()
            if odds.search(clean) and buy.search(clean):
                errors.append(f"{fname}:{i}: sells or implies odds/luck for money (D-007 never sell odds): {clean[:80]}")
            for j in n["jargon"]:
                if re.search(re.escape(j) if not j[0].isalpha() else rf"\b{re.escape(j)}", clean, re.I):
                    warnings.append(f"{fname}:{i}: internal jargon '{j}' in player text")
            for t in siding_terms:
                if t in clean.lower():
                    warnings.append(f"{fname}:{i}: names parked siding '{t}' (release.alpha.sidings): only if a change ships it")
            nums = re.findall(r"\d+(?:\.\d+)?%?", re.sub(r"\bv?\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?", "", clean))
            src_text = " ".join(by_id[x]["title"] + " " + by_id[x].get("note", "") for x in ids if x in by_id)
            for num in nums:
                if ids and num.rstrip("%") not in src_text:
                    warnings.append(f"{fname}:{i}: number {num} is not in {', '.join(ids)}; confirm it against canon")
            out.append(clean)
        return "\n".join(out).strip() + "\n"

    src = ctx.dir / "PATCH_NOTES.src.md"
    if not src.is_file():
        errors.append("PATCH_NOTES.src.md missing: `release.py notes` writes the brief; write the notes from it")
    else:
        text = scan(src.read_text(), src.name)
        (ctx.dir / "PATCH_NOTES.md").write_text(text)
        outputs.append("PATCH_NOTES.md")
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
        (ctx.dir / "STORE_UPDATE.txt").write_text(text)
        outputs.append("STORE_UPDATE.txt")
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
    missing = sorted(player - tagged, key=lambda x: int(x[2:]))
    for cid in missing:
        errors.append(f"{cid} ({by_id[cid]['title'][:60]}) is a player change the notes do not cover "
                      "(cover it, or `mark --audience internal`)")
    if not bible.ok:
        errors.append("rr-bible not found (RR_BIBLE_SKILL): canon check impossible")
    else:
        for o in outputs:
            code, findings, _ = bible.check(ctx.dir / o, skip="hex,fonts")
            for f in findings:
                (errors if f.get("level") == "ERROR" else warnings).append(f"{o}:{f.get('line')}: {f.get('msg')}")
    res = {"ok": not errors, "errors": errors, "warnings": sorted(set(warnings), key=warnings.index),
           "outputs": outputs, "changes_hash": changes_hash(ctx), "at": now()}
    save_json(ctx.dir / "notes-check.json", res)
    return res


# ---------------------------------------------------------------- gates
def G(gid, ctx, status, summary, details=None, fix=None):
    return {"id": gid, "name": ctx.presets["gate_names"][gid], "status": status, "summary": summary,
            "details": details or [], "fix": fix or []}


def soft(ctx):
    """Status for problems that block only strict channels."""
    return "FAIL" if ctx.presets["channels"][ctx.rel["channel"]]["strict"] else "WARN"


def audit_of(ctx, name):
    info = ctx.rel["places"][name]
    return load_json(ctx.dir / info["audit"], {}) or {}


def g1(ctx):
    rel, v = ctx.rel, ctx.rel.get("version")
    if not v:
        return G("G1", ctx, "PENDING", "no version", fix=["release.py version"])
    if not parse_ver(v):
        return G("G1", ctx, "FAIL", f"{v} is not semver", fix=["release.py version --set X.Y.Z-alpha.N"])
    hist = released_versions(ctx.root)
    if hist and ver_key(v) <= max(ver_key(h) for h in hist):
        return G("G1", ctx, "FAIL", f"{v} is not above released {max(hist, key=ver_key)}", fix=["release.py version"])
    status, det, fix = "PASS", [], []
    pre = parse_ver(v)[3].split(".")[0]
    if pre != ctx.channel_pre():
        status = soft(ctx)
        det.append(f"{v} does not carry channel {rel['channel']}'s tag '{ctx.channel_pre()}'")
    if not rel["places"]:
        return G("G1", ctx, "PENDING", f"{v}; no place attached", det, ["release.py attach NAME FILE"])
    for n, i in rel["places"].items():
        if i.get("stamp") is None:
            status = "FAIL" if status == "FAIL" else soft(ctx)
            det.append(f"{n}: no RR_Version stamp in the file")
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
                 fix=["release.py collect / add / mark --in-build yes"])
    if unknown:
        return G("G2", ctx, "PENDING", f"{len(unknown)} changes not confirmed in the build: {', '.join(unknown)}",
                 fix=[f"release.py mark {' '.join(unknown)} --in-build yes|no (owner knows what is in Studio)"])
    need = max((c["bump"] for c in inc), key=lambda b: LEVELS[b])
    v = rel.get("version")
    det, status = [], "PASS"
    if v and parse_ver(v):
        lives = [h for h in released_versions(ctx.root) if not parse_ver(h)[3]]
        base = max(lives, key=ver_key) if lives else "0.0.0"
        have = level_between(base, core(v))
        if LEVELS[have] < LEVELS[effective_level(need, base)]:
            status = "FAIL"
            det.append(f"{v} is a {have} step from {base}, changes need {effective_level(need, base)}")
    players = [c for c in inc if c["audience"] == "player"]
    diffs = [c for c in inc if c["src"].startswith("place:")]
    if diffs and not players:
        status = "WARN" if status == "PASS" else status
        det.append("scripts changed but no player-facing change describes them")
    return G("G2", ctx, status, f"{len(inc)} in build ({len(players)} player) · bump {need}" +
             (f" · {det[0]}" if det else ""), det, ["release.py version"] if status == "FAIL" else [])


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
    return G("G3", ctx, "WARN" if nc["warnings"] else "PASS", f"traced and covered · {len(nc['warnings'])} warnings",
             nc["warnings"][:10])


def combined_scripts(ctx, name):
    info = ctx.rel["places"][name]
    sdir = ctx.dir / Path(info["audit"]).parent / "scripts"
    idx = load_json(sdir / "index.json", []) or []
    lines, where = [], []
    for e in idx:
        f = sdir / e["file"]
        if f.is_file():
            for k, ln in enumerate(f.read_text(errors="replace").splitlines(), 1):
                lines.append(ln)
                where.append(f"{e['path']}:{k}")
    out = sdir.parent / "all_scripts.lua"
    out.write_text("\n".join(lines) + "\n")
    return out, where, idx, sdir


def g4(ctx):
    b = ctx.bible
    if not b.ok:
        return G("G4", ctx, "FAIL", "rr-bible not found", fix=["set RR_BIBLE_SKILL to the rr-bible folder"])
    if not ctx.rel["places"]:
        return G("G4", ctx, "PENDING", "no place attached", fix=["release.py attach NAME FILE"])
    status, det = "PASS", []
    off = 0
    for n in ctx.rel["places"]:
        props = ctx.dir / Path(ctx.rel["places"][n]["audit"]).parent / "props.lua"
        if props.is_file():
            _, finds, _ = b.check(props, skip="names,numbers")
            errs = [f for f in finds if f.get("level") == "ERROR"]
            off += len(errs)
            det += [f"{n} colour/font: {f['msg']}" for f in errs[:4]]
        allf, where, _, _ = combined_scripts(ctx, n)
        _, finds, _ = b.check(allf, skip="hex,fonts")
        for f in finds:
            loc = where[f["line"] - 1] if f.get("line") and f["line"] <= len(where) else "?"
            if f.get("level") == "ERROR":
                status = "FAIL"
            det.insert(0, f"{n} {loc}: {f['msg']}")
    if off and status == "PASS":
        status = "WARN"
    summ = (f"{off} off-palette colours/fonts in the places (bought or kitbashed assets are often off-token)" if off
            else "place colours and fonts on canon") + " · scripts: names and numbers " + \
        ("FAIL" if status == "FAIL" else "clean")
    return G("G4", ctx, status, summ, det[:12], ["fix the script string/number to canon, or record the change "
                                                   "with bible add-fact / decide (owner)"] if status == "FAIL" else [])


def g5(ctx):
    ev = ctx.rel["evidence"].get("security") or {}
    f = Path(ev["file"]) if ev.get("file") else ctx.dir / "security" / "SECURITY_GATE.json"
    guard = find_sibling("rr-exploit-guard", "RR_EXPLOIT_GUARD_SKILL")
    scan_dirs = " ".join(str(ctx.dir / Path(i["audit"]).parent / "scripts") for i in ctx.rel["places"].values())
    how = (f"rr-exploit-guard ({guard or 'not installed yet'}): scan {scan_dirs or '<attach places first>'} and write "
           f"{ctx.dir / 'security' / 'SECURITY_GATE.json'}")
    if not f.is_file():
        if ev.get("result"):
            st = {"pass": "PASS", "hold": soft(ctx), "fail": "FAIL"}[ev["result"]]
            return G("G5", ctx, st, f"manual security result {ev['result']} ({ev.get('by')}): {ev.get('note', '')}")
        return G("G5", ctx, "PENDING", "no security verdict", fix=[how])
    data = load_json(f, {}) or {}
    verdict = str(data.get("verdict", "")).upper()
    scanned = _ts(data.get("scanned_at"))
    newest = max((_ts(i["attached_at"]) for i in ctx.rel["places"].values()), default=None)
    if scanned and newest and scanned < newest:
        return G("G5", ctx, "PENDING", f"verdict {verdict} is older than the attached places (stale)", fix=[how])
    counts = f"blocking {len(data.get('blocking') or [])}, hold {len(data.get('hold') or [])}"
    st = {"PASS": "PASS", "HOLD": soft(ctx), "FAIL": "FAIL"}.get(verdict, "FAIL")
    det = [str(x)[:160] for x in (data.get("blocking") or [])[:5] + (data.get("hold") or [])[:5]]
    return G("G5", ctx, st, f"rr-exploit-guard {verdict or 'unreadable'} ({counts}, stage {data.get('stage', '?')})",
             det, [how] if st != "PASS" else [])


def need_kind(ctx, kind):
    spec = ctx.presets["evidence"][kind]
    if ctx.rel["channel"] not in spec["channels"]:
        return False
    return LEVELS.get(ctx.rel.get("bump", "patch"), 1) >= LEVELS[spec.get("min_bump", "none")]


def g6(ctx):
    ev, cfg, det, fix = ctx.rel["evidence"], ctx.cfg, [], []
    status = "PASS"
    t = ev.get("tests")
    if t:
        if t["result"] != "pass":
            status = "FAIL"
        det.append(f"tests {t['result']} ({t['by']}) {t.get('note', '')[:120]}")
    elif need_kind(ctx, "tests"):
        route, why = release_route(ctx)
        if cfg.get("luau_tests") and route == "api" and not why and ctx.rel["places"]:
            det.append("tests deferred: run_tests.lua runs on each saved version before publish; publish stops on a fail")
        else:
            status = "PENDING"
            det.append("no test result")
            fix.append("owner runs assets/luau/run_tests.lua in Studio (command bar, server) and records "
                       "`evidence tests --result pass --by owner --note \"N specs\"`")
    b = ev.get("bugbash")
    if b:
        status = "FAIL" if b["result"] != "pass" else status
        det.append(f"bug bash {b['result']} ({b['by']}) {b.get('note', '')[:80]}")
    elif need_kind(ctx, "bugbash"):
        status = "FAIL" if status == "FAIL" else "PENDING"
        det.append("bug bash needed (minor or bigger release): " + (ctx.bible.value("release.alpha.bug_bash") or ""))
        fix.append("owner runs the bug bash and records `evidence bugbash --result pass --by owner --note ...`")
    summ = " · ".join(d.split(":")[0] for d in det) or "no tests required"
    return G("G6", ctx, status, summ[:120], det, fix)


def run_extra(ctx, gid):
    out = []
    for x in ctx.presets.get("extra_checks", []):
        if x["gate"] != gid:
            continue
        sk = find_sibling(x["skill"])
        if not sk:
            out.append((x["name"], None, f"skipped: {x['skill']} not installed"))
            continue
        cmd = [c.replace("{python}", sys.executable).replace("{skill}", str(sk)) for c in x["cmd"]]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
            out.append((x["name"], r.returncode, " | ".join(tail)[:300]))
        except (OSError, subprocess.TimeoutExpired) as e:
            out.append((x["name"], 1, f"could not run: {e}"))
    return out


def audit_metrics(a):
    c = a.get("counts", {})
    return {"instances": a.get("instances", 0), "parts": c.get("parts", 0), "meshparts": c.get("meshparts", 0),
            "unanchored_parts": c.get("unanchored_parts", 0), "scripts": c.get("scripts", 0),
            "script_bytes": c.get("script_bytes", 0), "effects": sum((c.get("effects") or {}).values()),
            "bytes": a.get("bytes", 0)}


def g7(ctx):
    p, status, det, fix = ctx.presets["perf"], "PASS", [], []
    last = last_release(ctx.root)
    for n in ctx.rel["places"]:
        cur = audit_metrics(audit_of(ctx, n))
        prev_a = load_json(ctx.root / last["version"] / "places" / n / "audit" / "audit.json") if last else None
        if not prev_a:
            det.append(f"{n}: baseline {cur['instances']} instances, {cur['parts']} parts, {cur['script_bytes']} B scripts "
                       "(no previous audit to compare)")
            continue
        old = audit_metrics(prev_a)
        grew = [f"{m} {old[m]}->{cur[m]} (+{(cur[m] - old[m]) * 100 // max(old[m], 1)}%)" for m in p["metrics"]
                if cur[m] > old[m] and (cur[m] - old[m]) * 100 > p["warn_growth_pct"] * max(old[m], 1)]
        if grew:
            status = "WARN"
            det.append(f"{n} vs {last['version']}: " + ", ".join(grew))
            fix.append("owner: confirm on a phone (F9 memory, FPS) that the growth is fine; record `evidence perf`")
        else:
            det.append(f"{n}: no metric grew over {p['warn_growth_pct']}% vs {last['version']}")
    for name, code, tail in run_extra(ctx, "G7"):
        det.append(f"{name}: {'skipped' if code is None else ('ok' if code == 0 else 'FAILED')} {tail}")
        if code:
            status = "FAIL" if soft(ctx) == "FAIL" else ("WARN" if status == "PASS" else status)
    ev = ctx.rel["evidence"]
    for kind in ("perf", "livecheck"):
        e = ev.get(kind)
        if e and e["result"] != "pass":
            status = "FAIL"
            det.append(f"{kind} {e['result']} ({e['by']}): {e.get('note', '')}")
        elif e:
            det.append(f"{kind} pass ({e['by']}): {e.get('note', '')[:80]}")
    if not ev.get("livecheck") and need_kind(ctx, "livecheck"):
        status = "FAIL" if status == "FAIL" else "PENDING"
        det.append("live check needed: " + (ctx.bible.value("tech.streaming.live_check") or ""))
        fix.append("owner runs the live check and records `evidence livecheck --result pass --by owner --note ...`")
    return G("G7", ctx, status, (det[0] if det else "no places")[:120] + " (budgets: OQ-039 default A)", det, fix)


def g8(ctx):
    kinds = set(ctx.presets["visual_kinds"])
    vis = [c for c in ctx.included() if (c.get("mission") or {}).get("kind") in kinds]
    if not vis:
        return G("G8", ctx, "N/A", "no visual work from missions in this build")
    det, fix, bad = [], [], 0
    for c in vis:
        crit = c["mission"].get("critic") or []
        ok = [x for x in crit if x["certified"] and x["overall"] is not None and x["overall"] >= x["bar"]]
        if ok:
            det.append(f"{c['id']}: certified {ok[0]['overall']}/{ok[0]['bar']} by {', '.join(ok[0]['agents'])}")
            continue
        bad += 1
        led = "; ".join(f"{Path(x['dir']).name} {x['overall']}/{x['bar']} by {', '.join(x['agents'])}" for x in crit)
        det.append(f"{c['id']} {c['title'][:50]}: uncertified ({led or 'no critic ledger'})")
        fix.append(f"multiuse-critic: one independent --kind final pass on {c['mission']['dir']}")
    st = "PASS" if not bad else soft(ctx)
    return G("G8", ctx, st, f"{len(vis) - bad}/{len(vis)} visual changes certified by an independent critic", det, fix)


def g9(ctx):
    h, status, det, fix = ctx.presets["hygiene"], "PASS", [], []
    flag = re.compile(h["debug_flag"], re.I)
    canon_store = ctx.bible.value("tech.data.store_name")
    for n in ctx.rel["places"]:
        a = audit_of(ctx, n)
        _, where, idx, sdir = combined_scripts(ctx, n)
        stores = set()
        for e in idx:
            f = sdir / e["file"]
            if not f.is_file():
                continue
            txt = f.read_text(errors="replace")
            for k, ln in enumerate(txt.splitlines(), 1):
                if ln.lstrip().startswith("--"):
                    continue
                m = flag.search(ln)
                if m:
                    status = soft(ctx) if status != "FAIL" else status
                    det.append(f"{n} {e['path']}:{k}: debug flag {m.group(1)} = true")
            for rx in h["store_calls"]:
                stores |= set(re.findall(rx, txt))
        if stores and canon_store and canon_store not in stores:
            status = "WARN" if status == "PASS" else status
            det.append(f"{n}: data stores {sorted(stores)}; canon tech.data.store_name is {canon_store}")
        test_stores = [s for s in stores if re.search(r"test|dev|debug|tmp|temp", s, re.I)]
        if test_stores:
            status = soft(ctx) if status != "FAIL" else status
            det.append(f"{n}: test-looking data store {test_stores}")
        if a.get("placeholders"):
            status = soft(ctx) if status != "FAIL" else status
            det.append(f"{n}: placeholder instances {a['placeholders'][:5]}")
    if any("debug flag" in d for d in det):
        fix.append("turn debug flags off before a live release (tech.security.admin); alpha may keep owner-only admin")
    for name, code, tail in run_extra(ctx, "G9"):
        det.append(f"{name}: {'skipped' if code is None else ('ok' if code == 0 else 'FAILED')} {tail}")
        if code:
            status = soft(ctx) if status != "FAIL" else status
    return G("G9", ctx, status, (det[0] if det else "no debug flags, placeholders or store-name drift")[:120], det, fix)


def g10(ctx):
    words = ("release", "launch", "publish", "monetis")
    qs = ctx.bible.questions_about(words) if ctx.bible.ok else []
    qs = [q for q in qs if any(w in (q.get("title", "") + " " + (q.get("fields") or {}).get("blocks", "")).lower()
                               for w in words)]
    if not qs:
        return G("G10", ctx, "PASS", "no open question blocks releasing")
    det = [f"{q['id']} {q['title']}: default {(q.get('fields') or {}).get('default', '?')} (assumed)" for q in qs]
    return G("G10", ctx, "WARN", f"{len(qs)} open questions touch releasing; their defaults are in use", det,
             ["owner: `bible decide OQ-nnn X --by owner` when ready"])


def run(ctx):
    rel = ctx.rel
    gates = [fn(ctx) for fn in (g1, g2, g3, g4, g5, g6, g7, g8, g9, g10)]
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
    h = sha256_text(json.dumps([rel.get("version"), core_]))
    fixes = [f"{g['id']}: {x}" for g in gates if g["status"] in ("FAIL", "PENDING", "WARN") for x in g["fix"]]
    rep = {"version": rel.get("version"), "channel": rel["channel"], "verdict": verdict, "at": now(), "hash": h,
           "gates": gates, "fixes": fixes}
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
    (ctx.dir / "GATES.md").write_text("\n".join(L) + "\n")
    rel["gate"] = {"verdict": verdict, "at": rep["at"], "hash": h}
    ctx.save()
    return rep


if __name__ == "__main__":
    print(__doc__)
