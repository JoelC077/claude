#!/usr/bin/env bash
# rr-data-and-money -> rr-bible proposals (2026-09-28). NOT run by the skill build (it only touches its own folder).
# The orchestrator replays this once against the repo copy of rr-bible, then runs lint.
#   bash bible-proposals.sh            # real canon (repo copy)
#   bash bible-proposals.sh --canon DIR  # a copy, for a dry run
# Source RBXM = Roblox creator-docs pages read on 2026-09-28 from github:Roblox/creator-docs (raw files).
set -euo pipefail
BIBLE_DIR="${RR_BIBLE_SKILL:-$(dirname "$(find /home/user ~/.claude/skills -maxdepth 5 -path '*rr-bible/SKILL.md' 2>/dev/null | grep -v synced | head -1)")}"
CANON_ARGS=()
if [[ "${1:-}" == "--canon" ]]; then CANON_ARGS=(--canon "$2"); CANON_DIR="$2"; else CANON_DIR="$BIBLE_DIR/canon"; fi
B() { python3 "$BIBLE_DIR/scripts/bible.py" "${CANON_ARGS[@]}" "$@"; }

# 1. source line (sources.md is edited by hand per rr-bible's SKILL.md; idempotent)
if ! grep -q '`RBXM`' "$CANON_DIR/sources.md"; then
  python3 - "$CANON_DIR/sources.md" <<'PY'
import sys, re
p = sys.argv[1]; s = open(p).read()
line = ("- `RBXM` — Roblox Creator Docs analytics + monetization: production/analytics (event-types, custom-events, "
        "funnel-events, economy-events), reference AnalyticsService, MarketplaceService, PolicyService; production/"
        "monetization (index, developer-products, subscriptions, price-optimization, paid-random-items, roblox-plus, "
        "engagement-based-payouts), creator-rewards.md, production/publishing/thumbnails.md, read from the GitHub mirror "
        "Roblox/creator-docs | fetched 2026-09-28 | github:Roblox/creator-docs/content/en-us\n")
anchor = "\n## unreachable"
s = s.replace(anchor, "\n" + line.rstrip("\n") + "\n" + anchor, 1) if anchor in s else s + line
open(p, "w").write(s)
PY
fi

# 2. platform facts (status platform)
B add-fact tech.analytics.server_only "AnalyticsService events only from the server in published games; never from the client or Studio" \
  --src RBXM --status platform --title "Analytics platform facts" --note "RR_Analytics prints instead of sending in Studio"
B add-fact tech.analytics.rate_limit "120 + 20 x CCU AnalyticsService requests per minute" --src RBXM --status platform \
  --note "limits reset daily; RR_Analytics keeps each server under 20 x players + 20"
B add-fact tech.analytics.limits "3 custom fields (8,000 combined values, then Other); 10 funnels x 100 steps; 100 custom event names; 20 transaction types and 100 SKUs (then Other)" \
  --src RBXM --status platform --note "currencies: 10 in the guide, 5 in the API reference: use one (Coins)"
B add-fact tech.analytics.delay "charts populate within about 24 h; events roll off 90 days after the last data" --src RBXM --status platform
B add-fact economy.platform.price_optimization "Managed pricing (regional pricing + price optimization); optimization needs about 60,000 transactions in 30 days and prices read in-game with GetProductInfo, not hard-coded" \
  --src RBXM --status platform
B add-fact economy.platform.paid_random "paid random items (Robux or Robux-purchasable currency, incl. luck/pity boosts): all outcomes with % odds summing to 100% before purchase; PolicyService ArePaidRandomItemsRestricted hides them where restricted" \
  --src RBXM --status platform --note "fare packs make coins Robux-purchasable, so a coin-priced random crate counts"
B add-fact economy.platform.presentation "discounts genuine and fair; no false scarcity or restarting countdowns; no pushy purchase copy with minors" \
  --src RBXM --status platform
B add-fact economy.platform.roblox_plus "Roblox Plus: subscribers get 10-20% off passes/products/subscriptions paid by Roblox; up to 750 R\$ per Plus sign-up driven; up to 100 R\$ per subscriber with 60+ min a month in paid private servers" \
  --src RBXM --status platform
B add-fact economy.platform.subscriptions "experience subscriptions: monthly auto-renew, priced in Robux or local currency, paid in Robux; benefits for the full term; no tiers of the same benefits" \
  --src RBXM --status platform
B add-fact economy.platform.thumbnail_personalization "2+ active thumbnails: Roblox shows each to random users, then gives more Home impressions to the winner per user group; reports impressions, qualified plays, QPTR per thumbnail" \
  --src RBXM --status platform --note "adaptive traffic: read descriptively (abtest.py compare), not as an A/B verdict"
B add-fact tech.security.receipt_handler "MarketplaceService:BindReceiptHandler (per-product filter, Enum.ReceiptDecision) is the newer alternative to ProcessReceipt; bound handlers take precedence" \
  --src RBXM --status platform

# 3. canon fix: the odds rule cites the wrong decision id (D-008 is the Depot Lobby; the odds rule is D-007)
B add-fact economy.rules.never_sell_odds "nothing sold changes the odds at a fork; no revives, no fork rerolls" \
  --src PLAN --status canon --note "D-007" --replace

# 4. open questions found by the economy sim and the money gate (each with a default so work proceeds)
B add-question "Is the crew's fare paid to each member in full, or split?" \
  --option "A: each crew member banks the full crew fare" --option "B: split equally across the crew" \
  --option "C: each member banks their own passengers' share" \
  --default "A (co-op never costs a player fare; solo is already scaled by gameplay.crew.scaling)" \
  --src PLAN --context "gameplay.station.bank pays a crew bank; the save data needs a per-player amount. rr-data-and-money's sim assumes A." \
  --affects gameplay.station.bank --blocks "save-data award logic, economy sim"
B add-question "Starting coins for a new player?" \
  --option "A: 0 (first run cannot order supplies)" --option "B: a welcome grant that covers one supply kit, logged as an Onboarding economy source" \
  --option "C: first trip's Depotron orders are free" \
  --default "B (sim: with 0 coins about 40% of runs start short of the kit and 61% of installs leave before loco 2)" \
  --src PLAN --context "economy.currency.float was superseded by save data; nothing says what a new profile holds." \
  --affects economy.currency.earn --blocks "profile defaults, onboarding funnel"
B add-question "Base fare per run by difficulty (missing canon)" \
  --option "A: sim-calibrated 1,700 / 2,100 / 2,650 / 3,300 for an arriving crew member (Easy..Insane)" \
  --option "B: derive from the alpha formula (miles minus a penalty per breakdown) once measured" \
  --default "A until alpha data, then B" --src PLAN \
  --context "gameplay.progress.first_unlock implies about 1,250-1,700 per early run; economy.passes.fare_packs implies about 2,000 per run (20,000 = about 10 runs)." \
  --affects gameplay.station.alpha_fare,economy.passes.fare_packs --blocks "unlock prices, fare pack sizes"
B add-question "Largest fare pack vs the 10-runs cap" \
  --option "A: cut the large pack to about 17,000 fare" --option "B: raise late-game fares so 10 runs reach 20,000" \
  --option "C: relax the cap to about 12 runs" --default "A (smallest change; sim mean run fare 1,702 x 10 = 17,019)" \
  --src PLAN --affects economy.passes.fare_packs --blocks "money gate M07"
B add-question "Locomotive 3-5 and Line 2 prices (missing canon)" \
  --option "A: 10,000 / 12,000 / 14,000 / 16,000 fare (sim: about 2 h apart through hour 8.3)" \
  --option "B: owner-set after alpha pacing data" --default "A" --src PLAN \
  --context "gameplay.progress.pacing asks a new locomotive every about 2 h through hour 10 and nothing above about 15 successful runs." \
  --affects gameplay.progress.ladder,gameplay.progress.pacing --blocks "unlock UI, economy sim"
B add-question "Auto Stoker (economy.passes.auto_stoker) vs D-007" \
  --option "A: drop it as a Robux item; if data shows coal is a chore, fix coal for everyone" \
  --option "B: sell it (needs D-007 changed: it automates a crisis system for the whole crew)" \
  --option "C: an unlock earned with fare, for everyone" \
  --default "A (money gate: sells power and changes the crew's run = co-op pay-to-win)" --src PLAN \
  --affects economy.passes.auto_stoker --blocks "post-launch monetisation"
B add-question "Conductor's Toolbelt +2 tool slots vs carry one thing in hand" \
  --option "A: make it cosmetic (tool skins, belt model) at the same price" \
  --option "B: keep +2 slots after risky-rails-mechanic-reviewer and an owner reading of D-007" --option "C: drop it" \
  --default "A (gameplay.supplies.hand and pillars.reuse_verbs; +2 slots changes crisis handling)" --src PLAN \
  --affects economy.passes.toolbelt --blocks "money gate HOLD"

B lint
