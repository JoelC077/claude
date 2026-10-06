# Pass 3 delta: carriage-split sounds (Profile S, bar 8), before the final fresh pass

Mission 260929-train-splits. Maker: rr-soundsmith with RR_SOUND_PRESETS=src/sound.

Scores after pass 2: S1 8, S2 8, S3 8, S4 8, S5 8 (standing), S6 9. Every criterion is at or above the bar; this
round is the non-blocking polish only. Rollback: `critique-sound/round-2/` holds a full copy of src/sound as it
stood before this round.

Gates:
- validate --strict: PASS (0 errors, 0 warnings)
- synth: 36/36
- analyze: 7/7 PASS (final files)
- sheet and `sound crit --pass 3`: pass-3 files written
- build: PASS (luaparse on 4 Lua files, bible check 8/8)
- register dry runs: 7/7 pass, assets.json untouched

`split_timeline.png` in this folder is the redrawn split row.

## Fixes applied, with measured results
| id | done-when | measured | met |
|---|---|---|---|
| S4-4 Split voices and pitch | Voices lists "Split": 6; all seven split entries show a pitch range | facts.md: `Voices: {"Alarms": 6, "Actions": 8, "UI": 4, "Split": 6}`. Pitch ranges: split_explosion, metal_tear, split_glass and debris_rain 0.97-1.03 (were 0.96-1.04, 0.97-1.03, 0.93-1.07 and 0.90-1.10); the crashes keep theirs (topple_crash 0.96-1.04, topple_crash_2 0.806-0.874); wreck_scrape is 1.0-1.0 in the map because the client sets its PlaybackSpeed (see S2-4). At the +-3% extremes the boom still peaks at 6.3-6.7 ms and the tear snap lands at -7 to +8 ms from t 0 | yes |
| S2-4 scrape speed rule | the client sets PlaybackSpeed = clamp(35 / V, 0.7, 1.2) and fades 0.3 s once the wreck is under 2 studs/s; split_timeline.png shows the scrape at Speed 20, 35 and 50, each ending within 0.2 s of the slide end; row extended; rule noted in the wreck_scrape brief | Brief (moment) states the rule, with ctx.pitch carrying the speed. Lanes: Speed 20 (x1.20) ends 1.80 s against a slide end of 1.67 s (+0.13); Speed 35 (x1.00) ends 3.04 against 2.92 (+0.12); Speed 50 (x0.70) ends 4.28 against 4.17 (+0.11). Slide ends are ticked. The row runs to 4.5 s, not 4.0, because the Speed 50 lane ends at 4.28 s and would be off the image at 4.0 | yes |
| S1-3 breakdown_bang | stock sound, unchanged | see the line below | yes |

**S1-3:** breakdown_bang (stock, outside this mission) is unchanged. Its phone-ladder flags against metal_tear,
split_glass and topple_crash are accepted for the split (option c: a lost carriage outranks a breakdown alarm), and
the fix is queued for the rr-soundsmith library.

### How the scrape now ends
The wreck_scrape file is 3.1 s (was 2.7 s): the ramp is unchanged and a 0.45 s settle is appended. So the client's
stop, not the end of the file, closes the scrape at every speed, 0.13 s after the slide.

Slide end: taken as V/12 s from the snap, because break_spec's motion brakes from t 0 and R10's Lune test checks
that the drift reaches Speed at V/brake. The order's wording ("V/12 s from 0.3 s") would put each slide end 0.3 s
later. Under that reading the stop also comes 0.3 s later, so each lane still ends 0.13 s after its slide end. The
file needs about 3.05 s at Speed 35 and 3.0 s at Speed 50 for that, which is why it is 3.1 s. The old 2.7 s file
would have ended 0.22 s and 0.31 s early under that reading.

Measured on the new file: 3.10 s, M max -14.0, integrated -17.5, true peak -2.63 dBTP, phone loss 1.16 (dot -17.16),
lead 0.5 ms, tail 115 ms.

### Preview
`src/sound/preview/split_sequence_at_break.wav` now applies the client's rule at Speed 35: PlaybackSpeed 1.0 and a
0.3 s fade from 2.75 s, so the scrape ends at 3.05 s. Break 1's other layers are as before.

## Measured, final files
| id | file | length | M max | true peak | phone loss | in game (phone dot) | pitch |
|---|---|---|---|---|---|---|---|
| split_explosion | split_explosion.wav | 2.20 s | -14.04 | -2.93 | 1.19 | -10 (-11.19) | 0.97-1.03 |
| metal_tear | metal_tear.wav | 1.05 s | -14.0 | -2.94 | 0.51 | -12.5 (-13.01) | 0.97-1.03 |
| split_glass | split_glass.wav | 0.90 s | -14.0 | -4.64 | 0.40 | -13 (-13.40) | 0.97-1.03 |
| topple_crash | topple_crash.wav | 1.45 s | -14.0 | -2.30 | 0.54 | -13 (-13.54) | 0.96-1.04 |
| debris_rain | debris_rain.wav | 1.80 s | -14.0 | -3.72 | 1.08 | -16 (-17.08) | 0.97-1.03 |
| topple_crash_2 | topple_crash.wav (same file) | 1.45 s | -14.0 | -2.30 | 0.54 | -16 (-16.54) | 0.806-0.874 |
| wreck_scrape | wreck_scrape.wav | 3.10 s | -14.0 | -2.63 | 1.16 | -16 (-17.16) | 1.0, client clamp(35/V, 0.7, 1.2) |

## Open
- Studio listening test pending (owner). Nobody has heard the sounds; levels, roll-off and phone loss are modelled.
- No .ogg: ffmpeg is absent. Roblox takes the WAVs (87-298 KB).
- TrainSplitClient must implement the scrape rule. It is in final/SOUNDS.md route A: `Sound.event("wreck_scrape",
  {pitch = math.clamp(35 / V, 0.7, 1.2)})` returns the play entry; tween `entry.inst.Volume` to 0 over 0.3 s, then
  `entry.inst:Stop()`.

## Stays with the owner
1. Listen: the preview, then Studio.
2. Upload the six files in `src/sound/final/`.
3. Run the seven `register` commands in final/SOUNDS.md (topple_crash_2 reuses topple_crash's id).
4. `sound build`, then `validate --release`.
5. For route B, paste the ids into TrainSplitConfig.

## Files changed this round
- `src/sound/soundmap.json`: Split cap 6, pitch ranges, wreck_scrape brief and pitch.
- `src/sound/recipes.py`: wreck_scrape is 3.1 s, with the settle after the slide.
- `src/sound/make_final.py`: the preview applies the scrape rule.
- `src/sound/split_timeline.py`: scrape lanes at three speeds, row to 4.5 s, lanes drawn only while sounding.
- Refreshed: ph/, sheet/ (with split_timeline.png), build/, final/ (six WAVs and SOUNDS.md), preview/.
- `critique-sound/round-2/` (rollback); `critique-sound/pass-3/` (written by `sound crit`, plus split_timeline.png
  and this file).

Next, not run here: the pre-flight command printed by `sound crit`:

```
python3 <skills>/multiuse-critic/scripts/critic_kit.py build <M>/critique-sound --pass 3 --kind full --profile S --role "senior game audio designer" --images closeups.png
```

Adding `split_timeline.png` to `--images` lets the fresh critic see the split row with the three scrape speeds.
