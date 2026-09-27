# Mission 260927-ticket-hud
Objective: Remake the Risky Rails notification HUD in a style more fitting for the game, keeping the ticket frame, to 8/10 on multiuse-critic, then export a Roblox-ready ScreenGui package; progress in 10 numbered steps.
Kind: ui · Profile: B · Bar: 8 (owner) · Cap: 5 passes
Env: cloud; playwright=yes; agents=yes; design-critic=not installed; design link unreadable by Artifact tool

## Source prompt
prompt.txt + lines.md (8 lines; ids are cited only in the R-table source column).

## Requirements
| id | owner words | requirement | type | source | status | done-when |
|---|---|---|---|---|---|---|
| R1 | "notification system for my game" | In-game notification system (HUD) | context | L1 | open | covered by R3 |
| R2 | "It will be UI HUD" + design link | Prototype = the given Claude Design (file= name "Risky Rails - Notifications HUD"; owner title "Risky Rails - HUD notification"; see Q1) | reference | L2 | open | refs/hud.facts.md exists; Q1 answered or default logged |
| R3 | "please remake this" | New design, same function: 4 kinds, 10 types, states | deliverable | L3 | open | all 10 types + compact + overflow + merge rendered |
| R4 | "a style you deem ... more fitting" | Creative licence: Risky Rails style (steam, rail, weathered) | style-licence | L3 | open | style rationale in 2 lines at debrief; B5 >= 8 |
| R5 | "I like the ticket frame" | Keep ticket anatomy: stub, punch notches, perforation, stamp | style-keep | L4 | open | all 5 anatomy parts present on every kind |
| R6 | "Run critic agent until ... 8/10" | multiuse-critic loop, profile B, bar 8 | quality | L5 | open | every B1-B6 >= 8 with final pass |
| R7 | "export it ready for roblox" | ScreenGui builder + controller + icon sheet + ASSETS.md | export | L6 | open | Lua syntax check passes; ASSETS.md complete |
| R8 | "progress updates (steps ... up to 10)" | Exactly 10 numbered step updates | comms | L7 | open | progress.log has [1/10]..[10/10] |
| R*9 | (implied) | Preserve exact texts, kinds, lifetimes, cap 4, sticky crisis | derived | L2,L3 | open | text diff vs facts = 0 |
| R10 | "Thanks and have fun" | - | noise | L8 | noise | - |

## Decisions and assumptions
A1 Devices: phone landscape 844x390 primary (true size), PC 1280x720 second (rr-profile).
A2 Direction: enamel railway-signage + brass rivets on the ticket frame; soot-and-cream paper; keep Luckiest Guy + Montserrat. Alternative offered at debrief: punched-card/ticket-machine print.
A3 Placement: bottom-right stack, above the jump-button zone; newest at bottom; cap 4, "+N MORE".
A4 Scale sizing + UIAspectRatioConstraint; UIScale 1.0 phone, 1.16 PC.
Q1 Search Design artifacts for the owner's title "Risky Rails - HUD notification" and the link's file name "Notifications HUD" (punctuation and word order ignored). Match found -> use it, no question. No match -> (blocking) "Your design link did not open and no design named 'Risky Rails - HUD notification' / 'Notifications HUD' is listed; closest is '<title>' (name differs: <how>). Use it?" - pending
No other questions (style licence given; texts from refs).

## Spec
### Notification HUD
Boards: PC 1280x720; Phone 844x390 x6 scenarios (as prototype); Kit. Ticket 290x64 (compact 44). Kinds: danger / risk / cash / info with stub, bar, stamp colours from refs/hud.facts.md (fidelity exact for texts and behaviour, inspired for surface style).
States: enter/leave slide, crisis shake + pulse halo, merge bump + count badge, compact older, overflow chip.
Frames: phone 844x390 at 1:1 in contact sheet band; PC board scaled.

## Acceptance
Profile B list from mission-template.md, plus R5 anatomy check, R*9 text diff.

## Needs owner / placeholders
Crew names ({name}) are placeholders; asset ids in ASSETS.md are placeholders until upload.

## Next action
python3 <me>/scripts/plan.py check <M>/plan.json --mission <M>/mission.md
