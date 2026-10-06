--[[
harness.luau: Lune stand-ins for the Roblox engine pieces the scripts touch, a loader that runs the
production .lua files unchanged through @lune/luau with a custom environment, and the synthetic train
built from the export (src/analysis/groups.json).

Engine stand-ins (only for tests; the production files never see this module):
  BasePart:SubtractAsync  returns a UnionOperation whose box is the part box minus the cutter boxes
                          (exact grid decomposition in the part's frame; can be told to fail by export name)
  BasePart:GetJoints      joints registered by the test
  BasePart:SetNetworkOwner records the owner (throws for anchored parts, like the engine)
  Selection:Get, ChangeHistoryService recording/waypoints, Workspace:GetServerTimeNow (a fake clock),
  RunService (IsServer/IsStudio/Heartbeat/BindToRenderStep), RemoteEvent/BindableEvent signals,
  DataModel:IsLoaded, Players:GetPlayers, Instance:WaitForChild / GetAttributeChangedSignal /
  DescendantAdded, Sound:Play/Stop, ParticleEmitter:Emit.
]]

local fs = require("@lune/fs")
local serde = require("@lune/serde")
local roblox = require("@lune/roblox")
local luau = require("@lune/luau")
local task = require("@lune/task")

local Instance, CFrame, Vector3 = roblox.Instance, roblox.CFrame, roblox.Vector3

local H = {}

---------------------------------------------------------------- paths

local here = debug.info(1, "s")
local testsDir = here:match("^(.*)[/\\][^/\\]+$") or "."
H.testsDir = testsDir
H.luauDir = testsDir:match("^(.*)[/\\][^/\\]+$") or ".."
H.srcDir = H.luauDir:match("^(.*)[/\\][^/\\]+$") or "../.."
H.outDir = testsDir .. "/out"

function H.source(file)
	return fs.readFile(H.luauDir .. "/" .. file)
end

local groupsCache, specCache
function H.groups()
	groupsCache = groupsCache or serde.decode("json", fs.readFile(H.srcDir .. "/analysis/groups.json"))
	return groupsCache
end
function H.spec()
	specCache = specCache or serde.decode("json", fs.readFile(H.srcDir .. "/kit/break_spec.json"))
	return specCache
end

function H.writeOut(name, lines)
	if not fs.isDir(H.outDir) then
		fs.writeDir(H.outDir)
	end
	fs.writeFile(H.outDir .. "/" .. name, table.concat(lines, "\n") .. "\n")
end

---------------------------------------------------------------- shim state and signals

local state = {}
H.state = state

function H.resetState()
	state.selection = {}
	state.clock = 1000
	state.recordings = {}
	state.waypoints = {}
	state.failNames = {}
	state.csgCalls = 0
	state.joints = {}
	state.networkOwner = {}
	state.fired = {}
	state.players = {}
	state.renderSteps = {}
	state.isServer = true
	state.isStudio = true
	state.played = {}
	state.stopped = {}
	state.emitted = {}
	state.log = {}
	state.warnings = {}
end
H.resetState()

local function newSignal()
	local sig = { handlers = {} }
	function sig:Connect(fn)
		local h = { fn = fn, connected = true }
		table.insert(self.handlers, h)
		local conn = { Connected = true }
		function conn:Disconnect()
			h.connected = false
			self.Connected = false
		end
		return conn
	end
	function sig:Once(fn)
		local conn
		conn = self:Connect(function(...)
			conn:Disconnect()
			fn(...)
		end)
		return conn
	end
	function sig:Fire(...)
		for _, h in table.clone(self.handlers) do
			if h.connected then
				h.fn(...)
			end
		end
	end
	function sig:count()
		local n = 0
		for _, h in self.handlers do
			if h.connected then
				n += 1
			end
		end
		return n
	end
	return sig
end

local signals = {}
function H.signal(inst, key)
	signals[inst] = signals[inst] or {}
	signals[inst][key] = signals[inst][key] or newSignal()
	return signals[inst][key]
end
function H.resetSignal(inst, key)
	signals[inst] = signals[inst] or {}
	signals[inst][key] = newSignal()
end

---------------------------------------------------------------- SubtractAsync stand-in

local function uniqueSorted(list)
	table.sort(list)
	local out = {}
	for _, v in list do
		if #out == 0 or v - out[#out] > 1e-6 then
			table.insert(out, v)
		end
	end
	return out
end

-- Box of `c` in the frame P: {x0, x1, y0, y1, z0, z1}.
local function boxInFrame(P, c)
	local rel = P:ToObjectSpace(c.CFrame)
	local px, py, pz, r00, r01, r02, r10, r11, r12, r20, r21, r22 = rel:GetComponents()
	local s = c.Size / 2
	local ex = math.abs(r00) * s.X + math.abs(r01) * s.Y + math.abs(r02) * s.Z
	local ey = math.abs(r10) * s.X + math.abs(r11) * s.Y + math.abs(r12) * s.Z
	local ez = math.abs(r20) * s.X + math.abs(r21) * s.Y + math.abs(r22) * s.Z
	return { px - ex, px + ex, py - ey, py + ey, pz - ez, pz + ez }
end
H.boxInFrame = boxInFrame

local function subtractAsync(self, cutters)
	state.csgCalls += 1
	if state.onSubtract then
		state.onSubtract(self, cutters)
	end
	local name = self:GetAttribute("ExportName")
	if name and state.failNames[name] then
		error("CSG failed (simulated) on " .. name)
	end
	if typeof(cutters) ~= "table" or #cutters == 0 then
		error("SubtractAsync needs a list of parts")
	end
	-- keep the production code honest about where CSG inputs live
	assert(self:FindFirstAncestorOfClass("Workspace"), "SubtractAsync: the part must sit in the Workspace")
	local P = self.CFrame
	local h = self.Size / 2
	local lo, hi = { -h.X, -h.Y, -h.Z }, { h.X, h.Y, h.Z }
	local cuts = { { lo[1], hi[1] }, { lo[2], hi[2] }, { lo[3], hi[3] } }
	local boxes = {}
	for _, c in cutters do
		assert(c:FindFirstAncestorOfClass("Workspace"), "SubtractAsync: cutter parts must sit in the Workspace")
		local b = boxInFrame(P, c)
		table.insert(boxes, b)
		for axis = 1, 3 do
			for _, v in { b[2 * axis - 1], b[2 * axis] } do
				if v > lo[axis] and v < hi[axis] then
					table.insert(cuts[axis], v)
				end
			end
		end
	end
	local xs, ys, zs = uniqueSorted(cuts[1]), uniqueSorted(cuts[2]), uniqueSorted(cuts[3])
	local kl, kh = { math.huge, math.huge, math.huge }, { -math.huge, -math.huge, -math.huge }
	local kept = false
	for i = 1, #xs - 1 do
		local mx = (xs[i] + xs[i + 1]) / 2
		for j = 1, #ys - 1 do
			local my = (ys[j] + ys[j + 1]) / 2
			for k = 1, #zs - 1 do
				local mz = (zs[k] + zs[k + 1]) / 2
				local inside = false
				for _, b in boxes do
					if mx > b[1] and mx < b[2] and my > b[3] and my < b[4] and mz > b[5] and mz < b[6] then
						inside = true
						break
					end
				end
				if not inside then
					kept = true
					kl[1], kh[1] = math.min(kl[1], xs[i]), math.max(kh[1], xs[i + 1])
					kl[2], kh[2] = math.min(kl[2], ys[j]), math.max(kh[2], ys[j + 1])
					kl[3], kh[3] = math.min(kl[3], zs[k]), math.max(kh[3], zs[k + 1])
				end
			end
		end
	end
	if not kept then
		error("CSG result is empty")
	end
	local u = Instance.new("UnionOperation")
	u.Size = Vector3.new(kh[1] - kl[1], kh[2] - kl[2], kh[3] - kl[3])
	u.CFrame = P * CFrame.new((kl[1] + kh[1]) / 2, (kl[2] + kh[2]) / 2, (kl[3] + kh[3]) / 2)
	return u
end

---------------------------------------------------------------- engine stand-ins

roblox.implementMethod("BasePart", "SubtractAsync", subtractAsync)
roblox.implementMethod("BasePart", "GetJoints", function(self)
	local list = {}
	for _, j in state.joints do
		if j.Part0 == self or j.Part1 == self then
			table.insert(list, j)
		end
	end
	return list
end)
roblox.implementMethod("BasePart", "SetNetworkOwner", function(self, owner)
	if self.Anchored then
		error("Network Ownership API cannot be called on Anchored parts or parts welded to Anchored parts.")
	end
	state.networkOwner[self] = owner == nil and "server" or owner
end)
roblox.implementMethod("Selection", "Get", function()
	return table.clone(state.selection)
end)
roblox.implementMethod("ChangeHistoryService", "TryBeginRecording", function(_, name)
	table.insert(state.recordings, { begin = name })
	return "rec" .. #state.recordings
end)
roblox.implementMethod("ChangeHistoryService", "FinishRecording", function(_, id, op)
	table.insert(state.recordings, { finish = id, op = op })
end)
roblox.implementMethod("ChangeHistoryService", "SetWaypoint", function(_, name)
	table.insert(state.waypoints, name)
end)
roblox.implementMethod("Workspace", "GetServerTimeNow", function()
	return state.clock
end)
roblox.implementMethod("RunService", "IsServer", function()
	return state.isServer
end)
roblox.implementMethod("RunService", "IsClient", function()
	return not state.isServer
end)
roblox.implementMethod("RunService", "IsStudio", function()
	return state.isStudio
end)
roblox.implementProperty("RunService", "Heartbeat", function(self)
	return H.signal(self, "Heartbeat")
end)
roblox.implementMethod("RunService", "BindToRenderStep", function(_, name, _priority, fn)
	state.renderSteps[name] = fn
end)
roblox.implementMethod("RunService", "UnbindFromRenderStep", function(_, name)
	state.renderSteps[name] = nil
end)
roblox.implementMethod("RemoteEvent", "FireAllClients", function(_, payload)
	table.insert(state.fired, payload)
end)
roblox.implementProperty("RemoteEvent", "OnClientEvent", function(self)
	return H.signal(self, "OnClientEvent")
end)
roblox.implementProperty("RemoteEvent", "OnServerEvent", function(self)
	state.onServerEventUsed = true
	return H.signal(self, "OnServerEvent")
end)
roblox.implementMethod("BindableEvent", "Fire", function(self, ...)
	H.signal(self, "Event"):Fire(...)
end)
roblox.implementProperty("BindableEvent", "Event", function(self)
	return H.signal(self, "Event")
end)
roblox.implementMethod("DataModel", "IsLoaded", function()
	return true
end)
roblox.implementMethod("Players", "GetPlayers", function()
	return state.players
end)
roblox.implementMethod("Instance", "WaitForChild", function(self, name)
	local child = self:FindFirstChild(name)
	assert(child, "WaitForChild(" .. tostring(name) .. ") would wait forever in " .. self:GetFullName())
	return child
end)
roblox.implementMethod("Instance", "GetAttributeChangedSignal", function(self, attr)
	return H.signal(self, "Attr:" .. attr)
end)
roblox.implementProperty("Instance", "DescendantAdded", function(self)
	return H.signal(self, "DescendantAdded")
end)
roblox.implementMethod("Sound", "Play", function(self)
	-- recorded now: Lune cannot read an instance once it is destroyed (Roblox can)
	table.insert(state.played, { sound = self, name = self.Name, parent = self.Parent, speed = self.PlaybackSpeed, volume = self.Volume, at = state.clock })
end)
roblox.implementMethod("Sound", "Stop", function(self)
	state.stopped[self] = state.clock
end)
roblox.implementMethod("ParticleEmitter", "Emit", function(self, n)
	table.insert(state.emitted, { emitter = self, n = n })
end)

---------------------------------------------------------------- games, environments, modules

function H.newGame()
	local game = Instance.new("DataModel")
	for _, s in { "Workspace", "ServerStorage", "ReplicatedStorage", "ServerScriptService", "StarterPlayer", "SoundService", "Players", "Selection", "ChangeHistoryService", "RunService" } do
		game:GetService(s)
	end
	local ws = game:GetService("Workspace")
	if not ws:FindFirstChildOfClass("Terrain") then
		local t = Instance.new("Terrain")
		t.Parent = ws
	end
	return game
end

local function capture(list)
	return function(...)
		local parts = {}
		for i = 1, select("#", ...) do
			parts[i] = tostring((select(i, ...)))
		end
		table.insert(list, table.concat(parts, " "))
	end
end

local modules = {} -- [ModuleScript] = { file = , loaded = , value = }

function H.env(game, script)
	local env = {
		game = game,
		workspace = game:GetService("Workspace"),
		script = script,
		task = task,
		Instance = roblox.Instance,
		CFrame = roblox.CFrame,
		Vector3 = roblox.Vector3,
		Vector2 = roblox.Vector2,
		Color3 = roblox.Color3,
		BrickColor = roblox.BrickColor,
		Enum = roblox.Enum,
		NumberRange = roblox.NumberRange,
		NumberSequence = roblox.NumberSequence,
		NumberSequenceKeypoint = roblox.NumberSequenceKeypoint,
		ColorSequence = roblox.ColorSequence,
		ColorSequenceKeypoint = roblox.ColorSequenceKeypoint,
		PhysicalProperties = roblox.PhysicalProperties,
		print = capture(state.log),
		warn = capture(state.warnings),
	}
	env.require = function(mod)
		local entry = modules[mod]
		assert(entry, "require of an unknown module: " .. tostring(mod))
		if not entry.loaded then
			entry.loaded = true
			if entry.value == nil then
				entry.value = H.load(entry.file, game, mod)
			end
		end
		return entry.value
	end
	return env
end

-- Run a production file as-is (optionally with its top config lines changed) and return what it returns.
function H.load(file, game, script, overrides)
	local src = H.source(file)
	for name, value in overrides or {} do
		local literal = type(value) == "string" and ("%q"):format(value) or tostring(value)
		local count
		src, count = src:gsub("\nlocal " .. name .. " = [^\n]-( %-%-)", "\nlocal " .. name .. " = " .. literal .. "%1", 1)
		assert(count == 1, "could not set " .. name .. " in " .. file)
	end
	local fn = luau.load(src, { debugName = file, environment = H.env(game, script) })
	return fn()
end

-- Register a ModuleScript instance backed by a file (or by a ready-made table, e.g. a fake RR_VFX).
function H.module(parent, name, fileOrValue)
	local m = Instance.new("ModuleScript")
	m.Name = name
	m.Parent = parent
	if type(fileOrValue) == "string" then
		modules[m] = { file = fileOrValue }
	else
		modules[m] = { value = fileOrValue, loaded = true }
	end
	return m
end

-- Config, Shared (ReplicatedStorage) and TrainSplit (ServerScriptService) as ModuleScripts.
function H.installRuntime(game)
	local rs, sss = game:GetService("ReplicatedStorage"), game:GetService("ServerScriptService")
	local cfg = H.module(rs, "TrainSplitConfig", "TrainSplitConfig.lua")
	local shared = H.module(rs, "TrainSplitShared", "TrainSplitShared.lua")
	local server = H.module(sss, "TrainSplit", "TrainSplit.lua")
	local env = H.env(game, nil)
	return {
		Config = env.require(cfg),
		Shared = env.require(shared),
		requireServer = function()
			return env.require(server)
		end,
		serverModule = server,
	}
end

---------------------------------------------------------------- the synthetic train

-- Studio names are generic, so parts get "Part" / "Union" / their mesh name; the export name rides along
-- as an attribute for the checks only (the production code never reads it).
function H.buildTrain(game, transform)
	local train = Instance.new("Model")
	train.Name = "Train"
	local body = Instance.new("Model")
	body.Name = "Body"
	body.Parent = train
	local interior = Instance.new("Folder")
	interior.Name = "Interior"
	interior.Parent = train
	local seats = Instance.new("Model")
	seats.Name = "Seats"
	seats.Parent = interior
	local byName = {}
	for _, g in H.groups() do
		local cls, parent, studioName
		if g.name:match("^Union%d+$") then
			cls, parent, studioName = "UnionOperation", body, "Union"
		elseif g.name:match("^Part%d+$") then
			cls, parent, studioName = "Part", train, "Part"
		else
			cls, parent, studioName = "MeshPart", g.name:match("^Cushion") and seats or interior, (g.name:gsub("%d+$", ""))
		end
		local p = Instance.new(cls)
		p.Name = studioName
		p.Anchored = true
		local mn, mx = g.min, g.max
		p.Size = Vector3.new(mx[1] - mn[1], mx[2] - mn[2], mx[3] - mn[3])
		p.CFrame = transform * CFrame.new((mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2, (mn[3] + mx[3]) / 2)
		p:SetAttribute("ExportName", g.name)
		p.Parent = parent
		byName[g.name] = p
	end
	train.Parent = game:GetService("Workspace")
	return train, byName
end

---------------------------------------------------------------- expectations from the spec (independent of the scripts)

function H.origin(k)
	local S = H.spec()
	local c = S.roof_centres_export[tostring(k)]
	return Vector3.new(c[1], c[2] + S.floor_dy, c[3] + S.break_dz)
end

function H.dAt(X, Y)
	for _, c in H.spec().cells do
		if X >= c.X[1] and X < c.X[2] and Y >= c.Y[1] and Y < c.Y[2] then
			return c.d
		end
	end
	return nil
end

-- Carriage and half of an uncut part from its export box: the gangway (spans the join) goes where break_spec
-- "structure" says (v2.1: Carriage2.FrontHalf); everything else by its centre against its carriage's tear.
function H.expectedHalf(g)
	local S = H.spec()
	local zmid = (S.roof_centres_export["1"][3] + S.roof_centres_export["2"][3]) / 2
	if g.min[3] < zmid and g.max[3] > zmid then
		local k, half = S.structure.gangway:match("^Carriage(%d)%.(%a+)Half$")
		return tonumber(k), half
	end
	local zc = (g.min[3] + g.max[3]) / 2
	local k = zc < zmid and 1 or 2
	local o = H.origin(k)
	local X, Y, Z = (g.min[1] + g.max[1]) / 2 - o.X, (g.min[2] + g.max[2]) / 2 - o.Y, zc - o.Z
	return k, Z < (H.dAt(X, Y) or 0) and "Front" or "Rear"
end

function H.expectedCrossers()
	local S, set = H.spec(), {}
	for k = 1, 2 do
		for _, name in S.expected_crossers_export[tostring(k)] do
			set[name] = k
		end
	end
	return set
end

-- "C1.Front" etc. for an instance inside Train/CarriageN/{Front,Rear}Half, or nil.
function H.halfOf(inst, train)
	local p = inst.Parent
	while p and p ~= train do
		if (p.Name == "FrontHalf" or p.Name == "RearHalf") and p.Parent and p.Parent.Parent == train then
			local k = p.Parent.Name:match("^Carriage(%d)$")
			if k then
				return ("C%s.%s"):format(k, p.Name == "FrontHalf" and "Front" or "Rear")
			end
		end
		p = p.Parent
	end
	return nil
end

function H.byExportName(root)
	local map = {}
	for _, d in root:GetDescendants() do
		if d:IsA("BasePart") then
			local n = d:GetAttribute("ExportName")
			if n then
				map[n] = map[n] or {}
				table.insert(map[n], d)
			end
		end
	end
	return map
end

-- A fingerprint of every BasePart's place, to prove a script changed nothing.
function H.fingerprint(root)
	local n, sum = 0, 0
	for _, d in root:GetDescendants() do
		n += 1
		if d:IsA("BasePart") then
			local p = d.CFrame.Position
			sum += p.X * 1.3 + p.Y * 2.7 + p.Z * 0.9 + d.Size.X + d.Size.Y * 3 + d.Size.Z * 7
		end
	end
	return ("%d:%.4f"):format(n, sum)
end

return H
