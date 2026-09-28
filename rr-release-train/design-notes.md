# rr-release-train · design notes (2026-09-28)

## Job
Turn "ship it" into a gated, reversible Roblox release: version, changelog, player patch notes in the house voice,
pre-release gates, a publish plan (dry-run by default), a post-release smoke checklist and a rollback plan.
Scripts decide what is measurable; rr-exploit-guard judges security; multiuse-critic judges visuals; the owner
approves and holds the publish key.

## Pipeline (one CLI, `release.py`; one release in flight at `<R>/next/`, archived to `<R>/<version>/`)
```
init        next/ + release.json (channel alpha|beta|live)
attach      place files (.rbxl/.rbxlx), sha256 pinned, audited by placefile.py (tree, scripts, colours, flags)
collect     git log since the last release (conventional commits, Player-Note trailers; tooling repos summarised),
            done missions not yet shipped (objective, critic ledgers), script diff vs the last release's archive
add / mark  owner-stated Studio work; confirm in-build, audience, section, bump
version     semver from history + max bump (0.x: breaking -> minor; -alpha.N / -beta.N per channel)
changelog   Keep a Changelog section; --apply prepends it to <R>/CHANGELOG.md
notes       NOTES_BRIEF.md (player changes + voice slice read from rr-bible now) -> Claude writes the .src files
notes-check [C-n] tags trace, coverage, banned/metadata/D-007/jargon/siding rules, limits, bible check -> outputs
stamp       RR_Version.lua for ReplicatedStorage (the smoke test and Luau tests read it)
gate        G1 version · G2 changes · G3 notes · G4 canon · G5 security · G6 tests · G7 perf · G8 visuals ·
            G9 hygiene · G10 open questions -> GATES.md, GO / NO-GO
evidence / waive / approve   owner-only records; approval bound to version + file hashes + gate hash
plan        PUBLISH_PLAN.md + SMOKE.md + ROLLBACK.md
publish     dry-run default; --live: Save -> Luau tests on the saved version -> Publish -> optional restart
record      Studio route: owner reports the place version numbers
smoke       record results; any P0 fail -> rollback recommended
rollback    re-publish the previous release's archived files (dry-run default) or Creator Hub version history
```

## Decisions (with why)
1. **One release in flight, state in JSON.** `next/release.json` is the only state; `status` prints the next step,
   so a resumed session costs one call, not a re-read of everything.
2. **Evidence-bound approval.** Approval stores the version, every place sha256 and the gate-report hash; any change
   voids it. Live publish also needs `ROBLOX_API_KEY`, a reachable host and `--confirm <version>`. Waivers,
   approvals, evidence and live rollback accept `--by owner` only (rr-bible's decide rule).
3. **Save, test, then publish.** Open Cloud supports `versionType=Saved`; the Luau Execution API runs
   `assets/luau/run_tests.lua` on that exact saved version (specs + RR_Version check); only then Published.
   Every place is saved and tested before any is published.
4. **Studio route when the API cannot.** PartOperation/SurfaceAppearance/Editable*/BaseWrap in the place (the API
   does not update them) or files over the API size limit -> the plan says publish from Studio, then `record`.
5. **Honest place audit.** placefile.py reads binary (LZ4 built in, ZSTD via optional zstandard) and XML with the
   stdlib; it measures what the file holds, never runtime performance.
6. **Perf = regression + device evidence.** Canon has no place-level budget (OQ recorded): G7 diffs the audit with
   the previous release, runs `vfx budget --tier phone`, and wants the owner's live check for live releases.
7. **Traceable notes.** Every bullet carries [C-n] tags in the source; notes-check strips them; nothing is claimed
   that no in-build change backs; D-007 (never sell odds) and store metadata rules are enforced.
8. **Security is a contract.** rr-exploit-guard's `SECURITY_GATE.json` (`verdict` PASS/HOLD/FAIL, `scanned_at`)
   must be newer than the attached places; release-train extracts the scripts for it and only checks release
   hygiene itself (debug flags, data-store name, placeholders).
9. **Visual judgement stays with multiuse-critic.** G8 reads critic ledgers of shipped missions; self-reviewed work
   is uncertified (WARN in alpha/beta, FAIL in live). Release-train never scores.
10. **Canon at run time.** Tone, lexicon, banned names, sidings, bug bash, live check, funnel, store rules,
    data-store name, D-007 and Open Cloud limits are read through bible.py; gaps went in as OQs.

## Plugs
- rr-bible: get/search/check; add-fact (tech.publish Open Cloud facts), add-question (version scheme, notes voice,
  place perf budgets, staging place). `decide` stays the owner's.
- rr-mission-control: `missions/*/state.json` (status done), mission.md Objective, `critique-*/ledger.json`.
- multiuse-critic: ledgers read through the same standing rule (latest score per criterion; overall = lowest).
- rr-exploit-guard: scans `next/places/*/audit/scripts/`, writes `next/security/SECURITY_GATE.json`.
- rr-soundsmith `validate --release`, rr-vfx-lighting `budget --tier phone`: presets/gates.json extra checks, run
  when the skill is found, skipped (and said so) when not.

## Limits
Cloud: apis.roblox.com is blocked by the egress proxy (CONNECT 403, 2026-09-28) and there is no Studio, so live
publish, Luau tests and restarts run from the owner's machine or an environment with that host allowed. The Open
Cloud client is tested against a local mock of the documented endpoints, never against Roblox. The place parser
has been checked on rojo-rbx/rbx-test-files fixtures, not on a real Risky Rails place yet.
