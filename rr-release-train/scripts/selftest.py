#!/usr/bin/env python3
"""selftest.py - end-to-end test of rr-release-train on a temp releases root (never touches real releases).

  selftest.py [--keep]      run everything; prints one line per check and "all N passed"; --keep keeps the temp dir

Covers: semver rules, placefile (binary LZ4, ZSTD when the zstandard module exists, XML), collect (conventional
commits, trailers, tooling vs game repo, missions, script diff), mark/version/changelog, notes-check failures and
pass, gates (pending -> GO), owner-only refusals, approval voiding, publish dry-run and --live against a local mock
of the Open Cloud endpoints (Saved -> Luau tests -> Published -> restart), a failing Luau test that stops a publish,
the Studio route + record, smoke -> rollback advice, live rollback, abandon, and run_tests.lua in Lua 5.1 (lupa,
optional: pip install --target ~/.cache/rr-tools/py lupa). Canon is read from the real rr-bible (read-only).
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
def make_place(path, version, grow=False, union=False, debug=False, spec_ok=True):
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
        'local Store = ProfileStore.New("PlayerData_alpha1", {})\nreturn {}\n')
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
    (d / "state.json").write_text(json.dumps({"slug": slug, "kind": kind, "status": "done", "bar": 8}))
    (d / "mission.md").write_text(f"# Mission\nObjective: Build the {slug} thing, to 8/10, exported\n")
    (d / "critique-x" / "ledger.json").write_text(json.dumps([{"pass": 1, "agent": agent, "scores": {"A1": score}}]))


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
        if self.headers.get("x-api-key") != "test-key":
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
        check("placefile: binary LZ4 read", a["instances"] == 27 and a["stamp_version"] == "0.1.0-alpha.1", a["instances"])
        if importlib.util.find_spec("zstandard"):
            zstd_copy(tmp / "a.rbxl", tmp / "z.rbxl")
            Z = placefile.load(tmp / "z.rbxl")
            check("placefile: ZSTD chunks read", len(Z.insts) == 27 and "zstd" in Z.compression, dict(Z.compression))
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
        make_mission(ms, "260101-hud", "ui", "independent-critic", 8)
        make_mission(ms, "260102-wagon", "3d", "self-review", 8)
        make_place(tmp / "Lobby.rbxl", "0.1.0-alpha.1")
        make_place(tmp / "Trip.rbxl", "0.1.0-alpha.1")
        R("config", "--place", "Lobby", "--universe", "100", "--place-id", "200", "--start", code=0)
        R("config", "--place", "Trip", "--universe", "100", "--place-id", "300", "--repo", str(tmp / "game"),
          "--missions", str(ms), code=0)
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
              sum(1 for x in rel["changes"] if x["in_build"] == "unknown") == 2 and "mark" in o)
        ids = {x["src"].split(":")[1]: x["id"] for x in rel["changes"] if x["src"].startswith("mission:")}
        R("mark", ids["260101-hud"], "--in-build", "yes", "--title", "New HUD alerts", code=0)
        R("mark", ids["260102-wagon"], "--in-build", "no", code=0)
        c, o = R("version", code=0)
        check("version: 0.1.0-alpha.1", "0.1.0-alpha.1" in o, o)
        R("changelog", "--apply", code=0)
        R("changelog", "--apply", code=0)
        cl = (tmp / "rel/CHANGELOG.md").read_text()
        check("changelog --apply is idempotent", cl.count("## [0.1.0-alpha.1]") == 1 and "### Fixed" in cl)
        c, o = R("notes", code=0)
        check("notes brief carries canon voice", "identity.tone.company" in o and "D-007" in o, o[-400:])
        player = [x for x in json.loads((tmp / "rel/next/release.json").read_text())["changes"]
                  if x["audience"] == "player" and x["in_build"] == "yes"]
        internal = next(x["id"] for x in rel["changes"] if x["audience"] == "internal")
        nd = tmp / "rel/next"
        (nd / "PATCH_NOTES.src.md").write_text(f"# Notes\n- untagged claim\n- Buy the pass for better odds! [{player[0]['id']}]\n"
                                               f"- Refactored stuff [{internal}]\n- Flight or Die crossover [C-99]\n")
        (nd / "STORE_UPDATE.src.txt").write_text("Free coins giveaway this week\n")
        c, o = R("notes-check", code=1)
        check("notes-check catches untagged, D-007, internal, unknown tag, banned name, store rules, coverage",
              all(k in o for k in ("no [C-n] tag", "D-007", "is internal", "C-99", "Flight or Die", "free",
                                   "do not cover")), o[-900:])
        tags = " ".join(f"[{x['id']}]" for x in player)
        (nd / "PATCH_NOTES.src.md").write_text("# Risky Rails 0.1.0-alpha.1\n\nA notice from Management.\n\n"
                                               + "".join(f"- {x['title']}. [{x['id']}]\n" for x in player)
                                               + "\nMind the gap.\n")
        (nd / "STORE_UPDATE.src.txt").write_text(f"UPDATE: coal-low firebox flicker, new HUD alerts. {tags}\n"
                                                 "TITLE: Risky Rails [PULL THE LEVER]\n")
        c, o = R("notes-check", code=0)
        check("notes-check passes clean notes and strips tags", c == 0 and "[C-" not in (nd / "PATCH_NOTES.md").read_text(), o)
        c, o = R("gate")
        check("gate: NO-GO while security and bug bash are pending", c == 1 and "G5   security        PENDING" in o, o)
        c, o = R("evidence", "bugbash", "--result", "pass", "--by", "claude")
        check("evidence refuses a non-owner", c == 2 and "owner" in o)
        R("evidence", "bugbash", "--result", "pass", "--by", "owner", "--note", "selftest", code=0)
        (nd / "security").mkdir()
        (nd / "security/SECURITY_GATE.json").write_text(json.dumps({"verdict": "PASS", "blocking": [], "hold": [],
                                                                     "stage": "static+review", "scanned_at": now()}))
        c, o = R("gate")
        check("gate: GO once evidence is in (G6 deferred to Luau tests, G8 certified)",
              c == 0 and "G8   visuals         PASS" in o and "deferred" in (nd / "GATES.md").read_text(), o)
        c, o = R("approve", "--by", "claude", "--via", "x")
        check("approve refuses a non-owner", c == 2)
        R("approve", "--by", "owner", "--via", "selftest", code=0)
        make_place(tmp / "Trip.rbxl", "0.1.0-alpha.1", debug=True)
        R("attach", "Trip", str(tmp / "Trip.rbxl"), code=0)
        c, o = R("status", code=0)
        check("re-attaching voids the approval", "void" in o, o)
        c, o = R("publish", "--live", "--confirm", "0.1.0-alpha.1")
        check("live publish refused with a void approval", c == 1 and "approval" in o)
        R("gate", code=0)
        R("approve", "--by", "owner", "--via", "selftest", code=0)
        c, o = R("publish", code=0)
        check("publish without --live is a dry run", "DRY RUN" in o and not Mock.state["calls"], o[-300:])
        c, o = R("publish", "--live", "--confirm", "0.9.9")
        check("live publish needs --confirm VERSION", c == 1 and "--confirm" in o)
        c, o = R("publish", "--live", "--confirm", "0.1.0-alpha.1", "--restart", code=0)
        kinds = [x[0] for x in Mock.state["calls"]]
        check("live publish: Saved x2 -> Luau x2 -> Published x2 -> restart",
              kinds == ["Saved", "Saved", "Luau", "Luau", "Published", "Published", "Restart"], kinds)
        check("start place published last", [x[1] for x in Mock.state["calls"] if x[0] == "Published"] == ["300", "200"])
        hist = json.loads((tmp / "rel/history.json").read_text())
        check("history records the release and next/ is archived",
              hist[-1]["version"] == "0.1.0-alpha.1" and (tmp / "rel/0.1.0-alpha.1/release.json").is_file()
              and not (tmp / "rel/next").exists())
        c, o = R("smoke", "--result", "S1=pass,S2=fail", "--by", "owner")
        check("smoke: P0 fail recommends rollback", c == 1 and "ROLLBACK RECOMMENDED" in o, o)
        # release 2: patch, script diff, growth, failing then passing Luau tests
        subprocess.run(["git", "-C", str(tmp / "game"), "commit", "-q", "--allow-empty", "-m", "fix: coal counter"],
                       check=True)
        make_place(tmp / "Trip2.rbxl", "0.1.0-alpha.2", grow=True, debug=True)
        make_place(tmp / "Lobby2.rbxl", "0.1.0-alpha.2")
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
        (tmp / "rel/next/security").mkdir()
        (tmp / "rel/next/security/SECURITY_GATE.json").write_text(json.dumps({"verdict": "HOLD", "scanned_at": now()}))
        c, o = R("gate", code=0)
        g = (tmp / "rel/next/GATES.md").read_text()
        check("gate: HOLD warns in alpha, growth and debug flag warn", "G5   security        WARN" in o
              and "parts 20->40" in g and "debug flag DEBUG" in g, o)
        R("approve", "--by", "owner", "--via", "selftest", code=0)
        Mock.state["fail_tests"], n0 = True, len(Mock.state["calls"])
        c, o = R("publish", "--live", "--confirm", "0.1.0-alpha.2")
        check("failing Luau tests stop the publish before anything goes live",
              c == 1 and "Published" not in [x[0] for x in Mock.state["calls"][n0:]], o[-300:])
        Mock.state["fail_tests"] = False
        R("publish", "--live", "--confirm", "0.1.0-alpha.2", code=0)
        c, o = R("rollback", code=0)
        check("rollback dry run targets the previous release", "0.1.0-alpha.2 -> 0.1.0-alpha.1" in o and "DRY RUN" in o, o)
        c, o = R("rollback", "--live", "--confirm", "0.1.0-alpha.1")
        check("live rollback needs --by owner", c == 2)
        n0 = len(Mock.state["calls"])
        R("rollback", "--live", "--confirm", "0.1.0-alpha.1", "--by", "owner", code=0)
        hist = json.loads((tmp / "rel/history.json").read_text())
        check("live rollback re-publishes archived files and marks the release",
              hist[-1]["status"] == "rolled_back" and [x[0] for x in Mock.state["calls"][n0:]] == ["Published", "Published"])
        # release 3: Studio route (union) + record, then abandon
        make_place(tmp / "Lobby3.rbxl", "0.1.1-alpha.1", union=True)
        R("init", code=0)
        c, o = R("attach", "Lobby", str(tmp / "Lobby3.rbxl"), code=0)
        check("unions force the Studio route", "route studio" in o, o)
        R("add", "Seats are comfier", "--section", "Changed", code=0)
        R("version", code=0)
        c, o = R("publish", "--live", "--confirm", "0.1.1-alpha.1")
        check("live publish refused on the Studio route", c == 1)
        c, o = R("record", "--place", "Lobby=77", "--by", "owner", code=0)
        hist = json.loads((tmp / "rel/history.json").read_text())
        check("record logs a Studio publish", hist[-1]["route"] == "studio" and hist[-1]["places"]["Lobby"]["version_number"] == 77)
        R("init", code=0)
        R("abandon", "--reason", "selftest", code=0)
        check("abandon shelves next/", any((tmp / "rel/abandoned").iterdir()) and not (tmp / "rel/next").exists())
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
