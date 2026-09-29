--[[
TrainSplitDemo  (Script in ServerScriptService)  v2.0.0 - Studio test only.

Play in Studio, switch to the Server view, select the train Model and add the number attribute
RR_TestBreak = 1 or 2: that break snaps through TrainSplit.SplitAt. It does nothing in a live
server, and attributes set on the client never reach the server, so players cannot use it.
In the game itself your damage system calls TrainSplit.SplitAt (the kit has no automatic trigger).
]]

local RunService = game:GetService("RunService")
if not RunService:IsStudio() then
	return
end

local TrainSplit = require(script.Parent:WaitForChild("TrainSplit"))

local hooked = {}

local function hook(train)
	if hooked[train] then
		return
	end
	hooked[train] = true
	train:GetAttributeChangedSignal("RR_TestBreak"):Connect(function()
		local k = tonumber(train:GetAttribute("RR_TestBreak"))
		if not k then
			return
		end
		local intact = TrainSplit.IsIntact(train, k)
		local result = TrainSplit.SplitAt(train, k)
		print(("[TrainSplitDemo] %s break %d: %s, %d bodies, %d riders"):format(
			train:GetFullName(),
			k,
			intact and "snapped" or "already gone (no-op)",
			#result.bodies,
			#result.riders
		))
	end)
	print(("[TrainSplitDemo] ready: in the Server view set attribute RR_TestBreak = 1 or 2 on %s"):format(train:GetFullName()))
end

local function consider(inst)
	if inst.Name == "RR_Breaks" and inst.Parent and inst.Parent:IsA("Model") then
		hook(inst.Parent)
	end
end

for _, d in workspace:GetDescendants() do
	consider(d)
end
workspace.DescendantAdded:Connect(consider)
