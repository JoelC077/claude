# Patch brief: rr-mission-control 0.0.0 (2026-09-28)

Rules: stage first (`ship.py stage SKILL`), edit only the staged copy; one cluster per change; write the regression check first and see it fail (or, for a claimed fix, pass), then make the smallest fix; no new features; SKILL.md may grow by 5 lines at most; then `ship.py propose`. Owner approves before anything ships.

## P1 Critic independence and route when no Agent tool (self-review, remote, handoff) (rr-mission-control/critic-route, n=4, open 4, sev H)
Fix hint: One probe order in rr-mission-control, referenced (not restated) by every maker skill; never certify self scores.
Web-wide (also multiuse-critic, rr-exploit-guard, rr-game-feel, rr-release-train, rr-soundsmith): this skill owns the shared fix; make it once so the others can cite it.
Evidence:
- [H] m:260927-depot-buildings#9 (open): BLOCKER: the run brief said "You have the Agent tool" and critic passes MUST be independent subagents, but this subagent :: ent/Task tool (only SendMessage via ToolSearch; ToolSearch "select:Agent" returned nothing). rr-mission-control's fallback ("self-review, labelled self-assessed") was followed, so every critic score in this mission is SE
- [M] m:260927-depot-buildings#18 (open): Step 1 "env probe: Agent tool present?" is recorded as a state flag but nothing downstream checks it; I initially record :: om the run brief before discovering the tool was absent at step 5. The probe should be an actual tool check, run before the plan (plan.py estimated maker/critic subagent costs that never happened)
- [M] m:260927-ticket-hud#2 (open): No Agent tool in this session's toolset (only SendMessage/ListAgents via ToolSearch; ToolSearch "select:Agent" returned  :: (only SendMessage/ListAgents via ToolSearch; ToolSearch "select:Agent" returned nothing). The skill assumes Agent exists (steps 5, 7-8, rule 3/5) and its only fallback is "self-review ... labelled self-assessed". The tas
- [M] m:260927-ticket-hud#10 (open): Final pass requires "a fresh critic on the strongest model"; with no Agent tool it collapses into the same self-reviewer :: ement" gate is meaningless. The skill should either block the 8/10 claim or require an alternative independent reviewer (e.g. remote session)
Files: scripts/plan.py
Check to add (evals/evals.json "checks"): {"id": "fr-critic-route", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["m:260927-depot-buildings#9", "m:260927-depot-buildings#18", "m:260927-ticket-hud#2", "m:260927-ticket-hud#10"]}

## P2 Workspace root or path convention is ambiguous (rr-mission-control/roots, n=3, open 3, sev M)
Fix hint: One env var + flag per root, recorded in state; resume reads it back.
Web-wide (also rr-release-train): this skill owns the shared fix; make it once so the others can cite it.
Evidence:
- [M] m:260927-depot-buildings#1 (open): Mission root: skill says `<R>` = `<project>/.rr-missions` or `~/.rr-missions`; this run was told `/home/user/claude/miss :: Skill has no override flag for `<R>`; `mission_state.py resume` defaults to ~/.rr-missions so a resume would miss this mission unless ROOT is passed. Stored env.root in state as a workaround
- [M] m:260927-ticket-hud#1 (open): Missions root: SKILL says `<R>` = `<project>/.rr-missions` or `~/.rr-missions`; this run's harness required /home/user/c :: ssion_state.py resume` defaults to ~/.rr-missions, so a resumed session will not find this mission without passing the root. Evidence: SKILL.md "Paths" + mission_state.py usage
- [M] m:260927-ticket-hud#13 (open): Step 10 says memory goes to `<R>/memory/`; with the harness root override it is ambiguous; wrote to <M>/memory/ to stay  :: older
Files: scripts/mission_state.py, SKILL.md
Check to add (evals/evals.json "checks"): {"id": "fr-roots", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["m:260927-depot-buildings#1", "m:260927-ticket-hud#1", "m:260927-ticket-hud#13"]}

## P3 Owner-away or gated-run behaviour undefined (rr-mission-control/owner-away, n=2, open 2, sev M)
Fix hint: State the default (proceed on best match, persist questions to the mission file, mark fallback).
Web-wide (also rr-asset-foundry): this skill owns the shared fix; make it once so the others can cite it.
Evidence:
- [M] m:260927-depot-buildings#3 (open): Owner-away mode: skill says "Proceeding on defaults" but never says where the readback goes when nobody reads chat, nor  :: ust be persisted. Wrote them into mission.md Q-lines
- [M] m:260927-ticket-hud#4 (open): Rule "A question blocks only if a wrong guess wastes most of the work (e.g :: (e.g. which design file)" + owner away: the prototype-identity question is by the skill's own example blocking, but there is no guidance for "owner away, blocking question". Harness overrode: take default. The skill shou
Check to add (evals/evals.json "checks"): {"id": "fr-owner-away", "run": "TODO: command that exposes the problem", "exit": 0, "stdout_has": ["TODO"], "covers": ["m:260927-depot-buildings#3", "m:260927-ticket-hud#4"]}

