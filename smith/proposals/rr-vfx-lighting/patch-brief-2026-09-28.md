# Patch brief: rr-vfx-lighting 0.0.0 (2026-09-28)

Rules: stage first (`ship.py stage SKILL`), edit only the staged copy; one cluster per change; write the regression check first and see it fail (or, for a claimed fix, pass), then make the smallest fix; no new features; SKILL.md may grow by 5 lines at most; then `ship.py propose`. Owner approves before anything ships.

## P1 Silent success or false PASS hides a problem (rr-vfx-lighting/silent-pass, n=3, open 2, sev H)
Fix hint: Fail loudly (non-zero exit, named item) and add the case to the selftest.
Web-wide (also rr-data-and-money, rr-exploit-guard, rr-game-feel, rr-release-train, rr-soundsmith, rr-ui-foundry): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [M] t:rr-vfx-lighting#2 (open): No rule for requests that name effects or looks the pack lacks :: "brake sparks" and "dusk" have no preset or time (pack has `sparks_axle`, `sparks_powerbox`, `golden`). SKILL.md never says whether to map to the nearest preset or author a new one, nor how to add a new anchor/time (pres
- [H] t:rr-vfx-lighting#4 (claimed): `vfx preview all [NAMES]` silently ignores NAMES :: preview.py `lighting()` uses `a.names` only when `a.what == "lighting"`, `effects()` only when `== "vfx"`. So step 3's `preview all` always renders the 8 default looks + every preset, and a new look (dusk, not in `previe
- [L] t:rr-vfx-lighting#15 (open): New effect/look authoring is undocumented :: Adding an anchor (`stand.anchors`), a time (`times` + `biomes[b].times`) and budget sets for the new preset (`budgets.json` sets) all worked, but presets.md never lists this checklist; the budget sets would silently omit
Files: SKILL.md, references/presets.md, scripts/preview.py, presets/budgets.json
Check to add (evals/evals.json "checks"): {"id": "fr-silent-pass", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-vfx-lighting#2", "t:rr-vfx-lighting#4", "t:rr-vfx-lighting#15"]}

## P2 No path for jobs with several deliverables (screens, variants, effects, looks) (rr-vfx-lighting/multi-deliverable, n=2, open 0, sev M)
Fix hint: Accept a list of names end to end (render, sheet, crit, export) and test it with 2+ items.
Web-wide (also rr-asset-foundry, rr-ui-foundry): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [M] t:rr-vfx-lighting#6 (claimed): No single board for a mixed pack :: The skill yields `lighting/contact.png` and `vfx/contact.png` and says to run one CRIT per group; an effects+looks pack (the usual owner request) needs one board and one critic. Workaround: `contact_sheet.py` by hand + `
- [L] t:rr-vfx-lighting#14 (claimed): Export is always the whole library :: No subset/pack build: the owner asking for 4 effects + 3 looks gets 13 presets and 19 looks; pack wiring had to be written by hand (`PACK.md`)
Check to add (evals/evals.json "checks"): {"id": "fr-multi-deliverable", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-vfx-lighting#6", "t:rr-vfx-lighting#14"]}

## P3 Workflow tells missions to edit the shared skill instead of a mission copy (rr-vfx-lighting/edits-skill, n=1, open 0, sev M)
Fix hint: Default every write to the mission copy (env override such as RR_<X>_PRESETS); the skill folder is read-only at run time.
Web-wide (also rr-data-and-money, rr-soundsmith, rr-ui-foundry): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [M] t:rr-vfx-lighting#1 (claimed): Step 1 edits the skill's own presets :: Outside a mission, SKILL.md step 1 says "Pick or edit presets in `<fx>/presets/`": a standalone request would modify the shipped skill folder. Only the "Inside a mission" section says to copy `presets/` and set `RR_VFX_P
Files: SKILL.md
Check to add (evals/evals.json "checks"): {"id": "fr-edits-skill", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-vfx-lighting#1"]}

