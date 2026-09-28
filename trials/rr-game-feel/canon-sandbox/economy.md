# Economy and money

In-game currency, supply prices, passes and products, pacing rules, platform money facts and the owner's budget. Monetisation rule zero: sell time, status and identity; never sell odds.

## currency · Currency
- `economy.currency.name` = `coins` | R2A and the data layer say coins; the HUD and terminal show "$"; the plan says fare (OQ-003) | src: R2A, TN, ST, PLAN | conflict
- `economy.currency.earn` = `earned at the END of a trip (fare banked at stations), spent DURING the next trip on a different server` | so it must save | src: R2A | canon
- `economy.currency.float` = `company petty-cash float per crew per trip until save data exists` | replaced by ProfileStore in alpha week 2 | src: R2A | superseded
- `economy.currency.recovery_fee` = `5` | coins charged when the company retrieves a player who fell off | src: R2A | canon
- `economy.currency.failed_trip` = `open: does a failed trip pay anything?` | owner's own open item (OQ-011) | src: R2A | conflict

## supplies · Supply catalogue (Depotron / Supply Terminal)
- `economy.supplies.coal` = `40` | FUEL, "Keeps your train going. One full sack."; 10 R$ placeholder | src: ST | proposed
- `economy.supplies.toolbox` = `120` | REPAIR, "Fixes broken junctions and train parts."; 30 R$ placeholder | src: ST | proposed
- `economy.supplies.sandwich` = `25` | FOOD, "Gives your crew energy. Slightly squashed."; 5 R$ placeholder | src: ST | proposed
- `economy.supplies.medkit` = `90` | HEALTH, "Heals one hurt crew member."; 25 R$ placeholder; plan uses medkits on passengers (OQ-014) | src: ST | proposed
- `economy.supplies.robux_option` = `Always / Only when short / Hidden` | terminal prop; R$ prices are placeholders "set in Studio" (OQ-010) | src: ST | conflict
- `economy.supplies.old_catalogue` = `COAL CRATE 40 (45 s, 10 loads), FOOD CRATE 60 (30 s), TOOLBOX 50 (60 s), MYSTERY CRATE 15 (20 s)` | cab-interior order screen, replaced by Supply Terminal v4 | src: CI | superseded
- `economy.supplies.server_prices` = `prices come from the server's own table, never the client; server checks the price and takes the coins` | src: R2A, CI | canon

## passes · Passes and products (plan catalogue, not yet built)
- `economy.passes.double_fare` = `299 R$` | pass, 2x banked fare; shown once on results after the best run so far | src: PLAN | proposed
- `economy.passes.toolbelt` = `149 R$` | Conductor's Toolbelt, +2 tool slots | src: PLAN | proposed
- `economy.passes.first_class` = `399 R$` | golden coach livery, gold name tag, unique whistle, VIP lounge | src: PLAN | proposed
- `economy.passes.express_depot` = `199 R$` | private platform + pick the line; ship private servers first instead | src: PLAN | proposed
- `economy.passes.private_server` = `150 R$/month` | enable at launch | src: PLAN | proposed
- `economy.passes.auto_stoker` = `449 R$` | post-launch, only if data shows coal is a chore | src: PLAN | proposed
- `economy.passes.fare_packs` = `2,500 / 7,500 / 20,000 fare for 99 / 249 / 599 R$` | 1.0; capped at about 10 runs of earnings; shown when short by under 30% | src: PLAN, LPB | proposed
- `economy.passes.liveries` = `49-199 R$ or fare` | liveries, horns, headlamp colours; post-launch | src: PLAN | proposed
- `economy.passes.whale_total` = `2,000-3,000 R$` | all passes + liveries; no gacha, no infinite sink | src: PLAN | proposed

## rules · Monetisation rules
- `economy.rules.never_sell_odds` = `nothing sold changes the odds at a fork; no revives, no fork rerolls` | D-008 | src: PLAN | canon
- `economy.rules.no_early_prompts` = `no shop pop-ups before the first bank; at most two purchase prompts, both after run 3+` | src: PLAN, LPB | canon
- `economy.rules.fair_packs` = `fare packs must never be cheaper per fare than playing well` | src: PLAN | canon
- `economy.rules.daily_line_fair` = `nothing makes the Daily Line pay-to-rank` | src: PLAN | canon
- `economy.rules.r15_only` = `Avatar Settings R15-only (unlocks the 18+ US DevEx rate)` | src: PLAN, LPB | proposed
- `economy.rules.regional_pricing` = `regional pricing on for passes` | src: PLAN | proposed

## platform · Roblox money facts (verify before relying; dated Sep 2026)
- `economy.platform.creator_share` = `70%` | of Robux from passes, products and private servers | src: PLAN | platform
- `economy.platform.devex_rate` = `0.0038 USD per earned Robux` | 0.0054 for age-checked 18+ US players in eligible (R15-only) games | src: PLAN | platform
- `economy.platform.devex_min` = `30000` | earned Robux minimum to cash out, once per calendar month | src: PLAN | platform
- `economy.platform.creator_rewards` = `5 R$ per day per active spender who plays 10+ min` | treat as rounding, not revenue | src: PLAN | platform
- `economy.platform.ad_credit` = `about 1 USD per ad credit; about 280 R$ per credit` | developer-reported | src: LPB | platform
- `economy.platform.affiliate` = `Creator Affiliate Program deprecated 24 Jul 2025; no creator codes` | in-game promo codes still work | src: LPB | platform

## budget · Owner budget (marketing)
- `economy.budget.total_gbp` = `300` | stretch 500-800 only on evidence | src: RGP, PLAN | canon
- `economy.budget.allocation` = `60 art; 20 measurement; 60-75 engagement ads; 60 plays ads; 40 lapsed re-activation; 40-60 reserve` | LPB plan; MDP proposes 100 ads / 80 creators / 50 creative / 70 contingency (OQ-019) | src: LPB, MDP | conflict
- `economy.budget.gate` = `no spend before D1 >= 10% on two cohorts and bounce < 25%` | money before retention buys traffic the algorithm ignores | src: LPB | proposed
- `economy.budget.never` = `paid creators, promotion services, Discord growth, pre-bought months of ads` | src: LPB, MDP | proposed
- `economy.budget.stop_rule` = `stop if cost per D7-retained player > 10x (Robux per visit x 30 x 0.0038 USD)` | src: LPB | proposed
