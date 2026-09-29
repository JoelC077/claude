--[[
RR_BreakChecker  (Studio command bar, read-only)

Select the train Model in the Explorer, paste this whole script into the command bar, press Enter.
It changes nothing. It prints:
  - the carriages it found and each carriage's break frame,
  - every BasePart whose box crosses the jagged tear (these are what RR_TrainSplit_Setup will cut),
  - parts that sit inside the jagged band without crossing it (with their clearance to the tear),
  - a summary.
Studio names are generic ("Part", "Union"), so everything is found by geometry: each carriage's roof
union (about 19.48 x 3.59 x 62.34) fixes its break frame. With no such roof (another train) it clusters
the long parts along the train and checks one flat plane per carriage, PLANE_OFFSET studs from its centre.
After the setup has run it checks the halves instead: every part on its half's side of the tear, and nothing
left outside the halves (a crosser whose CSG failed stays outside until it is Separated and the setup re-run).
]]

local FRONT_AT = "min" -- the train's front is the "min" (lower) or "max" end of its long world axis
local MARGIN = 0.1 -- a box closer than this to the tear counts as crossing it
local PLANE_OFFSET = 0 -- plane fallback only: studs from the carriage centre toward the rear
local SHOW_BAND = true -- list the parts inside the jagged band that do not cross it

-- CORE BEGIN: break geometry, identical in RR_BreakChecker and RR_TrainSplit_Setup (the Lune suite checks it)
local SPEC_VERSION = "2.1.0"
local ROOF_SIG = { 3.59, 19.48, 62.34 } -- roof union size, smallest first (break_spec roof_signature)
local ROOF_TOL = 0.1 -- studs of slack per axis when matching a roof
local BREAK_DZ = 3.31 -- break plane = roof centre + 3.31 studs toward the rear
local FLOOR_DY = -12.258 -- frame origin height = the floor top, 12.258 below the roof centre
local ZEXT = 40 -- cutter reach along the carriage (a carriage spans -34.5 .. +27.9 from its break)
local LONG_PART = 0.6 -- plane fallback: parts this fraction of the longest one outline a carriage
local EXPECTED_CROSSERS = 10 -- per carriage in Joel's train (break_spec clearance check)

-- CELLS BEGIN (break_spec.json v2.1.0) {X0, X1, Y0, Y1, d, region}: inside a cell the tear is at Z = d.
-- Frame B: +X across (right when facing the front), +Y up from the floor top, +Z toward the rear.
local CELLS = {
	{ -14.0, -7.1, -12.0, 0.6, 0.6, "floor" },
	{ -7.1, -2.8, -12.0, 0.6, 2.4, "floor" },
	{ -2.8, 0.6, -12.0, 0.6, 0.9, "floor" },
	{ 0.6, 4.1, -12.0, 0.6, 3.6, "floor" },
	{ 4.1, 7.1, -12.0, 0.6, 1.5, "floor" },
	{ 7.1, 14.0, -12.0, 0.6, -0.3, "floor" },
	{ -14.0, -7.1, 0.6, 1.5, 0.7, "wall_W" },
	{ 7.1, 14.0, 0.6, 1.5, -0.6, "wall_E" },
	{ -14.0, -7.1, 1.5, 3.3, -0.4, "wall_W" },
	{ 7.1, 14.0, 1.5, 3.3, 0.5, "wall_E" },
	{ -14.0, -7.1, 3.3, 5.7, 0.9, "wall_W" },
	{ 7.1, 14.0, 3.3, 5.7, -0.2, "wall_E" },
	{ -14.0, -7.1, 5.7, 7.4, 0.1, "wall_W" },
	{ 7.1, 14.0, 5.7, 7.4, 0.8, "wall_E" },
	{ -14.0, -7.1, 7.4, 8.95, -0.8, "wall_W" },
	{ 7.1, 14.0, 7.4, 8.95, -0.5, "wall_E" },
	{ -14.0, -7.1, 8.95, 11.18, 0.4, "wall_W" },
	{ 7.1, 14.0, 8.95, 11.18, 0.2, "wall_E" },
	{ -7.1, 7.1, 0.6, 8.95, 0.2, "mid" },
	{ -7.1, -2.5, 8.95, 11.18, 0.3, "mid_pelmet" },
	{ -2.5, 2.5, 8.95, 11.18, -0.5, "mid_pelmet" },
	{ 2.5, 7.1, 8.95, 11.18, 0.25, "mid_pelmet" },
	{ -14.0, -7.1, 11.18, 18.0, 0.3, "roof" },
	{ -7.1, -4.6, 11.18, 18.0, -1.6, "roof" },
	{ -4.6, -1.9, 11.18, 18.0, -3.9, "roof" },
	{ -1.9, 0.9, 11.18, 18.0, -2.4, "roof" },
	{ 0.9, 3.7, 11.18, 18.0, -4.8, "roof" },
	{ 3.7, 7.1, 11.18, 18.0, -1.1, "roof" },
	{ 7.1, 14.0, 11.18, 18.0, 0.1, "roof" },
}
-- CELLS END

local Core = {}

function Core.v(v)
	return ("(%.2f, %.2f, %.2f)"):format(v.X, v.Y, v.Z)
end

function Core.size(v)
	return ("%.2f x %.2f x %.2f"):format(v.X, v.Y, v.Z)
end

function Core.baseParts(root)
	local list = {}
	for _, d in root:GetDescendants() do
		if d:IsA("BasePart") then
			table.insert(list, d)
		end
	end
	return list
end

-- A part inside another part travels with that part instead of being sorted on its own.
function Core.insidePart(part, root)
	local p = part.Parent
	while p and p ~= root do
		if p:IsA("BasePart") then
			return true
		end
		p = p.Parent
	end
	return false
end

-- Axis-aligned box of a part in frame F, from CFrame and Size only (works for any rotation).
function Core.boxIn(F, part)
	local rel = F:ToObjectSpace(part.CFrame)
	local px, py, pz, r00, r01, r02, r10, r11, r12, r20, r21, r22 = rel:GetComponents()
	local h = part.Size / 2
	local ex = math.abs(r00) * h.X + math.abs(r01) * h.Y + math.abs(r02) * h.Z
	local ey = math.abs(r10) * h.X + math.abs(r11) * h.Y + math.abs(r12) * h.Z
	local ez = math.abs(r20) * h.X + math.abs(r21) * h.Y + math.abs(r22) * h.Z
	return { x0 = px - ex, x1 = px + ex, y0 = py - ey, y1 = py + ey, z0 = pz - ez, z1 = pz + ez }
end

function Core.dAt(cells, X, Y)
	for _, c in cells do
		if X >= c[1] and X < c[2] and Y >= c[3] and Y < c[4] then
			return c[5]
		end
	end
	return nil
end

-- Cells whose X/Y footprint overlaps the box (eps widens the test).
function Core.touched(cells, b, eps)
	eps = eps or 0
	local list = {}
	for _, c in cells do
		if b.x1 > c[1] - eps and b.x0 < c[2] + eps and b.y1 > c[3] - eps and b.y0 < c[4] + eps then
			table.insert(list, c)
		end
	end
	return list
end

function Core.bounds(cells)
	local b = { x0 = math.huge, x1 = -math.huge, y0 = math.huge, y1 = -math.huge, dmin = math.huge, dmax = -math.huge }
	for _, c in cells do
		b.x0, b.x1 = math.min(b.x0, c[1]), math.max(b.x1, c[2])
		b.y0, b.y1 = math.min(b.y0, c[3]), math.max(b.y1, c[4])
		b.dmin, b.dmax = math.min(b.dmin, c[5]), math.max(b.dmax, c[5])
	end
	return b
end

-- Where a box sits against the tear: "front" | "rear" | "cross" (closer than margin counts as crossing),
-- the clearance to the tear, whether it sits in a tooth (between the plane Z = 0 and the tear, so it goes
-- with the half a flat cut would not give it) and whether it is beyond every cell.
function Core.classify(cells, b, margin)
	local front, rear, any, tooth = true, true, false, false
	local clearF, clearR = math.huge, math.huge
	for _, c in Core.touched(cells, b) do
		local d = c[5]
		any = true
		if b.z1 > d - margin then
			front = false
		end
		if b.z0 < d + margin then
			rear = false
		end
		clearF, clearR = math.min(clearF, d - b.z1), math.min(clearR, b.z0 - d)
		if b.z1 > math.min(0, d) and b.z0 < math.max(0, d) then
			tooth = true
		end
	end
	if not any then
		local zc = (b.z0 + b.z1) / 2
		return zc < 0 and "front" or "rear", math.abs(zc), false, true
	end
	if front then
		return "front", clearF, tooth, false
	elseif rear then
		return "rear", clearR, tooth, false
	end
	return "cross", 0, tooth, false
end

-- A plain Block Part whose axes line up with the frame: it can be sliced into exact boxes, no CSG.
function Core.isPlainBlock(part, F)
	if part.ClassName ~= "Part" or part.Shape ~= Enum.PartType.Block then
		return false
	end
	if part:FindFirstChildWhichIsA("DataModelMesh") then
		return false
	end
	local rel = F:ToObjectSpace(part.CFrame)
	for _, v in { rel.XVector, rel.YVector, rel.ZVector } do
		if math.max(math.abs(v.X), math.abs(v.Y), math.abs(v.Z)) < 0.9999 then
			return false
		end
	end
	return true
end

-- Per-cell boxes of a block (frame coordinates): the front piece of each cell ends at the tear, the rear starts there.
function Core.slices(cells, b)
	local out = {}
	for _, c in cells do
		local x0, x1 = math.max(b.x0, c[1]), math.min(b.x1, c[2])
		local y0, y1 = math.max(b.y0, c[3]), math.min(b.y1, c[4])
		if x1 - x0 > 1e-3 and y1 - y0 > 1e-3 then
			local zf, zr = math.min(b.z1, c[5]), math.max(b.z0, c[5])
			if zf - b.z0 > 1e-3 then
				table.insert(out, { side = "Front", cell = c, lo = Vector3.new(x0, y0, b.z0), hi = Vector3.new(x1, y1, zf) })
			end
			if b.z1 - zr > 1e-3 then
				table.insert(out, { side = "Rear", cell = c, lo = Vector3.new(x0, y0, zr), hi = Vector3.new(x1, y1, b.z1) })
			end
		end
	end
	return out
end

local function isRoof(part)
	local s = { part.Size.X, part.Size.Y, part.Size.Z }
	table.sort(s)
	for i = 1, 3 do
		if math.abs(s[i] - ROOF_SIG[i]) > ROOF_TOL then
			return false
		end
	end
	return true
end

-- The roof's long axis and its up axis (its thinnest dimension, turned to point up).
local function roofAxes(roof)
	local s, cf = roof.Size, roof.CFrame
	local dims, vecs = { s.X, s.Y, s.Z }, { cf.XVector, cf.YVector, cf.ZVector }
	local iLong, iUp = 1, 1
	for i = 2, 3 do
		if dims[i] > dims[iLong] then
			iLong = i
		end
		if dims[i] < dims[iUp] then
			iUp = i
		end
	end
	local up = vecs[iUp]
	if up.Y < 0 then
		up = -up
	end
	return vecs[iLong], up
end

-- Point an axis along the positive direction of its biggest world component, so "min"/"max" mean something.
local function canonical(v)
	local ax, ay, az = math.abs(v.X), math.abs(v.Y), math.abs(v.Z)
	local c = (ax >= ay and ax >= az) and v.X or (ay >= az and v.Y or v.Z)
	return c < 0 and -v or v
end

local function axisName(v)
	local ax, ay, az = math.abs(v.X), math.abs(v.Y), math.abs(v.Z)
	return (ax >= ay and ax >= az) and "X" or (ay >= az and "Y" or "Z")
end

local function frameFor(origin, rear, up)
	up = (up - rear * up:Dot(rear)).Unit
	return CFrame.fromMatrix(origin, up:Cross(rear), up, rear)
end

-- Each carriage's span along the train and the joins between neighbours (frame of carriage 1, Z = rear).
function Core.addSpans(found)
	local F = found.carriages[1].frame
	for _, car in found.carriages do
		local z = F:PointToObjectSpace(car.centre).Z
		car.span = { z - car.half, z + car.half }
	end
	found.joins = {}
	for i = 1, #found.carriages - 1 do
		local a, b = found.carriages[i].span[2], found.carriages[i + 1].span[1]
		found.joins[i] = { lo = math.min(a, b), hi = math.max(a, b), mid = (a + b) / 2 }
	end
end

-- No roof union: carriages are runs of long parts along the train; each gets one flat plane.
local function planeCarriages(parts, frontAt, planeOffset)
	local found = { mode = "plane", carriages = {}, roofs = {} }
	local longest, len = nil, 0
	for _, p in parts do
		local m = math.max(p.Size.X, p.Size.Y, p.Size.Z)
		if m > len then
			longest, len = p, m
		end
	end
	if not longest then
		return found
	end
	local s, cf = longest.Size, longest.CFrame
	local long = (s.X >= s.Y and s.X >= s.Z) and cf.XVector or (s.Y >= s.Z and cf.YVector or cf.ZVector)
	local L = canonical(long)
	local rear = frontAt == "max" and -L or L
	found.axis, found.axisName = rear, axisName(L)
	local F = frameFor(Vector3.zero, rear, Vector3.yAxis)
	local boxes, runs = {}, {}
	for i, p in parts do
		boxes[i] = Core.boxIn(F, p)
		if boxes[i].z1 - boxes[i].z0 >= LONG_PART * len then
			table.insert(runs, { boxes[i].z0, boxes[i].z1 })
		end
	end
	table.sort(runs, function(a, b)
		return a[1] < b[1]
	end)
	local clusters = {}
	for _, r in runs do
		local last = clusters[#clusters]
		if last and r[1] <= last[2] + 0.5 then
			last[2] = math.max(last[2], r[2])
		else
			table.insert(clusters, { r[1], r[2] })
		end
	end
	for i, cl in clusters do
		local x0, x1, y0, y1 = math.huge, -math.huge, math.huge, -math.huge
		for _, b in boxes do
			local zc = (b.z0 + b.z1) / 2
			if zc >= cl[1] and zc <= cl[2] then
				x0, x1 = math.min(x0, b.x0), math.max(x1, b.x1)
				y0, y1 = math.min(y0, b.y0), math.max(y1, b.y1)
			end
		end
		local mid = (cl[1] + cl[2]) / 2
		local xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
		local hw, hh = (x1 - x0) / 2 + 2, (y1 - y0) / 2 + 2
		table.insert(found.carriages, {
			index = i,
			frame = frameFor(F * Vector3.new(xc, yc, mid + planeOffset), rear, Vector3.yAxis),
			cells = { { -hw, hw, -hh, hh, 0, "plane" } },
			centre = F * Vector3.new(xc, yc, mid),
			half = (cl[2] - cl[1]) / 2,
			zext = (cl[2] - cl[1]) / 2 + math.abs(planeOffset) + 5,
		})
	end
	if #found.carriages > 0 then
		Core.addSpans(found)
	end
	return found
end

-- Carriages in train order (front first) with their break frames and cells.
-- Each carriage's roof union fixes its frame: B = roof centre + rear * BREAK_DZ + up * FLOOR_DY.
function Core.findCarriages(parts, frontAt, planeOffset)
	local roofs = {}
	for _, p in parts do
		if isRoof(p) then
			local dup = nil
			for i, r in roofs do
				if (r.CFrame.Position - p.CFrame.Position).Magnitude < 5 then
					dup = i
				end
			end
			if not dup then
				table.insert(roofs, p)
			elseif p:IsA("UnionOperation") and not roofs[dup]:IsA("UnionOperation") then
				roofs[dup] = p
			end
		end
	end
	if #roofs == 0 then
		return planeCarriages(parts, frontAt, planeOffset or 0)
	end
	local L = canonical((roofAxes(roofs[1])))
	local rear = frontAt == "max" and -L or L
	table.sort(roofs, function(a, b)
		return a.CFrame.Position:Dot(rear) < b.CFrame.Position:Dot(rear)
	end)
	local found = { mode = "roof", axis = rear, axisName = axisName(L), carriages = {}, roofs = roofs }
	for i, roof in roofs do
		local long, up = roofAxes(roof)
		local r = long:Dot(rear) >= 0 and long or -long
		local centre = roof.CFrame.Position
		table.insert(found.carriages, {
			index = i,
			roof = roof,
			frame = frameFor(centre + r * BREAK_DZ + up * FLOOR_DY, r, up),
			cells = CELLS,
			centre = centre,
			half = math.max(roof.Size.X, roof.Size.Y, roof.Size.Z) / 2,
			zext = ZEXT,
		})
	end
	Core.addSpans(found)
	return found
end

-- Which carriage and half a whole (uncut) part belongs to. Anything spanning or inside the gap between two
-- carriages (the gangway, built into the next carriage's front wall) joins the FRONT half of the carriage
-- behind (break_spec structure); the rest goes by its bbox centre against its carriage's tear.
function Core.assign(found, part)
	local b = Core.boxIn(found.carriages[1].frame, part)
	for j, jn in found.joins do
		if (b.z0 < jn.mid and b.z1 > jn.mid) or (b.z0 >= jn.lo - 0.05 and b.z1 <= jn.hi + 0.05) then
			return j + 1, "Front", true
		end
	end
	local zc, c = (b.z0 + b.z1) / 2, #found.carriages
	for j, jn in found.joins do
		if zc < jn.mid then
			c = j
			break
		end
	end
	local car = found.carriages[c]
	local p = car.frame:PointToObjectSpace(part.CFrame.Position)
	return c, p.Z < (Core.dAt(car.cells, p.X, p.Y) or 0) and "Front" or "Rear", false
end
-- CORE END

local lines = {}
local function say(fmt, ...)
	local s = select("#", ...) > 0 and fmt:format(...) or fmt
	table.insert(lines, s)
	print(s)
end

local function describe(part)
	return ("%-15s %s  size %s  at %s"):format(part.ClassName, part:GetFullName(), Core.size(part.Size), Core.v(part.CFrame.Position))
end

-- After the setup: every part in a half must sit on that half's side of its tear, and nothing may be left
-- outside the halves (a crosser the setup could not cut stays where it was until it is dealt with).
local function checkSplitTrain(train, report)
	say("Already split (RR_Breaks found): checking the halves against their tears.")
	local bad, halves = 0, {}
	for _, rec in train.RR_Breaks:GetChildren() do
		local B = rec:GetAttribute("BreakCFrame")
		local kept, lost = rec:FindFirstChild("KeptHalf"), rec:FindFirstChild("LostHalf")
		if typeof(B) == "CFrame" and kept and lost then
			local counts = {}
			for side, holder in { Front = kept, Rear = lost } do
				local half = holder.Value
				counts[side] = 0
				if half then
					table.insert(halves, half)
					for _, part in Core.baseParts(half) do
						if part.Name ~= "Root" then
							counts[side] += 1
							local p = B:PointToObjectSpace(part.CFrame.Position)
							local isFront = p.Z < (Core.dAt(CELLS, p.X, p.Y) or 0)
							-- the gangway sits far from the break on purpose
							if (side == "Front") ~= isFront and math.abs(p.Z) < 28 then
								bad += 1
								say("  wrong side? %s half of %s: %s", side, rec.Name, describe(part))
							end
						end
					end
				end
			end
			say("%s  Intact=%s  FrontHalf %d parts, RearHalf %d parts", rec.Name, tostring(rec:GetAttribute("Intact")), counts.Front, counts.Rear)
			report.halves[rec.Name] = counts
		else
			bad += 1
			say("  %s is incomplete (needs BreakCFrame, KeptHalf, LostHalf)", rec:GetFullName())
		end
	end
	local outside = {}
	for _, part in Core.baseParts(train) do
		local placed = part:IsDescendantOf(train.RR_Breaks) or Core.insidePart(part, train)
		for _, h in halves do
			placed = placed or part:IsDescendantOf(h)
		end
		if not placed then
			table.insert(outside, part)
			say("  outside the halves: %s", describe(part))
		end
	end
	if #outside > 0 then
		say("  %d part(s) sit outside the halves: stuck with the train when it snaps. If the setup could not cut one:", #outside)
		say("  select it, Model > Separate, then run RR_TrainSplit_Setup again (it only handles parts outside the halves).")
	end
	report.misplaced, report.outside = bad, #outside
	report.ok = bad == 0 and #outside == 0
	say("Summary: %s", report.ok and "every part sits in a half, on its side of the tear." or ("%d misplaced, %d outside the halves."):format(bad, #outside))
	return report
end

local function run()
	local report = { ok = false, mode = nil, carriages = {}, crossers = {}, band = {}, gangway = {}, halves = {}, lines = lines }
	local selection = game:GetService("Selection"):Get()
	local train = selection[1]
	if #selection ~= 1 or not train:IsA("Model") then
		say("RR_BreakChecker: select exactly one train Model in the Explorer, then run again.")
		return report
	end
	local parts = Core.baseParts(train)
	say("== RR_BreakChecker %s: %s (%d BaseParts) ==", SPEC_VERSION, train:GetFullName(), #parts)
	if train:FindFirstChild("RR_Breaks") then
		report.mode = "split"
		return checkSplitTrain(train, report)
	end

	local found = Core.findCarriages(parts, FRONT_AT, PLANE_OFFSET)
	report.mode = found.mode
	if #found.carriages == 0 then
		say("No carriages found: no roof union and no long parts. Is this the train Model?")
		return report
	end
	if found.mode == "roof" then
		say("Mode: roof unions -> jagged tear (%d cells, margin %.2f studs).", #CELLS, MARGIN)
	else
		say("Mode: no roof union of about 19.48 x 3.59 x 62.34 -> plane fallback: one flat cut per carriage, %.2f studs from its centre.", PLANE_OFFSET)
	end
	say("Front = the %s end of world %s (FRONT_AT = %q). If the train's front is the other end, set FRONT_AT = %q.",
		FRONT_AT, found.axisName, FRONT_AT, FRONT_AT == "min" and "max" or "min")

	local counts, bandCounts, teeth = {}, {}, 0
	for k, car in ipairs(found.carriages) do
		local F = car.frame
		local bounds = Core.bounds(car.cells)
		if car.roof then
			say("Carriage %d: roof %s at %s, size %s", k, car.roof:GetFullName(), Core.v(car.centre), Core.size(car.roof.Size))
		else
			say("Carriage %d: long parts from %.1f to %.1f along the train", k, car.span[1], car.span[2])
		end
		say("  Break %d frame: origin %s  right %s  up %s  rear %s", k, Core.v(F.Position), Core.v(F.XVector), Core.v(F.YVector), Core.v(F.ZVector))
		local crossers, band = {}, {}
		for _, part in parts do
			local b = Core.boxIn(F, part)
			if b.z1 > bounds.dmin - 8 and b.z0 < bounds.dmax + 8 then
				local side, clearance, tooth = Core.classify(car.cells, b, MARGIN)
				if side == "cross" then
					table.insert(crossers, { part = part, box = b })
				elseif b.z1 > bounds.dmin - MARGIN and b.z0 < bounds.dmax + MARGIN then
					table.insert(band, { part = part, side = side, clearance = clearance, tooth = tooth })
					if tooth then
						teeth += 1
					end
				end
			end
		end
		say("  Crossers (%d), cut by RR_TrainSplit_Setup:", #crossers)
		for _, c in crossers do
			local how = Core.isPlainBlock(c.part, F) and "slice per cell" or "CSG"
			say("    %s  [%d cell(s), %s]", describe(c.part), #Core.touched(car.cells, c.box), how)
		end
		table.sort(band, function(a, b)
			return a.clearance < b.clearance
		end)
		if SHOW_BAND then
			say("  In the jagged band (Z %.1f .. %.1f) without crossing (%d): half, clearance to the tear", bounds.dmin, bounds.dmax, #band)
			for _, e in band do
				say("    %-5s %5.2f  %s%s", e.side == "front" and "Front" or "Rear", e.clearance, describe(e.part), e.tooth and "  << inside a tooth: goes with the half a flat cut would not give it" or "")
			end
		end
		counts[k], bandCounts[k] = #crossers, #band
		report.carriages[k] = { frame = F, roof = car.roof, span = car.span }
		report.crossers[k] = crossers
		report.band[k] = band
	end

	for _, part in parts do
		if not Core.insidePart(part, train) and #found.joins > 0 then
			local c, half, gangway = Core.assign(found, part)
			if gangway then
				table.insert(report.gangway, part)
				say("Gangway between carriages -> Carriage%d.%sHalf: %s", c, half, describe(part))
			end
		end
	end

	local list = {}
	local matches = found.mode == "roof"
	for k, n in counts do
		list[k] = tostring(n)
		matches = matches and n == EXPECTED_CROSSERS
	end
	report.ok = true
	say("Summary: %d carriage(s); crossers %s; band %s; parts inside a tooth %d.", #found.carriages, table.concat(list, " + "),
		table.concat(bandCounts, " + "), teeth)
	if found.mode == "roof" then
		say(matches and "Crossers match the design (10 per carriage). Next: RR_TrainSplit_Setup with DRY_RUN = true."
			or "Crossers differ from the design (10 per carriage): check FRONT_AT and the lists above before the setup.")
	end
	if #found.carriages ~= 2 then
		say("Note: RR_TrainSplit_Setup handles exactly 2 carriages; it found %d.", #found.carriages)
	end
	return report
end

return run()
