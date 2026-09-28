---
name: rr-soundsmith
description: "Risky Rails audio kit: event-to-sound map, SoundGroup mix and loudness ladder as Luau, measurement and fixing of dropped .wav/.ogg/.mp3 files (LUFS, peak, loops, phone loss), PLACEHOLDER sounds, sourcing briefs and a licence gate. Not for haptics, shake or particles. Sub-skill of rr-mission-control (JARVIS): any Risky Rails request, even a short one squarely in this area, goes to rr-mission-control first, which routes here; fire directly only when this skill is named or another rr-* skill invokes it."
---

# RR Soundsmith

Audio for Risky Rails as data: one soundmap drives the checks, the Luau runtime, the briefs and the critic images;
files are measured by script; quality of the plan is judged by an independent critic, the sound itself by the owner's
ears. Precise, proactive, no fluff.

Paths (find by glob, never hard-code): `<snd>` = this folder;
`<bible>` = `dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path '*rr-bible/SKILL.md' 2>/dev/null | head -1)"`.
The scripts find rr-bible, rr-game-feel and multiuse-critic themselves (overrides `RR_BIBLE_SKILL`, `RR_FEEL_PRESETS`,
`RR_CRITIC_SKILL`); for the critic use the path `sound crit` prints, not your own glob.
`sound` below = `python3 <snd>/scripts/sound.py`. Dependencies: numpy (synth, sheet, fast analysis; analysis also runs
without it), Pillow (sheet), optional ffmpeg (.ogg/.mp3/.flac) and lupa (Lua tests); the scripts also look in
`~/.cache/rr-tools/py` (`pip install --target ~/.cache/rr-tools/py numpy Pillow lupa imageio-ffmpeg`).

## Where the data lives
`sound where` says which soundmap and register are in use: `$RR_SOUND_PRESETS` (a mission copy), else the project
home (`$RR_SOUND_HOME`, else `~/.rr-sound`) once it exists, else `<snd>/presets` (read-only defaults; `register`
refuses to write there because a re-sync overwrites it). After the owner approves a mission's sound work,
`sound promote --from <M>/src/sound` copies soundmap.json, assets.json (merged) and recipes.py to the home, so the
next mission and rr-release-train's G9 read the same register.

## Canon first
Read the slice you need through rr-bible, never from memory: `bible.py get av.audio --values` (priorities, licence
rule, file standard, placeholders), `get tech.audio` (import limits, Volume ranges, positional rules, API status),
`get gameplay.alerts`, `get gameplay.speed`, `get gameplay.run` (queue, depart ramp, arrival braking),
`get identity.tone`. `sound oq` lists every cited open question with its default (cheaper than `get questions`).
The soundmap cites canon keys and `{"v": n, "canon": key}` numbers; `sound validate` proves they agree and warns when
a cited OQ never mentions audio, the sound or its canon keys (a sibling may have taken the number).
Missing canon: add it to `meta.pending_oq` (title, options, default, context, affects, blocks) and cite
`pending:<key>`; `sound oq` prints the exact `bible.py add-question` command. Run it when you may write the bible
(owner present or mission-control allows it), then cite the number it prints and re-run `sound oq`. In a trial,
sandbox or owner-absent run never cite a sandbox number: keep `pending:` and hand the command over.
Label work on a default "assumed (OQ-nnn default)". The owner's new words beat canon: do the work, then record it.

## Workflow
1. **Edit the design** in the soundmap (read `references/schema.md` first): sounds with tier, group, class, space,
   voices, cooldown, pitch spread and a brief; events with a `phase` (lobby, depart, run, fork, crisis, arrive,
   results, any) and `via feel` (played by rr-game-feel's cue) or `via direct` (`Sound.event`); ladder; ducking;
   speed link. `sound list` (by phase), `sound show ID|EVENT`.
2. **Gate:** `sound validate --strict` must PASS: schema, canon agreement, cited OQs, rr-game-feel cue parity both
   ways, tiers vs feel priorities, ladder hierarchy with trims, ducking sanity, voice caps, Roblox ranges, licences.
   Notes are advice (a feel event that could carry a cue, a pending OQ, a sound with no placeholder recipe).
3. **Placeholders:** `sound synth all --out DIR` writes `PLACEHOLDER_<id>.wav` (48 kHz mono, INFO tag, levelled to
   the class standard) and `PLACEHOLDERS.md`. A new sound gets a recipe without touching skill code: `"synth":
   "<recipe>"` (reuse one, `synth.py --list`), `"synth": {len, layers}` (a layer spec, schema.md), or
   `r_<id>(rng)` in `<presets>/recipes.py`. For timing and mix only; say "placeholder" every time. Analysing synth
   output is a smoke test (synth levels with the same meter); the analyzer is proven on owner files.
4. **Owner's files:** `sound analyze FILES|DIR [--as ID]` (names like `lever_clunk_v2.wav` map by prefix):
   loudness, true peak, silence, clipping, seams, phone loss, import limits; FAIL (empty, silent, truncated, late
   start, clipping, .opus, over limits) means re-export, WARN means fix or accept (the mix compensates level).
   `--fix-out DIR [--mono]` writes `*_std.wav` copies; never touches the source. Methods: `references/standards.md`.
5. **Register** after the owner uploads: `sound register ID --file F --id N --source owner_upload --origin
   self-made|commissioned|cc0|purchased --proof P [--credit C]`, or `--source roblox_licensed --creator Roblox
   --id N --proof URL`, or `--source placeholder`. The licence gate refuses NC/ND/SA, CC-BY (not in
   av.audio.licence), rips, unknown terms, community uploads, a missing asset id and PLACEHOLDER-tagged files posing
   as final (`references/licensing.md`). The measured level sets Volume. `--dry-run` first when unsure.
6. **Briefs:** `build` writes AUDIO_BRIEFS.md (licence, tone, meter note once; a phase summary table with takes,
   length and sourcing route; then one brief per sound). `sound brief ID... --out F` only for an ad-hoc subset.
7. **Judge the plan (never self-score):** `sound sheet --from DIR --out SHEET` (tiles, ladder with phone dots,
   timeline against feel channels, contact.png + closeups.png, facts.md with the event and brief table; look at
   contact.png once), then `sound crit CRIT --pass N --from SHEET [--owner-away]` and the printed
   `critic_kit.py build ... --profile S`. Continue with the critic skill's steps 4-9 (fresh critic, delta passes,
   bar 8 unless the owner said otherwise). Critic route per rr-mission-control (agent, remote, handoff, self); a
   remote session cannot read local pass folders, so a workflow subagent without an Agent tool uses handoff (build
   as pre-flight, return the pass path, rebuild after the fixes). The critic cannot hear: it scores hierarchy,
   timing, phone survival, safety, brief style and coverage.
8. **Export:** `sound build --out DIR` writes `RR_SoundMap.lua` (generated), `RR_Sound.lua`,
   `RR_SoundDemo.client.lua`, `studio_sound_setup.lua`, `SOUND_SPEC.md` (phase order, open decisions),
   `AUDIO_BRIEFS.md`, `LICENCES.md`, README, then runs luaparse (else a balance check, named) and `bible check` per
   file; `python3 <snd>/scripts/luatest.py --map DIR/RR_SoundMap.lua` runs the runtime suite on it. Build PASS before
   handover; handover says "Studio listening test pending (owner)" (`references/fidelity.md`).
9. **Release gate:** `sound validate --release` fails on any placeholder or licence problem, and on unassigned
   alpha sounds once any alpha sound has audio (av.audio.placeholder); a build with no audio at all passes with a
   note (av.audio.priority_in_plan: sound is a COULD for the alpha). Deferring a sound = stage `siding`.
10. **Record** owner decisions (`bible.py decide OQ-nnn X --by owner`, then edit the soundmap). Presets never become
    canon by themselves.

## Runtime (what the owner wires in Studio)
- One LocalScript: `Sound.init(require(RS.RR_SoundMap), {feel = Feel})`; client only (canon: never clone Sounds on
  the server). Reuses `SoundService.RR_Mix` from `studio_sound_setup.lua`; a group Volume set there is the base,
  settings and ducking multiply on top.
- `Sound.setEmitter("lever", attachment)` per role (missing role: plays 2D, warned once).
- `Sound.setSpeed(speed)` whenever Speed changes (each Heartbeat or the replicated Speed value's Changed), including
  the ~5 s departure ramp and arrival braking; notch-only calls make the wheels jump and never fade at the stop.
- `Sound.event("trip_start")`, `Sound.event("lobby_enter")`, `Sound.event("ui_button_press")` for `via direct`
  events; `via feel` events play when `Feel.play` fires their cue (`Sound.event` on them is ignored while Feel is
  connected). `Sound.setSetting("sfx", 0.5)`, `Sound.duck("fail", 2)`, `Sound.stats()`.
- Demo keys: 1-0 events, L run/lobby page, T trip, N depart ramp, B brake to a stop, Z/X/C speeds, R radio, P stats.

## Inside a mission (rr-mission-control)
Sound is a deliverable of kind `mixed`: copy the presets in use (`sound where`) to `<M>/src/sound/` and
`export RR_SOUND_PRESETS=<M>/src/sound`; placeholders in `<M>/src/sound/ph/`, sheets in `<M>/src/sound/sheet/`,
critic in `<M>/critique-sound`, export in `<M>/export/sound/`. The maker's order points at steps 1-8; pre-flight =
step 2 plus `sound build --no-check`. On the owner's go: `sound promote --from <M>/src/sound`.

## Design rules (why the map looks like this)
- **Alarms first** (av.audio.priority): tiers fail > crisis > commit > reward > UI > loops, as rr-game-feel ranks
  events; crisis alarms are 2D train-wide plus a quieter positional layer at the source (OQ-035 default), each with
  its own rhythm and band, and a playing alarm is never cut by a crisis impact (glass, coupling).
- **Files to one standard, the mix in data:** rebalancing is a rebuild, never a re-upload (import quota, moderation).
- **Slapstick lands through sound** (av.audio.slapstick): droopy, clunky, cartoon; never horror or war (identity.tone).
- **Phones first:** energy in 0.5-4 kHz for anything that must be heard; phone loss is checked per class.
- **Speed is heard:** the wheel loop's rate and level follow Speed and fall silent at a stop (av.audio.speed_link).
- **Scripted ducking** (dB ramps per group, no self-ducking) over engine sidechain: deterministic and tested.

## Honest limits
- Cloud: no speakers, no Studio, no Studio MCP. File numbers are measured; in-game level, roll-off and phone loss
  are modelled (Volume curve assumed linear with 0.5 = file level). Placeholders are synthesised from code only.
- Runtime uses legacy Sound + SoundGroup (tech.audio.soundgroup_status: supported, Roblox now recommends the Audio
  API): chosen for group nesting and ducking tested in a Lua VM; an AudioPlayer/AudioEmitter port keeps the map.
- Cowork on the owner's machine: Studio (and a Studio MCP, if connected) can run the listening test directly; still
  never upload, publish or accept terms without the owner.
- Uploading audio, buying packs, accepting audio terms and publishing are the owner's gate; prepare, dry-run, hand
  over. Never message players or change the owner's Claude config.

## Maintain
`python3 <snd>/scripts/selftest.py` exercises every command on temp copies (must print all passed; never reads
`~/.rr-sound`; Lua tests need lupa, else skipped and said so). `python3 <snd>/scripts/luatest.py -v` runs the Lua
tests alone. The scripts write no `__pycache__`.
