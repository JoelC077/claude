-- RR_FeelDemo (LocalScript, StarterPlayerScripts) - rr-game-feel Studio demo. Play Solo, then:
--   left column: every event by group (click to play; the mock HUD and lever console are the targets)
--   top row: reduce motion, flashes, haptics, profile, speed rumble (0 / normal / fast), pressure redline, DUMP
--   lever console: drag the red knob sideways past the detent to commit; let go early to see the snapback
-- DUMP prints TweenService:GetValue for every easing style: copy the output lines into a file and run
--   python3 <rr-game-feel>/scripts/feel.py plot curves --out <dir> --compare <file>
-- Mock UI only: flat frames, no assets. Delete this script before publishing.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local folder = ReplicatedStorage:WaitForChild("RRFeel")
local Feel = require(folder:WaitForChild("RR_Feel"))
local P = Feel.Presets

local gui = Instance.new("ScreenGui")
gui.Name = "RR_FeelDemo"
gui.ResetOnSpawn = false
gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")

local INK = Color3.fromRGB(21, 23, 28) -- style.brand.ink
local PAPER = Color3.fromRGB(249, 242, 223) -- ui.hud_kinds.paper_top
local HAZARD = Color3.fromRGB(242, 194, 48) -- style.brand.hazard_yellow
local STEEL = Color3.fromRGB(72, 84, 110) -- ui.lever.panel_steel
local RED = Color3.fromRGB(226, 58, 46) -- style.brand.danger_red (halo, stamp)
local KNOB = Color3.fromRGB(240, 96, 76) -- ui.lever.knob

local function frame(props, parent)
	local f = Instance.new(props.class or "Frame")
	for k, v in pairs(props) do
		if k ~= "class" then f[k] = v end
	end
	f.Parent = parent
	return f
end

local function corner(r, parent)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, r)
	c.Parent = parent
end

-- mock targets -------------------------------------------------------------------------------------
local slot = frame({ Name = "TicketSlot", Size = UDim2.fromOffset(290, 64), Position = UDim2.new(1, -310, 1, -180),
	BackgroundTransparency = 1 }, gui)
local halo = frame({ Name = "Halo", Size = UDim2.new(1, 14, 1, 12), Position = UDim2.fromOffset(-7, -6),
	BackgroundColor3 = RED, BackgroundTransparency = 0.1 }, slot)
corner(18, halo)
local ticket = frame({ Name = "Ticket", class = "CanvasGroup", Size = UDim2.fromScale(1, 1), BackgroundColor3 = PAPER }, slot)
corner(11, ticket)
frame({ class = "TextLabel", Size = UDim2.new(1, -70, 1, 0), Position = UDim2.fromOffset(64, 0),
	BackgroundTransparency = 1, Text = "TICKET", TextColor3 = INK, TextScaled = true }, ticket)
local stamp = frame({ Name = "Stamp", class = "TextLabel", Size = UDim2.fromOffset(68, 36), Position = UDim2.new(1, -74, 0, 14),
	BackgroundColor3 = PAPER, Text = "X2", TextColor3 = INK, TextScaled = true, Rotation = -8 }, ticket)
local gauge = frame({ Name = "Gauge", Size = UDim2.fromOffset(56, 56), Position = UDim2.fromOffset(20, 60),
	BackgroundColor3 = PAPER }, gui)
corner(28, gauge)
local panel = frame({ Name = "LeverPanel", Size = UDim2.fromOffset(300, 90), Position = UDim2.new(0.5, -150, 1, -110),
	BackgroundColor3 = STEEL }, gui)
corner(12, panel)
local timer = frame({ Name = "Timer", Size = UDim2.new(1, -40, 0, 8), Position = UDim2.fromOffset(20, 8),
	BackgroundColor3 = HAZARD }, panel)
local lamp = frame({ Name = "Lamp", Size = UDim2.fromOffset(20, 20), Position = UDim2.fromOffset(12, 40),
	BackgroundColor3 = Color3.fromRGB(54, 58, 66) }, panel) -- style.world.ironwork
corner(10, lamp)
local knob = frame({ Name = "Knob", class = "TextButton", Size = UDim2.fromOffset(44, 44), Position = UDim2.new(0.5, -22, 0, 30),
	BackgroundColor3 = KNOB, Text = "" }, panel)
corner(22, knob)
local card = frame({ Name = "Panel", Size = UDim2.fromOffset(360, 190), Position = UDim2.new(0.5, -180, 0.5, -95),
	BackgroundColor3 = PAPER, Visible = false }, gui)
local report = frame({ Name = "Report", Size = UDim2.fromOffset(380, 220), Position = UDim2.new(0.5, -190, 0.5, -110),
	BackgroundColor3 = PAPER, Visible = false }, gui)
local reportStamp = frame({ Name = "ReportStamp", class = "TextLabel", Size = UDim2.fromOffset(190, 54),
	Position = UDim2.new(0.5, -40, 0.5, 0), BackgroundTransparency = 1, Text = "STAMP", TextColor3 = RED, TextScaled = true }, report)

local targets = { ticket = ticket, stamp = stamp, halo = halo, gauge = gauge, cash = stamp, lever_panel = panel,
	lever_knob = knob, lamp = lamp, timer = timer, panel = card, report = report, report_stamp = reportStamp }

-- controls ------------------------------------------------------------------------------------------
local col = frame({ Name = "Events", class = "ScrollingFrame", Size = UDim2.new(0, 190, 1, -60), Position = UDim2.fromOffset(8, 52),
	BackgroundTransparency = 0.4, BackgroundColor3 = INK, CanvasSize = UDim2.new(0, 0, 0, 0),
	AutomaticCanvasSize = Enum.AutomaticSize.Y }, gui)
local list = Instance.new("UIListLayout")
list.Padding = UDim.new(0, 4)
list.Parent = col

local function button(text, parent, onClick, w)
	local b = frame({ class = "TextButton", Size = UDim2.fromOffset(w or 180, 26), BackgroundColor3 = PAPER, Text = text,
		TextColor3 = INK, TextScaled = true }, parent)
	b.MouseButton1Down:Connect(function() Feel.play("ui_button_press", { targets = { button = b } }) end)
	b.MouseButton1Click:Connect(function()
		Feel.play("ui_button_release", { targets = { button = b } })
		onClick(b)
	end)
	return b
end

local side = 1
local names = {}
for name in pairs(P.events) do table.insert(names, name) end
table.sort(names, function(a, b)
	local ga, gb = P.events[a].group, P.events[b].group
	if ga == gb then return a < b end
	return ga < gb
end)
for _, name in ipairs(names) do
	button(P.events[name].group .. " · " .. name, col, function()
		card.Visible = name == "ui_panel_open" or name == "ui_panel_close"
		report.Visible = name == "fired_stamp"
		Feel.reset(panel)
		Feel.reset(timer)
		side = -side
		Feel.play(name, { targets = targets, side = side, count = { amount = 120, format = function(n) return "$" .. n end } })
	end)
end

local bar = frame({ Name = "Toggles", Size = UDim2.new(1, -16, 0, 34), Position = UDim2.fromOffset(8, 8), BackgroundTransparency = 1 }, gui)
local row = Instance.new("UIListLayout")
row.FillDirection = Enum.FillDirection.Horizontal
row.Padding = UDim.new(0, 6)
row.Parent = bar

local function toggle(label, get, set)
	local b
	b = button(label .. ": " .. tostring(get()), bar, function()
		set(not get())
		b.Text = label .. ": " .. tostring(get())
	end, 150)
end
toggle("reduce motion", function() return Feel.settings.reduceMotion end, function(v) Feel.setSetting("reduceMotion", v) end)
toggle("flashes", function() return Feel.settings.flashes end, function(v) Feel.setSetting("flashes", v) end)
toggle("haptics", function() return Feel.settings.haptics end, function(v) Feel.setSetting("haptics", v) end)
local profiles = { "subtle", "default", "loud" }
local pi = 2
button("profile: default", bar, function(b)
	pi = pi % #profiles + 1
	Feel.setSetting("profile", profiles[pi])
	b.Text = "profile: " .. profiles[pi]
end, 150)
local speeds = { 0, P.meta.speed_normal, P.meta.speed_fast }
local si = 1
button("speed: 0", bar, function(b)
	si = si % #speeds + 1
	Feel.setSpeed(speeds[si])
	b.Text = "speed: " .. speeds[si]
end, 110)
local redline = false
button("pressure: low", bar, function(b)
	redline = not redline
	Feel.setPressure(redline and 1 or 0)
	b.Text = redline and "pressure: redline" or "pressure: low"
end, 150)
button("DUMP", bar, function() print(Feel.curveDump(20)) end, 70)

-- lever drag ----------------------------------------------------------------------------------------
local dragging, committed, startX, forkId = false, false, 0, 0
local travel = 120 -- px from centre to either end on this mock console
local function knobAt(v) knob.Position = UDim2.new(0.5, -22 + v, 0, 30) end
knob.InputBegan:Connect(function(input)
	if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then
		dragging, committed, startX = true, false, input.Position.X
		forkId = forkId + 1 -- demo: every drag is a new junction
		Feel.reset(panel)
		Feel.reset(timer)
	end
end)
UserInputService.InputChanged:Connect(function(input)
	if not dragging or committed then return end
	if input.UserInputType ~= Enum.UserInputType.MouseMovement and input.UserInputType ~= Enum.UserInputType.Touch then return end
	-- two-way lever (gameplay.fork.lever: pulled left or right): u is signed, the sign picks the branch;
	-- a real game passes fork = the junction id so the lever re-arms once per junction (here: per drag)
	local dx = input.Position.X - startX
	local shown = Feel.leverDrag(dx / travel, { targets = targets, fork = forkId })
	if math.abs(shown) >= 1 then
		-- committed: the knob stops following the finger and snaps home (lever.snap, overshoot)
		committed = true
		Feel.animateValue(knob.Position.X.Offset + 22, shown * travel, P.lever.snap, knobAt)
		Feel.play("route_locked", { targets = targets })
	else
		knobAt(shown * travel)
	end
end)
UserInputService.InputEnded:Connect(function(input)
	if not dragging then return end
	if input.UserInputType ~= Enum.UserInputType.MouseButton1 and input.UserInputType ~= Enum.UserInputType.Touch then return end
	dragging = false
	if Feel.leverRelease({ targets = targets }) == "snapback" then
		Feel.animateValue(knob.Position.X.Offset + 22, 0, P.lever.snapback, knobAt)
	end
end)

print("RR_FeelDemo ready: " .. #names .. " events. Reduce motion follows Roblox settings until you toggle it here.")
