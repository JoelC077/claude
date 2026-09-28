# Fidelity: what the cloud proves, what only Studio can

## Proven in the cloud (selftest)
- `RR_FeelMath.lua` equals `feelmath.py` (Lua 5.1 VM via lupa; max error about 1e-15).
- `RR_Feel.lua` runs every event, full and reduce motion, against stubbed Roblox services: camera and FOV values
  equal the preview simulation frame by frame (one-frame offset: the runtime advances its clock before drawing);
  UI slides and fades equal the preview lanes; camera, FOV, overlay and targets return to rest; scripted cameras do
  not accumulate shake; flash limiter, hit-stop cooldown and animation freeze, lever detent/commit/snapback,
  HapticEffect keys and the gamepad fallback behave; the Studio demo builds and every button plays.
- Syntax: luaparse (Lua 5.1 grammar) on every .lua; `bible check` on every export.

## Approximated (say "preview", never "in game")
- Easing: previews use Penner forms. The runtime uses TweenService:GetValue, so in game the engine's curves win.
  Back, Elastic and Bounce constants in Roblox are undocumented; check with the curve dump (below).
- The phone plate is a flat mock (no lighting, default font, placeholder HUD shapes); only motion, magnitude and
  flash are meant to be read from it. Camera px in Facts is an upper bound (peaks of each axis added).
- Hit-stop freezes only this client's feel clock, character animation tracks and emitters registered with
  `Feel.freezable`. The world scroll is server-driven and keeps moving; ParticleEmitters not registered keep going.
- Haptics: HapticEffect presets (UIClick, GameplayCollision...) play Roblox's own waveform; the plotted keys are
  our approximation. Phones implement one motor; strength also follows the player's Roblox haptic setting.
- Stubs model only what RR_Feel touches; they prove logic, not rendering or frame pacing.

## Studio test list (owner)
1. Install per the export README; Play Solo with `RR_FeelDemo`; click through every event group.
2. DUMP, copy the Output lines into `dump.csv`, run `feel.py plot curves --out <dir> --compare dump.csv`:
   any `DIFF` line means that style's preview is off; the game is still right (engine curves).
3. Phone emulator (844x390): lever drag feels heavy then clunks; tickets readable while shaking; no flash feels
   harsh; turn Roblox's Reduce Motion on and replay the crisis group: everything still reads.
4. Real phone (haptics): lever commit, shovel and boiler burst are felt; UI clicks are light.
5. With the default camera and with a Scriptable fail camera: no drift after shakes.
6. Two clients: `actor` events only on the actor; hit-stop never delays lever input or the route lock.
