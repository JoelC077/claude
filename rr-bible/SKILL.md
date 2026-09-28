---
name: rr-bible
description: "Risky Rails single source of truth (JARVIS canon): every fact about the game in one sourced, machine-readable place. Identity and pillars, house-style palette tokens and fonts, world names and lobby layout, gameplay constants (crew, speeds, fuel, crises, exact HUD alert texts, difficulty, forks, modifiers), economy and prices, Roblox tech facts (studs, eye heights, FOV, tri budgets, streaming, security), UI tokens, audio/VFX, the asset register, dated decisions and open questions. Use it whenever Risky Rails work needs a fact, number, colour, font, name or string: before building, critiquing, writing copy, pricing or exporting; to export tokens to Luau/CSS/JSON; to canon-check a file ('is this on-brand?'); when the owner decides something; when canon is missing (record an open question); or when asked what is decided or open. Every rr-* skill reads canon through its bible.py instead of restating facts. Not for Roblox questions unrelated to Risky Rails."
---

# RR Bible

The canon for Risky Rails: about 660 sourced facts, 25 open questions and 22 dated decisions, harvested 2026-09-28 from the owner's Drive docs, claude.ai artifacts, past missions and the existing skills. Other skills read slices of it, never whole files, and never restate it.

Paths: `<bible>` = this skill's folder: `dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path '*rr-bible/SKILL.md' 2>/dev/null | head -1)"`. Script: `python3 <bible>/scripts/bible.py` (below: `bible`). Canon files: `<bible>/canon/*.md`. `RR_BIBLE_DIR` or `--canon` points it at another copy.

## Read canon (the token-cheap way)

| need | command |
|---|---|
| one value | `bible get gameplay.speed.normal` |
| a topic, values only | `bible get gameplay.fuel --values` |
| a whole section by bare name | `bible get lever` (ui.lever), `bible get fuel` |
| what sections exist | `bible list` or `bible list style` |
| which palettes exist | `bible get palette`, then `bible get style.brand --values` |
| an open question or decision | `bible get OQ-001`, `bible get D-013`, `bible get questions` |
| don't know the key | `bible search "coal"` (add `--limit 10`) |
| machine-readable | add `--json` |

Rules for readers:
- Pull the smallest slice that answers the question; `--values` unless you need status and source.
- Never copy canon into your own SKILL.md or references. Cite the key (`gameplay.crew.max`) and read it at run time.
- A miss exits 1 and prints close keys plus a few search hits. If the fact truly does not exist, record the gap (below); never invent it.

## What a fact line means

```
- `gameplay.fuel.shovel_pct` = `4` | one shovel load | src: CB, WR | canon   [| check: REGEX]
```

Key = `file.section.name`. Every fact cites source IDs from `canon/sources.md` (or `owner YYYY-MM-DD`). Statuses and how to use them:

| status | meaning | how to use |
|---|---|---|
| canon | owner decided or adopted | rely on it |
| measured | read from the real build, export or render | rely on it; re-measure if the build changed |
| platform | Roblox/external fact, dated | rely on it; recheck before launch-critical use |
| proposed | recommended in a doc, not confirmed | usable; say "proposed" when it matters |
| assumed | a past mission's default, never confirmed | usable as a default; flag it |
| conflict | sources disagree; an OQ names the options | do not pick: use that OQ's default and label output "assumed (OQ-nnn default)" |
| superseded | replaced | never use for new work |

Full grammar, block formats and how to add a domain file: `references/format.md`.

## Never contradict canon

- Numbers, colours, fonts, names and strings come from the bible. Exact strings (alerts, lexicon) are used verbatim.
- If the owner's new prompt contradicts canon, the owner wins: do the work, then record it (decide or add-fact with `src: owner DATE`).
- Visual judgement (is it good, is it on-style at 8/10) belongs to multiuse-critic. The bible supplies the facts the critic's brief needs; never self-score against it.

## Record canon (write through the script, never by hand-editing lines)

1. **A new measured or sourced fact:** `bible add-fact tech.units.coach_len 44 --src "owner 2026-09-30" --status measured --note "measured in Studio"`. Existing key: add `--replace`. New section: add `--title`. Numbers that files must never contradict: add `--check 'REGEX with (\d+)'`.
2. **Missing or undecided canon:** `bible add-question "Coach length?" --option "A: 44 studs" --option "B: 48 studs" --default "A (fits the station platform)" --src DS --affects tech.units.train_len`. Always give a default so work can proceed; label that work "assumed (OQ-nnn default)".
3. **The owner decides:** `bible decide OQ-003 C --by owner --via "chat 2026-09-30"`. Only the owner decides; any other `--by` is refused. It moves the block to decisions.md with the date and prints the affected fact keys: update each with `add-fact ... --status canon --src "owner DATE" --replace`.
4. **A new source:** add a line to `canon/sources.md`: `` - `ID` — title | date | where ``.
5. After any write: `bible lint` (must print `lint OK`).

Write to the repo copy of the skill (the script warns when it is about to write a synced copy under ~/.claude/skills/synced). Never commit or push unless asked.

## The canon gate

Before handing over any UI, HTML, SVG, CSS, Luau, build script or player-facing copy:

`bible check <file>` (exit 0 = PASS, 1 = FAIL, 2 = usage error; `--json` for tools)

It flags:
- **hex:** every colour (#hex, rgb/rgba, Color3.fromRGB/fromHex/new, hex("..") helpers) not within dE 2 of a token (`--near`), naming the nearest token; warns on superseded or undecided (conflict) tokens; notes when a colour sits in the Dead Rails sepia band or the Land or Die blue-sky band. White and black are neutral.
- **fonts:** CSS/SVG font-family (first family; `--all-fonts` for fallbacks), Google Fonts links, Enum.Font, rbxasset font families, @fontsource.
- **names:** banned phrases (`world.banned.*`), e.g. "Flight or Die"; undecided names (Trash Railways) warn.
- **numbers:** facts with a `check:` regex (crew max 6, 1 stud = 0.28 m, FOV 70, segment 512, poles 128, HUD cap 4).

On FAIL: switch to the token; or, for a deliberate one-off, `--allow HEX` and say why in the debrief; or propose it (`add-fact ... --status proposed`). `--skip hex,fonts,names,numbers` narrows the gate. Limits: named CSS colours, images and renders are not scanned (renders go to multiuse-critic); numbers are checked only where a fact carries a `check:` regex.

## Export tokens for builds

`bible tokens --format luau --out RR_Tokens.lua` (ModuleScript: `T.style.brand.hazard_yellow` = Color3, `T.fonts.display`), `--format css` (`--rr-style-brand-ink`), `--format json`. Default: style and ui colours plus fonts, everything but superseded; non-firm tokens are commented with their status. `--canon-only` exports canon/measured/platform only; `--prefix ui.hud_kinds.` narrows it. Regenerate instead of editing the output.

## What is open right now

`bible get questions` lists all 25 with defaults. The ones most likely to bite: OQ-001 HUD skin (heritage brass vs teal-cream/mustard livery, the owner's call), OQ-002 company name, OQ-003 currency naming, OQ-004/OQ-005 trip length and studs per mile, OQ-006..OQ-008 lever rules, OQ-010 Robux in the terminal vs "never sell odds", OQ-020 unreachable project docs, OQ-025 train exterior livery.

## Honest limits

- Snapshot of 2026-09-28. The claude.ai project docs (Visual Identity, Dimension System, Segment Designs, Full Project Summary) and the approved diesel "23" are not reachable from cloud sessions; those domains are partial (OQ-020). A few artifacts were indexed but not harvested (`references/harvest.md`).
- Cloud sessions have headless bpy 5.0 (Cycles), Playwright + Chromium, no Studio: facts from Studio are marked measured only when an artefact or the owner showed them.
- Never publish, spend, message players or change the owner's Claude config: prepare, dry-run and hand the gate to the owner.

## Maintain

- `python3 <bible>/scripts/selftest.py`: exercises every subcommand on a temp copy (must print all passed).
- Re-harvest or extend from new docs: `references/harvest.md`. Remove `__pycache__` after running scripts.
