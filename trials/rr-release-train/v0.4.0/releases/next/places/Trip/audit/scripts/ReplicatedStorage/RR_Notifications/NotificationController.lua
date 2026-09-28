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
