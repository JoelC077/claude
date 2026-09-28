-- RR_UIKit (ModuleScript, client) - rr-ui-foundry runtime for Risky Rails screens.
-- Builds a ScreenGui from a generated screen definition (screens/*.lua) with the "pin + scale" rule:
--   sizes  = Scale of the design area + UIAspectRatioConstraint (FitWithinMaxSize), so a group scales by
--            s = min(areaW / designW, areaH / designH);
--   pins   = AnchorPoint on an edge or centre, margins = design px * s * density (updated on resize);
--   UIScale density per GuiService.ViewportDisplaySize (Theme.density, from canon tech.ui_platform.layout).
-- Colours are bound to roles (Theme.skins[skin][role]); Kit.setSkin reskins every mounted screen live.
-- Also: component states (hover, pressed, on, disabled), the screen state machine, gamepad navigation
-- (NextSelection*, SelectionGroup, themed SelectionImageObject, ButtonB = back, key glyphs), the HUD stack
-- policy, touch-zone avoidance, and motion through rr-game-feel's RR_Feel when present (else fades that
-- snap under Reduce Motion). The same numbers drew the boards; luatest.py proves the layout parity.
--
-- API (LocalScripts):
--   local screen = Kit.mount(def, opts)       opts = { parent = PlayerGui, state = "open" }
--   screen:send(event) -> bool                 state machine event (illegal events are ignored and warned)
--   screen:set(key, value)                     screen data ({slot} texts, roles and chip "on" states follow)
--   screen:push(typeName, slots) / screen:clear(typeName)   HUD stack (type catalogue in the definition)
--   screen:board(board)                        apply a board from the definition (demo and tests)
--   screen.Action.Event:Connect(fn(name, data))   hit actions for game code;  screen.Changed (to, from, event)
--   screen:destroy()
--   Kit.setSkin(name) · Kit.useFeel(module) · Kit.inputClass() · Kit.displaySize() · Kit.reduceMotion()

local Players = game:GetService("Players")
local GuiService = game:GetService("GuiService")
local UserInputService = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")
local ContextActionService = game:GetService("ContextActionService")

local Theme = require(script.Parent:WaitForChild("RR_UITheme"))
local Templates = require(script.Parent:WaitForChild("RR_UITemplates"))

local Kit = {}
Kit.Theme = Theme
Kit.skin = Theme.skin
Kit.screens = {}
Kit.fadeTime = 0.15
Kit.reflowTime = 0.18

local Feel = nil
do
	local m = script.Parent:FindFirstChild("RR_Feel")
	if m then
		local ok, r = pcall(require, m)
		if ok then Feel = r end
	end
end

function Kit.useFeel(mod)
	Feel = mod
end

local PINS = { tl = { 0, 0 }, tc = { 0.5, 0 }, tr = { 1, 0 }, cl = { 0, 0.5 }, cc = { 0.5, 0.5 }, cr = { 1, 0.5 },
	bl = { 0, 1 }, bc = { 0.5, 1 }, br = { 1, 1 } }
local STATE_ORDER = { "on", "hover", "pressed", "disabled" }
local CLASSES = { frame = "Frame", text = "TextLabel", image = "ImageLabel", hit = "TextButton", stack = "Frame" }

-- ------------------------------------------------------------------ helpers
local function new(className, props, parent)
	local inst = Instance.new(className)
	for k, v in pairs(props) do
		inst[k] = v
	end
	if parent then inst.Parent = parent end
	return inst
end
Kit.new = new

local function fmt(v)
	if type(v) == "number" then
		if v == math.floor(v) then return string.format("%d", v) end
		return tostring(v)
	end
	return tostring(v)
end

local function fillSlots(s, slots, keepUnknown)
	if type(s) ~= "string" then return s end
	return (string.gsub(s, "{([%a_][%w_]*)|?(%a*)}", function(name, filter)
		local v = slots and slots[name]
		if v == nil or v == false then
			if keepUnknown then return nil end
			return ""
		end
		v = fmt(v)
		if filter == "lower" then return string.lower(v) end
		if filter == "upper" then return string.upper(v) end
		return v
	end))
end
Kit.fillSlots = fillSlots

local function condOk(expr, slots)
	if expr == nil then return true end
	local k, v = string.match(expr, "^%s*([%w_]+)%s*=%s*(.-)%s*$")
	if k then
		return string.lower(fmt(slots[k] or "")) == string.lower(v)
	end
	local x = slots[expr]
	return x ~= nil and x ~= false and x ~= 0 and x ~= "0" and x ~= "false" and x ~= ""
end
Kit.condOk = condOk

local function pinOf(n, x, y, w, h, pw, ph)
	if n.pin and PINS[n.pin] then return PINS[n.pin][1], PINS[n.pin][2] end
	local function f(c, s)
		if c < s / 3 then return 0 end
		if c > 2 * s / 3 then return 1 end
		return 0.5
	end
	return f(x + w / 2, pw), f(y + h / 2, ph)
end
Kit.pinOf = pinOf

local function color(role)
	local skin = Theme.skins[Kit.skin] or Theme.skins[Theme.skin]
	return skin[role]
end

function Kit.inputClass()
	local ok, v = pcall(function() return UserInputService.PreferredInput end)
	if ok and v then return v.Name end
	if UserInputService.GamepadEnabled and not UserInputService.TouchEnabled then return "Gamepad" end
	if UserInputService.TouchEnabled then return "Touch" end
	return "KeyboardAndMouse"
end

function Kit.displaySize()
	local ok, v = pcall(function() return GuiService.ViewportDisplaySize end)
	if ok and v then return v.Name end
	local c = Kit.inputClass()
	if c == "Touch" then return "Small" end
	if c == "Gamepad" then return "Large" end
	return "Medium"
end

function Kit.reduceMotion()
	if Feel and Feel.settings then return Feel.settings.reduceMotion == true end
	local ok, v = pcall(function() return GuiService.ReducedMotionEnabled end)
	return ok and v == true
end

local function fontFor(styleName)
	local st = Theme.type[styleName] or Theme.type.label
	local f = Theme.fonts[st.font]
	if f.enum then return Font.fromEnum(Enum.Font[f.enum]), st end
	return Font.new(f.family, Enum.FontWeight[st.weight] or Enum.FontWeight.Bold), st
end

-- transparency fades over a subtree (the no-Feel fallback; snaps under Reduce Motion)
local baseT = setmetatable({}, { __mode = "k" })
local TPROPS = { "BackgroundTransparency", "TextTransparency", "ImageTransparency", "Transparency" }
local function eachFadeable(root, fn)
	local list = { root }
	for _, d in ipairs(root:GetDescendants()) do table.insert(list, d) end
	for _, inst in ipairs(list) do
		for _, p in ipairs(TPROPS) do
			local ok, v = pcall(function() return inst[p] end)
			if ok and type(v) == "number" and not (p == "Transparency" and not inst:IsA("UIStroke")) then
				fn(inst, p, v)
			end
		end
	end
end

function Kit.fade(root, alpha, dur)
	if Kit.reduceMotion() then dur = 0 end
	eachFadeable(root, function(inst, p, v)
		baseT[inst] = baseT[inst] or {}
		if baseT[inst][p] == nil then baseT[inst][p] = v end
		local b = baseT[inst][p]
		local target = b + (1 - b) * (1 - alpha)
		if dur and dur > 0 then
			TweenService:Create(inst, TweenInfo.new(dur, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { [p] = target }):Play()
		else
			inst[p] = target
		end
	end)
end

function Kit.hasFeel(event)
	return Feel ~= nil and event ~= nil and Feel.Presets ~= nil and Feel.Presets.events ~= nil and Feel.Presets.events[event] ~= nil
end

function Kit.motion(event, targets, fallback, root)
	if Kit.hasFeel(event) then
		local ok = pcall(Feel.play, event, { targets = targets })
		if ok then return "feel" end
	end
	if root and fallback == "in" then
		Kit.fade(root, 0, 0)
		Kit.fade(root, 1, Kit.fadeTime)
	elseif root and fallback == "out" then
		Kit.fade(root, 0, Kit.fadeTime)
	end
	return "fallback"
end

-- ------------------------------------------------------------------ screen
local Screen = {}
Screen.__index = Screen

function Kit.mount(def, opts)
	opts = opts or {}
	local parent = opts.parent
	if not parent then parent = Players.LocalPlayer:WaitForChild("PlayerGui") end
	local self = setmetatable({
		def = def, parent = parent, nodes = {}, nodeDefs = {}, data = {}, regs = {}, binds = {}, comps = {},
		layers = {}, stacks = {}, texts = {}, onConds = {}, glyphs = {}, feel = {}, lift = {}, conns = {},
		baseText = {}, d = 1, state = nil,
	}, Screen)
	self.Action = Instance.new("BindableEvent")
	self.Changed = Instance.new("BindableEvent")
	for k, v in pairs(def.data or {}) do self.data[k] = v.default end
	for i, n in ipairs(def.nodes) do
		local mode = n.layer == "backdrop" and "None" or def.insets
		local L = self:layer(mode, n.layer == "backdrop")
		self:build(n, L.gui, nil, true, mode, self.data, { uiscaled = false, stretch = false, index = i })
	end
	self:setupNav()
	self:rescale()
	self:watchTouch()
	for _, c in ipairs(self.onConds) do self:setFlag(c.id, "on", condOk(c.expr, self.data)) end
	for mode, L in pairs(self.layers) do
		table.insert(self.conns, L.gui:GetPropertyChangedSignal("AbsoluteSize"):Connect(function() self:rescale() end))
	end
	pcall(function()
		table.insert(self.conns, GuiService:GetPropertyChangedSignal("ViewportDisplaySize"):Connect(function() self:rescale() end))
	end)
	pcall(function()
		table.insert(self.conns, UserInputService:GetPropertyChangedSignal("PreferredInput"):Connect(function() self:inputChanged() end))
	end)
	if def.machine then
		self.state = opts.state or def.machine.initial
		self:applyLook(false)
	end
	self:inputChanged()
	table.insert(Kit.screens, self)
	return self
end

function Screen:layer(mode, backdrop)
	if self.layers[mode] then return self.layers[mode] end
	local gui = new("ScreenGui", {
		Name = self.def.name .. (backdrop and "_Backdrop" or ""), ResetOnSpawn = false,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
		DisplayOrder = (self.def.displayOrder or 10) - (backdrop and 1 or 0),
	}, nil)
	pcall(function() gui.ScreenInsets = Enum.ScreenInsets[mode] end)
	pcall(function() gui.SafeAreaCompatibility = Enum.SafeAreaCompatibility.None end)
	gui.Parent = self.parent
	local L = { gui = gui, mode = mode, s = 1 }
	self.layers[mode] = L
	return L
end

-- registry of design-px properties that follow the scale
function Screen:reg(inst, kind, v, mode, dd, extra)
	local e = { inst = inst, kind = kind, v = v, mode = mode, dd = dd, x = extra }
	table.insert(self.regs, e)
	if self.layers[mode] and self.layers[mode].aw then self:applyReg(e) end
	return e
end

function Screen:k(mode, dd)
	local L = self.layers[mode]
	if not L then return dd and self.d or 1 end
	return L.s * (dd and self.d or 1)
end

function Screen:applyReg(e)
	local inst, k = e.inst, self:k(e.mode, e.dd)
	if e.kind == "TextSize" then
		inst.TextSize = e.v * k
	elseif e.kind == "Thickness" then
		inst.Thickness = e.v * k
	elseif e.kind == "Corner" then
		inst.CornerRadius = UDim.new(0, e.v * k)
	elseif e.kind == "Tile" then
		inst.TileSize = UDim2.fromOffset(e.v * k, e.v * k)
	elseif e.kind == "UIScale" then
		inst.Scale = self.d * self:ratio(e.mode, e.x and e.x.top)
	elseif e.kind == "Top" then
		self:placeTop(inst, e.x.node, e.mode)
	elseif e.kind == "Dy" then
		local b = e.x.base
		inst.Position = UDim2.new(b.X.Scale, b.X.Offset, b.Y.Scale, b.Y.Offset + (e.x.dy or 0) * k)
	elseif e.kind == "Focus" then
		local f = Theme.focus
		k = k * self:ratio(e.mode, self.focusTop)
		inst.Size = UDim2.new(1, 2 * f.pad * k, 1, 2 * f.pad * k)
		inst.Position = UDim2.fromOffset(-f.pad * k, -f.pad * k)
	end
end

-- own fit (the same rule as uimodel.group_fit): an area smaller than the design area shrinks a pinned group only
-- as much as that group needs to stay inside it; bigger areas scale every group by the same s.
local function extent(p, a, size, full)
	if p == 0 then return a + size end
	if p == 1 then return full - a end
	return size + 2 * math.abs(a + size / 2 - full / 2)
end

function Screen:groupFit(n, L, D)
	if L.s >= 1 or n.stretch then return L.s end
	local x, y, w, h = n.rect[1] - D.x, n.rect[2] - D.y, n.rect[3], n.rect[4]
	local px, py = pinOf(n, x, y, w, h, D.w, D.h)
	local ex = math.max(extent(px, x, w, D.w), 1e-6)
	local ey = math.max(extent(py, y, h, D.h), 1e-6)
	return math.max(L.s, math.min(1, L.aw / (ex * self.d), L.ah / (ey * self.d)))
end

-- px per design px of a top-level group relative to its layer's s (1 unless the group keeps its own fit)
function Screen:ratio(mode, topId)
	local L = self.layers[mode]
	return (L and L.r and topId and L.r[topId]) or 1
end

function Screen:rescale()
	self.d = Theme.density[Kit.displaySize()] or 1
	for mode, L in pairs(self.layers) do
		local a = L.gui.AbsoluteSize
		local D = Theme.design[mode]
		L.aw, L.ah = a.X, a.Y
		L.s = math.min(a.X / D.w, a.Y / D.h)
		L.r = {}
		for _, n in ipairs(self.def.nodes) do
			if ((n.layer == "backdrop") and "None" or self.def.insets) == mode and L.s > 0 then
				L.r[n.id] = self:groupFit(n, L, D) / L.s
			end
		end
	end
	self:computeLifts()
	local keep = {}
	for _, e in ipairs(self.regs) do
		if e.inst.Parent ~= nil or e.kind == "Focus" then
			self:applyReg(e)
			table.insert(keep, e)
		end
	end
	self.regs = keep
	for _, st in pairs(self.stacks) do st:refresh(false) end
end

-- ------------------------------------------------------------------ geometry
function Screen:topBox(n, mode)
	local L, D = self.layers[mode], Theme.design[mode]
	local k = L.s * self:ratio(mode, n.id) * self.d
	local x, y, w, h = n.rect[1] - D.x, n.rect[2] - D.y, n.rect[3], n.rect[4]
	local px, py = pinOf(n, x, y, w, h, D.w, D.h)
	local st = n.stretch
	if st then
		local sx, sy = string.find(st, "x") ~= nil, string.find(st, "y") ~= nil
		local mL, mR, mT, mB = x, D.w - x - w, y, D.h - y - h
		local bw = sx and (L.aw - (mL + mR) * k) or w * k
		local bh = sy and (L.ah - (mT + mB) * k) or h * k
		local bx = sx and mL * k or (px * L.aw + (x + px * w - px * D.w) * k - px * bw)
		local by = sy and mT * k or (py * L.ah + (y + py * h - py * D.h) * k - py * bh)
		return bx, by, bw, bh, px, py, k
	end
	local mx, my = x + px * w - px * D.w, y + py * h - py * D.h
	local bw, bh = w * k, h * k
	return px * L.aw + mx * k - px * bw, py * L.ah + my * k - py * bh, bw, bh, px, py, k
end

function Screen:placeTop(inst, n, mode)
	local D = Theme.design[mode]
	local L = self.layers[mode]
	if not L.aw then return end
	local k = L.s * self:ratio(mode, n.id) * self.d
	local x, y, w, h = n.rect[1] - D.x, n.rect[2] - D.y, n.rect[3], n.rect[4]
	local px, py = pinOf(n, x, y, w, h, D.w, D.h)
	local lift = self.lift[n.id] or 0
	if n.stretch then
		local sx, sy = string.find(n.stretch, "x") ~= nil, string.find(n.stretch, "y") ~= nil
		local mL, mR, mT, mB = x, D.w - x - w, y, D.h - y - h
		inst.AnchorPoint = Vector2.new(sx and 0 or px, sy and 0 or py)
		inst.Size = UDim2.new(sx and 1 or 0, sx and -(mL + mR) * k or w * k, sy and 1 or 0, sy and -(mT + mB) * k or h * k)
		inst.Position = UDim2.new(sx and 0 or px, sx and mL * k or (x + px * w - px * D.w) * k,
			sy and 0 or py, (sy and mT * k or (y + py * h - py * D.h) * k) - lift)
	else
		inst.AnchorPoint = Vector2.new(px, py)
		inst.Size = UDim2.fromScale(w / D.w, h / D.h)
		inst.Position = UDim2.new(px, (x + px * w - px * D.w) * k, py, (y + py * h - py * D.h) * k - lift)
	end
end

local function placeChild(inst, n, pdw, pdh, keep)
	local x, y, w, h = n.rect[1], n.rect[2], n.rect[3], n.rect[4]
	local qx, qy = pinOf(n, x, y, w, h, pdw, pdh)
	inst.AnchorPoint = Vector2.new(qx, qy)
	inst.Position = UDim2.fromScale((x + qx * w) / pdw, (y + qy * h) / pdh)
	inst.Size = UDim2.fromScale(w / pdw, h / pdh)
	if keep and w > 0 and h > 0 then
		new("UIAspectRatioConstraint", { AspectRatio = w / h }, inst)
	end
end

-- touch zones: the real JumpButton / thumbstick ring when the TouchGui exists, else Theme.zones (worst case)
function Screen:zoneRect(name, mode)
	local L = self.layers[mode]
	local tg = self.parent:FindFirstChild("TouchGui")
	local frame = tg and tg:FindFirstChild("TouchControlFrame")
	if frame then
		local obj
		if name == "jump" then
			obj = frame:FindFirstChild("JumpButton")
		else
			local dyn = frame:FindFirstChild("DynamicThumbstickFrame")
			obj = dyn and dyn:FindFirstChild("ThumbstickStart")
		end
		if obj and obj.Visible then
			local p, s, o = obj.AbsolutePosition, obj.AbsoluteSize, frame.AbsolutePosition
			return p.X - o.X, p.Y - o.Y, s.X, s.Y
		end
		if obj then return nil end
	end
	if Kit.inputClass() ~= "Touch" then return nil end
	local size = math.min(L.aw, L.ah) <= Theme.zones.smallScreen and "small" or "large"
	local z = Theme.zones[name] and Theme.zones[name][size]
	if not z then return nil end
	local x = name == "jump" and L.aw - z[1] or 0
	return x, L.ah - z[2], z[1], z[2]
end

-- re-lift when Roblox's touch controls appear, move, hide or show after mount (TouchGui is created late, the
-- JumpButton is hidden until a character spawns, ability controls move it)
local TOUCH_NAMES = { TouchGui = true, TouchControlFrame = true, JumpButton = true, DynamicThumbstickFrame = true, ThumbstickStart = true }

function Screen:relift()
	if self.dead then return end
	self:computeLifts()
	for _, e in ipairs(self.regs) do
		if e.kind == "Top" then self:applyReg(e) end
	end
	for _, st in pairs(self.stacks) do st:refresh(false) end
end

function Screen:watchTouch()
	local any = false
	for _, n in ipairs(self.def.nodes) do if n.avoid then any = true end end
	if not any then return end
	self.watched = self.watched or {}
	local function watch(obj)
		if not obj or self.watched[obj] then return end
		self.watched[obj] = true
		for _, prop in ipairs({ "Visible", "AbsolutePosition", "AbsoluteSize" }) do
			table.insert(self.conns, obj:GetPropertyChangedSignal(prop):Connect(function() self:relift() end))
		end
	end
	local function scan()
		local tg = self.parent:FindFirstChild("TouchGui")
		local frame = tg and tg:FindFirstChild("TouchControlFrame")
		if not frame then return end
		watch(frame:FindFirstChild("JumpButton"))
		local dyn = frame:FindFirstChild("DynamicThumbstickFrame")
		watch(dyn and dyn:FindFirstChild("ThumbstickStart"))
	end
	scan()
	table.insert(self.conns, self.parent.DescendantAdded:Connect(function(obj)
		if TOUCH_NAMES[obj.Name] then
			scan()
			self:relift()
		end
	end))
end

function Screen:computeLifts()
	for _, n in ipairs(self.def.nodes) do
		if n.avoid then
			local mode = n.layer == "backdrop" and "None" or self.def.insets
			self.lift[n.id] = 0
			local bx, by, bw, bh = self:topBox(n, mode)
			local lift = 0
			for _, zn in ipairs(n.avoid) do
				local zx, zy, zw, zh = self:zoneRect(zn, mode)
				if zx and bx < zx + zw and zx < bx + bw and by < zy + zh and zy < by + bh then
					lift = math.max(lift, by + bh - zy)
				end
			end
			self.lift[n.id] = lift
		end
	end
end

-- ------------------------------------------------------------------ building
function Screen:bindColor(inst, prop, role, slots, grad)
	local b = { inst = inst, prop = prop, role = role, slots = slots, grad = grad }
	table.insert(self.binds, b)
	self:applyBind(b)
	return b
end

function Screen:applyBind(b)
	if b.grad then
		local c1 = color(fillSlots(b.role[1], b.slots)) or Color3.new(1, 1, 1)
		local c2 = color(fillSlots(b.role[2], b.slots)) or c1
		b.inst.Color = ColorSequence.new(c1, c2)
	else
		local c = color(fillSlots(b.role, b.slots))
		if c then b.inst[b.prop] = c end
	end
end

function Screen:build(n, parent, pdesign, isTop, mode, slots, ctx)
	if not isTop and not (condOk(n["if"], slots) and not (n.unless and condOk(n.unless, slots))) then return nil end
	local class = CLASSES[n.type or "frame"] or "Frame"
	if n.pattern then class = "ImageLabel" end
	local inst = new(class, { Name = n.id, BackgroundTransparency = 1, BorderSizePixel = 0 }, nil)
	inst.ZIndex = ctx.index or 1
	local dd = not ctx.uiscaled
	local childCtx = { uiscaled = ctx.uiscaled, stretch = false, comp = ctx.comp }
	if isTop then
		self:reg(inst, "Top", 0, mode, true, { node = n })
		if not n.stretch then
			new("UIAspectRatioConstraint", { AspectRatio = n.rect[3] / n.rect[4] }, inst)
			self:reg(new("UIScale", { Scale = 1 }, inst), "UIScale", 1, mode, false, { top = n.id })
			childCtx.uiscaled = true
		end
		childCtx.stretch = n.stretch ~= nil
	else
		placeChild(inst, n, pdesign[1], pdesign[2], ctx.stretch)
	end
	dd = not childCtx.uiscaled
	if n.rot then inst.Rotation = n.rot end
	if n.visible == false then inst.Visible = false end
	if n.fill then
		self:bindColor(inst, "BackgroundColor3", n.fill, slots)
		inst.BackgroundTransparency = 1 - (n.comp and 1 or (n.alpha or 1))
	end
	if n.gradient then
		inst.BackgroundColor3 = Color3.new(1, 1, 1)
		inst.BackgroundTransparency = 1 - (n.alpha or 1)
		local g = new("UIGradient", { Rotation = 90 }, inst)
		self:bindColor(g, "Color", n.gradient, slots, true)
	end
	if n.stroke then
		local s = new("UIStroke", { ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, inst)
		pcall(function() s.BorderStrokePosition = Enum.BorderStrokePosition.Inner end)
		s.Name = "Stroke"
		self:bindColor(s, "Color", n.stroke[1], slots)
		self:reg(s, "Thickness", n.stroke[2], mode, dd)
	end
	if n.radius then
		local c = new("UICorner", {}, inst)
		if n.radius == "circle" then c.CornerRadius = UDim.new(0.5, 0) else self:reg(c, "Corner", n.radius, mode, dd) end
	end
	if n.clip then inst.ClipsDescendants = true end
	if n.pattern then
		inst.Image = Theme.assets.hazardTile
		inst.ScaleType = Enum.ScaleType.Tile
		self:reg(inst, "Tile", Theme.assets.hazardTilePx or 16, mode, dd)
	end
	if n.type == "text" then
		local face, st = fontFor(fillSlots(n.style, slots))
		inst.FontFace = face
		self:reg(inst, "TextSize", st.size, mode, dd)
		inst.TextXAlignment = n.align == "center" and Enum.TextXAlignment.Center or (n.align == "right" and Enum.TextXAlignment.Right or Enum.TextXAlignment.Left)
		inst.TextYAlignment = n.valign == "top" and Enum.TextYAlignment.Top or (n.valign == "bottom" and Enum.TextYAlignment.Bottom or Enum.TextYAlignment.Center)
		inst.TextWrapped = n.wrap == true
		if n.truncate then inst.TextTruncate = Enum.TextTruncate.AtEnd end
		self:bindColor(inst, "TextColor3", n.color or "ink", slots)
		local t = { inst = inst, template = n.text or "", slots = slots }
		self.texts[n.id] = t
		inst.Text = fillSlots(t.template, slots)
	elseif n.type == "image" then
		self:setImage(inst, fillSlots(n.image or "", slots), n)
		inst.ScaleType = Enum.ScaleType.Fit
		if n.tint then self:bindColor(inst, "ImageColor3", n.tint, slots) end
	elseif n.type == "hit" then
		inst.Text = ""
		inst.AutoButtonColor = false
		inst.Selectable = true
		inst.Active = true
		self:wireHit(inst, n)
	end
	if n.bar then
		local v = tonumber(slots[n.bar]) or 1
		local sz = inst.Size
		inst.Size = UDim2.fromScale(sz.X.Scale * math.max(0, math.min(1, v)), sz.Y.Scale)
	end
	if n.comp then
		childCtx.comp = { id = n.id, root = inst, def = n, flags = {}, base = {}, feel = {} }
		self.comps[n.id] = childCtx.comp
		if n.on then table.insert(self.onConds, { id = n.id, expr = n.on }) end
	end
	if n.feel then
		self.feel[n.feel] = self.feel[n.feel] or inst
		if ctx.comp then ctx.comp.feel[n.feel] = inst end
		if childCtx.comp then childCtx.comp.feel[n.feel] = inst end
	end
	self.nodes[n.id] = inst
	self.nodeDefs[n.id] = n
	for i, ch in ipairs(n.children or {}) do
		childCtx.index = i
		self:build(ch, inst, { n.rect[3], n.rect[4] }, false, mode, slots, childCtx)
	end
	if n.stack then
		self.stacks[n.id] = Kit.Stack.new(self, n, inst, mode, childCtx.uiscaled)
	end
	if n.comp then self:captureBase(childCtx.comp) end
	inst.Parent = parent
	return inst
end

function Screen:setImage(inst, name, n)
	local icons = Theme.assets.icons or {}
	if string.sub(name, 1, 5) == "icon." then
		local ic = icons[string.sub(name, 6)]
		if ic then
			inst.Image = Theme.assets.iconSheet
			inst.ImageRectOffset = Vector2.new(ic.offset[1], ic.offset[2])
			inst.ImageRectSize = Vector2.new(ic.size[1], ic.size[2])
		else
			inst.Visible = false
		end
	elseif string.sub(name, 1, 4) == "key." then
		local ok, img = pcall(function() return UserInputService:GetImageForKeyCode(Enum.KeyCode[string.sub(name, 5)]) end)
		if ok and img then inst.Image = img end
		table.insert(self.glyphs, inst)
	end
end

-- ------------------------------------------------------------------ components and states
function Screen:captureBase(comp)
	for _, over in pairs(comp.def.states or {}) do
		for id, props in pairs(over) do
			local inst = self.nodes[id]
			if inst and not comp.base[id] then
				local n = self.nodeDefs[id]
				comp.base[id] = { fill = n.fill, stroke = n.stroke, color = n.color, visible = n.visible ~= false,
					text = n.text, pos = inst.Position }
			end
		end
	end
end

function Screen:findBind(inst, prop)
	for _, b in ipairs(self.binds) do
		if b.inst == inst and b.prop == prop then return b end
	end
	return nil
end

function Screen:applyComp(id)
	local comp = self.comps[id]
	if not comp or not comp.def.states then return end
	local want = {}
	for tid, b in pairs(comp.base) do
		want[tid] = { fill = b.fill, stroke = b.stroke, color = b.color, visible = b.visible, text = b.text, dy = 0, alpha = 1 }
	end
	want[id] = want[id] or { dy = 0, alpha = 1 }
	for _, f in ipairs(STATE_ORDER) do
		if comp.flags[f] and comp.def.states[f] then
			for tid, props in pairs(comp.def.states[f]) do
				want[tid] = want[tid] or { dy = 0, alpha = 1 }
				for k, v in pairs(props) do want[tid][k] = v end
			end
		end
	end
	for tid, w in pairs(want) do
		local inst = self.nodes[tid]
		if inst then
			if w.fill then
				local b = self:findBind(inst, "BackgroundColor3")
				if b then b.role = w.fill; self:applyBind(b) end
			end
			if w.stroke then
				local s = inst:FindFirstChild("Stroke")
				if s then
					local b = self:findBind(s, "Color")
					if b then b.role = w.stroke[1]; self:applyBind(b) end
					for _, e in ipairs(self.regs) do
						if e.inst == s and e.kind == "Thickness" then e.v = w.stroke[2]; self:applyReg(e) end
					end
				end
			end
			if w.color then
				local b = self:findBind(inst, "TextColor3")
				if b then b.role = w.color; self:applyBind(b) end
			end
			if w.visible ~= nil and tid ~= id then inst.Visible = w.visible end
			if w.text and self.texts[tid] then inst.Text = fillSlots(w.text, self.texts[tid].slots) end
			local base = comp.base[tid] and comp.base[tid].pos or inst.Position
			if w.dy and w.dy ~= 0 then
				local e = self.dyReg and self.dyReg[inst]
				if not e then
					self.dyReg = self.dyReg or {}
					e = self:reg(inst, "Dy", 0, self:modeOf(id), not self:isScaled(id), { base = base, dy = w.dy })
					self.dyReg[inst] = e
				end
				e.x.dy = w.dy
				self:applyReg(e)
			elseif self.dyReg and self.dyReg[inst] then
				self.dyReg[inst].x.dy = 0
				self:applyReg(self.dyReg[inst])
			end
		end
	end
	Kit.fade(comp.root, want[id].alpha or 1, 0)
	comp.root.Selectable = not comp.flags.disabled
end

function Screen:modeOf(id)
	local top = id
	while self.nodeDefs[top] and self:parentId(top) do top = self:parentId(top) end
	local n = self.nodeDefs[top]
	return (n and n.layer == "backdrop") and "None" or self.def.insets
end

function Screen:parentId(id)
	local inst = self.nodes[id]
	local p = inst and inst.Parent
	if p and self.nodeDefs[p.Name] and self.nodes[p.Name] == p then return p.Name end
	return nil
end

function Screen:isScaled(id)
	local top = id
	while self:parentId(top) do top = self:parentId(top) end
	local n = self.nodeDefs[top]
	return n ~= nil and n.stretch == nil
end

function Screen:setFlag(id, flag, on)
	local comp = self.comps[id]
	if not comp then return end
	if (comp.flags[flag] or false) == (on or false) then return end
	comp.flags[flag] = on or nil
	self:applyComp(id)
end

function Screen:wireHit(inst, n)
	local id = n.id
	table.insert(self.conns, inst.MouseEnter:Connect(function() self:setFlag(id, "hover", true) end))
	table.insert(self.conns, inst.MouseLeave:Connect(function()
		self:setFlag(id, "hover", false)
		self:setFlag(id, "pressed", false)
	end))
	table.insert(self.conns, inst.MouseButton1Down:Connect(function()
		local comp = self.comps[id]
		if comp and comp.flags.disabled then return end
		self:setFlag(id, "pressed", true)
		Kit.motion("ui_button_press", { button = inst }, nil, nil)
	end))
	table.insert(self.conns, inst.MouseButton1Up:Connect(function() self:setFlag(id, "pressed", false) end))
	table.insert(self.conns, inst.Activated:Connect(function() self:activate(id) end))
end

function Screen:can(event)
	local m = self.def.machine
	if not m then return false end
	for _, t in ipairs(m.transitions) do
		if (t.from == self.state or t.from == "*") and t.event == event then return true end
	end
	return false
end

function Screen:activate(id)
	local n, comp = self.nodeDefs[id], self.comps[id]
	if comp and comp.flags.disabled then return false end
	local a = n and n.action
	if type(a) == "string" then
		self.Action:Fire(a, self.data)
		if self:can(a) then self:send(a) end
	elseif type(a) == "table" then
		for k, v in pairs(a.set or {}) do self:set(k, v) end
		for k, dir in pairs(a.cycle or {}) do
			local vals = (self.def.data[k] or {}).values or {}
			local idx = 1
			for i, v in ipairs(vals) do
				if v == self.data[k] then idx = i end
			end
			if #vals > 0 then self:set(k, vals[((idx - 1 + dir) % #vals) + 1]) end
		end
		self.Action:Fire(id, self.data)
	end
	return true
end

function Screen:set(key, value)
	self.data[key] = value
	for _, b in ipairs(self.binds) do
		if b.slots == self.data then self:applyBind(b) end
	end
	for _, t in pairs(self.texts) do
		if t.slots == self.data then t.inst.Text = fillSlots(self.textOverride and self.textOverride[t.inst] or t.template, self.data) end
	end
	for _, c in ipairs(self.onConds) do
		self:setFlag(c.id, "on", condOk(c.expr, self.data))
	end
end

-- ------------------------------------------------------------------ state machine
function Screen:send(event)
	local m = self.def.machine
	if not m then return false end
	for _, t in ipairs(m.transitions) do
		if (t.from == self.state or t.from == "*") and t.event == event then
			local from = self.state
			self.state = t.to
			self:applyLook(true, t.feel)
			self.Changed:Fire(t.to, from, event)
			return true
		end
	end
	warn(string.format("RR_UIKit %s: event '%s' ignored in state '%s'", self.def.name, tostring(event), tostring(self.state)))
	return false
end

local function setOf(list, self)
	local s = {}
	for _, id in ipairs(list or {}) do
		local rid = self:ref(id)
		if rid then s[rid] = true end
	end
	return s
end

function Screen:ref(id)
	if self.nodes[id] then return id end
	local hit
	for k in pairs(self.nodes) do
		if string.sub(k, -(#id + 1)) == "." .. id then
			if hit then return nil end
			hit = k
		end
	end
	return hit
end

function Screen:applyLook(animate, feelEvent)
	local look = (self.def.machine.states or {})[self.state] or {}
	local hide, show, dis = setOf(look.hide, self), setOf(look.show, self), setOf(look.disable, self)
	local panel = self.feel.panel
	local feelPlayed = false
	if animate and panel and Kit.hasFeel(feelEvent) then
		feelPlayed = Kit.motion(feelEvent, { panel = panel }, nil, nil) == "feel"
	end
	local delayHide = feelPlayed and 0.25 or Kit.fadeTime
	for id, n in pairs(self.nodeDefs) do
		local inst = self.nodes[id]
		local want = n.visible ~= false
		if hide[id] then want = false end
		if show[id] then want = true end
		if (hide[id] or show[id] or self.hiddenByLook and self.hiddenByLook[id]) and inst.Visible ~= want then
			local byFeel = feelPlayed and inst == panel
			if animate and want then
				inst.Visible = true
				if not byFeel then Kit.motion(nil, nil, "in", inst) end
			elseif animate and not want then
				if not byFeel then Kit.motion(nil, nil, "out", inst) end
				local token = {}
				self.hideTokens = self.hideTokens or {}
				self.hideTokens[id] = token
				task.delay(Kit.reduceMotion() and 0 or delayHide, function()
					if self.hideTokens[id] == token and not self:visibleIn(id) then inst.Visible = false end
				end)
			else
				inst.Visible = want
				Kit.fade(inst, 1, 0)
			end
		end
	end
	self.hiddenByLook = hide
	for id in pairs(self.comps) do
		self:setFlag(id, "disabled", dis[id] == true)
	end
	self.textOverride = {}
	for id, t in pairs(self.texts) do
		local rid = nil
		for k, v in pairs(look.text or {}) do
			if self:ref(k) == id then rid = v end
		end
		if rid then self.textOverride[t.inst] = rid end
		t.inst.Text = fillSlots(rid or t.template, t.slots)
	end
	self:focusForState()
end

function Screen:visibleIn(id)
	local look = (self.def.machine.states or {})[self.state] or {}
	return not setOf(look.hide, self)[id]
end

-- ------------------------------------------------------------------ gamepad navigation
function Screen:setupNav()
	local nav = self.def.nav or {}
	local ring = new("Frame", { Name = "RR_Focus", BackgroundTransparency = 1 }, nil)
	local f = Theme.focus
	local outer = new("UIStroke", { ApplyStrokeMode = Enum.ApplyStrokeMode.Border, Name = "Stroke" }, ring)
	self:bindColor(outer, "Color", "focus", self.data)
	self:reg(outer, "Thickness", f.outer, self.def.insets, true)
	local corner = new("UICorner", {}, ring)
	self:reg(corner, "Corner", 12 + f.radiusAdd, self.def.insets, true)
	local inner = new("Frame", { Name = "Inner", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, ring)
	local istroke = new("UIStroke", { ApplyStrokeMode = Enum.ApplyStrokeMode.Border, Name = "Stroke" }, inner)
	self:bindColor(istroke, "Color", "ink", self.data)
	self:reg(istroke, "Thickness", f.inner, self.def.insets, true)
	self:reg(ring, "Focus", 0, self.def.insets, true)
	self.focusRing = ring
	local function has(n, id)
		if n.id == id then return true end
		for _, c in ipairs(n.children or {}) do if has(c, id) then return true end end
		return false
	end
	local want = nav.modal or nav.default
	for _, n in ipairs(self.def.nodes) do
		if want and has(n, want) then self.focusTop = n.id end
	end
	for id, edges in pairs(nav.edges or {}) do
		local inst = self.nodes[id]
		if inst then
			inst.SelectionImageObject = ring
			if edges.up then inst.NextSelectionUp = self.nodes[edges.up] end
			if edges.down then inst.NextSelectionDown = self.nodes[edges.down] end
			if edges.left then inst.NextSelectionLeft = self.nodes[edges.left] end
			if edges.right then inst.NextSelectionRight = self.nodes[edges.right] end
		end
	end
	if nav.modal and self.nodes[nav.modal] then
		local m = self.nodes[nav.modal]
		m.SelectionGroup = true
		pcall(function()
			m.SelectionBehaviorUp = Enum.SelectionBehavior.Stop
			m.SelectionBehaviorDown = Enum.SelectionBehavior.Stop
			m.SelectionBehaviorLeft = Enum.SelectionBehavior.Stop
			m.SelectionBehaviorRight = Enum.SelectionBehavior.Stop
		end)
	end
end

function Screen:isOpen()
	local nav = self.def.nav or {}
	local root = nav.modal and self.nodes[nav.modal]
	if not root then return false end
	if not self.def.machine then return root.Visible end
	return self:visibleIn(nav.modal)
end

function Screen:focusForState()
	local nav = self.def.nav or {}
	local name = "RR_UI_Back_" .. self.def.name
	if self:isOpen() then
		if nav.back and not self.backBound then
			ContextActionService:BindActionAtPriority(name, function(_, inputState)
				if inputState == Enum.UserInputState.Begin then self:activate(nav.back) end
				return Enum.ContextActionResult.Sink
			end, false, 3000, Enum.KeyCode.ButtonB)
			self.backBound = true
		end
		if nav.default and Kit.inputClass() == "Gamepad" and self.nodes[nav.default] then
			GuiService.SelectedObject = self.nodes[nav.default]
		end
	else
		if self.backBound then
			ContextActionService:UnbindAction(name)
			self.backBound = false
		end
		local sel = GuiService.SelectedObject
		if sel then
			for _, inst in pairs(self.nodes) do
				if inst == sel then GuiService.SelectedObject = nil break end
			end
		end
	end
end

function Screen:inputChanged()
	local pad = Kit.inputClass() == "Gamepad"
	for _, g in ipairs(self.glyphs) do g.Visible = pad end
	self:rescale()
	if self.def.machine then self:focusForState() end
end

-- ------------------------------------------------------------------ runtime templates (HUD tickets)
function Screen:instantiate(name, slots, parent, rect, pdesign, mode, uiscaled, idPrefix)
	local tpl = Templates[name]
	local function prefix(parts)
		local out = {}
		for i, p in ipairs(parts) do
			local q = {}
			for k, v in pairs(p) do q[k] = v end
			q.id = idPrefix .. "." .. p.id
			if p.children then q.children = prefix(p.children) end
			out[i] = q
		end
		return out
	end
	local root = { id = idPrefix, type = "frame", rect = { rect[1], rect[2], rect[3], rect[4] }, pin = "tl",
		children = prefix(tpl.parts) }
	return self:build(root, parent, pdesign, false, mode, slots, { uiscaled = uiscaled, stretch = false, index = 1 })
end

function Screen:dropTree(inst)
	if not inst then return end
	local gone = {}
	for id, i in pairs(self.nodes) do
		if i == inst or i:IsDescendantOf(inst) then table.insert(gone, id) end
	end
	for _, id in ipairs(gone) do
		self.nodes[id] = nil
		self.nodeDefs[id] = nil
		self.texts[id] = nil
		self.comps[id] = nil
	end
	local keep = {}
	for _, b in ipairs(self.binds) do
		if not (b.inst == inst or b.inst:IsDescendantOf(inst)) then table.insert(keep, b) end
	end
	self.binds = keep
	inst:Destroy()
end

local Stack = {}
Stack.__index = Stack
Kit.Stack = Stack

function Stack.new(screen, n, inst, mode, uiscaled)
	local self = setmetatable({ screen = screen, n = n, st = n.stack, inst = inst, mode = mode, uiscaled = uiscaled,
		items = {}, seq = 0, more = nil }, Stack)
	return self
end

-- the same policy as uimodel.stack_visible (parity-tested)
function Stack:visible()
	local st = self.st
	local mx = st.max or 4
	if (self.screen.lift[self.n.id] or 0) > 0 and st.max_lifted then mx = st.max_lifted end
	local ranked = {}
	for _, it in ipairs(self.items) do table.insert(ranked, it) end
	table.sort(ranked, function(a, b)
		if a.sticky ~= b.sticky then return a.sticky end
		return a.seq > b.seq
	end)
	local vis = {}
	for i = 1, math.min(mx, #ranked) do table.insert(vis, ranked[i]) end
	table.sort(vis, function(a, b) return a.seq < b.seq end)
	local newest, newestCrisis = vis[#vis], nil
	for _, it in ipairs(vis) do
		if it.crisis then newestCrisis = it end
	end
	local full = {}
	for _, f in ipairs(st.full or {}) do
		if f == "newest" and newest then full[newest] = true end
		if f == "newest_crisis" and newestCrisis then full[newestCrisis] = true end
	end
	for _, it in ipairs(vis) do
		it.compact = st.compact ~= nil and not full[it]
		it.halo = it == newestCrisis
	end
	return vis, #self.items - #vis
end

function Stack:push(typeName, extra)
	local t = self.screen.def.types[typeName]
	if not t then
		warn("RR_UIKit: unknown alert type " .. tostring(typeName))
		return nil
	end
	self.seq = self.seq + 1
	local life = (extra and extra.life) or 1
	if self.st.merge == "type" then
		for _, it in ipairs(self.items) do
			if it.type == typeName then
				it.count = it.count + 1
				it.life = life
				it.born = os.clock()
				it.merged = true
				self:arm(it)
				self:refresh(true)
				return it
			end
		end
	end
	local slots = { kind = t.kind, title = t.title, body = fillSlots(t.body or "", extra or {}), stamp = t.stamp, icon = t.icon }
	local it = { type = typeName, seq = self.seq, slots = slots, count = 1, life = life, born = os.clock() }
	it.sticky = condOk(self.st.sticky, slots)
	it.crisis = condOk(self.st.crisis, slots)
	it.fresh = true
	table.insert(self.items, it)
	self:arm(it)
	self:refresh(true)
	return it
end

function Stack:arm(it)
	if it.sticky then return end
	local secs = (self.st.life_s or {})[it.slots.kind] or 5
	local token = {}
	it.token = token
	task.delay(secs, function()
		if it.token == token then self:remove(it) end
	end)
end

function Stack:remove(it)
	for i, x in ipairs(self.items) do
		if x == it then
			table.remove(self.items, i)
			break
		end
	end
	if it.inst then
		local inst = it.inst
		it.inst = nil
		local feel = self.st.feel or {}
		Kit.motion(feel.leave, { ticket = inst:FindFirstChild(inst.Name .. ".mover") or inst }, "out", inst)
		task.delay(Kit.reduceMotion() and 0 or (self.st.leave_s or Kit.fadeTime), function() self.screen:dropTree(inst) end)
	end
	self:refresh(false)
end

function Stack:clear(typeName)
	local gone = {}
	for _, it in ipairs(self.items) do
		if it.type == typeName then table.insert(gone, it) end
	end
	for _, it in ipairs(gone) do self:remove(it) end
	return #gone
end

function Stack:layout(vis)
	local gap = self.st.gap or 8
	local sw, sh = self.n.rect[3], self.n.rect[4]
	local y = sh
	local rects = {}
	for i = #vis, 1, -1 do
		local it = vis[i]
		local tpl = Templates[it.compact and self.st.compact or self.st.template]
		local h = tpl.size[2]
		y = y - h
		rects[i] = { sw - tpl.size[1], y, tpl.size[1], h }
		y = y - gap
	end
	return rects
end

function Stack:refresh(animate)
	local sc = self.screen
	if not sc.layers[self.mode] or not sc.layers[self.mode].aw then return end
	local vis, hidden = self:visible()
	local rects = self:layout(vis)
	local shown = {}
	local sw, sh = self.n.rect[3], self.n.rect[4]
	for i, it in ipairs(vis) do
		shown[it] = true
		local name = it.compact and self.st.compact or self.st.template
		local slots = { kind = it.slots.kind, title = it.slots.title, body = it.slots.body, stamp = it.slots.stamp,
			icon = it.slots.icon, count = it.count > 1 and it.count or nil, life = it.life, halo = it.halo, sticky = it.sticky }
		local sig = name .. "|" .. tostring(it.halo) .. "|" .. tostring(it.count) .. "|" .. tostring(it.life)
		local r = rects[i]
		if not it.inst or it.sig ~= sig then
			local old = it.inst
			if old then sc:dropTree(old) end
			it.inst = sc:instantiate(name, slots, self.inst, r, { sw, sh }, self.mode, self.uiscaled, self.n.id .. ".t" .. it.seq)
			it.sig = sig
			local feel = self.st.feel or {}
			local mover = sc.nodes[self.n.id .. ".t" .. it.seq .. ".mover"]
			if animate and it.fresh then
				Kit.motion(feel.enter, { ticket = mover or it.inst }, "in", it.inst)
				if it.crisis then
					Kit.motion(feel.crisis, { ticket = mover or it.inst, halo = sc.nodes[self.n.id .. ".t" .. it.seq .. ".halo_red"] }, nil, nil)
				end
			elseif animate and it.merged then
				Kit.motion(feel.merge, { stamp = sc.nodes[self.n.id .. ".t" .. it.seq .. ".badge"] }, nil, nil)
			end
			it.fresh, it.merged = false, false
		else
			local target = UDim2.fromScale((r[1]) / sw, r[2] / sh)
			if animate and not Kit.reduceMotion() then
				TweenService:Create(it.inst, TweenInfo.new(Kit.reflowTime, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Position = target }):Play()
			else
				it.inst.Position = target
			end
		end
	end
	for _, it in ipairs(self.items) do
		if not shown[it] and it.inst then
			sc:dropTree(it.inst)
			it.inst, it.sig = nil, nil
		end
	end
	if self.more then
		sc:dropTree(self.more)
		self.more = nil
	end
	if hidden > 0 and self.st.overflow and rects[1] then
		local tpl = Templates[self.st.overflow]
		local top = rects[1]
		local r = { top[1] - tpl.size[1] - (self.st.gap or 8), top[2] + 4, tpl.size[1], tpl.size[2] }
		self.more = sc:instantiate(self.st.overflow, { n = hidden }, self.inst, r, { sw, sh }, self.mode, self.uiscaled, self.n.id .. ".more")
	end
end

function Screen:push(typeName, extra)
	for _, st in pairs(self.stacks) do return st:push(typeName, extra) end
	return nil
end

function Screen:clear(typeName)
	for _, st in pairs(self.stacks) do return st:clear(typeName) end
	return 0
end

-- ------------------------------------------------------------------ boards (demo, tests)
function Screen:board(b)
	for k, v in pairs(b.data or {}) do self:set(k, v) end
	if b.state and self.def.machine and self.state ~= b.state then
		self.state = b.state
		self:applyLook(false)
	end
	for id, flag in pairs(b.comp_states or {}) do
		local rid = self:ref(id)
		if rid then self:setFlag(rid, flag, true) end
	end
	if b.select and self.nodes[self:ref(b.select) or ""] then GuiService.SelectedObject = self.nodes[self:ref(b.select)] end
	for _, st in pairs(self.stacks) do
		for _, it in ipairs(st.items) do
			if it.inst then self:dropTree(it.inst) end
		end
		st.items, st.seq = {}, 0
		for i, p in ipairs(b.push or {}) do
			local extra = {}
			for k, v in pairs(p[2] or {}) do extra[k] = v end
			extra.life = (b.life or {})[i] or 1
			st:push(p[1], extra)
		end
		st:refresh(false)
	end
end

function Screen:destroy()
	self.dead = true
	for _, c in ipairs(self.conns) do c:Disconnect() end
	if self.backBound then ContextActionService:UnbindAction("RR_UI_Back_" .. self.def.name) end
	for _, L in pairs(self.layers) do L.gui:Destroy() end
	for i, s in ipairs(Kit.screens) do
		if s == self then table.remove(Kit.screens, i) break end
	end
end

function Kit.setSkin(name)
	if not Theme.skins[name] then
		warn("RR_UIKit: unknown skin " .. tostring(name))
		return false
	end
	Kit.skin = name
	for _, s in ipairs(Kit.screens) do
		for _, b in ipairs(s.binds) do s:applyBind(b) end
	end
	return true
end

Kit.Screen = Screen
return Kit
