# rr-soundsmith · design notes (2026-09-28)

## Job
Audio for Risky Rails as data: an event -> sound map, a SoundService/SoundGroup mix with priority, voice and ducking
rules, a Luau runtime generated from it, measurement of any file the owner drops in (loudness, true peak, length,
silence, clipping, loop seams, phone band), clearly marked placeholder SFX for prototyping, sourcing briefs, and a
licence register that refuses anything not owner-uploaded or Roblox-licensed.

## Pipeline
```
bible get (canon slice) -> presets/soundmap.json   design, hand-edited: standards, ladder, groups, voices, ducking,
                                                    speed link, emitters, 29 sounds, 32 events (event -> actions, phase)
                           presets/assets.json      register, script-written: asset ids, licence, measured levels
  -> sound.py validate   schema, canon agreement, rr-game-feel cue parity (both ways), tiers, ladder hierarchy,
                         ducking sanity, Roblox ranges, licence rules (--release: no placeholder or unlicensed audio)
  -> sound.py synth      PLACEHOLDER_<id>.wav (numpy, seeded, 48 kHz mono, INFO chunk says placeholder),
                         normalised to the file standard by the analyser, PLACEHOLDERS.md
  -> sound.py analyze    any .wav natively; .ogg/.mp3/.flac through ffmpeg if present (else header-only length)
                         BS.1770-4 loudness (momentary max, short-term max, integrated, LRA), true peak (8x),
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
   count), global and per-group voice caps, steal by tier then age (new fail and crisis sounds always get a voice; playing alarms yield only to the fail or another alarm), cooldowns,
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

## Fix round (2026-09-28, after the trial and two reviews)
- Placeholders from data: a sound's `synth` names a recipe or holds a layer spec, and `<presets>/recipes.py` adds
  recipes, so a mission adds sounds without editing skill code; "no recipe" is a note. Lobby sounds ship built in.
- Events carry a `phase`; list, briefs, SOUND_SPEC and the critic facts are phase-ordered. Facts carry the event and
  brief table and a coverage line that separates "mapped and briefed" from "files in this pass".
- Open questions come from data: cited OQs are read through rr-bible (title, default) and checked for relevance;
  unrecorded ones live in `meta.pending_oq` as `pending:<key>` with a printed add-question command, so a sandbox never
  invents a number that a sibling can take.
- Runtime: a playing alarm-class voice yields only to a more important tier or another alarm (Alarms cap 6); each
  voice owns its positional layer (same take, stops with it); Studio group volumes are the base.
- Register home: the skill folder is read-only; `promote` moves a mission's soundmap and register to the project home
  that later runs and rr-release-train read. Release gate: silent builds pass (sound is a COULD), placeholders never.
- Licence gate follows canon exactly (no CC-BY), needs asset ids, anchors the rip pattern; the analyzer fails empty,
  silent, truncated and .opus files; true peak is 8x.
