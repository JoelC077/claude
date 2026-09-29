--[[
TrainSplitShared  (ModuleScript in ReplicatedStorage)

Pure, deterministic maths for the carriage split. The server (TrainSplit) moves each wreck with it
and every client (TrainSplitClient) smooths the same wreck with it, so both agree on where a wreck is
at any moment from nothing but the snap time. No Instances, no side effects, no wait: every number
arrives as an argument (the defaults live in TrainSplitConfig).

Break frame B: origin on the carriage centre line at floor-top height on the break plane;
+X across (right when facing the front), +Y up, +Z toward the rear of the train.
]]

local Shared = {}
Shared.Version = "2.2.0"

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

-- The wreck's speed over the ground: the terrain streams past the static train at V while the wreck slides
-- back at driftSpeed, so it has stopped (moves with the terrain) when the two match.
function Shared.terrainSpeed(t, V, a, recoil)
	return math.abs(V - Shared.driftSpeed(t, V, a, recoil))
end

-- Highest honest speed of a body's root (studs/s): 1.5x the terrain speed, the blast's shove, and the fastest
-- roll or bounce at the body's far edge (farRadius studs from the pivot line), plus the lift/sink/push rates
-- and a little slack. side picks the rest pose (+1 falls to +X).
function Shared.velocityCap(V, params, farRadius, side)
	local omega, lin = 0, 0
	local tp = params.topple
	if tp then
		local rest = Shared.restPose(params.rest, side) or {}
		local rollTime = math.max(tp.roll_time or 1, 1e-3)
		-- every ease here peaks at or below twice its average rate
		omega = 2 * math.rad(math.abs(rest.roll or tp.roll or 0)) / rollTime
		lin = 2 * (math.abs(tp.sink or 0) + math.abs(rest.lift or 0) + math.abs(tp.extra_back or 0)) / rollTime
		local bt = tp.bounce_time or 0
		if bt > 0 then
			omega = math.max(omega, math.pi * math.rad(math.abs(tp.bounce_back or 0)) / bt)
		end
	end
	local r = params.recoil
	local shove = (r and (r.time or 0) > 0) and 2 * math.abs(r.dist or 0) / r.time or 0
	return 1.5 * math.abs(V) + shove + omega * (farRadius or 0) + lin + 5
end

-- A velocity that is finite and no faster than cap (NaN or inf becomes zero).
function Shared.clampVelocity(v, cap)
	local m = v.Magnitude
	if m ~= m or m == math.huge then
		return Vector3.zero
	end
	if m > cap then
		return v * (cap / m)
	end
	return v
end

-- The rest pose for the falling side: rest = Config.ToppleRest ({["+X"] = {roll, lift}, ["-X"] = ...}) or a
-- pose already picked. The bogies are asymmetric, so each side lands at its own angle and height.
function Shared.restPose(rest, side)
	if not rest or rest.roll then
		return rest
	end
	return rest[(side or 1) >= 0 and "+X" or "-X"]
end

--[[
Topple of one lost body at time t -> roll, yaw, sink, lift, back.
  body  one Config.Topple entry: delay, roll_time, ease, bounce_back, bounce_time, yaw, sink, extra_back
  rest  its rest pose for the falling side: {roll (deg), lift (studs along world up)}
It waits `delay`, then over `roll_time` rolls onto its side while yaw (twist, deg), sink (dig-in), lift and
back (extra push along the rear axis) all ease in with it; it rocks back by bounce_back degrees and settles
over `bounce_time`, then lies still.
]]
function Shared.topple(t, body, rest)
	if not body then
		return 0, 0, 0, 0, 0
	end
	local tt = t - (body.delay or 0)
	if tt <= 0 then
		return 0, 0, 0, 0, 0
	end
	local roll = rest and rest.roll or body.roll or 0
	local lift = rest and rest.lift or 0
	local yaw, sink, back = body.yaw or 0, body.sink or 0, body.extra_back or 0
	local rollTime = math.max(body.roll_time or 1, 1e-3)
	if tt < rollTime then
		local e = Shared.ease(body.ease or "QuadIn", tt / rollTime)
		return roll * e, yaw * e, sink * e, lift * e, back * e
	end
	local bt = body.bounce_time or 0
	if bt > 0 and (body.bounce_back or 0) ~= 0 then
		local v = (tt - rollTime) / bt
		if v < 1 then
			return roll - body.bounce_back * math.sin(math.pi * v), yaw, sink, lift, back
		end
	end
	return roll, yaw, sink, lift, back
end

--[[
World CFrame of a lost body's root, t s after the snap.
  baseRootCF  root CFrame at the snap (intact position)
  breakCF     break frame B of the carriage that snapped
  pivotSide   +1 falls to the right (+X of B), -1 to the left
  params      { V, brake, recoil = {dist, time}, pivot = {X_abs, Y}, topple = one Config.Topple entry,
                rest = Config.ToppleRest (per side) }
The body rolls about the rail-level line on the falling side to that side's rest angle, twists about its
own vertical axis (mirrored with the side), slides back by drift(t) plus its extra push, and rises by
lift minus sink along world up.
]]
function Shared.bodyCFrame(baseRootCF, breakCF, pivotSide, t, params)
	if t <= 0 then
		return baseRootCF
	end
	local s = (pivotSide or 1) >= 0 and 1 or -1
	local z = Shared.drift(t, params.V, params.brake, params.recoil)
	local roll, yaw, sink, lift, back = Shared.topple(t, params.topple, Shared.restPose(params.rest, s))
	local rel = breakCF:ToObjectSpace(baseRootCF)
	local pivot = Vector3.new(s * params.pivot.X_abs, params.pivot.Y, 0)
	local rolled = CFrame.new(pivot) * CFrame.Angles(0, 0, -s * math.rad(roll)) * CFrame.new(-pivot) * rel
	local c = rolled.Position
	local twist = CFrame.new(c.X, 0, c.Z) * CFrame.Angles(0, s * math.rad(yaw), 0) * CFrame.new(-c.X, 0, -c.Z)
	return CFrame.new(0, lift - sink, 0) * (breakCF * (CFrame.new(0, 0, z + back) * twist * rolled))
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

-- (a * b) mod 2^32 in 16-bit halves, exact in doubles.
local function mul32(a, b)
	local ah, al = bit32.rshift(a, 16), bit32.band(a, 0xFFFF)
	local bh, bl = bit32.rshift(b, 16), bit32.band(b, 0xFFFF)
	return (al * bl + bit32.lshift((ah * bl + al * bh) % 65536, 16)) % 4294967296
end

-- Tiny xorshift32 so the server and every client roll the same numbers from one seed. The seed is hashed
-- first (murmur3 finaliser): raw xorshift gives nearly the same first number for every small seed.
function Shared.rng(seed)
	local s = math.floor(math.abs(seed or 1)) % 4294967296
	s = bit32.bxor(s, bit32.rshift(s, 16))
	s = mul32(s, 0x85EBCA6B)
	s = bit32.bxor(s, bit32.rshift(s, 13))
	s = mul32(s, 0xC2B2AE35)
	s = bit32.bxor(s, bit32.rshift(s, 16))
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
