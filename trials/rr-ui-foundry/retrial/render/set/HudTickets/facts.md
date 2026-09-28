## Facts: HudTickets (measured by rr-ui-foundry; render = model + Chromium, not Roblox)

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
