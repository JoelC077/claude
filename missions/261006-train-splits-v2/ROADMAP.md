# Train Split v2 roadmap
Planned 6 Oct 2026 by JARVIS (mission `261006-train-splits-v2`), then stress-tested by 3 independent reviewers (`review/`).
Nothing in your game has changed yet: this is the plan. It lives on branch **`claude/zealous-newton-h08ds8`** of
`JoelC077/claude`.

## In one minute
v2 turns your integrity system into three set pieces:
- **70%**: carriage 2 tears in half. The rear half explodes off, topples and falls behind, and anyone on it gets
  **flung**.
- **30%**: carriage 1 tears. Everything behind it goes, with a bigger blast.
- **0%**: a chain of explosions runs from the back of the train to the front and ends in one huge blast at the boiler
  (coal) or the fuel tank (diesel). The whole crew is launched, the camera cuts to a wide shot, YOU'RE FIRED lands and
  results follow.

It works on the Coal train, your Diesel and future trains: each train gets one config block, with no hand placement.

**You see it before the big spend:**
1. grey-box animatics with sound (session 2)
2. 3 style frames to pick from (session 3)
3. a quick Studio test of the fling, one effect and one sound on your phone (session 3)
4. your first listen to the hero sounds (session 4)

**Cost (estimates):**
- Build: about **3.5M tokens** over 7 sessions. v1 was about 2.5M.
- This planning turn already used about **1.9M**.
- A lean path is about 3.0M (see "Cost").
- Your time: about **7.5 hours** across the sessions, or 2-3 hours more if you take the Sonniss sound route (Q2 B).

## Before the alpha (only if your alpha is the week of 12 Oct; answer Q1 by 9 Oct)
- Make 0% end the run with your **existing** boiler-fail game over (effect, YOU'RE FIRED, results), firing once.
- If your current split hasn't worked in a playtest, switch it off for the alpha (`Config.Enabled = false` in
  TrainSplitConfig).
- Want me to do it? Send your integrity and round-flow scripts and say `alpha fix` (about 20k tokens).

## Before session 1: your checklist (4 things, plus 2 optional)
1. **Make the repo private.** `JoelC077/claude` is **public** right now, so anyone can read the v1 kit and these
   plans. Go to GitHub, then the repo's Settings > General > Danger Zone > Change visibility > Private. Do this before
   you upload your place.
2. **Answer the 3 questions below.** A reply like `Q1 yes · Q2 A · Q3 a b c e` is enough, or `go` to take all the
   defaults.
3. **Export from Studio**, on a copy of the place:
   - File > Save to File As > `.rbxlx`, zipped if it's over 25 MB.
   - Easiest: attach it in this chat.
   - Or on GitHub: switch the branch dropdown to `claude/zealous-newton-h08ds8` first, then Add file > Upload files
     into `missions/261006-train-splits-v2/intake/`.
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
5. *Optional:* keep the audio and video tools between cloud sessions. In the cloud environment menu (session title
   bar), choose Edit > Setup script and add:
   `pip install pyloudnorm soundfile pedalboard librosa scipy zstandard imageio-ffmpeg`
6. *Optional power-up:* run the Studio sessions from Claude Code on your PC with Roblox's Studio MCP connected. Then I
   can run the test bench in Studio myself. This needs your PC on.

**Where to start session 1.** Simplest: reply in **this chat**, which is already on the right branch. From a new
session, paste this:
> Resume JARVIS mission 261006-train-splits-v2, session 1. Use branch claude/zealous-newton-h08ds8 (it has
> missions/261006-train-splits-v2). Read ROADMAP.md and mission.md. My answers: Q1 … · Q2 … · Q3 … · (a) … (b) … (c) …
> (d) …. My export is attached / in intake/.

## The 3 questions (defaults in brackets)
- **Q1 Alpha (answer by 9 Oct).** Canon has the alpha in the week of 12 Oct, steam only. Is that still the plan?
  [Yes. v2 lands after the alpha, and the alpha gets the "Before the alpha" fix above.]
- **Q2 Sound sources.** "Best sounds ever" needs real recordings layered with synthesis, and this cloud can't reach
  the sound sites. Options:
  - **A:** let me fetch free CC0 sounds myself. You add `freesound.org` and `cdn.freesound.org` under the environment's
    Network access > Custom > Allowed domains, which takes 2 minutes. Whether Freesound also wants a free API key is
    unconfirmed; I'll tell you in session 3.
  - **B:** pro recordings, free. You download the Sonniss GDC bundles (big downloads), pick about 80 files from my
    search list (2-3 h) and share them with me via Google Drive.
  - **C:** a paid pack (BOOM Library, Pro Sound Effects), or commissioning a sound designer for the 3 hero sounds.
  [A, plus free CC0 packs I can already get and my own synthesis. Your first listen (round 0) decides whether we add B,
  and only then C.]
- **Q3 Clip extras.** Pick any:
  - a) warning build-up before each split and before 0% (creaks, sparks, a glowing crack line, no alarm). The mechanic
    review says a game over needs a visible last chance to feel fair.
  - b) a short slow-mo or freeze beat inside the 0% wide shot
  - c) flying props (coal lumps, luggage, sandwiches)
  - d) an auto screenshot and a Share button on the results screen
  - e) a second explosion when a wreck lands (your earlier "more explosions for comedy")
  - f) a runaway wheelset after the 0% blast
  [a b c e now; d later; f no]

## Sessions
"Mode" is the effort to pick when you start the session. JARVIS gives the hardest tasks (server core, fling, hero
sounds, 0% explosion) extra effort itself where it can. Builds and critic loops run with your laptop closed; a session
pauses where "you do" needs you.

| # | Session | You do (time) | est. tokens · mode |
|---|---|---|---|
| 1 | **Kickoff + sync** | the checklist; a 30 min Studio smoke test; read and OK the contract (5 min) | 0.2M · high |
| 2 | **Core systems** | create a private test place; a 45 min Studio run; watch the animatics | 0.6M · max |
| 3 | **Look + fling** | pick a style; upload 4 effect textures; a 30 min Studio spike | 0.85M · high |
| 4 | **Sound + 0% explosion** | listening round 0 (25 min, offline on your phone and headphones) | 0.7M · high |
| 5 | **Previews + critics** | watch the clips with sound and say what you hate (15 min) | 0.75M · high |
| 6 | **Your tests** | upload about 16 sounds; publish to the test place; about 2.5 h of tests | 0.3M · high |
| 7 | **Ship** | fuzz kit and grief test (about 35 min); approve the release | 0.15M · high, optional ultracode review about 0.4M |

**What each session builds** (plain words in brackets)
1. **Kickoff + sync.**
   - Read your export and write the contract: how v2 plugs into your code.
   - Get the offline tests green again: v1's are 91 pass / 52 fail.
   - **Diagnostics first:** every script prints numbered start-up steps, and a `Diagnose(train)` command plus a
     server-only test bench mean nothing fails silently again, the way v1's test split did.
   - An install kit for your Studio test.
2. **Core systems.**
   - Per-train profiles: Coal tear, your Diesel split mapped in, and a generic fallback.
   - Setup v2: break markers, any number of carriages, explosion chunks.
   - The stage machine (the logic that fires 70 then 30 then 0, each once; a big hit plays only the deepest stage).
   - 5 small patches to your own scripts (see Defaults).
   - Client-side motion maths.
   - Grey-box animatics with placeholder sound, so you OK the timing before any effects work.
3. **Look + fling.**
   - 3 style frames, and you pick one.
   - VFX pack v2: a layered hero burst (flash, a fireball of at least 30 studs, a soot column, a shock ring, glass,
     debris). It has 4 flipbooks (animated texture sheets) made in Blender, each with a plain fallback for weak phones,
     plus coal and diesel flavours.
   - Camera and feel: hit-stop, shake by distance, phone haptics, Reduce Motion.
   - The sound pipeline.
   - The fling system.
   - Ends with a **Studio spike** in your private test place, which checks the riskiest unknowns before we build on
     them: does everyone see the ragdoll, does the new audio play on your phone, does a flipbook load.
4. **Sound + 0% explosion.**
   - Hero sounds first: the 3 booms, the final blast, chain pops, tearing and glass. **You listen (round 0)** and say
     keep, louder, quieter or replace. Then the rest.
   - The effect timeline player.
   - The new Audio API sound bus with an in-Studio sound lab for blind A/B listening.
   - The full-train explosion.
5. **Previews + critics.**
   - Clips with sound of all 3 events from 6 cameras (roof, door, inside, forward-facing, clip camera, phone).
   - Independent critics: effects + motion + camera (bar 8, aim 9), sound, and the 3D tear (v1 never scored it).
6. **Your tests.**
   - Kit v2 (`.rbxmx`), published only to your **private test place**.
   - You run: the bench on both trains, a 2-player fling test, listening rounds 1 and 2 (phone speaker and
     headphones), screen recordings, MicroProfiler on your phone, a 3-client test.
   - A fresh critic scores your **real** recordings.
   - Done when you type `SOUND v2 OK` and `FLING OK`.
7. **Ship.**
   - Security gate: scan, an independent reviewer, the fuzz kit (a script you run in Studio), a 2-client grief test.
   - The release gate. Nothing goes to your live game without your typed go.
   - Debrief, and JARVIS skill upgrades from what we learned.

## The fling (your "players getting flung")
- The **server** picks who is flung, from where they stand: on the lost section means a full launch; near the break
  means a small knock. Each player's own device does the launch, because Roblox gives every player physics control of
  their own character. The ragdoll is switched on by the server, so everyone sees it.
- This system gives no player a new way to fling another. Generic exploiters are a separate problem; the security gate
  tests for them.
- Flings are **funny, never punishing**: no damage, no keep-on fee, you keep the item in your hand, and you're back on
  the train within about 4 s. At 0% everyone stays ragdolled until results.
- Riders under a roof go **through the roof** with a puff of debris. The fling also checks tunnels and bridges and puts
  you back before any fall into the void.
- Reduce Motion keeps the fling but drops shake, slow-mo and spin.

**Clip moments.** MVP: the fling, the 0% wave launch and the wide shot, plus whichever Q3 extras you pick. Later: a
"23.5 m!" flight callout and a "Most Flung" award. Parked: video capture (Roblox beta, 30 s max, must start before the
moment), landing tags, slow-mo at 70/30, hats popping off, flung NPC passengers.

## Sound: the honest path to "best ever"
- v1's 6 sounds were synthesised placeholders. Nobody has heard them and they were never uploaded. v2 replaces every
  one.
- Each hero sound gets 4+ layers (the crack, the body, a phone-safe punch, the tail), 3+ variations so it never
  repeats, and close, mid and far versions. The booms grow from 70 to 30 to 0 in tail length, depth and width.
- **I can't hear**, so my measurements and the sound critic only filter. **You decide**:
  - round 0 on plain files (session 4, before anything is uploaded)
  - rounds 1 and 2 in game (session 6)
  "Best ever" passes when you say so.

## Defaults I've assumed (say if wrong)
- 70% loses carriage 2's rear half; 30% loses carriage 1's rear half and everything behind it (the v1 break points).
- One huge hit that skips past several stages plays only the deepest one.
- Riders on a lost section are flung off at the snap.
- Your Diesel's split is kept and mapped into v2. v2 adds the effects, sound and fling on top.
- **5 small changes in your own scripts.** I write them as patches with steps:
  - your round flow waits for v2's "explosion done" signal (about 4.5 s after 0% starts; at most 6.5 s)
  - the keep-on fee skips flung players
  - the world scroll brakes at 0%
  - your events skip carriages that are gone
  - the run-end reason gets "train_explosion"
- The new sounds use Roblox's new Audio API, with a switch back to the old system. The rest of your game's audio is
  untouched, apart from a short duck before the big boom.
- **Canon: your decisions to record, once you confirm.**
  - Integrity is the breakdowns' consequence meter. This clashes with canon D-003, which cut "integrity".
  - 0% is a hard fail: the same results screen, and banked fare is kept.
  - Flings skip the keep-on fee.
  - Passengers lost in a split leave the count.
  - New sound licence classes: Sonniss, and my synthesis.
- **Phone first:**
  - Everything stays inside the canon phone effects budget (800 particles at peak, 8 debris pieces), with a cap on how
    much of the screen smoke covers.
  - No Roblox Explosion objects: they kill players and reach only 100 of the train's 165 studs.

## Cloud with your laptop closed?
**Yes.** This chat runs on Anthropic's cloud, not your laptop. This planning ran with your laptop closed.
- I only work when there's something to do: your message, a task already running, or a scheduled reminder. I don't
  start new sessions on my own, so you kick each one off from the Claude app or claude.ai/code (your phone works).
- Builds and critic loops run without you. A session pauses at its "you do" steps.
- Everything is pushed to GitHub as it goes, so nothing is lost if the cloud machine is recycled.
- The Studio MCP option is the exception: it needs your PC on.

## max or ultracode?
**Mostly high. Use max for session 2. Use ultracode at most once more.**
- **Effort (high/max)** is how hard each step thinks. Max costs more on every step, so save it for session 2: the core
  logic everything else sits on.
- **ultracode** fans work out to many extra agents and checkers. JARVIS already runs parallel builders and independent
  critics, so ultracode on build sessions would multiply your token bill for little gain.
- It earned its cost on this planning turn: the reviewers caught 5 plan-breaking problems before you saw it. It's worth
  one more run at the end, a final bug and exploit hunt across all v2 code (about 0.4M), if you have limit to spare.

## Cost
| | tokens (est.) |
|---|---|
| this planning turn (done) | about 1.9M |
| v2 build, sessions 1-7 | about 3.5M (plan.py's role-based figure: 2.6M, band 1.9-3.3M) |
| lean path | about 3.0M: skip Q3 c and e, the 3D tear critic, the analytics hooks, and one sound critic pass |
| optional final ultracode review | about 0.4M |

Spread it over a few weekly limits. Each session ends pushed, so pausing between sessions is free.

## Risks and how the plan handles them
| risk | handling |
|---|---|
| I haven't seen your new code | Session 1 reads your export before any integration code |
| No Studio in the cloud; v1 shipped untested | Diagnostics first, an early Studio spike, your test sessions, and a final critic on real recordings |
| I can't hear | Your listening rounds 0 and 2 are the gate |
| Phone performance is unmeasured | Canon budgets, quality tiers, a smoke-coverage cap, and MicroProfiler in your test place |
| Fling physics run on players' devices | The server picks targets and caps; the spike checks it early; a grief test before release |
| Roblox moderation can delay uploads | Textures go up in session 3; every flipbook has a plain fallback |
| Huge places or slow phones lose streamed parts | Train models stream as one unit; the multiplayer test includes a far player |
| Canon clashes | Your decisions get recorded in session 1 |
| Public repo | Make it private before uploading anything |

## Files
- `ROADMAP.md`: this page.
- `mission.md`: the requirements (every line of your message), defaults, overrides O1-O12 and the acceptance gates.
- `plan.json`: 49 tasks with sessions and owner steps.
- `tasks/`: ready-to-run orders for session 1 (T2, T4, T5).
- `refs/`:
  - `v1-kit.facts.md`: what v1 is and what is broken.
  - `canon-skills.facts.md`: canon, and what each JARVIS skill can do.
  - `roblox-vfx-physics.facts.md` and `roblox-audio.facts.md`: engine facts read from Roblox's docs repo, Oct 2026.
- `design/`:
  - `vfx-animation.md`, `sound.md`, `clip-gameover.md`, `systems.md`
  - `mechanic-review.md`: the independent verdicts
- `review/`: the 3 adversarial reviews of this plan, all applied.
