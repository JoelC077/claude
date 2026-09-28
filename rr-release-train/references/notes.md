# Patch notes: format and voice

Read `next/NOTES_BRIEF.md` only; it holds the player changes and the voice slice pulled from rr-bible when it
was written (tone, lexicon, banned names, store rules, parked sidings, D-007, the OQ-038 voice default). Do not
restate canon here or in the notes beyond what a change says.

## Files you write in next/
`PATCH_NOTES.src.md` (the Discord post; limit in presets `notes.discord_max`, one post):
```
# Risky Rails 0.1.0-alpha.2: <headline in the company voice, one line>

<optional one-line notice from Management, lexicon verbatim if used>

- <one player-visible change, plain and exact>. [C-4]
- Fixed: <what the player saw go wrong>, now <what happens>. [C-7]
- <two changes that read as one>. [C-5, C-6]

<one sign-off line in the company voice>
```
`STORE_UPDATE.src.txt` (the update line in the store description; `notes.store_max`), optionally a second line
`TITLE: Risky Rails <one emoji max> [NEW BRACKET]` when the update renames the bracket (`release.store.title`,
`release.ops.update_cadence`). Tags are allowed and stripped here too.

## Rules the check enforces
- Every bullet ends with `[C-n]` tags of in-build **player** changes; headline, notice and sign-off carry none.
- Every in-build player change is covered somewhere (or re-marked `--audience internal` because players cannot
  notice it).
- Nothing about internal work, tools, skills, missions, critics, canon IDs or engine jargon (list in presets).
- D-007: no line may tie money (Robux, passes, shop, buy) to odds, luck, revives or rerolls.
- Store text: no "free", no giveaway, no untrue update tag (`release.store.metadata_rules`); title one emoji max.
- Parked sidings (`release.alpha.sidings`) are named only if a tagged change ships them.
- Numbers in a bullet should appear in its change's title or note, or be checked against canon (warning).
- `bible check` runs on the stripped outputs (banned names, contradicting numbers).

## Voice (OQ-038 default A, until the owner decides)
Headline and one sign-off line in the notice-board voice of the under-resourced train company; every bullet
plain, short and exact: what the player sees, where, and what to do differently. Write for a 13-year-old on a
phone: one idea per bullet, no hedging, no hype, no emoji in bullets. Lexicon strings are used verbatim or not at
all. Fixes say what the player saw break. Balance changes give the before and after only when the change's text
has both numbers.

Good: `- The firebox glow flickers when coal runs low, so the stoker notices before the boiler does. [C-2]`
Bad: `- Improved the crisis system for a better experience! [C-2]` (vague, hype)
Bad: `- Refactored CrisisManager to use a RemoteEvent. [C-4]` (internal)
Bad: `- The Golden Lever pass boosts your odds at forks. [C-9]` (D-007)

## After the check
`PATCH_NOTES.md` and `STORE_UPDATE.txt` are what the owner posts; show them in chat for a final read. Posting to
Discord or editing the store page is the owner's action.
