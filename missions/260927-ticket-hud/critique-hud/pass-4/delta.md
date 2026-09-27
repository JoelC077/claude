# Delta since pass 3 (overall 7; B4) - from maker-log Round 3
Source saved before editing: critique-hud/round-3/src-before-critic-pass3/hud/. Edited src/hud/build.py, then reran it (all 6 boards, tokens.json, canvas.json rebuilt).
- C4-1 (blocks-8; NEEDS OWNER on the palette) -> the cash/fare stub changed from green (#56d994 to #23a05c) to mustard/brass (#f0c84a to #D9A627), with bar #8a5f1c and stamp #6b4712 (brass family). Crisis tickets (full and compact) now use `.card.crisisband`, a 6px ink band plus the ink rule instead of teal, so the only hue on a crisis ticket is red. Teal-cream and ink stay the base livery. No green remains in build.py or its outputs. Kit captions updated ("CASH - mustard stub", ink band on crisis).
- C5-1 -> covered by C4-1 (no green on the fare ticket).
- C1-1 -> non-crisis stamps get `.stamp.soft`: opacity .8 and rotate(-8deg) scale(.9).
- C6-1 -> the merge badge moved inside the stub corner (left 3px, top 3px, 20px, z-index 3, font 15px), so it no longer overhangs the frame.
- C2-1 -> the compact medallion glyph went from 17px to 18px (disc 21px). The full glyph is 23px. The timer bar was already 6px in CSS, so it is unchanged.
- C3-1 -> not changed (low, not blocks-8). Moving the pill down would take space from the 12px beam clearance.
