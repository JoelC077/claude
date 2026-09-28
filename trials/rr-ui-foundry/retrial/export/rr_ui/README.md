# RR_UI package (rr-ui-foundry)

Screens: HudTickets, LobbyCreateMatch. Generated; rebuild with `ui.py build` instead of editing generated files.

## Install
- Rojo: `rojo serve` with default.project.json (RR_UI lands in ReplicatedStorage; this is what ships).
  `demo.project.json` adds the Studio demo (RR_UIDemo) for the check below.
- By hand: make a Folder `RR_UI` in ReplicatedStorage with ModuleScripts RR_UIKit, RR_UITheme, RR_UITemplates and a
  Folder `screens` holding one ModuleScript per screen.
- Optional: put rr-game-feel's RR_Feel, RR_FeelPresets and RR_FeelMath in the same RR_UI folder; the kit then plays
  its events (reduce motion included). Without it the kit only fades, and snaps when Reduce Motion is on.
- **Remove RR_UIDemo before publishing** (it binds H/K/L and cycles boards; it returns at once outside Studio).

## Use (LocalScript)
```lua
local UI = require(game.ReplicatedStorage.RR_UI.RR_UIKit)
local hudTickets = UI.mount(require(game.ReplicatedStorage.RR_UI.screens.HudTickets))
hudTickets:push("CoalLow")                     -- alert types: CoalLow, PressureHigh, Breakdown, PassengersUpset, JunctionAhead, RiskyRoute, FareBanked, CrateLanded, CrewJoined, CrewLeft
hudTickets:push("CrewJoined", {name = "Sam"})   -- slots fill the body text
hudTickets:clear("CoalLow")                    -- the server's clear alert (ID)
local lobbyCreateMatch = UI.mount(require(game.ReplicatedStorage.RR_UI.screens.LobbyCreateMatch))
lobbyCreateMatch:send("open")                       -- machine events: open, close, join, cancel, joined
lobbyCreateMatch.Action.Event:Connect(function(name, data) end)   -- controls fire (name, data) for game code
UI.setSkin("A")                -- live reskin of every mounted screen
```

## Studio test (owner; nothing here has run in Roblox)
1. Play Solo with `demo.project.json` (or RR_UIDemo in StarterPlayerScripts): each screen cycles its boards; compare with the rendered PNGs.
2. HudTickets: push each alert type with the demo's H key; tickets stack, merge and expire as on the boards.
3. LobbyCreateMatch: L sends the next event (open, close, join, cancel, joined); every state looks like its board.
4. LobbyCreateMatch with a controller: focus starts on join, every control is reachable, ButtonB = panel.close.
5. Device emulator: iPhone 14 landscape, an iPad and 1920x1080: clear of the top bar, jump button and thumbstick; note GuiService:GetGuiInset() and the JumpButton's AbsolutePosition if they differ from the facts.
6. Settings > Reduce Motion on: panels and tickets fade or snap, nothing slides.
7. Upload the images in ASSETS.md and write asset_ids.json, then rebuild.
