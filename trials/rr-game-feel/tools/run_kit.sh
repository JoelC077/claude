#!/usr/bin/env bash
# Re-run the feel-kit pipeline (rr-game-feel SKILL.md steps 2-5 and 7) for this trial mission.
# Usage: tools/run_kit.sh [--pass N] [--help]   (default pass 1; critic briefs are kept once written)
# Needs: python3 + Pillow, rr-game-feel, rr-bible, multiuse-critic (found by glob), optional ~/.cache/rr-tools
# (luaparse, luau-compile, luau-lsp + globalTypes.None.d.luau) for the Luau gates.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1   # never leave __pycache__ in the shared skill folder
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then sed -n 2,5p "$0"; exit 0; fi
PASS=1; [[ "${1:-}" == "--pass" ]] && PASS="$2"
M="$(cd "$(dirname "$0")/.." && pwd)"
find_skill() { dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path "*$1/SKILL.md" 2>/dev/null | sed -n 1p)"; }
FEEL="$(find_skill rr-game-feel)"; CRITIC="$(find_skill multiuse-critic)"
F="$FEEL/scripts/feel.py"; CK="$CRITIC/scripts/critic_kit.py"; CS="$CRITIC/scripts/contact_sheet.py"
export RR_FEEL_PRESETS="$M/src/feel" RR_BIBLE_DIR="$M/canon-sandbox"
P="$M/src/feel/preview"; PL="$M/plots"; X="$M/export/feel"

python3 "$F" validate --strict
python3 "$F" plot all --out "$PL" | tail -1
for g in lever crisis info actions; do python3 "$F" preview "$g" --out "$P" --gif; done
python3 "$F" preview hard_brake --out "$P/ev_hard_brake" --gif      # separate folder: preview EVENT overwrites <group>/
python3 "$F" preview alert_crate_landed --out "$P/ev_crate_landed" --gif

for pair in lever:$P/lever crisis:$P/crisis info:$P/info crate:$P/ev_crate_landed/info brake:$P/ev_hard_brake/actions; do
  n=${pair%%:*}; d=${pair#*:}; C="$M/critique-feel-$n"
  python3 "$F" crit "$C" --pass "$PASS" --from "$d" | sed -n 1p
  if [[ "$n" == lever ]]; then   # the drag curve never reaches the critic otherwise
    python3 "$CS" "$C/pass-$PASS/closeups.png" \
      "lever drag curve: finger to knob, detent and commit at 70%, snap home, snapback (OQ-031 default)=$PL/lever.png@1" \
      "lever: lever_commit with reduce motion, then the other events=$P/lever/_grid.png" --tile 1300x402 --max-width 1528 | sed -n 1p
  fi
  python3 "$CK" build "$C" --pass "$PASS" --kind full --profile G --role "senior game-feel designer" --images closeups.png | sed -n 1p
done

python3 "$F" build --out "$X"
python3 "$M/tools/kit_tuning.py" --presets "$M/src/feel" --feel "$F" --out "$X"
mkdir -p "$M/sheets"; cd "$M/sheets"
python3 "$CS" kit_curves_1_lever.png "lever drag: finger to knob, detent 70%, snap, snapback=$PL/lever.png" \
  "lever_commit (actor, signature)=$PL/lever_commit.png" "lever_detent_tick=$PL/lever_detent_tick.png" \
  "lever_snapback=$PL/lever_snapback.png" "lever_commit_crew (other clients)=$PL/lever_commit_crew.png" --tile 740x228 | sed -n 1p
python3 "$CS" kit_curves_2_brake_crate_fare.png "hard_brake (OQ-043 default)=$PL/hard_brake.png" \
  "alert_crate_landed=$PL/alert_crate_landed.png" "alert_fare_banked=$PL/alert_fare_banked.png" \
  "sustain: speed rumble fades as the brake drops Speed=$PL/sustain.png" "easing styles (used ones marked)=$PL/easing.png" --tile 740x228 | sed -n 1p
python3 "$CS" kit_curves_3_crisis.png "hud_crisis_arrival (every crisis: ticket shake, halo)=$PL/hud_crisis_arrival.png" \
  "alert_coal_low=$PL/alert_coal_low.png" "alert_pressure_high=$PL/alert_pressure_high.png" \
  "alert_breakdown=$PL/alert_breakdown.png" "alert_passengers_upset=$PL/alert_passengers_upset.png" --tile 740x228 | sed -n 1p

"$M/tools/check_luau.sh"
