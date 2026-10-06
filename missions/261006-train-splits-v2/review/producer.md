# Producer review: train splits v2 roadmap (owner-fit lens)
Reviewer: independent, did not write the plan. 2026-10-06. **Verdict: fix-then-ship.** 2 blockers, 8 major, 2 minor.
Coverage: all of L1-L16 are mapped in mission.md, but L15 is missing from the page Joel reads.

## Blockers
**P1. The checklist and the "next session picks up from the files" claim break on branches.** Everything is on
`claude/zealous-newton-h08ds8`. The default branch (`claude/gracious-goldberg-crtklz`) has neither
`missions/260929-train-splits` nor `missions/261006-train-splits-v2`. A GitHub web upload to ".../intake/" lands on the
default branch, where the folder doesn't exist. A new cloud session starts there and sees no plan.
*Fix:* add step 0 to the ROADMAP checklist: "open the PR for this branch and merge it", or name the branch to pick in
GitHub's branch dropdown before uploading. Have every session push to one fixed branch. Add a paste-ready session-1
opening prompt that holds the Q1-Q3 and (a)-(d) answers; T1 expects clarify-1.raw but never says where Joel types them.

**P2. Token cost is understated and inconsistent.** ROADMAP says "about 3M", but its own session column adds up to 3.45M.
progress.log says "est 2.3M (band 1.7-2.9M; bottom-up ~3.3M)". The planning turn already used about 1.38M
(state.json `tokens`), before reviews and fixes, and Joel isn't told. v1 at about 2.5M used about 97% of a week, so the
total is about 4.8M+, roughly two full weekly limits.
*Fix:* use one number everywhere: build 3.45M est. (band), planning about 1.4M already spent. Add a "lean path" line
(see P4 and P10) to ROADMAP "In one minute".

## Major
**P3. L15 ("run on the cloud while my laptop is closed") isn't answered in ROADMAP.** R15 says "answered in the
reply". *Fix:* add a 4-line section:
- Yes for the maker and critic work.
- Sessions pause at T6, T12, T35, T37 and the fuzz/grief tests for Studio.
- Joel must start each session himself.
- The Studio MCP option needs his PC on.

**P4. Joel's ears come last.** Listening round 1 is in session 6, after the 0.9M critic session. That includes a sound
critic held to bar 9 that "can't hear" (ROADMAP Sound). *Fix:*
- Add an owner task after T18: listen to the hero WAVs on his phone from GitHub. No Studio needed.
- Cut T28-T31 to soundsmith gates plus one critic pass, at bar 8.
- Spend the fix rounds on his notes.

**P5. No early visible win.** The first in-Studio look at real fx, sound and fling is T35, about 3M tokens in.
Sessions 1-2 give him diagnostics and placeholders. *Fix:* make T12, or a new T19b in session 3, a vertical slice: the
70% split with the v2 burst, one fling and a placeholder boom, checked in a 15-minute Studio look. ROADMAP session 3
"You do" adds "watch the preview GIFs and try the fling".

**P6. The phone tests need a published build, and no step covers it.** T35 runs the "listening round 1 in RR_SoundLab
(phone + headphones)" test, and T37 needs the MicroProfiler on his phone with "3 clients + phone". Studio doesn't run on
a phone, and systems.md §4 says "private test server". Meanwhile ROADMAP says "Nothing publishes without your typed go".
*Fix:* add owner task T34b: File > Publish to Roblox As > a **new private test place**, never the live game. Add it to
ROADMAP session 6 "You do".

**P7. Sound sourcing and owner time are underestimated.** Q2 has Joel pull about 80 WAVs from the Sonniss GDC bundles
(multi-GB archives; sizes unverified). He then uploads them through GitHub web, which allows 25 MB per file and 100 files
per commit, and that bloats every clone. None of this is in "roughly 5 hours". The re-tally comes to about 7-9 h.
Q2 also omits the 2-minute option in roblox-audio.facts.md:82: widen the network policy for freesound.org (unverified:
an API key may be needed).
*Fix:*
- Offer that option in Q2.
- Tell him to convert files to 48 kHz/16-bit and trim them before upload.
- Show owner time per session.

**P8. The alpha (Q1) is 6 days away and the defaults differ between files.** ROADMAP says "whatever split you have now
stays". mission.md says "splits behind Config.Enabled=false". No task, and no Joel action, wires 0% to the boiler-fail
effect (also raised as engineering E2). *Fix:* mark Q1 "answer by 9 Oct". Add a "Before the alpha (you)" box with the
one default and the 0% hookup steps.

**P9. The "Mode" column contradicts plan.json, and ROADMAP never says what it controls.**
- Session 1: "max", but T2-T5 are high.
- Session 3: "high", but T19 is max.
- Session 4: T22 at max isn't mentioned.
- Session 6: "max", but T33 is medium and T36 high.

Max on an orchestrator that is waiting on Studio output burns tokens. *Fix:* "Mode = the effort you start the session
with; JARVIS sets each task's effort." Set sessions 1 and 6 to high. Note the max tasks in sessions 3 and 4. Give the
session-7 ultracode review an est. token cost.

**P10. The Q3 "extras" aren't really optional, and the defaults add cost.**
- b (wide shot + slow-mo) is already baked into "In one minute" ("the camera cuts to a wide shot") and A5 step 4.
- f defaults to "no", yet the 0% beat sheet in vfx-animation.md has "one runaway wheelset rolls off".
- d is "after the alpha", but v2 lands after the alpha anyway, and T22 builds the Share hook.

*Fix:*
- Make the defaults a + b. Move c and e to "later".
- Gate the wheelset, land_boom and Share hook on the Q3 answer in T13, T18 and T22.
- Remove the wide shot from "In one minute" unless b is picked.

## Minor
**P11.** The checklist says "I need 4 things" but lists 6. Session 1 "You do" leaves out T3 "Joel OKs the contract".
Session 7 "run the fuzz kit" doesn't say what that is or how long it takes. The jargon in "What each session builds"
needs a gloss: stage machine, client router, seeded motion maths, beat runner, Audio API bus, flipbooks.
**P12.** T4 greens 52 failing v1 tests that T7-T9 then rewrite. Limit it to the suites whose code survives into v2
(tear geometry, shared maths).
