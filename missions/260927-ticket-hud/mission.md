# Mission 260927-ticket-hud
Objective: Remake the Risky Rails notification HUD in a style more fitting for the game, keeping the ticket frame, to 8/10 on multiuse-critic, then export a Roblox-ready ScreenGui package; progress in 10 numbered steps.
Kind: ui · Profile: B · Bar: 8 (owner) · Cap: 5 passes
Env: cloud; playwright=yes (chromium /opt/pw-browsers); agents=NO Agent tool (critic = self-assessed, see SKILL-FRICTION #2); design-critic=not installed; design link unreadable by Artifact tool; owner away

## Source prompt
prompt.txt + lines.md (8 lines).

## Requirements
| id | owner words | requirement | type | source | status | done-when |
|---|---|---|---|---|---|---|
| R1 | "notification system for my game" | In-game notification system (HUD) | context | L1 | done | covered by R3 |
| R2 | "It will be UI HUD" + design link | Prototype = the given Claude Design; link unopenable, owner title not listed; using "Risky Rails Ticket Notifications" (Q1) | reference | L2 | fallback | refs/ticket-notifications.facts.md exists; Q1 default logged |
| R3 | "please remake this" | New design, same function: 4 kinds, 10 types, states | deliverable | L3 | done | all 10 types + compact + overflow + merge rendered |
| R4 | "a style you deem ... more fitting" | Creative licence: Risky Rails style (steam, rail, weathered, brass) | style-licence | L3 | done | style rationale at debrief; B5 >= 8 |
| R5 | "I like the ticket frame" | Keep ticket anatomy: stub, punch notches, perforation, stamp, medallion | style-keep | L4 | done | all anatomy parts present on every kind |
| R6 | "Run critic agent until ... 8/10" | multiuse-critic loop, profile B, bar 8 | quality | L5 | fallback | every B1-B6 >= 8 with final pass |
| R7 | "export it ready for roblox" | ScreenGui builder + controller + icon sheet + ASSETS.md | export | L6 | done | Luau syntax check passes; ASSETS.md complete |
| R8 | "progress updates (steps ... up to 10)" | Exactly 10 numbered step updates | comms | L7 | done | progress.log has [1/10]..[10/10] |
| R*9 | (implied) | Preserve exact texts, kinds, lifetimes, cap 4, sticky crisis | derived | L2,L3 | verified | text diff vs facts = 0 |
| R10 | "Thanks and have fun" | - | noise | L8 | noise | - |

## Decisions and assumptions
A1 Devices: phone landscape 844x390 primary (true size), PC 1280x720 second.
A2 Direction: "railway company ticket": soot-iron outer frame with brass rivets on the stub, aged cream card with faint printed guilloche/serial "No." line, kind stubs as enamel colours, stamp as rubber-stamp ink. Keep Luckiest Guy + Montserrat. Alternative at debrief: punched-card ticket-machine print.
A3 Placement: bottom-right stack above the jump-button zone; newest at bottom; cap 4, "+N MORE".
A4 Scale sizing + UIAspectRatioConstraint; UIScale 1.0 phone, 1.16 PC.
A5 Icons redrawn as simple chunky vector icons; Roblox export uses an icon sheet PNG (upload needed).
Q1 Your link didn't open and no design titled "Risky Rails - HUD notification"/"Notifications HUD" is listed; closest is "Risky Rails Ticket Notifications" (same ticket frame; created today, may be a later remake). Use it? - default: yes - answer: owner away, default taken (blocking by skill; harness said proceed)
No other questions.

## Spec
### Notification HUD
Boards: PC 1280x720; Phone 844x390 x4 scenarios (crisis at bottom, routine, crises+junction, overflow pinned); Kit. Ticket 290x64 (compact 44). Kinds/colours/texts from refs/ticket-notifications.facts.md (fidelity exact for texts+behaviour, inspired for surface).
States: enter/leave slide, crisis shake + pulse halo, merge bump + count badge, compact older, overflow chip.
Frames: phone 844x390 at 1:1 in contact sheet; PC board scaled.

## Acceptance
- B1 one job per element; most urgent state reads first
- B2 body >= 12 px, titles >= 16 px at 844x390; AA 4.5:1 body, 3:1 large
- B3 clear of topbar (top 36 px), thumbstick (bottom-left), jump (bottom-right ~120x120); Scale + UIAspectRatioConstraint plan
- B4 tokens palette; kinds distinct for colour-blind (icon/pattern backup)
- B5 Risky Rails house style; ticket anatomy preserved
- B6 motion defined, all states rendered (overflow, compact, merge)
- R5 anatomy check, R*9 text diff = 0

## Needs owner / placeholders
Q1 confirmation. Crew names placeholders; asset ids in ASSETS.md are placeholders until upload.

## Next action
see state.json
