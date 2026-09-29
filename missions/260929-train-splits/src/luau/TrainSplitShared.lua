--[[
TrainSplitShared  (ModuleScript in ReplicatedStorage)  v2.0.0

Pure, deterministic maths for the carriage split. The server (TrainSplit) moves each wreck with it
and every client (TrainSplitClient) smooths the same wreck with it, so both agree on where a wreck is
at any moment from nothing but the snap time. No Instances, no side effects, no wait: every number
arrives as an argument (the defaults live in TrainSplitConfig).

Break frame B: origin on the carriage centre line at floor-top height on the break plane;
+X across (right when facing the front), +Y up, +Z toward the rear of the train.
]]

local Shared = {}
Shared.Version = "2.0.0"

local EASE = {
	Linear = function(u)
		return u
	end,
	QuadIn = function(u) -- starts slow, like something tipping under gravity
		return u * u
	end,
	QuadOut = function(u)
		return 1 - (1 - u) * (1 - u)
	end,
	SineInOut = function(u)
		return 0.5 - 0.5 * math.cos(math.pi * u)
	end,
}

function Shared.ease(name, u)
	return (EASE[name] or EASE.Linear)(math.clamp(u, 0, 1))
end

-- The blast shoves the wreck back by recoil.dist over recoil.time (fast, easing out); the shove is kept.
function Shared.recoil(t, recoil)
	if not recoil or t <= 0 or (recoil.dist or 0) == 0 then
		return 0
	end
	if (recoil.time or 0) <= 0 then
		return recoil.dist
	end
	return recoil.dist * Shared.ease("QuadOut", t / recoil.time)
end

-- Seconds until the lost part has shed all of the train's speed and moves with the terrain.
function Shared.brakeTime(V, a)
	if a <= 0 then
		return math.huge
	end
	return V / a
end

-- How far (studs, toward the rear) the lost part has slid relative to the static train, t s after the snap.
-- It keeps the train's world speed V and brakes at a, so relative to the train it accelerates at a until
-- t = V/a; after that it is static relative to the terrain and falls behind at V.
function Shared.drift(t, V, a, recoil)
	if t <= 0 then
		return 0
	end
	local r = Shared.recoil(t, recoil)
	local T = Shared.brakeTime(V, a)
	if t <= T then
		return r + 0.5 * a * t * t
	end
	return r + 0.5 * a * T * T + V * (t - T)
end

-- d(drift)/dt: the wreck's speed toward the rear relative to the train.
function Shared.driftSpeed(t, V, a, recoil)
	if t <= 0 then
		return 0
	end
	local rv = 0
	if recoil and (recoil.dist or 0) ~= 0 and (recoil.time or 0) > 0 and t < recoil.time then
		rv = 2 * recoil.dist * (1 - t / recoil.time) / recoil.time
	end
	if t <= Shared.brakeTime(V, a) then
		return rv + a * t
	end
	return rv + V
end

-- Topple of one lost body at time t: roll (deg, onto its side), yaw (deg, twist), sink (studs into the ground).
-- body = one TrainSplitConfig.Topple entry. It waits `delay`, rolls over in `roll_time`, bounces off the
-- ground (bounce = {lowest, rest}) in `bounce_time`, then lies still.
function Shared.topple(t, body)
	if not body then
		return 0, 0, 0
	end
	local tt = t - (body.delay or 0)
	if tt <= 0 then
		return 0, 0, 0
	end
	local rollTime = math.max(body.roll_time or 1, 1e-3)
	local roll, yaw, sink = body.roll or 0, body.yaw or 0, body.sink or 0
	if tt < rollTime then
		local e = Shared.ease(body.ease or "QuadIn", tt / rollTime)
		return roll * e, yaw * e, sink * e
	end
	local bounce, bounceTime = body.bounce, body.bounce_time or 0
	if bounce and bounceTime > 0 then
		local v = (tt - rollTime) / bounceTime
		if v < 1 then
			-- from the impact angle to the rest angle, dipping back up to bounce[1] half way
			return roll + (bounce[2] - roll) * v + (bounce[1] - bounce[2]) * math.sin(math.pi * v), yaw, sink
		end
		return bounce[2], yaw, sink
	end
	return roll, yaw, sink
end

--[[
World CFrame of a lost body's root, t s after the snap.
  baseRootCF  root CFrame at the snap (intact position)
  breakCF     break frame B of the carriage that snapped
  pivotSide   +1 falls to the right (+X of B), -1 to the left
  params      { V, brake, recoil = {dist, time}, pivot = {X_abs, Y}, topple = one Config.Topple entry }
The body rolls about the rail-level line on the falling side, twists about its own vertical axis
(mirrored with the side), sinks a little and slides back by drift(t).
]]
function Shared.bodyCFrame(baseRootCF, breakCF, pivotSide, t, params)
	if t <= 0 then
		return baseRootCF
	end
	local s = (pivotSide or 1) >= 0 and 1 or -1
	local z = Shared.drift(t, params.V, params.brake, params.recoil)
	local roll, yaw, sink = Shared.topple(t, params.topple)
	local rel = breakCF:ToObjectSpace(baseRootCF)
	local pivot = Vector3.new(s * params.pivot.X_abs, params.pivot.Y, 0)
	local rolled = CFrame.new(pivot) * CFrame.Angles(0, 0, -s * math.rad(roll)) * CFrame.new(-pivot) * rel
	local c = rolled.Position
	local twist = CFrame.new(c.X, 0, c.Z) * CFrame.Angles(0, s * math.rad(yaw), 0) * CFrame.new(-c.X, 0, -c.Z)
	return breakCF * (CFrame.new(0, -sink, z) * twist * rolled)
end

-- Root velocity (studs/s, world) by central difference; feeds AssemblyLinearVelocity so riders are carried.
function Shared.bodyVelocity(baseRootCF, breakCF, pivotSide, t, params, h)
	h = h or 1 / 60
	local a = Shared.bodyCFrame(baseRootCF, breakCF, pivotSide, t - h, params).Position
	local b = Shared.bodyCFrame(baseRootCF, breakCF, pivotSide, t + h, params).Position
	return (b - a) / (2 * h)
end

function Shared.halfId(carriage, half)
	return ("C%d.%s"):format(carriage, half)
end

--[[
Which halves come off when break k snaps, given which breaks have already snapped.
  breakState  { [j] = true } for every break j that has snapped (break j sits in carriage j)
  k           the break snapping now
  carriages   carriage count (default: 2, or more if breakState says so)
Returns bodies, newState. bodies lists the newly lost halves grouped per carriage, front to rear, e.g.
{ {"C1.Rear"}, {"C2.Front", "C2.Rear"} }: each carriage's lost pieces animate as one body.
Halves already gone (behind an earlier snap) are never lost twice; a repeat or impossible snap returns {}.
]]
function Shared.lostHalves(breakState, k, carriages)
	breakState = breakState or {}
	local n = carriages or 2
	for j in breakState do
		if type(j) == "number" and j > n then
			n = j
		end
	end
	if k < 1 or k > n or breakState[k] then
		return {}, breakState
	end
	-- halves in train order: 2c-1 = Carriage c front, 2c = rear; break j sits between 2j-1 and 2j
	local function attached(h)
		for j = 1, n do
			if breakState[j] and h >= 2 * j then
				return false
			end
		end
		return true
	end
	local bodies, byCarriage = {}, {}
	for h = 2 * k, 2 * n do
		if attached(h) then
			local c = math.ceil(h / 2)
			if not byCarriage[c] then
				byCarriage[c] = {}
				table.insert(bodies, byCarriage[c])
			end
			table.insert(byCarriage[c], Shared.halfId(c, h % 2 == 1 and "Front" or "Rear"))
		end
	end
	if #bodies == 0 then
		return {}, breakState -- its carriage already left with an earlier snap
	end
	local newState = table.clone(breakState)
	newState[k] = true
	return bodies, newState
end

--[[
Resolve Config.Events into a time-sorted list for one snap.
  params { V, brake, bodies = { topple entry per lost body } }
"impact" becomes delay + roll_time for each body (one topple_crash each); t_end = "stop" becomes V/brake;
perBody events get one copy per body. Every item keeps its fields and gains `body` where relevant.
]]
function Shared.eventsTimeline(events, params)
	local out = {}
	local stopT = Shared.brakeTime(params.V, params.brake)
	local bodies = params.bodies or {}
	local function add(e, t, body, order)
		local item = table.clone(e)
		item.t = t
		item.body = body
		item.order = order
		if e.t_end == "stop" then
			item.t_end = stopT
		end
		table.insert(out, item)
	end
	for i, e in events do
		if e.t == "impact" then
			for b, topple in bodies do
				add(e, (topple.delay or 0) + (topple.roll_time or 0), b, i * 100 + b)
			end
		elseif e.perBody then
			for b in bodies do
				add(e, e.t, b, i * 100 + b)
			end
		else
			add(e, e.t, nil, i * 100)
		end
	end
	table.sort(out, function(a, b)
		if a.t == b.t then
			return a.order < b.order
		end
		return a.t < b.t
	end)
	return out
end

-- The tear depth d at (X, Y) of the break frame, or nil outside every cell ({X0, X1, Y0, Y1, d, region}).
function Shared.dAt(cells, X, Y)
	for _, c in cells do
		if X >= c[1] and X < c[2] and Y >= c[3] and Y < c[4] then
			return c[5]
		end
	end
	return nil
end

-- Tiny xorshift32 so the server and every client roll the same numbers from one seed.
function Shared.rng(seed)
	local s = math.floor(math.abs(seed or 1)) % 4294967296
	if s == 0 then
		s = 2463534242
	end
	return function()
		s = bit32.bxor(s, bit32.lshift(s, 13))
		s = bit32.bxor(s, bit32.rshift(s, 17))
		s = bit32.bxor(s, bit32.lshift(s, 5))
		return s / 4294967296
	end
end

-- Topple side: "left" = -1, "right" = +1, anything else ("random") comes from the seed.
function Shared.side(name, seed)
	if name == "left" then
		return -1
	elseif name == "right" then
		return 1
	end
	return Shared.rng(seed)() < 0.5 and -1 or 1
end

return Shared
