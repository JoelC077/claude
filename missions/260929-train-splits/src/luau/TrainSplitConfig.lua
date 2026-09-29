--[[
TrainSplitConfig  (ModuleScript in ReplicatedStorage)  v2.0.0

Every tunable for the carriage split lives here; the server (TrainSplit) and every client
(TrainSplitClient) read the same table, so change numbers here only.
Numbers marked "break_spec" come from src/kit/break_spec.json (mission 260929-train-splits, T0).

Break frame B (per carriage, saved by RR_TrainSplit_Setup in Train/RR_Breaks/BreakN.BreakCFrame):
origin on the carriage centre line, at floor-top height, on the break plane.
+X across the carriage (right when facing the front), +Y up, +Z toward the REAR of the train.
]]

local Config = {}

Config.Version = "2.0.0"
Config.RemoteName = "RR_TrainSplitFX" -- RemoteEvent in ReplicatedStorage, server -> clients only
Config.WreckFolderName = "RR_Wrecks" -- workspace folder the lost bodies move into

-- Motion. The train never moves: the world scrolls past it at the train's speed.
Config.SpeedAttribute = "Speed" -- attribute on the train Model, studs/s (your game keeps it current)
Config.SpeedDefault = 35 -- canon gameplay.speed.normal; used when the attribute is missing
Config.Brake = 12 -- break_spec motion.brake: studs/s^2 the lost part slows by until it moves with the terrain
Config.Recoil = { dist = 0.8, time = 0.2 } -- break_spec motion.recoil: the blast shoves the wreck back
Config.LeadTime = 0.25 -- the snap happens this long after SplitAt, so metal_tear (t = -0.25) is heard first
Config.LateTolerance = 0.5 -- a client that learns of the snap later than this skips the one-shot fx
Config.Despawn = { distance = 700, time = 30 } -- break_spec: studs behind where it broke off / seconds

-- Topple (break_spec topple). One entry per lost body, front-most first; a snap uses one side for all.
Config.Side = "random" -- "random" (seeded per snap) | "left" | "right" (as seen facing the front)
Config.Pivot = { X_abs = 11.7, Y = -8.6 } -- break frame: outer bogie edge at rail level on the falling side
Config.Topple = {
	-- the broken half
	{ delay = 0.45, roll = 88, roll_time = 1.05, ease = "QuadIn", bounce = { 82, 88 }, bounce_time = 0.35, yaw = 7, sink = 0.6 },
	-- a carriage dragged behind it (break 1 only: carriage 2)
	{ delay = 0.8, roll = 86, roll_time = 1.2, ease = "QuadIn", bounce = { 80, 86 }, bounce_time = 0.4, yaw = -4, sink = 0.5 },
}

-- The jagged tear, {X0, X1, Y0, Y1, d, region}: inside the cell the tear sits at Z = d.
-- Same numbers as RR_TrainSplit_Setup; the runtime uses them to tell riders from people on the kept half.
-- CELLS BEGIN (break_spec.json v2.0.0, 29 cells; the Lune suite checks they match)
Config.Cells = {
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

-- Timeline (break_spec events). t = seconds after the snap. fx = key into Config.FX, sound = key into
-- Config.Sounds, at = key into Config.Anchors (or "impact" / "wreck", resolved per lost body).
Config.Events = {
	{ t = -0.25, id = "metal_tear", sound = "metal_tear", at = "explosion" },
	{ t = 0.0, id = "split_explosion", fx = "split_explosion", sound = "split_explosion", shake = "big", at = "explosion" },
	{ t = 0.0, id = "glass_burst", fx = "glass_burst", sound = "split_glass", at = "windows" },
	{ t = 0.05, id = "torn_edge_smoke", fx = "torn_edge_smoke", loop = 20, at = "torn_edges" },
	{ t = 0.8, id = "debris_rain", sound = "debris_rain", at = "debris" },
	{ t = "impact", id = "topple_crash", fx = "topple_dust", sound = "topple_crash", shake = "medium", at = "impact" },
	{ t = 0.3, t_end = "stop", id = "wreck_scrape", sound = "wreck_scrape", at = "wreck", perBody = true },
}

-- Anchors in the break frame (studs). Window and torn-edge points were read off the export near the break.
Config.Anchors = {
	explosion = Vector3.new(0, 5, 0), -- break_spec events: split_explosion / metal_tear
	debris = Vector3.new(0, 3, 2), -- break_spec events: debris_rain
	windows = { -- panes either side of the break pillar (windows 4 and 5), both walls
		Vector3.new(-9.4, 6.6, -4.5),
		Vector3.new(9.4, 6.6, -4.5),
		Vector3.new(-9.4, 6.6, 4.5),
		Vector3.new(9.4, 6.6, 4.5),
	},
	torn_edges = { -- points on the tear: west wall, east wall, roof, floor (smoke on the kept end and the wreck)
		Vector3.new(-9.5, 5, 0.9),
		Vector3.new(9.5, 5, -0.2),
		Vector3.new(0, 13, -2.2),
		Vector3.new(0, 0.2, 0.9),
	},
}

-- FX preset names, played through ReplicatedStorage.RR_VFX (VFX.burst / VFX.attach) when it exists.
-- split_explosion, torn_edge_smoke and topple_dust are the T3 split presets; glass_burst is from the fx library.
-- A missing library or preset falls back to Config.FallbackFX below.
Config.FX = {
	split_explosion = "split_explosion",
	glass_burst = "glass_burst",
	torn_edge_smoke = "torn_edge_smoke",
	topple_dust = "topple_dust",
}
Config.FxAnchorLife = 12 -- seconds a one-shot fx anchor lives: longer than any preset's particles

-- Sounds: synthesised by the T4 sound pass (rr-soundsmith, mission 260929-train-splits), licence-clean.
-- Upload each file (Studio Asset Manager > Bulk Import, or the Creator Hub), then paste "rbxassetid://<id>".
-- An empty SoundId is skipped. Volumes keep the mix order boom > tear > crash > debris.
Config.SoundGroupName = "SFX" -- optional SoundGroup in SoundService; used when it exists
Config.Sounds = {
	metal_tear = { SoundId = "", Volume = 0.8, Is3D = true, RollOffMaxDistance = 350 }, -- T4 "metal_tear": rip just before the snap
	split_explosion = { SoundId = "", Volume = 1.0, Is3D = true, RollOffMaxDistance = 600 }, -- T4 "split_explosion": the boom
	split_glass = { SoundId = "", Volume = 0.6, Is3D = true, RollOffMaxDistance = 250 }, -- T4 glass burst: the windows at the break
	debris_rain = { SoundId = "", Volume = 0.45, Is3D = true, RollOffMaxDistance = 250 }, -- T4 "debris_rain": bits landing
	topple_crash = { SoundId = "", Volume = 0.75, Is3D = true, RollOffMaxDistance = 450 }, -- T4 "topple_crash": wreck hits the ground
	wreck_scrape = { SoundId = "", Volume = 0.5, Is3D = true, Looped = true, RollOffMaxDistance = 300 }, -- T4 "wreck_scrape": grind while braking
}

-- Camera shake (client). amplitude in degrees, fading to 0 at `falloff` studs from the camera.
Config.ReduceMotionAttribute = "ReduceMotion" -- Player attribute; true = no camera shake (your settings menu sets it)
Config.Shake = {
	big = { amplitude = 1.5, duration = 0.9, frequency = 14, falloff = 250 },
	medium = { amplitude = 0.6, duration = 0.5, frequency = 12, falloff = 150 },
}

-- Built-in fallback emitters (only when RR_VFX or a preset is missing). Built-in textures, phone-sized counts.
-- Lists are evenly spaced keypoints over a particle's life; colours are hex (canon soot/ironwork/brass/hazard).
local TEX_FIRE = "rbxasset://textures/particles/fire_main.dds"
local TEX_SMOKE = "rbxasset://textures/particles/smoke_main.dds"
local TEX_SPARK = "rbxasset://textures/particles/sparkles_main.dds"
Config.SmokeWind = 18 -- studs/s^2 pushing fallback smoke toward the rear: the air streams past the moving train
Config.FallbackFX = {
	split_explosion = {
		explosion = true, -- Roblox's built-in Explosion look (no pressure, breaks no joints)
		flash = { Brightness = 4, Range = 40, Color = "#FFC46B", Time = 0.12 }, -- one short flash (flash-safe)
		life = 3.5,
		emitters = {
			{ Texture = TEX_FIRE, Count = 30, Lifetime = { 0.35, 0.8 }, Speed = { 18, 36 }, Size = { 5, 11, 2 }, Transparency = { 0, 0.2, 1 }, Color = { "#FFE39A", "#FF7A1A", "#7A2E0B" }, LightEmission = 0.8, Drag = 5 },
			{ Texture = TEX_SMOKE, Count = 22, Lifetime = { 1.6, 3.2 }, Speed = { 6, 14 }, Size = { 6, 16, 22 }, Transparency = { 0.15, 0.5, 1 }, Color = { "#363A42", "#15181B" }, Drag = 2, Wind = true },
			{ Texture = TEX_SPARK, Count = 36, Lifetime = { 0.5, 1.1 }, Speed = { 30, 60 }, Size = { 0.5, 0.1 }, Transparency = { 0, 1 }, Color = { "#FFD27A", "#F2C230" }, LightEmission = 1, Drag = 1, Acceleration = { 0, -60, 0 } },
		},
	},
	glass_burst = {
		life = 1.2,
		emitters = {
			{ Texture = TEX_SPARK, Count = 14, Lifetime = { 0.4, 0.9 }, Speed = { 12, 24 }, Size = { 0.35, 0.1 }, Transparency = { 0, 1 }, Color = { "#E8F4FF", "#BFD8EE" }, LightEmission = 0.4, Acceleration = { 0, -50, 0 } },
		},
	},
	torn_edge_smoke = {
		loop = true,
		life = 3.5,
		emitters = {
			{ Texture = TEX_SMOKE, Rate = 4, Lifetime = { 2, 3.5 }, Speed = { 1, 3 }, Size = { 1.5, 5 }, Transparency = { 0.35, 1 }, Color = { "#4A4E55", "#15181B" }, Drag = 1, Wind = true },
		},
	},
	topple_dust = {
		life = 3,
		emitters = {
			{ Texture = TEX_SMOKE, Count = 28, Lifetime = { 1.4, 2.8 }, Speed = { 8, 16 }, Size = { 4, 10, 14 }, Transparency = { 0.2, 0.6, 1 }, Color = { "#8C7A60", "#5E5241" }, Drag = 3, Spread = 75 },
		},
	},
}

return Config
