#!/usr/bin/env python3
"""release.py - Risky Rails release manager (rr-release-train). One release in flight at <R>/next/.

  status                                   where the release stands and the next step (start every session here)
  init [--channel alpha|beta|live]         open <R>/next/
  config [--place NAME --universe U --place-id P [--start] [--route auto|api|studio]] [--repo PATH[:game|tools]]
         [--missions DIR] [--luau-tests on|off] [--bleed MIN]   <R>/config.json (Open Cloud IDs, repos, options)
  attach NAME FILE                         pin a place file (.rbxl/.rbxlx): copy, sha256, audit, extract scripts
  collect [--repo P] [--since REF] [--include-tools]   git log + finished missions + script diff -> changes
  add "TITLE" [--section S --audience player|internal --bump B --note HINT --memo M --via WHERE]   owner-stated change
  mark C-1 [C-2..] [--in-build yes|no|unknown --via WHERE --audience A --section S --bump B --title T --note HINT
       --memo M]                           --note = player wording hint (brief); --memo = internal, never shown
  changes                                  list changes
  version [--apply | --set X.Y.Z[-pre] [--force]] [--after X.Y.Z]
                                           propose the next semver (sets it when none is set yet); --after seeds
                                           history with a version shipped before this train
  changelog [--apply [PATH]]               Keep a Changelog [Unreleased] section; dated when the release ships
  notes                                    NOTES_BRIEF.md for writing PATCH_NOTES.src.md + STORE_UPDATE.src.txt
  notes-check                              trace/coverage/voice/limits/canon -> PATCH_NOTES.md, STORE_UPDATE.txt
  stamp                                    RR_Version.lua (ModuleScript for ReplicatedStorage)
  evidence KIND --result pass|fail --by owner [--note N]   KIND: tests bugbash livecheck perf security
  evidence security --file SECURITY_GATE.json              an rr-exploit-guard verdict stored elsewhere
  waive GATE --by owner --reason TEXT      owner accepts a failing or pending gate
  gate                                     G1-G10 -> GATES.md; exit 0 GO, 1 NO-GO
  approve --by owner --via "chat DATE"     owner approval bound to version + file hashes + gate report
  baseline --place NAME=VERSION_NUMBER ...  live version numbers before this publish (ROLLBACK.md target)
  plan                                     PUBLISH_PLAN.md, SMOKE.md, ROLLBACK.md
  publish [--live --confirm VERSION] [--restart]      DRY-RUN unless --live
  record --place NAME=VERSION_NUMBER ... --by owner   owner published from Studio
  smoke [--result S1=pass,S2=fail,S3=skip --by owner] post-release checklist; P0 fail -> rollback advice
  rollback [--to VERSION] [--live --confirm TARGET --by owner] [--restart]
                                           re-publish an earlier release's archive (DRY-RUN default)
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
from rtlib import (LEVELS, SKILL, Bible, die, git_top, history, latest_release, live_release,  # noqa: E402
                   load_json, load_presets, missions_roots, next_version, now, parse_ver, releases_root,
                   released_versions, save_json, scratch_warning, sha256_file, today, ver_key)

SECTIONS = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security", "Internal"]
AUDIENCES = ["player", "internal"]
BUMPS = ["major", "minor", "patch", "none"]
OWNER_KINDS = ("tests", "bugbash", "livecheck", "perf")  # security: rr-exploit-guard's file, or the owner


# ---------------------------------------------------------------- state
class Ctx:
    def __init__(self, a):
        self.a = a
        self.root = releases_root(getattr(a, "root", None))
        self.dir = Path(a.dir).resolve() if getattr(a, "dir", None) else self.root / "next"
        self.presets = load_presets()
        self._bible = None
        self.cfg = load_json(self.root / "config.json", {}) or {}
        for k, v in {"places": [], "repos": [], "missions": [], "luau_tests": True, "bleed_minutes": None}.items():
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


def bleed(ctx):
    """(minutes, why): config --bleed, else one measured trip + results + boarding from canon, rounded up."""
    b = ctx.presets.get("bleed") or {}
    cap = b.get("max", 60)
    if ctx.cfg.get("bleed_minutes"):
        return max(1, min(cap, int(ctx.cfg["bleed_minutes"]))), "config --bleed"
    try:
        trip = float(ctx.bible.value(b.get("trip_min", "gameplay.run.length_min")) or "x")
        extra = sum(float(ctx.bible.value(k) or 0) for k in b.get("extra_s", []))
    except ValueError:
        return b.get("fallback", 15), "fallback (canon trip length unreadable)"
    m = min(cap, -(-(trip * 60 + extra) // 60))
    return int(m), (f"canon: trip {trip:g} min + {' + '.join(k.split('.')[-1] for k in b.get('extra_s', []))} "
                    f"({extra:g} s), rounded up")


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
    gi = ctx.root / ".gitignore"
    if not gi.exists():
        gi.write_text("# place files stay in the owner's storage; commit history.json, CHANGELOG.md and the notes\n"
                      "*.rbxl\n*.rbxlx\n.notes-check/\n")
    live = live_release(ctx.root)
    print(f"opened {ctx.dir} (channel {ch}; live now {live['version'] if live else 'none recorded'})")
    if scratch_warning(ctx.root):
        print("warning: " + scratch_warning(ctx.root))
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
        if not 1 <= a.bleed <= 60:
            die("--bleed is 1-60 minutes (restartServers bleedOffDurationMinutes); 0 would kick crews mid-trip")
        cfg["bleed_minutes"] = a.bleed
    if a.channel:
        cfg["channel"] = a.channel
    ctx.save_cfg()
    pl = ", ".join(f"{p['name']}{'*' if p.get('start') else ''} u{p.get('universe_id', '?')}/p{p.get('place_id', '?')}"
                   f"{' route ' + p['route'] if p.get('route') else ''}" for p in cfg["places"])
    print(f"config {ctx.root / 'config.json'}: places [{pl or 'none'}] (* = start) · repos {len(cfg['repos'])} · "
          f"missions {len(cfg['missions'])} · luau tests {'on' if cfg['luau_tests'] else 'off'} · bleed "
          f"{bleed(ctx)[0]} min ({bleed(ctx)[1]})")


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
    stale = rel["evidence"].pop("tests", None)
    ctx.save()
    route, why = place_route(ctx, name, rel["places"][name])
    c = aud["counts"]
    print(f"{name}: {aud['format']} {aud['bytes']} B sha {aud['sha256'][:12]} | {aud['instances']} instances, "
          f"{c['scripts']} scripts -> {rel_path(ctx, pdir / 'audit' / 'scripts')} | stamp {aud['stamp_version'] or 'none'}"
          f" | route {route}" + (f" ({'; '.join(why)})" if why else ""))
    if stale:
        print(f"note: the earlier tests result ({stale['result']}, {stale['by']}) was for the old file; dropped")
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
    """Sources already live: a rolled-back release's changes are not live, so they come back next release."""
    return {s for h in history(ctx.root) if h.get("status") in ("published", "recorded") for s in h.get("shipped", [])}


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
    last = live_release(ctx.root) or {}
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


def mission_objective(mdir):
    mm = mdir / "mission.md"
    m = re.search(r"^Objective:\s*(.+)$", mm.read_text(errors="replace"), re.M) if mm.is_file() else None
    return m.group(1).strip() if m else ""


def mission_title(mdir, slug, kind):
    obj = mission_objective(mdir)
    if obj:
        head = obj.split(",")[0].strip()
        return (head if len(head) >= 25 else obj)[:140]
    words = re.sub(r"^\d{6}-", "", slug).replace("-", " ")
    return f"{words[:1].upper() + words[1:]} ({kind or 'mission'} {slug})"


def collect_missions(ctx, report):
    have, shipped = {c["src"] for c in ctx.rel["changes"]}, shipped_srcs(ctx)
    roots = missions_roots(ctx.cfg["missions"] + (ctx.a.missions or []))
    open_ = []
    if not roots:
        report.append("missions: none found ($RR_MISSIONS_ROOT, ~/.rr-missions, <project>/.rr-missions, config "
                      "--missions DIR)")
    changed = re.compile(ctx.presets.get("mission_changed", r"$^"), re.I)
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
            title = mission_title(mdir, mdir.name, kind)
            new_change(ctx, src=src, title=title, title_auto=title,
                       section="Changed" if changed.search(mission_objective(mdir)) else "Added",
                       bump=ctx.presets["mission_bump"].get(kind, ctx.presets["mission_bump"]["default"]),
                       audience="player", in_build="unknown", mission={"dir": str(mdir), "kind": kind, "bar": bar})
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
    last = live_release(ctx.root)
    if not last or last.get("status") == "seed":
        report.append("place diff: no archived release to compare with")
        return
    tele_rx = re.compile(ctx.presets.get("teleport_words", r"$^"))
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
        tele = []
        for pth in changed + added + removed:
            for d in (ctx.dir / Path(info["audit"]).parent, prev_dir):
                idx = {e["path"]: e["file"] for e in load_json(d / "scripts" / "index.json", []) or []}
                f = d / "scripts" / idx[pth] if pth in idx else None
                if f and f.is_file() and tele_rx.search(f.read_text(errors="replace")):
                    tele.append(pth.split(".")[-1])
                    break
        parts = [f"{len(x)} {w} ({short(x)})" for x, w in ((changed, "changed"), (added, "added"), (removed, "removed")) if x]
        new_change(ctx, src=f"place:{name}:{info['sha256'][:10]}", title=f"{name} scripts since {last['version']}: "
                   + "; ".join(parts), section="Internal", bump="none", audience="internal", in_build="yes",
                   scripts={"changed": changed, "added": added, "removed": removed, "teleport": sorted(set(tele))})
        report.append(f"place diff {name}: " + "; ".join(parts) + " -> make sure a change describes each"
                      + (f" · teleport code changed ({', '.join(sorted(set(tele)))}): old/new servers overlap during "
                         "the bleed-off" if tele else ""))


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
    mis = [c["id"] for c in ctx.rel["changes"] if c.get("title_auto") and c["title"] == c["title_auto"]]
    if mis:
        print(f"mission titles are dev objectives: retitle {', '.join(mis)} in player words (`mark C-n --title ...`)")
    if unk:
        print(f"next: ask the owner what is really in this build, then `mark {' '.join(unk)} --in-build yes|no "
              "--via \"chat DATE\"` (a mission is in the game only once the owner placed it in Studio)")
    else:
        print("next: `version`")


def print_changes(ctx):
    for c in ctx.rel["changes"]:
        print(f"{c['id']:>5} [{c.get('in_build', '?'):^7}] {c['audience']:<8} {c['section']:<8} {c['bump']:<5} "
              f"{c['src'][:34]:<34} {c['title'][:90]}" + (f" (owner: {c['via']})" if c.get("via") else ""))
    if not ctx.rel["changes"]:
        print("(no changes yet: `collect`, or `add \"what changed\"`)")


def cmd_add(ctx):
    ctx.need()
    a = ctx.a
    c = new_change(ctx, src=f"manual:{ctx.rel['next_id']}", title=a.title, section=a.section, audience=a.audience,
                   bump=a.bump, note=a.note or "", memo=a.memo or "", in_build="yes", via=a.via or "")
    ctx.save()
    print(f"{c['id']} added: {c['section']}/{c['bump']}/{c['audience']}: {c['title']}")


def cmd_mark(ctx):
    ctx.need()
    a = ctx.a
    for cid in a.ids:
        c = ctx.change(cid)
        for k in ("in_build", "audience", "section", "bump", "title", "note", "memo", "via"):
            v = getattr(a, k)
            if v is not None:
                c[k] = v
        if a.in_build and a.in_build != "yes":
            c.pop("via", None)
    ctx.save()
    print_changes(ctx)
    if a.in_build == "yes" and not a.via:
        print("note: no --via: G2 reports these as in build on the agent's word until the owner's answer is cited")


def cmd_changes(ctx):
    ctx.need()
    print_changes(ctx)


# ---------------------------------------------------------------- commands: version, changelog, notes, stamp
def max_bump(changes):
    return max((c["bump"] for c in changes), key=lambda b: LEVELS[b], default="none")


def seed_history(ctx, v, note):
    """Owner says a version shipped before this train: record it so numbering continues above it."""
    if not parse_ver(v):
        die(f"--after {v}: not semver")
    hist = history(ctx.root)
    if any(h["version"] == v for h in hist):
        return False
    hist.append({"version": v, "status": "seed", "date": today(), "at": now(), "places": {}, "shipped": [],
                 "note": note or "shipped before rr-release-train (owner)"})
    save_json(ctx.root / "history.json", hist)
    return True


def cmd_version(ctx):
    rel, a = ctx.need(), ctx.a
    if a.after and seed_history(ctx, a.after.lstrip("v"), a.note):
        print(f"history seeded: {a.after.lstrip('v')} shipped before this train (numbering continues above it)")
    inc = ctx.included()
    if not inc:
        die("no in-build changes: `collect` / `add` / `mark --in-build yes` first", 1)
    level = max_bump(inc)
    hist = released_versions(ctx.root)
    proposal = next_version(hist, level, ctx.channel_pre())
    cur, by = rel.get("version"), rel.get("version_by")
    why = [c["id"] for c in inc if c["bump"] == level][:6]
    basis = f"{level} bump from {', '.join(why) or 'none'}; channel {rel['channel']}; scheme OQ-037 default A"
    if a.set:
        v = a.set.lstrip("v")
        if not parse_ver(v):
            die(f"{v} is not semver (X.Y.Z or X.Y.Z-alpha.N)")
        if hist and ver_key(v) <= max(ver_key(h) for h in hist):
            die(f"{v} is not above the last used version {max(hist, key=ver_key)}")
        if cur and by == "owner" and v != cur and not a.force:
            die(f"{cur} was named by the owner; replacing it needs --force (and the owner's say-so)")
        if parse_ver(v)[3].split(".")[0] != ctx.channel_pre():
            print(f"warning: {v} does not carry the '{ctx.channel_pre() or 'no'}' tag of channel {rel['channel']} "
                  f"(G1 {'FAIL' if ctx.presets['channels'][rel['channel']]['strict'] else 'WARN'}); the scheme "
                  f"proposes {proposal}: ask the owner once, or record their scheme with `bible decide OQ-037`")
        rel["version"], rel["version_by"] = v, "owner"
    elif cur and not a.apply:
        print(f"version {cur} ({by or 'train'}); proposal now {proposal} ({basis})"
              + ("" if cur == proposal else " -> `version --apply` to take it" + (" (--force: owner-named)"
                                                                                   if by == "owner" else "")))
        return 0
    else:
        if cur and by == "owner" and cur != proposal and not a.force:
            die(f"{cur} was named by the owner; keep it, or `version --apply --force` (owner's say-so) for {proposal}")
        rel["version"], rel["version_by"] = proposal, "train"
    rel["bump"] = level
    ctx.save()
    print(f"{rel['version']}  ({basis})")
    print("next: `changelog --apply`, `notes`, `stamp`")


UNREL = "## [Unreleased]"


def changelog_section(ctx):
    rel = ctx.rel
    by = {s: [] for s in SECTIONS}
    for c in ctx.included():
        by.setdefault(c["section"], []).append(c)
    lines = [UNREL, f"<!-- rr-release-train: {rel['version']}, dated when it ships -->", ""]
    for s in SECTIONS:
        if by.get(s):
            lines.append(f"### {s}")
            lines += [f"- {c['title']} ({c['id']})" for c in by[s]]
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _drop_unreleased(text):
    return re.sub(r"^## \[Unreleased\].*?(?=^## \[|\Z)", "", text, flags=re.S | re.M)


def write_changelog(target, sec):
    head = ("# Changelog\n\nAll notable changes to Risky Rails. Format: Keep a Changelog "
            "(https://keepachangelog.com/en/1.1.0/); versions: semver (rr-bible OQ-037).\n\n")
    text = _drop_unreleased(target.read_text() if target.is_file() else head)
    i = text.find("\n## [")
    text = (text.rstrip() + "\n\n" + sec) if i < 0 else (text[:i + 1] + sec + "\n" + text[i + 1:])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


def cmd_changelog(ctx):
    rel = ctx.need()
    if not rel.get("version"):
        die("run `version` first")
    sec = changelog_section(ctx)
    (ctx.dir / "CHANGELOG.section.md").write_text(sec)
    if ctx.a.apply is not None:
        target = Path(ctx.a.apply or ctx.root / "CHANGELOG.md")
        write_changelog(target, sec)
        rel["changelog"] = str(target)
        ctx.save()
        print(f"{target}: [Unreleased] holds {rel['version']} ({sum(1 for c in ctx.included())} entries); "
              "it is dated when the release ships")
    else:
        print(sec)


def date_changelog(ctx, v):
    """At publish/record: [Unreleased] (this version) becomes [v] - today, under a fresh empty [Unreleased]."""
    target = Path(ctx.rel.get("changelog") or ctx.root / "CHANGELOG.md")
    if ctx.rel.get("version") and not (target.is_file() and f"rr-release-train: {v}," in target.read_text()):
        write_changelog(target, changelog_section(ctx))
    text = target.read_text()
    text = re.sub(rf"^## \[Unreleased\]\n<!-- rr-release-train: {re.escape(v)},[^\n]*-->\n",
                  f"{UNREL}\n\n## [{v}] - {today()}\n", text, flags=re.M)
    target.write_text(text)


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
    v = rel["version"]
    L = [f"# Notes brief · {v} ({rel['channel']})", "",
         "Everything needed is here. Write the two files next to this brief, then run `release.py notes-check`.", "",
         f"## PATCH_NOTES.src.md (the Discord post, <= {n['discord_max']} characters once tags are stripped)", "```",
         f"# Risky Rails {v}: <headline in the company voice; numbers only if a change has them>", "",
         "<optional notice: a lexicon string verbatim, or a line ending with the [C-n] of the change it is about>", "",
         "- <one player-visible change: what, where, what to do differently>. [C-4]",
         "- Fixed: <what the player saw go wrong>, now <what happens>. [C-7]", "",
         "<sign-off: a lexicon string verbatim, e.g. Mind the gap>", "```",
         "Good: `- The firebox glow flickers when coal runs low, so the stoker notices first. [C-2]`",
         "Bad: `- Improved the crisis system for a better experience! [C-2]` (vague, hype) · "
         "`- Refactored X to use a RemoteEvent. [C-4]` (internal)",
         "The check: every line traces (bullets by tag; notice and sign-off are lexicon verbatim or tagged); say only "
         "what the change says (a wording hint marked 'do not say' is binding); no promises (soon, next week); numbers "
         "only from the change; parked sidings only on a tagged line whose change ships them; D-007 (no money next to "
         "odds or luck); no internal jargon; one emoji max; `bible check`.", "",
         f"## STORE_UPDATE.src.txt: one line <= {n['store_max']} characters (tags allowed); optional second line "
         f"`TITLE: ...` (<= {n['title_max']}, one emoji max, pattern release.store.title below). No \"free\", no giveaway.",
         "", "## Player changes (cover every one)"]
    L += [f"- [{c['id']}] {c['section']}: {c['title']}" + (f" | wording hint: {c['note']}" if c.get("note") else "")
          for c in player] or ["- (none: an internal-only release; skip the notes or say so in one line)"]
    L += ["", "## Not for players (never mention)"]
    L += [f"- [{c['id']}] {c['title'][:120]}" for c in internal] or ["- (none)"]
    voice = voice_lines(ctx)
    L += ["", "## Voice (read from rr-bible just now)"] + voice
    (ctx.dir / "NOTES_BRIEF.md").write_text("\n".join(L) + "\n")
    print(f"wrote {ctx.dir / 'NOTES_BRIEF.md'}: {len(player)} player changes to cover, {len(internal)} internal, "
          f"{len(voice)} voice lines. Read it (nothing else), write PATCH_NOTES.src.md + STORE_UPDATE.src.txt, "
          "then `notes-check`.")


def cmd_notes_check(ctx):
    ctx.need()
    res = gates.notes_check(ctx)
    for lvl in ("errors", "warnings"):
        for m in res[lvl]:
            print(f"{lvl[:-1].upper()}: {m}")
    print(("notes-check PASS" if res["ok"] else "notes-check FAIL") + f" -> {', '.join(res['outputs']) or 'no outputs'}"
          + ("" if res["ok"] else " (clean files are written only on PASS)"))
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
    if a.kind == "security":
        if a.file:
            f = Path(a.file).expanduser().resolve()
            try:
                data = load_json(f)
            except ValueError:
                data = None
            bad = ["not found"] if data is None else gates.security_file_problems(data)
            if bad:
                die(f"{f}: not an rr-exploit-guard SECURITY_GATE.json ({'; '.join(bad)}); security is rr-exploit-guard's "
                    "call (or the owner's: `evidence security --result R --by owner --note ...`)", 1)
            e = {"result": str(data["verdict"]).lower(), "by": "rr-exploit-guard", "file": str(f),
                 "sha256": sha256_file(f), "at": now(), "note": a.note or ""}
        else:
            owner_only(a.by, "a security result without an rr-exploit-guard verdict file")
            if not a.result:
                die("--result pass|hold|fail")
            e = {"result": a.result, "by": "owner", "note": a.note or "", "at": now()}
    else:
        owner_only(a.by, f"recording {a.kind} results")
        if not a.result:
            die("--result pass|fail")
        e = {"result": a.result, "by": "owner", "note": a.note or "", "at": now()}
    rel["evidence"][a.kind] = e
    ctx.save()
    print(f"evidence {a.kind}: {e['result']} ({e['by']}) {e['note']}")


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
            "gates": (rel.get("gate") or {}).get("hash"), "notes": sha256_file(notes) if notes.is_file() else None,
            "luau_tests": bool(ctx.cfg.get("luau_tests")), "route": release_route(ctx)[0] if rel["places"] else None}


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
        die(f"gate verdict is {rep['verdict']} ({', '.join(rep['blockers'])}): fix or waive first", 1)
    if not rel["places"]:
        die("no place files attached", 1)
    rel["approval"] = {"by": "owner", "via": ctx.a.via, "at": now(), "binding": binding(ctx)}
    rel["status"] = "approved"
    ctx.save()
    print(f"approved {rel['version']} (owner, {ctx.a.via}); bound to {len(rel['places'])} place hashes, the gate report, "
          "the notes, the route and the Luau-tests setting")
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
    if LEVELS.get(rel.get("bump", "patch"), 1) >= LEVELS["minor"]:
        items.append(("S5", "P1", "Live check: " + (b.value("tech.streaming.live_check") or "3+ players incl. a phone")))
    rows = []
    for c in [c for c in ctx.included() if c["audience"] == "player"][:8]:
        t = f"{c['id']} works as the patch notes say: {c['title'][:90]}"
        m = c.get("mission") or {}
        if m.get("kind") == "ui":
            t += " · fire it through real play on a live server (e.g. a crisis on a Trip), not a demo script"
        elif m.get("kind") == "3d":
            t += " · walk it on a phone: scale, collisions, colours"
        watch = gates.mission_notes(m["dir"])["watch"] if m.get("dir") else []
        if watch:
            t += " · watch: " + "; ".join(watch)[:220]
        rows.append(("P1", t))
    if any((c.get("scripts") or {}).get("teleport") for c in ctx.included()):
        rows.append(("P1", "Mixed versions: during the bleed-off an old Lobby sends a crew to the new Trip and back; "
                           "crew, train type and coins intact (TeleportData contract)"))
    rows.append(("P1", "Server restart for the update: a crew mid-trip when its old server closes keeps its banked "
                       "fare (gameplay.run.fail_screen: banked fare is kept; needs a BindToClose save)"))
    rows.append(("P2", "Old servers drained: every server you join shows the new version (S1 check)"))
    return items + [(f"S{len(items) + i}", p, t) for i, (p, t) in enumerate(rows, 1)]


def archived_route(ctx, version, name, p):
    """('API re-publish'|'Creator Hub version history', why) for putting an archived place back."""
    f = ctx.root / version / p.get("file", "")
    if not f.is_file() or sha256_file(f) != p.get("sha256"):
        return "Creator Hub version history", "archived file missing or changed"
    a = load_json(ctx.root / version / "places" / name / "audit" / "audit.json", {}) or {}
    bad = sorted(c for c in (a.get("classes") or {}) if c in gates.canon_unsupported(ctx))
    if bad and (ctx.place_cfg(name) or {}).get("route") != "api":
        return "Creator Hub version history", f"holds {', '.join(bad)}: the API would not restore them"
    return "API re-publish", ""


def write_plan_docs(ctx):
    rel, cfg = ctx.rel, ctx.cfg
    v = rel.get("version") or "(no version)"
    ok_ap, ap_why = approval_state(ctx)
    reach, reach_why = opencloud.probe()
    key = bool(opencloud.api_key())
    route, rwhy = release_route(ctx)
    bm, bwhy = bleed(ctx)
    live = live_release(ctx.root)
    archived = live and live.get("status") != "seed"
    L = [f"# Publish plan · {v} ({rel['channel']})", "",
         f"Preconditions now: approval {ap_why} · ${opencloud.KEY_ENV} {'set' if key else 'NOT set'} · "
         f"API host {reach_why} · Luau tests on saved version: {'on' if cfg['luau_tests'] else 'off'}", "",
         f"**Route for this release: {route.upper()}** (one route for every place so they go live together)"
         + "".join(f"\n- {x}" for x in rwhy), "",
         "| order | place | route | file | sha256 | why |", "|---|---|---|---|---|---|"]
    for i, n in enumerate(ordered_places(ctx), 1):
        info = rel["places"][n]
        r, why = place_route(ctx, n, info)
        L.append(f"| {i} | {n}{' (start)' if (ctx.place_cfg(n) or {}).get('start') else ''} | {r} | "
                 f"{info['file']} | {info['sha256'][:12]} | {'; '.join(why) or '-'} |")
    L += ["", "## Before publishing"]
    if not archived and not rel.get("baseline"):
        L.append("0. Rollback target: write down each place's live version number now (Creator Hub > place > Version "
                 "History) and record it: `release.py baseline --place Lobby=N --place Trip=M` (ROLLBACK.md uses it).")
    L += ["1. The attached files in `places/` become the release archive (the next release's rollback source); keep a "
          "copy in the owner's storage too (the releases root may be a disposable session).",
          "2. `release.py publish` (dry run): prints every request; fix anything it lists as missing.",
          "", "## Steps (API route)",
          f"3. From a machine that reaches apis.roblox.com with the key set: `release.py publish --live --confirm {v}`"
          " [--restart]. It re-runs the gates (must match the approval), uploads each place as **Saved**, runs"
          " `assets/luau/run_tests.lua` on each saved version (specs + RR_Version), and only if all pass uploads each"
          " as **Published**, start place last.",
          f"4. Servers: `--restart` restarts old-version servers with a {bm}-minute bleed-off ({bwhy}; needs "
          "universe:write), or Creator Hub > experience > ... > Restart Servers for Updates. Until then old and new "
          "servers overlap (old Lobby -> new Trip teleports).",
          "5. Run SMOKE.md within the first hour; any P0 fail -> ROLLBACK.md.", "",
          "## Steps (Studio route)",
          "3. Open the exact attached file in Studio (sha256 above), File > Publish to Roblox.",
          "4. Note each place's new version number (Creator Hub > place > Version History).",
          "5. `release.py record --place NAME=VERSION ... --by owner`, then SMOKE.md.", "",
          "Timing: publish when you can watch the first hour, outside the owner-on-the-train sessions "
          f"(`release.ops.timetable`: {ctx.bible.value('release.ops.timetable') or 'n/a'})."]
    (ctx.dir / "PUBLISH_PLAN.md").write_text("\n".join(L) + "\n")
    S = [f"# Smoke checklist · {v}", "", "Run on live servers right after publishing. Record: "
         "`release.py smoke --result S1=pass,S2=fail,S6=skip --by owner`. Any P0 fail -> roll back (ROLLBACK.md).", "",
         "| id | prio | check | result |", "|---|---|---|---|"]
    S += [f"| {i} | {p} | {t} | |" for i, p, t in smoke_items(ctx)]
    (ctx.dir / "SMOKE.md").write_text("\n".join(S) + "\n")
    R = [f"# Rollback plan · {v}", "",
         "Trigger: any P0 smoke fail, joins failing, coins or purchases lost, or an error spike. Decide within minutes; "
         "a rollback is cheaper than a hotfix under pressure.", ""]
    if archived:
        R.append(f"Target: {live['version']}, live now (released {live.get('date', '?')}"
                 + (f"; restored by the rollback of {live['via_rollback']}" if live.get("via_rollback") else "") + ").")
        R += ["", "| place | live version number | archived file | route |", "|---|---|---|---|"]
        api = True
        for n, pl in (live.get("places") or {}).items():
            r, why = archived_route(ctx, live["version"], n, pl)
            api = api and r.startswith("API")
            R.append(f"| {n} | {pl.get('version_number', '?')} | {pl.get('file', '-')} | {r}{' (' + why + ')' if why else ''} |")
        R += [""]
        if api:
            R.append(f"A. API: `release.py rollback` (dry run), then `release.py rollback --live --confirm {live['version']}"
                     " --by owner --restart` (re-publishes the archived files; new version numbers, same content).")
        R.append("B. Creator Hub > Creations > the experience > Places > each place > Version History: restore the "
                 "version number above, then Restart Servers for Updates.")
    else:
        base = (rel.get("baseline") or {}).get("places") or {}
        R.append("Target: the versions live before this publish: " + (", ".join(f"{n} {x}" for n, x in base.items())
                 if base else "NOT RECORDED: before publishing, `release.py baseline --place Lobby=N --place Trip=M` "
                 "(Creator Hub > place > Version History)") + (f" (after {live['version']}, shipped before this train)"
                                                               if live else "") + ".")
        R.append("Creator Hub > Creations > the experience > Places > each place > Version History: restore that version, "
                 "then Restart Servers for Updates.")
    store = ctx.bible.value("tech.data.store_name") or "the canon data store"
    R += ["", "Data: DataStore writes are not rolled back. If this release changed the saved profile shape, the "
          f"previous build must still read profiles this one wrote ({store}); if it cannot, fix forward instead.",
          "After: post one line in the patch-notes channel (what broke, that it is rolled back), keep the release "
          "folder for the post-mortem, fix, re-run the train with a new version number (never reuse one)."]
    (ctx.dir / "ROLLBACK.md").write_text("\n".join(R) + "\n")
    return reach, reach_why, key, ok_ap, ap_why


def cmd_plan(ctx):
    rel = ctx.need()
    if not rel["places"]:
        die("attach the place files first")
    reach, reach_why, key, ok_ap, ap_why = write_plan_docs(ctx)
    route, why = release_route(ctx)
    print(f"route: {route}" + "".join(f"\n  {x}" for x in why))
    print(f"approval {ap_why} · key {'set' if key else 'not set'} · API {reach_why} · bleed-off {bleed(ctx)[0]} min")
    print(f"wrote PUBLISH_PLAN.md, SMOKE.md, ROLLBACK.md in {ctx.dir}")


def cmd_baseline(ctx):
    rel = ctx.need()
    nums = {}
    for x in ctx.a.place:
        n, _, num = x.partition("=")
        if not num.isdigit():
            die(f"--place {x}: need NAME=VERSION_NUMBER (Creator Hub > place > Version History)")
        nums[n] = int(num)
    rel["baseline"] = {"places": nums, "at": now(), "via": ctx.a.via or ""}
    ctx.save()
    print("live before this publish: " + ", ".join(f"{n} v{x}" for n, x in nums.items()) + " -> ROLLBACK.md (`plan`)")


def luau_script(version):
    return (SKILL / "assets" / "luau" / "run_tests.lua").read_text().replace("{{EXPECTED_VERSION}}", version)


def log_step(ctx, log, name="publish-log.json", **kw):
    kw["at"] = now()
    log.append(kw)
    save_json(ctx.dir / name, log)
    print(" ".join(f"{k}={v}" for k, v in kw.items() if k != "at"))


def dry_run(ctx, places, version, restart, label, publish_only=False, bleed_min=None):
    reqs = []
    for n, f in places:
        pc = ctx.place_cfg(n) or {}
        u, p = pc.get("universe_id", "<universe_id>"), pc.get("place_id", "<place_id>")
        if not publish_only:
            reqs.append({"place": n, "step": "save", **opencloud.describe_publish(u, p, f, "Saved")})
            if ctx.cfg["luau_tests"]:
                reqs.append({"place": n, "step": "test", "method": "POST", "url": f"{opencloud.base()}/cloud/v2/"
                             f"universes/{u}/places/{p}/versions/<saved>/luau-execution-session-tasks",
                             "body": f"assets/luau/run_tests.lua with EXPECTED={version}; then GET the task until "
                                     "COMPLETE"})
        reqs.append({"place": n, "step": "publish", **opencloud.describe_publish(u, p, f, "Published")})
    if restart:
        us = sorted({str((ctx.place_cfg(n) or {}).get("universe_id", "<universe_id>")) for n, _ in places})
        body = opencloud.restart_body(bleed(ctx)[0] if bleed_min is None else bleed_min)
        reqs += [{"step": "restart", "method": "POST", "url": f"{opencloud.base()}/cloud/v2/universes/{u}:restartServers",
                  "body": body} for u in us]
    save_json(ctx.dir / f"{label}-dryrun.json", reqs)
    for r in reqs:
        print(f"[dry-run] {r['place'] + ' ' if 'place' in r else ''}{r['step']}: {r['method']} {r['url']}"
              + (f"  ({r.get('bytes')} B)" if r.get("bytes") else "")
              + (f"  body {json.dumps(r['body'])}" if r["step"] == "restart" else ""))
    return reqs


def key_needs(ctx, restart, tests=True):
    return ("publish",) + (("tests",) if tests and ctx.cfg["luau_tests"] else ()) + (("restart",) if restart else ())


def live_ready(ctx, version, confirm, need):
    problems = []
    if confirm != version:
        problems.append(f"--confirm must equal {version}")
    if not opencloud.api_key():
        problems.append(f"${opencloud.KEY_ENV} is not set (references/publishing.md: API key)")
    reach, why = opencloud.probe()
    if not reach:
        problems.append(f"API host {why} (cloud sessions block it; run from the owner's machine or allow the host)")
    elif opencloud.api_key():
        us = sorted({(p.get("universe_id") or "?") for p in ctx.cfg["places"]})
        kp, notes = opencloud.key_report(opencloud.api_key(), us, need)
        problems += kp
        for x in notes[:1]:
            print("note: " + x)
    return problems


def cmd_publish(ctx):
    rel = ctx.need()
    a = ctx.a
    if not rel["places"] or not rel.get("version"):
        die("need a version and attached places")
    names = ordered_places(ctx)
    route, why = release_route(ctx)
    files = [(n, ctx.dir / rel["places"][n]["file"]) for n in names]
    if not a.live:
        ok_ap, ap_why = approval_state(ctx)
        dry_run(ctx, files, rel["version"], a.restart, "publish")
        g = rel.get("gate") or {}
        blockers = [] if ok_ap else [f"approval {ap_why}" + ("" if (g.get("verdict") or "").startswith("GO") else
                                     f" (and approval needs gate GO: now {g.get('verdict', 'not run')}"
                                     f"{' on ' + ', '.join(g.get('blockers') or []) if g.get('blockers') else ''})")]
        blockers += [f"route {route}: {x}" for x in why]
        blockers += live_ready(ctx, rel["version"], rel["version"], key_needs(ctx, a.restart))
        print("DRY RUN: nothing was sent." + (" Live publish is blocked by:\n  - " + "\n  - ".join(blockers)
                                              if blockers else f" Ready: `publish --live --confirm {rel['version']}`"))
        return 0
    rep = gates.run(ctx)
    ok_ap, ap_why = approval_state(ctx)
    if not rep["verdict"].startswith("GO") or not ok_ap:
        die(f"live publish refused: gates now {rep['verdict']}"
            + (f" ({', '.join(rep['blockers'])})" if rep["blockers"] else "") + f"; approval {ap_why}. Nothing was "
            "sent. Fix, `gate`, and the owner approves again.", 1)
    if route != "api" or why:
        die(f"not an API release ({'; '.join(why)}): publish every place from Studio and `record`, or fix config "
            "(PUBLISH_PLAN.md)", 1)
    problems = live_ready(ctx, rel["version"], a.confirm, key_needs(ctx, a.restart))
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
                body = opencloud.restart_servers(u, key, None, bleed(ctx)[0])
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
    date_changelog(ctx, v)
    entry = {"version": v, "channel": rel["channel"], "status": "published", "route": route, "date": today(),
             "at": now(), "bump": rel.get("bump"),
             "places": {n: {"version_number": numbers.get(n), "sha256": i["sha256"], "file": i["file"]}
                        for n, i in rel["places"].items()},
             "shipped": [c["src"] for c in ctx.included()], "repos": rel.get("repos", {}),
             "gate": (rel.get("gate") or {}).get("verdict")}
    if rel.get("unapproved_publish"):
        entry["unapproved_publish"] = rel["unapproved_publish"]
    rel["status"], rel["published"] = "published", entry
    ctx.save()
    hist = history(ctx.root)
    hist.append(entry)
    save_json(ctx.root / "history.json", hist)
    shutil.move(str(ctx.dir), str(dest))
    print(f"{v} {route} -> history, CHANGELOG dated; archived to {dest}")
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
    rep = gates.run(ctx)
    ok, why = approval_state(ctx)
    if not ok or not rep["verdict"].startswith("GO"):
        rel["unapproved_publish"] = {"approval": why, "gates": rep["verdict"], "blockers": rep["blockers"]}
        print(f"warning: published without a matching approval (approval {why}; gates {rep['verdict']}); "
              "recorded in history as unapproved_publish")
    finish(ctx, nums, "studio")


# ---------------------------------------------------------------- commands: smoke, rollback, status, abandon
def smoke_state(ctx, entry):
    d = ctx.root / entry["version"]
    rel = load_json(d / "release.json", {}) or {}
    sub = Ctx(ctx.a)
    sub.dir, sub.rel = d, rel
    items = {i: (p, t) for i, p, t in smoke_items(sub)} if rel else {}
    done = rel.get("smoke") or {}
    open_ = [i for i, (p, _) in items.items() if i not in done and p in ("P0", "P1")]
    return d, rel, items, done, open_


def cmd_smoke(ctx):
    last = latest_release(ctx.root)
    if not last:
        die("no published release in history.json")
    d, rel, items, done, open_ = smoke_state(ctx, last)
    if not ctx.a.result:
        print((d / "SMOKE.md").read_text() if (d / "SMOKE.md").is_file() else "\n".join(
            f"{i} {p} {t}" for i, (p, t) in items.items()))
        return 0
    owner_only(ctx.a.by, "recording smoke results")
    res = {}
    for x in ctx.a.result.split(","):
        k, _, r = x.partition("=")
        k, r = k.strip().upper(), r.strip().lower()
        if k not in items:
            die(f"unknown smoke id {k or x!r} (SMOKE.md has {', '.join(items)})")
        if r not in ("pass", "fail", "skip"):
            die(f"{k}={r or '?'}: result is pass, fail or skip")
        res[k] = r
    rel.setdefault("smoke", {}).update(res)
    save_json(d / "release.json", rel)
    fails = [i for i, r in rel["smoke"].items() if r == "fail"]
    p0 = [i for i in fails if items[i][0] == "P0"]
    todo = [i for i in items if i not in rel["smoke"]]
    print(f"smoke {last['version']}: {len(rel['smoke'])} recorded, fails {fails or 'none'}, open {todo or 'none'}")
    if p0:
        print(f"ROLLBACK RECOMMENDED ({', '.join(p0)} is P0): {d / 'ROLLBACK.md'}; `release.py rollback` (dry run)")
        return 1
    return 0


def cmd_rollback(ctx):
    a = ctx.a
    top, live = latest_release(ctx.root), live_release(ctx.root)
    if not top or not live or live.get("status") == "seed":
        die("no archived release on record to roll back to: Creator Hub > place > Version History (ROLLBACK.md)", 1)
    if top.get("status") == "rolled_back" and not a.to:
        die(f"{top['version']} is already rolled back; {live['version']} content is live now. Going back further is "
            "the owner's call: `rollback --to VERSION`", 1)
    cands = [h for h in history(ctx.root) if h.get("status") in ("published", "recorded")
             and ver_key(h["version"]) < ver_key(live["version"])]
    cands.sort(key=lambda h: ver_key(h["version"]))
    prev = next((h for h in cands if h["version"] == a.to), None) if a.to else (cands[-1] if cands else None)
    if not prev:
        die(f"no earlier published release{' ' + a.to if a.to else ''} to roll back to "
            f"({', '.join(h['version'] for h in cands) or 'none'}): Creator Hub > place > Version History", 1)
    files, notes = [], []
    for n, p in (prev.get("places") or {}).items():
        r, why = archived_route(ctx, prev["version"], n, p)
        if r.startswith("API"):
            files.append((n, ctx.root / prev["version"] / p["file"]))
        else:
            notes.append(f"{n}: {why} -> Creator Hub restore version {p.get('version_number')}")
    print(f"roll back {live['version']} -> {prev['version']}")
    for x in notes:
        print("  " + x)
    ctx.dir = ctx.root / live["version"]
    if not a.live:
        for n in [n for n, _ in files if not ctx.place_cfg(n)]:
            print(f"  {n}: no config IDs")
        reqs = dry_run(ctx, files, prev["version"], a.restart, "rollback", publish_only=True, bleed_min=0)
        print(f"DRY RUN: nothing was sent ({len(reqs)} requests). Live: "
              f"`rollback --live --confirm {prev['version']} --by owner --restart`"
              + (" (the rest through Creator Hub)" if notes and files else ""))
        return 0
    owner_only(a.by, "a live rollback")
    problems = live_ready(ctx, prev["version"], a.confirm, ("publish",) + (("restart",) if a.restart else ()))
    if problems or notes:
        die("live rollback refused:\n  - " + "\n  - ".join(problems + notes), 1)
    key, log, nums = opencloud.api_key(), load_json(ctx.dir / "rollback-log.json", []) or [], {}
    try:
        for n, f in files:
            pc = ctx.place_cfg(n)
            nums[n] = opencloud.publish_place(pc["universe_id"], pc["place_id"], f, "Published", key, canon_limit(ctx))
            log_step(ctx, log, "rollback-log.json", place=n, step="rollback-published", version_number=nums[n],
                     content=prev["version"])
        if a.restart:
            for u in sorted({ctx.place_cfg(n)["universe_id"] for n, _ in files}):
                opencloud.restart_servers(u, key, None, 0)
                log_step(ctx, log, "rollback-log.json", step="restart", universe=u, bleed=0)
    except opencloud.OCError as e:
        print(f"OPEN CLOUD ERROR: {e}; rolled back so far: {', '.join(nums) or 'none'} -> use Creator Hub for the rest")
        return 1
    full = history(ctx.root)
    for h in full:
        if h["version"] == live["version"]:
            h["status"] = "rolled_back"
            h["rollback"] = {"to": prev["version"], "at": now(), "places": nums, "by": "owner"}
    save_json(ctx.root / "history.json", full)
    print(f"rolled back to {prev['version']} content; {live['version']} marked rolled_back. Re-run S1-S3 of SMOKE.md.")
    return 0


def cmd_status(ctx):
    top, live = latest_release(ctx.root), live_release(ctx.root)
    print(f"root {ctx.root} · live now {live['version'] if live else 'none recorded'}"
          + (f" (after rolling back {live['via_rollback']})" if live and live.get("via_rollback") else ""))
    if scratch_warning(ctx.root):
        print("warning: " + scratch_warning(ctx.root))
    rel = ctx.rel
    if not rel:
        if top:
            _, _, items, done, open_ = smoke_state(ctx, top)
            p0 = [i for i in open_ if items[i][0] == "P0"]
            if open_ and top.get("status") != "rolled_back":
                print(f"{top['version']} published {top.get('date', '?')}: smoke open {', '.join(open_)}"
                      + (f" (P0: {', '.join(p0)})" if p0 else ""))
                print(f"next: the owner runs {ctx.root / top['version'] / 'SMOKE.md'}; `smoke --result ... --by owner`; "
                      "then `init` for the next release")
                return 0
        print("no release in flight. next: `init --channel alpha`")
        return 0
    ch = rel["changes"]
    cnt = lambda k, v: sum(1 for c in ch if c.get(k) == v)
    print(f"next/: {rel.get('version') or 'no version'}" + (f" ({rel.get('version_by')})" if rel.get("version") else "")
          + f" · channel {rel['channel']} · status {rel['status']} · opened {rel.get('created', '?')}")
    print(f"changes {len(ch)}: in-build {cnt('in_build', 'yes')}, unknown {cnt('in_build', 'unknown')}, "
          f"out {cnt('in_build', 'no')} · player {sum(1 for c in ctx.included() if c['audience'] == 'player')}")
    for n, i in rel["places"].items():
        print(f"place {n}: {i['format']} sha {i['sha256'][:12]} stamp {i.get('stamp') or 'none'} attached {i['attached_at']}")
    nc = load_json(ctx.dir / "notes-check.json")
    stale = bool(nc) and nc.get("changes_hash") != gates.changes_hash(ctx)
    print(f"notes: {('checked ' + ('PASS' if nc['ok'] else 'FAIL') + (' but STALE (changes or version moved)' if stale else '')) if nc else 'not checked'}"
          f" · gate {(rel.get('gate') or {}).get('verdict', 'not run')} · approval {approval_state(ctx)[1]}")
    stamps_bad = [n for n, i in rel["places"].items() if i.get("stamp") != rel.get("version")]
    g = rel.get("gate") or {}
    if not rel["places"]:
        step = "attach the place files"
    elif not ch:
        step = "collect"
    elif cnt("in_build", "unknown"):
        step = "ask the owner, then mark the unknown changes --in-build yes|no --via \"chat DATE\""
    elif not rel.get("version"):
        step = "version"
    elif not (ctx.dir / "PATCH_NOTES.src.md").is_file():
        step = "notes, then write PATCH_NOTES.src.md + STORE_UPDATE.src.txt"
    elif not nc or not nc["ok"] or stale:
        step = "notes-check"
    elif stamps_bad:
        step = (f"stamp; the owner pastes RR_Version into ReplicatedStorage, saves, re-exports; attach "
                f"{', '.join(stamps_bad)} again")
    elif not g.get("verdict", "").startswith("GO"):
        step = "gate (fix what it lists" + (f": {', '.join(g.get('blockers') or [])}" if g.get("blockers") else "") \
               + "), then ask the owner to approve"
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
    cl = Path(rel.get("changelog") or ctx.root / "CHANGELOG.md")
    if rel.get("version") and cl.is_file() and f"rr-release-train: {rel['version']}," in cl.read_text():
        cl.write_text(_drop_unreleased(cl.read_text()))
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(ctx.dir), str(dest))
    print(f"shelved to {dest}" + (" · its [Unreleased] changelog section removed" if rel.get("version") else ""))


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
    p.add_argument("--note", help="player wording hint, shown in the notes brief")
    p.add_argument("--memo", help="internal note, never shown to the notes writer")
    p.add_argument("--via", help="where the owner said it (chat DATE)")
    p = add("mark")
    p.add_argument("ids", nargs="+")
    p.add_argument("--in-build", dest="in_build", choices=["yes", "no", "unknown"])
    p.add_argument("--audience", choices=AUDIENCES)
    p.add_argument("--section", choices=SECTIONS)
    p.add_argument("--bump", choices=BUMPS)
    p.add_argument("--title")
    p.add_argument("--note", help="player wording hint, shown in the notes brief")
    p.add_argument("--memo", help="internal note, never shown to the notes writer")
    p.add_argument("--via", help="owner's confirmation for --in-build yes (chat DATE)")
    add("changes")
    p = add("version")
    p.add_argument("--apply", action="store_true", help="take the proposal (replaces the current version)")
    p.add_argument("--set", help="the owner named this version")
    p.add_argument("--force", action="store_true", help="replace an owner-named version (owner's say-so)")
    p.add_argument("--after", help="seed history: this version shipped before the train (owner's word)")
    p.add_argument("--note")
    p = add("changelog")
    p.add_argument("--apply", nargs="?", const="")
    add("notes")
    add("notes-check")
    add("stamp")
    p = add("evidence")
    p.add_argument("kind", choices=list(OWNER_KINDS) + ["security"])
    p.add_argument("--result", choices=["pass", "fail", "hold"])
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
    p = add("baseline")
    p.add_argument("--place", action="append", required=True)
    p.add_argument("--via")
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
    p.add_argument("--to", help="target version (owner's call after a first rollback)")
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
