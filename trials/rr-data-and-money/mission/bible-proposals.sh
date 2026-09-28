#!/usr/bin/env bash
# rr-data-and-money TRIAL mission -> rr-bible proposals (2026-09-28). NOT run: the trial may not write canon.
# Dry-run checked with --dry-run (would become OQ-042 at the time of the trial). The owner or orchestrator runs it, then `bible lint`.
# Already pending in ../bible-proposals.sh (skill build) and NOT repeated here: starting coins, base fare per difficulty,
# loco 3-5 + line 2 prices, largest fare pack vs the 10-runs cap, Toolbelt vs carry-one-thing.
set -euo pipefail
# APPLIED 2026-09-28 by the rr-bible reconcile as OQ-056 (src PLAN, DAM). Replaying would duplicate it.
echo "mission/bible-proposals.sh: already applied to rr-bible on 2026-09-28 (OQ-056); nothing to do"; exit 0
BIBLE_DIR="${RR_BIBLE_SKILL:-$(dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path '*rr-bible/SKILL.md' 2>/dev/null | grep -v synced | head -1)")}"
B() { python3 "$BIBLE_DIR/scripts/bible.py" "$@"; }
B add-question "Launch entry purchase: bring one identity item (horn or headlamp colour, 49 R\$) forward to launch?" \
  --option "A: Yes, one 49 R\$ identity item at launch as the first-purchase step" \
  --option "B: No, liveries stay post-launch; the 99 R\$ fare pack is the cheapest launch item" \
  --default "B (canon economy.passes.liveries says post-launch; the owner decides)" --src PLAN \
  --context "rr-data-and-money trial ladder: at launch the cheapest item is a time item (fare pack S, 99 R\$); money.md wants an identity entry at or under 99 R\$" \
  --affects economy.passes.liveries
B lint
