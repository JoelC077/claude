# RR Feel runtime (generated 2026-09-28 by rr-game-feel)

Client-only juice for Risky Rails. Nothing here has run in Roblox yet: **Studio test pending (owner)**.
Presets: `src/feel/feel.json` (the only place to change numbers; rebuild after).

## Install (Studio)
1. ReplicatedStorage > Folder `RRFeel` with four ModuleScripts: `RR_Feel`, `RR_FeelMath`, `RR_FeelPresets`,
   `RR_FeelTyped` (paste each file; names must match).
2. Optional demo: `RR_FeelDemo.client.lua` as a LocalScript in StarterPlayerScripts. Play Solo: buttons fire every
   event, a toggle flips reduce motion, a two-way lever console shows the drag feel, `DUMP` prints easing curves.
3. With rr-ui-foundry's kit: `Kit.useFeel(require(ReplicatedStorage.RRFeel.RR_Feel))` once, or UI transitions fall
   back to plain fades.

## Use (LocalScripts only)
```lua
local Feel = require(game.ReplicatedStorage.RRFeel.RR_FeelTyped)   -- typed; RR_Feel is the same module untyped
Feel.play("lever_commit", { side = -1, targets = { lever_panel = panel, lamp = lamp } })
Feel.playFor("shovel_coal", actorUserId, ctx)   -- server events carry the actor's UserId; `who` decides who feels it
Feel.play("alert_fare_banked", { targets = { ticket = parts.mover, stamp = parts.stamp, cash = label },
    count = { amount = 12500, format = Hud.formatCash } })   -- the HUD's own formatter: the count ends on its stamp
Feel.setSpeed(speed)          -- every throttle change: rumble floor follows Speed (av.vfx.speed_link)
Feel.setPressure(p01)         -- 0..1 of the gauge; floor rises past the threshold (OQ-013 numbers)
Feel.Cue.Event:Connect(function(event, cue) end)   -- sound and VFX modules subscribe here
Feel.setSetting("reduceMotion", true)  -- also: shake (0..1), flashes, haptics, profile subtle|default|loud
```
Events: `ui_button_press`, `ui_button_release`, `ui_panel_open`, `ui_panel_close`, `hud_ticket_enter`, `hud_ticket_leave`, `hud_merge_bump`, `hud_crisis_arrival`, `alert_coal_low`, `alert_pressure_high`, `alert_breakdown`, `alert_passengers_upset`, `alert_junction_ahead`, `alert_risky_route`, `alert_fare_banked`, `alert_crate_landed`, `alert_crew_joined`, `alert_crew_left`, `fork_countdown_tick`, `lever_detent_tick`, `lever_commit`, `lever_commit_crew`, `lever_snapback`, `route_locked`, `shovel_coal`, `repair_fixed`, `windows_smash`, `coupling_snap`, `boiler_burst`, `fired_stamp`, `depart`, `throttle_notch`, `station_arrive`, `hard_brake`.

## Lever (two-way, gameplay.fork.lever)
```lua
-- u is signed: - left, + right (the sign picks the branch); fork = the junction id re-arms the lever per junction
local startX, travel = 0, knobTravelPx
knob.InputBegan:Connect(function(input) startX = input.Position.X end)
UserInputService.InputChanged:Connect(function(input)   -- global tracking: the finger leaves the 64 px knob
    if not dragging then return end
    local shown = Feel.leverDrag((input.Position.X - startX) / travel, { targets = t, fork = junctionId })
    knob.Position = UDim2.new(0.5, shown * travel, 0.5, 0)   -- |shown| == 1: committed (animate lever.snap)
end)
-- on release: if Feel.leverRelease({ targets = t }) == "snapback" then animate the knob home (lever.snapback)
```
The detent tick fires at 60% of the travel, the commit once at 70%; the lever stays
committed until a new `fork` id (or `Feel.leverReset()`). `RR_FeelDemo` has the full wiring; a UIDragDetector works too.

## HUD wiring (NotificationController): one writer per property
The shipped HUD animates the same objects itself (ticket slide in, crisis shake, halo pulse on RenderStepped).
Two writers fight, and RR_Feel restores the position it captured when an event starts, so a ticket captured
mid-slide ends parked off-screen. Before passing `ticket`/`halo` targets:
1. Delete the controller's own motion for those objects: the `mover.Position = UDim2.fromScale(1.25, 0)` + slide
   tween, the crisis `{ -5, 5, -4, 3, 0 }` shake loop, and the `haloRed` pulse in its RenderStepped callback.
2. Call Feel after the ticket is built at its rest position (mover at 0,0): `hud_ticket_enter`, `hud_ticket_leave`,
   `hud_merge_bump`, `hud_crisis_arrival` (targets: ticket = parts.mover, stamp = parts.stamp, halo = parts.haloRed).
3. Set `haloRed.BackgroundTransparency = 0`: the pulse multiplies the designed opacity (at 0.1 it would reach
   0.27-0.855 instead of canon's 0.3-0.95).
Or keep the controller's motion and pass only the other roles (gauge, stamp, cash): camera, haptics and cues still play.

## Rules baked in
- Reduce motion starts from `GuiService.ReducedMotionEnabled` (tech.feel.reduced_motion) and follows its changes.
- Screen flashes: at most 3 per second across all events, peaks capped (av.feel.flash_limit).
- Hit-stop freezes only this client's Feel effects, its character's animation tracks and emitters registered with
  `Feel.freezable(emitter)`; the server-driven world scroll never pauses (av.feel.hitstop_local).
- Haptics use HapticEffect (phones, gamepads, Quest) and fall back to HapticService:SetMotor on gamepads.
- Camera effects run after the camera scripts (BindToRenderStep, Camera + 1) and never accumulate; FOV kicks
  are applied as a delta, so a fail camera that sets its own FOV mid-kick keeps it.
- Camera pitch: + tips the view up, - down (a lurch forward or a nod is negative).
- Open decisions in use: OQ-031 lever input (default drag console), OQ-032 feel settings (default: Roblox's own
  Reduce Motion for the alpha), OQ-013 pressure numbers, OQ-006 who may pull.
