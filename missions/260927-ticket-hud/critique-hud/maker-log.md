# Maker log

## Round 1 (after critic pass 1, overall 6 / B5)
Source saved before editing: critique-hud/round-1/src-before-critic-pass1/hud/ (the older round-1/hud/ is the self-review copy). Edited src/hud/build.py, then reran it (all 6 boards, tokens.json, canvas.json rebuilt).
- B5-1 -> card fill flat teal-cream #E6E0C4 with a 4px teal #3E8C86 top band and a 1px ink rule under it; frame background now ink #15171c (the iron gradient is gone) with a mustard #D9A627 inner lining; the medallion ring, rivets, +N pill and merge-badge borders changed from brass #d9a441 to mustard #D9A627; a red buffer-beam bar (#C0392B, 6px, ink edge) now sits under full crisis tickets; tokens updated (card, teal, mustard, beam); the Kit intro text now describes the livery. The frame stays 3px ink, not 4px, so that only the newest crisis halo is 4px or more (B1-1 done-when). Every kind now carries the teal livery band, and risk also keeps its yellow/black stub.
- B1-1 -> older (compact) crises now have a 2px #C0392B frame (was a 3px red border) and a stub at filter:saturate(.6), with no buffer-beam. Only the newest crisis keeps the 4px ink + red halo, which now has a pulse glow (box-shadow 4px ring plus 14px red glow).
- B2-1 -> body subtext is now 15px weight 600 (was 13.5px/700) on a flat card (hatch removed); the timer bar is now 6px (was 5px). Titles moved down 2px to clear the band; the compact title line-height is 20px. Measured minimum font on Phone: 15px.
- B3-1 -> the "+N MORE" pill is now a flex item in the stack (.stack>.more), right-aligned to the ticket edge, with an 8px gap (5px gap + 3px margin). To keep it below the topbar, the stack gap went from 6 to 5px and the crisis slot padding from 5 to 4px. Measured in PhoneOverflow: pill y 36-63, top ticket starts at y 71, no overlap, and the pill clears the 36px topbar.
- B6-1 -> the hatch texture is removed; perforation is now 4 solid dots at 5px (was 3-6 dots at 4px, 80% opacity) on both full and compact tickets; rivets are 10px with a 2px ink edge (was 1.5px).
- B4-1 (optional) -> the teal crew stub moved to blue-teal #2F7F9A (gradient #4a9dba to #2F7F9A, bar #22607a), which puts it further from the green cash stub.

## Round 2 (after critic pass 2, overall 7 / B3, B4, B6)
Source saved before editing: critique-hud/round-2/src-before-critic-pass2/hud/. Edited src/hud/build.py, then reran it (all 6 boards, tokens.json, canvas.json rebuilt).
- B3-1 -> the phone stack bottom anchor moved from 112 to 123px (+11). The beam is now 4px (was 6px) and sits at top H-3 (was H-1), so it hangs 3px below the ticket instead of 7px. To keep PhoneOverflow under the topbar: stack gap 5->4px, .more margin-bottom 3->0 and padding 3/2->2/1px, newest-crisis slot padding 4px->2px top / 4px bottom. Measured (Chromium, 844x390): beam bottom y266 vs jump-zone top y278, so 12px clearance on Phone and PhoneOverflow. The PhoneOverflow pill is at y36-61 (clears the 36px topbar), the first ticket at y65 (4px gap). PC is unchanged (no jump zone).
- B6-1 -> the end notches changed from 16px ink dots at top -8px / H-8 (these crossed the gap) to 10px punches inset inside the frame: left 54px, top 1px and H-11 (centre 6px from the ticket edge). Measured: 0 notch pixels outside any ticket on all four phone boards.
- B4-1 (NEEDS OWNER: crew loses its own hue) -> the crew stub changed from blue-teal to neutral ink (gradient #2a2e33 to #15171c) with a mustard #D9A627 timer bar. The mustard/brass medallion carries the icon. The teal top band is now 6px (was 4px), with a 1px ink rule at 6-7px, so teal is the dominant livery hue. The kind accents are now only red, yellow/black and green, plus the teal and mustard livery.
- B5-2 -> covered by B4-1 (6px band). The titles moved down 2px (full top 7, body 29, compact top 6 with line-height 18) to clear the thicker band.

## Round 3 (after critic pass 3, overall 7 / B4)
Source saved before editing: critique-hud/round-3/src-before-critic-pass3/hud/. Edited src/hud/build.py, then reran it (all 6 boards, tokens.json, canvas.json rebuilt).
- C4-1 (blocks-8; NEEDS OWNER on the palette) -> the cash/fare stub changed from green (#56d994 to #23a05c) to mustard/brass (#f0c84a to #D9A627), with bar #8a5f1c and stamp #6b4712 (brass family). Crisis tickets (full and compact) now use `.card.crisisband`, a 6px ink band plus the ink rule instead of teal, so the only hue on a crisis ticket is red. Teal-cream and ink stay the base livery. No green remains in build.py or its outputs. Kit captions updated ("CASH - mustard stub", ink band on crisis).
- C5-1 -> covered by C4-1 (no green on the fare ticket).
- C1-1 -> non-crisis stamps get `.stamp.soft`: opacity .8 and rotate(-8deg) scale(.9).
- C6-1 -> the merge badge moved inside the stub corner (left 3px, top 3px, 20px, z-index 3, font 15px), so it no longer overhangs the frame.
- C2-1 -> the compact medallion glyph went from 17px to 18px (disc 21px). The full glyph is 23px. The timer bar was already 6px in CSS, so it is unchanged.
- C3-1 -> not changed (low, not blocks-8). Moving the pill down would take space from the 12px beam clearance.

## Round 4 (after critic pass 4, overall 7 / B2, B3)
Source saved before editing: critique-hud/round-4/src-before-critic-pass4/hud/. Edited src/hud/build.py, then reran it (all 6 boards rebuilt).
- C4-1 (blocks-8; NEEDS OWNER: soft vs full-ink stamp) -> `.stamp.soft` now uses opacity 1 (was .8). It keeps rotate(-8deg) scale(.9), so the softening comes only from the rotation and scale. The stamp ink #6b4712 is at full strength again, back to the pass-3 contrast of about 7:1.
- C4-2 (blocks-8) -> the crisis `.halo` changed from a box at left/right -7px (ink box plus a red :after) to a box at inset 0 with border-radius 11px. The ring is drawn only with box-shadow (3px red, then a 5px ink spread), and the pulse glow is added as further box-shadows (8px red spread and a 16px blur). The halo :after rule is removed. The frame of the full crisis ticket now starts at the same x as the compact tickets, and the frame width stays 290.
- C3-1, C4-3, C4-4 -> not changed (low, not blocks-8).

## Round 5 (after critic pass 5, overall 7 / B6)
Source saved before editing: critique-hud/round-5/src-before-critic-pass5/hud/. Edited src/hud/build.py, then reran it (all 6 boards rebuilt).
- C5-1 (blocks-8) -> the crisis `.halo` fill changed from transparent to ink #15171c. The slot's 4px bottom padding (and 2px top) under the full crisis ticket used to show the scene's teal/green through the halo; it is now ink, the same as the frame. Measured with Pillow on the COAL LOW bottom edge (x542-832, y248-268, 844x390): teal pixels 334 in pass 5 -> 0 now, on both Phone and PhoneOverflow. 4x zoom crop: pass-6/closeups.png.
- C5-2 -> the compact timer bar moved from bottom 2px to bottom 0 inside the card, which gives 2px more gap between the compact title and the bar.
- C5-3 -> compact (older) crisis stubs changed from saturate(.6) to saturate(.8). The full red and the halo stay only on the full (newest) crisis ticket. Kit caption updated to "stub 80% sat".
- Roblox export not changed: its crisis halo is already a solid ink Frame (no transparent gap), so C5-1 does not apply there. The export still has the v1 palette and does not include rounds 1-4.
