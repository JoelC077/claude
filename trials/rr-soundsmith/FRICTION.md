# FRICTION — rr-soundsmith trial run

Task: full sound map + SoundGroups/ducking config Luau for a run (lobby, departure, junction, crisis, arrival),
5 placeholder WAVs, loudness analysis, sourcing brief. Skill followed as written; skill not edited.
Each entry: where, what happened (evidence), severity (H/M/L), suggested fix.

Result: 17 friction points. H 2 (F1, F9) · M-H 1 (F12) · M 4 (F2, F3, F10, F11) · L-M/M-L 4 (F4, F14, F15, F16)
· L 6 (F5, F6, F7, F8, F13, F17). Two blocked the skill's own path (F1 strict gate, F9 critic inputs) and needed trial-side workarounds.

## F1 · New sounds cannot get a placeholder without editing skill code (H)
- Where: SKILL.md step 1 + step 3, references/schema.md ("should have a synth recipe (synth.py --list)"), sound.py
  `cmd_synth` (`sy.render(sid, sid, ...)`) and validate (`no placeholder recipe` is a warning, so `--strict` fails).
- Evidence: adding the 4 lobby sounds to the mission copy of soundmap.json -> `sound validate --strict` =
  `validate FAIL: 0 errors, 4 warnings` (logs/logs_validate1.txt), all "no placeholder recipe (synth skips it)". A mission
  only copies presets/, so the step-2 gate is unreachable for any new sound without editing `<snd>/scripts/synth.py`.
- Workaround used: trials/rr-soundsmith/tools/ph_recipes.py registers 4 recipes into `synth.RECIPES` and calls
  `sound.main` (validate PASS, logs/logs_validate2.txt).
- Fix: let a sound name a recipe in data (`"synth": "ticket_chime"` alias, or a small param recipe such as
  {tone, noise band, env}), and/or load extra recipes from `$RR_SOUND_PRESETS/recipes.py`; make "no recipe" a note,
  not a strict-gate warning.

## F2 · No lobby / queue / results phase in the preset map, schema or SKILL.md (M)
- Evidence: preset soundmap has 25 sounds and 26 events, none for the Depot Lobby (queue pad join, 15 s countdown
  `gameplay.run.queue_countdown_s`, launch/teleport `tech.data.launching_lock`, lobby ambience). rr-game-feel's
  feel.json has no lobby events either. SKILL.md never says "lobby"; canon has no lobby audio facts.
- Effect: the task's first phase had to be designed from scratch (4 sounds, 6 events) and needed a new open
  question (lobby music vs diegetic bed; OQ-037 in the sandbox canon).
- Fix: ship lobby_bed / queue_punch / queue_bell / guard_whistle (or equivalents) in presets with recipes; add a
  `phase` field (lobby, depart, run, fork, crisis, arrive, results) so `list`/`sheet` can show coverage per phase.

## F3 · Critic route is ambiguous for a subagent that also has create_session (M)
- Where: SKILL.md step 7 "No Agent tool: follow rr-mission-control's critic route".
- Evidence: rr-mission-control SKILL.md line 46 orders agent -> remote (create_session) -> handoff. This run has
  `mcp__Claude_Code_Remote__create_session` but runs as a workflow subagent. A remote container cannot read
  /home/user/claude/trials/... (the sheet PNGs), so `remote` means publishing images as Artifacts first (cost and
  visibility) for a plan critique. Chose `handoff` (cheapest honest route); the skill does not say which wins.
- Fix: in SKILL.md step 7, "subagent/workflow run -> handoff even if create_session exists; remote only when the
  pass folder is reachable or publishable".

## F4 · Canon writes during a trial or dry mission are not covered (L-M)
- Where: "Canon first" says `bible.py add-question ...` for missing canon; no dry-run/sandbox guidance.
- Evidence: the trial may only touch its own folder, yet lobby audio needed an OQ. rr-bible supports `--canon DIR`
  / `$RR_BIBLE_DIR`; sound.py's subprocess inherits it, so copying canon to trials/.../canon-sandbox worked
  (OQ-037 added there, lint OK, real bible untouched: `git status rr-bible` clean). Against the real bible the same
  soundmap fails: `ERROR OQ-037 cited but not found in rr-bible`.
- Fix: one line in SKILL.md: "trial or owner-absent run: export RR_BIBLE_DIR=<copy> or use `--dry-run`; the OQ number
  is provisional until recorded in the real bible".

## F5 · `bible.py get questions` is a token sink (L)
- Evidence: the skill's canon list includes `get questions`, which prints all 36 OQs (36 lines, most unrelated:
  HUD skin, marketing budget...). The three audio OQs were then needed in full anyway (`get OQ-021` etc.).
- Fix: replace with `get OQ-021`, `get OQ-035`, `get OQ-036` (already named under "Open decisions").

## F6 · Skill folder ships a __pycache__ (L)
- Evidence: `find /home/user/claude/rr-soundsmith` at trial start listed `scripts/__pycache__/audiolib.cpython-311.pyc`
  before any command of this trial ran. Build rule says remove __pycache__. selftest.py removes it at the end
  (line 230), so it was gone after the trial's selftest run; any other command (sound.py imports audiolib/synth/sheet)
  recreates it in the skill folder. Fix: `sys.dont_write_bytecode = True` at the top of sound.py and luatest.py.

## F7 · Two ways to resolve `<critic>` (L)
- Evidence: SKILL.md's glob `find ~/.claude/skills /home/user ... | head -1` returns the synced copy under
  /root/.claude/skills/synced/.../multiuse-critic; sound.py `find_sibling` prefers the sibling
  /home/user/claude/multiuse-critic. Identical today (`diff -rq` empty), but they can drift apart silently.
- Fix: SKILL.md tells the agent to take the critic path that `sound crit` prints, not its own glob.

## F8 · Analysing self-made placeholders is circular (L)
- Evidence: `sound analyze src/sound/ph` = 5 PASS, because `synth` levels each file with the same BS.1770 meter
  (e.g. m_max -14.0 exactly). The analysis proves only length/phone/peak shape. Useful signal came from a simulated
  owner drop (analysis/owner_drop_sim: +6 dB, 90 ms lead, stereo) -> FAIL "92.2 ms of silence before the sound",
  WARN peak -0.93 dBTP; `--fix-out --mono` -> PASS at -14.0. Also: the simulated re-export lost the INFO tags and
  was no longer recognised as a placeholder (only tags and names mark one): `register whistle --file
  .../whistle_v2_std.wav --source owner_upload --origin self-made --proof trial --dry-run` is accepted, while the
  tagged original is refused (logs/register_dryrun.txt). Any string passes as --proof.
- Fix: SKILL.md step 3/4 could say "analysis of synth output is a smoke test; judge the analyzer on owner files";
  optionally match PLACEHOLDERS.md sha1/fingerprints in `register` to catch a re-exported placeholder.

## F9 · Critic order promises evidence it does not contain; S5 and S6 cannot be scored (H)
- Where: `sound crit` + `sound sheet` (facts.md) -> critique-sound/pass-1/critic.md.
- Evidence: critic.md line 13 says "Facts has the measurements and the event table"; facts.md has no event table, no
  brief text and no emitter list (`grep -i "must say\|sounds like" critic.md` = only rubric lines). Yet S5 is judged
  "through the brief text" and S6 needs "every event mapped, every sound briefed, emitters named", and the order
  forbids opening any other file. A fresh critic would have to guess or score S5/S6 on nothing.
- Workaround used: appended a 29-row "Event map and brief lines (maker addendum)" (events, space/emitter, must_say,
  avoid; ~1.3k tokens) before "## Images"; the untouched original is critique-sound/critic.pass1.generated.md.
- Fix: `sheet` writes that table into facts.md (it already has everything in the Model).

## F10 · Coverage in the sheet conflates "no file" with "no sound" (M)
- Evidence: facts.md "5 of 29 sounds have a file here ... Missing: boiler_boom, alarm_pressure, ..." while the S6
  anchor 4 is "Events with no sound". With a partial placeholder set (this task: 5 by request), the critic reads 24
  "missing" sounds that are in fact mapped and briefed. Handled by a scope note in the F9 addendum.
- Fix: split Coverage into "mapped + briefed: 29/29, events 32/32" and "files present: 5/29 (scope)".

## F11 · Open-decision lists are hard-coded, so new OQs never reach the owner or the critic (M)
- Evidence: SOUND_SPEC.md "Open decisions" and the critic brief "Owner worries" are fixed strings (sound.py:1059 and
  :1195) naming OQ-021/035/036 only. OQs cited by sounds (OQ-037 lobby here; also OQ-031, OQ-013, OQ-012, OQ-003 in
  the presets) are absent from both, and `meta.oq` is ignored.
- Fix: build both lists from `meta.oq` plus every sound's `oq`, reading title and default through the Bible class.

## F12 · OQ citations are checked for existence only; a sibling's OQ silently took the number (M-H)
- Evidence: the lobby question was OQ-037 in the sandbox (F4). Minutes later rr-release-train added a different
  OQ-037 ("Release version scheme and channels", src RT) to the real bible. Now
  `validate --strict` against the real bible = PASS and the lobby_bed brief says "Open: OQ-037 (defaults in use)",
  pointing at the release-version question. Before that commit it was a hard ERROR.
- Fix: validate that a cited OQ's `affects`/`blocks`/context mentions rr-soundsmith, the sound id or an av.audio key
  (warn otherwise); SKILL.md: re-read the OQ number after `add-question` and cite that.

## F13 · Brief wording assumes the train for every 2D sound (L)
- Evidence: AUDIO_BRIEFS.md lobby_bed / queue_punch / queue_bell / guard_whistle say "Space: 2D, heard train-wide";
  the lobby has no train. Hard-coded at sound.py:837.
- Fix: "2D (global, same level everywhere)" or a per-sound `where` text.

## F14 · `luatest.py --map` runs no tests but exits 0 (M-L)
- Evidence: `luatest.py --map export/sound/RR_SoundMap.lua -v` prints only "loaded ...: 29 sounds, 32 events", exit 0
  (luatest.py lines 309-314 return right after loading). Its --help says it "Loads the map ... then checks: group
  tree, pools, ...". The default run (fake ids from the mission soundmap) gives 50/50, which is the real check.
- Fix: run the suite on the given map (inject fake ids where missing) or print "load check only, 0 tests".

## F15 · Step 6 duplicates step 8; the sourcing brief is long and has no summary (L-M)
- Evidence: `brief all --out AUDIO_BRIEFS.md` (step 6) and `build` (step 8) both write AUDIO_BRIEFS.md (identical;
  root copy removed). The file is 42.4 KB / 475 lines for 29 sounds; the same licence sentence is repeated 29 times
  (6.5 KB, 15%). No phase order and no shopping list (what to source first, Creator Store search terms vs commission,
  variation counts in one table), which is what an owner or a sound designer scans first.
- Fix: step 6 only for ad-hoc subsets; put the licence rule once in a header plus a summary table (id, phase, tier,
  variations, length, route), then the per-sound briefs.

## F16 · Handoff mode vs step order (L-M)
- Evidence: step 7 (critic) comes before step 8 (export), and rr-mission-control's handoff route says "return that
  path and stop". The task needed the Luau export in the same run. SKILL.md does not say whether `build` may run
  before a verdict. Built anyway (pre-flight allows `build --no-check`) and marked the export "critic pending".
- Fix: say "in handoff mode, build as pre-flight, hand over the pass path, and re-build after fixes".

## F17 · Contact sheet ladder labels collide (L)
- Evidence: src/sound/sheet/contact.png top axis prints "ambient" (-27) and "music" (-25) as "ambientmusic".
- Fix: stagger labels closer than ~40 px.

## What worked (no friction)
- Canon reads through rr-bible were cheap and exact; `validate` proved canon numbers, feel cue parity (26 feel events,
  priorities vs tiers) and caught a missing OQ as a hard ERROR (against the real bible, before F12's collision).
- `synth` 5 placeholders in 3.4 s, each at the class target (m_max -14.0 / integrated -20.0), INFO-tagged, manifest
  with sha1; `analyze` flagged a simulated bad owner file precisely (92.2 ms lead FAIL, -0.93 dBTP WARN) and
  `--fix-out --mono` fixed it to PASS without touching the source.
- Licence gate refused a PLACEHOLDER-tagged file posing as owner audio (dry-run).
- `build` PASS in 1.7 s: RR_SoundMap.lua, runtime, demo, studio_sound_setup.lua, SOUND_SPEC.md, briefs, licences,
  README; luaparse on 4 Lua files and `bible check` on 8 files. luatest 50/50 on the mission soundmap (ducking
  attack/hold/release, stealing, speed link, Feel bridge, 3D alarm layer); selftest 62/62 in 40 s.
- `sheet` + `crit` + `critic_kit.py build` produced a ~3k-token critic order and a readable contact sheet first time.
- Mission layout (`RR_SOUND_PRESETS=<M>/src/sound`) kept every write inside the trial folder.
