# Fidelity: what the cloud proves, what only Studio can

## Proven in the cloud (selftest)
- `RR_FeelMath.lua` equals `feelmath.py` (Lua 5.1 VM via lupa; max error about 1e-15), including the spring peak
  normalisation (punch amps and kick angles are delivered peaks) and the signed lever curve.
- `RR_Feel.lua` runs every event, full and reduce motion, against stubbed Roblox services: camera and FOV values
  equal the preview simulation frame by frame (one-frame offset: the runtime advances its clock before drawing);
  UI slides and fades equal the preview lanes; camera, FOV, overlay and targets return to rest; scripted cameras do
  not accumulate shake; a FOV set by another script mid-kick is kept; a flash that ends during a stall leaves no
  colour; flash limiter, hit-stop cooldown and animation freeze; two-way lever with the tick before the commit and
  one commit per junction (`ctx.fork`); `playFor` routing by `who`; HapticEffect keys and the gamepad fallback; the
  Studio demo builds and every button plays.
- Luau: `luau-compile` (the real parser) on every export; `luau-lsp` strict typecheck of `RR_FeelTyped.luau` and a
  caller: a wrong event or role name is a type error. The runtime itself is untyped (nonstrict: 0 diagnostics).
  Without the tools the gate reports SKIP ("syntax unchecked"), never a false PASS or FAIL. `bible check` on every
  export.

## Approximated (say "preview", never "in game")
- Easing: previews use Penner forms. The runtime uses TweenService:GetValue, so in game the engine's curves win.
  Back, Elastic and Bounce constants in Roblox are undocumented; check with the curve dump (below).
- The phone plate is a flat mock (no lighting, default font, placeholder HUD shapes); only motion, magnitude and
  flash are meant to be read from it. Camera px in Facts is an upper bound (peaks of each axis added).
- Camera signs follow Roblox camera space (+ pitch looks up, + yaw turns left, + roll tilts left); the preview
  draws the same. How a direction feels (a lurch, a turn toward the lever) is judged in Studio.
- Hit-stop freezes only this client's feel clock, character animation tracks and emitters registered with
  `Feel.freezable`. The world scroll is server-driven and keeps moving; ParticleEmitters not registered keep going.
- Haptics: HapticEffect presets (UIClick, GameplayCollision...) play Roblox's own waveform; the plotted keys are
  our approximation. Phones implement one motor; strength also follows the player's Roblox haptic setting.
- Stubs model only what RR_Feel touches; they prove logic, not rendering or frame pacing.

## Studio test list (owner)
1. Install per the export README; Play Solo with `RR_FeelDemo`; click through every event group.
2. DUMP, copy the Output lines as they are (timestamps are fine) into `dump.txt`, run
   `feel.py plot curves --out <dir> --compare dump.txt`: a `DIFF` line means that style's preview is off; the game
   is still right (engine curves).
3. Phone emulator (844x390): the lever drags heavy, ticks, then clunks with the view turning toward the pulled
   side, both ways; station arrival leans the view forward (down), depart leans it back (up); tickets readable while shaking; no flash
   feels harsh; turn Roblox's Reduce Motion on and replay the crisis group: everything still reads.
4. HUD wired per the README (controller motion removed): tickets land at rest after fare, crate and crisis events;
   the halo pulses once, not twice.
5. Real phone (haptics): lever commit, shovel and boiler burst are felt; UI clicks are light.
6. With the default camera and with a Scriptable fail camera that sets its own FOV: no drift after shakes or kicks.
7. Two clients: `actor` events only on the actor (`playFor`); hit-stop never delays lever input or the route lock.
