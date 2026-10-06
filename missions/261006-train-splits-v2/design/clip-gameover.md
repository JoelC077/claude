# P7 design: 0% full-train explosion (game over) + clipability
Mission 261006-train-splits-v2 · planning only · 2026-10-06 · sources: refs/context.md, v1-kit, canon-skills (P2),
roblox-vfx-physics (P3), design/sound.md (P6 cue ids). Numbers marked est. are design guesses for Studio tuning;
"unverified" = Roblox behaviour not confirmed. P5 owns the VFX beat sheet; times here are high level and P5 wins.
Owner asks: L7 (0% explosion), L11 (explosion + "players getting flung, other funny things"). All else PROPOSED.

## 1. Each event, three players
A = on the lost section · B = kept section, within ~25 studs (est.) of the break · C = far (loco cab / front).
Players stay alive throughout: flings never touch Health (no respawn timers, no death UI).

**70% (C2 lost) and 30% (C1 + rest lost)** — same shape; at 30% most of the crew is usually A.
| t (s) | A (lost section) | B (kept, near break) | C (far) |
|---|---|---|---|
| -3..0 PROPOSED | creak_warn groans, seam sparks/smoke at the next break; can walk forward to safety | same, louder | faint creak, Joel's integrity HUD |
| -0.25 | tear_70/30 rip under feet | rip, floor jolt | distant crack |
| 0 | boom; seat weld destroyed; **launched** up/back (§2), fling_whoosh, ragdoll | boom close; **knock**: short hop away from the gap, ragdoll 0.8 s | boom (2D body + far render), light shake |
| 0.1-1.5 | airborne, spinning; sees train recede and own carriage topple below; no control | on the floor, gets up ~1.5 s; sees the gap open and wreck topple (1.5/2.0 s) | can turn and run back to look |
| ~1.2-2.5 | lands: body_impact by speed, comic landing pose, ragdoll 1.0 s | normal control; open torn edge is a real drop (keep-on applies) | normal |
| ~3-4 | returned to the coach (poof, "back to work") — no fee (Q1) | normal | normal |
At 30% the "coach" for returns is whatever is left (loco/tender); return point comes from the train profile.

**0% (whole train)** — everyone is A. A = rearmost, B = mid, C = cab.
| t (s) | A | B | C |
|---|---|---|---|
| <10% PROPOSED | build-up (§4) everywhere | same | same; cab lamps flicker |
| -0.2 | preboom_suck: world goes near-silent | same | same |
| 0 | first chain_pop at the rear chunk; A launched by it | sees pop, braces | sees smoke at the rear |
| 0.3·k | pops walk forward one chunk per ~0.3 s (est.); each launches the players on its chunk | launched when its pop fires | |
| final (~1.0-1.6) | in the air | in the air | final_blast at the loco core; C launched highest |
| +0.1 → +3.0 | cut to cinematic wide, slow-mo ~1 s, everyone tumbling (§4) | same shot | same shot |
| +3.0 | lands in a heap, stays ragdolled; YOU'RE FIRED stamp + gameover_sting | same | same |
| ~+5 | results screen (Joel's flow) | | |

## 2. Fling system (CORE, L11)
**Who.** Server-only selection from geometry, never from client input:
| case | rule | strength |
|---|---|---|
| on a lost section at the snap | character root over a part labelled lost (RR_Half lost set) or within its box | full fling |
| kept side near the break | within 25 studs (est.) of the break point | knock (never toward the gap) |
| 0% | on/near chunk k when pop k fires (radius 30 est.); anyone missed is taken by final_blast within 150 studs (est.) | full fling, 0% table |
| already ragdolled | cooldown 3 s per player, except 0% overrides | - |

**How (target velocity, mass-independent; Gravity assumed Roblox default 196.2 studs/s², verify in place).**
| type | up vy | back (train −Z) | lateral | spin | apex (calc) | air cap | after landing |
|---|---|---|---|---|---|---|---|
| split fling | 70-90 | 25-45 | ±10 | 4-10 rad/s | 12-21 studs | 2.5 s | ragdoll 1.0 s, get up, return to coach |
| knock | 30-45 | away from gap 10-20 | ±5 | 0-3 | 2-5 studs | 1.0 s | ragdoll 0.8 s, get up in place |
| 0% fling | 90-130 | 15-35 | outward from pop 20-40 | 6-12 | 21-43 studs | 3.0 s | ragdoll until results |
Values seeded per event (v1 `Shared.rng`), so every client agrees. Air cap hit → server return (split) or freeze in
pose (0%).
- **Seated:** server destroys the SeatWeld first (3 s re-sit cooldown is engine behaviour), then flings. Seated B
  players near the break stay seated (seat jolt only).
- **Already in the air:** velocity is *set*, not added, so jumping cannot double a fling.
- **Authority:** server picks targets and vector, marks `RR_FlingUntil` (server time) on the player, and fires
  `RR_Fling` (server→client) to the owner. The owning client (characters are client-owned) sets Humanoid state
  Physics, IsKinematic=false on AnimationConstraints (Avatar Joint Upgrade; Motor6D + BallSocket fallback, Q5), sets
  AssemblyLinearVelocity/AngularVelocity, then restores IsKinematic and GettingUp. Server ApplyImpulse on a
  client-owned root is unverified, so the client applies it. An exploiter can only skip their own fling (harmless).
- **Return:** split flings end with a return to the train profile's return point ~1 s after landing; Joel's keep-on
  check skips players while `RR_FlingUntil` is live (needs his code, Q1).
- **Anti-grief:** no remote accepts a target from a client; any OnServerEvent on `RR_Fling` = misuse flag (v1
  pattern). Flung players switch to collision group `RR_Flung` (no player collide) until get-up; props and debris are
  client-local and non-colliding, so they cannot push anyone. Wrecks stay server-anchored/CFramed (v1) or
  SetNetworkOwner(nil), never client-owned. Flings never grant or take coins, Health or items. Generic exploiter
  self-physics flinging is outside this system and outside static scans (G5 gap).
- **Comfort:** camera keeps world-up (no roll), follows root position only, lag 0.15 s (est.); own-fling camera
  ≤ 2.5 s; flashes per av.feel.flash_limit; slow-mo once per run, ≤ 1.2 s. **Reduce Motion**
  (GuiService.ReducedMotionEnabled): no shake, FOV kick or slow-mo; cinematic becomes a static wide; the fling still
  happens (meaning kept) but with half spin.

## 3. Clip moments catalogue
| # | idea | what it looks like | why it clips | cost | risk | canon/tone fit | status | mech review? |
|---|---|---|---|---|---|---|---|---|
| 1 | ragdoll fling | split riders launched off, spinning, cartoon landing | the owner's ask; physical, visible | M | client physics varies by device; AJU | slapstick ✓; D-002 tension | CORE | yes |
| 2 | 0% wave launch | pops run rear→front, each launching its riders, cab last and highest | one shot shows the whole crew flying | M | timing with 6 clients | fail_cinematic ✓ | CORE | yes |
| 3 | cinematic wide + slow-mo | side-on wide, ~1 s slow-mo at final_blast (effects TimeScale, audio low-pass, own-character velocity ×0.35 with counter-gravity VectorForce) | money shot every fail | M | no engine time scale; hack may look floaty (unverified) | clip_moments ✓ | PROPOSED (task-set) | yes |
| 4 | flying props | luggage, coal lumps, sandwiches, seat cushions arcing with the crew (client, seeded, ≤8 debris per budget) | funny objects beside players | M | phone budget OQ-029 | ✓ | PROPOSED | no |
| 5 | flight callout | "23.5 m!" pops over the landing spot (studs × 0.28) | number invites one-upping | S | cosmetic only; client positions | ✓ | PROPOSED | no |
| 6 | "Most Flung" award | Incident Report award to the longest flight | named bragging on results | S | needs Joel's report hook | incident_report ✓ | PROPOSED | yes |
| 7 | screenshot + Share | auto capture at final_blast+0.4 s, HUD hidden; Share button on results (PromptShareCapture) | ready-made clip + invite link | M | under-13 limits; failures quiet | results share prompt ✓ | PROPOSED | yes |
| 8 | video capture | offer "record?" when integrity < 10% (StartVideoCaptureAsync, 30 s, beta) | real video of the blow-up | L | beta, platforms unknown, needs opt-in | ✓ | PROPOSED | yes |
| 9 | comedic landings | landing tags: head-first in the tender, back in a seat ("Nailed it"), bounce off a crate | surprise payoff | M | detection fiddly | ✓ | PROPOSED | no |
| 10 | slow-mo snap (70/30) | players within 25 studs get 0.5 s effect slow-mo + punch-in | makes splits clip too | S | fights hit-stop rule (≤150 ms canon) | partial | PROPOSED | yes |
| 11 | hat pop | accessories fly off on launch, land nearby (local only) | cheap extra chaos | S | cosmetic desync | ✓ | PROPOSED | no |
| 12 | NPC passengers flung | seated passenger NPCs ragdoll out with the crew, screaming | canon passengers lost on coupling snap | M | NPC count perf; passengers canon is minimal | coupling ✓ | PROPOSED | yes |

## 4. The 0% explosion as the game-over beat (CORE, L7/L11)
**Build-up below 10% (PROPOSED, Q8):** creak_warn every ~4 s, seam sparks and smoke at chunk joints, cab lamp
flicker, micro-shake (Reduce Motion off), optional alarm_integrity (P6 default off), alert "SHE'S GONNA BLOW!" in
Joel's HUD style. No input change: crew can still save it if his integrity system allows repair.

**Chain order** (chunks from the train profile, rear→front): any live lost wreck (secondary pop, PROPOSED) →
carriage chunks → tender/fuel → **core** (Coal: boiler; Diesel: fuel tank/engine). N ≤ 5 chunks, pops 0.3 s apart,
final_blast 0.4 s after the last (est.). Each pop launches its riders; final_blast takes everyone still grounded.
Chunk pieces are scripted + client debris (P5 counts). No Explosion instance (kills Humanoids, no falloff, ≤ 100 of
the 165-stud train).

**Camera:**
| t (s) | shot |
|---|---|
| 0 → final | own follow camera |
| final +0.1 | cut to a side-on wide, 140-180 studs out (est., frames 165 studs), slight upward dolly |
| +0.1 → +1.2 | slow-mo, then ramp out over 0.5 s |
| to +3.0 | hold the wide on the falling crew (canon 3 s fail moment) |
| +3.0 | YOU'RE FIRED stamp (reuses av.vfx.boiler_fail and the feel `fired_stamp`) |

**Time to game-over screen:** results open about 5 s after final_blast (est.), about 6-7 s after 0% is hit. The world
scroll brakes to a stop over ~3 s if the streamer allows it (Q4).

**Fit to Joel's flow (unknown; we need from his code):** (1) the 0% signal name and whether it can fire twice;
(2) his fail entry point to results (args, delay, reason; add `train_explosion` to run_end reason); (3) death/respawn
settings: CharacterAutoLoads, RespawnTime, ClassicDeath, Avatar Joint Upgrade; (4) keep-on script, for the
`RR_FlingUntil` skip; (5) seat type and custom seating code; (6) custom camera scripts and HUD hide/show API;
(7) segment-streamer speed control; (8) collision groups in use; (9) the universal layer's train handle (chunks, core,
return point); (10) the Incident Report award hook.

**Any train:** the per-train profile (P8) gives `chunks` (model paths, else bounding-box slices along the axis),
`core` (part name, else loco box centre), `returnPoint`, `flavour` (coal/diesel; P5 fx, P6 sound). One config block
per train; future trains add a profile only.

## 5. Recommendation
**MVP v2 (5):** #1 ragdoll fling · #2 0% wave launch · #3 cinematic wide + slow-mo · #4 flying props · #7 screenshot + Share.
- #1 and #2 are the ask.
- #3 turns the game over into the canon 3 s clip moment.
- #4 is cheap, because P5's debris carries it.
- #7 is the only growth payoff and is screenshot-only, so it carries no beta risk.

**Later:** #5 + #6 (small, need Joel's HUD/report hooks) · #9 + #11 (polish once the fling feels right) · #10
(clashes with the hit-stop rule) · #8 (beta, opt-in) · #12 (passengers minimal in alpha).

## 6. Build tasks
| id | deliverable | skill and commands | depends | model/effort | est. tok | done-when |
|---|---|---|---|---|---|---|
| CG0 | canon drafts: fling, 0% fail state, keep-on exemption, D-002/D-003 notes | rr-bible `bible.py add-question --dry-run`; owner decides, then add-fact | P9 review | sonnet/low | 15k | OQs listed; owner answers Q1-Q5 |
| CG1 | Shared fling maths (vector gen, seeded, arcs, apex/air time, flight distance) + Lune tests | Lune `run_tests.luau` | P8 Lune fix | sonnet/high | 40k | tests PASS; tables in §2 reproduced |
| CG2 | Server FlingService: target selection, cooldown, SeatWeld, `RR_FlingUntil`, `RR_Fling` remote, return | Luau; rr-exploit-guard `guard scan <M>/export --out <M>/security --fail-on high` | CG1, P8 intake + contract | opus/high | 70k | guard 0 high; misuse flag tested in Lune mock |
| CG3 | Client FlingClient: ragdoll (AJU + Motor6D fallback), velocity/spin, air cap, landing tiers, get-up, collision group, Reduce Motion | Luau | CG2 | opus/high | 70k | Studio: solo + 2-client Team Test fling/knock/0% pass (owner) |
| CG4 | ExplodeAll orchestrator: chunks from profile, pop order, wave launch, `Exploded` signal, hand-off to Joel's fail | Luau, Lune | CG2, P8 profile, P5 chunking | opus/high | 80k | Coal + Diesel both explode in order; results open once |
| CG5 | Camera: cinematic wide, slow-mo, stamp timing, comfort | rr-game-feel `feel.py set …`, `validate --strict`, `preview final_blast_cam --out D --gif --rm`, `crit`, `build --out D` | CG4, P5 beats | opus/high | 60k | validate PASS; Profile G ≥ 8 (D-020) |
| CG6 | Flying props (client, seeded) | rr-vfx-lighting `vfx validate --strict`, `vfx budget`, `vfx preview … --gif`; Luau | P5 debris, CG4 | sonnet/high | 40k | budget PASS (OQ-029) |
| CG7 | Capture + Share (screenshot, HUD hide, quiet failure) | Luau | CG5, Joel's results hook | sonnet/med | 30k | share sheet opens on phone; no error on unsupported device |
| CG8 | Sound hooks (fling_whoosh, body_impact, chain_pop, preboom_suck, final_blast, gameover_sting) | rr-soundsmith per P6 S1 | P6 S1, CG3/CG4 | sonnet/med | 20k | cues fire within 1 frame of beats (lab overlay) |
| CG9 | Analytics: `player_flung`, `train_explosion` reason | rr-data-and-money `track.py validate --strict`, `build` | CG2 | sonnet/low | 15k | validate PASS; server-only |
| CG10 | Motion review (no ragdoll critic exists, gap G2): 6-player 0% capture by the owner, rubric draft for skill-smith | multiuse-critic Profile F motion check + owner video; rr-skill-smith friction note | CG3-CG6 | opus/high | 40k | Joel types "FLING OK"; friction logged |
| CG11 | phone perf at 0% with 6 ragdolls + fx | MicroProfiler steps (P8) | CG3-CG6 | owner + sonnet/low | 10k | within P5 budgets on a mid-range phone |

## Owner questions (default in brackets)
- Q1: Are flung players charged the 5-coin keep-on fee? [No. The fling system returns them.]
- Q2: Do lost-section riders get flung off, or ride the wreck away? [Flung off at the snap.]
- Q3: Can a fling hurt or kill? [No, cosmetic only.]
- Q4: Does the world stop scrolling at 0%? [It brakes to a stop over ~3 s.]
- Q5: Is Avatar Joint Upgrade on in your place? [Assume yes; also ship the Motor6D fallback.]
- Q6: Video capture in v2? [No, the later set.]
- Q7: Add a "Most Flung" award? [Later set.]
- Q8: Build-up below 10%? [Yes, with the alarm off.]
- Q9: Record integrity (D-003) and flings vs "company handles falling" (D-002) as owner decisions? [Yes.]
