# P9 mechanic review: 0% game over, fling, clip moments (+ P5 fling/slow-mo/camera)
Checklist C1 new system · C2 verb reuse · C3 funny not punishing · C4 physical/loud · C5 scope · C6 where to log.
Canon via `bible.py get/search` 2026-10-06 (Cowork plan docs absent; rr-bible PLAN/MRS facts stand in).
P7 = design/clip-gameover.md, P5 = design/vfx-animation.md.

**Counts: 2 go · 11 go with changes · 5 park** (18 rows).

## Headline hits
- **C5 scope (biggest):** alpha departs the week of 12 Oct, steam-only (D-015, release.dates.alpha); sound + crisis fx
  are only a week-2 COULD (release.alpha.week2_could). Split v2 cannot ride the alpha. Only a safe 0% path can (MR-Q1).
- **C1 D-003:** the owner's integrity system matches the cut "integrity separate from breakdowns". 0% adds a fail state
  missing from gameplay.crisis.fail_states. Both need owner decisions before canon (OQ drafts below).
- **C3:** fling is funny only if it never costs anything: no keep-on fee (gameplay.train.keep_on = 5 coins), no Health,
  no lost tool, short loss of control.

## Verdicts
| # | idea | verdict | rule / canon behind it | changes required |
|---|---|---|---|---|
| G1 | 0% game-over sequence (P7 §1, §4) | go with changes | owner L7; fail_cinematic + clip_moments = 3 s moment; run.fail_screen (banked fare kept); C1 | Idempotent 0% handler (fires once, results open once). If one hit crosses several thresholds, run only the deepest stage (MR-Q5). By 0% only loco/tender (+C1 front?) remain, so chunks and the wide frame come from the *live* bounding box, not train_len 165. The cause line must differ from boiler_explosion (coal core = boiler would read as the pressure fail). Add `train_explosion` to fail_states and run_end only after the owner decides. |
| G2 | build-up below 10% (P7 §4, P5 meltdown rows) | go with changes | C3: a hard fail needs a visible last chance, else it feels arbitrary; ui.rules.exact_texts | Make it the default, not an extra: it is the anti-arbitrary signal. "SHE'S GONNA BLOW!" is not in gameplay.alerts, so it needs an owner-approved add-fact first. Alarm stays off (OQ-035 layering). |
| G3 | fling system incl. #1 ragdoll fling and knock (P7 §2) | go with changes | owner L11; pillars.physical_loud; D-002 "falling off is handled by the company"; never_trust_client | **Ceiling:** lost-section riders sit under an intact roof (floor 5, roof 14), and tunnels give only 4 studs above the roof (tech.units.stock_roof). A 70-90 vy fling bonks. Fix: the RR_Flung group does not collide with train parts for ~0.5 s ("through the roof" puff), plus an up-raycast that caps vy under tunnels/bridges (gameplay.train.low_bridge state). Return on the air cap **or** below a Y floor (viaduct drop) before any void death. Keep-on exempt while `RR_FlingUntil` is live (P7 Q1 → required). Held item stays in hand (MR-Q4). Loss of control ≤ 4 s from snap to return (est.). Spread the return points for up to 6 crew (gameplay.crew.max) on a loco-only train. |
| #2 | 0% wave launch | go with changes | clip_moments; crew.max 6 | Pop count from the live chunks (often 2-3, not 5). The final_blast must catch any grounded player (P7 has this; keep it). Seeded per event. |
| #3 | cinematic wide + slow-mo (P7 #3 + P5 0% "clip beat") | go with changes | av.feel.hitstop_local ≤ 150 ms; no global time scale (refs D) | P7 and P5 disagree. Adopt P5's: effect TimeScale + scripted chunks only, ≤ 0.5 s. **Drop P7's own-character ×0.35 counter-gravity hack**: other players' replicated bodies stay full speed, so one slowed body reads as a bug. Hit-stop 150 ms on the own camera, then cut to the wide. |
| #4 | flying props | go with changes | pillars.reuse_verbs (one asset pool); OQ-029 (8 debris) | Props come from the existing carry pool (coal lump, sandwich, wrench). They **share** P5's 8-debris cap and do not add to it. |
| #5 | flight callout "23.5 m!" | go (after alpha) | tech.units.stud_m 0.28; physical and loud | none (cosmetic, client) |
| #6 | "Most Flung" award | go with changes | results.incident_report: one silly award per player | Computed on the server from the seeded vector (CG1 maths), never from client landing positions. Needs Joel's report hook. |
| #7 | screenshot + Share | go with changes | results.blame already has a share prompt; refs D: no rule found on rewarding shares | Reuse the one results share prompt; no second button. Never reward a share. Fail quietly. After the alpha (3-5 testers need no growth loop). |
| #8 | video capture prompt | park (post-launch) | C4: a "record?" prompt at <10% is a menu at the climax; beta API | none now |
| #9 | comedic landing tags | park (polish after fling feel) | C5 | none |
| #10 | slow-mo snap at 70/30 | park (cut) | hitstop_local ≤ 150 ms; co-op keeps playing at 70/30 (P5: no forced camera) | none |
| #11 | hat pop | park (polish) | C5; local-only desync | none |
| #12 | NPC passengers flung | park until passengers ship | D-005; gameplay.crisis.coupling (proposed); release.alpha.week2_should "passengers (minimal)" | Decide passenger accounting first (MR-Q3). |
| V1 | P5: room for the fling (0.0-1.2) | go | client-only non-colliding chunks; tech.streaming.fx_client | none |
| V2 | P5 camera at 70/30 (hit-stop 100 ms, big shake, haptic, no forced cam) | go with changes | hitstop_local; flash_limit | One camera owner: a flung player's fling camera suppresses shake. Scale shake by distance (P7: far = light). |
| V3 | P5 camera at 0% (FOV -3/+6, pull-out, stamp +5, results +8) | go with changes | fail_cinematic 3 s | One timeline: final_blast → hit-stop → wide by +0.15 s → stamp at +3 → results ≈ +5 (P7). P5's +8 overruns the canon moment. |
| V4 | Reduce Motion (P5 0.4 s hold vs P7 static wide, half spin) | go with changes | av.feel.reduce_motion; OQ-032 A | Merge: static wide, 0.4 s hold, no shake/FOV/pull-out. The fling still happens with half spin; world-up camera. |

## Owner questions (default in brackets)
- MR-Q1 Split v2 in the alpha? [No. The alpha gets only a safe 0% path: existing boiler_fail fx + YOU'RE FIRED + results. v2 after the alpha.]
- MR-Q2 Is integrity a 5th crisis system? [No. It is the breakdowns system's consequence meter; D-003 stands with a note.]
- MR-Q3 Do passengers lost in a split count toward "all passengers dead"? [No. They leave the count and the fare drops.]
- MR-Q4 What happens to a held tool or item when flung? [It stays in hand.]
- MR-Q5 What if one hit crosses 70 and 30, or 30 and 0? [Play only the deepest stage, losing everything behind it.]
- MR-Q6 How do roofed riders get out? [Through the roof: no train collision for ~0.5 s, plus a roof puff.]
- I endorse P7 Q1-Q3 and Q9 as written. P7 Q8 (build-up) becomes required (G2).

## OQ drafts (`bible.py add-question --dry-run` only; nothing written; numbers provisional)
| slug | title | default |
|---|---|---|
| OQ-TBD-integrity-d003 | Integrity vs D-003: 5th crisis system or the breakdowns meter? | A: breakdowns meter, D-003 stands |
| OQ-TBD-zero-fail | Is the 0% integrity explosion a hard fail? | A: hard fail, same results, banked fare kept, reason `train_explosion` |
| OQ-TBD-fling-keepon | Flung players and the keep-on fee | A: exempt, returned free |
| OQ-TBD-split-passengers | Passengers lost in a split vs "all passengers dead" | A: they leave the count |
| OQ-TBD-v2-alpha | Split v2 scope against the alpha | A: safe 0% path only in alpha |
After answers: a D-002 note (cosmetic fling, company return) and the alert add-fact (G2).

## Where to log (C6)
rr-bible OQs/decisions → M/ROADMAP.md: alpha-safe 0% path · v2 core (G1-G3, #2-#4, V1-V4) · later (#5-#7) · parked (#8-#12).
