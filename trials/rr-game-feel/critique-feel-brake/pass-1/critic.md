# Critic brief — Risky Rails feel presets: actions (rr-game-feel) — pass 1 (full)

## How to work
- You're reviewing work you didn't make. Be direct. Every point must rest on something visible in the images or measured under Facts.
- Your answer must be your 3rd message at the latest. Message 1: open this file and every image the prompt names, all together, as parallel tool calls in one message. Message 2: your answer. Only if a number you need is missing may you take one extra look in message 2 (one crop or one more image); then answer in message 3.
- Opening files or images one at a time is a failure. So is opening files not named in the prompt, running scripts, or reading source code.
- If a detail needs a zoom you can't get, say so in the issue instead of guessing.
- Keep your reasoning proportionate. Settle each criterion from the evidence and move on; don't draft the answer twice. Your thinking is the biggest cost of a pass.

## Brief
- Purpose: game feel (juice) per event: camera shake and kicks, hit-stop, UI punch, flashes, FOV kicks and haptics that say what happened and how big, on a phone, without hurting play.
- Audience: friend groups 16+ (age-checked) at launch; most players and ad traffic are on phones (phone 844 x 390 landscape).
- Player view: players stay on the train; third-person eye 9.5 studs, first-person 4.5, vertical FOV 70. The train never moves; the world scrolls (the train never moves; the world scrolls, so players stand on it with zero jitter). The images are curve plots, a feel matrix and mock phone frames at the peak of each event: judge timing, curve shape, magnitude and hierarchy as intent, not engine pixels.
- Stage: feel presets before any Studio playtest; the runtime uses the same formulas (Limits in Facts).
- Fixed constraints: tone an incompetent train company: under-resourced but still operating; slapstick safety failures, not grim horror; not a western, not zombies, not horror, not a train simulator; interactions are physical and visible (lever, shovel, wrench), never a quiet menu or vote; failure is funny and chaotic, never punishing or arbitrary. Red only for the danger signal. Flashes: 3 per second (full-screen and vignette flashes: at most 3 in any 1 s, peak opacity 0.35 (red 0.25), off with the flashes setting; element lamps are exempt). Reduce motion: motion off, meaning kept. Hit-stop: local and cosmetic, at most 150 ms.
- Owner worries / already decided: feel must scale by tier (fail > crisis > commit > reward > UI); the lever is the signature moment (identity.pillars.fork_bet). Open, on defaults: OQ-031 lever input (drag console), OQ-032 feel settings (Roblox Reduce Motion only for the alpha), OQ-013 pressure numbers. Sound is not in these images (cues name sounds for a later skill); judge the visual and haptic channels only.
- Mission focus: hard brake is assumed (OQ-037 default A): the communication-cord emergency stop or the driver's brake at a pressure redline. The train never moves, so the lurch is camera, FOV, a dark vignette and haptics only; it must stay under the lever commit (the signature) and every crisis in loudness. The feel matrix FOV column prints magnitudes with a plus sign: the brake kick is -4 deg (the view narrows), see the timeline.
step 2: pre-answered (canon via rr-bible; owner away)

## Facts (measured)
# Facts: feel presets, group actions (measured by feel.py)

- Phone 844 x 390, FOV 70; camera px = rotation at the screen centre + translation of geometry 8 studs away + half the roll at the screen edge (upper bound).
- Limits: camera px by tier {'1': 40, '2': 28, '3': 18, '4': 10, '5': 4}; hit-stop <= 150 ms; screen flash <= 0.35 (red 0.25), <= 3/s; events <= 3.0 s (fail 3 s).
- Hero hard_brake: peak frame at t=0.15 s. Filmstrip frames are the same mock at six times.

- hard_brake (tier 3, all): camera 3.4 px (roll 0.0 deg, kick 0.696 deg), FOV 4.0, hit-stop 0 ms, screen flash 0.12, haptic 0.6 for 600 ms, UI punch 0% / 0.0 px, lasts 2.1 s, loudness 0.167. Reduce motion: camera 0.0 px; reads through haptic, flash, cue.

- Sustained rumble (constant while running): Speed at max 1.66 px, pressure at redline 1.66 px, both capped 2.89 px (limit 3 px).
- Limits of these images: the plate is a mock (flat colours, default font, no Roblox lighting); easing uses Penner forms (compare with a Studio dump: feel.py plot curves --compare); sound cues are not shown; the world keeps scrolling during hit-stop because the server moves it. Studio test pending (owner).

## Images
- `contact.png` 1564x700 (1.09 MP)
  1. hard_brake peak frame (phone true size) + feel matrix — 1:1 true size
  2. hard_brake timeline (dashed: reduce motion) + filmstrip — 1:1 true size
- `closeups.png` 512x260 (0.13 MP)

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

### Criteria scored this pass: G1, G2, G3, G4, G5, G6
### G1 Signal and hierarchy
Does each event say what happened and how big, and do bigger events feel bigger (fail > crisis > commit > reward > UI)?
- **4:** Events feel alike, a routine event outshouts a crisis in the matrix, or you cannot tell from the frame and lanes what kind of moment it is.
- **7:** Tiers read in order and each event has a clear main channel; one pair is too close in loudness or one event's channels fight (two peaks competing).
- **9:** Every event has one unmistakable signature channel, loudness steps cleanly by tier in the matrix, and the lever commit and the fail are the two moments you remember.

### G2 Timing and curves
Anticipation, impact, settle: durations, easing choice, overshoot, spring damping, delays between channels.
- **4:** Linear or mushy curves on impacts, springs that ring on or stop abruptly, delays that make channels land at different moments, or everything lasting the same time.
- **7:** Curves suit their jobs (fast out, eased settle; overshoot where it sells weight) with one event too slow, too floaty or one channel landing off the beat.
- **9:** Every curve is chosen for its moment: impacts land within 1-2 frames across channels, settles are quick and clean, overshoot and hit-stop are used sparingly where they add weight.

### G3 Comfort and accessibility
Motion sickness, photosensitivity, 12-minute sessions, the reduce-motion variant.
- **4:** Constant shake or roll a player feels all trip, a full-screen flash near strobe rate or bright red, hit-stop that feels like lag, or a reduce-motion variant that loses the meaning.
- **7:** Within the limits in Facts; one event is harsher than it needs to be (roll, flash peak or duration) or one reduce-motion variant is weak.
- **9:** Comfortable for a whole trip on a phone: sustained rumble is barely there, flashes are brief and rare, and every reduce-motion lane still carries the event through colour, scale or haptics.

### G4 Phone read
Judge at the true-size phone frame and the pixel numbers in Facts.
- **4:** UI punches too small to see at 844x390, camera moves so large the HUD or interaction points leave the thumb's reach, or effects hide the lever, gauges or tickets.
- **7:** Readable on the phone with one event too subtle (under a few pixels) or one too big for the screen.
- **9:** Every event reads at phone size in its first 150 ms, UI punches are visible without covering neighbours, camera motion stays inside a thumb's comfort.

### G5 Style match
See the shared House style block, applied to motion: slapstick, physical, chunky, toy-like.
- **4:** Feels like another game: grim slow-motion, horror red strobe, realistic handheld camera, or floaty mobile-app easing on physical moments.
- **7:** Physical and funny on most events; one feels generic (a stock app bounce, a cinematic shake that is too serious).
- **9:** Every event feels like the same incompetent train company: heavy clunks, cartoon overshoot, comic timing on fails, never cruel.

### G6 Polish and consistency
- **4:** Families disagree (tickets enter three different ways), springs of the same kind have random numbers, channels stack into noise when two events overlap.
- **7:** Consistent families with one outlier; small issues (a tail that lingers, a haptic that does not match its visual).
- **9:** Shared curves per family, clean stacking (limiter, cooldowns), haptic waveforms match the visual beats, nothing lingers after the moment.

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
