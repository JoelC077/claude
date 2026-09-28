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

## Profile G — Game feel (juice presets for Roblox events)

Judge the event as designed: curve plots (timeline lanes per channel, dashed = reduce motion), the feel matrix,
filmstrips and the true-size phone frame at the event's peak. The phone plate is a mock and sound is not shown;
never score plate art or missing audio. Score timing, curve shape, magnitude, hierarchy and comfort as measured.

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

## Shared blocks

### House style
<!-- include-with: A6, B5, G5 -->
Risky Rails house style, from the project's thumbnail formula and the approved diesel "23":
- hazard yellow/black against teal-cream or mustard livery
- ink-black details and red buffer beams
- chunky, readable, slightly toy-like forms with capped-post yellow rails
- never Dead Rails' sepia/orange desert look or Land or Die's blue-sky/white-plane look

For work outside Risky Rails, the brief's "House style" line replaces this block.

### Motion note
<!-- include-with: A5, A7, B2 -->
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
