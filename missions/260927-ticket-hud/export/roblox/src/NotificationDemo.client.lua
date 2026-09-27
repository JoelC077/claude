-- NotificationDemo (LocalScript in StarterPlayerScripts) - fires every type once for a Studio test.
-- Put NotificationHud and NotificationController ModuleScripts in ReplicatedStorage.RR_Notifications.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Controller = require(ReplicatedStorage:WaitForChild("RR_Notifications"):WaitForChild("NotificationController"))

local script_ = {
	{ "CrewJoined", { name = "MayaChoo" } },
	{ "FareBanked", { amount = 120 } },
	{ "FareBanked", { amount = 40 } },
	{ "JunctionAhead" },
	{ "CoalLow" },
	{ "RiskyRoute" },
	{ "CrateLanded" },
	{ "PressureHigh", { sticky = true } },
	{ "Breakdown" },
	{ "PassengersUpset" },
	{ "CrewLeft", { name = "Tinkerbolt_TheGreat" } },
}
task.wait(2)
for _, step in ipairs(script_) do
	Controller.Notify(step[1], step[2])
	task.wait(1.2)
end
task.wait(4)
Controller.Resolve("PressureHigh")
