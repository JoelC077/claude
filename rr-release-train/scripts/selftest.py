#!/usr/bin/env python3
"""selftest.py - end-to-end test of rr-release-train on a temp releases root (never touches real releases).

  selftest.py [--keep]      run everything; prints one line per check and "all N passed"; --keep keeps the temp dir

Covers: semver rules, placefile (binary LZ4, ZSTD when the zstandard module exists, XML), mission discovery,
collect (conventional commits, trailers, tooling vs game repo, missions, script diff), mark --via, version
(proposal/apply/owner-named/--after seed), changelog [Unreleased] -> dated at publish, notes-check (every line
traced, promises, sidings, outputs only on PASS), gates (security binding, fresh critic ledgers, hygiene: debug
names, blank asset ids, demo scripts; G10 channel block), owner-only refusals incl. security self-certification,
approval voiding (files, Luau-tests setting, a changed security verdict caught by the live re-gate), key
introspection, publish dry-run and --live against a local mock of Open Cloud (Saved -> Luau tests -> Published ->
restart with the canon bleed-off), a failing Luau test that stops a publish, smoke validation and rollback advice,
live rollback (target, no second rollback without --to, logs kept apart), the Studio route + record, abandon, and
run_tests.lua in Lua 5.1 (lupa, optional: pip install --target ~/.cache/rr-tools/py lupa). Canon is read from the
real rr-bible (read-only).
"""
import http.server
import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import placefile  # noqa: E402
from rtlib import next_version, now  # noqa: E402

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(f"{'ok  ' if cond else 'FAIL'} {name}" + (f"  [{detail}]" if detail and not cond else ""))


# ---------------------------------------------------------------- fixtures
def make_place(path, version, grow=False, union=False, debug=False, spec_ok=True, junk=False):
    I, r = [], [0]

    def add(cls, parent, **props):
        ref = r[0]
        r[0] += 1
        I.append((ref, cls, parent, props))
        return ref
    ws = add("Workspace", None, Name="Workspace", StreamingEnabled=True)
    rs = add("ReplicatedStorage", None, Name="ReplicatedStorage")
    sss = add("ServerScriptService", None, Name="ServerScriptService")
    add("ModuleScript", rs, Name="RR_Version", Source=f'return {{ version = "{version}", channel = "alpha" }}\n')
    add("ModuleScript", sss, Name="Coal", Source=f"local DEBUG = {'true' if debug else 'false'}\n"
        "local antiCheatEnabled = true\nlocal CHEAT_DETECTION = true\n"
        'local Store = ProfileStore.New("PlayerData_alpha1", {})\nreturn {}\n')
    add("Script", sss, Name="Main", Source="local Coal = require(script.Parent.Coal)\n")
    if junk:
        add("ModuleScript", rs, Name="Icons", Source='return { Sheet = "rbxassetid://0" }\n')
        sp = add("StarterPlayer", None, Name="StarterPlayer")
        add("LocalScript", sp, Name="AlertDemo", Source="local I = require(game.ReplicatedStorage.Icons)\n")
        add("Decal", ws, Name="Sign", Texture="rbxassetid://0")
    add("ModuleScript", sss, Name="Coal.spec", Source="return { a = function() assert(%s) end }\n" % str(spec_ok).lower())
    train = add("Model", ws, Name="Train")
    for i in range(40 if grow else 20):
        add("Part", train, Name=f"P{i}", Anchored=True, Color=("rgb8", 246, 197, 0))
    if union:
        add("UnionOperation", train, Name="Boiler", Anchored=True)
    placefile.write_binary(path, I)


def zstd_copy(src, dst):
    """Re-encode every LZ4 chunk of a binary place as ZSTD (what current Studio writes)."""
    import zstandard
    data = Path(src).read_bytes()
    out, i = bytearray(data[:32]), 32
    while i < len(data):
        tag, clen, ulen = data[i:i + 4], *struct.unpack("<II", data[i + 4:i + 12])
        body = data[i + 16:i + 16 + (clen or ulen)]
        if clen:
            raw = placefile.lz4_block(body, ulen)
            body = zstandard.ZstdCompressor().compress(raw)
            out += tag + struct.pack("<III", len(body), ulen, 0) + body
        else:
            out += data[i:i + 16] + body
        i += 16 + (clen or ulen)
    Path(dst).write_bytes(bytes(out))


def make_git(repo):
    def g(*a):
        subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)
    repo.mkdir(parents=True)
    g("init", "-q")
    g("config", "user.email", "t@t")
    g("config", "user.name", "t")
    (repo / "default.project.json").write_text("{}")
    for i, (subj, body) in enumerate([("chore: project", ""), ("feat(crisis): coal low flashes the firebox",
                                       "Player-Note: the firebox flickers when coal is low"),
                                      ("fix: lever pulled twice after lock", ""), ("refactor: split module", ""),
                                      ("tweak seat colours", "Release-Note: skip")]):
        (repo / f"f{i}.lua").write_text(str(i))
        g("add", "-A")
        g("commit", "-qm", subj, *(["-m", body] if body else []))


def make_mission(root, slug, kind, agent, score):
    d = root / slug
    (d / "critique-x").mkdir(parents=True)
    (d / "export").mkdir()
    (d / "state.json").write_text(json.dumps({"slug": slug, "kind": kind, "status": "done", "bar": 8}))
    (d / "mission.md").write_text(f"# Mission\nObjective: Build the {slug} thing, to 8/10, exported\n")
    (d / "critique-x" / "ledger.json").write_text(json.dumps([{"pass": 1, "kind": "full", "agent": agent,
                                                               "scores": {"A1": score}}]))
    (d / "export" / "ASSETS.md").write_text("| src/AlertDemo.client.lua | StarterPlayerScripts | LocalScript (Studio "
                                            "test; delete for release) |\n- Watch: overflow chip position after UIScale.\n")
    return d


class Mock(http.server.BaseHTTPRequestHandler):
    state = {"n": 10, "calls": [], "fail_tests": False, "tasks": {}}

    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        s = self.state
        if self.path.endswith("/logs"):
            return self._send(200, {"luauExecutionSessionTaskLogs": [{"messages": ["specs ran"]}]})
        m = re.match(r"^/cloud/v2/(universes/.+/tasks/(t\d+))$", self.path)
        if m:
            ok, ver = not s["fail_tests"], s["tasks"][m.group(2)]
            return self._send(200, {"path": m.group(1), "state": "COMPLETE", "output": {"results": [
                {"ok": ok, "passed": 1 if ok else 0, "failed": 0 if ok else 1, "version": ver}]}})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        s = self.state
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.headers.get("x-api-key") != "test-key" and self.path != "/api-keys/v1/introspect":
            return self._send(401, {"error": "bad key"})
        m = re.match(r"^/universes/v1/(\d+)/places/(\d+)/versions\?versionType=(Saved|Published)$", self.path)
        if m:
            s["n"] += 1
            s["calls"].append((m.group(3), m.group(2), len(body), self.headers.get("Content-Type")))
            return self._send(200, {"versionNumber": s["n"]})
        m = re.match(r"^/cloud/v2/universes/(\d+)/places/(\d+)/versions/(\d+)/luau-execution-session-tasks$", self.path)
        if m:
            script = json.loads(body)["script"]
            ver = re.search(r'local EXPECTED = "([^"]+)"', script).group(1)
            tid = f"t{len(s['tasks']) + 1}"
            s["tasks"][tid] = ver
            s["calls"].append(("Luau", m.group(2), ver, None))
            return self._send(200, {"path": f"universes/{m.group(1)}/places/{m.group(2)}/versions/{m.group(3)}/"
                                            f"luau-execution-sessions/s1/tasks/{tid}", "state": "QUEUED"})
        if self.path == "/api-keys/v1/introspect":
            ok = json.loads(body).get("apiKey") == "test-key"
            s["introspect"] = s.get("introspect", 0) + 1
            return self._send(200 if ok else 401, {"name": "k", "enabled": True, "expired": s.get("expired", False),
                                                   "scopes": [{"name": n, "operations": ["write"], "universeIds": ["100"]}
                                                              for n in ("universe-places", "universe",
                                                                        "universe.place.luau-execution-session")]})
        if re.match(r"^/cloud/v2/universes/\d+:restartServers$", self.path):
            s["calls"].append(("Restart", json.loads(body), None, None))
            return self._send(200, {})
        self._send(404, {"error": "not found"})


# ---------------------------------------------------------------- runner
def main():
    keep = "--keep" in sys.argv
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        return 0
    tmp = Path(tempfile.mkdtemp(prefix="rr-release-selftest-"))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Mock)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    env = dict(os.environ, RR_OPENCLOUD_BASE=f"http://127.0.0.1:{srv.server_port}", ROBLOX_API_KEY="test-key",
               NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost", RR_RELEASES_ROOT=str(tmp / "rel"))
    env.pop("RR_MISSIONS_ROOT", None)

    def R(*args, code=None, envx=None):
        e = dict(env, **(envx or {}))
        p = subprocess.run([sys.executable, str(HERE / "release.py"), *args], capture_output=True, text=True, env=e,
                           cwd=tmp)
        out = p.stdout + p.stderr
        if code is not None and p.returncode != code:
            print(f"     release.py {' '.join(args)} -> exit {p.returncode}, wanted {code}\n" + out[-800:])
        return p.returncode, out
    try:
        # semver
        check("semver: first alpha is 0.1.0-alpha.1", next_version([], "patch", "alpha") == "0.1.0-alpha.1")
        check("semver: alpha increments", next_version(["0.1.0-alpha.1"], "minor", "alpha") == "0.1.0-alpha.2")
        check("semver: 0.x breaking -> minor", next_version(["0.1.0"], "major", "") == "0.2.0")
        check("semver: never sorts below history", next_version(["0.1.0-beta.2"], "patch", "alpha") == "0.1.1-alpha.1")
        # placefile
        make_place(tmp / "a.rbxl", "0.1.0-alpha.1")
        P = placefile.load(tmp / "a.rbxl")
        a = placefile.audit(P)
        check("placefile: binary LZ4 read", a["instances"] == 28 and a["stamp_version"] == "0.1.0-alpha.1", a["instances"])
        if importlib.util.find_spec("zstandard"):
            zstd_copy(tmp / "a.rbxl", tmp / "z.rbxl")
            Z = placefile.load(tmp / "z.rbxl")
            check("placefile: ZSTD chunks read", len(Z.insts) == 28 and "zstd" in Z.compression, dict(Z.compression))
        else:
            print("skip placefile ZSTD: zstandard not installed")
        (tmp / "x.rbxlx").write_text('<roblox version="4"><Item class="Workspace" referent="R0"><Properties>'
                                     '<string name="Name">Workspace</string></Properties><Item class="Script" '
                                     'referent="R1"><Properties><string name="Name">S</string><ProtectedString '
                                     'name="Source">print(1)</ProtectedString></Properties></Item></Item></roblox>')
        X = placefile.audit(placefile.load(tmp / "x.rbxlx"))
        check("placefile: XML read", X["counts"]["scripts"] == 1 and X["format"] == "xml")
        # setup
        make_git(tmp / "game")
        ms = tmp / "missions"
        hud = make_mission(ms, "260101-hud", "ui", "independent-critic", 8)
        make_mission(ms, "260102-wagon", "3d", "self-review", 8)
        home = tmp / "home"
        (home / ".rr-missions" / "260103-x").mkdir(parents=True)
        (home / ".rr-missions" / "260103-x" / "state.json").write_text("{}")
        p_ = subprocess.run([sys.executable, str(HERE / "rtlib.py"), "where"], capture_output=True, text=True,
                            env=dict(env, HOME=str(home)), cwd=tmp)
        check("missions: ~/.rr-missions (mission-control's default) is discovered", ".rr-missions" in p_.stdout, p_.stdout)
        make_place(tmp / "Lobby.rbxl", "0.1.0-alpha.1")
        make_place(tmp / "Trip.rbxl", "0.1.0-alpha.1")
        c, o = R("config", "--place", "Lobby", "--universe", "100", "--place-id", "200", "--start", code=0)
        check("config prints one line, not the JSON", o.count("\n") == 1 and "{" not in o, o)
        R("config", "--place", "Trip", "--universe", "100", "--place-id", "300", "--repo", str(tmp / "game"),
          "--missions", str(ms), code=0)
        c, o = R("config", "--bleed", "0")
        check("config refuses a 0-minute bleed-off", c == 2)
        R("init", "--channel", "alpha", code=0)
        c, o = R("init", code=2)
        check("init refuses a second release in flight", c == 2)
        R("attach", "Lobby", str(tmp / "Lobby.rbxl"), code=0)
        c, o = R("attach", "Trip", str(tmp / "Trip.rbxl"), code=0)
        check("attach audits and routes api", "route api" in o, o[-300:])
        c, o = R("collect", code=0)
        rel = json.loads((tmp / "rel/next/release.json").read_text())
        ch = {x["title"]: x for x in rel["changes"]}
        check("collect: feat -> Added/minor with Player-Note",
              ch.get("Coal low flashes the firebox", {}).get("bump") == "minor" and "flickers" in ch["Coal low flashes the firebox"]["note"])
        check("collect: fix -> Fixed/patch", ch.get("Lever pulled twice after lock", {}).get("section") == "Fixed")
        check("collect: refactor and Release-Note skip are internal",
              ch["Split module"]["audience"] == "internal" and ch["Tweak seat colours"]["audience"] == "internal")
        check("collect: missions need in-build confirmation",
              sum(1 for x in rel["changes"] if x["in_build"] == "unknown") == 2 and "--via" in o)
        ids = {x["src"].split(":")[1]: x["id"] for x in rel["changes"] if x["src"].startswith("mission:")}
        R("mark", ids["260101-hud"], "--in-build", "yes", "--title", "New HUD alerts", code=0)
        R("mark", ids["260102-wagon"], "--in-build", "no", code=0)
        c, o = R("collect", code=0)
        check("collect stops asking to retitle a retitled mission", "retitle" not in o, o[-300:])
        c, o = R("version", code=0)
        check("version: sets 0.1.0-alpha.1 when none is set", "0.1.0-alpha.1" in o, o)
        R("changelog", "--apply", code=0)
        R("changelog", "--apply", code=0)
        cl = (tmp / "rel/CHANGELOG.md").read_text()
        check("changelog --apply: one [Unreleased] section, not dated on draft day",
              cl.count("## [Unreleased]") == 1 and "## [0.1.0-alpha.1]" not in cl and "### Fixed" in cl, cl[:400])
        c, o = R("notes", code=0)
        brief = (tmp / "rel/next/NOTES_BRIEF.md").read_text()
        check("notes: brief holds template + canon voice; stdout is one summary line",
              "identity.tone.company" in brief and "D-007" in brief and "# Risky Rails" in brief
              and o.count("\n") <= 2, o[-300:])
        player = [x for x in json.loads((tmp / "rel/next/release.json").read_text())["changes"]
                  if x["audience"] == "player" and x["in_build"] == "yes"]
        internal = next(x["id"] for x in rel["changes"] if x["audience"] == "internal")
        nd = tmp / "rel/next"
        (nd / "PATCH_NOTES.src.md").write_text(f"# Notes: 50% off everything\nA notice from Management.\n"
                                               f"- untagged claim\n- Buy the pass for better odds! [{player[0]['id']}]\n"
                                               f"- Refactored stuff [{internal}]\n- Flight or Die crossover [C-99]\n"
                                               "The diesel train arrives next week.\n")
        (nd / "STORE_UPDATE.src.txt").write_text("Free coins giveaway this week\n")
        c, o = R("notes-check", code=1)
        check("notes-check catches untagged, D-007, internal, unknown tag, banned name, store rules, coverage",
              all(k in o for k in ("no [C-n] tag", "D-007", "is internal", "C-99", "Flight or Die", "free",
                                   "do not cover")), o[-900:])
        check("notes-check traces non-bullet lines: untraced notice, number, promise, parked siding",
              all(k in o for k in ("untraced line", "number 50%", "promises future content", "parked siding")), o[-900:])
        check("notes-check FAIL writes no 'clean' outputs", not (nd / "PATCH_NOTES.md").exists())
        tags = " ".join(f"[{x['id']}]" for x in player)
        (nd / "PATCH_NOTES.src.md").write_text("# Risky Rails 0.1.0-alpha.1: the company regrets nothing\n\n"
                                               + "".join(f"- {x['title']}. [{x['id']}]\n" for x in player)
                                               + "\nMind the gap.\n")
        (nd / "STORE_UPDATE.src.txt").write_text(f"UPDATE: coal-low firebox flicker, new HUD alerts. {tags}\n"
                                                 "TITLE: Risky Rails [PULL THE LEVER]\n")
        c, o = R("notes-check", code=0)
        check("notes-check passes clean notes and strips tags", c == 0 and "[C-" not in (nd / "PATCH_NOTES.md").read_text(), o)
        c, o = R("gate")
        g = (nd / "GATES.md").read_text()
        check("gate: NO-GO while security and bug bash are pending", c == 1 and "G5   security        PENDING" in o, o)
        check("gate: agent-marked in-build change is flagged (no --via)", "agent's word" in g, g[:600])
        check("gate: debug names: DEBUG-style flags only (antiCheatEnabled, CHEAT_DETECTION pass)",
              "antiCheatEnabled" not in g and "CHEAT_DETECTION" not in g)
        check("gate: G7 first release asks for phone evidence", "no baseline" in g, g[:900])
        R("mark", ids["260101-hud"], "--via", "chat selftest", code=0)
        c, o = R("evidence", "bugbash", "--result", "pass", "--by", "claude")
        check("evidence refuses a non-owner", c == 2 and "owner" in o)
        c, o = R("evidence", "security", "--result", "pass")
        check("security cannot be self-certified (no --by owner, no verdict file)", c == 2, o)
        (tmp / "bogus.json").write_text(json.dumps({"verdict": "PASS"}))
        c, o = R("evidence", "security", "--file", str(tmp / "bogus.json"))
        check("security evidence file must be an rr-exploit-guard verdict", c == 1 and "rr-exploit-guard" in o, o)
        R("evidence", "bugbash", "--result", "pass", "--by", "owner", "--note", "selftest", code=0)

        def sec(verdict, stage="alpha", d=nd):
            r = json.loads((d / "release.json").read_text())
            (d / "security").mkdir(exist_ok=True)
            (d / "security/SECURITY_GATE.json").write_text(json.dumps({
                "skill": "rr-exploit-guard", "verdict": verdict, "blocking": [], "hold": [], "stage": stage,
                "scanned_at": now(), "places": {f"{n}:{Path(i['file']).name}": i["sha256"] for n, i in r["places"].items()}}))
        sec("PASS", stage="beta")
        c, o = R("gate")
        check("G5: a verdict for another stage is not accepted", "G5   security        PENDING" in o, o)
        sec("PASS")
        c, o = R("gate")
        check("G8: independent 8/8 without a final pass is not certified", "G8   visuals         WARN" in o, o)
        led = hud / "critique-x" / "ledger.json"
        led.write_text(json.dumps(json.loads(led.read_text()) + [{"pass": 2, "kind": "final", "agent": "critic-2",
                                                                    "scores": {"A1": 8}}]))
        c, o = R("gate")
        check("gate: GO once evidence is in (G6 deferred, G8 re-reads the ledger: final pass agrees)",
              c == 0 and "G8   visuals         PASS" in o and "deferred" in (nd / "GATES.md").read_text(), o)
        c, o = R("approve", "--by", "claude", "--via", "x")
        check("approve refuses a non-owner", c == 2)
        R("approve", "--by", "owner", "--via", "selftest", code=0)
        R("config", "--luau-tests", "off", code=0)
        c, o = R("status", code=0)
        check("turning Luau tests off after approval voids it", "void" in o and "luau_tests" in o, o)
        R("config", "--luau-tests", "on", code=0)
        sec("FAIL")
        n0 = len(Mock.state["calls"])
        c, o = R("publish", "--live", "--confirm", "0.1.0-alpha.1")
        check("live publish re-runs the gates: a FAIL verdict after approval stops it",
              c == 1 and "NO-GO" in o and len(Mock.state["calls"]) == n0, o[-300:])
        make_place(tmp / "Trip.rbxl", "0.1.0-alpha.1", debug=True)
        R("attach", "Trip", str(tmp / "Trip.rbxl"), code=0)
        sec("PASS")
        c, o = R("status", code=0)
        check("re-attaching voids the approval", "void" in o, o)
        R("gate", code=0)
        R("approve", "--by", "owner", "--via", "selftest", code=0)
        c, o = R("publish", code=0)
        check("publish without --live is a dry run (key introspected, nothing published)",
              "DRY RUN" in o and "Ready" in o and not Mock.state["calls"] and Mock.state.get("introspect"), o[-300:])
        c, o = R("publish", "--live", "--confirm", "0.9.9")
        check("live publish needs --confirm VERSION", c == 1 and "--confirm" in o)
        Mock.state["expired"] = True
        c, o = R("publish", "--live", "--confirm", "0.1.0-alpha.1")
        check("live publish refused on an expired key (introspect)", c == 1 and "expired" in o, o[-300:])
        Mock.state["expired"] = False
        c, o = R("publish", "--live", "--confirm", "0.1.0-alpha.1", "--restart", code=0)
        kinds = [x[0] for x in Mock.state["calls"]]
        check("live publish: Saved x2 -> Luau x2 -> Published x2 -> restart",
              kinds == ["Saved", "Saved", "Luau", "Luau", "Published", "Published", "Restart"], kinds)
        check("restart bleed-off comes from canon (trip + results + boarding)",
              Mock.state["calls"][-1][1].get("bleedOffDurationMinutes") == 14, Mock.state["calls"][-1])
        check("start place published last", [x[1] for x in Mock.state["calls"] if x[0] == "Published"] == ["300", "200"])
        hist = json.loads((tmp / "rel/history.json").read_text())
        cl = (tmp / "rel/CHANGELOG.md").read_text()
        check("history records the release, next/ is archived, CHANGELOG dated at publish",
              hist[-1]["version"] == "0.1.0-alpha.1" and (tmp / "rel/0.1.0-alpha.1/release.json").is_file()
              and not (tmp / "rel/next").exists() and "## [0.1.0-alpha.1] - " in cl and "## [Unreleased]" in cl, cl[:300])
        c, o = R("status", code=0)
        check("status after a publish points at the open smoke checks", "smoke open" in o and "S1" in o, o)
        c, o = R("smoke", "--result", "S1=pss", "--by", "owner")
        check("smoke rejects a result that is not pass/fail/skip", c == 2)
        c, o = R("smoke", "--result", "S99=pass", "--by", "owner")
        check("smoke rejects an unknown id", c == 2)
        c, o = R("smoke", "--result", "S1=pass,s2=fail", "--by", "owner")
        check("smoke: ids normalised; P0 fail recommends rollback", c == 1 and "ROLLBACK RECOMMENDED" in o, o)
        # release 2: patch, script diff, growth, junk, failing then passing Luau tests
        subprocess.run(["git", "-C", str(tmp / "game"), "commit", "-q", "--allow-empty", "-m", "fix: coal counter"],
                       check=True)
        make_place(tmp / "Trip2.rbxl", "0.1.0-alpha.2", grow=True, debug=True)
        make_place(tmp / "Lobby2.rbxl", "0.1.0-alpha.2", junk=True)
        R("init", code=0)
        R("attach", "Lobby", str(tmp / "Lobby2.rbxl"), code=0)
        R("attach", "Trip", str(tmp / "Trip2.rbxl"), code=0)
        c, o = R("collect", code=0)
        check("collect: only new commits, script diff vs the last release",
              "1 new changes" in o and "scripts since 0.1.0-alpha.1" in o, o)
        c, o = R("version", code=0)
        check("version: 0.1.0-alpha.2", "0.1.0-alpha.2" in o, o)
        rel = json.loads((tmp / "rel/next/release.json").read_text())
        unk = [x["id"] for x in rel["changes"] if x["in_build"] == "unknown"]
        check("a mission marked out of the build comes back next release", len(unk) == 1)
        R("mark", *unk, "--in-build", "no", code=0)
        pid = [x["id"] for x in rel["changes"] if x["audience"] == "player" and x["in_build"] == "yes"]
        (tmp / "rel/next/PATCH_NOTES.src.md").write_text("# Fixes\n" + "".join(f"- Coal counter fixed. [{i}]\n" for i in pid))
        R("notes-check", code=0)
        sec("HOLD", d=tmp / "rel/next")
        c, o = R("gate", code=0)
        g = (tmp / "rel/next/GATES.md").read_text()
        check("gate: HOLD warns in alpha, growth and debug flag warn", "G5   security        WARN" in o
              and "parts 20->40" in g and "debug flag DEBUG" in g, o)
        check("G9: blank asset ids (script + property), demo script, demo-only module",
              all(k in g for k in ("blank asset id rbxassetid://0", "blank asset ids in properties", "AlertDemo",
                                   "only a demo script requires: Icons")), g[-1500:])
        R("approve", "--by", "owner", "--via", "selftest", code=0)
        Mock.state["fail_tests"], n0 = True, len(Mock.state["calls"])
        c, o = R("publish", "--live", "--confirm", "0.1.0-alpha.2")
        check("failing Luau tests stop the publish before anything goes live",
              c == 1 and "Published" not in [x[0] for x in Mock.state["calls"][n0:]], o[-300:])
        Mock.state["fail_tests"] = False
        R("gate", code=0)
        R("approve", "--by", "owner", "--via", "selftest", code=0)
        R("publish", "--live", "--confirm", "0.1.0-alpha.2", code=0)
        c, o = R("rollback", code=0)
        check("rollback dry run: previous release, publish-only requests",
              "0.1.0-alpha.2 -> 0.1.0-alpha.1" in o and "DRY RUN" in o and "Saved" not in o, o)
        c, o = R("rollback", "--live", "--confirm", "0.1.0-alpha.1")
        check("live rollback needs --by owner", c == 2)
        n0 = len(Mock.state["calls"])
        R("rollback", "--live", "--confirm", "0.1.0-alpha.1", "--by", "owner", code=0)
        hist = json.loads((tmp / "rel/history.json").read_text())
        plog = json.loads((tmp / "rel/0.1.0-alpha.2/publish-log.json").read_text())
        check("live rollback re-publishes archived files, marks the release, keeps the publish log",
              hist[-1]["status"] == "rolled_back" and [x[0] for x in Mock.state["calls"][n0:]] == ["Published", "Published"]
              and any(x["step"] == "published" for x in plog) and (tmp / "rel/0.1.0-alpha.2/rollback-log.json").is_file())
        c, o = R("rollback")
        check("no second rollback without the owner naming --to", c == 1 and "--to" in o, o)
        # release 3: rolled-back changes come back; ROLLBACK.md targets what is live; Studio route + record
        make_place(tmp / "Lobby3.rbxl", "0.1.0-alpha.3", union=True)
        R("init", code=0)
        c, o = R("attach", "Lobby", str(tmp / "Lobby3.rbxl"), code=0)
        check("unions force the Studio route", "route studio" in o, o)
        c, o = R("collect", code=0)
        check("changes of a rolled-back release come back", "Coal counter" in o, o[-600:])
        R("add", "Seats are comfier", "--section", "Changed", "--via", "chat selftest", code=0)
        c, o = R("version", code=0)
        R("plan", code=0)
        rb = (tmp / "rel/next/ROLLBACK.md").read_text()
        check("ROLLBACK.md targets the live content (alpha.1 restored), not the rolled-back build",
              "Target: 0.1.0-alpha.1" in rb and "rollback of 0.1.0-alpha.2" in rb, rb[:500])
        c, o = R("publish", "--live", "--confirm", "0.1.0-alpha.3")
        check("live publish refused on the Studio route", c == 1)
        c, o = R("record", "--place", "Lobby=77", "--by", "owner", code=0)
        hist = json.loads((tmp / "rel/history.json").read_text())
        check("record logs a Studio publish; an unapproved one is marked in history",
              hist[-1]["route"] == "studio" and hist[-1]["places"]["Lobby"]["version_number"] == 77
              and hist[-1].get("unapproved_publish"))
        R("init", code=0)
        R("add", "Placeholder", code=0)
        R("version", code=0)
        R("changelog", "--apply", code=0)
        R("abandon", "--reason", "selftest", code=0)
        cl = (tmp / "rel/CHANGELOG.md").read_text()
        check("abandon shelves next/ and drops its [Unreleased] section",
              any((tmp / "rel/abandoned").iterdir()) and not (tmp / "rel/next").exists()
              and "Placeholder" not in cl, cl[:300])
        # owner-named version, history seed, live-channel open-question block
        seed = ["--root", str(tmp / "rel-seed")]
        R(*seed, "init", "--channel", "live", code=0)
        R(*seed, "add", "Bigger depot", "--bump", "minor", "--via", "chat selftest", code=0)
        c, o = R(*seed, "version", "--after", "0.3.2", code=0)
        check("version --after seeds history: the next minor is 0.4.0", "0.4.0" in o and "seeded" in o, o)
        R(*seed, "version", "--set", "0.5.0", code=0)
        c, o = R(*seed, "version", "--apply")
        check("version --apply refuses to replace an owner-named version without --force", c == 2 and "owner" in o, o)
        c, o = R(*seed, "gate")
        check("G10 fails a live release while an OQ blocks the live channel (OQ-040)",
              c == 1 and "G10  open questions  FAIL" in o and "OQ-040" in (tmp / "rel-seed/next/GATES.md").read_text(), o)
        # other CLIs
        for s in ("opencloud.py", "gates.py", "placefile.py", "rtlib.py"):
            p = subprocess.run([sys.executable, str(HERE / s), "--help"], capture_output=True, text=True)
            check(f"{s} --help", p.returncode == 0 and len(p.stdout) > 50)
        p = subprocess.run([sys.executable, str(HERE / "opencloud.py"), "request", str(tmp / "Lobby.rbxl"), "--universe",
                            "1", "--place", "2"], capture_output=True, text=True, env=env)
        check("opencloud request redacts the key", "$ROBLOX_API_KEY" in p.stdout and "test-key" not in p.stdout)
        luau_tests()
    finally:
        srv.shutdown()
        if keep:
            print(f"kept {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)
        for d in HERE.parent.rglob("__pycache__"):
            shutil.rmtree(d, ignore_errors=True)
    bad = [n for n, ok in RESULTS if not ok]
    print(f"all {len(RESULTS)} passed" if not bad else f"{len(bad)} of {len(RESULTS)} FAILED: {', '.join(bad)}")
    return 1 if bad else 0


def luau_tests():
    sys.path.insert(0, str(Path.home() / ".cache" / "rr-tools" / "py"))
    try:
        from lupa import lua51
    except ImportError:
        print("skip run_tests.lua: lupa not installed (pip install --target ~/.cache/rr-tools/py lupa)")
        return
    src = (HERE.parent / "assets/luau/run_tests.lua").read_text()
    mock = r'''
local function inst(name, class, children, mod)
  local o = {Name = name, ClassName = class, children = children or {}, mod = mod}
  function o:IsA(c) return self.ClassName == c end
  function o:FindFirstChild(n) for _, c in ipairs(self.children) do if c.Name == n then return c end end end
  function o:GetDescendants() local out = {} local function walk(x) for _, c in ipairs(x.children) do
    table.insert(out, c) walk(c) end end walk(self) return out end
  return o
end
local services = {
  ReplicatedStorage = inst("ReplicatedStorage", "Folder", {inst("RR_Version", "ModuleScript", nil,
    function() return {version = VERSION, channel = "alpha"} end)}),
  ServerScriptService = inst("ServerScriptService", "Folder", {
    inst("Coal.spec", "ModuleScript", nil, function() return {
      ["coal ok"] = function() assert(1 + 1 == 2) end,
      ["coal bad"] = function() if FAIL then error("coal went negative") end end } end),
    inst("One.spec", "ModuleScript", nil, function() return function() end end)}),
  ServerStorage = inst("ServerStorage", "Folder", {})}
game = {GetService = function(_, n) return services[n] end}
require = function(m) return m.mod() end
'''
    for version, fail, want_ok, label in (("0.1.0-alpha.1", False, True, "passes"),
                                          ("0.1.0-alpha.1", True, False, "reports a failing spec"),
                                          ("0.0.9", False, False, "catches a stamp mismatch")):
        L = lua51.LuaRuntime(unpack_returned_tuples=True)
        L.globals().VERSION = version
        L.globals().FAIL = fail
        L.execute(mock)
        res = L.execute(src.replace("{{EXPECTED_VERSION}}", "0.1.0-alpha.1"))
        check(f"run_tests.lua (Lua 5.1) {label}", bool(res["ok"]) == want_ok and res["tests"] == 3,
              f"ok={res['ok']} tests={res['tests']} failed={res['failed']}")


if __name__ == "__main__":
    sys.exit(main())
