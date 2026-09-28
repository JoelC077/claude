--!strict
-- RR_FeelKitExample (LocalScript, StarterPlayerScripts): how the five moments are wired. Example only: the
-- remote names and GUI paths below are placeholders for the owner's own HUD and alert script.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Kit = require(ReplicatedStorage:WaitForChild("RRFeel"):WaitForChild("RR_FeelKit"))

type LeverParts = Kit.LeverParts
type TicketParts = Kit.TicketParts
type Handle = Kit.Handle

local gui = Players.LocalPlayer:WaitForChild("PlayerGui")

-- Lever console (OQ-031 default: drag). Feed the finger's travel along the console; draw the returned knob.
local function wireLever(parts: LeverParts, side: Kit.Side, knobTravelPx: number)
	local startX: number? = nil
	parts.lever_knob.InputBegan:Connect(function(input: InputObject)
		if input.UserInputType == Enum.UserInputType.Touch or input.UserInputType == Enum.UserInputType.MouseButton1 then
			startX = input.Position.X
		end
	end)
	parts.lever_knob.InputChanged:Connect(function(input: InputObject)
		local x0 = startX
		if x0 == nil then
			return
		end
		local u = math.abs(input.Position.X - x0) / knobTravelPx
		local knob = Kit.leverDrag(u, parts, side)
		parts.lever_knob.Position = UDim2.new(0.5, side * knob * knobTravelPx, 0.5, 0)
	end)
	parts.lever_knob.InputEnded:Connect(function(_input: InputObject)
		startX = nil
		if Kit.leverRelease(parts, side) == "snapback" then
			parts.lever_knob.Position = UDim2.new(0.5, 0, 0.5, 0) -- or Feel.animateValue with P.lever.snapback
		end
	end)
end

-- Crisis alarms: keep each handle so the halo loop stops when the server clears the alert.
local activeCrisis: { [Kit.CrisisKind]: Handle } = {}

local function onCrisisShown(kind: Kit.CrisisKind, parts: TicketParts, gauge: GuiObject?)
	local old = activeCrisis[kind]
	if old then
		old:Stop()
	end
	activeCrisis[kind] = Kit.crisisAlarm(kind, parts, gauge)
end

local function onCrisisCleared(kind: Kit.CrisisKind)
	local h = activeCrisis[kind]
	if h then
		h:Stop()
		activeCrisis[kind] = nil
	end
end

-- Placeholder remotes; replace with the game's alert transport (gameplay.alerts.transport).
local remotes = ReplicatedStorage:FindFirstChild("RRFeelExampleRemotes")
if remotes then
	local brake = remotes:FindFirstChild("HardBrake")
	if brake and brake:IsA("RemoteEvent") then
		brake.OnClientEvent:Connect(function()
			Kit.hardBrake()
		end)
	end
	local speed = remotes:FindFirstChild("Speed")
	if speed and speed:IsA("RemoteEvent") then
		speed.OnClientEvent:Connect(function(v: number)
			Kit.setSpeed(v)
		end)
	end
end

-- Sample use with placeholder HUD objects (only when they exist).
local hud = gui:FindFirstChild("RRHud")
if hud then
	local ticket = hud:FindFirstChild("Ticket")
	local halo = hud:FindFirstChild("Halo")
	local stamp = hud:FindFirstChild("Stamp")
	local cash = hud:FindFirstChild("Cash")
	if ticket and ticket:IsA("GuiObject") then
		local parts: TicketParts = { ticket = ticket, halo = if halo and halo:IsA("GuiObject") then halo else nil }
		Kit.crateLanded(parts)
		onCrisisShown("pressure_high", parts)
		task.delay(3, onCrisisCleared, "pressure_high" :: Kit.CrisisKind)
		if stamp and stamp:IsA("GuiObject") and cash and cash:IsA("TextLabel") then
			Kit.fareBanked(120, { ticket = ticket, stamp = stamp, cash = cash })
		end
	end
	local console = hud:FindFirstChild("LeverConsole")
	if console then
		local knob = console:FindFirstChild("Knob")
		local lamp = console:FindFirstChild("Lamp")
		if console:IsA("GuiObject") and knob and knob:IsA("GuiObject") and lamp and lamp:IsA("GuiObject") then
			wireLever({ lever_panel = console, lever_knob = knob, lamp = lamp }, 1, 120)
		end
	end
end
