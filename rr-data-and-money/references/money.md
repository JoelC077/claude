# Money: products, value ladder, prices, guardrails

Read when adding, pricing, prompting or reviewing anything sold, or when asked "how do we make money".
Canon first: `bible get economy.passes --values`, `bible get economy.rules --values`, `bible get D-007`, OQ-010.

## Product types (Roblox creator-docs, fetched 2026-09-28; proposed to rr-bible as source RBXM)
| type | behaviour | API | Risky Rails use |
|---|---|---|---|
| Pass | one-time Robux fee, permanent, sold on the Store tab and in-game (1 R$ minimum); never reaches ProcessReceipt: the server applies it on `PromptGamePassPurchaseFinished` and checks `UserOwnsGamePassAsync` on join | `UserOwnsGamePassAsync`, `PromptGamePassPurchase`, `PromptGamePassPurchaseFinished` | Double Fare, Toolbelt, First Class, liveries |
| Developer product | repeatable; Store-tab sales only if "Allow external purchases" is on (after a test-mode check) | `PromptProductPurchase`; grant in `BindReceiptHandler` (per-product filter, returns `Enum.ReceiptDecision`) or the legacy `ProcessReceipt`, never in `PromptProductPurchaseFinished`; idempotent by PurchaseId (`tech.security.process_receipt`) | fare packs |
| Subscription | monthly auto-renew, priced in Robux or local currency, paid to you in Robux; benefits for the full term; no Bronze/Silver/Gold tiers of the same benefits | `GetUserSubscriptionStatusAsync`, `PromptSubscriptionPurchase`, `PromptCancelSubscription` | none in canon (owner decision) |
| Private servers | monthly Robux fee | experience settings | `economy.passes.private_server` |
| Premium / Creator Rewards | Premium engagement payouts ended 24 Jul 2025, replaced by Creator Rewards (`economy.platform.creator_rewards`; the docs add: Active Spender = $9.99+ spent in 60 days, and yours must be one of their first three experiences that day). Premium perks must not give a gameplay advantage | `MembershipType`, `PromptPremiumPurchase` | perks only if cosmetic |
| Roblox Plus | subscribers get 10-20% off passes, products and subscriptions, paid by Roblox (your earnings per sale unchanged); up to 750 R$ per Plus sign-up you drive; up to 100 R$ per subscriber with 60+ min a month in paid private servers | `PromptRobloxSubscriptionPurchase` | a reason to keep private servers paid |
| Managed pricing | regional pricing + price optimization; optimization needs about 60,000 transactions in 30 days and prices read with `GetProductInfo` | `GetProductInfo`, `GetUsersPriceLevelsAsync` | script prices dynamically from day one |

Robux to money: earned R$ = price x `economy.platform.creator_share`; USD = earned x `economy.platform.devex_rate`
(cash-out minimum `economy.platform.devex_min`). `econ.py ladder` prints both per product. Roblox does not keep
per-user purchase history for developer products: save grants in the profile.

## Value ladder (what a healthy catalogue looks like)
- Entry item at or under 99 R$ that is identity (a livery, a horn): the first purchase is the hardest.
- One core time item (Double Fare) priced mid-ladder and shown once, at a proud moment (results after the best
  run so far, canon `economy.passes.double_fare`).
- A status anchor above it (First Class) so the core item reads as the sensible buy.
- A ceiling: canon `economy.passes.whale_total` (no gacha, no infinite sink). Veterans' spare fare goes into
  fare-priced cosmetics (`economy.passes.liveries`), never into an endless Robux sink.
- Steps of about x1.3-x2 between neighbours; gaps over x3 leave players nowhere to climb (ladder flags them).
- Price endings players already know on Roblox (49, 99, 149, 199, 249, 299, 399, 499); regional pricing is canon
  `economy.rules.regional_pricing` (proposed).
- Fare packs: bulk is better value per fare, but never better than earning it (`economy.rules.fair_packs`); cap and
  when they may be shown: `economy.passes.fare_packs` (the economy preset carries the numbers, canon-checked). The
  sim checks the cap against simulated run fares; the gate fails a pack over it.
- A ladder is judged on what ships: `econ.py ladder` shows launch states by default (`--state all` adds
  post-launch); an item that exists only under an open question's non-default option is an owner option beside the
  ladder, labelled, not its entry step.

## Guardrails (econ.py guard -> MONEY_GATE.md/.json; FAIL blocks release, HOLD needs the owner)
| rule | what fails | why |
|---|---|---|
| M01 | anything that sells odds, survival or power; HOLD for access/convenience | D-007: time, status and identity only |
| M02 | effect text that reads like odds (revive, reroll, shield, auto-repair...) under a harmless label | honesty of the label |
| M03 | gameplay-touching items (tools, carry rule, crisis handling): HOLD until risky-rails-mechanic-reviewer and the owner | pillars `reuse_verbs`, `four_systems` |
| M04 | one buyer changes the whole crew's run | co-op pay-to-win: the crew did not pay |
| M05 | paid random items, including coin-priced ones (fare packs make coins Robux-purchasable) and luck or pity boosts: every outcome's odds as percentages summing to 100% shown before purchase, `PolicyService:GetPolicyInfoForPlayerAsync(p).ArePaidRandomItemsRestricted` honoured, and an owner decision because canon says no gacha | Roblox paid random items policy; `economy.passes.whale_total` |
| M06 | prompts too early or too many placements (numbers from the canon-checked economy preset) | `economy.rules.no_early_prompts` |
| M07 | fare packs over the cap (a 10% tolerance for canon's "about" is printed) or shown too early | `economy.passes.fare_packs` |
| M08 | anything that changes Daily Line rank; fare multipliers must rank unboosted fare | `economy.rules.daily_line_fair` |
| M09 | price trust, receipts, double grants: handed to rr-exploit-guard | `tech.security.*` |
| M10 | subscriptions without a per-period benefit or cancel behaviour | players must get what renews |
| M12 | staking banked coins on a chance outcome (coins are buyable via packs) | that is wagering, not a fork bet |
| M15 | products that depend on an open question (OQ-010 Robux supplies) | the owner decides first |
| M16 | a price or pack size that departs from its canon value (HOLD) | a mission may propose, the owner decides |
| M17 | a launch-state item whose canon says post-launch (HOLD) | the owner moves it, not the ladder |
Hidden products never HOLD or FAIL (INFO only); post-launch ones show as FUTURE. `--gate`: exit 1 FAIL, 3 HOLD.

Presentation rules the gate cannot see (Roblox monetization guidelines; check by hand): discounts must be genuine
(not always "on sale") and fair (not a pressure window); no false scarcity, no countdown that restarts; no pushy
copy with minors ("View Item", "See Price", not "BUY NOW"); PolicyService gates subscriptions, commerce, paid random
items and trading per player. House rules on top: no shop pop-ups mid-crisis, copy says exactly what is bought,
prompts dismiss in one tap. The audience moves younger after launch (`identity.audience.target`).

Current findings on the canon catalogue (run the gate for the live list): Auto Stoker automates a crisis system
for the whole crew (M01 + M04; post-launch, so FUTURE); the Toolbelt's +2 hotbar tool slots (`gameplay.supplies.tools`)
mean fewer trips per crisis, convenience that can act as survival power under D-007 (M03 HOLD; the carry-one-thing
hand rule is separate; the base slot count is not in canon); Robux supplies stay hidden (OQ-010 default A).

## Adding or changing a product (the order that avoids rework)
1. Gameplay-touching? risky-rails-mechanic-reviewer first; save its checklist output as `<R>/money/review-<id>.md`.
2. Add it to `<R>/presets/catalogue.json` (a copy; price as `{v, canon}` once canon has it, else `{v, assumed}` and
   propose it through bible.py).
3. `econ.py guard --sim econ.json` (+ `--src` for prompt call sites) and `econ.py sim` if it adds fare or changes pacing.
4. Owner decides (`bible decide` / `add-fact --src "owner DATE"`); the owner sets the live price in Creator Hub.
5. rr-exploit-guard audits the receipt and grant code; the owner reads `MONEY_GATE.json` before release
   (rr-release-train has no money gate yet; SKILL.md Plugs has the proposed entry).
6. Test the price only if traffic allows (experiments.md); otherwise ship at the canon price and watch the memo.
