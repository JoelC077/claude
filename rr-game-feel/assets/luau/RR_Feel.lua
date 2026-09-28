-- RR_Feel (ModuleScript, client only) - rr-game-feel runtime for Risky Rails.
-- Event presets come from RR_FeelPresets (generated from presets/feel.json); math from RR_FeelMath.
-- One render-step loop drives every channel: tweens, punches, pulses, camera shake (trauma), camera kicks,
-- FOV kicks, flashes, gamepad haptics and hit-stop. Motion runs on the feel clock, which pauses during
-- hit-stop; flashes, haptics and cues run on real time. Nothing here touches the server or world parts.
--
-- API (LocalScripts):
--   Feel.play(name, ctx) -> handle        ctx = { targets = { role = GuiObject }, side = -1|1, gain = 1,
--                                                 count = { amount = n, format = fn } }; handle:Stop()
--   Feel.playFor(name, actorUserId, ctx) -> handle|nil   routes by the event's who (actor, crew, all, local)
--   Feel.addTrauma(x) · Feel.setSpeed(speed) · Feel.setPressure(p01) · Feel.hitStop(ms)
--   Feel.leverDrag(u, ctx) -> knob -1..1 (u signed: - left, + right; ctx.fork = junction id re-arms the lever)
--   Feel.leverRelease(ctx) -> "committed"|"snapback" · Feel.leverReset() (same as a new ctx.fork)
--   Feel.animateValue(from, to, spec, onStep) -> handle   (spec = { style, dir, dur }, feel clock)
--   Feel.freezable(emitter) · Feel.reset(obj) · Feel.setSetting(key, value) · Feel.settings · Feel.Cue · Feel.Changed
--   Feel.curveDump(n) -> CSV text of TweenService:GetValue for every style (for feel.py plot --compare)

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local GuiService = game:GetService("GuiService")
local HapticService = game:GetService("HapticService")
local Workspace = game:GetService("Workspace")

local P = require(script.Parent:WaitForChild("RR_FeelPresets"))
local M = require(script.Parent:WaitForChild("RR_FeelMath"))

local Feel = {}
Feel.Presets = P
Feel.Math = M
Feel.Cue = Instance.new("BindableEvent") -- Fire(eventName, { sfx = "...", vfx = "..." })
Feel.Changed = Instance.new("BindableEvent") -- Fire(key, value)

M.engine = function(style, direction, t)
	return TweenService:GetValue(t, Enum.EasingStyle[style], Enum.EasingDirection[direction])
end

local MOTION = { tween = true, punch = true, camkick = true, shake = true, fovkick = true, pulse = true }
local SHAKE, LIMITS, A11Y, LEVER = P.shake, P.limits, P.a11y, P.lever
local REST = { scale = 1, rot = 0, alpha = 1, x = 0, y = 0, x_px = 0, y_px = 0, count = 1 }

-- ---------------------------------------------------------------- settings
local settings = { reduceMotion = false, shake = 1, flashes = true, haptics = true, profile = "default" }
Feel.settings = settings
local rmOverridden = false

local function readReducedMotion()
	local ok, v = pcall(function() return GuiService.ReducedMotionEnabled end)
	if ok and not rmOverridden then settings.reduceMotion = v == true end
end
readReducedMotion()
pcall(function()
	GuiService:GetPropertyChangedSignal("ReducedMotionEnabled"):Connect(function()
		readReducedMotion()
		Feel.Changed:Fire("reduceMotion", settings.reduceMotion)
	end)
end)

function Feel.setSetting(key, value)
	if key == "reduceMotion" then
		rmOverridden = value ~= nil
		if value == nil then readReducedMotion() else settings.reduceMotion = value == true end
	elseif key == "shake" then
		settings.shake = M.clamp(tonumber(value) or 1, 0, 1)
	elseif key == "flashes" or key == "haptics" then
		settings[key] = value == true
	elseif key == "profile" then
		assert(P.profiles[value], "unknown profile " .. tostring(value))
		settings.profile = value
	else
		error("unknown setting " .. tostring(key))
	end
	Feel.Changed:Fire(key, settings[key])
end

-- reduce-motion factor (number) or mode ("fade", "snap", "skip") for a channel
local function rmFactor(ch)
	if not settings.reduceMotion then return 1 end
	if ch.type == "flash" and ch.scope == "element" then return 1 end
	local t = A11Y.reduce_motion
	local key = ch.type
	if ch.type == "tween" then key = "tween_" .. ch.prop end
	local rm = ch.rm
	if rm == nil then rm = t[key] end
	if rm == nil then rm = t[ch.type] end
	if rm == nil or rm == "keep" then return 1 end
	return rm
end

local function gainFor(ch, ctx)
	local g = (ctx and ctx.gain) or 1
	local prof = P.profiles[settings.profile] or {}
	g = g * (prof[ch.type] or 1)
	if ch.type == "shake" or ch.type == "camkick" or ch.type == "fovkick" then g = g * settings.shake end
	return g
end

-- ---------------------------------------------------------------- state
local clock = 0 -- feel clock (s): pauses during hit-stop
local frozenUntil, lastStopEnd, wasFrozen = 0, -1e9, false
local trauma, sustain = 0, { speed = 0, pressure = 0 }
local effects = {} -- running channels
local targets = setmetatable({}, { __mode = "k" }) -- per GuiObject: captured layout values while effects run
local parked = setmetatable({}, { __mode = "k" }) -- targets an event left moved or faded (Feel.reset restores)
local freezables = setmetatable({}, { __mode = "k" })
local frozenTracks, frozenEmitters = {}, {}
local flashTimes = {}
local fovLast, fovApplied = nil, 0 -- FOV we wrote and the kick inside it (applied as a delta, never a stale base)
local camLast, camOffset = nil, CFrame.new()
local overlayLit, motorOn = false, false
local overlay, flashFrame, vignette

-- ---------------------------------------------------------------- targets (GuiObjects)
local function tstate(obj)
	local s = targets[obj] or parked[obj]
	parked[obj] = nil
	if s then
		targets[obj] = s
		return s
	end
	-- layout values captured at first touch; only the properties a channel animates are ever written
	s = { pos = obj.Position, rot = obj.Rotation, visible = obj.Visible, touched = {}, fades = nil }
	targets[obj] = s
	return s
end

local function uiscale(obj, s)
	if not s.uiscale then
		local sc = obj:FindFirstChild("RR_FeelScale") or obj:FindFirstChildOfClass("UIScale")
		if not sc then
			sc = Instance.new("UIScale")
			sc.Name = "RR_FeelScale"
			sc.Parent = obj
		end
		s.uiscale, s.scale = sc, sc.Scale
	end
	return s.uiscale
end

local FADE_PROPS = {
	BackgroundTransparency = true, ImageTransparency = true, TextTransparency = true, TextStrokeTransparency = true,
}

local function fadeBases(obj, s)
	if s.fades then return end
	s.fades = {}
	if obj:IsA("CanvasGroup") then
		s.fades[obj] = { GroupTransparency = obj.GroupTransparency }
		return
	end
	local list = obj:GetDescendants()
	table.insert(list, obj)
	for _, d in ipairs(list) do
		local rec = {}
		for prop in pairs(FADE_PROPS) do
			local ok, v = pcall(function() return d[prop] end)
			if ok and type(v) == "number" then rec[prop] = v end
		end
		if d:IsA("UIStroke") then rec.Transparency = d.Transparency end
		if next(rec) then s.fades[d] = rec end
	end
end

local function applyTarget(obj, s, c)
	local T = s.touched
	if c.x or c.y or c.x_px or c.y_px then
		T.pos = true
		obj.Position = s.pos + UDim2.new(c.x or 0, c.x_px or 0, c.y or 0, c.y_px or 0)
	end
	if c.rot_abs or c.rot then
		T.rot = true
		obj.Rotation = (c.rot_abs or s.rot) + (c.rot or 0)
	end
	if c.scale_abs or c.scale then
		T.scale = true
		uiscale(obj, s).Scale = (c.scale_abs or s.scale) * (1 + (c.scale or 0))
	end
	if c.hidden ~= nil then
		T.visible = true
		obj.Visible = s.visible and not c.hidden
	end
	local a = c.alpha
	if a ~= nil then
		T.alpha = true
		fadeBases(obj, s)
		for d, rec in pairs(s.fades) do
			if d.Parent then
				for prop, base in pairs(rec) do
					d[prop] = 1 - (1 - base) * M.clamp(a, 0, 1)
				end
			end
		end
	end
	if c.count and c.countCtx then
		local amt = c.countCtx.amount or 0
		local fmt = c.countCtx.format or tostring
		obj.Text = fmt(math.floor(amt * c.count + 0.5))
	end
end

local function restoreTarget(obj, s)
	local T = s.touched
	if T.pos then obj.Position = s.pos end
	if T.rot then obj.Rotation = s.rot end
	if T.visible then obj.Visible = s.visible end
	if T.scale and s.uiscale then s.uiscale.Scale = s.scale end
	if T.alpha and s.fades then
		for d, rec in pairs(s.fades) do
			if d.Parent then
				for prop, base in pairs(rec) do d[prop] = base end
			end
		end
	end
	targets[obj] = nil
end

-- ---------------------------------------------------------------- overlay (flashes)
local function ensureOverlay()
	if overlay and overlay.Parent then return end
	local pg = Players.LocalPlayer:WaitForChild("PlayerGui")
	overlay = Instance.new("ScreenGui")
	overlay.Name = "RR_FeelOverlay"
	overlay.IgnoreGuiInset = true
	overlay.ResetOnSpawn = false
	overlay.DisplayOrder = 100
	flashFrame = Instance.new("Frame")
	flashFrame.Name = "Flash"
	flashFrame.Size = UDim2.fromScale(1, 1)
	flashFrame.BorderSizePixel = 0
	flashFrame.BackgroundTransparency = 1
	flashFrame.Active = false
	flashFrame.Parent = overlay
	vignette = {}
	-- four edge strips with gradients: a vignette without an image asset
	local edges = {
		{ UDim2.fromScale(1, 0.35), UDim2.fromScale(0, 0), 90 },
		{ UDim2.fromScale(1, 0.35), UDim2.fromScale(0, 0.65), -90 },
		{ UDim2.fromScale(0.25, 1), UDim2.fromScale(0, 0), 0 },
		{ UDim2.fromScale(0.25, 1), UDim2.fromScale(0.75, 0), 180 },
	}
	for i, e in ipairs(edges) do
		local f = Instance.new("Frame")
		f.Name = "Vignette" .. i
		f.Size, f.Position = e[1], e[2]
		f.BorderSizePixel = 0
		f.BackgroundTransparency = 1
		local g = Instance.new("UIGradient")
		g.Rotation = e[3]
		g.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) })
		g.Parent = f
		f.Parent = overlay
		vignette[i] = f
	end
	overlay.Parent = pg
end

local function flashAllowed(ch)
	if ch.scope == "element" then return true end
	if not settings.flashes then return false end
	local now = os.clock()
	local recent = {}
	for _, t in ipairs(flashTimes) do
		if now - t < 1 then table.insert(recent, t) end
	end
	flashTimes = recent
	if #recent >= A11Y.flash.per_second_max then return false end
	table.insert(flashTimes, now)
	return true
end

local function isRed(c)
	local h, s, v = c:ToHSV()
	return s > 0.45 and v > 0.2 and (h < 0.04 or h > 0.96)
end

-- ---------------------------------------------------------------- haptics
local hapticEffectOK = pcall(function()
	local e = Instance.new("HapticEffect")
	e:Destroy()
end)

local function playHaptic(ch, gain, eff)
	if not settings.haptics then return false end
	if hapticEffectOK then
		local ok = pcall(function()
			local e = Instance.new("HapticEffect")
			if ch.effect ~= "Custom" and math.abs(gain - 1) < 1e-3 then
				e.Type = Enum.HapticEffectType[ch.effect]
			else
				e.Type = Enum.HapticEffectType.Custom
				local keys = {}
				local t0 = ch.keys[1][1]
				for _, k in ipairs(ch.keys) do
					table.insert(keys, FloatCurveKey.new(k[1] - t0, M.clamp(k[2] * gain, 0, 1), Enum.KeyInterpolationMode.Linear))
				end
				e:SetWaveformKeys(keys)
			end
			e.Parent = Workspace
			e:Play()
			e.Ended:Connect(function() e:Destroy() end)
			task.delay(3, function() if e.Parent then e:Destroy() end end)
		end)
		if ok then return false end
	end
	-- fallback: step the waveform on a gamepad's large motor (HapticService is deprecated but still works)
	local ok, supported = pcall(function()
		return HapticService:IsVibrationSupported(Enum.UserInputType.Gamepad1)
			and HapticService:IsMotorSupported(Enum.UserInputType.Gamepad1, Enum.VibrationMotor.Large)
	end)
	return ok and supported -- true: the step loop drives the motor for this effect
end

local function setMotor(v)
	pcall(function() HapticService:SetMotor(Enum.UserInputType.Gamepad1, Enum.VibrationMotor.Large, v) end)
end

-- ---------------------------------------------------------------- hit-stop
local function freeze(on)
	if on then
		local char = Players.LocalPlayer.Character
		local hum = char and char:FindFirstChildOfClass("Humanoid")
		local animator = hum and hum:FindFirstChildOfClass("Animator")
		if animator then
			for _, tr in ipairs(animator:GetPlayingAnimationTracks()) do
				frozenTracks[tr] = tr.Speed
				tr:AdjustSpeed(0)
			end
		end
		for e in pairs(freezables) do
			if e.Parent then
				frozenEmitters[e] = e.TimeScale
				e.TimeScale = 0
			end
		end
	else
		for tr, speed in pairs(frozenTracks) do
			pcall(function() tr:AdjustSpeed(speed) end)
		end
		for e, ts in pairs(frozenEmitters) do
			if e.Parent then e.TimeScale = ts end
		end
		frozenTracks, frozenEmitters = {}, {}
	end
end

function Feel.hitStop(ms)
	local now = os.clock()
	if now < lastStopEnd + LIMITS.hitstop_cooldown_s then return false end
	ms = math.min(ms, LIMITS.hitstop_ms_max)
	frozenUntil = math.max(frozenUntil, now + ms / 1000)
	lastStopEnd = frozenUntil
	return true
end

function Feel.freezable(emitter)
	freezables[emitter] = true
end

-- ---------------------------------------------------------------- trauma and sustain
function Feel.addTrauma(x)
	local f = rmFactor({ type = "shake" })
	if type(f) ~= "number" then f = 1 end
	trauma = math.min(SHAKE.max_trauma, trauma + x * f * settings.shake)
end

function Feel.setSpeed(speed)
	local s = P.sustain.speed
	sustain.speed = s.gain * M.clamp(speed / s.ref, 0, 1)
end

function Feel.setPressure(p)
	local s = P.sustain.pressure
	sustain.pressure = s.gain * M.clamp((p - s.threshold) / (1 - s.threshold), 0, 1)
end

-- ---------------------------------------------------------------- play
local function expand(name, delay, out, depth)
	local ev = P.events[name]
	assert(ev, "RR_Feel: unknown event " .. tostring(name))
	assert(depth < 5, "RR_Feel: include depth")
	for _, inc in ipairs(ev.include or {}) do
		expand(inc.event, delay + (inc.delay or 0), out, depth + 1)
	end
	for _, ch in ipairs(ev.channels or {}) do
		table.insert(out, { ch = ch, delay = delay + (ch.delay or 0) })
	end
	return out
end

local warned = {}
local function targetFor(ch, ctx, evName)
	if not ch.target then return nil end
	local t = ctx.targets and ctx.targets[ch.target]
	if not t and not warned[evName .. ch.target] then
		warned[evName .. ch.target] = true
		if RunService:IsStudio() then warn("RR_Feel: " .. evName .. " has no target '" .. ch.target .. "' (channel skipped)") end
	end
	return t
end

function Feel.play(name, ctx)
	ctx = ctx or {}
	if not P.events[name] then error("RR_Feel: unknown event " .. tostring(name)) end
	local handle = { effects = {} }
	local now = os.clock()
	for _, item in ipairs(expand(name, 0, {}, 0)) do
		local ch, delay = item.ch, item.delay
		local f = rmFactor(ch)
		local g = gainFor(ch, ctx)
		local skip = f == "skip"
		if ch.type == "hitstop" then
			skip = true
			if delay <= 0 then Feel.hitStop(ch.ms) else task.delay(delay, function() Feel.hitStop(ch.ms) end) end
		elseif ch.type == "cue" then
			skip = true
			if delay <= 0 then Feel.Cue:Fire(name, ch) else task.delay(delay, function() Feel.Cue:Fire(name, ch) end) end
		elseif ch.type == "shake" then
			skip = true
			if type(f) == "number" and f > 0 then
				local amount = ch.trauma * g * f
				if delay <= 0 then trauma = math.min(SHAKE.max_trauma, trauma + amount)
				else
					table.insert(effects, { kind = "trauma", t0 = clock + delay, amount = amount })
				end
			end
		end
		local obj = targetFor(ch, ctx, name)
		if not skip and ch.target and not obj and not (ch.type == "flash" and ch.scope ~= "element") then skip = true end
		if not skip then
			local e = { ch = ch, f = f, g = g, obj = obj, ctx = ctx, name = name, side = ctx.side or 1,
				real = not MOTION[ch.type], t0 = MOTION[ch.type] and (clock + delay) or (now + delay) }
			if ch.type == "flash" then
				e.color = ch.color
				local cap = A11Y.flash.screen_peak_max
				if isRed(ch.color) then cap = A11Y.flash.red_peak_max end
				e.peak = ch.scope == "element" and ch.peak or math.min(ch.peak, cap)
				e.pendingCheck = true
			elseif ch.type == "haptic" then
				e.pendingHaptic = true
				e.keyOffset = ch.keys[1][1] / 1000 -- the waveform starts at its first key
				e.t0 = e.t0 + e.keyOffset
			elseif ch.type == "tween" and obj then
				tstate(obj)
				if ch.before == "hidden" then e.hidden = true end
				if f == "fade" then e.fade = math.abs(ch.to - (REST[ch.prop] or 0)) < 1e-9 and "in" or "out" end
			elseif obj then
				tstate(obj)
			end
			table.insert(effects, e)
			table.insert(handle.effects, e)
		end
	end
	function handle:Stop()
		for _, e in ipairs(self.effects) do e.dead = true end
	end
	return handle
end

-- server events carry the actor's UserId; each client calls this and the event's who decides where it plays:
-- actor = only the actor's client, crew = everyone else's, all/local = every client that calls it
function Feel.playFor(name, actorUserId, ctx)
	local ev = P.events[name]
	if not ev then error("RR_Feel: unknown event " .. tostring(name)) end
	local me = Players.LocalPlayer and Players.LocalPlayer.UserId
	local isActor = actorUserId ~= nil and me == actorUserId
	if ev.who == "actor" and not isActor then return nil end
	if ev.who == "crew" and isActor then return nil end
	return Feel.play(name, ctx)
end

-- a number animated on the feel clock with engine easing (lever knob snaps, world lever handles, counters)
function Feel.animateValue(from, to, spec, onStep)
	local e = { kind = "value", from = from, to = to, spec = spec, onStep = onStep, t0 = clock }
	table.insert(effects, e)
	return { Stop = function() e.dead = true end }
end

-- ---------------------------------------------------------------- lever
-- u = finger travel along the console, -1..1 (sign = side). The knob lags the finger (heavy); the detent tick
-- fires at lever.notch (before the commit, so it is felt on its own), the commit once at lever.detent. The lever
-- stays committed until a new junction: pass ctx.fork = the junction's id (or call Feel.leverReset()).
local lever = { committed = false, notched = false, side = 1, fork = nil }
function Feel.leverReset()
	lever.committed, lever.notched = false, false
end

local function sideCtx(ctx, s)
	local c = {}
	for k, v in pairs(ctx) do c[k] = v end
	if c.side == nil then c.side = s end
	return c
end

function Feel.leverDrag(u, ctx)
	ctx = ctx or {}
	if ctx.fork ~= nil and ctx.fork ~= lever.fork then
		lever.fork = ctx.fork
		Feel.leverReset()
	end
	if lever.committed then return lever.side end
	local s = 1
	if u < 0 then s = -1 end
	local a = math.abs(u)
	local c = sideCtx(ctx, s)
	local notch = LEVER.notch or LEVER.detent
	if a >= notch and not lever.notched then
		lever.notched = true
		Feel.play(LEVER.detent_event, c)
	elseif a < notch - (LEVER.notch_rearm or 0.05) then
		lever.notched = false
	end
	if a >= LEVER.detent then
		lever.committed, lever.side = true, c.side
		Feel.play(LEVER.commit_event, c)
	end
	return M.leverDisplay(u, LEVER.detent, LEVER.resist)
end

function Feel.leverRelease(ctx)
	if lever.committed then return "committed" end
	lever.notched = false
	Feel.play(LEVER.snapback_event, ctx)
	return "snapback"
end

-- ---------------------------------------------------------------- per-frame
-- reduce motion "fade": no travel, hold the end that is at rest (to when entering, from when leaving)
local function fadeHold(ch)
	local rest = REST[ch.prop] or 0
	if math.abs(ch.to - rest) < 1e-9 then return ch.to end
	return ch.from
end

local function channelValue(e, lt)
	local ch, f = e.ch, e.f
	local num = type(f) == "number" and f or 1
	if ch.type == "tween" then
		if f == "snap" then return ch.to end
		if f == "fade" then return fadeHold(ch) end
		local a = M.ease(ch.style or "Quad", ch.dir or "Out", ch.dur > 0 and lt / ch.dur or 1)
		local v = ch.from + (ch.to - ch.from) * a
		if num ~= 1 then v = ch.to + (v - ch.to) * num end
		return v
	elseif ch.type == "punch" then -- amp is the delivered peak (M.peakGain normalises the spring)
		local z, shape = ch.damping or 0.3, ch.shape or "sin"
		return M.spring(lt, ch.amp * e.g * num / M.peakGain(ch.freq_hz, z, shape, ch.dur), ch.freq_hz, z, shape, ch.dur)
	elseif ch.type == "camkick" then
		local z, shape = ch.damping or 0.4, ch.shape or "sin"
		return M.spring(lt, e.g * num / M.peakGain(ch.freq_hz, z, shape, ch.dur), ch.freq_hz, z, shape, ch.dur)
	elseif ch.type == "fovkick" then
		return ch.delta_deg * e.g * num * M.envelope(lt, ch["in"], ch.hold or 0, ch.out, ch.style_in or "Quad", ch.style_out or "Sine")
	elseif ch.type == "flash" then
		return e.peak * e.g * num * M.envelope(lt, ch["in"], ch.hold or 0, ch.out, "Linear", "Quad")
	elseif ch.type == "pulse" then
		return M.pulse(lt, ch.min, ch.max, ch.period)
	elseif ch.type == "haptic" then
		return math.min(1, M.keysAt(ch.keys, lt + (e.keyOffset or 0)) * e.g * num)
	end
	return 0
end

local function channelLength(ch)
	if ch.type == "tween" or ch.type == "punch" or ch.type == "camkick" then return ch.dur or 0 end
	if ch.type == "flash" or ch.type == "fovkick" then return ch["in"] + (ch.hold or 0) + ch.out end
	if ch.type == "haptic" then return (ch.keys[#ch.keys][1] - ch.keys[1][1]) / 1000 end
	if ch.type == "pulse" then return ch.dur or math.huge end
	return 0
end

local function step(dt)
	local now = os.clock()
	local frozen = now < frozenUntil
	if frozen ~= wasFrozen then
		freeze(frozen)
		wasFrozen = frozen
	end
	if not frozen then clock = clock + dt end

	local comp = {} -- per GuiObject composite this frame
	local pitch, yaw, roll, fovDelta, motor = 0, 0, 0, 0, 0
	local screenA, screenC, vigA, vigC = 0, nil, 0, nil
	local keep = {}
	for _, e in ipairs(effects) do
		local alive = not e.dead
		if alive and e.kind == "trauma" then
			if clock >= e.t0 then
				trauma = math.min(SHAKE.max_trauma, trauma + e.amount)
				alive = false
			end
		elseif alive and e.kind == "value" then
			local lt = clock - e.t0
			local a = M.ease(e.spec.style, e.spec.dir, e.spec.dur > 0 and lt / e.spec.dur or 1)
			e.onStep(e.from + (e.to - e.from) * a)
			if lt >= e.spec.dur then alive = false end
		elseif alive then
			local ch = e.ch
			local lt = (e.real and now or clock) - e.t0
			if e.obj and not e.obj.Parent then alive = false end
			if alive and lt >= 0 then
				if e.pendingCheck then
					e.pendingCheck = false
					if not flashAllowed(ch) then alive = false end
				end
				if alive and e.pendingHaptic then
					e.pendingHaptic = false
					e.motorDriven = playHaptic(ch, e.g * (type(e.f) == "number" and e.f or 1), e)
					if not e.motorDriven then alive = false end
				end
			end
			if alive then
				local len = channelLength(ch)
				local ctype = tostring(ch.type)
				if lt > len + 0.05 and ctype ~= "tween" then
					alive = false
				elseif ctype == "camkick" then
					if lt >= 0 then
						local u = channelValue(e, lt)
						local s = ch.side_sign and e.side or 1
						pitch = pitch + ch.angles_deg[1] * u
						yaw = yaw + ch.angles_deg[2] * u * s
						roll = roll + ch.angles_deg[3] * u * s
					end
				elseif ctype == "fovkick" then
					if lt >= 0 then fovDelta = fovDelta + channelValue(e, lt) end
				elseif ctype == "haptic" then
					if lt >= 0 then motor = math.max(motor, channelValue(e, lt)) end
				elseif ctype == "flash" then
					local a = lt >= 0 and channelValue(e, lt) or 0
					if ch.scope == "screen" then
						if a > screenA then screenA, screenC = a, e.color end
					elseif ch.scope == "vignette" then
						if a > vigA then vigA, vigC = a, e.color end
					elseif e.obj then
						if not e.flashFrame then
							local fr = Instance.new("Frame")
							fr.Name = "RR_FeelFlash"
							fr.Size = UDim2.fromScale(1, 1)
							fr.BorderSizePixel = 0
							fr.BackgroundColor3 = e.color
							fr.ZIndex = e.obj.ZIndex + 1
							local corner = e.obj:FindFirstChildOfClass("UICorner")
							if corner then corner:Clone().Parent = fr end
							fr.Parent = e.obj
							e.flashFrame = fr
						end
						e.flashFrame.BackgroundTransparency = 1 - M.clamp(a, 0, 1)
					end
				elseif e.obj then
					local c = comp[e.obj]
					if not c then
						c = {}
						comp[e.obj] = c
					end
					if ch.type == "tween" then
						local done = lt >= ch.dur
						local v
						if e.hidden then
							if lt < 0 then c.hidden = true elseif c.hidden == nil then c.hidden = false end
						end
						if lt < 0 then
							if ch.before == "rest" then v = REST[ch.prop] or ch.to else v = ch.from end
							if e.f == "snap" then v = ch.to elseif e.f == "fade" then v = fadeHold(ch) end
						else
							v = channelValue(e, math.min(lt, ch.dur))
						end
						local p = ch.prop
						if p == "scale" then c.scale_abs = v
						elseif p == "rot" then c.rot_abs = v
						elseif p == "alpha" then c.alpha = (c.alpha or 1) * v
						elseif p == "count" then c.count, c.countCtx = v, e.ctx.count
						else c[p] = (c[p] or 0) + v end
						if e.fade then
							local k = lt < 0 and 0 or M.ease("Quad", "Out", math.min(1, lt / ch.dur))
							c.alpha = (c.alpha or 1) * (e.fade == "in" and k or 1 - k)
						end
						if done then
							-- a finished tween holds its end value until the target's last effect ends
							e.held = true
						end
					elseif ch.type == "punch" then
						local v = lt >= 0 and channelValue(e, lt) or 0
						local p = ch.prop
						if p == "scale" then c.scale = (c.scale or 0) + v
						elseif p == "rot" then c.rot = (c.rot or 0) + v
						else c[p] = (c[p] or 0) + v end
					elseif ch.type == "pulse" then
						if lt >= 0 then
							local v = channelValue(e, lt)
							if ch.prop == "alpha" then c.alpha = (c.alpha or 1) * v else c.scale_abs = v end
						end
					end
				end
			end
			if not alive and e.flashFrame then e.flashFrame:Destroy() end
		end
		if alive then table.insert(keep, e) end
	end
	-- drop held tweens once nothing else runs on their target
	local busy = {}
	for _, e in ipairs(keep) do
		if e.obj and not e.held then busy[e.obj] = true end
	end
	effects = {}
	for _, e in ipairs(keep) do
		if not (e.held and e.obj and not busy[e.obj]) then table.insert(effects, e) end
	end
	for obj, s in pairs(targets) do
		if not obj.Parent then
			targets[obj] = nil
		elseif comp[obj] and busy[obj] then
			applyTarget(obj, s, comp[obj])
		elseif comp[obj] then
			applyTarget(obj, s, comp[obj]) -- final frame at the end values
			local c = comp[obj]
			if (c.x or 0) == 0 and (c.y or 0) == 0 and (c.alpha or 1) >= 0.999 then
				restoreTarget(obj, s)
			else
				-- the event moved or faded it away on purpose (a console that left): leave it, keep the layout values
				targets[obj] = nil
				parked[obj] = s
			end
		else
			restoreTarget(obj, s)
		end
	end

	-- camera: trauma decays on the feel clock; the floor comes from Speed and pressure
	if not frozen then trauma = math.max(0, trauma - SHAKE.decay_per_s * dt) end
	local rmShake = rmFactor({ type = "shake" })
	if type(rmShake) ~= "number" then rmShake = 1 end
	local floor = math.min(SHAKE.sustain_cap, sustain.speed + sustain.pressure) * settings.shake * rmShake
	local s = math.max(trauma, floor) ^ SHAKE.power
	local q = clock * SHAKE.freq_hz
	local cam = Workspace.CurrentCamera
	if cam then
		-- undo our last offset if nobody reset the camera since (a scripted camera), so shake never accumulates
		if camLast and cam.CFrame == camLast then cam.CFrame = camLast * camOffset:Inverse() end
		local A, O, N = SHAKE.max_angle_deg, SHAKE.max_offset_studs, M.noise1
		local p = pitch + A[1] * s * N(M.SEEDS.pitch, q)
		local yw = yaw + A[2] * s * N(M.SEEDS.yaw, q)
		local r = roll + A[3] * s * N(M.SEEDS.roll, q)
		local ox, oy = O[1] * s * N(M.SEEDS.x, q), O[2] * s * N(M.SEEDS.y, q)
		if math.abs(p) + math.abs(yw) + math.abs(r) + math.abs(ox) + math.abs(oy) > 1e-5 then
			camOffset = CFrame.new(ox, oy, 0) * CFrame.Angles(math.rad(p), math.rad(yw), math.rad(r))
			cam.CFrame = cam.CFrame * camOffset
			camLast = cam.CFrame
		else
			camLast, camOffset = nil, CFrame.new()
		end
		-- FOV kick as a delta: if another script set the FOV since our last write, that value is the new base
		if math.abs(fovDelta) <= 1e-4 then fovDelta = 0 end
		if fovDelta ~= 0 or fovApplied ~= 0 then
			local base = cam.FieldOfView
			if fovLast ~= nil and base == fovLast then base = base - fovApplied end
			cam.FieldOfView = base + fovDelta
			fovApplied = fovDelta
			fovLast = cam.FieldOfView
			if fovDelta == 0 then fovLast = nil end
		end
	end

	-- flashes: one more write after the last lit frame clears screen and vignette even if a flash ended
	-- between frames (a hitch or an app switch), so no edge colour is ever left on screen
	if screenA > 0 or vigA > 0 or overlayLit then
		ensureOverlay()
		flashFrame.BackgroundColor3 = screenC or flashFrame.BackgroundColor3
		flashFrame.BackgroundTransparency = 1 - M.clamp(screenA, 0, 1)
		for _, f in ipairs(vignette) do
			f.BackgroundColor3 = vigC or f.BackgroundColor3
			f.BackgroundTransparency = 1 - M.clamp(vigA, 0, 1)
		end
		overlayLit = screenA > 0 or vigA > 0
	end
	if motor > 0 or motorOn then
		setMotor(settings.haptics and motor or 0)
		motorOn = motor > 0
	end
end

RunService:BindToRenderStep("RR_Feel", Enum.RenderPriority.Camera.Value + 1, step)

-- ---------------------------------------------------------------- tools
-- put a target back to the layout values captured before the first effect (e.g. before re-showing a console)
function Feel.reset(obj)
	local s = targets[obj] or parked[obj]
	if s then
		parked[obj] = nil
		targets[obj] = s
		restoreTarget(obj, s)
	end
end

function Feel.stats()
	local now, recent = os.clock(), 0
	for _, t in ipairs(flashTimes) do
		if now - t < 1 then recent = recent + 1 end
	end
	return { effects = #effects, trauma = trauma, clock = clock, frozen = now < frozenUntil,
		reduceMotion = settings.reduceMotion, flashesLastSecond = recent }
end

function Feel.curveDump(n)
	n = n or 20
	local lines = {}
	for _, st in ipairs(M.STYLES) do
		for _, dr in ipairs(M.DIRECTIONS) do
			for i = 0, n do
				local t = i / n
				table.insert(lines, string.format("%s,%s,%.4f,%.6f", st, dr, t, M.engine(st, dr, t)))
			end
		end
	end
	return table.concat(lines, "\n")
end

return Feel
