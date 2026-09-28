# Patch brief: rr-game-feel 0.0.0 (2026-09-28)

Rules: stage first (`ship.py stage SKILL`), edit only the staged copy; one cluster per change; write the regression check first and see it fail (or, for a claimed fix, pass), then make the smallest fix; no new features; SKILL.md may grow by 5 lines at most; then `ship.py propose`. Owner approves before anything ships.

## P1 Critic evidence misses part of the deliverable (one close-up, hero only, no tiles) (rr-game-feel/critic-evidence, n=2, open 1, sev H)
Fix hint: Let the brief carry every deliverable (or a second evidence sheet) and label tiles; add an eval that counts deliverables vs tiles.
Web-wide (also multiuse-critic, rr-mission-control, rr-soundsmith, rr-vfx-lighting): the shared part belongs in multiuse-critic; reference it, do not copy it.
Evidence:
- [H] t:rr-game-feel#4 (claimed): Critics only see each group's hero event :: Kit events that are not heroes (crate landed, hard brake) never reach a critic. The lever drag curve (`lever.png`), the core of "lever pull", is not in the lever closeups either. `critic_kit --images` allows only one clo
- [L] t:rr-game-feel#16 (open): The tuning table and a plots contact sheet are not first-class outputs :: FEEL_SPEC.md holds prose tables per event (640 lines for 34 events), with no per-moment knob table with ranges and no sheet of the plots
Check to add (evals/evals.json "checks"): {"id": "fr-critic-evidence", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-game-feel#4", "t:rr-game-feel#16"]}

## P2 Tool missing in the cloud image; no documented fallback (rr-game-feel/toolchain, n=1, open 0, sev H)
Fix hint: Name the cloud fallback (and its limits) next to the preferred tool.
Web-wide (also rr-exploit-guard, rr-mission-control): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [H] t:rr-game-feel#1 (claimed): The skill cannot produce or verify strict-typed Luau :: The runtime has no `--!strict` and no annotations, and the only syntax gate is luaparse (Lua 5.1 grammar), which rejects Luau type syntax. Real tools install in about 20 s in the cloud and would replace luaparse
Check to add (evals/evals.json "checks"): {"id": "fr-toolchain", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-game-feel#1"]}

## P3 A checker measures the wrong thing (rr-game-feel/wrong-measure, n=1, open 0, sev H)
Fix hint: Measure the delivered result (per piece / per frame) and plant a known-bad case in the selftest.
Web-wide (also rr-asset-foundry, rr-release-train, rr-soundsmith): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [H] t:rr-game-feel#2 (claimed): Canon agreement checks the knob, not the delivered motion :: `hud_crisis_arrival` cites canon "+-5 px" and passes, but its 12 Hz noise punch moves the ticket 1.49 px. The HUD export it claims to follow shakes at about 5 Hz, -5/+5/-4/+3 px. `lever_snapback` (amp 4) moves 0.66 px. N
Check to add (evals/evals.json "checks"): {"id": "fr-wrong-measure", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-game-feel#2"]}

