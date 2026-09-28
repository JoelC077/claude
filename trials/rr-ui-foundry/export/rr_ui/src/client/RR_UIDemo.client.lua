-- RR_UIDemo (LocalScript, StarterPlayerScripts) - rr-ui-foundry Studio check.
-- Mounts every screen in ReplicatedStorage.RR_UI.screens and cycles each screen's boards (the same boards
-- the critic saw) every 4 seconds. Keys: K cycles the skin (OQ-001 options), L sends the next state-machine
-- event of the first screen that has one, H pushes a random HUD alert. Remove it before shipping.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local root = ReplicatedStorage:WaitForChild("RR_UI")
local UI = require(root:WaitForChild("RR_UIKit"))

local mounted = {}
for _, m in ipairs(root:WaitForChild("screens"):GetChildren()) do
	if m:IsA("ModuleScript") then
		local ok, def = pcall(require, m)
		if ok then
			table.insert(mounted, UI.mount(def))
		else
			warn("[RR_UIDemo] " .. m.Name .. ": " .. tostring(def))
		end
	end
end

local skins = {}
for name in pairs(UI.Theme.skins) do table.insert(skins, name) end
table.sort(skins)

task.spawn(function()
	local round = 0
	while true do
		round = round + 1
		for _, s in ipairs(mounted) do
			local boards = s.def.boards or {}
			if #boards > 0 then
				local b = boards[((round - 1) % #boards) + 1]
				s:board(b)
				print(string.format("[RR_UIDemo] %s: board %s (skin %s, input %s, display %s)", s.def.name,
					tostring(b.name), UI.skin, UI.inputClass(), UI.displaySize()))
			end
		end
		task.wait(4)
	end
end)

UserInputService.InputBegan:Connect(function(input, processed)
	if processed then return end
	if input.KeyCode == Enum.KeyCode.K then
		local i = table.find(skins, UI.skin) or 0
		UI.setSkin(skins[(i % #skins) + 1])
		print("[RR_UIDemo] skin " .. UI.skin)
	elseif input.KeyCode == Enum.KeyCode.L then
		for _, s in ipairs(mounted) do
			if s.def.machine then
				for _, t in ipairs(s.def.machine.transitions) do
					if t.from == s.state then
						s:send(t.event)
						print("[RR_UIDemo] " .. s.def.name .. " -> " .. t.event .. " -> " .. s.state)
						return
					end
				end
			end
		end
	elseif input.KeyCode == Enum.KeyCode.H then
		for _, s in ipairs(mounted) do
			if s.def.types then
				local names = {}
				for n in pairs(s.def.types) do table.insert(names, n) end
				s:push(names[math.random(1, #names)], { name = "Joel" })
			end
		end
	end
end)
