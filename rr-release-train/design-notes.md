# rr-release-train · design notes (2026-09-28)

## Job
Turn "ship it" into a gated, reversible Roblox release: a version, a changelog, player patch notes in the house
voice, pre-release gates, a publish plan (dry-run by default), a post-release smoke checklist and a rollback
plan. Scripts decide what is measurable, rr-exploit-guard judges security, multiuse-critic judges visuals, the
owner approves and presses publish.

## Pipeline (one CLI, `release.py`, state in `<R>/<version>/release.json`)
```
init       <R>/<ver>/ + release.json; version from history + changes, or given
collect    git log since the last release (per repo; conventional commits, Player-Note / Release-Note trailers,
           internal-path rule), finished missions (state.json, objective, critic ledgers), rr-bible decisions
           since the last release, the owner's manual `add` (Studio work has no git trail)
           -> changes.json: stable C-ids, section, audience player|review|internal, bump level
bump       semver from history + changes; 0.x: breaking -> minor; -alpha.N / -beta.N per channel
changelog  CHANGELOG.section.md (Keep a Changelog); --apply prepends it to a CHANGELOG.md
notes      notes-brief.md: player changes + the voice slice read from rr-bible now
           Claude writes PATCH_NOTES.src.md + STORE_UPDATE.src.txt with [C-id] tags
notes-check  tags trace to changes, player changes covered, D-007 odds, banned and metadata rules, parked
           sidings, internal jargon, limits, bible check -> PATCH_NOTES.md, STORE_UPDATE.txt (tags stripped)
stamp      RR_Version.lua (version, channel, commit, notes) for the owner to place in ReplicatedStorage
attach     place files (.rbxl/.rbxlx) or source dirs, sha256 pinned; audit runs on attach
gate       G1 version, G2 changes, G3 notes, G4 canon, G5 security (exploit-guard verdict), G6 tests,
           G7 perf, G8 visuals (critic ledgers), G9 hygiene, G10 open questions -> GATES.md, GO / NO-GO
waive      owner only; approve owner only, bound to version + file hashes + gate verdict
plan       PUBLISH_PLAN.md: archive -> Save -> Luau tests on that saved version -> Publish -> restart -> smoke
publish    dry-run default; --live needs approval, key, network, --confirm VERSION; Studio route recorded
smoke      SMOKE.md from canon; results recorded; P0 fail -> rollback recommended
rollback   ROLLBACK.md: re-publish the archived previous files, or Creator Hub version history; data notes
```

## Decisions (with why)
1. **Evidence-bound approval.** Approval stores sha256 of every place file, the version and the gate verdict hash;
   any change voids it. Live publish also needs the key in the environment, the host reachable and
   `--confirm <version>`. Waivers, approvals and manual evidence accept `--by owner` only (rr-bible's rule).
2. **Save, test, then publish.** Open Cloud uploads a Saved version first, runs `assets/luau/run_tests.lua`
   against that exact version (Luau execution tasks), and publishes only when specs pass and the saved place
   carries the release's RR_Version. All places are saved and tested before any is published.
3. **Honest place audit.** `placefile.py` reads binary (LZ4 built in, ZSTD via the optional zstandard module,
   because current Studio saves ZSTD) and XML places with the stdlib, cross-checked binary vs XML on the
   rojo-rbx/rbx-test-files fixtures. It measures what files hold (tree, counts, scripts, colours, fonts,
   flags), never runtime performance.
4. **Perf is regression plus evidence.** Canon has no place-level budget (new OQ), so G7 compares the audit with
   the previous release's audit (growth thresholds in presets/gates.json), runs sibling budget checks
   (`vfx budget`) and asks for owner device evidence (phone FPS, memory soak) where canon demands it.
5. **Traceable notes.** Every bullet carries [C-id] tags in the source; notes-check strips them. Nothing is
   claimed that no change backs (release.store.metadata_rules); parked sidings are flagged; D-007 is enforced.
6. **Security is a contract.** rr-exploit-guard's verdict file (JSON `verdict` or a `VERDICT:` line, bound to the
   build's sha256) feeds G5; release-train extracts the scripts for it and only checks release hygiene itself
   (debug flags, the canon data-store name).
7. **Visual judgement stays with multiuse-critic.** G8 reads critic ledgers; self-reviewed work is uncertified
   (warn in alpha, block in live). Release-train never scores.
8. **Studio route when the API cannot.** PartOperation/SurfaceAppearance/Editable*/BaseWrap in the place, files
   over 10 MiB, or no network -> the plan says publish from Studio, then `record` the version numbers.
9. **Canon at run time.** Tone, lexicon, banned names, sidings, bug bash, live check, funnel, store rules, store
   name, admin rule and decisions are read through bible.py; new platform facts and four OQs were recorded
   through bible.py (version scheme, notes voice, place perf budgets, staging place).

## Plugs
- rr-bible: `get`/`search`/`check` via its CLI (found by glob or RR_BIBLE_SKILL); `add-fact`/`add-question` for
  gaps; `decide` stays the owner's.
- rr-mission-control: collect reads `<M>/state.json`, mission.md Objective, debrief and `critique-*/ledger.json`;
  mission exports can be attached as source payloads for the canon gate.
- multiuse-critic: G8 reads ledgers (standing score per criterion, independent passes only); new store art goes
  through risky-rails-thumbnail-ideas + the critic, never self-scored.
- Siblings: presets/gates.json runs their validators (sound --release, feel, vfx + budget, ui, asset verify).
- rr-exploit-guard: verdict file contract (references/gates.md); missing skill or verdict = G5 pending.

## Limits
Cloud sessions: apis.roblox.com and create.roblox.com are blocked by the egress proxy (measured 2026-09-28), no
Studio, and place files come from the owner. The parser has not yet seen a real Risky Rails place file.
