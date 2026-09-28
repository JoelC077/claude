# rr-soundsmith fix report (2026-09-28)

**Inputs:** FRICTION.md (F1-F17) and two independent reviews, scored 7 and 6.5.
**Result:** All high and medium findings are applied, and so are the cheap lows. Three are rejected and one optional friction fix is declined (listed below). The skill is re-run, re-trialled, validated and packaged.
**REPORT.md was not written:** this subagent environment blocks writing report files. The text below is that report.

## Changes (skill: /home/user/claude/rr-soundsmith)

### Placeholders (F1, both reviews)
- A mission can add a placeholder sound without editing skill code, in any of three ways:
  - `"synth": "<recipe>"` reuses an existing recipe.
  - `"synth": {len, layers, repeat}` is a layer spec (tone, noise, bell, click, modes). Loops wrap so they are seamless.
  - `r_<id>` can be defined in `<presets>/recipes.py`.
- `validate` checks all three without numpy, so strict results are the same on every machine. "No recipe" is now a note, not a warning.
- The trial's `tools/ph_recipes.py` wrapper is now obsolete.

### Lobby phase (F2)
- Presets now ship `lobby_bed`, `queue_punch`, `queue_bell` and `guard_whistle` with built-in recipes, plus 6 lobby events.
- Events carry a `phase`: lobby, depart, run, fork, crisis, arrive, results or any.
- `list`, the briefs, SOUND_SPEC and the critic facts are all ordered by phase.

### Critic evidence (F9, F10)
- `facts.md` now has an event and brief table in phase order: sound, tier and group, space and emitter, events, must say, sounds like, avoid.
- Coverage is split in two:
  - mapped and briefed: 32/32 events, 29/29 sounds, 8/8 emitters;
  - files in this pass: 5/29, marked "not a coverage gap".
- The critic brief is built from data. Stage comes from file and asset states; open decisions come from rr-bible.
- Step 2 is pre-answered only with `--owner-away`.
- `sound crit` prints the critic path to use (F7).

### Open questions (F4, F5, F11, F12)
- `sound oq` lists every cited OQ with its title, status and default. It replaces `get questions`.
- `validate` warns when a cited OQ never mentions audio, rr-soundsmith, the sound or its canon keys. This catches the collision where OQ-037 became the release-versioning question.
- A question not yet in the bible goes in `meta.pending_oq` and is cited as `pending:<key>`. `sound oq` and SOUND_SPEC print the exact `add-question` command, so a sandbox never invents a number.

### Lua runtime
- A crisis alarm that is playing gives up its voice only to the fail or to another alarm. Glass and coupling impacts are dropped instead. The Alarms cap is now 6.
- Each voice owns its own positional layer. It plays the same take and stops with the voice.
- A SoundGroup volume set in Studio is kept as the base; settings and ducking multiply on top, and `destroy()` restores it.
- The SOUND_SPEC wording now matches this behaviour.
- `validate` warns when one sound can fill more than half its group cap. `ui_click` voices went from 3 to 2.

### Speed wiring
- The README, SKILL.md, SOUND_SPEC and the runtime header now say: call `Sound.setSpeed` whenever Speed changes, including the departure ramp and arrival braking.
- New demo keys: N ramps departure over 5 s, B brakes to a stop over 4 s, L switches to a lobby page with a 5-tick countdown.
- A new Lua test checks the braking fade.

### Register home and release gate
- `sound where` shows which soundmap and register are in use.
- `register` refuses to write into the skill folder.
- `sound promote --from <M>/src/sound` copies the soundmap, the register (merged) and `recipes.py` to the project home (`$RR_SOUND_HOME` or `~/.rr-sound`), keeping backups. Later runs and rr-release-train's G9 then read that home.
- `--release` now behaves like this:
  - Any placeholder or licence problem is an error.
  - A build with no audio at all passes with a note, citing av.audio.priority_in_plan (sound is optional for the alpha).
  - Once any alpha sound has audio, unassigned alpha sounds are errors (av.audio.placeholder). Moving a sound to stage `siding` defers it.

### Analyzer and licence gate
- The analyzer now fails empty, silent (below -70 LUFS), truncated and `.opus` files.
- The gain hint is capped at +30 dB, matching `fix-out`. `--mono` without numpy now says "mono skipped".
- The licence gate now:
  - drops CC-BY, because canon av.audio.licence doesn't list it;
  - refuses origin cc0 when the licence text names attribution;
  - requires `--id` for owner uploads and Roblox-licensed audio;
  - matches rips only as a whole word, so "Ripley Sound" passes.
- `licensing.md` now says to keep purchased assets private and never distribute them on the Creator Store.

### True peak
- True peak now uses 8x oversampling with 64 taps per phase, instead of 4x.
- `lever_clunk` now reads -1.41 dBTP, matching ffmpeg (-1.4) and a 16x reference (-1.39). The old reading was -1.77.
- Selftest adds half-scale inter-sample tones at fs/3, fs/4, fs/6 and fs/8, each within 0.15 dB of -6.02.

### Briefs (F13, F15)
- AUDIO_BRIEFS opens with a header said once: licence, tone, delivery, and a dual-mono meter note.
- Then comes a phase summary table: takes, length, space, state and sourcing route.
- The file is 35.1 KB instead of 42.4 KB; the licence line appears once instead of 29 times.
- 2D sounds now read "2D (global)" instead of assuming the train.
- `build` writes the briefs; the `brief` command is for subsets only.

### Hygiene and docs (F3, F6, F8, F14, F16, F17)
- `luatest --map` now runs the full suite on a built map. If the map lacks the sounds the suite needs, it exits 2 with "load check only".
- No script writes `__pycache__` any more, and `~/.cache/rr-tools/py` is on the path for numpy.
- Ladder labels closer than 40 px are staggered.
- SKILL.md now covers:
  - the handoff route for a subagent, and building as pre-flight in handoff mode;
  - that analysing synth output is only a smoke test;
  - the choice of the legacy Sound API (tech.audio.soundgroup_status);
  - running the listening test in Cowork.
- References updated: schema, licensing, brief-format, standards, fidelity. `design-notes.md` has a fix-round section.

## Rejected items
- **Recording the lobby question in the real bible now.** This run may only touch the skill and trial folders, and siblings are writing the bible in parallel, which is what caused F12. It is carried as `pending:lobby-audio`, with the exact command handed over.
- **Spawning the fresh critic.** This subagent has no Agent tool, and a remote session can't read the local pass folder. It is handed off instead: `critique-sound/pass-1/critic.md` is regenerated and no longer needs the maker's addendum.
- **"True peak over-reads tones", as stated.** The -5.44 reading comes from a sine that starts abruptly, whose band-limited peak really is about -5.41. The real problem was under-reading, and that is fixed.
- **Fingerprinting re-exported placeholders in `register` (F8, optional fix, declined).** A re-export changes the bytes, so a match would never fire.

## Re-trial (trials/rr-soundsmith; real bible, no wrapper)
- `validate --strict`: PASS, with 0 errors, 0 warnings and 5 notes.
- The old soundmap that cites OQ-037 now gets a WARN ("wrong number?"). Log: `logs/logs_fix_validate.txt`.
- `validate --release` with every sound unassigned: PASS, with a "ships silent" note.
- `synth`: all 5 placeholders are byte-identical to the first trial (same sha1), including lobby_bed from its built-in recipe.
- The simulated owner file still fails on 92.2 ms of lead silence, and `--fix-out --mono` fixes it to a PASS.
- `sheet`, `crit` and `critic_kit build`: the critic order is about 5,050 tokens and carries the event table.
- `build`: PASS. `luatest --map` on the built map: 59/59.
- RUN_SOUND_MAP.md is regenerated with the corrected notes.
- Against the old runtime, the new tests score 51/59; the 8 failures are exactly the bugs this round fixed.

## Validator result
- selftest: 81/81 (was 62). luatest: 59/59 (was 50).
- `quick_validate`: "Skill is valid!"
- SKILL.md is 124 lines; the description is 1015 characters with no angle brackets.
- No `__pycache__` left in the skill or trial folders.
- rr-bible was only read. Its `git status` shows edits, but they come from sibling skills.

## Package
/home/user/claude/dist/rr-soundsmith.skill (18 files, 104.7 KB)

## Scores
- Reviews: 7 and 6.5 (before the fix).
- Critic: not run, so the plan is not certified yet; no self-score.

Files are in /home/user/claude/trials/rr-soundsmith:
- REPORT.md (not written; this text is the report)
- logs/logs_fix_validate.txt
- logs/logs_fix_selftest.txt
- logs/logs_fix_luatest.txt
- critique-sound/pass-1/critic.md
- export/sound/
- RUN_SOUND_MAP.md
- analysis/ANALYSIS.txt