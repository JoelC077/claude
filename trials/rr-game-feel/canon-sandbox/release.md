# Release, store and growth

Dates, the alpha scope, phase gates, KPI targets, store page and thumbnail/icon rules, launch operations. Numbers from LPB correct older PLAN values where they differ.

## dates · Timeline
- `release.dates.alpha` = `week of 12 Oct 2026` | 3-5 testers, the steam train start to finish | src: R2A | canon
- `release.dates.soft_launch` = `about 20 Dec 2026, 16+ only` | a Friday 20:00 UK in the Christmas break recommended | src: PLAN, LPB | proposed
- `release.dates.full_push` = `Feb 2027` | Update 1 (second line, classes) + under-16 eligibility | src: PLAN | proposed
- `release.dates.scale_or_stop` = `March 2027 onward` | src: PLAN | proposed

## alpha · Road to Alpha (current plan)
- `release.alpha.week1` = `end segment (done), HUD notifications, modifiers + junction cards, tools + ordering supplies, tunnel + bridge biome` | the biome may slip into week 2 | src: R2A | canon
- `release.alpha.week2_must` = `live-server check, save data + teleport home, trip lifecycle, keep players on the train, fair crises for small crews, bug bash` | src: R2A | canon
- `release.alpha.week2_should` = `admin shortcuts, passengers (minimal), UI work (Incident Report, first-time hints, queue pads, phone pass, Persistent streaming)` | src: R2A | canon
- `release.alpha.week2_could` = `sound + crisis effects` | src: R2A | canon
- `release.alpha.sidings` = `diesel train, client-side world, "run it again" vote, rejoin after disconnect, analytics funnel, Monday parking lot (cab button behaviours, radio dispatcher, junction lamp, cab dressing, bullet train)` | parked on purpose | src: R2A | canon
- `release.alpha.feedback` = `after each trip ask: what confused you, best moment, would you play again?` | sit in and watch without explaining | src: R2A | canon
- `release.alpha.bug_bash` = `scripted: join together, one leaves, all leave, rejoin; fail, arrive, jump off, roof in tunnel; solo on difficulty 4; teleport home and spend; double-tap an order; spam the lever after it locks; 4x soak with F9 memory flat` | src: R2A | canon

## gates · Phase gates
- `release.gates.validation` = `at least half of 10-20 testers start a second run unprompted and talk about the lever` | Phase 1 gate; still open on 22 Sep | src: PLAN, WR | canon
- `release.gates.closed_test` = `run completion 30-60%, no P0 bugs, median session >= 10 min` | miss = slip launch two weeks | src: PLAN, LPB | canon
- `release.gates.spend` = `D1 >= 10% on two cohorts and bounce < 25% before any ad spend` | src: LPB | proposed
- `release.gates.continue` = `DAU >= 100, payer conversion >= 1.5%, >= 0.4 R$ per visit` | otherwise finish as a portfolio piece | src: PLAN, LPB | canon
- `release.gates.abandon` = `D1 < 8% after two onboarding iterations: stop spending` | src: LPB | proposed

## kpi · KPI targets (GameAnalytics Sep 2026 benchmarks; big games only)
- `release.kpi.bounce_60s` = `< 20%` | first-play bounce | src: PLAN, LPB | canon
- `release.kpi.bounce_180s` = `< 15%` | minutes 2-3 | src: LPB | proposed
- `release.kpi.session_min` = `>= 10` | one full run + results | src: PLAN, LPB | canon
- `release.kpi.d1` = `>= 10% soft launch; >= 13% before scaling spend` | PLAN's 12-15% superseded | src: LPB | proposed
- `release.kpi.d7` = `>= 2% soft launch; >= 3% by Update 1` | 5% is a stretch | src: LPB | proposed
- `release.kpi.d30` = `>= 0.7%` | src: LPB | proposed
- `release.kpi.completion` = `30-60%` | runs arriving / runs started | src: PLAN, LPB | canon
- `release.kpi.conversion` = `>= 1.5% of DAU` | src: PLAN, LPB | canon
- `release.kpi.funnel` = `join > picked up tool > shovelled coal > pulled lever > first bank > run end` | AnalyticsService steps, plus run_end(reason), player_left(phase), lever_pulled(by, choice, time_left) | src: LPB, PLAN | canon

## store · Store page
- `release.store.title` = `Risky Rails [one emoji] [PULL THE LEVER]` | swap the bracket per update; one emoji max; the docs' emoji did not survive export (likely a train), so pick it in Studio | src: PLAN, LPB | proposed
- `release.store.first_line` = `Keep the train alive with your crew. Pull the lever at every junction - safe track or risky track? - and bank your fare before it all goes wrong. 1-6 players.` | src: LPB | proposed
- `release.store.metadata_rules` = `no "free", no giveaway, no unrelated tags, no update tag that is not true` | src: LPB | platform
- `release.store.genre` = `Survival, sub-genre co-op/vehicle` | benchmark against Land or Die's audience, not train sims | src: LPB | proposed

## thumbs · Thumbnails and icon (formula; details in the thumbnail skill)
- `release.thumbs.formula` = `one readable idea at 200 px; characters large in the front third with exaggerated faces; action mid-moment; one dominant hue + hazard-yellow accent; 1-3 huge words top-left or top-centre; lever or split track in frame; honest` | src: LPB, THS | canon
- `release.thumbs.canvas` = `768 x 432 working canvas (16:9); 1920 x 1080 upload` | src: THS, LPB | canon
- `release.thumbs.bottom_strip` = `y 360-432 on 768x432 holds no text, faces or key objects` | metadata overlay zone | src: THS | canon
- `release.thumbs.launch_count` = `4-6 genuinely different concepts at launch` | keep top 2, replace bottom 3 with variants of the winner monthly | src: LPB | proposed
- `release.thumbs.variant_rule` = `a variant changes ONE thing only` | src: THS, LPB | canon
- `release.thumbs.icon` = `square, reads at 64 px: loco front-on at a slightly low angle on track splitting beneath it, hazard chevron on the buffer beam, one colour idea, no text` | "the train one", never a western | src: LPB, THS | canon

## ops · Launch and live operations
- `release.ops.timetable` = `16:00 / 20:00 / 22:00 UK daily for the first two weeks, the owner on the train` | src: LPB | proposed
- `release.ops.captains` = `6-10 Discord crew captains; reward a role and a cosmetic, never Robux` | src: LPB | proposed
- `release.ops.no_ads_day1` = `no ads in the first 24 hours` | src: LPB | proposed
- `release.ops.update_cadence` = `a titled update every 2-4 weeks, each with an Event, a code, a title bracket change` | src: PLAN, LPB | proposed
- `release.ops.marketing_time` = `about 45 min/day marketing; protect build time` | src: LPB | proposed
- `release.ops.moments` = `Roblox Moments/Captures API: prompt a capture at fail moments` | src: LPB | proposed
- `release.ops.taglines` = `Every fork is a bet. / Keep it alive. Pick a track. Bank it before it blows. / Left is safe. Right pays double. / Who pulled the lever?` | src: LPB | proposed
