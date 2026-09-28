#!/usr/bin/env python3
"""rr-skill-smith evals: per-skill regression evals, run before any new version ships.

Usage:
  evals.py [--root R] [--home H] run SKILL|all [--dir CANDIDATE] [--only builtin,checks,triggers] [--quick]
                                  [--save-baseline] [--json]
  evals.py triggers [--skill S] [--top 3]     route every trigger prompt across the web (lexical proxy)
  evals.py init SKILL                         write <skill>/evals/evals.json skeleton (never overwrites)
  evals.py live SKILL [--out F]               write a skill-creator eval set + print the run_eval command (costs tokens)
  evals.py agent SKILL                        write the grading brief for the model-graded "evals" items
  evals.py record SKILL RESULTS.json          store model-graded results ({"results": [{"id", "pass", "evidence"}]})

Evals live in <skill>/evals/evals.json (skill-creator schema, not packaged):
  {"skill_name": S, "budget": {"skill_md_max_lines": N, "skill_md_max_chars": N},
   "triggers": [{"query": "...", "should_trigger": true, "k": 1}],
   "checks": [{"id": "...", "run": "python3 {skill}/scripts/x.py ...", "exit": 0, "stdout_has": [], "stdout_not": [],
               "stdout_re": "", "timeout": 120, "slow": false, "covers": ["t:rr-x#4"]}],
   "evals": [{"id": 1, "prompt": "...", "expected_output": "...", "expectations": ["..."]}]}
Placeholders in "run": {skill} (the candidate folder), {root}, {bible}, {critic}, {home}, {tmp} (fresh temp dir,
also the cwd). Checks run with PYTHONDONTWRITEBYTECODE=1 and must not change the skill folder (hygiene fails if so).
Built-in checks on every skill: validate (skill-creator quick_validate), lean (SKILL.md size vs budget and baseline
+10%), hygiene (no __pycache__, tree unchanged by the checks), drift (no ERROR, WARN not above baseline).
Triggers: a lexical router (BM25 over every installed skill's description) must rank the skill first for
should_trigger prompts and not first for the others. It is a cheap proxy; `live` runs the real test.
Exit 1 on any failing check or trigger regression (vs <home>/baselines/<skill>.json).
"""
import sys

sys.dont_write_bytecode = True
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smithlib as L  # noqa: E402

HARD_MAX_LINES = 500


# ---------------------------------------------------------------- lexical trigger router
def terms(text):
    words = []
    for w in re.findall(r"[a-z][a-z0-9]+", text.lower().replace("-", " ")):
        if len(w) < 3 or w in L.STOP:
            continue
        for suf in ("ing", "ed", "es", "s"):
            if w.endswith(suf) and len(w) - len(suf) >= 4:
                w = w[: -len(suf)]
                break
        words.append(w)
    return words + [a + "_" + b for a, b in zip(words, words[1:])]


class Router:
    def __init__(self, descs):
        self.docs = {n: terms(n.replace("-", " ") + " " + d) for n, d in descs.items()}
        self.N = len(self.docs)
        self.avg = sum(len(t) for t in self.docs.values()) / max(1, self.N)
        df = {}
        for t in self.docs.values():
            for w in set(t):
                df[w] = df.get(w, 0) + 1
        self.idf = {w: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for w, n in df.items()}

    def rank(self, query):
        q = set(terms(query))
        out = []
        for name, t in self.docs.items():
            tf = {}
            for w in t:
                if w in q:
                    tf[w] = tf.get(w, 0) + 1
            s = sum(self.idf[w] * f * 2.2 / (f + 1.2 * (0.25 + 0.75 * len(t) / self.avg)) for w, f in tf.items())
            if name in query.lower():
                s += 10
            out.append((round(s, 2), name))
        out.sort(reverse=True)
        return out


def web_descs(root, override=None):
    descs = {n: s["desc"] for n, s in L.web(root, include_all_installed=True).items()}
    if override:
        descs.update(override)
    return descs


def run_triggers(ev, name, router):
    res = []
    for i, t in enumerate(ev.get("triggers", [])):
        ranked = router.rank(t["query"])
        pos = next((k for k, (_, n) in enumerate(ranked, 1) if n == name), 99)
        score = next((s for s, n in ranked if n == name), 0)
        k = int(t.get("k", 1))
        ok = (pos <= k and score > 0) if t["should_trigger"] else pos != 1
        res.append({"id": f"trigger:{i}", "query": t["query"], "should": t["should_trigger"], "rank": pos,
                    "top": ranked[0][1], "pass": ok})
    return res


# ---------------------------------------------------------------- checks
def subst(cmd, ctx):
    for k, v in ctx.items():
        cmd = cmd.replace("{" + k + "}", str(v))
    return cmd


def run_check(ch, ctx):
    tmp = Path(tempfile.mkdtemp(prefix="smith-eval-"))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", RR_SMITH_EVAL="1")
    cmd = subst(ch["run"], dict(ctx, tmp=tmp))
    t0 = time.time()
    try:
        r = subprocess.run(cmd, shell=True, cwd=tmp, capture_output=True, text=True, env=env,
                           timeout=int(ch.get("timeout", 120)))
        out, code = (r.stdout or "") + (r.stderr or ""), r.returncode
    except subprocess.TimeoutExpired:
        out, code = "TIMEOUT", -9
    dt = time.time() - t0
    shutil.rmtree(tmp, ignore_errors=True)
    why = []
    if code != int(ch.get("exit", 0)):
        why.append(f"exit {code} != {ch.get('exit', 0)}")
    for s in ch.get("stdout_has", []):
        if s not in out:
            why.append(f"missing '{s}'")
    for s in ch.get("stdout_not", []):
        if s in out:
            why.append(f"has '{s}'")
    if ch.get("stdout_re") and not re.search(ch["stdout_re"], out, re.M):
        why.append(f"no match /{ch['stdout_re']}/")
    if ch.get("max_seconds") and dt > ch["max_seconds"]:
        why.append(f"took {dt:.0f}s > {ch['max_seconds']}s")
    tail = " | ".join(x for x in out.strip().splitlines()[-3:])[:300]
    return {"id": ch["id"], "pass": not why, "why": "; ".join(why), "seconds": round(dt, 1), "tail": tail,
            "covers": ch.get("covers", [])}


def builtin_checks(name, d, ev, base, root, skills):
    res = []
    ok, msg = L.quick_validate(d)
    res.append({"id": "builtin:validate", "pass": ok, "why": "" if ok else msg, "tail": msg})
    text = L.read(Path(d) / "SKILL.md")
    lines, chars = text.count("\n") + 1, len(text)
    bud = ev.get("budget", {})
    why = []
    if lines > HARD_MAX_LINES:
        why.append(f"{lines} lines > {HARD_MAX_LINES}")
    if bud.get("skill_md_max_lines") and lines > bud["skill_md_max_lines"]:
        why.append(f"{lines} lines > budget {bud['skill_md_max_lines']}")
    if bud.get("skill_md_max_chars") and chars > bud["skill_md_max_chars"]:
        why.append(f"{chars} chars > budget {bud['skill_md_max_chars']}")
    b_chars = (base or {}).get("metrics", {}).get("skill_md_chars")
    if b_chars and chars > b_chars * 1.10 and not bud.get("skill_md_max_chars"):
        why.append(f"SKILL.md grew {chars - b_chars} chars (> 10% over baseline {b_chars})")
    res.append({"id": "builtin:lean", "pass": not why, "why": "; ".join(why),
                "tail": f"{lines} lines, {chars} chars (~{L.toks(chars)} tokens)"})
    import drift  # noqa: E402  (sibling script)
    fs = [f for f in drift.run(root, skills, {name}, None, {name: str(d)}) if f["skill"] == name]
    err = [f for f in fs if f["level"] == "ERROR"]
    warn = sum(1 for f in fs if f["level"] == "WARN")
    b_warn = (base or {}).get("metrics", {}).get("drift_warn")
    why = [f"{len(err)} ERROR: " + "; ".join(f"{f['file']}:{f['line']} {f['msg']}" for f in err[:3])] if err else []
    if b_warn is not None and warn > b_warn:
        why.append(f"drift WARN {warn} > baseline {b_warn}")
    res.append({"id": "builtin:drift", "pass": not why, "why": "; ".join(why), "tail": f"{len(err)} ERROR, {warn} WARN"})
    return res, {"skill_md_lines": lines, "skill_md_chars": chars, "drift_warn": warn, "drift_error": len(err)}


# ---------------------------------------------------------------- run
def eval_file(d):
    return Path(d) / "evals" / "evals.json"


def load_eval(d, name):
    ev = L.load_json(eval_file(d))
    if ev is None:
        return {"skill_name": name, "triggers": [], "checks": [], "evals": [], "_missing": True}
    return ev


def run_skill(name, d, root, home, skills, only, quick, router=None):
    ev = load_eval(d, name)
    base = L.load_json(home / "baselines" / f"{name}.json")
    junk_before = L.junk_in(d)
    h0 = L.tree_hash(d)
    res, metrics = [], {}
    if "builtin" in only:
        b, metrics = builtin_checks(name, d, ev, base, root, skills)
        res += b
    if "checks" in only:
        ctx = {"skill": Path(d).resolve(), "root": root, "bible": root / "rr-bible", "critic": root / "multiuse-critic",
               "home": home}
        for ch in ev.get("checks", []):
            if quick and ch.get("slow"):
                res.append({"id": ch["id"], "pass": None, "why": "skipped (--quick)", "tail": ""})
                continue
            res.append(run_check(ch, ctx))
    if "builtin" in only:
        junk_after = L.junk_in(d)
        changed = L.tree_hash(d) != h0
        why = []
        if junk_before:
            why.append("junk in skill: " + ", ".join(junk_before[:3]))
        if changed:
            why.append("checks changed the skill folder")
        if junk_after and not junk_before:
            L.clean_junk(d)
            why.append("checks left __pycache__ (removed)")
        res.append({"id": "builtin:hygiene", "pass": not why, "why": "; ".join(why), "tail": ""})
    trig = []
    if "triggers" in only and ev.get("triggers"):
        if router is None:
            meta, _ = L.frontmatter(L.read(Path(d) / "SKILL.md"))
            router = Router(web_descs(root, {name: meta.get("description", "")}))
        trig = run_triggers(ev, name, router)
    regress = []
    if base:
        bpass = {r["id"] for r in base.get("results", []) + base.get("triggers", []) if r.get("pass")}
        for r in res + trig:
            if r["id"] in bpass and r.get("pass") is False:
                regress.append(r["id"])
    fails = [r for r in res if r.get("pass") is False]
    tfail = [t for t in trig if not t["pass"]]
    tnew = [t for t in tfail if t["id"] not in regress]
    out = {"skill": name, "dir": str(d), "when": L.now(), "tree": L.tree_hash(d), "version": L.version_of(d)[0],
           "results": res, "triggers": trig, "metrics": metrics, "regressions": regress,
           "missing_evals": bool(ev.get("_missing")),
           "trigger_acc": round(sum(t["pass"] for t in trig) / len(trig), 2) if trig else None,
           "agent_pending": len(ev.get("evals", [])),
           "ok": not fails and not regress}
    out["summary"] = (f"{name}: {'PASS' if out['ok'] else 'FAIL'} checks {sum(1 for r in res if r.get('pass'))}/"
                      f"{sum(1 for r in res if r.get('pass') is not None)}"
                      + (f", triggers {sum(t['pass'] for t in trig)}/{len(trig)}" if trig else ", no triggers")
                      + (f", {len(tnew)} trigger miss(es) also failing at baseline or new" if tnew and base else
                         (f", {len(tnew)} trigger miss(es)" if tnew else ""))
                      + (f", REGRESSIONS: {', '.join(regress)}" if regress else "")
                      + (" (no evals/evals.json: run evals.py init)" if ev.get("_missing") else ""))
    return out


def save_run(home, out, baseline=False):
    name = out["skill"]
    L.save_json(home / "evals" / f"{name}.last.json", out)
    runs = home / "runs" / name
    runs.mkdir(parents=True, exist_ok=True)
    (runs / "history.jsonl").open("a", encoding="utf-8").write(json.dumps(
        {"when": out["when"], "version": out["version"], "ok": out["ok"], "trigger_acc": out["trigger_acc"],
         "metrics": out["metrics"], "fails": [r["id"] for r in out["results"] if r.get("pass") is False]}) + "\n")
    if baseline:
        L.save_json(home / "baselines" / f"{name}.json", out)


def print_run(out, verbose=False):
    print(out["summary"])
    for r in out["results"]:
        if r.get("pass") is False or verbose:
            mark = "ok  " if r.get("pass") else ("skip" if r.get("pass") is None else "FAIL")
            print(f"  {mark} {r['id']}: {r.get('why') or r.get('tail', '')}"[:260])
    for t in out["triggers"]:
        if not t["pass"] or verbose:
            print(f"  {'ok  ' if t['pass'] else 'MISS'} {t['id']} should={t['should']} rank={t['rank']} "
                  f"top={t['top']}: {t['query'][:80]}")


def cmd_run(a, root, home, skills):
    names = sorted(n for n, s in skills.items() if s["origin"] == "root") if a.skill == "all" else [a.skill]
    if a.skill != "all" and a.skill not in skills:
        L.die(f"unknown skill {a.skill}")
    if a.dir and a.skill == "all":
        L.die("--dir needs one skill")
    only = set((a.only or "builtin,checks,triggers").split(","))
    router = None
    if not a.dir:
        router = Router(web_descs(root))
    bad = 0
    outs = []
    for n in names:
        d = Path(a.dir).resolve() if a.dir else Path(skills[n]["dir"])
        out = run_skill(n, d, root, home, skills, only, a.quick, router)
        save_run(home, out, a.save_baseline)
        outs.append(out)
        bad += not out["ok"]
        if not a.json:
            print_run(out, a.verbose)
    if a.json:
        print(json.dumps(outs if len(outs) > 1 else outs[0], indent=1))
    if a.save_baseline:
        print(f"baseline saved for {len(outs)} skill(s) in {home / 'baselines'}")
    return 1 if bad else 0


def cmd_triggers(a, root, home, skills):
    router = Router(web_descs(root))
    rows, miss = [], 0
    for n, s in sorted(skills.items()):
        if a.skill and n != a.skill:
            continue
        ev = load_eval(s["dir"], n)
        for t in run_triggers(ev, n, router):
            if not t["pass"]:
                miss += 1
                top = router.rank(t["query"])[: a.top]
                rows.append([n, "yes" if t["should"] else "no", t["rank"], ", ".join(f"{x} {sc:g}" for sc, x in top),
                             t["query"][:70]])
    if rows:
        print(L.md_table(["skill", "should", "rank", "top routes", "query"], rows))
    print(f"{miss} trigger miss(es) (lexical proxy)")
    return 1 if miss else 0


SKELETON = {
    "skill_name": "",
    "budget": {"skill_md_max_lines": 0, "skill_md_max_chars": 0},
    "triggers": [
        {"query": "TODO a prompt the owner would type that must load this skill", "should_trigger": True},
        {"query": "TODO a near-miss prompt that belongs to a sibling skill", "should_trigger": False}],
    "checks": [],
    "evals": []}


def cmd_init(a, root, home, skills):
    if a.skill not in skills:
        L.die(f"unknown skill {a.skill}")
    d = Path(skills[a.skill]["dir"])
    f = eval_file(d)
    if f.exists():
        print(f"exists: {f} (not overwritten)")
        return 0
    sk = json.loads(json.dumps(SKELETON))
    sk["skill_name"] = a.skill
    text = L.read(d / "SKILL.md")
    sk["budget"] = {"skill_md_max_lines": max(120, int((text.count("\n") + 1) * 1.1)),
                    "skill_md_max_chars": int(len(text) * 1.1)}
    if (d / "scripts" / "selftest.py").exists():
        sk["checks"].append({"id": "selftest", "run": "python3 {skill}/scripts/selftest.py", "exit": 0, "timeout": 600,
                             "slow": True})
    L.save_json(f, sk)
    print(f"wrote {f}: fill the TODO triggers and add 1-3 output checks")
    return 0


def cmd_live(a, root, home, skills):
    if a.skill not in skills:
        L.die(f"unknown skill {a.skill}")
    ev = load_eval(skills[a.skill]["dir"], a.skill)
    items = [{"query": t["query"], "should_trigger": t["should_trigger"]} for t in ev.get("triggers", [])]
    out = Path(a.out) if a.out else home / "runs" / a.skill / "trigger-eval-set.json"
    L.save_json(out, items)
    sc = L.skill_creator()
    print(f"wrote {out} ({len(items)} queries). Live trigger test (spends tokens: queries x runs):")
    print(f"  cd {sc or '<skill-creator>'} && python3 -m scripts.run_eval --eval-set {out} "
          f"--skill-path {skills[a.skill]['dir']} --runs-per-query 1 --num-workers 4")
    return 0


def cmd_agent(a, root, home, skills):
    if a.skill not in skills:
        L.die(f"unknown skill {a.skill}")
    d = skills[a.skill]["dir"]
    ev = load_eval(d, a.skill)
    items = ev.get("evals", [])
    if not items:
        print("no model-graded evals in evals.json (\"evals\": [...]); nothing to brief")
        return 0
    res_path = home / "runs" / a.skill / f"agent-{L.today()}.json"
    lines = [f"# Eval run: {a.skill} {L.version_of(d)[0]}", "",
             f"Skill folder: {d} (read its SKILL.md first and follow it). Work in a temp folder; never write into "
             "the skill, the bible or the owner's config; never publish, spend or message anyone.",
             "For each prompt below: do the task as the skill says (dry-run anything that would write canon), then "
             "grade every expectation PASS or FAIL with one line of evidence (a path, a number, a quoted line).",
             f"Write JSON to {res_path}: {{\"results\": [{{\"id\": ID, \"pass\": true|false, \"evidence\": \"...\"}}]}} "
             "(pass = all expectations of that id pass). Reply with the path only.", ""]
    for it in items:
        lines += [f"## {it['id']}", f"Prompt: {it['prompt']}"]
        if it.get("files"):
            lines.append("Files: " + ", ".join(str(Path(d) / f) for f in it["files"]))
        lines += [f"- {x}" for x in it.get("expectations", [])] + [""]
    brief = home / "runs" / a.skill / f"agent-brief-{L.today()}.md"
    brief.parent.mkdir(parents=True, exist_ok=True)
    brief.write_text("\n".join(lines), encoding="utf-8")
    print(f"brief: {brief} (~{L.toks(len(chr(10).join(lines)))} tokens); give it to ONE fresh subagent, then "
          f"evals.py record {a.skill} {res_path}")
    return 0


def cmd_record(a, root, home, skills):
    data = L.load_json(a.results)
    if not data or "results" not in data:
        L.die("results file needs {\"results\": [{\"id\", \"pass\", \"evidence\"}]}")
    last = L.load_json(home / "evals" / f"{a.skill}.last.json", {}) or {}
    last["agent"] = {"when": L.now(), "results": data["results"],
                     "pass": sum(1 for r in data["results"] if r.get("pass")), "n": len(data["results"])}
    L.save_json(home / "evals" / f"{a.skill}.last.json", last)
    print(f"recorded {last['agent']['pass']}/{last['agent']['n']} model-graded evals for {a.skill}")
    return 0 if last["agent"]["pass"] == last["agent"]["n"] else 1


def main(argv=None):
    ap = L.common_args(argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter))
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("run", help="run a skill's regression evals (or all)")
    p.add_argument("skill")
    p.add_argument("--dir", help="candidate folder (a staged copy) to test instead of the live skill")
    p.add_argument("--only", help="comma list of builtin,checks,triggers")
    p.add_argument("--quick", action="store_true", help="skip checks marked slow")
    p.add_argument("--save-baseline", action="store_true", help="store this run as the regression baseline")
    p.add_argument("--verbose", "-v", action="store_true")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("triggers", help="route all trigger prompts; list the misses")
    p.add_argument("--skill")
    p.add_argument("--top", type=int, default=3)
    p = sp.add_parser("init", help="write an evals.json skeleton")
    p.add_argument("skill")
    p = sp.add_parser("live", help="export triggers for skill-creator run_eval (real model, costs tokens)")
    p.add_argument("skill")
    p.add_argument("--out")
    p = sp.add_parser("agent", help="write the brief for model-graded evals")
    p.add_argument("skill")
    p = sp.add_parser("record", help="store model-graded results")
    p.add_argument("skill")
    p.add_argument("results")
    a = ap.parse_args(argv)
    root = L.find_root(a.root)
    home = L.ensure_home(L.smith_home(root, a.home))
    skills = L.web(root)
    return {"run": cmd_run, "triggers": cmd_triggers, "init": cmd_init, "live": cmd_live, "agent": cmd_agent,
            "record": cmd_record}[a.cmd](a, root, home, skills)


if __name__ == "__main__":
    sys.exit(main())
