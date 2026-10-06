# Mission 261006-train-splits-v2
Objective: Plan v2 of the train split system. The splits at 70% and 30% integrity and the full-train explosion at 0%
should get the best VFX, animation and sound, plus flinging and clip moments, on every train (Coal, Diesel, future
ones). The plan must be buildable session by session from the files in this folder once Joel is back.
Kind: mixed (fx + motion + sound + Luau + mechanics) · Profiles: F+M+G (av), S (sound), A (3D tear), security gate ·
Bar: 8; sound 9 (L10 "best sounds ever", a 10/10 ask, becomes 9; met by Joel's listening round 2) · Cap: 5 passes per
critic group.
Env:
- cloud; blender = bpy 5.0.1 headless (Cycles CPU); lune 0.10.5; agents = yes (critic_mode agent); Studio/Blender MCP:
  none
- the network blocks roblox.com, freesound and sonniss (GitHub and PyPI work)
- repo JoelC077/claude is PUBLIC, and its default branch is claude/gracious-goldberg-crtklz (this mission lives on
  claude/zealous-newton-h08ds8)
This turn = steps 1-4 (planning) plus an adversarial review (review/). Steps 5-10 are the build, per ROADMAP.md.
Cost:
- planning this turn: ~1.9M est. (workflows 1.58M measured + orchestration)
- build: ~3.5M est. (bottom-up; plan.py 2.6M, band 1.9-3.3M)
- lean path: ~3.0M (ROADMAP.md)

## Source prompt
prompt.raw / prompt.txt (verbatim) and lines.md (L1-L16). Shared brief: refs/context.md.
Facts: refs/v1-kit.facts.md, refs/canon-skills.facts.md, refs/roblox-vfx-physics.facts.md, refs/roblox-audio.facts.md.
Designs: design/vfx-animation.md (P5), design/sound.md (P6), design/clip-gameover.md (P7), design/systems.md (P8),
design/mechanic-review.md (P9). Reviews: review/engineering.md, review/av-quality.md, review/producer.md.
**Where a design file disagrees with this file, this file wins (Overrides O1-O12).**

## Requirements
| id | owner words | requirement | type | source | status | done-when |
|---|---|---|---|---|---|---|
| R1 | "its time to start on the new split system" | v2 of the train split system, built on v1 (mission 260929-train-splits) | context | L1 | planned | session 1 run from ROADMAP.md |
| R2 | "added a Diesel Train, which already has its split sorted" | v2 works on the Diesel and keeps Joel's own Diesel split (profile mode presplit or external). Per-train profiles replace v1's CoalTrain-only roof signature and 2-carriage loops | constraint | L2 | planned | Bench.run("all") passes on Coal and Diesel in Studio (T12) |
| R3 | "integrated universal compatibility, so all events work regardless of the train selected" | v2 hooks into Joel's train-agnostic event layer through one bridge plus 5 small host patches (O11). No train names in the split code. His events skip lost sections (IsSectionPresent) | constraint | L3 | planned | contract.md bound to his real symbols; no train names outside profiles |
| R4 | "I have since also added an integrity system" | Joel's integrity system drives the split system; TrainSplit never writes integrity | context | L4 | planned | the bridge reads his signal (contract.md) |
| R5 | "split 1 (carriage 2) happens at 70% integrity" | At <= 70%, C2's rear half is lost (v1 mid-carriage break) with explosion, topple and fling | deliverable | L5 | planned | Lune threshold suites; Studio bench on both trains |
| R6 | "split 2 (carriage 1 and rest) happens at 30% integrity" | At <= 30%, C1's rear half and everything behind it are lost | deliverable | L6 | planned | Lune order and multi-cross suites (O1); Studio bench |
| R7 | "Full train explosion (game over) happens at 0% integrity [HASNT BEEN WORKED IN]" | At 0%: a chain reaction through what is left, everyone flung, then hand-off to Joel's game-over flow (O2). For the alpha: a safe 0% path (T1b) | deliverable | L7 | planned | plays once on both trains; the fail flow opens once (T22, T35) |
| R8 | "better VFX, better animation" | VFX and motion v2 for 70/30/0: a style picked by Joel, layered hero bursts, flipbooks with scored fallbacks, a scripted topple with anticipation and overshoot, seeded debris (v1 fx critic: 5/10) | quality | L8 | planned | av final on real Studio captures (T36b): F, M and G each >= 8 (aim 9); budgets PASS |
| R9 | "extremely good sounds." | Sound v2: every v1 synth file replaced by layered recorded (CC0, or Sonniss if chosen) and synthesised sounds with variations and close/mid/far versions, on an Audio API bus | quality | L9 | planned | soundsmith gates PASS; critique-sound-v2 final per O8 |
| R10 | "Like, literally the best sounds ever." | Bar 9 for sound, met only by Joel's blind listening: round 0 (offline, end of session 4) and round 2 (in game, phone speaker and headphones) | quality | L10 | planned | Joel types "SOUND v2 OK" after round 2 |
| R11 | "work on the full train explosion, PLUS clipability (players getting flung, other funny things)" | Fling system (ragdoll; targets picked by the server, applied by each client; safe), the 0% wide shot, plus the clip extras chosen in Q3 | deliverable | L11 | planned | T19b spike + 2-client Team Test "FLING OK"; Q3 picks shipped |
| R12 | "plan out the roadmap for when I am back" | This turn: ROADMAP.md, mission.md, plan.json and session-1 orders, reviewed and pushed | deliverable | L12 | done | pushed; PLAN OK; COVERAGE OK; review fixes applied |
| R13 | "Use JARVIS and whatever else" | JARVIS process plus ultracode workflows (research, design, adversarial review) | process | L13 | done | progress.log; design/ and review/ files |
| R14 | "one of the most important systems in the game" | Full gates with none skipped; diagnostics first; real-engine checks early (T19b) and a final on real captures | quality | L14 | planned | every Acceptance gate has a final result in the debrief |
| R15 | "Confirm you can run on the cloud while my laptop is close" | Answer, with its limits (also in ROADMAP.md) | comms | L15 | done | answered in the reply and in ROADMAP.md |
| R16 | "would you reccomend max or ultracode" | Recommendation per session | comms | L16 | done | answered in the reply and in the ROADMAP mode column |
| R*17 | (implied) | Server-authoritative: remotes server to client only; fling targets and caps come from the server; exploit-guard gate | derived | L11 | planned | guard scan 0 high + reviewer verdict + 2-client grief test (T38o) |
| R*18 | (implied) | Phone budgets (OQ-029 plus O7: screen coverage, carry-over emitters), voice pool, Reduce Motion, flash limits | derived | L8 | planned | budget checks + MicroProfiler on Joel's phone in the test place |
| R*19 | (implied) | Joel's Studio code is the source of truth: export and diff before any integration code; repo made private first | derived | L2 | planned | refs/intake.facts.md exists; repo private |
| R*20 | (implied) | v1 loose ends closed: silent-test root cause, surviving Lune suites green, checker on RR_Half labels, 3D tear critic, sounds uploaded | derived | L1 | planned | T4-T6 done; critique-splits-v2 scored (T32/T32f) |

## Decisions and assumptions (defaults; say if wrong)
A1 70% loses C2's rear half (v1 mid-carriage break). 30% loses C1's rear half and everything behind it.
A2 One hit past several thresholds plays only the deepest stage (O1).
A3 Flings are cosmetic:
   - no damage, no keep-on fee, and the held item stays in hand
   - at 70%/30%, players are back on the train within 4 s of the snap
   - at 0%, they stay ragdolled until results
   - roofed riders go "through the roof": no train collision for 0.5 s, plus an up-raycast and a Y floor
A4 Riders on a lost section are flung off at the snap; they do not ride the wreck away.
A5 0% timeline: see O2 (one table, relative to t0).
A6 Joel's Diesel split is kept and mapped into v2 (profile presplit, or external if it moves parts itself). v2 adds fx,
   sound and fling on top.
A7 Split, explosion and fling audio moves to a new Audio API bus, with a Config switch back to legacy Sound (O9). The
   game's other audio is untouched apart from the pre-boom duck.
A8 Canon updates are recorded as Joel's decisions at T3 once he confirms (bible add-fact / decide):
   - integrity is the breakdowns' consequence meter (D-003 note)
   - 0% is a hard fail, train_explosion: same results screen, banked fare kept
   - flings are exempt from keep-on
   - passengers lost in a split leave the count
   - the audio licence classes sonniss_gdc (proof: licence PDF) and claude_synth (proof: recipe + render log) (O9)
A9 Bars: av 8 (aim 9), final on real captures · sound per O8 · 3D tear 8 · security gate PASS · perf within budgets.
A10 Phone first: OQ-029 budgets plus O7, Reduce Motion (GuiService.ReducedMotionEnabled), flash <= 3/s at peak 0.35.
A11 There are no Explosion instances anywhere: they kill Humanoids, have no falloff and reach at most 100 of the 165 studs.

Q1 (answer by 9 Oct) Alpha: canon has the alpha in the week of 12 Oct, steam only (D-015), and v2 cannot be ready by
   then. Default: v2 lands after the alpha.
   - For the alpha, 0% uses the existing boiler-fail path (fx, YOU'RE FIRED, results), firing once (T1b).
   - The current split stays only if it works in Joel's own playtest; otherwise it goes behind Config.Enabled=false.
Q2 Sound sources. "Best ever" needs recorded material, and this cloud cannot download it. Options:
   - A: Joel allows freesound.org and cdn.freesound.org in the environment's Custom allowed domains, and Claude pulls
     CC0 sounds. Whether this also needs a free API key is unverified; it is checked in session 3.
   - B: Joel downloads the free Sonniss GDC bundles (large) and picks about 80 files from Claude's search list
     (2-3 h), sent via Google Drive.
   - C: a paid pack, or commissioning a sound designer for the 3 hero sounds.
   Default: A + Kenney CC0 + synthesis. Listening round 0 decides whether to add B, then C.
Q3 Clip extras (pick any):
   - a: warning build-up before each split and before 0% (the mechanic review calls it needed so a hard fail is fair)
   - b: a slow or freeze beat inside the 0% wide shot
   - c: flying props
   - d: an auto screenshot + Share on results
   - e: a secondary explosion when a wreck lands (his earlier "more explosions for comedy")
   - f: a runaway wheelset
   Default: a, b, c, e; d later; f no. The lean path drops c and e.

## Overrides (final; they win over design/*.md)
O1 **Multi-cross**: the deepest crossed stage fires alone. lostSet = the union of all crossed stages. Example: 100 → 20
   fires S30 only, and C2's rear half is in lostSet. There is no stagger_s. Lune: 100→50 = S70 · 100→20 = S30 only ·
   100→0 = Destroyed only · a fired stage never re-fires. (Replaces systems.md section 2 multi-cross and the section 4
   order + stagger suite.)
O2 **0% timeline**, with t0 = the scheduled start (server time, sent with lead O6). The server chunk cap is a fixed 5
   including the heart chunk; PC adds cosmetic debris only.
   | t | beat |
   |---|---|
   | 0-0.2 | inhale: duck, glows drop, carry-over emitters fade |
   | 0.2 | first chain pop, then every 0.3 s, at most 4 pops, rear to front, each launching its riders |
   | 1.5 | hero blast at the heart (Coal: boiler; Diesel: fuel tank), fixed time; hit-stop 0.15 s local |
   | 1.65 | the wide shot (core) |
   | within 1.65-2.15 | Q3b slow/freeze beat, <= 0.5 s (chosen from the T12b animatic; default a hero-frame hold + camera push; all-client own-character slow at the shared t0 only if the animatic shows it reads better) |
   | 4.5 (blast + 3) | SequenceDone; Joel's fail flow shows YOU'RE FIRED, then results at about blast + 5 |
   His flow must not end the run before SequenceDone; his timeout is t0 + 6.5.
O3 **Motion authority**: wrecks and chunks animate on each client from the train attributes RR_SplitStage, RR_SplitSeed
   and RR_SplitT0, which late joiners read too. The server writes only the start pose, the final pose and the despawn: 0
   server CFrame writes per frame during motion. Lune: no per-frame writes; a late joiner rebuilds the pose from seed and
   t0. (Replaces vfx-animation.md section 3a "server writes 1 root CFrame per body".)
O4 **Streaming**:
   - T2 records StreamingEnabled, the streaming radii and ModelStreamingMode.
   - Setup v2 sets the train models to Atomic (or Persistent).
   - The payload carries train + stage + seed + t0 only, with no Instance lists; clients derive lost parts from RR_Half.
   - Bounded waits print [TS2-C] steps.
   - The MP tests add a far client and a stream-out/in during topple.
O5 **Fling path**:
   - A per-owner RR_Fling remote (server to the owning client) carries {kind, dir, mag <= cap}. The broadcast carries no
     fling data.
   - The server sets IsKinematic=false on the character's AnimationConstraints, which replicates to every client. The
     owning client applies velocity and recovery.
   - Verified in the T19b spike before T20-T22.
   - Wording: the system gives no player a new way to fling another; generic exploit flinging is outside it.
O6 **Timing**:
   - Lead >= 0.4 s (Config.LeadS).
   - Beats already past on arrival are dropped, except the snap. The boom is never shifted.
   - Config.Audio.PreRollMs covers device latency.
   - AV sync is checked on the phone in T37: film it with a second phone's slow-mo camera.
O7 **Phone budget additions**:
   - A translucent screen-coverage cap per camera, est. <= 35% for > 0.5 s, on roof3p and the phone tiles.
   - Carry-over emitters from 70/30 count in the 0% row and fade at the inhale.
   - A near-camera size/ZOffset rule for riders inside the fireball radius.
   - A fallback-only board per event, scored as an F-low row; the fallback is swapped in by script per quality level.
O8 **Sound bars**: soundsmith gates PASS; critic S1-S6 >= 8 with S1-S3 >= 9 (measured). The 9/10 "best ever" bar is met
   only by Joel's listening round 2. The size ladder from 70 to 30 to 0 is set by tail length (est. 2/3/6 s), sub
   extension, layer count, stereo width and the pre-boom silence; LU order is only a sanity check.
O9 **Sound sourcing and runtime**:
   - Sources: Kenney CC0 via GitHub; Freesound CC0 if Q2 A; Sonniss only if Q2 B; synthesis is registered as
     claude_synth.
   - Roblox-licensed audio is runtime-only (played by id), never an offline source.
   - Raw files travel via Drive, never git.
   - The legacy fallback is a timed check: AudioPlayer not IsReady 5 s after spawn means legacy, with a [TS2-C] step.
   - T2 inventories Joel's audio routing (SoundGroups, ambient and music owners).
O10 **Cameras**: roof3p_back, door1p_back, coach1p (30%), a forward-facing roof/cab cam, the clip cam and a phone
   844x390. F1 is also scored from the forward cam. Strips are dense around beats (every 2nd frame from -0.3 to +0.5 s),
   and T11's curve plots go into the critic packet.
O11 **Host patches** (T3b): 5 small patches to Joel's code, delivered as patch files with apply steps:
   1. the round flow waits for SequenceDone
   2. keep-on skips RR_FlingUntil
   3. the scroll driver brakes at 0%
   4. the event layer skips IsSectionPresent=false
   5. run_end gets the reason train_explosion
O12 **Checkpoints with Joel** before heavy spend:
   - T12b grey-box animatics (MP4 with placeholder audio): timing OK
   - T13b style frame pick
   - T19b Studio spike in the private test place: fling, Audio API on the phone, flipbook
   - T17b listening round 0, offline
   The test place is private and separate (T11p); the release gate covers the live game only.

## Spec (build source: design files + Overrides)
- Stage machine per train: Intact -> S70 -> S30 -> Destroyed, stored in the attribute RR_SplitStage; each stage fires
  once; reset = a fresh clone (Reset() cleans up).
- Bridge: TrainIntegrityBridge is the only file reading Joel's integrity API (attribute or callback; T2 decides). Host
  patches per O11.
- Profiles: TrainSplitConfig.Trains[profile] with breaks.mode tear | presplit | external | plane, stages 70/30/0,
  chunks (O2), flavour, heart, return points.
- Remotes: RR_TrainSplitFX v=2 broadcast {train, stage, seed, t0} (O4); RR_Fling per owner (O5).
- Beat sheets: design/vfx-animation.md section 2, with O2. Sound map: design/sound.md section 2. Fling numbers:
  design/clip-gameover.md section 2, with A3/A4 and the P9 ceiling fix.

## Acceptance
- av (critique-av-v2, one critic): F1-F6 >= 8 plus an F-low row (fallback-only), M1-M4 >= 8, G1-G6 >= 8; overall =
  lowest, aim 9. The final (T36b) is scored on Joel's real Studio/test-place captures. Budgets PASS per event,
  including O7.
- sound (critique-sound-v2): soundsmith validate --strict, analyze 0 FAIL, validate --release PASS; O8 critic bars;
  the 8 "best ever" checks (design/sound.md section 1, with the O8 ladder); listening rounds 0 and 2; "SOUND v2 OK".
- 3D tear (critique-splits-v2): A1-A7 >= 8 on the Coal tear with live geometry (v1 never scored it), with a fix round
  if needed.
- Systems: Lune 0 FAIL including the new suites (O1, O3, O4); Diagnose PASS and Bench.run("all") on Coal and Diesel;
  multiplayer checks (design/systems.md section 4 + O4); MicroProfiler within budgets on Joel's phone (test place).
- Fling: T19b spike, then solo and 2-client Team Test; no ceiling bonk; no void death; keep-on skipped; Reduce Motion
  honoured; "FLING OK".
- Security: guard scan 0 high/critical, independent reviewer verdict, fuzz kit + 2-client grief test (T38o), gate PASS
  (or HOLD on owner items only).
- Release: rr-release-train gate GO before any live publish; Joel confirms.

## Needs owner / placeholders
- Make JoelC077/claude private before uploading the place or sound files: it is public now.
- Start session 1 in this chat (it is on the right branch), or use the paste-ready prompt in ROADMAP.md.
- Answer Q1 (by 9 Oct), Q2 and Q3. The exports E1-E7 go into intake/ (design/systems.md section 1, plus O4/O9
  inventory). The 4 E7 answers.
- Optional: the env setup script line (audio + video tools); a Studio MCP for live Studio sessions (needs his PC on).
- Checkpoints in O12; flipbook and sound uploads; the private test place; Studio benches; listening rounds 0 and 2;
  phone perf; the multiplayer test; fuzz + grief test; release approval.
- OQ drafts (dry-run only, nothing written to canon): OQ-TBD-integrity-d003, -zero-fail, -fling-keepon,
  -split-passengers, -v2-alpha, plus the A8 licence classes.

## Next action
Owner: the ROADMAP.md "Before session 1" checklist (and "Before the alpha" if Q1 = yes). Then session 1: spawn T2
(tasks/T2.md) on M/intake/, plus T4 (tasks/T4.md) in parallel.
