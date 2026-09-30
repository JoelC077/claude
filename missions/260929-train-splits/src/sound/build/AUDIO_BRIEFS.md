# Risky Rails audio briefs (rr-soundsmith)

Generated 2026-09-29 from soundmap.json and canon; 36 sounds in phase order; format in references/brief-format.md. Edit the soundmap, not this file.

- **Licence** (av.audio.licence): only owner-uploaded audio (self-made, commissioned, CC0 or bought with a game licence, proof recorded) or Roblox-licensed Creator Store audio (by Roblox or its partners). Record proof with `sound.py register`. Uploaded audio stays private to the game: never distribute it on the Creator Store.
- **Tone** (identity.tone): an incompetent train company: under-resourced but still operating; slapstick safety failures, not grim horror; not a western, not zombies, not horror, not a train simulator.
- **Delivery:** dry (no reverb baked in), WAV 48 or 44.1 kHz, 16 or 24-bit; mono for anything positional.
- **Meter:** levels are ITU BS.1770 with mono counted as dual mono (+3 dB, as heard on two speakers). On a meter that reads mono as one channel, aim 3 dB lower (m_max -14 reads -17 there).
- **Done when:** `sound.py analyze <file> --as <id>` shows no FAIL, then register and build.
- **Route:** store = Roblox-licensed Creator Store search using Sounds like; self-made = record or perform it; commission = a sound designer with a written rights grant.

| phase | id | tier | class | takes | length s | space | state | route |
|---|---|---|---|---|---|---|---|---|
| lobby | guard_whistle | 4 | oneshot | 1 | 0.6-1.2 | 2d | unassigned | store / self-made |
| lobby | queue_punch | 4 | oneshot | 2 | 0.15-0.4 | 2d | unassigned | store / self-made |
| lobby | queue_bell | 5 | ui | 1 | 0.2-0.55 | 2d | unassigned | store / self-made |
| lobby | lobby_bed | 6 | loop | 1 | 8.0-20.0 | 2d | unassigned | self-made loop / store |
| depart | whistle | 4 | oneshot | 1 | 1.2-2.2 | 2d | unassigned | store / self-made |
| depart | firebox_loop | 6 | loop | 1 | 4.0-12.0 | 3d @firebox | unassigned | self-made loop / store |
| depart | wheels_loop | 6 | loop | 1 | 4.0-12.0 | 2d | unassigned | self-made loop / store |
| depart | wind_bed | 6 | loop | 1 | 6.0-20.0 | 2d | unassigned | self-made loop / store |
| run | crate_thump | 4 | oneshot | 2 | 0.4-0.8 | 3d @roof | unassigned | store / self-made |
| fork | countdown_tick | 3 | oneshot | 1 | 0.08-0.2 | 2d | unassigned | store / self-made |
| fork | junction_beep | 3 | oneshot | 1 | 0.3-0.6 | 2d | unassigned | store / self-made |
| fork | lever_clunk | 3 | oneshot | 3 | 0.35-0.6 | 3d @lever | unassigned | store / self-made |
| fork | stamp_slam | 3 | oneshot | 2 | 0.2-0.4 | 2d | unassigned | store / self-made |
| fork | points_throw | 4 | oneshot | 1 | 0.35-0.6 | 2d | unassigned | store / self-made |
| crisis | boiler_boom | 1 | impact | 1 | 2.0-3.5 | 2d | unassigned | commission / self-made (distinct) |
| crisis | alarm_coal | 2 | alarm | 1 | 1.2-2.0 | 2d +3d | unassigned | commission / self-made (distinct) |
| crisis | alarm_pressure | 2 | alarm | 1 | 1.2-2.0 | 2d +3d | unassigned | commission / self-made (distinct) |
| crisis | breakdown_bang | 2 | alarm | 2 | 1.0-1.8 | 2d +3d | unassigned | commission / self-made (distinct) |
| crisis | coupling_snap | 2 | impact | 1 | 0.9-1.5 | 2d +3d | unassigned | store / self-made |
| crisis | glass_smash | 2 | impact | 3 | 0.8-1.4 | 3d @coach | unassigned | store / self-made |
| crisis | passengers_scream | 2 | alarm | 2 | 1.0-1.8 | 2d +3d | unassigned | commission / self-made (distinct) |
| crisis | split_explosion | 2 | impact | 1 | 2.0-2.4 | 2d +3d | unassigned | store / self-made |
| crisis | metal_tear | 3 | impact | 1 | 0.8-1.3 | 3d @break | unassigned | store / self-made |
| crisis | split_glass | 3 | impact | 1 | 0.6-0.9 | 3d @break | unassigned | store / self-made |
| crisis | topple_crash | 3 | impact | 1 | 1.0-1.8 | 3d @wreck | unassigned | store / self-made |
| crisis | debris_rain | 4 | impact | 1 | 1.2-2.2 | 3d @break | unassigned | store / self-made |
| crisis | shovel_thud | 4 | oneshot | 3 | 0.4-0.8 | 3d @firebox | unassigned | store / self-made |
| crisis | topple_crash_2 | 4 | impact | 1 | 1.0-1.8 | 3d @wreck | unassigned | store / self-made |
| crisis | wreck_scrape | 4 | impact | 1 | 2.6-3.2 | 3d @wreck | unassigned | store / self-made |
| crisis | wrench_clank | 4 | oneshot | 2 | 0.5-1.0 | 3d @powerbox | unassigned | store / self-made |
| arrive | brake_hiss | 4 | oneshot | 1 | 1.0-2.0 | 2d | unassigned | store / self-made |
| arrive | cash_register | 4 | oneshot | 1 | 0.6-1.2 | 2d | unassigned | store / self-made |
| arrive | radio_loop | 7 | music | 1 | 8.0-30.0 | 3d @cab | unassigned | self-made loop / store |
| any | horn | 4 | oneshot | 1 | 0.5-1.0 | 3d @cab | unassigned | store / self-made |
| any | ticket_chime | 5 | ui | 1 | 0.2-0.5 | 2d | unassigned | store / self-made |
| any | ui_click | 5 | ui | 2 | 0.03-0.1 | 2d | unassigned | store / self-made |

## guard_whistle · lobby · tier 4 · Actions · oneshot · unassigned

- **Moment:** the queue pad launches (Launching lock on, teleport starts). Events: queue_launch (Sound.event).
- **Must say:** all aboard: we're going
- **Sounds like:** a guard's pea whistle, one long trilled blast, friendlier than a referee
- **Layers:** pea whistle 2.5-3.2 kHz with a 25-35 Hz trill; breath onset
- **Length:** 0.6-1.2 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 1
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -15 LUFS in game (ladder t4).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** the steam whistle chord (departure owns it), referee triple blasts, police whistles.
- **Canon:** `tech.data.launching_lock`: a Launching lock on the pad during teleport; a failed teleport puts the player back on the pad · `world.lobby.queue_platform`: 20 x 10 at (20,5)

## queue_punch · lobby · tier 4 · Actions · oneshot · unassigned

- **Moment:** a player steps onto a queue pad (pitched down when they step off). Events: queue_join (Sound.event), queue_leave (Sound.event).
- **Must say:** you're on the crew for this train
- **Sounds like:** a conductor's ticket punch biting card, chk-chk, with a small brass click
- **Layers:** two punch bites 70 ms apart; card snap 1-3 kHz; brass click
- **Length:** 0.15-0.4 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 2 (runtime pitch spread 0.96-1.04)
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -15 LUFS in game (ladder t4).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** cash sounds (the till owns money), UI blips, stapler.
- **Canon:** `world.lobby.queue_platform`: 20 x 10 at (20,5) · `gameplay.run.queue_countdown_s`: 15

## queue_bell · lobby · tier 5 · UI · ui · unassigned

- **Moment:** each of the last 5 s of the queue-pad countdown (the runtime raises pitch 4% per step). Events: queue_countdown_tick (Sound.event).
- **Must say:** this train leaves soon: get on the pad
- **Sounds like:** a station platform hand-bell, one ding per second
- **Layers:** hand-bell strike 1.2-2.5 kHz; ring damped under 0.5 s
- **Length:** 0.2-0.55 s; sound starts within 5 ms, tail silence under 150 ms
- **Variations:** 1
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** ui standard m_max -20 LUFS, at most -1 dBTP; the mix sets -19 LUFS in game (ladder t5).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** the fork countdown tick (the loudest countdown belongs to the lever), school bells, alarm clocks.
- **Canon:** `gameplay.run.queue_countdown_s`: 15 · `world.lobby.queue_platform`: 20 x 10 at (20,5)

## lobby_bed · lobby · tier 6 · Ambient · loop · unassigned

- **Moment:** while a player is in the Depot Lobby (lobby place; stops before the teleport). Events: lobby_enter (Sound.event), lobby_leave (Sound.event).
- **Must say:** a sleepy, run-down depot where our train is waiting
- **Sounds like:** a resting steam loco breathing slow puffs, an iron lantern buzzing, a few distant birds and a creaking sign
- **Layers:** slow steam breaths every 3-4 s; idle rumble 40-200 Hz; lantern buzz 100/200 Hz; sparse birds 2-5 kHz
- **Length:** 8.0-20.0 s; seamless loop, no fade in or out
- **Variations:** 1
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** loop standard integrated -20 LUFS, at most -1 dBTP; the mix sets -27 LUFS in game (ladder ambient).
- **Phones:** loses at most 8 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** music (open question lobby-audio, default A: no music), crowd walla, city traffic, night crickets or wind howl (horror-adjacent).
- **Canon:** `world.names.lobby`: Depot Lobby · `world.lobby.display_track`: 32 x 6 at (14,70) · `world.lobby.lamps`: (23,28) (37,28) (23,47) (37,47) · `identity.tone.company`: an incompetent train company: under-resourced but still operating; slapstick safety failures, not grim horror
- **Open:** OQ-044 (Lobby audio: music bed or diegetic depot ambience?) default A: diegetic Depot Lobby bed only (resting loco breathing, lamp buzz, birds), no music, lik

## whistle · depart · tier 4 · Actions · oneshot · unassigned

- **Moment:** the whistle before departure; the world starts to scroll. Events: depart.
- **Must say:** we're off: cheerful, big, steam
- **Sounds like:** a three-chime steam whistle, bright chord with breathy steam
- **Layers:** three-note chord; steam breath noise; slight scoop up at the start
- **Length:** 1.2-2.2 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 1
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -15 LUFS in game (ladder t4).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** diesel horns (alpha is steam only), ship horns.
- **Canon:** `av.audio.depart`: whistle before departure · `gameplay.run.depart`: whistle, then ramp to Normal over about 5 s · `av.audio.pack`: whistle, hiss, wheels, alarms

## firebox_loop · depart · tier 6 · Ambient · loop · unassigned

- **Moment:** all trip, near the firebox. Events: trip_start (Sound.event), trip_end (Sound.event).
- **Must say:** the fire is alive (the cab has a heartbeat)
- **Sounds like:** a steady fire roar with small crackles
- **Layers:** low roar; crackles
- **Length:** 4.0-12.0 s; seamless loop, no fade in or out
- **Variations:** 1
- **Space:** 3D at the firebox (firebox door in the cab); deliver mono.
- **Level:** loop standard integrated -20 LUFS, at most -1 dBTP; the mix sets -27 LUFS in game (ladder ambient).
- **Phones:** loses at most 8 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** campfire-at-night mood.
- **Canon:** `gameplay.crisis.firebox`: shovel coal from the bins into the firebox; fire drives pressure · `av.vfx.firebox_glow`: three orange Neon strips behind the firebox door (#FF9A3C, #FF7A22, #FF5A14); flicker by script later

## wheels_loop · depart · tier 6 · Ambient · loop · unassigned

- **Moment:** all trip while Speed > 0 (rate and level follow Speed). Events: trip_start (Sound.event), trip_end (Sound.event).
- **Must say:** we're moving, and how fast
- **Sounds like:** clickety-clack rail joints over a rolling rumble, recorded at the Normal notch
- **Layers:** rail-joint double clacks; rolling rumble 40-300 Hz; faint rail sing
- **Length:** 4.0-12.0 s; seamless loop, no fade in or out
- **Variations:** 1
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** loop standard integrated -20 LUFS, at most -1 dBTP; the mix sets -27 LUFS in game (ladder ambient).
- **Phones:** loses at most 8 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** modern welded-rail hum, squeals.
- **Canon:** `av.audio.speed_link`: wheel sound follows Speed · `av.audio.pack`: whistle, hiss, wheels, alarms · `gameplay.speed.drives`: Speed drives scenery velocity, camera shake, wheel sound and steam particle rate

## wind_bed · depart · tier 6 · Ambient · loop · unassigned

- **Moment:** all trip outdoors (Line 1 grassland). Events: trip_start (Sound.event), trip_end (Sound.event).
- **Must say:** open country going by
- **Sounds like:** light wind with gentle gusts
- **Layers:** wind; slow gusts
- **Length:** 6.0-20.0 s; seamless loop, no fade in or out
- **Variations:** 1
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** loop standard integrated -20 LUFS, at most -1 dBTP; the mix sets -27 LUFS in game (ladder ambient).
- **Phones:** loses at most 8 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** storms, howling.
- **Canon:** `world.biomes.base`: lowland farmland / grassland

## crate_thump · run · tier 4 · Actions · oneshot · unassigned

- **Moment:** the supply crate lands on the coach roof. Events: alert_crate_landed.
- **Must say:** your crate is up there, go get it
- **Sounds like:** a wooden crate dropping onto a metal roof, with a short creak
- **Layers:** wood thump; roof boom; creak
- **Length:** 0.4-0.8 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 2 (runtime pitch spread 0.95-1.05)
- **Space:** 3D at the roof (coach roof where crates land); deliver mono.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -15 LUFS in game (ladder t4).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** explosions.
- **Canon:** `gameplay.alerts.crate_landed`: CRATE LANDED! / Grab it before it slides off! · `gameplay.supplies.flow`: order at the Depotron (ProximityPrompt E); crate parachutes onto the coach roof after a delay; someone climbs the ladder to fetch it; unfetched crates slide off

## countdown_tick · fork · tier 3 · Actions · oneshot · unassigned

- **Moment:** each of the last 3 seconds of the lever countdown (the runtime raises pitch 6% per step). Events: fork_countdown_tick.
- **Must say:** decide now: the loudest countdown in the game
- **Sounds like:** a big wooden clock tick crossed with a signal-box bell tap
- **Layers:** wood-block knock with a bright 2-3 kHz edge
- **Length:** 0.08-0.2 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 1
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -13 LUFS in game (ladder t3).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** bomb-timer beeps, sci-fi blips.
- **Canon:** `av.feel.fork_loudest`: the fork carries the loudest countdown in the game · `gameplay.fork.lever`: a physical lever pulled left or right under a gantry countdown; the cab map/screens show the branches

## junction_beep · fork · tier 3 · Actions · oneshot · unassigned

- **Moment:** JUNCTION AHEAD! ticket lands; the junction lamp starts flashing. Events: alert_junction_ahead.
- **Must say:** a fork is coming, get to the lever
- **Sounds like:** two crisp signal beeps, like a level-crossing warning
- **Layers:** two 1 kHz square-ish beeps
- **Length:** 0.3-0.6 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 1
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -13 LUFS in game (ladder t3).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** anything alarm-like; this is information, not danger.
- **Canon:** `av.audio.junction_beep`: beep with the junction warning lamp from 1 mile out · `gameplay.alerts.junction_ahead`: JUNCTION AHEAD! / Safe or risky? Pull it!

## lever_clunk · fork · tier 3 · Actions · oneshot · unassigned

- **Moment:** the puller's knob passes the detent; the bet is locked (lands with the hit-stop). Events: lever_commit (lands with a 70 ms hit-stop at 0 ms).
- **Must say:** heavy, final, mechanical: no going back
- **Sounds like:** an iron lever dropping into a notch; a big latch; a pinball flipper's thunk
- **Layers:** click transient under 10 ms; body thunk 80-200 Hz; short metal ring
- **Length:** 0.35-0.6 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 3 (runtime pitch spread 0.96-1.04)
- **Space:** 3D at the lever (the junction lever handle (cab or gantry)); deliver mono.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -13 LUFS in game (ladder t3).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** gunshots, long reverb, UI-like clicks.
- **Canon:** `gameplay.fork.lever`: a physical lever pulled left or right under a gantry countdown; the cab map/screens show the branches · `identity.pillars.fork_bet`: every junction is a physical lever bet: safe branch or risky branch with stacking multipliers and a hidden hazard · `identity.pillars.physical_loud`: interactions are physical and visible (lever, shovel, wrench), never a quiet menu or vote
- **Open:** OQ-031 (Lever input: how does a player pull the lever?) default A: walk up to the lever; a ProximityPrompt opens the lever console; drag the knob past the

## stamp_slam · fork · tier 3 · Actions · oneshot · unassigned

- **Moment:** RISKY ROUTE! stamp and the YOU'RE FIRED stamp land. Events: alert_risky_route, fired_stamp (lands with a 60 ms hit-stop at 0 ms).
- **Must say:** official, comic, final: a rubber stamp hitting a desk
- **Sounds like:** a rubber stamp slammed on paper on a wooden desk
- **Layers:** low thump; paper slap
- **Length:** 0.2-0.4 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 2 (runtime pitch spread 0.95-1.05)
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -13 LUFS in game (ladder t3).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** gavel or gunshot.
- **Canon:** `gameplay.alerts.risky_route`: RISKY ROUTE! / Multiplier up / X2 · `av.vfx.boiler_fail`: boiler bursts, then a YOU'RE FIRED stamp on the Incident Report

## points_throw · fork · tier 4 · Actions · oneshot · unassigned

- **Moment:** the crew (not the puller) hears the route lock. Events: lever_commit_crew.
- **Must say:** the points just moved: the bet is placed
- **Sounds like:** distant railway points clacking over, two heavy clacks
- **Layers:** two metal clacks 90 ms apart; low thud
- **Length:** 0.35-0.6 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 1 (runtime pitch spread 0.97-1.03)
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -15 LUFS in game (ladder t4).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** sounding like the lever clunk itself.
- **Canon:** `gameplay.fork.lock`: the lever locks once the route commits; hide the lever UI when the route is locked

## boiler_boom · crisis · tier 1 · Alarms · impact · unassigned

- **Moment:** the boiler explodes (hard fail); the YOU'RE FIRED stamp follows. Events: boiler_burst (lands with a 120 ms hit-stop at 0 ms).
- **Must say:** total, cartoon disaster: huge but funny, never grim
- **Sounds like:** a big cartoon kaboom, then clattering debris and one last pan-like clang
- **Layers:** low boom 30-80 Hz with a mid crack; debris clatter; a final comic clang
- **Length:** 2.0-3.5 s; sound starts within 10 ms, tail silence under 500 ms
- **Variations:** 1 (runtime pitch spread 0.98-1.02)
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** impact standard m_max -14 LUFS, at most -1 dBTP; the mix sets -9 LUFS in game (ladder t1).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** war or horror explosions, screams, long ringing tinnitus.
- **Canon:** `gameplay.crisis.fail_states`: boiler explosion (hard), all passengers dead (hard), stall (soft), terminus buffer overrun (fail) · `av.vfx.boiler_fail`: boiler bursts, then a YOU'RE FIRED stamp on the Incident Report · `identity.pillars.funny_failure`: failure is funny and chaotic, never punishing or arbitrary

## alarm_coal · crisis · tier 2 · Alarms · alarm · unassigned

- **Moment:** COAL LOW! ticket lands. Events: alert_coal_low.
- **Must say:** the fire is dying, go shovel: a sad, droopy call you learn in one trip
- **Sounds like:** a two-note descending brass wah-wah, like a deflating trombone on a klaxon
- **Layers:** two descending tones 350-500 Hz with strong 1-3 kHz harmonics; slight pitch droop
- **Length:** 1.2-2.0 s; sound starts within 15 ms, tail silence under 300 ms
- **Variations:** 1
- **Space:** 2D (global: same level everywhere), plus a positional layer at the firebox (OQ-035 default); deliver mono.
- **Level:** alarm standard m_max -14 LUFS, at most -1 dBTP; the mix sets -11 LUFS in game (ladder t2).
- **Phones:** loses at most 4.5 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** sirens (pressure owns the rising siren), horror stings.
- **Canon:** `av.audio.priority`: crisis alarms first: in a group they tell someone in the other carriage what is wrong · `gameplay.alerts.coal_low`: COAL LOW! / Shovel coal in the firebox! · `gameplay.crisis.firebox`: shovel coal from the bins into the firebox; fire drives pressure
- **Open:** OQ-035 (Crisis alarms: heard train-wide or at the source?) default A: 2D train-wide at full level plus a quieter positional layer at the source (boiler, powe

## alarm_pressure · crisis · tier 2 · Alarms · alarm · unassigned

- **Moment:** PRESSURE HIGH! ticket lands. Events: alert_pressure_high.
- **Must say:** it is about to blow: rising, urgent, kettle-like
- **Sounds like:** a kettle shriek rising into fast beeps, with a steam hiss under it
- **Layers:** rising whistle 0.7-1.6 kHz; fast 2 kHz beeps; steam hiss
- **Length:** 1.2-2.0 s; sound starts within 15 ms, tail silence under 300 ms
- **Variations:** 1
- **Space:** 2D (global: same level everywhere), plus a positional layer at the boiler (OQ-035 default); deliver mono.
- **Level:** alarm standard m_max -14 LUFS, at most -1 dBTP; the mix sets -11 LUFS in game (ladder t2).
- **Phones:** loses at most 4.5 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** air-raid sirens, anything that sounds like the coal alarm.
- **Canon:** `av.audio.priority`: crisis alarms first: in a group they tell someone in the other carriage what is wrong · `gameplay.alerts.pressure_high`: PRESSURE HIGH! / The boiler's gonna blow! · `gameplay.crisis.pressure`: gauge in the cab; open the safety valve or brake when it redlines
- **Open:** OQ-035 (Crisis alarms: heard train-wide or at the source?) default A: 2D train-wide at full level plus a quieter positional layer at the source (boiler, powe; OQ-013 (Boiler pressure numbers (missing canon)) default A: Tune in Studio from the coal numbers and record the result with add-fact.

## breakdown_bang · crisis · tier 2 · Alarms · alarm · unassigned

- **Moment:** BREAKDOWN! ticket lands (electrics, axle, window or coupling fault). Events: alert_breakdown.
- **Must say:** something mechanical just broke: grab a wrench
- **Sounds like:** a metal bang with sparks crackling, then two blunt buzzer blasts
- **Layers:** metal bang; spark crackle; two 220 Hz buzzer blasts
- **Length:** 1.0-1.8 s; sound starts within 15 ms, tail silence under 300 ms
- **Variations:** 2 (runtime pitch spread 0.97-1.03)
- **Space:** 2D (global: same level everywhere), plus a positional layer at the powerbox (OQ-035 default); deliver mono.
- **Level:** alarm standard m_max -14 LUFS, at most -1 dBTP; the mix sets -11 LUFS in game (ladder t2).
- **Phones:** loses at most 4.5 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** gunshots, glass (windows own glass).
- **Canon:** `av.audio.priority`: crisis alarms first: in a group they tell someone in the other carriage what is wrong · `gameplay.alerts.breakdown`: BREAKDOWN! / Grab a wrench and fix it! · `gameplay.crisis.breakdowns`: broken windows, electrics down, axle sparks, coupling strain, derailed bogie
- **Open:** OQ-035 (Crisis alarms: heard train-wide or at the source?) default A: 2D train-wide at full level plus a quieter positional layer at the source (boiler, powe; OQ-012 (HUD alert IDs: per fault or generic BREAKDOWN?) default A: Per-fault IDs (WindowBroken, ElectricsDown, ...) with new texts the owner approves.

## coupling_snap · crisis · tier 2 · Alarms · impact · unassigned

- **Moment:** a coupling snaps and a carriage is lost. Events: coupling_snap.
- **Must say:** we just lost a carriage: a big, final snap
- **Sounds like:** a heavy chain link snapping with a metal twang and a chain rattling away
- **Layers:** snap; twang falling in pitch; chain rattle
- **Length:** 0.9-1.5 s; sound starts within 10 ms, tail silence under 500 ms
- **Variations:** 1 (runtime pitch spread 0.97-1.03)
- **Space:** 2D (global: same level everywhere), plus a positional layer at the coach (OQ-035 default); deliver mono.
- **Level:** impact standard m_max -14 LUFS, at most -1 dBTP; the mix sets -11 LUFS in game (ladder t2).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** gunshot, bone-crack sounds.
- **Canon:** `gameplay.crisis.coupling`: coupling snaps: lose the carriage and its passengers

## glass_smash · crisis · tier 2 · Alarms · impact · unassigned

- **Moment:** a coach window smashes. Events: windows_smash.
- **Must say:** a window just went: where it is matters
- **Sounds like:** a pane shattering with bright shards tinkling down
- **Layers:** impact crack; shard tinkles 2-8 kHz
- **Length:** 0.8-1.4 s; sound starts within 10 ms, tail silence under 500 ms
- **Variations:** 3 (runtime pitch spread 0.93-1.07)
- **Space:** 3D at the coach (the coach body (windows, coupling end)); deliver mono.
- **Level:** impact standard m_max -14 LUFS, at most -1 dBTP; the mix sets -11 LUFS in game (ladder t2).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** long tails, bottle-break cliches.
- **Canon:** `gameplay.crisis.windows`: windows smash; passengers scream and get distressed · `av.vfx.glass`: glass from the windows

## passengers_scream · crisis · tier 2 · Alarms · alarm · unassigned

- **Moment:** PASSENGERS UPSET! ticket lands. Events: alert_passengers_upset.
- **Must say:** the passengers are panicking: comic, not scary
- **Sounds like:** a small cartoon crowd going waaah with rising pitch, like a sitcom gasp
- **Layers:** 3-6 voices on an open ah vowel; upward pitch bend
- **Length:** 1.0-1.8 s; sound starts within 15 ms, tail silence under 300 ms
- **Variations:** 2 (runtime pitch spread 0.95-1.05)
- **Space:** 2D (global: same level everywhere), plus a positional layer at the coach (OQ-035 default); deliver mono.
- **Level:** alarm standard m_max -14 LUFS, at most -1 dBTP; the mix sets -11 LUFS in game (ladder t2).
- **Phones:** loses at most 4.5 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** real screams of pain or fear, children crying, horror.
- **Canon:** `av.audio.priority`: crisis alarms first: in a group they tell someone in the other carriage what is wrong · `gameplay.alerts.passengers_upset`: PASSENGERS UPSET! / Check the carriages, fast! · `gameplay.crisis.passengers`: seated NPCs (diner NPCs reused); mood calm > distressed > critical; drops during crises
- **Open:** OQ-035 (Crisis alarms: heard train-wide or at the source?) default A: 2D train-wide at full level plus a quieter positional layer at the source (boiler, powe

## split_explosion · crisis · tier 2 · Alarms · impact · unassigned

- **Moment:** t 0: a carriage tears in half at its break point; the fireball, glass burst and big camera shake land with it (train-wide 2D plus a positional layer at the break). Events: split_explosion (Sound.event).
- **Must say:** the train just ripped apart: the biggest bang of the run after the boiler fail, huge but funny
- **Sounds like:** a cartoon KA-BWOOM: a round boom that drops in pitch, a bright crack on top, fizzy firework crackle, then clunky bits clattering down
- **Layers:** mid crack-body 0.6-2.5 kHz in the first 0.3 s: the KA-BLAM phones hear; pitched body 150 to 62 Hz, its harmonics up to 2.5 kHz; sub thump 90 to 38 Hz with its upper harmonics (psychoacoustic bass); noise burst: crack 1.5-7.5 kHz (35 ms), roar 0.4-2.6 kHz (0.3 s); firework crackle 1.8-7 kHz thinning over 1.4 s; debris tail: wood clunks and tin clinks from 0.3 s; tail high-passed 20 to 500 Hz from 1.0 to 1.4 s: no rolling rumble
- **Length:** 2.0-2.4 s; sound starts within 10 ms, tail silence under 500 ms
- **Variations:** 1 (runtime pitch spread 0.97-1.03)
- **Space:** 2D (global: same level everywhere), plus a positional layer at the break (OQ-035 default); deliver mono.
- **Level:** impact standard m_max -14 LUFS, at most -1 dBTP; the mix sets -10 LUFS in game (ladder t2).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** war or artillery blasts, long rolling rumble, shrapnel whizzes, screams, ringing tinnitus; never louder than the boiler fail.
- **Canon:** `gameplay.crisis.coupling`: coupling snaps: lose the carriage and its passengers · `av.audio.priority`: crisis alarms first: in a group they tell someone in the other carriage what is wrong · `av.audio.slapstick`: slapstick lands through sound · `identity.pillars.funny_failure`: failure is funny and chaotic, never punishing or arbitrary
- **Open:** OQ-035 (Crisis alarms: heard train-wide or at the source?) default A: 2D train-wide at full level plus a quieter positional layer at the source (boiler, powe

## metal_tear · crisis · tier 3 · Split · impact · unassigned

- **Moment:** t -0.25 s: the carriage's seam gives way at the break point; the snap inside the file sits at 0.25 s so it lands on the explosion (t 0). Events: metal_tear (Sound.event).
- **Must say:** the metal can't hold any more: a strained groan ripping open, then SNAP
- **Sounds like:** a cartoon zip-rip through sheet metal: a creaky groan, a rising rrrrip, a sharp snap, then the torn sheet wobbling wub-wub-wub and drooping
- **Layers:** stick-slip creak through plate modes 0.3-3.1 kHz, rate rising 60 to 150 Hz under strain; rip: crackle and hiss sweeping 0.7 to 3.5 kHz, accelerating; snap at 0.25 s: crack 1.2-8 kHz, metal ping 1.3-3.5 kHz, small low thunk; wobble-sheet droop 420 to 180 Hz, wobble 7 to 4 Hz; last 150 ms faded to silence
- **Length:** 0.8-1.3 s; sound starts within 10 ms, tail silence under 500 ms
- **Variations:** 1 (runtime pitch spread 0.97-1.03)
- **Space:** 3D at the break (a carriage's break point (break frame B origin, 5 studs up: the torn seam); TrainSplitClient points it at an Attachment on the kept half's torn end); deliver mono.
- **Level:** impact standard m_max -14 LUFS, at most -1 dBTP; the mix sets -12.5 LUFS in game (ladder t3).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** horror metal screeches, whale-like groans, anything that outlasts the boom; never move the snap off 0.25 s.
- **Canon:** `gameplay.crisis.coupling`: coupling snaps: lose the carriage and its passengers · `av.audio.slapstick`: slapstick lands through sound · `identity.pillars.physical_loud`: interactions are physical and visible (lever, shovel, wrench), never a quiet menu or vote

## split_glass · crisis · tier 3 · Split · impact · unassigned

- **Moment:** t 0: the window panes nearest the break burst with the explosion (glass_burst fx); fire once, or once per side about 0.1 s apart. Events: split_glass (Sound.event).
- **Must say:** the windows went too: bright shards riding over the boom
- **Sounds like:** glass_smash's shards pitched up 3 semitones with the pane crack taken out (the boom already is the hit): a bright sprinkle
- **Layers:** shard tinkles about 2.4-9.5 kHz (glass_smash +3 semitones); no pane-crack transient
- **Length:** 0.6-0.9 s; sound starts within 10 ms, tail silence under 500 ms
- **Variations:** 1 (runtime pitch spread 0.97-1.03)
- **Space:** 3D at the break (a carriage's break point (break frame B origin, 5 studs up: the torn seam); TrainSplitClient points it at an Attachment on the kept half's torn end); deliver mono.
- **Level:** impact standard m_max -14 LUFS, at most -1 dBTP; the mix sets -13 LUFS in game (ladder t3).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** a second crack or boom, long tails, bottle-break cliches.
- **Canon:** `gameplay.crisis.windows`: windows smash; passengers scream and get distressed · `av.vfx.glass`: glass from the windows

## topple_crash · crisis · tier 3 · Split · impact · unassigned

- **Moment:** the broken half lands on its side at delay + roll time, about 1.5 s (on break 1 carriage 2 follows at 2.0 s on topple_crash_2); topple_dust and the medium shake land with it; its bounce thud sits at 0.35 s. Events: topple_crash (Sound.event).
- **Must say:** the wreck hit the ground hard: heavy, clunky, final
- **Sounds like:** a cartoon KER-RUNCH: a dull thud, wood splintering, a bin-lid clang drooping in pitch, gravel spraying, and a small bounce thud
- **Layers:** splinter burst 0.8-2.5 kHz in the first 80 ms; bin-lid clang 0.8-2.5 kHz struck in the first 80 ms, pitch drooping 4%; low impact 70 to 45 Hz with its upper harmonics; gravel tail: grains 1.5-6 kHz thinning over 1.2 s; bounce clunk at 0.35 s (topple bounce_time); last 150 ms faded to silence
- **Length:** 1.0-1.8 s; sound starts within 10 ms, tail silence under 500 ms
- **Variations:** 1 (runtime pitch spread 0.96-1.04)
- **Space:** 3D at the wreck (the lost body that slides and topples (moves with it); TrainSplitClient points it at an Attachment on that body (break 1: the broken half, then carriage 2 for its own crash)); deliver mono.
- **Level:** impact standard m_max -14 LUFS, at most -1 dBTP; the mix sets -13 LUFS in game (ladder t3).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** car-crash glass, a second explosion, bone-crunch or body-fall sounds.
- **Canon:** `av.audio.slapstick`: slapstick lands through sound · `identity.pillars.funny_failure`: failure is funny and chaotic, never punishing or arbitrary · `identity.pillars.physical_loud`: interactions are physical and visible (lever, shovel, wrench), never a quiet menu or vote

## debris_rain · crisis · tier 4 · Split · impact · unassigned

- **Moment:** t 0.8 s: bits of the carriage rain down on the kept half's roof and the track around the break. Events: debris_rain (Sound.event).
- **Must say:** it is still falling apart: small, clunky, a bit silly
- **Sounds like:** a handful of wood chips, bolts and tin bits pattering onto a metal roof, dense then sparse
- **Layers:** wood knocks 0.4-1.2 kHz with a faint roof boom; metal tinks 1.7-4.2 kHz; pebble ticks 2-7 kHz; two bigger clunks 200-420 Hz; dust hiss 1-5 kHz
- **Length:** 1.2-2.2 s; sound starts within 10 ms, tail silence under 500 ms
- **Variations:** 1 (runtime pitch spread 0.97-1.03)
- **Space:** 3D at the break (a carriage's break point (break frame B origin, 5 studs up: the torn seam); TrainSplitClient points it at an Attachment on the kept half's torn end); deliver mono.
- **Level:** impact standard m_max -14 LUFS, at most -1 dBTP; the mix sets -16 LUFS in game (ladder t4).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** gunfire rhythm (keep the spacing random), shrapnel whizzes, rain-on-window ambience.
- **Canon:** `av.audio.slapstick`: slapstick lands through sound · `identity.pillars.funny_failure`: failure is funny and chaotic, never punishing or arbitrary

## shovel_thud · crisis · tier 4 · Actions · oneshot · unassigned

- **Moment:** one shovel load lands in the firebox. Events: shovel_coal (lands with a 30 ms hit-stop at 0 ms).
- **Must say:** that helped: scrape, throw, the fire answers
- **Sounds like:** a shovel scrape, coal thrown in, a whoomph of fire
- **Layers:** scrape; coal thud; fire whoomph
- **Length:** 0.4-0.8 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 3 (runtime pitch spread 0.94-1.06)
- **Space:** 3D at the firebox (firebox door in the cab); deliver mono.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -15 LUFS in game (ladder t4).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** digging in dirt, gravel footsteps.
- **Canon:** `gameplay.crisis.firebox`: shovel coal from the bins into the firebox; fire drives pressure · `gameplay.fuel.shovel_pct`: 4

## topple_crash_2 · crisis · tier 4 · Split · impact · unassigned

- **Moment:** break 1 only, about 2.0 s: carriage 2 (the whole carriage dragged behind) lands on its side, 0.5 s after the broken half. Events: topple_crash_2 (Sound.event).
- **Must say:** the second, bigger body lands a beat later: lower and a little further away
- **Sounds like:** topple_crash's own file at PlaybackSpeed 0.84 (+-4%) and 3 dB under it (-16 vs -13 LUFS); register the same asset id
- **Layers:** topple_crash's layers, about 3 semitones lower and 19% longer
- **Length:** 1.0-1.8 s; sound starts within 10 ms, tail silence under 500 ms
- **Variations:** 1 (runtime pitch spread 0.806-0.874)
- **Space:** 3D at the wreck (the lost body that slides and topples (moves with it); TrainSplitClient points it at an Attachment on that body (break 1: the broken half, then carriage 2 for its own crash)); deliver mono.
- **Level:** impact standard m_max -14 LUFS, at most -1 dBTP; the mix sets -16 LUFS in game (ladder t4).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** a second upload (it is the same file), a hit identical to the first.
- **Canon:** `av.audio.slapstick`: slapstick lands through sound · `identity.pillars.funny_failure`: failure is funny and chaotic, never punishing or arbitrary · `identity.pillars.physical_loud`: interactions are physical and visible (lever, shovel, wrench), never a quiet menu or vote

## wreck_scrape · crisis · tier 4 · Split · impact · unassigned

- **Moment:** t 0.3 s until the lost part reaches the terrain's speed (V/brake: about 2.9 s at the normal speed 35 and brake 12): the wreck grinds along the ballast as it slows. Speed rule (TrainSplitClient): PlaybackSpeed = clamp(35 / V, 0.7, 1.2), passed as ctx.pitch (the map's own pitch stays 1.0), and a 0.3 s fade-out once the wreck is under 2 studs/s relative to the terrain, so it ends about 0.13 s after the slide at any Speed; the file runs 3.1 s so that stop, not the file's end, always closes it. Events: wreck_scrape (Sound.event).
- **Must say:** the wreck is sliding away and running out of steam
- **Sounds like:** a heavy metal box grinding over gravel: a rough grrrr that wobbles as the wreck rocks, slowing and sagging in pitch until it stops
- **Layers:** grinding noise 0.28-2.5 kHz with 16-60 Hz stick-slip roughness (low-passed at 2.5 kHz); fade-in 0.6 s from -12 dB: it emerges under the boom; wobble: timbre sway 5 to 3 Hz; faint droopy metal whine 520 to 430 Hz; gravel pops 1.5-2.5 kHz; low rumble 45-220 Hz; 0.45 s settle after the slide (heard only if the stop comes late)
- **Length:** 2.6-3.2 s; sound starts within 10 ms, tail silence under 500 ms
- **Variations:** 1
- **Space:** 3D at the wreck (the lost body that slides and topples (moves with it); TrainSplitClient points it at an Attachment on that body (break 1: the broken half, then carriage 2 for its own crash)); deliver mono.
- **Level:** impact standard m_max -14 LUFS, at most -1 dBTP; the mix sets -16 LUFS in game (ladder t4).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** brake squeal or rail screech (horror-adjacent), engine noise, anything that keeps going after the wreck stops.
- **Canon:** `gameplay.speed.normal`: 35 · `av.audio.slapstick`: slapstick lands through sound

## wrench_clank · crisis · tier 4 · Actions · oneshot · unassigned

- **Moment:** a breakdown task completes (wrench, wire match). Events: repair_fixed (lands with a 40 ms hit-stop at 0 ms).
- **Must say:** fixed: clank-clank-ding
- **Sounds like:** two wrench clanks on iron, then a small bell ding
- **Layers:** two metal clanks; ding
- **Length:** 0.5-1.0 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 2 (runtime pitch spread 0.96-1.04)
- **Space:** 3D at the powerbox (the coach power box); deliver mono.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -15 LUFS in game (ladder t4).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** power-tool whirs.
- **Canon:** `gameplay.crisis.breakdowns`: broken windows, electrics down, axle sparks, coupling strain, derailed bogie

## brake_hiss · arrive · tier 4 · Actions · oneshot · unassigned

- **Moment:** the train stops at the station marker. Events: station_arrive.
- **Must say:** we made it: a long exhale
- **Sounds like:** a big steam brake hiss with a low settle
- **Layers:** broadband hiss; low rumble settle
- **Length:** 1.0-2.0 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 1 (runtime pitch spread 0.97-1.03)
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -15 LUFS in game (ladder t4).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** air-brake squeal of modern trains.
- **Canon:** `gameplay.run.arrival`: station segment with a StopMarker; lock throttle, stop events and coal drain; Miles counter hits 0 as the train stops · `av.audio.pack`: whistle, hiss, wheels, alarms

## cash_register · arrive · tier 4 · Actions · oneshot · unassigned

- **Moment:** FARE BANKED! at a station. Events: alert_fare_banked.
- **Must say:** money is safe: a satisfying ka-ching
- **Sounds like:** an old till: drawer slide then a bright bell
- **Layers:** drawer slide; bell 2-3 kHz
- **Length:** 0.6-1.2 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 1
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -15 LUFS in game (ladder t4).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** casino jackpots or coin showers (never sell odds).
- **Canon:** `gameplay.alerts.fare_banked`: FARE BANKED! / Station paid out / $120 · `identity.pillars.banked_fare`: fare is banked at stations; a crash loses only what is not banked
- **Open:** OQ-003 (Currency: coins, "$" or fare?) default C: Data name Coins, player-facing "$" as already built; "fare" is the in-run event (FARE B

## radio_loop · arrive · tier 7 · Music · music · unassigned

- **Moment:** the cab Radio button toggles a loop. Events: trip_end (Sound.event), radio_button (Sound.event).
- **Must say:** a crackly, cheerful little station tune
- **Sounds like:** a jaunty old-timey jingle through a tinny radio speaker
- **Layers:** melody; bass; radio band-pass and crackle
- **Length:** 8.0-30.0 s; seamless loop, no fade in or out
- **Variations:** 1
- **Space:** 3D at the cab (cab dashboard (horn button, radio)); deliver mono.
- **Level:** music standard integrated -18 LUFS, at most -1 dBTP; the mix sets -25 LUFS in game (ladder music).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** licensed pop songs, anything not owner-made or Roblox-licensed.
- **Canon:** `av.audio.horn`: Horn cab button plays a sound; Radio button plays a loop · `release.alpha.sidings`: diesel train, client-side world, "run it again" vote, rejoin after disconnect, analytics funnel, Monday parking lot (cab button behaviours, radio dispatcher, junction lamp, cab dressing, bullet train)
- **Open:** OQ-021 (Audio identity (missing canon)) default A: Diegetic only for the alpha (whistle, hiss, wheels, alarms), no music during runs.

## horn · any · tier 4 · Actions · oneshot · unassigned

- **Moment:** a player presses the cab Horn button. Events: horn_button (Sound.event).
- **Must say:** honk: silly and fun to spam (cooldown stops abuse)
- **Sounds like:** a short two-tone toy horn
- **Layers:** two detuned tones
- **Length:** 0.5-1.0 s; sound starts within 10 ms, tail silence under 300 ms
- **Variations:** 1
- **Space:** 3D at the cab (cab dashboard (horn button, radio)); deliver mono.
- **Level:** oneshot standard m_max -14 LUFS, at most -1 dBTP; the mix sets -15 LUFS in game (ladder t4).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** loud modern diesel horns.
- **Canon:** `av.audio.horn`: Horn cab button plays a sound; Radio button plays a loop · `release.alpha.sidings`: diesel train, client-side world, "run it again" vote, rejoin after disconnect, analytics funnel, Monday parking lot (cab button behaviours, radio dispatcher, junction lamp, cab dressing, bullet train)

## ticket_chime · any · tier 5 · UI · ui · unassigned

- **Moment:** an info ticket (crew joined or left) lands. Events: alert_crew_joined (Sound.event), alert_crew_left (Sound.event).
- **Must say:** for your information: soft, never urgent
- **Sounds like:** a two-note station chime, very short
- **Layers:** two bell tones
- **Length:** 0.2-0.5 s; sound starts within 5 ms, tail silence under 150 ms
- **Variations:** 1
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** ui standard m_max -20 LUFS, at most -1 dBTP; the mix sets -19 LUFS in game (ladder t5).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** notification sounds of real phone apps.
- **Canon:** `gameplay.alerts.crew_joined`: CREW JOINED! / {name} is aboard · `gameplay.alerts.crew_left`: CREW LEFT! / {name} left the train

## ui_click · any · tier 5 · UI · ui · unassigned

- **Moment:** a GUI button is pressed. Events: ui_button_press (Sound.event).
- **Must say:** pressed: tiny and dry
- **Sounds like:** a small mechanical switch click
- **Layers:** click + short tonal blip
- **Length:** 0.03-0.1 s; sound starts within 5 ms, tail silence under 150 ms
- **Variations:** 2 (runtime pitch spread 0.97-1.03)
- **Space:** 2D (global: same level everywhere); deliver mono or stereo.
- **Level:** ui standard m_max -20 LUFS, at most -1 dBTP; the mix sets -19 LUFS in game (ladder t5).
- **Phones:** loses at most 6 dB on a phone speaker: keep energy in 0.5-4 kHz.
- **Avoid:** phone keyboard clicks, anything longer than 100 ms.
- **Canon:** `ui.lever.commit`: side lamp lights hazard yellow on commit; timer spent; hint hidden
