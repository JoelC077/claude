--[[
Lune suite for the carriage split (mission 260929-train-splits, T2).
Run from src/luau:   lune run tests/run_tests.luau
Prints PASS/FAIL per check and exits non-zero on any failure. Reports from the base scenario are written to
tests/out/ (checker, setup dry run, setup apply, checker after the setup) for reading.
]]

local process = require("@lune/process")
local luau = require("@lune/luau")
local roblox = require("@lune/roblox")
local task = require("@lune/task")
local H = require("./harness")

local Instance, CFrame, Vector3 = roblox.Instance, roblox.CFrame, roblox.Vector3
local state = H.state

local passed, failed = 0, 0
local function check(name, ok, detail)
	if ok then
		passed += 1
		print("PASS  " .. name .. (detail and ("  (" .. tostring(detail) .. ")") or ""))
	else
		failed += 1
		print("FAIL  " .. name .. (detail and ("  -- " .. tostring(detail)) or ""))
	end
	return ok
end
local function section(title)
	print("\n== " .. title .. " ==")
end
local function guarded(name, fn)
	local ok, err = pcall(fn)
	if not ok then
		check(name .. " ran without error", false, err)
	end
end
local function near(a, b, eps)
	return math.abs(a - b) <= (eps or 1e-6)
end
local function nearV(a, b, eps)
	return (a - b).Magnitude <= (eps or 1e-4)
end
local function setOf(list)
	local s = {}
	for _, v in list do
		s[v] = true
	end
	return s
end
local function sameSet(a, b)
	for k in a do
		if not b[k] then
			return false
		end
	end
	for k in b do
		if not a[k] then
			return false
		end
	end
	return true
end
local function names(set)
	local t = {}
	for k in set do
		table.insert(t, k)
	end
	table.sort(t)
	return table.concat(t, ",")
end

local S = H.spec()
local EXPECTED = H.expectedCrossers() -- export name -> break
local BLOCKS = setOf(S.block_parts_export)

---------------------------------------------------------------- static

section("static: files, shared geometry, spec numbers, APIs")
local FILES = {
	"RR_BreakChecker.lua",
	"RR_TrainSplit_Setup.lua",
	"TrainSplitShared.lua",
	"TrainSplitConfig.lua",
	"TrainSplit.lua",
	"TrainSplitClient.lua",
	"TrainSplitDemo.server.lua",
}
for _, f in FILES do
	local ok, err = pcall(luau.compile, H.source(f))
	check("compiles: " .. f, ok, not ok and err or nil)
end

guarded("static", function()
	local checkerCore = H.source("RR_BreakChecker.lua"):match("%-%- CORE BEGIN(.-)%-%- CORE END")
	local setupCore = H.source("RR_TrainSplit_Setup.lua"):match("%-%- CORE BEGIN(.-)%-%- CORE END")
	check("checker and setup carry the identical geometry core", checkerCore ~= nil and checkerCore == setupCore)

	local function cellsIn(file, expr)
		local body = H.source(file):match("%-%- CELLS BEGIN[^\n]*\n(.-)%-%- CELLS END")
		return luau.load("local Config = {}\n" .. body .. "\nreturn " .. expr, { debugName = file .. ":cells" })()
	end
	local function sameCells(cells)
		if #cells ~= #S.cells then
			return false, ("%d cells, spec has %d"):format(#cells, #S.cells)
		end
		for i, c in S.cells do
			local m = cells[i]
			if not (near(m[1], c.X[1]) and near(m[2], c.X[2]) and near(m[3], c.Y[1]) and near(m[4], c.Y[2]) and near(m[5], c.d) and m[6] == c.region) then
				return false, "cell " .. i .. " differs"
			end
		end
		return true, #cells .. " cells"
	end
	check("setup cells == break_spec.json", sameCells(cellsIn("RR_TrainSplit_Setup.lua", "CELLS")))
	check("checker cells == break_spec.json", sameCells(cellsIn("RR_BreakChecker.lua", "CELLS")))
	check("TrainSplitConfig.Cells == break_spec.json", sameCells(cellsIn("TrainSplitConfig.lua", "Config.Cells")))
	local versions = {
		H.source("RR_TrainSplit_Setup.lua"):match('local SPEC_VERSION = "([^"]*)"'),
		H.source("RR_BreakChecker.lua"):match('local SPEC_VERSION = "([^"]*)"'),
		H.source("TrainSplitConfig.lua"):match('Config%.Version = "([^"]*)"'),
		H.source("TrainSplitShared.lua"):match('Shared%.Version = "([^"]*)"'),
		H.source("TrainSplit.lua"):match('TrainSplit%.Version = "([^"]*)"'),
	}
	local sameVersion = #versions == 5
	for _, v in versions do
		sameVersion = sameVersion and v == S.version
	end
	check("every script carries break spec version " .. S.version .. " (run tests/sync_spec.luau after a spec change)", sameVersion, table.concat(versions, ", "))

	local game = H.newGame()
	local Config = H.load("TrainSplitConfig.lua", game, nil)
	local m, t = S.motion, S.topple
	check("config motion == break_spec (speed, brake, recoil, despawn)", Config.SpeedDefault == m.speed_default and Config.Brake == m.brake
		and Config.Recoil.dist == m.recoil.dist and Config.Recoil.time == m.recoil.time
		and Config.Despawn.distance == m.despawn_distance and Config.Despawn.time == m.despawn_time and Config.SpeedAttribute == "Speed")
	local toppleOk = Config.Pivot.X_abs == t.pivot.X_abs and Config.Pivot.Y == t.pivot.Y and #Config.Topple == #t.bodies
	for i, b in t.bodies do
		local c = Config.Topple[i]
		for _, key in { "delay", "roll", "roll_time", "ease", "bounce_time", "yaw", "sink" } do
			toppleOk = toppleOk and c[key] == b[key]
		end
		toppleOk = toppleOk and c.bounce[1] == b.bounce[1] and c.bounce[2] == b.bounce[2]
	end
	check("config topple == break_spec (pivot, 2 bodies)", toppleOk)
	local times = {}
	for _, e in Config.Events do
		times[e.id] = e.t
	end
	local eventsOk = true
	for _, e in S.events do
		if type(e.t) == "number" then
			eventsOk = eventsOk and times[e.id] == e.t
		end
	end
	check("config event times == break_spec", eventsOk and times.topple_crash == "impact" and times.wreck_scrape == 0.3)
	check("config anchors == break_spec (explosion, debris)", nearV(Config.Anchors.split_core, Vector3.new(0, 5, 0)) and nearV(Config.Anchors.debris, Vector3.new(0, 3, 2)))
	local te = Config.Anchors.torn_edge
	check("TornEdge anchor sits on the tear (Z = the cell's d at its X, Y)", near(te.Z, H.dAt(te.X, te.Y), 1e-5), ("Z %.2f, d %.2f"):format(te.Z, H.dAt(te.X, te.Y)))
	local soundKeys = { "metal_tear", "split_explosion", "split_glass", "debris_rain", "topple_crash", "wreck_scrape" }
	local soundsOk = true
	for _, key in soundKeys do
		local d = Config.Sounds[key]
		soundsOk = soundsOk and d ~= nil and d.SoundId == "" and type(d.Volume) == "number" and type(d.Is3D) == "boolean"
	end
	check("config sounds: 6 ids (empty until uploaded) with Volume/Is3D", soundsOk)
	local c, x, g, dr = Config.Sounds.split_explosion, Config.Sounds.metal_tear, Config.Sounds.topple_crash, Config.Sounds.debris_rain
	check("sound mix boom > tear > crash > debris (SOUNDS.md volumes)", c.Volume2D > x.Volume and x.Volume > g.Volume and g.Volume > dr.Volume)

	-- deprecated or unsafe APIs anywhere in the production code (comments stripped)
	local bad = {}
	local patterns = {
		{ "[^%w_%.:]wait%s*%(", "wait()" },
		{ "[^%w_%.:]spawn%s*%(", "spawn()" },
		{ "[^%w_%.:]delay%s*%(", "delay()" },
		{ "[^%w_%.:]tick%s*%(", "tick()" },
		{ "loadstring", "loadstring" },
		{ "getfenv", "getfenv" },
		{ "setfenv", "setfenv" },
		{ "require%s*%(%s*%d", "asset require" },
		{ "OnServerEvent", "OnServerEvent" },
		{ "FireServer", "FireServer" },
		{ "InvokeServer", "InvokeServer" },
		{ ":connect%(", "lower-case connect" },
		{ "Instance%.new%(%s*\"[%w_]+\"%s*,", "Instance.new with a parent" },
	}
	for _, f in FILES do
		for line in (H.source(f) .. "\n"):gmatch("([^\n]*)\n") do
			local code = " " .. (line:gsub("%-%-.*$", ""))
			for _, p in patterns do
				if code:find(p[1]) then
					table.insert(bad, f .. ": " .. p[2])
				end
			end
		end
	end
	check("no deprecated/unsafe APIs (wait/spawn/delay/tick/loadstring/asset require/OnServerEvent/FireServer)", #bad == 0, #bad > 0 and table.concat(bad, "; ") or nil)
end)

---------------------------------------------------------------- pure runtime functions

section("TrainSplitShared: pure maths")
guarded("shared", function()
	local game = H.newGame()
	local Shared = H.load("TrainSplitShared.lua", game, nil)
	local Config = H.load("TrainSplitConfig.lua", game, nil)
	local V, a, rc = 35, 12, { dist = 0.8, time = 0.2 }
	-- recoil 0.8 eased over 0.2 s, then 0.5*a*t^2 until T = V/a = 2.9167 s, then + V*(t - T)
	local expected = { [0] = 0, [0.2] = 1.04, [1] = 6.8, [2.917] = 51.853333, [5] = 124.758333 }
	for _, tt in { 0, 0.2, 1, 2.917, 5 } do
		local got = Shared.drift(tt, V, a, rc)
		check(("drift(t=%g) = %.4f studs"):format(tt, got), near(got, expected[tt], 1e-4), "expected " .. expected[tt])
	end
	local T = Shared.brakeTime(V, a)
	check("brake time V/brake = 2.917 s, slide 51.04 studs", near(T, 35 / 12) and near(Shared.drift(T, V, a, nil), 51.041667, 1e-4))
	check("after V/brake the wreck falls behind at exactly V", near(Shared.drift(6, V, a, rc) - Shared.drift(5, V, a, rc), V, 1e-9))
	check("drift is continuous at V/brake", near(Shared.drift(T - 1e-6, V, a, rc), Shared.drift(T + 1e-6, V, a, rc), 1e-4))
	check("drift speed: a*t while braking, V after", near(Shared.driftSpeed(1, V, a, rc), 12) and near(Shared.driftSpeed(4, V, a, rc), 35))
	check("reaches the 700-stud despawn at t = 21.46 s", Shared.drift(21.4, V, a, rc) < 700 and Shared.drift(21.5, V, a, rc) > 700)

	local b1, b2 = Config.Topple[1], Config.Topple[2]
	local function topple(tt, bi, er, ey, es)
		local r, y, s = Shared.topple(tt, Config.Topple[bi])
		check(("topple body %d at t=%.3f: roll %.2f yaw %.2f sink %.3f"):format(bi, tt, r, y, s),
			near(r, er, 1e-6) and near(y, ey, 1e-6) and near(s, es, 1e-6), ("expected %g %g %g"):format(er, ey, es))
	end
	-- key times from the spec: waits its delay, half way through the roll (QuadIn -> a quarter), impact,
	-- top of the bounce, settled, later
	for bi, sb in S.topple.bodies do
		local d, rt, bt = sb.delay, sb.roll_time, sb.bounce_time
		topple(d, bi, 0, 0, 0)
		topple(d + rt / 2, bi, sb.roll / 4, sb.yaw / 4, sb.sink / 4)
		topple(d + rt, bi, sb.roll, sb.yaw, sb.sink)
		topple(d + rt + bt / 2, bi, (sb.roll + sb.bounce[2]) / 2 + sb.bounce[1] - sb.bounce[2], sb.yaw, sb.sink)
		topple(d + rt + bt, bi, sb.bounce[2], sb.yaw, sb.sink)
		topple(d + rt + bt + 1, bi, sb.bounce[2], sb.yaw, sb.sink)
	end

	local function lost(stateTable, k)
		local bodies = Shared.lostHalves(stateTable, k)
		local out = {}
		for _, body in bodies do
			table.insert(out, table.concat(body, "+"))
		end
		return table.concat(out, " | ")
	end
	check("lost set, break 1: C1.Rear | C2 (both halves, one body)", lost({}, 1) == "C1.Rear | C2.Front+C2.Rear", lost({}, 1))
	check("lost set, break 2: C2.Rear", lost({}, 2) == "C2.Rear", lost({}, 2))
	check("lost set, 1 then 2: nothing more", lost({ [1] = true }, 2) == "", lost({ [1] = true }, 2))
	check("lost set, 2 then 1: C1.Rear | C2.Front", lost({ [2] = true }, 1) == "C1.Rear | C2.Front", lost({ [2] = true }, 1))
	check("lost set, same break twice: nothing", lost({ [1] = true }, 1) == "" and lost({ [2] = true }, 2) == "")
	local _, newState = Shared.lostHalves({}, 1)
	check("lostHalves returns the new state and leaves the input alone", newState[1] == true)

	local B = CFrame.new(10, 5, 20) * CFrame.Angles(0, 0.3, 0)
	local base = B * CFrame.new(0.5, 6, 15)
	local params = { V = V, brake = a, recoil = rc, pivot = Config.Pivot, topple = b1 }
	check("bodyCFrame at t <= 0 is the intact place", Shared.bodyCFrame(base, B, 1, 0, params) == base and Shared.bodyCFrame(base, B, 1, -0.2, params) == base)
	local r5 = B:ToObjectSpace(Shared.bodyCFrame(base, B, 1, 5, params))
	check("bodyCFrame t=5 right: lies on its right side (+X), slid back by drift(5)", r5.YVector.X > 0.98 and near(r5.Position.Z - 15, Shared.drift(5, V, a, rc), 1e-4),
		("up.X %.3f dz %.3f"):format(r5.YVector.X, r5.Position.Z - 15))
	local l5 = B:ToObjectSpace(Shared.bodyCFrame(base, B, -1, 5, params))
	check("bodyCFrame t=5 left: mirrors to -X", l5.YVector.X < -0.98 and near(l5.Position.Z, r5.Position.Z, 1e-4))
	local v1 = Shared.bodyVelocity(base, B, 1, 1, params)
	check("bodyVelocity along the train = drift speed (12 studs/s at t=1)", near(v1:Dot(B.ZVector), 12, 1e-3), v1:Dot(B.ZVector))

	local timeline = Shared.eventsTimeline(Config.Events, { V = V, brake = a, bodies = { b1, b2 } })
	local seq = {}
	for _, e in timeline do
		table.insert(seq, ("%s@%.2f"):format(e.id, e.t))
	end
	local want = "metal_tear@-0.25 split_explosion@0.00 glass_burst@0.00 torn_edge_smoke@0.05 wreck_scrape@0.30 debris_rain@0.80 topple_crash@1.50 topple_crash@2.00"
	check("events timeline (break 1, two bodies)", table.concat(seq, " ") == want, table.concat(seq, " "))
	local scrape
	for _, e in timeline do
		if e.id == "wreck_scrape" then
			scrape = e
		end
	end
	check("wreck_scrape ends at V/brake", scrape and near(scrape.t_end, T))
	check("side: left -1, right +1, random is seeded", Shared.side("left", 1) == -1 and Shared.side("right", 1) == 1
		and Shared.side("random", 42) == Shared.side("random", 42))
	local seen = {}
	for seed = 1, 200 do
		seen[Shared.side("random", seed)] = true
	end
	check("random side takes both values over seeds", seen[1] and seen[-1])
end)

---------------------------------------------------------------- the train: checker and setup, four placements

local function addFixtures(train, byName, cf)
	local fx = {}
	local B1 = cf * CFrame.new(H.origin(1))
	fx.attWorld = B1 * CFrame.new(0, 5, 10) -- behind the tear: must land on the rear piece
	fx.att = Instance.new("Attachment")
	fx.att.Name = "TestAtt"
	fx.att.CFrame = byName.Union19.CFrame:ToObjectSpace(fx.attWorld)
	fx.att.Parent = byName.Union19
	fx.light = Instance.new("PointLight")
	fx.light.Name = "TestLight"
	fx.light.Parent = byName.CurtainCorroded1
	fx.tex = Instance.new("Texture")
	fx.tex.Name = "TestTexture"
	fx.tex.Parent = byName.Part269
	byName.Union12:SetAttribute("Paint", "green")
	byName.Union12:AddTag("RR_TestTag")
	fx.weld = Instance.new("WeldConstraint")
	fx.weld.Name = "TestWeld"
	fx.weld.Part0 = byName.Union28
	fx.weld.Part1 = byName.Union22
	fx.weld.Parent = train.Body
	fx.script = Instance.new("Script")
	fx.script.Name = "TestScript"
	fx.script.Parent = train
	train.PrimaryPart = byName.Union28
	return fx
end

-- Box of an instance in frame B as {x0, x1, y0, y1, z0, z1}.
local function box(B, part)
	return H.boxInFrame(B, part)
end

-- Expected front/rear piece boxes of a CSG crosser: per cell column, front = [z0, min(z1, d)], rear = [max(z0, d), z1].
local function expectedPieces(b)
	local F = { math.huge, -math.huge, math.huge, -math.huge, math.huge, -math.huge }
	local R = table.clone(F)
	local function grow(t, x0, x1, y0, y1, z0, z1)
		t[1], t[2] = math.min(t[1], x0), math.max(t[2], x1)
		t[3], t[4] = math.min(t[3], y0), math.max(t[4], y1)
		t[5], t[6] = math.min(t[5], z0), math.max(t[6], z1)
	end
	for _, c in S.cells do
		local x0, x1 = math.max(b[1], c.X[1]), math.min(b[2], c.X[2])
		local y0, y1 = math.max(b[3], c.Y[1]), math.min(b[4], c.Y[2])
		if x1 > x0 and y1 > y0 then
			if b[5] < c.d then
				grow(F, x0, x1, y0, y1, b[5], math.min(b[6], c.d))
			end
			if b[6] > c.d then
				grow(R, x0, x1, y0, y1, math.max(b[5], c.d), b[6])
			end
		end
	end
	return F, R
end
local function sameBox(a, b, eps)
	for i = 1, 6 do
		if not near(a[i], b[i], eps or 1e-3) then
			return false
		end
	end
	return true
end

local SCENARIOS = {
	{ name = "base", cf = CFrame.new(), front = "min" },
	{ name = "moved (+500, +20, -300)", cf = CFrame.new(500, 20, -300), front = "min" },
	{ name = "moved + rotated 90 deg", cf = CFrame.new(500, 20, -300) * CFrame.Angles(0, math.rad(90), 0), front = "min" },
	{ name = "moved + rotated 180 deg", cf = CFrame.new(500, 20, -300) * CFrame.Angles(0, math.rad(180), 0), front = "max" },
}

for si, sc in SCENARIOS do
	section("train " .. sc.name .. " (FRONT_AT = " .. sc.front .. ")")
	guarded(sc.name, function()
		H.resetState()
		local game = H.newGame()
		local train, byName = H.buildTrain(game, sc.cf)
		local fx = addFixtures(train, byName, sc.cf)
		state.selection = { train }
		local groupCount = #H.groups()

		-- checker: read-only, finds the 20 designed crossers
		local before = H.fingerprint(game)
		local rep = H.load("RR_BreakChecker.lua", game, nil, { FRONT_AT = sc.front })
		check("checker is read-only", H.fingerprint(game) == before)
		check("checker: roof mode, 2 carriages", rep.mode == "roof" and #rep.carriages == 2)
		local total = 0
		for k = 1, 2 do
			local got = {}
			for _, c in rep.crossers[k] or {} do
				got[c.part:GetAttribute("ExportName")] = true
				total += 1
			end
			local want = setOf(S.expected_crossers_export[tostring(k)])
			check(("checker: carriage %d crossers == break_spec list (10)"):format(k), sameSet(got, want), names(got))
		end
		check("checker: 20 crossers in all", total == 20, total)
		check("checker: gangway found (Union22)", #rep.gangway == 1 and rep.gangway[1]:GetAttribute("ExportName") == "Union22")
		local teeth = 0
		for k = 1, 2 do
			for _, e in rep.band[k] or {} do
				if e.tooth then
					teeth += 1
				end
			end
		end
		check("checker: band listed, no part inside a tooth", #(rep.band[1] or {}) > 0 and teeth == 0, ("band %d + %d"):format(#(rep.band[1] or {}), #(rep.band[2] or {})))
		if si == 1 then
			H.writeOut("checker_base.txt", rep.lines)
		end

		-- setup dry run: the plan, nothing changes
		before = H.fingerprint(game)
		local dry = H.load("RR_TrainSplit_Setup.lua", game, nil, { FRONT_AT = sc.front })
		check("setup DRY_RUN: plan made, nothing changed", dry.ok and dry.dryRun and H.fingerprint(game) == before and #state.recordings == 0)
		local P = dry.plan
		local planned, methodsOk = {}, true
		for _, cr in P.crossers do
			local n = cr.part:GetAttribute("ExportName")
			planned[n] = true
			local want = BLOCKS[n] and "slice" or "csg"
			methodsOk = methodsOk and cr.method == want and EXPECTED[n] == cr.k
			if BLOCKS[n] then
				methodsOk = methodsOk and #cr.pieces == 12 and cr.front == 6 and cr.rear == 6
			end
		end
		check("setup DRY_RUN: 20 crossers = break_spec, blocks sliced 6+6, rest CSG", sameSet(planned, EXPECTED) and #P.crossers == 20 and methodsOk, names(planned))
		local dryText = table.concat(dry.lines, "\n")
		check("setup DRY_RUN report is readable (frames, halves, crossers, notes)", dryText:find("Break 1 frame") and dryText:find("Carriage1.FrontHalf")
			and dryText:find("Crossers %(20%)") and dryText:find("Gangway") and dryText:find("TestWeld") ~= nil)
		if si == 1 then
			H.writeOut("setup_dryrun_base.txt", dry.lines)
		end

		-- setup apply
		local res = H.load("RR_TrainSplit_Setup.lua", game, nil, { FRONT_AT = sc.front, DRY_RUN = false })
		check("setup apply ran", res.ok, res.error or res.refused)
		if not res.ok then
			return
		end
		local rec = state.recordings
		check("undo: one ChangeHistory recording, committed", #rec == 2 and rec[1].begin == "RR_TrainSplit_Setup" and rec[2].op == roblox.Enum.FinishRecordingOperation.Commit)
		check("CSG: 18 crossers x 2 SubtractAsync calls", state.csgCalls == 36, state.csgCalls)
		check("no CSG failures", #res.failures == 0)
		if si == 1 then
			H.writeOut("setup_apply_base.txt", res.lines)
		end

		-- structure
		local structOk = true
		for k = 1, 2 do
			local car = train:FindFirstChild("Carriage" .. k)
			for _, side in { "FrontHalf", "RearHalf" } do
				local half = car and car:FindFirstChild(side)
				local root = half and half.PrimaryPart
				structOk = structOk and half ~= nil and half:IsA("Model") and root ~= nil and root.Name == "Root" and root.Anchored
					and root.Transparency == 1 and not root.CanCollide and root.Size == Vector3.new(1, 1, 1)
			end
		end
		check("Train/Carriage1..2/{FrontHalf,RearHalf} with an invisible anchored 1x1x1 Root as PrimaryPart", structOk)

		-- break records
		local breaks = train:FindFirstChild("RR_Breaks")
		local recOk = breaks ~= nil
		for k = 1, 2 do
			local r = breaks and breaks:FindFirstChild("Break" .. k)
			local B = r and r:GetAttribute("BreakCFrame")
			local want = sc.cf * CFrame.new(H.origin(k))
			recOk = recOk and r ~= nil and r:IsA("Configuration") and r:GetAttribute("Carriage") == k and r:GetAttribute("Intact") == true
				and r:GetAttribute("Version") == S.version and typeof(B) == "CFrame" and nearV(B.Position, want.Position, 0.01)
				and nearV(B.ZVector, sc.cf.ZVector, 1e-4) and nearV(B.YVector, Vector3.new(0, 1, 0), 1e-4)
				and r.KeptHalf.Value == train["Carriage" .. k].FrontHalf and r.LostHalf.Value == train["Carriage" .. k].RearHalf
		end
		check("RR_Breaks/Break1..2: Carriage, BreakCFrame (at the designed origin, Z = rear), Intact, Version, Kept/LostHalf", recOk)

		-- backups
		local backups = game:GetService("ServerStorage"):FindFirstChild("RR_Backups")
		local bk = backups and backups:GetChildren()[1]
		local copy = bk and bk:FindFirstChild("Train")
		local copyParts = 0
		for _, d in copy and copy:GetDescendants() or {} do
			if d:IsA("BasePart") then
				copyParts += 1
			end
		end
		local originals = {}
		for _, d in bk and bk.CutOriginals:GetChildren() or {} do
			originals[d:GetAttribute("ExportName")] = true
		end
		check("backup: full copy of the train (" .. groupCount .. " parts)", copyParts == groupCount, copyParts)
		check("backup: the 20 cut originals kept, never destroyed", sameSet(originals, EXPECTED), names(originals))

		-- every piece and part in the right half
		local map = H.byExportName(train)
		local wrong, counts = {}, {}
		for _, g in H.groups() do
			local k = EXPECTED[g.name]
			local list = map[g.name] or {}
			if k then
				local F, R = 0, 0
				for _, p in list do
					local half = H.halfOf(p, train)
					if half == ("C%d.Front"):format(k) then
						F += 1
					elseif half == ("C%d.Rear"):format(k) then
						R += 1
					else
						table.insert(wrong, g.name .. " piece in " .. tostring(half))
					end
				end
				local want = BLOCKS[g.name] and 6 or 1
				if F ~= want or R ~= want then
					table.insert(wrong, ("%s: %d front / %d rear pieces"):format(g.name, F, R))
				end
			else
				local ek, eh = H.expectedHalf(g)
				local want = ("C%d.%s"):format(ek, eh)
				local got = #list == 1 and H.halfOf(list[1], train) or ("%d copies"):format(#list)
				counts[want] = (counts[want] or 0) + 1
				if got ~= want then
					table.insert(wrong, ("%s in %s, expected %s"):format(g.name, tostring(got), want))
				end
			end
		end
		check("every other part in the right half", #wrong == 0, #wrong > 0 and table.concat(wrong, "; ", 1, math.min(#wrong, 6))
			or ("uncut: C1 front %d rear %d, C2 front %d rear %d"):format(counts["C1.Front"] or 0, counts["C1.Rear"] or 0, counts["C2.Front"] or 0, counts["C2.Rear"] or 0))
		check("setup report counts per half match", res.counts[1].Front == (counts["C1.Front"] or 0) + 9 + 6 and res.counts[2].Rear == (counts["C2.Rear"] or 0) + 9 + 6,
			("C1F %d C1R %d C2F %d C2R %d"):format(res.counts[1].Front, res.counts[1].Rear, res.counts[2].Front, res.counts[2].Rear))
		check("gangway (Union22) in " .. S.structure.gangway .. " (break_spec structure)", map.Union22 and H.halfOf(map.Union22[1], train) == "C2.Front")

		-- the cuts themselves
		local sliceOk, sliceDetail = true, nil
		for name, k in EXPECTED do
			if BLOCKS[name] then
				local B = train.RR_Breaks["Break" .. k]:GetAttribute("BreakCFrame")
				local original = bk.CutOriginals:FindFirstChild("Part")
				for _, d in bk.CutOriginals:GetChildren() do
					if d:GetAttribute("ExportName") == name then
						original = d
					end
				end
				local vol = 0
				for _, piece in map[name] do
					local b = box(B, piece)
					local cx, cy = (b[1] + b[2]) / 2, (b[3] + b[4]) / 2
					local d = H.dAt(cx, cy)
					local front = H.halfOf(piece, train):find("Front") ~= nil
					local okSide = front and b[6] <= d + 1e-4 or (not front and b[5] >= d - 1e-4)
					local cellOk = false
					for _, c in S.cells do
						if b[1] >= c.X[1] - 1e-4 and b[2] <= c.X[2] + 1e-4 and b[3] >= c.Y[1] - 1e-4 and b[4] <= c.Y[2] + 1e-4 then
							cellOk = true
						end
					end
					vol += piece.Size.X * piece.Size.Y * piece.Size.Z
					if not (okSide and cellOk and piece.ClassName == "Part") then
						sliceOk, sliceDetail = false, name .. " piece off its cell/side"
					end
				end
				local full = original.Size.X * original.Size.Y * original.Size.Z
				if not near(vol, full, 1e-6 * full) then
					sliceOk, sliceDetail = false, ("%s volume %.4f vs %.4f"):format(name, vol, full)
				end
			end
		end
		check("blocks Part269/Part409 sliced per cell: 12 exact boxes each, each inside one cell on its side, volume kept", sliceOk, sliceDetail)

		local csgOk, csgDetail = true, nil
		for _, d in bk.CutOriginals:GetChildren() do
			local name = d:GetAttribute("ExportName")
			local k = EXPECTED[name]
			if k and not BLOCKS[name] then
				local B = train.RR_Breaks["Break" .. k]:GetAttribute("BreakCFrame")
				local wantF, wantR = expectedPieces(box(B, d))
				for _, piece in map[name] do
					local front = H.halfOf(piece, train) == ("C%d.Front"):format(k)
					local want = front and wantF or wantR
					local same = piece.ClassName == "UnionOperation" and piece.Name == d.Name and piece.Color == d.Color
						and piece.Material == d.Material and piece.Anchored == d.Anchored
					if not (same and sameBox(box(B, piece), want)) then
						csgOk, csgDetail = false, ("%s %s piece"):format(name, front and "front" or "rear")
					end
				end
			end
		end
		check("CSG pieces: front = part minus rear cutters, rear = minus front cutters, looks copied (18 parts)", csgOk, csgDetail)

		-- builder hierarchy, children, references
		local h1 = train.Carriage1.FrontHalf
		check("builder's containers mirrored in the halves (Body Model, Interior Folder, Seats Model)", h1:FindFirstChild("Body") and h1.Body:IsA("Model")
			and h1:FindFirstChild("Interior") and h1.Interior:IsA("Folder") and h1.Interior:FindFirstChild("Seats") and h1.Interior.Seats:IsA("Model") ~= nil)
		check("emptied containers (Interior, Seats) moved to the backup; Body stays, it still holds TestWeld", train:FindFirstChild("Interior") == nil
			and train:FindFirstChild("Body") ~= nil and train.Body:FindFirstChild("TestWeld") == fx.weld and res.emptied == 2, res.emptied)
		local att = nil
		for _, d in train:GetDescendants() do
			if d.Name == "TestAtt" then
				att = d
			end
		end
		check("attachment re-homed by world position onto the rear piece", att and att.Parent:GetAttribute("ExportName") == "Union19"
			and H.halfOf(att, train) == "C1.Rear" and nearV((att.Parent.CFrame * att.CFrame).Position, fx.attWorld.Position, 1e-4))
		local light = nil
		for _, d in train:GetDescendants() do
			if d.Name == "TestLight" then
				light = d
			end
		end
		check("light re-homed onto the piece holding the part centre", light and light.Parent:GetAttribute("ExportName") == "CurtainCorroded1" and H.halfOf(light, train) == "C1.Rear")
		local texCount = 0
		for _, p in map.Part269 do
			if p:FindFirstChild("TestTexture") then
				texCount += 1
			end
		end
		check("texture copied onto every slice (12)", texCount == 12, texCount)
		local tagged = 0
		for _, p in map.Union12 do
			if p:GetAttribute("Paint") == "green" and p:HasTag("RR_TestTag") then
				tagged += 1
			end
		end
		check("attributes and CollectionService tags copied to both pieces", tagged == 2)
		local weldReported = false
		for _, j in res.joints do
			if j.inst == fx.weld and j.fields[1] == "Part0" then
				weldReported = true
			end
		end
		check("joint that referenced a cut original is reported", weldReported)
		check("scripts stay where they were", train:FindFirstChild("TestScript") == fx.script)
		check("train PrimaryPart (was the roof) now the roof's front piece", train.PrimaryPart and train.PrimaryPart:GetAttribute("ExportName") == "Union28"
			and H.halfOf(train.PrimaryPart, train) == "C1.Front")
		check("temporary cutters removed from the workspace", game.Workspace:FindFirstChild("RR_TmpCutters") == nil)

		-- afterwards
		local after = H.load("RR_BreakChecker.lua", game, nil, { FRONT_AT = sc.front })
		check("checker after the setup: every part in a half, on its side of the tear", after.mode == "split" and after.misplaced == 0 and after.outside == 0 and after.ok,
			("%s misplaced, %s outside"):format(tostring(after.misplaced), tostring(after.outside)))
		if si == 1 then
			H.writeOut("checker_after_setup_base.txt", after.lines)
		end
		local again = H.load("RR_TrainSplit_Setup.lua", game, nil, { FRONT_AT = sc.front, DRY_RUN = false })
		check("setup refuses to run twice when every part is in a half", again.refused ~= nil and again.refused:find("already set up") ~= nil)
	end)
end

---------------------------------------------------------------- refusals, fallback, CSG failure

section("refusals, plane fallback, CSG failure")
guarded("refusals", function()
	-- one carriage only
	H.resetState()
	local game = H.newGame()
	local train, byName = H.buildTrain(game, CFrame.new())
	for _, p in train:GetDescendants() do
		if p:IsA("BasePart") and p.CFrame.Position.Z > 116.6 then
			p.Parent = nil
		end
	end
	state.selection = { train }
	local r = H.load("RR_TrainSplit_Setup.lua", game, nil)
	check("setup refuses unless exactly 2 carriages (1 found)", r.refused ~= nil and r.refused:find("found 1 carriage") ~= nil, r.refused)

	-- no roof union: refused unless the plane fallback is allowed; checker falls back to a plane
	H.resetState()
	game = H.newGame()
	train, byName = H.buildTrain(game, CFrame.new())
	byName.Union28.Parent = nil
	byName.Union134.Parent = nil
	state.selection = { train }
	r = H.load("RR_TrainSplit_Setup.lua", game, nil)
	check("setup refuses a train with no roof union (plane fallback off)", r.refused ~= nil and r.refused:find("no roof union") ~= nil)
	local c = H.load("RR_BreakChecker.lua", game, nil, { PLANE_OFFSET = 3.31 })
	check("checker plane fallback: clusters 2 carriages, lists plane crossers", c.mode == "plane" and #c.carriages == 2 and #(c.crossers[1] or {}) > 0,
		("%d carriages, %d + %d crossers"):format(#c.carriages, #(c.crossers[1] or {}), #(c.crossers[2] or {})))
	r = H.load("RR_TrainSplit_Setup.lua", game, nil, { ALLOW_PLANE_FALLBACK = true, PLANE_OFFSET = 3.31 })
	check("setup plans a flat cut when ALLOW_PLANE_FALLBACK = true", r.ok and r.plan.found.mode == "plane" and #r.plan.crossers > 0, r.refused)

	-- a CSG failure is reported with what to do; the part stays whole, its cutters are kept
	H.resetState()
	game = H.newGame()
	train, byName = H.buildTrain(game, CFrame.new())
	state.selection = { train }
	state.failNames.CurtainCorroded2 = true
	r = H.load("RR_TrainSplit_Setup.lua", game, nil, { DRY_RUN = false })
	local f = r.failures and r.failures[1]
	local text = table.concat(r.lines or {}, "\n")
	check("CSG failure: setup finishes, 19 cut, 1 failure reported", r.ok and #r.cut == 19 and #r.failures == 1 and f.cr.part == byName.CurtainCorroded2)
	check("CSG failure: part kept whole where it was (Train.Interior), outside the halves, not in the backup",
		byName.CurtainCorroded2.Parent == train:FindFirstChild("Interior") and H.halfOf(byName.CurtainCorroded2, train) == nil)
	check("CSG failure: cutter boxes saved for a manual cut", f and f.cutters and #f.cutters:GetDescendants() > 2)
	check("CSG failure: the report says what to do (Separate, re-run; or cut by hand)", text:find("Model > Separate") ~= nil and text:find("simulated") ~= nil
		and text:find("by hand") ~= nil)
end)

section("wall-shell CSG failures: kept in place, Separate, re-run")
guarded("rerun", function()
	H.resetState()
	local game = H.newGame()
	local train, byName = H.buildTrain(game, CFrame.new())
	state.selection = { train }
	-- the two wall-shell unions per carriage have non-manifold export meshes: assume CSG refuses all four
	local shells = { "Union19", "Union61", "Union84", "Union86" }
	for _, n in shells do
		state.failNames[n] = true
	end
	local r1 = H.load("RR_TrainSplit_Setup.lua", game, nil, { DRY_RUN = false })
	check("first run finishes: 16 cut, the 4 wall shells fail and are listed", r1.ok and #r1.cut == 16 and #r1.failures == 4, r1.error)
	local inPlace = true
	for _, n in shells do
		inPlace = inPlace and byName[n].Parent == train:FindFirstChild("Body") and H.halfOf(byName[n], train) == nil
	end
	check("failed shells stay where they were (Train.Body), outside the halves, not in the backup", inPlace)
	local text = table.concat(r1.lines, "\n")
	check("the report prints the fallback: Separate, then run the setup again", text:find("Model > Separate") ~= nil and text:find("run this setup again") ~= nil)
	local chk = H.load("RR_BreakChecker.lua", game, nil)
	check("checker on the partly set-up train flags the 4 parts outside the halves", chk.mode == "split" and chk.outside == 4 and not chk.ok, chk.outside)
	local roots = { train.Carriage1.FrontHalf.PrimaryPart, train.Carriage2.RearHalf.PrimaryPart }

	-- Studio's Separate gives the union's own parts back in its parent: here two side walls and a roof strip
	-- (plain Blocks) and a negative window part per shell
	for _, n in shells do
		local u = byName[n]
		local cf, sz = u.CFrame, u.Size
		local function add(p, name, offset, size)
			p.Name = name
			p.Anchored = true
			p.Size = size
			p.CFrame = cf * CFrame.new(offset)
			p:SetAttribute("ExportName", n .. "/" .. name)
			p.Parent = train.Body
		end
		add(Instance.new("Part"), "Part", Vector3.new(-sz.X / 2 + 0.15, 0, 0), Vector3.new(0.3, sz.Y, sz.Z))
		add(Instance.new("Part"), "Part", Vector3.new(sz.X / 2 - 0.15, 0, 0), Vector3.new(0.3, sz.Y, sz.Z))
		add(Instance.new("Part"), "Part", Vector3.new(0, sz.Y / 2 - 0.2, 0), Vector3.new(sz.X - 0.6, 0.4, sz.Z))
		add(Instance.new("NegateOperation"), "NegativePart", Vector3.new(-sz.X / 2 + 0.15, 0, 0), Vector3.new(0.5, 4, 4))
		u.Parent = nil
	end
	state.failNames = {}
	local dry = H.load("RR_TrainSplit_Setup.lua", game, nil)
	local slices, skips, csg = 0, 0, 0
	for _, cr in dry.plan.crossers or {} do
		if cr.method == "slice" then
			slices += 1
		elseif cr.method == "skip" and cr.part:IsA("NegateOperation") then
			skips += 1
		elseif cr.method == "csg" then
			csg += 1
		end
	end
	check("re-run DRY_RUN plans only the 16 separated parts: 12 blocks sliced; negative parts never cut", dry.ok and dry.rerun and #dry.plan.parts == 16
		and slices == 12 and csg == 0 and skips >= 1 and table.concat(dry.lines, "\n"):find("negative part") ~= nil,
		("%d parts, %d slices, %d crossing negatives left whole"):format(#(dry.plan.parts or {}), slices, skips))
	local r2 = H.load("RR_TrainSplit_Setup.lua", game, nil, { DRY_RUN = false })
	check("re-run applies: 12 blocks sliced, no failures, nothing refused", r2.ok and r2.rerun and #r2.cut == 12 and #r2.failures == 0, r2.error or r2.refused)
	local oneEach = #train:GetChildren() == 3 and #train.RR_Breaks:GetChildren() == 2 and train.RR_Breaks.Break1:GetAttribute("Intact") == true
	local bodies = 0
	for _, c in train.Carriage1.FrontHalf:GetChildren() do
		if c.Name == "Body" then
			bodies += 1
		end
	end
	check("re-run reuses the halves, mirrors and records (no duplicates)", oneEach and bodies == 1 and train.Carriage1.FrontHalf.PrimaryPart == roots[1]
		and train.Carriage2.RearHalf.PrimaryPart == roots[2])
	local placed = true
	for _, p in H.byExportName(train) do
		for _, part in p do
			placed = placed and H.halfOf(part, train) ~= nil
		end
	end
	check("every part, piece and negative part now in a half", placed)
	local after = H.load("RR_BreakChecker.lua", game, nil)
	check("checker after the re-run: all in the halves, on the right side", after.ok and after.outside == 0 and after.misplaced == 0)
	local third = H.load("RR_TrainSplit_Setup.lua", game, nil, { DRY_RUN = false })
	check("a third run refuses: nothing left outside the halves", third.refused ~= nil and third.refused:find("every part sits in a half") ~= nil)
	check("each run left its own backup", #game:GetService("ServerStorage").RR_Backups:GetChildren() == 2)
end)

---------------------------------------------------------------- server runtime

local function splitWorld()
	H.resetState()
	local game = H.newGame()
	local train = H.buildTrain(game, CFrame.new())
	state.selection = { train }
	local res = H.load("RR_TrainSplit_Setup.lua", game, nil, { DRY_RUN = false })
	assert(res.ok, "setup failed: " .. tostring(res.error or res.refused))
	local rt = H.installRuntime(game)
	return { game = game, train = train, rt = rt, TS = rt.requireServer() }
end

local function partsIn(inst)
	local list = {}
	for _, d in inst:GetDescendants() do
		if d:IsA("BasePart") then
			table.insert(list, d)
		end
	end
	return list
end

local clientPayload, clientWorld

section("TrainSplit (server): break 2, then break 1")
guarded("server 2 then 1", function()
	local w = splitWorld()
	local TS, train, game = w.TS, w.train, w.game
	local Shared = w.rt.Shared
	local B2 = train.RR_Breaks.Break2:GetAttribute("BreakCFrame")
	local function fakePlayer(name, pos)
		local p = Instance.new("Player")
		p.Name = name
		local char = Instance.new("Model")
		char.Name = name
		local hrp = Instance.new("Part")
		hrp.Name = "HumanoidRootPart"
		hrp.CFrame = CFrame.new(pos)
		hrp.Parent = char
		char.Parent = game.Workspace
		p.Character = char
		return p
	end
	local rider = fakePlayer("Rider", (B2 * CFrame.new(0, 3, 10)).Position)
	local stayer = fakePlayer("Stayer", (B2 * CFrame.new(0, 3, -10)).Position)
	state.players = { rider, stayer }
	local snapped, despawned = {}, {}
	TS.Snapped.Event:Connect(function(t, k, result)
		table.insert(snapped, { t = t, k = k, result = result })
	end)
	TS.Despawned.Event:Connect(function(t, k, model)
		table.insert(despawned, model)
	end)
	check("remote RR_TrainSplitFX exists (server -> clients)", game.ReplicatedStorage:FindFirstChild("RR_TrainSplitFX") and game.ReplicatedStorage.RR_TrainSplitFX:IsA("RemoteEvent"))
	check("GetBreaks / IsIntact before any snap", #TS.GetBreaks(train) == 2 and TS.IsIntact(train, 1) and TS.IsIntact(train, 2))

	local lostHalf = train.RR_Breaks.Break2.LostHalf.Value
	local lostParts = partsIn(lostHalf)
	local result = TS.SplitAt(train, 2, { seed = 7 })
	local body = result.bodies[1]
	check("SplitAt(2): one body holding Carriage2.RearHalf, in workspace.RR_Wrecks", #result.bodies == 1 and lostHalf.Parent == body
		and body.Parent == game.Workspace:FindFirstChild("RR_Wrecks"))
	local root = body.PrimaryPart
	local welds, anchoredLeft = 0, 0
	for _, p in lostParts do
		if p.Anchored then
			anchoredLeft += 1
		end
	end
	for _, d in root:GetChildren() do
		if d:IsA("WeldConstraint") and d.Part0 == root then
			welds += 1
		end
	end
	check("body parts welded to the anchored root and unanchored", root.Anchored and anchoredLeft == 0 and welds == #lostParts, ("%d welds, %d parts"):format(welds, #lostParts))
	check("riders: the player on the lost half, not the one on the kept half", #result.riders == 1 and result.riders[1] == rider)
	check("break 2 recorded as snapped; break 1 still intact", not TS.IsIntact(train, 2) and TS.IsIntact(train, 1) and train.RR_Breaks.Break2:GetAttribute("SnapTime") ~= nil)
	local payload = state.fired[1]
	check("FireAllClients once: k, t0 = server time + lead, breakCF, bodies, params, seed", #state.fired == 1 and payload.k == 2 and near(payload.t0, 1000.25)
		and payload.breakCF == B2 and payload.bodies[1].root == root and payload.params.V == 35 and payload.seed == 7
		and payload.side == Shared.side("random", 7) and payload.kept == train.Carriage2.FrontHalf.PrimaryPart)
	check("Snapped fired with the result", #snapped == 1 and snapped[1].k == 2 and snapped[1].result == result)

	local hb = H.signal(game:GetService("RunService"), "Heartbeat")
	local base = payload.bodies[1].base
	local params = { V = 35, brake = 12, recoil = w.rt.Config.Recoil, pivot = w.rt.Config.Pivot, topple = w.rt.Config.Topple[1] }
	state.clock = payload.t0 - 0.1
	hb:Fire(1 / 60)
	check("before the snap moment the wreck holds still", root.CFrame == base)
	state.clock = payload.t0 + 1
	hb:Fire(1 / 60)
	local want = Shared.bodyCFrame(base, B2, payload.side, 1, params)
	check("Heartbeat drives root.CFrame from TrainSplitShared", nearV(root.CFrame.Position, want.Position, 1e-4) and nearV(root.CFrame.YVector, want.YVector, 1e-4))
	check("root.AssemblyLinearVelocity carries riders (12 studs/s back at t=1)", near(root.AssemblyLinearVelocity:Dot(B2.ZVector), 12, 0.01))
	state.clock = payload.t0 + 20
	hb:Fire(1 / 60)
	check("still there at t=20 s (under 700 studs)", body.Parent ~= nil and #despawned == 0)
	state.clock = payload.t0 + 22
	hb:Fire(1 / 60)
	task.wait()
	check("despawned past 700 studs: Despawned fired, wreck destroyed", #despawned == 1 and despawned[1] == body and body.Parent == nil)

	local again = TS.SplitAt(train, 2)
	check("SplitAt(2) again is a no-op", #again.bodies == 0 and #state.fired == 1)
	local keptC2 = train.RR_Breaks.Break2.KeptHalf.Value
	local function gangwayIn(root)
		for _, p in partsIn(root) do
			if p:GetAttribute("ExportName") == "Union22" then
				return true
			end
		end
		return false
	end
	check("break 2 keeps the gangway (it belongs to Carriage2.FrontHalf)", gangwayIn(keptC2) and keptC2:IsDescendantOf(train))
	local r1 = TS.SplitAt(train, 1, { seed = 3 })
	check("then SplitAt(1) loses only C1.Rear + C2.Front, as two bodies", #r1.bodies == 2 and train.RR_Breaks.Break1.LostHalf.Value.Parent == r1.bodies[1]
		and keptC2.Parent == r1.bodies[2])
	check("break 1 then takes the gangway away with Carriage2's front half", gangwayIn(r1.bodies[2]) and not gangwayIn(r1.bodies[1]))
	local p2 = state.fired[2]
	check("payload for break 1 carries both topple bodies", p2 and #p2.bodies == 2 and p2.bodies[1].topple.delay == 0.45 and p2.bodies[2].topple.delay == 0.8)
	check("server never listens to clients (no OnServerEvent)", state.onServerEventUsed == nil)
end)

section("TrainSplit (server): break 1 first")
guarded("server 1 first", function()
	local w = splitWorld()
	local TS, train = w.TS, w.train
	train:SetAttribute("Speed", 20)
	local keptPart, lostPart
	for _, p in partsIn(train.RR_Breaks.Break1.KeptHalf.Value) do
		if p.Name ~= "Root" then
			keptPart = p
		end
	end
	for _, p in partsIn(train.RR_Breaks.Break1.LostHalf.Value) do
		if p.Name ~= "Root" then
			lostPart = p
		end
	end
	local weld = Instance.new("WeldConstraint")
	weld.Part0 = lostPart
	weld.Part1 = keptPart
	weld.Parent = lostPart
	table.insert(state.joints, weld)
	local c2Front, c2Rear = train.RR_Breaks.Break2.KeptHalf.Value, train.RR_Breaks.Break2.LostHalf.Value
	local r = TS.SplitAt(train, 1, { seed = 11 })
	check("SplitAt(1): C1.Rear alone, then both C2 halves together", #r.bodies == 2 and train.RR_Breaks.Break1.LostHalf.Value.Parent == r.bodies[1]
		and c2Front.Parent == r.bodies[2] and c2Rear.Parent == r.bodies[2])
	local gangwayWith = nil
	for i, body in r.bodies do
		for _, p in partsIn(body) do
			if p:GetAttribute("ExportName") == "Union22" then
				gangwayWith = i
			end
		end
	end
	check("break 1 loses the gangway, with Carriage2 (body 2)", gangwayWith == 2)
	check("break 2 marked Detached, no longer splittable", train.RR_Breaks.Break2:GetAttribute("Detached") == true and not TS.IsIntact(train, 2))
	check("train Speed attribute drives the motion (V = 20)", state.fired[1].params.V == 20)
	check("a joint from the wreck to the kept train is switched off", weld.Enabled == false)
	local r2 = TS.SplitAt(train, 2)
	check("SplitAt(2) after 1 is a no-op", #r2.bodies == 0 and #state.fired == 1)
	clientPayload, clientWorld = state.fired[1], w
end)

---------------------------------------------------------------- client

section("TrainSplitClient: fx through RR_VFX, sounds, shake, smoothing")
guarded("client", function()
	assert(clientPayload, "no payload from the server test")
	local w, payload = clientWorld, clientPayload
	local game, Shared, Config = w.game, w.rt.Shared, w.rt.Config
	local B = payload.breakCF
	local rs, players = game:GetService("ReplicatedStorage"), game:GetService("Players")
	state.isServer = false
	local viewer = Instance.new("Player")
	viewer.Name = "Viewer"
	viewer.Parent = players
	players.LocalPlayer = viewer
	local cam = Instance.new("Camera")
	cam.CFrame = B * CFrame.new(20, 8, -25)
	cam.Parent = game.Workspace
	game.Workspace.CurrentCamera = cam
	for key, def in Config.Sounds do
		def.SoundId = "rbxassetid://" .. key -- test ids so the sound path runs
	end
	local log = {}
	local function worldCF(anchor)
		return anchor:IsA("Attachment") and anchor.Parent.CFrame * anchor.CFrame or anchor.CFrame
	end
	local fakeVfx = {
		burst = function(anchor, name)
			table.insert(log, { op = "burst", name = name, cf = worldCF(anchor), parent = anchor.Parent, t = state.clock - payload.t0 })
			return { name = name }
		end,
		attach = function(anchor, name)
			local h = { name = name }
			table.insert(log, { op = "attach", name = name, cf = worldCF(anchor), parent = anchor.Parent, h = h, t = state.clock - payload.t0 })
			return h
		end,
		setIntensity = function(h, k)
			table.insert(log, { op = "setIntensity", h = h, k = k, t = state.clock - payload.t0 })
		end,
		detach = function(h)
			table.insert(log, { op = "detach", h = h, t = state.clock - payload.t0 })
		end,
		setActive = function()
			table.insert(log, { op = "setActive" })
		end,
	}
	local rrfx = Instance.new("Folder")
	rrfx.Name = "RRFX" -- where the fx README installs RR_VFX
	rrfx.Parent = rs
	H.module(rrfx, "RR_VFX", fakeVfx)
	local ls = Instance.new("LocalScript")
	ls.Parent = game:GetService("StarterPlayer")
	H.load("TrainSplitClient.lua", game, ls)
	local remote = rs.RR_TrainSplitFX
	check("client listens on RR_TrainSplitFX", H.signal(remote, "OnClientEvent"):count() == 1)
	local cam0 = cam.CFrame
	H.signal(remote, "OnClientEvent"):Fire(payload)
	local shook = false
	local lastT
	for i = 0, 26 * 30 do
		state.clock = payload.t0 - 0.3 + i / 30
		lastT = state.clock - payload.t0
		local fn = state.renderSteps.RR_TrainSplit
		if fn then
			fn()
		end
		if lastT > 0 and lastT < 0.5 and cam.CFrame ~= cam0 then
			shook = true
		end
	end

	local function find(op, name)
		local list = {}
		for _, e in log do
			if e.op == op and (name == nil or e.name == name) then
				table.insert(list, e)
			end
		end
		return list
	end
	local function frameIs(cf, x, y, z)
		return nearV(cf.XVector, x, 1e-3) and nearV(cf.YVector, y, 1e-3) and nearV(cf.ZVector, z, 1e-3)
	end
	local fwd, up, right = -B.ZVector, B.YVector, B.XVector
	local core = find("burst", "split_explosion")
	check("split_explosion: one VFX.burst at t=0 on SplitCore (0,5,0), anchor X forward / Y up / Z right, on a static part", #core == 1
		and near(core[1].t, 0, 1 / 30) and nearV(core[1].cf.Position, (B * CFrame.new(0, 5, 0)).Position, 1e-3)
		and frameIs(core[1].cf, fwd, up, right) and core[1].parent:IsA("BasePart"))
	local glass = find("burst", "glass_burst")
	local glassOk = #glass == 2
	for _, e in glass do
		local p = B:PointToObjectSpace(e.cf.Position)
		glassOk = glassOk and near(math.abs(p.X), 9.75, 1e-3) and near(p.Y, 6.6, 1e-3) and near(p.Z, -4.5, 1e-3)
			and nearV(e.cf.ZVector, p.X > 0 and right or -right, 1e-3) and near(e.t, 0, 1 / 30)
	end
	check("glass_burst: SplitGlassL/R on the kept half's pane nearest the break, Z pointing out", glassOk)
	local edge = find("attach", "torn_edge_smoke")
	check("torn_edge_smoke: one VFX.attach at t=0.05 on TornEdge (on the roof tooth) on the kept half", #edge == 1 and near(edge[1].t, 0.05, 1 / 30)
		and edge[1].parent == payload.kept and nearV(edge[1].cf.Position, (B * CFrame.new(Config.Anchors.torn_edge)).Position, 1e-3)
		and frameIs(edge[1].cf, fwd, up, right))
	local fade, gone = find("setIntensity"), find("detach")
	check("torn edge fades by setIntensity(h, 0) at +20 s and detaches at +23.5 s", #fade == 1 and fade[1].h == edge[1].h and fade[1].k == 0
		and near(fade[1].t, 20.05, 1 / 30) and #gone == 1 and gone[1].h == edge[1].h and near(gone[1].t, 23.55, 1 / 30))
	check("never VFX.setActive (it would stop the other break's smoke)", #find("setActive") == 0)
	local dust = find("burst", "topple_dust")
	local dustOk = #dust == 2
	for i, e in dust do
		local p = B:PointToObjectSpace(e.cf.Position)
		dustOk = dustOk and near(p.X, payload.side * 11.7, 1e-3) and near(p.Y, -8.6, 1e-3) and frameIs(e.cf, fwd, up, right)
			and near(e.t, i == 1 and 1.5 or 2.0, 1 / 30) and e.parent:IsA("Terrain")
	end
	check("topple_dust: WreckDust on the ground at the track-side edge when each body lands (1.5 s, 2.0 s)", dustOk)

	local played = {}
	for _, p in state.played do
		played[p.name] = played[p.name] or {}
		table.insert(played[p.name], p)
	end
	local function n(key)
		return played[key] and #played[key] or 0
	end
	check("sounds: tear, explosion (3D + 2D), glass x2, scrape, debris, crash x2", n("RR_metal_tear") == 1 and n("RR_split_explosion") == 2 and n("RR_split_glass") == 2
		and n("RR_wreck_scrape") == 1 and n("RR_debris_rain") == 1 and n("RR_topple_crash") == 2)
	check("metal_tear starts 0.25 s before the snap", n("RR_metal_tear") == 1 and near(played.RR_metal_tear[1].at - payload.t0, -0.25, 1 / 30))
	local flat = 0
	for _, p in played.RR_split_explosion or {} do
		if p.parent == game:GetService("SoundService") then
			flat += 1
		end
	end
	check("split_explosion has a flat train-wide layer in SoundService", flat == 1)
	check("split_glass plays once per side, 0.1 s apart", n("RR_split_glass") == 2 and near(played.RR_split_glass[2].at - played.RR_split_glass[1].at, 0.1, 1 / 30))
	local scrape = played.RR_wreck_scrape and played.RR_wreck_scrape[1]
	local stopT = 20 / 12
	check("wreck_scrape fitted to the slide at Speed 20 and faded out at V/brake", scrape and scrape.speed >= 1.25 * 0.95 - 1e-6 and scrape.speed <= 1.25 * 1.05 + 1e-6
		and state.stopped[scrape.sound] and state.stopped[scrape.sound] - payload.t0 <= stopT + 0.25, scrape and scrape.speed)
	local crash = played.RR_topple_crash
	check("second topple_crash (carriage 2) pitched down x0.94", crash and #crash == 2 and crash[2].speed <= 1.06 * 0.94 + 1e-6 and crash[2].speed >= 0.92 * 0.94 - 1e-6)
	check("camera shakes on the explosion (camera 32 studs away)", game.Workspace.CurrentCamera == cam and shook)
	local smoothOk = true
	for i, b in payload.bodies do
		local want = Shared.bodyCFrame(b.base, B, payload.side, lastT, { V = 20, brake = 12, recoil = Config.Recoil, pivot = Config.Pivot, topple = b.topple })
		smoothOk = smoothOk and nearV(b.root.CFrame.Position, want.Position, 1e-4)
	end
	check("each wreck root smoothed every frame from TrainSplitShared", smoothOk)

	-- again without RR_VFX, with reduce motion on: built-in emitters, no shake
	rrfx.Parent = nil
	H.resetSignal(remote, "OnClientEvent")
	state.renderSteps = {}
	state.emitted = {}
	viewer:SetAttribute(Config.ReduceMotionAttribute, true)
	local ls2 = Instance.new("LocalScript")
	ls2.Parent = game:GetService("StarterPlayer")
	H.load("TrainSplitClient.lua", game, ls2)
	local cam1 = cam.CFrame
	H.signal(remote, "OnClientEvent"):Fire(payload)
	for i = 0, 3 * 30 do
		state.clock = payload.t0 - 0.3 + i / 30
		local fn = state.renderSteps.RR_TrainSplit
		if fn then
			fn()
		end
	end
	local explosions = 0
	for _, d in game.Workspace:GetChildren() do
		if d:IsA("Explosion") then
			explosions += 1
		end
	end
	check("without RR_VFX: built-in fallback emitters and explosion play", #state.emitted >= 6 and explosions == 1, ("%d emits"):format(#state.emitted))
	check("reduce motion on: no camera shake", cam.CFrame == cam1)
	check("client warnings: none", #state.warnings == 0, table.concat(state.warnings, " | "))
end)

---------------------------------------------------------------- demo

section("TrainSplitDemo")
guarded("demo", function()
	local w = splitWorld()
	local sss = w.game:GetService("ServerScriptService")
	state.isStudio = false
	local s1 = Instance.new("Script")
	s1.Parent = sss
	H.load("TrainSplitDemo.server.lua", w.game, s1)
	check("demo does nothing outside Studio", H.signal(w.train, "Attr:RR_TestBreak"):count() == 0)
	state.isStudio = true
	local s2 = Instance.new("Script")
	s2.Parent = sss
	H.load("TrainSplitDemo.server.lua", w.game, s2)
	check("demo hooks the split train in Studio", H.signal(w.train, "Attr:RR_TestBreak"):count() == 1)
	w.train:SetAttribute("RR_TestBreak", 2)
	H.signal(w.train, "Attr:RR_TestBreak"):Fire()
	check("RR_TestBreak = 2 -> SplitAt(2)", not w.TS.IsIntact(w.train, 2) and w.TS.IsIntact(w.train, 1) and #state.fired == 1)
end)

print(("\n%d passed, %d failed"):format(passed, failed))
process.exit(failed > 0 and 1 or 0)
