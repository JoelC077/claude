# Facts: HudTickets (measured by rr-ui-foundry; render = model + Chromium, not Roblox)

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

Boards: HudTickets__routine__phone__C.png, HudTickets__crisis__phone__C.png, HudTickets__overflow__phone__C.png, HudTickets__routine__phone_notch__C.png, HudTickets__routine__tablet__C.png, HudTickets__routine__pc__C.png, HudTickets__routine__console__C.png, HudTickets__routine__phone__A.png, HudTickets__routine__phone__B.png, HudTickets__routine__phone__C__zones.png
