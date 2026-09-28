# RR_UI package (rr-ui-foundry)

Screens: HudTickets, LobbyCreateMatch. Generated; rebuild with `ui.py build` instead of editing generated files.

## Install
- Rojo: `rojo serve` with default.project.json (RR_UI lands in ReplicatedStorage, the demo in StarterPlayerScripts).
- By hand: make a Folder `RR_UI` in ReplicatedStorage with ModuleScripts RR_UIKit, RR_UITheme, RR_UITemplates and a
  Folder `screens` holding one ModuleScript per screen; put RR_UIDemo in StarterPlayerScripts as a LocalScript.
- Optional: put rr-game-feel's RR_Feel, RR_FeelPresets and RR_FeelMath in the same RR_UI folder; the kit then plays
  its events (reduce motion included). Without it the kit only fades, and snaps when Reduce Motion is on.

## Use (LocalScript)
```lua
local UI = require(game.ReplicatedStorage.RR_UI.RR_UIKit)
local hud = UI.mount(require(game.ReplicatedStorage.RR_UI.screens.HudTickets))
hud:push("CoalLow")                 -- tickets: type name + slots, e.g. hud:push("CrewJoined", {name = "Sam"})
hud:clear("CoalLow")                -- the server's clear alert (ID)
local lobby = UI.mount(require(game.ReplicatedStorage.RR_UI.screens.LobbyCreateMatch))
lobby:send("open")                  -- state machine events; lobby.Action.Event fires (name, data) for game code
UI.setSkin("A")                     -- live reskin of every mounted screen
```

## Studio test (owner; nothing here has run in Roblox)
1. Play Solo with the demo: each screen cycles its boards; compare with the boards in the render folder.
2. Device emulator: iPhone 14 landscape, an iPad and 1920x1080; check the HUD clears the jump button and top bar.
3. Gamepad (or the emulator's controller): Select starts navigation on the lobby; ButtonB closes it.
4. Settings > Reduce Motion on: panels and tickets fade instead of sliding.
5. Upload the images in ASSETS.md and paste the ids.
