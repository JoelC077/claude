# Pass 2 delta: carriage-split sounds (Profile S, bar 8)

Mission 260929-train-splits. Maker: rr-soundsmith with RR_SOUND_PRESETS=src/sound. Rollback (round 1, frozen before
any edit): `critique-sound/round-1/` holds soundmap.json, assets.json, recipes.py and make_final.py.

The sheet is built from `src/sound/sheet_src/`: the stock placeholders plus the six delivered files and
topple_crash_2 (links). The split row is in `split_timeline.png` (next to this file; source
`src/sound/sheet/split_timeline.png`, drawn by `src/sound/split_timeline.py`).

Gates:
- validate --strict: PASS (0 errors, 0 warnings)
- synth: 36/36
- analyze: 7/7 PASS (final files)
- sheet and crit: pass-2 files written
- build: PASS (luaparse on 4 Lua files, bible check 8/8)

## Criteria below the bar after pass 1
| criterion | pass 1 |
|---|---|
| S1 Signal and hierarchy | 5 |
| S2 Timing and envelope | 6 |
| S3 Clarity on a phone | 6 |
| S4 Mix safety and fatigue | 6 |
| S6 Coverage and polish | 7 |

S5 Style match (8) is at the bar.

## Fixes applied, measured against each done-when
| id | done-when | measured now (pass 1) | met |
|---|---|---|---|
| S1-1 split_explosion phone band | phone loss <= 1.4 dB; ladder phone dot >= -11.4 LUFS, right of glass_smash, coupling_snap and breakdown_bang, left of boiler_boom -10.66; phone share >= 0.65; target about -10, M max -14, TP <= -1 dBTP | phone loss 1.19 (3.07); dot -11.19 (-13.07): right of glass_smash -11.46, coupling_snap -12.04 and breakdown_bang -15.13, left of boiler_boom -10.66; phone share 0.71 (0.44); level -10; M max -14.04; TP -2.93 | yes |
| S4-1 Split group | group column reads Split for the five; Voices lists "Split": 4; a split uses only the boom's voices in Alarms; no t2 row ends at the t3 step | facts.md: metal_tear, split_glass and topple_crash read t3 Split; debris_rain, wreck_scrape (and topple_crash_2) read t4 Split; split_explosion reads t2 Alarms. `Voices: {"Alarms": 6, "Actions": 8, "UI": 4, "Split": 4}`. The only t2 split row is the boom at -10. Tear and glass are t3 at -12.5 and -13 (unchanged). Split is not in the split duck; the fail duck has Split -10 | yes |
| S2-1 split timeline row | the row exists and shows the tear snap and the boom peak within 10 ms of 0 | sheet.py draws `via: feel` events only, so `split_timeline.png` draws the carriage_split row from -0.3 to 3.5 s: tear -0.25, boom 0, glass 0, scrape 0.3, debris 0.8, topples 1.5 and 2.0 (x0.84), with the note that the split has no rr-game-feel channels (TrainSplitClient's shake is drawn as markers). Tear snap and boom peak both fall in the first 10 ms bin (+5 ms). Sample peaks: tear snap at 250.3 ms in its file (+0.3 ms), boom at 6.5 ms | yes |
| S3-1 topple_crash phone band | phone loss <= 1.5 dB; dot >= 2 LU right of the scrape and debris dots and right of every t4 dot; phone share >= 0.70; keep -13 | phone loss 0.54 (2.85); share 0.77 (0.51); dot -13.54 (-15.85): 3.5 LU right of scrape -17.12 and debris -17.08, right of the top t4 dot (guard_whistle -15.04); level -13. Splinter burst and bin-lid clang at 0.8-2.5 kHz, both inside the first 80 ms | yes |
| S2-3 tails | metal_tear and topple_crash fade the last 150 ms to silence; tail >= 10 ms; waveforms reach zero before the tile edge (extend the crash to 1.8 s if its clang still rings at 1.45 s) | tails: metal_tear 49.1 ms (1.9), topple_crash 97.8 ms (2.0); every split file is exactly zero for its last 20 ms. The clang does not ring at 1.45 s: the level before the fade is -56 dB re peak, so the crash stays 1.45 s. Root cause of the old 2 ms tails: the render's DC step lifted the "silent" end by the signal mean (-53 dBFS on the tear). `_finish()` now high-passes at 20 Hz, fades, and zeroes the mean under the fade window | yes |
| S6-1 delivered files | not named or tagged PLACEHOLDER: final/metal_tear.wav ... wreck_scrape.wav, tagged self-made; sheet tiles from the finals; register as far as the gate allows | final/{metal_tear, split_explosion, split_glass, debris_rain, topple_crash, wreck_scrape}.wav: PCM bit-identical to the synth output. INFO: INAM = id, ICMT "... self-made". The six tiles carry no PLACEHOLDER label. Register dry runs pass for all seven ids (topple_crash_2 on topple_crash.wav, same id). Controls: the ph/ copy is refused (PLACEHOLDER tag), and without `--id` the gate stops ("needs --id N") | yes, up to the asset id |

Quick fixes (not blocking):

| id | asked | measured now (pass 1) |
|---|---|---|
| S1-2 | split_glass as its own file: +3 semitones, no pane-crack transient, shards only, <= 0.9 s, air >= 0.40 | r_split_glass: glass_smash with its first 15 ms (the crack) cut, high-passed at 2.2 kHz, resampled +3 semitones; 0.90 s (1.10); air 0.41 (0.29); phone loss 0.40 |
| S3-2 | wreck_scrape low-pass 2.5 kHz and a 0.6 s fade-in from -12 dB | done: air band 0.000; the envelope peak moved to 0.5-0.6 s; phone loss 1.12 (1.06) |
| S2-2 | split_explosion high-pass sweep 20 to 500 Hz from 1.0 to 1.4 s; 2.2 s with a 300 ms fade; sub <= 0.22 | done: 2.20 s (2.75); fade 1.88-2.18 s, then 20 ms of zero; sub 0.11 (0.32) |
| S4-2 | a second topple variation for the 2.0 s hit: PlaybackSpeed 0.84, -3 dB, both +-4%, listed in the soundmap | `topple_crash_2`: `"synth": "topple_crash"` gives the same samples (checked), so there is no second upload; pitch 0.806-0.874; t4 trim -1 = -16 LUFS (3 dB under -13); event `topple_crash_2`. topple_crash's pitch is now 0.96-1.04 |
| S4-3 | how RR_Sound combines concurrent ducks; state the rule; net Ambient duck <= 14 dB | `Sound.step` takes, per group, the deepest active rule (minimum dB; attack and release from that rule), so concurrent ducks do not add. A rule holds while its trigger plays, plus hold. Net Ambient in a split is -12 (split) over -8 (crisis), so no values changed; the rule is stated in the split rule's note. Correction: pass 1's note ("released by 1.22 s") was wrong; the duck holds for the boom's whole 2.2 s plus 0.3 s. Moving the layers to Split makes that harmless |

One consequential change, not asked for: after S3-1 the crash (-13.54 on a phone) overtook the tear (-13.81). The
tear's low end was moved up (wobble high-pass to 450 Hz, less 310 Hz plate mode, smaller thunk), so its phone loss
went 1.31 to 0.51. Phone order is now boom -11.19 > tear -13.01 > crash -13.54 > topple_crash_2 -16.54 > debris
-17.08 / scrape -17.12. The snap timing and tail are unchanged.

## Open issues
| id | problem | done-when |
|---|---|---|
| O1 (S1) | facts.md "Hierarchy on a phone speaker" flags metal_tear (t3, -13.0), split_glass (t3, -13.4) and topple_crash (t3, -13.5) over breakdown_bang (t2, -15.1). breakdown_bang is a stock alarm that loses 4.1 dB on a phone; the stock countdown_tick and junction_beep sit over it too. The flags follow from S4-1 (t3 at current levels) plus S3-1: the crash cannot drop below -14.1 on a phone while keeping -13 and a share >= 0.70 (tried: phone loss 0.86 gives share 0.66; 1.24 gives 0.56). Options: (a) fix breakdown_bang's phone band (clears all five flags); (b) trim tear -0.9 and glass -0.8 dB (leaves the crash flag); (c) accept, since a lost carriage outranks a breakdown alarm | the facts.md phone-hierarchy list names no split sound, or the orchestrator accepts (c) |
| O2 | nobody has heard the sounds (cloud, no speakers); levels, roll-off and phone loss are modelled | the owner's Studio listening test, starting with preview/split_sequence_at_break.wav |
| O3 | wreck_scrape is timed for Speed 35: it runs about 1 s past the slide at Speed 20 and stops 1.3 s early at Speed 50 | the owner accepts it, or TrainSplitClient stops or retimes it by V/brake |
| O4 | no .ogg: ffmpeg and imageio-ffmpeg are absent; Roblox takes the WAVs (87-259 KB) | n/a unless the owner wants .ogg |

## Stays with the owner
1. Listen: the preview, then Studio.
2. Upload the six files in `src/sound/final/`.
3. Run the seven `register` commands in final/SOUNDS.md with the asset ids (topple_crash_2 reuses topple_crash's id).
4. `sound build`, then `validate --release`.
5. For route B, paste the ids into TrainSplitConfig.

## Files changed in round 1
- In `src/sound/`: soundmap.json, recipes.py, make_final.py.
- New in `src/sound/`: split_timeline.py, sheet_src/, sheet/split_timeline.png.
- Refreshed in `src/sound/`: ph/, sheet/, build/, preview/split_sequence_at_break.wav.
- `src/sound/final/`: the six `<id>.wav` files plus SOUNDS.md (the old rr_split_*.wav files are removed).
- In `critique-sound/`: round-1/ (rollback), pass-2/ (written by `sound crit`, plus delta.md and split_timeline.png).

Next, not run here: the pre-flight command printed by `sound crit`:

```
python3 <skills>/multiuse-critic/scripts/critic_kit.py build <M>/critique-sound --pass 2 --kind full --profile S --role "senior game audio designer" --images closeups.png
```

Adding `split_timeline.png` to `--images` lets the critic see the split row.
