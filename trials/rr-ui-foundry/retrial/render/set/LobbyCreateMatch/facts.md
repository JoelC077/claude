## Facts: LobbyCreateMatch (measured by rr-ui-foundry; render = model + Chromium, not Roblox)

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
