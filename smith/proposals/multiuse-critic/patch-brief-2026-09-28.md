# Patch brief: multiuse-critic 0.0.0 (2026-09-28)

Rules: stage first (`ship.py stage SKILL`), edit only the staged copy; one cluster per change; write the regression check first and see it fail (or, for a claimed fix, pass), then make the smallest fix; no new features; SKILL.md may grow by 5 lines at most; then `ship.py propose`. Owner approves before anything ships.

## P1 Output or docs spend tokens for nothing (multiuse-critic/token-sink, n=1, open 1, sev M)
Fix hint: Print a summary by default (--full for the rest); read slices, not whole files.
Web-wide (also rr-release-train, rr-soundsmith): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [M] m:260927-depot-buildings#4 (open): Brief format (step 3) requires multiuse-critic's format, but rr-mission-control says "Read a reference only at the step  :: (step 3) requires multiuse-critic's format, but rr-mission-control says "Read a reference only at the step that names it" while the brief format lives in the critic SKILL.md (steps 1-2), which step 3 does not name. Had t
Files: SKILL.md
Check to add (evals/evals.json "checks"): {"id": "fr-token-sink", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["m:260927-depot-buildings#4"]}

## P2 Critic independence and route when no Agent tool (self-review, remote, handoff) (multiuse-critic/critic-route, n=1, open 1, sev M)
Fix hint: One probe order in rr-mission-control, referenced (not restated) by every maker skill; never certify self scores.
Web-wide (also rr-exploit-guard, rr-game-feel, rr-mission-control, rr-release-train, rr-soundsmith): the shared part belongs in rr-mission-control; reference it, do not copy it.
Evidence:
- [M] m:260927-depot-buildings#13 (open): critic_kit.py log --tokens semantics: for a continued agent it expects cumulative carried tokens and subtracts; for self :: agent context, so "new this pass" numbers are fiction. Self-review needs its own ledger mode
Files: scripts/critic_kit.py
Check to add (evals/evals.json "checks"): {"id": "fr-critic-route", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["m:260927-depot-buildings#13"]}

## P3 Critic evidence misses part of the deliverable (one close-up, hero only, no tiles) (multiuse-critic/critic-evidence, n=1, open 1, sev M)
Fix hint: Let the brief carry every deliverable (or a second evidence sheet) and label tiles; add an eval that counts deliverables vs tiles.
Web-wide (also rr-game-feel, rr-mission-control, rr-soundsmith, rr-vfx-lighting): this skill owns the shared fix; make it once so the others can cite it.
Evidence:
- [M] m:260927-depot-buildings#14 (open): Maker template says makers "never read the critic pipeline docs", but the pipeline doc has the contact-sheet layout, ren :: the maker must produce; I (orchestrator) had to read 3d-pipeline.md anyway to write correct orders
Files: references/3d-pipeline.md
Check to add (evals/evals.json "checks"): {"id": "fr-critic-evidence", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["m:260927-depot-buildings#14"]}

