# Orchestrated critic loop (default for workflow / cloud runs)

Use when the mission lead cannot spawn agents (`env.critic_mode=handoff`) or when an orchestrator/workflow drives the mission. Measured: leads that self-scored "reached 8" failed grading; the same missions with fresh critics per pass landed at 7-8 honestly.

Loop, one pass per round (cap 5 passes):
1. **Prep (lead):** build/fix, pre-flight, `critic_kit.py build <CRIT> pass-N` (must exit 0), write `<CRIT>/pass-N/critic.md` = the critic order (brief + rubric profile + bar + kind full|delta|final + "write verdict.md here, overall = lowest criterion"). `mission_state.py next <M> "critic pass N: <CRIT>/pass-N/critic.md"`. Return that path and stop.
2. **Fresh critic (orchestrator):** spawn a NEW agent on the strongest model with only critic.md and the pass folder. It never sees the maker's context, earlier self-assessments or build scripts. Fresh every pass is fine (continuation is a token optimisation, not a requirement); the final pass is always fresh.
3. **Maker (lead, resumed):** read verdict.md, check it (critic step 6), log with `mission_state.py step <M> 7|8 "<scores>" --tokens N [--est]`, apply the ranked fixes, go to 1.
Stop: every criterion >= bar in a fresh final pass, or the cap / a stop rule (report the real scores, e.g. "7/10, B6 short: <reason>").

Orchestrator contract: pass the lead the verdict path and nothing else; do not paraphrase or soften scores; never let the lead write verdict.md.
