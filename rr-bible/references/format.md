# Bible format (read only when editing structure or adding a domain)

## Files

| file | holds |
|---|---|
| `canon/sources.md` | source registry: `` - `ID` — title \| date \| where `` (IDs: capital letters and digits) |
| `canon/<domain>.md` | fact lines grouped in sections; domains: identity, style, world, gameplay, economy, tech, ui, av, assets, release |
| `canon/decisions.md` | `### D-nnn · YYYY-MM-DD · title` blocks, append-only |
| `canon/open-questions.md` | `### OQ-nnn · title` blocks; removed when decided |

A new domain is just a new `canon/<name>.md` with a `# Title`, one purpose line and `## section · Title` headings; the script discovers it. Keys in it start with `<name>.`.

## Fact line

```
- `file.section.name` = `value` | note | src: ID, ID detail, owner 2026-09-28 | status | check: REGEX
```

- `file` = the file stem; `section` = the id of the `## section · Title` it sits under (lint enforces both).
- `value`: no backticks. Colours are `#RRGGBB` upper-case (that is what makes them tokens). Fonts live in `style.type.*` as plain family names.
- `note` optional; no ` | ` inside. Reference open questions and decisions by id (`OQ-004`, `D-013`); lint checks they exist. A `conflict` fact must name its OQ.
- `src`: comma-separated; the first word of each part must be a source ID or `owner`.
- `status`: canon, measured, platform, proposed, assumed, conflict, superseded.
- `check` (optional, last): a regex with at least one capture group; `bible check FILE` compares every captured number with the value and flags differences. Write it to match phrasings people actually use and test it on a sample line (`add-fact` rejects regexes without a group).
- One fact per key. To change a value use `add-fact KEY VALUE --replace`; keep history by adding a `*_old` key with status superseded when the old value still appears in shipped work.

## Open question block

```
### OQ-nnn · Title
- status: open
- raised: YYYY-MM-DD
- src: ID, ID
- context: one or two sentences with the evidence on each side
- options:
  - A: ...
  - B: ...
- default: A (why; this is what skills do until the owner decides)
- affects: fact.key, fact.key
- blocks: what waits on it
```

## Decision block

```
### D-nnn · YYYY-MM-DD · Title
- decision: the choice, in one or two sentences
- by: owner (how: adopted plan, chat, as built)
- src: owner YYYY-MM-DD, ID
- from: OQ-nnn        (when it came from a question)
- affects: fact.key   (optional)
```

Numbers never get reused: a decided OQ keeps its number in the decision's `from:` line, and `add-question` counts those.

## Status discipline

- Only the owner makes `canon`. A Claude-authored doc's recommendation is `proposed`, even when well argued. A plan the owner then built on is `canon` with the build as evidence.
- `measured` needs an artefact: an export, a render, a Studio screenshot, a board status, a mission ledger.
- Mission defaults taken while the owner was away are `assumed` until he confirms.
- When two sources disagree, write the fact once as `conflict` with the most likely value, note the other value, and open an OQ with both as options.
