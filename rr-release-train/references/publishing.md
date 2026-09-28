# Publishing, the API key, rollback

Platform facts (endpoints, size limit, unsupported classes, scopes) are rr-bible `tech.publish.oc_*` (source
RBXOC, Creator Docs read 2026-09-28; the place API is marked BETA). Recheck them before a launch-critical publish:
`bible get tech.publish`.

## 1. Create the key (owner, once)
1. Creator Dashboard > API Keys (create.roblox.com/dashboard/credentials) > **Create API Key**; name it
   `RR_PLACE_PUBLISHING`.
2. Access Permissions: add **universe-places**, keep **Restrict by Experience** on, pick Risky Rails, operation
   **Write**. Optional, only if wanted: **universe.place.luau-execution-session** Write (Luau tests on the saved
   version, recommended) and **universe** Write (`--restart`). Nothing else.
3. Security: leave IP restriction off unless publishing only from one fixed IP. Set an expiry (for example 90 days)
   and put the renewal in the calendar; an expired key fails a publish at the worst moment.
4. Save & Generate, copy the key into a password manager. The key acts with the owner's permissions on that
   experience: anyone holding it can replace the live game.

## 2. Store it as a secret (never in the repo, never in chat)
The scripts read only the environment variable `ROBLOX_API_KEY`.
- **Owner's machine (recommended for live publishes):** in the terminal that will publish,
  `export ROBLOX_API_KEY="$(pbpaste)"` (macOS) or read it from the password manager's CLI; it lives only in that
  shell. Do not add it to `.bashrc`, `.env` files inside the repo, or Claude settings.
- **Claude Code cloud environment:** the cloud environment menu in the session's title bar > Edit > environment
  variables (or API credentials where offered): `ROBLOX_API_KEY`. Also add `apis.roblox.com` to the allowed
  domains under Network access (the default policy blocks it: CONNECT 403). Every session in that environment can
  then publish, so prefer a key with an expiry, and remove it when not releasing.
- Check without revealing it: `python3 <rt>/scripts/opencloud.py probe` prints "key set / not set" and whether the
  host answers.

## 3. Dry run (default, safe anywhere)
`rel publish` prints each request (method, URL, content type, file, bytes; the key shown as `$ROBLOX_API_KEY`),
writes `next/publish-dryrun.json`, and lists what blocks a live run: approval, route, key, network.

## 4. Live publish (owner present, owner asked for it)
Preconditions checked by the script: approval valid (version, place hashes, gate report and notes unchanged),
route API for every place, key set, host reachable, `--confirm` equals the version.
Order: every place is uploaded with `versionType=Saved` (not live) -> `run_tests.lua` runs on each saved version
through a Luau execution task (spec modules named `*.spec`, plus `RR_Version.version == release`) -> only when all
pass, each place is uploaded with `versionType=Published`, non-start places first, the start place last ->
`--restart` calls restartServers with `closeAllVersions false` and a bleed-off (`config --bleed MIN`, 1-60, default
10) so running trips finish. Each step is appended to `next/publish-log.json`.
POSTs are retried only on HTTP 429; an ambiguous 5xx is reported, never blindly re-sent.
Partial failure (one place published, another failed): the script says which are live. Either finish (fix and
rerun; already-live places just get a new version with the same file) or roll back the published ones.
Without the Luau scope, `config --luau-tests off` and record the owner's Studio run as evidence instead.

## 5. Studio route
Chosen for the whole release when any place holds classes the API does not update (PartOperation incl. unions and
negates, SurfaceAppearance, EditableImage/Mesh, BaseWrap) or is over the size limit. If the owner confirms none of
those instances changed since the last Studio publish, `rel config --place NAME --route api` allows the API for
that place (unchanged ones are kept by Roblox; edited ones would silently not update).
Steps: open exactly the attached file (check its sha256 in PUBLISH_PLAN.md), File > Publish to Roblox, read each
place's new version number in Creator Hub > place > Version History, then
`rel record --place Lobby=57 --place Trip=31 --by owner`.

## 6. Restarting servers without the API
Creator Hub > Creations > the experience > the ... menu > Restart Servers for Updates (or Shut Down All Servers
for an emergency). Players on old servers otherwise keep the old version until their server empties.

## 7. Rollback
- Target: the previous published release in `<R>/history.json`; its place files are archived under
  `<R>/<version>/places/` (verified by sha256 before use).
- API: `rel rollback` (dry run), then `rel rollback --live --confirm <previous version> --by owner --restart`
  (immediate restart; this is an emergency). New version numbers, old content; the bad release is marked
  `rolled_back` in history and its version is never reused.
- No archive or no key: Creator Hub > Creations > experience > Places > place > Version History > restore the
  previous version number (ROLLBACK.md lists them), then Restart Servers for Updates.
- Data: DataStore/ProfileStore writes stay. If the bad release wrote a new profile shape, check the previous
  build tolerates it (unknown fields ignored, no crash on load) before rolling back; otherwise fix forward.
- Afterwards: one honest line to players (the owner posts it), keep the failed release folder for the post-mortem,
  fix, and run the train again with a new version.

## 8. Staging (OQ-040)
Default A: no staging place in the closed alpha. Before the public soft launch, a private copy of the experience
(separate universe, same places) lets each candidate be published and smoke-tested first: add its IDs with
`rel config --place Lobby --universe <staging> ...` in a separate releases root (`--root releases-staging`).
