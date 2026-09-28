# Patch brief: rr-ui-foundry 0.0.0 (2026-09-28)

Rules: stage first (`ship.py stage SKILL`), edit only the staged copy; one cluster per change; write the regression check first and see it fail (or, for a claimed fix, pass), then make the smallest fix; no new features; SKILL.md may grow by 5 lines at most; then `ship.py propose`. Owner approves before anything ships.

## P1 Skill values contradict canon (numbers, gauge, colours, strings) (rr-ui-foundry/canon-drift, n=2, open 2, sev H)
Fix hint: Read the value from rr-bible at run time (key cited), and add a drift.py check or a `check:` regex to the fact.
Web-wide (also rr-data-and-money, rr-release-train, rr-vfx-lighting): the shared part belongs in rr-bible; reference it, do not copy it.
Evidence:
- [H] t:rr-ui-foundry#2 (open): Notched phones fall below canon minimums while validate still passes :: SKILL.md step 2 applies min text and targets "on the phone (warnings on other devices)", and `phone_notch` counts as another device. - The layout rule uses one global `s = min(areaW/844, areaH/332)`. The 59 px notch inse
- [M] t:rr-ui-foundry#4 (open): The shipped example was the trial task, and it contradicts its own source :: `specs/hud_tickets.json` and `specs/lobby_create_match.json` already are "HUD + Create match". - Step 1 says "Start from specs/". It doesn't say to copy the spec into the mission (`<M>/src/<d>/spec.json` appears only und
Files: SKILL.md, specs/hud_tickets.json, specs/lobby_create_match.json
Check to add (evals/evals.json "checks"): {"id": "fr-canon-drift", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-ui-foundry#2", "t:rr-ui-foundry#4"]}

## P2 Silent success or false PASS hides a problem (rr-ui-foundry/silent-pass, n=2, open 2, sev H)
Fix hint: Fail loudly (non-zero exit, named item) and add the case to the selftest.
Web-wide (also rr-data-and-money, rr-exploit-guard, rr-game-feel, rr-release-train, rr-soundsmith, rr-vfx-lighting): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [H] t:rr-ui-foundry#1 (open): BUILD PASS can't be reached for any lobby spec that differs from the shipped example: 2 false FAILs in luatest :: `ui build` reported `FAIL luatest parity` and `BUILD FAIL`. Parity itself matched 1628/1628; the two failures came from runtime checks: - `luatest.py:438` loads the lobby spec from `U.SKILL / "specs"` instead of the spec
- [L] t:rr-ui-foundry#7 (open): A copied example spec loses its icons without an error :: The spec keeps `"icons": "../assets/icons"`, resolved relative to the spec file (`uimodel.py:561`). Outside `specs/` the only sign is a warning ("placeholder on boards"). spec.md doesn't say that leaving out `icons` fall
Files: scripts/luatest.py:438, scripts/luatest.py:406, scripts/luatest.py:388, SKILL.md, scripts/uimodel.py:561, references/spec.md
Check to add (evals/evals.json "checks"): {"id": "fr-silent-pass", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-ui-foundry#1", "t:rr-ui-foundry#7"]}

## P3 No path for jobs with several deliverables (screens, variants, effects, looks) (rr-ui-foundry/multi-deliverable, n=1, open 1, sev H)
Fix hint: Accept a list of names end to end (render, sheet, crit, export) and test it with 2+ items.
Web-wide (also rr-asset-foundry, rr-vfx-lighting): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [H] t:rr-ui-foundry#3 (open): A kit job covering 2 or more screens has no path through render and crit :: `ui render` and `ui crit` take one spec each. `brief_md` describes one screen. multiuse-critic wants one `critic.md`, one `contact.png` and at most one close-up, and two specs give 20 boards. - To show the kit's main cla
Check to add (evals/evals.json "checks"): {"id": "fr-multi-deliverable", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-ui-foundry#3"]}

