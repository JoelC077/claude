#!/usr/bin/env python3
"""Self-test for bible.py: runs every subcommand against a throwaway copy of the canon.

Usage: python3 selftest.py [--canon DIR] [--keep]
  --canon DIR  canon to copy (default: ../canon next to this script)
  --keep       keep the temp copy and print its path
Exit 0 when every check passes. The real canon is never written.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BIBLE = HERE / "bible.py"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--canon", default=str(HERE.parent / "canon"))
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="rr-bible-test-"))
    canon = tmp / "canon"
    shutil.copytree(a.canon, canon)
    results = []

    def run(*args):
        p = subprocess.run([sys.executable, str(BIBLE), "--canon", str(canon), *args],
                           capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr

    def expect(name, cond, out=""):
        results.append((name, bool(cond)))
        if not cond:
            print(f"FAIL {name}\n{out[:800]}")

    rc, out = run("lint")
    expect("lint clean canon", rc == 0 and "lint OK" in out, out)
    rc, out = run("list")
    expect("list", rc == 0 and "open questions:" in out, out)
    rc, out = run("list", "gameplay")
    expect("list file", rc == 0 and "gameplay.fuel" in out, out)
    rc, out = run("get", "gameplay.crew.max")
    expect("get key", rc == 0 and out.startswith("gameplay.crew.max = 6"), out)
    rc, out = run("get", "gameplay.fuel", "--values")
    expect("get prefix --values", rc == 0 and "gameplay.fuel.shovel_pct = 4" in out and "|" not in out, out)
    rc, out = run("get", "fuel")
    expect("get bare section", rc == 0 and "gameplay.fuel." in out, out)
    rc, out = run("get", "identity")
    expect("get file", rc == 0 and "identity.game.title = Risky Rails" in out, out)
    rc, out = run("get", "OQ-001")
    expect("get OQ", rc == 0 and "### OQ-001" in out and "- default:" in out, out)
    rc, out = run("get", "D-001", "--json")
    expect("get D --json", rc == 0 and json.loads(out)["id"] == "D-001", out)
    rc, out = run("get", "gameplay.crew.nope")
    expect("get miss exits 1", rc == 1 and "no key or topic" in out, out)
    rc, out = run("get", "palette")
    expect("get palette index", rc == 0 and "style.brand" in out, out)
    rc, out = run("search", "Depotron")
    expect("search hit", rc == 0 and "Depotron" in out, out)
    rc, out = run("search", "qqqzzz")
    expect("search miss exits 1", rc == 1, out)
    rc, out = run("stats", "--json")
    st = json.loads(out) if rc == 0 else {}
    expect("stats", rc == 0 and st.get("facts", 0) > 100 and st.get("open_questions", 0) > 0, out)

    rc, out = run("tokens", "--format", "json")
    tj = json.loads(out) if rc == 0 else {}
    expect("tokens json", rc == 0 and tj["colors"]["style.brand.hazard_yellow"] == "#F2C230"
           and tj["fonts"]["display"] == "Luckiest Guy", out)
    rc, out = run("tokens", "--format", "css")
    expect("tokens css", rc == 0 and out.count("{") == out.count("}") and "--rr-style-brand-ink: #15171C;" in out, out)
    rc, out = run("tokens", "--format", "luau")
    expect("tokens luau", rc == 0 and out.count("{") == out.count("}") and out.strip().endswith("return T")
           and 'Color3.fromHex("F2C230")' in out, out)
    rc, out = run("tokens", "--format", "json", "--canon-only")
    expect("tokens canon-only smaller", rc == 0 and len(json.loads(out)["colors"]) < len(tj["colors"]), out)

    good = tmp / "good.css"
    good.write_text(".a{font-family:'Luckiest Guy',sans-serif;color:#F2C230;background:#15171C}\n"
                    ".b{color:rgba(21,23,28,.5)} /* Up to 6 players; vertical FOV 70; 1 stud = 0.28 m */\n")
    rc, out = run("check", str(good))
    expect("check pass", rc == 0 and "check PASS" in out, out)
    bad = tmp / "bad.html"
    bad.write_text("<style>.t{font-family:'Comic Sans MS';color:#C8A165}.u{color:#E8B021}</style>\n"
                   "<p>Like Flight or Die. Up to 8 players. FOV 90. Join Trash Railways.</p>\n"
                   "<script>local c = Color3.fromRGB(124,138,86)</script>\n")
    rc, out = run("check", str(bad), "--json")
    cj = json.loads(out) if out.strip().startswith("{") else {"findings": []}
    kinds = {(f["level"], f["kind"]) for f in cj["findings"]}
    expect("check fail exit 1", rc == 1, out)
    expect("check finds hex/font/name/number",
           {("ERROR", "hex"), ("ERROR", "font"), ("ERROR", "name"), ("ERROR", "number"), ("WARN", "hex"),
            ("WARN", "name")} <= kinds, out)
    rc, out = run("check", str(bad), "--skip", "hex,fonts,names,numbers")
    expect("check skip", rc == 0, out)
    rc, out = run("check", str(bad), "--allow", "C8A165", "--skip", "fonts,names,numbers")
    expect("check allow", rc == 0, out)

    rc, out = run("add-fact", "gameplay.fuel.test_rate", "1.5", "--src", "CB", "--note", "selftest", "--status", "proposed")
    expect("add-fact new", rc == 0 and "added in gameplay.md" in out, out)
    rc, out = run("get", "gameplay.fuel.test_rate")
    expect("add-fact readable", rc == 0 and "= 1.5" in out, out)
    rc, out = run("add-fact", "gameplay.fuel.test_rate", "2", "--src", "CB")
    expect("add-fact dup refused", rc == 1, out)
    rc, out = run("add-fact", "gameplay.fuel.test_rate", "2", "--src", "CB", "--replace")
    expect("add-fact replace", rc == 0 and "replaced" in out, out)
    rc, out = run("add-fact", "gameplay.newsec.thing", "x", "--src", "owner 2026-09-28", "--status", "canon",
                  "--title", "New section")
    expect("add-fact new section", rc == 0 and "## newsec · New section" in (canon / "gameplay.md").read_text(), out)
    rc, out = run("add-fact", "gameplay.fuel.bad", "x", "--src", "NOPE")
    expect("add-fact bad src", rc == 2, out)
    rc, out = run("add-fact", "gameplay.fuel.chk", "3", "--src", "CB", "--check", r"(\d+) shovels")
    expect("add-fact with check", rc == 0, out)
    t = tmp / "n.txt"
    t.write_text("it takes 5 shovels")
    rc, out = run("check", str(t))
    expect("custom number check fires", rc == 1 and "gameplay.fuel.chk" in out, out)

    rc, out = run("add-question", "Selftest question", "--option", "A: yes", "--option", "B: no",
                  "--default", "A (test)", "--src", "WR", "--affects", "gameplay.fuel.test_rate")
    m = re.search(r"added (OQ-\d{3})", out)
    expect("add-question", rc == 0 and m, out)
    qid = m.group(1) if m else "OQ-999"
    rc, out = run("decide", qid, "B", "--by", "someone")
    expect("decide refuses non-owner", rc == 1, out)
    rc, out = run("decide", qid, "Z", "--by", "owner")
    expect("decide refuses bad option", rc == 1, out)
    rc, out = run("decide", qid, "B", "--by", "owner", "--via", "selftest")
    expect("decide", rc == 0 and "decided" in out and "gameplay.fuel.test_rate" in out, out)
    expect("decide moved block", qid not in (canon / "open-questions.md").read_text()
           and f"- from: {qid}" in (canon / "decisions.md").read_text())
    rc, out = run("get", qid)
    expect("get decided OQ points to D", rc == 0 and "was decided" in out, out)
    rc, out = run("lint")
    expect("lint after writes", rc == 0, out)

    g = canon / "gameplay.md"
    g.write_text(g.read_text() + "- `gameplay.fuel.broken` = `x` src: CB canon\n"
                 "- `gameplay.fuel.shovel_pct` = `5` | dup | src: NOPE | canon\n")
    rc, out = run("lint")
    expect("lint catches faults", rc == 1 and "malformed" in out and "duplicate key" in out
           and "unknown source" in out, out)

    passed = sum(ok for _, ok in results)
    print(f"selftest: {passed}/{len(results)} passed" + (f" (temp kept at {tmp})" if a.keep else ""))
    if not a.keep:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
