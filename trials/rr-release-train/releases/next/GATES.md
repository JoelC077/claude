# Gates · 0.1.0-alpha.1 (alpha) · NO-GO

Run 2026-09-28T03:25Z. Blocking in alpha: G1, G2, G3, G4, G5, G6, G9. Visual judgement: multiuse-critic; security: rr-exploit-guard; approval: the owner.

| gate | status | summary |
|---|---|---|
| G1 version | PASS | 0.1.0-alpha.1 · stamps match |
| G2 changes | PASS | 7 in build (4 player) · bump minor |
| G3 patch notes | PASS | traced and covered · 0 warnings |
| G4 canon | WARN | 6 off-palette colours/fonts in the places (bought or kitbashed assets are often off-token) · scripts: names and numbers clean |
| G5 security | PENDING | no security verdict |
| G6 tests | PENDING | no test result · bug bash needed (minor or bigger release) |
| G7 performance | PASS | Lobby: baseline 44 instances, 33 parts, 737 B scripts (no previous audit to compare) (budgets: OQ-039 default A) |
| G8 visuals | WARN | 0/2 visual changes certified by an independent critic |
| G9 hygiene | WARN | Lobby ServerScriptService.CrisisManager:3: debug flag DEBUG = true |
| G10 open questions | WARN | 6 open questions touch releasing; their defaults are in use |

## G4 canon · WARN
- Lobby colour/font: #2A6040: off-palette; nearest style.cab.wall_green #2F6B4F (dE 5.3)
- Lobby colour/font: #F6C500: off-palette; nearest style.brand.hazard_yellow #F2C230 (dE 9.6)
- Lobby colour/font: #FF00FF: off-palette; nearest ui.hud_kinds.danger_stub_top #F0604F (dE 108.4)
- Trip colour/font: #2A6040: off-palette; nearest style.cab.wall_green #2F6B4F (dE 5.3)
- Trip colour/font: #F6C500: off-palette; nearest style.brand.hazard_yellow #F2C230 (dE 9.6)
- Trip colour/font: #FF00FF: off-palette; nearest ui.hud_kinds.danger_stub_top #F0604F (dE 108.4)

## G5 security · PENDING
- fix: rr-exploit-guard (not installed yet): scan /home/user/claude/trials/rr-release-train/releases/next/places/Lobby/audit/scripts /home/user/claude/trials/rr-release-train/releases/next/places/Trip/audit/scripts and write /home/user/claude/trials/rr-release-train/releases/next/security/SECURITY_GATE.json

## G6 tests · PENDING
- no test result
- bug bash needed (minor or bigger release): scripted: join together, one leaves, all leave, rejoin; fail, arrive, jump off, roof in tunnel; solo on difficulty 4; teleport home and spend; double-tap an order; spam the lever after it locks; 4x soak with F9 memory flat
- fix: owner runs assets/luau/run_tests.lua in Studio (command bar, server) and records `evidence tests --result pass --by owner --note "N specs"`
- fix: owner runs the bug bash and records `evidence bugbash --result pass --by owner --note ...`

## G7 performance · PASS
- Lobby: baseline 44 instances, 33 parts, 737 B scripts (no previous audit to compare)
- Trip: baseline 43 instances, 32 parts, 738 B scripts (no previous audit to compare)
- effects: phone concurrency budget (rr-vfx-lighting): ok ok   boiler_fail    steady 14, peak 68, emitters 5, fill 2916, lights 4 (1 shadowed), beams 0, debris 6 | ok   derail         steady 54, peak 122, emitters 7, fill 5073, lights 4 (1 shadowed), beams 0, debris 5 | budget PASS: 0 set(s) over

## G8 visuals · WARN
- C-6 New depot and main hall in the Depot Lobby: uncertified (critique-buildings 8/8 by self-review-final; critique-depot-indep 7/8 by (unrecorded); critique-hall-indep 7/8 by (unrecorded))
- C-7 New ticket-style HUD alerts: uncertified (critique-hud 6/8 by independent-critic)
- fix: multiuse-critic: one independent --kind final pass on /home/user/claude/missions/260927-depot-buildings
- fix: multiuse-critic: one independent --kind final pass on /home/user/claude/missions/260927-ticket-hud

## G9 hygiene · WARN
- Lobby ServerScriptService.CrisisManager:3: debug flag DEBUG = true
- Lobby: placeholder instances ['Workspace.PLACEHOLDER_Signal']
- Trip: placeholder instances ['Workspace.PLACEHOLDER_Signal']
- audio: no placeholder or unlicensed sound (rr-soundsmith): FAILED   note  feel parity: ui_button_press exists in rr-game-feel without a cue; add {"type": "cue", "sfx": "ui_click"} there to route it through Feel (then set via feel here) |   note  feel parity: alert_crew_joined exists in rr-game-feel without a cue; add {"type": "cue", "sfx": "ticket_chime"} there to
- fix: turn debug flags off before a live release (tech.security.admin); alpha may keep owner-only admin

## G10 open questions · WARN
- OQ-010 Robux in the supply terminal: default A for the alpha; any Robux product passes the mechanic reviewer and D-007 first (assumed)
- OQ-019 Marketing budget split: default A (assumed)
- OQ-024 Launch player cap: default A (assumed)
- OQ-037 Release version scheme and channels (missing canon): default A (sorts correctly, says how big a change is, keeps test builds apart) (assumed)
- OQ-039 Place-level performance budgets (missing canon): default A until B is measured at the alpha live check (assumed)
- OQ-040 Staging place for release candidates (missing canon): default A (zero setup now; B before the public soft launch, when a bad publish hits real players) (assumed)
- fix: owner: `bible decide OQ-nnn X --by owner` when ready
