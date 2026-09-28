---
name: rr-release-train
description: "Risky Rails release manager: semver bump, changelog and player patch notes traced to commits and missions, pre-release gates (canon, exploit-guard, tests, perf, critic), a dry-run Open Cloud publish plan, smoke checklist and rollback. Never publishes without the owner's typed confirm. Not for designing features. Sub-skill of rr-mission-control (JARVIS): any Risky Rails request, even a short one squarely in this area, goes to rr-mission-control first, which routes here; fire directly only when this skill is named or another rr-* skill invokes it."
---

# RR Release Train

One release in flight at `<R>/next/`, driven by one CLI. Scripts decide what is measurable, rr-exploit-guard judges
security, multiuse-critic judges visuals, the owner approves and holds the key. Nothing goes live from a dry run.

Paths: `<rt>` = `dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path '*rr-release-train/SKILL.md' 2>/dev/null | head -1)"`.
`rel` below = `python3 <rt>/scripts/release.py`. Canon comes from rr-bible (`bible` = its `scripts/bible.py`, found by
glob or `$RR_BIBLE_SKILL`).
**Releases root `<R>`** (`--root`, else `$RR_RELEASES_ROOT`, else `<git top of cwd>/releases`) holds history.json (every
version ever used) and the archived place files (the rollback source). It must outlive the session: set
`$RR_RELEASES_ROOT` once to a folder the owner names (Cowork and the owner's machine: `~/rr-releases`; never the
scratchpad). In a cloud session commit `history.json`, `CHANGELOG.md` and the notes; place files stay out of git
(`init` writes the .gitignore) and in the owner's storage. `status` warns when `<R>` is a temp path.

## Start every session with `rel status`
It prints the release, what is attached, notes/gate/approval state and the **next step** (after a publish: the open
smoke checks). Do that step; do not re-read files the status already summarises.

## Hard rules
- **Dry run by default.** `publish` sends nothing without `--live`, a valid owner approval, `$ROBLOX_API_KEY` (checked
  by introspection: enabled, not expired, scopes), a reachable API host and `--confirm <version>`; `--live` re-runs
  the gates and refuses unless they still match the approval. A live `rollback` needs `--by owner`, the key and
  `--confirm <target>`. Never pass `--live` unless the owner asked for the live publish in this conversation.
- **Owner-only records:** `approve`, `waive`, `record`, `smoke --result`, `evidence tests|bugbash|livecheck|perf`, a
  security result without an rr-exploit-guard file, and a live `rollback` take `--by owner`. Pass it only when the
  owner said so in chat, and cite it (`--via "chat DATE"` on approve, `--note` / `--reason` elsewhere). The same goes
  for `mark --in-build yes --via "chat DATE"`: without `--via`, G2 says "on the agent's word".
- **Never self-score.** Visual quality is multiuse-critic's (G8 re-reads its ledgers every run); security is
  rr-exploit-guard's (G5 reads its verdict, bound to the attached files' sha256 and the channel). If a gate needs
  them, run or request them; never write their files yourself.
- **Canon, not memory.** Voice, lexicon, banned names, data-store name, trip length (bleed-off), bug bash, live check
  and Open Cloud limits are read from rr-bible at run time. A gap is an open question (`bible add-question`).
- Never spend money, message players, post to Discord or change the owner's Claude config: write the post, the
  owner posts it.

## The train
1. **Open:** `rel init --channel alpha|beta|live` (first time: `rel config --place Lobby --universe U --place-id P
   --start`, `rel config --place Trip ...`, optional `--repo PATH` for a Rojo repo, `--missions DIR`).
2. **Attach the build:** the owner saves each place from Studio (File > Save to File As .rbxl) and gives the paths;
   Rojo users `rojo build -o Place.rbxl`. `rel attach Lobby path.rbxl` pins sha256, audits the file (instances,
   scripts, colours, fonts, stamp, blank asset ids, API-unsupported classes) and extracts every script to
   `next/places/<name>/audit/scripts/`.
3. **Collect:** `rel collect`. Game-repo commits become changes (feat -> Added/minor, fix -> Fixed/patch, `!` or
   BREAKING -> major, refactor/chore -> internal; `Player-Note:` gives wording, `Release-Note: skip` hides one).
   Tooling repos (this JARVIS repo) are summarised. Done missions (found in `$RR_MISSIONS_ROOT`, `~/.rr-missions`,
   `<project>/.rr-missions` or `--missions`) come in as **unknown**: ask the owner which are really in Studio, then
   `rel mark C-6 --in-build yes --via "chat DATE"`; retitle them in player words (`--title`; `--note` = wording hint
   the notes writer sees, `--memo` = internal). Studio-only work: `rel add "Coal lasts longer on Easy" --section
   Changed --via "chat DATE"`. The script diff against the live release lists what changed, flags teleport code.
4. **Version:** `rel version` sets the proposal when none is set (history + biggest in-build bump; 0.x: breaking ->
   minor; channel tag), later only proposes (`--apply` takes it). `--set X` only when the owner names one. If that
   name clashes with the scheme (OQ-037 default A: closed alpha = 0.1.0-alpha.N, 1.0.0 at soft launch), ask once:
   the scheme's number, or the owner records theirs with `bible decide OQ-037`. Versions shipped before the train:
   `rel version --after 0.3.2` seeds history so numbering continues above them.
5. **Changelog:** `rel changelog --apply` writes the `[Unreleased]` section of `<R>/CHANGELOG.md`; publish/record
   dates it, abandon removes it.
6. **Patch notes:** `rel notes` writes `NOTES_BRIEF.md` (format, examples, player changes, voice slice from rr-bible).
   Read only the brief, then write `next/PATCH_NOTES.src.md` and `next/STORE_UPDATE.src.txt`. `rel notes-check`
   must PASS: every bullet tagged `[C-n]`, every non-bullet line a lexicon string verbatim or tagged, no promises,
   numbers traced, sidings, D-007, store rules, jargon, `bible check`. Only a PASS writes the clean `PATCH_NOTES.md`
   and `STORE_UPDATE.txt` (edge cases: `references/notes.md`).
7. **Stamp:** `rel stamp` -> `RR_Version.lua`; the owner pastes it as ModuleScript `ReplicatedStorage.RR_Version`,
   saves and re-exports; re-attach. A missing or wrong stamp fails G1 (the Luau tests and smoke S1 read it).
8. **Security:** rr-exploit-guard scans `next/places/*/audit/scripts/` and gates with `--stage <channel> --out
   next/security` (G5 prints the exact command). A verdict for other files or another stage is PENDING.
9. **Gate:** `rel gate` -> `GATES.md`, verdict GO / GO-WITH-WARNINGS / NO-GO, each gate with its fix. Ask the owner
   for the evidence it needs (bug bash for minor+ releases, phone perf for new content, live check for live minor+).
   Only the owner waives: `rel waive G8 --by owner --reason "..."`. Gate table and contracts: `references/gates.md`.
10. **Approve (owner):** show GATES.md, the notes and the version; on a yes: `rel approve --by owner --via "chat
    2026-10-12"`. It binds version, place hashes, gate report, notes, route and the Luau-tests setting; any change
    voids it (`status` says so).
11. **Plan:** `rel plan` -> `PUBLISH_PLAN.md` (route: API, or Studio when a place holds classes the API does not
    update or exceeds its size limit; bleed-off from canon trip length), `SMOKE.md` (with each mission's watch
    items), `ROLLBACK.md`. No archived release yet: `rel baseline --place Lobby=56 --place Trip=31` records the live
    version numbers the rollback would restore.
12. **Publish:** `rel publish [--restart]` (dry run: every request, blockers incl. the gate verdict). Live, from a
    machine that reaches apis.roblox.com: `rel publish --live --confirm 0.1.0-alpha.2 [--restart]` saves each place,
    runs `assets/luau/run_tests.lua` on each saved version, then publishes, start place last. Studio route: the owner
    publishes, then `rel record --place Lobby=57 --place Trip=31 --by owner`. Either way next/ is archived to
    `<R>/<version>/` and history.json updated.
13. **Smoke:** within the first hour the owner runs `SMOKE.md`; `rel smoke --result S1=pass,S2=fail,S6=skip --by
    owner`. Any P0 fail -> rollback recommended.
14. **Rollback:** `rel rollback` (dry run: re-publish the archive of the release before the live one), then `rel
    rollback --live --confirm <target> --by owner --restart`, or Creator Hub version history (ROLLBACK.md; always so
    for places holding unions). A second rollback needs the owner to name `--to VERSION`. DataStore writes do not
    roll back: a release that changes the saved profile shape must stay readable by the previous build.

## API key (the secret)
Scopes, creation steps, storage and risks: `references/publishing.md` (read it when setting the key up). In short:
universe-places Write on Risky Rails only (+ luau-execution-session Write, + universe Write), an expiry, and a key
unused for 60 days auto-expires. It lives only in `$ROBLOX_API_KEY`: owner's machine `export
ROBLOX_API_KEY="$(pbpaste)"` in the publishing shell (or the password manager's CLI); cloud environment settings >
environment variables (a new session picks it up) plus `apis.roblox.com` allowed; Cowork: the owner's own terminal.
Never in a repo file, never in chat. `python3 <rt>/scripts/opencloud.py probe` checks it without printing it.

## Plugs
- rr-bible: canon reads; `check` on notes and scripts; gaps as OQs (OQ-037 version scheme, OQ-038 notes voice,
  OQ-039 place perf budgets, OQ-040 staging place, OQ-042 shutdown mid-trip).
- rr-mission-control: `state.json` done + `mission.md` Objective + `critique-*/ledger.json` + export notes
  ("Watch:", "delete for release").
- multiuse-critic: G8 applies its done rule (standing = latest score per criterion, overall = lowest, independent,
  at the bar, and a final pass that agrees). Store art goes through risky-rails-thumbnail-ideas + the critic.
- rr-exploit-guard: scans the extracted scripts, writes SECURITY_GATE.json. Not installed = G5 PENDING, said so.
- rr-soundsmith / rr-vfx-lighting: `presets/gates.json` extra checks; advisory (they judge their libraries) unless
  their cmd takes `{audits}`.

## Honest limits
- Cloud sessions: apis.roblox.com is blocked by the egress proxy and there is no Studio, so live publish, Luau tests
  and restarts run where the host is reachable. The Open Cloud client is tested against a local mock of the
  documented endpoints (selftest), never against Roblox.
- The audit reads what a place file holds: not runtime FPS or memory (owner evidence), mesh triangles, or edits
  inside unions (why unions force the Studio route unless the owner sets `config --place NAME --route api`). The
  no-caller and number-drift checks are heuristics (WARN only).
- placefile.py reads binary (LZ4; ZSTD needs `pip install --target ~/.cache/rr-tools/py zstandard`) and XML
  places; checked on rojo-rbx/rbx-test-files, not yet on a real Risky Rails place.

## Maintain
`python3 <rt>/scripts/selftest.py` (temp root, mock Open Cloud, Lua 5.1 run of run_tests.lua via optional lupa)
must print `all N passed`. Remove `__pycache__` after running scripts. Release-process numbers (limits, growth
threshold, strictness, patterns) live in `presets/gates.json`; game facts never do.
