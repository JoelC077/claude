# World and naming

Places, names, the lobby, Line 1, biomes and segment prefabs, the gag lexicon, and banned names (enforced by `bible.py check`).

## names · Proper names
- `world.names.company` = `Risky Rails Railway Co.` | R2A masthead; Supply Terminal v4 footer says "TRASH RAILWAYS CO."; see OQ-002 | src: R2A, ST | conflict
- `world.names.depot_monitor` = `Depotron 3000` | the cab/coach order computer ("DEPOTRON 3000", "PRESS E TO OPEN_") | src: CI, R2A | canon
- `world.names.supply_depot` = `Risky Rails Supply Depot` | header on the Depotron order screen | src: CI | proposed
- `world.names.works_plate` = `RISKY RAILS No. 7` | brass works plate on the backhead | src: CB | proposed
- `world.names.lobby` = `Depot Lobby` | walk-around, static hub | src: BP, PROF | canon
- `world.names.line_1` = `Line 1` | the MVP line; lowland grassland base biome | src: RN, DS | canon
- `world.names.daily_line` = `Daily Line` | one seeded route per day for everyone, with a banked-fare leaderboard | src: PLAN | canon
- `world.names.results_screen` = `Incident Report` | results screen name (alpha UI list) | src: R2A | canon
- `world.names.blame_card` = `Blame card` | names who pulled the fatal lever | src: PLAN, LPB | canon
- `world.names.locos` = `Starter, Diesel, Electric, Bullet` | eras unlock in that order; MVP ships 3 variants of one family | src: DS, PLAN | proposed
- `world.names.stations` = `Station A, Station B, Terminus` | placeholders; real station names not chosen (OQ-016) | src: DS | assumed

## lobby · Depot Lobby layout (blueprint Rev 01; plan x right from west, y down from north, studs)
- `world.lobby.footprint` = `60 x 70` | fenced main lobby; plus depot yard 40 x 20 at (10,70) | src: BP | canon
- `world.lobby.occupancy` = `6` | "small hub, don't over-build"; numbers are a starting point | src: BP | canon
- `world.lobby.grid_studs` = `5` | one grid square = 5 studs; paving slab 5 x 5 | src: BP | canon
- `world.lobby.north` = `direction from spawn to the join-queue platform` | src: BP | canon
- `world.lobby.spawn` = `(30,60) facing north` | station/depot behind the player | src: BP | canon
- `world.lobby.central_path` = `8 x 45 at (26,15)` | cracked paving strip spawn to queue | src: BP | canon
- `world.lobby.lamps` = `(23,28) (37,28) (23,47) (37,47)` | iron railway lanterns about 19 studs apart | src: BP | canon
- `world.lobby.info_board` = `3 x 8 at (1.5,32)` | west wall; timber/iron frame, peeling notices, one vine | src: BP | canon
- `world.lobby.classes_pad` = `12 x 12 at (44,30)` | placeholder, post-launch | src: BP | canon
- `world.lobby.fence` = `palisade fence, bent-bar and vine-overgrown panels; no separate wall` | src: BP | canon
- `world.lobby.depot_building` = `24 x 14 at (18,76)` | two-gable stone station house, front faces the yard (north) | src: BP | canon
- `world.lobby.display_track` = `32 x 6 at (14,70)` | equipped train sits here; gravel ballast | src: BP | canon
- `world.lobby.clutter` = `moss, ivy, crates, drums; heaviest near the building` | src: BP | canon
- `world.lobby.queue_platform` = `20 x 10 at (20,5)` | main CTA; boldest lighting and signage | src: BP | canon
- `world.lobby.first_shift_pad` = `FIRST SHIFT - START HERE` | difficulty-1 pad by the spawn | src: R2A | canon
- `world.lobby.main_hall` = `34 x 14 at plan (13,-16), facing spawn` | not on the blueprint; mission default, owner never confirmed (OQ-015) | src: DEPM | assumed

## route · Line 1 route structure
- `world.route.forks` = `5` | per run | src: PLAN, DS | canon
- `world.route.graph` = `3-lane braid; safe branches run the middle, risky bulge out; every lane reconverges at stations` | src: PLAN, DS | canon
- `world.route.stations` = `2 intermediate + terminus` | banking at A and B; terminus is the brake check | src: PLAN, DS | canon
- `world.route.biome_rule` = `biomes change only when a fork modifier calls for it` | owner decision (D-009) | src: RN | canon
- `world.route.junction_is_transition` = `the junction prefab is the biome transition` | saves three approach prefabs | src: RN, DS | canon
- `world.route.junctions_outside_biomes` = `never start a biome if a junction is due before it would end` | the left branch swings wide and would hit tunnel walls | src: R2A | canon

## biomes · Biomes
- `world.biomes.base` = `lowland farmland / grassland` | opposite of Dead Rails' desert; buildable in parts + Terrain far layer | src: RN, GP, NB | canon
- `world.biomes.mvp_forks` = `tunnel and deep cutting; viaduct; marshalling yard` | each exists because a hazard needed a place | src: RN | canon
- `world.biomes.later` = `alpine grade (Insane home), coastal causeway, urban approach, night moorland` | held for 1.0+ | src: RN | proposed
- `world.biomes.alpha_week1` = `tunnel + bridge biome (entrance, middles, exit)` | tunnels darken client lighting; bridges get fog/haze | src: R2A | canon
- `world.biomes.segment_designs` = `Grasslands, Coastal Wetland, Arctic` | worked-up segment docs in the claude.ai project (SEGD, unreachable) | src: NB | proposed

## prefabs · Line 1 segment prefabs (18 of about 20 budgeted)
- `world.prefabs.01` = `Straight, embankment` | +6 above land, 44 crest | src: DS | canon
- `world.prefabs.02` = `Straight, cutting` | -8 below land, 60 top width; cheapest sightline break | src: DS | canon
- `world.prefabs.03` = `Gentle curve` | R about 900, 32 deg sweep; mirror for L/R | src: DS | canon
- `world.prefabs.04` = `Farm crossing` | road 34 wide; gates "temporarily" taped | src: DS | canon
- `world.prefabs.05` = `Small overbridge` | clearance 22, span 88 | src: DS | canon
- `world.prefabs.06` = `Station approach` | Temporary Speed Restriction board lives here | src: DS | canon
- `world.prefabs.07` = `Junction / fork` | gantry + points; reused for all five forks | src: DS, LBJ | canon
- `world.prefabs.08` = `Intermediate station` | platform 290, dwell 20 s; Short Platform variant derives from it | src: DS | canon
- `world.prefabs.09` = `Terminus` | buffers at 480; braking marker in the previous segment for fast locos | src: DS | canon
- `world.prefabs.10` = `Tunnel mouth` | bore 18 h x 30 w; 2 s visible portal minimum even at Bullet speed | src: DS | canon
- `world.prefabs.11` = `Tunnel interior` | 4 studs above the carriage roof: crouch survives, standing does not | src: DS | canon
- `world.prefabs.12` = `Viaduct span` | deck 70 above valley; low or absent parapet in places | src: DS | canon
- `world.prefabs.13` = `Viaduct, taped span` | the hidden hazard made physical; notice dated 2019 | src: DS | canon
- `world.prefabs.14` = `Yard entry` | 4 roads; contradictory signal aspects arm Signal Conflict | src: DS | canon
- `world.prefabs.15` = `Yard interior, sidings` | 5 roads at 40 centres; running line kept clear | src: DS | canon
- `world.prefabs.16` = `Water tower` | 62 tall landmark, once per line; best thumbnail silhouette | src: DS | canon
- `world.prefabs.17` = `Derailed wreck` | one reused carriage on its side; foreshadowing | src: DS | canon
- `world.prefabs.18` = `Signal box` | occupied, facing away; pairs with 14 | src: DS | canon
- `world.prefabs.station_end` = `end-of-line station segment with a StopMarker part` | built week 1 of the alpha plan | src: R2A | measured

## lexicon · Gags and fixed strings (use exactly)
- `world.lexicon.out_of_order` = `OUT OF ORDER, PROBABLY FOREVER` | wreck sign; comedy tell that it is not a horror train | src: LPB | proposed
- `world.lexicon.days_without` = `days without an accident: 0` | crooked cab sign (dashboard: DAYS WITHOUT AN ACCIDENT 0) | src: CB, CI | proposed
- `world.lexicon.do_not_press` = `DO NOT PRESS` | cab button that does something stupid | src: CI | proposed
- `world.lexicon.do_not_lick` = `WIRES. DO NOT LICK.` | tape label on the power box | src: CI | proposed
- `world.lexicon.hit_it` = `HIT IT IF IT FREEZES` | Depotron label | src: CI | proposed
- `world.lexicon.no_stoking` = `No smoking, no stoking` | coach notice | src: WR | proposed
- `world.lexicon.mind_gap` = `Mind the gap` | small plate at the coach step | src: WR | proposed
- `world.lexicon.retrieved` = `Retrieved by the company. 5-coin recovery fee.` | when a player is put back on the train | src: R2A | canon
- `world.lexicon.low_bridge` = `LOW BRIDGE` | warning about 5 s before a tunnel | src: R2A | canon
- `world.lexicon.fired` = `YOU'RE FIRED` | stamp on the Incident Report after a slapstick fail | src: R2A | proposed
- `world.lexicon.grades` = `Employee of the Month ... Disciplinary Hearing` | Incident Report joke grade range | src: R2A | canon
- `world.lexicon.shift_briefing` = `Shovel coal / Fix what breaks / Pick the route` | three-line briefing while waiting on the platform | src: R2A | proposed
- `world.lexicon.waiting` = `Waiting for {name} to board...` | HUD line during trip start | src: R2A | canon
- `world.lexicon.loading_coins` = `loading coins...` | lobby shows this while the save finishes, never a flash of 0 | src: R2A | canon
- `world.lexicon.coins_saved` = `your coins are saved` | friendly kick message after 3 failed teleports | src: R2A | canon
- `world.lexicon.climb_up` = `CLIMB UP! Grab it on the roof!` | supply order confirmation | src: ST | proposed
- `world.lexicon.tsr_sign` = `TEMPORARY (dated four years ago)` | Temporary Speed Restriction board gag | src: RN | proposed
- `world.lexicon.clearance_inside` = `clearance warning posted inside the tunnel, where it is useless` | src: RN | proposed

## banned · Names and phrases that must not appear (check flags these)
- `world.banned.flight_or_die` = `Flight or Die` | the real game is "Land or Die!" (Plenty of Planets) | src: PLAN | canon
- `world.banned.trash_railways` = `Trash Railways` | company name is an open question (OQ-002); do not spread it until decided | src: ST | conflict
- `world.banned.free_robux` = `free Robux` | metadata/scam bait, moderation risk | src: LPB | canon
- `world.banned.giveaway` = `giveaway` | Roblox penalises leading with giveaways in metadata | src: LPB | canon
