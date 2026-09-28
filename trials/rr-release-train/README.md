# rr-release-train trial (2026-09-28)

A dry run of the whole train on synthetic inputs, in a cloud session (no Studio, apis.roblox.com blocked).

Inputs
- `places/Lobby.rbxl`, `places/Trip.rbxl`: synthetic binary places from `make_fixture.py` (not the real game):
  RR_Version stamp 0.1.0-alpha.1, ProfileStore `PlayerData_alpha1`, a lever remote, one `.spec` module; the
  Lobby also has a `DEBUG = true` flag, a union and a PLACEHOLDER part so the gates have something to find.
- A throwaway Rojo-style git repo (scratchpad) with conventional commits, a Player-Note and a Release-Note: skip.
- The real JARVIS repo (detected as tooling, summarised) and the two real missions in `/home/user/claude/missions`
  (marked in-build here only to exercise G8; the owner has not confirmed either is in Studio).
- Fake Open Cloud IDs (universe 1111, places 2222/3333).

Run: config, init, attach x2, collect, mark (retitled the two missions in player words), version, changelog
--apply, notes, the notes written from the brief, notes-check, stamp, gate, plan, publish (dry run), status.

Results (`releases/next/`)
- Version 0.1.0-alpha.1 (minor: a feat commit and two missions); CHANGELOG.md written.
- notes-check PASS; `PATCH_NOTES.md`, `STORE_UPDATE.txt` are the clean outputs.
- Gate NO-GO, correctly: G5 pending (rr-exploit-guard not installed yet, no verdict), G6 pending (Studio route,
  so no deferred Luau tests; bug bash needed for a minor release), G8 warn (depot: self-reviewed 8 and
  independent 7s with unrecorded critic; HUD: standing 6), G9 warn (DEBUG flag), G4 warn (off-palette fixture
  colours), G10 warn (6 release-related OQs incl. the four new ones).
- Route STUDIO for the release: the Lobby union cannot be updated by the API (tech.publish.oc_unsupported).
- Publish dry run lists every request and the blockers: approval, route, key not set, host blocked (CONNECT 403).
- Owner-only steps (approve, live publish, record, smoke, rollback) were not faked here; `scripts/selftest.py`
  exercises them against a local mock of the Open Cloud endpoints.

Friction noticed and fixed during the trial
- Commits came newest-first; now chronological. Mission objectives made dev-worded changelog lines; collect now
  cuts them at the first clause and asks for a player-words retitle. Version strings tripped the number check;
  now ignored. G10 matched any OQ mentioning "release"; now only title or `blocks:`. Mixed API/Studio places
  could go live at different times; now one route per release.
