---
name: rr-soundsmith
description: "Risky Rails (Roblox) audio: the event to sound map (lever clunk, whistle, crisis alarms, fare bank, crate land, wheels and ambient loops), a SoundService/SoundGroup mix with a loudness ladder by tier, voice caps, priority stealing and ducking, generated as Luau (map, client runtime, Studio setup), measurement of audio files the owner drops in (BS.1770 loudness, true peak, silence, clipping, loop seams, phone-speaker loss, Roblox import limits) with fixed copies, clearly marked PLACEHOLDER sound effects for prototyping, sourcing briefs, and a licence gate that admits only owner-uploaded or Roblox-licensed audio. Use whenever Risky Rails work mentions sound, audio, SFX, music, alarms, whistle, horn, ambience, loops, volume, mix, loudness, LUFS, ducking, SoundGroup, SoundService, placeholders, audio licensing or Creator Store audio; when the owner drops .wav, .ogg or .mp3 files; or for sound deliverables in rr-mission-control missions. Not for haptics or shake (rr-game-feel) or particles (rr-vfx-lighting)."
---

# RR Soundsmith

Audio for Risky Rails as data: one soundmap drives the checks, the Luau runtime, the briefs and the critic images;
files are measured by script; quality of the plan is judged by an independent critic, the sound itself by the owner's
ears. Precise, proactive, no fluff.

Paths (find by glob, never hard-code): `<snd>` = this folder;
`<bible>` = `dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path '*rr-bible/SKILL.md' 2>/dev/null | head -1)"`;
`<critic>` = the same with `*multiuse-critic/SKILL.md`. The scripts find rr-bible, rr-game-feel and multiuse-critic
themselves (overrides `RR_BIBLE_SKILL`, `RR_FEEL_PRESETS`, `RR_CRITIC_SKILL`; presets `RR_SOUND_PRESETS`).
`sound` below = `python3 <snd>/scripts/sound.py`. Dependencies: numpy (synth, sheet, fast analysis; analysis also runs
without it), Pillow (sheet), ffmpeg optional for .ogg/.mp3/.flac (`pip install --target ~/.cache/rr-tools/py imageio-ffmpeg`).

## Canon first
Read the slice you need through rr-bible, never from memory: `bible.py get av.audio --values` (priorities, licence
rule, file standard, placeholders), `get tech.audio` (Roblox import limits, Volume ranges, positional rules,
ducking API), `get gameplay.alerts`, `get gameplay.speed`, `get identity.tone`, `get questions`. The soundmap cites
canon keys and `{"v": n, "canon": key}` numbers; `sound validate` proves they agree. Missing canon: `bible.py
add-question` with options and a default, cite the OQ in the sound, label the work "assumed (OQ-nnn default)".
The owner's new words beat canon: do the work, then record it (`add-fact ... --src "owner DATE"` or `decide`).

## Workflow
1. **Edit the design** in `<snd>/presets/soundmap.json` (read `references/schema.md` first): sounds with tier,
   group, class, space, voices, cooldown, pitch spread and a brief; events (`via feel` = played by rr-game-feel's cue,
   `via direct` = `Sound.event`); ladder; ducking; speed link. `sound list`, `sound show ID|EVENT`.
2. **Gate:** `sound validate --strict` must PASS: schema, canon agreement, rr-game-feel cue parity both ways, tiers
   vs feel priorities, ladder hierarchy with trims, ducking sanity (no self-ducking), Roblox ranges, licences. Notes
   are advice (e.g. a feel event that could carry a cue).
3. **Placeholders:** `sound synth all --out DIR` writes `PLACEHOLDER_<id>.wav` (48 kHz mono, INFO tag, levelled to
   the class standard) and `PLACEHOLDERS.md`. For prototyping timing and mix only; say "placeholder" every time.
4. **Owner's files:** `sound analyze FILES|DIR [--as ID]` (names like `lever_clunk_v2.wav` map by prefix):
   loudness, true peak, silence, clipping, seams, phone loss, import limits; FAIL means re-export, WARN means fix or
   accept (the mix compensates level). `--fix-out DIR [--mono]` writes `*_std.wav` copies; never touches the source.
   Standards and methods: `references/standards.md`.
5. **Register** after the owner uploads: `sound register ID --file F --id N --source owner_upload --origin
   self-made|commissioned|cc0|purchased|cc-by --proof P [--credit C]`, or `--source roblox_licensed --creator Roblox
   --proof URL`, or `--source placeholder`. The licence gate refuses NC/ND/SA, rips, unknown terms, community uploads
   and PLACEHOLDER-tagged files posing as final (`references/licensing.md`). The measured level sets Volume.
6. **Briefs:** `sound brief all --out AUDIO_BRIEFS.md` for sourcing or commissioning (`references/brief-format.md`).
7. **Judge the plan (never self-score):** `sound sheet --from DIR --out SHEET` (tiles, ladder with phone dots,
   timeline against feel channels, contact.png + closeups.png, facts.md; look at contact.png once), then
   `sound crit CRIT --pass N --from SHEET` and the printed `critic_kit.py build ... --profile S`. Continue with
   `<critic>/SKILL.md` steps 4-9 (fresh critic, delta passes, bar 8 unless the owner said otherwise). No Agent tool:
   follow rr-mission-control's critic route (remote session, handoff to the caller, or a labelled UNCERTIFIED
   self-review capped at bar-1). The critic cannot hear: it scores hierarchy, timing, phone survival, safety, style of
   the briefs and coverage.
8. **Export:** `sound build --out DIR` writes `RR_SoundMap.lua` (generated), `RR_Sound.lua`,
   `RR_SoundDemo.client.lua`, `studio_sound_setup.lua`, `SOUND_SPEC.md`, `AUDIO_BRIEFS.md`, `LICENCES.md`, README,
   then runs luaparse (else a balance check, named) and `bible check` per file. Build PASS before handover; handover
   says "Studio listening test pending (owner)" (`references/fidelity.md` has the 15-minute test).
9. **Release gate:** `sound validate --release` fails while any alpha sound is placeholder or unassigned.
10. **Record** owner decisions (`bible.py decide OQ-nnn X --by owner`, then edit the soundmap). Presets never become
    canon by themselves.

## Runtime (what the owner wires in Studio)
- One LocalScript: `Sound.init(require(RS.RR_SoundMap), {feel = Feel})`; client only (canon: never clone Sounds on
  the server). Reuses `SoundService.RR_Mix` from `studio_sound_setup.lua`.
- `Sound.setEmitter("lever", attachment)` per role (missing role: plays 2D, warned once); `Sound.setSpeed(speed)` on
  every throttle change; `Sound.event("trip_start")`, `Sound.event("ui_button_press")` for `via direct` events.
- `via feel` events play when `Feel.play` fires their cue; `Sound.event` on them is ignored while Feel is connected,
  so nothing plays twice. `Sound.setSetting("sfx", 0.5)`, `Sound.duck("fail", 2)`, `Sound.stats()`.

## Inside a mission (rr-mission-control)
Sound is a deliverable of kind `mixed`: copy `presets/` to `<M>/src/sound/` and `export RR_SOUND_PRESETS=<M>/src/sound`;
placeholders in `<M>/src/sound/ph/`, sheets in `<M>/src/sound/sheet/`, critic in `<M>/critique-sound`, export in
`<M>/export/sound/`. The maker's order points at steps 1-8; pre-flight = step 2 plus `sound build --no-check`.

## Design rules (why the map looks like this)
- **Alarms first** (av.audio.priority): tiers fail > crisis > commit > reward > UI > loops, as rr-game-feel ranks
  events; crisis alarms are 2D train-wide plus a quieter positional layer at the source (OQ-035 default) and each
  has its own rhythm and band so the other carriage can name it.
- **Files to one standard, the mix in data:** rebalancing is a rebuild, never a re-upload (import quota, moderation).
- **Slapstick lands through sound** (av.audio.slapstick): droopy, clunky, cartoon; never horror or war (identity.tone).
- **Phones first:** energy in 0.5-4 kHz for anything that must be heard; phone loss is checked per class.
- **Speed is heard:** the wheel loop's rate and level follow Speed and fall silent at a stop (av.audio.speed_link).
- **Scripted ducking** (dB ramps per group, no self-ducking) over engine sidechain: deterministic and tested.

## Open decisions (defaults in use; the owner decides)
OQ-021 audio identity (A: diegetic only, no music bed in runs; the cab radio is a siding), OQ-035 alarm placement
(A: 2D plus positional layer), OQ-036 community Creator Store audio (A: refused). `bible.py get OQ-035`.

## Honest limits
- Cloud: no speakers, no Studio, no Studio MCP. File numbers are measured; in-game level, roll-off and phone loss
  are modelled (Volume curve assumed linear with 0.5 = file level). Placeholders are synthesised from code only.
- Uploading audio, buying packs, accepting audio terms and publishing are the owner's gate; prepare, dry-run, hand over.
- Never message players or change the owner's Claude config.

## Maintain
`python3 <snd>/scripts/selftest.py` exercises every command on temp copies (must print all passed; the Lua runtime
tests need lupa: `pip install --target ~/.cache/rr-tools/py lupa`, else skipped and said so).
`python3 <snd>/scripts/luatest.py -v` runs the Lua tests alone. Remove `__pycache__` after running scripts.
