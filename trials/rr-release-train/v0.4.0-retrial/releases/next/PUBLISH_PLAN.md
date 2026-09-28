# Publish plan · 0.4.0 (alpha)

Preconditions now: approval not approved · $ROBLOX_API_KEY NOT set · API host unreachable: Tunnel connection failed: 403 Forbidden · Luau tests on saved version: on

**Route for this release: API** (one route for every place so they go live together)

| order | place | route | file | sha256 | why |
|---|---|---|---|---|---|
| 1 | Trip | api | places/Trip/Trip.rbxl | efbb8e45d933 | - |
| 2 | Lobby (start) | api | places/Lobby/Lobby.rbxl | 0e129e9e9bcf | - |

## Before publishing
0. Rollback target: write down each place's live version number now (Creator Hub > place > Version History) and record it: `release.py baseline --place Lobby=N --place Trip=M` (ROLLBACK.md uses it).
1. The attached files in `places/` become the release archive (the next release's rollback source); keep a copy in the owner's storage too (the releases root may be a disposable session).
2. `release.py publish` (dry run): prints every request; fix anything it lists as missing.

## Steps (API route)
3. From a machine that reaches apis.roblox.com with the key set: `release.py publish --live --confirm 0.4.0` [--restart]. It re-runs the gates (must match the approval), uploads each place as **Saved**, runs `assets/luau/run_tests.lua` on each saved version (specs + RR_Version), and only if all pass uploads each as **Published**, start place last.
4. Servers: `--restart` restarts old-version servers with a 14-minute bleed-off (canon: trip 12 min + results_home_s + board_wait_s (75 s), rounded up; needs universe:write), or Creator Hub > experience > ... > Restart Servers for Updates. Until then old and new servers overlap (old Lobby -> new Trip teleports).
5. Run SMOKE.md within the first hour; any P0 fail -> ROLLBACK.md.

## Steps (Studio route)
3. Open the exact attached file in Studio (sha256 above), File > Publish to Roblox.
4. Note each place's new version number (Creator Hub > place > Version History).
5. `release.py record --place NAME=VERSION ... --by owner`, then SMOKE.md.

Timing: publish when you can watch the first hour, outside the owner-on-the-train sessions (`release.ops.timetable`: 16:00 / 20:00 / 22:00 UK daily for the first two weeks, the owner on the train).
