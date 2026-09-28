---
name: rr-game-feel
description: "Risky Rails juice runtime and presets: tweens, camera shake, hit-stop, UI punch, flashes, FOV kicks, haptics and lever drag feel, with reduce-motion and flash-safety rules. Not for particles, lighting, sound or layout. Sub-skill of rr-mission-control (JARVIS): any Risky Rails request, even a short one squarely in this area, goes to rr-mission-control first, which routes here; fire directly only when this skill is named or another rr-* skill invokes it."
---

# RR Game Feel

Juice for Risky Rails as data: presets in JSON, one Luau runtime that reads them, specs, plots, previews and a
tuning table generated from the same numbers, quality judged by an independent critic. Precise, proactive, no fluff.

Paths (find by glob, never hard-code): `<feel>` = this folder;
`<bible>` = `dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path '*rr-bible/SKILL.md' 2>/dev/null | head -1)"`;
`<critic>` = the same with `*multiuse-critic/SKILL.md`. The scripts find both themselves (env overrides
`RR_BIBLE_SKILL`, `RR_CRITIC_SKILL`, `RR_VFX_SKILL`, `RR_SOUND_SKILL`). `feel` below = `python3 <feel>/scripts/feel.py`.

**Which presets file:** never edit `<feel>/presets/feel.json` (a synced skill is overwritten). Copy it into the
project or mission (`<M>/src/feel/feel.json`) and pass `--presets <that file>` on every call: shell variables do not
survive between tool calls. Every command prints the file it used; check that line.

## Canon first
Read the slice you need through rr-bible, never from memory: `bible.py get av.feel --values`, `get ui.hud.motion`,
`get ui.hud.crisis_extra`, `get ui.lever`, `get gameplay.fork`, `get gameplay.alerts`, `get tech.feel`,
`get tech.camera`, `get identity.pillars`, `get questions`. Presets cite canon as
`{"v": n, "canon": key, "match": "phrase"}` (the phrase of the fact that holds the number) and colours as `@key`;
`feel validate` proves they agree. The owner's new words beat canon: do the work, then record it (`add-fact ...
--src "owner DATE"` or `decide`), then `bible.py lint`.
**Missing canon:** `bible.py add-question "TITLE" --option "A: .." --option "B: .." --default "A (why)" --src IDS
--affects KEYS --dry-run`, then without `--dry-run`, then `lint`; cite the new OQ in the event (`oq`) and label the
work "assumed (OQ-nnn default)". In a trial or when parallel skills are writing the bible, do not number it
yourself (numbers race: a sandbox OQ-037 was another skill's question): cite `OQ-TBD-<slug>` and put the full
command in the handover as an owner gate. validate warns when a cited OQ's title has nothing to do with the event.

## Moments to events (plain words -> preset keys)
lever pull = `lever` drag + `lever_detent_tick`, `lever_commit` (actor), `lever_commit_crew`, `lever_snapback`,
`route_locked` · crisis alarm = `hud_crisis_arrival` inside `alert_coal_low`, `alert_pressure_high`,
`alert_breakdown`, `alert_passengers_upset` (+ `windows_smash`, `coupling_snap`) · fare banked =
`alert_fare_banked` · crate landed = `alert_crate_landed` · fail = `boiler_burst`, `fired_stamp`. A moment with no
event (e.g. a hard brake): add one per `references/schema.md` "Adding an event", with its OQ if canon is silent.

## Workflow
1. **Edit presets** with `feel set 'events.E.channels[0].amp=4' ... --presets F` (keeps canon bindings and the house
   layout; `feel fmt` reformats a hand edit). Read `references/schema.md` first: punch `amp` and camkick
   `angles_deg` are the delivered peaks; camera pitch + tips the view up (a lurch forward or a nod is negative).
   `feel list` shows tier and loudness; `feel show EVENT` prints the spec, measured peaks and every higher-tier
   event it outshouts: quote that line, never "quieter than every X" from memory.
2. **Gate:** `feel validate --strict` must PASS: schema and Roblox enums, canon agreement (bound phrases), colour
   tokens (red only for tiers 1-2), OQs, comfort limits in phone pixels, visibility (shake, kicks and pixel punches
   a phone shows), flash rate and peaks, hit-stop, reduce motion still reads on every device (a haptic alone does
   not), pitch vs intent, loudness hierarchy (no event louder than most of a higher tier), rumble, vfx and sfx cue
   names. NOTE lines are for the handover (unrecorded OQs, hierarchy pairs), not failures.
3. **Plot:** `feel plot all --out <dir>` (under a second). Look at the plots you changed.
4. **Preview:** `feel preview GROUP|EVENT|E1,E2,..|all --out <dir> [--name N] [--gif]`: groups go to
   `<dir>/<group>`, one event to `<dir>/ev_<event>`, a list to `<dir>/<N>` (use a list so every moment of a
   mission reaches a critic, not only group heroes). Each folder: peak frame at phone size, feel matrix,
   timelines, filmstrip, `contact.png` + `closeups.png` (the lever drag curve joins any set with a lever event),
   `facts.md`, GIFs. Look at each `contact.png` once. Say "preview", never "in game".
5. **Judge (never self-score):** `feel crit <CRIT> --pass N --from <dir>/<folder>` writes the rubric (Profile G),
   pass files and a brief from canon, then prints the `critic_kit.py build ... --profile G` command. Continue with
   `<critic>/SKILL.md` steps 4-9 (fresh critic, delta passes, bar 8 unless the owner said otherwise). Critic route:
   an Agent/Task tool if you have one; in a workflow or cloud run without it, hand the printed critic orders to
   the caller (a remote session cannot see untracked local files); last resort a labelled UNCERTIFIED self-review
   capped at bar-1.
6. **Fix** in the presets only (keep the pass JSON in `CRIT/round-N/`). `feel changed --since <round JSON>` names
   the groups to re-preview and re-critique; redo 2-5 for those only.
7. **Export:** `feel build --out <dir>` writes `RR_FeelPresets.lua`, `RR_FeelTyped.luau` (strict types: event
   names, roles, settings), `RR_Feel.lua`, `RR_FeelMath.lua`, `RR_FeelDemo.client.lua`, `FEEL_SPEC.md`, README, then
   gates: Luau syntax (luau-compile; else luaparse; else SKIP, reported "syntax unchecked"), strict typecheck of
   `RR_FeelTyped.luau` (luau-lsp + Roblox types), `bible check`. Tools: `python3 <feel>/scripts/luau_check.py
   --status | --install` (pinned, ~25 MB into ~/.cache/rr-tools). `feel tune [SEL] --out <dir>` writes
   `TUNING.md` + `tuning.csv` (every knob, its safe range, canon locks, measured result). Build PASS is required
   before handover; the handover says "Studio test pending (owner)".
8. **Record** what the owner decides (`bible.py decide OQ-nnn X --by owner`, then the preset). Presets never
   become canon by themselves; `feel spec` output is not canon either.

## Runtime (what the owner wires in Studio)
- `local Feel = require(RRFeel.RR_FeelTyped)` in `--!strict` code (same module as `RR_Feel`, typed).
  `Feel.play(name, {targets = {role = GuiObject}, side = -1|1})`; missing targets skip their channel (warned in
  Studio). `Feel.playFor(name, actorUserId, ctx)` applies `who` (actor / crew / all): the server event carries
  the actor's UserId.
- **One writer per property.** The shipped HUD (NotificationController) animates the ticket and halo itself. Wire
  `ticket`/`halo` only after removing its slide, shake and halo pulse, and set `haloRed` opacity to 1 (the pulse
  multiplies the designed opacity); or pass only the other roles. The README says exactly what to delete.
- Lever (two-way): `Feel.leverDrag(u, {targets, fork = junctionId})` with u signed (- left, + right) returns the
  knob to draw; the detent tick fires at `lever.notch`, the commit once at `lever.detent`, and a new `fork`
  re-arms it (or `Feel.leverReset()`). Track the drag with UserInputService.InputChanged or a UIDragDetector;
  `Feel.leverRelease(ctx)` returns `"snapback"` before the detent. `RR_FeelDemo` is the reference wiring.
- Counting labels: pass the HUD's own money formatter (`count = {amount, format = Hud.formatCash}`).
- `Feel.setSpeed(speed)` on every throttle change, `Feel.setPressure(p01)`; `Feel.Cue.Event:Connect(fn)` for sound
  and VFX; `Feel.freezable(emitter)`; `Feel.reset(obj)`; `Feel.setSetting("reduceMotion"|"shake"|"flashes"|
  "haptics"|"profile", v)`. With rr-ui-foundry: `Kit.useFeel(require(RRFeel.RR_Feel))`.
- Live tuning in Studio: edit `Feel.Presets.events.<name>.channels[i]` in the command bar, then copy the numbers
  back with `feel set` (the JSON stays the source).

## Inside a mission (rr-mission-control)
Feel is a deliverable of kind `mixed`: presets in `<M>/src/feel/feel.json` (always `--presets` it), previews in
`<M>/src/feel/preview/`, one critic per group or moment set in `<M>/critique-feel-<name>`, export and tuning table
in `<M>/export/feel/`. The maker's order points at this SKILL.md steps 1-7; pre-flight = step 2 plus
`feel build --no-check` succeeding. UI and HUD deliverables call these events instead of hand-rolled tweens.

## Design rules (why the presets look like this)
- **The train never moves** (identity.pillars.stable_train): all feel is client-side camera and UI; sustained
  rumble stays tiny on a phone (limits.sustain_px_max); hit-stop never pauses the server-driven world.
- **Hierarchy by tier:** fail > crisis > commit > reward > UI. The lever commit is the signature (fork_bet,
  physical_loud); crises carry the ticket shake and halo from canon; information tickets only slide in. An event
  that is quiet on purpose says why in `quiet_ok`; one allowed to be loud, in `loud_ok` (critics see both).
- **Comfort is a rule:** flashes per av.feel.flash_limit, red only for danger, small roll, hit-stop per
  av.feel.hitstop_local, reduce motion per av.feel.reduce_motion; the limits live in feel.json bound to those keys.
- **Engine where exact, own math where it must match:** tweens use TweenService:GetValue; springs, noise, kicks and
  envelopes use RR_FeelMath, identical to the preview code.

## Open decisions (defaults in use; the owner decides)
OQ-031 lever input (default: drag console, the drag curve assumes it), OQ-032 feel settings (default: Roblox's own
Reduce Motion for the alpha, in-game panel at launch), OQ-013 pressure numbers (pressure rumble uses 0..1 of the
gauge), OQ-006 who may pull. `bible.py get OQ-031` shows the options.

## Honest limits
- Cloud: Pillow, lupa (Lua 5.1), luau-compile + luau-lsp if installed; no Roblox Studio or Studio MCP. Nothing
  has run in Roblox: engine easing constants, camera module interplay, HapticEffect on real phones, pitch
  direction as felt and frame pacing need the owner's Studio test (`references/fidelity.md`, last section).
- The runtime is untyped Lua 5.1-compatible (so the cloud can run it); strict typing is `RR_FeelTyped.luau`.
- Previews are mock plates; sound is only named. Publishing, asset upload and config changes are the owner's gate.

## Maintain
`python3 <feel>/scripts/selftest.py` exercises every command on temp copies, planted-bad presets, the Luau gates
and the Lua runtime (must print all passed; Lua tests need `pip install --target ~/.cache/rr-tools/py lupa`).
`python3 <feel>/scripts/luatest.py -v` runs the Lua tests alone. The scripts never write `__pycache__`.
