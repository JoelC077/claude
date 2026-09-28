# Risky Rails run sound map (phase order)

Generated from src/sound/soundmap.json + export/sound/SOUND_SPEC.md. Level = in-game target LUFS (ladder); Volume = Sound.Volume the runtime sets (modelled, ref 0.5). Every sound is unassigned: placeholders exist for 5 (src/sound/ph).

## Lobby (Depot Lobby place)

Mix: no ducking; lobby_bed is the only loop; open question OQ-044 (lobby audio) default A: no music

| event | via | action | sound | tier | group | space | level | Volume |
|---|---|---|---|---|---|---|---|---|
| lobby_enter | direct | start | lobby_bed | 6 | Ambient | 2d | -27 | 0.2233 |
| queue_join | direct | play | queue_punch | 4 | Actions | 2d | -15 | 0.4456 |
| queue_leave | direct | play | queue_punch | 4 | Actions | 2d | -15 | 0.4456 |
| queue_countdown_tick | direct | play | queue_bell | 5 | UI | 2d | -19 | 0.561 |
| queue_launch | direct | play | guard_whistle | 4 | Actions | 2d | -15 | 0.4456 |
| lobby_leave | direct | stop | lobby_bed | 6 | Ambient | 2d | -27 | 0.2233 |

## Departure

Mix: wheels_loop follows Speed 0 -> Normal over ~5 s (gameplay.run.depart) when game code calls Sound.setSpeed every frame of the ramp; silent below 1.5 studs/s

| event | via | action | sound | tier | group | space | level | Volume |
|---|---|---|---|---|---|---|---|---|
| trip_start | direct | start | wheels_loop | 6 | Ambient | 2d | -27 | 0.2233 |
| trip_start | direct | start | firebox_loop | 6 | Ambient | 3d @firebox | -27 | 0.2233 |
| trip_start | direct | start | wind_bed | 6 | Ambient | 2d | -27 | 0.2233 |
| depart | feel | play | whistle | 4 | Actions | 2d | -15 | 0.4456 |

## Junction

Mix: duck `fork` (countdown_tick, lever_clunk, junction_beep): Ambient -5, Music -6 dB

| event | via | action | sound | tier | group | space | level | Volume |
|---|---|---|---|---|---|---|---|---|
| alert_junction_ahead | feel | play | junction_beep | 3 | Actions | 2d | -13 | 0.561 |
| fork_countdown_tick | feel | play | countdown_tick | 3 | Actions | 2d | -13 | 0.561 |
| lever_commit | feel | play | lever_clunk | 3 | Actions | 3d @lever | -13 | 0.561 |
| lever_commit_crew | feel | play | points_throw | 4 | Actions | 2d | -15 | 0.4456 |
| alert_risky_route | feel | play | stamp_slam | 3 | Actions | 2d | -13 | 0.561 |

## Crisis

Mix: duck `crisis` (any Alarms sound): Ambient -8, Music -10, UI -3 dB; duck `fail` (boiler_boom): Actions -10, UI -12, Ambient -14, Music -18 dB; Alarms cap 6: a playing crisis alarm is never cut by glass or coupling impacts

| event | via | action | sound | tier | group | space | level | Volume |
|---|---|---|---|---|---|---|---|---|
| alert_coal_low | feel | play | alarm_coal | 2 | Alarms | 2d +3d @firebox | -11 | 0.7063 |
| alert_pressure_high | feel | play | alarm_pressure | 2 | Alarms | 2d +3d @boiler | -11 | 0.7063 |
| alert_breakdown | feel | play | breakdown_bang | 2 | Alarms | 2d +3d @powerbox | -11 | 0.7063 |
| alert_passengers_upset | feel | play | passengers_scream | 2 | Alarms | 2d +3d @coach | -11 | 0.7063 |
| windows_smash | feel | play | glass_smash | 2 | Alarms | 3d @coach | -11 | 0.7063 |
| coupling_snap | feel | play | coupling_snap | 2 | Alarms | 2d +3d @coach | -11 | 0.7063 |
| shovel_coal | feel | play | shovel_thud | 4 | Actions | 3d @firebox | -15 | 0.4456 |
| repair_fixed | feel | play | wrench_clank | 4 | Actions | 3d @powerbox | -15 | 0.4456 |
| alert_crate_landed | feel | play | crate_thump | 4 | Actions | 3d @roof | -15 | 0.4456 |
| boiler_burst | feel | play | boiler_boom | 1 | Alarms | 2d | -9 | 0.8891 |
| fired_stamp | feel | play | stamp_slam | 3 | Actions | 2d | -13 | 0.561 |

## Arrival

Mix: wheels fade with Speed to silence at the StopMarker when Sound.setSpeed is called every frame while braking (README step 4); trip_end stops all trip loops

| event | via | action | sound | tier | group | space | level | Volume |
|---|---|---|---|---|---|---|---|---|
| station_arrive | feel | play | brake_hiss | 4 | Actions | 2d | -15 | 0.4456 |
| alert_fare_banked | feel | play | cash_register | 4 | Actions | 2d | -15 | 0.4456 |
| trip_end | direct | stop | wheels_loop | 6 | Ambient | 2d | -27 | 0.2233 |
| trip_end | direct | stop | firebox_loop | 6 | Ambient | 3d @firebox | -27 | 0.2233 |
| trip_end | direct | stop | wind_bed | 6 | Ambient | 2d | -27 | 0.2233 |
| trip_end | direct | stop | radio_loop | 7 | Music | 3d @cab | -25 | 0.2233 |

## Any time

Mix: horn and radio are sidings (not alpha)

| event | via | action | sound | tier | group | space | level | Volume |
|---|---|---|---|---|---|---|---|---|
| ui_button_press | direct | play | ui_click | 5 | UI | 2d | -19 | 0.561 |
| alert_crew_joined | direct | play | ticket_chime | 5 | UI | 2d | -19 | 0.561 |
| alert_crew_left | direct | play | ticket_chime | 5 | UI | 2d | -19 | 0.561 |
| horn_button | direct | play | horn | 4 | Actions | 3d @cab | -15 | 0.4456 |
| radio_button | direct | toggle | radio_loop | 7 | Music | 3d @cab | -25 | 0.2233 |

Unphased events: none.
