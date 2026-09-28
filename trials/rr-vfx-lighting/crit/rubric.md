# Critic rubric

`scripts/critic_kit.py` copies the parts a pass needs into that pass's `critic.md`: How to work, the scoring rules, only the criteria being scored (plus any shared block they pull in), the issue format and one output format. Critics never read this whole file. Edit wording here; keep the `##`/`###` headings and the `include-with` comments, because the kit finds sections by them.

## How to work

- You're reviewing work you didn't make. Be direct. Every point must rest on something visible in the images or measured under Facts.
- Your answer must be your 3rd message at the latest. Message 1: open this file and every image the prompt names, all together, as parallel tool calls in one message. Message 2: your answer. Only if a number you need is missing may you take one extra look in message 2 (one crop or one more image); then answer in message 3.
- Opening files or images one at a time is a failure. So is opening files not named in the prompt, running scripts, or reading source code.
- If a detail needs a zoom you can't get, say so in the issue instead of guessing.
- Keep your reasoning proportionate. Settle each criterion from the evidence and move on; don't draft the answer twice. Your thinking is the biggest cost of a pass.

## Scoring rules

Score each criterion 0–10. The anchors at 4, 7 and 9 are fixed. Interpolate between them: a 5 or 6 sits between the 4 and 7 descriptions, and an 8 meets all of 7 with no more than one gap from 9. The bar for "£500 commission" work is **8 on every criterion**. **The overall score is the lowest criterion score, never the average.**

1. **Anchor + evidence, or it doesn't count.** Every score cites the anchor it meets, names the view or measurement that shows it, and lists the issues holding it below the next anchor. A score with no evidence line is void.
2. **A score of 8 or more needs zero open issues tagged `blocks-8` on that criterion.** If you raise any issue that stops a criterion reaching 8, tag it `blocks-8` and keep the score at 7 or below.
3. **Score what is visible or measured, not what is intended.** Don't use source code, part names or the maker's notes to lift a score. They are only for naming fixes.
4. **Don't grade relative to earlier versions.** "Better than before" is not a score. Only the anchors are.
5. **Placeholders the owner must supply don't lower a score** if they are clearly marked, for example a seating layout the owner will specify. Unmarked fake content does lower it.
6. **Put your score where the evidence falls.** Don't round up to reach a bar. If you are torn between two whole numbers, score the lower one and name the evidence that would move it up.
7. **The player's view decides.** Judge first from the views that show the work as it is really seen: the POV cameras, the 400 px game-distance render, the real-size UI frame. Detail visible only in a construction close-up can't lift a score the player can't see.
8. **Scores at the bar are sticky.** A criterion that an earlier pass scored at or above the bar (listed under Standing scores) can only drop if you either (a) cite a part that changed since that pass, or (b) state a missed `blocks-8` issue with pixel or measurement evidence and say why it was missed, for example because it only shows in a view added this pass. Otherwise keep the standing score.

## Profile A — 3D models and assets

Default for Risky Rails vehicles, props and environments.

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

## Profile B — 2D: UI, screens, thumbnails, canvases, web pages

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

## Profile F — Effects and lighting (Roblox look-dev presets)

Judge the preview images as intent: shape, colour, value and readability. They are approximations of Roblox (the
Limits line in Facts says how), so never score engine-exact pixels; do score what the preset data would plainly do.

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

## Shared blocks

### House style
<!-- include-with: A6, B5, F5 -->
Risky Rails house style, from the project's thumbnail formula and the approved diesel "23":
- hazard yellow/black against teal-cream or mustard livery
- ink-black details and red buffer beams
- chunky, readable, slightly toy-like forms with capped-post yellow rails
- never Dead Rails' sepia/orange desert look or Land or Die's blue-sky/white-plane look

For work outside Risky Rails, the brief's "House style" line replaces this block.

### Motion note
<!-- include-with: A5, A7, B2, F2 -->
Hairline repeated detail (cresting, balusters, slats, thin trim, 1 px strokes) flickers and crawls when the camera or the world moves, even when a still render looks clean. If the brief says the work is seen in motion (a moving camera, a scrolling world, a sign passed at speed) and repeated detail is under 2 px wide at the 400 px or real-size view, raise it as a `blocks-8` issue: thicken it to at least 5 px, merge it into one solid shape, or drop it.

## Issue format

Every issue, every pass:
```
[C#-n] <criterion> · <where: part/element and view>   impact: high|med|low   blocks-8: yes|no
  Problem: <what is visible or measured>
  Fix: <exact change: part name + value, or element + value>
  Done when: <an objective check a later pass can verify from the renders or measurements>
```
Rank issues by impact on the lowest-scoring criteria first. Generic notes such as "improve detail", "add polish" or "make it pop" are banned. If you can't name the part and the value, drop the issue.

## Output — full

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

## Output — delta

Score only the criteria listed under Rubric. Output exactly:
```
VERIFY:
<issue id>: fixed | not fixed | worse — <evidence: view + what's visible/measured>
SCORES (listed criteria only):
<C#> <name>: <n>/10 — meets <anchor> because <evidence>; below <next anchor> because <issue ids>
DROPS: <for a standing score you would lower: rule 8 (a) the changed part, or (b) the missed blocks-8 issue with pixel/measurement evidence and why it was missed; else none>
NEW ISSUES (issue format, listed criteria only, or none):
REGRESSIONS: <anything visibly broken elsewhere on the contact sheet, or none>
```

## Output — final

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
