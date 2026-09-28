# rr-release-train fix pass (2026-09-28)

**REPORT.md was not written.** The harness blocks subagents from writing report .md files, so the report is only here. For the same reason I deleted the re-trial README I had drafted.

**Inputs:** FRICTION.md (20 items) and 2 independent reviews (scores 7 and 6). I applied every HIGH and MED finding and the cheap LOWs; four partial rejections are listed below. The selftest grew from 50 to 76 checks and all pass. The re-trial on the v0.4.0 inputs is in `/home/user/claude/trials/rr-release-train/v0.4.0-retrial/`.

## Changes

### Gates (scripts/gates.py)
- **G1:** a missing RR_Version stamp is now FAIL. The Luau tests and smoke check S1 both need it.
- **G2:**
  - A mission or manual change marked in-build without `mark|add --via "chat DATE"` is flagged as "on the agent's word" (WARN in alpha/beta, FAIL in live).
  - Teleport code in the script diff is a WARN: during the bleed-off, old Lobby servers still send crews to the new Trip.
- **G4:** the summary now says numbers are only compared where canon has a check pattern. A heuristic drift check was added and catches `gap = 6` against canon `ui.hud.gap_px = 8`.
- **G5:** SECURITY_GATE.json must come from rr-exploit-guard (`skill`), list every attached place's sha256 (`places`), and match the channel (`stage`); otherwise PENDING.
  - `evidence security` accepts only a validated verdict file, or a manual result with `--by owner` (shown as owner-attested).
  - Self-certification is refused.
- **G6:**
  - A `.spec` that names DataStore, ProfileStore, Messaging or MemoryStore is FAIL, and run_tests.lua sets `_G.RR_RELEASE_TEST`.
  - A failed Open Cloud test run no longer blocks a retry, and re-attaching a place drops the old test result.
- **G7:** a first release with no baseline gives WARN "no baseline: phone evidence needed" and lists absolute counts, including 771 MeshParts.
- **G8:**
  - Critic ledgers are re-read from the mission folder every run.
  - Certification follows multiuse-critic's done rule: independent, at the bar, and a final pass that agrees.
  - The fix text depends on the standing: below the bar it says "finish the fix loop, then a final pass".
- **G9:**
  - Blank asset ids (`rbxassetid://0`) are caught in scripts and in place properties (placefile now records `blank_assets` and parses XML Content).
  - Demo and test scripts are caught by name and by a mission's "delete for release" note.
  - New modules that nothing requires, or that only a demo requires, are flagged.
  - Debug-flag names are now matched as whole names, so `antiCheatEnabled` and `CHEAT_DETECTION` pass.
- **G10:**
  - It now reads every open question.
  - It fails when an OQ's `blocks` names the release channel (OQ-040 blocks live).
  - An OQ that touches an in-build mission (by source ID or by the mission's terms) is WARN in alpha/beta, FAIL in live; this now finds OQ-001 and OQ-015.
- **Sibling checks:** rr-soundsmith and rr-vfx-lighting results are advisory and sit outside the verdict and the approval hash, with the full failing lines. A check whose command contains `{audits}` would count in its gate.

### Release flow (release.py, rtlib.py, opencloud.py)
- **Live publish:**
  - `publish --live` re-runs the gates and refuses unless they are GO and match the approved hash.
  - The approval also binds the route and the Luau-tests setting.
  - `record` re-runs the gates and stores `unapproved_publish` in history.
- **API key:** the key is checked through `api-keys/v1/introspect`: enabled, not expired, warning under 14 days to expiry, and scopes for each universe. This runs in `probe`, in the dry-run blockers and before live calls. I added canon fact `tech.publish.oc_key_autoexpire` (keys unused for 60 days expire).
- **Bleed-off:**
  - The default now comes from canon: a 12-minute trip plus results and boarding gives 14 minutes.
  - `--bleed` is limited to 1–60, the calculation is printed in PUBLISH_PLAN, and the dry run shows the same restart body the live call sends.
  - I recorded OQ-042 (a crew mid-trip at shutdown keeps its banked fare; default A), and a smoke row cites it.
- **Rollback:**
  - The target is the release before the one live now, and "live now" follows earlier rollbacks.
  - A second rollback needs the owner to name `--to`.
  - Rollbacks log to `rollback-log.json`, so the bad release's publish log is kept.
  - Places whose archive holds unions go through Creator Hub.
  - The dry run shows publish-only requests, a rolled-back release's changes come back at the next `collect`, and ROLLBACK.md names what is live.
- **Notes check:** every line is now traced.
  - A notice or sign-off must be a lexicon string verbatim or carry a tag.
  - Numbers outside bullets must trace to a change.
  - Promises ("next week", "soon") are an ERROR.
  - A parked siding is an ERROR unless the tagged change names it.
  - The clean files are written only on PASS.
- **Changelog:** it stays `[Unreleased]`, gets its date when the release ships, and `abandon` removes it.
- **Version:**
  - `version` sets a number only when none is set; after that it only proposes (`--apply` takes it).
  - An owner-named version needs `--force` to replace.
  - `--after X` seeds history, and a clash with the channel scheme prints guidance: ask once, or record it with `bible decide OQ-037`.
- **Baseline:** `baseline --place Name=Version` records the live version numbers before a first release, so ROLLBACK.md has a target.
- **Smoke:**
  - Rows include each mission's "Watch:" lines, and UI rows say to trigger the feature through real play, not a demo.
  - A mixed-version row is added when teleport code changed.
  - Smoke ids are normalised and checked.
- **Status:** shows open smoke checks after a publish, stale notes, the stamp step, gate blockers, who opened the release and when, and a warning when the releases root is a temp path.
- **Mission discovery:** checks `$RR_MISSIONS_ROOT`, `~/.rr-missions` and `<project>/.rr-missions`, and says "none found" when empty. A "remake" mission arrives as Changed, and the retitle reminder stops once a mission is retitled.
- **Fewer tokens:**
  - `config` and `notes` print one line each.
  - The notes brief now contains the template and a good/bad example, so it works on its own.
  - SKILL.md's gate table and key section are now pointers.
  - `mark --memo` holds internal notes that never reach the brief.

### Docs
- SKILL.md is 125 lines and adds:
  - where the releases folder should live so it persists (including Cowork);
  - that a new cloud session is needed to pick up the key;
  - corrected rollback wording.
- `references/gates.md`, `notes.md` (now edge cases only), `publishing.md` and `design-notes.md` are updated.
- I corrected the first trial's README: it overstated the dry run's curl coverage, the notes check was not strong, and the HUD had no caller.

## Rejected or partial
- **Pass the audit folders to the sibling checks (review 1, M5):** the sibling commands (`sound.py validate`, `vfx.py budget`) take no such input, and they are outside my folder. I applied the fallback instead: advisory and outside the hash, plus the `{audits}` hook for when they add it.
- **Make `record` refuse on a gate mismatch (review 2, H2):** `record` logs a Studio publish the owner has already made, so refusing would lose history. It re-runs the gates and marks `unapproved_publish` instead.
- **`version` without `--set` only prints (review 1, low):** it still sets a number when none exists, since there is nothing to overwrite and it saves a call. After that it only proposes.
- **Ask mission_state.py for its root (review 2, M):** it has no command for that, so I mirrored its documented default folders.
- No finding was judged wrong.

## Validation
- The selftest passes all 76 checks. Script lint is clean and every script's `--help` runs.
- `quick_validate` returned "Skill is valid!", and rr-bible's lint is OK after the two new records. `__pycache__` is removed.
- In the re-trial:
  - G9 catches the two place-file misses from the first trial: the blank icon ids and the NotificationDemo script.
  - It also catches the HUD caller gap: NotificationController is required only by the demo in Lobby and by nothing in Trip.
  - G10 finds OQ-001 and OQ-015, and G4 flags `gap = 6`.
  - The first trial's notes now fail on the "TEMPORARY" notice about the Main Hall.
  - Each note line the reviewers probed (the 500-coin notice, "arrive next week", naming parked sidings) is now an ERROR.
  - `version` no longer overwrites the owner-named 0.4.0.
  - The dry run shows a 14-minute bleed-off, and the blockers show the gate verdict (NO-GO on G5, G6).

## Package
/home/user/claude/dist/rr-release-train.skill

## Scores
Review scores before this pass: [7, 6].

Files are in /home/user/claude/rr-release-train and /home/user/claude/trials/rr-release-train/v0.4.0-retrial:
- SKILL.md
- scripts/release.py
- scripts/gates.py
- scripts/rtlib.py
- scripts/opencloud.py
- scripts/placefile.py
- scripts/selftest.py
- presets/gates.json
- assets/luau/run_tests.lua
- references/gates.md
- references/notes.md
- references/publishing.md
- design-notes.md
- v0.4.0-retrial/gate.txt
- v0.4.0-retrial/publish-dryrun.txt
- v0.4.0-retrial/releases/next/