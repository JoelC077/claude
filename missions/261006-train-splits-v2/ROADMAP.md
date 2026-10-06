# Train Split v2 roadmap
Planned 6 Oct 2026 by JARVIS (mission `261006-train-splits-v2`). Nothing in your game has changed yet: this is the plan.
Machine plan: `plan.json` (42 tasks). Contract: `mission.md`. Designs: `design/`. Research: `refs/`.

## In one minute
v2 turns your integrity system into three set pieces:
- **70%**: carriage 2 tears in half. The rear half explodes off, topples and falls behind, and anyone on it gets
  **flung**.
- **30%**: carriage 1 tears. Everything behind it goes, with a bigger blast.
- **0%**: a chain of explosions runs from the back of the train to the front and ends in one huge blast at the boiler
  (coal) or the fuel tank (diesel). The whole crew is launched, the camera cuts to a wide shot, YOU'RE FIRED lands at
  +3 s and results show at about +5 s.

It works on the Coal train, your Diesel and future trains: each train gets one config block, with no hand placement.

**Cost:** 7 sessions, about **3M tokens** (estimate; v1 was about 2.5M). Your time is roughly 5 hours across all
sessions, mostly Studio tests and two listening rounds.

**Before anything else, I need 4 things from you** (next section). Then session 1 can start.

## Before session 1: your checklist
1. **Make the repo private.** `JoelC077/claude` is **public** right now, so anyone can read the v1 kit and these
   plans. Go to GitHub, then the repo's Settings > General > Danger Zone > Change visibility > Private. Do this before
   you upload your place or any sound packs.
2. **Answer the 3 questions below.** A reply like `Q1 yes · Q2 yes · Q3 a b c e` is enough, or `go` to take all the
   defaults.
3. **Export from Studio**, on a copy of the place:
   - File > Save to File As > `.rbxlx`.
   - Upload it to `missions/261006-train-splits-v2/intake/` on GitHub (Add file > Upload files). Zip it first if it is
     over 25 MB.
   - If the whole place can't go up, right-click > Save to File (`.rbxmx`) each of these instead:
     - the integrity system
     - your universal event layer and the train select/spawn code
     - the Diesel train with its split
     - the TrainSplit scripts as installed now
     - the round/game-over flow and the world-scroll driver
4. **Type 4 answers:**
   - (a) did `[TrainSplitDemo] ready` ever print in Output?
   - (b) were you in the Client or the Server view when you set `RR_TestBreak`?
   - (c) can integrity go back up (repairs)?
   - (d) does each run clone a fresh train from a template?
5. *Optional:* make the cloud keep the audio tools between sessions. In the cloud environment menu (session title bar),
   choose Edit > Setup script and add:
   `pip install pyloudnorm soundfile pedalboard librosa scipy zstandard imageio-ffmpeg`
6. *Optional power-up:* run the Studio sessions from Claude Code on your PC with Roblox's Studio MCP connected. Then I
   can run the test bench in Studio myself instead of you pasting Output.

## The 3 questions (defaults in brackets)
- **Q1 Alpha.** Canon has the alpha in the week of 12 Oct, steam only. Is that still the plan? [Yes. We start v2 now,
  but it lands after the alpha. For the alpha, whatever split you have now stays. Game over at 0% uses the existing
  boiler-fail effect, then YOU'RE FIRED, then results, until v2's explosion is ready.]
- **Q2 Sound sources.** "Best sounds ever" needs real recordings layered with synthesis. This cloud can't download them
  (network policy blocks the sound sites). [You download about 80 WAVs from the free Sonniss GDC bundles; I'll list
  exactly which in session 3. They go into the private repo. Budget $0. A paid pack (BOOM Library, Pro Sound Effects)
  only if your listening test fails on glass or metal tearing.]
- **Q3 Extras I'm proposing.** Pick any:
  - a) warning build-up before each split and before 0% (creaks, sparks, a glowing crack line, no alarm). The
    mechanic review says a game over needs a visible last chance to feel fair.
  - b) a cinematic wide shot plus half a second of slow-mo at 0%
  - c) flying props (coal lumps, luggage, sandwiches)
  - d) an auto screenshot and a Share button on the results screen
  - e) a second explosion when a wreck lands
  - f) a runaway wheelset rolling off after the 0% blast
  [a b c e now; d after the alpha; f no]

## Sessions
"Mode" is the effort level to pick when you start that session. Use ultracode only where it says so.

| # | Session | You do | est. tokens · mode |
|---|---|---|---|
| 1 | **Kickoff + sync** | the checklist above, then a 30 min Studio smoke test | 0.2M · max |
| 2 | **Core systems** | a 30 min Studio bench run on both trains | 0.45M · max |
| 3 | **Look + fling** | upload 4 effect textures | 0.8M · high |
| 4 | **Sound + 0% explosion** | before it: download about 80 WAVs | 0.7M · high (max for the hero sounds) |
| 5 | **Previews + critics** | watch the GIFs and say what you hate | 0.9M · high |
| 6 | **Your tests** | upload about 16 sounds; about 2 h in Studio | 0.15M · max |
| 7 | **Ship** | run the fuzz kit; approve the release | 0.25M · high, plus one ultracode review if you have limit spare |

Spread them over 2-3 weeks of your weekly limit. Each session ends with everything committed and pushed, so a new
session can always pick up from the files.

**What each session builds**
1. **Kickoff + sync.**
   - Read your export.
   - Write the integration contract: one bridge file is the only thing that touches your integrity system.
   - Record your canon decisions.
   - Get the offline tests green: v1's are 91 pass / 52 fail.
   - Diagnostics first: every v2 script prints numbered boot steps, and a `Diagnose(train)` plus a server-only test
     bench mean nothing fails silently again, the way v1's test split did.
2. **Core systems.**
   - Per-train profiles: Coal tear, your Diesel split mapped in, and a generic fallback.
   - Setup v2: break markers, any number of carriages, explosion chunks.
   - The stage machine: Intact → 70 → 30 → 0, each stage fires once, a big hit plays only the deepest stage, and Reset
     works.
   - The hand-off to your game over, the client router, and the seeded motion maths.
3. **Look + fling.**
   - VFX pack v2: a layered hero burst (flash, a fireball of at least 30 studs, a soot column, a shock ring at floor
     level, glass, debris), 4 Blender-made flipbooks that each have a plain fallback, and coal and diesel flavours.
   - Camera and feel: hit-stop, shake by distance, haptics, Reduce Motion.
   - The sound pipeline.
   - The fling system (details below).
4. **Sound + 0% explosion.**
   - Hero sounds (the 3 booms, final blast, chain pops, tearing, glass), then the rest.
   - The client beat runner.
   - The new Audio API sound bus and an in-Studio `RR_SoundLab` for blind A/B listening.
   - The full-train explosion.
5. **Previews + critics.**
   - GIFs of all 3 events from the roof, a door, the clip camera and a phone frame, with the real effects. v1's GIFs
     used stand-ins.
   - Independent critic loops: effects + motion + camera (bar 8, aim 9), sound (bar 9), and the 3D tear (v1 never
     scored it).
6. **Your tests.**
   - Kit v2 as a `.rbxmx` with install, upgrade and rollback steps.
   - You run: the bench on both trains, a 2-player fling test, listening rounds 1 and 2 (phone speaker and headphones),
     MicroProfiler on your phone, a 3-client multiplayer test.
   - I fix from your notes.
   - Done when you type `SOUND v2 OK` and `FLING OK`.
7. **Ship.**
   - Security gate: scan, an independent reviewer, the fuzz kit, a 2-client grief test.
   - The release gate. Nothing publishes without your typed go.
   - Debrief, and JARVIS skill upgrades from what we learned.

## The fling (your "players getting flung")
- The **server** picks who is flung, from where they stand: on the lost section means a full launch; near the break
  means a small knock. Each player's **own client** does the ragdoll and the launch, because Roblox gives every player
  physics control of their own character. No player can fling another.
- Flings are **funny, never punishing**: no damage, no keep-on fee, you keep the item in your hand, and you're back on
  the train within about 4 s. At 0% everyone stays ragdolled until results.
- Riders under a roof go **through the roof** with a puff of debris. The fling also checks tunnels and bridges and puts
  you back before any fall into the void.
- Reduce Motion keeps the fling but drops shake, slow-mo and spin.

**Clip moments.** MVP: the fling, the 0% wave launch, plus whichever of Q3 b, c, d you pick. Later: a "23.5 m!" flight
callout and a "Most Flung" award on the Incident Report. Parked: video capture (Roblox beta, 30 s max, and it must start
before the moment), landing tags, slow-mo at 70/30, hats popping off, flung NPC passengers.

## Sound: the honest path to "best ever"
- v1's 6 sounds were synthesised placeholders. Nobody has heard them and they were never uploaded. v2 replaces every
  one.
- Each hero sound gets 4+ layers: the crack, the body, a phone-safe punch and the tail. It also gets 3+ variations so
  it never repeats, plus close, mid and far versions, and the booms get bigger from 70 to 30 to 0. Real recordings make
  the crack, tear and glass; synthesis adds the low end, whooshes and comedy sweeteners (boing, slide whistle). Most
  phones can't play deep bass, so the low end is shaped so the boom still lands on a phone speaker.
- **I can't hear.** Measurements and the sound critic only earn the real test, which is your blind A/B listening on
  your phone speaker and on headphones. "Best ever" passes when you say so.

## Defaults I've assumed (say if wrong)
- 70% loses carriage 2's rear half; 30% loses carriage 1's rear half and everything behind it (the v1 break points).
- Riders on a lost section are flung off at the snap; they don't ride the wreck away.
- Your Diesel's split is kept and mapped into v2. v2 adds the effects, sound and fling on top.
- Your round flow waits for v2's "explosion done" signal before results, for at most 8 s. The world scroll brakes to a
  stop at 0%.
- The new sounds use Roblox's new Audio API, with a switch back to the old system. The rest of your game's audio is
  untouched.
- **Canon: your decisions to record, once you confirm.**
  - Integrity is the breakdowns' consequence meter. This clashes with canon D-003, which cut "integrity".
  - 0% is a hard fail, "train_explosion": the same results screen, and banked fare is kept.
  - Flings are exempt from the keep-on fee.
  - Passengers lost in a split leave the count.
- **Phone first:**
  - Everything stays inside the canon phone effects budget (800 particles at peak, 8 debris pieces).
  - No Roblox Explosion objects: they kill players and reach only 100 of the train's 165 studs.
  - Flashes are capped, and Reduce Motion is respected.

## Risks and how the plan handles them
| risk | handling |
|---|---|
| I haven't seen your new code (Diesel, integrity, universal layer) | Session 1 reads your export before any integration code. Estimates after that are provisional |
| No Studio in the cloud; v1 shipped untested | Diagnostics first, plus 4 short Studio sessions from you. A Studio MCP would remove most of this |
| I can't hear | Your 2 listening rounds are the gate, not my scores |
| Phone performance is unmeasured | Canon budgets, quality tiers, and your MicroProfiler run in session 6 |
| Fling physics run on players' devices | Server-chosen targets and caps; an exploiter can only skip their own fling; a 2-player grief test |
| Roblox moderation can delay textures and sounds | Upload early (sessions 3 and 6); every flipbook has a plain fallback |
| Canon clashes (integrity, flings, fees, fail list) | Your decisions get recorded in session 1 |
| Public repo | Make it private before uploading anything |

## max or ultracode?
Mostly **max**. Use ultracode once, at the end.
- **max** (effort) means one agent thinking as hard as it can. It is best for integration, core logic and Studio
  debugging with you (sessions 1, 2 and 6, plus the hero sounds in 4), where one deep thinker beats many quick ones.
  **high** is enough for sessions 3, 5 and 7.
- **ultracode** fans the work out to many agents and adds independent checkers on top. JARVIS already runs parallel
  makers and independent critics, so ultracode on every session would roughly multiply your token bill for little
  gain. It earns its cost on wide jobs: this planning turn (research + 4 designs + reviews) and a final pre-release
  bug and exploit hunt across all v2 code (session 7), if you have limit to spare.

## Files
- `ROADMAP.md`: this page.
- `mission.md`: the requirements (every line of your message mapped), defaults and acceptance gates.
- `plan.json`: the task graph with sessions.
- `tasks/`: ready-to-run orders for session 1.
- `refs/`:
  - `v1-kit.facts.md`: what v1 is and what is broken.
  - `canon-skills.facts.md`: canon and what each JARVIS skill can do.
  - `roblox-vfx-physics.facts.md` and `roblox-audio.facts.md`: engine facts, read from Roblox's docs repo, Oct 2026.
- `design/`:
  - `vfx-animation.md`: beat sheets and budgets.
  - `sound.md`: the sound map and the "best ever" checks.
  - `clip-gameover.md`: fling numbers and clip moments.
  - `systems.md`: integration, tests and security.
  - `mechanic-review.md`: the independent verdicts.
- `review/`: the adversarial review of this roadmap.
