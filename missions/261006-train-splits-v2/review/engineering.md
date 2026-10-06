# Engineering review: train splits v2 plan (senior Roblox lens)
Reviewer: independent, did not write the plan. Date: 2026-10-06. **Verdict: fix-then-ship.** 2 blockers, 7 major, 3 minor.

## Blockers
**E1. The multi-cross rule contradicts itself, and the tests enforce the wrong one.** mission A2 and ROADMAP say "a big
hit plays only the deepest stage" (MR-Q5). But mission Spec names design/systems.md §2 as the build source, and §2 says
"all fire in order, `stagger_s` apart". §4's suite says "100→20 = 70 then 30 at +stagger", and T9's done_when ("the 8 new
Lune suites pass") locks that in. *Fix:* add to mission Spec "A2 overrides systems §2 multi-cross and §4 order+stagger".
Rewrite the suite as: 100→20 = S30 only, with the lostSet still including C2's rear half; 100→0 = Destroyed only. Drop
`stagger_s` from profiles and from T9's do.

**E2. The alpha default differs between files and nobody owns the alpha 0% path.** ROADMAP Q1 says "whatever split you
have now stays"; mission Q1 says "splits behind Config.Enabled=false". v1's test split never worked in Studio
(context.md). Integrity 0% "HASN'T BEEN WORKED IN" (L7). No plan.json task wires 0% → boiler-fail → YOU'RE FIRED →
results, and the alpha is 6 days away. *Fix:* use one default in both files: Config.Enabled=false. Add an owner task
T1b (session 0/1, before 12 Oct) for the alpha-safe 0% hookup, with a 5-line recipe, or state plainly in the ROADMAP
that it is Joel's job.

## Major
**E3. Changes to Joel's code have no task.** The contract needs these changes in his scripts:
- the round flow waits for `SequenceDone` and does not reset early;
- keep-on skips `RR_FlingUntil`;
- the scroll driver brakes;
- the event layer checks `IsSectionPresent`;
- the run_end reason gets `train_explosion`.

ROADMAP's line "one bridge file is the only thing that touches your integrity system" hides this work. *Fix:* add task
"Host patches" (session 2, deps T3): small diffs plus owner apply steps. Make T12 and T22 depend on it.

**E4. Who drives the wreck is undecided.** P5 §3a says "server writes 1 root CFrame per body, clients re-run the seeded
curve", and §5 and systems §4 budget "server CFrame writes ≤ 3/frame". If both write to the same server-owned anchored
part, replication snaps the client pose back (jitter). Anchored CFrame replication is also not interpolated, so it
stutters on phones. *Fix:* the client drives the motion from new attributes `RR_SplitSeed`/`RR_SplitT0`, which late
joiners also read. The server writes only the start and end poses and the despawn. Set the budget to 0 writes/frame and
add a Lune contract test.

**E5. StreamingEnabled is never inventoried.** It is missing from T2 §4, the contract and the MP checks. Instance refs in
the payload (`train`, `chunks`, `lost={part ids}`) arrive nil if not streamed. Client-local CFrames reset on
stream-out/in, and wrecks drift 700 studs. *Fix:*
- T2 records StreamingEnabled, the radii and ModelStreamingMode;
- Setup v2 sets the train to Atomic/Persistent;
- the payload carries names and attributes, never Instances, and lost parts are derived from RR_Half and the stage;
- the router does a bounded wait;
- add an MP check with a far-away client.

**E6. The riskiest engine unknowns are first tested in session 6 (T35).** These come after about 2.4M tokens of
sessions 3-5:
- AJU ragdoll seen by others: a client-side `IsKinematic` flip does not replicate (SetStateEnabled does not either,
  facts §C);
- velocity applied by the client after the server removes the SeatWeld;
- Audio API IsReady and phone cost (sound.md §3 "unverified").

*Fix:* add owner task T19b, a 20-min Studio spike at the end of session 3: a 2-client fling (server-set vs client-set
IsKinematic), one AudioPlayer played on a phone, and one flipbook. Make T20, T21 and T22 depend on it.

**E7. plan.json has dependency errors.**
- T22 is missing T10, T15 (wide shot, CG5), T20 (the client chunks play in the beat runner) and T21 (CG8 hooks). It
  runs in parallel with T20/T21 on the same client files.
- T19 is missing T10 (the fling rides `RR_TrainSplitFX`) and T15 (one camera owner).
- Nothing depends on T14 (flipbook ids) or T32 (3D tear, which has no fix loop), yet G8 gates on "3D A".
- The session-7 fuzz kit and grief test are owner steps inside a critic task.

*Fix:* add those deps. Add T32→fix→T33 and T14→T33. Make T40 depend on T32. Split out an owner task "T38o fuzz +
grief test", and flag T40 as owner.

**E8. Studio sessions 1-2 have no way to install the code.** T6 says "install the hotfix" and T12 says "Setup v2 on
templates", but the only packager is T33 in session 6 (systems I11 depended on the I10 kit). *Fix:* add "interim kit
rbxmx + INSTALL steps" to T5's and T10's done_when, or add exporter tasks before T6 and T12.

**E9. The 0% timeline and chunk count are inconsistent.**
- A5 / ROADMAP: results at about +5 s, 8 s timeout.
- systems §2: "SequenceDone (+8 s) or a 12 s timeout".
- P5: "+8 results".
- P7: +5 s after final_blast.

The reference point is never stated. With an 8-chunk PC cap, final_blast lands at about 2.8 s, so results come at
about 7.8 s, just under the 8 s timeout. Chunk caps per device ("6 phone / 8 PC") break "same seed = same picture" and
the server-timed fling per pop. *Fix:*
- one table in A5 with all times measured from `TrainDestroyed` t0;
- a fixed server chunk cap (≤ 5), with PC adding only cosmetic debris;
- SequenceDone at a fixed t0+X and the timeout at X+2;
- say who stamps YOU'RE FIRED.

## Minor
**E10.** The fling remote is described two ways: inside the broadcast payload (systems §2) or as its own `RR_Fling` to
the owner (P7). Pick one in T19. Also, ROADMAP "No player can fling another" overclaims: facts §B say an owning client
can fling others and collision groups can be bypassed. Reword it to "this system gives no new way to fling others".

**E11.** Cost and owner time are understated. The session column sums to 3.45M, not "about 3M". Session 6 (0.15M) also
holds T33 + T36. Sonniss GDC bundles are multi-GB downloads (est., unverified), not "about 80 WAVs", and raw WAVs in git
hit the 25 MB web limit and bloat the repo. Fix the totals. SOURCING.md should give the bundle, part and file, and the
raw files should go into Drive intake.

**E12.** Audio integration gaps:
- Forcing legacy "if an AudioPlayer is not IsReady at init" will trip before preload. Make it a timed check after
  preload.
- The preboom duck "all but D" needs Joel's ambient and music routing, but T2 does not inventory his audio. Add it to
  T2 §4.

## Missing
StreamingEnabled inventory · host-code patch task · alpha-safe 0% task · interim install kit · Studio spike before
session 4 · owner fuzz/grief task · 3D tear fix loop.
