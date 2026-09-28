## Facts: KitBoard (measured by rr-ui-foundry; render = model + Chromium, not Roblox)

- Design space: phone screen 844x390, ScreenGui CoreUISafeInsets area 844x332 px (top bar 58 px, tech.ui_platform.topbar_inset).
- Layout: pin + scale with own fit (a smaller area shrinks a group only as much as it needs). px per design px: PC 1.16 (tech.ui_platform.layout); UIScale after the fit: Small 1, Medium 0.7649, Large 1 (Large = OQ-033).
- Skin on the main boards: C = assumed (OQ-001 default); other skins on closeups.
- Purpose: Kit board, not a screen: controls rows = cta, primary, secondary, icon buttons, then chips; columns = normal, hover, pressed, disabled (chips: off, on, pressed, disabled). Panels with and without close. Tickets: danger (crisis halo), risk, cash (stamp), info (count badge) full and compact, +N MORE.

| device | px per design px | smallest text | smallest target | touch zones | stack |
|---|---|---|---|---|---|
| phone | 1.000 | 14 px (t_danger.body) | 44 px (c_off) | small | - |
| pc | 1.160 | 16.2 px (t_danger.body) | 51 px (c_off) | - | - |

- Lowest text contrast per skin (WCAG vs the fill it sits on; canon ui.rules.contrast: 4.5:1 body, 3:1 large text >= 18.66 px bold or 24 px): A 3.19:1 b_secondary_pressed.label (board controls; large text, AA 3:1); B 3.82:1 pn_plain.title (board panels; large text, AA 3:1); C 3.19:1 b_primary_pressed.label (board controls; large text, AA 3:1)
- Minimum text (ui.rules.min_text): display 16 px, body 12 px, touch target 44 px (tech.ui_platform.touch_target_px); errors on every touch device.
- Text wider than its box (Chromium): none
- Image placeholders on boards: none
- Fonts on boards: Luckiest Guy, Montserrat (embedded woff2)
- Checks: 0 errors, 8 warnings.
  - W [phone] b_primary_normal sits in the thumbstick touch area (it takes the walk touch)
  - W [phone] b_primary_hover sits in the thumbstick touch area (it takes the walk touch)
  - W [phone] b_secondary_normal sits in the thumbstick touch area (it takes the walk touch)
  - W [phone] b_secondary_hover sits in the thumbstick touch area (it takes the walk touch)
  - W [phone] b_icon_normal sits in the thumbstick touch area (it takes the walk touch)
  - W [phone] b_icon_hover sits in the thumbstick touch area (it takes the walk touch)
  - W [phone] c_off sits in the thumbstick touch area (it takes the walk touch)
  - W [phone] c_on sits in the thumbstick touch area (it takes the walk touch)
  - i literal copy (not from canon; owner confirms): b_cta_normal.label: 'CTA'; b_cta_hover.label: 'CTA'; b_cta_pressed.label: 'CTA'; b_cta_disabled.label: 'CTA'; b_primary_normal.label: 'PRIMARY'; b_primary_hover.label: 'PRIMARY'; b_primary_pressed.label: 'PRIMARY'; b_primary_disabled.label: 'PRIMARY'; b_secondary_normal.label: 'SECONDARY'; b_secondary_hover.label: 'SECONDARY'; b_secondary_pressed.label: 'SECONDARY'; b_secondary_disabled.label: 'SECONDARY'; pn_close.title: 'WITH CLOSE'; pn_plain.title: 'NO CLOSE'; t_danger.title: 'COAL LOW!'; t_danger.body: 'Shovel coal in the firebox!'; tc_danger.title: 'COAL LOW!'; t_risk.title: 'JUNCTION AHEAD!'; t_risk.body: 'Safe or risky? Pull it!'; tc_risk.title: 'JUNCTION AHEAD!'; t_cash.title_s: 'FARE BANKED!'; t_cash.body: 'Station paid out'; tc_cash.title: 'FARE BANKED!'; t_info.title: 'CRATE LANDED!'; t_info.body: 'Grab it before it slides off!'; tc_info.title: 'CRATE LANDED!'; t_more.chip: '+2 MORE'

Boards: KitBoard__controls__phone__C.png, KitBoard__panels__phone__C.png, KitBoard__tickets__phone__C.png, KitBoard__controls__pc__C.png, KitBoard__controls__phone__A.png, KitBoard__controls__phone__B.png, KitBoard__controls__phone__C__zones.png
