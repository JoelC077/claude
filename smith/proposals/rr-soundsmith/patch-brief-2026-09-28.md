# Patch brief: rr-soundsmith 0.0.0 (2026-09-28)

Rules: stage first (`ship.py stage SKILL`), edit only the staged copy; one cluster per change; write the regression check first and see it fail (or, for a claimed fix, pass), then make the smallest fix; no new features; SKILL.md may grow by 5 lines at most; then `ship.py propose`. Owner approves before anything ships.

## P1 Open-question ids collide, go stale or are hard-coded (rr-soundsmith/oq-ids, n=3, open 0, sev H)
Fix hint: Cite OQ ids read at run time (`bible get questions --json`), check the title matches, never keep an OQ list in code.
Web-wide (also rr-asset-foundry, rr-data-and-money, rr-game-feel, rr-release-train): the shared part belongs in rr-bible; reference it, do not copy it.
Evidence:
- [M] t:rr-soundsmith#F2 (claimed): No lobby / queue / results phase in the preset map, schema or SKILL.md (M) :: (M) - Evidence: preset soundmap has 25 sounds and 26 events, none for the Depot Lobby (queue pad join, 15 s countdown `gameplay.run.queue_countdown_s`, launch/teleport `tech.data.launching_lock`, lobby ambience). rr-game
- [M] t:rr-soundsmith#F11 (claimed): Open-decision lists are hard-coded, so new OQs never reach the owner or the critic (M) :: (M) - Evidence: SOUND_SPEC.md "Open decisions" and the critic brief "Owner worries" are fixed strings (sound.py:1059 and :1195) naming OQ-021/035/036 only. OQs cited by sounds (OQ-037 lobby here; also OQ-031, OQ-013, OQ-
- [H] t:rr-soundsmith#F12 (partial): OQ citations are checked for existence only; a sibling's OQ silently took the number (M-H) :: (M-H) - Evidence: the lobby question was OQ-037 in the sandbox (F4). Minutes later rr-release-train added a different OQ-037 ("Release version scheme and channels", src RT) to the real bible. Now `validate --strict` agai
Files: SKILL.md, scripts/sound.py:1059
Check to add (evals/evals.json "checks"): {"id": "fr-oq-ids", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-soundsmith#F2", "t:rr-soundsmith#F11", "t:rr-soundsmith#F12"]}

## P2 Critic independence and route when no Agent tool (self-review, remote, handoff) (rr-soundsmith/critic-route, n=2, open 0, sev M)
Fix hint: One probe order in rr-mission-control, referenced (not restated) by every maker skill; never certify self scores.
Web-wide (also multiuse-critic, rr-exploit-guard, rr-game-feel, rr-mission-control, rr-release-train): the shared part belongs in rr-mission-control; reference it, do not copy it.
Evidence:
- [M] t:rr-soundsmith#F3 (claimed): Critic route is ambiguous for a subagent that also has create_session (M) :: (M) - Where: SKILL.md step 7 "No Agent tool: follow rr-mission-control's critic route". - Evidence: rr-mission-control SKILL.md line 46 orders agent -> remote (create_session) -> handoff. This run has `mcp__Claude_Code_R
- [M] t:rr-soundsmith#F16 (claimed): Handoff mode vs step order (L-M) :: (L-M) - Evidence: step 7 (critic) comes before step 8 (export), and rr-mission-control's handoff route says "return that path and stop". The task needed the Luau export in the same run. SKILL.md does not say whether `bui
Files: SKILL.md, SKILL.md:46
Check to add (evals/evals.json "checks"): {"id": "fr-critic-route", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-soundsmith#F3", "t:rr-soundsmith#F16"]}

## P3 Critic evidence misses part of the deliverable (one close-up, hero only, no tiles) (rr-soundsmith/critic-evidence, n=2, open 0, sev H)
Fix hint: Let the brief carry every deliverable (or a second evidence sheet) and label tiles; add an eval that counts deliverables vs tiles.
Web-wide (also multiuse-critic, rr-game-feel, rr-mission-control, rr-vfx-lighting): the shared part belongs in multiuse-critic; reference it, do not copy it.
Evidence:
- [H] t:rr-soundsmith#F9 (claimed): Critic order promises evidence it does not contain; S5 and S6 cannot be scored (H) :: (H) - Where: `sound crit` + `sound sheet` (facts.md) -> critique-sound/pass-1/critic.md. - Evidence: critic.md line 13 says "Facts has the measurements and the event table"; facts.md has no event table, no brief text and
- [L] t:rr-soundsmith#F17 (claimed): Contact sheet ladder labels collide (L) :: (L) - Evidence: src/sound/sheet/contact.png top axis prints "ambient" (-27) and "music" (-25) as "ambientmusic". - Fix: stagger labels closer than ~40 px
Check to add (evals/evals.json "checks"): {"id": "fr-critic-evidence", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["t:rr-soundsmith#F9", "t:rr-soundsmith#F17"]}

