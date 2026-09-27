# Risky Rails ticket notifications - Roblox package

## Files
| file | put it in | type |
|---|---|---|
| src/NotificationHud.lua | ReplicatedStorage/RR_Notifications/NotificationHud | ModuleScript (builder: tokens, types, ticket builder) |
| src/NotificationController.lua | ReplicatedStorage/RR_Notifications/NotificationController | ModuleScript (client API: Notify, Resolve) |
| src/NotificationDemo.client.lua | StarterPlayer/StarterPlayerScripts/NotificationDemo | LocalScript (Studio test; delete for release) |
| icons/rr_ticket_icons.png | upload as Decal/Image | 640x256, 5x2 cells of 128px (icons.json) |
| icons/rr_hazard_tile.png | upload as Image | 32x32 hazard stripe tile for the risk stub |

## Upload order (asset ids are placeholders until you do this)
1. Studio > Asset Manager > Bulk Import `icons/rr_ticket_icons.png` and `icons/rr_hazard_tile.png`.
2. Copy each image id; in NotificationHud.lua set `Hud.IconSheet = "rbxassetid://<id>"` and `Hud.HazardTile = "rbxassetid://<id>"`.
3. Create Folder `ReplicatedStorage.RR_Notifications`, add the two ModuleScripts with the names above.
4. Add the demo LocalScript, press Play: every type fires once (merge, overflow +N MORE, sticky crisis resolve after ~15 s).

## Use from game code (client)
```lua
local N = require(game.ReplicatedStorage.RR_Notifications.NotificationController)
N.Notify("CoalLow")                         -- crisis, 7 s
N.Notify("PressureHigh", {sticky = true})   -- stays until N.Resolve("PressureHigh")
N.Notify("FareBanked", {amount = 40})       -- merges: count badge + cash total ($12,000 -> $12K)
N.Notify("CrewJoined", {name = player.DisplayName})  -- names capped at 10 chars + "…"
```
Server -> client: fire a RemoteEvent with (typeName, data) and call Notify in its OnClientEvent.

## Sizing
Stack anchored bottom-right (AnchorPoint 1,1), 14 px right / 112 px bottom on phone (clear of the jump button),
18.56 / 127.6 on PC; UIScale 1.0 phone (touch + viewport height <= 500), 1.16 otherwise; each ticket has a
UIAspectRatioConstraint. Fonts: Enum.Font.LuckiestGuy, Montserrat Bold (built-in families).

## Verified here / pending
- Luau files parsed OK (luaparse, Lua 5.3 grammar; no Luau-only syntax used). luau-analyze/selene not installed.
- Notification texts in NotificationHud.lua = design = prototype facts (diff 0).
- Layout numbers mirror the design (card inset 5, text x 61 in card = 66 in ticket, stub 54, medallion 36/28, notch x 51).
- Studio test pending (owner): no Roblox Studio in the cloud session. Watch: UIStroke on rotated stamp, hazard tile scale, "+N MORE" chip position after UIScale.
