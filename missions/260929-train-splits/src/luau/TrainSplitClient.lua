--[[
TrainSplitClient  (LocalScript in StarterPlayerScripts)  v2.0.0

Plays a carriage snap for this player: the break_spec timeline of fx, sounds and camera shake,
plus smooth wreck motion. Listens to ReplicatedStorage.RR_TrainSplitFX (server -> client only)
and never sends anything back.

Everything runs off one render-step callback and the shared server clock
(workspace:GetServerTimeNow()), so every player sees the same moment and nothing drifts.
FX go through RR_VFX (ReplicatedStorage.RR_VFX or ReplicatedStorage.RRFX.RR_VFX) when it exists:
VFX.burst for one-shots, VFX.attach + setIntensity + detach for the torn-edge smoke (never setActive:
it works by preset name and would stop the other break's smoke too). Without RR_VFX, or when a
preset fails, a small built-in emitter set from TrainSplitConfig.FallbackFX plays instead.
Sounds are plain Sound instances from TrainSplitConfig.Sounds (empty ids are skipped).
Camera shake is off when the player's reduce-motion attribute is true.
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
		local folder = ReplicatedStorage:FindFirstChild("RRFX")
		local mod = ReplicatedStorage:FindFirstChild("RR_VFX") or (folder and folder:FindFirstChild("RR_VFX"))
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

local function terrain()
	return workspace:FindFirstChildOfClass("Terrain")
end

-- RR_VFX anchor frame: X forward (toward the front), Y up, Z right; yaw -90 turns Z to the left instead.
local function anchorCF(B, p, yaw)
	return B * CFrame.new(p) * CFrame.Angles(0, math.rad(yaw or 90), 0)
end

-- An Attachment at a world CFrame on a static part (Terrain sits at the origin) or a moving one.
local function anchorOn(part, worldCF)
	local a = Instance.new("Attachment")
	a.Name = "RR_SplitFX"
	a.CFrame = part.CFrame:ToObjectSpace(worldCF)
	a.Parent = part
	return a
end

local function worldOf(anchor)
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

---------------------------------------------------------------- fx

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
		blast.Position = worldOf(anchor).Position
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

local function playFx(snap, e, anchor, t)
	local preset = Config.FX[e.fx] or e.fx
	local lib = getVfx()
	local fn = lib and (e.loop and lib.attach or lib.burst)
	if type(fn) == "function" then
		local ok, handle = pcall(fn, anchor, preset)
		if ok then
			if e.loop then
				-- fade the loop out by intensity (never setActive: that is per preset name, for every handle)
				later(snap, t + e.loop, function()
					if lib.setIntensity then
						lib.setIntensity(handle, 0)
					end
				end)
				later(snap, t + e.loop + (e.fade or 0), function()
					if lib.detach then
						lib.detach(handle)
					end
				end)
			end
			return
		end
		warn(("TrainSplitClient: RR_VFX %q failed (%s); using fallback fx"):format(preset, tostring(handle)))
	end
	fallbackFx(snap, e.fx, anchor, t, e.loop)
end

---------------------------------------------------------------- sound

local function newSound(key, def, volume, pitch)
	local sound = Instance.new("Sound")
	sound.Name = "RR_" .. key
	sound.SoundId = def.SoundId
	sound.Volume = volume
	sound.PlaybackSpeed = pitch
	sound.RollOffMode = Enum.RollOffMode.InverseTapered
	sound.RollOffMinDistance = def.RollOffMinDistance or 10
	sound.RollOffMaxDistance = def.RollOffMaxDistance or 240
	local group = def.Group and SoundService:FindFirstChild(def.Group)
	if group and group:IsA("SoundGroup") then
		sound.SoundGroup = group
	end
	return sound
end

local function playSound(snap, e, parent, t)
	local def = Config.Sounds[e.sound]
	if not def or type(def.SoundId) ~= "string" or def.SoundId == "" then
		return nil -- no id pasted yet: stay silent
	end
	local pitch = 1
	if def.Pitch then
		pitch = def.Pitch[1] + math.random() * (def.Pitch[2] - def.Pitch[1])
	end
	if def.BodyPitch and e.body then
		pitch *= def.BodyPitch[e.body] or 1
	end
	if def.Length and def.FitSpeed and e.t_end and e.t_end > e.t and e.t_end < math.huge then
		-- stretch the authored clip over this snap's slide (it was made for Speed 35)
		pitch *= math.clamp(def.Length / (e.t_end - e.t), def.FitSpeed[1], def.FitSpeed[2])
	end
	-- a Sound in an attachment or part is heard from there; in SoundService it is flat (2D)
	local sound = newSound(e.sound, def, def.Volume or 0.5, pitch)
	sound.Parent = (def.Is3D ~= false and parent) or SoundService
	sound:Play()
	local sounds = { sound }
	if def.Volume2D then
		local flat = newSound(e.sound, def, def.Volume2D, pitch)
		flat.Parent = SoundService
		flat:Play()
		table.insert(sounds, flat)
	end
	if not e.t_end then
		later(snap, t + (def.Length or 4) / pitch + 1, function()
			for _, s in sounds do
				s:Destroy()
			end
		end)
	end
	return sound
end

---------------------------------------------------------------- shake

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

---------------------------------------------------------------- the timeline

-- Where an event happens: a list of anchors (Attachments, or a wreck root) and one world position.
local function anchorsFor(snap, e, at)
	local B = snap.breakCF
	if at == "wreck" then
		local body = snap.bodies[e.body or 1]
		local root = body and bodyRoot(body)
		return root and { root } or {}, root and root.CFrame.Position or B.Position
	elseif at == "impact" then
		-- WreckDust: upright on the ground at the landed body's track-side edge, mid-length, X along the track
		local body = snap.bodies[e.body or 1]
		if not body then
			return {}, B.Position
		end
		local z = B:ToObjectSpace(body.base).Position.Z + Shared.drift(e.t, body.params.V, body.params.brake, body.params.recoil)
		local cf = anchorCF(B, Vector3.new(snap.side * body.params.pivot.X_abs, body.params.pivot.Y, z))
		return { anchorOn(terrain(), cf) }, cf.Position
	elseif at == "torn_edge" then
		local holder = (snap.kept and snap.kept.Parent) and snap.kept or terrain()
		local cf = anchorCF(B, Config.Anchors.torn_edge)
		return { anchorOn(holder, cf) }, cf.Position
	end
	local spec = Config.Anchors[at]
	local list = {}
	if typeof(spec) == "Vector3" then
		spec = { spec }
	end
	for _, s in spec or {} do
		local p, yaw = s, nil
		if typeof(s) ~= "Vector3" then
			p, yaw = s.p, s.yaw
		end
		table.insert(list, anchorOn(terrain(), anchorCF(B, p, yaw)))
	end
	return list, (list[1] and worldOf(list[1]).Position) or B.Position
end

local function runEvent(snap, e, t, now)
	local anchors, where = anchorsFor(snap, e, e.at)
	if e.fx then
		for _, a in anchors do
			playFx(snap, e, a, t)
		end
	end
	if e.sound then
		local parents = e.soundAt and anchorsFor(snap, e, e.soundAt) or anchors
		local stagger = Config.Sounds[e.sound] and Config.Sounds[e.sound].Stagger
		for i, parent in parents do
			if i == 1 then
				local sound = playSound(snap, e, parent, t)
				if sound and e.t_end then
					snap.loops[e] = sound
				end
			elseif stagger then
				later(snap, t + (i - 1) * stagger, function()
					playSound(snap, e, parent, t + (i - 1) * stagger)
				end)
			end
		end
	end
	if e.shake then
		addShake(e.shake, where, now)
	end
	-- attachments made for this event go once their fx are done (RR_VFX reads them until then)
	local keep = (e.loop or 0) + (e.fade or 0) + (Config.FxAnchorLife or 12)
	for _, a in anchors do
		if a:IsA("Attachment") then
			later(snap, t + keep, function()
				a:Destroy()
			end)
		end
	end
end

local function step()
	local now = workspace:GetServerTimeNow()
	for i = #active, 1, -1 do
		local snap = active[i]
		local t = now - snap.t0
		for _, e in snap.timeline do
			if not snap.fired[e] and t >= e.t then
				snap.fired[e] = true
				-- a one-shot heard about too late is skipped; loops and slides still start
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
					table.insert(snap.fades, { sound = sound, from = sound.Volume, start = t, dur = 0.15 })
				end
			end
		end
		for j = #snap.fades, 1, -1 do
			local f = snap.fades[j]
			local u = (t - f.start) / f.dur
			if u >= 1 then
				table.remove(snap.fades, j)
				f.sound:Stop()
				f.sound:Destroy()
			else
				f.sound.Volume = f.from * (1 - u)
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
				local ok, err = pcall(job.fn)
				if not ok then
					warn("TrainSplitClient: cleanup", err)
				end
			end
		end
		if t > snap.finishT and #snap.cleanup == 0 and #snap.fades == 0 then
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
		fades = {},
		cleanup = {},
	}
	local topples = {}
	for i, b in payload.bodies do
		snap.bodies[i] = {
			name = b.name,
			root = b.root,
			base = b.base,
			params = { V = params.V, brake = params.brake, recoil = params.recoil, pivot = params.pivot, topple = b.topple },
		}
		topples[i] = b.topple
	end
	snap.stopT = Shared.brakeTime(params.V, params.brake)
	snap.timeline = Shared.eventsTimeline(Config.Events, { V = params.V, brake = params.brake, bodies = topples })
	local finish = params.despawnTime or 30
	for _, e in snap.timeline do
		local ends = (e.t_end or e.t) + (e.loop or 0) + (e.fade or 0) + 1
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
