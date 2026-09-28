-- RR_Lighting (ModuleScript, client only): applies rr-vfx-lighting looks from RR_LightingPresets (generated).
-- Looks are resolved offline for every biome.time; only overrides (tunnel_under, overbridge_flash) apply here as
-- add/mul/lerp ops, in push order. Canon: tunnels darken client lighting while a tunnel segment is under the train
-- (av.vfx.tunnel). It edits Lighting and its own RRFX_* effects (and an existing Atmosphere, since only one counts).
-- Phones: effects listed in P.phone_post_off are disabled (tech.lighting.post_low_quality).
--
--   Lighting.apply("grassland.day", 1.5)     tween to a look
--   Lighting.push("tunnel_under")             streamer: tunnel segment under the train; Lighting.pop("tunnel_under")
--   Lighting.push("overbridge_flash")         overrides with a duration pop themselves
--   Lighting.setFlashes(false)                players' flashes setting: overrides marked flash (overbridge) are skipped
-- Looks switch their fx_on presets through VFX.setLookFx, so a preset attached later still follows the look.
-- Studio test pending (owner).

local LightingService = game:GetService("Lighting")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local P = require(script.Parent:WaitForChild("RR_LightingPresets"))
local okV, VFX = pcall(function()
	return require(script.Parent:FindFirstChild("RR_VFX"))
end)
if not okV then
	VFX = nil
end

local M = {current = nil, stack = {}, flashes = true}
local tweens = {}
local phone = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled

-- presets that looks switch on and off (headlamp, rain); crisis effects are never touched here
local lookDriven = {}
for _, look in pairs(P.looks) do
	for _, f in ipairs(look.fx_on) do
		lookDriven[f] = true
	end
end
for _, ov in pairs(P.overrides) do
	for _, f in ipairs(ov.fx_on) do
		lookDriven[f] = true
	end
end
if VFX and VFX.setLookFx then
	VFX.setLookFx(lookDriven, {})   -- known before any look is applied: look-driven presets start off
end

local function ensure(cls)
	if cls == "Lighting" then
		return LightingService
	end
	local inst = LightingService:FindFirstChild("RRFX_" .. cls)
	if not inst and cls == "Atmosphere" then
		inst = LightingService:FindFirstChildOfClass("Atmosphere")
	end
	if not inst then
		inst = Instance.new(cls)
		inst.Name = "RRFX_" .. cls
		inst.Parent = LightingService
	end
	return inst
end

local function phoneOff(cls)
	for _, c in ipairs(P.phone_post_off) do
		if c == cls then
			return true
		end
	end
	return false
end

local function applyOp(cur, op)
	local k = op[1]
	if k == "set" then
		return op[2]
	elseif k == "add" then
		return cur + op[2]
	elseif k == "mul" then
		if typeof(cur) == "Color3" then
			return Color3.new(math.min(1, cur.R * op[2]), math.min(1, cur.G * op[2]), math.min(1, cur.B * op[2]))
		end
		return cur * op[2]
	elseif k == "lerp" then
		return cur:Lerp(op[2], op[3])
	end
	return cur
end

local function resolve(name)
	local look = P.looks[name]
	assert(look, "RR_Lighting: no look " .. tostring(name))
	local out, fx = {}, {}
	for cls, props in pairs(look) do
		if cls == "fx_on" then
			for _, f in ipairs(props) do
				fx[f] = true
			end
		else
			local t = {}
			for k, v in pairs(props) do
				t[k] = v
			end
			out[cls] = t
		end
	end
	for _, oname in ipairs(M.stack) do
		local ov = P.overrides[oname]
		for cls, ops in pairs(ov.ops) do
			out[cls] = out[cls] or {}
			for k, op in pairs(ops) do
				local cur = out[cls][k]
				if cur ~= nil or op[1] == "set" then
					out[cls][k] = applyOp(cur, op)
				end
			end
		end
		for _, f in ipairs(ov.fx_on) do
			fx[f] = true
		end
	end
	return out, fx
end

local function tweenTo(inst, props, t)
	if tweens[inst] then
		tweens[inst]:Cancel()
		tweens[inst] = nil
	end
	local tw, now = {}, {}
	for k, v in pairs(props) do
		local ty = typeof(v)
		local jump = k == "ClockTime" and math.abs(v - inst.ClockTime) > 6
		if t > 0 and not jump and (ty == "number" or ty == "Color3") then
			tw[k] = v
		else
			now[k] = v
		end
	end
	for k, v in pairs(now) do
		pcall(function()
			inst[k] = v
		end)
	end
	if next(tw) then
		local ok, tween = pcall(function()
			return TweenService:Create(inst, TweenInfo.new(t, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), tw)
		end)
		if ok then
			tweens[inst] = tween
			tween:Play()
		else
			for k, v in pairs(tw) do
				pcall(function()
					inst[k] = v
				end)
			end
		end
	end
end

function M.apply(name, t)
	M.current = name
	local looks, fx = resolve(name)
	t = t or 1
	for cls, props in pairs(looks) do
		local inst = ensure(cls)
		if cls ~= "Lighting" and phone and phoneOff(cls) then
			props = {Enabled = false}
		end
		tweenTo(inst, props, t)
	end
	if VFX and VFX.setLookFx then
		VFX.setLookFx(lookDriven, fx)
	end
end

function M.setFlashes(on)
	M.flashes = on ~= false
end

function M.push(name, t)
	local ov = P.overrides[name]
	assert(ov, "RR_Lighting: no override " .. tostring(name))
	if ov.flash and not M.flashes then
		return
	end
	for _, n in ipairs(M.stack) do
		if n == name then
			return
		end
	end
	table.insert(M.stack, name)
	M.apply(M.current or P.default, t or ov.tween_in)
	if ov.duration then
		task.delay(ov.duration, function()
			M.pop(name)
		end)
	end
end

function M.pop(name, t)
	for i, n in ipairs(M.stack) do
		if n == name then
			table.remove(M.stack, i)
			M.apply(M.current or P.default, t or P.overrides[name].tween_out)
			return
		end
	end
end

function M.setPhone(on)
	phone = on and true or false
	if M.current then
		M.apply(M.current, 0)
	end
end

function M.looks()
	local names = {}
	for n in pairs(P.looks) do
		table.insert(names, n)
	end
	table.sort(names)
	return names
end

-- compare with the preview's printed sun direction (facts: sun.dir_roblox) when calibrating the heading
function M.sunDirection()
	return LightingService:GetSunDirection()
end

return M
