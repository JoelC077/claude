# Patch notes: edge cases

`rel notes` writes `next/NOTES_BRIEF.md` with everything a normal release needs: the file format, a good/bad pair,
the player changes (with wording hints) and the voice slice read from rr-bible (tone, lexicon, banned names, store
rules, parked sidings, D-007, the OQ-038 voice default). Read the brief, not this file, unless a case below applies.
Never restate canon here or in the notes beyond what a change says.

## What `notes-check` enforces (every line of both .src files)
- Bullets end with `[C-n]` tags of in-build **player** changes; every in-build player change is covered somewhere
  (or re-marked `--audience internal` because players cannot notice it).
- Headline (`# `): free company voice, but its numbers must come from a change, and no promises or sidings.
- Any other line (notice, sign-off) is a `world.lexicon` string verbatim (trailing `.`/`!` allowed) or ends with the
  `[C-n]` tag of the change it is about. A lexicon joke is not a licence to comment on something undecided (a
  "TEMPORARY" sign on a building whose placement is an open question is a claim: leave it out).
- No promises of future content (`notes.promise_words` in presets: soon, next week, coming soon, stay tuned...):
  plans are the owner's to announce.
- Parked sidings (`release.alpha.sidings`) only on a tagged line whose change text names them.
- Numbers: in bullets they should appear in the tagged change's title or note (warning); outside bullets they must
  (error). Version strings are ignored.
- D-007 on every line: nothing ties money (Robux, passes, shop, buy) to odds, luck, revives or rerolls.
- Store text: no "free", no giveaway, no untrue update tag (`release.store.metadata_rules`); title one emoji max.
- Internal jargon (presets `notes.jargon`) is a warning; `bible check` runs on the stripped outputs.
- Outputs are written only on PASS; a FAIL deletes stale `PATCH_NOTES.md`/`STORE_UPDATE.txt`.

## Edge cases
- **A wording hint says "do not say X"** (e.g. placement not final): binding, even though the check cannot see it.
- **Internal-only release:** no notes needed (G3 N/A); if the owner wants a post, one tagged line per change still.
- **Two changes read as one:** one bullet, both tags: `[C-5, C-6]`.
- **Balance change:** give before and after only when the change's text has both numbers; otherwise describe it.
- **Fix:** say what the player saw break, then what happens now.
- **Store title change:** second line `TITLE: Risky Rails <one emoji max> [NEW BRACKET]` (`release.store.title`,
  `release.ops.update_cadence`).
- **A headline feature no place calls yet** (G9 "modules nothing requires"): the notes describe the change as the
  owner confirmed it; raise the G9 finding with the owner before posting.

## After the check
`PATCH_NOTES.md` and `STORE_UPDATE.txt` are what the owner posts; show them in chat for a final read. Posting to
Discord or editing the store page is the owner's action.
