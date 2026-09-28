# rr-soundsmith · design notes (2026-09-28)

## Job
Audio for Risky Rails as data: an event -> sound map, a SoundService/SoundGroup mix with priority, voice and ducking
rules, a Luau runtime generated from it, measurement of any file the owner drops in (loudness, true peak, length,
silence, clipping, loop seams, phone band), clearly marked placeholder SFX for prototyping, sourcing briefs, and a
licence register that refuses anything not owner-uploaded or Roblox-licensed.

## Pipeline
```
bible get (canon slice) -> presets/soundmap.json   design, hand-edited: standards, ladder, groups, voices, ducking,
                                                    speed link, emitters, 25 sounds, 26 events (event -> actions)
                           presets/assets.json      register, script-written: asset ids, licence, measured levels
  -> sound.py validate   schema, canon agreement, rr-game-feel cue parity (both ways), tiers, ladder hierarchy,
                         ducking sanity, Roblox ranges, licence rules (--release: no placeholder or unlicensed audio)
  -> sound.py synth      PLACEHOLDER_<id>.wav (numpy, seeded, 48 kHz mono, INFO chunk says placeholder),
                         normalised to the file standard by the analyser, PLACEHOLDERS.md
  -> sound.py analyze    any .wav natively; .ogg/.mp3/.flac through ffmpeg if present (else header-only length)
                         BS.1770-4 loudness (momentary max, short-term max, integrated, LRA), true peak (4x),
                         clipping, DC, lead/tail silence, loop seam, phone-band share, platform limits; --fix-out
                         writes gain-normalised copies (never touches the owner's file)
  -> sound.py register   file + asset id + licence proof -> assets.json (measured level feeds the mix)
  -> sound.py brief      AUDIO_BRIEFS.md: one sourcing brief per sound (format in references/brief-format.md)
  -> sound.py sheet      waveform+spectrogram tiles, mix ladder, event timelines vs rr-game-feel channels,
                         contact.png + closeups.png + facts.md (multiuse-critic layout)
  -> sound.py crit       CRIT/rubric.md = critic rubric + Profile S (sound plan), pass files, brief from canon
  -> sound.py build      RR_SoundMap.lua (generated) + RR_Sound.lua + RR_SoundDemo.client.lua +
                         studio_sound_setup.lua + SOUND_SPEC.md + AUDIO_BRIEFS.md + LICENCES.md + README;
                         luaparse and bible check gates
```

## Decisions (with why)
1. **Files to one standard, mix in data.** Every file is normalised to its class standard (one-shots by momentary
   max, loops and music by integrated loudness, all <= -1 dBTP). The hierarchy lives in the ladder (loudness per
   tier) and each sound's Volume is computed from the file's measured level. Re-balancing never needs a re-upload
   (Roblox import quota and moderation delay).
2. **Hierarchy is checked, not hoped for.** Tiers match rr-game-feel priorities (1 fail ... 5 UI, loops below);
   validate fails a sound louder than a more important tier by over 1 LU, and ducking that does not clear room.
3. **One trigger route.** Sound ids equal rr-game-feel cue names. Events with a feel preset play through
   `Feel.Cue` (`via: feel`); validate proves both files agree. Other events (UI clicks, trip loops, cab buttons)
   are `via: direct` (`Sound.event(name)`); validate suggests the cue channel rr-game-feel could add.
4. **Scripted ducking, not engine sidechain.** Group volumes move in dB with attack/hold/release per rule on one
   Heartbeat step: deterministic, testable in a Lua VM, no self-ducking. CompressorSoundEffect.SideChain stays
   documented as the alternative (Studio-test only).
5. **Client pool** (canon av.audio.client_pool): Sound instances pre-made on the client per sound (its voice
   count), global and per-group voice caps, steal by tier then age, crisis tiers never dropped, cooldowns,
   pitch spread and no-repeat variations. 3D sounds use emitter roles set at run time; missing role = 2D + warn.
6. **Crisis alarms reach the other carriage** (av.audio.priority): 2D train-wide plus a quieter positional layer
   at the source, the default of a new open question (placement). Wheel sound follows Speed (av.audio.speed_link).
7. **Placeholders are honest.** Synthesised from code only (no samples, so no third-party rights), prefixed
   PLACEHOLDER_, INFO chunk says so, registered as source `placeholder`; `validate --release` fails while any
   alpha sound still uses one. Loudness is measured by our own BS.1770 implementation, tested on EBU 3341 cases.
8. **Licensing is a gate, not advice.** Only `owner_upload` (self-made, commissioned, CC0, or bought with a game
   licence, proof recorded) or `roblox_licensed` (Creator Store audio by Roblox or its partners). Community uploads,
   NC/ND/SA, rips and unknown terms are refused (open question records the community-upload default).
9. **Critic judges the plan, the owner's ears judge the sound.** Profile S scores what images and measurements can
   show (hierarchy, timing against the feel beat, phone band, repetition, coverage); nobody in the cloud listens.

## Plugs
- rr-bible: canon read at run time (av.audio.*, gameplay.speed.*, gameplay.alerts.*, tech.units.*, identity.*);
  new platform facts (tech.audio.*), proposed rules (av.audio.licence, av.audio.file_standard), open questions for
  alarm placement and community audio; `bible check` on every export.
- rr-game-feel: cue names and event priorities read from its feel.json (found by glob); parity checked.
- rr-mission-control: sound is a deliverable of kind `mixed` (presets in `<M>/src/sound/`, RR_SOUND_PRESETS).
- multiuse-critic: contact_sheet.py and critic_kit.py by glob; Profile S merged into CRIT/rubric.md.

## Limits
No Studio and no speakers in the cloud: Roblox's Volume-to-gain curve, rolloff feel, phone speakers and the
real mix need the owner's listening test (references/fidelity.md). Uploading, publishing and spending are the
owner's gate. Placeholders are for prototyping only.
