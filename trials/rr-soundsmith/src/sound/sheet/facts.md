# Facts (rr-soundsmith sheet; measured by audiolib, BS.1770-4)

You cannot hear these sounds. Judge the plan and the measurements; the owner's ears in Studio are the final check.
Ladder (LUFS in game): t1 -9, t2 -11, t3 -13, t4 -15, t5 -19, ambient -27, music -25. Phone level = target minus the loss through a phone-speaker model (HP 450 Hz, LP 10 kHz).

| sound | tier | file | s | level | TP | lead ms | tail ms | phone loss | bands sub/low/phone/air | seam | check |
|---|---|---|---|---|---|---|---|---|---|---|---|
| alarm_coal | 2 | PLACEHOLDER_alarm_coal.wav | 1.70 | -14.0 m_max | -14.55 | 1.5 | 54.1 | 2.51 | 0.00/0.49/0.51/0.00 | - | PASS |
| lever_clunk | 3 | PLACEHOLDER_lever_clunk.wav | 0.50 | -14.03 m_max | -1.41 | 0.0 | 46.0 | 2.32 | 0.17/0.41/0.42/0.00 | - | PASS |
| brake_hiss | 4 | PLACEHOLDER_brake_hiss.wav | 1.60 | -14.0 m_max | -6.77 | 0.0 | 0.4 | 1.27 | 0.01/0.00/0.38/0.61 | - | PASS |
| whistle | 4 | PLACEHOLDER_whistle.wav | 1.80 | -14.0 m_max | -6.92 | 3.8 | 9.3 | 0.46 | 0.00/0.00/1.00/0.00 | - | PASS |
| lobby_bed | 6 | PLACEHOLDER_lobby_bed.wav | 12.00 | -20.0 integrated | -8.88 | 0.0 | 0.0 | 0.87 | 0.15/0.05/0.42/0.38 | x0.96 | PASS |

## Hierarchy on a phone speaker

holds: no lower tier is louder than a higher tier by over 1 LU on a phone

## Ducking

- fail: boiler_boom -> Actions -10 dB, UI -12 dB, Ambient -14 dB, Music -18 dB; attack 0.02 s, hold 0.5 s, release 1.6 s
- crisis: group Alarms -> Ambient -8 dB, Music -10 dB, UI -3 dB; attack 0.05 s, hold 0.25 s, release 0.8 s
- fork: countdown_tick, lever_clunk, junction_beep -> Ambient -5 dB, Music -6 dB; attack 0.03 s, hold 0.3 s, release 0.6 s

## Event and brief table (phase order; from soundmap.json)

| phase | sound | tier/group | space | events | must say | sounds like | avoid |
|---|---|---|---|---|---|---|---|
| lobby | guard_whistle | t4 Actions | 2d | queue_launch (direct) | all aboard: we're going | a guard's pea whistle, one long trilled blast, friendlier than a referee | the steam whistle chord (departure owns it), referee triple blasts, police whis… |
| lobby | queue_punch | t4 Actions | 2d | queue_join (direct), queue_leave (direct) | you're on the crew for this train | a conductor's ticket punch biting card, chk-chk, with a small brass click | cash sounds (the till owns money), UI blips, stapler |
| lobby | queue_bell | t5 UI | 2d | queue_countdown_tick (direct) | this train leaves soon: get on the pad | a station platform hand-bell, one ding per second | the fork countdown tick (the loudest countdown belongs to the lever), school be… |
| lobby | lobby_bed | t6 Ambient | 2d | lobby_enter (direct), lobby_leave (direct) | a sleepy, run-down depot where our train is waiting | a resting steam loco breathing slow puffs, an iron lantern buzzing, a few distant birds a… | music (open question lobby-audio, default A: no music), crowd walla, city traff… |
| depart | whistle | t4 Actions | 2d | depart (feel) | we're off: cheerful, big, steam | a three-chime steam whistle, bright chord with breathy steam | diesel horns (alpha is steam only), ship horns |
| depart | firebox_loop | t6 Ambient | 3d @firebox | trip_start (direct), trip_end (direct) | the fire is alive (the cab has a heartbeat) | a steady fire roar with small crackles | campfire-at-night mood |
| depart | wheels_loop | t6 Ambient | 2d | trip_start (direct), trip_end (direct) | we're moving, and how fast | clickety-clack rail joints over a rolling rumble, recorded at the Normal notch | modern welded-rail hum, squeals |
| depart | wind_bed | t6 Ambient | 2d | trip_start (direct), trip_end (direct) | open country going by | light wind with gentle gusts | storms, howling |
| run | crate_thump | t4 Actions | 3d @roof | alert_crate_landed (feel) | your crate is up there, go get it | a wooden crate dropping onto a metal roof, with a short creak | explosions |
| fork | countdown_tick | t3 Actions | 2d | fork_countdown_tick (feel) | decide now: the loudest countdown in the game | a big wooden clock tick crossed with a signal-box bell tap | bomb-timer beeps, sci-fi blips |
| fork | junction_beep | t3 Actions | 2d | alert_junction_ahead (feel) | a fork is coming, get to the lever | two crisp signal beeps, like a level-crossing warning | anything alarm-like; this is information, not danger |
| fork | lever_clunk | t3 Actions | 3d @lever | lever_commit (feel) | heavy, final, mechanical: no going back | an iron lever dropping into a notch; a big latch; a pinball flipper's thunk | gunshots, long reverb, UI-like clicks |
| fork | stamp_slam | t3 Actions | 2d | alert_risky_route (feel), fired_stamp (feel) | official, comic, final: a rubber stamp hitting a desk | a rubber stamp slammed on paper on a wooden desk | gavel or gunshot |
| fork | points_throw | t4 Actions | 2d | lever_commit_crew (feel) | the points just moved: the bet is placed | distant railway points clacking over, two heavy clacks | sounding like the lever clunk itself |
| crisis | boiler_boom | t1 Alarms | 2d | boiler_burst (feel) | total, cartoon disaster: huge but funny, never grim | a big cartoon kaboom, then clattering debris and one last pan-like clang | war or horror explosions, screams, long ringing tinnitus |
| crisis | alarm_coal | t2 Alarms | 2d +3d @firebox -4 dB | alert_coal_low (feel) | the fire is dying, go shovel: a sad, droopy call you learn in one trip | a two-note descending brass wah-wah, like a deflating trombone on a klaxon | sirens (pressure owns the rising siren), horror stings |
| crisis | alarm_pressure | t2 Alarms | 2d +3d @boiler -4 dB | alert_pressure_high (feel) | it is about to blow: rising, urgent, kettle-like | a kettle shriek rising into fast beeps, with a steam hiss under it | air-raid sirens, anything that sounds like the coal alarm |
| crisis | breakdown_bang | t2 Alarms | 2d +3d @powerbox -4 dB | alert_breakdown (feel) | something mechanical just broke: grab a wrench | a metal bang with sparks crackling, then two blunt buzzer blasts | gunshots, glass (windows own glass) |
| crisis | coupling_snap | t2 Alarms | 2d +3d @coach -4 dB | coupling_snap (feel) | we just lost a carriage: a big, final snap | a heavy chain link snapping with a metal twang and a chain rattling away | gunshot, bone-crack sounds |
| crisis | glass_smash | t2 Alarms | 3d @coach | windows_smash (feel) | a window just went: where it is matters | a pane shattering with bright shards tinkling down | long tails, bottle-break cliches |
| crisis | passengers_scream | t2 Alarms | 2d +3d @coach -4 dB | alert_passengers_upset (feel) | the passengers are panicking: comic, not scary | a small cartoon crowd going waaah with rising pitch, like a sitcom gasp | real screams of pain or fear, children crying, horror |
| crisis | shovel_thud | t4 Actions | 3d @firebox | shovel_coal (feel) | that helped: scrape, throw, the fire answers | a shovel scrape, coal thrown in, a whoomph of fire | digging in dirt, gravel footsteps |
| crisis | wrench_clank | t4 Actions | 3d @powerbox | repair_fixed (feel) | fixed: clank-clank-ding | two wrench clanks on iron, then a small bell ding | power-tool whirs |
| arrive | brake_hiss | t4 Actions | 2d | station_arrive (feel) | we made it: a long exhale | a big steam brake hiss with a low settle | air-brake squeal of modern trains |
| arrive | cash_register | t4 Actions | 2d | alert_fare_banked (feel) | money is safe: a satisfying ka-ching | an old till: drawer slide then a bright bell | casino jackpots or coin showers (never sell odds) |
| arrive | radio_loop | t7 Music | 3d @cab | trip_end (direct), radio_button (direct) | a crackly, cheerful little station tune | a jaunty old-timey jingle through a tinny radio speaker | licensed pop songs, anything not owner-made or Roblox-licensed |
| any | horn | t4 Actions | 3d @cab | horn_button (direct) | honk: silly and fun to spam (cooldown stops abuse) | a short two-tone toy horn | loud modern diesel horns |
| any | ticket_chime | t5 UI | 2d | alert_crew_joined (direct), alert_crew_left (direct) | for your information: soft, never urgent | a two-note station chime, very short | notification sounds of real phone apps |
| any | ui_click | t5 UI | 2d | ui_button_press (direct) | pressed: tiny and dry | a small mechanical switch click | phone keyboard clicks, anything longer than 100 ms |

## Coverage

Mapped: 32/32 events play a sound; 29/29 sounds are played by an event; 29/29 briefed; 8/8 3D sounds have an emitter role.
Files in this pass: 5/29 (the scope of this sheet). No file here (mapped and briefed above; not a coverage gap): guard_whistle, queue_punch, queue_bell, firebox_loop, wheels_loop, wind_bed, crate_thump, countdown_tick, junction_beep, stamp_slam, points_throw, boiler_boom, alarm_pressure, breakdown_bang, coupling_snap, glass_smash, passengers_scream, shovel_thud, wrench_clank, cash_register, radio_loop, horn, ticket_chime, ui_click. 4 rr-game-feel events drawn in the timeline.
Asset states: all unassigned (no uploads registered yet).
Voices: {"Alarms": 6, "Actions": 8, "UI": 4}, max 16; new fail and crisis sounds always get a voice; a playing crisis alarm is cut only by the fail or another alarm.
