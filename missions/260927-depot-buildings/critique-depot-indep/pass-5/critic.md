# Critic brief — Depot Lobby: Depot station house (independent critique) — pass 5 (final)

## How to work
- You're reviewing work you didn't make. Be direct. Every point must rest on something visible in the images or measured under Facts.
- Your answer must be your 3rd message at the latest. Message 1: open this file and every image the prompt names, all together, as parallel tool calls in one message. Message 2: your answer. Only if a number you need is missing may you take one extra look in message 2 (one crop or one more image); then answer in message 3.
- Opening files or images one at a time is a failure. So is opening files not named in the prompt, running scripts, or reading source code.
- If a detail needs a zoom you can't get, say so in the issue instead of guessing.
- Keep your reasoning proportionate. Settle each criterion from the evidence and move on; don't draft the answer twice. Your thinking is the biggest cost of a pass.

## Brief
Purpose: the Depot station house of the Risky Rails Depot Lobby (walk-around hub, 6 players): two-gable stone station house, 24x14 studs at plan (18,76), front (long side, twin cross-gables) faces north onto the yard/display track. Score the DEPOT only.
Audience: Risky Rails players (Roblox, 13+ mixed), owner as art director.
Player view: third-person eye 9.5 studs (first-person 5), vertical FOV 70, walking around a static lobby; seen mostly from 20-60 studs; 400x225 game-distance render included.
Stage: post-iteration build (4 self-assessed passes; this is the first independent pass).
Fixed constraints: studs (1 BU = 1 stud), 5-stud avatars, doors >= 7x9; <= 10k tris per part, <= 20k per building; one 256px palette atlas (32px cells), one material; every recolourable part a separate named object; weathered-rural railway style (stone, iron, timber, moss, soot, brass), decay at edges, clean routes; chunky readable forms.
Owner worries / already decided: facade-only (open doorway, dark interior plane, no interior); no invented signage text (name board is a blank placeholder); owner wants many separate parts for recolouring. Bar 8 on every criterion.

## Standing scores
. Bar: 8 on every criterion. Rule 8 applies to any you lower.

## Changes since pass 4
# Fixes since pass 4 (maker round 4)
- A4-1: slatedk roof darkened ~10% (#2f333a); all Depot stone walls moved to new warmer/lighter cell stonewm #b6ab90. Maker-measured game render: lit wall luma 140 vs roof 64 (54%); shaded wall 95 vs 64 (33%).
- A7-1: name board gains inset ink border + darker cream field (new cell creamdk #d2c290); still blank, now visibly a placeholder (owner to decide wording).
- A5-1 (cheap): lamp post shaft 0.6 -> 0.9 studs wide.
- A1-1 (rear dormer peak): left as-is.
- Rebuilt 389 parts, 4,980 tris, palette verified, 0 backfaces, re-exported.

## Facts (measured)
## Depot (measured fresh from src/depot/depot.blend, 2026-09-27, pass 5)
- parts (separate named Depot_* mesh objects): 389; materials: 1 (palette atlas)
- tris: 4,980 total (budget 10k/part, 20k/building); 0 parts over target; largest part 36 tris
- backfaces from POV 3P cam: 0 px
- world bbox (studs, incl. ground slab + dressing): x 10..50 (40), y -94..-60 (34), z -0.5..31.3 (bell cote apex)
- wall footprint 24x14, eave 14 (unchanged per maker rebuild)
- stone walls/gables/bays/dormer cheek now Depot_*_Stonewm_* (11 parts, warmer lighter stone cell)
- name board: Depot_NameBoardBorder_Ink_01 + Depot_NameBoardField_Creamdk_01 layered on cream board; still blank (placeholder)
- lamp posts Depot_Lamp01/02Post_Iron: shaft 0.9 studs wide (maker log)
- yard rail Depot_YardRail_Hazard_01/02: 11 x 1.0 x 1.2 studs each; 10-stud gap on door axis
- renders: depot_pov3p (stand (30,-58), eye 9.5, FOV70) and depot_pov1p (eye 5) at 400x225; depot_game 400x225 from fixed Depot_Cam_Game; construction views 34/side/back/door 1280x720 from fixed build cameras
- UI render: not applicable (3D asset only, no UI in src)

## Images
- `contact.png` 658x867 (0.57 MP)
  1. Game 400x225 — 1:1 true size
  2. POV 3P eye9.5 — fit x0.80
  3. POV 1P eye5 — fit x0.80
  4. 3/4 — fit x0.25
  5. Side — fit x0.25
  6. Back — fit x0.25
  7. Door — fit x0.25

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
Verify the latest fixes, then score every criterion. Output exactly:
```
VERIFY:
<issue id>: fixed | not fixed | worse — <evidence>
FIRST READ: <eye path, and what it reads as vs the brief — 2 lines>
SCORES:
<C#> <name>: <n>/10 — meets <anchor> because <evidence>; below <next anchor> because <issue ids>
DROPS: <rule 8 justification for any standing score you lowered, else none>
ISSUES (ranked; issue format; blocks-8 first):
...
OVERALL: <lowest score> (<criterion>)
NEEDS OWNER: <decisions only the owner can make, or none>
```
