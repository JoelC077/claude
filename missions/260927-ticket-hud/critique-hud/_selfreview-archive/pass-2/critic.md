# Critic brief — Risky Rails ticket notification HUD (remake) — pass 2 (delta)

## Standing scores
B1 7 (pass 1) · B2 8 (pass 1) · B3 7 (pass 1) · B4 7 (pass 1) · B5 7 (pass 1) · B6 7 (pass 1). Bar: 8 on every criterion. Rule 8 applies to any you lower.

## Changes since pass 1
Below bar: B1 7, B3 7, B4 7, B5 7, B6 7
Open: B1-1 newest crisis compact (PhoneCrises); B1-2 red-halo wall (overflow); B3-1 unanchored +1 MORE chip, stack top at 39; B4-1 stub hidden by medallion; B5-1 iron/brass not legible; B6-1 kit dead space.
Applied: BREAKDOWN full on PhoneCrises; halo only on newest crisis, older crises red 3px frame ring; chip overlaps top ticket's top-left (top -14px), stack top y=80; medallion 42->36 (compact 30->28) centred on 54px stub, 9px kind colour each side; 2px brass #d9a441 pinline inside every frame, rivets 8->10px; kit board 1400x1180 -> 1320x1080.

## Facts that changed since pass 1 (the rest stand)
- Phone: stack right 14px, bottom 112px (jump button zone top at y~278); overflow board stack top y=80 (chip y=66) (topbar ends 36).
- Ticket 290x64 full / 290x40 compact; newest crisis +10px halo, older crises 3px red frame; gap 6px; body 13.5px Montserrat 700 #463c2e on card #f7edd3-#e7d4a6; titles Luckiest Guy 20 (compact 18).

## Images
- `contact.png` 856x1167 (1.00 MP)
  1. Phone overflow 844x390 — 1:1 true size
  2. Phone crisis — fit x0.47
  3. Phone routine — fit x0.47
  4. Phone crises+junction — fit x0.47
  5. PC 1280x720 — fit x0.31
  6. Kit — fit x0.21

## Rubric
Score only: B1, B3, B4, B5, B6 (anchors, scoring rules and issue format as in pass 1).

## Output
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
