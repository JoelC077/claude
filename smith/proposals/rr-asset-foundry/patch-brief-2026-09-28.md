# Patch brief: rr-asset-foundry 0.0.0 (2026-09-28)

Rules: stage first (`ship.py stage SKILL`), edit only the staged copy; one cluster per change; write the regression check first and see it fail (or, for a claimed fix, pass), then make the smallest fix; no new features; SKILL.md may grow by 5 lines at most; then `ship.py propose`. Owner approves before anything ships.

## P1 No path for jobs with several deliverables (screens, variants, effects, looks) (rr-asset-foundry/multi-deliverable, n=2, open 0, sev M)
Fix hint: Accept a list of names end to end (render, sheet, crit, export) and test it with 2+ items.
Web-wide (also rr-ui-foundry, rr-vfx-lighting): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [M] t:rr-asset-foundry#F4 (claimed): one POV stand only (need = pov3p, game, pov1p, 34, side, end) :: (need = pov3p, game, pov1p, 34, side, end). multiuse-critic 3d-pipeline.md: "If the camera or the world moves ..., render 2-3 POV positions along the path"; the foundry's own brief says the world scrolls (D-002)
- [M] t:rr-asset-foundry#F5 (claimed): SKILL.md has no route to a variant sheet for variants made one by one :: `sheet` needs a batch folder (batch.json). The only documented route, `batch wagon --vary preset=open_coal,box_van,flat_crates` (dry run), would: - rebuild all three as WagonOpenCoalV001-V003 under batch-WagonOpenCoal (n
Files: scripts/foundry.py, SKILL.md
Check to add (evals/evals.json "checks"): {"id": "fr-multi-deliverable", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-asset-foundry#F4", "t:rr-asset-foundry#F5"]}

## P2 A checker measures the wrong thing (rr-asset-foundry/wrong-measure, n=1, open 0, sev H)
Fix hint: Measure the delivered result (per piece / per frame) and plant a known-bad case in the selftest.
Web-wide (also rr-game-feel, rr-release-train, rr-soundsmith): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [H] t:rr-asset-foundry#F1 (claimed): the A5 "key features >= 5 px at game distance" check measures the wrong thing, so it can never warn and facts.md tells t :: te of the truth. - It takes max(w, h) of a whole part's bounding box ("Largest projected side"); multiuse-critic rubric A5 and 3d-pipeline.md judge the smaller dimension. Parts hold several pieces in one mesh (WagonOpenC
Files: scripts/fkit.py
Check to add (evals/evals.json "checks"): {"id": "fr-wrong-measure", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-asset-foundry#F1"]}

## P3 Canon writes lack a dry-run or sandbox route (trials, parallel lanes) (rr-asset-foundry/canon-writes, n=1, open 0, sev H)
Fix hint: Name `bible.py ... --dry-run` plus the OQ-TBD-<slug> placeholder rule in the one step that records canon.
Web-wide (also rr-data-and-money, rr-game-feel, rr-soundsmith, rr-ui-foundry, rr-vfx-lighting): the shared part belongs in rr-bible; reference it, do not copy it.
Evidence:
- [H] t:rr-asset-foundry#F2 (claimed): families/wagon.py VIEW["player"] + pov() = _rolling.pov_next_vehicle :: the wagon's player view contradicts canon, and the crit brief and POV renders inherit it. - The family says "Players ride the train and never leave it: they see a wagon from the next vehicle's end platform or roof"; POV 
Files: families/wagon.py, SKILL.md
Check to add (evals/evals.json "checks"): {"id": "fr-canon-writes", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-asset-foundry#F2"]}

