# Publish plan · 0.1.0-alpha.1 (alpha)

Preconditions now: approval not approved · $ROBLOX_API_KEY NOT set · API host unreachable: Tunnel connection failed: 403 Forbidden · Luau tests on saved version: on

**Route for this release: STUDIO** (one route for every place so they go live together)
- Lobby: API does not update UnionOperation x1 (tech.publish.oc_unsupported; if none changed since the last Studio publish: config --place Lobby --route api)

| order | place | route | file | sha256 | why |
|---|---|---|---|---|---|
| 1 | Trip | api | places/Trip/Trip.rbxl | 81fa462a0506 | - |
| 2 | Lobby (start) | studio | places/Lobby/Lobby.rbxl | 90f525385ef2 | API does not update UnionOperation x1 (tech.publish.oc_unsupported; if none changed since the last Studio publish: config --place Lobby --route api) |

## Steps (API route)
1. Archive: the attached files in `places/` are the release archive (rollback source for the next one).
2. `release.py publish` (dry run): prints every request; fix anything it lists as missing.
3. From a machine that reaches apis.roblox.com with the key set: `release.py publish --live --confirm 0.1.0-alpha.1` [--restart]. It uploads each place as **Saved**, runs `assets/luau/run_tests.lua` on each saved version (specs + RR_Version), and only if all pass uploads each as **Published**, start place last.
4. Servers: `--restart` restarts old-version servers with a 10-minute bleed-off (needs universe:write), or Creator Hub > experience > ... > Restart Servers for Updates.
5. Run SMOKE.md within the first hour; any P0 fail -> ROLLBACK.md.

## Steps (Studio route)
1. Open the exact attached file in Studio (sha256 above), File > Publish to Roblox.
2. Note each place's new version number (Creator Hub > place > Version History).
3. `release.py record --place NAME=VERSION ... --by owner`, then SMOKE.md.

Timing: publish when you can watch the first hour, outside the owner-on-the-train sessions (`release.ops.timetable`: 16:00 / 20:00 / 22:00 UK daily for the first two weeks, the owner on the train).
