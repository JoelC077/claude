# Patch brief: rr-release-train 0.0.0 (2026-09-28)

Rules: stage first (`ship.py stage SKILL`), edit only the staged copy; one cluster per change; write the regression check first and see it fail (or, for a claimed fix, pass), then make the smallest fix; no new features; SKILL.md may grow by 5 lines at most; then `ship.py propose`. Owner approves before anything ships.

## P1 A checker measures the wrong thing (rr-release-train/wrong-measure, n=2, open 0, sev H)
Fix hint: Measure the delivered result (per piece / per frame) and plant a known-bad case in the selftest.
Web-wide (also rr-asset-foundry, rr-game-feel, rr-soundsmith): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [H] t:rr-release-train#1 (claimed): G9 misses placeholder asset ids :: The shipped HUD module has `Hud.IconSheet = "rbxassetid://0"` and `Hud.HazardTile = "rbxassetid://0"` (NotificationHud.lua:17-18; ASSETS.md: "asset ids are placeholders until you do this"; canon `assets.missions.hud_pack
- [H] t:rr-release-train#2 (claimed): G9 misses a demo script left in the build :: `StarterPlayer/StarterPlayerScripts/NotificationDemo.client.lua` (ASSETS.md: "Studio test; delete for release") fires every alert type at every player on join. Extracted by attach, not flagged by any gate. Needs: flag sc
Files: scripts/gates.py:492, scripts/placefile.py:400
Check to add (evals/evals.json "checks"): {"id": "fr-wrong-measure", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-release-train#1", "t:rr-release-train#2"]}

## P2 Open-question ids collide, go stale or are hard-coded (rr-release-train/oq-ids, n=2, open 0, sev H)
Fix hint: Cite OQ ids read at run time (`bible get questions --json`), check the title matches, never keep an OQ list in code.
Web-wide (also rr-asset-foundry, rr-data-and-money, rr-game-feel, rr-soundsmith): the shared part belongs in rr-bible; reference it, do not copy it.
Evidence:
- [H] t:rr-release-train#3 (claimed): G10 filters open questions by keyword, not by what ships :: It listed OQ-019 (marketing budget) and OQ-024 (launch player cap) but not OQ-001 (HUD skin: `blocks: final HUD export`; canon default is C hybrid, this build ships A heritage brass) nor OQ-015 (Main Hall: where, and doe
- [H] t:rr-release-train#4 (claimed): Owner-named version vs channel has no path :: Task/owner named "v0.4.0"; history is empty so `rel version` proposed 0.1.0-alpha.1; `--set 0.4.0` only warns "does not carry the 'alpha' tag" and G1 WARNs. SKILL.md says "`--set` only when the owner names one" but not w
Files: SKILL.md
Check to add (evals/evals.json "checks"): {"id": "fr-oq-ids", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-release-train#3", "t:rr-release-train#4"]}

## P3 Silent success or false PASS hides a problem (rr-release-train/silent-pass, n=2, open 0, sev H)
Fix hint: Fail loudly (non-zero exit, named item) and add the case to the selftest.
Web-wide (also rr-data-and-money, rr-exploit-guard, rr-game-feel, rr-soundsmith, rr-ui-foundry, rr-vfx-lighting): reuse the same fix pattern; check their claimed fixes first.
Evidence:
- [H] t:rr-release-train#5 (claimed): G2 passes on the agent's word :: `mark --in-build yes` needs no owner citation (unlike approve/evidence), so G2 PASSed "2 in build" although the owner never confirmed either mission is in Studio (I marked them from the release name, trial assumption). S
- [M] t:rr-release-train#10 (claimed): G9 audio extra check is a false WARN :: rr-soundsmith `sound validate --release` "FAILED" on library-level feel-parity notes ("ui_button_press exists in rr-game-feel without a cue") though the places hold 0 Sound instances; GATES.md truncates it mid-sentence (
Files: SKILL.md, presets/gates.json
Check to add (evals/evals.json "checks"): {"id": "fr-silent-pass", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-release-train#5", "t:rr-release-train#10"]}

