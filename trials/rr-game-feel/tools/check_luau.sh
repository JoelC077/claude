#!/usr/bin/env bash
# Luau gates for export/feel with real Luau tools (not a Lua 5.1 parser).
# Usage: tools/check_luau.sh [--install] [--help]
#   --install  fetch luau (luau-lang/luau release) and luau-lsp (JohnnyMorganz/luau-lsp release) plus the Roblox
#              type definitions into ~/.cache/rr-tools (about 20 MB, once). Nothing else is changed.
# Gates: 1) luau-compile --null on every file (the real Luau parser and compiler);
#        2) luau-lsp analyze with Roblox types + a sourcemap: RR_FeelKit*.luau must be clean in --!strict;
#           the rr-game-feel runtime files (untyped, nonstrict) are reported, not gated.
set -uo pipefail
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then sed -n 2,8p "$0"; exit 0; fi
M="$(cd "$(dirname "$0")/.." && pwd)"; X="$M/export/feel"; T=~/.cache/rr-tools; B="$T/bin"
DEFS="$T/globalTypes.None.d.luau"
if [[ "${1:-}" == "--install" ]]; then
  mkdir -p "$B"; tmp="$(mktemp -d)"
  curl -sSL -o "$tmp/luau.zip" https://github.com/luau-lang/luau/releases/download/0.740/luau-ubuntu.zip
  curl -sSL -o "$tmp/lsp.zip" https://github.com/JohnnyMorganz/luau-lsp/releases/download/1.70.1/luau-lsp-linux-x86_64.zip
  curl -sSL -o "$DEFS" https://raw.githubusercontent.com/JohnnyMorganz/luau-lsp/1.70.1/scripts/globalTypes.None.d.luau
  (cd "$tmp" && unzip -oq luau.zip -d "$B" && unzip -oq lsp.zip -d "$B"); chmod +x "$B"/luau*; rm -rf "$tmp"
fi
if [[ ! -x "$B/luau-compile" || ! -x "$B/luau-lsp" || ! -f "$DEFS" ]]; then
  echo "Luau tools missing: run $0 --install (or document: syntax only checked by luaparse, Lua 5.1 grammar)"; exit 2
fi
fail=0
cd "$X"
for f in *.lua *.luau; do
  if "$B/luau-compile" --null "$f" >/dev/null 2>"$M/luau-check/compile.err"; then echo "PASS compile $f"
  else echo "FAIL compile $f: $(head -1 "$M/luau-check/compile.err")"; fail=1; fi
done
an() { "$B/luau-lsp" analyze --platform roblox --definitions=@roblox="$DEFS" --sourcemap "$M/luau-check/sourcemap.json" "$@" 2>&1 | grep -v '^\[INFO\]\|didChangeWatched'; }
out="$(an RR_FeelKit.luau RR_FeelKitExample.client.luau)"
if [[ -z "$out" ]]; then echo "PASS strict typecheck RR_FeelKit.luau RR_FeelKitExample.client.luau (luau-lsp $("$B/luau-lsp" --version), Roblox types)"
else echo "FAIL strict typecheck:"; echo "$out"; fail=1; fi
for f in RR_Feel.lua RR_FeelMath.lua RR_FeelPresets.lua RR_FeelDemo.client.lua; do
  echo "INFO nonstrict diagnostics $f: $(an "$f" | grep -c 'Error:') (runtime is untyped; see FRICTION.md)"
done
exit $fail
