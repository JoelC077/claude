-- RR_VFX (ModuleScript, client only): applies rr-vfx-lighting effect presets from RR_FXPresets (generated).
-- Canon it follows: effects are client-side and attached to the stationary train (av.vfx.client_side,
-- tech.streaming.fx_client); steam rate follows Speed (av.vfx.speed_link). The train never moves, so drift comes
-- from Workspace.GlobalWind = -forward * Speed (particles with WindAffectsDrag and Drag > 0 follow it).
-- Trails need moving attachments: use VFX.trail only on things that move (debris), never on the train body.
--
--   local h = VFX.attach(anchor, "steam_chimney")   anchor = BasePart or Attachment on the train
--   VFX.setSpeed(speed, forwardVector)               every throttle notch change (also sets GlobalWind)
--   VFX.burst(anchor, "coal_dust")                   one-shot presets; cleans itself up
--   VFX.setActive("sparks_axle", true)               start/stop every handle of a loop preset
--   VFX.setFlashes(false)                             players' flashes setting: soft pulses, no flicker (av.feel.flash_limit)
--   VFX.detach(h); VFX.budget()                       remove one; live-particle estimate vs the tier budget
-- Loops start ON, except: priority-1 crisis loops and presets marked start = "off" (sparks_brake) start OFF until
-- setActive; presets a look switches (headlamp, rain) follow the current look, even when attached after
-- Lighting.apply (RR_Lighting calls VFX.setLookFx). attach(anchor, name, {enabled = true/false}) overrides both.
-- Studio test pending (owner): generated and syntax-checked in the cloud, run against stubs in a Lua VM
-- (scripts/luatest.py), never run in Studio.

local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")
local DebrisService = game:GetService("Debris")

local P = require(script.Parent:WaitForChild("RR_FXPresets"))

local VFX = {}
VFX.presets = P.presets
VFX.budgetGuard = true

local handles = {}
local lookDriven, lookOn = {}, {}   -- set by RR_Lighting: presets looks switch, and which the current look has on
local speed, speedK = 0, 0
VFX.flashes = true
local FLASH_OFF_PEAK = 1.5   -- flashes setting off: pulses peak at most this and last twice as long
local forward = Vector3.new(1, 0, 0)
local heartbeat = nil

local function detectTier()
	if UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled then
		return "phone"
	end
	return "pc"
end
VFX.tier = detectTier()

local function tierCfg()
	return P.meta.tiers[VFX.tier] or P.meta.tiers.pc
end

local function rateScale(priority)
	local t = tierCfg()
	return (t.rate_scale and t.rate_scale[priority]) or 1
end

local function fxFolder()
	local f = workspace:FindFirstChild("RRFX_Client")
	if not f then
		f = Instance.new("Folder")
		f.Name = "RRFX_Client"
		f.Parent = workspace
	end
	return f
end

-- attachment frame: "up" puts the UpVector along dir (particles emit along it), "look" the LookVector (lights)
local function orient(offset, dir, mode)
	if not dir then
		return CFrame.new(offset)
	end
	local d = dir.Unit
	if mode == "look" then
		if math.abs(d.Y) > 0.999 then
			return CFrame.new(offset) * CFrame.Angles(d.Y > 0 and math.pi / 2 or -math.pi / 2, 0, 0)
		end
		return CFrame.lookAt(offset, offset + d)
	end
	if math.abs(d.Y) > 0.999 then
		return d.Y > 0 and CFrame.new(offset) or CFrame.new(offset) * CFrame.Angles(math.pi, 0, 0)
	end
	return CFrame.lookAt(offset, offset + d) * CFrame.Angles(-math.pi / 2, 0, 0)
end

local function basePart(anchor)
	if anchor:IsA("Attachment") then
		return anchor.Parent, anchor.CFrame
	end
	return anchor, CFrame.new()
end

local function applyProps(inst, props)
	for k, v in pairs(props) do
		local ok, err = pcall(function()
			inst[k] = v
		end)
		if not ok then
			warn("RR_VFX: " .. inst.ClassName .. "." .. k .. ": " .. tostring(err))
		end
	end
end

local function pulse(light, peak, duration)
	if not VFX.flashes then
		peak, duration = math.min(peak, FLASH_OFF_PEAK), duration * 2
	end
	light.Brightness = peak
	TweenService:Create(light, TweenInfo.new(duration, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {Brightness = 0}):Play()
end

-- live-particle estimate of one handle (loops at their current rate)
local function handleLive(h)
	local live = 0
	if not h.active or h.preset.kind ~= "loop" then
		return 0
	end
	for _, rec in ipairs(h.layers) do
		if rec.inst and rec.inst:IsA("ParticleEmitter") then
			live = live + rec.inst.Rate * rec.inst.Lifetime.Max
		end
	end
	return live
end

local function linked(p, L)
	if p.speed_link then
		for _, n in ipairs(p.speed_link.layers) do
			if n == L.name then
				return true
			end
		end
	end
	return false
end

-- 0..1 share of the speed-linked rate at the current Speed (lights named in speed_link dim with it)
local function linkFrac(p)
	local sl = p.speed_link
	if not sl or sl.max <= 0 then
		return 1
	end
	return (sl.idle + (sl.max - sl.idle) * speedK) / sl.max
end

local function loopRate(h, rec)
	local p, L = h.preset, rec.L
	if p.crackle then
		return 0
	end
	local rate = L.props.Rate or 0
	if linked(p, L) then
		rate = p.speed_link.idle + (p.speed_link.max - p.speed_link.idle) * speedK
	end
	return rate * h.scale * (h.intensity or 1) * (h.guard or 1)
end

local function refresh(h)
	h.scale = rateScale(h.preset.priority)
	if h.preset.kind ~= "loop" then
		-- bursts own their emitters and lights (VFX.burst); a refresh must never switch a flash off mid-burst
		for _, rec in ipairs(h.layers) do
			if rec.inst and rec.inst:IsA("ParticleEmitter") then
				rec.inst.Enabled = false
			end
		end
		return
	end
	for _, rec in ipairs(h.layers) do
		local inst = rec.inst
		if inst then
			if inst:IsA("ParticleEmitter") then
				inst.Rate = loopRate(h, rec)
				inst.Enabled = h.active
			elseif inst:IsA("Light") then
				inst.Enabled = h.active
				rec.scale = linked(h.preset, rec.L) and linkFrac(h.preset) or 1
				if not rec.L.flicker and rec.L.props.Brightness then
					inst.Brightness = rec.L.props.Brightness * rec.scale
				end
			elseif inst:IsA("Beam") then
				inst.Enabled = h.active
			end
		end
	end
end

-- signal over ambience: when the tier budget is exceeded, priority-3 loops give way first, then priority 2
local function enforceBudget()
	if not VFX.budgetGuard then
		return
	end
	local limit = tierCfg().live_particles or math.huge
	for _, h in ipairs(handles) do
		h.guard = 1
		refresh(h)
	end
	for prio = 3, 2, -1 do
		local total, mine = 0, 0
		for _, h in ipairs(handles) do
			local l = handleLive(h)
			total = total + l
			if h.preset.priority == prio then
				mine = mine + l
			end
		end
		if total <= limit or mine <= 0 then
			return
		end
		local k = math.max(0, (limit - (total - mine)) / mine)
		for _, h in ipairs(handles) do
			if h.preset.priority == prio then
				h.guard = k
				refresh(h)
			end
		end
	end
end

local function spawnDebris(h, L)
	local d = L.debris
	local part, baseCF = basePart(h.anchor)
	local origin = (part.CFrame * baseCF * CFrame.new(L.offset)).Position
	local up = (L.dir or Vector3.new(0, 1, 0)).Unit
	local spread = math.rad(d.spread)
	local folder = fxFolder()
	for i = 1, d.count do
		local c = Instance.new("Part")
		c.Size = d.size
		c.Color = d.colours[(i - 1) % #d.colours + 1]
		c.Material = Enum.Material.SmoothPlastic
		c.CanCollide = false
		c.CanQuery = false
		c.CanTouch = false
		c.CastShadow = false
		c.CFrame = CFrame.new(origin) * CFrame.Angles(math.random() * 6.28, math.random() * 6.28, math.random() * 6.28)
		local dir = (CFrame.lookAt(Vector3.new(), up) * CFrame.Angles((math.random() * 2 - 1) * spread, (math.random() * 2 - 1) * spread, 0)).LookVector
		local v = d.speed[1] + math.random() * (d.speed[2] - d.speed[1])
		c.Parent = folder
		c.AssemblyLinearVelocity = dir * v - forward * (speed * (d.carry or 0))
		c.AssemblyAngularVelocity = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 20
		if (d.gravity_scale or 1) < 1 then
			local att = Instance.new("Attachment")
			att.Parent = c
			local vf = Instance.new("VectorForce")
			vf.Attachment0 = att
			vf.RelativeTo = Enum.ActuatorRelativeTo.World
			vf.Force = Vector3.new(0, c.AssemblyMass * workspace.Gravity * (1 - d.gravity_scale), 0)
			vf.Parent = c
		end
		if d.trail and d.trail ~= "" then
			VFX.trail(c, d.trail)
		end
		DebrisService:AddItem(c, d.lifetime)
	end
end

local function step()
	local t = os.clock()
	for _, h in ipairs(handles) do
		if h.active then
			for _, rec in ipairs(h.layers) do
				local f = rec.L.flicker
				if f and rec.inst then
					local k = (f.min + f.max) / 2   -- flashes off: steady glow, no flicker
					if VFX.flashes then
						k = f.min + (f.max - f.min) * (0.5 + 0.5 * math.sin(t * f.hz * 2 * math.pi + rec.phase))
					end
					rec.inst.Brightness = (rec.L.props.Brightness or 1) * k * (rec.scale or 1)
				end
			end
			local c = h.preset.crackle
			if c and h.preset.kind == "loop" and t >= (h.nextCrackle or 0) then
				for _, rec in ipairs(h.layers) do
					if rec.inst and rec.inst:IsA("ParticleEmitter") then
						rec.inst:Emit(math.max(1, math.floor(math.random(c.emit[1], c.emit[2]) * h.scale + 0.5)))
					elseif rec.inst and rec.inst:IsA("Light") and c.flash then
						pulse(rec.inst, c.flash.peak, c.flash.duration)
					end
				end
				h.nextCrackle = t + c.every[1] + math.random() * (c.every[2] - c.every[1])
			end
		end
	end
end

function VFX.attach(anchor, name, opts)
	opts = opts or {}
	local p = P.presets[name]
	assert(p, "RR_VFX: no preset " .. tostring(name))
	assert(anchor and (anchor:IsA("BasePart") or anchor:IsA("Attachment")), "RR_VFX: anchor must be a BasePart or Attachment")
	local part, baseCF = basePart(anchor)
	local active = false
	if p.kind == "loop" then
		if opts.enabled ~= nil then
			active = opts.enabled ~= false
		elseif lookDriven[name] then
			active = lookOn[name] == true
		else
			active = p.start ~= "off"
		end
	end
	local h = {name = name, preset = p, anchor = anchor, layers = {}, holders = {}, scale = rateScale(p.priority),
		active = active, intensity = opts.intensity}
	for _, L in ipairs(p.layers) do
		local rec = {L = L, phase = math.random() * 6.28}
		local tag = "RRFX_" .. name .. "_" .. L.name
		if L.class == "Debris" then
			rec.debris = true
		elseif L.parent == "part" then
			local box = Instance.new("Part")
			box.Name = tag
			box.Anchored = true
			box.CanCollide = false
			box.CanQuery = false
			box.CanTouch = false
			box.CastShadow = false
			box.Transparency = 1
			box.Size = L.part_size
			box.CFrame = part.CFrame * baseCF * CFrame.new(L.offset)
			local inst = Instance.new(L.class)
			applyProps(inst, L.props)
			if L.dir and L.dir.Y < 0 then
				inst.EmissionDirection = Enum.NormalId.Bottom
			end
			inst.Parent = box
			box.Parent = fxFolder()
			rec.inst = inst
			table.insert(h.holders, box)
		elseif L.class == "Beam" then
			local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
			a0.Name, a1.Name = tag .. "_0", tag .. "_1"
			a0.CFrame = baseCF * CFrame.new(L.offset)
			a1.CFrame = baseCF * CFrame.new(L.a1)
			a0.Parent, a1.Parent = part, part
			local b = Instance.new("Beam")
			applyProps(b, L.props)
			b.Attachment0, b.Attachment1 = a0, a1
			b.Parent = a0
			rec.inst = b
			table.insert(h.holders, a0)
			table.insert(h.holders, a1)
		else
			local att = Instance.new("Attachment")
			att.Name = tag
			local mode = (L.class == "SpotLight" or L.class == "SurfaceLight") and "look" or "up"
			att.CFrame = baseCF * orient(L.offset, L.dir, mode)
			att.Parent = part
			local inst = Instance.new(L.class)
			applyProps(inst, L.props)
			inst.Parent = att
			rec.inst = inst
			table.insert(h.holders, att)
		end
		table.insert(h.layers, rec)
	end
	table.insert(handles, h)
	refresh(h)
	enforceBudget()
	if not heartbeat then
		heartbeat = RunService.Heartbeat:Connect(step)
	end
	return h
end

function VFX.burst(anchor, name, opts)
	local p = P.presets[name]
	assert(p, "RR_VFX: no preset " .. tostring(name))
	local h = VFX.attach(anchor, name, {enabled = false})
	local done = 0
	for _, rec in ipairs(h.layers) do
		local L = rec.L
		local delay = L.delay or 0
		if rec.inst and rec.inst:IsA("ParticleEmitter") and L.emit then
			local n = math.max(1, math.floor(L.emit * h.scale + 0.5))
			task.delay(delay, function()
				if rec.inst.Parent then
					rec.inst:Emit(n)
				end
			end)
			done = math.max(done, delay + rec.inst.Lifetime.Max)
		elseif rec.inst and rec.inst:IsA("Light") then
			rec.inst.Enabled = true
			if L.pulse then
				task.delay(delay, function()
					pulse(rec.inst, L.pulse.peak, L.pulse.duration)
				end)
				done = math.max(done, delay + L.pulse.duration)
			end
		elseif rec.debris then
			task.delay(delay, function()
				spawnDebris(h, L)
			end)
			done = math.max(done, delay + L.debris.lifetime)
		end
	end
	task.delay(done + 0.5, function()
		VFX.detach(h)
	end)
	return h
end

function VFX.setSpeed(s, fwd)
	speed = s or 0
	if fwd and fwd.Magnitude > 0 then
		forward = fwd.Unit
	end
	speedK = math.clamp(speed / P.meta.speed_max, 0, 1)
	workspace.GlobalWind = -forward * speed * P.meta.wind_scale
	for _, h in ipairs(handles) do
		refresh(h)
	end
	enforceBudget()
end

function VFX.setIntensity(h, k)
	h.intensity = k
	refresh(h)
	enforceBudget()
end

function VFX.setActive(name, on)
	for _, h in ipairs(handles) do
		if h.name == name and h.preset.kind == "loop" then
			h.active = on and true or false
			refresh(h)
		end
	end
	enforceBudget()
end

-- RR_Lighting: which presets looks drive, and which the current look has on (late attaches follow it)
function VFX.setLookFx(driven, on)
	lookDriven, lookOn = driven or {}, on or {}
	for _, h in ipairs(handles) do
		if lookDriven[h.name] and h.preset.kind == "loop" then
			h.active = lookOn[h.name] == true
			refresh(h)
		end
	end
	enforceBudget()
end

function VFX.setFlashes(on)
	VFX.flashes = on ~= false
end

function VFX.setTier(tier)
	if P.meta.tiers[tier] then
		VFX.tier = tier
		for _, h in ipairs(handles) do
			refresh(h)
		end
		enforceBudget()
	end
end

function VFX.trail(part, name)
	local t = P.trails[name]
	if not t then
		warn("RR_VFX: no trail " .. tostring(name))
		return nil
	end
	local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
	a0.Position = Vector3.new(0, t.width / 2, 0)
	a1.Position = Vector3.new(0, -t.width / 2, 0)
	a0.Parent, a1.Parent = part, part
	local tr = Instance.new("Trail")
	applyProps(tr, t.props)
	tr.Attachment0, tr.Attachment1 = a0, a1
	tr.Parent = part
	return tr
end

function VFX.detach(h)
	for i, x in ipairs(handles) do
		if x == h then
			table.remove(handles, i)
			break
		end
	end
	for _, inst in ipairs(h.holders) do
		inst:Destroy()
	end
	h.holders = {}
	enforceBudget()
end

function VFX.budget()
	local live = 0
	for _, h in ipairs(handles) do
		live = live + handleLive(h)
	end
	return live, tierCfg().live_particles, VFX.tier
end

return VFX
