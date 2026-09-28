#!/usr/bin/env python3
"""release.py - Risky Rails release manager (rr-release-train). One release in flight at <R>/next/.

  status                                   where the release stands and the next step (start every session here)
  init [--channel alpha|beta|live]         open <R>/next/
  config [--place NAME --universe U --place-id P [--start] [--route auto|api|studio]] [--repo PATH[:game|tools]]
         [--missions DIR] [--luau-tests on|off] [--bleed MIN]   <R>/config.json (Open Cloud IDs, repos, options)
  attach NAME FILE                         pin a place file (.rbxl/.rbxlx): copy, sha256, audit, extract scripts
  collect [--repo P] [--since REF] [--include-tools]   git log + finished missions + script diff -> changes
  add "TITLE" [--section S --audience player|internal --bump B --note TEXT]   owner-stated change
  mark C-1 [C-2..] [--in-build yes|no|unknown --audience A --section S --bump B --title T --note N]
  changes                                  list changes
  version [--set X.Y.Z[-pre]]              next semver from history + the biggest in-build bump
  changelog [--apply [PATH]]               Keep a Changelog section (--apply prepends to <R>/CHANGELOG.md)
  notes                                    NOTES_BRIEF.md for writing PATCH_NOTES.src.md + STORE_UPDATE.src.txt
  notes-check                              trace/coverage/voice/limits/canon -> PATCH_NOTES.md, STORE_UPDATE.txt
  stamp                                    RR_Version.lua (ModuleScript for ReplicatedStorage)
  evidence KIND --result pass|fail --by owner [--note N] [--file F]   KIND: tests bugbash livecheck perf security
  waive GATE --by owner --reason TEXT      owner accepts a failing or pending gate
  gate                                     G1-G10 -> GATES.md; exit 0 GO, 1 NO-GO
  approve --by owner --via "chat DATE"     owner approval bound to version + file hashes + gate report
  plan                                     PUBLISH_PLAN.md, SMOKE.md, ROLLBACK.md
  publish [--live --confirm VERSION] [--restart]      DRY-RUN unless --live
  record --place NAME=VERSION_NUMBER ... --by owner   owner published from Studio
  smoke [--result S1=pass,S2=fail --by owner]         post-release checklist; P0 fail -> rollback advice
  rollback [--live --confirm PREV --by owner] [--restart]   re-publish the previous release (DRY-RUN default)
  abandon --reason TEXT                    shelve next/ under <R>/abandoned/

<R> = --root, $RR_RELEASES_ROOT, or <git top of cwd>/releases. Canon via rr-bible (glob or $RR_BIBLE_SKILL).
Never publishes without --live, owner approval, $ROBLOX_API_KEY and --confirm. Exit: 0 ok, 1 check failed, 2 usage.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gates  # noqa: E402
import opencloud  # noqa: E402
import placefile  # noqa: E402
from gates import canon_limit, place_route, release_route  # noqa: E402
from rtlib import (LEVELS, SKILL, Bible, die, git_top, history, last_release, load_json,  # noqa: E402
                   load_presets, missions_roots, next_version, now, parse_ver, releases_root, released_versions,
                   save_json, sha256_file, today, ver_key)

SECTIONS = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security", "Internal"]
AUDIENCES = ["player", "internal"]
BUMPS = ["major", "minor", "patch", "none"]
OWNER_KINDS = ("tests", "bugbash", "livecheck", "perf")


# ---------------------------------------------------------------- state
class Ctx:
    def __init__(self, a):
        self.a = a
        self.root = releases_root(getattr(a, "root", None))
        self.dir = Path(a.dir).resolve() if getattr(a, "dir", None) else self.root / "next"
        self.presets = load_presets()
        self._bible = None
        self.cfg = load_json(self.root / "config.json", {}) or {}
        for k, v in {"places": [], "repos": [], "missions": [], "luau_tests": True, "bleed_minutes": 10}.items():
            self.cfg.setdefault(k, v)
        self.rel = load_json(self.dir / "release.json")

    @property
    def bible(self):
        if self._bible is None:
            self._bible = Bible()
        return self._bible

    def need(self):
        if not self.rel:
            die(f"no release in flight at {self.dir}: run `release.py init`")
        return self.rel

    def save(self):
        self.rel["updated"] = now()
        save_json(self.dir / "release.json", self.rel)

    def save_cfg(self):
        save_json(self.root / "config.json", self.cfg)

    def place_cfg(self, name):
        return next((p for p in self.cfg["places"] if p["name"] == name), None)

    def change(self, cid):
        c = next((c for c in self.rel["changes"] if c["id"] == cid), None)
        if not c:
            die(f"no change {cid}; `release.py changes` lists them")
        return c

    def included(self):
        return [c for c in self.rel["changes"] if c.get("in_build") == "yes"]

    def channel_pre(self):
        return self.presets["channels"][self.rel["channel"]]["prerelease"]


def owner_only(by, what):
    if (by or "").strip().lower() != "owner":
        die(f"{what} is the owner's call: pass --by owner only when the owner said so (cite it with --via/--note).")


def rel_path(ctx, p):
    try:
        return str(Path(p).resolve().relative_to(ctx.dir))
    except ValueError:
        return str(p)


def ordered_places(ctx):
    """Non-start places first, the start place last (players enter through it)."""
    names = list(ctx.rel.get("places", {}))
    return sorted(names, key=lambda n: (bool((ctx.place_cfg(n) or {}).get("start")), n))


# ---------------------------------------------------------------- commands: setup
def cmd_init(ctx):
    if ctx.rel and not ctx.a.force:
        die(f"a release is already in flight at {ctx.dir} ({ctx.rel.get('version') or 'no version yet'}): "
            "`release.py status`, or `abandon` it first")
    ch = ctx.a.channel or ctx.cfg.get("channel") or "alpha"
    ctx.dir.mkdir(parents=True, exist_ok=True)
    ctx.rel = {"version": None, "channel": ch, "created": now(), "changes": [], "next_id": 1, "places": {},
               "repos": {}, "evidence": {}, "waivers": {}, "approval": None, "gate": None, "status": "draft"}
    ctx.save()
    last = last_release(ctx.root)
    print(f"opened {ctx.dir} (channel {ch}; last release {last['version'] if last else 'none'})")
    print("next: attach the place files (`attach Lobby Lobby.rbxl`), then `collect`")


def cmd_config(ctx):
    a, cfg = ctx.a, ctx.cfg
    if a.place:
        pc = ctx.place_cfg(a.place) or {"name": a.place}
        if pc not in cfg["places"]:
            cfg["places"].append(pc)
        if a.universe:
            pc["universe_id"] = int(a.universe)
        if a.place_id:
            pc["place_id"] = int(a.place_id)
        if a.start:
            for p in cfg["places"]:
                p["start"] = p is pc
        if a.route:
            pc["route"] = a.route
    for r in a.repo or []:
        path, _, kind = r.partition(":") if re.match(r"^[^:]+:(game|tools)$", r) else (r, "", "")
        path = str(Path(path).expanduser().resolve())
        cfg["repos"] = [x for x in cfg["repos"] if x["path"] != path] + [{"path": path, "kind": kind or "auto"}]
    for m in a.missions or []:
        m = str(Path(m).expanduser().resolve())
        if m not in cfg["missions"]:
            cfg["missions"].append(m)
    if a.luau_tests:
        cfg["luau_tests"] = a.luau_tests == "on"
    if a.bleed is not None:
        cfg["bleed_minutes"] = max(0, min(60, a.bleed))
    if a.channel:
        cfg["channel"] = a.channel
    ctx.save_cfg()
    print(json.dumps(cfg, indent=1))


def cmd_attach(ctx):
    rel = ctx.need()
    src = Path(ctx.a.file).expanduser().resolve()
    if not src.is_file() or src.suffix.lower() not in (".rbxl", ".rbxlx"):
        die(f"{src}: need an existing .rbxl or .rbxlx (Rojo users: `rojo build -o place.rbxl` first)")
    name = ctx.a.name
    pdir = ctx.dir / "places" / name
    if pdir.exists():
        shutil.rmtree(pdir)
    pdir.mkdir(parents=True)
    dst = pdir / src.name
    shutil.copy2(src, dst)
    try:
        P = placefile.load(dst)
    except (OSError, placefile.PlaceError) as e:
        die(f"cannot read {src.name}: {e}", 1)
    aud = placefile.write_audit(P, pdir / "audit")
    rel["places"][name] = {"file": rel_path(ctx, dst), "src": str(src), "sha256": aud["sha256"], "bytes": aud["bytes"],
                           "format": aud["format"], "attached_at": now(), "stamp": aud["stamp_version"],
                           "instances": aud["instances"], "audit": rel_path(ctx, pdir / "audit" / "audit.json")}
    ctx.save()
    route, why = place_route(ctx, name, rel["places"][name])
    c = aud["counts"]
    print(f"{name}: {aud['format']} {aud['bytes']} B sha {aud['sha256'][:12]} | {aud['instances']} instances, "
          f"{c['scripts']} scripts -> {rel_path(ctx, pdir / 'audit' / 'scripts')} | stamp {aud['stamp_version'] or 'none'}"
          f" | route {route}" + (f" ({'; '.join(why)})" if why else ""))
    if rel.get("approval"):
        print("note: files changed after approval; the approval no longer matches (re-run gate + approve)")


# ---------------------------------------------------------------- commands: changes
def new_change(ctx, **kw):
    rel = ctx.rel
    c = {"id": f"C-{rel['next_id']}", "section": "Changed", "audience": "player", "bump": "patch", "in_build": "yes",
         "note": ""}
    c.update(kw)
    rel["next_id"] += 1
    rel["changes"].append(c)
    return c


def shipped_srcs(ctx):
    return {s for h in history(ctx.root) if h.get("status") != "abandoned" for s in h.get("shipped", [])}


def repo_kind(path, declared, presets):
    if declared in ("game", "tools"):
        return declared
    p = Path(path)
    if any(list(p.glob(m)) for m in presets["game_repo_markers"]):
        return "game"
    if any((p / m).exists() for m in presets["tools_repo_markers"]):
        return "tools"
    return "game"


def classify_commit(subject, body, presets):
    """(section, bump, title, audience, note, skip)."""
    m = re.match(r"^(\w+)(\([^)]*\))?(!)?:\s*(.+)$", subject)
    trailers = dict((k.lower(), v.strip()) for k, v in re.findall(r"^(Player-Note|Release-Note):\s*(.+)$", body, re.M | re.I))
    skip = trailers.get("release-note", "").lower() in ("skip", "none", "internal")
    if m and m.group(1).lower() in presets["conventional"]:
        section, bump = presets["conventional"][m.group(1).lower()]
        title = m.group(4)
        if m.group(3) or "BREAKING CHANGE" in body:
            bump = "major"
    else:
        title, section, bump = (m.group(4) if m else subject), "Changed", "patch"
        for rx, sec, b in presets["keywords"]:
            if re.search(rx, title, re.I):
                section, bump = sec, b
                break
    audience = "internal" if section == "Internal" or skip else "player"
    return section, bump, title[:1].upper() + title[1:], audience, trailers.get("player-note", ""), skip


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return r.returncode, r.stdout


def collect_git(ctx, report):
    a, rel = ctx.a, ctx.rel
    repos = [{"path": str(Path(r.split(":")[0]).resolve()), "kind": r.split(":")[1] if ":" in r else "auto"}
             for r in (a.repo or [])] or ctx.cfg["repos"]
    if not repos and git_top():
        repos = [{"path": str(git_top()), "kind": "auto"}]
    last = last_release(ctx.root) or {}
    have = {c["src"] for c in rel["changes"]}
    shipped = shipped_srcs(ctx)
    for r in repos:
        path, kind = r["path"], repo_kind(r["path"], r.get("kind"), ctx.presets)
        code, head = git(path, "rev-parse", "HEAD")
        if code:
            report.append(f"git {path}: not a git repo, skipped")
            continue
        head = head.strip()
        since = a.since or (last.get("repos") or {}).get(path)
        rng = [f"{since}..HEAD"] if since and git(path, "merge-base", "--is-ancestor", since, "HEAD")[0] == 0 else []
        code, out = git(path, "log", "--no-merges", "--reverse", "-n", str(a.max), "--format=%H%x1f%ad%x1f%s%x1f%b%x1e",
                        "--date=short", *rng)
        commits = [x.strip("\n").split("\x1f") for x in out.split("\x1e") if x.strip()]
        rel["repos"][path] = head
        name = Path(path).name
        if kind == "tools" and not a.include_tools:
            report.append(f"git {name}: tooling repo, {len(commits)} commits since "
                          f"{since[:8] if rng else 'the start'} not listed (--include-tools lists them as Internal)")
            continue
        added = 0
        for sha, date, subj, body in commits:
            src = f"git:{name}@{sha[:10]}"
            if src in have or src in shipped:
                continue
            section, bump, title, audience, note, skip = classify_commit(subj, body, ctx.presets)
            if kind == "tools":
                section, bump, audience = "Internal", "none", "internal"
            new_change(ctx, src=src, title=title, section=section, bump=bump, audience=audience, note=note,
                       date=date, in_build="yes")
            added += 1
        report.append(f"git {name} ({kind}): {added} new changes from {len(commits)} commits"
                      + (f" since {since[:8]}" if rng else ""))


def ledger_summary(crit_dir, bar):
    rows = load_json(crit_dir / "ledger.json", []) or []
    if not rows:
        return None
    stand, agents = {}, {}
    for r in rows:
        for c, s in (r.get("scores") or {}).items():
            stand[c], agents[c] = s, (r.get("agent") or "").strip()
    overall = min(stand.values()) if stand else None
    who = set(agents.values())
    certified = bool(who) and all(w and "self" not in w.lower() for w in who)
    return {"dir": str(crit_dir), "overall": overall, "bar": bar, "passes": len(rows), "certified": certified,
            "agents": sorted(w or "(unrecorded)" for w in who)}


def mission_title(mdir, slug, kind):
    mm = mdir / "mission.md"
    if mm.is_file():
        m = re.search(r"^Objective:\s*(.+)$", mm.read_text(errors="replace"), re.M)
        if m:
            obj = m.group(1).strip()
            head = obj.split(",")[0].strip()
            return (head if len(head) >= 25 else obj)[:140]
    words = re.sub(r"^\d{6}-", "", slug).replace("-", " ")
    return f"{words[:1].upper() + words[1:]} ({kind or 'mission'} {slug})"


def collect_missions(ctx, report):
    have, shipped = {c["src"] for c in ctx.rel["changes"]}, shipped_srcs(ctx)
    roots = missions_roots(ctx.cfg["missions"] + (ctx.a.missions or []))
    open_ = []
    for root in roots:
        for st_path in sorted(root.glob("*/state.json")):
            mdir, st = st_path.parent, load_json(st_path, {}) or {}
            src = f"mission:{mdir.name}"
            if src in have or src in shipped:
                continue
            if st.get("status") != "done":
                open_.append(mdir.name)
                continue
            kind, bar = st.get("kind"), st.get("bar") or 8
            crit = [s for s in (ledger_summary(d, bar) for d in sorted(mdir.glob("critique*")) if d.is_dir()) if s]
            new_change(ctx, src=src, title=mission_title(mdir, mdir.name, kind), section="Added",
                       bump=ctx.presets["mission_bump"].get(kind, ctx.presets["mission_bump"]["default"]),
                       audience="player", in_build="unknown",
                       mission={"dir": str(mdir), "kind": kind, "bar": bar, "critic": crit})
        report.append(f"missions {root}: scanned")
    if open_:
        report.append("missions not done (not collected): " + ", ".join(open_))


def script_index(audit_dir):
    idx = load_json(Path(audit_dir) / "scripts" / "index.json", []) or []
    out = {}
    for e in idx:
        f = Path(audit_dir) / "scripts" / e["file"]
        out[e["path"]] = (sha256_file(f), f.read_text(errors="replace").count("\n") + 1) if f.is_file() else ("", 0)
    return out


def collect_place_diff(ctx, report):
    last = last_release(ctx.root)
    if not last:
        report.append("place diff: no previous release to compare with")
        return
    for name, info in ctx.rel["places"].items():
        prev_dir = ctx.root / last["version"] / "places" / name / "audit"
        if not prev_dir.is_dir():
            report.append(f"place diff {name}: no archived audit for {last['version']}")
            continue
        old, new = script_index(prev_dir), script_index(ctx.dir / Path(info["audit"]).parent)
        added = sorted(set(new) - set(old))
        removed = sorted(set(old) - set(new))
        changed = sorted(p for p in set(new) & set(old) if new[p][0] != old[p][0])
        ctx.rel["changes"] = [c for c in ctx.rel["changes"] if not c["src"].startswith(f"place:{name}:")]
        if not (added or removed or changed):
            report.append(f"place diff {name}: no script changes since {last['version']}")
            continue
        short = lambda ps: ", ".join(p.split(".")[-1] for p in ps[:6]) + (f" +{len(ps) - 6}" if len(ps) > 6 else "")
        parts = [f"{len(x)} {w} ({short(x)})" for x, w in ((changed, "changed"), (added, "added"), (removed, "removed")) if x]
        new_change(ctx, src=f"place:{name}:{info['sha256'][:10]}", title=f"{name} scripts since {last['version']}: "
                   + "; ".join(parts), section="Internal", bump="none", audience="internal", in_build="yes",
                   scripts={"changed": changed, "added": added, "removed": removed})
        report.append(f"place diff {name}: " + "; ".join(parts) + " -> make sure a change describes each")


def cmd_collect(ctx):
    ctx.need()
    report = []
    collect_git(ctx, report)
    collect_missions(ctx, report)
    collect_place_diff(ctx, report)
    ctx.save()
    print("\n".join(report))
    print_changes(ctx)
    unk = [c["id"] for c in ctx.rel["changes"] if c.get("in_build") == "unknown"]
    mis = [c["id"] for c in ctx.rel["changes"] if c["src"].startswith("mission:")]
    if mis:
        print(f"mission titles are dev objectives: retitle {', '.join(mis)} in player words (`mark C-n --title ...`)")
    if unk:
        print(f"next: confirm what is really in this build: `mark {' '.join(unk)} --in-build yes|no` "
              "(missions are only in the game once the owner placed them in Studio)")
    else:
        print("next: `version`")


def print_changes(ctx):
    for c in ctx.rel["changes"]:
        print(f"{c['id']:>5} [{c.get('in_build', '?'):^7}] {c['audience']:<8} {c['section']:<8} {c['bump']:<5} "
              f"{c['src'][:34]:<34} {c['title'][:90]}")
    if not ctx.rel["changes"]:
        print("(no changes yet: `collect`, or `add \"what changed\"`)")


def cmd_add(ctx):
    ctx.need()
    a = ctx.a
    c = new_change(ctx, src=f"manual:{ctx.rel['next_id']}", title=a.title, section=a.section, audience=a.audience,
                   bump=a.bump, note=a.note or "", in_build="yes")
    ctx.save()
    print(f"{c['id']} added: {c['section']}/{c['bump']}/{c['audience']}: {c['title']}")


def cmd_mark(ctx):
    ctx.need()
    a = ctx.a
    for cid in a.ids:
        c = ctx.change(cid)
        for k in ("in_build", "audience", "section", "bump", "title", "note"):
            v = getattr(a, k)
            if v is not None:
                c[k] = v
    ctx.save()
    print_changes(ctx)


def cmd_changes(ctx):
    ctx.need()
    print_changes(ctx)


# ---------------------------------------------------------------- commands: version, changelog, notes, stamp
def max_bump(changes):
    return max((c["bump"] for c in changes), key=lambda b: LEVELS[b], default="none")


def cmd_version(ctx):
    rel = ctx.need()
    inc = ctx.included()
    if not inc:
        die("no in-build changes: `collect` / `add` / `mark --in-build yes` first", 1)
    level = max_bump(inc)
    hist = released_versions(ctx.root)
    if ctx.a.set:
        v = ctx.a.set.lstrip("v")
        if not parse_ver(v):
            die(f"{v} is not semver (X.Y.Z or X.Y.Z-alpha.N)")
        if hist and ver_key(v) <= max(ver_key(h) for h in hist):
            die(f"{v} is not above the last released version {max(hist, key=ver_key)}")
        pre = parse_ver(v)[3].split(".")[0]
        if pre != ctx.channel_pre():
            print(f"warning: {v} does not carry the '{ctx.channel_pre() or 'no'}' tag of channel {rel['channel']}")
    else:
        v = next_version(hist, level, ctx.channel_pre())
    rel["version"], rel["bump"] = v, level
    ctx.save()
    why = [c["id"] for c in inc if c["bump"] == level][:6]
    print(f"{v}  ({level} bump from {', '.join(why) or 'none'}; channel {rel['channel']}; scheme OQ-037 default A)")
    print("next: `changelog`, `notes`, `stamp`")


def changelog_section(ctx):
    rel = ctx.rel
    by = {s: [] for s in SECTIONS}
    for c in ctx.included():
        by.setdefault(c["section"], []).append(c)
    lines = [f"## [{rel['version']}] - {today()}", ""]
    for s in SECTIONS:
        if by.get(s):
            lines.append(f"### {s}")
            lines += [f"- {c['title']} ({c['id']})" for c in by[s]]
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def cmd_changelog(ctx):
    rel = ctx.need()
    if not rel.get("version"):
        die("run `version` first")
    sec = changelog_section(ctx)
    (ctx.dir / "CHANGELOG.section.md").write_text(sec)
    print(sec)
    if ctx.a.apply is not None:
        target = Path(ctx.a.apply or ctx.root / "CHANGELOG.md")
        head = ("# Changelog\n\nAll notable changes to Risky Rails. Format: Keep a Changelog "
                "(https://keepachangelog.com/en/1.1.0/); versions: semver (rr-bible OQ-037).\n\n")
        text = target.read_text() if target.is_file() else head
        text = re.sub(rf"## \[{re.escape(rel['version'])}\].*?(?=^## \[|\Z)", "", text, flags=re.S | re.M)
        i = text.find("\n## [")
        text = (text.rstrip() + "\n\n" + sec) if i < 0 else (text[:i + 1] + sec + "\n" + text[i + 1:])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        print(f"prepended to {target}")


def voice_lines(ctx):
    b = ctx.bible
    out = []
    for key in ("identity.tone.company", "identity.tone.comedy_tell", "identity.tone.not", "release.store.title",
                "release.store.metadata_rules", "release.alpha.sidings"):
        v = b.value(key)
        if v:
            out.append(f"- `{key}`: {v}")
    lex = [f["value"] for f in b.facts("world.lexicon")]
    if lex:
        out.append("- lexicon (verbatim when used): " + " · ".join(lex))
    banned = [f["value"] for f in b.facts("world.banned")]
    if banned:
        out.append("- never write: " + " · ".join(banned))
    d7 = b.get("D-007")
    if isinstance(d7, dict):
        out.append(f"- D-007 {d7.get('title', '')}: {(d7.get('fields') or {}).get('decision', '')}")
    oq = b.get("OQ-038")
    if isinstance(oq, dict) and (oq.get("fields") or {}).get("status", "open") == "open":
        dflt = (oq.get("fields") or {}).get("default", "")
        opt = dict(oq.get("options") or []).get(dflt[:1], "")
        out.append(f"- voice rule (OQ-038 default {dflt[:1]}, assumed until the owner decides): {opt}")
    return out or ["- rr-bible not found: set RR_BIBLE_SKILL; do not write notes without the voice slice"]


def cmd_notes(ctx):
    rel = ctx.need()
    if not rel.get("version"):
        die("run `version` first")
    n = ctx.presets["notes"]
    player = [c for c in ctx.included() if c["audience"] == "player"]
    internal = [c for c in ctx.included() if c["audience"] != "player"]
    L = [f"# Notes brief · {rel['version']} ({rel['channel']})", "",
         "Write two files next to this brief, then run `release.py notes-check`:",
         f"- `PATCH_NOTES.src.md`: the Discord post. `# ` headline, bullets, one sign-off line; "
         f"<= {n['discord_max']} characters once tags are stripped.",
         f"- `STORE_UPDATE.src.txt`: one line for the store description, <= {n['store_max']} characters; "
         f"optional second line `TITLE: <experience title>` (<= {n['title_max']} characters, pattern below).",
         "Rules: every bullet starts `- ` and ends with the tags of the changes it describes, e.g. "
         "`- Coal lasts longer on Easy. [C-4]`; headline and sign-off carry no tags. Cover every player change; "
         "say only what the change says; numbers only from the change or canon; nothing about internal work.", "",
         "## Player changes (cover every one)"]
    L += [f"- [{c['id']}] {c['section']}: {c['title']}" + (f" | wording hint: {c['note']}" if c.get("note") else "")
          for c in player] or ["- (none: an internal-only release; say so in one line or skip notes)"]
    L += ["", "## Not for players (never mention)"]
    L += [f"- [{c['id']}] {c['title'][:120]}" for c in internal] or ["- (none)"]
    L += ["", "## Voice (read from rr-bible just now)"] + voice_lines(ctx)
    (ctx.dir / "NOTES_BRIEF.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nwrote {ctx.dir / 'NOTES_BRIEF.md'}")


def cmd_notes_check(ctx):
    ctx.need()
    res = gates.notes_check(ctx)
    for lvl in ("errors", "warnings"):
        for m in res[lvl]:
            print(f"{lvl[:-1].upper()}: {m}")
    print(("notes-check PASS" if res["ok"] else "notes-check FAIL") + f" -> {', '.join(res['outputs']) or 'no outputs'}")
    return 0 if res["ok"] else 1


def cmd_stamp(ctx):
    rel = ctx.need()
    if not rel.get("version"):
        die("run `version` first")
    lua = ("-- RR_Version (generated by rr-release-train; regenerate, do not edit). ModuleScript in ReplicatedStorage.\n"
           "-- The Luau release tests and the smoke check read it to prove which build a server runs.\n"
           f'return {{\n\tversion = "{rel["version"]}",\n\tchannel = "{rel["channel"]}",\n\tbuilt = "{now()}",\n}}\n')
    out = ctx.dir / "RR_Version.lua"
    out.write_text(lua)
    rel["stamp_file"] = rel_path(ctx, out)
    ctx.save()
    print(lua)
    print(f"wrote {out}\nowner: Studio -> ReplicatedStorage -> ModuleScript named RR_Version -> paste -> File > Save; "
          "then re-export the place and `attach` it again (G1 checks the stamp inside the file)")


# ---------------------------------------------------------------- commands: evidence, waive, gate, approve
def cmd_evidence(ctx):
    rel = ctx.need()
    a = ctx.a
    if a.kind in OWNER_KINDS:
        owner_only(a.by, f"recording {a.kind} results")
    e = {"result": a.result, "by": a.by or "file", "note": a.note or "", "at": now()}
    if a.file:
        f = Path(a.file).expanduser().resolve()
        if not f.is_file():
            die(f"{f} not found")
        e["file"], e["sha256"] = str(f), sha256_file(f)
    rel["evidence"][a.kind] = e
    ctx.save()
    print(f"evidence {a.kind}: {a.result} ({e['by']}) {e['note']}")


def cmd_waive(ctx):
    rel = ctx.need()
    owner_only(ctx.a.by, "waiving a gate")
    g = ctx.a.gate.upper()
    if g not in ctx.presets["gate_names"] or g == "G1":
        die(f"{g}: waivable gates are G2-G10")
    rel["waivers"][g] = {"by": "owner", "reason": ctx.a.reason, "at": now()}
    ctx.save()
    print(f"{g} waived by owner: {ctx.a.reason}" + ("  (security waiver: say so in the debrief)" if g == "G5" else ""))


def cmd_gate(ctx):
    ctx.need()
    rep = gates.run(ctx)
    for g in rep["gates"]:
        print(f"{g['id']:<4} {g['name']:<15} {g['status']:<8} {g['summary']}")
    print(f"verdict: {rep['verdict']}  -> {ctx.dir / 'GATES.md'}")
    if rep["fixes"]:
        print("fix first:\n" + "\n".join(f"  {x}" for x in rep["fixes"][:12]))
    return 0 if rep["verdict"].startswith("GO") else 1


def binding(ctx):
    rel = ctx.rel
    notes = ctx.dir / "PATCH_NOTES.md"
    return {"version": rel.get("version"), "places": {n: i["sha256"] for n, i in sorted(rel["places"].items())},
            "gates": (rel.get("gate") or {}).get("hash"), "notes": sha256_file(notes) if notes.is_file() else None}


def approval_state(ctx):
    ap = ctx.rel.get("approval")
    if not ap:
        return False, "not approved"
    for n, i in ctx.rel["places"].items():
        f = ctx.dir / i["file"]
        if not f.is_file() or sha256_file(f) != i["sha256"]:
            return False, f"{n} file changed on disk"
    cur = binding(ctx)
    diff = [k for k in cur if cur[k] != ap["binding"].get(k)]
    return (not diff), ("valid" if not diff else "void: " + ", ".join(diff) + " changed since approval")


def cmd_approve(ctx):
    rel = ctx.need()
    owner_only(ctx.a.by, "approving a release")
    rep = gates.run(ctx)
    if not rep["verdict"].startswith("GO"):
        die(f"gate verdict is {rep['verdict']}: fix or waive first (`release.py gate`)", 1)
    if not rel["places"]:
        die("no place files attached", 1)
    rel["approval"] = {"by": "owner", "via": ctx.a.via, "at": now(), "binding": binding(ctx)}
    rel["status"] = "approved"
    ctx.save()
    print(f"approved {rel['version']} (owner, {ctx.a.via}); bound to {len(rel['places'])} place hashes + gate report")
    print("next: `plan`, then `publish` (dry run) and, from a machine that can reach the API, "
          f"`publish --live --confirm {rel['version']}`")


# ---------------------------------------------------------------- commands: plan, publish, record
def smoke_items(ctx):
    b, rel = ctx.bible, ctx.rel
    v = rel.get("version") or "?"
    items = [("S1", "P0", f"Join a fresh live server: no red errors in F9; F9 server console "
                          f"`print(require(game.ReplicatedStorage.RR_Version).version)` prints {v}"),
             ("S2", "P0", "One full trip with 2+ players through the funnel: "
                          + (b.value("release.kpi.funnel") or "join, tool, coal, lever, bank, run end")),
             ("S3", "P0", "Coins banked at results survive teleport home and a rejoin ("
                          + (b.value("tech.data.award_order") or "award, end session, teleport") + ")"),
             ("S4", "P1", "Creator Hub > Analytics > Error Report and the F9 server log: no new error spike in the "
                          "first 30 minutes")]
    minor = LEVELS.get(rel.get("bump", "patch"), 1) >= LEVELS["minor"]
    if minor:
        items.append(("S5", "P1", "Live check: " + (b.value("tech.streaming.live_check") or "3+ players incl. a phone")))
    n = len(items)
    for c in [c for c in ctx.included() if c["audience"] == "player"][:8]:
        n += 1
        items.append((f"S{n}", "P1", f"{c['id']} works as the patch notes say: {c['title'][:100]}"))
    items.append((f"S{n + 1}", "P2", "Old servers drained: every server you join shows the new version (S1 check)"))
    return items


def write_plan_docs(ctx):
    rel, cfg = ctx.rel, ctx.cfg
    v = rel.get("version") or "(no version)"
    ok_ap, ap_why = approval_state(ctx)
    reach, reach_why = opencloud.probe()
    key = bool(opencloud.api_key())
    L = [f"# Publish plan · {v} ({rel['channel']})", "",
         f"Preconditions now: approval {ap_why} · ${opencloud.KEY_ENV} {'set' if key else 'NOT set'} · "
         f"API host {reach_why} · Luau tests on saved version: {'on' if cfg['luau_tests'] else 'off'}", "",
         f"**Route for this release: {release_route(ctx)[0].upper()}** (one route for every place so they go live "
         "together)" + ("".join(f"\n- {x}" for x in release_route(ctx)[1]) if release_route(ctx)[1] else ""), "",
         "| order | place | route | file | sha256 | why |", "|---|---|---|---|---|---|"]
    for i, n in enumerate(ordered_places(ctx), 1):
        info = rel["places"][n]
        route, why = place_route(ctx, n, info)
        L.append(f"| {i} | {n}{' (start)' if (ctx.place_cfg(n) or {}).get('start') else ''} | {route} | "
                 f"{info['file']} | {info['sha256'][:12]} | {'; '.join(why) or '-'} |")
    L += ["", "## Steps (API route)",
          "1. Archive: the attached files in `places/` are the release archive (rollback source for the next one).",
          "2. `release.py publish` (dry run): prints every request; fix anything it lists as missing.",
          f"3. From a machine that reaches apis.roblox.com with the key set: `release.py publish --live --confirm {v}`"
          " [--restart]. It uploads each place as **Saved**, runs `assets/luau/run_tests.lua` on each saved"
          " version (specs + RR_Version), and only if all pass uploads each as **Published**, start place last.",
          f"4. Servers: `--restart` restarts old-version servers with a {cfg['bleed_minutes']}-minute bleed-off"
          " (needs universe:write), or Creator Hub > experience > ... > Restart Servers for Updates.",
          "5. Run SMOKE.md within the first hour; any P0 fail -> ROLLBACK.md.", "",
          "## Steps (Studio route)",
          "1. Open the exact attached file in Studio (sha256 above), File > Publish to Roblox.",
          "2. Note each place's new version number (Creator Hub > place > Version History).",
          "3. `release.py record --place NAME=VERSION ... --by owner`, then SMOKE.md.", "",
          "Timing: publish when you can watch the first hour, outside the owner-on-the-train sessions "
          f"(`release.ops.timetable`: {ctx.bible.value('release.ops.timetable') or 'n/a'})."]
    (ctx.dir / "PUBLISH_PLAN.md").write_text("\n".join(L) + "\n")
    S = [f"# Smoke checklist · {v}", "", "Run on live servers right after publishing. Record: "
         "`release.py smoke --result S1=pass,S2=fail --by owner`. Any P0 fail -> roll back (ROLLBACK.md).", "",
         "| id | prio | check | result |", "|---|---|---|---|"]
    S += [f"| {i} | {p} | {t} | |" for i, p, t in smoke_items(ctx)]
    (ctx.dir / "SMOKE.md").write_text("\n".join(S) + "\n")
    last = last_release(ctx.root)
    R = [f"# Rollback plan · {v}", "",
         "Trigger: any P0 smoke fail, joins failing, coins or purchases lost, or an error spike. Decide within minutes; "
         "a rollback is cheaper than a hotfix under pressure.", ""]
    if last:
        R.append(f"Target: {last['version']} (released {last.get('date', '?')}).")
        R.append("")
        R.append("| place | previous version number | archived file | route |")
        R.append("|---|---|---|---|")
        for n, p in (last.get("places") or {}).items():
            f = ctx.root / last["version"] / p.get("file", "")
            R.append(f"| {n} | {p.get('version_number', '?')} | {f if f.is_file() else 'missing'} | "
                     f"{'API re-publish' if f.is_file() else 'Creator Hub version history'} |")
        R += ["", f"A. API: `release.py rollback` (dry run), then `release.py rollback --live --confirm {last['version']}"
              " --by owner --restart` (re-publishes the archived files; new version numbers, same content).",
              "B. Creator Hub > Creations > the experience > Places > each place > Version History: restore the"
              " previous version number above, then Restart Servers for Updates."]
    else:
        R += ["Target: none recorded (first release through rr-release-train).",
              "Creator Hub > Creations > the experience > Places > each place > Version History: restore the version"
              " before this publish, then Restart Servers for Updates."]
    store = ctx.bible.value("tech.data.store_name") or "the canon data store"
    R += ["", "Data: DataStore writes are not rolled back. If this release changed the saved profile shape, the "
          f"previous build must still read profiles this one wrote ({store}); if it cannot, fix forward instead.",
          "After: post one line in the patch-notes channel (what broke, that it is rolled back), keep next/ state, "
          "fix, re-run the train with a new version number (never reuse one)."]
    (ctx.dir / "ROLLBACK.md").write_text("\n".join(R) + "\n")
    return reach, reach_why, key, ok_ap, ap_why


def cmd_plan(ctx):
    rel = ctx.need()
    if not rel["places"]:
        die("attach the place files first")
    reach, reach_why, key, ok_ap, ap_why = write_plan_docs(ctx)
    route, why = release_route(ctx)
    print(f"route: {route}" + "".join(f"\n  {x}" for x in why))
    print(f"approval {ap_why} · key {'set' if key else 'not set'} · API {reach_why}")
    print(f"wrote PUBLISH_PLAN.md, SMOKE.md, ROLLBACK.md in {ctx.dir}")


def luau_script(version):
    return (SKILL / "assets" / "luau" / "run_tests.lua").read_text().replace("{{EXPECTED_VERSION}}", version)


def log_step(ctx, log, **kw):
    kw["at"] = now()
    log.append(kw)
    save_json(ctx.dir / "publish-log.json", log)
    print(" ".join(f"{k}={v}" for k, v in kw.items() if k != "at"))


def dry_run(ctx, places, version, restart, label):
    reqs = []
    for n, f in places:
        pc = ctx.place_cfg(n) or {}
        u, p = pc.get("universe_id", "<universe_id>"), pc.get("place_id", "<place_id>")
        reqs.append({"place": n, "step": "save", **opencloud.describe_publish(u, p, f, "Saved")})
        if ctx.cfg["luau_tests"]:
            reqs.append({"place": n, "step": "test", "method": "POST", "url": f"{opencloud.base()}/cloud/v2/universes/"
                         f"{u}/places/{p}/versions/<saved>/luau-execution-session-tasks",
                         "body": f"run_tests.lua with EXPECTED={version}"})
        reqs.append({"place": n, "step": "publish", **opencloud.describe_publish(u, p, f, "Published")})
    if restart:
        us = sorted({str((ctx.place_cfg(n) or {}).get("universe_id", "<universe_id>")) for n, _ in places})
        reqs += [{"step": "restart", "method": "POST", "url": f"{opencloud.base()}/cloud/v2/universes/{u}:restartServers",
                  "body": {"closeAllVersions": False, "bleedOffServers": True,
                           "bleedOffDurationMinutes": ctx.cfg["bleed_minutes"]}} for u in us]
    save_json(ctx.dir / f"{label}-dryrun.json", reqs)
    for r in reqs:
        print(f"[dry-run] {r['place'] + ' ' if 'place' in r else ''}{r['step']}: {r['method']} {r['url']}"
              + (f"  ({r.get('bytes')} B)" if r.get("bytes") else ""))
    return reqs


def live_ready(ctx, version, confirm):
    problems = []
    if confirm != version:
        problems.append(f"--confirm must equal {version}")
    if not opencloud.api_key():
        problems.append(f"${opencloud.KEY_ENV} is not set (references/publishing.md: API key)")
    reach, why = opencloud.probe()
    if not reach:
        problems.append(f"API host {why} (cloud sessions block it; run from the owner's machine or allow the host)")
    return problems


def cmd_publish(ctx):
    rel = ctx.need()
    a = ctx.a
    if not rel["places"] or not rel.get("version"):
        die("need a version and attached places")
    names = ordered_places(ctx)
    route, why = release_route(ctx)
    ok_ap, ap_why = approval_state(ctx)
    files = [(n, ctx.dir / rel["places"][n]["file"]) for n in names]
    if not a.live:
        dry_run(ctx, files, rel["version"], a.restart, "publish")
        blockers = [f"approval {ap_why}"] if not ok_ap else []
        blockers += [f"route {route}: {x}" for x in why]
        blockers += [] if opencloud.api_key() else [f"${opencloud.KEY_ENV} not set"]
        reach, why = opencloud.probe()
        blockers += [] if reach else [f"API host {why}"]
        print("DRY RUN: nothing was sent." + (" Live publish is blocked by:\n  - " + "\n  - ".join(blockers)
                                              if blockers else f" Ready: `publish --live --confirm {rel['version']}`"))
        return 0
    if not ok_ap:
        die(f"approval {ap_why}: re-run `gate`, then the owner approves", 1)
    if route != "api" or why:
        die(f"not an API release ({'; '.join(why)}): publish every place from Studio and `record`, or fix config "
            "(PUBLISH_PLAN.md)", 1)
    problems = live_ready(ctx, rel["version"], a.confirm)
    if problems:
        die("live publish refused:\n  - " + "\n  - ".join(problems), 1)
    key, log, limit = opencloud.api_key(), load_json(ctx.dir / "publish-log.json", []) or [], canon_limit(ctx)
    saved, results = {}, {}
    try:
        for n, f in files:
            if sha256_file(f) != rel["places"][n]["sha256"]:
                die(f"{n}: file changed since attach", 1)
            pc = ctx.place_cfg(n)
            saved[n] = opencloud.publish_place(pc["universe_id"], pc["place_id"], f, "Saved", key, limit)
            log_step(ctx, log, place=n, step="saved", version_number=saved[n])
        if ctx.cfg["luau_tests"]:
            for n, _ in files:
                pc = ctx.place_cfg(n)
                r = opencloud.run_luau(pc["universe_id"], pc["place_id"], saved[n], luau_script(rel["version"]), key)
                out = r["results"][0] if r["results"] and isinstance(r["results"][0], dict) else {}
                results[n] = {"state": r["state"], "ok": bool(out.get("ok")), "passed": out.get("passed"),
                              "failed": out.get("failed"), "failures": out.get("failures"), "version": out.get("version"),
                              "error": r.get("error")}
                log_step(ctx, log, place=n, step="tested", state=r["state"], ok=results[n]["ok"],
                         passed=out.get("passed"), failed=out.get("failed"), stamp=out.get("version"))
            bad = [n for n, r in results.items() if not r["ok"]]
            rel["evidence"]["tests"] = {"result": "fail" if bad else "pass", "by": "opencloud", "at": now(),
                                        "note": json.dumps(results)[:1500]}
            ctx.save()
            if bad:
                die(f"Luau tests failed on the saved version of {', '.join(bad)}: nothing was published "
                    "(saved versions are not live). See publish-log.json.", 1)
        published = {}
        for n, f in files:
            pc = ctx.place_cfg(n)
            published[n] = opencloud.publish_place(pc["universe_id"], pc["place_id"], f, "Published", key, limit)
            log_step(ctx, log, place=n, step="published", version_number=published[n])
        if a.restart:
            for u in sorted({ctx.place_cfg(n)["universe_id"] for n in names}):
                body = opencloud.restart_servers(u, key, None, ctx.cfg["bleed_minutes"])
                log_step(ctx, log, step="restart", universe=u, bleed=body.get("bleedOffDurationMinutes", 0))
    except opencloud.OCError as e:
        done = [x["place"] for x in log if x.get("step") == "published"]
        print(f"OPEN CLOUD ERROR: {e}")
        print(f"published so far: {', '.join(done) or 'none'}. "
              + ("Mixed versions are live: roll the published ones back (ROLLBACK.md) or finish this publish."
                 if done else "Nothing is live; fix and retry."))
        return 1
    finish(ctx, {n: published[n] for n in names}, "api")
    return 0


def finish(ctx, numbers, route):
    rel = ctx.rel
    v = rel["version"]
    dest = ctx.root / v
    if dest.exists():
        die(f"{dest} already exists; refusing to overwrite an archived release")
    entry = {"version": v, "channel": rel["channel"], "status": "published", "route": route, "date": today(),
             "at": now(), "bump": rel.get("bump"),
             "places": {n: {"version_number": numbers.get(n), "sha256": i["sha256"], "file": i["file"]}
                        for n, i in rel["places"].items()},
             "shipped": [c["src"] for c in ctx.included()], "repos": rel.get("repos", {})}
    rel["status"], rel["published"] = "published", entry
    ctx.save()
    hist = history(ctx.root)
    hist.append(entry)
    save_json(ctx.root / "history.json", hist)
    shutil.move(str(ctx.dir), str(dest))
    print(f"{v} {route} -> history; archived to {dest}")
    print(f"next: run {dest / 'SMOKE.md'} now; record with `smoke --result S1=pass,... --by owner`")


def cmd_record(ctx):
    rel = ctx.need()
    owner_only(ctx.a.by, "recording a Studio publish")
    nums = {}
    for p in ctx.a.place:
        n, _, num = p.partition("=")
        if n not in rel["places"] or not num.isdigit():
            die(f"--place {p}: need NAME=VERSION_NUMBER for an attached place ({', '.join(rel['places'])})")
        nums[n] = int(num)
    missing = [n for n in rel["places"] if n not in nums]
    if missing:
        die(f"also give --place for: {', '.join(missing)}")
    if not approval_state(ctx)[0]:
        print("warning: publishing without a valid approval on record; noted in history")
        rel["unapproved_publish"] = True
    finish(ctx, nums, "studio")


# ---------------------------------------------------------------- commands: smoke, rollback, status, abandon
def latest_dir(ctx):
    last = last_release(ctx.root)
    if not last:
        die("no published release in history.json")
    return last, ctx.root / last["version"]


def cmd_smoke(ctx):
    last, d = latest_dir(ctx)
    rel = load_json(d / "release.json", {})
    sub = Ctx(ctx.a)
    sub.dir, sub.rel = d, rel
    items = {i: (p, t) for i, p, t in smoke_items(sub)}
    if not ctx.a.result:
        print((d / "SMOKE.md").read_text() if (d / "SMOKE.md").is_file() else "\n".join(
            f"{i} {p} {t}" for i, (p, t) in items.items()))
        return 0
    owner_only(ctx.a.by, "recording smoke results")
    res = dict(x.split("=", 1) for x in ctx.a.result.split(",") if "=" in x)
    rel.setdefault("smoke", {}).update({k.strip(): v.strip() for k, v in res.items()})
    save_json(d / "release.json", rel)
    fails = [i for i, r in rel["smoke"].items() if r.lower() == "fail"]
    p0 = [i for i in fails if items.get(i, ("P1",))[0] == "P0"]
    todo = [i for i in items if i not in rel["smoke"]]
    print(f"smoke {last['version']}: {len(rel['smoke'])} recorded, fails {fails or 'none'}, open {todo or 'none'}")
    if p0:
        print(f"ROLLBACK RECOMMENDED ({', '.join(p0)} is P0): {d / 'ROLLBACK.md'}; `release.py rollback` (dry run)")
        return 1
    return 0


def cmd_rollback(ctx):
    a = ctx.a
    hist = [h for h in history(ctx.root) if h.get("status") == "published"]
    hist.sort(key=lambda h: ver_key(h["version"]))
    if len(hist) < 2:
        die("no earlier published release to roll back to: Creator Hub > place > Version History (ROLLBACK.md)", 1)
    bad, prev = hist[-1], hist[-2]
    files, notes = [], []
    for n, p in (prev.get("places") or {}).items():
        f = ctx.root / prev["version"] / p.get("file", "")
        if f.is_file() and sha256_file(f) == p.get("sha256"):
            files.append((n, f))
        else:
            notes.append(f"{n}: archived file missing or changed -> Creator Hub restore version {p.get('version_number')}")
    print(f"roll back {bad['version']} -> {prev['version']}")
    for x in notes:
        print("  " + x)
    ctx.dir = ctx.root / bad["version"]
    if not a.live:
        sub_cfg_places = [n for n, _ in files if not ctx.place_cfg(n)]
        dry = [(n, f) for n, f in files]
        for n in sub_cfg_places:
            print(f"  {n}: no config IDs")
        orig = ctx.cfg["luau_tests"]
        ctx.cfg["luau_tests"] = False
        reqs = dry_run(ctx, dry, prev["version"], a.restart, "rollback")
        ctx.cfg["luau_tests"] = orig
        print(f"DRY RUN: nothing was sent ({len(reqs)} requests). Live: "
              f"`rollback --live --confirm {prev['version']} --by owner --restart`")
        return 0
    owner_only(a.by, "a live rollback")
    problems = live_ready(ctx, prev["version"], a.confirm)
    if problems or notes:
        die("live rollback refused:\n  - " + "\n  - ".join(problems + notes), 1)
    key, log, nums = opencloud.api_key(), [], {}
    try:
        for n, f in files:
            pc = ctx.place_cfg(n)
            nums[n] = opencloud.publish_place(pc["universe_id"], pc["place_id"], f, "Published", key, canon_limit(ctx))
            log_step(ctx, log, place=n, step="rollback-published", version_number=nums[n], content=prev["version"])
        if a.restart:
            for u in sorted({ctx.place_cfg(n)["universe_id"] for n, _ in files}):
                opencloud.restart_servers(u, key, None, 0)
                log_step(ctx, log, step="restart", universe=u, bleed=0)
    except opencloud.OCError as e:
        print(f"OPEN CLOUD ERROR: {e}; rolled back so far: {', '.join(nums) or 'none'} -> use Creator Hub for the rest")
        return 1
    full = history(ctx.root)
    for h in full:
        if h["version"] == bad["version"]:
            h["status"] = "rolled_back"
            h["rollback"] = {"to": prev["version"], "at": now(), "places": nums}
    save_json(ctx.root / "history.json", full)
    save_json(ctx.dir / "rollback-log.json", log)
    print(f"rolled back to {prev['version']} content; {bad['version']} marked rolled_back. Re-run S1-S3 of SMOKE.md.")
    return 0


def cmd_status(ctx):
    last = last_release(ctx.root)
    print(f"root {ctx.root} · last release {last['version'] + ' (' + last['status'] + ')' if last else 'none'}")
    rel = ctx.rel
    if not rel:
        print("no release in flight. next: `init --channel alpha`")
        return 0
    ch = rel["changes"]
    cnt = lambda k, v: sum(1 for c in ch if c.get(k) == v)
    print(f"next/: {rel.get('version') or 'no version'} · channel {rel['channel']} · status {rel['status']}")
    print(f"changes {len(ch)}: in-build {cnt('in_build', 'yes')}, unknown {cnt('in_build', 'unknown')}, "
          f"out {cnt('in_build', 'no')} · player {sum(1 for c in ctx.included() if c['audience'] == 'player')}")
    for n, i in rel["places"].items():
        print(f"place {n}: {i['format']} sha {i['sha256'][:12]} stamp {i.get('stamp') or 'none'} attached {i['attached_at']}")
    nc = load_json(ctx.dir / "notes-check.json")
    print(f"notes: {'checked ' + ('PASS' if nc['ok'] else 'FAIL') if nc else 'not checked'} · gate "
          f"{(rel.get('gate') or {}).get('verdict', 'not run')} · approval {approval_state(ctx)[1]}")
    if not rel["places"]:
        step = "attach the place files"
    elif not ch:
        step = "collect"
    elif cnt("in_build", "unknown"):
        step = "mark the unknown changes --in-build yes|no"
    elif not rel.get("version"):
        step = "version"
    elif not (ctx.dir / "PATCH_NOTES.src.md").is_file():
        step = "notes, then write PATCH_NOTES.src.md + STORE_UPDATE.src.txt"
    elif not nc or not nc["ok"]:
        step = "notes-check"
    elif not rel.get("gate") or not rel["gate"]["verdict"].startswith("GO"):
        step = "gate (fix what it lists), then ask the owner to approve"
    elif not approval_state(ctx)[0]:
        step = "owner approval: `approve --by owner --via ...` (only when the owner said so)"
    else:
        step = "plan, publish (dry run), then the owner runs publish --live or publishes from Studio and `record`s"
    print(f"next: {step}")
    return 0


def cmd_abandon(ctx):
    rel = ctx.need()
    dest = ctx.root / "abandoned" / f"{now().replace(':', '')}-{rel.get('version') or 'draft'}"
    rel["status"], rel["abandoned"] = "abandoned", {"reason": ctx.a.reason, "at": now()}
    ctx.save()
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(ctx.dir), str(dest))
    print(f"shelved to {dest}")


# ---------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="releases root (default $RR_RELEASES_ROOT or <git top>/releases)")
    ap.add_argument("--dir", help="release folder (default <root>/next)")
    sp = ap.add_subparsers(dest="cmd", required=True)
    add = lambda name, **kw: sp.add_parser(name, **kw)
    add("status")
    p = add("init")
    p.add_argument("--channel", choices=["alpha", "beta", "live"])
    p.add_argument("--force", action="store_true")
    p = add("config")
    p.add_argument("--place")
    p.add_argument("--universe")
    p.add_argument("--place-id")
    p.add_argument("--start", action="store_true")
    p.add_argument("--route", choices=["auto", "api", "studio"], help="per place; api only after checking unions etc.")
    p.add_argument("--repo", action="append")
    p.add_argument("--missions", action="append")
    p.add_argument("--luau-tests", choices=["on", "off"])
    p.add_argument("--bleed", type=int)
    p.add_argument("--channel", choices=["alpha", "beta", "live"])
    p = add("attach")
    p.add_argument("name")
    p.add_argument("file")
    p = add("collect")
    p.add_argument("--repo", action="append")
    p.add_argument("--missions", action="append")
    p.add_argument("--since")
    p.add_argument("--max", type=int, default=200)
    p.add_argument("--include-tools", action="store_true")
    p = add("add")
    p.add_argument("title")
    p.add_argument("--section", choices=SECTIONS, default="Changed")
    p.add_argument("--audience", choices=AUDIENCES, default="player")
    p.add_argument("--bump", choices=BUMPS, default="patch")
    p.add_argument("--note")
    p = add("mark")
    p.add_argument("ids", nargs="+")
    p.add_argument("--in-build", dest="in_build", choices=["yes", "no", "unknown"])
    p.add_argument("--audience", choices=AUDIENCES)
    p.add_argument("--section", choices=SECTIONS)
    p.add_argument("--bump", choices=BUMPS)
    p.add_argument("--title")
    p.add_argument("--note")
    add("changes")
    p = add("version")
    p.add_argument("--set")
    p = add("changelog")
    p.add_argument("--apply", nargs="?", const="")
    add("notes")
    add("notes-check")
    add("stamp")
    p = add("evidence")
    p.add_argument("kind", choices=list(OWNER_KINDS) + ["security"])
    p.add_argument("--result", choices=["pass", "fail", "hold"], required=True)
    p.add_argument("--by")
    p.add_argument("--note")
    p.add_argument("--file")
    p = add("waive")
    p.add_argument("gate")
    p.add_argument("--by", required=True)
    p.add_argument("--reason", required=True)
    add("gate")
    p = add("approve")
    p.add_argument("--by", required=True)
    p.add_argument("--via", required=True)
    add("plan")
    p = add("publish")
    p.add_argument("--live", action="store_true")
    p.add_argument("--confirm")
    p.add_argument("--restart", action="store_true")
    p = add("record")
    p.add_argument("--place", action="append", required=True)
    p.add_argument("--by", required=True)
    p = add("smoke")
    p.add_argument("--result")
    p.add_argument("--by")
    p = add("rollback")
    p.add_argument("--live", action="store_true")
    p.add_argument("--confirm")
    p.add_argument("--by")
    p.add_argument("--restart", action="store_true")
    p = add("abandon")
    p.add_argument("--reason", required=True)
    a = ap.parse_args(argv)
    ctx = Ctx(a)
    fn = globals()["cmd_" + a.cmd.replace("-", "_")]
    return fn(ctx) or 0


if __name__ == "__main__":
    sys.exit(main())
