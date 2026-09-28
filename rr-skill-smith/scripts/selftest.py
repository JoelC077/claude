#!/usr/bin/env python3
"""rr-skill-smith selftest: builds a tiny fake JARVIS root (bible, two skills, trials, a mission) in a temp folder and
exercises every script end to end. Uses the real rr-bible/scripts/bible.py when it can find it (drift checks need it).

Usage: selftest.py [--keep]   (prints "selftest: N/N passed"; exit 1 on any failure)
"""
import sys

sys.dont_write_bytecode = True
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SMITH = HERE.parent
sys.path.insert(0, str(HERE))
import smithlib as L  # noqa: E402

RESULTS = []


def ok(cond, name, detail=""):
    RESULTS.append((bool(cond), name))
    print(f"{'ok  ' if cond else 'FAIL'} {name}" + (f"  [{detail[:300]}]" if detail and not cond else ""))


def w(p, text):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def find_bible_script():
    for c in (os.environ.get("JARVIS_ROOT"), SMITH.parent, Path("/home/user/claude")):
        if c and (Path(c) / "rr-bible" / "scripts" / "bible.py").exists():
            return Path(c) / "rr-bible" / "scripts" / "bible.py"
    return None


def build(root):
    bs = find_bible_script()
    w(root / "rr-bible/SKILL.md", '---\nname: rr-bible\ndescription: "Risky Rails canon: facts, colours, fonts and open '
      'questions. Use whenever Risky Rails work needs a fact."\n---\n# Bible\n')
    if bs:
        (root / "rr-bible/scripts").mkdir(parents=True)
        shutil.copy(bs, root / "rr-bible/scripts/bible.py")
    c = root / "rr-bible/canon"
    w(c / "sources.md", "# Sources\n\n- `T1` — Test source | 2026-01-01 | here\n")
    w(c / "open-questions.md", "# Open questions\n\n### OQ-001 · Hard brake: how hard does the brake shake the camera?\n"
      "- status: open\n- raised: 2026-01-01\n- src: T1\n- options:\n  - A: soft\n  - B: hard\n- default: A\n"
      "- affects: gameplay.brake.shake\n")
    w(c / "decisions.md", "# Decisions\n\n### D-001 · 2026-01-01 · Crew size settled (was OQ-002)\n- decision: six\n"
      "- by: owner\n- src: T1\n")
    w(c / "style.md", "# Style\n\n## brand · Brand\n- `style.brand.hazard_yellow` = `#F2C230` | accent | src: T1 | canon\n"
      "- `style.brand.old_red` = `#AA0000` | old | src: T1 | superseded\n")
    w(c / "gameplay.md", "# Gameplay\n\n## crew · Crew\n- `gameplay.crew.max` = `6` | players per server | src: T1 | "
      "canon | check: (?:up to|max(?:imum)?(?: of)?)\\s*(\\d+)\\s*(?:players|crew)\\b\n")
    w(c / "tech.md", "# Tech\n\n## units · Units\n- `tech.units.gauge` = `8` | track gauge in studs | src: T1 | canon\n")
    # rr-alpha: planted drift
    w(root / "rr-alpha/SKILL.md", '---\nname: rr-alpha\ndescription: "Risky Rails train whistle and horn sound designer. '
      'Use whenever the owner asks for whistle, horn or chuff sounds, loudness or sound mixing."\n---\n# Alpha\n\n'
      "`<a>` = this folder. `alpha` below = `python3 <a>/scripts/alpha.py`.\nRun `alpha list --strict`, then "
      "`alpha show NAME`.\nThe accent is #F2C231 here. Read `gameplay.crew.max` with `<bible>/scripts/bible.py get`.\n")
    w(root / "rr-alpha/scripts/alpha.py", "import argparse\nap = argparse.ArgumentParser()\n"
      "sp = ap.add_subparsers(dest='cmd', required=True)\np = sp.add_parser('list')\n"
      "p.add_argument('--strict', action='store_true')\np = sp.add_parser('show')\np.add_argument('name')\n"
      "a = ap.parse_args()\nprint('whistle horn chuff' if a.cmd == 'list' else 'show ' + a.name)\n")
    w(root / "rr-alpha/references/guide.md", "Use #F2C230 for highlights. Crews go up to 9 players.\n"
      "OQ-001 decides the whistle loudness in the lobby music.\nSee OQ-777 and OQ-TBD-whistle. OQ-002 is settled.\n"
      "Keys: `gameplay.crew.maxx` and `style.brand.old_red`.\nScripts: `<bible>/scripts/nope.py`, `alpha list --nope`, "
      "`alpha frobnicate`.\nTrack gauge of 5 studs.\nAlso references/missing.md and the rr-alphx skill.\n")
    w(root / "rr-alpha/evals/evals.json", json.dumps({
        "skill_name": "rr-alpha", "triggers": [{"query": "make the train whistle louder", "should_trigger": True}],
        "checks": [{"id": "list", "run": "python3 {skill}/scripts/alpha.py list", "stdout_has": ["whistle"]}]}))
    # rr-beta: clean skill for the ship flow
    w(root / "rr-beta/SKILL.md", '---\nname: rr-beta\ndescription: "Risky Rails lobby UI builder: lobby panels, buttons '
      'and menus for phone and console. Use whenever the owner wants a lobby panel, button or menu built."\n---\n'
      "# Beta\n\nRun `python3 <b>/scripts/beta.py build` to build a panel.\n")
    w(root / "rr-beta/scripts/beta.py", "import argparse\nap = argparse.ArgumentParser()\n"
      "sp = ap.add_subparsers(dest='cmd', required=True)\nsp.add_parser('build')\nap.parse_args()\nprint('built panel')\n")
    w(root / "rr-beta/evals/evals.json", json.dumps({
        "skill_name": "rr-beta",
        "triggers": [{"query": "build the lobby panel buttons for phone", "should_trigger": True},
                     {"query": "make the train whistle louder", "should_trigger": False}],
        "checks": [{"id": "build", "run": "python3 {skill}/scripts/beta.py build", "stdout_has": ["built"]}],
        "evals": [{"id": 1, "prompt": "build a lobby panel", "expected_output": "a panel",
                   "expectations": ["prints built"]}]}))
    # trial + mission evidence
    w(root / "trials/rr-alpha/FRICTION.md", "# FRICTION — rr-alpha trial\n\n## Run log\n1. did things\n\n## Friction (5)\n"
      "F1 [H] scripts/alpha.py list — silently ignores NAMES — evidence: out.txt\n"
      "F2 [M] every run writes __pycache__ into the skill folder\n## F3 · Brief is generic (L)\n"
      "| # | Sev | Where | Friction | Evidence |\n|---|---|---|---|---|\n"
      "| 4 | H | step 2 | Canon check contradicts canon gauge | x |\n\n- [M, fixed] engine — dedupe collided\n"
      "## Environment, not skill\n- [L] no ffmpeg in the cloud image\n## What worked\n- [H] must not be parsed\n")
    w(root / "trials/rr-alpha/REPORT.md", "# fix report\n\nAll high and medium findings are applied.\n")
    w(root / "trials/rr-alpha/crit/pass-1/verdict.md", "SCORES:\nF1 Signal: 5/10 — weak\nF2 Form: 7/10 — ok\n"
      "OVERALL: 5 (F1 Signal)\n")
    m = root / "missions/260101-demo"
    w(m / "SKILL-FRICTION.md", "# SKILL-FRICTION (rr-beta + rr-alpha), mission 260101-demo\n\n"
      "1. beta.py writes __pycache__ into the skill folder on every run.\n"
      "2. BLOCKER: the lobby panel build has no path for 2 or more screens.\n"
      "3. alpha.py list prints the whole library (token sink).\n")
    w(m / "state.json", json.dumps({"tokens": 1234, "status": "done"}))
    w(m / "critique/ledger.json", json.dumps([{"pass": 1, "agent": "self-review", "scores": {"A1": 6, "A2": 7},
                                                "new": 100, "tokens": 100}]))
    w(m / "critique/pass-1/verdict.md", "SELF-ASSESSED final\nSCORES: A1 6 · A2 7\nOVERALL: 6\n")
    return bool(bs)


def main():
    keep = "--keep" in sys.argv
    tmp = Path(tempfile.mkdtemp(prefix="smith-selftest-"))
    root, home, fake_home = tmp / "jarvis", tmp / "home", tmp / "userhome"
    fake_home.mkdir(parents=True)
    has_bible = build(root)
    env = dict(os.environ, HOME=str(fake_home), PYTHONDONTWRITEBYTECODE="1")
    env.pop("JARVIS_ROOT", None)
    env.pop("RR_SMITH_HOME", None)
    env.pop("RR_BIBLE_DIR", None)

    def run(script, *args, cwd=None):
        r = subprocess.run([sys.executable, str(HERE / script), "--root", str(root), "--home", str(home), *args],
                           capture_output=True, text=True, env=env, cwd=cwd or tmp, timeout=300)
        return r.returncode, r.stdout + r.stderr

    try:
        # ---- help
        for s in ("harvest.py", "drift.py", "evals.py", "ship.py", "health.py"):
            r = subprocess.run([sys.executable, str(HERE / s), "--help"], capture_output=True, text=True, env=env)
            ok(r.returncode == 0 and "usage" in r.stdout.lower(), f"{s} --help")
        # ---- harvest
        code, out = run("harvest.py", "scan")
        ok(code == 0 and "2 friction logs" in out, "harvest scan finds both logs", out)
        fr = L.load_json(home / "frictions.json")
        ids = {i["id"]: i for i in fr["items"]}
        ok(set(ids) == {"t:rr-alpha#F1", "t:rr-alpha#F2", "t:rr-alpha#F3", "t:rr-alpha#4", "t:rr-alpha#b1",
                        "t:rr-alpha#b2", "m:260101-demo#1", "m:260101-demo#2", "m:260101-demo#3"},
           "parses numbered, F-id, F-heading, table and bullet items; skips run log and what worked", str(sorted(ids)))
        ok(ids.get("t:rr-alpha#F3", {}).get("sev") == "L" and ids.get("t:rr-alpha#4", {}).get("sev") == "H",
           "severity from heading and table")
        ok(ids.get("t:rr-alpha#F1", {}).get("status") == "claimed" and ids.get("t:rr-alpha#F3", {}).get("status") == "open",
           "REPORT blanket claim covers H/M only")
        ok(ids.get("t:rr-alpha#b1", {}).get("status") == "claimed" and ids.get("t:rr-alpha#b2", {}).get("status") == "env",
           "[fixed] hint and environment section")
        ok(ids.get("m:260101-demo#1", {}).get("skill") == "rr-beta" and ids.get("m:260101-demo#3", {}).get("skill") == "rr-alpha",
           "mission items attributed by script name")
        ok(ids.get("m:260101-demo#2", {}).get("sev") == "H", "BLOCKER counts as High")
        ok(ids.get("t:rr-alpha#F1", {}).get("title", "").startswith("silently ignores NAMES"), "title leads with the problem",
           ids.get("t:rr-alpha#F1", {}).get("title", ""))
        cl = L.load_json(home / "clusters.json")["clusters"]
        py = [c for c in cl if c["theme"] == "pycache"]
        ok(py and all(set(c["web_skills"]) == {"rr-alpha", "rr-beta"} for c in py), "web-wide pycache theme across 2 skills")
        sc = L.load_json(home / "scores.json")
        crit = [s for s in sc["scores"] if s["kind"] == "critic"]
        ok(any(s["skill"] == "rr-alpha" and s["overall"] == 5 and s["independent"] for s in crit)
           and any(s["overall"] == 6 and not s["independent"] for s in crit), "critic scores with independence flag")
        ok(any(c["kind"] == "mission" and c["tokens"] == 1234 for c in sc["costs"]), "mission token cost harvested")
        code, out = run("harvest.py", "clusters", "--skill", "rr-alpha")
        ok(code == 0 and "rr-alpha/" in out, "clusters per skill")
        code, out = run("harvest.py", "patch", "rr-alpha")
        brief = next((home / "proposals" / "rr-alpha").glob("patch-brief-*.md"), None)
        ok(code == 0 and brief and "Check to add" in L.read(brief), "patch brief written", out)
        code, out = run("harvest.py", "close", "m:260101-demo#2", "--by", "selftest")
        run("harvest.py", "scan")
        ids = {i["id"]: i for i in L.load_json(home / "frictions.json")["items"]}
        ok(ids["m:260101-demo#2"]["status"] == "fixed", "close survives a rescan")
        code, out = run("harvest.py", "list", "--status", "all", "--json")
        ok(code == 0 and json.loads(out), "list --json")
        # ---- drift
        if has_bible:
            code, out = run("drift.py", "rr-alpha", "--json", "--level", "INFO")
            d = json.loads(out)["findings"]
            msgs = " | ".join(f"{f['level']} {f['kind']} {f['msg']}" for f in d)
            want = [("ERROR", "hex", "near-copy"), ("WARN", "hex", "restated"), ("ERROR", "numbers", "up to 9 players"),
                    ("ERROR", "oq", "OQ-777"), ("WARN", "oq", "OQ-TBD"), ("WARN", "oq", "is decided"),
                    ("WARN", "oq", "cited for"), ("ERROR", "keys", "gameplay.crew.maxx"), ("WARN", "keys", "superseded"),
                    ("ERROR", "refs", "rr-bible/scripts/nope.py"), ("ERROR", "refs", "references/missing.md"),
                    ("WARN", "refs", "did you mean rr-alpha"), ("WARN", "flags", "--nope"),
                    ("WARN", "flags", "frobnicate"), ("WARN", "studs", "5 studs")]
            for lvl, kind, frag in want:
                ok(any(f["level"] == lvl and f["kind"] == kind and frag in f["msg"] for f in d),
                   f"drift {lvl} {kind}: {frag}", msgs)
            ok(code == 1, "drift exits 1 on ERROR")
            ok(not any(f["kind"] == "flags" and "--strict" in f["msg"] for f in d), "documented real flag not flagged")
            code, out = run("drift.py", "rr-beta")
            ok(code == 0, "clean skill has no drift ERROR", out)
        else:
            ok(True, "drift tests skipped (rr-bible/scripts/bible.py not found)")
        # ---- evals
        code, out = run("evals.py", "run", "rr-beta", "--save-baseline")
        ok(code == 0 and "PASS" in out, "evals pass on the clean skill", out)
        ok((home / "baselines" / "rr-beta.json").exists(), "baseline saved")
        code, out = run("evals.py", "run", "rr-alpha")
        ok(code == 1 and "builtin:drift" in out, "planted drift fails the drift built-in", out)
        stage = tmp / "cand" / "rr-beta"
        shutil.copytree(root / "rr-beta", stage)
        sk = L.read(stage / "SKILL.md")
        w(stage / "SKILL.md", sk.replace(sk.split('description: "')[1].split('"')[0], "Risky Rails whistle and horn helper."))
        code, out = run("evals.py", "run", "rr-beta", "--dir", str(stage))
        ok(code == 1 and "REGRESSIONS: trigger:" in out, "description edit that loses a trigger = regression", out)
        shutil.rmtree(stage)
        shutil.copytree(root / "rr-beta", stage)
        ev = json.loads(L.read(stage / "evals/evals.json"))
        ev["checks"].append({"id": "dirty", "run": "touch {skill}/scripts/junk.txt"})
        ev["checks"].append({"id": "exitcode", "run": "python3 -c 'import sys; sys.exit(3)'", "exit": 0})
        w(stage / "evals/evals.json", json.dumps(ev))
        code, out = run("evals.py", "run", "rr-beta", "--dir", str(stage))
        ok(code == 1 and "checks changed the skill folder" in out and "exit 3 != 0" in out,
           "hygiene catches a check that writes the skill; exit code asserted", out)
        code, out = run("evals.py", "triggers")
        ok(code == 0 and "0 trigger miss" in out, "trigger router over the web", out)
        code, out = run("evals.py", "init", "rr-bible")
        ok(code == 0 and (root / "rr-bible/evals/evals.json").exists(), "init writes a skeleton")
        code, out = run("evals.py", "live", "rr-beta")
        ok(code == 0 and (home / "runs/rr-beta/trigger-eval-set.json").exists(), "live exports a run_eval set")
        code, out = run("evals.py", "agent", "rr-beta")
        ok(code == 0 and any((home / "runs/rr-beta").glob("agent-brief-*.md")), "agent brief written")
        w(tmp / "res.json", json.dumps({"results": [{"id": 1, "pass": True, "evidence": "built"}]}))
        code, out = run("evals.py", "record", "rr-beta", str(tmp / "res.json"))
        ok(code == 0 and "1/1" in out, "record model-graded results")
        # ---- ship
        code, out = run("ship.py", "init-changelog", "rr-beta")
        ok(code == 0 and L.version_of(root / "rr-beta")[0] == "1.0.0", "init-changelog starts 1.0.0")
        run("evals.py", "run", "rr-beta", "--save-baseline")
        code, out = run("ship.py", "stage", "rr-beta")
        st = home / "stage" / "rr-beta"
        ok(code == 0 and (st / "SKILL.md").exists(), "stage copies the skill")
        w(st / "scripts/beta.py", L.read(st / "scripts/beta.py").replace("built panel", "built panel v2"))
        code, out = run("ship.py", "propose", "rr-beta", "--bump", "patch", "--summary", "panel v2",
                        "--fixes", "m:260101-demo#1")
        ok(code == 0 and (home / "proposals/rr-beta-1.0.1.md").exists(), "propose writes the proposal", out)
        ok("built panel v2" in L.read(home / "proposals/rr-beta-1.0.1.md"), "proposal carries the diff")
        ok("v2" not in L.read(root / "rr-beta/scripts/beta.py"), "propose leaves the live skill untouched")
        code, out = run("ship.py", "apply", "rr-beta", "--approved", "agent 2026-01-01")
        ok(code == 2, "apply refuses a non-owner approval", out)
        w(st / "scripts/beta.py", L.read(st / "scripts/beta.py") + "# later edit\n")
        code, out = run("ship.py", "apply", "rr-beta", "--approved", "owner 2026-01-01 via chat")
        ok(code == 1 and "changed since the proposal" in out, "apply refuses a candidate changed after the proposal", out)
        code, out = run("ship.py", "propose", "rr-beta", "--bump", "patch", "--summary", "panel v2",
                        "--fixes", "m:260101-demo#1")
        code, out = run("ship.py", "apply", "rr-beta", "--approved", "owner 2026-01-01 via chat")
        ok(code == 0 and "shipped rr-beta 1.0.1" in out, "owner-approved apply ships", out)
        ok(L.version_of(root / "rr-beta")[0] == "1.0.1" and "owner 2026-01-01" in L.read(root / "rr-beta/CHANGELOG.md"),
           "CHANGELOG bumped with approval")
        ok("v2" in L.read(root / "rr-beta/scripts/beta.py") and not st.exists(), "staged files copied, stage cleared")
        pk = root / "dist" / "rr-beta.skill"
        names = zipfile.ZipFile(pk).namelist() if pk.exists() else []
        ok("rr-beta/SKILL.md" in names and not any("/evals/" in n or "__pycache__" in n for n in names),
           "package excludes evals and caches", str(names))
        ok(any((home / "backups").rglob("rr-beta.skill")), "previous version backed up")
        run("harvest.py", "scan")
        ids = {i["id"]: i for i in L.load_json(home / "frictions.json")["items"]}
        ok(ids["m:260101-demo#1"]["status"] == "fixed", "apply closes the fixed frictions")
        code, out = run("ship.py", "status")
        ok(code == 0 and "1.0.1" in out, "status lists versions")
        code, out = run("ship.py", "package", "all", "--dist", str(tmp / "dist2"))
        ok(code == 0 and len(list((tmp / "dist2").glob("*.skill"))) == 3, "package all", out)
        code, out = run("ship.py", "propose", "rr-beta", "--bump", "patch", "--summary", "x", "--in-place")
        ok(code == 1 and "no changes" in out, "in-place propose with no change refuses")
        w(root / "rr-beta/scripts/beta.py", L.read(root / "rr-beta/scripts/beta.py").replace("v2", "v3"))
        code, out = run("ship.py", "propose", "rr-beta", "--bump", "minor", "--summary", "v3 in place", "--in-place")
        ok(code == 0 and (home / "proposals/rr-beta-1.1.0.md").exists(), "in-place propose diffs against the package", out)
        code, out = run("ship.py", "apply", "rr-beta", "--approved", "owner 2026-01-02 via chat")
        bk = home / "backups" / "rr-beta-1.0.1" / "rr-beta.skill"
        old_src = zipfile.ZipFile(bk).read("rr-beta/scripts/beta.py").decode() if bk.exists() else ""
        ok(code == 0 and L.version_of(root / "rr-beta")[0] == "1.1.0" and "v2" in old_src and "v3" not in old_src,
           "in-place apply bumps and backs up the previous package", out)
        ok((home / "closed.json").exists() and ".gitignore" in os.listdir(home), "closes kept in closed.json; home gitignore")
        # ---- health
        code, out = run("health.py")
        ok(code == 0 and all((home / f"health.{x}").exists() for x in ("html", "md", "json")), "health writes html, md, json",
           out)
        md = L.read(home / "health.md")
        ok("| rr-alpha | critical |" in md and "rr-beta" in md, "health status per skill", md[:400])
        h = L.read(home / "health.html")
        ok("prefers-color-scheme:dark" in h and "<title>JARVIS Web Health</title>" in h and "http" not in
           h.split("<body>")[1][:200], "html is self-contained with dark mode")
        run("health.py", "--no-evals", "--no-scan")
        ok(len(L.read(home / "history.jsonl").splitlines()) == 2, "history appends a snapshot per run")
        # ---- hygiene of the smith itself
        ok(not L.junk_in(SMITH), "no __pycache__ in the smith", str(L.junk_in(SMITH)))
        ok(L.quick_validate(SMITH)[0], "smith validates", L.quick_validate(SMITH)[1])
    finally:
        if keep:
            print(f"kept {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    n = sum(1 for r, _ in RESULTS if r)
    print(f"selftest: {n}/{len(RESULTS)} passed")
    return 0 if n == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
