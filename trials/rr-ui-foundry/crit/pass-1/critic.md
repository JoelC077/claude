# Critic brief — Risky Rails UI kit: HUD ticket stack + Create match panel (one token set) — pass 1 (full)

## How to work
- You're reviewing work you didn't make. Be direct. Every point must rest on something visible in the images or measured under Facts.
- Your answer must be your 3rd message at the latest. Message 1: open this file and every image the prompt names, all together, as parallel tool calls in one message. Message 2: your answer. Only if a number you need is missing may you take one extra look in message 2 (one crop or one more image); then answer in message 3.
- Opening files or images one at a time is a failure. So is opening files not named in the prompt, running scripts, or reading source code.
- If a detail needs a zoom you can't get, say so in the issue instead of guessing.
- Keep your reasoning proportionate. Settle each criterion from the evidence and move on; don't draft the answer twice. Your thinking is the biggest cost of a pass.

## Brief
Purpose: a reusable Roblox UI kit. Screen 1 (HUD): tell the crew what just happened and what to do next without covering the game; crises read first. Screen 2 (Create match, lobby modal): pick crew size and difficulty, then join; one obvious primary action. Both must read as one game's UI (same components, tokens, type).
Audience: friend groups 16+ (age-checked) at launch; 10-15 once eligible; readable for 10-year-olds, funny for 19-year-olds; most players and ad traffic are on phones.
Player view: screen overlays on a phone in landscape, 844x390 at true size (ScreenGui CoreUISafeInsets, top bar 58 px); PC 1280x720 is second (true-size crops on the close-up). The HUD sits over the running game; Create match is a modal over a dimmed game. Grey pills and circles are Roblox's own top bar, jump button and thumbstick; the background is a mock game plate, not part of the UI.
Stage: draft (generated from one spec per screen by rr-ui-foundry; the same numbers build the Roblox package). The HUD is the ticket design from mission 260927-ticket-hud; Create match follows the Depot Ticket UI sketch (rows: label left, controls right; one accent does selected / current / Join; tier colours only as difficulty).
Fixed constraints: rr-bible tokens only (skin C = assumed, OQ-001 default; skins A/B on the close-up are the other options); fonts Luckiest Guy, Montserrat; text >= 12 px body / 16 px titles, targets >= 44 px; clear of top bar, jump and thumbstick; exact game strings from canon; players chips 1/2/3 as sketched (crew size is an open question).
Already decided / open: OQ-001 HUD skin (default C; A vs C side by side is on the close-up); OQ-017 menu accent (follows OQ-001); OQ-003 currency ($ default); OQ-012 alert IDs; OQ-033 platforms (phone + PC gated); OQ-034 HUD stack lifted above the newer jump button (3 tickets while lifted). Owner away: step 2 pre-answered from canon.

## Facts (measured)
- Measured by rr-ui-foundry validate/render (render = model + Chromium, not Roblox).

- Sheets: contact.png = both screens on the phone at true size (tiles 1-2) + other states and the notched phone (x0.33; "Match INSANE, pad focus" = gamepad focus on JOIN with ">" pressed). closeups.png = PC 1280x720 true-size crops of both screens + skins A and B (x0.50).
- Kit change in this pass (trial kit copy): panel header 50 -> 56 px and close button 44 -> 52 px; Create match targets drawn at 52 design px, because a notched phone scales the whole design by 0.86 (Create match chips 44.7 px there).
- Create match copy is literal (not canon): CREATE MATCH, PLAYERS, DIFFICULTY, JOIN, JOINING...; HUD strings are canon (gameplay.alerts.*), text diff 0.

## HudTickets (measured by rr-ui-foundry; render = model + Chromium, not Roblox)

- Design space: phone screen 844x390, ScreenGui CoreUISafeInsets area 844x332 px (top bar 58 px, tech.ui_platform.topbar_inset).
- Layout: pin + scale (Scale sizes + UIAspectRatioConstraint, pinned margins x the same scale); UIScale density Small 1, Medium 0.7649, Large 1 (tech.ui_platform.layout; Large = OQ-033 default).
- Skin on the main boards: C = assumed (OQ-001 default); other skins on closeups.

| device | px per design px | smallest text | smallest target | touch zones | stack |
|---|---|---|---|---|---|
| phone | 1.000 | 14 px (stack.t3.body) | - | small | routine: 3 visible, +0 more; crisis: 3 visible, +1 more; overflow: 3 visible, +3 more |
| phone_notch | 0.860 | 12 px (stack.t3.body) | - | small | routine: 3 visible, +0 more; crisis: 3 visible, +1 more; overflow: 3 visible, +3 more |
| tablet | 1.398 | 19.6 px (stack.t7.body) | - | large | routine: 3 visible, +0 more; crisis: 3 visible, +1 more; overflow: 3 visible, +3 more |
| pc | 1.160 | 16.2 px (stack.t3.body) | - | - | routine: 3 visible, +0 more; crisis: 4 visible, +0 more; overflow: 4 visible, +2 more |
| console | 2.275 | 31.8 px (stack.t3.body) | - | - | routine: 3 visible, +0 more; crisis: 4 visible, +0 more; overflow: 4 visible, +2 more |

- Lowest text contrast per skin (WCAG, text vs the fill it sits on): A 6.76:1 (stack.t3.stamp); B 7.11:1 (stack.t3.stamp); C 7.12:1 (stack.t3.stamp)
- Minimum text (ui.rules.min_text): display 16 px, body 12 px on phone; touch target 44 px (tech.ui_platform.touch_target_px).
- Text wider than its box (Chromium): none
- Image placeholders on boards: none
- Fonts on boards: Luckiest Guy, Montserrat (embedded woff2)
- Checks: 0 errors, 8 warnings.
  - W [phone_notch] text stack.t1.title 15.5 px < 16 px (board routine)
  - W [phone_notch] text stack.t2.title 15.5 px < 16 px (board routine)
  - W [phone_notch] text stack.t2.title 15.5 px < 16 px (board crisis)
  - W [phone_notch] text stack.t3.title 15.5 px < 16 px (board crisis)
  - W [phone_notch] text stack.more.chip 13.8 px < 16 px (board crisis)
  - W [phone_notch] text stack.t5.title 15.5 px < 16 px (board overflow)
  - W [phone_notch] text stack.t5.badge 13.8 px < 16 px (board overflow)
  - W [phone_notch] text stack.more.chip 13.8 px < 16 px (board overflow)
  - i [phone] stack is lifted 24 px above the small jump zone at run time
  - i [phone_notch] stack is lifted 40 px above the small jump zone at run time
  - i [tablet] stack is lifted 75 px above the large jump zone at run time


## LobbyCreateMatch (measured by rr-ui-foundry; render = model + Chromium, not Roblox)

- Design space: phone screen 844x390, ScreenGui CoreUISafeInsets area 844x332 px (top bar 58 px, tech.ui_platform.topbar_inset).
- Layout: pin + scale (Scale sizes + UIAspectRatioConstraint, pinned margins x the same scale); UIScale density Small 1, Medium 0.7649, Large 1 (tech.ui_platform.layout; Large = OQ-033 default).
- Skin on the main boards: C = assumed (OQ-001 default); other skins on closeups.

| device | px per design px | smallest text | smallest target | touch zones | stack |
|---|---|---|---|---|---|
| phone | 1.000, 1.000 | 14 px (lbl_players) | 52 px (p1) | small | - |
| phone_notch | 1.000, 0.860 | 12 px (lbl_players) | 44.7 px (p1) | small | - |
| tablet | 1.398, 1.398 | 19.6 px (lbl_diff) | 72.7 px (p1) | large | - |
| pc | 1.160, 1.160 | 16.2 px (lbl_players) | 60.3 px (p1) | - | - |
| console | 2.275, 2.275 | 31.8 px (lbl_players) | 118.3 px (panel.close) | - | - |

- Lowest text contrast per skin (WCAG, text vs the fill it sits on): A 3.19:1 (diff_next.label); B 3.82:1 (panel.title); C 6.7:1 (join.label)
- Minimum text (ui.rules.min_text): display 16 px, body 12 px on phone; touch target 44 px (tech.ui_platform.touch_target_px).
- Text wider than its box (Chromium): none
- Image placeholders on boards: none
- Fonts on boards: Luckiest Guy, Montserrat (embedded woff2)
- Checks: 0 errors, 0 warnings.
  - i literal copy (not from canon; owner confirms): panel.title: 'CREATE MATCH'; lbl_players: 'PLAYERS'; lbl_diff: 'DIFFICULTY'; join.label: 'JOIN'; join.label: 'JOINING...'
  - i nav: p1.up = panel.close but panel.close.down = p3
  - i nav: p2.up = panel.close but panel.close.down = p3
  - i nav: p2.down = diff_next but diff_next.up = p3
  - i nav: diff_next.down = join but join.up = diff_prev

## Images
- `contact.png` 856x1138 (0.97 MP)
  1. HUD phone 844x390 routine (C) — 1:1 true size
  2. Create match phone 844x390 open (C) — 1:1 true size
  3. HUD crisis phone — fit x0.33
  4. HUD overflow phone — fit x0.33
  5. HUD notched phone — fit x0.33
  6. Match INSANE, pad focus — fit x0.33
  7. Match joining — fit x0.33
  8. Match notched phone — fit x0.33
- `closeups.png` 1218x890 (1.08 MP)

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
