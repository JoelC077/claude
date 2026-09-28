# Critic brief — Risky Rails look-dev pack (rr-vfx-lighting) — pass 1 (full)

## How to work
- You're reviewing work you didn't make. Be direct. Every point must rest on something visible in the images or measured under Facts.
- Your answer must be your 3rd message at the latest. Message 1: open this file and every image the prompt names, all together, as parallel tool calls in one message. Message 2: your answer. Only if a number you need is missing may you take one extra look in message 2 (one crop or one more image); then answer in message 3.
- Opening files or images one at a time is a failure. So is opening files not named in the prompt, running scripts, or reading source code.
- If a detail needs a zoom you can't get, say so in the issue instead of guessing.
- Keep your reasoning proportionate. Settle each criterion from the evidence and move on; don't draft the answer twice. Your thinking is the biggest cost of a pass.

## Brief
- Purpose: a Roblox-native look-dev pack (effects: steam_chimney, smoke_chimney, sparks_brake, coal_dust; looks: grassland.day, grassland.dusk, grassland.night, set through Lighting, Atmosphere, ColorCorrection, Bloom and SunRays) that makes each game state read at a glance on a phone. What each effect is for: steam_chimney: chimney steam; rate follows Speed (idle to gameplay.speed.fast); smoke_chimney: coal smoke mixed into the steam; darker, fewer, slower puffs; rate follows Speed; sparks_brake: brakes on (station arrival, pressure-crisis brake): fans of sparks thrown out past both body sides and back from the loco wheels, plus a ground glow; rate and glow follow Speed so they die as the train stops. Effect proposed: canon has the brake, not brake sparks; coal_dust: one shovel into the firebox: dust puff, embers and a firebox flare.
- Audience: friend groups 16+ (age-checked) at launch; most players and ad traffic are on phones (phone 844 x 390 landscape).
- Player view: players stay on the train (roofs, coaches, cab); third-person eye 9.5 studs above the floor, first-person 4.5, vertical FOV 70. The train never moves; the world scrolls at Speed 20/35/50 studs/s, so effects drift back with Workspace.GlobalWind.
- Stage: look-dev presets; the images are preview approximations (see the Limits lines in Facts), judged as intent: shape, colour, value, readability, not engine-exact pixels. The train is a stand-in (livery open, OQ-025): judge the looks and effects, not the train's paint. Strips are construction views; judge signal from the POV tiles.
- Fixed constraints: tone an incompetent train company: under-resourced but still operating; slapstick safety failures, not grim horror; not a western, not zombies, not horror, not a train simulator. Never sepia, orange-desert, western or zombie looks (Dead Rails) or blue-sky plus white-plane looks (Land or Die); no uniform saturated Roblox-default grass green; red only for the one danger signal (style.dont.red_decoration). Haze stays: it hides the streamer's spawn edge (tech.lighting.atmosphere = Density about 0.3, colour tinted grey-green). Colours are rr-bible tokens or declared effect colours. Phone budget and priorities are in Facts (crisis signals keep full rate on phones; ambience drops first).
- Owner worries / already decided: crisis effects must be the loudest thing in frame (sound carries slapstick too, av.audio.slapstick). Open, on defaults: OQ-026 Time of day and when the lighting look changes (default C); OQ-029 Phone budget for effects and lighting (default A). Placeholders: built-in textures stand in for custom flipbooks (asset upload is the owner's).
step 2: pre-answered (canon via rr-bible; owner away)

## Facts (measured)
# Look-dev board: steam_chimney, smoke_chimney, sparks_brake, coal_dust, grassland.day, grassland.dusk, grassland.night (2026-09-28)

Presets from /home/user/claude/trials/rr-vfx-lighting/retrial/fx. Tiles show the player's views (POV composites: particles over the lit plate); strips on closeups.png are construction views for shape and timing only.

## Looks

Cameras: roof3p = coach B roof, eye 9.5 (tech.camera.eye_3p); door1p = leaning out of coach A's doorway, eye 4.5 (tech.camera.eye_1p); cab1p = loco cab facing the firebox, eye 12.0 above rail (tech.camera.cab_view); coach1p = inside coach A facing the power box. FOV 70.0; phone renders at 844x390 (tech.ui_platform.phone). Stand envelope: gauge 8, body 17.4 wide, floor 5, roof 14 (tech.units.*, OQ-030); stand-in train: navy, cream band and interiors, hazard-yellow roof rails (style.form.rails); livery open (OQ-025).

| look | cam | sun elev | luma | clip/crush % (train) | train vs world | hazard vs world | ground (sat) | sky | spawn-edge fog | bands |
|---|---|---|---|---|---|---|---|---|---|---|
| grassland.day | roof3p | 38.8 | 149.4 | 0.0/0.0 (0.0) | 3.25:1 | 1.26:1 | #93A660 (0.28) | #ACBEAE | 0.956 at 2048 | none |
| grassland.day phone | roof3p | 38.8 | 152.9 | 0.0/0.0 (0.0) | 3.18:1 | 1.24:1 | #94A761 (0.28) | #ADBEAE | 0.956 at 2048 | none |
| grassland.day@door1p | door1p | 38.8 | 114.3 | 0.0/4.58 (10.5) | 2.04:1 | None:1 | #728942 (0.35) | #AABDAF | 0.956 at 2048 | none |
| grassland.dusk | roof3p | 1.7 | 84.5 | 0.0/0.0 (0.0) | 2.28:1 | 1.98:1 | #6C6849 (0.2) | #685A60 | 0.968 at 2048 | none |
| grassland.dusk phone | roof3p | 1.7 | 88.2 | 0.0/0.0 (0.0) | 2.37:1 | 1.87:1 | #6F6A49 (0.2) | #685B60 | 0.968 at 2048 | none |
| grassland.dusk@door1p | door1p | 1.7 | 85.1 | 0.0/0.02 (0.04) | 1.11:1 | None:1 | #62613C (0.24) | #66595F | 0.968 at 2048 | none |
| grassland.night | roof3p | -47.8 (moon) | 28.6 | 0.0/0.55 (0.4) | 1.57:1 | 1.99:1 | #33483B (0.17) | #01030F | 0.969 at 2048 | none |
| grassland.night phone | roof3p | -47.8 (moon) | 30.1 | 0.0/0.44 (0.3) | 1.55:1 | 2.04:1 | #33493B (0.17) | #010410 | 0.969 at 2048 | none |
| grassland.night@door1p | door1p | -47.8 (moon) | 48.2 | 0.0/6.18 (11.0) | 1.05:1 | None:1 | #39513C (0.17) | #00030E | 0.969 at 2048 | none |
| grassland.day@cab1p | cab1p | 38.8 | 65.5 | 0.95/27.16 (27.99) | 3.45:1 | None:1 | #8CA158 (0.3) | None | 0.956 at 2048 | none |

Checks against canon: spawn-edge fog >= 0.9 hides the streamer's spawn edge (tech.lighting.atmosphere, tech.streaming.window); ground saturation <= 0.45 (style.material.ground_value); bands = frame and sky means tested against the Dead Rails sepia and Land or Die blue-sky bands (style.dont.*); contrast = relative luminance ratio in the same frame.

Flags (maker heuristics, not canon: train vs world under 2:1 fades on a dim phone; crush over 5% loses shape):
- grassland.dusk@door1p (door1p): train vs world 1.11:1 < 2:1
- grassland.night (roof3p): train vs world 1.57:1 < 2:1
- grassland.night phone (roof3p): train vs world 1.55:1 < 2:1
- grassland.night@door1p (door1p): train vs world 1.05:1 < 2:1; crush 6.18% > 5% (train 11.0%)
- grassland.day@cab1p (cab1p): crush 27.16% > 5% (train 27.99%)

Limits: Previews are approximations, not Roblox: Cycles + a numpy post (filmic curve, Atmosphere fog from depth, bloom, sun rays, ColorCorrection). Skybox, Future light falloff and Roblox tone mapping are not modelled; phone variants assume no shadows and no Bloom/SunRays (tech.lighting.post_low_quality). The train is a stand-in (livery open, OQ-025). Studio test pending (owner).

## Effects

Side strips: steady state at Speed 35.0 (gameplay.speed.normal) on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar (tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.

| preset | kind | priority | anchor | start | live phone / pc (budget formula, full rate) | sim live (strip) | px/stud | canon / OQ |
|---|---|---|---|---|---|---|---|---|
| steam_chimney | loop | 2 | Chimney | on | 40 / 58 | 38/38/38 | 3.66 | av.vfx.speed_link, gameplay.speed.drives |
| smoke_chimney | loop | 3 | Chimney | on | 10 / 21 | 15/15/15 | 2.61 | av.vfx.speed_link |
| sparks_brake | loop | 2 | BrakeShoe | off | 90 / 128 | 68/68/68 | 15.84 | gameplay.run.brake_formula, gameplay.crisis.pressure |
| coal_dust | burst | 2 | Firebox | event | 15 / 20 | 20/20/11/20 | 17.78 | gameplay.crisis.firebox, gameplay.fuel.shovel_pct |

POV composites: particles over the lookdev plate from the same camera (PC 768x432, phone 844x390 at phone rates); loops at steady state at Speed gameplay.speed.fast, bursts shown t s after they fire. Per preset: visible/live, h = hidden by the train or ground, o = off-screen, share of the screen, then drawn alone over the plate: mean luma change / 90th-percentile luma change.

| POV | look | cam | tier | overdraw max/p95 | screen | per preset |
|---|---|---|---|---|---|---|
| grassland.day_roof3p | grassland.day | roof3p | pc | 30/19 | 3.7% | steam 50/50 h0 o0 1.74% +20/39; smoke 16/16 h0 o0 3.25% -17/34; sparks 3/92 h89 o0 0.00% +9/11 |
| grassland.day_roof3p.phone | grassland.day | roof3p | phone | 21/14 | 1.8% | steam 34/34 h0 o0 1.22% +17/40; smoke 9/10 h0 o1 1.36% -20/33; sparks 1/61 h60 o0 0.00% +12/16 |
| grassland.day_door1p | grassland.day | door1p | pc | 4/3 | 1.1% | steam 0/50 h34 o16 0.90% +33/85; smoke 0/16 h10 o6 0.00%; sparks 28/92 h64 o0 0.16% +29/73 |
| grassland.dusk_roof3p | grassland.dusk | roof3p | pc | 30/19 | 3.7% | steam 50/50 h0 o0 1.74% -4/9; smoke 16/16 h0 o0 3.25% -11/23; sparks 3/92 h89 o0 0.00% +9/10; headlamp light |
| grassland.dusk_roof3p.phone | grassland.dusk | roof3p | phone | 21/14 | 1.8% | steam 34/34 h0 o0 1.22% -4/7; smoke 9/10 h0 o1 1.36% -13/22; sparks 1/61 h60 o0 0.00% +12/16; headlamp light |
| grassland.dusk_door1p | grassland.dusk | door1p | pc | 4/3 | 1.1% | steam 0/50 h34 o16 0.90% +5/34; smoke 0/16 h10 o6 0.00%; sparks 28/92 h64 o0 0.16% +29/73; headlamp light |
| grassland.night_roof3p | grassland.night | roof3p | pc | 30/19 | 3.7% | steam 50/50 h0 o0 1.74% +23/49; smoke 16/16 h0 o0 3.25% -0/2; sparks 3/92 h89 o0 0.00% +8/10; headlamp light |
| grassland.night_roof3p.phone | grassland.night | roof3p | phone | 21/14 | 1.8% | steam 34/34 h0 o0 1.22% +20/49; smoke 9/10 h0 o1 1.36% +0/2; sparks 1/61 h60 o0 0.00% +12/15; headlamp light |
| grassland.night_door1p | grassland.night | door1p | pc | 4/3 | 1.1% | steam 0/50 h34 o16 0.90% +2/25; smoke 0/16 h10 o6 0.00%; sparks 28/92 h64 o0 0.16% +29/73; headlamp light |
| coal_dust | grassland.day | cab1p | pc | 10/7 | 1.6% | coal 20/20 h0 o0 1.64% -26/117 |

Visibility (warnings are for the maker to fix before the critic; hidden counts are facts):
- steam_chimney: mostly hidden by the train or ground from door1p
- steam_chimney: faint in grassland.dusk_roof3p, grassland.dusk_roof3p.phone (drawn alone, 90% of its pixels change luma by under 25: it barely differs from what is behind it; heuristic)
- smoke_chimney: mostly hidden by the train or ground from door1p
- smoke_chimney: faint in grassland.dusk_roof3p, grassland.dusk_roof3p.phone, grassland.night_roof3p, grassland.night_roof3p.phone (drawn alone, 90% of its pixels change luma by under 25: it barely differs from what is behind it; heuristic)
- sparks_brake: mostly hidden by the train or ground from door1p, roof3p, roof3p phone

Budgets (assumed (OQ-029 default A): not canon until the owner decides; re-measure at the alpha live check (tech.streaming.live_check)); 9 sets holding a pack preset:
- phone: 9 of 9 sets within; tightest storm_crisis: steady 390 of 400, peak 390 of 800, emitters 6 of 12, lights 5 of 8
- pc: 9 of 9 sets within; tightest storm_crisis: steady 671 of 1500, peak 671 of 2500, emitters 6 of 24, lights 5 of 16

Limits: Effects are simulated from the preset data with Roblox ParticleEmitter rules; textures are procedural stand-ins for the built-ins; particles are not lit by the scene beyond a LightInfluence factor; lights show as glow dots only; drift = Workspace.GlobalWind at train speed. Studio test pending (owner).

## Images
- `contact.png` 856x1140 (0.98 MP)
  1. grassland.day roof3p PHONE (phone rates; no shadows, Bloom, SunRays): steam, smoke | hid sparks · stand-in train — 1:1 true size
  2. day roof: steam, smoke | hid sparks — fit x0.50
  3. dusk roof: steam, smoke, headlamp | hid sparks — fit x0.50
  4. night roof: steam, smoke, headlamp | hid sparks — fit x0.50
  5. day door: steam, sparks | hid smoke — fit x0.50
  6. dusk door: steam, sparks, headlamp | hid smoke — fit x0.50
  7. night door: steam, sparks, headlamp | hid smoke — fit x0.50
- `closeups.png` 786x1162 (0.91 MP)

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

### Criteria scored this pass: F1, F2, F3, F4, F5, F6
### F1 Signal
Does each effect or look say its game state at a glance from the player's view (crisis, speed, danger, fail)?
- **4:** You cannot tell which crisis an effect belongs to, or a look hides the train, the interaction points or the HUD area.
- **7:** Every crisis effect is recognisable in the POV frame, but one reads late (too small, too brief or lost against its backdrop) or two crises look alike.
- **9:** Each crisis effect is unmistakable within a second from the roof or door view, louder than any ambience; looks keep the train and interactables the clearest thing in frame.

### F2 Form and motion
Particles: silhouette over life, size and transparency curves, drift with the train's speed. Lighting: key direction, shadow shape, depth layering.
- **4:** Uniform blobs or dots, popping in or out, effects that drift the wrong way for a moving train, or flat lighting with no key direction.
- **7:** Clear shapes that grow and fade believably and stream back with speed; one effect is lumpy, too sparse or ends abruptly, or one look has muddy depth.
- **9:** Every effect has a designed shape at start, middle and end, chunky enough for the toy-like style; looks layer near, middle and far ground cleanly with a readable key light.

### F3 Colour and value
- **4:** Off-palette, muddy or washed-out colour; values collapse so the train, ground and sky merge; night or tunnel goes black.
- **7:** Disciplined palette with clear value steps; one look or effect drifts (too saturated ground, grey-on-grey smoke, a crushed or clipped area).
- **9:** Every colour is a house token or a declared effect colour used on purpose; value separates sky, ground, train and effects in every look, day to night.

### F4 Phone read
Judge the phone-fallback renders (no shadows, no Bloom or SunRays) and the phone budget in Facts.
- **4:** The look depends on post effects or shadows that phones drop, or the crisis stack is over the phone budget.
- **7:** Phone renders still read, with one noticeable loss (a night look goes murky, a glow disappears); budgets are within limits but tight.
- **9:** Phone fallback looks intentional, not broken; every crisis signal survives the priority scaling; budgets have headroom.

### F5 Style match
See the shared House style block, applied to light, haze and effect colour.
- **4:** It looks like another game: Dead Rails sepia or desert haze, Land or Die blue sky, realistic grit or horror darkness.
- **7:** It shares the palette and tone, but one look or effect breaks the family (a realistic smoke, a cold horror tunnel, a neon glow).
- **9:** Slapstick, chunky, readable and warm-hearted in every look and effect: you would assume the same art director made them with the approved assets.

### F6 Polish
- **4:** Placeholder-looking effects, abrupt transitions, visible emitter boxes or seams, effects clipping through the train.
- **7:** Finished where players look; small issues remain (an ember colour off, a beam end too hard, a look's horizon band).
- **9:** Rewards a close look: timings, fades and colour ramps are deliberate, and the set is consistent across all presets.

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
