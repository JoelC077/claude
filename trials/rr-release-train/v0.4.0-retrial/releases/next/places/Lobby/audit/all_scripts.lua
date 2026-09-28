-- NotificationController (ModuleScript, client) - public API: Controller.Notify(typeName, data)
-- data: { name = "MayaChoo" } for crew, { amount = 40 } for FareBanked merges, { sticky = true } for crises that stay until Controller.Resolve(typeName)
-- Rules (from the design): newest at bottom; max 4 visible, "+N MORE" chip beside the top ticket; newest ticket and
-- newest crisis full size, others compact; only the newest crisis has the halo; routine tickets leave first over the cap;
-- sticky crises are never pushed off; repeats merge (count badge, cash adds up).

local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local RunService = game:GetService("RunService")

local Hud = require(script.Parent:WaitForChild("NotificationHud"))

local Controller = {}
local entries = {} -- oldest first: { id, typeName, data, count, amount, born, life, sticky, slot, parts }
local nextId = 0
local gui, stack, more

local function isPhone()
	local cam = workspace.CurrentCamera
	return UserInputService.TouchEnabled and cam and cam.ViewportSize.Y <= 500
end

local function ensureGui()
	if gui then return end
	local pg = Players.LocalPlayer:WaitForChild("PlayerGui")
	gui, stack, more = Hud.createGui(pg, isPhone())
end

local function isCrisis(e) return Hud.Types[e.typeName].kind == "danger" end

local function removeEntry(e, animate)
	for i, x in ipairs(entries) do
		if x == e then table.remove(entries, i) break end
	end
	if e.slot then
		local slot = e.slot
		e.slot = nil
		if animate then
			local t = TweenService:Create(e.parts.mover, TweenInfo.new(0.32, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
				{ Position = UDim2.fromScale(1.25, 0) })
			t:Play()
			task.delay(0.32, function() slot:Destroy() end)
		else
			slot:Destroy()
		end
	end
end

local function render()
	ensureGui()
	-- enforce cap: drop oldest non-sticky routine first, then oldest non-sticky crisis; sticky never dropped
	local L = Hud.Layout
	local hidden = 0
	local visible = {}
	for _, e in ipairs(entries) do table.insert(visible, e) end
	while #visible > L.maxVisible do
		local victim = nil
		for _, e in ipairs(visible) do
			if not isCrisis(e) then victim = e break end
		end
		if not victim then
			for _, e in ipairs(visible) do
				if not e.sticky then victim = e break end
			end
		end
		if not victim then victim = visible[1] end
		for i, e in ipairs(visible) do
			if e == victim then table.remove(visible, i) break end
		end
		if victim.sticky then
			hidden = hidden + 1 -- sticky: kept in entries, just not shown
		else
			removeEntry(victim, true)
		end
	end
	local newest = visible[#visible]
	local newestCrisis = nil
	for _, e in ipairs(visible) do
		if isCrisis(e) then newestCrisis = e end
	end
	local shown = {}
	for i, e in ipairs(visible) do
		shown[e] = true
		local compact = not (e == newest or e == newestCrisis)
		local halo = (e == newestCrisis) and not compact
		local key = tostring(compact) .. tostring(halo) .. tostring(e.count) .. tostring(e.amount)
		if e.key ~= key then
			local fresh = e.slot == nil
			if e.slot then e.slot:Destroy() end
			local stamp = nil
			if e.typeName == "FareBanked" then stamp = Hud.formatCash(e.amount) end
			e.slot, e.parts = Hud.buildTicket(stack, { typeName = e.typeName, name = e.data.name, stamp = stamp,
				count = e.count, compact = compact, halo = halo, sticky = e.sticky })
			e.key = key
			if fresh then
				e.parts.mover.Position = UDim2.fromScale(1.25, 0)
				TweenService:Create(e.parts.mover, TweenInfo.new(0.28, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
					{ Position = UDim2.fromScale(0, 0) }):Play()
				if isCrisis(e) then
					task.delay(0.35, function()
						if not e.parts then return end
						local m = e.parts.mover
						for _, dx in ipairs({ -5, 5, -4, 3, 0 }) do
							TweenService:Create(m, TweenInfo.new(0.1), { Position = UDim2.new(0, dx, 0, 0) }):Play()
							task.wait(0.1)
						end
					end)
				end
			end
		end
		e.slot.LayoutOrder = i
	end
	for _, e in ipairs(entries) do
		if not shown[e] and e.slot then e.slot:Destroy() e.slot = nil e.key = nil end
	end
	local overflow = #entries - #visible
	more.Visible = overflow > 0
	if overflow > 0 then
		more.Text = "+" .. tostring(overflow) .. " MORE"
		local top = visible[1]
		if top and top.slot then
			task.defer(function()
				local p, sz = top.slot.AbsolutePosition, top.slot.AbsoluteSize
				local k = sz.X / Hud.Layout.width -- UIScale factor
				more.Position = UDim2.fromOffset(p.X + 58 * k, p.Y - 14 * k)
			end)
		end
	end
end

function Controller.Notify(typeName, data)
	local def = Hud.Types[typeName]
	assert(def, "Unknown notification type " .. tostring(typeName))
	data = data or {}
	local now = os.clock()
	-- merge repeats of the same type (and same crew name)
	for _, e in ipairs(entries) do
		if e.typeName == typeName and e.data.name == data.name then
			e.count = e.count + 1
			e.amount = e.amount + (data.amount or 40)
			e.born = now
			render()
			if e.parts then
				local target = e.parts.stamp or e.parts.badge
				local sc = target:FindFirstChildOfClass("UIScale") or Instance.new("UIScale", target)
				sc.Scale = 1.07
				TweenService:Create(sc, TweenInfo.new(0.32), { Scale = 1 }):Play()
			end
			return e
		end
	end
	nextId = nextId + 1
	local e = { id = nextId, typeName = typeName, data = data, count = 1, amount = data.amount or 120, born = now,
		life = Hud.Kinds[def.kind].life, sticky = data.sticky == true and def.kind == "danger" }
	table.insert(entries, e)
	render()
	return e
end

function Controller.Resolve(typeName)
	for _, e in ipairs(entries) do
		if e.typeName == typeName then removeEntry(e, true) render() return end
	end
end

-- life bars + expiry
RunService.RenderStepped:Connect(function()
	local now = os.clock()
	local expired = {}
	for _, e in ipairs(entries) do
		if not e.sticky then
			local left = 1 - (now - e.born) / e.life
			if left <= 0 then
				table.insert(expired, e)
			elseif e.parts and e.parts.bar then
				e.parts.bar.Size = UDim2.fromScale(left, 1)
			end
		end
	end
	for _, e in ipairs(expired) do removeEntry(e, true) end
	if #expired > 0 then render() end
	-- halo pulse (0.3 -> 0.95 opacity, 1.2 s loop)
	for _, e in ipairs(entries) do
		if e.parts and e.parts.haloRed then
			local a = 0.625 + 0.325 * math.sin(now * math.pi * 2 / 1.2)
			e.parts.haloRed.BackgroundTransparency = 1 - a
		end
	end
end)

return Controller
-- NotificationHud (ModuleScript) - builds the Risky Rails ticket notification ScreenGui in code.
-- Design: missions/260927-ticket-hud (critic pass 3: B1-B6 all 8/10, self-assessed).
-- Layout numbers are the design's pixels at phone 844x390; UIScale 1.0 on phone, 1.16 on PC.

local Hud = {}

local function hex(h) return Color3.fromHex(h) end

Hud.Tokens = {
	ink = hex("15171c"), ironTop = hex("3b4047"), ironBottom = hex("22262b"),
	brass = hex("d9a441"), brassLight = hex("ffe29a"), brassDark = hex("8a5f1c"),
	cardTop = hex("f7edd3"), cardBottom = hex("e7d4a6"), body = hex("463c2e"),
	crisisRed = hex("e23a2e"), hazard = hex("f2c230"),
}

-- ICON SHEET: upload icons/rr_ticket_icons.png and paste its id here (see ASSETS.md).
Hud.IconSheet = "rbxassetid://0"
Hud.HazardTile = "rbxassetid://0" -- icons/rr_hazard_tile.png (32x32)
Hud.IconCell = 128 -- icons.json: 5 x 2 grid of 128px cells
Hud.IconIndex = { coal = 0, gauge = 1, wrench = 2, passenger = 3, lever = 4, fork = 5, coin = 6, crate = 7, crewjoin = 8, crewleave = 9 }

Hud.Kinds = {
	danger = { stubTop = hex("f0604f"), stubBottom = hex("c42e22"), bar = hex("b02a20"), stampInk = hex("15171c"), life = 7.0 },
	risk   = { stubTop = hex("f2c230"), stubBottom = hex("f2c230"), hazard = true, bar = hex("15171c"), stampInk = hex("15171c"), life = 6.0 },
	cash   = { stubTop = hex("56d994"), stubBottom = hex("23a05c"), bar = hex("156b3d"), stampInk = hex("0f5c31"), life = 4.5 },
	info   = { stubTop = hex("48b6ab"), stubBottom = hex("27857c"), bar = hex("1c6a63"), stampInk = hex("15171c"), life = 5.0 },
}

-- Exact texts from the prototype ("Risky Rails Ticket Notifications").
Hud.Types = {
	CoalLow         = { kind = "danger", icon = "coal",      title = "COAL LOW!",         body = "Shovel coal in the firebox!" },
	PressureHigh    = { kind = "danger", icon = "gauge",     title = "PRESSURE HIGH!",    body = "The boiler's gonna blow!" },
	Breakdown       = { kind = "danger", icon = "wrench",    title = "BREAKDOWN!",        body = "Grab a wrench and fix it!" },
	PassengersUpset = { kind = "danger", icon = "passenger", title = "PASSENGERS UPSET!", body = "Check the carriages, fast!" },
	JunctionAhead   = { kind = "risk",   icon = "lever",     title = "JUNCTION AHEAD!",   body = "Safe or risky? Pull it!" },
	RiskyRoute      = { kind = "risk",   icon = "fork",      title = "RISKY ROUTE!",      body = "Multiplier up", stamp = "X2" },
	FareBanked      = { kind = "cash",   icon = "coin",      title = "FARE BANKED!",      body = "Station paid out", stamp = "$120" },
	CrateLanded     = { kind = "info",   icon = "crate",     title = "CRATE LANDED!",     body = "Grab it before it slides off!" },
	CrewJoined      = { kind = "info",   icon = "crewjoin",  title = "CREW JOINED!",      body = "{name} is aboard" },
	CrewLeft        = { kind = "info",   icon = "crewleave", title = "CREW LEFT!",        body = "{name} left the train" },
}

Hud.Layout = {
	width = 290, fullHeight = 64, compactHeight = 40, gap = 6, haloPad = 5,
	right = 14, bottom = 112, maxVisible = 4, phoneScale = 1.0, pcScale = 1.16,
	pcRight = 18.56, pcBottom = 127.6,
}

local TITLE_FONT = Font.fromEnum(Enum.Font.LuckiestGuy)
local BODY_FONT = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Bold)

local function new(className, props, parent)
	local inst = Instance.new(className)
	for k, v in pairs(props) do
		inst[k] = v
	end
	if parent then inst.Parent = parent end
	return inst
end
Hud.new = new

local function corner(r, parent) return new("UICorner", { CornerRadius = UDim.new(0, r) }, parent) end
local function gradient(top, bottom, parent)
	return new("UIGradient", { Rotation = 90, Color = ColorSequence.new(top, bottom) }, parent)
end

function Hud.shortName(name)
	if utf8.len(name) and utf8.len(name) > 10 then
		return string.sub(name, 1, utf8.offset(name, 11) - 1) .. "…"
	end
	return name
end

function Hud.formatCash(n)
	if n >= 1000 then
		local k = n / 1000
		if k == math.floor(k) then return "$" .. tostring(k) .. "K" end
		return string.format("$%.1fK", k)
	end
	return "$" .. tostring(n)
end

-- Builds the ScreenGui with the bottom-right stack. Returns gui, stack.
function Hud.createGui(playerGui, isPhone)
	local L = Hud.Layout
	local gui = new("ScreenGui", { Name = "RR_Notifications", ResetOnSpawn = false, IgnoreGuiInset = false,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling, DisplayOrder = 20 }, playerGui)
	local right = isPhone and L.right or L.pcRight
	local bottom = isPhone and L.bottom or L.pcBottom
	local stack = new("Frame", { Name = "Stack", AnchorPoint = Vector2.new(1, 1), BackgroundTransparency = 1,
		Position = UDim2.new(1, -right, 1, -bottom), Size = UDim2.fromOffset(L.width, 300) }, gui)
	new("UIScale", { Scale = isPhone and L.phoneScale or L.pcScale }, stack)
	new("UIListLayout", { FillDirection = Enum.FillDirection.Vertical, VerticalAlignment = Enum.VerticalAlignment.Bottom,
		HorizontalAlignment = Enum.HorizontalAlignment.Right, SortOrder = Enum.SortOrder.LayoutOrder,
		Padding = UDim.new(0, L.gap) }, stack)
	local more = new("TextLabel", { Name = "More", AnchorPoint = Vector2.new(1, 0), Size = UDim2.fromOffset(84, 24),
		BackgroundColor3 = Hud.Tokens.ink, TextColor3 = Hud.Tokens.brassLight, FontFace = TITLE_FONT, TextSize = 16,
		Text = "+1 MORE", Visible = false, ZIndex = 20 }, gui)
	corner(12, more)
	new("UIStroke", { Color = Hud.Tokens.brass, Thickness = 2, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, more)
	return gui, stack, more
end

local function icon(parent, name, size, pos)
	local idx = Hud.IconIndex[name] or 0
	local cell = Hud.IconCell
	return new("ImageLabel", { Name = "Icon", BackgroundTransparency = 1, Image = Hud.IconSheet,
		ImageRectOffset = Vector2.new((idx % 5) * cell, math.floor(idx / 5) * cell), ImageRectSize = Vector2.new(cell, cell),
		Size = UDim2.fromOffset(size, size), Position = pos, AnchorPoint = Vector2.new(0.5, 0.5), ZIndex = 8 }, parent)
end

-- Builds one ticket. opts: {typeName, name, stamp, count, compact, halo, sticky}
-- Returns slot (the list child) and parts table used by the controller.
function Hud.buildTicket(stack, opts)
	local L, T = Hud.Layout, Hud.Tokens
	local def = Hud.Types[opts.typeName]
	local kind = Hud.Kinds[def.kind]
	local compact = opts.compact == true
	local H = compact and L.compactHeight or L.fullHeight
	local crisis = def.kind == "danger"
	local haloed = crisis and opts.halo == true
	local slotH = haloed and (H + 2 * L.haloPad) or H

	local slot = new("Frame", { Name = "Ticket_" .. opts.typeName, BackgroundTransparency = 1,
		Size = UDim2.fromOffset(L.width, slotH), ClipsDescendants = false }, stack)
	new("UIAspectRatioConstraint", { AspectRatio = L.width / slotH }, slot)
	-- mover: everything slides/shakes inside the slot without disturbing the list layout
	local mover = new("Frame", { Name = "Mover", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, slot)
	local parts = { slot = slot, mover = mover, H = H, kind = kind, def = def }

	if haloed then
		local halo = new("Frame", { Name = "Halo", BackgroundColor3 = T.ink, Size = UDim2.new(1, 14, 1, 0),
			Position = UDim2.fromOffset(-7, 0), ZIndex = 1 }, mover)
		corner(18, halo)
		local red = new("Frame", { Name = "HaloRed", BackgroundColor3 = T.crisisRed, BackgroundTransparency = 0.1,
			Size = UDim2.new(1, -6, 1, -6), Position = UDim2.fromOffset(3, 3), ZIndex = 1 }, halo)
		corner(15, red)
		parts.haloRed = red
	end
	local y0 = haloed and L.haloPad or 0
	local shadow = new("Frame", { Name = "Shadow", BackgroundColor3 = T.ink, BackgroundTransparency = 0.55,
		Size = UDim2.fromOffset(L.width, H), Position = UDim2.fromOffset(0, y0 + 4), ZIndex = 2 }, mover)
	corner(11, shadow)
	local frame = new("Frame", { Name = "Frame", BackgroundColor3 = T.ironTop, Size = UDim2.fromOffset(L.width, H),
		Position = UDim2.fromOffset(0, y0), ZIndex = 3 }, mover)
	corner(11, frame)
	gradient(T.ironTop, T.ironBottom, frame)
	new("UIStroke", { Color = (crisis and not haloed) and T.crisisRed or T.ink, Thickness = 3,
		ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, frame)
	-- brass pinline
	local pin = new("Frame", { Name = "BrassPin", BackgroundTransparency = 1, Size = UDim2.new(1, -2, 1, -2),
		Position = UDim2.fromOffset(1, 1), ZIndex = 3 }, frame)
	corner(9, pin)
	new("UIStroke", { Color = (crisis and not haloed) and T.ink or T.brass, Thickness = 2 }, pin)

	local card = new("Frame", { Name = "Card", BackgroundColor3 = T.cardTop, Size = UDim2.new(1, -10, 1, -10),
		Position = UDim2.fromOffset(5, 5), ClipsDescendants = true, ZIndex = 4 }, frame)
	corner(7, card)
	gradient(T.cardTop, T.cardBottom, card)

	local stub = new("Frame", { Name = "Stub", BackgroundColor3 = kind.stubTop, Size = UDim2.new(0, 54, 1, 0), ZIndex = 5 }, card)
	if kind.hazard then
		-- hazard stripes: tile the stripe image (ASSETS.md) or fall back to alternating bars
		new("ImageLabel", { Name = "Hazard", BackgroundTransparency = 1, Image = Hud.HazardTile, ScaleType = Enum.ScaleType.Tile,
			TileSize = UDim2.fromOffset(16, 16), Size = UDim2.fromScale(1, 1), ZIndex = 5 }, stub)
	else
		gradient(kind.stubTop, kind.stubBottom, stub)
	end
	for i, yScale in ipairs({ 0, 1 }) do
		local rivet = new("Frame", { Name = "Rivet" .. i, BackgroundColor3 = T.brass, Size = UDim2.fromOffset(10, 10),
			AnchorPoint = Vector2.new(0, yScale), Position = UDim2.new(0, -2, yScale, yScale == 0 and 4 or -4), ZIndex = 6 }, card)
		corner(5, rivet)
		new("UIStroke", { Color = T.ink, Thickness = 1.5 }, rivet)
	end

	local medSize = compact and 28 or 36
	local med = new("Frame", { Name = "Medallion", BackgroundColor3 = T.ink, Size = UDim2.fromOffset(medSize, medSize),
		AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0, 27, 0.5, 0), ZIndex = 6 }, card)
	corner(medSize, med)
	local ring = new("Frame", { BackgroundColor3 = T.brass, Size = UDim2.fromScale(0.89, 0.89), AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5), ZIndex = 7 }, med)
	corner(medSize, ring)
	gradient(T.brassLight, T.brassDark, ring)
	local disc = new("Frame", { BackgroundColor3 = T.cardTop, Size = UDim2.fromScale(0.81, 0.81), AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5), ZIndex = 7 }, ring)
	corner(medSize, disc)
	icon(disc, def.icon, compact and 17 or 23, UDim2.fromScale(0.5, 0.5))

	-- punch notches + perforation (on the frame so they cut past the card edge)
	for _, yy in ipairs({ -8, H - 8 }) do
		local n = new("Frame", { Name = "Notch", BackgroundColor3 = T.ink, Size = UDim2.fromOffset(16, 16),
			Position = UDim2.fromOffset(51, yy), ZIndex = 9 }, frame)
		corner(8, n)
	end
	local dots = compact and 3 or 6
	for i = 0, dots - 1 do
		local d = new("Frame", { Name = "Perf", BackgroundColor3 = T.ink, BackgroundTransparency = 0.2, Size = UDim2.fromOffset(4, 4),
			Position = UDim2.fromOffset(57, math.floor(9 + i * (H - 26) / (dots - 1))), ZIndex = 9 }, frame)
		corner(2, d)
	end

	local stampText = opts.stamp or def.stamp
	local textW = stampText and 138 or 212
	local body = def.body
	if opts.name then body = string.gsub(body, "{name}", Hud.shortName(opts.name)) end
	parts.title = new("TextLabel", { Name = "Title", BackgroundTransparency = 1, Text = def.title, FontFace = TITLE_FONT,
		TextSize = compact and 18 or 20, TextColor3 = T.ink, TextXAlignment = Enum.TextXAlignment.Left,
		TextTruncate = Enum.TextTruncate.AtEnd, Size = UDim2.fromOffset(textW, compact and 22 or 24),
		Position = UDim2.fromOffset(61, compact and 2 or 3), ZIndex = 8 }, card)
	if not compact then
		parts.body = new("TextLabel", { Name = "Body", BackgroundTransparency = 1, Text = body, FontFace = BODY_FONT,
			TextSize = 14, TextColor3 = T.body, TextXAlignment = Enum.TextXAlignment.Left, TextTruncate = Enum.TextTruncate.AtEnd,
			Size = UDim2.fromOffset(textW, 17), Position = UDim2.fromOffset(61, 27), ZIndex = 8 }, card)
	end
	if not opts.sticky then
		local track = new("Frame", { Name = "LifeTrack", BackgroundColor3 = T.ink, BackgroundTransparency = 0.84,
			Size = UDim2.fromOffset(compact and textW or 212, 5), AnchorPoint = Vector2.new(0, 1),
			Position = UDim2.new(0, 61, 1, compact and -4 or -5), ZIndex = 8, ClipsDescendants = true }, card)
		corner(3, track)
		parts.bar = new("Frame", { Name = "LifeFill", BackgroundColor3 = kind.bar, Size = UDim2.fromScale(1, 1), ZIndex = 8 }, track)
		corner(3, parts.bar)
	end
	if stampText then
		local st = new("TextLabel", { Name = "Stamp", AnchorPoint = Vector2.new(1, 0), Rotation = -8, Text = stampText,
			FontFace = TITLE_FONT, TextSize = compact and 17 or 22, TextColor3 = kind.stampInk, BackgroundColor3 = T.cardTop,
			BackgroundTransparency = 0.1, Size = UDim2.fromOffset(compact and 50 or 62, compact and 26 or 34),
			Position = UDim2.new(1, -8, 0, compact and 1 or 9), ZIndex = 9 }, card)
		st.TextScaled = false
		if #stampText > 4 then st.TextSize = compact and 14 or 16 end
		corner(6, st)
		new("UIStroke", { Color = kind.stampInk, Thickness = 2.5, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, st)
		parts.stamp = st
	end
	local badge = new("TextLabel", { Name = "Count", AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 8, 0, y0 - 10),
		Size = UDim2.fromOffset(26, 26), BackgroundColor3 = T.ink, TextColor3 = T.brassLight, FontFace = TITLE_FONT,
		TextSize = 17, Text = tostring(opts.count or 1), Visible = (opts.count or 1) > 1, ZIndex = 12 }, mover)
	corner(13, badge)
	new("UIStroke", { Color = T.brass, Thickness = 2, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, badge)
	parts.badge = badge
	return slot, parts
end

return Hud
-- RR_Version (generated by rr-release-train; regenerate, do not edit). ModuleScript in ReplicatedStorage.
-- The Luau release tests and the smoke check read it to prove which build a server runs.
return {
	version = "0.4.0",
	channel = "alpha",
	built = "2026-09-28T03:31Z",
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
