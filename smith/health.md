# JARVIS web health (2026-09-28T05:56Z)

6 critical, 5 warning, 3 good; 185 friction items from 10 logs; snapshot 2.

| skill | status | ver | critic | evals | trig | drift E/W | frictions open (H) +claimed | SKILL.md tok | next |
|---|---|---|---|---|---|---|---|---|---|
| multiuse-critic | warning | unversioned | - | 6/6 | 100% | 0/0 | 9 (0H) +0c | 4331 | harvest.py patch multiuse-critic |
| risky-rails-mechanic-reviewer | good | unversioned | - | - | - | 0/0 | 0 (0H) +0c | 973 | installed copy: fix at its source |
| risky-rails-thumbnail-ideas | warning | unversioned | - | - | - | 0/1 | 0 (0H) +0c | 6160 | installed copy: fix at its source |
| rr-asset-foundry | warning | unversioned | 7 | 6/6 | 100% | 0/0 | 0 (0H) +12c | 3095 | bar loop: fix verdict issues, fresh critic |
| rr-bible | good | unversioned | - | 9/9 | 100% | 0/0 | 0 (0H) +0c | 2156 | - |
| rr-data-and-money | warning | unversioned | rev 6 | 7/7 | 89% | 0/4 | 0 (0H) +23c | 3175 | add evals that prove the claimed High fixes |
| rr-exploit-guard | critical | unversioned | missed 8 (2H) | 7/7 | 88% | 0/1 | 11 (0H) +18c | 3305 | harvest.py patch rr-exploit-guard |
| rr-game-feel | critical | unversioned | 4 | 6/6 | 100% | 0/7 | 5 (0H) +12c | 2904 | harvest.py patch rr-game-feel |
| rr-mission-control | critical | unversioned | 7 | 7/7 | 100% | 0/4 | 27 (1H) +0c | 3874 | harvest.py patch rr-mission-control |
| rr-release-train | warning | unversioned | rev 6 | 5/5 | 89% | 0/0 | 6 (0H) +14c | 2933 | add evals that prove the claimed High fixes |
| rr-skill-smith | good | 1.0.0 | - | 6/6 | 100% | 0/0 | 0 (0H) +0c | 1573 | - |
| rr-soundsmith | critical | unversioned | 5 | 6/6 | 100% | 0/0 | 0 (0H) +15c | 2942 | bar loop: fix verdict issues, fresh critic |
| rr-ui-foundry | critical | unversioned | 7 | 6/6 | 88% | 0/2 | 13 (3H) +0c | 2757 | harvest.py patch rr-ui-foundry |
| rr-vfx-lighting | critical | unversioned | 4 | 7/7 | 88% | 0/2 | 4 (0H) +12c | 2860 | harvest.py patch rr-vfx-lighting |

## Web-wide recurring problems (fix once, in the owning skill)
- Silent success or false PASS hides a problem [silent-pass]: 7 skills, 13 items. Fix: Fail loudly (non-zero exit, named item) and add the case to the selftest.
- Critic independence and route when no Agent tool (self-review, remote, handoff) [critic-route]: 6 skills, 12 items. Fix: One probe order in rr-mission-control, referenced (not restated) by every maker skill; never certify self scores.
- Canon writes lack a dry-run or sandbox route (trials, parallel lanes) [canon-writes]: 6 skills, 6 items. Fix: Name `bible.py ... --dry-run` plus the OQ-TBD-<slug> placeholder rule in the one step that records canon.
- Generated critic brief is generic instead of job-specific [generic-brief]: 6 skills, 7 items. Fix: Fill Purpose/audience from the job (mission R-lines or --purpose), and refuse a brief that still holds a placeholder.
- Open-question ids collide, go stale or are hard-coded [oq-ids]: 5 skills, 8 items. Fix: Cite OQ ids read at run time (`bible get questions --json`), check the title matches, never keep an OQ list in code.
- Critic evidence misses part of the deliverable (one close-up, hero only, no tiles) [critic-evidence]: 5 skills, 7 items. Fix: Let the brief carry every deliverable (or a second evidence sheet) and label tiles; add an eval that counts deliverables vs tiles.
- Skill values contradict canon (numbers, gauge, colours, strings) [canon-drift]: 4 skills, 6 items. Fix: Read the value from rr-bible at run time (key cited), and add a drift.py check or a `check:` regex to the fact.
- A checker measures the wrong thing [wrong-measure]: 4 skills, 5 items. Fix: Measure the delivered result (per piece / per frame) and plant a known-bad case in the selftest.
- Workflow tells missions to edit the shared skill instead of a mission copy [edits-skill]: 4 skills, 4 items. Fix: Default every write to the mission copy (env override such as RR_<X>_PRESETS); the skill folder is read-only at run time.
- Scripts leave __pycache__ in the skill folder [pycache]: 4 skills, 4 items. Fix: Put `import sys; sys.dont_write_bytecode = True` before local imports in every entry script; add a hygiene eval.
- Tool missing in the cloud image; no documented fallback [toolchain]: 3 skills, 4 items. Fix: Name the cloud fallback (and its limits) next to the preferred tool.
- No path for jobs with several deliverables (screens, variants, effects, looks) [multi-deliverable]: 3 skills, 5 items. Fix: Accept a list of names end to end (render, sheet, crit, export) and test it with 2+ items.
- Output or docs spend tokens for nothing [token-sink]: 3 skills, 4 items. Fix: Print a summary by default (--full for the rest); read slices, not whole files.
- Workspace root or path convention is ambiguous [roots]: 2 skills, 4 items. Fix: One env var + flag per root, recorded in state; resume reads it back.
- Owner-away or gated-run behaviour undefined [owner-away]: 2 skills, 3 items. Fix: State the default (proceed on best match, persist questions to the mission file, mark fallback).
- Token or cost numbers are estimated but not labelled [cost-accounting]: 2 skills, 2 items. Fix: Label every non-measured token figure est. in ledgers and debriefs (a flag on the logging command).
- Relative paths leak into prompts and handoffs [relative-paths]: 2 skills, 2 items. Fix: Resolve every path to absolute before printing it into a spawn prompt or brief.

## Open High frictions
- m:260927-depot-buildings#9 (rr-mission-control): BLOCKER: the run brief said "You have the Agent tool" and critic passes MUST be independent subagents, but this subagent
- t:rr-ui-foundry#1 (rr-ui-foundry): BUILD PASS can't be reached for any lobby spec that differs from the shipped example: 2 false FAILs in luatest
- t:rr-ui-foundry#2 (rr-ui-foundry): Notched phones fall below canon minimums while validate still passes
- t:rr-ui-foundry#3 (rr-ui-foundry): A kit job covering 2 or more screens has no path through render and crit

## Contract drift (21 ERROR/WARN; first 15)
- WARN risky-rails-thumbnail-ideas SKILL.md:81 22 canon colour(s) restated in instructions: #15171C=style.brand.ink, #E23A2E=style.brand.danger_red, #F2C230=style.bran
- WARN rr-data-and-money presets/economy.json:45 hard-coded OQ list (4 ids)
- WARN rr-data-and-money presets/economy.json:65 OQ-052 cited for '{"id": "loco_4", "price": {"v": 12000, "assumed": "about 2 h later; OQ' but it is 'Locomotive 3-5 and 
- WARN rr-data-and-money references/economy-model.md:30 `economy.currency.float` is superseded
- WARN rr-data-and-money scripts/econ.py:337 `economy.currency.float` is superseded
- WARN rr-exploit-guard references/fixes.md:119 OQ-010 cited for '`NotProcessedYet` when the player, the profile or the grant is missing' but it is 'Robux in the supply
- WARN rr-game-feel SKILL.md:30 OQ-TBD placeholder not reconciled
- WARN rr-game-feel references/schema.md:15 OQ-TBD placeholder not reconciled
- WARN rr-game-feel references/schema.md:73 OQ-TBD placeholder not reconciled
- WARN rr-game-feel scripts/feel.py:476 OQ-TBD placeholder not reconciled
- WARN rr-game-feel scripts/feel.py:492 OQ-TBD placeholder not reconciled
- WARN rr-game-feel scripts/feel.py:787 OQ-TBD placeholder not reconciled
- WARN rr-game-feel scripts/feel.py:1080 hard-coded OQ list (4 ids)
- WARN rr-mission-control references/examples/mission-p1.md:39 8 canon colour(s) restated in instructions: #9A9384=style.depot_kit.stone, #7D776B=style.depot_kit.stone_dark, #CABB8A=s
- WARN rr-mission-control references/roblox-export.md:11 1 canon colour(s) restated in instructions: #9A9384=style.depot_kit.stone

Reasons per skill: health.json rows[].reasons. Detail: harvest.py clusters --skill S; drift.py S; evals.py run S -v.
