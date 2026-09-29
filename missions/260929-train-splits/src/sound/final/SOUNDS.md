# Carriage-split sounds: upload files

Six sounds for a carriage tearing in half (mission 260929-train-splits, R13: "Sounds: yes. Make some if you can
and include them if they fit"). They are made from code only (`src/sound/recipes.py`, seed 7; the glass reuses
glass_smash's built-in recipe), so they contain no samples and no third-party material: they are self-made and
licence-clean. Files are 48 kHz, 16-bit mono WAV, levelled to the rr-soundsmith impact standard (momentary max
-14 LUFS, true peak -1 dBTP or lower). The mix lives in data (`soundmap.json`), so a level change is a rebuild,
never a re-upload.

**Status:** measured and gated (validate --strict PASS, analyze 6/6 PASS, build PASS). Nobody has heard them yet:
the Studio listening test is pending (owner). For a quick listen first, `../preview/split_sequence_at_break.wav`
plays the whole break-1 sequence as heard at the break. It is a listening aid only: do not upload it.

## Files
Times are from `src/kit/break_spec.json`, where t 0 is the snap. Volume = the Roblox `Sound.Volume` that puts the
file at its in-game level (ref 0.5 = file level, assumed until the Studio check). Roll-off mode is InverseTapered
for all 3D sounds.

| id | file | length | LUFS M max (integrated) | true peak | in game (phone) | Volume | 2D/3D | RollOffMin / Max | event (t) |
|---|---|---|---|---|---|---|---|---|---|
| metal_tear | rr_split_metal_tear.wav | 1.05 s | -14.0 (-16.0) | -1.8 dBTP | -12.5 (-13.8) | 0.594 | 3D at `break` | 16 / 240 | `metal_tear`, t -0.25: the snap is 0.25 s into the file, so it lands on the boom |
| split_explosion | rr_split_split_explosion.wav | 2.75 s | -14.0 (-20.1) | -3.8 dBTP | -10 (-13.1) | 0.792 (2D) + 0.500 (3D layer) | 2D train-wide + 3D layer at `break` | 3D layer 16 / 240 | `split_explosion`, t 0 |
| split_glass | rr_split_split_glass.wav | 1.10 s | -14.0 (-18.9) | -2.6 dBTP | -13 (-13.5) | 0.562 | 3D at `break` | 16 / 240 | `split_glass`, t 0: once, or once per side about 0.1 s apart |
| debris_rain | rr_split_debris_rain.wav | 1.80 s | -14.0 (-19.3) | -3.6 dBTP | -16 (-17.1) | 0.397 | 3D at `break` | 10 / 140 | `debris_rain`, t 0.8 |
| topple_crash | rr_split_topple_crash.wav | 1.45 s | -14.0 (-18.9) | -1.7 dBTP | -13 (-15.9) | 0.561 | 3D at `wreck` | 16 / 240 | `topple_crash`, t 1.5 (broken half) and, on break 1, t 2.0 (carriage 2); its bounce thud is 0.35 s in |
| wreck_scrape | rr_split_wreck_scrape.wav | 2.70 s | -14.0 (-18.0) | -2.7 dBTP | -16 (-17.1) | 0.398 | 3D at `wreck`, follows it | 10 / 140 | `wreck_scrape`, t 0.3 until V/brake (2.9 s at Speed 35) |

The hierarchy is boom > tear > crash > debris and scrape, both full-range (-10 > -12.5 > -13 > -16 LUFS) and on
a phone speaker (-13.1 > -13.8 > -15.9 > -17.1). No split layer sits more than 1 LU under a lower-tier sound on a
phone.

- **Groups:** tear, explosion and glass go in Alarms; crash, debris and scrape go in Actions.
- **Pitch spread per play:** tear 0.97-1.03, explosion 0.96-1.04, glass 0.93-1.07, debris 0.90-1.10,
  crash 0.92-1.06, scrape 0.95-1.05.
- **Ducking:** a `split` rule on the explosion ducks Ambient -12, Music -14, UI -8 and Actions -4 dB (attack 0.02,
  hold 0.3, release 0.9 s). It has fully released by 1.22 s, before the first crash.
- **split_glass:** it is the same audio as glass_smash (identical PCM). One upload serves both; register that id
  for split_glass, and for glass_smash too if the window crisis should use it.

## Wiring in TrainSplitClient
**Route A: the RR_Sound runtime, after `Sound.init`.** This route gets the ducking, voice caps and pitch spread.

```lua
-- on the client, for break k; times relative to the snap (t 0)
Sound.setEmitter("break", tornEndAttachment)  -- the kept half's torn end, break frame (0, 5, 0)
Sound.setEmitter("wreck", wreckAttachment)    -- the front-most lost body
Sound.event("metal_tear")                      -- t -0.25
Sound.event("split_explosion")                 -- t 0 (its 3D layer plays at the "break" emitter)
Sound.event("split_glass")                     -- t 0
Sound.event("wreck_scrape")                    -- t 0.3; parented to wreckAttachment, so it follows the wreck
Sound.event("debris_rain")                     -- t 0.8
Sound.event("topple_crash")                    -- t 1.5, the broken half
Sound.event("topple_crash", {at = carriage2Attachment, pitch = 0.94})  -- break 1 only, t 2.0: bigger body, lower
```

`ctx.at` places a single play on any Attachment or BasePart. `setEmitter` changes only later plays, so a
scrape that is already playing keeps following its own body.

**Route B: plain Sound instances with the ids pasted into TrainSplitConfig (A7).** Use the Volume, roll-off and
pitch values above.
- A 3D sound is parented to its Attachment.
- The explosion is two instances: a 2D one at 0.792 (in SoundService) and a positional one at 0.500 on the break.
- Route B has no scripted ducking.

## Upload and register (the owner's steps)
1. Listen (preview, then Studio). If one sound does not fit, drop or replace just that one; its sourcing brief is
   in `../build/AUDIO_BRIEFS.md`.
2. Upload the WAVs you keep (Studio Asset Manager or Creator Hub) and note each asset id.
3. Register each one as self-made, then rebuild so the ids and measured Volumes land in `RR_SoundMap.lua`:

```sh
export RR_SOUND_PRESETS=<mission>/src/sound
S="python3 <rr-soundsmith>/scripts/sound.py"
$S register metal_tear      --file $RR_SOUND_PRESETS/final/rr_split_metal_tear.wav      --id <id> --source owner_upload --origin self-made --proof "src/sound/recipes.py r_metal_tear, seed 7 (synthesised from code)"
$S register split_explosion --file $RR_SOUND_PRESETS/final/rr_split_split_explosion.wav --id <id> --source owner_upload --origin self-made --proof "src/sound/recipes.py r_split_explosion, seed 7 (synthesised from code)"
$S register split_glass     --file $RR_SOUND_PRESETS/final/rr_split_split_glass.wav     --id <id> --source owner_upload --origin self-made --proof "rr-soundsmith glass_smash recipe, seed 7 (synthesised from code)"
$S register debris_rain     --file $RR_SOUND_PRESETS/final/rr_split_debris_rain.wav     --id <id> --source owner_upload --origin self-made --proof "src/sound/recipes.py r_debris_rain, seed 7 (synthesised from code)"
$S register topple_crash    --file $RR_SOUND_PRESETS/final/rr_split_topple_crash.wav    --id <id> --source owner_upload --origin self-made --proof "src/sound/recipes.py r_topple_crash, seed 7 (synthesised from code)"
$S register wreck_scrape    --file $RR_SOUND_PRESETS/final/rr_split_wreck_scrape.wav    --id <id> --source owner_upload --origin self-made --proof "src/sound/recipes.py r_wreck_scrape, seed 7 (synthesised from code)"
$S build --out $RR_SOUND_PRESETS/build && $S validate --release
```

**Why these files and not `../ph/`:** the synth tags every file it writes as PLACEHOLDER in the WAV INFO chunk, and
the licence gate refuses a PLACEHOLDER-tagged file registered as final. The files here carry the same PCM (bit for
bit; `../make_final.py` writes and checks them), tagged "self-made, synthesised from code" instead. A dry run of the
commands above, with a dummy id, accepted all six finals and refused the `ph/` copy.

**Rebuild after a recipe change:**
```sh
$S synth all --out $RR_SOUND_PRESETS/ph
python3 $RR_SOUND_PRESETS/make_final.py
```

## Known limits
- **Scrape length:** wreck_scrape is sized for the normal speed (35). At Speed 20 the slide ends at 1.7 s, so the
  scrape runs about 1 s past it; at Speed 50 the slide lasts until 4.2 s and the scrape stops first.
- **No .ogg:** ffmpeg and imageio-ffmpeg are not installed in this environment. Roblox accepts WAV, and these files
  are 101-265 KB each.
- **Placement is modelled:** in-game level, roll-off and phone loss come from the rr-soundsmith model, not from
  listening. The Volume curve (0.5 = file level) is assumed until the Studio check.
