# Routing: request type -> specialist skill (steps 1, 4, 5, 6, 9)

Find each specialist once at step 1 and store it: `mission_state.py set <M> env.skill.<name>=<folder>`
(`dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path '*<name>/SKILL.md' 2>/dev/null | head -1)"`).
Not found: the row's fallback applies; say so in the readback. The maker's order file names the specialist's
SKILL.md steps and its command lines; the maker does the specialist's work through its scripts, never ad hoc.
Short names (`fdy`, `ui`, `vfx`, `feel`, `sound`, `bible.py`) are each skill's own script, defined on its SKILL.md
Paths line. Canon for every row comes from rr-bible (`bible.py get <slice>`), never from memory or this file.

| request | skill (`--kind`) | inputs in `<M>/src/<d>/` | maker does (step 5) | pre-flight gate (step 6) | critic (7-8) | export (step 9) |
|---|---|---|---|---|---|---|
| coach, wagon, tank, hut, signal box, shelter, crates, drums, barriers, track (`fdy list --match` hits) | rr-asset-foundry (3d) | `plan.json` (preset + `--set`) | `fdy make <family> --preset P --set k=v --out <M>/src/<d> --renders full` | exit 0 of `make` (no FAIL line) | `fdy crit` into `<M>/critique-<group>/` | `fdy verify <variant>`; copy to `<M>/export/<d>/` with `families/<family>.py` in place of build.py |
| any other 3D build (depot, station, bespoke prop) | none (3d) | `build.py` | `blender_kit` build (agent-orders "Maker v1") | kit checks (SKILL.md step 6) | multiuse-critic Profile A | `roblox-export.md` 3D; recurring shape: foundry "Promote a mission build" |
| HUD, screen, modal, lobby panel, buttons, chips (fixed layout) | rr-ui-foundry (ui) | `spec.json` + icons | its SKILL.md steps 1-5, `RR_UI_KIT=<M>/kit` if the kit changes | `ui validate` + `ui render` (replaces `render_design.py`) | `ui crit` into `<M>/critique-<d>/` | `ui build <spec> --out <M>/export/<d>/` = BUILD PASS (replaces hand-made layout parity) |
| scrolling lists, web pages, a Design canvas only | none (ui) | canvas / HTML | agent-orders "Maker v1" | `render_design.py` | multiuse-critic Profile B | `roblox-export.md` UI |
| effects, particles, lighting looks | rr-vfx-lighting (mixed) | `vfx init <M>/src/fx` | its steps 1-7 with `--presets <M>/src/fx` | its step 2 + `vfx build --no-check` | `<M>/critique-fx-*` | `vfx build --out <M>/export/fx --only <pack>` |
| juice: shake, tweens, hit-stop, flashes, haptics, lever feel | rr-game-feel (mixed) | `feel.json` copy | its steps 1-7, `--presets <M>/src/feel/feel.json` | `validate --strict` + `build --no-check` | `<M>/critique-feel-<set>` | `<M>/export/feel/` |
| sound map, mix, placeholders | rr-soundsmith (mixed) | `export RR_SOUND_PRESETS=<M>/src/sound` | its steps 1-8 | its step 2 + `sound build --no-check` | `<M>/critique-sound` | `<M>/export/sound/`; `sound promote` only on the owner's go |
| analytics, prices, experiments, economy | rr-data-and-money (no kind: run standalone) | its `<R>/presets/` | its SKILL.md route | `track.py validate`, `luatest.py --gate`, `track.py scan --strict`, `econ.py validate`, `econ.py guard --gate` | none (numbers, not visuals) | its outputs; gameplay-touching products go to risky-rails-mechanic-reviewer |
| new mechanic or rule change | risky-rails-mechanic-reviewer (standalone) | the idea text | review before any build | its verdict | none | none |
| thumbnails, icons | risky-rails-thumbnail-ideas, judged by multiuse-critic | concept brief | its steps | 200 px test | multiuse-critic | none |
| "ship it", release, patch notes | rr-release-train (standalone) | done missions (`status=done`) | none: it reads missions | its gates | none | its publish plan (owner-run) |

## Cross-cutting gates (any row)
- **Luau in the export** (ui, feel, fx, sound, foundry `studio_setup.lua`, hand-written scripts): `python3
  <rr-exploit-guard>/scripts/guard.py scan <M>/export --out <M>/security --fail-on high` before export; fix or list
  every finding in the debrief. Its review follows the same critic route as step 7 (`env.critic_mode`).
- **Canon:** a specialist that finds a gap drafts an OQ (`bible.py add-question ... --dry-run` when the owner is away)
  and labels work "assumed (OQ-nnn default)"; list the drafts under Needs owner.
- **Mixed missions:** one T0 in mission.md names the shared event names (rr-game-feel events drive UI transitions,
  fx cues and sounds), then each specialist chain runs in parallel; export tasks depend only on their own final pass.
- **Specialist critic hand-offs** all end in `<critic>/scripts/critic_kit.py build`; independence rules are
  multiuse-critic's and SKILL.md steps 7-8 (no self-scores toward the bar).
