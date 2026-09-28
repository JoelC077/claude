# Gates and evidence contracts

`rel gate` writes `next/GATES.md` (human) and `next/gates.json` (hash bound into the approval; `publish --live` and
`record` re-run the gates and compare). Statuses: PASS · WARN · FAIL · PENDING (evidence missing) · WAIVED (owner) ·
N/A. Verdict: **NO-GO** on any FAIL, or a PENDING gate in the channel's blocking set; **GO-WITH-WARNINGS** on WARN or
a pending advisory gate; else **GO**. Blocking sets and strictness: `presets/gates.json` (`blocking`, `channels`).
"Soft" problems are WARN in alpha/beta and FAIL in live. Baselines ("vs the live release") use the release whose
content is live now: after a rollback, the one rolled back to.

| gate | reads | FAIL / PENDING when | soft (WARN in alpha/beta) | WARN only |
|---|---|---|---|---|
| G1 version | release.json, each audit's `RR_Version` | not semver; not above every used version; stamp missing or different | channel tag missing | - |
| G2 changes | changes | nothing confirmed; unknown in-build (PENDING); version below the needed bump | mission/manual change in build without `--via` (agent's word) | only script diffs; teleport code changed (old/new servers overlap in the bleed-off) |
| G3 notes | notes-check.json | not run or stale (PENDING); errors | - | warnings |
| G4 canon | `bible check` on combined scripts (names, numbers with a canon check pattern) and props.lua (colours, fonts) | banned name or contradicting number | - | off-palette colours/fonts; `name = number` that differs from a single-number fact of `ui`/`gameplay`/`economy` whose key names it (heuristic) |
| G5 security | SECURITY_GATE.json | missing, not rr-exploit-guard's, not bound to the attached sha256s, other stage (PENDING); verdict FAIL | verdict HOLD | - |
| G6 tests | evidence `tests`, `bugbash`, spec sources | a spec names DataStore/ProfileStore/Messaging/MemoryStore; test fail; no result and not deferrable (PENDING); bug bash missing on minor+ (PENDING) | - | - |
| G7 perf | audits vs the live release, evidence `perf`, `livecheck` | owner evidence fail; live check missing on live minor+ (PENDING) | no baseline and no `perf` evidence | growth > 15% |
| G8 visuals | critic ledgers of in-build missions of kind ui/3d/vfx/thumbnail/design, read fresh | - | any not certified | - |
| G9 hygiene | extracted scripts, audit, mission export notes | - | `DEBUG`-style flag `= true`; blank asset id (`rbxassetid://0`) in a script or property; demo/test script or one its mission marks "delete for release"; placeholder instances; test-looking data store | new module nothing in its place requires, or only a demo requires; store name differs from canon |
| G10 open questions | every open OQ | an OQ whose `blocks` names this channel (e.g. OQ-040 for live) | an OQ touching an in-build mission (its source ID, or its words in title/affects/blocks) | OQs about release/launch/publish/monetisation |

Waivers: `rel waive GN --by owner --reason "..."` (G2-G10; never G1). A G5 waiver is reported in the debrief.

## G2 in-build confirmation
Missions and manual changes are in the build only on the owner's word: `mark C-n --in-build yes --via "chat DATE"`
(or `add ... --via`). Git commits of a game repo need none (the repo builds the place).

## G6 "deferred"
On the API route with `luau_tests` on (default), tests are not needed before approval: `publish --live` runs
`assets/luau/run_tests.lua` on each **saved** version and refuses to publish on any failure (an earlier Open Cloud
run is shown, not held against a retry; re-attaching drops any tests result). On the Studio route the owner runs the
same file in Studio (Play Solo, command bar in the server view; the `[RR tests]` lines in Output are the result),
then `rel evidence tests --result pass --by owner --note "7 tests, stamp 0.1.0-alpha.2"`.

Spec convention (the owner's code): a ModuleScript named `Something.spec` under ServerScriptService, ServerStorage or
ReplicatedStorage, returning a function or a table of `name = function() assert(...) end`. No specs = `tests 0`; the
stamp check still runs. **Live data:** on Open Cloud the tests run in the production universe, where DataStores are
real. Specs never call DataStoreService, ProfileStore, MessagingService or MemoryStoreService (G6 fails a spec that
names them); data modules check `_G.RR_RELEASE_TEST` (run_tests.lua sets it) and stub themselves. Worth writing
first, as pure logic with stubbed data: the bug bash items (`bible get release.alpha.bug_bash`), one crate per order
(`tech.security.one_crate`), receipts granted once (`tech.security.process_receipt`, against a stub store).

## Evidence kinds (`rel evidence KIND ...`)
| kind | who | what to note |
|---|---|---|
| tests | owner (or opencloud, automatic) | spec count, where run |
| bugbash | owner | which items of `release.alpha.bug_bash` ran, any skipped |
| livecheck | owner | players, devices, lag setting, pass criteria of `tech.streaming.live_check` |
| perf | owner | phone model, FPS, F9 memory start/end of a 4x soak; new content walked |
| security | rr-exploit-guard file (`--file`), or `--by owner` (shown as owner-attested) | a verdict stored elsewhere |

## rr-exploit-guard contract (G5)
File: `next/security/SECURITY_GATE.json` (or `evidence security --file PATH`, validated). Keys read: `skill` =
`rr-exploit-guard`, `verdict` (`PASS` | `HOLD` | `FAIL`), `scanned_at`, `places` (map -> sha256; every attached
place's sha256 must be there), `stage` (must equal the channel), optional `blocking`, `hold` (shown). Input: every
`next/places/<name>/audit/scripts/` (Rojo-style names; `index.json` maps file -> instance path); `guard.py gate
--stage <channel> --out next/security`. Re-attaching a place unbinds the verdict.

## multiuse-critic contract (G8)
Per mission, read fresh each run: `critique-*/ledger.json` rows `{pass, kind, agent, scores{criterion: n}}`.
Standing = latest score per criterion; overall = lowest. Certified = every standing score from a recorded agent whose
name has no "self", overall >= the mission's bar (state.json `bar`, default 8), and the last independent `kind:
final` row has every score at the bar (the critic's done rule). The fix G8 prints depends on the standing: below the
bar -> finish the fix loop in rr-mission-control, then a final pass; at the bar on self-review -> one independent
final pass.

## Extra checks (presets/gates.json `extra_checks`)
Each: `{gate, name, skill, cmd}`; `{python}` and `{skill}` are substituted; the skill is found by glob. They judge the
sibling's own library, so they print under "Advisory" in GATES.md, outside the verdict and the approval hash. A cmd
containing the token `{audits}` receives the build's audit folders and then counts in its gate (exit 0 ok, non-zero
= soft problem). Add a sibling's release check here, not in code.
