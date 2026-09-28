# rr-game-feel · design notes (2026-09-28)

## Job
The juice for Risky Rails: one client runtime (tweens and easing, trauma camera shake, camera kicks, hit-stop,
UI punch and pulse, screen and element flashes, FOV kicks, haptics, lever-pull feel) driven by per-event presets
kept as JSON, with accessibility built in, a generated feel spec per event, curve plots and mock phone previews
made in the cloud, and quality judged by multiuse-critic.

## Pipeline
```
bible get (canon slice) -> presets/feel.json (source of truth: events -> channels, knobs, a11y, profiles, limits)
  -> feel.py validate  schema, Roblox enums, canon numbers agree, colour tokens (red only for danger), OQ refs,
                       comfort limits (shake px on a phone, hit-stop, flash rate and peak), reduce-motion still
                       communicates, loudness hierarchy by priority tier
  -> feel.py spec      FEEL_SPEC.md: per event intent, trigger, who, timeline table, phone px, reduce-motion, canon
  -> feel.py plot      Pillow PNGs: easing sheet, event timelines (full vs reduce-motion), lever drag, sustain,
                       Studio curve-dump comparison
  -> feel.py preview   mock phone POV frames (844x390) with shake, kick, FOV, flash, punch applied; filmstrip,
                       GIF, feel matrix, contact.png + closeups.png + facts.md (multiuse-critic layout)
  -> feel.py crit      CRIT/rubric.md = critic rubric + Profile G (game feel), pass files, brief from canon
  -> critic_kit.py build --profile G -> independent critic (never self-scored)
  -> feel.py build     RR_FeelPresets.lua (generated) + RR_Feel.lua + RR_FeelMath.lua + RR_FeelDemo.client.lua
                       + FEEL_SPEC.md + README; luaparse and bible check gates
```

## Files
- `presets/feel.json`: shake, sustain (speed, pressure), lever, a11y, profiles, limits, roles, ~30 events in
  groups ui, alerts, lever, impacts, fail, ambient; events compose (`include`) so the HUD enter lives once.
- `scripts/feelmath.py` (stdlib): Penner easing for all 11 Roblox styles x 3 directions, damped springs, a
  deterministic 1D gradient noise shared with Luau, trauma sim, lever drag curve, haptic envelopes, event sampler.
- `scripts/feel.py` (stdlib CLI), `scripts/feelplot.py` (Pillow), `scripts/luatest.py` (runs the Luau in a Lua 5.1
  VM via lupa against stubbed Roblox services), `scripts/selftest.py`.
- `assets/luau/`: `RR_FeelMath.lua` (pure, same formulas as feelmath.py), `RR_Feel.lua` (runtime),
  `RR_FeelDemo.client.lua` (Studio demo, curve dump).
- `references/`: schema.md (preset format, knobs), rubric-feel.md (Profile G), fidelity.md (preview vs Roblox,
  Studio test list).

## Decisions (with why)
1. **Data first.** One JSON drives the runtime, the specs, the plots and the previews, so they cannot drift.
   Canon numbers are `{"v": n, "canon": key}` and colours `@key`; validate proves they agree with rr-bible.
2. **Engine where it is exact, own math where it must match.** UI tweens run on TweenService (engine easing);
   springs, shake noise, kicks and envelopes are stepped by one RenderStepped loop with RR_FeelMath, whose
   formulas are identical to feelmath.py; luatest.py proves it and runs RR_Feel.lua frame by frame against the
   preview simulation (camera, FOV and UI lanes equal to 1e-15).
3. **Trauma model** (Eiserloh): events add trauma, it decays linearly, shake = trauma^power x max offset and
   angle through smooth noise. Sustain sources (Speed, canon av.vfx.speed_link; pressure, OQ-013 default) set a
   floor, capped low because the train never moves and players stand with zero jitter (stable_train pillar).
4. **Hit-stop is local and cosmetic.** Only the acting player's client freezes its own effects, character
   animation tracks and registered emitters, <= 150 ms, with a cooldown. The server-driven world scroll never
   pauses; the preview shows that honestly.
5. **Haptics: HapticEffect first** (phones, gamepads, Quest; HapticService is deprecated per the docs),
   HapticService:SetMotor fallback for gamepads. Waveforms are keyframes in ms.
6. **Accessibility is a rule, not an option.** Reduce motion defaults from GuiService.ReducedMotionEnabled,
   drops shake, kicks and FOV, shrinks punches, turns slides into fades; flashes obey a 3-per-second limit and
   peak caps (red lower), can be switched off; validate fails an event that stops communicating under reduce
   motion. Settings API (`Feel.setSetting`) is ready for an in-game panel (open question).
7. **Hierarchy is checked, not hoped for.** Each event has a priority tier (1 fail ... 5 UI tick); a loudness
   score (shake, kick, hit-stop, flash, FOV, haptic, punch) must not let a lower tier outshout a higher one.
8. **Critic Profile G** (signal, timing and curves, comfort, phone read, style, polish) merged into
   CRIT/rubric.md so critic_kit.py works unchanged. Plots and mock frames are judged as intent; the owner's
   Studio playtest is the final feel check.

## Plugs
- rr-bible: canon read at run time (ui.hud.motion, ui.hud.crisis_extra, ui.lever.*, gameplay.alerts.*,
  gameplay.speed.*, gameplay.run.depart, gameplay.crisis.fail_cinematic, tech.camera.*, tech.ui_platform.*,
  av.feel.*, av.vfx.*, identity.pillars.*, style tokens); `bible check` on every export; platform facts
  (tech.feel.*) and open questions recorded through bible.py.
- rr-mission-control: feel is a deliverable of kind `mixed`; presets in `<M>/src/feel/` (RR_FEEL_PRESETS),
  pre-flight = `validate --strict` + `build --no-check`, critic `<M>/critique-feel-<group>`, export `<M>/export/feel/`.
- multiuse-critic: contact_sheet.py and critic_kit.py found by glob, never copied; Profile G rubric.
- Siblings: event `cues` name rr-vfx-lighting presets (checked when that skill is found) and sound names for
  rr-soundsmith (free text until it exists); the runtime fires `Feel.Cue` so those modules subscribe.

## Limits
No Studio: nothing here has run in Roblox. Previews are mock plates; Roblox's exact Elastic/Bounce shapes,
camera module interplay, HapticEffect feel on real phones and frame pacing need the owner's Studio test
(`references/fidelity.md`). Never publish, spend or change the owner's config.
