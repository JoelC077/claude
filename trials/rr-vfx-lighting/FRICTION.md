# FRICTION: rr-vfx-lighting trial (2026-09-28)

Task: preset pack = steam + chimney smoke + brake sparks + coal dust; looks grassland day, dusk, night run;
Luau + JSON + preview renders + contact sheet + multiuse-critic pass-1 critic.md (profile B).
Each entry: where, what went wrong or was missing, evidence, suggested fix. Severity: H (blocks or misleads),
M (costs time/tokens or needs a workaround), L (wording/polish).

1. **M · Step 1 edits the skill's own presets.** Outside a mission, SKILL.md step 1 says "Pick or edit presets in
   `<fx>/presets/`": a standalone request would modify the shipped skill folder. Only the "Inside a mission"
   section says to copy `presets/` and set `RR_VFX_PRESETS`. Workaround: copied to `trials/.../src/fx/` and set
   the env var. Fix: make "copy presets to a work dir + `RR_VFX_PRESETS`" step 1 for every run.
2. **M · No rule for requests that name effects or looks the pack lacks.** "brake sparks" and "dusk" have no
   preset or time (pack has `sparks_axle`, `sparks_powerbox`, `golden`). SKILL.md never says whether to map to the
   nearest preset or author a new one, nor how to add a new anchor/time (presets.md covers value forms only).
   Decision taken: author `sparks_brake` (new anchor `BrakeShoe`) and a `dusk` time, since golden (ClockTime 17.3,
   sun ~10 deg up) is not dusk. Fix: one line: "a named effect/look the pack lacks: author it (new anchor in
   `stand.anchors`, new time listed in `biomes[b].times`), never silently substitute".
3. **L · Canon-gap recording has no dry-run path.** "Missing canon: record it with `bible.py add-question`" writes
   to the shared bible; in a trial or a read-only run there is no instruction to use `--dry-run` (bible.py supports
   it). A preset `oq` must name a real OQ id, so a dry-run question cannot be cited; the work can only be labelled
   in prose.
4. **H · `vfx preview all [NAMES]` silently ignores NAMES.** preview.py `lighting()` uses `a.names` only when
   `a.what == "lighting"`, `effects()` only when `== "vfx"`. So step 3's `preview all` always renders the 8 default
   looks + every preset, and a new look (dusk, not in `preview.default_set`) is never rendered. Workaround: two calls,
   `preview lighting <looks>` then `preview vfx <presets>` into the same `--out`. Fix: pass NAMES through by type.
5. **H · POV composites are hard-coded** (preview.py `POV_SETS`: crisis, cruise, boiler, night, rain). For this pack
   the vfx `contact.png` hero became `pov_crisis` showing `steam_valve` (not in the pack) and `pov_boiler` was on the
   sheet, while `sparks_brake` and `coal_dust` got no player-view frame at all. Workaround:
   `tools/pack_pov.py` calls `fxsim.pov` directly over each look (+ the look's `fx_on`), pc and phone tier. Fix:
   derive POVs from NAMES (named effects over each named look) or keep POV sets in data.
6. **M · No single board for a mixed pack.** The skill yields `lighting/contact.png` and `vfx/contact.png` and says to
   run one CRIT per group; an effects+looks pack (the usual owner request) needs one board and one critic. Workaround:
   `contact_sheet.py` by hand + `tools/board_facts.py` to merge facts (lighting table, 4 effect rows, pack POV numbers,
   pack-relevant phone budget lines). Fix: `vfx preview pack` or `vfx crit --from DIR --from DIR`.
7. **M · `vfx crit` brief is group-generic.** `brief()` is hard-coded: Purpose "for crises, fails and running",
   worries naming OQ-027 rain / OQ-028 derail (not in this pack); `--group` accepts only lighting|vfx. Hand-edited 3
   lines of `crit/brief.md`.
8. **M · Profile mismatch.** Task asked for profile B; `vfx crit` hard-wires Profile F and prints `--profile F`. B's
   criteria (job and hierarchy, legibility, layout) are UI criteria; F (signal, form and motion, colour and value,
   phone read, style, polish) fits a look-dev board. Built B as asked (merged `crit/rubric.md` holds both, so
   `critic_kit.py build --profile B` worked). Fix: SKILL.md one line: "judging a preview board = Profile F; B is for UI".
9. **M · No cab camera.** Cameras are roof3p and door1p only (lookdev_bpy `camera()`); `coal_dust` (anchor Firebox,
   inside the cab) and `firebox_glow` never appear in any POV, only in strips. Canon has `tech.camera.cab_view` (eye
   about 12 above rail). Fix: add a `cab1p` camera.
10. **M · Rail-level effects are invisible from the roof POV, and facts do not say so.** Diagnostic on
    `pov_grassland.day`: `sparks_brake` 44 live, 37 occluded by the train, 7 below ground, 0 visible; door1p 18 visible
    at under 0.1% of the screen. `fxsim.pov` returns `hidden_by_depth` but `write_vfx_facts` drops it, so an effect
    can vanish from every player view with nothing flagged. Fix: per-preset visible/hidden counts in facts.md and a
    warning when a named effect covers under ~0.1% of every POV.
11. **M · "Fix blank or broken views" has no threshold for a too-weak effect.** First `sparks_brake` (Rate 28, Size
    0.32) was legal and gated PASS but read as ~3 sub-2px streaks (strip "live 12"). Tuned once by eye before the
    critic (Rate 60, Size 1.0, outward dir); that is maker judgement the skill neither sanctions nor forbids. Fix: a
    measured floor in facts (px coverage or px/stud x size) instead of eyeballing.
12. **L · Stand gauge contradicts canon.** lookdev_bpy `track()` puts rails at z +-2.4 (4.8 apart);
    `tech.units.gauge` = 8. Wheel anchors placed to canon (z +-4.2) sit outside the preview rails.
13. **L · Event loops start on.** `VFX.attach` starts loops active (`opts.enabled ~= false`); brake/valve-style loops
    need `{enabled = false}` + `setActive`. SKILL.md Runtime and the export README do not say so; found by reading
    RR_VFX.lua.
14. **L · Export is always the whole library.** No subset/pack build: the owner asking for 4 effects + 3 looks gets 13
    presets and 19 looks; pack wiring had to be written by hand (`PACK.md`).
15. **L · New effect/look authoring is undocumented.** Adding an anchor (`stand.anchors`), a time (`times` +
    `biomes[b].times`) and budget sets for the new preset (`budgets.json` sets) all worked, but presets.md never lists
    this checklist; the budget sets would silently omit a new preset unless the maker adds sets.
16. **L · Relative CRIT path leaks into the spawn prompt.** `vfx crit crit ...` printed a `critic_kit.py build crit`
    command; the resulting prompt had relative paths, unusable by a caller in another cwd. Rebuilt with an absolute
    path. Fix: resolve CRIT to absolute in `preview.crit()`.
17. **L · Two multiuse-critic copies, resolved inconsistently.** SKILL.md's shell recipe (`find ... | head -1`)
    gives the synced copy under `~/.claude/skills`; `vfx.py` (find_sibling) printed
    `/home/user/claude/multiuse-critic/scripts/critic_kit.py`. Identical today (`diff -rq` clean); nothing warns if
    they drift.
18. **L · critic.md lists no tiles for closeups.png** (Images section shows only its size), so the critic cannot map
    closeup tile numbers to labels without reading the image labels (multiuse-critic `critic_kit.py`, not this skill).

## What worked
- Canon slices via `bible.py get` were fast and exact (brake mechanic, gauge, camera eyes, OQ-026/029 found in 5 calls).
- `validate --strict` + `budget` ran in about a second, accepted the new preset, time, declared colours (with band
  check) and 4 new budget sets first time; build PASS with luaparse + canon check in 2 s.
- Lighting preview: 9 Cycles renders (3 looks x roof/door + 3 phone) in 45 s with measured facts (sun elevation,
  train-vs-world contrast, spawn-edge fog, sepia/blue-sky bands); effects sim + GIFs in 3 s.
- Data-driven runtime: `speed_link` made brake sparks fade as the train stops with no code; the demo LocalScript
  picked up the new preset and look automatically.
- critic_kit accepted the merged rubric; pass-1 critic.md is ~3.6k tokens with facts inline.
