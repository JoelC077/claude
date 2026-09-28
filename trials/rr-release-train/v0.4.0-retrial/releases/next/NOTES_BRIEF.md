# Notes brief · 0.4.0 (alpha)

Everything needed is here. Write the two files next to this brief, then run `release.py notes-check`.

## PATCH_NOTES.src.md (the Discord post, <= 2000 characters once tags are stripped)
```
# Risky Rails 0.4.0: <headline in the company voice; numbers only if a change has them>

<optional notice: a lexicon string verbatim, or a line ending with the [C-n] of the change it is about>

- <one player-visible change: what, where, what to do differently>. [C-4]
- Fixed: <what the player saw go wrong>, now <what happens>. [C-7]

<sign-off: a lexicon string verbatim, e.g. Mind the gap>
```
Good: `- The firebox glow flickers when coal runs low, so the stoker notices first. [C-2]`
Bad: `- Improved the crisis system for a better experience! [C-2]` (vague, hype) · `- Refactored X to use a RemoteEvent. [C-4]` (internal)
The check: every line traces (bullets by tag; notice and sign-off are lexicon verbatim or tagged); say only what the change says (a wording hint marked 'do not say' is binding); no promises (soon, next week); numbers only from the change; parked sidings only on a tagged line whose change ships them; D-007 (no money next to odds or luck); no internal jargon; one emoji max; `bible check`.

## STORE_UPDATE.src.txt: one line <= 300 characters (tags allowed); optional second line `TITLE: ...` (<= 50, one emoji max, pattern release.store.title below). No "free", no giveaway.

## Player changes (cover every one)
- [C-1] Added: New buildings in the Depot Lobby: the stone station house and the Main Hall | wording hint: Depot: two-gable stone station house, front faces the yard. Main Hall: the big hall of the lobby (placement not final, OQ-015: do not say where)
- [C-2] Changed: Alerts got a makeover: every alert now arrives as a railway ticket | wording hint: Same alerts as before (crises, junctions, fares, crates, crew) with a new look: railway-ticket card with a stub, punch notches and a rubber stamp; they stack bottom-right, clear of the jump button on phones

## Not for players (never mention)
- (none)

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
