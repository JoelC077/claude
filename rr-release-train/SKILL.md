---
name: rr-release-train
description: "Risky Rails (Roblox) release manager: turns 'ship it' into a gated, reversible release. Collects changes from git log (conventional commits, Player-Note trailers), finished rr-mission-control missions and a script diff of the place file; bumps semver (0.x, -alpha.N / -beta.N channels); writes a Keep a Changelog entry and player patch notes in the house voice read from rr-bible, every line traced to a change; runs pre-release gates (version stamp, canon, rr-exploit-guard verdict, Luau tests, perf regression, multiuse-critic certification, debug flags, open questions); plans the publish through Roblox Open Cloud place publishing (dry-run by default; live only with the owner's approval, an API key secret and a typed confirm), then a smoke checklist and rollback plan. Use whenever Joel wants to release, publish, ship or push an update, bump the version, write patch notes or a changelog, check if a build is ready, set up the Open Cloud API key, or roll back a bad update. Not for designing features."
---

# RR Release Train

One release in flight at `<R>/next/`, driven by one CLI. Scripts decide what is measurable, rr-exploit-guard judges
security, multiuse-critic judges visuals, the owner approves and holds the key. Nothing goes live from a dry run.

Paths: `<rt>` = `dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path '*rr-release-train/SKILL.md' 2>/dev/null | head -1)"`.
`rel` below = `python3 <rt>/scripts/release.py`. `<R>` = `--root`, `$RR_RELEASES_ROOT`, or `<git top of cwd>/releases`.
Canon comes from rr-bible (`bible` = its `scripts/bible.py`, found by glob or `$RR_BIBLE_SKILL`).

## Start every session with `rel status`
It prints the release, what is attached, notes/gate/approval state and the **next step**. Do that step; do not
re-read files the status already summarises.

## Hard rules
- **Dry run by default.** `publish` and `rollback` send nothing without `--live`, a valid owner approval,
  `$ROBLOX_API_KEY`, a reachable API host and `--confirm <version>`. Never pass `--live` unless the owner asked
  for the live publish in this conversation.
- **Owner-only records:** `approve`, `waive`, `record`, `smoke --result`, `evidence tests|bugbash|livecheck|perf`
  and a live `rollback` take `--by owner`. Pass it only when the owner said so in chat, and cite it
  (`--via "chat DATE"` on approve, `--note` / `--reason` elsewhere).
- **Never self-score.** Visual quality is multiuse-critic's (G8 reads its ledgers); security is rr-exploit-guard's
  (G5 reads its verdict). If a gate needs them, run or request them; never write their files yourself.
- **Canon, not memory.** Voice, lexicon, banned names, data-store name, bug bash, live check and Open Cloud limits
  are read from rr-bible at run time. A gap is an open question (`bible add-question`), not a guess.
- Never spend money, message players, post to Discord or change the owner's Claude config: write the post, the
  owner posts it.

## The train
1. **Open:** `rel init --channel alpha|beta|live` (first time: `rel config --place Lobby --universe U --place-id P
   --start`, `rel config --place Trip ...`, optional `--repo PATH` for a Rojo repo, `--missions DIR`).
2. **Attach the build:** the owner saves each place from Studio (File > Save to File As .rbxl) and gives the paths;
   Rojo users `rojo build -o Place.rbxl`. `rel attach Lobby path.rbxl` pins sha256, audits the file (instances,
   scripts, colours, fonts, stamp, API-unsupported classes) and extracts every script to
   `next/places/<name>/audit/scripts/`.
3. **Collect:** `rel collect`. Game-repo commits become changes (feat -> Added/minor, fix -> Fixed/patch, `!` or
   BREAKING -> major, refactor/chore -> internal; `Player-Note:` gives wording, `Release-Note: skip` hides one).
   Tooling repos (this JARVIS repo) are summarised, not listed. Done missions come in as **unknown**: ask the
   owner which are really in Studio, then `rel mark C-6 --in-build yes|no`; retitle missions in player words
   (`--title`, `--note`). Studio-only work has no trail: `rel add "Coal lasts longer on Easy" --section Changed`.
   A script diff against the last release lists what changed so nothing ships undescribed.
4. **Version:** `rel version` (history + biggest in-build bump; 0.x: breaking -> minor; channel tag). `--set` only
   when the owner names one (1.0.0 at soft launch per OQ-037 default).
5. **Changelog:** `rel changelog --apply` (Keep a Changelog section; prepends to `<R>/CHANGELOG.md`, idempotent).
6. **Patch notes:** `rel notes` writes `NOTES_BRIEF.md` (player changes + the voice slice from rr-bible). Read only
   the brief, then write `next/PATCH_NOTES.src.md` and `next/STORE_UPDATE.src.txt` (format:
   `references/notes.md`). `rel notes-check` must PASS: every bullet tagged `[C-n]` to an in-build player change,
   every player change covered, D-007 and store rules, jargon, parked sidings, limits, `bible check`. It writes the
   clean `PATCH_NOTES.md` and `STORE_UPDATE.txt`.
7. **Stamp:** `rel stamp` -> `RR_Version.lua`; the owner pastes it as ModuleScript `ReplicatedStorage.RR_Version`,
   saves and re-exports; re-attach. G1 checks the stamp inside the file; the Luau tests and smoke S1 read it.
8. **Security:** hand `next/places/*/audit/scripts/` to rr-exploit-guard; it writes
   `next/security/SECURITY_GATE.json` (contract: `references/gates.md`). Missing or older than the attached files =
   G5 PENDING.
9. **Gate:** `rel gate` -> `GATES.md`, verdict GO / GO-WITH-WARNINGS / NO-GO. Fix what it lists; ask the owner for
   evidence it needs (bug bash for minor+ releases: `release.alpha.bug_bash`; live check for live minor+).
   Only the owner waives: `rel waive G8 --by owner --reason "..."`.
10. **Approve (owner):** show the owner GATES.md verdict, the notes and the version; on a yes:
    `rel approve --by owner --via "chat 2026-10-12"`. It binds version + place hashes + gate report + notes;
    any change voids it (`status` says so).
11. **Plan:** `rel plan` -> `PUBLISH_PLAN.md` (route per release: API, or Studio when a place holds classes the
    API does not update or exceeds its size limit), `SMOKE.md`, `ROLLBACK.md`.
12. **Publish:** `rel publish` (dry run: every request printed, blockers listed). Live, from a machine that reaches
    apis.roblox.com with the key: `rel publish --live --confirm 0.1.0-alpha.2 [--restart]` uploads each place as
    Saved, runs `assets/luau/run_tests.lua` on each saved version (specs + stamp), and only if all pass
    publishes, start place last; `--restart` bleeds old servers off. Studio route: the owner publishes from
    Studio, then `rel record --place Lobby=57 --place Trip=31 --by owner`. Either way next/ is archived to
    `<R>/<version>/` and history.json updated.
13. **Smoke:** within the first hour the owner runs `SMOKE.md` (join + stamp, full trip through the funnel,
    coins survive teleport and rejoin, error report, each changed item); `rel smoke --result S1=pass,S2=fail
    --by owner`. Any P0 fail -> rollback recommended.
14. **Rollback:** `rel rollback` (dry run: re-publish the previous release's archived files), then
    `rel rollback --live --confirm <prev> --by owner --restart`, or Creator Hub version history (ROLLBACK.md).
    DataStore writes do not roll back: a release that changes the saved profile shape must stay readable by the
    previous build.

Details only when needed: gates and evidence contracts `references/gates.md`; Open Cloud, the API key secret, live
publish and rollback `references/publishing.md`; patch-notes format and voice `references/notes.md`.

## Gates at a glance
| gate | checks | typical fix |
|---|---|---|
| G1 version | semver, above history, channel tag, RR_Version stamp in every place | `stamp`, re-attach |
| G2 changes | confirmed in-build changes, bump matches version | `mark`, `version` |
| G3 notes | notes-check passed and not stale | rewrite .src, `notes-check` |
| G4 canon | `bible check`: script names/numbers (FAIL), place colours/fonts (WARN) | fix to canon or record a decision |
| G5 security | rr-exploit-guard verdict, fresh | run exploit-guard |
| G6 tests | Luau specs (deferred to publish on the API route) or owner result; bug bash for minor+ | owner evidence |
| G7 perf | audit growth vs last release, `vfx budget --tier phone`, live check (live) | owner phone evidence |
| G8 visuals | multiuse-critic ledgers of shipped missions, independent and at bar | independent final pass |
| G9 hygiene | debug flags, data-store name vs canon, placeholders, `sound validate --release` | turn flags off |
| G10 open questions | OQs blocking release or launch, defaults in use | owner decides |

Alpha/beta: G7, G8 and G9 problems warn; live: they block. Blocking sets live in `presets/gates.json`.

## API key (the secret), in short
Creator Dashboard > API Keys (create.roblox.com/dashboard/credentials): **universe-places: Write** on Risky Rails only
(+ `universe.place.luau-execution-session: Write` for the tests, + `universe: Write` for `--restart`), expiry set.
Store it as the environment variable `ROBLOX_API_KEY`: on the owner's machine from a password manager
(`export ROBLOX_API_KEY=...` in that shell only), or in a cloud environment's settings (environment variables;
also allow `apis.roblox.com` under network access). Never in a file in the repo, never pasted into chat.
Full steps and risks: `references/publishing.md`.

## Plugs
- rr-bible: canon reads; `check` on notes and scripts; gaps as OQs (OQ-037 version scheme, OQ-038 notes voice,
  OQ-039 place perf budgets, OQ-040 staging place; defaults in use until the owner decides).
- rr-mission-control: `missions/*/state.json` done + `mission.md` Objective + `critique-*/ledger.json`.
- multiuse-critic: G8 uses its standing rule (latest score per criterion, overall = lowest; self-review is not
  certification). Store art goes through risky-rails-thumbnail-ideas + the critic, never scored here.
- rr-exploit-guard: scans the extracted scripts, writes SECURITY_GATE.json. Not installed = G5 PENDING, said so.
- rr-soundsmith / rr-vfx-lighting: `presets/gates.json` extra checks, skipped (and reported) when absent.

## Honest limits
- Cloud sessions: apis.roblox.com is blocked by the egress proxy and there is no Studio, so live publish, Luau tests
  and restarts run where the host is reachable (the owner's machine, or an environment that allows it). The Open
  Cloud client is tested against a local mock of the documented endpoints (selftest), never against Roblox.
- The audit reads what a place file holds; it cannot see runtime FPS or memory (owner evidence), mesh triangles
  (remote assets) or edits inside unions (why unions force the Studio route unless the owner overrides with
  `config --place NAME --route api`).
- placefile.py reads binary (LZ4; ZSTD needs `pip install --target ~/.cache/rr-tools/py zstandard`) and XML
  places; checked on rojo-rbx/rbx-test-files, not yet on a real Risky Rails place.

## Maintain
`python3 <rt>/scripts/selftest.py` (temp root, mock Open Cloud, Lua 5.1 run of run_tests.lua via optional lupa)
must print `all N passed`. Remove `__pycache__` after running scripts. Release-process numbers (limits, growth
threshold, strictness) live in `presets/gates.json`; game facts never do.
