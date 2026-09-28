#!/usr/bin/env python3
"""rr-skill-smith health: the JARVIS web health report (per-skill status, scores, cost trends, open frictions,
contract drift, recurring problems). Zero model tokens: it runs harvest, drift and the quick evals itself.

Usage:
  health.py [--root R] [--home H] [--no-evals] [--no-scan] [--out-dir D] [--json]

Writes <home>/health.html (self-contained page, light/dark, phone-width), <home>/health.md (compact, for the model:
read this, not the html) and <home>/health.json, and appends a snapshot to <home>/history.jsonl for trends.
Status per skill: critical = failing eval or regression, drift ERROR, open High friction, latest independent critic
below 6, or a VULN in the latest independent security review; warning = below the 8/10 bar, drift WARN, only
self-assessed scores, trigger proxy under 80%, no evals, or High fixes claimed but unverified; good otherwise.
"""
import sys

sys.dont_write_bytecode = True
import argparse
import html
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smithlib as L  # noqa: E402
import harvest  # noqa: E402
import drift  # noqa: E402
import evals  # noqa: E402

BAR = 8


def gather(root, home, skills, run_evals=True, rescan=True):
    if rescan or not (home / "frictions.json").exists():
        harvest.scan(root, home, skills)
    fr = L.load_json(home / "frictions.json", {})
    sc = L.load_json(home / "scores.json", {})
    cl = (L.load_json(home / "clusters.json", {}) or {}).get("clusters", [])
    findings = drift.run(root, skills)
    L.save_json(home / "drift.json", {"checked": L.now(), "summary": drift.summary(findings), "findings": findings})
    ev = {}
    root_skills = sorted(n for n, s in skills.items() if s["origin"] == "root")
    if run_evals:
        router = evals.Router(evals.web_descs(root))
        for n in root_skills:
            out = evals.run_skill(n, Path(skills[n]["dir"]), root, home, skills, {"builtin", "checks", "triggers"},
                                  quick=True, router=router)
            evals.save_run(home, out)
            ev[n] = out
    else:
        for n in root_skills:
            ev[n] = L.load_json(home / "evals" / f"{n}.last.json")
    hist = []
    hp = home / "history.jsonl"
    if hp.exists():
        for line in L.read(hp).splitlines():
            try:
                hist.append(json.loads(line))
            except ValueError:
                pass
    rows = []
    for n in sorted(skills):
        s = skills[n]
        items = [i for i in fr.get("items", []) if i["skill"] == n]
        crit = sorted([x for x in sc.get("scores", []) if x["skill"] == n and x["kind"] == "critic"],
                      key=lambda x: (x["date"], x.get("pass") or 0))
        indep = [x for x in crit if x["independent"]]
        review = [x for x in sc.get("scores", []) if x["skill"] == n and x["kind"] == "review"]
        sec = sorted([x for x in sc.get("scores", []) if x["skill"] == n and x["kind"] == "security" and x["independent"]],
                     key=lambda x: x["date"])
        costs = [x for x in sc.get("costs", []) if x["skill"] == n]
        dr = [f for f in findings if f["skill"] == n]
        e = ev.get(n) or {}
        res = e.get("results", [])
        ver = L.version_of(s["dir"])[0]
        r = {"skill": n, "origin": s["origin"], "version": ver if ver != "0.0.0" else "unversioned",
             "skill_md_tokens": L.toks(s["skill_md_chars"]), "desc_chars": len(s["desc"]),
             "open": sum(1 for i in items if i["status"] == "open"),
             "open_h": sum(1 for i in items if i["status"] == "open" and i["sev"] == "H"),
             "claimed": sum(1 for i in items if i["status"] == "claimed"),
             "claimed_h": sum(1 for i in items if i["status"] == "claimed" and i["sev"] == "H"),
             "partial": sum(1 for i in items if i["status"] == "partial"),
             "fixed": sum(1 for i in items if i["status"] == "fixed"),
             "critic_last": indep[-1]["overall"] if indep else None,
             "critic_last_src": indep[-1]["source"] if indep else "",
             "critic_self_only": bool(crit) and not indep,
             "critic_series": [[x["date"], x["overall"], x["independent"], x["source"]] for x in crit][-12:],
             "review": review[-1]["values"] if review else None,
             "missed": sum(x["new"] for x in sec if x["date"] == sec[-1]["date"]) if sec else None,
             "missed_high": sum(x.get("new_high", 0) for x in sec if x["date"] == sec[-1]["date"]) if sec else None,
             "critic_tokens": sum(x["tokens"] for x in costs if x["kind"] == "critic"),
             "mission_tokens": sum(x["tokens"] for x in costs if x["kind"] == "mission"),
             "tokens_estimated": any(x.get("estimated") for x in costs),
             "drift_error": sum(1 for f in dr if f["level"] == "ERROR"),
             "drift_warn": sum(1 for f in dr if f["level"] == "WARN"),
             "evals_ok": e.get("ok") if e else None, "evals_missing": e.get("missing_evals") if e else None,
             "checks_pass": sum(1 for x in res if x.get("pass")), "checks_total": sum(1 for x in res if x.get("pass") is not None),
             "eval_fails": [x["id"] for x in res if x.get("pass") is False], "regressions": e.get("regressions", []) if e else [],
             "trigger_acc": e.get("trigger_acc") if e else None,
             "clusters": [c for c in cl if c["skill"] == n][:3]}
        prev = next((h["skills"].get(n) for h in reversed(hist) if n in h.get("skills", {})), None)
        r["skill_md_tokens_prev"] = prev.get("skill_md_tokens") if prev else None
        r["md_series"] = [h["skills"][n]["skill_md_tokens"] for h in hist if n in h.get("skills", {})][-11:] + \
            [r["skill_md_tokens"]]
        status(r)
        rows.append(r)
    web = {}
    for c in cl:
        if len(c["web_skills"]) > 1:
            web.setdefault(c["theme"], {"title": c["title"], "fix": c["fix"], "skills": c["web_skills"], "n": 0})
            web[c["theme"]]["n"] += c["n"]
    snap = {"when": L.now(), "skills": {r["skill"]: {k: r[k] for k in ("version", "skill_md_tokens", "open", "open_h",
                                                                        "claimed", "drift_error", "drift_warn",
                                                                        "critic_last", "trigger_acc", "evals_ok",
                                                                        "critic_tokens", "status")} for r in rows}}
    with hp.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(snap) + "\n")
    open_h = sorted([i for i in fr.get("items", []) if i["status"] == "open" and i["sev"] == "H"],
                    key=lambda i: i["skill"])
    drift_top = sorted([f for f in findings if f["level"] != "INFO"],
                       key=lambda f: (drift.LEVELS[f["level"]], f["skill"], f["file"], f["line"]))
    return {"when": L.now(), "root": str(root), "rows": rows, "web_themes": web, "open_h": open_h,
            "drift": drift_top, "snapshots": len(hist) + 1,
            "sources": len(fr.get("sources", [])), "items": len(fr.get("items", []))}


def status(r):
    crit, warn = [], []
    if r["origin"] == "root" and r["evals_ok"] is False:
        crit.append("eval fail: " + ", ".join((r["regressions"] or r["eval_fails"])[:3]))
    if r["drift_error"]:
        crit.append(f"{r['drift_error']} drift ERROR")
    if r["open_h"]:
        crit.append(f"{r['open_h']} open High friction")
    if r["critic_last"] is not None and r["critic_last"] < 6:
        crit.append(f"critic {r['critic_last']:g}/10")
    if r["missed_high"]:
        crit.append(f"independent review found {r['missed_high']} High issue(s) the skill missed")
    if r["critic_last"] is not None and 6 <= r["critic_last"] < BAR:
        warn.append(f"critic {r['critic_last']:g} < bar {BAR}")
    if r["critic_self_only"]:
        warn.append("self-assessed scores only")
    if r["drift_warn"]:
        warn.append(f"{r['drift_warn']} drift WARN")
    if r["trigger_acc"] is not None and r["trigger_acc"] < 0.8:
        warn.append(f"triggers {r['trigger_acc']:.0%}")
    if r["origin"] == "root" and r["evals_missing"]:
        warn.append("no evals")
    if r["claimed_h"]:
        warn.append(f"{r['claimed_h']} High fix(es) claimed, unverified")
    if r["missed"] and not r["missed_high"]:
        warn.append(f"independent review found {r['missed']} issue(s) the skill missed")
    if r["open"] - r["open_h"] >= 3:
        warn.append(f"{r['open'] - r['open_h']} open Medium/Low frictions")
    r["status"] = "critical" if crit else ("warning" if warn else "good")
    r["reasons"] = crit + warn
    if r["origin"] != "root":
        r["next"] = "installed copy: fix at its source"
    elif r["evals_ok"] is False:
        r["next"] = f"fix eval {(r['regressions'] or r['eval_fails'])[0]}"
    elif r["drift_error"]:
        r["next"] = f"drift.py {r['skill']}: fix the ERROR lines"
    elif r["open_h"] or (r["clusters"] and r["clusters"][0]["open"]):
        r["next"] = f"harvest.py patch {r['skill']}"
    elif r["critic_last"] is not None and r["critic_last"] < BAR:
        r["next"] = "bar loop: fix verdict issues, fresh critic"
    elif r["missed"]:
        r["next"] = "teach the scanner the reviewer's NEW findings; re-review"
    elif r["claimed_h"]:
        r["next"] = "add evals that prove the claimed High fixes"
    elif r["drift_warn"]:
        r["next"] = f"drift.py {r['skill']}: cite keys instead of values"
    else:
        r["next"] = "-"


# ---------------------------------------------------------------- markdown (for the model)
def fmt_score(r):
    if r["critic_last"] is not None:
        return f"{r['critic_last']:g}"
    if r["missed"] is not None:
        return f"missed {r['missed']}" + (f" ({r['missed_high']}H)" if r["missed_high"] else "")
    if r["critic_self_only"]:
        return "self only"
    return f"rev {min(r['review']):g}" if r["review"] else "-"


def render_md(d):
    rows = []
    for r in d["rows"]:
        tr = f"{r['trigger_acc']:.0%}" if r["trigger_acc"] is not None else "-"
        ev = f"{r['checks_pass']}/{r['checks_total']}" if r["checks_total"] else "-"
        delta = ""
        if r["skill_md_tokens_prev"] is not None and r["skill_md_tokens_prev"] != r["skill_md_tokens"]:
            delta = f" ({r['skill_md_tokens'] - r['skill_md_tokens_prev']:+d})"
        rows.append([r["skill"], r["status"], r["version"], fmt_score(r), ev, tr, f"{r['drift_error']}/{r['drift_warn']}",
                     f"{r['open']} ({r['open_h']}H) +{r['claimed']}c", f"{r['skill_md_tokens']}{delta}", r["next"]])
    out = [f"# JARVIS web health ({d['when']})", "",
           f"{sum(r['status'] == 'critical' for r in d['rows'])} critical, {sum(r['status'] == 'warning' for r in d['rows'])} "
           f"warning, {sum(r['status'] == 'good' for r in d['rows'])} good; {d['items']} friction items from "
           f"{d['sources']} logs; snapshot {d['snapshots']}.", "",
           L.md_table(["skill", "status", "ver", "critic", "evals", "trig", "drift E/W", "frictions open (H) +claimed",
                       "SKILL.md tok", "next"], rows), ""]
    if d["web_themes"]:
        out.append("## Web-wide recurring problems (fix once, in the owning skill)")
        for t, w in sorted(d["web_themes"].items(), key=lambda kv: -len(kv[1]["skills"])):
            out.append(f"- {w['title']} [{t}]: {len(w['skills'])} skills, {w['n']} items. Fix: {w['fix']}")
        out.append("")
    if d["open_h"]:
        out.append("## Open High frictions")
        out += [f"- {i['id']} ({i['skill']}): {i['title'][:120]}" for i in d["open_h"][:12]]
        out.append("")
    if d["drift"]:
        out.append(f"## Contract drift ({len(d['drift'])} ERROR/WARN; first 15)")
        out += [f"- {f['level']} {f['skill']} {f['file']}:{f['line']} {f['msg'][:120]}" for f in d["drift"][:15]]
        out.append("")
    out.append("Reasons per skill: health.json rows[].reasons. Detail: harvest.py clusters --skill S; drift.py S; "
               "evals.py run S -v.")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- html (for the owner)
CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink-2:#52514e;--muted:#898781;
--grid:#e1e0d9;--axis:#c3c2b7;--ring:rgba(11,11,11,.10);--accent:#2a78d6;--good:#0ca30c;--warning:#fab219;
--critical:#d03b3b;--chip:#f0efec}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;
--ink:#fff;--ink-2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--ring:rgba(255,255,255,.10);--accent:#3987e5;
--chip:#262624}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink-2:#c3c2b7;--muted:#898781;
--grid:#2c2c2a;--axis:#383835;--ring:rgba(255,255,255,.10);--accent:#3987e5;--chip:#262624}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1280px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:28px 0 10px}
.sub{color:var(--ink-2);margin:0 0 18px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:8px}
.tile{background:var(--surface);border:1px solid var(--ring);border-radius:10px;padding:12px 14px}
.tile .l{color:var(--ink-2);font-size:12px}.tile .v{font-size:26px;font-weight:600}
.tile.hero .v{font-size:48px;line-height:1.1}
.wrap{overflow-x:auto;background:var(--surface);border:1px solid var(--ring);border-radius:10px}
table{border-collapse:collapse;width:100%;min-width:980px}
td.sk{white-space:nowrap}td.wide{min-width:200px}
th,td{text-align:left;padding:8px 8px;border-bottom:1px solid var(--grid);vertical-align:top}
th{font-size:12px;color:var(--ink-2);font-weight:600}
th .why{font-weight:400;margin:0;white-space:nowrap}
td.n{font-variant-numeric:tabular-nums;white-space:nowrap}
tr:last-child td{border-bottom:0}
.chip{display:inline-flex;align-items:center;gap:6px;white-space:nowrap;font-weight:600}
.dot{width:16px;height:16px;border-radius:50%;display:inline-grid;place-items:center;font-size:11px;color:#fff;font-weight:700}
.dot.good{background:var(--good)}.dot.warning{background:var(--warning);color:#0b0b0b}.dot.critical{background:var(--critical)}
.why{color:var(--ink-2);font-size:12px;margin-top:2px}
.muted{color:var(--muted)}
.list{background:var(--surface);border:1px solid var(--ring);border-radius:10px;padding:4px 14px;margin:0}
.list li{list-style:none;padding:8px 0;border-bottom:1px solid var(--grid)}.list li:last-child{border-bottom:0}
code{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--chip);padding:1px 4px;border-radius:4px}
svg.spark{display:block;overflow:visible}
svg.spark .line{fill:none;stroke:var(--muted);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
svg.spark .base{stroke:var(--grid);stroke-width:1}
svg.spark .end{fill:var(--accent);stroke:var(--surface);stroke-width:2}
svg.spark .self{fill:var(--surface);stroke:var(--muted);stroke-width:2}
svg.spark .hit{fill:transparent}
footer{color:var(--muted);font-size:12px;margin-top:28px}
@media (max-width:700px){table{min-width:0}thead{display:none}table,tbody,tr,td{display:block}
tr{padding:10px 12px;border-bottom:1px solid var(--grid)}tr:last-child{border-bottom:0}
td{border:0;padding:2px 0}td.wide{min-width:0}td.sk{white-space:normal}
td[data-l]::before{content:attr(data-l) ": ";color:var(--ink-2);font-size:12px}
td.n svg.spark{display:inline-block;vertical-align:middle;margin-left:8px}}
"""


def esc(x):
    return html.escape(str(x), quote=True)


def rich(x):
    """escape, then `code` spans"""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(x))


def spark(points, lo=0, hi=10, w=96, h=26, fmt="{:g}"):
    """points: [(label, value, filled)] -> inline svg; single series, last point in the accent."""
    if not points:
        return '<span class="muted">-</span>'
    vals = [p[1] for p in points]
    if hi is None:
        lo, hi = min(vals), max(vals)
        if lo == hi:
            lo, hi = lo - 1, hi + 1
    n = len(points)
    xs = [4 + (w - 8) * (i / (n - 1) if n > 1 else 0.5) for i in range(n)]
    ys = [h - 4 - (h - 8) * ((v - lo) / (hi - lo)) for v in vals]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(zip(xs, ys)))
    parts = [f'<svg class="spark" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
             f'aria-label="trend: {esc(", ".join(fmt.format(v) for v in vals))}">',
             f'<line class="base" x1="0" x2="{w}" y1="{h - 1}" y2="{h - 1}"/>']
    if n > 1:
        parts.append(f'<path class="line" d="{path}"/>')
    for i, (x, y) in enumerate(zip(xs, ys)):
        label, v, filled = points[i]
        tip = esc(f"{label}: {fmt.format(v)}")
        if i == n - 1:
            parts.append(f'<circle class="{"end" if filled else "self"}" cx="{x:.1f}" cy="{y:.1f}" r="4"/>')
        parts.append(f'<circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="9"><title>{tip}</title></circle>')
    parts.append("</svg>")
    return "".join(parts)


def render_html(d):
    rows = d["rows"]
    n_crit = sum(r["status"] == "critical" for r in rows)
    n_warn = sum(r["status"] == "warning" for r in rows)
    open_h = sum(r["open_h"] for r in rows)
    derr = sum(r["drift_error"] for r in rows)
    dwarn = sum(r["drift_warn"] for r in rows)
    ev_ok = sum(1 for r in rows if r["evals_ok"])
    ev_n = sum(1 for r in rows if r["evals_ok"] is not None)
    show_ctok = any(r["critic_tokens"] for r in rows)
    icon = {"good": "&#10003;", "warning": "!", "critical": "&#10005;"}
    label = {"good": "Good", "warning": "Watch", "critical": "Act"}
    body = [f'<main><h1>JARVIS web health</h1><p class="sub">{esc(d["when"])} · {len(rows)} skills · '
            f'{d["items"]} friction items from {d["sources"]} logs · snapshot {d["snapshots"]}. '
            'Proposals only: nothing here ships without the owner.</p>',
            '<div class="kpis">',
            f'<div class="tile hero"><div class="l">Skills that need action</div><div class="v">{n_crit}</div>'
            f'<div class="l">{n_warn} to watch</div></div>',
            f'<div class="tile"><div class="l">Open High frictions</div><div class="v">{open_h}</div></div>',
            f'<div class="tile"><div class="l">Contract drift (error / warn)</div><div class="v">{derr} / {dwarn}</div></div>',
            f'<div class="tile"><div class="l">Skills passing evals</div><div class="v">{ev_ok} / {ev_n}</div></div>',
            "</div>", "<h2>Skills</h2>", '<div class="wrap"><table>',
            "<thead><tr><th>Skill</th><th>Status</th><th>Why, and the next move</th><th>Critic</th>"
            "<th>Evals · trig.</th><th>Drift<div class=why>error / warn</div></th>"
            "<th>Frictions<div class=why>open (High) / claimed</div></th><th>SKILL.md<div class=why>tokens</div></th>" + ("<th>Critic tokens</th>" if show_ctok else "") + "</tr></thead><tbody>"]
    for r in rows:
        pts = [(f"{s[0]} {Path(s[3]).parent.name}{'' if s[2] else ' (self)'}", s[1], s[2]) for s in r["critic_series"]]
        score = fmt_score(r)
        md_pts = [(f"snapshot {i + 1}", v, True) for i, v in enumerate(r["md_series"])]
        delta = ""
        if r["skill_md_tokens_prev"] is not None and r["skill_md_tokens_prev"] != r["skill_md_tokens"]:
            delta = f' <span class="muted">({r["skill_md_tokens"] - r["skill_md_tokens_prev"]:+d})</span>'
        ev = f"{r['checks_pass']}/{r['checks_total']}" if r["checks_total"] else '<span class="muted">-</span>'
        tr = f"{r['trigger_acc']:.0%}" if r["trigger_acc"] is not None else '<span class="muted">-</span>'
        ctok = (f"{r['critic_tokens']:,}" + (" est." if r["tokens_estimated"] else "")) if r["critic_tokens"] else \
            '<span class="muted">-</span>'
        why = "; ".join(r["reasons"][:3]) or "no open issues"
        body.append(
            f'<tr><td class="sk"><b>{esc(r["skill"])}</b><div class="why">{esc(r["version"])}'
            f'{" · installed copy" if r["origin"] != "root" else ""}</div></td>'
            f'<td><span class="chip"><span class="dot {r["status"]}" aria-hidden="true">{icon[r["status"]]}</span>'
            f'{label[r["status"]]}</span></td>'
            f'<td class="wide">{esc(why)}<div class="why">Next: {rich(r["next"])}</div></td>'
            f'<td class="n" data-l="Critic"><b>{esc(score)}</b>{spark(pts) if len(pts) > 1 else ""}</td>'
            f'<td class="n" data-l="Evals · triggers">{ev + " · " + tr if r["checks_total"] else ev}</td>'
            f'<td class="n" data-l="Drift error / warn">{r["drift_error"]} / {r["drift_warn"]}</td>'
            f'<td class="n" data-l="Frictions open (High) / claimed">{r["open"]} ({r["open_h"]}) / {r["claimed"]}</td>'
            f'<td class="n" data-l="SKILL.md tokens">{r["skill_md_tokens"]:,}{delta}'
            f'{spark(md_pts, hi=None, fmt="{:,.0f}") if len(md_pts) > 1 else ""}</td>'
            + (f'<td class="n" data-l="Critic tokens">{ctok}</td>' if show_ctok else "") + '</tr>')
    body.append("</tbody></table></div>")
    if d["web_themes"]:
        body.append("<h2>Recurring across skills</h2><ul class='list'>")
        for t, w in sorted(d["web_themes"].items(), key=lambda kv: -len(kv[1]["skills"])):
            body.append(f"<li><b>{esc(w['title'])}</b> <span class='muted'>({len(w['skills'])} skills, {w['n']} items: "
                        f"{esc(', '.join(w['skills']))})</span><div class='why'>Fix once: {rich(w['fix'])}</div></li>")
        body.append("</ul>")
    if d["open_h"]:
        body.append("<h2>Open High frictions</h2><ul class='list'>")
        for i in d["open_h"][:20]:
            body.append(f"<li><code>{esc(i['id'])}</code> <b>{esc(i['skill'])}</b>: {esc(i['title'][:160])}</li>")
        body.append("</ul>")
    if d["drift"]:
        body.append("<h2>Contract drift</h2><ul class='list'>")
        for f in d["drift"][:30]:
            body.append(f"<li><b>{esc(f['level'])}</b> {esc(f['skill'])} <code>{esc(f['file'])}:{f['line']}</code> "
                        f"{rich(f['msg'][:160])}<div class='why'>{rich(f['fix'])}</div></li>")
        if len(d["drift"]) > 30:
            body.append(f"<li class='muted'>{len(d['drift']) - 30} more in health.json</li>")
        body.append("</ul>")
    body.append("<footer>Generated by rr-skill-smith health.py. Critic scores: latest independent critic (filled dot); "
                "hollow dot = self-assessed. Trigger % is a lexical proxy; run evals.py live for the real test. "
                "Token figures marked est. are estimates.</footer></main>")
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' "
            "content='width=device-width,initial-scale=1'><title>JARVIS Web Health</title><style>" + CSS +
            "</style></head><body>" + "\n".join(body) + "</body></html>\n")


def main(argv=None):
    ap = L.common_args(argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter))
    ap.add_argument("--no-evals", action="store_true", help="use the last eval results instead of running quick evals")
    ap.add_argument("--no-scan", action="store_true", help="reuse the last harvest")
    ap.add_argument("--out-dir", help="where to write health.* (default <home>)")
    ap.add_argument("--json", action="store_true", help="print health.json instead of the summary")
    a = ap.parse_args(argv)
    root = L.find_root(a.root)
    home = L.ensure_home(L.smith_home(root, a.home))
    skills = L.web(root)
    d = gather(root, home, skills, run_evals=not a.no_evals, rescan=not a.no_scan)
    out = Path(a.out_dir).resolve() if a.out_dir else home
    out.mkdir(parents=True, exist_ok=True)
    L.save_json(out / "health.json", d)
    md = render_md(d)
    (out / "health.md").write_text(md, encoding="utf-8")
    (out / "health.html").write_text(render_html(d), encoding="utf-8")
    if a.json:
        print(json.dumps(d, indent=1))
    else:
        print(md.split("\n## ")[0].rstrip())
        print(f"\nwrote {out / 'health.html'}, {out / 'health.md'}, {out / 'health.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
