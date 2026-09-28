-- RR_FXDemo.client.lua (LocalScript in StarterPlayerScripts): a Studio test stand for rr-vfx-lighting. Not for
-- production. Expects the RRFX folder in ReplicatedStorage (README.md). Keys:
--   L next look · T tunnel on/off · O overbridge flash · B next burst · 1/2/3 speed notch · 0 stop · P phone/PC tier
--   K print the live-particle budget · U print the sun direction (compare with preview facts sun.dir_roblox)

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local folder = ReplicatedStorage:WaitForChild("RRFX")
local P = require(folder:WaitForChild("RR_FXPresets"))
local VFX = require(folder:WaitForChild("RR_VFX"))
local LightingFX = require(folder:WaitForChild("RR_Lighting"))

local player = Players.LocalPlayer
local character = player.Character or player.CharacterAdded:Wait()
local root = character:WaitForChild("HumanoidRootPart")

-- test stand 40 studs in front of the player: one attachment per loop preset, 12 studs apart
local stand = Instance.new("Part")
stand.Name = "RRFX_TestStand"
stand.Anchored = true
stand.CanCollide = false
stand.Transparency = 1
stand.Size = Vector3.new(1, 1, 1)
stand.CFrame = root.CFrame * CFrame.new(0, 2, -40)
stand.Parent = workspace

local loops, bursts = {}, {}
for name, p in pairs(P.presets) do
	if p.kind == "loop" then
		table.insert(loops, name)
	else
		table.insert(bursts, name)
	end
end
table.sort(loops)
table.sort(bursts)

local anchors = {}
for i, name in ipairs(loops) do
	local a = Instance.new("Attachment")
	a.Name = "Demo_" .. name
	a.Position = Vector3.new((i - (#loops + 1) / 2) * 12, 0, 0)
	a.Parent = stand
	anchors[name] = a
	VFX.attach(a, name)
end
local burstAnchor = Instance.new("Attachment")
burstAnchor.Position = Vector3.new(0, 0, -14)
burstAnchor.Parent = stand

local looks = LightingFX.looks()
local lookIndex, burstIndex, tunnel = 1, 0, false
LightingFX.apply(looks[lookIndex], 0)
VFX.setSpeed(P.meta.speeds.normal or 35, stand.CFrame.RightVector)

print("RR_FXDemo: L look, T tunnel, O overbridge, B burst, 1/2/3 speed, 0 stop, P tier, K budget, U sun. Look: " .. looks[lookIndex])

UserInputService.InputBegan:Connect(function(input, processed)
	if processed then
		return
	end
	local k = input.KeyCode
	if k == Enum.KeyCode.L then
		lookIndex = lookIndex % #looks + 1
		LightingFX.apply(looks[lookIndex], 1)
		print("look " .. looks[lookIndex])
	elseif k == Enum.KeyCode.T then
		tunnel = not tunnel
		if tunnel then
			LightingFX.push("tunnel_under")
		else
			LightingFX.pop("tunnel_under")
		end
		print("tunnel_under " .. tostring(tunnel))
	elseif k == Enum.KeyCode.O then
		LightingFX.push("overbridge_flash")
	elseif k == Enum.KeyCode.B then
		burstIndex = burstIndex % #bursts + 1
		VFX.burst(burstAnchor, bursts[burstIndex])
		print("burst " .. bursts[burstIndex])
	elseif k == Enum.KeyCode.One or k == Enum.KeyCode.Two or k == Enum.KeyCode.Three then
		local s = (k == Enum.KeyCode.One and P.meta.speeds.slow) or (k == Enum.KeyCode.Two and P.meta.speeds.normal) or P.meta.speeds.fast
		VFX.setSpeed(s, stand.CFrame.RightVector)
		print("speed " .. tostring(s))
	elseif k == Enum.KeyCode.Zero then
		VFX.setSpeed(0, stand.CFrame.RightVector)
		print("speed 0")
	elseif k == Enum.KeyCode.P then
		VFX.setTier(VFX.tier == "phone" and "pc" or "phone")
		LightingFX.setPhone(VFX.tier == "phone")
		print("tier " .. VFX.tier)
	elseif k == Enum.KeyCode.K then
		local live, limit, tier = VFX.budget()
		print(string.format("live particles %.0f / %s (%s)", live, tostring(limit), tier))
	elseif k == Enum.KeyCode.U then
		print("sun direction " .. tostring(LightingFX.sunDirection()))
	end
end)
