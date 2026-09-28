# Gameplay constants

Crew, run flow, speeds, fuel, crises, alert presets, difficulty, forks, modifiers, stations, supplies, results. Numbers marked `conflict` are open (see OQ ids); never pick one silently.

## crew · Crew and servers
- `gameplay.crew.max` = `6` | players per server; one train per server | src: PLAN, BP | canon | check: (?:up to|max(?:imum)?(?: of)?|1\s*[-–]\s*)\s*(\d+)\s*(?:players|crew)\b
- `gameplay.crew.min` = `1` | solo must be a real game | src: PLAN, R2A | canon
- `gameplay.crew.scaling` = `solo x1.6, 2 players x1.25, 3+ x1 (multiply event gaps; recalc on join/leave)` | src: R2A | canon
- `gameplay.crew.small_easy` = `difficulty 1 with fewer than 3 players: one crisis at a time` | src: R2A | canon
- `gameplay.crew.no_pairs` = `no crisis needs two people at once` | src: R2A | canon
- `gameplay.crew.roles` = `roles self-select by grabbing tools; no class menu at MVP` | classes are a 1.0 feature | src: PLAN | canon
- `gameplay.crew.spawn` = `SpawnLocations only on the train, never inside a segment` | src: R2A | canon
- `gameplay.crew.launch_cap` = `4` | max players for the first launch fortnight so servers fill (recommendation) | src: LPB | proposed

## run · Run flow
- `gameplay.run.length_min` = `12` | a full trip today (alpha build) | src: R2A | measured
- `gameplay.run.target_min` = `9-11` | design target per run | src: PLAN | proposed
- `gameplay.run.queue_countdown_s` = `15` | queue pads launch after 15 s with whoever is on; never a solo waiting alone | src: R2A, LPB | canon
- `gameplay.run.board_wait_s` = `45` | wait for all expected UserIds to load, then time out; HUD shows "Waiting for {name} to board..." | src: R2A | canon
- `gameplay.run.depart` = `whistle, then ramp to Normal over about 5 s` | start at a station with Speed 0 | src: R2A | canon
- `gameplay.run.first_event_s` = `45-75` | first event is the windows (easy to read) | src: R2A | canon
- `gameplay.run.first_fork` = `about 2:00` | first bet while stakes are low | src: PLAN, LPB | proposed
- `gameplay.run.first_bank` = `about 4:00` | so an early fail still keeps something | src: PLAN, LPB | proposed
- `gameplay.run.arrival` = `station segment with a StopMarker; lock throttle, stop events and coal drain; Miles counter hits 0 as the train stops` | end segment done 27 Sep | src: R2A | measured
- `gameplay.run.brake_formula` = `Speed = math.min(Speed, math.sqrt(2 * BRAKE * distanceToStop))` | lock the throttle while arriving | src: R2A | canon
- `gameplay.run.brake_const` = `5` | stops from Normal in about 7 s over about 120 studs; tune by feel | src: R2A | canon
- `gameplay.run.results_home_s` = `30` | results screen sends everyone home | src: R2A | canon
- `gameplay.run.teleport_retries` = `3` | pcall retries, then kick with "your coins are saved" | src: R2A | canon
- `gameplay.run.leavers` = `if the driver leaves, controls free up; no crisis waits on someone who has gone` | src: R2A | canon
- `gameplay.run.fail_screen` = `fail uses the same results screen; banked fare is kept` | src: R2A, PLAN | canon

## speed · Throttle and speed (as built)
- `gameplay.speed.slow` = `20` | Speed value (studs/s) at the Slow notch = 0.20 mi/s | src: CB, CI | canon
- `gameplay.speed.normal` = `35` | Normal notch = 0.35 mi/s; dashboard shows 35 MPH | src: CB, CI | canon
- `gameplay.speed.fast` = `50` | Fast notch = 0.50 mi/s | src: CB, CI | canon
- `gameplay.speed.studs_per_mile` = `100` | as built: Miles = distance / 100 and Speed/100 = mi/s; the Dimension System says 160 (OQ-005) | src: R2A, CB | conflict
- `gameplay.speed.drives` = `Speed drives scenery velocity, camera shake, wheel sound and steam particle rate` | src: PLAN | canon
- `gameplay.speed.loco_table` = `Starter 0.35, Diesel 0.50, Electric 0.75, Bullet 1.00 mi/s` | drawn at 160 studs/mile; recheck against as-built scale (OQ-005) | src: DS | proposed

## fuel · Firebox and coal
- `gameplay.fuel.burn_slow_pct_s` = `0.25` | fuel % per second at Slow | src: CB, WR | canon
- `gameplay.fuel.burn_normal_pct_s` = `0.40` | src: CB, WR | canon
- `gameplay.fuel.burn_fast_pct_s` = `0.70` | src: CB, WR | canon
- `gameplay.fuel.shovel_pct` = `4` | one shovel load, about 1.5 s to shovel | src: CB, WR | canon
- `gameplay.fuel.smother_pct` = `90` | over 90% smothers the fire: mashing the firebox is wrong | src: CB | canon
- `gameplay.fuel.bin_loads` = `40` | both cab bins together; a 250-mile run at Normal needs about 70, so top up from the coach or at a stop | src: CB | proposed
- `gameplay.fuel.coal_location` = `two coal bins in the cab against the back wall, either side of the doorway` | no tender car (D-013) | src: CB, WR | canon

## crisis · The four crisis systems
- `gameplay.crisis.systems` = `firebox/coal, boiler pressure, breakdowns, passengers` | four, not eight (D-003) | src: PLAN, MRS | canon
- `gameplay.crisis.firebox` = `shovel coal from the bins into the firebox; fire drives pressure` | ignored: fire dies, pressure drops, train stalls (soft fail) | src: PLAN, WR | canon
- `gameplay.crisis.pressure` = `gauge in the cab; open the safety valve or brake when it redlines` | ignored: boiler explosion (hard fail); numbers not yet defined (OQ-013) | src: PLAN | canon
- `gameplay.crisis.breakdowns` = `broken windows, electrics down, axle sparks, coupling strain, derailed bogie` | spatial task along the train, sometimes on the roof | src: PLAN, R2A, WR | canon
- `gameplay.crisis.windows` = `windows smash; passengers scream and get distressed` | first event of every run; Dodgy track doubles it | src: R2A | canon
- `gameplay.crisis.electrics` = `electrics down: power box wire-matching game (match colour terminals, lights ControlUnit.Light1-3); HUD stack hides or glitches` | src: R2A, WR, CI | canon
- `gameplay.crisis.coupling` = `coupling snaps: lose the carriage and its passengers` | src: PLAN | proposed
- `gameplay.crisis.passengers` = `seated NPCs (diner NPCs reused); mood calm > distressed > critical; drops during crises` | sandwiches calm them; distressed lowers fare; all dead = hard fail | src: PLAN, R2A | canon
- `gameplay.crisis.passenger_hunger` = `hunger state shown by a billboard icon (sandwich, thermometer, skull)` | src: WR | proposed
- `gameplay.crisis.fail_states` = `boiler explosion (hard), all passengers dead (hard), stall (soft), terminus buffer overrun (fail)` | src: PLAN, DS | canon
- `gameplay.crisis.fail_cinematic` = `3-second camera moment per fail, designed to be clipped` | boiler bursts, then YOU'RE FIRED stamp | src: PLAN, R2A | proposed

## alerts · HUD alert presets (exact texts; layout in ui.hud)
- `gameplay.alerts.transport` = `one server-driven RemoteEvent: show alert (ID) and clear alert (ID); one client script owns the stack` | counts per ID, e.g. WINDOW BROKEN x4 | src: R2A | canon
- `gameplay.alerts.coal_low` = `COAL LOW! / Shovel coal in the firebox!` | kind danger, icon coal | src: TN | canon
- `gameplay.alerts.pressure_high` = `PRESSURE HIGH! / The boiler's gonna blow!` | kind danger, icon gauge | src: TN | canon
- `gameplay.alerts.breakdown` = `BREAKDOWN! / Grab a wrench and fix it!` | kind danger, icon wrench; per-fault IDs open (OQ-012) | src: TN | canon
- `gameplay.alerts.passengers_upset` = `PASSENGERS UPSET! / Check the carriages, fast!` | kind danger, icon passenger | src: TN | canon
- `gameplay.alerts.junction_ahead` = `JUNCTION AHEAD! / Safe or risky? Pull it!` | kind risk, icon lever | src: TN | canon
- `gameplay.alerts.risky_route` = `RISKY ROUTE! / Multiplier up / X2` | kind risk, icon fork, stamp X2 | src: TN | canon
- `gameplay.alerts.fare_banked` = `FARE BANKED! / Station paid out / $120` | kind cash, icon coin; merges +$40 each with a count badge; $12,000 shows $12K | src: TN | canon
- `gameplay.alerts.crate_landed` = `CRATE LANDED! / Grab it before it slides off!` | kind info, icon crate | src: TN | canon
- `gameplay.alerts.crew_joined` = `CREW JOINED! / {name} is aboard` | kind info; names cap at 10 chars + ellipsis | src: TN | canon
- `gameplay.alerts.crew_left` = `CREW LEFT! / {name} left the train` | kind info | src: TN | canon
- `gameplay.alerts.life_danger_ms` = `7000` | sticky variant: no bar, stays until fixed | src: TN | canon
- `gameplay.alerts.life_risk_ms` = `6000` | src: TN | canon
- `gameplay.alerts.life_cash_ms` = `4500` | src: TN | canon
- `gameplay.alerts.life_info_ms` = `5000` | src: TN | canon
- `gameplay.alerts.first_hints` = `3-4 first-time hints, once per player, saying WHERE (e.g. "Electrics down - power box, coach end")` | saved as a hints-seen flag | src: R2A | canon

## difficulty · Difficulty tiers
- `gameplay.difficulty.tiers` = `Easy, Medium, Hard, Insane` | src: DS, RN, DTU | canon
- `gameplay.difficulty.numeric` = `difficulty 1-4 = Easy, Medium, Hard, Insane` | R2A counts in numbers; mapping inferred | src: R2A, DS | assumed
- `gameplay.difficulty.trip_miles` = `250 / 312.5 / 375 / 437.5` | base 250 +25% per step (cab screens built on it); Drawing Set says 300/375/469/586 (OQ-004) | src: CB, DS | conflict
- `gameplay.difficulty.read_once` = `read Difficulty once per server, not per player` | src: R2A | canon
- `gameplay.difficulty.gantry_countdown_s` = `10` | 7 s on harder lines | src: PLAN | proposed
- `gameplay.difficulty.band_easy` = `x1.2-1.4` | single system, telegraphed, nothing fatal | src: RN | proposed
- `gameplay.difficulty.band_medium` = `x1.5-1.7` | two systems interact or one pushed hard | src: RN | proposed
- `gameplay.difficulty.band_hard` = `x1.8-2.2` | multi-system, real fail risk, a hidden element | src: RN | proposed
- `gameplay.difficulty.band_insane` = `x2.5-3.0` | attacks coordination, not just the train | src: RN | proposed

## fork · Junctions and the lever
- `gameplay.fork.safe` = `x1.0 fare multiplier, one known mild hazard` | src: PLAN | canon
- `gameplay.fork.risky` = `x1.5-2.0 fare multiplier (up to x3.0 on Insane), one revealed hazard plus one hidden "?"` | src: PLAN, RN | canon
- `gameplay.fork.stacking` = `multipliers stack across the run and apply to fare banked at the next station` | src: PLAN | canon
- `gameplay.fork.hidden_rule` = `the hidden hazard is which variant, never whether` | a narrowed unknown, or the fork is a coin flip | src: RN | canon
- `gameplay.fork.lever` = `a physical lever pulled left or right under a gantry countdown; the cab map/screens show the branches` | never a UI vote (D-004) | src: PLAN | canon
- `gameplay.fork.default` = `nobody pulls: the train takes the safe/straight branch and loses that fork's bonus` | JB draft ran it into a buffer spur (OQ-008) | src: PLAN, JB | conflict
- `gameplay.fork.lock` = `the lever locks once the route commits; hide the lever UI when the route is locked` | bug bash spams the lever after it locks | src: R2A | canon
- `gameplay.fork.cards` = `each route gets 1-2 modifiers, rolled on the server when the junction spawns, shown on its junction card; clients only display` | a face-down "???" card is on-brand | src: R2A | canon
- `gameplay.fork.modifier_life` = `modifiers apply in lockRoute and last until the next junction; announced through the HUD` | src: R2A | canon
- `gameplay.fork.trigger` = `a JunctionTrigger part opens the junction board; the cab wheel raises and lowers the board` | src: LBJ, CI | canon
- `gameplay.fork.warning_lamp` = `junction lamp flashes from 1 mile out with a beep` | the only warning without a forward view | src: CB | proposed
- `gameplay.fork.tempting` = `each route tempting, not strictly better or worse; if one card is always better the lever stops being a choice` | src: R2A | canon

## modifiers · Fork modifiers (data, not code)
- `gameplay.modifiers.alpha_count` = `6-8` | start set for the alpha | src: R2A | canon
- `gameplay.modifiers.fields` = `name, card text, effects (miles, breakdown frequency, major boost, fare multiplier)` | EventScheduler hook can change gaps and majorBoost | src: R2A | canon
- `gameplay.modifiers.shortcut` = `Shortcut: -20 miles, more breakdowns` | src: R2A | proposed
- `gameplay.modifiers.scenic` = `Scenic: +10 miles, x1.3 fare` | src: R2A | proposed
- `gameplay.modifiers.dodgy_track` = `Dodgy track: windows break twice as often` | src: R2A | proposed
- `gameplay.modifiers.no_signal` = `No signal: HUD down` | src: R2A | proposed
- `gameplay.modifiers.express` = `Express: forced Fast` | src: R2A | proposed
- `gameplay.modifiers.easy_pool` = `Temporary Speed Restriction x1.2; Greasy Rail x1.3; Short Platform x1.3; Stiff Points x1.4` | src: RN | proposed
- `gameplay.modifiers.medium_pool` = `Tunnel Section x1.5; Ruling Gradient x1.6; Overbooked Service x1.6; Borrowed Stock x1.7` | src: RN | proposed
- `gameplay.modifiers.hard_pool` = `Viaduct Crossing x1.9; Signal Conflict x2.0; Bad Coal x2.0; Night Running x2.2` | src: RN | proposed
- `gameplay.modifiers.insane_pool` = `Frozen Line x2.6; Inspection Run x2.7; Signal Blackout x2.8; Cascade Failure x3.0` | src: RN | proposed
- `gameplay.modifiers.rules` = `one system per modifier and one modifier per system per branch; tagged for compatibility; about half change biome` | src: RN | proposed

## station · Stations and banking
- `gameplay.station.dwell_s` = `20` | relief beat; bank number goes up visibly | src: PLAN, DS | canon
- `gameplay.station.bank` = `passengers who reach a station pay fare x accumulated multipliers into the crew bank` | src: PLAN | canon
- `gameplay.station.fare_by_mood` = `fares paid at the station depend on passenger mood` | src: R2A | canon
- `gameplay.station.alpha_fare` = `miles minus a penalty per breakdown` | simple alpha formula | src: R2A | proposed
- `gameplay.station.terminate_vote` = `optional "terminate service" vote at Station B keeps everything` | src: PLAN | proposed

## supplies · Supplies and tools
- `gameplay.supplies.flow` = `order at the Depotron (ProximityPrompt E); crate parachutes onto the coach roof after a delay; someone climbs the ladder to fetch it; unfetched crates slide off` | src: R2A, CI | canon
- `gameplay.supplies.one_order` = `one order at a time; each order spawns exactly one crate` | src: R2A, CI | canon
- `gameplay.supplies.hand` = `carry one thing in hand at a time (coal, wrench, food)` | src: THS | canon
- `gameplay.supplies.tools` = `shovel (coal), wrench (fixes electricals faster), sandwich (calms/feeds), medkit, toolbox (repairs)` | tools in the hotbar, one clear job each | src: R2A, ST, PLAN | canon

## train · The train
- `gameplay.train.layout` = `locomotive cab + coach (booths, sandwich bar, power box at the coach end, roof ladder, balcony)` | src: WR, CB | measured
- `gameplay.train.keep_on` = `server checks about 5 times a second; anyone outside the train area for 1.5 s is put back in the coach for a 5-coin fee` | src: R2A | canon
- `gameplay.train.low_bridge` = `LOW BRIDGE warning about 5 s before a tunnel; anyone still on the roof is moved inside` | src: R2A | canon
- `gameplay.train.cab_controls` = `3-notch throttle, wheel (raises junction board), horn, lights, alarm, DO NOT PRESS; screens: speed, next junction (miles + about N s), fuel` | src: CB, CI | canon
- `gameplay.train.comm_cord` = `red communication cord in the coach any player can pull` | effect undecided (OQ-018) | src: WR | proposed

## results · Results and progression
- `gameplay.results.incident_report` = `breakdowns, wrong turns, coal shovelled, a joke grade and one silly award per player` | src: R2A | canon
- `gameplay.results.blame` = `Blame card names who pulled the fatal lever; MVP; share prompt; one-tap re-queue` | src: PLAN | canon
- `gameplay.results.next_goal` = `results show "next unlock in X" and tomorrow's Daily Line; big "Invite your crew" button` | src: LPB | proposed

## progress · Progression
- `gameplay.progress.ladder` = `fare > locomotives (3 at MVP, 5 at 1.0) > lines (1, then 2) > classes (1.0) > liveries (post-launch)` | src: PLAN | canon
- `gameplay.progress.first_unlock` = `second locomotive at about 2,500 fare, landing inside the first 30 minutes (about 2 runs)` | src: PLAN, LPB | proposed
- `gameplay.progress.pacing` = `a new locomotive every about 2 h through hour 10; nothing above about 15 successful runs in the 1.0 economy` | src: PLAN | proposed
- `gameplay.progress.diesel` = `diesel train is after the alpha (its own fuel system, crisis set and cab)` | TrainType field in TeleportData now | src: R2A | canon
