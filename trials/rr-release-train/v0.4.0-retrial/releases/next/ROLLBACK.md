# Rollback plan · 0.4.0

Trigger: any P0 smoke fail, joins failing, coins or purchases lost, or an error spike. Decide within minutes; a rollback is cheaper than a hotfix under pressure.

Target: the versions live before this publish: NOT RECORDED: before publishing, `release.py baseline --place Lobby=N --place Trip=M` (Creator Hub > place > Version History).
Creator Hub > Creations > the experience > Places > each place > Version History: restore that version, then Restart Servers for Updates.

Data: DataStore writes are not rolled back. If this release changed the saved profile shape, the previous build must still read profiles this one wrote (PlayerData_alpha1); if it cannot, fix forward instead.
After: post one line in the patch-notes channel (what broke, that it is rolled back), keep the release folder for the post-mortem, fix, re-run the train with a new version number (never reuse one).
