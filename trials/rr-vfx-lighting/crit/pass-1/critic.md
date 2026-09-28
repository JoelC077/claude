# Critic brief — Risky Rails preset pack look-dev board: steam, chimney smoke, brake sparks, coal dust + grassland day, dusk, night run (rr-vfx-lighting) — pass 1 (full)

## How to work
- You're reviewing work you didn't make. Be direct. Every point must rest on something visible in the images or measured under Facts.
- Your answer must be your 3rd message at the latest. Message 1: open this file and every image the prompt names, all together, as parallel tool calls in one message. Message 2: your answer. Only if a number you need is missing may you take one extra look in message 2 (one crop or one more image); then answer in message 3.
- Opening files or images one at a time is a failure. So is opening files not named in the prompt, running scripts, or reading source code.
- If a detail needs a zoom you can't get, say so in the issue instead of guessing.
- Keep your reasoning proportionate. Settle each criterion from the evidence and move on; don't draft the answer twice. Your thinking is the biggest cost of a pass.

## Brief
- Purpose: one look-dev board for a Roblox-native preset pack: running effects (chimney steam, coal smoke, brake sparks, a coal-shovel dust burst) and three lighting looks (grassland day, dusk, Night Running) that must each read at a glance on a phone. Judge the board as the owner will use it: can he tell what each preset looks like, and does each preset do its job?
- Audience: friend groups 16+ (age-checked) at launch; most players and ad traffic are on phones (phone 844 x 390 landscape).
- Player view: players stay on the train (roofs, coaches, cab); third-person eye 9.5 studs above the floor, first-person 4.5, vertical FOV 70. The train never moves; the world scrolls at Speed 20/35/50 studs/s, so effects drift back with Workspace.GlobalWind.
- Stage: look-dev presets, pass 1 (no fixes yet); the images are preview approximations (see the Limits line in Facts), judged as intent: shape, colour, value, readability, not engine-exact pixels.
- Fixed constraints: tone an incompetent train company: under-resourced but still operating; slapstick safety failures, not grim horror; not a western, not zombies, not horror, not a train simulator. Never sepia, orange-desert, western or zombie looks (Dead Rails) or blue-sky plus white-plane looks (Land or Die); no uniform saturated Roblox-default grass green; red only for the one danger signal (style.dont.red_decoration). Haze stays: it hides the streamer's spawn edge (tech.lighting.atmosphere = Density about 0.3, colour tinted grey-green). Colours are rr-bible tokens or declared effect colours. Phone budget and priorities are in Facts (crisis signals keep full rate on phones; ambience drops first).
- Owner request and defaults: the owner asked for exactly this pack. Brake sparks and the dusk look have no canon yet (assumed; braking itself is canon, gameplay.run.brake_formula). Night = the Night Running modifier look (proposed); dusk has no slot in the run under OQ-026 default C. Phone budget OQ-029 default. Built-in textures stand in for custom flipbooks. Coal dust fires inside the cab, which no preview camera sees: judge it from its time strip.
step 2: pre-answered (canon via rr-bible; owner away)

## Facts (measured)
# Look-dev board facts: pack = steam_chimney, smoke_chimney, sparks_brake, coal_dust; looks grassland.day, .dusk, .night

Player view: roof3p = standing on a coach roof, eye 9.5 studs up (tech.camera.eye_3p); door1p = leaning out of a coach doorway, eye 4.5 (tech.camera.eye_1p); vertical FOV 70.0 (tech.camera.fov_v). The train never moves (identity.pillars.stable_train).

| look | cam | sun elev | luma | clip/crush % | train vs world | ground (HSL sat) | sky | spawn-edge fog | bands |
|---|---|---|---|---|---|---|---|---|---|
| grassland.day | roof3p | 38.8 | 155.3 | 0.0/0.0 | 3.56:1 | #8DA15B (0.28) | #ACBEAE | 0.956 at 2048 | none |
| grassland.day phone | roof3p | 38.8 | 156.7 | 0.0/0.0 | 3.69:1 | #91A55D (0.28) | #ACBEAE | 0.956 at 2048 | none |
| grassland.dusk | roof3p | 1.7 | 73.4 | 0.0/0.0 | 1.92:1 | #444937 (0.14) | #5E5A63 | 0.968 at 2048 | none |
| grassland.dusk phone | roof3p | 1.7 | 74.4 | 0.0/0.0 | 1.98:1 | #454A38 (0.14) | #5E5A63 | 0.968 at 2048 | none |
| grassland.night | roof3p | -47.8 (moon) | 30.3 | 0.0/0.49 | 1.64:1 | #304637 (0.18) | #01030F | 0.969 at 2048 | none |
| grassland.night phone | roof3p | -47.8 (moon) | 30.3 | 0.0/0.49 | 1.65:1 | #304637 (0.18) | #01030F | 0.969 at 2048 | none |
| grassland.day@door1p | door1p | 38.8 | 110.4 | 0.0/14.66 | 2.46:1 | #7B9148 (0.34) | #A9BDAF | 0.956 at 2048 | none |
| grassland.dusk@door1p | door1p | 1.7 | 59.6 | 0.0/14.99 | 1.2:1 | #38412E (0.17) | #5B5862 | 0.968 at 2048 | none |
| grassland.night@door1p | door1p | -47.8 (moon) | 39.3 | 0.0/26.17 | 1.23:1 | #354D39 (0.18) | #00030E | 0.969 at 2048 | none |

Checks against canon:
- spawn-edge fog: canon keeps haze to hide the streamer's spawn edge (tech.lighting.atmosphere, tech.streaming.window); below 0.9 the edge may show.
- ground saturation: canon says nothing above about 45% (style.material.ground_value).
- bands: frame and sky means tested against the Dead Rails sepia and Land or Die blue-sky bands (style.dont.*).
- train vs world: relative-luminance ratio of the train to everything around it in the same frame.


## Effects (side strips at Speed 35; phone live uses the budget formula at full rate)

| preset | kind | priority | anchor | phone live (budget formula) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|
| steam_chimney | loop | 2 | Chimney | 40 | 38/38/38 | 3.66 | av.vfx.speed_link, gameplay.speed.drives |
| smoke_chimney | loop | 3 | Chimney | 10 | 15/15/15 | 2.61 | av.vfx.speed_link |
| sparks_brake | loop | 2 | BrakeShoe | 42 | 29/29/29 | 23.7 | gameplay.run.brake_formula, gameplay.crisis.pressure |
| coal_dust | burst | 2 | Firebox | 15 | 20/20/11/20 | 23.7 | gameplay.crisis.firebox, gameplay.fuel.shovel_pct |

## Pack POV composites (Speed = gameplay.speed.fast 50; loops at steady state; the look's fx_on presets added)

| composite | tier | live | hidden by geometry | overdraw max | screen covered |
|---|---|---|---|---|---|
| pov_grassland.day | pc | 111 | 44 | 27 | 4.9% |
| pov_grassland.day_door1p | pc | 111 | 69 | 4 | 0.4% |
| pov_grassland.day.phone | phone | 75 | 31 | 19 | 2.0% |
| pov_grassland.dusk | pc | 111 | 44 | 27 | 4.9% |
| pov_grassland.dusk_door1p | pc | 111 | 69 | 4 | 0.4% |
| pov_grassland.dusk.phone | phone | 75 | 31 | 19 | 2.0% |
| pov_grassland.night | pc | 111 | 44 | 27 | 4.9% |
| pov_grassland.night_door1p | pc | 111 | 69 | 4 | 0.4% |
| pov_grassland.night.phone | phone | 75 | 31 | 19 | 2.0% |

- coal_dust fires inside the cab (anchor Firebox): no preview camera is in the cab, so it appears only in its time strip.
- sparks_brake sits at the loco wheels at rail level: from coach B's roof (roof3p) the train body hides it; door1p sees about half.

## Phone budget, pack-relevant sets (all PC sets within)

- phone cruise: steady 54, peak 54, fill 3183 stud^2, lights 3 -> within
- phone arrival_brake: steady 96, peak 96, fill 3200 stud^2, lights 3 -> within
- phone pressure_brake: steady 132, peak 147, fill 3541 stud^2, lights 4 -> within
- phone night_brake: steady 96, peak 111, fill 3226 stud^2, lights 5 -> within
- phone crisis_stack_brake: steady 182, peak 197, fill 3546 stud^2, lights 6 -> within

Limits: Previews are approximations, not Roblox: Cycles + a numpy post (filmic curve, Atmosphere fog from depth, bloom, sun rays, ColorCorrection). Skybox, Future light falloff and Roblox tone mapping are not modelled; phone variants assume no shadows and no Bloom/SunRays (tech.lighting.post_low_quality). Studio test pending (owner).
Limits: Effects are simulated from the preset data with Roblox ParticleEmitter rules; textures are procedural stand-ins for the built-ins; particles are not lit by the scene beyond a LightInfluence factor; lights show as glow dots only; drift = Workspace.GlobalWind at train speed. Studio test pending (owner).

## Images
- `contact.png` 786x1182 (0.93 MP)
  1. POV roof3p grassland.day, pack at Speed 50 (steam, smoke, brake sparks) — 1:1 true size
  2. POV roof3p grassland.dusk (+headlamp) — fit x0.50
  3. POV roof3p grassland.night (+headlamp) — fit x0.50
  4. POV door1p grassland.dusk (+headlamp) — fit x0.50
  5. POV roof3p night PHONE fallback + phone rates — fit x0.50
  6. sparks_brake side strip, Speed 35 — fit x0.50
  7. coal_dust burst time strip — fit x0.37
- `closeups.png` 786x726 (0.57 MP)

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

### Criteria scored this pass: B1, B2, B3, B4, B5, B6
### B1 Job and hierarchy
- **4:** Unclear what it's for, or the key action or information is buried.
- **7:** The job is clear, but a second element competes with the focal point.
- **9:** One focal point that does the job in a glance, with a clear order after it.

### B2 Legibility at real size
Judge at the real-size frame on the contact sheet (1:1): a 200 px tile, a phone, a PC screen, or an in-world sign at its POV size. Measured contrast, text sizes and targets are under Facts.
- **4:** Key text is unreadable at the real viewing size, or fails contrast.
- **7:** Everything is readable, but secondary text is small or low-contrast.
- **9:** Everything reads at the real size, and all text passes WCAG AA as measured.

### B3 Layout and spacing
- **4:** No grid, crowded, clipped or overlapping.
- **7:** A consistent grid with a few uneven gaps or alignments.
- **9:** Shared edges and consistent gaps, with grouping that explains the content.

### B4 Colour
- **4:** Clashing or muddy, with meaning carried only by colour.
- **7:** A disciplined palette with one or two off-palette or unintended accents.
- **9:** One dominant hue and one accent, with every colour used on purpose.

### B5 Style match
See the shared House style block, applied to type, palette and iconography. The anchors are A6's:
- **4:** It looks like it belongs to a different game: wrong palette, type or icon language.
- **7:** It shares the palette and some detail language, but one element breaks the family (a different lettering face, icon style or level of detail).
- **9:** You'd assume the same artist made it and the approved assets together.

### B6 Polish
- **4:** Placeholders, typos, inconsistent components.
- **7:** Finished, with small inconsistencies.
- **9:** Consistent to the pixel.

### House style
Risky Rails house style, from the project's thumbnail formula and the approved diesel "23":
- hazard yellow/black against teal-cream or mustard livery
- ink-black details and red buffer beams
- chunky, readable, slightly toy-like forms with capped-post yellow rails
- never Dead Rails' sepia/orange desert look or Land or Die's blue-sky/white-plane look

For work outside Risky Rails, the brief's "House style" line replaces this block.

### Motion note
Hairline repeated detail (cresting, balusters, slats, thin trim, 1 px strokes) flickers and crawls when the camera or the world moves, even when a still render looks clean. If the brief says the work is seen in motion (a moving camera, a scrolling world, a sign passed at speed) and repeated detail is under 2 px wide at the 400 px or real-size view, raise it as a `blocks-8` issue: thicken it to at least 5 px, merge it into one solid shape, or drop it.

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
