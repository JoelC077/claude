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

