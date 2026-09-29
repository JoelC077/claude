# Carriage-split sounds: upload files

Six files for a carriage tearing in half (mission 260929-train-splits, R13: "Sounds: yes. Make some if you can
and include them if they fit"). They are made from code only: `src/sound/recipes.py`, plus split_glass reshaping
rr-soundsmith's synthesised glass_smash. There are no samples and no third-party material, so they are self-made
and licence-clean.

Format: 48 kHz, 16-bit mono WAV, levelled to the rr-soundsmith impact standard (momentary max -14 LUFS, true peak
-1 dBTP or lower). Every file fades to true silence 20 ms before its end. The mix lives in data (`soundmap.json`),
so a level change is a rebuild, never a re-upload.

Status after critic pass 1 fixes: validate --strict PASS, analyze 7/7 PASS, build PASS. Nobody has heard them yet,
so the Studio listening test is pending (owner). For a first listen, `../preview/split_sequence_at_break.wav` plays
break 1 as heard at the break. It is a listening aid only: do not upload it.

## Files
Times are from `src/kit/break_spec.json` (t 0 = the snap).
- **Volume:** the Roblox `Sound.Volume` that puts the file at its in-game level (0.5 = file level, assumed until the
  Studio check).
- **Roll-off:** InverseTapered for every 3D sound.
- **Groups:** the boom is in Alarms. Every other layer is in Split, a SoundGroup of its own with a voice cap of 4.
  Split is never ducked by the boom and is ducked by the fail like Actions.

| id | file | length | LUFS M max (integrated) | true peak | in game (phone) | Volume | group | 2D/3D | RollOffMin / Max | event (t) |
|---|---|---|---|---|---|---|---|---|---|---|
| metal_tear | metal_tear.wav | 1.05 s | -14.0 (-16.0) | -2.9 dBTP | -12.5 (-13.0) | 0.594 | Split t3 | 3D at `break` | 16 / 240 | `metal_tear`, t -0.25: its snap peaks 0.25 s into the file (+0.3 ms), on the boom |
| split_explosion | split_explosion.wav | 2.20 s | -14.0 (-20.9) | -2.9 dBTP | -10 (-11.2) | 0.796 (2D) + 0.502 (3D layer) | Alarms t2 | 2D train-wide + 3D layer at `break` | 3D layer 16 / 240 | `split_explosion`, t 0: peaks at +6.5 ms |
| split_glass | split_glass.wav | 0.90 s | -14.0 (-16.8) | -4.6 dBTP | -13 (-13.4) | 0.561 | Split t3 | 3D at `break` | 16 / 240 | `split_glass`, t 0: once, or once per side about 0.1 s apart |
| debris_rain | debris_rain.wav | 1.80 s | -14.0 (-19.3) | -3.7 dBTP | -16 (-17.1) | 0.397 | Split t4 | 3D at `break` | 10 / 140 | `debris_rain`, t 0.8 |
| topple_crash | topple_crash.wav | 1.45 s | -14.0 (-19.1) | -2.3 dBTP | -13 (-13.5) | 0.561 | Split t3 | 3D at `wreck` | 16 / 240 | `topple_crash`, t 1.5 (the broken half); its bounce clunk is 0.35 s in |
| topple_crash_2 | topple_crash.wav (same file, no upload) | 1.73 s at 0.84 | as topple_crash | -2.3 dBTP | -16 (-16.5) | 0.397, PlaybackSpeed 0.806-0.874 | Split t4 | 3D at `wreck` | 16 / 240 | `topple_crash_2`, t 2.0 on break 1 (carriage 2) |
| wreck_scrape | wreck_scrape.wav | 2.70 s | -14.0 (-17.2) | -2.9 dBTP | -16 (-17.1) | 0.397 | Split t4 | 3D at `wreck`, follows it | 10 / 140 | `wreck_scrape`, t 0.3 until V/brake (2.9 s at Speed 35) |

The order holds on full-range speakers (-10 > -12.5 > -13 > -16 LUFS) and on a phone speaker (-11.2 boom > -13.0 tear >
-13.5 crash > -16.5 to -17.1 for debris, scrape and the second topple). On a phone, split_explosion sits just under the
boiler fail (-10.7) and above every other crisis sound.

- **Pitch spread per play:** tear 0.97-1.03, explosion 0.96-1.04, glass 0.93-1.07, debris 0.90-1.10,
  topple_crash 0.96-1.04, topple_crash_2 0.806-0.874, scrape 0.95-1.05.
- **Ducking (RR_Sound):** the `split` rule ducks Ambient -12, Music -14, UI -8 and Actions -4 dB. It stays on while
  the boom plays (2.2 s) plus 0.3 s, then releases over 0.9 s. Concurrent rules do not add: per group the deepest
  active duck wins, so Ambient dips 12 dB in a split, not 12 + 8.

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
Sound.event("topple_crash_2", {at = carriage2Attachment})  -- break 1 only, t 2.0: carriage 2
```

`ctx.at` places a single play on any Attachment or BasePart. `setEmitter` changes only later plays, so a
scrape that is already playing keeps following its own body.

**Route B: plain Sound instances with the ids pasted into TrainSplitConfig (A7).** Use the Volume, roll-off, pitch
and group values above.
- A 3D sound is parented to its Attachment.
- The explosion is two instances: a 2D one at 0.796 and a positional one at 0.502 on the break.
- topple_crash_2 is the topple_crash asset at PlaybackSpeed 0.84 (+-4%) and Volume 0.397.
- Route B has no scripted ducking.

## Upload and register (the owner's steps)
Everything short of an asset id is already checked. A dry run of each command below, with a dummy id, passed the
licence gate for all seven sound ids. The PLACEHOLDER-tagged `../ph/` copies are refused, and `register` without
`--id` stops with "needs --id N: the Roblox asset id of the uploaded audio". What stays for the owner:

1. Listen (the preview, then Studio). If one sound does not fit, drop or replace just that one; its brief is in
   `../build/AUDIO_BRIEFS.md`.
2. Upload the six WAVs in this folder (Studio Asset Manager or Creator Hub) and note each asset id.
   topple_crash_2 has no file of its own.
3. Register the seven sound ids (topple_crash_2 takes topple_crash's file and id), then rebuild and run the ship gate:

```sh
export RR_SOUND_PRESETS=<mission>/src/sound
S="python3 <rr-soundsmith>/scripts/sound.py"; F=$RR_SOUND_PRESETS/final
P="--source owner_upload --origin self-made --proof src/sound/recipes.py(synthesised-from-code)"
$S register metal_tear      --file $F/metal_tear.wav      --id <id> $P
$S register split_explosion --file $F/split_explosion.wav --id <id> $P
$S register split_glass     --file $F/split_glass.wav     --id <id> $P
$S register debris_rain     --file $F/debris_rain.wav     --id <id> $P
$S register topple_crash    --file $F/topple_crash.wav    --id <id> $P
$S register topple_crash_2  --file $F/topple_crash.wav    --id <topple_crash id> $P
$S register wreck_scrape    --file $F/wreck_scrape.wav    --id <id> $P
$S build --out $RR_SOUND_PRESETS/build && $S validate --release
```

4. For route B, paste the ids into TrainSplitConfig.

**Why these files and not `../ph/`:** the synth tags every file it writes as PLACEHOLDER in the WAV INFO chunk, and
the licence gate refuses such a file registered as final. The files here carry the same PCM (bit for bit;
`../make_final.py` writes and checks them), named after the sound and tagged "self-made, synthesised from code".

**Rebuild after a recipe change:**
```sh
$S synth all --out $RR_SOUND_PRESETS/ph
python3 $RR_SOUND_PRESETS/make_final.py    # rewrites these files and the preview
```

## Known limits
- **Scrape length:** wreck_scrape is sized for the normal speed (35). At Speed 20 it runs about 1 s past the slide;
  at Speed 50 it stops 1.3 s early.
- **No .ogg:** ffmpeg and imageio-ffmpeg are not installed here. Roblox accepts WAV, and these files are 87-259 KB.
- **Placement is modelled:** in-game level, roll-off and phone loss come from the rr-soundsmith model, not from
  listening. The Volume curve (0.5 = file level) is assumed until the Studio check.
