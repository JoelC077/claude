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
   and put the renewal in the calendar; an expired key fails a publish at the worst moment. A key nobody uses or
   updates for 60 days **auto-expires** even without an expiry (`bible get tech.publish.oc_key_autoexpire`): the
   closed alpha (week of 12 Oct) to the soft launch (about 20 Dec) is longer than that, so publish, or toggle
   Enable Key off/on, at least every 60 days. `probe` and every live call introspect the key first.
4. Save & Generate, copy the key into a password manager. The key acts with the owner's permissions on that
   experience: anyone holding it can replace the live game.

## 2. Store it as a secret (never in the repo, never in chat)
The scripts read only the environment variable `ROBLOX_API_KEY`.
- **Owner's machine (recommended for live publishes):** in the terminal that will publish,
  `export ROBLOX_API_KEY="$(pbpaste)"` (macOS) or read it from the password manager's CLI; it lives only in that
  shell. Do not add it to `.bashrc`, `.env` files inside the repo, or Claude settings.
- **Claude Code cloud environment:** the cloud environment menu in the session's title bar > Edit > environment
  variables (or API credentials where offered): `ROBLOX_API_KEY`. Also add `apis.roblox.com` to the allowed
  domains under Network access (the default policy blocks it: CONNECT 403). Only a **new session** picks the
  variable up. Every session in that environment can then publish, so prefer a key with an expiry, and remove it
  when not releasing.
- **Cowork:** the owner publishes from their own terminal with the key exported there; keep `$RR_RELEASES_ROOT` at
  `~/rr-releases` so history and the archive persist between conversations.
- Check without revealing it: `python3 <rt>/scripts/opencloud.py probe [--universe U]` prints "key set / not set",
  whether the host answers and, with the key set, what `POST api-keys/v1/introspect` says (enabled, expired,
  expiry date, write scopes on the universe). The key goes in the request body and is never printed.

## 3. Dry run (default, safe anywhere)
`rel publish` prints each request (method, URL, content type, file, bytes; the key shown as `$ROBLOX_API_KEY`),
writes `next/publish-dryrun.json`, and lists what blocks a live run: approval (and the gate verdict behind it),
route, key (introspected when the host answers), network. The restart body shown is the one that would be sent.

## 4. Live publish (owner present, owner asked for it)
Preconditions checked by the script: the gates, re-run now, are GO and match the approved report; approval valid
(version, place hashes, gate report, notes, route and the Luau-tests setting unchanged); route API for every place;
key set, enabled, not expired, with the needed scopes; host reachable; `--confirm` equals the version.
Order: every place is uploaded with `versionType=Saved` (not live) -> `run_tests.lua` runs on each saved version
through a Luau execution task (spec modules named `*.spec`, plus `RR_Version.version == release`) -> only when all
pass, each place is uploaded with `versionType=Published`, non-start places first, the start place last ->
`--restart` calls restartServers with `closeAllVersions false` and a bleed-off so running trips can finish: default
one measured trip plus results and boarding from canon (`gameplay.run.length_min` + `results_home_s` +
`board_wait_s`, rounded up: 14 min today; `config --bleed MIN` overrides, 1-60). A crew still mid-trip when its
server closes must keep its banked fare (OQ-042 default A: award it in BindToClose); SMOKE.md checks it. Each step
is appended to `next/publish-log.json`.
**Two versions at once:** until the bleed-off ends, old Lobby servers still teleport crews into new Trip servers
(Trip publishes first, the start place last). A release that changes TeleportData (`tech.data.teleport_data`) must
accept the old shape on the new side; G2 warns when teleport code changed and SMOKE.md adds a mixed-version row.
**Live data:** the Luau tests run in the production universe, so specs must not touch DataStores (references/gates.md).
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
- Target: the newest published release older than the one live now (history.json); its place files are archived
  under `<R>/<version>/places/` (verified by sha256 before use). After one rollback, `rollback` refuses to go further
  unless the owner names the target: `--to VERSION`. ROLLBACK.md always names what is live now (after a rollback:
  the restored release with the rollback's version numbers). First release through the train: record the live
  version numbers before publishing (`rel baseline --place Lobby=N --place Trip=M`) so ROLLBACK.md has a target.
- API: `rel rollback` (dry run: publish-only requests), then `rel rollback --live --confirm <target> --by owner
  --restart` (immediate restart; this is an emergency). New version numbers, old content; the bad release is marked
  `rolled_back` in history, its changes come back in the next collect, its version is never reused, and its
  `publish-log.json` is kept (the rollback writes `rollback-log.json`).
- A place whose archive holds classes the API does not update (unions, SurfaceAppearance...) is rolled back through
  Creator Hub: re-publishing over the API would leave the bad build's versions of those parts live.
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
