# Licensing gate

Rule (canon, proposed): `bible.py get av.audio.licence`. Platform facts: `bible.py get tech.audio.rights`. Open:
OQ-036 (community Creator Store uploads, default refused). `register` enforces this; nothing unlicensed reaches
assets.json, and `validate` re-checks every entry.

## Allowed sources (`--source`)
| source | origin (`--origin`) | proof (`--proof`, required) | notes |
|---|---|---|---|
| `owner_upload` | `self-made` | project file or "made by owner DATE" | includes recordings the owner made himself |
| | `commissioned` | the contract or message granting rights for use in the game | name the author in `--credit` if they asked |
| | `cc0` | the licence URL on the source page | keep a copy of the page; sites change |
| | `purchased` | receipt + licence URL; the licence must cover games or interactive media and uploading to a platform | many "royalty-free" packs allow games but forbid redistributing the raw files: keep the uploaded asset private to your experiences and never distribute it on the Creator Store |
| `roblox_licensed` | (none) | the Creator Store URL | needs `--id`; `--creator` must be Roblox or a Roblox audio partner shown on the asset; anything else warns; `--community` is refused (OQ-036 A). Licensed for use inside Roblox only: do not reuse it in trailers or ads |
| `placeholder` | `rr-soundsmith synth` | none | files must be named `PLACEHOLDER_*` (the INFO chunk says so); never ship |

`owner_upload` and `roblox_licensed` need `--id` (the asset id the game plays). Every uploaded file also passes
`analyze` first: empty, silent, truncated or clipped files are refused. `--credit` records an author who asked to be
named (LICENCES.md lists it for the game description).

## Refused (register exits 1, nothing written)
NC (non-commercial), ND (no derivatives: levelling and trimming are edits), SA (share-alike), CC-BY (canon
av.audio.licence names self-made, commissioned, CC0 and game-licensed purchases only; the owner can extend the rule,
then the gate follows), an origin `cc0` whose licence text names attribution, rips from games, films, YouTube or TikTok
(matched as whole words: "Ripley" is fine), "free download" with no licence, unknown or "not sure" terms, a
PLACEHOLDER-tagged file registered as final, a community upload of Creator Store audio. The gate reads text: it
cannot prove a claim, so the proof (receipt, URL, contract) is what the owner keeps.

## Why this strict
Roblox requires the uploader to hold the rights (tech.audio.rights); a takedown or a moderation strike silences the
sound in live servers and can hit the owner's account. Roblox-licensed tracks and effects come with rights inside
Roblox; community uploads carry only the uploader's claim.

## The owner's steps (never done by Claude)
Uploading audio, accepting the Audio Terms, spending on packs and publishing are the owner's gate. Claude prepares
files (`analyze --fix-out`), briefs and the register commands, then hands over.
