# Open questions

Undecided canon. Each has options and a recommended default: skills may proceed on the default when the owner is away, but must say so and mark their output "assumed (OQ-nnn default)". Only the owner decides; record it with `bible.py decide OQ-nnn <option> --by owner`. New gaps are added with `bible.py add-question`.

### OQ-001 · HUD skin: heritage brass or teal-cream/mustard livery?
- status: open
- raised: 2026-09-27
- src: HUDM, RUB, THS, TN
- context: The HUD remake went heritage brass (soot-iron frame, brass pinline and rivets, aged card, rubber-stamp values; self-assessed 8/10). The brand formula and critic house style say hazard yellow/black against teal-cream or mustard livery. The in-world trim is brass/charcoal/cream. Not decided: owner's call.
- options:
  - A: Heritage brass HUD as remade (ui.hud_remake tokens).
  - B: Teal-cream/mustard livery HUD (prototype kind colours, brand teal and mustard, hazard stripes).
  - C: Hybrid: frame and chrome from the in-world trim (brass, charcoal, cream) so HUD and cab read as one company; kind stubs in brand colours (red crisis, hazard risk, teal crew, mustard or green cash).
- default: C, then one independent critic pass on A vs C boards side by side before the owner picks
- affects: ui.hud.skin, style.brand.mustard, style.brand.livery_teal_sheet
- blocks: final HUD export, rr-ui-foundry tokens

### OQ-002 · Company name
- status: open
- raised: 2026-09-24
- src: R2A, ST
- context: The timetable masthead says "RISKY RAILS RAILWAY CO."; the Supply Terminal v4 footer says "TRASH RAILWAYS CO."; props say "RISKY RAILS No. 7" and "RISKY RAILS SUPPLY DEPOT".
- options:
  - A: Risky Rails Railway Co. everywhere.
  - B: Trash Railways Co. as the company (self-deprecating).
  - C: Official name Risky Rails Railway Co.; "Trash Railways" only as scrawled graffiti on company signs.
- default: A (matches the title, works plate and depot signage; searchable)
- affects: world.names.company, world.banned.trash_railways
- blocks: signage, terminal footer, store copy

### OQ-003 · Currency: coins, "$" or fare?
- status: open
- raised: 2026-09-25
- src: R2A, TN, ST, PLAN
- context: The plan says fare; the timetable and save data say coins; the HUD shows "FARE BANKED! $120" and the terminal shows "$".
- options:
  - A: Coins everywhere with a coin icon; no "$".
  - B: Cash "$" everywhere.
  - C: Data name Coins, player-facing "$" as already built; "fare" is the in-run event (FARE BANKED).
- default: C (zero rework; one currency)
- affects: economy.currency.name, gameplay.alerts.fare_banked
- blocks: UI copy, economy tables

### OQ-004 · Trip length per difficulty
- status: open
- raised: 2026-09-18
- src: CB, DS
- context: Cab build: base 250 miles +25% of base per step (250, 312.5, 375, 437.5). Drawing Set: 300, 375, 469, 586 (compounding). At Normal (0.35 mi/s) 250 miles is 11.9 min, matching the measured 12-minute trip.
- options:
  - A: 250 / 312.5 / 375 / 437.5 (linear).
  - B: 300 / 375 / 469 / 586 (compounding).
  - C: Set from playtest data after the alpha.
- default: A until alpha data says otherwise
- affects: gameplay.difficulty.trip_miles
- blocks: segment counts per run, fuel economy

### OQ-005 · Studs per game-mile
- status: open
- raised: 2026-09-25
- src: R2A, CB, DS, NB
- context: The Dimension System doc sets 1 mile = 160 studs; the build uses Miles = distance / 100 and Speed/100 = mi/s. Segment (512) and pole (128) sizes are in studs and are unaffected.
- options:
  - A: 100 studs per mile (as built); update the Dimension System and loco table.
  - B: 160 studs per mile; rescale Speed values and the miles counter.
- default: A
- affects: gameplay.speed.studs_per_mile, gameplay.speed.loco_table
- blocks: loco speed table, run length maths

### OQ-006 · Who may pull the lever?
- status: open
- raised: 2026-09-10
- src: RN, DS, JB
- context: If anyone can, a stranger can yank it against four others; the plan calls the argument the feature. A UI vote is ruled out (D-004).
- options:
  - A: Anyone, no confirm; the first committed pull locks the route.
  - B: Driver only (a role).
  - C: Anyone, with a short hold-to-commit.
- default: A (matches the lever panel and lock rule); watch for griefing in public servers
- affects: gameplay.fork.lever, gameplay.fork.lock
- blocks: junction logic, lever UI

### OQ-007 · When does the crew learn what is on each branch?
- status: open
- raised: 2026-09-10
- src: RN, DS, R2A
- context: This timing decides whether the fork reads as a decision or a gamble.
- options:
  - A: When the junction board opens at the JunctionTrigger: route cards with 1-2 modifiers, a face-down "???" allowed.
  - B: Earlier, via the cab map / next-junction screen.
  - C: Only during the gantry countdown.
- default: A, and prototype B in the grey-box
- affects: gameplay.fork.cards, gameplay.fork.trigger
- blocks: junction cards UI

### OQ-008 · What happens when nobody pulls?
- status: open
- raised: 2026-09-10
- src: PLAN, RN, JB, LBJ
- context: The plan defaults to the safe branch and loses the bonus; the Rev A blueprint ran the default onto a derelict spur into a buffer; Rev B has only straight and left.
- options:
  - A: Straight/safe branch; lose only that fork's bonus.
  - B: Straight/safe branch; lose the whole stacked multiplier.
  - C: Derelict spur into the buffer (a fail).
- default: A; revisit B if Signal Blackout ships
- affects: gameplay.fork.default
- blocks: junction logic

### OQ-009 · Throttle authority
- status: open
- raised: 2026-09-10
- src: RN
- context: Speed is player-adjustable at a fuel and pressure cost; open throttle is a second argument generator.
- options:
  - A: Anyone can change the notch.
  - B: Driver only.
- default: A for the alpha; revisit from playtests
- affects: gameplay.train.cab_controls
- blocks: none

### OQ-010 · Robux in the supply terminal
- status: open
- raised: 2026-09-24
- src: ST, PLAN
- context: The terminal has a USE ROBUX option (Always / Only when short / Hidden) with placeholder prices. Buying coal or tools mid-crisis with Robux sits close to selling survival odds (D-007).
- options:
  - A: Hidden: coins only.
  - B: Only when short.
  - C: Always.
- default: A for the alpha; any Robux product passes the mechanic reviewer and D-007 first
- affects: economy.supplies.robux_option
- blocks: release gate for monetisation

### OQ-011 · Does a failed trip pay anything?
- status: open
- raised: 2026-09-25
- src: R2A, PLAN
- context: The owner's own open item in the timetable. The banked-fare pillar says a crash keeps what was banked.
- options:
  - A: Pays the banked fare.
  - B: Pays nothing.
  - C: Pays the banked fare minus a penalty.
- default: A (it is a pillar)
- affects: economy.currency.failed_trip
- blocks: save-data award logic

### OQ-012 · HUD alert IDs: per fault or generic BREAKDOWN?
- status: open
- raised: 2026-09-25
- src: R2A, TN
- context: The timetable keys alerts by ID with counts ("WINDOW BROKEN x4") and clears by ID; the prototype has one generic "BREAKDOWN! / Grab a wrench and fix it!". Per-fault texts do not exist yet.
- options:
  - A: Per-fault IDs (WindowBroken, ElectricsDown, ...) with new texts the owner approves.
  - B: Generic BREAKDOWN only.
  - C: Per-fault IDs sharing the BREAKDOWN! title, fault named in the body.
- default: A, with proposed texts marked proposed until approved
- affects: gameplay.alerts.breakdown
- blocks: HUD type table

### OQ-013 · Boiler pressure numbers (missing canon)
- status: open
- raised: 2026-09-28
- src: PLAN, WR, CB
- context: Pressure follows fire level and gradient, redline explodes, low pressure stalls, pressure drives Speed; no gauge range, redline, rise or vent rates exist in reach. A balance sheet (risky_rails_speed_balance.xlsx) exists only in an old chat.
- options:
  - A: Tune in Studio from the coal numbers and record the result with add-fact.
  - B: Recover the balance spreadsheet and import it.
- default: A
- affects: gameplay.crisis.pressure
- blocks: gauge UI, pressure crisis tuning

### OQ-014 · Who does the medkit heal?
- status: open
- raised: 2026-09-24
- src: ST, PLAN
- context: The plan treats critical passengers with a medkit; the terminal copy says "Heals one hurt crew member". Crew health is not one of the four systems (a 5th-system risk).
- options:
  - A: Passengers (fix the terminal copy).
  - B: Crew (adds crew health).
- default: A
- affects: economy.supplies.medkit
- blocks: terminal copy, passenger system

### OQ-015 · Main Hall: where, and does it stay?
- status: open
- raised: 2026-09-27
- src: DEPM, BP
- context: The owner asked for "the main hall" but the blueprint names only the depot. The mission placed a 34 x 14 hall north of the join-queue platform facing spawn (assumed, never confirmed).
- options:
  - A: Keep the mission placement.
  - B: No main hall (blueprint: small hub, don't over-build).
  - C: Owner places it.
- default: A until the owner says otherwise
- affects: world.lobby.main_hall, assets.missions.main_hall
- blocks: lobby dressing

### OQ-016 · Station, depot and signage names
- status: open
- raised: 2026-09-27
- src: DEPM, DS
- context: Station A/B and the terminus are placeholders; the depot name board and roundel were left blank to avoid invented text.
- options:
  - A: The owner names them.
  - B: Propose three name sets in the house voice for the owner to pick.
- default: B (proposals marked proposed until picked)
- affects: world.names.stations
- blocks: signage text

### OQ-017 · Lobby and menu accent
- status: open
- raised: 2026-09-08
- src: DTU
- context: Depends on OQ-001. The Create match panel was drawn with one accent in two reads, teal #1FAE8E or brass #D69A2D; the critic dry test assumed teal.
- options:
  - A: Teal.
  - B: Brass.
  - C: Follow the OQ-001 outcome so HUD and menus share one accent family.
- default: C
- affects: ui.lobby.accent_teal, ui.lobby.accent_brass
- blocks: lobby UI

### OQ-018 · What does the communication cord do?
- status: open
- raised: 2026-09-22
- src: WR
- options:
  - A: Emergency stop that costs time.
  - B: Prank that summons the guard.
  - C: Cut it.
- default: A
- affects: gameplay.train.comm_cord
- blocks: coach props

### OQ-019 · Marketing budget split
- status: open
- raised: 2026-09-13
- src: LPB, MDP
- context: LPB (newer, gate-aware) says never pay creators; MDP puts 80 of 300 on creators.
- options:
  - A: LPB: 60 art, 20 measurement, 60-75 engagement ads, 60 plays ads, 40 lapsed re-activation, 40-60 reserve.
  - B: MDP: 100 ads, 80 creators, 50 creative, 70 contingency.
- default: A
- affects: economy.budget.allocation
- blocks: release-train spend plan

### OQ-020 · Missing canon: project docs and the approved diesel
- status: open
- raised: 2026-09-28
- src: NB, RUB, WR
- context: The claude.ai project docs (Visual Identity, Dimension System, Segment Designs, Full Project Summary) and the approved diesel "23" are not reachable from a cloud session; the bible marks those domains partial.
- options:
  - A: The owner pastes or publishes them once; a session imports them with add-fact and lint.
  - B: Leave as is.
- default: A
- affects: assets.approved.diesel_23, identity.tone.company
- blocks: full style canon (materials, fence, depot dressing checklist)

### OQ-021 · Audio identity (missing canon)
- status: open
- raised: 2026-09-28
- src: R2A, PLAN
- context: Only priorities exist (alarms first, slapstick through sound, client pool). No music, stinger or per-crisis alarm design.
- options:
  - A: Diegetic only for the alpha (whistle, hiss, wheels, alarms), no music during runs.
  - B: A light music bed in runs.
  - C: Decide after the alpha.
- default: A
- affects: av.audio.pack
- blocks: rr-soundsmith

### OQ-022 · How do the coach doors open?
- status: open
- raised: 2026-09-22
- src: WR
- context: Doors v3 are delivered but solid, so the coach is unreachable from the balcony.
- options:
  - A: Open automatically when a player walks up.
  - B: Swing on click (like the power box door).
  - C: No collision; walk straight through.
- default: A (phone-friendly, no new verb)
- affects: assets.train.coach_doors_v3
- blocks: coach access

### OQ-023 · Ratify the shared in-world trim palette
- status: open
- raised: 2026-09-22
- src: WR, CB
- context: The Works Report proposed one trim set for all rolling stock (charcoal #363A42, brass #C9953A, cream #EBDDBE, navy #1B2A3B, hazard #E8AC22, walnut #7A4A26, diamond plate #8A8D98). The cab guide used #EDE3C8 for tape labels and #E8B021 for hazard.
- options:
  - A: Ratify the WR set as canon (tape labels move to #EBDDBE).
  - B: Adjust values, then ratify.
- default: A
- affects: style.world.ironwork, style.world.brass, style.world.cream, style.world.hazard, style.world.walnut, style.world.diamond_plate, style.cab.tape_label
- blocks: rr-asset-foundry palette atlas

### OQ-024 · Launch player cap
- status: open
- raised: 2026-09-13
- src: LPB, PLAN
- context: Servers hold 6; the playbook recommends capping at 4 for the first launch fortnight so servers fill.
- options:
  - A: 4 for the first fortnight, then 6.
  - B: 6 from day one.
- default: A
- affects: gameplay.crew.launch_cap
- blocks: release-train launch checklist

### OQ-025 · Train exterior livery: the coach is green in Studio, but no hex is recorded
- status: open
- raised: 2026-09-28
- src: WR, THS, RUB
- context: The Works Report calls the train navy cab, cream coach and green exterior and suggests a waist band, coach number and roundel; the brand formula and critic house style expect teal-cream or mustard livery with red buffer beams. The loco exterior was not in reach.
- options:
  - A: Measure the as-built exterior colours in Studio and record them
  - B: Repaint to the brand livery (teal #2F8F86, cream band #EFE4C8, hazard yellow, red buffer beams)
  - C: Decide together with OQ-001 so HUD, livery and thumbnails share one family
- default: A (record what exists first; no repaint without the owner)
- affects: style.brand.teal, style.brand.cream
- blocks: rr-asset-foundry train exteriors, thumbnails that show the real train

### OQ-026 · Time of day and when the lighting look changes
- status: open
- raised: 2026-09-28
- src: VFXL, RN, R2A
- context: No canon for time of day. Canon has a lowland grassland base biome, fork-driven biome changes (D-009), tunnels darkening client lighting and a Night Running hard modifier. rr-vfx-lighting ships day, golden, night and storm looks per biome.
- options:
  - A: One fixed day look for the whole trip; only the tunnel darkening changes it
  - B: A slow day-to-dusk cycle across the 12-minute trip
  - C: Day by default; the look changes only with the biome or a fork modifier (Night Running = night look, a weather modifier = storm look); golden kept for the Depot lobby and results
- default: C (follows D-009: nothing changes unless a fork says so; each look stays readable because it is authored, not interpolated)
- affects: world.biomes.base, gameplay.modifiers.hard_pool
- blocks: rr-vfx-lighting look assignment per branch

### OQ-027 · Is there weather (rain)?
- status: open
- raised: 2026-09-28
- src: VFXL, RN
- context: No canon mentions weather. rr-vfx-lighting ships a rain preset and a storm look because they were requested; neither is wired to any mechanic.
- options:
  - A: No weather for the alpha; the rain preset and storm look stay shelved
  - B: Rain as a visual-only fork modifier look
  - C: Rain as a gameplay modifier (for example wet rails) with its look
- default: A (alpha is steam-only and week 2 is full; the presets cost nothing until used)
- blocks: rain preset and storm look use

### OQ-028 · Derailment: breakdown task or explosion?
- status: open
- raised: 2026-09-28
- src: VFXL, PLAN, R2A
- context: Canon lists derailed bogie as a breakdown (a spatial task) and the only explosion as the boiler hard fail (av.vfx.boiler_fail). A derail explosion was requested for rr-vfx-lighting.
- options:
  - A: Derailment stays a breakdown task with sparks, dust and a jolt; only the boiler explodes
  - B: Add a derailment hard fail with a slapstick explosion and its own 3-second clip moment
- default: A (keeps the four crisis systems and fail list as decided; the derail_explosion preset ships unassigned)
- affects: gameplay.crisis.breakdowns, gameplay.crisis.fail_states, av.vfx.boiler_fail
- blocks: derail_explosion preset use

### OQ-029 · Phone budget for effects and lighting
- status: open
- raised: 2026-09-28
- src: VFXL, R2A, RBXD
- context: No canon budget for particles, lights or post effects, though most players are on phones (identity.audience.devices). rr-vfx-lighting presets/budgets.json holds a default: phone about 400 live particles steady, 800 peak for 2 s, 12 emitters, 2 shadowed lights, 8 lights in view, Bloom and SunRays off; crisis-signal effects keep full rate, ambience drops to half.
- options:
  - A: Adopt the rr-vfx-lighting default budget now
  - B: Measure first on the owner's phone during the alpha live check, then set numbers
- default: A (usable now; revisit with B's numbers at the live check)
- affects: identity.audience.devices, tech.lighting.post_low_quality
- blocks: none (defaults used)
