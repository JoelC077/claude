#!/usr/bin/env python3
"""Real Luau gates for rr-game-feel exports (the Luau parser and type checker, not a Lua 5.1 grammar).

  luau_check.py FILE... [--strict FILE,...] [--json]   compile every file (luau-compile --null); typecheck the
                                                       --strict files with luau-lsp + Roblox types (must be
                                                       clean); report diagnostics for the others (info)
  luau_check.py --status                               which tools are installed, where
  luau_check.py --install                              download the pinned tools into ~/.cache/rr-tools (network,
                                                       about 25 MB, once; nothing outside that folder changes)

Tools: PATH first, then ~/.cache/rr-tools/bin (luau-compile, luau-lsp); Roblox types:
~/.cache/rr-tools/globalTypes.None.d.luau. Pinned: luau 0.740 (luau-lang/luau), luau-lsp 1.70.1 and its
globalTypes.None.d.luau at the same tag. A sourcemap (ReplicatedStorage.RRFeel.<module> = file) is generated in
a temp folder so require(script.Parent...) resolves. Standard library only.
Exit: 0 pass, 1 a gate failed, 2 usage, 3 tools missing (gates SKIPPED: report "syntax unchecked").
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

sys.dont_write_bytecode = True
TOOLS = Path.home() / ".cache" / "rr-tools"
BIN = TOOLS / "bin"
DEFS = TOOLS / "globalTypes.None.d.luau"
PINS = {
    "luau": "https://github.com/luau-lang/luau/releases/download/0.740/luau-ubuntu.zip",
    "luau-lsp": "https://github.com/JohnnyMorganz/luau-lsp/releases/download/1.70.1/luau-lsp-linux-x86_64.zip",
    "types": "https://raw.githubusercontent.com/JohnnyMorganz/luau-lsp/1.70.1/scripts/globalTypes.None.d.luau",
}


def tool(name):
    p = shutil.which(name)
    if p:
        return p
    q = BIN / name
    return str(q) if q.is_file() and os.access(q, os.X_OK) else None


def status():
    return {"luau-compile": tool("luau-compile"), "luau-lsp": tool("luau-lsp"),
            "types": str(DEFS) if DEFS.is_file() else None}


def compile_check(path):
    """(state, message): state PASS, FAIL or SKIP (no luau-compile)."""
    lc = tool("luau-compile")
    if not lc:
        return "SKIP", "luau-compile not installed (luau_check.py --install)"
    r = subprocess.run([lc, "--null", str(path)], capture_output=True, text=True)
    if r.returncode == 0:
        return "PASS", "luau-compile"
    return "FAIL", "luau-compile: " + ((r.stderr or r.stdout).strip().splitlines() or ["error"])[0]


def sourcemap(files, folder):
    kids = [{"name": Path(f).name.split(".")[0], "className": "LocalScript" if ".client." in Path(f).name else "ModuleScript",
             "filePaths": [str(Path(f).resolve())]} for f in files]
    sm = {"name": "Game", "className": "DataModel", "children": [
        {"name": "ReplicatedStorage", "className": "ReplicatedStorage", "children": [
            {"name": "RRFeel", "className": "Folder", "children": kids}]}]}
    p = Path(folder) / "sourcemap.json"
    p.write_text(json.dumps(sm), encoding="utf-8")
    return p


def analyze(files, all_files):
    """{file: [diagnostic lines]} from luau-lsp analyze with Roblox types; None when tools are missing."""
    lsp = tool("luau-lsp")
    if not lsp or not DEFS.is_file():
        return None
    out = {}
    with tempfile.TemporaryDirectory() as td:
        sm = sourcemap(all_files, td)
        for f in files:
            r = subprocess.run([lsp, "analyze", "--platform", "roblox", f"--definitions=@roblox={DEFS}",
                                "--sourcemap", str(sm), str(f)], capture_output=True, text=True)
            lines = [ln for ln in (r.stdout + r.stderr).splitlines()
                     if ln.strip() and not ln.startswith("[INFO]") and "didChangeWatched" not in ln]
            out[str(f)] = lines
    return out


def check(files, strict=(), quiet=False):
    """Run the gates; returns (exit code, report lines)."""
    lines, fail, skipped = [], False, False
    for f in files:
        st, msg = compile_check(f)
        lines.append(f"  {st} syntax {Path(f).name}: {msg}")
        fail |= st == "FAIL"
        skipped |= st == "SKIP"
    res = analyze(list(strict) + [f for f in files if f not in strict], files)
    if res is None:
        lines.append("  SKIP typecheck: luau-lsp or Roblox types not installed (luau_check.py --install)")
        skipped = True
    else:
        for f, diag in res.items():
            name = Path(f).name
            if f in [str(x) for x in strict]:
                errs = [d for d in diag if "Error" in d]
                lines.append(f"  {'PASS' if not errs else 'FAIL'} strict typecheck {name}" +
                             ("" if not errs else ":\n    " + "\n    ".join(errs[:12])))
                fail |= bool(errs)
            elif not quiet:
                n = sum(1 for d in diag if "Error" in d)
                lines.append(f"  INFO typecheck {name}: {n} diagnostics (untyped Lua 5.1-compatible runtime; not gated)")
    return (1 if fail else 3 if skipped else 0), lines


def install():
    BIN.mkdir(parents=True, exist_ok=True)
    try:
        import urllib.request
        with tempfile.TemporaryDirectory() as td:
            for key in ("luau", "luau-lsp"):
                z = Path(td) / f"{key}.zip"
                urllib.request.urlretrieve(PINS[key], z)
                with zipfile.ZipFile(z) as zf:
                    zf.extractall(BIN)
            urllib.request.urlretrieve(PINS["types"], DEFS)
        for p in BIN.iterdir():
            if p.name.startswith("luau"):
                p.chmod(0o755)
    except Exception as e:  # network policy, proxy, missing release
        print(f"install failed: {e}\nmanual: download {PINS['luau']} and {PINS['luau-lsp']} into {BIN} (unzip, "
              f"chmod +x) and {PINS['types']} to {DEFS}")
        return 1
    print(f"installed into {TOOLS}: " + json.dumps(status()))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--strict", default="", help="comma list of files that must typecheck clean")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.install:
        return install()
    if a.status:
        print(json.dumps(status(), indent=1))
        return 0 if all(status().values()) else 3
    if not a.files:
        ap.print_help()
        return 2
    strict = [f for f in a.strict.split(",") if f]
    code, lines = check(a.files + [f for f in strict if f not in a.files], strict)
    if a.json:
        print(json.dumps({"code": code, "lines": lines}, indent=1))
    else:
        print("\n".join(lines))
        print({0: "luau_check PASS", 1: "luau_check FAIL", 3: "luau_check SKIPPED (tools missing): syntax unchecked"}[code])
    return code


if __name__ == "__main__":
    sys.exit(main())
