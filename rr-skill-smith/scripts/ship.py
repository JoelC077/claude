#!/usr/bin/env python3
"""rr-skill-smith ship: stage -> propose -> (owner approves) -> apply: version, CHANGELOG, .skill package.

Usage:
  ship.py [--root R] [--home H] status [SKILL]
  ship.py stage SKILL [--force]            copy the live skill to <home>/stage/SKILL; edit the copy, never the live one
  ship.py diff SKILL [--in-place]          what would ship (staged vs live, or live vs its last package)
  ship.py propose SKILL --bump patch|minor|major --summary TEXT [--section Fixed|Changed|Added|Removed]
                  [--fixes ID ...] [--in-place] [--full]
        run evals (+ validate + drift) on the candidate, write <home>/proposals/SKILL-VERSION.md/.json. Nothing
        live changes. --in-place: the edits are already in the live folder (e.g. an owner-approved integration run);
        the candidate is the live folder and the diff is against dist/SKILL.skill.
  ship.py apply SKILL --approved "owner YYYY-MM-DD via chat" [--full]
        only with a proposal whose evals passed and whose candidate has not changed since (tree hash); reruns the
        evals, backs the live skill up to <home>/backups/, copies the staged files over it, writes CHANGELOG.md,
        packages <root>/dist/SKILL.skill, saves the eval baseline and closes the --fixes frictions.
  ship.py package SKILL|all [--dist DIR]   validate + clean + zip the live folder as it is (no version change)
  ship.py init-changelog SKILL|all [--version 1.0.0] [--note TEXT]   start CHANGELOG.md where it is missing

Versions: the top "## [x.y.z] - date" of <skill>/CHANGELOG.md (0.0.0 when none). Packages exclude __pycache__, *.pyc,
.DS_Store and the root evals/ folder (same rules as skill-creator package_skill). Only the owner approves: --approved
must start with "owner". Never publishes, uploads or commits.
"""
import sys

sys.dont_write_bytecode = True
import argparse
import difflib
import re
import shutil
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smithlib as L  # noqa: E402

CL_HEAD = ("# Changelog\n\nNotable changes to {name}. Versions are set by rr-skill-smith (`ship.py`); the owner "
           "approves each one.\n\n")


def skill_or_die(skills, name, root_only=True):
    if name not in skills:
        L.die(f"unknown skill {name}; known: {', '.join(sorted(skills))}")
    if root_only and skills[name]["origin"] != "root":
        L.die(f"{name} is an installed copy ({skills[name]['dir']}); ship only skills in the JARVIS root")
    return Path(skills[name]["dir"])


def package(src, name, dist):
    """zip src as <name>/... into dist/<name>.skill; returns (path, n_files)."""
    ok, msg = L.quick_validate(src)
    if not ok:
        L.die(f"validation failed for {name}: {msg}", 1)
    L.clean_junk(src)
    dist = Path(dist)
    dist.mkdir(parents=True, exist_ok=True)
    out = dist / f"{name}.skill"
    tmp = out.with_suffix(".skill.tmp")
    n = 0
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in L.skill_files(src, text_only=False, packaged=True):
            z.write(p, f"{name}/{p.relative_to(src)}")
            n += 1
    tmp.replace(out)
    return out, n


def zip_texts(path, name):
    out = {}
    if not Path(path).exists():
        return out
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            if info.is_dir() or not info.filename.startswith(name + "/"):
                continue
            relp = info.filename[len(name) + 1:]
            try:
                out[relp] = z.read(info).decode("utf-8")
            except UnicodeDecodeError:
                out[relp] = None
    return out


def dir_texts(d):
    out = {}
    for p in L.skill_files(d, text_only=False, packaged=True):
        try:
            out[str(p.relative_to(d))] = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            out[str(p.relative_to(d))] = None
    return out


def diff_trees(old, new, max_lines=400):
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(k for k in set(old) & set(new) if old[k] != new[k])
    lines = []
    for k in changed + added:
        a = (old.get(k) or "").splitlines() if old.get(k) is not None else ["<binary>"]
        b = (new.get(k) or "").splitlines() if new.get(k) is not None else ["<binary>"]
        lines += list(difflib.unified_diff(a, b, f"a/{k}", f"b/{k}", n=1, lineterm=""))
    stat = f"{len(changed)} changed, {len(added)} added, {len(removed)} removed"
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... diff cut at {max_lines} lines ({len(lines)} total)"]
    return stat, changed, added, removed, lines


def run_evals(name, cand, root, home, skills, full):
    import evals  # noqa: E402
    out = evals.run_skill(name, Path(cand), root, home, skills, {"builtin", "checks", "triggers"}, quick=not full)
    evals.save_run(home, out)
    return out


def candidate(a, home, skills):
    live = skill_or_die(skills, a.skill)
    staged = home / "stage" / a.skill
    if getattr(a, "in_place", False):
        return live, live, None
    if not staged.exists():
        L.die(f"nothing staged for {a.skill}: ship.py stage {a.skill}, edit {staged}, then propose (or --in-place)")
    return live, staged, staged


# ---------------------------------------------------------------- commands
def cmd_status(a, root, home, skills):
    rows = []
    for n, s in sorted(skills.items()):
        if s["origin"] != "root" or (a.skill and n != a.skill):
            continue
        ver, date = L.version_of(s["dir"])
        last = L.load_json(home / "evals" / f"{n}.last.json") or {}
        pk = Path(root) / "dist" / f"{n}.skill"
        props = sorted((home / "proposals").glob(f"{n}-*.json")) if (home / "proposals").exists() else []
        pend = [p for p in props if not (L.load_json(p) or {}).get("applied")]
        stale = ""
        if pk.exists():
            newest = max((p.stat().st_mtime for p in L.skill_files(s["dir"], text_only=False, packaged=True)), default=0)
            stale = "stale" if newest > pk.stat().st_mtime else "ok"
        rows.append([n, (ver if ver != "0.0.0" else "unversioned") + (f" ({date})" if date else ""), (last.get("summary", "-").split(": ", 1)[-1])[:60],
                     "yes" if (home / "stage" / n).exists() else "-",
                     ", ".join(p.stem.split("-")[-1] for p in pend) or "-", stale or "none"])
    print(L.md_table(["skill", "version", "last eval", "staged", "pending proposal", "dist/.skill"], rows))
    return 0


def cmd_stage(a, root, home, skills):
    live = skill_or_die(skills, a.skill)
    dst = home / "stage" / a.skill
    if dst.exists() and not a.force:
        print(f"already staged: {dst} (--force to restart from the live skill)")
        return 0
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(live, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    print(f"staged {a.skill} {L.version_of(live)[0]} -> {dst}\nedit there; then ship.py propose {a.skill} --bump patch "
          f"--summary '...' [--fixes IDS]")
    return 0


def cmd_diff(a, root, home, skills):
    live, cand, staged = candidate(a, home, skills)
    old = zip_texts(Path(root) / "dist" / f"{a.skill}.skill", a.skill) if a.in_place else dir_texts(live)
    stat, *_, lines = diff_trees(old, dir_texts(cand), a.max_lines)
    print("\n".join(lines))
    print(stat)
    return 0


def cmd_propose(a, root, home, skills):
    live, cand, staged = candidate(a, home, skills)
    cur, _ = L.version_of(live)
    new = "1.0.0" if cur == "0.0.0" else L.bump(cur, a.bump)
    old = zip_texts(Path(root) / "dist" / f"{a.skill}.skill", a.skill) if a.in_place else dir_texts(live)
    stat, changed, added, removed, dlines = diff_trees(old, dir_texts(cand))
    if not (changed or added or removed):
        L.die("no changes to propose", 1)
    ev = run_evals(a.skill, cand, root, home, skills, a.full)
    fr = L.load_json(home / "frictions.json", {}) or {}
    known = {i["id"]: i for i in fr.get("items", [])}
    unknown = [f for f in (a.fixes or []) if f not in known]
    tree = L.tree_hash(cand)
    entry = changelog_entry(new, a.section, a.summary, a.fixes, ev, None)
    prop = {"skill": a.skill, "from": cur, "version": new, "bump": a.bump, "summary": a.summary, "section": a.section,
            "fixes": a.fixes or [], "in_place": bool(a.in_place), "candidate": str(cand), "tree": tree,
            "evals_ok": ev["ok"], "eval_summary": ev["summary"], "stat": stat, "created": L.now(), "applied": None}
    pdir = home / "proposals"
    L.save_json(pdir / f"{a.skill}-{new}.json", prop)
    md = [f"# Proposal: {a.skill} {cur} -> {new} ({a.bump})", "",
          f"**Summary:** {a.summary}", f"**Evals:** {ev['summary']}", f"**Files:** {stat}",
          f"**Fixes:** {', '.join(a.fixes) if a.fixes else '-'}" + (f" (unknown ids: {', '.join(unknown)})" if unknown else ""),
          f"**Candidate:** {cand} (tree {tree})", "",
          "Owner: approve with `ship.py apply " + a.skill + " --approved \"owner <date> via <where>\"`, or reply "
          "with changes. Nothing ships without it.", "", "## Changelog entry", "", entry, "", "## Eval results", ""]
    md += [f"- {'ok' if r.get('pass') else ('skip' if r.get('pass') is None else 'FAIL')} {r['id']}"
           + (f": {r['why']}" if r.get("why") else "") for r in ev["results"]]
    if ev["triggers"]:
        md.append(f"- triggers {sum(t['pass'] for t in ev['triggers'])}/{len(ev['triggers'])} (lexical proxy)")
    md += ["", "## Diff", "", "```diff"] + dlines + ["```", ""]
    (pdir / f"{a.skill}-{new}.md").write_text("\n".join(md), encoding="utf-8")
    print(f"proposal: {pdir / f'{a.skill}-{new}.md'}\n{ev['summary']}\n{stat}")
    if not ev["ok"]:
        print("evals FAIL: fix the candidate and propose again; apply will refuse this proposal")
        return 1
    print(f"awaiting owner approval: ship.py apply {a.skill} --approved \"owner {L.today()} via chat\"")
    return 0


def changelog_entry(ver, section, summary, fixes, ev, approved):
    lines = [f"## [{ver}] - {L.today()}", f"### {section}", f"- {summary}" + (f" (fixes {', '.join(fixes)})" if fixes else "")]
    tail = f"Evals: {ev['summary'].split(': ', 1)[-1]}" if ev else ""
    if approved:
        tail += f"; approved: {approved}"
    if tail:
        lines.append(tail)
    return "\n".join(lines)


def write_changelog(d, name, entry):
    f = Path(d) / "CHANGELOG.md"
    text = L.read(f)
    if not text.strip():
        text = CL_HEAD.format(name=name)
    m = re.search(r"^## \[", text, re.M)
    text = (text[: m.start()] + entry + "\n\n" + text[m.start():]) if m else (text.rstrip() + "\n\n" + entry + "\n")
    f.write_text(text, encoding="utf-8")


def cmd_apply(a, root, home, skills):
    if not re.match(r"^owner\b", a.approved.strip(), re.I):
        L.die('only the owner approves: --approved "owner YYYY-MM-DD via <where>"', 2)
    live = skill_or_die(skills, a.skill)
    props = sorted((home / "proposals").glob(f"{a.skill}-*.json"), key=lambda p: p.stat().st_mtime) \
        if (home / "proposals").exists() else []
    props = [p for p in props if not (L.load_json(p) or {}).get("applied")]
    if not props:
        L.die(f"no pending proposal for {a.skill}: ship.py propose first", 1)
    pf = props[-1]
    prop = L.load_json(pf)
    if not prop["evals_ok"]:
        L.die(f"{pf.name}: its evals failed; fix and propose again", 1)
    cand = Path(prop["candidate"])
    if not cand.exists() or L.tree_hash(cand) != prop["tree"]:
        L.die(f"{cand} changed since the proposal (or is gone): propose again so the owner approves what ships", 1)
    cur, _ = L.version_of(live)
    if cur != prop["from"]:
        L.die(f"live {a.skill} is {cur}, the proposal was made from {prop['from']}: propose again", 1)
    ev = run_evals(a.skill, cand, root, home, skills, a.full)
    if not ev["ok"]:
        L.die(f"evals fail now: {ev['summary']}", 1)
    bdir = home / "backups" / f"{a.skill}-{cur}"
    last_pk = Path(root) / "dist" / f"{a.skill}.skill"
    if prop["in_place"] and last_pk.exists():  # live already holds the new edits: the old version is the last package
        bdir.mkdir(parents=True, exist_ok=True)
        backup = bdir / last_pk.name
        shutil.copy2(last_pk, backup)
    else:
        backup, _ = package(live, a.skill, bdir)
    if not prop["in_place"]:
        for p in L.skill_files(live, text_only=False, packaged=True):
            relp = p.relative_to(live)
            if not (cand / relp).exists():
                p.unlink()
        for p in L.skill_files(cand, text_only=False, packaged=False):
            dst = live / p.relative_to(cand)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
    write_changelog(live, a.skill, changelog_entry(prop["version"], prop["section"], prop["summary"], prop["fixes"], ev,
                                                   a.approved))
    pk, n = package(live, a.skill, a.dist or Path(root) / "dist")
    import evals  # noqa: E402
    final = evals.run_skill(a.skill, live, root, home, skills, {"builtin", "checks", "triggers"}, quick=True)
    evals.save_run(home, final, baseline=True)
    fr = L.load_json(home / "frictions.json")
    closed = 0
    if fr and prop["fixes"]:
        for it in fr["items"]:
            if it["id"] in prop["fixes"]:
                L.set_closed(home, it["fp"], {"status": "fixed", "by": f"{a.skill} {prop['version']} ({a.approved})",
                                              "date": L.today(), "id": it["id"]})
                it["status"] = "fixed"
                closed += 1
        L.save_json(home / "frictions.json", fr)
    prop["applied"] = {"when": L.now(), "by": a.approved, "package": str(pk), "backup": str(backup)}
    L.save_json(pf, prop)
    if not prop["in_place"]:
        shutil.rmtree(cand, ignore_errors=True)
    print(f"shipped {a.skill} {prop['version']} (approved: {a.approved}); package {pk} ({n} files); backup {backup}; "
          f"{closed} friction(s) closed; baseline saved. Not published or committed.")
    return 0


def cmd_package(a, root, home, skills):
    names = [n for n, s in sorted(skills.items()) if s["origin"] == "root"] if a.skill == "all" else [a.skill]
    for n in names:
        d = skill_or_die(skills, n)
        pk, k = package(d, n, a.dist or Path(root) / "dist")
        print(f"{n} {L.version_of(d)[0]}: {pk} ({k} files)")
    return 0


def cmd_init_changelog(a, root, home, skills):
    names = [n for n, s in sorted(skills.items()) if s["origin"] == "root"] if a.skill == "all" else [a.skill]
    for n in names:
        d = skill_or_die(skills, n)
        if (d / "CHANGELOG.md").exists():
            print(f"{n}: has CHANGELOG.md ({L.version_of(d)[0]})")
            continue
        write_changelog(d, n, f"## [{a.version}] - {L.today()}\n### Added\n- {a.note}")
        print(f"{n}: CHANGELOG.md started at {a.version}")
    return 0


def main(argv=None):
    ap = L.common_args(argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter))
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("status", help="versions, last eval, staged and pending proposals")
    p.add_argument("skill", nargs="?")
    p = sp.add_parser("stage", help="copy the live skill to the stage for editing")
    p.add_argument("skill")
    p.add_argument("--force", action="store_true")
    p = sp.add_parser("diff", help="show what would ship")
    p.add_argument("skill")
    p.add_argument("--in-place", action="store_true")
    p.add_argument("--max-lines", type=int, default=300)
    p = sp.add_parser("propose", help="eval the candidate and write a proposal for the owner")
    p.add_argument("skill")
    p.add_argument("--bump", required=True, choices=["patch", "minor", "major"])
    p.add_argument("--summary", required=True)
    p.add_argument("--section", default="Fixed", choices=["Fixed", "Changed", "Added", "Removed", "Security"])
    p.add_argument("--fixes", nargs="*", help="friction ids this closes (harvest.py list)")
    p.add_argument("--in-place", action="store_true", help="candidate = live folder; diff vs dist/SKILL.skill")
    p.add_argument("--full", action="store_true", help="also run checks marked slow (full selftests)")
    p = sp.add_parser("apply", help="ship an approved proposal (owner only)")
    p.add_argument("skill")
    p.add_argument("--approved", required=True, help='"owner YYYY-MM-DD via chat"')
    p.add_argument("--full", action="store_true")
    p.add_argument("--dist")
    p = sp.add_parser("package", help="validate + zip the live skill (no version change)")
    p.add_argument("skill")
    p.add_argument("--dist")
    p = sp.add_parser("init-changelog", help="start CHANGELOG.md where missing")
    p.add_argument("skill")
    p.add_argument("--version", default="1.0.0")
    p.add_argument("--note", default="First versioned release (overnight build, trial and fix round).")
    L.common_sub(sp)
    a = ap.parse_args(argv)
    root = L.find_root(a.root)
    home = L.ensure_home(L.smith_home(root, a.home))
    skills = L.web(root)
    return {"status": cmd_status, "stage": cmd_stage, "diff": cmd_diff, "propose": cmd_propose, "apply": cmd_apply,
            "package": cmd_package, "init-changelog": cmd_init_changelog}[a.cmd](a, root, home, skills)


if __name__ == "__main__":
    sys.exit(main())
