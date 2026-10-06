# Mission 261006-train-splits-v2
Objective: Plan v2 of the train split system. The splits at 70% and 30% integrity and the full-train explosion at 0%
should get the best VFX, animation and sound, plus flinging and clip moments, on every train (Coal, Diesel, future ones).
The plan must be buildable session by session from the files in this folder once Joel is back.
Kind: mixed (fx + motion + sound + Luau + mechanics) · Profiles: F+M+G (av), S (sound), A (3D tear), security gate ·
Bar: 8; sound 9 (L10: "best sounds ever", a 10/10 ask, becomes 9) · Cap: 5 passes per critic group.
Env: cloud; blender=bpy 5.0.1 headless (Cycles CPU); lune 0.10.5; agents=yes (critic_mode agent); Studio/Blender MCP:
none; network blocks roblox.com, freesound and sonniss (GitHub works); repo JoelC077/claude is PUBLIC (2026-10-06).
This turn = steps 1-4 (planning). Steps 5-10 are the build, run per ROADMAP.md when Joel is back.

## Source prompt
prompt.raw / prompt.txt (verbatim) and lines.md (L1-L16). Shared brief: refs/context.md.
Facts: refs/v1-kit.facts.md, refs/canon-skills.facts.md, refs/roblox-vfx-physics.facts.md, refs/roblox-audio.facts.md.
Designs: design/vfx-animation.md (P5), design/sound.md (P6), design/clip-gameover.md (P7), design/systems.md (P8),
design/mechanic-review.md (P9).

## Requirements
| id | owner words | requirement | type | source | status | done-when |
|---|---|---|---|---|---|---|
| R1 | "its time to start on the new split system" | v2 of the train split system, built on v1 (mission 260929-train-splits) | context | L1 | planned | session 1 run from ROADMAP.md |
| R2 | "added a Diesel Train, which already has its split sorted" | v2 works on the Diesel and keeps Joel's own Diesel split (profile mode presplit or external). Per-train profiles replace v1's CoalTrain-only roof signature and 2-carriage loops | constraint | L2 | planned | Bench.run("all") passes on Coal and Diesel in Studio (T12) |
| R3 | "integrated universal compatibility, so all events work regardless of the train selected" | v2 hooks into Joel's train-agnostic event layer through one bridge file. No train names in the split code. His events skip lost sections (IsSectionPresent) | constraint | L3 | planned | contract.md bound to his real symbols; no train names outside profiles |
| R4 | "I have since also added an integrity system" | Joel's integrity system drives the split system; TrainSplit never writes integrity | context | L4 | planned | the bridge reads his signal (contract.md) |
| R5 | "split 1 (carriage 2) happens at 70% integrity" | At <= 70%, C2's rear half is lost (v1 mid-carriage break) with explosion, topple and fling | deliverable | L5 | planned | Lune threshold suites; Studio bench on both trains |
| R6 | "split 2 (carriage 1 and rest) happens at 30% integrity" | At <= 30%, C1's rear half and everything behind it are lost | deliverable | L6 | planned | Lune order and multi-cross suites; Studio bench |
| R7 | "Full train explosion (game over) happens at 0% integrity [HASNT BEEN WORKED IN]" | At 0%: a chain reaction through what is left, everyone flung, then hand-off to Joel's game-over flow | deliverable | L7 | planned | plays once on both trains; results open once (T22, T38) |
| R8 | "better VFX, better animation" | VFX and motion v2 for 70/30/0: layered hero bursts, flipbooks with fallbacks, scripted topple with anticipation and overshoot, seeded debris (v1 fx critic: 5/10) | quality | L8 | planned | critique-av-v2 final: F, M and G each >= 8 (aim 9); budgets PASS |
| R9 | "extremely good sounds." | Sound v2: every v1 synth file is replaced by layered recorded and synthesised sounds with variations and close/mid/far versions, on an Audio API bus | quality | L9 | planned | soundsmith gates PASS; critique-sound-v2 final >= 9 |
| R10 | "Like, literally the best sounds ever." | Bar 9 for sound, plus Joel's blind listening test on phone speaker and headphones | quality | L10 | planned | Joel types "SOUND v2 OK" after listening round 2 |
| R11 | "work on the full train explosion, PLUS clipability (players getting flung, other funny things)" | Fling system (ragdoll; targets picked by the server, applied by each client; safe) plus the MVP clip set from the mechanic review | deliverable | L11 | planned | 2-client Team Test "FLING OK"; the clip set chosen in Q3 shipped |
| R12 | "plan out the roadmap for when I am back" | This turn: ROADMAP.md, mission.md, plan.json and session-1 orders, pushed | deliverable | L12 | planned | files pushed; PLAN OK; COVERAGE OK |
| R13 | "Use JARVIS and whatever else" | JARVIS process plus ultracode workflows (research, design, adversarial review) | process | L13 | planned | progress.log; design/ and review/ files |
| R14 | "one of the most important systems in the game" | Full gates with none skipped (v1 skipped the fx/sound finals, the 3D critic and the security re-check); diagnostics first, so nothing ships untested | quality | L14 | planned | every Acceptance gate has a final result in the debrief |
| R15 | "Confirm you can run on the cloud while my laptop is close" | Answer, with its limits | comms | L15 | planned | answered in the reply |
| R16 | "would you reccomend max or ultracode" | Recommendation per session | comms | L16 | planned | answered in the reply and in the ROADMAP mode column |
| R*17 | (implied) | Server-authoritative: remotes server to client only; fling targets and caps come from the server; exploit-guard gate | derived | L11 | planned | guard scan 0 high + reviewer verdict + 2-client grief test |
| R*18 | (implied) | Phone budgets (OQ-029: 800 peak per 2 s, 400 live, 12 emitters, 8 debris), voice pool, Reduce Motion, flash limits | derived | L8 | planned | budget checks + MicroProfiler on Joel's phone |
| R*19 | (implied) | Joel's Studio code is the source of truth: export and diff before any integration code; repo made private first | derived | L2 | planned | refs/intake.facts.md exists; repo private |
| R*20 | (implied) | v1 loose ends closed: silent test root cause, Lune green, checker on RR_Half labels, 3D tear critic, sounds uploaded | derived | L1 | planned | T4-T6 done; critique-splits-v2 scored |

## Decisions and assumptions (defaults; say if wrong)
A1 70% loses C2's rear half (v1 mid-carriage break). 30% loses C1's rear half and everything behind it.
A2 One hit past several thresholds plays only the deepest stage (mechanic review MR-Q5; P8's staggered replay is the
   alternative).
A3 Flings are cosmetic:
   - no damage, no keep-on fee, and the held item stays in hand
   - at 70%/30%, players are back on the train within 4 s of the snap
   - at 0%, they stay ragdolled until results
   - roofed riders go "through the roof": no train collision for 0.5 s, plus an up-raycast and a Y floor
A4 Riders on a lost section are flung off at the snap; they do not ride the wreck away.
A5 The 0% timeline is one merged version (P5 + P7, fixed by P9):
   1. inhale -0.2 s
   2. one chain pop per live chunk, rear to front, 0.3 s apart
   3. hero blast at the heart (Coal: boiler, Diesel: fuel tank), with hit-stop 150 ms
   4. the wide shot by +0.15 s, with slow-mo only on fx and scripted chunks (<= 0.5 s)
   5. YOU'RE FIRED at +3 s; results at about +5 s
   The world scroll brakes to a stop. Joel's round flow waits for SequenceDone (timeout 8 s).
A6 Joel's Diesel split is kept and mapped into v2 (profile presplit, or external if it moves parts itself). v2 adds fx,
   sound and fling on top.
A7 Split, explosion and fling audio moves to a new Audio API bus, with a Config switch back to legacy Sound. The game's
   other audio is untouched.
A8 Canon updates are recorded as Joel's decisions once he confirms (bible add-fact / decide):
   - integrity is the breakdowns' consequence meter (D-003 note)
   - 0% is a hard fail, train_explosion: same results screen, banked fare kept
   - flings are exempt from keep-on
   - passengers lost in a split leave the count
A9 Bars: av 8 (aim 9) · sound 9 + listening sign-off · 3D tear 8 · security gate PASS · perf within budgets.
A10 Phone first: OQ-029 budgets, Reduce Motion (GuiService.ReducedMotionEnabled), flash <= 3/s at peak 0.35.
A11 There are no Explosion instances anywhere: they kill Humanoids, have no falloff and reach at most 100 of the 165 studs.

Q1 Alpha scope: canon has the alpha in the week of 12 Oct, steam only (D-015), and split v2 cannot be ready by then.
   Default: v2 is built after the alpha. The alpha ships with splits behind Config.Enabled=false and a safe 0% path
   (the existing boiler-fail fx, YOU'RE FIRED and results).
Q2 Sound sources: "best ever" needs recorded material, and this session cannot download it. Default: you pull ~80 WAVs
   from the free Sonniss GDC bundles (list in SOURCING.md, written in session 3) into the private repo; Kenney CC0 comes
   via GitHub; low end, whooshes and sweeteners are synthesised here; $0. A paid pack only if listening round 1 fails on
   glass or tearing.
Q3 Proposed extras (pick any):
   a. warning build-up before each split and before 0% (creaks, sparks, crack line, no alarm). The mechanic review calls
      this needed so a hard fail is fair.
   b. cinematic wide plus a short slow-mo at 0%
   c. flying props (they share the 8-debris cap)
   d. auto screenshot + Share on the results screen (after the alpha)
   e. a secondary explosion when a wreck lands
   f. a runaway wheelset after the 0% blast
   Default: a, b, c, e yes; d after the alpha; f no.

## Spec (build source: the design files; the stage machine and payload are in design/systems.md section 2)
- Stage machine per train: Intact -> S70 -> S30 -> Destroyed, stored in the attribute RR_SplitStage; each stage fires
  once; reset = a fresh clone (Reset() cleans up).
- Bridge: TrainIntegrityBridge is the only file touching Joel's integrity API (attribute or callback; I1 decides).
- Profiles: TrainSplitConfig.Trains[profile] with breaks.mode tear | presplit | external | plane, stages 70/30/0,
  chunks (cap 6 phone / 8 PC, from the live bounding box at 0%), flavour, heart, return points.
- Remote: one server-to-client RR_TrainSplitFX v=2 {train, stage, seed, t0, lost, chunks, flavour, fling}.
- Beat sheets: design/vfx-animation.md section 2, with A5's 0% timeline. Sound map: design/sound.md section 2.
  Fling numbers: design/clip-gameover.md section 2, with A3/A4 and the P9 ceiling fix.
- Preview frames: roof3p_back, door1p_back, clip cam and phone 844x390, at 24 fps from -1 to +6 s (0%: -3 to +8).

## Acceptance
- av (critique-av-v2, one critic): F1-F6 >= 8, motion M1-M4 >= 8, feel G1-G6 >= 8, overall = lowest, aim 9. Every
  flipbook's plain fallback reaches 8 alone. Budgets PASS per event (design/vfx-animation.md section 5).
- sound (critique-sound-v2): soundsmith validate --strict, analyze 0 FAIL, validate --release PASS; S1-S6 >= 9; the
  8 "best ever" checks (design/sound.md section 1); listening round 2 passes; "SOUND v2 OK".
- 3D tear (critique-splits-v2): A1-A7 >= 8 on the Coal tear with live geometry (v1 never scored).
- Systems: Lune 0 FAIL, including the 8 new suites; Diagnose PASS and Bench.run("all") on Coal and Diesel; multiplayer
  checks (design/systems.md section 4); MicroProfiler within budgets on Joel's phone.
- Fling: solo and 2-client Team Test; no ceiling bonk; no void death; keep-on skipped; Reduce Motion honoured;
  "FLING OK".
- Security: guard scan 0 high/critical, independent reviewer verdict, fuzz kit run, gate PASS (or HOLD on owner items
  only).
- Release: rr-release-train gate GO before any publish; Joel confirms.

## Needs owner / placeholders
- Make JoelC077/claude private before uploading the place or sound packs: it is public now.
- Answer Q1-Q3; the exports E1-E7 go into intake/ (design/systems.md section 1); the 4 E7 answers.
- Optional: the env setup script line (audio tools), a Studio MCP for live Studio sessions.
- Session 3: Sonniss subset; upload 4 flipbooks + ~16 sound assets; paste ids.
- Sessions 5-6: Studio benches, 2 listening rounds, phone perf, multiplayer test, release approval.
- OQ drafts (dry-run only, nothing written to canon): OQ-TBD-integrity-d003, -zero-fail, -fling-keepon,
  -split-passengers, -v2-alpha.

## Next action
Owner: the "Before session 1" checklist in ROADMAP.md. Then session 1: spawn T2 (tasks/T2.md) on M/intake/, plus T4
(tasks/T4.md) in parallel.
