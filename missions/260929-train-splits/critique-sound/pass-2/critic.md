# Critic brief — Carriage split sounds (rr-soundsmith plan for mission 260929-train-splits) — pass 2 (delta)

## Standing scores
S1 5 (pass 1) · S2 6 (pass 1) · S3 6 (pass 1) · S4 6 (pass 1) · S5 8 (pass 1) · S6 7 (pass 1). Bar: 8 on every criterion. Rule 8 applies to any you lower.

## Changes since pass 1
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

## Facts that changed since pass 1 (the rest stand)
### Facts (rr-soundsmith sheet; measured by audiolib, BS.1770-4)
| split_explosion | 2 | split_explosion.wav | 2.20 | -14.04 m_max | -2.93 | 0.0 | 132.9 | 1.19 | 0.11/0.17/0.71/0.01 | - | PASS |
| metal_tear | 3 | metal_tear.wav | 1.05 | -14.0 m_max | -2.94 | 0.0 | 49.1 | 0.51 | 0.02/0.10/0.84/0.03 | - | PASS |
| split_glass | 3 | split_glass.wav | 0.90 | -14.0 m_max | -4.64 | 0.0 | 165.1 | 0.4 | 0.00/0.00/0.59/0.41 | - | PASS |
| topple_crash | 3 | topple_crash.wav | 1.45 | -14.0 m_max | -2.3 | 0.0 | 97.8 | 0.54 | 0.22/0.01/0.77/0.00 | - | PASS |
| debris_rain | 4 | debris_rain.wav | 1.80 | -14.0 m_max | -3.72 | 0.0 | 84.2 | 1.08 | 0.01/0.17/0.75/0.08 | - | PASS |
| topple_crash_2 | 4 | topple_crash_2.wav | 1.45 | -14.0 m_max | -2.3 | 0.0 | 97.8 | 0.54 | 0.22/0.01/0.77/0.00 | - | PASS |
| wreck_scrape | 4 | wreck_scrape.wav | 2.70 | -14.0 m_max | -2.93 | 1.0 | 60.2 | 1.12 | 0.20/0.10/0.69/0.00 | - | PASS |
inversions: countdown_tick (t3, -13.1) over breakdown_bang (t2, -15.1); junction_beep (t3, -13.0) over breakdown_bang (t2, -15.1); metal_tear (t3, -13.0) over breakdown_bang (t2, -15.1); split_glass (t3, -13.4) over breakdown_bang (t2, -15.1); topple_crash (t3, -13.5) over breakdown_bang (t2, -15.1); cash_register (t4, -15.1) over stamp_slam (t3, -16.3); guard_whistle (t4, -15.0) over stamp_slam (t3, -16.3)
- fail: boiler_boom -> Actions -10 dB, Split -10 dB, UI -12 dB, Ambient -14 dB, Music -18 dB; attack 0.02 s, hold 0.5 s, release 1.6 s
| crisis | metal_tear | t3 Split | 3d @break | metal_tear (direct) | the metal can't hold any more: a strained groan ripping open, then SNAP | a cartoon zip-rip through sheet metal: a creaky groan, a rising rrrrip, a sharp snap, the… | horror metal screeches, whale-like groans, anything that outlasts the boom; nev… |
| crisis | split_glass | t3 Split | 3d @break | split_glass (direct) | the windows went too: bright shards riding over the boom | glass_smash's shards pitched up 3 semitones with the pane crack taken out (the boom alrea… | a second crack or boom, long tails, bottle-break cliches |
| crisis | topple_crash | t3 Split | 3d @wreck | topple_crash (direct) | the wreck hit the ground hard: heavy, clunky, final | a cartoon KER-RUNCH: a dull thud, wood splintering, a bin-lid clang drooping in pitch, gr… | car-crash glass, a second explosion, bone-crunch or body-fall sounds |
| crisis | debris_rain | t4 Split | 3d @break | debris_rain (direct) | it is still falling apart: small, clunky, a bit silly | a handful of wood chips, bolts and tin bits pattering onto a metal roof, dense then sparse | gunfire rhythm (keep the spacing random), shrapnel whizzes, rain-on-window ambi… |
| crisis | topple_crash_2 | t4 Split | 3d @wreck | topple_crash_2 (direct) | the second, bigger body lands a beat later: lower and a little further away | topple_crash's own file at PlaybackSpeed 0.84 (+-4%) and 3 dB under it (-16 vs -13 LUFS);… | a second upload (it is the same file), a hit identical to the first |
| crisis | wreck_scrape | t4 Split | 3d @wreck | wreck_scrape (direct) | the wreck is sliding away and running out of steam | a heavy metal box grinding over gravel: a rough grrrr that wobbles as the wreck rocks, sl… | brake squeal or rail screech (horror-adjacent), engine noise, anything that kee… |
Mapped: 39/39 events play a sound; 36/36 sounds are played by an event; 36/36 briefed; 14/14 3D sounds have an emitter role.
Files in this pass: 36/36 (the scope of this sheet). No file here (mapped and briefed above; not a coverage gap): none. 19 rr-game-feel events drawn in the timeline.
Voices: {"Alarms": 6, "Actions": 8, "UI": 4, "Split": 4}, max 16; new fail and crisis sounds always get a voice; a playing crisis alarm is cut only by the fail or another alarm.

## Images
- `contact.png` 792x1216 (0.96 MP)
  1. Ladder — 1:1 true size
  2. boiler_boom — fit x1.00
  3. alarm_coal — fit x1.00
  4. alarm_pressure — fit x1.00
  5. breakdown_bang — fit x1.00
  6. coupling_snap — fit x1.00
  7. glass_smash — fit x1.00
  8. passengers_scream — fit x1.00
  9. split_explosion — fit x1.00
  10. countdown_tick — fit x1.00
  11. junction_beep — fit x1.00
  12. lever_clunk — fit x1.00
  13. metal_tear — fit x1.00
  14. split_glass — fit x1.00
  15. stamp_slam — fit x1.00
  16. topple_crash — fit x1.00
- `split_timeline.png` 900x298 (0.27 MP)

## Rubric
Score only: S1, S2, S3, S4, S6 (anchors, scoring rules and issue format as in pass 1).

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
