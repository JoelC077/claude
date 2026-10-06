# Mission 261006-train-splits-v2: shared brief (every planning agent reads this first)

Paths: M = /home/user/claude/missions/261006-train-splits-v2 · V1 = /home/user/claude/missions/260929-train-splits ·
SK = /root/.claude/skills/synced/80b8703d-5ce2-4cfa-8173-3f10e032ad2b_d09bd656-edae-46f7-90d5-de67eb3c3270

## What this turn is
PLANNING ONLY. Joel (owner, solo developer of the Roblox game Risky Rails) is away with his laptop closed. He asked JARVIS
(rr-mission-control) to plan the v2 roadmap of the train split system so the build can start when he is back. Nothing is
built or changed in his game this turn. Your output feeds the roadmap the orchestrator writes (M/ROADMAP.md, M/mission.md,
M/plan.json).

## Owner's words, 2026-10-06 (verbatim in M/prompt.raw, line ids in M/lines.md)
- L2 "I have since added a Diesel Train, which already has its split sorted."
- L3 "i have also integrated universal compatibility, so all events work regardless of the train selected."
- L4-L7 integrity system: split 1 (carriage 2) at 70% integrity · split 2 (carriage 1 and rest) at 30% ·
  full train explosion (game over) at 0% [HASN'T BEEN WORKED IN]
- L8-L10 "in V2, I want better VFX, better animation, and extremely good sounds. Like, literally the best sounds ever."
- L11 "work on the full train explosion, PLUS clipability (players getting flung, other funny things)"
- L14 "This is one of the most important systems in the game."

## The game (standing facts; canon lives in rr-bible, never guess numbers)
Risky Rails: Roblox co-op train game. Players ride a train that never moves; the world and terrain scroll past (in-run).
Phone landscape 844x390 is the primary device, PC second. Tone for this event: big but slapstick (owner decision
2026-09-29, v1 mission A6, overriding the OQ-028 default for this event). Units are studs.

## v1 (mission 260929-train-splits, delivered 2026-09-29/30)
CoalTrain, 2 carriages. An edit-time setup script (RR_TrainSplit_Setup) finds each carriage's break frame from its roof
union's size signature, CSG-cuts the ~10 unions per carriage that cross a 29-cell jagged tear (break_spec v2.3), and labels
every part in place with the attribute RR_Half. It no longer moves parts into folders, because that broke the game's
path-based scripts.
Runtime: ReplicatedStorage.Modules.TrainSplit, with the server script in ServerScriptService.Scripts.TrainSystems.
- TrainSplit.SplitAt(train, k): k=1 loses C1's rear half and all of C2; k=2 loses C2's rear half.
- Lost bodies brake from the train's Speed down to terrain speed and drift back. They topple onto their side (a scripted
  roll of about 97 deg with a bounce) and despawn at 700 studs or 30 s.
- A client LocalScript plays the explosion fx (rr-vfx-lighting presets), 6 synthesised sounds (rr-soundsmith) and
  camera shake. The RemoteEvent goes server to client only.
Status at hand-off:
- Setup ran OK on the live CoalTrain.
- The test split (RR_TestBreak attribute) did nothing in Studio and was never debugged.
- The offline Lune tests are out of date (live roof signature and in-place mode).
- The fx critic stood at 5/10 with its fixes unscored.
- The 3D critic and the security re-check are unfinished.
- The 6 wavs have not been uploaded yet.
Earlier v2 list: V1/NEXT.md.

## What changed since v1 that Claude has NOT seen
Joel's Diesel Train, his "universal compatibility" event layer and his integrity system exist only in his Studio place.
None of it is in this repo. Any plan must start by getting that code and model into the repo (an owner export) before
integrating.
The break order has also changed. v1 allowed either break first; now:
1. carriage 2 always splits first (70%);
2. then carriage 1 and the rest (30%);
3. then the whole train (0%).

## Environment (probed 2026-10-06)
Cloud container (claude.ai/code).
- No Roblox Studio and no Studio MCP.
- No live Blender. bpy 5.0.1 runs headless with Cycles on the CPU.
- Lune 0.10.5.
- Python 3.11 with numpy 1.26 and Pillow 12. No scipy, ffmpeg or sox. pip installs from PyPI work.
- The network policy blocks create.roblox.com, devforum.roblox.com, freesound.org and sonniss.com from the shell
  (CONNECT 403). The WebSearch and WebFetch tools may still work, because they do not go through the shell. The owner
  can widen the policy (environment settings, Custom allowed domains).

Skills (SK/<name>):
- rr-mission-control (JARVIS)
- rr-bible (canon: scripts/bible.py)
- rr-vfx-lighting, rr-soundsmith, rr-game-feel
- rr-exploit-guard, multiuse-critic, risky-rails-mechanic-reviewer
- rr-skill-smith, rr-release-train, rr-data-and-money

## Rules for every planning agent
- Plan, don't build. Write only your listed output file(s). Never modify anything under V1 or the skills.
- Joel's asks are CORE. Mark every owner-visible feature he did not ask for as PROPOSED; he decides.
- Take numbers from rr-bible or measured sources, never invent them. Mark estimates "est.". Mark Roblox API claims you
  could not verify as "unverified".
- Write for a planner: tables and bullets, no essays. Respect the length cap in your order.
