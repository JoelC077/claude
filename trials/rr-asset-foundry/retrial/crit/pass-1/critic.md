# Critic brief — WagonOpenCoal — pass 1 (full)

## How to work
- You're reviewing work you didn't make. Be direct. Every point must rest on something visible in the images or measured under Facts.
- Your answer must be your 3rd message at the latest. Message 1: open this file and every image the prompt names, all together, as parallel tool calls in one message. Message 2: your answer. Only if a number you need is missing may you take one extra look in message 2 (one crop or one more image); then answer in message 3.
- Opening files or images one at a time is a failure. So is opening files not named in the prompt, running scripts, or reading source code.
- If a detail needs a zoom you can't get, say so in the issue instead of guessing.
- Keep your reasoning proportionate. Settle each criterion from the evidence and move on; don't draft the answer twice. Your thinking is the biggest cost of a pass.

## Brief
- Purpose: ASSUMPTION: yard dressing. A two-axle open wagon heaped with coal on the marshalling-yard sidings the crew's train passes (world.biomes.mvp_forks, world.prefabs.15). Scenery, not interactive: it sells 'working railway' and must not read as a tender or a refuel point (D-013: coal lives in two cab bins, no tender).
- Audience: friend groups 16+ (age-checked) at launch; 10-15 once eligible; readable for 10-year-olds, funny for 19-year-olds
- Player view: third-person eye 9.5 studs above the floor, first-person 4.5, vertical FOV 70. WagonOpenCoal: premise siding: ASSUMED, not canon yet (the owner decides): yard dressing on the marshalling-yard sidings (world.prefabs.15, world.biomes.mvp_forks), seen from the coach on the running line (gameplay.train.layout, gameplay.train.keep_on) at the siding spacing of world.prefabs.15 while the world scrolls past (D-002); seen in motion, so style.dont.hairlines applies. POV stands: from the coach, abeam; from the coach, approaching (contact tiles 1, 3 and 4).
- Stage: generated draft (parametric: fixes are parameter or family-code changes, then a rebuild).
- Fixed constraints: <= 10,000 tris per MeshPart (cap 20,000); colours only rr-bible tokens (listed in facts); flat palette colours, no textures, decals or text (style.dont.invented_text); separate named parts per recolour group; invisible box collision proxies.
- Owner worries / decided: open questions OQ-025, OQ-030 (their values are assumptions, not style choices to critique). ASSUMPTION (owner not asked; re-trial of the fixes): where wagons appear is not canon yet (question drafted in rr-asset-foundry design-notes.md; yard sidings by default). Width 17.4 on gauge 8 is the OQ-030 coach envelope (owner decides whether yard wagons are narrower). No lettering or numbering (style.dont.invented_text). Pass-1 issues addressed (previous critique): straps, coal heap, running gear, patch, cap rail, deck gaps.

## Facts (measured)
# WagonOpenCoal (measured by rr-asset-foundry 2026-09-28)
- family wagon, preset open_coal (two-axle open wagon heaped with coal); seed 1
- params: kind open, length 30.0, width 17.4 (tech.units.stock_width, proposed), gauge 8.0 (tech.units.gauge, proposed), deck 5.0 (tech.units.stock_floor, proposed), running auto, wheel_r 2.0, side_h 4.0, body_h 7.0, planks 4, load coal, heap 2.75, peaks 2, weathering 0.3, door True
- size, studs (Blender x, y, z-up): 32.8 x 18.06 x 12.66; in Studio X 32.8, Y(up) 12.66, Z 18.06
- parts: 56 separate named <Asset>_<Part>_<Group>_<nn>; groups Chassis 14, Buffer 2, Steel 10, Iron 16, Timber 5, Cap 4, Door 2, Load 2, Repair 1
- collision: 5 box proxies (invisible, CanCollide true); visual parts CanCollide false
- tris: 1,858 total; largest part WagonOpenCoal_Heap_Load_01 250 (target 10,000 / cap 20,000 per MeshPart)
- palette atlas: 13 cells exact=True; 793 faces, 0 span cells, 0 near an edge, 0 off-palette
- colours used (rr-bible tokens): Chassis style.world.soot_black #15181B Metal, Steel style.thumb.steel #8A929B Metal, Buffer style.brand.buffer_red #C9412E SmoothPlastic, Iron style.world.ironwork #363A42 Metal, Timber style.depot_kit.timber_dark #8F5A2A WoodPlanks, Door style.depot_kit.timber_light #B87A3D WoodPlanks, Load style.cab.coal #262626 Slate, Cap style.depot_kit.timber_light #B87A3D WoodPlanks, Repair style.depot_kit.timber_light #B87A3D WoodPlanks
- back faces (every POV and construction camera): 0 px in 6 views; coplanar overlaps: 0; floating parts: 0
- A5, smallest on-screen side of any single piece (key features >= 5 px): 400 px game view: BufferHead 5.3 px, DoorStrap 5.4 px, Lump 5.4 px, Strap 5.6 px, EndStrap 5.7 px, Cap 5.8 px, Side 6.3 px, Repair 6.9 px, Axlebox 8.4 px, Wheel 15.2 px, Door 16.1 px; POV 3P 768 px: Cap 7.8 px, BufferHead 8.0 px, EndStrap 8.3 px, Side 8.4 px, DoorStrap 8.5 px, Lump 10.5 px, Strap 10.8 px, Axlebox 12.4 px, Repair 13.7 px, Door 25.5 px, Wheel 32.7 px
- player view premise siding: pov3p = from the coach, abeam at [0.0, -30.6, 5.0]; pov3p_2 = from the coach, approaching at [50.0, -30.6, 5.0] (ASSUMED, not canon yet (the owner decides): yard dressing on the marshalling-yard sidings ...)
- measured: deck top above rail: 5 studs
- measured: open wagon inside: 29 x 16.4 x 4 studs
- FBX reimport: 61 meshes, size [32.8, 18.06, 12.66], 1918 tris, no unit warning
- Studio setup script: ok (luaparse: ok)
- canon gate (bible check studio_setup.lua): PASS
- open questions: OQ-025, OQ-030 (values labelled assumed/proposed until the owner decides)
- not measured here: Studio import and the setup script (no Studio in the cloud; owner test)

## Images
- `contact.png` 1186x870 (1.03 MP)
  1. POV 3P from the coach, abeam — 1:1 true size
  2. game 400px — 1:1 true size
  3. POV 1P — fit x0.42
  4. POV 3P from the coach, approaching — fit x0.42
  5. 3/4 — fit x0.50
  6. side — fit x0.50
  7. end — fit x0.50

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

### Criteria scored this pass: A1, A2, A3, A4, A5, A6, A7
### A1 Silhouette
- **4:** The outline is a generic box or tube. You can't tell what it is, or which way is front, from a flat black shape.
- **7:** It reads as the right object in the side and 3/4 views. The masses are clear but even: nothing leads the eye, and some edges are straight runs with no rhythm.
- **9:** It is instantly identifiable as a black shape from every review angle. It has one strong primary mass, secondary shapes that give rhythm (roofline, porches, wheels, stacks), and a distinctive profile a player could draw from memory. A long or repetitive asset (platform, canopy, fence, carriage, wall) also has a focal point: one element that leads the eye, such as a clock, sign, gable, raised bay or colour break, so the run doesn't read as pure repetition.

### A2 Proportions and avatar scale
- **4:** Parts are the wrong size relative to each other or to a 5-stud Roblox avatar: doors avatars can't fit through, steps too tall, wheels toy-sized.
- **7:** Overall proportions are believable and avatars fit. One or two elements feel off: parts slightly under- or over-scaled, or cramped openings.
- **9:** Every part is sized to the object's logic and to avatar use. Openings, steps, rails, seats and walkways fit a 5-stud avatar with room, and the key proportions match the reference or family the asset belongs to.

### A3 Topology and construction
- **4:** Visible intersections, gaps, floating parts, flipped or dark faces, z-fighting, or parts over the 20,000-triangle MeshPart cap.
- **7:** Clean at normal distance, with minor hidden intersections. Triangles sit within budget, but some are spent where no one looks. Parts are split for gameplay (doors, glass, seats), and collision is roughly right.
- **9:** No visible construction faults at any review distance. Triangles go where the silhouette and close-ups need them. Every gameplay part is separate and sensibly named, collision proxies cover walkable and blocking surfaces, and nothing overlaps between vehicles.

### A4 Materials and colour
- **4:** Flat, untreated colours with no hierarchy, or colours that won't survive import (plain Blender materials with no texture or vertex-colour path into Roblox).
- **7:** A clear palette with a dominant hue and an accent. Values separate the major parts, and the import path is solved (a baked texture, palette atlas or colour plan per MeshPart). Surfaces are clean but still read as plastic.
- **9:** The palette is deliberate and matches the house style. Value contrast separates every functional part (walkable surfaces, grab points, hazards). Materials hint at what they are (metal, glass, wood) through roughness and value without noise, and the colours import into Roblox exactly as reviewed.

### A5 Read at game distance
Judge at the 400 px wide game-distance render (shown 1:1 on the contact sheet) and in the POV views. A key feature (entrance, step, handrail, lever, sign, livery band, support) reads only if it spans **at least 5 px** in its smaller dimension at 400 px.
- **4:** At 400 px it turns to mush: key features are under 5 px or merge, and the livery and interaction points vanish.
- **7:** It reads as the object at distance, but some key features are under 5 px: lettering, handrails and steps shimmer or disappear, and the interaction points are only obvious up close.
- **9:** At 400 px every key feature is 5 px or more, and the silhouette, livery bands and every interaction point still read in the POV views. Detail is scaled for the game camera, not for the close-up render.

### A6 Style match
See the shared House style block.
- **4:** It looks like it belongs to a different game: wrong palette, realism level or detail language.
- **7:** It shares the palette and some detail language, but one element breaks the family (a different lettering face, rail style or level of detail).
- **9:** You'd assume the same artist made it and the approved assets together: the same palette logic, line weight, rail, step and lettering language, and the same level of detail.

### A7 Polish
- **4:** Unfinished areas: bare undersides, missing ends, placeholder text, obvious copy-paste repetition.
- **7:** Finished everywhere a player normally looks. Close-ups show small misalignments, uneven spacing or details that stop short.
- **9:** It rewards a close look. Details are aligned and spaced on purpose, ends and undersides are resolved, and small touches (tail lamps, numbering, wear marks where the style allows) are in place.

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
