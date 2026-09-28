#!/usr/bin/env python3
"""TRIAL ADDITION (not part of rr-soundsmith): phase-ordered run sound map from the mission soundmap and the built
SOUND_SPEC.md. Since the fix, SOUND_SPEC itself is phase-ordered (events carry a phase); this adds the per-phase mix notes.  python3 run_map.py SOUNDMAP SPEC OUT"""
import json, re, sys

if len(sys.argv) != 4 or sys.argv[1] in ("-h", "--help"):
    sys.exit(print(__doc__) or 0)
m = json.load(open(sys.argv[1]))
rows = {}
for line in open(sys.argv[2]):
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(c) == 11 and c[1] in m["events"]:
        rows.setdefault(c[1], []).append(c[1:])
PHASES = [
    ("Lobby (Depot Lobby place)", ["lobby_enter", "queue_join", "queue_leave", "queue_countdown_tick", "queue_launch", "lobby_leave"],
     "no ducking; lobby_bed is the only loop; open question OQ-044 (lobby audio) default A: no music"),
    ("Departure", ["trip_start", "depart"], "wheels_loop follows Speed 0 -> Normal over ~5 s (gameplay.run.depart) when game code calls Sound.setSpeed every frame of the ramp; silent below 1.5 studs/s"),
    ("Junction", ["alert_junction_ahead", "fork_countdown_tick", "lever_commit", "lever_commit_crew", "alert_risky_route"],
     "duck `fork` (countdown_tick, lever_clunk, junction_beep): Ambient -5, Music -6 dB"),
    ("Crisis", ["alert_coal_low", "alert_pressure_high", "alert_breakdown", "alert_passengers_upset", "windows_smash",
                "coupling_snap", "shovel_coal", "repair_fixed", "alert_crate_landed", "boiler_burst", "fired_stamp"],
     "duck `crisis` (any Alarms sound): Ambient -8, Music -10, UI -3 dB; duck `fail` (boiler_boom): Actions -10, UI -12, Ambient -14, Music -18 dB; Alarms cap 6: a playing crisis alarm is never cut by glass or coupling impacts"),
    ("Arrival", ["station_arrive", "alert_fare_banked", "trip_end"], "wheels fade with Speed to silence at the StopMarker when Sound.setSpeed is called every frame while braking (README step 4); trip_end stops all trip loops"),
    ("Any time", ["ui_button_press", "alert_crew_joined", "alert_crew_left", "horn_button", "radio_button"], "horn and radio are sidings (not alpha)"),
]
seen = set()
L = ["# Risky Rails run sound map (phase order)", "",
     "Generated from src/sound/soundmap.json + export/sound/SOUND_SPEC.md. Level = in-game target LUFS (ladder); Volume = "
     "Sound.Volume the runtime sets (modelled, ref 0.5). Every sound is unassigned: placeholders exist for 5 (src/sound/ph).", ""]
for name, evs, note in PHASES:
    L += [f"## {name}", "", f"Mix: {note}", "", "| event | via | action | sound | tier | group | space | level | Volume |",
          "|---|---|---|---|---|---|---|---|---|"]
    for e in evs:
        seen.add(e)
        for c in rows.get(e, []):
            L.append(f"| {c[0]} | {c[1]} | {c[2]} | {c[3]} | {c[4]} | {c[5]} | {c[6]} | {c[7]} | {c[8]} |")
    L.append("")
missing = [e for e in m["events"] if e not in seen]
L.append(f"Unphased events: {', '.join(missing) if missing else 'none'}.")
open(sys.argv[3], "w").write("\n".join(L) + "\n")
print(f"wrote {sys.argv[3]}; unphased: {missing or 'none'}")
