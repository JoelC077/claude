# Patch brief: rr-data-and-money 0.0.0 (2026-09-28)

Rules: stage first (`ship.py stage SKILL`), edit only the staged copy; one cluster per change; write the regression check first and see it fail (or, for a claimed fix, pass), then make the smallest fix; no new features; SKILL.md may grow by 5 lines at most; then `ship.py propose`. Owner approves before anything ships.

## P1 Silent success or false PASS hides a problem (rr-data-and-money/silent-pass, n=2, open 0, sev M)
Fix hint: Fail loudly (non-zero exit, named item) and add the case to the selftest.
Web-wide (also rr-exploit-guard, rr-game-feel, rr-release-train, rr-soundsmith, rr-ui-foundry, rr-vfx-lighting): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [M] t:rr-data-and-money#8 (claimed): sweeps silently use a smaller, noisier sample and leave no record :: `cmd_sim` sweeps use installs/3 and 300 engaged players (800 in a full sim). With the same v0 config: | | runs to loco_2 | minutes | earned ARPDAU | |---|---|---|---| | full sim | 7.0 | 94 | 0.974 | | sweep row | 6.0 | 8
- [L] t:rr-data-and-money#22 (claimed): `--sim` without economy rows is skipped silently :: The memo gives no note that the sim comparison could not run. Also, no memo text marks inputs as synthetic apart from the file name in "Data notes" and the headline written here; `SYNTHETIC_*` inputs could stamp the memo
Check to add (evals/evals.json "checks"): {"id": "fr-silent-pass", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-data-and-money#8", "t:rr-data-and-money#22"]}

## P2 Skill values contradict canon (numbers, gauge, colours, strings) (rr-data-and-money/canon-drift, n=2, open 0, sev M)
Fix hint: Read the value from rr-bible at run time (key cited), and add a drift.py check or a `check:` regex to the fact.
Web-wide (also rr-release-train, rr-ui-foundry, rr-vfx-lighting): the shared part belongs in rr-bible; reference it, do not copy it.
Evidence:
- [M] t:rr-data-and-money#9 (claimed): canon can be overridden without a warning :: Re-labelling a canon-backed value `{"v", "assumed"}` passes `validate`, `sim` and `guard` with 0 warnings. v0 did this for supplies (60/200/30/150 vs canon 40/120/25/90) and for loco_2 (4,000 vs canon 2,500); the trial c
- [L] t:rr-data-and-money#16 (claimed): the gate is silent on prices that depart from canon :: M13 INFO rows cover only canon-proposed prices; the assumed fare_pack_l 15,000/449 gets no row
Check to add (evals/evals.json "checks"): {"id": "fr-canon-drift", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-data-and-money#9", "t:rr-data-and-money#16"]}

## P3 Workflow tells missions to edit the shared skill instead of a mission copy (rr-data-and-money/edits-skill, n=1, open 0, sev M)
Fix hint: Default every write to the mission copy (env override such as RR_<X>_PRESETS); the skill folder is read-only at run time.
Web-wide (also rr-soundsmith, rr-ui-foundry, rr-vfx-lighting): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [M] t:rr-data-and-money#4 (claimed): SKILL tells missions to edit the skill's own presets :: Three places: - step 1.2: "Edit `<me>/presets/tracking-plan.json`" - Money: "New or changed products go into `<me>/presets/catalogue.json`" - economy-model.md: "Change the preset" The installed skill is synced (edits get
Files: presets/tracking-plan.json, presets/catalogue.json, references/economy-model.md, scripts/track.py
Check to add (evals/evals.json "checks"): {"id": "fr-edits-skill", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-data-and-money#4"]}

