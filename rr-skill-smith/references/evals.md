# Writing regression evals

File: `<skill>/evals/evals.json` (skill-creator schema plus smith keys; root `evals/` is never packaged).

```json
{"skill_name": "rr-x",
 "budget": {"skill_md_max_lines": 130, "skill_md_max_chars": 13000},
 "triggers": [{"query": "the lever feels floaty, make it snappier", "should_trigger": true},
              {"query": "make brake spark particles", "should_trigger": false}],
 "checks": [{"id": "fr-silent-pass", "run": "python3 {skill}/scripts/x.py preview all a b", "exit": 0,
             "stdout_has": ["a", "b"], "stdout_not": ["Traceback"], "stdout_re": "", "timeout": 120,
             "slow": false, "covers": ["t:rr-x#4"]}],
 "evals": [{"id": 1, "prompt": "...", "expected_output": "...", "expectations": ["..."]}]}
```

## Checks (zero tokens, run on every propose/apply)

- One check per failure mode, named `fr-<theme>` or after the bug; `covers` lists the friction ids it proves.
- Commands run in a fresh temp folder (`{tmp}`, the cwd) with `PYTHONDONTWRITEBYTECODE=1`. Placeholders: `{skill}` (the candidate being tested: stage or live), `{root}`, `{bible}`, `{critic}`, `{home}`. Build fixtures inline (`printf ... > f.lua && ...`).
- A check must fail on the old code and pass on the fix. Write it first; run it against the live skill to see the failure (`evals.py run S --only checks`).
- Assert on behaviour (exit code, named item in the output), not on canon values: `stdout_re` with `\d+` rather than the current number, so a canon change does not break the eval.
- Checks must not write into the skill, the bible, `~/` or the owner's config (hygiene fails on any change to the skill tree; use `--dry-run` routes and `{tmp}`).
- `slow: true` for anything over about 30 s (full selftests); `--quick` skips them while iterating.

## Triggers (lexical proxy, zero tokens)

- 5+ prompts the owner would really type (casual, typos fine) and 3+ near-misses that belong to a sibling skill. Name the sibling in your head: every negative should test one boundary in the description ("Not for ...").
- Do not tune prompts to please the proxy; a miss that also fails at baseline is reported, not blocking. Only regressions block.
- The real test (costs tokens): `evals.py live S` then the printed skill-creator `run_eval` command, `--runs-per-query 1` unless the owner asks for more.

## Model-graded evals (tokens: only when asked)

`evals` items follow skill-creator's schema. `evals.py agent S` writes one brief for one fresh subagent (dry-run rules included); it returns a results JSON; `evals.py record S FILE`. Keep expectations verifiable (a path, a number, a quoted line).

## Budgets and baselines

`budget` caps SKILL.md; without it, growth over 10% vs the baseline fails `lean`. `drift` fails on any ERROR and on more WARN than the baseline. The baseline is the last approved ship (`<home>/baselines/S.json`).
