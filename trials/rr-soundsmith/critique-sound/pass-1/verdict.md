FIRST READ: The eye goes first to the red t1/t2 block on the Ladder, then down the yellow and teal staircase, then to the four phone dots. There lever_clunk's dot sits level with the t4 whistle's dot. On the timeline, lever_clunk peaks right on the 0 ms hit-stop.
Overall this reads as an alarms-first plan with a comic brief table and clean 2 LU steps on the bars. The phone view, the in-game peaks, the ducking and the repetition safety are not yet at professional delivery.

SCORES:
S1 Signal and hierarchy: 6/10 — meets the 4 anchor and most of 7 because the Ladder bars step t1 -9 / t2 -11 / t3 -13 / t4 -15 / t5 -19 with no overlap, and each crisis-alarm brief has its own rhythm (a descending wah-wah, a kettle shriek into beeps, a bang then 2 buzzes, a snap then a rattle, a shatter, a crowd waaah). It is below 7 because on the phone dots lever_clunk (-15.32) is only 0.14 LU above the whistle (-15.46) and 1.8 LU below alarm_coal (-13.51), and because the t2 glass_smash is 3D-only (S1-1, S1-2). Below 9 also: S1-3, S1-4.
S2 Timing and envelope: 7/10 — meets 7 because leads are 0.0-3.8 ms in Facts, and on the timeline lever_clunk peaks at 0 ms under the hit-stop and flash. Lengths suit their moments (brake_hiss 1.6 s exhale, whistle 1.8 s departure), and the lobby_bed seam is x0.96 PASS. It is below 8 because of S2-1 (a 0.4 ms tail on brake_hiss). Below 9 also: S2-2.
S3 Clarity on a phone: 6/10 — above 4 because no tier-1 to tier-3 file lives below 150 Hz (sub 0.00 and 0.17) and phone losses are 2.51 and 2.32 dB, both under 3. It is below 7 because the alarm and the commit keep only 51% and 42% of their energy in 0.5-4 kHz: the tiles show their bands at or below the 500 Hz tick (S3-1, S3-2). This low-band energy is also why the phone dots in S1-1 collapse.
S4 Mix safety and fatigue: 5/10 — above 4 because voice caps exist (Alarms 6, Actions 8, UI 4, max 16), every duck has a 0.02-0.05 s attack and a 0.6-1.6 s release, and every file as delivered has TP of -1.41 or lower. It is below 7 because lever_clunk reaches -0.38 dBTP in game (S4-1), the fork duck pumps on every tick (S4-2), and no variations or cooldowns are planned for repeatable sounds (S4-3). Below 9 also: S4-4.
S5 Style match: 7/10 — meets 7 because the event briefs are comic and physical: the deflating-trombone coal alarm, the cartoon kaboom with a pan clang, the pinball-flipper lever, the rubber stamp, the toy horn and the sitcom-gasp passengers. Every avoid column also bans horror, war and diesel. It is below 8 because of S5-1 (generic briefs for glass_smash and wind_bed).
S6 Coverage and polish: 7/10 — meets 7 because Coverage shows 32/32 events mapped, 29/29 sounds played and briefed and 8/8 3D emitters, and all 5 files carry PLACEHOLDER in both the filename and the tile. It is below 8 because of S6-1. Below 9 also: S6-2.

ISSUES (ranked by impact, lowest-scoring criteria first; issue format):
[S4-1] S4 · lever_clunk, Facts TP against the Ladder t3 target   impact: high   blocks-8: yes
  Problem: The file measures TP -1.41 dBTP at -14.03 LUFS m_max. The Ladder plays t3 at -13, a gain of +1.03 dB, so the in-game true peak is -0.38 dBTP before anything else is summed with it. The same arithmetic will push a -14-normalised boiler_boom (t1 -9, +5 dB) well past 0 dBTP.
  Fix: True-peak-limit lever_clunk to -2.1 dBTP or lower at -14 m_max. Add a sheet check: file TP + (tier target - file level) must be -1.0 dBTP or lower. At -14 m_max that means t1 files need TP of -6.0 or lower, t2 files -4.0 or lower and t3 files -2.1 or lower.
  Done when: Facts shows lever_clunk TP of -2.1 or lower, and an in-game TP column reads -1.0 dBTP or lower for every file.
[S4-2] S4 · fork duck line in the Ducking table (trigger countdown_tick)   impact: high   blocks-8: yes
  Problem: The duck runs attack 0.03 + hold 0.3 + release 0.6 = 0.93 s and retriggers on every countdown_tick. At one tick per second (queue_bell's rate; the fork tick rate is not in Facts) the wheels and wind drop 5 dB and fully recover on every tick. That is a 1 Hz pump under the tensest moment of the run.
  Fix: Remove countdown_tick from the fork trigger list. Key the duck on alert_junction_ahead and hold it until lever_commit, then release 0.6 s after lever_clunk. If that is not possible, set the fork hold to 1.2 s so it bridges the ticks. Keep Ambient -5 and Music -6.
  Done when: The Ducking fork line has no per-tick trigger, or its hold is at least the tick interval plus 0.1 s.
[S4-3] S4 · variation and cooldown plan in the event table / Coverage, plus the lobby_bed tile   impact: med   blocks-8: yes
  Problem: No sound has a variation set, and only horn names a cooldown. Several sounds repeat many times over a 12-minute trip: shovel_thud (every shovel during coal-low), wrench_clank, ui_click, queue_punch, glass_smash and countdown_tick. The lobby_bed spectrogram also shows three identical, evenly spaced bird bursts in its 12.0 s loop, so the same calls come back 15 times a minute.
  Fix: shovel_thud: 4 variations, pitch ±5%, minimum interval 0.25 s. wrench_clank: 3 variations. ui_click: 3 variations plus a 0.05 s cooldown. queue_punch: 2 variations. glass_smash: 3 variations. lobby_bed: remove the birds from the bed and play them as a pool of 4 one-shot calls with random gaps of 6-20 s.
  Done when: Facts or soundmap has a variations/cooldown column showing shovel_thud 4 or more, wrench_clank 3 or more, ui_click 3 or more and glass_smash 3 or more, and the lobby_bed tile shows no periodic bird blocks.
[S4-4] S4 · fail duck, Music -18 dB   impact: low   blocks-8: no
  Problem: -18 dB is outside the 3-14 dB range. It takes the radio from -25 to -43, which effectively mutes it for the 0.5 s hold plus the 1.6 s release.
  Fix: Set the fail duck on Music to -12 dB.
  Done when: The Ducking fail line shows a Music duck of 14 dB or less.
[S1-1] S1 · phone dots on the Ladder, t2/t3/t4   impact: high   blocks-8: yes
  Problem: The bars step 2 LU apart, but on the phone dots alarm_coal is -13.51, lever_clunk -15.32, whistle -15.46 and brake_hiss -16.27. The commit sits only 0.14 LU above a routine departure whistle and 1.8 LU below the crisis alarm, on the device most players use.
  Fix: First apply S3-1 (alarm_coal phone loss 1.0 dB or less) and S3-2 (lever_clunk 1.5 dB or less). Then trim whistle to -16 LUFS m_max, because its energy is 100% in the phone band and it loses only 0.46 dB, so it plays hot on phones.
  Done when: The Ladder dots read alarm_coal -12.0 or higher, lever_clunk -14.5 or higher and whistle -16.4 or lower, i.e. at least 1.5 LU between adjacent tiers.
[S1-2] S1 · glass_smash space column in the event table   impact: high   blocks-8: yes
  Problem: glass_smash is a t2 Alarm but plays only in 3D @coach. Every other t2 alarm is 2D train-wide plus a 3D layer at -4 dB (OQ-035 default A). A window breaking in one carriage may never reach the other, which breaks the canon rule that alarms tell the other carriage what is wrong.
  Fix: Set space to 2d at -6 dB plus 3d @coach at full level. This keeps the brief's "where it is matters".
  Done when: The event table row reads 2d -6 dB +3d @coach.
[S1-3] S1 · t3 bars on the Ladder (countdown_tick, junction_beep, lever_clunk, stamp_slam, all at -13)   impact: med   blocks-8: no
  Problem: junction_beep's own brief says "information, not danger", yet it sits at the commit tier. Four identical t3 bars mean lever_clunk does not stand out as the commit sound.
  Fix: Move junction_beep to t4 (-15 LUFS).
  Done when: The Ladder shows junction_beep at -15 and only three t3 bars.
[S1-4] S1 · alarm_pressure vs passengers_scream briefs   impact: low   blocks-8: no
  Problem: Both are 2D train-wide t2 alarms, and both briefs describe a rising pitch ("rising, urgent" and "waaah with rising pitch"). alarm_pressure's avoid column names only the coal alarm.
  Fix: Change passengers_scream's sounds-like to "a cartoon crowd waaah that rises then collapses into a groan", and add "anything rising like the pressure alarm" to its avoid column.
  Done when: The passengers_scream row names a falling contour and its avoid column names alarm_pressure.
[S3-1] S3 · alarm_coal bands and the contact.png tile 2 spectrogram   impact: high   blocks-8: yes
  Problem: Bands are 0.00/0.49/0.51/0.00, so half the energy is in 150-500 Hz. The tones sit on or below the 500 Hz tick, and the phone loss of 2.51 dB is the worst in the set. Its 3D layer plays @firebox, where firebox_loop's "fire roar" fills the same low-mid band.
  Fix: Add "fundamental 500 Hz or higher" to the brief, and re-render the placeholder as a descending two-note figure at roughly 740 -> 554 Hz, or add a 1-2.5 kHz klaxon-buzz layer. Target phone band 0.75 or more and low band 0.25 or less.
  Done when: Facts shows alarm_coal phone band 0.75 or more and phone loss 1.0 dB or less, and the tile shows its main bands above the 500 Hz tick.
[S3-2] S3 · lever_clunk bands and the contact.png tile 3   impact: med   blocks-8: yes
  Problem: Bands are 0.17/0.41/0.42/0.00, so 58% of the commit sits below 500 Hz and the phone loss is 2.32 dB. The tile shows the dense energy in the bottom rows.
  Fix: Add a 1.5-3 kHz latch-click transient in the first 15 ms and high-pass at 60 Hz. Add "a bright latch click on top of the thunk" to the brief.
  Done when: Facts shows lever_clunk phone band 0.60 or more, sub 0.05 or less and phone loss 1.5 dB or less.
[S2-1] S2 · brake_hiss tail (Facts) and the closeups.png tile 2   impact: med   blocks-8: yes
  Problem: The tail is 0.4 ms, against 46-54 ms on the other one-shots, and the broadband hiss runs to the tile's last column. The file probably ends on signal, which would click. I cannot confirm a click at this zoom.
  Fix: Apply a 120 ms fade-out ending at 1.60 s, followed by 20 ms of silence.
  Done when: Facts shows brake_hiss tail of 20 ms or more, and the station_arrive envelope reaches zero before the end of the file.
[S2-2] S2 · alert_coal_low envelope on the closeups.png timeline   impact: low   blocks-8: no
  Problem: At 1:1 scale (300 px per second) the first pulse reaches full height about 0.07-0.08 s after 0 ms, while the haptic channel starts at 0. The lead is only 1.5 ms but the peak is late. This is a pixel reading and needs a zoom to confirm. I also cannot confirm at this zoom that the four even pulses carry the brief's two-note descending pitch.
  Fix: Set the first note's attack to 10 ms or less. Keep the soft ramps on pulses 2-4.
  Done when: The timeline shows alert_coal_low at full height by 0.01 s.
[S5-1] S5 · glass_smash and wind_bed "sounds like" text in the event table   impact: med   blocks-8: yes
  Problem: "a pane shattering with bright shards tinkling down" and "light wind with gentle gusts" read like stock-library descriptions. Nothing in them says incompetent train company, unlike boiler_boom's pan clang or alarm_coal's deflating trombone.
  Fix: glass_smash: "a cheap pane going with a comic crash, then one late shard dropping with a plink". wind_bed: "light wind with gentle gusts, and a loose sign or door rattling on each gust".
  Done when: Both rows in the event table carry those comic beats.
[S6-1] S6 · Stage/register line vs the 5 PLACEHOLDER files   impact: med   blocks-8: yes
  Problem: Five PLACEHOLDER_*.wav files are measured and labelled on their tiles, yet the register reads 0 final, 0 placeholder, 29 unassigned, and no licence state is recorded for them.
  Fix: Register alarm_coal, lever_clunk, brake_hiss, whistle and lobby_bed as state=placeholder, licence=self-made (synthesised), with the generator and date as proof.
  Done when: The Stage line reads "0 final, 5 placeholder, 24 unassigned" and each of the 5 rows shows a licence state.
[S6-2] S6 · emitter check in Coverage   impact: low   blocks-8: no
  Problem: Coverage says 8/8 3D sounds have an emitter role, but 13 sounds carry a 3D layer: the 8 pure 3D sounds plus the 5 hybrid 2d +3d alarms. @boiler appears only on alarm_pressure's layer, so the check does not show that it resolves.
  Fix: Count the hybrid 3D layers in the emitter check.
  Done when: Coverage reads 13/13 3D layers have an emitter role.

OVERALL: 5 (S4 Mix safety and fatigue)
NEEDS OWNER: Should glass_smash be an exception to OQ-035 (stay 3D-only because "where it is matters") or get the 2D layer from S1-2? What is the fork countdown tick rate, and should the duck hold for the whole countdown? Does the cab radio_loop (t7 Music at -25, louder than the t6 beds) count as diegetic under OQ-021 default A for the alpha? An ears check in Studio of all 5 placeholders.
KEEP: 1) The brief table's comic language and its cross-avoids: alarm_pressure avoids the coal alarm, points_throw avoids the lever clunk, queue_bell avoids the fork tick. 2) lever_clunk's 0 ms lead, with its peak landing on the lever_commit hit-stop and flash. 3) The 2d + 3d -4 dB layering on the crisis alarms and the 2 LU tier steps on the bars.