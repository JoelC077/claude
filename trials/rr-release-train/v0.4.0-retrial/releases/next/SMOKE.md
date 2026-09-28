# Smoke checklist · 0.4.0

Run on live servers right after publishing. Record: `release.py smoke --result S1=pass,S2=fail,S6=skip --by owner`. Any P0 fail -> roll back (ROLLBACK.md).

| id | prio | check | result |
|---|---|---|---|
| S1 | P0 | Join a fresh live server: no red errors in F9; F9 server console `print(require(game.ReplicatedStorage.RR_Version).version)` prints 0.4.0 | |
| S2 | P0 | One full trip with 2+ players through the funnel: join > picked up tool > shovelled coal > pulled lever > first bank > run end | |
| S3 | P0 | Coins banked at results survive teleport home and a rejoin (award coins on the server at results, end the session, and only then teleport) | |
| S4 | P1 | Creator Hub > Analytics > Error Report and the F9 server log: no new error spike in the first 30 minutes | |
| S5 | P1 | Live check: publish; full trip with 3+ players incl. one phone; Studio Incoming Replication Lag about 200 ms; F9 open; pass = smooth scenery, lever and HUD respond within 0.5 s | |
| S6 | P1 | C-1 works as the patch notes say: New buildings in the Depot Lobby: the stone station house and the Main Hall · walk it on a phone: scale, collisions, colours | |
| S7 | P1 | C-2 works as the patch notes say: Alerts got a makeover: every alert now arrives as a railway ticket · fire it through real play on a live server (e.g. a crisis on a Trip), not a demo script · watch: UIStroke on rotated stamp, hazard tile scale, "+N MORE" chip position after UIScale. | |
| S8 | P1 | Server restart for the update: a crew mid-trip when its old server closes keeps its banked fare (OQ-042 default A: awarded in BindToClose, like a fail) | |
| S9 | P2 | Old servers drained: every server you join shows the new version (S1 check) | |
