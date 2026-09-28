# v0.4.0 dry-run release trial (2026-09-28)

"v0.4.0 Ticket HUD + depot buildings", run by following rr-release-train's SKILL.md. Nothing was published;
`--live` and every owner-only command were never used. Friction: `../FRICTION.md`.

Inputs
- Git history of /home/user/claude (tooling repo: summarised, not listed) and missions 260927-depot-buildings,
  260927-ticket-hud (both marked in-build as a TRIAL ASSUMPTION: the owner has not confirmed they are in Studio).
- Place files are stand-ins (`make_places.py`, no Studio here): the builder fixture's base scripts plus the real
  HUD modules and demo LocalScript and one MeshPart per depot/hall parts.csv row. `places-pre/` = stamp 0.3.0,
  `places/` = after pasting `rel stamp`'s RR_Version.
- Fake Open Cloud IDs: universe 9990001, Lobby 9990011 (start), Trip 9990012. `RR_RELEASES_ROOT=v0.4.0/releases`.

Deliverables (`releases/`)
- `CHANGELOG.md` (Keep a Changelog, 0.4.0) · `next/PATCH_NOTES.md` + `next/STORE_UPDATE.txt` (notes-check PASS)
- `next/GATES.md`: NO-GO (G5 no security verdict, G6 bug bash); warnings G1 tag, G4, G8 0/2 certified, G9, G10
- `next/PUBLISH_PLAN.md` (API route, Trip then Lobby) · `next/SMOKE.md` · `next/ROLLBACK.md` · `next/RR_Version.lua`
- `publish-dryrun.txt` + `next/publish-dryrun.json` (every request; the save/publish uploads carry a curl line, the
  Luau test and restart steps do not; blockers: approval, key, host)

Found beyond the gates (owner, before any publish): HUD icon ids are `rbxassetid://0` (upload icons first);
NotificationDemo LocalScript must be deleted; OQ-001 (HUD skin, blocks final HUD export; default C, build ships
A) and OQ-015 (Main Hall placement) are open; HUD standing 6/8 on multiuse-critic with its last fix pending;
0.4.0 vs the alpha tag (OQ-037) needs the owner's call.

Corrections after independent review: the notes check was not strong (the untagged notice line, which reused the
TSR sign gag on the Main Hall of open question OQ-015, passed untraced), and the headline HUD has no caller in
Trip and only the demo in Lobby. Both are now caught by the skill; see `../v0.4.0-retrial/`.
