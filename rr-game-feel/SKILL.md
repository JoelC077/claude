---
name: rr-game-feel
description: "Risky Rails (Roblox) game feel, the juice: one client Luau runtime plus per-event presets for tweens and easing, trauma camera shake, camera kicks, hit-stop, UI punch and pop, screen and element flashes, FOV kicks, haptics (HapticEffect, HapticService fallback) and the lever-pull drag feel, with tuning knobs, subtle/default/loud profiles, reduce-motion and flash-safety rules, a generated feel spec per event, curve plots and mock phone previews made in the cloud, and hand-off to multiuse-critic. Use whenever Risky Rails work mentions feel, juice, game feel, screen shake, camera shake, hit-stop, hitstop, freeze frame, punch, pop, bounce, easing, tween curves, flashes, rumble, vibration, haptics, lever feel, satisfying, impact, snappy, reduce motion or motion sickness; when a HUD, lever, crisis, fail or reward moment needs to feel better; or for feel deliverables in rr-mission-control missions. Not for particles or lighting (rr-vfx-lighting), sound (cues only) or static UI layout."
---

# RR Game Feel

Juice for Risky Rails as data: presets in JSON, one Luau runtime that reads them, specs, plots and previews
generated from the same numbers, quality judged by an independent critic. Precise, proactive, no fluff.

Paths (find by glob, never hard-code): `<feel>` = this folder;
`<bible>` = `dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path '*rr-bible/SKILL.md' 2>/dev/null | head -1)"`;
`<critic>` = the same with `*multiuse-critic/SKILL.md`. The scripts find both themselves (env overrides
`RR_BIBLE_SKILL`, `RR_CRITIC_SKILL`, `RR_FEEL_PRESETS`). `feel` below = `python3 <feel>/scripts/feel.py`.

## Canon first
Read the slice you need through rr-bible, never from memory: `bible.py get av.feel --values`, `get ui.hud.motion`,
`get ui.hud.crisis_extra`, `get ui.lever`, `get gameplay.alerts`, `get tech.feel` (HapticEffect, ReducedMotionEnabled,
GetValue), `get tech.camera`, `get identity.pillars`, `get questions`. Presets cite canon as `{"v": n, "canon": key}`
and colours as `@key`; `feel validate` proves they agree. Missing canon: `bible.py add-question` with options and a
default, cite the OQ in the event, label the work "assumed (OQ-nnn default)". The owner's new words beat canon: do
the work, then record it (`add-fact ... --src "owner DATE"` or `decide`).

## Workflow
1. **Pick or edit presets** in `<feel>/presets/feel.json`. Read `references/schema.md` first (channel types, props,
   `before`, reduce-motion modes, limits). `feel list [--group G]` shows every event with tier and loudness;
   `feel show EVENT` prints its spec (add `--rm` for reduce motion, `--json` for data).
2. **Gate:** `feel validate --strict` must PASS: schema and Roblox enums, canon agreement, colour tokens (red only
   for tiers 1-2), OQ refs, comfort limits in phone pixels, flash rate and peaks, hit-stop, reduce-motion still
   communicates, loudness hierarchy by tier, sustained rumble, vfx cue names.
3. **Plot:** `feel plot all --out <dir>` (under a second): `easing.png` (all 11 styles x 3 directions, used ones
   marked), `lever.png`, `sustain.png`, one timeline per event (lanes per channel, hit-stop shaded, reduce motion
   dashed). Look at the plots you changed.
4. **Preview:** `feel preview all --out <dir> [--gif]` writes one folder per group (ui, crisis, info, lever,
   actions, fail): the hero event's peak frame at true phone size, the feel matrix (loudness by tier),
   timelines, a filmstrip, `contact.png` + `closeups.png` (multiuse-critic sizes), `facts.md`, GIFs for the owner.
   Look at each `contact.png` once; fix broken views before a critic sees them. Say "preview", never "in game".
5. **Judge (never self-score):** `feel crit <CRIT> --pass N --from <dir>/<group>` writes `CRIT/rubric.md`
   (critic rubric + Profile G: signal and hierarchy, timing and curves, comfort, phone read, style, polish), the
   pass files and a brief built from canon, then prints the `critic_kit.py build ... --profile G` command.
   Continue with `<critic>/SKILL.md` steps 4-9 (fresh critic, delta passes, bar 8 unless the owner said otherwise).
   No Agent tool: follow rr-mission-control's critic route (remote session, handoff to the caller, or a labelled
   UNCERTIFIED self-review capped at bar-1).
6. **Fix** in the JSON only (keep the earlier JSON in `CRIT/round-N/`), re-run 2-5.
7. **Export:** `feel build --out <dir>` writes `RR_FeelPresets.lua` (generated), `RR_Feel.lua`, `RR_FeelMath.lua`,
   `RR_FeelDemo.client.lua`, `FEEL_SPEC.md` (the feel spec per event) and a README, then runs luaparse (install
   once: `npm i --prefix ~/.cache/rr-tools luaparse`; else a balance check, named in the output) and `bible check`.
   Build PASS is required before handover. Handover says: "Studio test pending (owner)".
8. **Record** what the owner decides (`bible.py decide OQ-nnn X --by owner`, update the preset and the facts).
   Presets never become canon by themselves; `feel spec` output is not canon either.

## Runtime (what the owner wires in Studio)
- `Feel.play("lever_commit", {targets = {lever_panel = panel, lamp = lamp}, side = -1})`: roles map to GuiObjects
  (`schema.md`); missing targets skip their channel (warned in Studio). Returns a handle (`:Stop()` for loops).
- `Feel.setSpeed(speed)` on every throttle change (rumble follows Speed, av.vfx.speed_link), `Feel.setPressure(p01)`.
- Lever console: `Feel.leverDrag(u, ctx)` returns the knob position and fires the detent tick and commit once;
  `Feel.leverRelease(ctx)` snaps back before the detent; `Feel.animateValue(from, to, P.lever.snap, fn)` for the
  knob and the in-world handle (throw_deg).
- `Feel.Cue.Event:Connect(fn)` for sound and VFX (cue names; rr-vfx-lighting preset names are checked);
  `Feel.freezable(emitter)` joins hit-stop; `Feel.reset(obj)` restores a target an event sent away.
- `Feel.setSetting("reduceMotion"|"shake"|"flashes"|"haptics"|"profile", v)`; reduce motion starts from
  `GuiService.ReducedMotionEnabled` and follows it until overridden.
- `actor` events play only on the acting player's client, `crew` on the others', `all` everywhere.

## Inside a mission (rr-mission-control)
Feel is a deliverable of kind `mixed`: copy `presets/` to `<M>/src/feel/` and set `RR_FEEL_PRESETS=<M>/src/feel`;
previews in `<M>/src/feel/preview/`, one critic per group in `<M>/critique-feel-<group>`, export in
`<M>/export/feel/`. The maker's order points at this SKILL.md steps 1-7; pre-flight = step 2 plus
`feel build --no-check` succeeding. UI and HUD deliverables should call these events instead of hand-rolled tweens.

## Design rules (why the presets look like this)
- **The train never moves** (identity.pillars.stable_train): all feel is client-side camera and UI; sustained
  rumble stays under 3 px on a phone; hit-stop never pauses the server-driven world.
- **Hierarchy by tier:** fail > crisis > commit > reward > UI. The lever commit is the signature (fork_bet,
  physical_loud); crises carry the ticket shake and halo from canon; information tickets only slide in.
- **Comfort is a rule:** screen flashes at most 3 per second with capped peaks (av.feel.flash_limit), red only for
  danger, roll under 2 deg, reduce motion keeps meaning (av.feel.reduce_motion), hit-stop at most 150 ms, local.
- **Engine where exact, own math where it must match:** tweens use TweenService:GetValue; springs, noise, kicks and
  envelopes use RR_FeelMath, identical to the preview code.

## Open decisions (defaults in use; the owner decides)
OQ-031 lever input (default: drag console, the drag curve assumes it), OQ-032 feel settings (default: Roblox's own
Reduce Motion for the alpha, in-game panel at launch), OQ-013 pressure numbers (pressure rumble uses 0..1 of the
gauge), OQ-006 who may pull. `bible.py get OQ-031` shows the options.

## Honest limits
- Cloud: Pillow, luaparse, lupa (Lua 5.1) if installed; no Roblox Studio or Studio MCP. Nothing has run in Roblox:
  engine easing constants, camera module interplay, HapticEffect on real phones and frame pacing need the owner's
  Studio test (`references/fidelity.md`, last section).
- Previews are mock plates; sound is only named. Publishing, asset upload and config changes are the owner's gate.

## Maintain
`python3 <feel>/scripts/selftest.py` exercises every command on temp copies and the Lua runtime (must print all
passed; Lua runtime tests need `pip install --target ~/.cache/rr-tools/py lupa`, else they are skipped and said
so). `python3 <feel>/scripts/luatest.py -v` runs the Lua tests alone. Remove `__pycache__` after running scripts.
