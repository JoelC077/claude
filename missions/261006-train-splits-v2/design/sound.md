# P6 design: sound v2 for train splits ("literally the best sounds ever", L9-L10)
> **Read with mission.md Overrides O1-O12** (2026-10-06, after the 3-lens review in ../review/): where this file disagrees with mission.md, mission.md wins. Key ones here: O6 lead/late policy + PreRollMs, O8 sound bars + size ladder, O9 sourcing (CC0/Sonniss/claude_synth; Roblox-licensed runtime-only; timed legacy fallback).

Mission 261006-train-splits-v2 · planning only · sources: refs/v1-kit.facts.md (P1), canon-skills.facts.md (P2),
roblox-audio.facts.md (P4), rr-soundsmith SKILL + references. Beat times are v1 values (est.); P5's timeline wins.

## 1. Where v1 stands, and the v2 bar
**v1:** 6 synthesised 48 kHz mono WAVs (tear, boom, glass, debris, topple, scrape; topple_crash_2 reuses topple) on legacy
Sound/SoundGroup via RR_Sound; Profile S 8/10 after 2 passes, no final fresh pass. **Never heard, never uploaded, Config
ids "" → silent in game.** SOUNDS.md and Config disagree on group and Volume. Synth is placeholder grade (P4 §E,
av.audio.placeholder): v2 **replaces every file**, keeping v1's timeline, ladder, ducks and voice plan as the base.

**"Best ever", as checks (all must pass):**
| bar | check |
|---|---|
| Layers | hero sounds (70, 30, 0 %) ≥4 layers: transient 2-6 kHz, body 60-250 Hz, saturated punch 150-400 Hz, tail; others ≥2 (recipe file shows them) |
| Variations | ≥3 round-robin variants for anything that fires more than once a run (final blast 2); no variant twice in a row; pitch ±3-5 %, gain ±1.5 dB |
| Perspective | close/mid/far renders for booms, tear, crash (far: less HF, more tail, delay) + a 2D train-wide body layer |
| Ladder | canon in-game levels (t1 -9, t2 -11, t3 -13, t4 -15 LUFS); booms rise ≥1 LU per step 70 → 30 → 0; order holds under the phone model (HP 450 / LP 10k) |
| Phone | every t1-t3 sound within its class phone-loss limit (`sound analyze`); confirmed on Joel's phone at half volume |
| Timing | file onset ≤5 ms (tear: designed lead); in game each cue within 1 frame (16.7 ms) of its VFX beat, logged by the lab overlay |
| No fatigue | 20 splits in a row: Joel never hears "that one again"; no loop seam click (analyze) |
| Sign-off | §5 listening test passes on phone speaker **and** headphones; Joel types "SOUND v2 OK" |

## 2. Sound event map v2
Groups: **D** = new Destruction bus; **A** = Alarms. Perspectives: C/M/F = close/mid/far. Tiers follow canon.
| event id | trigger | layers | var | space | persp | duck / priority | status |
|---|---|---|---|---|---|---|---|
| creak_warn | integrity within ~5 pts above 70/30/0 (est.; P8 sets) | low groan (modal 80-400 Hz) + squeal + rivet ticks | 4 | 3D at the next break | - | t4 D, cooldown 4 s | PROPOSED |
| alarm_integrity | below 10 % (est.) | 2-tone klaxon with its own band and rhythm (OQ-035: 2D + positional) | 1 loop | 2D + 3D | - | t2 A, crisis duck | PROPOSED (default off) |
| tear_70 / tear_30 | t -0.25 before each snap | crack + sheet rip + rivet pops + low thump | 4 | 3D at the break | C/M/F | t3 D | CORE |
| glass | t 0, 1-2 panes, 0.1 s stagger | break + shard tinkle (3-8 kHz grains) + falling bits | 4 | 3D per pane | C/F | t3 D, cooldown 0.08 | CORE |
| boom_70 | t 0, integrity hits 70 % | crack + body + sub + tail + debris sweetener | 3 | 2D body + 3D crack/tail | C/M/F | t2 A at -11; "split" duck | CORE |
| boom_30 | t 0, integrity hits 30 % | as boom_70, larger body and longer tail | 3 | 2D + 3D | C/M/F | t2 A at -10 (trim +1) | CORE |
| debris_rain | t 0.8 | scattered metal/wood hits, dense then sparse | 4 (sheet) | 3D at the break | C/F | t4 D | CORE |
| scrape_loop | t 0.3 to V/12 s, rate from Speed | grind loop + spark hiss | 2 | 3D, follows the wreck | - | t4 D, keyed loop | CORE |
| topple_crash | wreck impact (v1: 1.5 / 2.0 s) | crunch + thud + metal ring-out | 4 | 3D at the wreck | C/M/F | t3 D (2nd body t4) | CORE |
| wreck_land | wreck comes to rest | heavy settle + bounce clunk + dust hiss | 3 | 3D | M/F | t4 D | CORE |
| fire_loop | burning wreck / 0 % hulk (if P5 adds fire) | crackle grains + roar bed | 1 (60 s est.) | 3D | - | t5 D, loop -20 | PROPOSED |
| chain_pop | 0 % sequence: one per carriage/part, P7 beats | short boom (crack + body), rising pitch per pop | 5 | 3D at each part | C/M | t2 D, steals debris first | CORE |
| preboom_suck | 150-250 ms before final_blast | reverse swell into hard duck (near silence) | 1 | 2D | - | ducks all except D | CORE |
| final_blast | integrity hits 0 % | crack + pressure body + sub + 6 s roll + debris + glass sweep | 2 | 2D stereo + 3D | C/M/F | t1 A at -9 = boiler fail; "fail" duck | CORE |
| gameover_sting | after final_blast, at the results cut | reuse canon `fired_stamp` + new "deflate" sweetener; no music (OQ-021 A) | 1 | 2D | - | t2, UI | CORE (reuse) + PROPOSED sweetener |
| fling_whoosh | server confirms a fling | air whoosh; rate and volume follow speed | 4 | 3D on the character (2D for yourself) | - | t4 D; local player plus 2 nearest only | CORE (L11) |
| body_impact | ragdoll contact (3 tiers by speed) | thud + cloth + light crunch (cartoon, no gore) | 3 per tier | 3D | - | t4 D, cooldown 0.15 per player | CORE (L11) |
| comic_sweet | fling apex or landing: boing, slide whistle, cartoon pop, coin jingle | synth plus CC0 | 6 | 3D, dry | - | t3 D, at most 1 per fling | PROPOSED |
| diesel_sweet | per-train flavour (diesel cough or sputter at the split) | recorded engine sputter | 2 | 3D | - | t4 D | PROPOSED |
Tone: big but slapstick (v1 A6); never war or horror (identity.tone); "slapstick lands through sound" (av.audio.slapstick).

## 3. Engine architecture
- **Decision: Audio API for a new Destruction bus (D); everything else stays on legacy RR_Sound.** Why: Roblox
  discourages legacy Sound (P4 §A, H), and D needs effects legacy cannot wire (EQ, glue compressor, limiter, low-pass for
  slow-mo, pitch shifter). Fallback: `Config.Audio.Backend = "audioapi"|"legacy"`, same soundmap and asset ids; legacy
  is forced if an AudioPlayer is not IsReady at init or the Studio test fails. Unverified: AudioInteractionGroup to
  isolate D's listener, PreloadAsync on AudioPlayer.Asset, Audio API cost on phones.
- **Mix graph:** Master = Ambient (wheels, wind) + Train + Events + Music; Events = Alarms, Actions, UI (legacy) and D
  (players → emitters/faders → EQ → compressor → limiter -1 dBFS → device output).
- **Ducking:** v1's scripted controller (deterministic, Lua-tested; canon "scripted over sidechain") drives SoundGroup and
  AudioFader volumes alike. Keep `split` and `fail`; add `preboom` (all but D -30 dB in 20 ms, hold 150-250 ms, then
  `fail`). Sidechain inside D (booms duck debris and whooshes 3-6 dB): PROPOSED polish.
- **Distance:** custom attenuation tables from v1 presets (6/90, 10/140, 16/240 studs). Each client picks the C/M/F render
  at trigger by distance (<40, 40-120, >120 studs, est.; train 165): no runtime filters, cheap and predictable. Doppler
  off (world is CFramed).
- **Slow-mo** (only if P7 keeps one): pre-rendered time-stretched `_slow` tail of final_blast, AudioFilter low-pass
  (~800 Hz est.) on world buses, sweeteners dry. Hit-stop (≤150 ms, canon proposed) leaves audio alone.
- **Latency:** the server sends the snap time (GetServerTimeNow + v1 0.25 s lead); each client schedules sound and VFX
  from that one t0 on one Heartbeat runner. D's sheets (~12-16 assets est.) preload at train spawn; a layer that is not
  ready is skipped, never delayed.
- **Voices (phones):** 16 one-shots (v1 assumption, unverified): D 8, Alarms 6, Actions 8, UI 4; steal by tier then
  oldest. Priority final_blast > boom > chain_pop > tear > crash > glass > debris > whoosh > sweetener; blast and booms
  protected; other players' flings play impacts only beyond the nearest 2. Peak at 0 %: blast 2 + chain 2 + debris 2 +
  spare 2 (est.).

## 4. Sourcing and production pipeline
| layer family | source (licence-clean, av.audio.licence) | search terms | fetch |
|---|---|---|---|
| tear, creak, scrape, crash | Sonniss #GameAudioGDC bundles (free, royalty-free, no attribution; contents unverified) | metal tear, sheet metal rip, metal stress groan, hull creak, metal scrape loop, car crash, container drop, rivet | owner (blocked here) |
| glass | Sonniss; Roblox-licensed Creator Store | window smash, glass shatter, glass debris | owner |
| explosion crack/body/tail | Sonniss; Roblox-licensed | explosion close, explosion distant, dynamite, thunder roll (no gunshot or war packs) | owner |
| debris, body impacts | Kenney CC0 on GitHub (README proof); Sonniss | impact, debris metal, body fall, box drop | **session (git works)** + owner |
| sub, whoosh, preboom, fire roar, klaxon, sweeteners | synthesised here (P4: production grade) | - | session |
| fire crackle | Sonniss | fire crackle loop, bonfire | owner |
| upgrade if round 1 fails glass/tear | BOOM Library or Pro Sound Effects (paid, est. tens-low hundreds USD) | - | owner |
- Refused unless Joel changes canon: Freesound CC-BY/NC, Zapsplat free, Pixabay, BBC RemArc, community Creator Store
  (OQ-036). Joel pulls 3-5 candidates per family (~80 WAVs est.) into a private place the session can read (Q4); raw
  Sonniss files never go public.
- **Chain** (mission-local `src/sound/design/render.py`; pip pyloudnorm, soundfile, pedalboard, librosa, scipy): JSON
  layer recipe (source, offset ms, gain, pitch, EQ) → trim and align onsets → 30 Hz HPF → assemble → 2nd/3rd-harmonic
  saturation on body/sub (phone) → C/M/F renders (far: LP 3-4 kHz, convolution tail, delay) → glue comp → -1 dBTP
  limiter → `sound analyze --fix-out` → variants packed into OGG sound sheets (regions generated into config).
- **Masters:** one-shots -14 LUFS M-max, loops -20 integrated, ≤ -1 dBTP, 48 kHz; mono for 3D, stereo only for 2D hero
  layers. The mix lives in data (rebuild, not re-upload).
- **Names:** `rrs_<event>_<layer|persp>_v<n>_r<rev>.ogg`, sheets `rrs_sheet_<family>_r<rev>.ogg`; an uploaded rev is
  never overwritten; assets.json maps rev → id.
- **To Roblox:** Joel bulk-imports in Asset Manager (≤40 uploads with revisions est.; quota 100/30 d, 2,000 if
  ID-verified), grants the experience, pastes ids into `UPLOAD_IDS.csv`; the session runs `sound register` and rebuilds.
- **Ledger:** `src/sound/LICENCES.csv`: final rev | every source file | pack | licence | proof (PDF, receipt or README URL)
  | origin (a mixed asset takes its most restrictive source).

## 5. Quality gates
1. **Soundsmith (measured):** `validate --strict` PASS; `analyze` 0 FAIL on finals, each WARN accepted in writing; phone
   loss within class limits; ladder order holds after the phone model; `luatest.py` PASS incl. Audio API mocks; `build`
   PASS; `validate --release` PASS.
2. **Profile S critic** (fresh; bar 8 per D-020, target 9 on S1-S3). **It cannot hear.** It checks hierarchy from
   measured levels, timing against P5's beats, modelled phone survival, fatigue maths (variants, cooldowns, voices),
   layer band coverage from spectrogram/band plots, brief and style fit, coverage. A 9 only earns the listening test.
3. **Joel's listening test** (Studio `RR_SoundLab`, ~20 min): keys 7/3/0 trigger the events, F flings, R repeats 20×.
   Phone speaker at half volume (Team Test) and PC headphones. Blind A/B (random X/Y, revealed after the vote): v1 vs v2,
   and variant A vs B per hero sound. **Pass:** each hero sound ≥4/5 on both devices; no "replace"; 3 booms ordered by
   size blind; every event named eyes-shut from the far coach; v2 beats v1 every time; no "late" flag in the frame
   overlay; no repeat noticed in the soak. Notes (keep/louder/quieter/replace per sound) become trim_db or a re-render.

## 6. Build task list
Model/effort as suggested; tokens est.
| id | deliverable | skill / commands | depends | model/effort | est. tok | done-when | owner steps |
|---|---|---|---|---|---|---|---|
| S0 | env setup line for audio deps | pip line for the setup script | - | sonnet/low | 5k | imports OK in a fresh session | paste it into the env settings |
| S1 | soundmap v2 (`src/sound`, `RR_SOUND_PRESETS`) | `sound where`, copy presets, edit, `validate --strict`, `oq` | P5 beats, P7 sequence, P8 intake of hook names | opus/high | 60k | strict PASS; pending OQs listed | - |
| S2 | placeholders + preview WAVs per event (timing only) | `sound synth all --out ph`, mission timeline render | S1 | sonnet/med | 30k | 4 previews (70/30/0/fling) | optional listen |
| S3 | briefs + SOURCING.md + Kenney CC0 pull | `sound build`, git clone CC0 repos | S1 | sonnet/med | 40k | every layer has a source route and terms | - |
| S4 | raw candidates delivered | - | S3 | owner | - | ~80 WAVs readable here, licence PDFs saved | download Sonniss, pick, drop (Q4) |
| S5 | render.py + recipe schema + tests | python, pedalboard | S0 | opus/high | 80k | renders variants/persp/sheets; tests PASS | - |
| S6 | hero pass: booms 70/30, final_blast, chain_pop, preboom, tear, glass | render.py, `analyze --fix-out`, `sheet` | S4, S5 | opus/max | 150k | gate 1 PASS for these | - |
| S7 | support pass: debris, scrape, crash, land, fire, whoosh, impacts, sweeteners | same | S6 | opus/high | 100k | gate 1 PASS | - |
| S8 | Profile S critic loop to bar | `sound sheet`, `sound crit … --owner-away`, critic_kit | S7 | opus/high (fresh critic) | 80k | ≥8 all, ≥9 S1-S3 | - |
| S9 | runtime: Audio API backend, D bus, sheet regions, perspective pick, pool, preload, preboom duck, slow-mo hooks, legacy fallback | RR_Sound adapter (mission copy), `luatest.py` with mocks, `build` | S1, P8 client timeline | opus/high | 120k | luatest + build PASS; fallback test PASS | - |
| S10 | RR_SoundLab panel + blind A/B + frame overlay + listening sheet | Luau + md | S9 | sonnet/high | 50k | luaparse PASS | - |
| S11 | upload + register | `register --dry-run`, then `register`; `validate --release` | S8 | sonnet/low | 20k | release PASS | upload ~16 assets, grant access, paste ids |
| S12 | listening round 1, then revision | trim_db edits or re-render, re-upload revs | S10, S11 | opus/high | 60k | feedback applied | run the test (§5), send notes |
| S13 | round 2 sign-off + promote + friction log | `sound promote`, SKILL-FRICTION.md (gaps G3, G4) | S12 | sonnet/med | 20k | "SOUND v2 OK" logged; promoted | type sign-off; approve promote |
Total est. ~815k tokens across sessions, plus 2 owner listening rounds and 1-2 upload rounds.
