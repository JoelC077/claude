# Adversarial review: AV quality lens (AAA audio/VFX director)
Mission 261006-train-splits-v2 · reviewer did not write the plan · verdict: **fix-then-ship**

The bones are good: layered hero bursts, scripted seeded motion, perspective renders, an Audio API bus and an honest
"I can't hear". The problem is **the order of work**. The two things that make AV great (a human seeing and hearing it
together, early, on the real device) come last, after most of the tokens are spent on critics that can't hear and
only see a simulator.

## Findings (ranked)
| # | sev | where | problem | fix |
|---|---|---|---|---|
| 1 | blocker | plan T10-T12, T13, T23; ROADMAP S5 | No animatic or look lock before 310k of fx and 400k of sound. Joel's first picture-plus-sound check is Studio session 6. Session 5 shows him **silent** GIFs ("watch the GIFs and say what you hate") | New T12b (S2): grey-box animatic MP4s with S2 placeholder audio (imageio-ffmpeg is already in the env line). Joel OKs the timing. New T13a: 3 style frames (toon, semi-real, hybrid) on the train stand. Joel picks one before the full T13. T23 outputs MP4 with the rendered mix, not GIF |
| 2 | blocker | T17, T28-T37; ROADMAP Q2 | The first human ear arrives in session 6 (T35), after 4 sound-critic passes and an upload round. The paid-pack fallback ("if round 1 fails") lands in a 0.15M session. The commissioned-designer option (refs/roblox-audio.facts.md line 86) is never offered | New T17b "round 0" at the start of S4: Joel auditions the raw shortlist, then the hero renders, as WAV/MP4 on his phone and headphones. No upload, no Studio. Decide paid pack or commission there. Add "c) commission the 3 hero sounds" to ROADMAP Q2 |
| 3 | major | mission.md Acceptance and T31 vs sound.md §5.2 | Bars contradict: S1-S6 >= 9 vs "bar 8, target 9 on S1-S3". A deaf critic at 9 on everything can burn the 5-pass cap. The "best ever" ladder (+1 LU per step, final at -9 = boiler fail) makes 0% no bigger than a crisis sound | Measured critic: 8 on all, 9 on S1-S3. The 9 comes from the listening test. Define size by tail 2/3/6 s, sub extension, layer count, width and the preboom silence, not LU |
| 4 | major | sound.md §4; T16, T34 | The soundsmith licence gate has no origin for Sonniss free bundles (no receipt) or Claude production synth (placeholder, "never ship"). Roblox-licensed Creator Store audio cannot be downloaded and remixed offline. `validate --release` will fail at S6/S7 | T3: owner decision extending av.audio.licence (sonniss_gdc + licence PDF; claude_synth + recipe proof). rr-skill-smith patch before T18. Roblox-licensed audio only as runtime layers |
| 5 | major | T35, T37; ROADMAP S6 | "Phone speaker" listening and phone MicroProfiler need the place running on the phone. Studio/Team Test plays on the PC. A private test-place publish is not planned and clashes with "nothing publishes without your typed go" | Add an owner step: publish to a separate private test place (not the live game). Joel's go covers only that place. Add it to the S6 "You do" list |
| 6 | major | vfx §5 tiers; mission Acceptance | "Every flipbook's plain fallback reaches 8 alone" has no board and no critic row. How the client detects low-memory is unspecified. What an auto-off 8x8 sheet renders is unverified (it could be the whole atlas) | T12: Joel checks what auto-off renders. T13 done-when: fallback-only board per event. T24/T27: score an F-low row. Fallback picked by quality level in script |
| 7 | major | vfx §5 budgets | Counts particles, not fill-rate (facts: "large near-camera smoke is the phone killer"). At 0%, 780/800 leaves 2.5 % headroom and ignores live 70/30 torn-edge fire/smoke, the "dying train" loop, fling puffs and props. Roof riders sit inside a 30-stud fireball | Add a per-camera translucent-coverage metric (est. cap). Count carry-over emitters in the 0% row and kill them at the inhale. Near-camera fade via ZOffset/size. T37: MicroProfiler per event with 6 players |
| 8 | major | T23-T27 | av "final >= 8" is certified on fxsim approximations. Motion strips at 8 fixed times miss the 0.15 s anticipation, the overshoot near 1.5 s and the 0.3 s chain cadence | T35: Joel captures 3 events x 2 cams in Studio (PC + phone). The av final re-scores on those. Dense strips: every 2nd frame around each beat, plus T11 curve plots |
| 9 | major | mission A5.4; MR #3 | The merged slow-mo slows fx and chunks to 0.3x for <= 0.5 s while the flung crew, the subject of the shot, flies at full speed. That reads as lag, and it shows only 0.15 s of action | All clients start the same own-character slow at t0 (all bodies slow, which removes MR's objection), or use a hero-frame hold plus a camera push. Decide from the T12b animatic |
| 10 | major | sound.md §3 Latency; systems §2 | The 0.25 s lead makes the tear (t0-0.25) always late by one-way ping. There is no policy for packets after t0. "Within 1 frame" logs Play() calls, not device audio output latency | Lead >= 0.4 s (est.). Policy: drop pre-roll beats once past, never shift the boom. Owner phone check: a phone-camera slow-mo video of flash vs boom. Configurable audio pre-roll |
| 11 | major | ROADMAP Q2, S4 "You do", 5 h | "I'll list exactly which" WAVs is a promise the session can't keep (bundle contents unverified, shell blocked). Bundles are tens of GB. GitHub web upload caps files at 25 MB. The 5 h owner estimate omits all of this | Offer to allow-list sonniss.com in the env (context.md says the owner can) so the session fetches the files itself. Otherwise state est. 2-3 h, 48 kHz trims, <= 25 MB per file |
| 12 | minor | T23 cams; vfx §2 30% | All previews face the blast. The 30% interior "coach1p" cam is not in T23. Nobody judges what a player facing forward gets (sound, light, shake) | Add coach1p (30%) and a forward roof/cab cam to T23. Score F1 signal from it |

## Missing
- An AV lock step (animatic + style frame) and an owner round 0 before production.
- A real-engine critic pass. Every score today is on a simulator.
- A private test place for phone tests.
- A licence-gate decision for the planned sources.
- Fill-rate and carry-over in the phone budget.
- A late-packet policy.
