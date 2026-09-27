# Critic brief — Risky Rails ticket notification HUD (remake) — pass 2 (final)

## How to work
- You're reviewing work you didn't make. Be direct. Every point must rest on something visible in the images or measured under Facts.
- Your answer must be your 3rd message at the latest. Message 1: open this file and every image the prompt names, all together, as parallel tool calls in one message. Message 2: your answer. Only if a number you need is missing may you take one extra look in message 2 (one crop or one more image); then answer in message 3.
- Opening files or images one at a time is a failure. So is opening files not named in the prompt, running scripts, or reading source code.
- If a detail needs a zoom you can't get, say so in the issue instead of guessing.
- Keep your reasoning proportionate. Settle each criterion from the evidence and move on; don't draft the answer twice. Your thinking is the biggest cost of a pass.

## Brief
Purpose: in-run notification stack telling the train crew what needs doing now (crises), what is coming (junction/risk), and rewards/crew news, without hiding the track.
Audience: Risky Rails players (Roblox, 13+ mixed), owner as art director.
Player view: phone landscape 844x390 true size (primary), PC 1280x720 (UIScale 1.16); screen overlay, Scale sizing + UIAspectRatioConstraint; world scrolls behind; Roblox topbar (top 36px), thumbstick (bottom-left) and jump button (bottom-right) drawn as dashed zones.
Stage: draft.
Fixed constraints: owner likes the ticket frame (stub, punch notches, perforation, medallion, value stamp must stay); exact texts/kinds/lifetimes from the prototype; cap 4 visible + "+N MORE"; newest at bottom; fonts Luckiest Guy + Montserrat. Background scene is a stand-in, not judged.
Owner worries / already decided: style licence given ("somewhat more fitting for the game") -> railway-company ticket: soot-iron frame, brass rivets + brass medallion, aged card with faint hatch, rubber-stamp values. Crew names are placeholders. Motion is specified in text on the Kit board (static renders). step 2: pre-answered

## Standing scores
B5 6 (pass 1). Bar: 8 on every criterion. Rule 8 applies to any you lower.

## Changes since pass 1
# Delta since critic pass 1 (overall 6, lowest B5) - maker's claims, verify against the renders
- B5-1 livery: card flat teal-cream #E6E0C4 with 4px teal #3E8C86 top band + 1px ink rule; frame bg ink #15171c (iron gradient gone) with mustard #D9A627 inner lining; medallion ring, rivets, +N pill, merge badges now mustard; red buffer-beam bar (#C0392B, 6px) under full crisis tickets; frame stays 3px ink. Risk keeps yellow/black stub.
- B1-1 crisis hierarchy: older (compact) crises 2px red frame, stub saturate(.6), no beam; only newest crisis keeps 4px ink + red halo with pulse glow.
- B2-1 legibility: subtext 15px/600 (was 13.5px/700) on flat card (hatch removed); timer bar 6px (was 5px); titles 2px lower; compact title line-height 20px.
- B3-1 overflow: "+N MORE" pill is a flex item right-aligned in the stack, 8px gap; stack gap 6->5px, crisis slot padding 5->4px. Maker measured pill y 36-63, top ticket y 71, clears 36px topbar.
- B6-1 detail: hatch removed; perforation 4 solid dots at 5px; rivets 10px with 2px ink edge.
- B4-1 (optional): crew stub moved to blue-teal #2F7F9A to separate from green cash.

## Facts (measured)
# Facts pass 2 (independent, fresh render of current src/hud via render_design.py, measured)
- Phone.html: 844x390, texts 8, min contrast 7.05, sizes 15/17/18/20/24px, contrast fails 0, small text 0, overlaps 0, spill 0, clipped 1, fonts not loaded 0, errors 0
- PhoneRoutine.html: 844x390, texts 7, min contrast 7.05, sizes 15/17/18/20/22/24px, contrast fails 0, small text 0, overlaps 0, spill 0, clipped 1, fonts not loaded 0, errors 0
- PhoneCrises.html: 844x390, texts 5, min contrast 8.2 (was 7.9), sizes 15/18/20px, contrast fails 0, small text 0, overlaps 0, spill 0, clipped 1, errors 0
- PhoneOverflow.html: 844x390, texts 6, min contrast 8.2 (was 7.9), sizes 15/16/18/20px, contrast fails 0, small text 0, overlaps 0, spill 0, clipped 1, errors 0
- PC.html: 1280x720, texts 20, min contrast 7.05, sizes 13/15/17/18/20/22/24px (13px x8 are PC scene labels, not ticket text), contrast fails 0, overlaps 0, clipped 1, errors 0
- Kit.html: 1320x1080, texts 67, min contrast 5.38, sizes 12-34px (12px x17 are kit annotations), contrast fails 0, small text 0, overlaps 0, errors 0
- Smallest ticket text on all Phone boards: 15px (pass 1: 13.5px).
- 'offboard' items are stand-in background hills (scene decoration, not judged); 'clipped' = scene container clipping, not ticket text.
- Contact sheet (856x1332, 1.14 MP): Phone crisis + Phone overflow at 1:1 true size (844x390); crises+junction, routine, PC, Kit scaled to fit. Full-size PNGs in pass-2/.
- Spec (from mission.md): ticket 290x64 / compact 44; cap 4 + '+N MORE'; newest at bottom; bottom-right stack above jump zone; topbar top 36px; Luckiest Guy + Montserrat.
- Previous self-review passes (archived in _selfreview-archive/) are NOT shown to this critic.

## Images
- `contact.png` 856x1332 (1.14 MP)
  1. Phone crisis — 1:1 true size
  2. Phone overflow — 1:1 true size
  3. Phone crises+junction — fit x0.47
  4. Phone routine — fit x0.47
  5. PC — fit x0.31
  6. Kit — fit x0.21

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
