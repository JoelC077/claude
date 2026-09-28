# RR Feel runtime (generated 2026-09-28 by rr-game-feel)

Client-only juice for Risky Rails. Nothing here has run in Roblox yet: **Studio test pending (owner)**.

## Install (Studio)
1. ReplicatedStorage > Folder `RRFeel` with three ModuleScripts: `RR_Feel`, `RR_FeelMath`, `RR_FeelPresets`
   (paste each .lua file; names must match).
2. Optional demo: `RR_FeelDemo.client.lua` as a LocalScript in StarterPlayerScripts. Play Solo: buttons fire every
   event, a toggle flips reduce motion, a lever console shows the drag feel, and `DUMP` prints easing curves.

## Use (LocalScripts only)
```lua
local Feel = require(game.ReplicatedStorage.RRFeel.RR_Feel)
Feel.play("lever_commit", { side = -1, targets = { lever_panel = panel, lamp = lamp } })
Feel.play("alert_fare_banked", { targets = { ticket = parts.mover, stamp = parts.stamp, cash = label },
    count = { amount = 120, format = function(n) return string.format("%d", n) end } })
Feel.setSpeed(speed)          -- every throttle change: rumble floor follows Speed (av.vfx.speed_link)
Feel.setPressure(p01)         -- 0..1 of the gauge; floor rises past the threshold (OQ-013 numbers)
local knob = Feel.leverDrag(fingerFraction)   -- displayed knob position; fires the detent tick and commit
Feel.leverRelease()           -- snapback before the detent
Feel.Cue.Event:Connect(function(event, cue) end)   -- sound and VFX modules subscribe here
Feel.setSetting("reduceMotion", true)  -- also: shake (0..1), flashes, haptics, profile subtle|default|loud
```
Events: `ui_button_press`, `ui_button_release`, `ui_panel_open`, `ui_panel_close`, `hud_ticket_enter`, `hud_ticket_leave`, `hud_merge_bump`, `hud_crisis_arrival`, `alert_coal_low`, `alert_pressure_high`, `alert_breakdown`, `alert_passengers_upset`, `alert_junction_ahead`, `alert_risky_route`, `alert_fare_banked`, `alert_crate_landed`, `alert_crew_joined`, `alert_crew_left`, `fork_countdown_tick`, `lever_detent_tick`, `lever_commit`, `lever_commit_crew`, `lever_snapback`, `route_locked`, `shovel_coal`, `repair_fixed`, `windows_smash`, `coupling_snap`, `boiler_burst`, `fired_stamp`, `depart`, `throttle_notch`, `station_arrive`, `hard_brake`.

## Rules baked in
- Reduce motion starts from `GuiService.ReducedMotionEnabled` (tech.feel.reduced_motion) and follows its changes.
- Screen flashes: at most 3 per second across all events, peaks capped (av.feel.flash_limit).
- Hit-stop freezes only this client's Feel effects, its character's animation tracks and emitters registered with
  `Feel.freezable(emitter)`; the server-driven world scroll never pauses (av.feel.hitstop_local).
- Haptics use HapticEffect (phones, gamepads, Quest) and fall back to HapticService:SetMotor on gamepads.
- Camera effects run after the camera scripts (BindToRenderStep, Camera + 1) and never accumulate.

## Wiring notes
- The HUD (NotificationController) can replace its hand-rolled tweens with `hud_ticket_enter`, `hud_ticket_leave`,
  `hud_merge_bump` and `hud_crisis_arrival` (targets: ticket = parts.mover, stamp, halo = parts.haloRed).
- `actor` events play only on the acting player's client (lever_commit, shovel_coal, repair_fixed); `crew`
  events on everyone else's (lever_commit_crew); `all` on every client.
- Open decisions in use: OQ-031 lever input (default drag console), OQ-032 feel settings (default: Roblox's own
  Reduce Motion for the alpha), OQ-013 pressure numbers, OQ-006 who may pull.
