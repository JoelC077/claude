# Gates · 0.4.0 (alpha) · NO-GO

Run 2026-09-28T04:14Z. Blocking in alpha: G1, G2, G3, G4, G5, G6, G9. Visual judgement: multiuse-critic; security: rr-exploit-guard; approval: the owner.

| gate | status | summary |
|---|---|---|
| G1 version | WARN | 0.4.0 · 0.4.0 does not carry channel alpha's tag 'alpha' |
| G2 changes | WARN | 2 in build (2 player) · bump minor · in build on the agent's word, no owner citation: C-1, C-2 |
| G3 patch notes | PASS | every line traced · 0 warnings |
| G4 canon | WARN | 2 off-palette colours/fonts · scripts: no banned name; numbers compared only where canon has a check pattern · 2 possible number drifts (heuristic) |
| G5 security | PENDING | no security verdict |
| G6 tests | PENDING | tests deferred · bug bash needed (minor or bigger release) |
| G7 performance | WARN | no baseline: owner phone evidence needed · Lobby: no baseline to compare (first audited release): 820 instances, 801 parts (771 MeshParts, 3 (budgets: OQ-039 default A) |
| G8 visuals | WARN | 0/2 visual changes certified (independent, at the bar, final pass agrees) |
| G9 hygiene | WARN | 8 findings · Lobby ReplicatedStorage.RR_Notifications.NotificationHud:17: blank asset id rbxassetid://0 (upload the asset, set the id) |
| G10 open questions | WARN | 6 touch in-build changes · 13 open questions in play |

## G1 version · WARN
- 0.4.0 does not carry channel alpha's tag 'alpha'

## G2 changes · WARN
- in build on the agent's word, no owner citation: C-1, C-2
- fix: ask the owner what is in Studio, then release.py mark C-1 C-2 --in-build yes --via "chat DATE"

## G4 canon · WARN
- Lobby colour/font: #2A6040: off-palette; nearest style.cab.wall_green #2F6B4F (dE 5.3)
- Trip colour/font: #2A6040: off-palette; nearest style.cab.wall_green #2F6B4F (dE 5.3)
- possible number drift: Lobby NotificationHud:44 gap = 6; canon ui.hud.gap_px = 8 (between tickets (remake used 6))
- possible number drift: Trip NotificationHud:44 gap = 6; canon ui.hud.gap_px = 8 (between tickets (remake used 6))
- fix: fix the script to canon, or record the change with bible add-fact / decide (owner)

## G5 security · PENDING
- fix: rr-exploit-guard (/home/user/claude/rr-exploit-guard): scan /home/user/claude/trials/rr-release-train/v0.4.0-retrial/releases/next/places/Lobby/audit/scripts /home/user/claude/trials/rr-release-train/v0.4.0-retrial/releases/next/places/Trip/audit/scripts, gate --stage alpha --out /home/user/claude/trials/rr-release-train/v0.4.0-retrial/releases/next/security

## G6 tests · PENDING
- tests deferred: run_tests.lua runs on each saved version before publish; publish stops on a fail
- bug bash needed (minor or bigger release): scripted: join together, one leaves, all leave, rejoin; fail, arrive, jump off, roof in tunnel; solo on difficulty 4; teleport home and spend; double-tap an order; spam the lever after it locks; 4x soak with F9 memory flat
- fix: owner runs the bug bash and records `evidence bugbash --result pass --by owner --note ...`

## G7 performance · WARN
- Lobby: no baseline to compare (first audited release): 820 instances, 801 parts (771 MeshParts, 3 unanchored), 7 scripts, 0 effects, 20 KB file
- Trip: no baseline to compare (first audited release): 46 instances, 30 parts (0 MeshParts, 3 unanchored), 6 scripts, 0 effects, 12 KB file
- fix: owner: play the new content on a phone (F9 memory, FPS) and record `evidence perf --result pass --by owner --note "phone, FPS, MB"`

## G8 visuals · WARN
- C-1 New buildings in the Depot Lobby: the stone statio: uncertified (critique-buildings 8/8 by self-review-final, no independent final pass; critique-depot-indep 7/8 by (unrecorded), no independent final pass; critique-hall-indep 7/8 by (unrecorded), no independent final pass)
- C-2 Alerts got a makeover: every alert now arrives as : uncertified (critique-hud 6/8 by independent-critic, no independent final pass)
- fix: C-1: at the bar on self-review only: one independent --kind final multiuse-critic pass (/home/user/claude/missions/260927-depot-buildings/critique-buildings)
- fix: C-2: standing 6/8: finish the fix loop in rr-mission-control (fix the open blocks-8 issues), then one independent --kind final pass (/home/user/claude/missions/260927-ticket-hud/critique-hud)

## G9 hygiene · WARN
- Lobby ReplicatedStorage.RR_Notifications.NotificationHud:17: blank asset id rbxassetid://0 (upload the asset, set the id)
- Lobby ReplicatedStorage.RR_Notifications.NotificationHud:18: blank asset id rbxassetid://0 (upload the asset, set the id)
- Lobby StarterPlayer.StarterPlayerScripts.NotificationDemo: marked delete-for-release by its mission (LocalScript) ships in the build
- Lobby: modules nothing in this place requires: CrisisManager (dead code, or the feature is not wired up here)
- Lobby: modules only a demo script requires: NotificationController (only NotificationDemo) (delete the demo and nothing calls them)
- Trip ReplicatedStorage.RR_Notifications.NotificationHud:17: blank asset id rbxassetid://0 (upload the asset, set the id)
- Trip ReplicatedStorage.RR_Notifications.NotificationHud:18: blank asset id rbxassetid://0 (upload the asset, set the id)
- Trip: modules nothing in this place requires: NotificationController, CrisisManager (dead code, or the feature is not wired up here)
- fix: owner uploads the assets (Asset Manager) and sets the ids, then re-attach
- fix: owner deletes demo/test scripts from the place, saves, re-attaches

## G10 open questions · WARN
- touches C-2: OQ-001 HUD skin: heritage brass or teal-cream/mustard livery?: default C, then one independent critic pass on A vs C boards side by side before the owner picks (assumed) (blocks: final HUD export, rr-ui-foundry tokens)
- OQ-010 Robux in the supply terminal: default A for the alpha; any Robux product passes the mechanic reviewer and D-007 first (assumed)
- touches C-2: OQ-012 HUD alert IDs: per fault or generic BREAKDOWN?: default A, with proposed texts marked proposed until approved (assumed) (blocks: HUD type table)
- touches C-1: OQ-015 Main Hall: where, and does it stay?: default A until the owner says otherwise (assumed) (blocks: lobby dressing)
- touches C-1: OQ-016 Station, depot and signage names: default B (proposals marked proposed until picked) (assumed) (blocks: signage text)
- OQ-019 Marketing budget split: default A (assumed)
- touches C-1: OQ-020 Missing canon: project docs and the approved diesel: default A (assumed) (blocks: full style canon (materials, fence, depot dressing checklist))
- OQ-024 Launch player cap: default A (assumed)
- touches C-2: OQ-034 HUD stack bottom offset vs the newer jump button: default A (the classic jump layout keeps canon's 4-ticket stack; the ability-controls layout is de (assumed) (blocks: none (default in use))
- OQ-037 Release version scheme and channels (missing canon): default A (sorts correctly, says how big a change is, keeps test builds apart) (assumed)
- OQ-039 Place-level performance budgets (missing canon): default A until B is measured at the alpha live check (assumed)
- OQ-040 Staging place for release candidates (missing canon): default A (zero setup now; B before the public soft launch, when a bad publish hits real players) (assumed)
- OQ-042 Server shutdown mid-trip (update restart): what does the crew keep?: default A (a restart for an update is the studio's fault, not the crew's; matches the fail rule) (assumed)
- fix: owner: `bible decide OQ-nnn X --by owner` (or waive G10 with a reason) when ready

## Advisory: sibling library checks (not about this build; not in the verdict or approval)
- G7 (library, not this build) effects: phone concurrency budget (rr-vfx-lighting): ok budget PASS: 0 set(s) over
- G9 (library, not this build) audio: no placeholder or unlicensed sound (rr-soundsmith): ok note  release: no alpha sound has audio yet: this build ships silent, which the plan allows (av.audio.priority_in_plan: sound is a COULD for the alpha)
