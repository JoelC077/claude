--[[
TrainSplitClient  (LocalScript in StarterPlayerScripts)  v2.0.0

Plays a carriage snap for this player: the break_spec timeline of fx, sounds and camera shake,
plus smooth wreck motion. Listens to ReplicatedStorage.RR_TrainSplitFX (server -> client only)
and never sends anything back.

Everything runs off one render-step callback and the shared server clock
(workspace:GetServerTimeNow()), so every player sees the same moment and nothing drifts.
FX go through ReplicatedStorage.RR_VFX (VFX.burst / VFX.attach) when it exists, else a small
built-in emitter set from TrainSplitConfig.FallbackFX. Camera shake is off when the player's
reduce-motion attribute is true.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")

local Config = require(ReplicatedStorage:WaitForChild("TrainSplitConfig"))
local Shared = require(ReplicatedStorage:WaitForChild("TrainSplitShared"))
local remote = ReplicatedStorage:WaitForChild(Config.RemoteName)
local player = Players.LocalPlayer

local RENDER_NAME = "RR_TrainSplit"
local active = {} -- snaps being played
local shakes = {} -- running camera shakes
local bound = false

-- RR_VFX is looked up on first use, so it may load after this script.
local vfxLib = nil
local function getVfx()
	if vfxLib == nil then
		vfxLib = false
		local mod = ReplicatedStorage:FindFirstChild("RR_VFX")
		if mod and mod:IsA("ModuleScript") then
			local ok, lib = pcall(require, mod)
			if ok and type(lib) == "table" then
				vfxLib = lib
			else
				warn("TrainSplitClient: RR_VFX failed to load, using fallback fx:", lib)
			end
		end
	end
	return vfxLib or nil
end

---------------------------------------------------------------- small builders

local function numberSeq(list)
	if type(list) == "number" then
		return NumberSequence.new(list)
	elseif #list == 1 then
		return NumberSequence.new(list[1])
	end
	local keys = {}
	for i, v in list do
		table.insert(keys, NumberSequenceKeypoint.new((i - 1) / (#list - 1), v))
	end
	return NumberSequence.new(keys)
end

local function colorSeq(list)
	if type(list) == "string" then
		return ColorSequence.new(Color3.fromHex(list))
	elseif #list == 1 then
		return ColorSequence.new(Color3.fromHex(list[1]))
	end
	local keys = {}
	for i, hex in list do
		table.insert(keys, ColorSequenceKeypoint.new((i - 1) / (#list - 1), Color3.fromHex(hex)))
	end
	return ColorSequence.new(keys)
end

local function range(v)
	if type(v) == "number" then
		return NumberRange.new(v)
	end
	return NumberRange.new(v[1], v[2] or v[1])
end

local function later(snap, t, fn)
	table.insert(snap.cleanup, { at = t, fn = fn })
end

-- Static fx point (Terrain sits at the origin, so its attachments are in world space).
local function worldAnchor(worldCF)
	local a = Instance.new("Attachment")
	a.Name = "RR_SplitFX"
	a.CFrame = worldCF
	a.Parent = workspace:FindFirstChildOfClass("Terrain")
	return a
end

-- Fx point riding on a part (a wreck root or the kept half's root).
local function partAnchor(part, worldCF)
	local a = Instance.new("Attachment")
	a.Name = "RR_SplitFX"
	a.CFrame = part.CFrame:ToObjectSpace(worldCF)
	a.Parent = part
	return a
end

local function anchorWorld(anchor)
	if anchor:IsA("Attachment") then
		return anchor.Parent.CFrame * anchor.CFrame
	end
	return anchor.CFrame
end

local function bodyRoot(body)
	if body.root and body.root.Parent then
		return body.root
	end
	-- the reference can arrive before the wreck streams in: find it by name
	local folder = workspace:FindFirstChild(Config.WreckFolderName)
	local model = folder and folder:FindFirstChild(body.name)
	body.root = model and model.PrimaryPart or nil
	return body.root
end

---------------------------------------------------------------- fx, sound, shake

local function fallbackFx(snap, key, anchor, t, loopFor)
	local def = Config.FallbackFX[key]
	if not def then
		return
	end
	local wind = snap.breakCF.ZVector * (Config.SmokeWind or 0) -- the air streams toward the rear
	local emitters = {}
	for _, spec in def.emitters or {} do
		local pe = Instance.new("ParticleEmitter")
		pe.Texture = spec.Texture
		pe.Lifetime = range(spec.Lifetime)
		pe.Speed = range(spec.Speed)
		pe.Size = numberSeq(spec.Size)
		pe.Transparency = numberSeq(spec.Transparency or 0)
		pe.Color = colorSeq(spec.Color or "#FFFFFF")
		pe.LightEmission = spec.LightEmission or 0
		pe.Drag = spec.Drag or 0
		pe.SpreadAngle = Vector2.new(spec.Spread or 180, spec.Spread or 180)
		pe.Rotation = NumberRange.new(0, 360)
		pe.RotSpeed = NumberRange.new(-60, 60)
		local acc = spec.Acceleration and Vector3.new(spec.Acceleration[1], spec.Acceleration[2], spec.Acceleration[3]) or Vector3.zero
		pe.Acceleration = spec.Wind and acc + wind or acc
		pe.Enabled = false
		pe.Parent = anchor
		if def.loop then
			pe.Rate = spec.Rate or 4
			pe.Enabled = true
		else
			pe:Emit(spec.Count or 10)
		end
		table.insert(emitters, pe)
	end
	local pos = anchorWorld(anchor).Position
	if def.flash then
		local light = Instance.new("PointLight")
		light.Brightness = def.flash.Brightness
		light.Range = def.flash.Range
		light.Color = Color3.fromHex(def.flash.Color)
		light.Shadows = false
		light.Parent = anchor
		later(snap, t + def.flash.Time, function()
			light:Destroy()
		end)
	end
	if def.explosion then
		local blast = Instance.new("Explosion") -- look only: no pressure, no broken joints, no craters
		blast.BlastPressure = 0
		blast.BlastRadius = 4
		blast.DestroyJointRadiusPercent = 0
		blast.ExplosionType = Enum.ExplosionType.NoCraters
		blast.Position = pos
		blast.Parent = workspace
	end
	local stopAt = t + (loopFor or 0)
	if loopFor then
		later(snap, stopAt, function()
			for _, pe in emitters do
				pe.Enabled = false
			end
		end)
	end
	later(snap, stopAt + (def.life or 3), function()
		for _, pe in emitters do
			pe:Destroy()
		end
	end)
end

local function stopHandle(handle)
	if type(handle) == "function" then
		handle()
	elseif typeof(handle) == "Instance" then
		handle:Destroy()
	elseif type(handle) == "table" then
		local stop = handle.Stop or handle.Destroy or handle.stop or handle.destroy
		if type(stop) == "function" then
			stop(handle)
		end
	end
end

local function playFx(snap, e, anchor, t)
	local preset = Config.FX[e.fx] or e.fx
	local lib = getVfx()
	local fn = lib and (e.loop and lib.attach or lib.burst)
	if type(fn) == "function" then
		local ok, handle = pcall(fn, anchor, preset)
		if ok then
			if e.loop then
				later(snap, t + e.loop, function()
					pcall(stopHandle, handle)
				end)
			end
			return
		end
		warn(("TrainSplitClient: RR_VFX preset %q failed (%s); using fallback"):format(preset, tostring(handle)))
	end
	fallbackFx(snap, e.fx, anchor, t, e.loop)
end

local function playSound(snap, key, parent, t)
	local def = Config.Sounds[key]
	if not def or type(def.SoundId) ~= "string" or def.SoundId == "" then
		return nil -- no id pasted yet: stay silent
	end
	local sound = Instance.new("Sound")
	sound.Name = "RR_" .. key
	sound.SoundId = def.SoundId
	sound.Volume = def.Volume or 0.5
	sound.Looped = def.Looped == true
	sound.RollOffMode = Enum.RollOffMode.InverseTapered
	sound.RollOffMinDistance = def.RollOffMinDistance or 10
	sound.RollOffMaxDistance = def.RollOffMaxDistance or 400
	local group = SoundService:FindFirstChild(Config.SoundGroupName or "")
	if group and group:IsA("SoundGroup") then
		sound.SoundGroup = group
	end
	-- a Sound inside an attachment or part is heard from there; in SoundService it is flat (2D)
	sound.Parent = (def.Is3D ~= false and parent) or SoundService
	sound:Play()
	if not sound.Looped then
		later(snap, t + (def.MaxLength or 10), function()
			sound:Destroy()
		end)
	end
	return sound
end

local function addShake(kind, worldPos, now)
	if player and player:GetAttribute(Config.ReduceMotionAttribute) == true then
		return
	end
	local spec = Config.Shake[kind]
	local camera = workspace.CurrentCamera
	if not spec or not camera then
		return
	end
	local scale = math.clamp(1 - (camera.CFrame.Position - worldPos).Magnitude / spec.falloff, 0, 1)
	if scale > 0 then
		table.insert(shakes, { start = now, amp = spec.amplitude * scale, dur = spec.duration, freq = spec.frequency, seed = math.random() * 100 })
	end
end

---------------------------------------------------------------- the timeline

-- Where an event happens: a list of anchors plus one world position (for distance-scaled shake).
local function anchorsFor(snap, e)
	local B = snap.breakCF
	local at = e.at
	if at == "wreck" then
		local body = snap.bodies[e.body]
		local root = body and bodyRoot(body)
		return root and { root } or {}, root and root.CFrame.Position or B.Position
	elseif at == "impact" then
		local body = snap.bodies[e.body]
		local root = body and bodyRoot(body)
		if not root then
			return {}, B.Position
		end
		-- ground contact under the falling side at impact time, riding with the wreck
		local rel = B:ToObjectSpace(body.base)
		local _, _, sink = Shared.topple(e.t, body.params.topple)
		local z = rel.Position.Z + Shared.drift(e.t, body.params.V, body.params.brake, body.params.recoil)
		local hit = B * CFrame.new(snap.side * body.params.pivot.X_abs, body.params.pivot.Y - sink, z)
		local rootAt = Shared.bodyCFrame(body.base, B, snap.side, e.t, body.params)
		local a = Instance.new("Attachment")
		a.Name = "RR_SplitFX"
		a.CFrame = rootAt:ToObjectSpace(hit)
		a.Parent = root
		return { a }, hit.Position
	elseif at == "torn_edges" then
		local list = {}
		local holders = { snap.kept }
		local first = snap.bodies[1]
		if first and first.torn then
			table.insert(holders, bodyRoot(first))
		end
		for _, holder in holders do
			if holder and holder.Parent then
				for _, p in Config.Anchors.torn_edges do
					table.insert(list, partAnchor(holder, B * CFrame.new(p)))
				end
			end
		end
		return list, B.Position
	end
	local points = Config.Anchors[at]
	if typeof(points) == "Vector3" then
		points = { points }
	end
	local list = {}
	for _, p in points or {} do
		table.insert(list, worldAnchor(B * CFrame.new(p)))
	end
	return list, (list[1] and anchorWorld(list[1]).Position) or B.Position
end

local function runEvent(snap, e, t, now)
	local anchors, where = anchorsFor(snap, e)
	if e.fx then
		for _, a in anchors do
			playFx(snap, e, a, t)
		end
	end
	if e.sound and anchors[1] then
		local sound = playSound(snap, e.sound, anchors[1], t)
		if sound and e.t_end then
			snap.loops[e] = sound
		end
	end
	if e.shake then
		addShake(e.shake, where, now)
	end
	-- attachments made for this event go once their fx are done
	local keep = (e.loop or 0) + (Config.FxAnchorLife or 12)
	for _, a in anchors do
		if a:IsA("Attachment") then
			later(snap, t + keep, function()
				a:Destroy()
			end)
		end
	end
end

local function shakeAngles(now)
	local x, y, z = 0, 0, 0
	for i = #shakes, 1, -1 do
		local s = shakes[i]
		local u = (now - s.start) / s.dur
		if u >= 1 then
			table.remove(shakes, i)
		elseif u >= 0 then
			local a = 2 * s.amp * (1 - u) * (1 - u) -- math.noise is about +-0.5
			local ph = (now - s.start) * s.freq
			x += math.noise(ph, s.seed) * a
			y += math.noise(s.seed, ph) * a
			z += math.noise(ph, ph, s.seed) * a * 0.5
		end
	end
	return x, y, z
end

local function step()
	local now = workspace:GetServerTimeNow()
	for i = #active, 1, -1 do
		local snap = active[i]
		local t = now - snap.t0
		for _, e in snap.timeline do
			if not snap.fired[e] and t >= e.t then
				snap.fired[e] = true
				-- a one-shot heard about too late is skipped; loops still start
				if t - e.t <= Config.LateTolerance or e.loop or e.t_end then
					local ok, err = pcall(runEvent, snap, e, t, now)
					if not ok then
						warn("TrainSplitClient:", e.id, err)
					end
				end
			end
			if e.t_end and snap.fired[e] and not snap.ended[e] and t >= e.t_end then
				snap.ended[e] = true
				local sound = snap.loops[e]
				if sound then
					sound:Stop()
					sound:Destroy()
				end
			end
		end
		-- smooth each wreck root locally; its welded parts follow
		for _, body in snap.bodies do
			local root = bodyRoot(body)
			if root and t <= snap.params.despawnTime and not (snap.params.handoff and t >= snap.stopT) then
				root.CFrame = Shared.bodyCFrame(body.base, snap.breakCF, snap.side, t, body.params)
			end
		end
		for j = #snap.cleanup, 1, -1 do
			local job = snap.cleanup[j]
			if t >= job.at then
				table.remove(snap.cleanup, j)
				pcall(job.fn)
			end
		end
		if t > snap.finishT and #snap.cleanup == 0 then
			table.remove(active, i)
		end
	end
	if #shakes > 0 then
		local camera = workspace.CurrentCamera
		local x, y, z = shakeAngles(now)
		if camera then
			camera.CFrame = camera.CFrame * CFrame.Angles(math.rad(x), math.rad(y), math.rad(z))
		end
	end
	if #active == 0 and #shakes == 0 and bound then
		bound = false
		RunService:UnbindFromRenderStep(RENDER_NAME)
	end
end

local function valid(p)
	return type(p) == "table"
		and type(p.t0) == "number"
		and typeof(p.breakCF) == "CFrame"
		and type(p.params) == "table"
		and type(p.bodies) == "table"
end

local function onSnap(payload)
	if not valid(payload) then
		return
	end
	local params = payload.params
	local snap = {
		k = payload.k,
		t0 = payload.t0,
		breakCF = payload.breakCF,
		side = (payload.side or 1) >= 0 and 1 or -1,
		params = params,
		kept = payload.kept,
		bodies = {},
		fired = {},
		ended = {},
		loops = {},
		cleanup = {},
	}
	local topples = {}
	for i, b in payload.bodies do
		snap.bodies[i] = {
			name = b.name,
			root = b.root,
			base = b.base,
			torn = b.torn,
			params = { V = params.V, brake = params.brake, recoil = params.recoil, pivot = params.pivot, topple = b.topple },
		}
		topples[i] = b.topple
	end
	snap.stopT = Shared.brakeTime(params.V, params.brake)
	snap.timeline = Shared.eventsTimeline(Config.Events, { V = params.V, brake = params.brake, bodies = topples })
	local finish = params.despawnTime or 30
	for _, e in snap.timeline do
		local ends = (e.t_end or e.t) + (e.loop or 0) + 6
		if ends < math.huge then
			finish = math.max(finish, ends)
		end
	end
	snap.finishT = finish
	table.insert(active, snap)
	if not bound then
		bound = true
		-- after the camera scripts, so the shake sits on top of this frame's camera
		RunService:BindToRenderStep(RENDER_NAME, Enum.RenderPriority.Camera.Value + 1, step)
	end
end

remote.OnClientEvent:Connect(onSnap)
