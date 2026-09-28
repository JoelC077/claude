# Gates and evidence contracts

`rel gate` writes `next/GATES.md` (human) and `next/gates.json` (hash bound into the approval).
Statuses: PASS · WARN · FAIL · PENDING (evidence missing) · WAIVED (owner) · N/A.
Verdict: **NO-GO** on any FAIL, or a PENDING gate in the channel's blocking set; **GO-WITH-WARNINGS** on WARN or a
pending advisory gate; else **GO**. Blocking sets and strictness: `presets/gates.json` (`blocking`, `channels`).
"Soft" problems below are WARN in alpha/beta and FAIL in live.

| gate | reads | FAIL / PENDING when | soft (WARN in alpha/beta) |
|---|---|---|---|
| G1 version | release.json, each place audit's `RR_Version` | not semver, not above history, stamp differs from the version | channel tag missing, no stamp |
| G2 changes | changes | nothing confirmed; unknown in-build (PENDING); version below the needed bump | only script diffs, no player change |
| G3 notes | notes-check.json | not run or stale (PENDING); errors | warnings |
| G4 canon | `bible check` on each place's combined scripts (names, numbers) and props.lua (colours, fonts) | script ERROR (banned name, contradicting number) | off-palette colours/fonts in the place |
| G5 security | SECURITY_GATE.json | missing or older than the attached places (PENDING); verdict FAIL | verdict HOLD |
| G6 tests | evidence `tests`, `bugbash` | test fail; no result and not deferrable (PENDING); bug bash missing on a minor+ release (PENDING) | - |
| G7 perf | audits vs last release, extra checks, evidence `perf`, `livecheck` | owner evidence fail; live check missing on live minor+ (PENDING) | growth > 15%, `vfx budget` over |
| G8 visuals | critic ledgers of in-build missions of kind ui/3d/vfx/thumbnail/design | - | any not certified |
| G9 hygiene | extracted scripts, audit, extra checks | - | `DEBUG`-style flag `= true`, test-looking data store, placeholders, store name differs from canon, `sound validate --release` fails |
| G10 open questions | `bible` OQs whose title or `blocks:` mention release/launch/publish/monetisation | never | always WARN while any is open |

Waivers: `rel waive GN --by owner --reason "..."` (G2-G10; never G1). A G5 waiver is reported in the debrief.

## G6 "deferred"
On the API route with `luau_tests` on (default), tests are not needed before approval: `publish --live` runs
`assets/luau/run_tests.lua` on each **saved** version and refuses to publish on any failure (recorded as evidence
`tests` = fail). On the Studio route the owner runs the same file in Studio (Play Solo, command bar in the server
view; the `[RR tests]` lines in Output are the result), then
`rel evidence tests --result pass --by owner --note "7 tests, stamp 0.1.0-alpha.2"`.

Spec convention (the owner's code): a ModuleScript named `Something.spec` anywhere under ServerScriptService,
ServerStorage or ReplicatedStorage, returning a function or a table of `name = function() assert(...) end`.
No specs yet = `tests 0`; the stamp check still runs. Canon-driven specs worth writing first: the bug bash items
(`bible get release.alpha.bug_bash`), one crate per order (`tech.security.one_crate`), receipts granted once
(`tech.security.process_receipt`).

## Evidence kinds (`rel evidence KIND --result pass|fail|hold`)
| kind | who | what to note |
|---|---|---|
| tests | owner (or opencloud, automatic) | spec count, where run |
| bugbash | owner | which items of `release.alpha.bug_bash` ran, any skipped |
| livecheck | owner | players, devices, lag setting, pass criteria of `tech.streaming.live_check` |
| perf | owner | phone model, FPS, F9 memory start/end of a 4x soak |
| security | anyone, `--file SECURITY_GATE.json` | a verdict file stored elsewhere |

## rr-exploit-guard contract (G5)
File: `next/security/SECURITY_GATE.json` (or `evidence security --file PATH`). Keys read:
`verdict` (`PASS` | `HOLD` | `FAIL`), `scanned_at` (ISO 8601 UTC; must be later than every place's `attached_at`),
optional `blocking` and `hold` (lists, shown in GATES.md), `stage`. Input to scan: every folder
`next/places/<name>/audit/scripts/` (Rojo-style names: `.server.lua`, `.client.lua`, `.lua`; `index.json` maps
file -> instance path). Re-attaching a place makes the verdict stale.

## multiuse-critic contract (G8)
Per mission: `critique-*/ledger.json` rows `{pass, agent, scores{criterion: n}}`. Standing = latest score per
criterion; overall = lowest. Certified = every criterion's latest row came from a recorded agent whose name does
not contain "self", and overall >= the mission's bar (state.json `bar`, default 8). Fix: one independent
`--kind final` critic pass through multiuse-critic on the mission's CRIT folder.

## Extra checks (presets/gates.json `extra_checks`)
Each: `{gate, name, skill, cmd}`; `{python}` and `{skill}` are substituted; the skill is found by glob. Exit 0 =
ok, non-zero = soft problem, skill missing = reported as skipped. Add a sibling's release check here, not in code.
