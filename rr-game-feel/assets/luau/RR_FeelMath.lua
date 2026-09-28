-- RR_FeelMath (ModuleScript) - rr-game-feel. Pure math, no Roblox services, Lua 5.1 compatible.
-- The same formulas as scripts/feelmath.py, so the cloud plots and previews match the runtime.
-- RR_Feel sets M.engine to TweenService:GetValue so easing in game is the engine's own.

local M = {}

local sin, cos, exp, sqrt, floor, pi = math.sin, math.cos, math.exp, math.sqrt, math.floor, math.pi
local BACK_S = 1.70158
local ELASTIC_C4 = 2 * pi / 3

M.STYLES = { "Linear", "Sine", "Back", "Quad", "Quart", "Quint", "Bounce", "Elastic", "Exponential", "Circular", "Cubic" }
M.DIRECTIONS = { "In", "Out", "InOut" }
M.SEEDS = { pitch = 11, yaw = 23, roll = 37, x = 41, y = 53, ui = 67 }
M.engine = nil -- optional function(style, direction, t) -> eased value (RR_Feel sets TweenService:GetValue)

function M.clamp(x, lo, hi)
	if x < lo then return lo end
	if x > hi then return hi end
	return x
end

local function bounceOut(t)
	local n1, d1 = 7.5625, 2.75
	if t < 1 / d1 then
		return n1 * t * t
	elseif t < 2 / d1 then
		t = t - 1.5 / d1
		return n1 * t * t + 0.75
	elseif t < 2.5 / d1 then
		t = t - 2.25 / d1
		return n1 * t * t + 0.9375
	end
	t = t - 2.625 / d1
	return n1 * t * t + 0.984375
end

local IN = {
	Linear = function(t) return t end,
	Sine = function(t) return 1 - cos(t * pi / 2) end,
	Quad = function(t) return t * t end,
	Cubic = function(t) return t * t * t end,
	Quart = function(t) return t * t * t * t end,
	Quint = function(t) return t * t * t * t * t end,
	Exponential = function(t)
		if t <= 0 then return 0 end
		return 2 ^ (10 * t - 10)
	end,
	Circular = function(t) return 1 - sqrt(math.max(0, 1 - t * t)) end,
	Back = function(t) return (BACK_S + 1) * t * t * t - BACK_S * t * t end,
	Elastic = function(t)
		if t <= 0 then return 0 end
		if t >= 1 then return 1 end
		return -(2 ^ (10 * t - 10)) * sin((t * 10 - 10.75) * ELASTIC_C4)
	end,
	Bounce = function(t) return 1 - bounceOut(1 - t) end,
}

-- Penner forms of the 11 Roblox EasingStyles; direction In, Out or InOut
function M.easeOwn(style, direction, t)
	local f = IN[style]
	assert(f, "unknown EasingStyle " .. tostring(style))
	t = M.clamp(t, 0, 1)
	if direction == "In" then
		return f(t)
	elseif direction == "Out" then
		return 1 - f(1 - t)
	elseif direction == "InOut" then
		if t < 0.5 then return f(2 * t) / 2 end
		return 1 - f(2 - 2 * t) / 2
	end
	error("unknown EasingDirection " .. tostring(direction))
end

function M.ease(style, direction, t)
	if M.engine then
		return M.engine(style, direction, M.clamp(t, 0, 1))
	end
	return M.easeOwn(style, direction, t)
end

local function frac(x) return x - floor(x) end

local function grad(i, seed)
	return frac(sin(i * 12.9898 + seed * 78.233) * 43758.5453) * 2 - 1
end

-- 1D gradient noise, smooth, 0 at integers, range about [-1, 1]
function M.noise1(seed, x)
	local i0 = floor(x)
	local f = x - i0
	local u = f * f * f * (f * (f * 6 - 15) + 10)
	return 2 * (grad(i0, seed) * f * (1 - u) + grad(i0 + 1, seed) * (f - 1) * u)
end

-- punch at local time t: "sin" kicks out from 0, "cos" starts displaced, "noise" is a decaying jitter
function M.spring(t, amp, freq, damping, shape, dur, seed)
	if t < 0 or (dur and t >= dur) then return 0 end
	if shape == "noise" then
		local d = dur or 0.5
		local k = 1 - t / d
		return amp * k * k * M.noise1(seed or M.SEEDS.ui, t * freq)
	end
	local w = 2 * pi * freq
	local z = M.clamp(damping or 0.3, 0, 0.999)
	local wd = w * sqrt(1 - z * z)
	local s
	if shape == "cos" then s = cos(wd * t) else s = sin(wd * t) end
	return amp * exp(-z * w * t) * s
end

-- largest |spring| of a unit spring over [0, dur), 240 samples (feelmath.peak_gain is identical); punches and
-- camera kicks divide by it, so a preset's amp (and angles_deg) is the peak the player sees
M.PEAK_SAMPLES = 240
local peakCache = {}
function M.peakGain(freq, damping, shape, dur, seed)
	local d = dur or 0.5
	local key = string.format("%.17g|%.17g|%s|%.17g|%s", freq, damping or 0.3, shape or "sin", d, tostring(seed or M.SEEDS.ui))
	local g = peakCache[key]
	if g then return g end
	g = 0
	for i = 0, M.PEAK_SAMPLES - 1 do
		local v = math.abs(M.spring(d * i / M.PEAK_SAMPLES, 1, freq, damping, shape, d, seed))
		if v > g then g = v end
	end
	if g <= 1e-6 then g = 1 end
	peakCache[key] = g
	return g
end

-- 0 -> 1 over tIn (styleIn Out), hold, 1 -> 0 over tOut (styleOut InOut)
function M.envelope(t, tIn, hold, tOut, styleIn, styleOut)
	if t < 0 then return 0 end
	if t < tIn then return M.ease(styleIn or "Quad", "Out", t / tIn) end
	t = t - tIn
	if t < (hold or 0) then return 1 end
	t = t - (hold or 0)
	if t < tOut then return 1 - M.ease(styleOut or "Quad", "InOut", t / tOut) end
	return 0
end

function M.pulse(t, lo, hi, period)
	return lo + (hi - lo) * (0.5 - 0.5 * cos(2 * pi * t / period))
end

-- keys = { {ms, value}, ... } sorted; linear between keys, 0 outside
function M.keysAt(keys, t)
	local ms = t * 1000
	local n = #keys
	if n == 0 or ms < keys[1][1] or ms > keys[n][1] then return 0 end
	for i = 1, n - 1 do
		local a, b = keys[i], keys[i + 1]
		if ms >= a[1] and ms <= b[1] then
			if b[1] == a[1] then return a[2] end
			return a[2] + (b[2] - a[2]) * (ms - a[1]) / (b[1] - a[1])
		end
	end
	return keys[n][2]
end

-- knob position for a finger at u (-1..1 of travel, sign = side): heavy before the detent, 1 at it
function M.leverDisplay(u, detent, resist)
	local sgn = 1
	if u < 0 then sgn = -1 end
	local a = M.clamp(math.abs(u), 0, 1)
	if a >= detent then return sgn end
	return sgn * detent * (a / detent) ^ resist
end

return M
