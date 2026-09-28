# Notes brief · 0.1.0-alpha.1 (alpha)

Write two files next to this brief, then run `release.py notes-check`:
- `PATCH_NOTES.src.md`: the Discord post. `# ` headline, bullets, one sign-off line; <= 2000 characters once tags are stripped.
- `STORE_UPDATE.src.txt`: one line for the store description, <= 300 characters; optional second line `TITLE: <experience title>` (<= 50 characters, pattern below).
Rules: every bullet starts `- ` and ends with the tags of the changes it describes, e.g. `- Coal lasts longer on Easy. [C-4]`; headline and sign-off carry no tags. Cover every player change; say only what the change says; numbers only from the change or canon; nothing about internal work.

## Player changes (cover every one)
- [C-2] Added: Coal low alert now flashes the firebox | wording hint: When coal runs low the firebox glow flickers so the stoker notices.
- [C-3] Fixed: Lever could be pulled twice after it locked
- [C-6] Added: New depot and main hall in the Depot Lobby | wording hint: stone station house and a bigger hall north of the queue pads
- [C-7] Added: New ticket-style HUD alerts | wording hint: alerts arrive as punched tickets; up to 4 stack

## Not for players (never mention)
- [C-1] Rojo project
- [C-4] Split supply terminal module
- [C-5] Tweak coach seat colours

## Voice (read from rr-bible just now)
- `identity.tone.company`: an incompetent train company: under-resourced but still operating; slapstick safety failures, not grim horror
- `identity.tone.comedy_tell`: signage and props carry the joke (OUT OF ORDER, PROBABLY FOREVER; days without an accident: 0)
- `identity.tone.not`: not a western, not zombies, not horror, not a train simulator
- `release.store.title`: Risky Rails [one emoji] [PULL THE LEVER]
- `release.store.metadata_rules`: no "free", no giveaway, no unrelated tags, no update tag that is not true
- `release.alpha.sidings`: diesel train, client-side world, "run it again" vote, rejoin after disconnect, analytics funnel, Monday parking lot (cab button behaviours, radio dispatcher, junction lamp, cab dressing, bullet train)
- lexicon (verbatim when used): OUT OF ORDER, PROBABLY FOREVER · days without an accident: 0 · DO NOT PRESS · WIRES. DO NOT LICK. · HIT IT IF IT FREEZES · No smoking, no stoking · Mind the gap · Retrieved by the company. 5-coin recovery fee. · LOW BRIDGE · YOU'RE FIRED · Employee of the Month ... Disciplinary Hearing · Shovel coal / Fix what breaks / Pick the route · Waiting for {name} to board... · loading coins... · your coins are saved · CLIMB UP! Grab it on the roof! · TEMPORARY (dated four years ago) · clearance warning posted inside the tunnel, where it is useless
- never write: Flight or Die · Trash Railways · free Robux · giveaway
- D-007 Never sell odds: Monetise time, status and identity only. Nothing sold changes a fork's odds; no revives, no rerolls.
- voice rule (OQ-038 default A, assumed until the owner decides): headline and one sign-off line in the company notice-board voice (the under-resourced train company, lexicon jokes), every bullet plain and exact; posted to Discord plus a one-line update blurb for the store description
