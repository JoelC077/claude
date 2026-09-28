# Formats the smith reads and writes

## Friction logs (what missions and trials should leave)

Where: `<mission>/SKILL-FRICTION.md` or `trials/<skill>/FRICTION.md` (any `*FRICTION*.md` under a missions root or `trials/` is harvested). First line names the skills used, e.g. `# SKILL-FRICTION (rr-mission-control + multiuse-critic), mission 260930-signal-box`.

Preferred item (one per line, continuation lines indented or plain):

```
3. [H] scripts/preview.py lighting() — `preview all NAMES` ignores NAMES — evidence: facts.md lists 13 presets for 2 names
```

Severity: H = wrong output or blocks the ask, M = extra work or tokens, L = polish. Also parsed: `F4 [H] ...`, `## F4 · title (M)`, `N. **H: title.** body`, tables with a `Sev` column, `- [M, open] ...` bullets, `## High` / `## Medium` / `## Low` sections. Sections named "What worked", "Run log" or "Results" are skipped; "Environment" items get status env. Mark a fixed item `[H, fixed]` in the log, or say so in the trial's REPORT.md ("All high and medium findings are applied", or cite `F4`); lines in a "Rejected / partial" section mark items partial.

Attribution: a trial item belongs to its trial's skill; a mission item to the first skill (or unique script/reference name, e.g. `critic_kit.py`) it mentions, else the first skill in the header. Other skills mentioned are listed as `also`.

## Scores and costs

- Critic: `pass-N/verdict.md` (`SCORES` lines, `OVERALL: N`; "SELF-ASSESSED" marks self scores) and `ledger*.json` (critic_kit: scores, tokens, new). Overall = lowest criterion.
- Security: review `verdict.md` with `Rnn | SAFE|VULN|UNSURE` rows and `NEW:` lines (issues the scanner missed; `| high |` counts as High).
- Reviews: `REPORT.md` "Review scores ... [7, 6.5]".
- Cost: ledger `new` tokens (critic), mission `state.json` `tokens` (estimates unless measured).

## Proposal and changelog

`ship.py propose` writes `<home>/proposals/S-VERSION.md` (summary, evals, files, fixes, changelog entry, diff) and `.json` (tree hash of the candidate: apply refuses if it changed). CHANGELOG entry:

```
## [1.1.0] - 2026-09-30
### Fixed
- preview honours NAMES; unknown names exit 2 (fixes t:rr-vfx-lighting#4)
Evals: PASS checks 9/9, triggers 8/8; approved: owner 2026-09-30 via chat
```

## Themes (`assets/themes.json`)

`{"id", "title", "any": [regex, ...], "fix": "one minimal change"}`. An item's theme is the one with the most hits (title hits count double). Clusters = (skill, theme); a theme present in 2+ skills is web-wide and ranks higher.
