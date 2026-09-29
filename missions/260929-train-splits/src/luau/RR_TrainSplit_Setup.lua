--[[
RR_TrainSplit_Setup  (Studio command bar)  v2.0.0

Restructures the train into carriage halves and cuts the parts that cross each carriage's jagged tear,
so the halves meet seamlessly until TrainSplit.SplitAt tears them apart in game.

1. Select the train Model in the Explorer (run RR_BreakChecker on it first).
2. Paste this whole script into the command bar with DRY_RUN = true and press Enter: it prints the plan
   (parts per half, every crosser and how it will be cut, anything unexpected) and changes nothing.
3. Set DRY_RUN = false and run it again. It saves an undo step, clones the train into
   ServerStorage.RR_Backups, builds Train/Carriage1..2/{FrontHalf, RearHalf} (each with an invisible
   anchored Root as PrimaryPart), moves every part into its half (the builder's folders and models are
   mirrored inside each half), cuts the crossers, writes Train/RR_Breaks and prints a report.
   Ctrl+Z undoes all of it. Nothing is destroyed: cut originals are moved into the backup folder.
It refuses to run twice (RR_Breaks exists) and unless it finds exactly 2 carriages.
Cutting: plain axis-aligned Block parts are sliced into exact per-cell boxes; everything else uses
part:SubtractAsync (front piece = part minus the REAR cutter boxes, rear piece = minus the FRONT ones).
]]

local DRY_RUN = true -- true: print the plan and change nothing; false: do it
local FRONT_AT = "min" -- the train's front is the "min" (lower) or "max" end of its long world axis
local MARGIN = 0.1 -- a box closer than this to the tear counts as crossing it (same as RR_BreakChecker)
local CUTTER_BRIDGE = 0.01 -- neighbouring cutter boxes overlap by this much where both remove material, so
                           -- float round-off between them cannot leave paper-thin slivers (0 = off)
local ALLOW_PLANE_FALLBACK = false -- no roof union found (another train): allow one flat cut per carriage
local PLANE_OFFSET = 0 -- plane fallback only: studs from the carriage centre toward the rear

-- CORE BEGIN: break geometry, identical in RR_BreakChecker and RR_TrainSplit_Setup (the Lune suite checks it)
local SPEC_VERSION = "2.0.0"
local ROOF_SIG = { 3.59, 19.48, 62.34 } -- roof union size, smallest first (break_spec roof_signature)
local ROOF_TOL = 0.1 -- studs of slack per axis when matching a roof
local BREAK_DZ = 3.31 -- break plane = roof centre + 3.31 studs toward the rear
local FLOOR_DY = -12.258 -- frame origin height = the floor top, 12.258 below the roof centre
local ZEXT = 40 -- cutter reach along the carriage (a carriage spans -34.5 .. +27.9 from its break)
local LONG_PART = 0.6 -- plane fallback: parts this fraction of the longest one outline a carriage
local EXPECTED_CROSSERS = 10 -- per carriage in Joel's train (break_spec clearance check)

-- CELLS BEGIN (break_spec.json v2.0.0) {X0, X1, Y0, Y1, d, region}: inside a cell the tear is at Z = d.
-- Frame B: +X across (right when facing the front), +Y up from the floor top, +Z toward the rear.
local CELLS = {
	{ -14.0, -6.2, -12.0, 0.4, 0.6, "floor" },
	{ -6.2, -2.8, -12.0, 0.4, 2.4, "floor" },
	{ -2.8, 0.6, -12.0, 0.4, 0.9, "floor" },
	{ 0.6, 4.1, -12.0, 0.4, 3.6, "floor" },
	{ 4.1, 7.5, -12.0, 0.4, 1.5, "floor" },
	{ 7.5, 14.0, -12.0, 0.4, -0.3, "floor" },
	{ -14.0, -7.5, 0.4, 1.5, 0.7, "wall_W" },
	{ 7.5, 14.0, 0.4, 1.5, -0.6, "wall_E" },
	{ -14.0, -7.5, 1.5, 3.3, -0.4, "wall_W" },
	{ 7.5, 14.0, 1.5, 3.3, 0.5, "wall_E" },
	{ -14.0, -7.5, 3.3, 5.7, 0.9, "wall_W" },
	{ 7.5, 14.0, 3.3, 5.7, -0.2, "wall_E" },
	{ -14.0, -7.5, 5.7, 7.4, 0.1, "wall_W" },
	{ 7.5, 14.0, 5.7, 7.4, 0.8, "wall_E" },
	{ -14.0, -7.5, 7.4, 9.1, -0.8, "wall_W" },
	{ 7.5, 14.0, 7.4, 9.1, -0.5, "wall_E" },
	{ -14.0, -7.5, 9.1, 10.4, 0.4, "wall_W" },
	{ 7.5, 14.0, 9.1, 10.4, 0.2, "wall_E" },
	{ -7.5, 7.5, 0.4, 9.1, 0.2, "mid" },
	{ -7.5, -2.5, 9.1, 10.4, 0.3, "mid_pelmet" },
	{ -2.5, 2.5, 9.1, 10.4, -0.5, "mid_pelmet" },
	{ 2.5, 7.5, 9.1, 10.4, 0.6, "mid_pelmet" },
	{ -14.0, -7.5, 10.4, 18.0, 0.3, "roof" },
	{ -7.5, -4.6, 10.4, 18.0, -1.6, "roof" },
	{ -4.6, -1.9, 10.4, 18.0, -3.9, "roof" },
	{ -1.9, 0.9, 10.4, 18.0, -2.2, "roof" },
	{ 0.9, 3.8, 10.4, 18.0, -4.8, "roof" },
	{ 3.8, 7.5, 10.4, 18.0, -1.1, "roof" },
	{ 7.5, 14.0, 10.4, 18.0, 0.1, "roof" },
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
local function addSpans(found)
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
		addSpans(found)
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
	addSpans(found)
	return found
end

-- Which carriage and half a whole (uncut) part belongs to. Anything spanning or inside the gap between two
-- carriages (the gangway) joins the rear half of the carriage in front; the rest goes by its bbox centre
-- against its carriage's tear.
function Core.assign(found, part)
	local b = Core.boxIn(found.carriages[1].frame, part)
	for j, jn in found.joins do
		if (b.z0 < jn.mid and b.z1 > jn.mid) or (b.z0 >= jn.lo - 0.05 and b.z1 <= jn.hi + 0.05) then
			return j, "Rear", true
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

local ServerStorage = game:GetService("ServerStorage")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local lines = {}
local function say(fmt, ...)
	local s = select("#", ...) > 0 and fmt:format(...) or fmt
	table.insert(lines, s)
	print(s)
end

local function describe(inst)
	local size = inst:IsA("BasePart") and ("  size %s  at %s"):format(Core.size(inst.Size), Core.v(inst.CFrame.Position)) or ""
	return ("%s %s%s"):format(inst.ClassName, inst:GetFullName(), size)
end

-- What a CSG piece takes over from its original, where the engine lets a script set it.
local LOOK = {
	"Color", "Material", "MaterialVariant", "Transparency", "Reflectance", "UsePartColor", "CastShadow",
	"CanCollide", "CanQuery", "CanTouch", "CollisionGroup", "Anchored", "Massless", "Locked",
	"CustomPhysicalProperties", "SmoothingAngle", "CollisionFidelity", "RenderFidelity",
}

local function copyLook(from, to)
	to.Name = from.Name
	for _, prop in LOOK do
		local okGet, value = pcall(function()
			return from[prop]
		end)
		if okGet then
			pcall(function()
				to[prop] = value
			end)
		end
	end
	for name, value in from:GetAttributes() do
		to:SetAttribute(name, value)
	end
	for _, tag in from:GetTags() do
		to:AddTag(tag)
	end
end

-- How a crosser's child is re-homed onto the pieces.
local function childRule(child)
	if child:IsA("Attachment") then
		return "position" -- keeps its world position, on the piece that holds it
	elseif child:IsA("Light") or child:IsA("ParticleEmitter") or child:IsA("Fire") or child:IsA("Smoke")
		or child:IsA("Sparkles") or child:IsA("Sound") then
		return "centre" -- emits from the part, so it goes with the piece holding the part's centre
	elseif child:IsA("Decal") or child:IsA("SurfaceAppearance") then
		return "copy" -- surface looks belong on every piece (Texture is a Decal too)
	end
	return "other"
end

local RULE_TEXT = {
	position = "by its world position",
	centre = "to the piece holding the part centre",
	copy = "copied onto every piece (check how it tiles)",
	other = "moved to the piece holding the part centre: check it",
}

---------------------------------------------------------------- plan (DRY_RUN and apply share it)

-- Cutter boxes for one side, in frame coordinates {x0, x1, y0, y1, z0, z1, name}. Each cell the part touches
-- gives a box from its tear to the far end (FRONT: -zext .. d, REAR: d .. zext). Thin bridges over the edges
-- two cells share, spanning only the Z range both remove, overlap the boxes so round-off leaves no sliver.
local function cutterSpecs(car, b, side)
	local cells = Core.touched(car.cells, b, 0.01)
	local function zRange(d)
		if side == "Front" then
			return -car.zext, d
		end
		return d, car.zext
	end
	local specs = {}
	for _, c in cells do
		local z0, z1 = zRange(c[5])
		table.insert(specs, { c[1], c[2], c[3], c[4], z0, z1, c[6] })
	end
	local o = CUTTER_BRIDGE
	if o > 0 then
		for i = 1, #cells - 1 do
			for j = i + 1, #cells do
				local z0, z1 = zRange(side == "Front" and math.min(cells[i][5], cells[j][5]) or math.max(cells[i][5], cells[j][5]))
				for _, pq in { { cells[i], cells[j] }, { cells[j], cells[i] } } do
					local p, q = pq[1], pq[2]
					local bridge
					if math.abs(p[2] - q[1]) < 1e-6 and math.min(p[4], q[4]) - math.max(p[3], q[3]) > 1e-6 then
						bridge = { p[2] - o, p[2] + o, math.max(p[3], q[3]) - o, math.min(p[4], q[4]) + o, z0, z1, "bridge" }
					elseif math.abs(p[4] - q[3]) < 1e-6 and math.min(p[2], q[2]) - math.max(p[1], q[1]) > 1e-6 then
						bridge = { math.max(p[1], q[1]) - o, math.min(p[2], q[2]) + o, p[4] - o, p[4] + o, z0, z1, "bridge" }
					end
					if bridge and z1 - z0 > 1e-6 and bridge[2] > b.x0 and bridge[1] < b.x1 and bridge[4] > b.y0 and bridge[3] < b.y1 then
						table.insert(specs, bridge)
					end
				end
			end
		end
	end
	return specs
end

local function planCut(found, part, k, box)
	local car = found.carriages[k]
	local cr = { part = part, k = k, box = box, notes = {}, front = 0, rear = 0, children = part:GetChildren() }
	local cb = Core.bounds(car.cells)
	cr.touched = Core.touched(car.cells, box, 0.01)
	if box.z0 < -car.zext or box.z1 > car.zext then
		cr.method = "skip"
		cr.why = ("it reaches %.1f studs from the break, past the cutters' %.0f"):format(math.max(-box.z0, box.z1), car.zext)
	elseif box.x0 < cb.x0 or box.x1 > cb.x1 or box.y0 < cb.y0 or box.y1 > cb.y1 then
		cr.method = "skip"
		cr.why = "it sticks out past the tear cells (wider or taller than the carriage)"
	elseif Core.isPlainBlock(part, car.frame) then
		cr.method = "slice"
		cr.pieces = Core.slices(car.cells, box)
		local vol = 0
		for _, s in cr.pieces do
			local e = s.hi - s.lo
			vol += e.X * e.Y * e.Z
			if s.side == "Front" then
				cr.front += 1
			else
				cr.rear += 1
			end
		end
		local full = (box.x1 - box.x0) * (box.y1 - box.y0) * (box.z1 - box.z0)
		if math.abs(vol - full) > 1e-4 * full then
			table.insert(cr.notes, ("the slices hold %.2f%% of the block (slivers under 0.001 stud are dropped)"):format(100 * vol / full))
		end
	else
		cr.method = "csg"
		cr.front, cr.rear = 1, 1
		cr.boxes = { Front = #cutterSpecs(car, box, "Front"), Rear = #cutterSpecs(car, box, "Rear") }
		if part:IsA("MeshPart") then
			table.insert(cr.notes, "MeshPart: if this Studio refuses CSG on meshes it is reported and left whole")
		end
		if part:FindFirstChildWhichIsA("DataModelMesh") then
			table.insert(cr.notes, "has a SpecialMesh/BlockMesh child: CSG cuts the part's box shape, not the mesh")
		end
	end
	return cr
end

-- Joints, welds and object values that point at any part in `set`.
local function referencesTo(set)
	local list = {}
	for _, d in workspace:GetDescendants() do
		local fields = {}
		if d:IsA("JointInstance") or d:IsA("WeldConstraint") or d:IsA("NoCollisionConstraint") then
			if set[d.Part0] then
				table.insert(fields, "Part0")
			end
			if set[d.Part1] then
				table.insert(fields, "Part1")
			end
		elseif d:IsA("ObjectValue") and d.Value and set[d.Value] then
			table.insert(fields, "Value")
		end
		if #fields > 0 then
			table.insert(list, { inst = d, fields = fields })
		end
	end
	return list
end

local function plan(train)
	local P = { train = train, notes = {}, crossers = {}, moves = {}, gangway = {}, counts = {}, joints = {} }
	if train:FindFirstChild("RR_Breaks") then
		P.refuse = "this train is already set up (it has RR_Breaks). To redo it, undo (Ctrl+Z) or restore the copy in ServerStorage.RR_Backups first."
		return P
	end
	local parts = Core.baseParts(train)
	P.parts = parts
	local found = Core.findCarriages(parts, FRONT_AT, PLANE_OFFSET)
	P.found = found
	if found.mode == "plane" and not ALLOW_PLANE_FALLBACK then
		P.refuse = "no roof union of about 19.48 x 3.59 x 62.34 was found, so the jagged tear has nothing to hang on. "
			.. "Run RR_BreakChecker to see what it finds; for another train set ALLOW_PLANE_FALLBACK = true (flat cut)."
		return P
	end
	if #found.carriages ~= 2 then
		P.refuse = ("found %d carriage(s); this kit handles exactly 2 (one roof union per carriage)"):format(#found.carriages)
		for i, r in found.roofs or {} do
			table.insert(P.notes, ("roof %d: %s at %s"):format(i, r:GetFullName(), Core.v(r.CFrame.Position)))
		end
		return P
	end
	for k = 1, 2 do
		P.counts[k] = { Front = 0, Rear = 0 }
	end
	local cutSet, perBreak = {}, { 0, 0 }
	for _, part in parts do
		if Core.insidePart(part, train) then
			-- travels inside its parent part; only worth a word if it crosses a tear
			for k, car in found.carriages do
				if Core.classify(car.cells, Core.boxIn(car.frame, part), MARGIN) == "cross" then
					table.insert(P.notes, ("%s crosses break %d but sits inside another part, so it stays whole with it"):format(describe(part), k))
				end
			end
		else
			local hits = {}
			for k, car in found.carriages do
				local box = Core.boxIn(car.frame, part)
				if Core.classify(car.cells, box, MARGIN) == "cross" then
					table.insert(hits, { k = k, box = box })
				end
			end
			local c, half, gangway = Core.assign(found, part)
			local cr = #hits == 1 and planCut(found, part, hits[1].k, hits[1].box) or nil
			if cr and cr.method ~= "skip" then
				table.insert(P.crossers, cr)
				cutSet[part] = true
				perBreak[cr.k] += 1
				P.counts[cr.k].Front += cr.front
				P.counts[cr.k].Rear += cr.rear
			else
				if cr then
					table.insert(P.crossers, cr)
					perBreak[cr.k] += 1
					table.insert(P.notes, ("%s crosses break %d but is NOT cut: %s; it stays whole in Carriage%d.%sHalf"):format(describe(part), cr.k, cr.why, c, half))
				elseif #hits > 1 then
					table.insert(P.notes, ("%s crosses both breaks; it stays whole in Carriage%d.%sHalf"):format(describe(part), c, half))
				end
				table.insert(P.moves, { part = part, c = c, half = half })
				P.counts[c][half] += 1
				if gangway then
					table.insert(P.gangway, part)
				end
			end
		end
	end
	local order = { slice = 1, csg = 2, skip = 3 }
	table.sort(P.crossers, function(a, b)
		if a.k ~= b.k then
			return a.k < b.k
		elseif a.method ~= b.method then
			return order[a.method] < order[b.method]
		end
		return a.part.CFrame.Position.Y < b.part.CFrame.Position.Y
	end)
	P.cutSet = cutSet
	P.joints = referencesTo(cutSet)

	-- anything else worth a look before it runs
	if found.mode == "roof" then
		for k = 1, 2 do
			if perBreak[k] ~= EXPECTED_CROSSERS then
				table.insert(P.notes, ("break %d has %d crossers; Joel's train has %d per carriage: check FRONT_AT and RR_BreakChecker"):format(k, perBreak[k], EXPECTED_CROSSERS))
			end
		end
	end
	for _, name in { "Carriage1", "Carriage2" } do
		local existing = train:FindFirstChild(name)
		if existing then
			table.insert(P.notes, ("the train already has a child named %s (%s); the new %s Model sits beside it (the runtime finds halves through RR_Breaks, not by name)"):format(name, existing.ClassName, name))
		end
	end
	local scripts, loose, hidden = 0, 0, 0
	for _, d in train:GetDescendants() do
		if d:IsA("LuaSourceContainer") then
			scripts += 1
		end
		if d:IsA("BasePart") and not d.Anchored and not Core.insidePart(d, train) then
			loose += 1
		end
		if not d.Archivable then
			hidden += 1
		end
	end
	if scripts > 0 then
		table.insert(P.notes, ("%d script(s) in the train stay where they are; check any that find parts by path"):format(scripts))
	end
	if loose > 0 then
		table.insert(P.notes, ("%d part(s) are not anchored; TrainSplit welds only anchored parts to a wreck"):format(loose))
	end
	if hidden > 0 then
		table.insert(P.notes, ("%d instance(s) have Archivable = false, so the backup copy will not include them"):format(hidden))
	end
	local function primaryNote(m)
		if m:IsA("Model") and m.PrimaryPart and cutSet[m.PrimaryPart] then
			table.insert(P.notes, ("%s has a crosser as PrimaryPart; it will point at the front piece"):format(m:GetFullName()))
		end
	end
	primaryNote(train)
	for _, d in train:GetDescendants() do
		primaryNote(d)
	end
	return P
end

local function printPlan(P)
	local found = P.found
	say("Mode: %s. Front = the %s end of world %s (FRONT_AT = %q).", found.mode == "roof" and "roof unions -> jagged tear" or "plane fallback",
		FRONT_AT, found.axisName, FRONT_AT)
	for k, car in found.carriages do
		local F = car.frame
		say("Break %d frame: origin %s  right %s  up %s  rear %s", k, Core.v(F.Position), Core.v(F.XVector), Core.v(F.YVector), Core.v(F.ZVector))
	end
	say("Parts per half (whole parts + cut pieces, plus 1 Root each):")
	for k = 1, 2 do
		say("  Carriage%d.FrontHalf %4d    Carriage%d.RearHalf %4d", k, P.counts[k].Front, k, P.counts[k].Rear)
	end
	say("Crossers (%d) and how each is cut:", #P.crossers)
	for _, cr in P.crossers do
		local how
		if cr.method == "slice" then
			how = ("slice into %d exact boxes (%d front, %d rear)"):format(#cr.pieces, cr.front, cr.rear)
		elseif cr.method == "csg" then
			how = ("SubtractAsync over %d cell(s): front = minus %d rear boxes, rear = minus %d front boxes (cells + edge bridges)"):format(#cr.touched, cr.boxes.Rear, cr.boxes.Front)
		else
			how = "NOT CUT: " .. cr.why
		end
		say("  Break %d  %s  ->  %s", cr.k, describe(cr.part), how)
		for _, n in cr.notes do
			say("      note: %s", n)
		end
		for _, child in cr.children do
			say("      child %s %q: %s", child.ClassName, child.Name, RULE_TEXT[childRule(child)])
		end
	end
	for _, g in P.gangway do
		say("Gangway between the carriages -> Carriage1.RearHalf: %s", describe(g))
	end
	for _, j in P.joints do
		say("Points at a part that will be cut: %s (%s)", describe(j.inst), table.concat(j.fields, ", "))
	end
	if #P.notes > 0 then
		say("Worth a look:")
		for _, n in P.notes do
			say("  - %s", n)
		end
	else
		say("Nothing unexpected.")
	end
end

---------------------------------------------------------------- apply

local function newFolder(name, parent)
	local f = Instance.new("Folder")
	f.Name = name
	f.Parent = parent
	return f
end

-- Mirror the builder's containers (same class and name) inside a half, created on first use.
local function mirrorOf(ctx, half, container)
	if container == ctx.train or container == nil then
		return half
	end
	ctx.mirrors[half] = ctx.mirrors[half] or {}
	local m = ctx.mirrors[half][container]
	if m then
		return m
	end
	local parent = mirrorOf(ctx, half, container.Parent)
	local ok, inst = pcall(Instance.new, container.ClassName)
	if not ok or not inst then
		inst = Instance.new("Folder")
	end
	inst.Name = container.Name
	for name, value in container:GetAttributes() do
		inst:SetAttribute(name, value)
	end
	for _, tag in container:GetTags() do
		inst:AddTag(tag)
	end
	inst.Parent = parent
	ctx.mirrors[half][container] = inst
	ctx.containers[container] = true
	return inst
end

-- Models from the part up to the train that use it as PrimaryPart (read before it moves).
local function primaryOwners(ctx, part)
	local owners = {}
	local p = part.Parent
	while p do
		if p:IsA("Model") and p.PrimaryPart == part then
			table.insert(owners, p)
		end
		if p == ctx.train then
			break
		end
		p = p.Parent
	end
	return owners
end

-- The PrimaryPart role moves with the part (or to a crosser's front piece): the train points at it, and so
-- does each builder's model's mirror in the half it went to.
local function passPrimary(ctx, owners, half, newPart)
	for _, m in owners do
		if m == ctx.train then
			ctx.train.PrimaryPart = newPart
		else
			local mirror = mirrorOf(ctx, half, m)
			if mirror:IsA("Model") then
				mirror.PrimaryPart = newPart
			end
		end
	end
end

local function cutterBoxes(car, b, side, template, folder)
	local list = {}
	for _, s in cutterSpecs(car, b, side) do
		local p = Instance.new("Part")
		p.Name = ("Cutter%s_%s"):format(side, s[7])
		p.Anchored = true
		p.CanCollide = false
		p.CanQuery = false
		p.CanTouch = false
		p.CastShadow = false
		-- the cut faces take the cutter's look, so match the part being cut
		p.Color = template.Color
		p.Material = template.Material
		pcall(function()
			p.MaterialVariant = template.MaterialVariant
		end)
		p.Size = Vector3.new(s[2] - s[1], s[4] - s[3], s[6] - s[5])
		p.CFrame = car.frame * CFrame.new((s[1] + s[2]) / 2, (s[3] + s[4]) / 2, (s[5] + s[6]) / 2)
		p.Parent = folder
		table.insert(list, p)
	end
	return list
end

local function subtract(part, cutters)
	local cf, rf
	pcall(function()
		cf = part.CollisionFidelity
	end)
	pcall(function()
		rf = part.RenderFidelity
	end)
	local ok, result = pcall(function()
		if cf and rf then
			return part:SubtractAsync(cutters, cf, rf)
		end
		return part:SubtractAsync(cutters)
	end)
	if ok and typeof(result) == "Instance" and result:IsA("BasePart") then
		return result
	end
	return nil, ok and "SubtractAsync returned nothing" or tostring(result)
end

-- Size of a box (frame extents) in the axes of a part lined up with the frame.
local function localSize(rot, ext)
	local _, _, _, r00, r01, r02, r10, r11, r12, r20, r21, r22 = rot:GetComponents()
	return Vector3.new(
		math.abs(r00) * ext.X + math.abs(r10) * ext.Y + math.abs(r20) * ext.Z,
		math.abs(r01) * ext.X + math.abs(r11) * ext.Y + math.abs(r21) * ext.Z,
		math.abs(r02) * ext.X + math.abs(r12) * ext.Y + math.abs(r22) * ext.Z
	)
end

local function sideOf(car, pos)
	local p = car.frame:PointToObjectSpace(pos)
	return p.Z < (Core.dAt(car.cells, p.X, p.Y) or 0) and "Front" or "Rear", p
end

local function pieceFor(made, side, p)
	local first
	for _, m in made do
		if m.side == side then
			if not m.lo then
				return m.part
			end
			if p.X >= m.lo.X - 1e-3 and p.X <= m.hi.X + 1e-3 and p.Y >= m.lo.Y - 1e-3 and p.Y <= m.hi.Y + 1e-3 then
				return m.part
			end
			first = first or m.part
		end
	end
	return first or made[1].part
end

local function rehome(ctx, cr, car, made)
	local part = cr.part
	local centreSide, centreP = sideOf(car, part.CFrame.Position)
	for _, child in part:GetChildren() do
		local rule = childRule(child)
		if rule == "position" then
			local world = part.CFrame * child.CFrame
			local side, p = sideOf(car, world.Position)
			local target = pieceFor(made, side, p)
			child.CFrame = target.CFrame:ToObjectSpace(world)
			child.Parent = target
		elseif rule == "copy" then
			for _, m in made do
				local copy = child:Clone() -- nil when Archivable is off: then it stays on the original
				if copy then
					copy.Parent = m.part
				end
			end
		else
			child.Parent = pieceFor(made, centreSide, centreP)
		end
		table.insert(ctx.R.rehomed, { child = child, from = part, rule = rule })
	end
end

local function cutOne(ctx, cr)
	local part, car = cr.part, ctx.found.carriages[cr.k]
	local from = part.Parent
	local owners = primaryOwners(ctx, part)
	local made = {}
	if cr.method == "slice" then
		local rot = car.frame:ToObjectSpace(part.CFrame).Rotation
		local archivable = part.Archivable
		part.Archivable = true
		for _, s in cr.pieces do
			local piece = part:Clone() -- a clone keeps every property, attribute and tag
			piece:ClearAllChildren()
			piece.Size = localSize(rot, s.hi - s.lo)
			piece.CFrame = car.frame * CFrame.new((s.lo + s.hi) / 2) * rot
			table.insert(made, { part = piece, side = s.side, lo = s.lo, hi = s.hi })
		end
		part.Archivable = archivable
	else
		local rearBoxes = cutterBoxes(car, cr.box, "Rear", part, ctx.tmp)
		local frontBoxes = cutterBoxes(car, cr.box, "Front", part, ctx.tmp)
		local front, errF = subtract(part, rearBoxes)
		local rear, errR = subtract(part, frontBoxes)
		if not (front and rear) then
			if front then
				front:Destroy()
			end
			if rear then
				rear:Destroy()
			end
			-- keep the cutters so the cut can be done by hand
			local keep = newFolder(("%02d_%s"):format(#ctx.R.failures + 1, part.Name), ctx.cutters)
			local rf, ff = newFolder("RearCutter_makes_front_piece", keep), newFolder("FrontCutter_makes_rear_piece", keep)
			for _, b in rearBoxes do
				b.Parent = rf
			end
			for _, b in frontBoxes do
				b.Parent = ff
			end
			return nil, errF or errR, keep
		end
		copyLook(part, front)
		copyLook(part, rear)
		made = { { part = front, side = "Front" }, { part = rear, side = "Rear" } }
	end
	for _, m in made do
		m.part.Parent = mirrorOf(ctx, ctx.halves[cr.k][m.side], from)
	end
	passPrimary(ctx, owners, ctx.halves[cr.k].Front, pieceFor(made, "Front", Vector3.zero))
	rehome(ctx, cr, car, made)
	part.Parent = ctx.originals -- never destroyed
	return made
end

local function makeRoot(model, frame)
	local lo, hi
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") then
			local b = Core.boxIn(frame, d)
			lo = lo and Vector3.new(math.min(lo.X, b.x0), math.min(lo.Y, b.y0), math.min(lo.Z, b.z0)) or Vector3.new(b.x0, b.y0, b.z0)
			hi = hi and Vector3.new(math.max(hi.X, b.x1), math.max(hi.Y, b.y1), math.max(hi.Z, b.z1)) or Vector3.new(b.x1, b.y1, b.z1)
		end
	end
	local root = Instance.new("Part")
	root.Name = "Root"
	root.Size = Vector3.new(1, 1, 1)
	root.Transparency = 1
	root.Anchored = true
	root.CanCollide = false
	root.CanQuery = false
	root.CanTouch = false
	root.CastShadow = false
	root.Massless = true
	root.CFrame = frame * CFrame.new(lo and (lo + hi) / 2 or Vector3.zero)
	root.Parent = model
	model.PrimaryPart = root
	return root
end

local function depth(inst)
	local n = 0
	while inst.Parent do
		n += 1
		inst = inst.Parent
	end
	return n
end

local function doApply(P, R)
	local train, found = P.train, P.found
	local ctx = { train = train, found = found, mirrors = {}, containers = {}, halves = {}, R = R }

	-- 1. backup: a full copy first, then every cut original joins it
	local backups = ServerStorage:FindFirstChild("RR_Backups") or newFolder("RR_Backups", ServerStorage)
	local t = os.date("!*t")
	local name = ("%s_%04d%02d%02d-%02d%02d%02dZ"):format(train.Name, t.year, t.month, t.day, t.hour, t.min, t.sec)
	local unique, n = name, 1
	while backups:FindFirstChild(unique) do
		n += 1
		unique = name .. "_" .. n
	end
	local archivable = train.Archivable
	train.Archivable = true
	local copy = train:Clone()
	train.Archivable = archivable
	if not copy then
		error("could not copy the train for the backup")
	end
	local bk = Instance.new("Folder")
	bk.Name = unique
	bk:SetAttribute("Train", train:GetFullName())
	bk:SetAttribute("Version", SPEC_VERSION)
	copy.Parent = bk
	ctx.originals = newFolder("CutOriginals", bk)
	ctx.cutters = newFolder("Cutters", bk)
	bk.Parent = backups
	R.backup = bk

	-- 2. the new structure
	for k = 1, 2 do
		local carriage = Instance.new("Model")
		carriage.Name = "Carriage" .. k
		ctx.halves[k] = {}
		for _, side in { "Front", "Rear" } do
			local half = Instance.new("Model")
			half.Name = side .. "Half"
			half.Parent = carriage
			ctx.halves[k][side] = half
		end
		carriage.Parent = train
	end
	R.halves = ctx.halves

	-- 3. whole parts into their halves
	for _, mv in P.moves do
		local owners = primaryOwners(ctx, mv.part)
		local half = ctx.halves[mv.c][mv.half]
		mv.part.Parent = mirrorOf(ctx, half, mv.part.Parent)
		passPrimary(ctx, owners, half, mv.part)
	end

	-- 4. the crossers (cutters live in a temporary folder and are destroyed after)
	ctx.tmp = newFolder("RR_TmpCutters", workspace)
	for i, cr in P.crossers do
		if cr.method ~= "skip" then
			say("  cutting %d/%d: %s (%s)", i, #P.crossers, describe(cr.part), cr.method)
			local made, err, kept = cutOne(ctx, cr)
			if made then
				table.insert(R.cut, { cr = cr, pieces = made })
			else
				-- left whole in the half that holds its centre
				local c, half = Core.assign(found, cr.part)
				local from = cr.part.Parent
				cr.part.Parent = mirrorOf(ctx, ctx.halves[c][half], from)
				table.insert(R.failures, { cr = cr, err = err, cutters = kept, c = c, half = half })
			end
		end
	end
	ctx.tmp:Destroy()

	-- 5. roots, break records, emptied containers
	for k, car in found.carriages do
		for _, side in { "Front", "Rear" } do
			makeRoot(ctx.halves[k][side], car.frame)
		end
	end
	local breaks = newFolder("RR_Breaks", nil)
	for k, car in found.carriages do
		local rec = Instance.new("Configuration")
		rec.Name = "Break" .. k
		rec:SetAttribute("Carriage", k)
		rec:SetAttribute("BreakCFrame", car.frame)
		rec:SetAttribute("Intact", true)
		rec:SetAttribute("Version", SPEC_VERSION)
		rec:SetAttribute("Mode", found.mode == "roof" and "jagged" or "plane")
		for field, side in { KeptHalf = "Front", LostHalf = "Rear" } do
			local v = Instance.new("ObjectValue")
			v.Name = field
			v.Value = ctx.halves[k][side]
			v.Parent = rec
		end
		rec.Parent = breaks
	end
	breaks.Parent = train
	local emptied = {}
	for container in ctx.containers do
		table.insert(emptied, container)
	end
	table.sort(emptied, function(a, b)
		return depth(a) > depth(b)
	end)
	local emptiedFolder
	for _, container in emptied do
		if container.Parent and #container:GetDescendants() == 0 then
			emptiedFolder = emptiedFolder or newFolder("EmptiedContainers", bk)
			container.Parent = emptiedFolder
			R.emptied += 1
		end
	end
	local cutOriginals = {}
	for _, c in R.cut do
		cutOriginals[c.cr.part] = true
	end
	R.joints = referencesTo(cutOriginals)
	for k = 1, 2 do
		R.counts[k] = {}
		for _, side in { "Front", "Rear" } do
			local count = 0
			for _, d in ctx.halves[k][side]:GetDescendants() do
				if d:IsA("BasePart") and d.Name ~= "Root" then
					count += 1
				end
			end
			R.counts[k][side] = count
		end
	end
end

local function printResult(P, R)
	say("Result:")
	for k = 1, 2 do
		say("  Carriage%d.FrontHalf %4d parts    Carriage%d.RearHalf %4d parts   (+ Root each)", k, R.counts[k].Front, k, R.counts[k].Rear)
	end
	local sliced, pieces = 0, 0
	for _, c in R.cut do
		pieces += #c.pieces
		if c.cr.method == "slice" then
			sliced += 1
		end
	end
	say("  Crossers cut: %d of %d (%d sliced into boxes, %d by CSG), %d pieces.", #R.cut, #P.crossers, sliced, #R.cut - sliced, pieces)
	say("  CSG failures: %d", #R.failures)
	for _, f in R.failures do
		say("    %s: %s", describe(f.cr.part), f.err)
		say("      It stays whole in Carriage%d.%sHalf (it will poke out of the tear). What to do: select it and try", f.c, f.half)
		say("      Model > Separate, then Union again (repairs a broken union), undo the setup and run it again; or cut it")
		say("      by hand with the saved cutter boxes in %s: Negate the boxes and Union them with a copy", f.cutters:GetFullName())
		say("      of the part (RearCutter makes the front piece, FrontCutter the rear); a MeshPart may need splitting in Blender.")
		say("      If CSG struggles with the many boxes, undo and try CUTTER_BRIDGE = 0 (fewer boxes, small sliver risk).")
	end
	for _, r in R.rehomed do
		say("  Re-homed %s %q from %s: %s", r.child.ClassName, r.child.Name, r.from.Name, RULE_TEXT[r.rule])
	end
	for _, j in R.joints do
		say("  Still points at a cut original (now in the backup): %s (%s); re-point it at a piece or delete it", describe(j.inst), table.concat(j.fields, ", "))
	end
	if R.emptied > 0 then
		say("  %d emptied container(s) moved into the backup (EmptiedContainers).", R.emptied)
	end
	say("  Backup: %s (full copy, CutOriginals, Cutters).", R.backup:GetFullName())
	say("  Undo: Ctrl+Z (one step).")
	say("Next: run RR_BreakChecker again (it checks the halves), then test with TrainSplitDemo (RR_TestBreak = 1 or 2).")
end

local function run()
	local R = { ok = false, dryRun = DRY_RUN, cut = {}, failures = {}, rehomed = {}, joints = {}, counts = {}, emptied = 0, lines = lines }
	local selection = game:GetService("Selection"):Get()
	local train = selection[1]
	if #selection ~= 1 or not train:IsA("Model") then
		R.refused = "select exactly one train Model in the Explorer, then run again"
		say("RR_TrainSplit_Setup: %s.", R.refused)
		return R
	end
	say("== RR_TrainSplit_Setup %s %s: %s ==", SPEC_VERSION, DRY_RUN and "DRY RUN (nothing changes)" or "APPLY", train:GetFullName())
	local P = plan(train)
	R.plan = P
	if P.refuse then
		R.refused = P.refuse
		say("Refused: %s", P.refuse)
		for _, n in P.notes do
			say("  - %s", n)
		end
		return R
	end
	printPlan(P)
	if DRY_RUN then
		R.ok = true
		say("Dry run only. Set DRY_RUN = false and run again to do it.")
		return R
	end

	local recording
	local okRec, id = pcall(function()
		return ChangeHistoryService:TryBeginRecording("RR_TrainSplit_Setup", "Split the train into carriage halves")
	end)
	if okRec and id then
		recording = id
	else
		pcall(function()
			ChangeHistoryService:SetWaypoint("Before RR_TrainSplit_Setup")
		end)
	end
	local ok, err = pcall(doApply, P, R)
	if recording then
		pcall(function()
			ChangeHistoryService:FinishRecording(recording, ok and Enum.FinishRecordingOperation.Commit or Enum.FinishRecordingOperation.Cancel)
		end)
	else
		pcall(function()
			ChangeHistoryService:SetWaypoint("RR_TrainSplit_Setup")
		end)
	end
	if not ok then
		R.error = tostring(err)
		say("FAILED: %s", R.error)
		say(recording and "Every change was rolled back." or "Press Ctrl+Z to undo the partial change.")
		return R
	end
	R.ok = true
	printResult(P, R)
	return R
end

return run()
