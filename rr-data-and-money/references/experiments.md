# Experiments: design and analysis that survive a small game

Read before planning or reading any A/B test (thumbnails, icons, prices, onboarding, anything).

## First question: is it testable at our traffic?
`abtest.py size --base P --mde-rel R --daily N` before anything else. Detecting 10% -> 12% needs about 3,841
users per arm; at 150 eligible players a day that is 7+ weeks. When `plan` says NOT TESTABLE (over 6 weeks):
test a bolder change, pick a higher-traffic metric (plays per impression beats D7), or ship and read pre/post,
labelled "pre/post, not an experiment" (seasonality, updates and featuring confound it).

## Design checklist (abtest.py plan writes it down and hashes it)
- One hypothesis, one change per variant (thumbnails: canon `release.thumbs.variant_rule`).
- Primary metric chosen before launch; guardrails with a non-inferiority margin (`--guardrail d1:0.01`).
- Unit: UserId for in-game changes (RR_Analytics `expose` hashes salt:UserId, identical in lobby and trip place
  and in Python); impressions for thumbnails/icons.
- **Co-op interference:** if the change is shared by the crew (lever rules, crisis timing, train-wide HUD),
  players in one server see both arms. Randomise by server or crew instead and analyse per crew; the sample
  grows by the design effect 1 + (m - 1) x ICC (m = crew size). Personal UI (a hint only you see) is fine per user.
- Exposure at the moment the change is seen (not at join); exposure logged once per player.
- alpha 0.05 two-sided, power 0.8, whole weeks (min 7 days) to cover weekday/weekend and update cycles.
- No peeking. `analyze` refuses a verdict before the planned sample and readout date and hides interim estimates.
  If an early stop matters (a price test losing money), plan `--looks K`: O'Brien-Fleming boundaries (simulated,
  any spacing; the sample grows x1.01-1.03). `abtest.py peek --looks 14` shows why: 14 daily peeks at p < 0.05
  give about a 22% false-win rate.
- SRM first: arm counts that miss the planned split (chi-square p < 0.001) mean assignment or logging is broken;
  the result is void whatever it says.

## Surfaces
- **Thumbnails.** Make variants with risky-rails-thumbnail-ideas; multiuse-critic judges them (200 px read) before
  they go live; the numbers only measure players. Roblox's native tool is **thumbnail personalization** (2+ active
  thumbnails): a bandit that shows each to random users, then gives more Home impressions to the winner per user
  group while still exploring. It reports impressions, qualified plays, session time per qualified play and
  qualified play-through rate (QPTR) per thumbnail. Adaptive traffic means no SRM and no fair head-to-head verdict:
  read it with `abtest.py compare` (Wilson CIs, flags a thumbnail clearly below the best once it has enough
  impressions). Roblox's advice: keep several active, test new ones with each major update, swap losers at the next
  update. Guardrail: D1/bounce of the players a thumbnail brings (`release.kpi.bounce_60s`); honest thumbnails only
  (`release.thumbs.formula`). One change per variant (`release.thumbs.variant_rule`).
- **Icons.** No native icon personalization in the docs (2026-09-28). A rotation (one icon per whole week) is
  pre/post, confounded by updates and featuring: label it so, and only rotate between updates. Icon rules:
  `release.thumbs.icon` (reads at 64 px).
- **Prices.** Roblox's own price optimization (part of Managed pricing, with regional pricing) needs about
  60,000 transactions in 30 days and prices read in-game with `GetProductInfo` (never hard-coded): script prices
  that way from day one so it can switch on later. Below that volume an in-game test is usually NOT TESTABLE too:
  ship the canon price and watch the memo. When it is testable: one developer product per price, same benefit, with
  "Allow external purchases" off so the Store tab cannot leak the cheaper price (passes are always on the Store tab:
  avoid pass price tests). Primary: Robux per exposed player (`--metric rpu`, exact for once-per-player items);
  guardrail: payer conversion. Stay inside the canon ladder, never test a money-gate FAIL, and the owner sets every
  live price in Creator Hub.
- **Onboarding.** New players only (expose on their first join), primary D1 or `first_bank` reached, guardrail
  session length; tag the onboarding funnel with the experiment in the tracking plan so the dashboard splits it.

## Reading the result
- Report the effect with its 95% CI, then the p-value. "NO DIFFERENCE" means the CI bounds the effect: keep the
  control or the cheaper option. A CI that excludes zero but sits below the MDE is real and small.
- More than two arms: Holm-adjusted p-values (analyze does it); the plan sized them with Bonferroni.
- Segments (platform, country, age) found after the fact are hypotheses for the next test, not results.
- Small counts switch to Fisher's exact test automatically (any expected cell under 10).
- Revenue per user with repeat purchases is heavy-tailed: use per-user rows (arm,value) for Welch + bootstrap.

## Methods (for audit)
Two proportions: pooled z; Newcombe hybrid-score CI for the difference; Katz log-ratio CI for lift; Fisher exact
for small cells. Means: Welch t with Satterthwaite df. RPU (single purchase at price P): variance P^2 p(1-p)/n.
Sample size: Fleiss normal approximation without continuity correction. SRM: chi-square goodness of fit.
Sequential: O'Brien-Fleming boundary C/sqrt(t), C = (1 - alpha) quantile of max |B(t_j)| over seeded Brownian
paths (matches the published table to 0.01). All in `scripts/statlib.py`, stdlib only.
