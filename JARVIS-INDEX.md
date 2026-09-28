# JARVIS index (Risky Rails skill web), 2026-09-28

## Skills

| skill | what it does | when it fires | depends on | trial review scores (pre-fix) | independent certification (fixed re-trial) |
|---|---|---|---|---|---|
| rr-mission-control | Front door and router. Classifies a request as a light answer, a single skill or a mission, then chains sub-skills and keeps mission state | FIRST for any Risky Rails or Roblox game-dev prompt, including terse ones that never name the game | every skill below | routing eval 17/28 (simulated) before this fix | n/a |
| rr-bible | Canon store: facts, hex tokens, decisions, open questions; get/export/check | Called by MC and all rr-* skills; directly only when named | none | selftest 39/39 | n/a |
| rr-asset-foundry | Parametric Blender families to Roblox-ready variants (atlas, LOD, FBX) | Via MC (asset requests); direct only when named | rr-bible, multiuse-critic | 7, 6.5 | **7** (3 blocks-8) |
| rr-vfx-lighting | Particle, beam, light and Lighting/Atmosphere preset packs, JSON to Luau | Via MC | rr-bible, multiuse-critic | 5, 6 | **4** (9 blocks-8) |
| rr-game-feel | Juice runtime: tweens, shake, hit-stop, UI punch, haptics, lever feel | Via MC | rr-bible | 7, 6.5 | **4** (9 blocks-8) |
| rr-ui-foundry | JSON screen spec to critic boards and a Luau UI package | Via MC | rr-bible, multiuse-critic | not recorded | **7** (6 blocks-8) |
| rr-soundsmith | Event-to-sound map, mix ladder, file measuring, licence gate | Via MC, or when audio files are dropped in | rr-bible | 7, 6.5 | **5** (10 blocks-8) |
| rr-exploit-guard | Luau security scan, fix patterns, PASS/HOLD/FAIL gate | Via MC or rr-release-train | rr-bible | 7, 6 | security reviews: vuln corpus FAIL correctly (19 blockers); fixed corpus 1 blocker left (R10 no session lock) |
| rr-release-train | Semver, changelog, patch notes, gates, dry-run publish plan, rollback | Via MC as the final gate | rr-exploit-guard, rr-bible, multiuse-critic | 7, 6 | release trial: 2 confirmed blockers |
| rr-data-and-money | Analytics plan, dashboard memo, A/B stats, prices, economy sim, money gate | Via MC | rr-bible | 6.5, 6 | n/a |
| multiuse-critic | Independent rubric critic (overall = lowest criterion), fix and re-check loop | Chained by MC after builds; direct when named or for non-RR designs | none | n/a | n/a |
| rr-skill-smith | Harvests frictions, drafts skill patches, regression evals, web health report | When asked to improve or fix skills, or for "web health" | all skills | selftest 73/73 | n/a |
| risky-rails-mechanic-reviewer (installed) | Reviews a mechanic idea against design rules | Chained by MC | none | n/a | n/a |
| risky-rails-thumbnail-ideas (installed) | Thumbnail and icon concepts | Chained by MC, then critic | multiuse-critic | n/a | n/a |

No certified score reaches the 8/10 bar (D-020) yet.

## How auto-activation works

Claude reads every skill's description and loads the best match. MC's description claims every Risky Rails prompt, and each sub-skill's description now says to go to MC first unless the sub-skill is named. The installed risky-rails-* skills could not be edited, so MC's description names thumbnail ideas and "what if" mechanic ideas as its own. A real `claude -p` trigger test still loads MC for only 2 of 24 prompts (see limits), so turn on the always-on line.

**One-line always-on setup** (claude.ai Settings > Profile preferences, or a Project's instructions):

    For any Risky Rails or Roblox game-dev work, start with the rr-mission-control skill (JARVIS) and let it choose and chain the sub-skills; answer small questions via rr-bible without mission files.

Claude Code alternative: jarvis-setup/CLAUDE.md.snippet or the hook (jarvis-setup/HOOK-INSTALL.md).

## Install order

Use Save skill on each dist/*.skill, in this order:
1. multiuse-critic
2. rr-bible
3. rr-asset-foundry, rr-vfx-lighting, rr-game-feel, rr-ui-foundry, rr-soundsmith, rr-exploit-guard, rr-release-train, rr-data-and-money, rr-skill-smith (any order)
4. rr-mission-control (last)

## Owner decisions waiting

Bible lint: 734 facts, 56 open questions, 22 decisions, 50 sources. OQ-037, OQ-041 and OQ-042 id collisions from the sandbox lanes were renumbered to new ids. Every question below has a default, and it is used until you decide.

| id | question | default |
|---|---|---|
| OQ-043 | Hard brake: what fires it and how hard is it? | A: one hard_brake event, about 2x the arrival brake |
| OQ-044 | Lobby audio: music or diegetic ambience? | A: diegetic bed, no music |
| OQ-045 | Where do freight wagons appear? | A: yard dressing on the sidings |
| OQ-046 | Create match: what do the Players chips pick? | A: party size 1/2/3 |
| OQ-047 | HUD: one expanded slot, or two? | A: keep canon compact_rule |
| OQ-048 | Crew fare: full for each member, or split? | A: each banks the full fare |
| OQ-049 | Starting coins | B: welcome grant of about 100 |
| OQ-050 | Base fare per run by difficulty | A: 1,700 / 2,100 / 2,650 / 3,300 |
| OQ-051 | Largest fare pack vs the 10-runs cap | A: smallest change |
| OQ-052 | Loco 3-5 and Line 2 prices | A: one loco about every 2 h |
| OQ-053 | Auto Stoker pass vs D-007 | A: do not sell (pay-to-win) |
| OQ-054 | Conductor's Toolbelt +2 slots vs D-007 | A: do not sell |
| OQ-055 | Who pays for a crew supply order? | A: the player who orders |
| OQ-056 | Bring one 49 R$ identity item forward to launch? | B: keep it post-launch |

Also still open: OQ-001 HUD skin and OQ-002 company name. For the full list run `bible.py get questions`.

## Owner setup for full power

- Open Cloud API key, stored as an environment secret, with apis.roblox.com allowed in network access. Needed for real publishes. rr-release-train still waits for your typed confirm.
- Roblox Studio MCP, so Claude can apply and inspect things in Studio.
- A Rojo repo of the game, so exploit-guard, release-train and the UI and feel packages work on real code.

## Honest limits

- Nothing has been tested in Roblox Studio yet. All Luau was checked only by offline luatest parity checks and selftests.
- The cloud session cannot reach apis.roblox.com.
- Certified scores are 4 to 7. None meets the 8/10 bar.
- In the real CLI trigger test, rr-mission-control loaded for 2 of 24 Risky Rails prompts, both before and after this fix, with 1 run per query. It had no false triggers (0 of 4), but `claude -p` tends to answer short prompts without loading any skill. The always-on line is what makes routing reliable.
