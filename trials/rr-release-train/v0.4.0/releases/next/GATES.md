# Gates · 0.4.0 (alpha) · NO-GO

Run 2026-09-28T03:31Z. Blocking in alpha: G1, G2, G3, G4, G5, G6, G9. Visual judgement: multiuse-critic; security: rr-exploit-guard; approval: the owner.

| gate | status | summary |
|---|---|---|
| G1 version | WARN | 0.4.0 · 0.4.0 does not carry channel alpha's tag 'alpha' |
| G2 changes | PASS | 2 in build (2 player) · bump minor |
| G3 patch notes | PASS | traced and covered · 0 warnings |
| G4 canon | WARN | 2 off-palette colours/fonts in the places (bought or kitbashed assets are often off-token) · scripts: names and numbers clean |
| G5 security | PENDING | no security verdict |
| G6 tests | PENDING | tests deferred · bug bash needed (minor or bigger release) |
| G7 performance | PASS | Lobby: baseline 820 instances, 801 parts, 21827 B scripts (no previous audit to compare) (budgets: OQ-039 default A) |
| G8 visuals | WARN | 0/2 visual changes certified by an independent critic |
| G9 hygiene | WARN | audio: no placeholder or unlicensed sound (rr-soundsmith): FAILED   note  feel parity: ui_button_press exists in rr-game |
| G10 open questions | WARN | 6 open questions touch releasing; their defaults are in use |

## G1 version · WARN
- 0.4.0 does not carry channel alpha's tag 'alpha'

## G4 canon · WARN
- Lobby colour/font: #2A6040: off-palette; nearest style.cab.wall_green #2F6B4F (dE 5.3)
- Trip colour/font: #2A6040: off-palette; nearest style.cab.wall_green #2F6B4F (dE 5.3)

## G5 security · PENDING
- fix: rr-exploit-guard (not installed yet): scan /home/user/claude/trials/rr-release-train/v0.4.0/releases/next/places/Lobby/audit/scripts /home/user/claude/trials/rr-release-train/v0.4.0/releases/next/places/Trip/audit/scripts and write /home/user/claude/trials/rr-release-train/v0.4.0/releases/next/security/SECURITY_GATE.json

## G6 tests · PENDING
- tests deferred: run_tests.lua runs on each saved version before publish; publish stops on a fail
- bug bash needed (minor or bigger release): scripted: join together, one leaves, all leave, rejoin; fail, arrive, jump off, roof in tunnel; solo on difficulty 4; teleport home and spend; double-tap an order; spam the lever after it locks; 4x soak with F9 memory flat
- fix: owner runs the bug bash and records `evidence bugbash --result pass --by owner --note ...`

## G7 performance · PASS
- Lobby: baseline 820 instances, 801 parts, 21827 B scripts (no previous audit to compare)
- Trip: baseline 46 instances, 30 parts, 20944 B scripts (no previous audit to compare)
- effects: phone concurrency budget (rr-vfx-lighting): ok ok   boiler_fail    steady 14, peak 68, emitters 5, fill 2916, lights 4 (1 shadowed), beams 0, debris 6 | ok   derail         steady 54, peak 122, emitters 7, fill 5073, lights 4 (1 shadowed), beams 0, debris 5 | budget PASS: 0 set(s) over

## G8 visuals · WARN
- C-1 New buildings in the Depot Lobby: the stone statio: uncertified (critique-buildings 8/8 by self-review-final; critique-depot-indep 7/8 by (unrecorded); critique-hall-indep 7/8 by (unrecorded))
- C-2 Alerts got a makeover: every alert now arrives as : uncertified (critique-hud 6/8 by independent-critic)
- fix: multiuse-critic: one independent --kind final pass on /home/user/claude/missions/260927-depot-buildings
- fix: multiuse-critic: one independent --kind final pass on /home/user/claude/missions/260927-ticket-hud

## G9 hygiene · WARN
- audio: no placeholder or unlicensed sound (rr-soundsmith): FAILED   note  feel parity: ui_button_press exists in rr-game-feel without a cue; add {"type": "cue", "sfx": "ui_click"} there to route it through Feel (then set via feel here) |   note  feel parity: alert_crew_joined exists in rr-game-feel without a cue; add {"type": "cue", "sfx": "ticket_chime"} there to

## G10 open questions · WARN
- OQ-010 Robux in the supply terminal: default A for the alpha; any Robux product passes the mechanic reviewer and D-007 first (assumed)
- OQ-019 Marketing budget split: default A (assumed)
- OQ-024 Launch player cap: default A (assumed)
- OQ-037 Release version scheme and channels (missing canon): default A (sorts correctly, says how big a change is, keeps test builds apart) (assumed)
- OQ-039 Place-level performance budgets (missing canon): default A until B is measured at the alpha live check (assumed)
- OQ-040 Staging place for release candidates (missing canon): default A (zero setup now; B before the public soft launch, when a bad publish hits real players) (assumed)
- fix: owner: `bible decide OQ-nnn X --by owner` when ready
