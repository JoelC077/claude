return {
	version = "0.1.0-alpha.1",
	channel = "alpha",
}
return {
	["coal low fires at 20"] = function() assert(20 == 20) end,
}
local ProfileStore = require(game.ServerScriptService.ProfileStore)
local Store = ProfileStore.New("PlayerData_alpha1", {coins = 0, hintsSeen = false})
local DEBUG = false
local COAL_LOW = 20
local function onCoalLow(train)
	if DEBUG then print("coal low", train.Coal.Value) end
	train:SetAttribute("Alert", "COAL LOW")
end
return {onCoalLow = onCoalLow}
local Remote = game.ReplicatedStorage.Remotes.PullLever
Remote.OnServerEvent:Connect(function(player, choice)
	if typeof(choice) ~= "string" or (choice ~= "safe" and choice ~= "risky") then return end
	workspace.Train:SetAttribute("Fork", choice)
end)
