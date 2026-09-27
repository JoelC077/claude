# Delta since pass 5 (overall 7; B6) - from maker-log Round 5
Source saved before editing: critique-hud/round-5/src-before-critic-pass5/hud/. Edited src/hud/build.py, then reran it (all 6 boards rebuilt).
- C5-1 (blocks-8) -> the crisis `.halo` fill changed from transparent to ink #15171c. The slot's 4px bottom padding (and 2px top) under the full crisis ticket used to show the scene's teal/green through the halo; it is now ink, the same as the frame. Measured with Pillow on the COAL LOW bottom edge (x542-832, y248-268, 844x390): teal pixels 334 in pass 5 -> 0 now, on both Phone and PhoneOverflow. 4x zoom crop: pass-6/closeups.png.
- C5-2 -> the compact timer bar moved from bottom 2px to bottom 0 inside the card, which gives 2px more gap between the compact title and the bar.
- C5-3 -> compact (older) crisis stubs changed from saturate(.6) to saturate(.8). The full red and the halo stay only on the full (newest) crisis ticket. Kit caption updated to "stub 80% sat".
- Roblox export not changed: its crisis halo is already a solid ink Frame (no transparent gap), so C5-1 does not apply there. The export still has the v1 palette and does not include rounds 1-4.
