# Train split kit (mission 260929-train-splits)

Nothing here has run in Roblox Studio yet: test on a copy of your place first.

## Install
1. Select your train Model in Studio. Paste `studio/RR_BreakChecker.lua` into the command bar: it lists what gets cut (expect 10 pieces per carriage).
2. Paste `studio/RR_TrainSplit_Setup.lua` with DRY_RUN = true, read the report, then set DRY_RUN = false and run it again. It backs up the train to ServerStorage.RR_Backups first.
   - If a union fails to cut, select it, right-click and choose Separate, then run the setup again.
3. Place the runtime scripts:
   - ServerScriptService: `TrainSplit` (ModuleScript) and `TrainSplitDemo.server.lua` (Script, test only).
   - ReplicatedStorage: `TrainSplitShared` and `TrainSplitConfig` (ModuleScripts).
   - StarterPlayerScripts: `TrainSplitClient` (LocalScript).
4. Effects: put `fx/RR_VFX.lua` and `fx/RR_FXPresets.lua` in ReplicatedStorage as ModuleScripts named RR_VFX and RR_FXPresets.
5. Sounds: upload `sounds/*.wav`, then paste each asset id into `TrainSplitConfig.Sounds`. Volumes are in `sounds/SOUNDS.md`.

## Use
From your window and wall damage code (server only):
`require(ServerScriptService.TrainSplit).SplitAt(workspace.Train, 1)` for a carriage 1 split, or `2` for carriage 2.
For rewards or penalties, use `TrainSplit.ConfirmRiders(result)`; never use the raw riders list.
To test in Play mode: `workspace.Train:SetAttribute("RR_TestBreak", 1)`.
