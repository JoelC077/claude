--[[
TrainSplit  (ModuleScript in ServerScriptService)

Tears a carriage in half at runtime. Needs RR_TrainSplit_Setup to have run on the train:
Train/Carriage1..2/{FrontHalf, RearHalf} and Train/RR_Breaks/Break1..2.

	local TrainSplit = require(game:GetService("ServerScriptService").TrainSplit)
	local result = TrainSplit.SplitAt(train, 1)   -- your damage system decides when (windows and walls not fixed)
	TrainSplit.Snapped.Event:Connect(function(train, k, result) end)
	TrainSplit.Despawned.Event:Connect(function(train, k, wreck) end)  -- fires just before the wreck is destroyed

Riders: result.riders are CANDIDATES only, a snapshot of where each client said its character was at the
snap. Anything that rewards or punishes a rider must use the server re-check instead:
	local riders = TrainSplit.ConfirmRiders(result)  -- yields until Config.RiderConfirmDelay after the snap

Server authority: only the server moves wrecks. Every lost part is welded to an anchored root the server
drives, so no client ever owns wreck physics; the wreck's size, place and speed come from parts that were
anchored at the snap (never from unanchored, possibly client-owned ones), its speed is capped, and it
despawns by the computed slide, not by where a part is. Clients hear about a snap once, through the
RR_TrainSplitFX RemoteEvent (server -> clients); a client firing it back is ignored and flagged once.
Require this module once at server start so the RemoteEvent exists before clients look for it.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage:WaitForChild("TrainSplitConfig"))
local Shared = require(ReplicatedStorage:WaitForChild("TrainSplitShared"))

local TrainSplit = {}
TrainSplit.Version = "2.3.0"

local BRAKE_FALLBACK = 12 -- break_spec motion.brake, used if Config.Brake is not a positive number
local CONFIRM_MARGIN = 6 -- studs around a wreck that still count as "on it" when riders are re-checked

local function findOrMake(parent, className, name)
	local inst = parent:FindFirstChild(name)
	if inst and inst:IsA(className) then
		return inst
	end
	inst = Instance.new(className)
	inst.Name = name
	inst.Parent = parent
	return inst
end

local remote = findOrMake(ReplicatedStorage, "RemoteEvent", Config.RemoteName)
TrainSplit.Snapped = findOrMake(script, "BindableEvent", "Snapped")
TrainSplit.Despawned = findOrMake(script, "BindableEvent", "Despawned")

-- Honest clients never fire this remote. Draining it keeps an exploiter's FireServer spam out of the engine's
-- queue; the sender is flagged once (warning + Player attribute) for your anti-cheat, and nothing else happens.
local flagged = setmetatable({}, { __mode = "k" })
remote.OnServerEvent:Connect(function(player)
	if typeof(player) ~= "Instance" or flagged[player] then
		return
	end
	flagged[player] = true
	pcall(function()
		player:SetAttribute(Config.MisuseAttribute, true)
	end)
	warn(("TrainSplit: %s fired %s, which is server -> client only; ignored (flagged once)"):format(player.Name, remote.Name))
end)

local function finite(x)
	return type(x) == "number" and x == x and x ~= math.huge and x ~= -math.huge
end

-- The train's speed for the maths: Speed attribute, else opts.speed, else the default. Never NaN, inf or
-- negative (a negative speed would throw the wreck forward into the kept train).
local function trainSpeed(train, opts)
	local v = train:GetAttribute(Config.SpeedAttribute)
	if not finite(v) then
		v = opts.speed
	end
	if not finite(v) then
		v = Config.SpeedDefault
	end
	return math.clamp(v, 0, Config.MaxSpeed)
end

local function brakeRate()
	if finite(Config.Brake) and Config.Brake > 0 then
		return Config.Brake
	end
	return BRAKE_FALLBACK
end

local function vmin(a, b)
	return Vector3.new(math.min(a.X, b.X), math.min(a.Y, b.Y), math.min(a.Z, b.Z))
end
local function vmax(a, b)
	return Vector3.new(math.max(a.X, b.X), math.max(a.Y, b.Y), math.max(a.Z, b.Z))
end

-- AABB of a part in frame B (B-space min, max), from its CFrame and Size only.
local function boxIn(B, part)
	local rel = B:ToObjectSpace(part.CFrame)
	local _, _, _, r00, r01, r02, r10, r11, r12, r20, r21, r22 = rel:GetComponents()
	local h = part.Size / 2
	local e = Vector3.new(
		math.abs(r00) * h.X + math.abs(r01) * h.Y + math.abs(r02) * h.Z,
		math.abs(r10) * h.X + math.abs(r11) * h.Y + math.abs(r12) * h.Z,
		math.abs(r20) * h.X + math.abs(r21) * h.Y + math.abs(r22) * h.Z
	)
	return rel.Position - e, rel.Position + e
end

-- Break records written by the setup, indexed by break number.
function TrainSplit.GetBreaks(train)
	local list = {}
	local folder = train and train:FindFirstChild("RR_Breaks")
	if not folder then
		return list
	end
	for _, rec in folder:GetChildren() do
		local k = tonumber(string.match(rec.Name, "^Break(%d+)$"))
		local cf = rec:GetAttribute("BreakCFrame")
		if k and typeof(cf) == "CFrame" then
			local kept, lost = rec:FindFirstChild("KeptHalf"), rec:FindFirstChild("LostHalf")
			list[k] = {
				k = k,
				record = rec,
				cframe = cf,
				carriage = rec:GetAttribute("Carriage") or k,
				intact = rec:GetAttribute("Intact") ~= false,
				detached = rec:GetAttribute("Detached") == true,
				kept = kept and kept.Value,
				lost = lost and lost.Value,
			}
		end
	end
	return list
end

-- True while break k can still snap: not snapped yet and its carriage still on the train.
function TrainSplit.IsIntact(train, k)
	local b = TrainSplit.GetBreaks(train)[k]
	return b ~= nil and b.intact and not b.detached
end

local function wreckFolder()
	return findOrMake(workspace, "Folder", Config.WreckFolderName)
end

local function otherEnd(joint, part)
	local a, b
	if joint:IsA("JointInstance") or joint:IsA("WeldConstraint") then
		a, b = joint.Part0, joint.Part1
	elseif joint:IsA("Constraint") then
		a = joint.Attachment0 and joint.Attachment0.Parent
		b = joint.Attachment1 and joint.Attachment1.Parent
	else
		return nil
	end
	if a == part then
		return b
	end
	return a
end

-- A joint from the wreck to the kept train would hold it back: switch those off (never destroyed).
-- Joints to characters (seat welds) are left alone so seated riders go with the wreck.
local function releaseFromTrain(parts, train)
	local released = 0
	for _, part in parts do
		local ok, joints = pcall(part.GetJoints, part)
		if ok then
			for _, joint in joints do
				local other = otherEnd(joint, part)
				if other and other:IsDescendantOf(train) and pcall(function()
					joint.Enabled = false
				end) then
					released += 1
				end
			end
		end
	end
	return released
end

-- One lost body: its halves move into a Model in workspace.RR_Wrecks around an anchored root.
local function makeBody(train, k, index, B, halves)
	local parts, lo, hi = {}, nil, nil
	local function grow(part)
		local a, b = boxIn(B, part)
		lo = lo and vmin(lo, a) or a
		hi = hi and vmax(hi, b) or b
	end
	for _, half in halves do
		for _, d in half:GetDescendants() do
			if d:IsA("BasePart") then
				table.insert(parts, d)
				-- only parts anchored at the snap count: an unanchored one may be client-owned and anywhere
				if d.Anchored then
					grow(d)
				end
			end
		end
	end
	if #parts == 0 then
		return nil
	end
	if not lo then
		for _, half in halves do
			local r = half.PrimaryPart
			if r then
				grow(r)
			end
		end
	end
	if not lo then
		lo, hi = Vector3.new(-1, -1, -1), Vector3.new(1, 1, 1)
	end
	local centre = (lo + hi) / 2
	local model = Instance.new("Model")
	model.Name = ("RR_Wreck_%s_B%d_%d"):format(train.Name, k, index)
	pcall(function()
		model.ModelStreamingMode = Enum.ModelStreamingMode.Atomic -- stream the wreck as one piece
	end)
	local root = Instance.new("Part")
	root.Name = "BodyRoot"
	root.Size = Vector3.new(1, 1, 1)
	root.Transparency = 1
	root.Anchored = true
	root.CanCollide = false
	root.CanQuery = false
	root.CanTouch = false
	root.CastShadow = false
	root.CFrame = B * CFrame.new(centre)
	root.Parent = model
	model.PrimaryPart = root
	model.Parent = wreckFolder()
	for _, half in halves do
		half.Parent = model
	end
	local released = releaseFromTrain(parts, train)
	-- Weld every lost part (anchored or not), then unanchor: the anchored root carries all of it, one CFrame per
	-- body per frame, and no part is left as a free assembly a client could own.
	for _, part in parts do
		local weld = Instance.new("WeldConstraint")
		weld.Name = "RR_WreckWeld"
		weld.Part0 = root
		weld.Part1 = part
		weld.Parent = root
	end
	for _, part in parts do
		part.Anchored = false
	end
	for _, part in parts do
		-- belt and braces: throws for parts welded to the anchored root, which are server-side anyway
		pcall(part.SetNetworkOwner, part, nil)
	end
	-- the farthest corner from either pivot line sizes the speed cap
	local far = 0
	for _, x in { lo.X, hi.X } do
		for _, y in { lo.Y, hi.Y } do
			for _, s in { -1, 1 } do
				far = math.max(far, Vector2.new(x - s * Config.Pivot.X_abs, y - Config.Pivot.Y).Magnitude)
			end
		end
	end
	return { model = model, root = root, base = root.CFrame, lo = lo, hi = hi, centre = centre, far = far, released = released }
end

-- Players standing (or seated) on a lost body at the snap: candidates, judged from client-owned positions.
-- The broken body also has to be behind the tear itself, because its box reaches forward where the roof bites.
local function findCandidates(B, bodies)
	local riders, seen = {}, {}
	for _, player in Players:GetPlayers() do
		local character = player.Character
		local hrp = character and character:FindFirstChild("HumanoidRootPart")
		if hrp and hrp:IsA("BasePart") and not seen[player] then
			local p = B:PointToObjectSpace(hrp.CFrame.Position)
			for i, body in bodies do
				local lo, hi = body.lo, body.hi
				local inside = p.X >= lo.X - 1 and p.X <= hi.X + 1 and p.Y >= lo.Y - 1 and p.Y <= hi.Y + 8
					and p.Z >= lo.Z - 1 and p.Z <= hi.Z + 1
				if inside and i == 1 then
					local feetY = math.clamp(p.Y - 3, lo.Y, hi.Y)
					inside = p.Z > (Shared.dAt(Config.Cells, p.X, feetY) or 0)
				end
				if inside then
					seen[player] = true
					table.insert(riders, player)
					break
				end
			end
		end
	end
	return riders
end

-- Drives every body of one snap from the Shared maths until it has slid far enough behind to despawn.
local function drive(run)
	local stopT = Shared.brakeTime(run.V, run.brake)
	local connection
	connection = RunService.Heartbeat:Connect(function()
		local t = workspace:GetServerTimeNow() - run.t0
		local alive = 0
		for _, body in run.bodies do
			if not body.gone then
				if not body.handedOff then
					body.root.CFrame = Shared.bodyCFrame(body.base, run.B, run.side, t, body.params)
					-- velocity on the anchored root carries riders like a conveyor; capped so it can never fling them
					local v = Shared.bodyVelocity(body.base, run.B, run.side, t, body.params)
					body.root.AssemblyLinearVelocity = Shared.clampVelocity(v, body.cap)
					if run.terrain and t >= stopT then
						-- now static relative to the terrain: the owner's terrain mover takes over
						body.handedOff = true
						body.root.AssemblyLinearVelocity = Vector3.zero
						body.model.Parent = run.terrain
					end
				end
				-- despawn by the computed slide, never by where a part happens to be
				local slid = Shared.drift(t, run.V, run.brake, Config.Recoil)
				if slid >= Config.Despawn.distance or t >= Config.Despawn.time or not body.model.Parent then
					body.gone = true
					TrainSplit.Despawned:Fire(run.train, run.k, body.model)
					local model = body.model
					task.defer(function()
						model:Destroy() -- deferred so Despawned handlers still see the wreck
					end)
				else
					alive += 1
				end
			end
		end
		if alive == 0 then
			connection:Disconnect()
		end
	end)
	return connection
end

local runs = setmetatable({}, { __mode = "k" }) -- result -> its snap, for ConfirmRiders

--[[
SplitAt(train, k, opts) -> { bodies = {Model}, riders = {Player} }
Snaps break k (1 = Carriage1, 2 = Carriage2). Server only; calling it again for the same break,
or for a break whose carriage already left, does nothing and returns empty lists.
Lost set (break_spec): break 1 loses Carriage1.RearHalf plus whatever of Carriage2 is still attached
(the gangway belongs to Carriage2.FrontHalf); break 2 loses Carriage2.RearHalf. 2 then 1 loses only
C1.Rear + C2.Front.
riders are candidates (see the header): confirm them with TrainSplit.ConfirmRiders(result).
opts (all optional):
  speed    studs/s when the train has no usable Speed attribute (default Config.SpeedDefault)
  side     "left" | "right" | "random" (default Config.Side)
  seed     number, makes side and fx rolls repeatable
  terrain  Instance: once the wreck moves at terrain speed it is parented here, for your terrain mover
  lead     seconds before the snap (default Config.LeadTime)
]]
function TrainSplit.SplitAt(train, k, opts)
	opts = opts or {}
	local result = { bodies = {}, riders = {} }
	if not RunService:IsServer() then
		warn("TrainSplit.SplitAt is server-only")
		return result
	end
	if typeof(train) ~= "Instance" or type(k) ~= "number" then
		warn("TrainSplit.SplitAt(train: Model, k: number) got", typeof(train), typeof(k))
		return result
	end
	local breaks = TrainSplit.GetBreaks(train)
	local brk = breaks[k]
	if not brk then
		warn(("TrainSplit: %s has no Break%d; run RR_TrainSplit_Setup on it first"):format(train:GetFullName(), k))
		return result
	end
	if not TrainSplit.IsIntact(train, k) then
		return result -- already snapped, or its carriage already left: nothing to do
	end

	local state = {}
	for j, b in breaks do
		state[j] = not b.intact
	end
	local groups = Shared.lostHalves(state, k, #breaks)

	-- Record the snap before touching anything, so a repeat call is a no-op even if something below fails.
	brk.record:SetAttribute("Intact", false)
	brk.record:SetAttribute("SnapTime", workspace:GetServerTimeNow())
	for j, b in breaks do
		if j > k and b.intact then
			b.record:SetAttribute("Detached", true) -- its whole carriage leaves with this snap
		end
	end
	if #groups == 0 then
		return result
	end

	local halves = {}
	for _, b in breaks do
		halves[Shared.halfId(b.carriage, "Front")] = b.kept
		halves[Shared.halfId(b.carriage, "Rear")] = b.lost
	end

	local B = brk.cframe
	local V = trainSpeed(train, opts)
	local brake = brakeRate()
	local seed = finite(opts.seed) and opts.seed or math.random(1, 2147483646)
	local side = Shared.side(opts.side or Config.Side, seed)
	-- t0 is the snap moment on the shared server clock; the lead lets the tear sound play first.
	local t0 = workspace:GetServerTimeNow() + (finite(opts.lead) and math.max(opts.lead, 0) or Config.LeadTime)

	local run = { train = train, k = k, B = B, side = side, t0 = t0, V = V, brake = brake, terrain = opts.terrain, bodies = {} }
	for i, ids in groups do
		local models = {}
		for _, id in ids do
			local half = halves[id]
			if half and half.Parent then
				table.insert(models, half)
			end
		end
		local body = #models > 0 and makeBody(train, k, i, B, models)
		if body then
			body.params = {
				V = V,
				brake = brake,
				recoil = Config.Recoil,
				pivot = Config.Pivot,
				topple = Config.Topple[math.min(i, #Config.Topple)],
				rest = Config.ToppleRest,
			}
			body.cap = Shared.velocityCap(V, body.params, body.far, side)
			table.insert(run.bodies, body)
			table.insert(result.bodies, body.model)
		end
	end
	if #run.bodies == 0 then
		return result
	end
	result.riders = findCandidates(B, run.bodies)
	runs[result] = run

	local kept = brk.kept
	local payload = {
		v = 1,
		k = k,
		t0 = t0,
		breakCF = B,
		seed = seed,
		side = side,
		kept = kept and (kept.PrimaryPart or kept:FindFirstChild("Root")) or nil,
		params = {
			V = V,
			brake = brake,
			recoil = Config.Recoil,
			pivot = Config.Pivot,
			rest = Config.ToppleRest,
			handoff = opts.terrain ~= nil,
			despawnTime = Config.Despawn.time,
		},
		bodies = {},
	}
	for i, body in run.bodies do
		payload.bodies[i] = { name = body.model.Name, root = body.root, base = body.base, topple = body.params.topple }
	end
	drive(run)
	remote:FireAllClients(payload)
	TrainSplit.Snapped:Fire(train, k, result)
	return result
end

-- Still on one of this snap's wrecks, judged on the server: seated in it (the seat weld is server-side), or
-- the character within CONFIRM_MARGIN of the wreck's snap-time box, carried to where the wreck is now.
local function stillOn(player, run)
	local character = player.Character
	if not character then
		return false
	end
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	local seat = humanoid and humanoid.SeatPart
	local hrp = character:FindFirstChild("HumanoidRootPart")
	for _, body in run.bodies do
		if not body.gone and body.model.Parent then
			if seat and seat:IsDescendantOf(body.model) then
				return true
			end
			if hrp and hrp:IsA("BasePart") then
				local p = body.root.CFrame:PointToObjectSpace(hrp.CFrame.Position)
				local lo, hi, m = body.lo - body.centre, body.hi - body.centre, CONFIRM_MARGIN
				if p.X >= lo.X - m and p.X <= hi.X + m and p.Y >= lo.Y - m and p.Y <= hi.Y + m and p.Z >= lo.Z - m and p.Z <= hi.Z + m then
					return true
				end
			end
		end
	end
	return false
end

--[[
ConfirmRiders(result, delay) -> {Player}
Re-checks the candidates in result.riders on the server `delay` seconds after the snap (default
Config.RiderConfirmDelay; yields until then): a candidate counts if it is seated in a wreck or still over
one. Use this list, not result.riders, for anything that rewards or punishes a rider.
]]
function TrainSplit.ConfirmRiders(result, delay)
	local run = result and runs[result]
	if not run then
		return {}
	end
	delay = finite(delay) and math.max(delay, 0) or Config.RiderConfirmDelay
	local wait = run.t0 + delay - workspace:GetServerTimeNow()
	if wait > 0 then
		task.wait(wait)
	end
	local confirmed = {}
	for _, player in result.riders do
		if player.Parent and stillOn(player, run) then
			table.insert(confirmed, player)
		end
	end
	return confirmed
end

return TrainSplit
