# Pass 2 delta: carriage-split fx pack (maker's measured report, not a score)

Board: `M/src/fx/preview/board` (copied here by `vfx crit`): split_explosion, torn_edge_smoke, topple_dust, glass_split,
boiler_burst, interior_split. Rollback: `M/critique-fx-split/round-1/` (pass-1 vfx.json + budgets.json, read-only).
Numbers come from facts.md or from maker pixel measures on the tool's own strips and POVs (stand-in textures, stand
geometry). Studio test pending (owner).

## Criteria below the bar (pass 1, bar 8)
F1 Signal 6 · F2 Form and motion 5 · F3 Colour and value 6 · F4 Phone read 7 · F5 Style match 7 · F6 Polish 6 ·
overall 5 (F2).

## Read first: names, board, stand
- **glass_split** is the mission variant of glass_burst; glass_burst is unchanged for the windows crisis. It is called
  glass_split, not split_glass, because the board labels a tile by the first word of the name, and "split" would clash
  with split_explosion. TrainSplitClient now calls `VFX.burst(pane, "glass_split")` for the two panes.
- **interior_split** is a preview-only twin of split_explosion (identical layers) on an anchor inside coach A. It is
  needed because the preview gives each burst one POV (its anchor's near camera) and rejects `preset@camera`. It is
  not exported and not wired. Its budget set is carriage_split_inside, with the same cost.
- **derail_explosion** was measured from roof3p in the same config: 0 of 68 particles visible (all hidden by the train
  at rail level), 0.00% of the screen. It is left off this board. With 7 names, the ~1 MP sheet cap drops
  torn_edge_smoke's strip ("Not on the sheets" in facts), and F2-3 and F3-1 need that strip.
- **Stand settings (preview only):** Bogie and Boiler near_camera were set to roof3p for the comparison, and
  glass_split has a shorter strip window.
- **Stand caveat:** the stand has no tear and all its cameras look forward, while players look back at the tear. So
  wind-carried soot, smoke and debris drift toward the camera in these tiles, and away from players in game. This
  inflates the roof shares and the trail spans.

## Issues: done-when, fix, measured

**F2-1 glass shards** (small and faint)
- Done when: the faint flag clears (p90 >= 25); shards >= 5 px wide in a 1:1 door1p frame; >= 12 live at t=1 s in the strip.
- Fix: glass_split, 23 shards on one emitter. The puff layer was dropped, which frees an emitter for the torn embers.
  Size 0.7 +- 0.2, Lifetime 1.4-1.8 s, random Rotation and RotSpeed, three glint dips 0 -> 0.6 -> 0, LightEmission 0.8,
  Acceleration -25 with Drag 1.2 (a floatier fall).
- Measured: p90 65 (+31/65), no faint flag. 17 shard blobs in pov_glass_split (768x432, 1:1): median width 8 px,
  p25 6 px, min 4 px. Strip at t=1 s: 23 live. **Met** (one blob is 4 px).

**F2-2 topple dust band**
- Done when: the 0.4 s strip shows one unbroken band >= 5 studs tall; door1p puff saturation >= 0.15 and p90 >= 70.
- Fix: 16 puffs (asked 14). Size 6 -> 8 (at 0.25) -> 8.5 over 1.5-1.7 s (asked 3 -> 10, which is only 4.75 studs at
  0.4 s and left the band broken). Box 30x3x3 along the body, Speed 12-16, Drag 3, Acceleration -2, wind drift on.
  Colour dust_cream #CFC8A6: the asked ~#CFC3A2 fails validate (sepia/desert band), so the hue moved about 6 deg.
- Measured: the 0.4 s strip has one run of 33.5 studs with no gap (the scale avatar is drawn over the band). Band
  height median 5.1 studs (p10 3.5). door1p p90 118 (+67/118), saturation mean 0.25, median 0.22. **Met.**

**F2-3 torn smoke continuity**
- Done when: a continuous plume with no gap longer than one puff width over the first 15 studs (sky and pasture
  strips); roof3p phone p90 >= 40.
- Fix:
  - Size 1.5 -> 5.
  - Transparency 0 -> 0.1, then fading over the last 40%. The asked 0.4 start gave a phone p90 of 13-21.
  - Rate 14, Lifetime 1.4-1.8 s: live 19 phone / 28 PC, within 20/28 including embers.
  - Source box 2.5x3x19, and Acceleration 11 / Drag 0.2 for a steep column.
- Measured: along the plume axis over 0-15 studs, the largest gap is 1.25 studs (sky) and 1.75 studs (pasture), at
  about 9.5 studs of travel, where a puff is about 3.6 studs wide. The plume reaches 15.9 studs (sky) and 14.0 studs
  (pasture). roof3p phone p90 40 (-14/40); PC 33. **Met** (the pasture plume reaches 14.0 of 15 studs).

**F2-4 fire core and shock dust**
- Done when: with the Light off, a warm fireball >= 20 studs across at 0.12-0.4 s that touches the soot at 0.4 s, and
  a low dust band reaching >= 10 studs each side of the anchor at 0.4 s.
- Fire core fix: its own burst of 6 puffs.
  - Size 13 -> 19 over 0.7-0.85 s (asked 8 -> 22 over 0.6 s). The 13-stud birth gives the 20-stud pop at 0.12 s; the
    19 end keeps phone fill under 7000.
  - Colour white -> yellow -> orange -> charcoal (soot_black).
  - Speed 66-80, Spread 80, Drag 4 with WindAffectsDrag, the same drag as the soot (same wind drift).
- Shock fix: 7 flat puffs in a horizontal fan, SpreadAngle [10,180] on dir +X (the tool maps [180,10] to a vertical
  fan). Speed 34-42, Drag 0.8, Size 4 -> 12 over 0.75-0.85 s. Colour ballast grey -> cream, so it reads on the pale
  strip sky and against the navy body.
- Measured (maker run with the light layer removed): the fireball is 20.5 studs across at 0.12 s and 34.2 at 0.4 s,
  and touches the soot at 0.4 s. The shock layer alone reaches 12.4 studs back and 12.1 forward at 0.4 s. In the full
  strip the fireball covers the rear part of the band (7.0 back / 13.2 forward visible). **Met.**

**F1-1 BIG**
- Done when: roof3p split share >= 30% with part above the horizon; interior tile share >= 35%; at roof3p the split's
  share and p90 beat derail and boiler. Also: the burst is >= 30 studs across by 0.4 s, and soot rises about
  12 studs/s so the cloud top clears the roof by >= 15 studs at 1 s.
- Fix:
  - The F2-4 changes above.
  - Soot: 5 puffs, Size 6 -> 11 -> 12, offset +7, terminal rise 12 studs/s (Acceleration 48 / Drag 4).
  - roof3p POV at 0.35 s. At 0.5 s the fire had cooled and p90 was 32-55, below boiler.
  - The interior twin is 17 studs from coach1p, with its POV at 0.25 s.
- Measured:
  - roof3p split: 61.4% of the screen, p90 107 (+58/107). Boiler: 0.64%, p90 85. Derail: 0.00% (0 of 68 visible).
  - 2,164 split pixels (0.7% of the frame) sit above the horizon row at 0.35 s (split-only render).
  - Interior tile: 38.3% (+68/166).
  - Burst: 36.3 studs across at 0.4 s.
  - Soot top: y 34.4 at 1 s, which is 20.4 studs above the roof.
- **Met** (the part above the horizon is small at 0.35 s).

**F3-1 torn smoke colour and ember glow**
- Done when: roof3p puffs lighter than the roof and darker than the sky; the dark strip shows >= 10 studs of plume;
  ember glow hue 20-40 deg with saturation >= 0.5.
- Fix:
  - torn_grey #60645E (asked ~#6E726C). It is 14 luma darker so the column reads on the pale sky at phone rates.
    LightInfluence 0.3.
  - Embers on their own emitter: sparkle texture, firebox #FF7A22 (hue 24 deg), LightEmission 1, 2 per second, size
    0.9 -> 0.4.
  - Glow light Brightness 2.
- Measured:
  - roof3p smoke luma over the roof is 77 (PC) and 79 (phone), against a roof of 59-60.
  - Over the sky it is 163 (PC) and 159 (phone), against a sky of 181-182.
  - The dark strip plume is 15.1 studs.
  - Ember cores on the dark strip: hue 24.6 deg, saturation 0.58 (6 px).
  - The light's glow dot around them: hue 24.5 deg, saturation 0.38. The preview draws lights as dim glow dots.
- **Met for the embers; the glow dot reads 0.38.**

**F4-1 phone tiles for bursts**
- Done when: each burst's phone p90 is >= 80% of its PC value.
- The tool cannot make these tiles:
  - `vfx preview` composites a burst only once, on the PC plate (768x432) of its anchor's stand.near_camera.
  - `--phone` renders phone plates only for look POVs, and those carry loops only (steady state at phone rates).
  - A preset cannot be named at a camera (`split_explosion@coach1p` gives "not a preset or look").
  - So no burst gets an 844x390 tile or a phone luma line.
- Priority-1 bursts keep rate scale 1.0 on phones (same particle counts). Only the plate differs: no Bloom, SunRays or
  shadows, at 844x390.
- The one phone line available is the torn smoke: phone p90 40 vs PC 33 (121%). **Tool limit.**

**F6-1 debris trail scythe** (polish, not blocking)
- Done when: no trail spans more than 25% of the roof3p frame height, and every visible head shows orange.
- Fix: a new trail, split_streak, on both debris layers; debris_smoke and debris_spark stay for derail and boiler.
  - Width 0.4, WidthScale 1 -> 0, Lifetime 0.12 s.
  - Colour firebox orange at the head -> ironwork soot grey at the tail; Transparency 0 -> 1.
  - Chunks: carry 0.6 (heavy chunks keep some train momentum), thrown straight up.
- Measured (debris-only render at roof3p, t=0.35): 6 streaks, 3 of them spanning 33-38% of the frame height. 5 of 6
  heads are orange.
- Why the span test fails here: the preview draws each debris trail along the whole path since launch. Renders are
  pixel-identical for Trail Lifetime 0.2 and 0.12, so this measures the debris flight, not the Trail. In Roblox a
  0.12 s trail at about 55 studs/s is about 7 studs, roughly 20-25% of the frame at 20-25 studs.
- **Not met in the preview.**

## Gates (this board)
- `validate --strict` PASS: 18 presets, 0 errors, 0 warnings, flash safety included.
- `budget` PASS on every set. carriage_split (split_explosion, torn_edge_smoke, topple_dust, glass_split x2, cruise) on
  phone: steady 74/400, peak 154/800, emitters 11/12, fill 6946/7000, lights 5/8, debris 8/8.
- `build --only split_explosion torn_edge_smoke topple_dust glass_split` PASS: luaparse on all 6 files, canon ok. The
  interior twin is not exported.
- Preview: 0 WARNs. The note "interior_split mostly hidden from coach1p" comes from the stand coach's closed ceiling
  and end wall.

## Kept
- Flash pulse unchanged (8 for 0.4 s at the snap).
- Round black cartoon soot and orange-headed debris streaks by 0.4-1 s.
- Wind drift on every emitter.
- Crisis bursts at priority 1, at full phone rate, inside the budget.

## Next (not run by the maker)
`python3 <critic>/scripts/critic_kit.py build M/critique-fx-split --pass 2 --kind full --profile F --role "senior VFX and lighting artist" --images closeups.png`
(as printed by `vfx crit`).
