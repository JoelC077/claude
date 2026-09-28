local ProfileStore = require(game.ServerScriptService.ProfileStore)
local Store = ProfileStore.New("PlayerData_alpha1", {coins = 0, hintsSeen = false})
local DEBUG = true
local COAL_LOW = 20
local function onCoalLow(train)
	if DEBUG then print("coal low", train.Coal.Value) end
	train:SetAttribute("Alert", "COAL LOW")
end
return {onCoalLow = onCoalLow}
