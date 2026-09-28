# Critic brief — Risky Rails sound plan (rr-soundsmith) — pass 1 (full)

## How to work
- You're reviewing work you didn't make. Be direct. Every point must rest on something visible in the images or measured under Facts.
- Your answer must be your 3rd message at the latest. Message 1: open this file and every image the prompt names, all together, as parallel tool calls in one message. Message 2: your answer. Only if a number you need is missing may you take one extra look in message 2 (one crop or one more image); then answer in message 3.
- Opening files or images one at a time is a failure. So is opening files not named in the prompt, running scripts, or reading source code.
- If a detail needs a zoom you can't get, say so in the issue instead of guessing.
- Keep your reasoning proportionate. Settle each criterion from the evidence and move on; don't draft the answer twice. Your thinking is the biggest cost of a pass.

## Brief
- Purpose: the event -> sound plan and mix: each sound says what happened and how urgent, alarms reach the other carriage, the hierarchy holds on a phone, placeholders mark timing until final audio arrives.
- Audience: friend groups 16+ (age-checked) at launch; most players and ad traffic are on phones.
- Player view: you cannot hear anything. The images are waveforms, spectrograms, a loudness ladder, phone-speaker loss and event timelines against rr-game-feel's channels; Facts has the measurements and the event and brief table (phase, events, space, must say, sounds like, avoid). Judge the plan and the numbers, never 'how it sounds'; the owner's ears are the final check.
- Stage: 5 of 29 sounds have a file in this pass (5 synthesised PLACEHOLDERs, 0 owner files); register: 0 final, 0 placeholder, 29 unassigned. Sounds without a file are judged on the event and brief table.
- Fixed constraints: crisis alarms first: in a group they tell someone in the other carriage what is wrong; slapstick lands through sound; wheel sound follows Speed; tone an incompetent train company: under-resourced but still operating; slapstick safety failures, not grim horror; not a western, not zombies, not horror, not a train simulator. Licences: only owner-uploaded audio (self-made, commissioned, CC0 or bought with a game licence, proof recorded) or Roblox-licensed Creator Store audio (by Roblox or its partners).
- Owner worries / already decided: alarms first (canon). Open decisions, defaults in use: OQ-021 Audio identity (missing canon) (default A: Diegetic only for the alpha (whistle, hiss, wheels, alarms), no music during ); OQ-035 Crisis alarms: heard train-wide or at the source? (default A: 2D train-wide at full level plus a quieter positional layer at the source (bo); OQ-036 Creator Store audio uploaded by the community: allowed? (default A: no; only owner uploads and Creator Store audio published by Roblox or its lic); pending:lobby-audio Lobby audio: music bed or diegetic depot ambience? (default A: diegetic Depot Lobby bed only (resting loco breathing, lamp buzz, birds), no ); OQ-031 Lever input: how does a player pull the lever? (default A: walk up to the lever; a ProximityPrompt opens the lever console; drag the kno); OQ-013 Boiler pressure numbers (missing canon) (default A: Tune in Studio from the coal numbers and record the result with add-fact.); OQ-012 HUD alert IDs: per fault or generic BREAKDOWN? (default A: Per-fault IDs (WindowBroken, ElectricsDown, ...) with new texts the owner app); OQ-003 Currency: coins, "$" or fare? (default C: Data name Coins, player-facing "$" as already built; "fare" is the in-run eve). Placeholder timbre is not the brief: judge the plan, levels, timing and distinctness, and the brief text for style.
step 2: pre-answered (canon via rr-bible; owner away; assumptions are the defaults above)

## Facts (measured)
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

## Images
- `contact.png` 792x629 (0.50 MP)
  1. Ladder — 1:1 true size
  2. alarm_coal — fit x1.00
  3. lever_clunk — fit x1.00
- `closeups.png` 792x328 (0.26 MP)

## Rubric
### Scoring rules
Score each criterion 0–10. The anchors at 4, 7 and 9 are fixed. Interpolate between them: a 5 or 6 sits between the 4 and 7 descriptions, and an 8 meets all of 7 with no more than one gap from 9. The bar for "£500 commission" work is **8 on every criterion**. **The overall score is the lowest criterion score, never the average.**

1. **Anchor + evidence, or it doesn't count.** Every score cites the anchor it meets, names the view or measurement that shows it, and lists the issues holding it below the next anchor. A score with no evidence line is void.
2. **A score of 8 or more needs zero open issues tagged `blocks-8` on that criterion.** If you raise any issue that stops a criterion reaching 8, tag it `blocks-8` and keep the score at 7 or below.
3. **Score what is visible or measured, not what is intended.** Don't use source code, part names or the maker's notes to lift a score. They are only for naming fixes.
4. **Don't grade relative to earlier versions.** "Better than before" is not a score. Only the anchors are.
5. **Placeholders the owner must supply don't lower a score** if they are clearly marked, for example a seating layout the owner will specify. Unmarked fake content does lower it.
6. **Put your score where the evidence falls.** Don't round up to reach a bar. If you are torn between two whole numbers, score the lower one and name the evidence that would move it up.
7. **The player's view decides.** Judge first from the views that show the work as it is really seen: the POV cameras, the 400 px game-distance render, the real-size UI frame. Detail visible only in a construction close-up can't lift a score the player can't see.
8. **Scores at the bar are sticky.** A criterion that an earlier pass scored at or above the bar (listed under Standing scores) can only drop if you either (a) cite a part that changed since that pass, or (b) state a missed `blocks-8` issue with pixel or measurement evidence and say why it was missed, for example because it only shows in a view added this pass. Otherwise keep the standing score.

### Criteria scored this pass: S1, S2, S3, S4, S5, S6
### S1 Signal and hierarchy
Does each event get a sound that says what happened and how urgent, and do more important tiers sit louder (fail > crisis > commit > reward > UI > loops)?
- **4:** Tiers overlap on the ladder, a routine sound sits above a crisis alarm, or two crisis alarms look alike in the tiles (same rhythm, same band) so the other carriage could not tell them apart.
- **7:** The ladder steps in order and each crisis alarm has its own rhythm or band; one pair is close (under 2 LU apart across tiers) or one alarm's shape resembles another's.
- **9:** Clean steps by tier on the bars and on the phone dots, every crisis alarm distinct in both rhythm and spectrum, and the lever commit and the fail are the two sounds that stand out.

### S2 Timing and envelope
Attack against the feel beat (hit-stop, kick, flash at 0 ms), length against the moment, tails, loop seams.
- **4:** Sounds start late (lead silence), long tails run past the moment or into the next event, or a loop shows a seam.
- **7:** Attacks land on the feel beat and lengths suit their moments; one sound is too long, too slow to peak, or one tail lingers.
- **9:** Every impact peaks within 10 ms of its feel beat, lengths match the moment (UI under 0.1 s, alarms under the ticket life), tails are clean, loops seamless.

### S3 Clarity on a phone
Judge the dots on the ladder, the phone-loss numbers and the spectrogram bands (ticks mark 500 Hz and 4 kHz).
- **4:** A crisis or commit sound lives mostly below 150 Hz and drops more than 6 dB on a phone, or phone dots invert the hierarchy.
- **7:** Alarms and commits keep their energy in 0.5-4 kHz; one sound loses more than its limit or two concurrent sounds share the same band.
- **9:** Every tier-1 to tier-3 sound survives a phone speaker within 3 dB, the hierarchy holds on the dots, and concurrent sounds sit in different bands.

### S4 Mix safety and fatigue
Peaks, ducking, voice limits and repetition over a 12-minute trip.
- **4:** Peaks over -1 dBTP or clipping, ducking that pumps (long attack, instant release) or removes the ambience entirely, no voice caps, or frequent sounds without variations or cooldowns.
- **7:** Safe peaks and sensible ducking; one frequent sound (click, shovel, glass) lacks variations or a cooldown, or one duck is deeper than it needs.
- **9:** Every file within the peak ceiling, ducks of 3-14 dB with short attacks and smooth releases, caps and cooldowns on every repeatable sound, variations wherever a sound repeats within a minute.

### S5 Style match
See the shared House style block, applied to sound through the brief text and the placeholder plan: slapstick lands through sound, chunky and toy-like, never horror.
- **4:** The plan reads grim or realistic: screams of pain, horror stings, war explosions, modern diesel horns on a steam alpha.
- **7:** Comic and physical on most sounds; one brief is generic (a stock app notification, a cinematic boom).
- **9:** Every brief sounds like the same incompetent train company: clunky levers, droopy alarms, cartoon bangs, never cruel.

### S6 Coverage and polish
- **4:** Events with no sound, sounds no event plays, missing licence or placeholder labels, or 3D sounds without emitter roles.
- **7:** Full coverage with one gap (an info event silent, a missing variation, an unlabelled placeholder in Facts).
- **9:** Every event mapped, every sound briefed, licence states clean, placeholders labelled, emitters named, nothing left over.

### House style
Risky Rails house style, from the project's thumbnail formula and the approved diesel "23":
- hazard yellow/black against teal-cream or mustard livery
- ink-black details and red buffer beams
- chunky, readable, slightly toy-like forms with capped-post yellow rails
- never Dead Rails' sepia/orange desert look or Land or Die's blue-sky/white-plane look

For work outside Risky Rails, the brief's "House style" line replaces this block.

### Issue format
Every issue, every pass:
```
[C#-n] <criterion> · <where: part/element and view>   impact: high|med|low   blocks-8: yes|no
  Problem: <what is visible or measured>
  Fix: <exact change: part name + value, or element + value>
  Done when: <an objective check a later pass can verify from the renders or measurements>
```
Rank issues by impact on the lowest-scoring criteria first. Generic notes such as "improve detail", "add polish" or "make it pop" are banned. If you can't name the part and the value, drop the issue.

## Output
Output exactly:
```
FIRST READ: <eye path, and what it reads as vs the brief — 2 lines>
SCORES:
<C#> <name>: <n>/10 — meets <anchor> because <evidence: view + what's visible/measured>; below <next anchor> because <issue ids>
ISSUES (ranked by impact, lowest-scoring criteria first; issue format):
...
OVERALL: <lowest score> (<criterion>)
NEEDS OWNER: <decisions only the owner can make, or none>
KEEP: <at most 3 things that must survive the fixes>
```
