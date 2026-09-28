# Critic brief — UI kit set: HudTickets + LobbyCreateMatch — pass 1 (full)

## How to work
- You're reviewing work you didn't make. Be direct. Every point must rest on something visible in the images or measured under Facts.
- Your answer must be your 3rd message at the latest. Message 1: open this file and every image the prompt names, all together, as parallel tool calls in one message. Message 2: your answer. Only if a number you need is missing may you take one extra look in message 2 (one crop or one more image); then answer in message 3.
- Opening files or images one at a time is a failure. So is opening files not named in the prompt, running scripts, or reading source code.
- If a detail needs a zoom you can't get, say so in the issue instead of guessing.
- Keep your reasoning proportionate. Settle each criterion from the evidence and move on; don't draft the answer twice. Your thinking is the biggest cost of a pass.

## Brief
Purpose: HudTickets: Tell the crew what just happened and what to do next without covering the game; crises read first. (a screen overlay over the running game (HUD))
Source: HudTickets: TN prototype + HUDM remake; canon ui.hud.*, gameplay.alerts.*
Purpose: LobbyCreateMatch: Pick crew size and difficulty, then join the queue; one obvious primary action. (a modal panel over the game)
Source: LobbyCreateMatch: DTU Depot Ticket UI 'Create match': rows (label left, controls right); one accent for the selected count, the current difficulty and Join; tier colours only as difficulty. Canon ui.lobby.*, ui.rules.*
Audience: friend groups 16+ (age-checked) at launch; 10-15 once eligible; readable for 10-year-olds, funny for 19-year-olds; most players and ad traffic are on phones
Player view: phone landscape 844x390 at true size (ScreenGui CoreUISafeInsets, top bar 58 px); the PC crop is true size too; other boards are scaled by the kit's pin + scale rule. Grey pills and circles are Roblox's own top bar, jump button and thumbstick.
Stage: draft (generated from the spec by rr-ui-foundry; the same numbers build the Roblox package).
Fixed constraints: rr-bible tokens only (skin C = assumed (OQ-001 default)); fonts Luckiest Guy, Montserrat; text >= 12/16 px, targets >= 44 px; clear of top bar, jump and thumbstick; exact game strings from canon.
Canon this design keeps (rr-bible; a fix that would break one goes under NEEDS OWNER, not ISSUES): ui.hud.anchor = bottom-right stack, newest at the bottom; ui.hud.max_visible = 4; ui.hud.gap_px = 8; ui.hud.compact_rule = the newest ticket and the newest crisis stay full size; older ones go compact (title + bar only); ui.hud.crisis_extra = crisis: ink halo + red halo (#E23A2E, pulsing 0.3-0.95), one shake on arrival (0.5 s, +-5 px); ui.hud.motion = enter: slide from 125% + fade; leave: slide out, removed after 320 ms; merge bump scale 1.07 > 1 over 0.32 s; gameplay.alerts.transport = one server-driven RemoteEvent: show alert (ID) and clear alert (ID); one client script owns the stack; ui.lobby.controls = Players 1/2/3 chips, Difficulty < MEDIUM >, Join; chips 44 x 44, radius 12; ui.rules.one_accent = one accent hue does all the "this is active" work (selected, current, Join); ui.rules.difficulty_never_chrome = difficulty colours appear only as difficulty, never as chrome; ui.rules.colourblind = kinds and terminals carry an icon or shape backup, never colour alone; tech.ui_platform.touch_target_px = 44; gameplay.difficulty.tiers = Easy, Medium, Hard, Insane; gameplay.crew.max = 6
Already decided / open: OQ-001 HUD skin: heritage brass or teal-cream/mustard livery? (open; default in use: C, then one independent critic pass on A vs C boards side by side before the owner picks); OQ-003 Currency: coins, "$" or fare? (open; default in use: C (zero rework; one currency)); OQ-012 HUD alert IDs: per fault or generic BREAKDOWN? (open; default in use: A, with proposed texts marked proposed until approved); OQ-034 HUD stack bottom offset vs the newer jump button (open; default in use: A (the classic jump layout keeps canon's 4-ticket stack; the ability-controls layout is detected, not guessed)); OQ-017 Lobby and menu accent (open; default in use: C); OQ-033 UI platforms: which devices must every screen support, and how big is UI on a TV? (open; default in use: A (no extra alpha work beyond the nav graph the kit builds anyway; keeps console open))
step 2: pre-answered (canon via rr-bible; owner away)

## Facts (measured)
## Facts: HudTickets + LobbyCreateMatch (one kit, one token set)

### Facts: HudTickets (measured by rr-ui-foundry; render = model + Chromium, not Roblox)

- Design space: phone screen 844x390, ScreenGui CoreUISafeInsets area 844x332 px (top bar 58 px, tech.ui_platform.topbar_inset).
- Layout: pin + scale with own fit (a smaller area shrinks a group only as much as it needs). px per design px: PC 1.16 (tech.ui_platform.layout); UIScale after the fit: Small 1, Medium 0.7649, Large 1 (Large = OQ-033).
- Skin on the main boards: C = assumed (OQ-001 default); other skins on closeups.
- Purpose: Tell the crew what just happened and what to do next without covering the game; crises read first.

| device | px per design px | smallest text | smallest target | touch zones | stack |
|---|---|---|---|---|---|
| phone | 1.000 | 14 px (stack.t3.body) | - | small | routine: 3 visible, +0 more; crisis: 3 visible, +1 more; overflow: 3 visible, +3 more |
| phone_notch | 0.937 | 13.1 px (stack.t3.body) | - | small | routine: 3 visible, +0 more; crisis: 3 visible, +1 more; overflow: 3 visible, +3 more |
| tablet | 1.398 | 19.6 px (stack.t7.body) | - | large | routine: 3 visible, +0 more; crisis: 3 visible, +1 more; overflow: 3 visible, +3 more |
| pc | 1.160 | 16.2 px (stack.t3.body) | - | - | routine: 3 visible, +0 more; crisis: 4 visible, +0 more; overflow: 4 visible, +2 more |
| console | 2.275 | 31.8 px (stack.t3.body) | - | - | routine: 3 visible, +0 more; crisis: 4 visible, +0 more; overflow: 4 visible, +2 more |

- Lowest text contrast per skin (WCAG vs the fill it sits on; canon ui.rules.contrast: 4.5:1 body, 3:1 large text >= 18.66 px bold or 24 px): A 6.76:1 stack.t3.stamp (board routine; large text, AA 3:1); B 7.11:1 stack.t3.stamp (board routine; large text, AA 3:1); C 7.12:1 stack.t3.stamp (board routine; large text, AA 3:1)
- Minimum text (ui.rules.min_text): display 16 px, body 12 px, touch target 44 px (tech.ui_platform.touch_target_px); errors on every touch device.
- Text wider than its box (Chromium): none
- Image placeholders on boards: none
- Fonts on boards: Luckiest Guy, Montserrat (embedded woff2)
- Checks: 0 errors, 0 warnings.
  - i [phone] stack is lifted 24 px above the small jump zone at run time
  - i [phone_notch] stack is lifted 31 px above the small jump zone at run time
  - i [tablet] stack is lifted 75 px above the large jump zone at run time

Boards: HudTickets__routine__phone__C.png, HudTickets__crisis__phone__C.png, HudTickets__overflow__phone__C.png, HudTickets__routine__phone_notch__C.png, HudTickets__routine__tablet__C.png, HudTickets__routine__pc__C.png, HudTickets__routine__console__C.png, HudTickets__routine__phone__A.png, HudTickets__routine__phone__B.png, HudTickets__routine__phone__C__zones.png

### Facts: LobbyCreateMatch (measured by rr-ui-foundry; render = model + Chromium, not Roblox)

- Design space: phone screen 844x390, ScreenGui CoreUISafeInsets area 844x332 px (top bar 58 px, tech.ui_platform.topbar_inset).
- Layout: pin + scale with own fit (a smaller area shrinks a group only as much as it needs). px per design px: PC 1.16 (tech.ui_platform.layout); UIScale after the fit: Small 1, Medium 0.7649, Large 1 (Large = OQ-033).
- Skin on the main boards: C = assumed (OQ-001 default); other skins on closeups.
- Purpose: Pick crew size and difficulty, then join the queue; one obvious primary action.

| device | px per design px | smallest text | smallest target | touch zones | stack |
|---|---|---|---|---|---|
| phone | 1.000, 1.000 | 14 px (lbl_players) | 44 px (p1) | small | - |
| phone_notch | 1.000, 1.000 | 14 px (lbl_players) | 44 px (p1) | small | - |
| tablet | 1.398, 1.398 | 19.6 px (lbl_diff) | 61.5 px (p1) | large | - |
| pc | 1.160, 1.160 | 16.2 px (lbl_players) | 51 px (p1) | - | - |
| console | 2.275, 2.275 | 31.8 px (lbl_players) | 100.1 px (diff_next) | - | - |

- Lowest text contrast per skin (WCAG vs the fill it sits on; canon ui.rules.contrast: 4.5:1 body, 3:1 large text >= 18.66 px bold or 24 px): A 7.27:1 join.label (board open; large text, AA 3:1); B 3.82:1 panel.title (board joining; large text, AA 3:1); C 6.7:1 join.label (board joining; large text, AA 3:1)
- Minimum text (ui.rules.min_text): display 16 px, body 12 px, touch target 44 px (tech.ui_platform.touch_target_px); errors on every touch device.
- Text wider than its box (Chromium): none
- Image placeholders on boards: none
- Fonts on boards: Luckiest Guy, Montserrat (embedded woff2)
- Checks: 0 errors, 0 warnings.
  - i literal copy (not from canon; owner confirms): panel.title: 'CREATE MATCH'; lbl_players: 'PLAYERS'; lbl_diff: 'DIFFICULTY'; join.label: 'JOIN'; join.label: 'JOINING...'

Boards: LobbyCreateMatch__open__phone__C.png, LobbyCreateMatch__insane__phone__C.png, LobbyCreateMatch__joining__phone__C.png, LobbyCreateMatch__open__phone_notch__C.png, LobbyCreateMatch__open__tablet__C.png, LobbyCreateMatch__open__pc__C.png, LobbyCreateMatch__open__console__C.png, LobbyCreateMatch__open__phone__A.png, LobbyCreateMatch__open__phone__B.png, LobbyCreateMatch__open__phone__C__zones.png

## Images
- `contact.png` 856x1083 (0.93 MP)
  1. Hud phone 844x390 routine (C) — 1:1 true size
  2. Lobby phone 844x390 open (C) — 1:1 true size
  3. Hud PC 1280x720 routine, crop — fit x0.78
  4. Lobby PC 1280x720 open, crop — fit x0.61
- `closeups.png` 984x1038 (1.02 MP)

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
