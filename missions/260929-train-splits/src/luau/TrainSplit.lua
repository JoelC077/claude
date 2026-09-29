--[[
TrainSplit  (ModuleScript in ServerScriptService)  v2.0.0

Tears a carriage in half at runtime. Needs RR_TrainSplit_Setup to have run on the train:
Train/Carriage1..2/{FrontHalf, RearHalf} and Train/RR_Breaks/Break1..2.

	local TrainSplit = require(game:GetService("ServerScriptService").TrainSplit)
	TrainSplit.SplitAt(train, 1)   -- your damage system decides when (windows and walls not fixed)
	TrainSplit.Snapped.Event:Connect(function(train, k, result) end)   -- result = { bodies, riders }
	TrainSplit.Despawned.Event:Connect(function(train, k, wreck) end)  -- fires just before the wreck is destroyed

Server authority: only the server moves wrecks. Clients hear about a snap once, through the
RR_TrainSplitFX RemoteEvent (server -> clients); nothing is ever read from clients.
Require this module once at server start so the RemoteEvent exists before clients look for it.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage:WaitForChild("TrainSplitConfig"))
local Shared = require(ReplicatedStorage:WaitForChild("TrainSplitShared"))

local TrainSplit = {}
TrainSplit.Version = "2.0.0"

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

-- Server -> clients only: this module never connects OnServerEvent, so clients cannot drive anything.
local remote = findOrMake(ReplicatedStorage, "RemoteEvent", Config.RemoteName)
TrainSplit.Snapped = findOrMake(script, "BindableEvent", "Snapped")
TrainSplit.Despawned = findOrMake(script, "BindableEvent", "Despawned")

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
	for _, half in halves do
		for _, d in half:GetDescendants() do
			if d:IsA("BasePart") then
				table.insert(parts, d)
				local a, b = boxIn(B, d)
				lo = lo and lo:Min(a) or a
				hi = hi and hi:Max(b) or b
			end
		end
	end
	if not lo then
		return nil
	end
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
	root.CFrame = B * CFrame.new((lo + hi) / 2)
	root.Parent = model
	model.PrimaryPart = root
	model.Parent = wreckFolder()
	for _, half in halves do
		half.Parent = model
	end
	local released = releaseFromTrain(parts, train)
	-- Weld first, unanchor second: the anchored root then carries everything (one CFrame per body per frame).
	local anchored = {}
	for _, part in parts do
		if part.Anchored then
			local weld = Instance.new("WeldConstraint")
			weld.Name = "RR_WreckWeld"
			weld.Part0 = root
			weld.Part1 = part
			weld.Parent = root
			table.insert(anchored, part)
		end
	end
	for _, part in anchored do
		part.Anchored = false
	end
	return { model = model, root = root, base = root.CFrame, lo = lo, hi = hi, released = released }
end

-- Players standing (or seated) on a lost body. The broken body also has to be behind the tear itself,
-- because its box reaches forward into the kept half where the roof bites.
local function findRiders(B, bodies)
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

-- Drives every body of one snap from the Shared maths until it is far enough behind to despawn.
local function drive(run)
	local stopT = Shared.brakeTime(run.V, Config.Brake)
	local connection
	connection = RunService.Heartbeat:Connect(function()
		local t = workspace:GetServerTimeNow() - run.t0
		local alive = 0
		for _, body in run.bodies do
			if not body.gone then
				if not body.handedOff then
					body.root.CFrame = Shared.bodyCFrame(body.base, run.B, run.side, t, body.params)
					-- velocity on the anchored root carries riders like a conveyor
					body.root.AssemblyLinearVelocity = Shared.bodyVelocity(body.base, run.B, run.side, t, body.params)
					if run.terrain and t >= stopT then
						-- now static relative to the terrain: the owner's terrain mover takes over
						body.handedOff = true
						body.root.AssemblyLinearVelocity = Vector3.zero
						body.model.Parent = run.terrain
					end
				end
				local dist = (body.root.CFrame.Position - body.base.Position).Magnitude
				if dist >= Config.Despawn.distance or t >= Config.Despawn.time or not body.model.Parent then
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

--[[
SplitAt(train, k, opts) -> { bodies = {Model}, riders = {Player} }
Snaps break k (1 = Carriage1, 2 = Carriage2). Server only; calling it again for the same break,
or for a break whose carriage already left, does nothing and returns empty lists.
Lost set (break_spec): break 1 loses Carriage1.RearHalf (with the gangway) plus whatever of
Carriage2 is still attached; break 2 loses Carriage2.RearHalf. 2 then 1 loses only C1.Rear + C2.Front.
opts (all optional):
  speed    studs/s when the train has no Speed attribute (default Config.SpeedDefault)
  side     "left" | "right" | "random" (default Config.Side)
  seed     number, makes side and fx rolls repeatable
  terrain  Instance: once the wreck moves at terrain speed it is parented here, for your terrain mover
  lead     seconds before the snap (default Config.LeadTime)
Riders are carried with the wreck; what happens to them next is up to your rules.
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
	for j, b in breaks do
		halves[Shared.halfId(b.carriage, "Front")] = b.kept
		halves[Shared.halfId(b.carriage, "Rear")] = b.lost
	end

	local B = brk.cframe
	local V = tonumber(train:GetAttribute(Config.SpeedAttribute)) or opts.speed or Config.SpeedDefault
	local seed = opts.seed or math.random(1, 2147483646)
	local side = Shared.side(opts.side or Config.Side, seed)
	-- t0 is the snap moment on the shared server clock; the lead lets the tear sound play first.
	local t0 = workspace:GetServerTimeNow() + (opts.lead or Config.LeadTime)

	local run = { train = train, k = k, B = B, side = side, t0 = t0, V = V, terrain = opts.terrain, bodies = {} }
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
				brake = Config.Brake,
				recoil = Config.Recoil,
				pivot = Config.Pivot,
				topple = Config.Topple[math.min(i, #Config.Topple)],
			}
			table.insert(run.bodies, body)
			table.insert(result.bodies, body.model)
		end
	end
	if #run.bodies == 0 then
		return result
	end
	result.riders = findRiders(B, run.bodies)

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
			brake = Config.Brake,
			recoil = Config.Recoil,
			pivot = Config.Pivot,
			handoff = opts.terrain ~= nil,
			despawnTime = Config.Despawn.time,
		},
		bodies = {},
	}
	for i, body in run.bodies do
		payload.bodies[i] = { name = body.model.Name, root = body.root, base = body.base, topple = body.params.topple, torn = i == 1 }
	end
	drive(run)
	remote:FireAllClients(payload)
	TrainSplit.Snapped:Fire(train, k, result)
	return result
end

return TrainSplit
