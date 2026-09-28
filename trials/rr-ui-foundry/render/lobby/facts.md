# Facts: LobbyCreateMatch (measured by rr-ui-foundry; render = model + Chromium, not Roblox)

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

Boards: LobbyCreateMatch__open__phone__C.png, LobbyCreateMatch__insane__phone__C.png, LobbyCreateMatch__joining__phone__C.png, LobbyCreateMatch__open__phone_notch__C.png, LobbyCreateMatch__open__tablet__C.png, LobbyCreateMatch__open__pc__C.png, LobbyCreateMatch__open__console__C.png, LobbyCreateMatch__open__phone__A.png, LobbyCreateMatch__open__phone__B.png, LobbyCreateMatch__open__phone__C__zones.png
