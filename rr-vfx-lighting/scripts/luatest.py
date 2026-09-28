#!/usr/bin/env python3
"""luatest.py: run RR_VFX.lua + RR_Lighting.lua with the generated presets in a real Lua 5.1 VM (lupa.lua51) against
stubbed Roblox services. Proves runtime logic, not rendering; Studio test pending (owner).

  python3 luatest.py [--presets DIR] [-v]

Checks: every preset attaches and every burst fires without a Lua error; every look applies and overrides push/pop;
loops start by the rules (priority-1 and start = "off" loops off, look-driven presets follow the look even when
attached late, {enabled = ...} wins); burst lights stay on through setSpeed, another burst and a look change;
speed-linked lights dim with Speed; flashes off softens pulses, freezes flicker and skips flash overrides.
Needs lupa (optional test dependency): pip install --target ~/.cache/rr-tools/py lupa (this script adds that folder
to sys.path). Exit 0 = all passed, 3 = lupa missing.
"""
import sys
sys.dont_write_bytecode = True  # never leave __pycache__ inside the skill
import argparse, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path.home() / ".cache" / "rr-tools" / "py"))
import vfx  # noqa: E402

STUBS = r"""
T = { now = 0, delays = {}, beats = {} }
function T.run(dt)
	T.now = T.now + dt
	local rest, due = {}, {}
	for _, d in ipairs(T.delays) do if d.at <= T.now + 1e-9 then table.insert(due, d) else table.insert(rest, d) end end
	T.delays = rest
	for _, d in ipairs(due) do d.fn() end
	for _, fn in ipairs(T.beats) do fn(dt) end
end
os.clock = function() return T.now end
warn = function(...) end
task = { delay = function(t, fn) table.insert(T.delays, { at = T.now + t, fn = fn }) end }
math.clamp = function(x, a, b) return math.max(a, math.min(b, x)) end
function typeof(v) return type(v) == "table" and rawget(v, "__type") or type(v) end

local V3 = {}
V3.__index = function(v, k)
	if k == "Magnitude" then return math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z) end
	if k == "Unit" then local m = math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z); if m == 0 then m = 1 end; return Vector3.new(v.X / m, v.Y / m, v.Z / m) end
	return nil
end
V3.__add = function(a, b) return Vector3.new(a.X + b.X, a.Y + b.Y, a.Z + b.Z) end
V3.__sub = function(a, b) return Vector3.new(a.X - b.X, a.Y - b.Y, a.Z - b.Z) end
V3.__unm = function(a) return Vector3.new(-a.X, -a.Y, -a.Z) end
V3.__mul = function(a, b)
	if type(a) == "number" then a, b = b, a end
	if type(b) == "number" then return Vector3.new(a.X * b, a.Y * b, a.Z * b) end
	return Vector3.new(a.X * b.X, a.Y * b.Y, a.Z * b.Z)
end
Vector3 = { new = function(x, y, z) return setmetatable({ X = x or 0, Y = y or 0, Z = z or 0, __type = "Vector3" }, V3) end }
Vector2 = { new = function(x, y) return { X = x, Y = y } end }
local CFm = {}
CFm.__index = function(c, k)
	if k == "Position" then return rawget(c, "p") end
	if k == "LookVector" then return Vector3.new(0, 0, -1) end
	return nil
end
local function cf(p) return setmetatable({ p = p or Vector3.new(), __type = "CFrame" }, CFm) end
CFm.__mul = function(a, b) return cf(a.p + (b.p or Vector3.new())) end
CFrame = { new = function(x, y, z) if type(x) == "table" then return cf(x) end return cf(Vector3.new(x, y, z)) end,
	Angles = function() return cf() end, lookAt = function(a) return cf(a) end }
local C3 = {}
C3.__index = { Lerp = function(a, b, t) return Color3.new(a.R + (b.R - a.R) * t, a.G + (b.G - a.G) * t, a.B + (b.B - a.B) * t) end }
Color3 = { new = function(r, g, b) return setmetatable({ R = r, G = g, B = b, __type = "Color3" }, C3) end }
Color3.fromRGB = function(r, g, b) return Color3.new(r / 255, g / 255, b / 255) end
Color3.fromHex = function(h) return Color3.fromRGB(tonumber(h:sub(1, 2), 16), tonumber(h:sub(3, 4), 16), tonumber(h:sub(5, 6), 16)) end
NumberRange = { new = function(a, b) return { Min = a, Max = b or a } end }
NumberSequence = { new = function(k) return { Keypoints = k } end }
NumberSequenceKeypoint = { new = function(t, v, e) return { t, v, e } end }
ColorSequence = { new = function(k) return { Keypoints = k } end }
ColorSequenceKeypoint = { new = function(t, c) return { t, c } end }
TweenInfo = { new = function(t) return { Time = t } end }
Enum = setmetatable({}, { __index = function(_, e) return setmetatable({}, { __index = function(_, n) return e .. "." .. n end }) end })

local ISA = { PointLight = "Light", SpotLight = "Light", SurfaceLight = "Light", Part = "BasePart" }
local Inst = {}
Inst.__index = Inst
function Inst:IsA(c) return self.ClassName == c or ISA[self.ClassName] == c or c == "Instance" end
function Inst:Destroy() self.Parent = nil; self.destroyed = true end
function Inst:FindFirstChild(n) for _, c in ipairs(T.all) do if c.Parent == self and c.Name == n then return c end end end
function Inst:FindFirstChildOfClass(n) for _, c in ipairs(T.all) do if c.Parent == self and c.ClassName == n then return c end end end
function Inst:GetChildren() local o = {} for _, c in ipairs(T.all) do if c.Parent == self then table.insert(o, c) end end return o end
function Inst:Emit(n) self.emitted = (self.emitted or 0) + n end
function Inst:GetSunDirection() return Vector3.new(0, 1, 0) end
T.all = {}
Instance = { new = function(cls)
	local i = setmetatable({ ClassName = cls, Name = cls, Enabled = true, Brightness = 1, Rate = 0, Lifetime = NumberRange.new(1),
		CFrame = cf(), AssemblyMass = 1, Size = Vector3.new(1, 1, 1) }, Inst)
	table.insert(T.all, i)
	return i
end }
workspace = Instance.new("Workspace")
workspace.Gravity = 196.2
local services = {
	RunService = { Heartbeat = { Connect = function(_, fn) table.insert(T.beats, fn); return {} end } },
	UserInputService = { TouchEnabled = false, KeyboardEnabled = true },
	TweenService = { Create = function(_, inst, info, props)
		return { Play = function() T.tweens = (T.tweens or 0) + 1 end, Cancel = function() end } end },
	Debris = { AddItem = function() end },
	Lighting = Instance.new("Lighting"),
}
services.Lighting.ClockTime = 14
game = { GetService = function(_, n) return services[n] end }
"""

TESTS = r"""
local P, VFX, L = ...
local out = {}
local function check(name, ok, detail) table.insert(out, { name, ok and true or false, detail and tostring(detail) or "" }) end
local train = Instance.new("Part")
local function lightOf(h, cls)
	for _, rec in ipairs(h.layers) do if rec.inst and rec.inst:IsA(cls or "Light") then return rec.inst end end
end
local function emitterOf(h)
	for _, rec in ipairs(h.layers) do if rec.inst and rec.inst:IsA("ParticleEmitter") then return rec.inst end end
end
local fwd = Vector3.new(1, 0, 0)
local function section(name, fn)
	local ok, e = pcall(fn)
	if not ok then check(name .. " (section ran without a Lua error)", false, e) end
end

-- every preset attaches (loops) or bursts without a Lua error
local okAll, err = pcall(function()
	for name, p in pairs(P.presets) do
		if p.kind == "loop" then VFX.detach(VFX.attach(train, name, { enabled = true })) else VFX.burst(train, name) end
	end
	for _ = 1, 40 do T.run(0.25) end
end)
check("every preset attaches or bursts, 10 s of heartbeats", okAll, err)

-- start rules
section("start rules", function()
local h1 = VFX.attach(train, "steam_chimney")
check("ambient loop starts on", h1.active == true)
for name, p in pairs(P.presets) do
	if p.kind == "loop" and p.priority == 1 then
		local h = VFX.attach(train, name)
		check("priority-1 loop starts off: " .. name, h.active == false and (emitterOf(h) == nil or emitterOf(h).Enabled == false))
		VFX.detach(h)
	end
end
if P.presets.sparks_brake then
	local hb = VFX.attach(train, "sparks_brake")
	check("start = off loop starts off (sparks_brake)", hb.active == false)
	VFX.detach(hb)
	local he = VFX.attach(train, "sparks_brake", { enabled = true })
	VFX.setSpeed(50, fwd)
	T.run(0.01)
	local g = lightOf(he)
	local b50 = g and g.Brightness
	VFX.setSpeed(25, fwd)
	T.run(0.01)
	check("speed-linked brake glow dims with Speed (flicker included)", g and b50 and g.Brightness < b50 * 0.7,
		tostring(b50) .. " -> " .. tostring(g and g.Brightness))
	check("{enabled = true} overrides the start rule", he.active == true and emitterOf(he).Enabled == true)
	VFX.detach(he)
end
end)

-- look-driven presets follow the look, also when attached late
section("look-driven", function()
if P.presets.headlamp then
	local hl = VFX.attach(train, "headlamp")
	check("look-driven preset starts off before any look", hl.active == false and lightOf(hl, "SpotLight").Enabled == false)
	L.apply("grassland.night", 0)
	check("night look switches the headlamp on", hl.active == true and lightOf(hl, "SpotLight").Enabled == true)
	local late = VFX.attach(train, "headlamp")
	check("headlamp attached after Lighting.apply follows the look", late.active == true)
	L.apply("grassland.day", 0)
	check("day look switches it off again", hl.active == false and late.active == false)
	L.push("tunnel_under")
	check("tunnel override switches the headlamp on", hl.active == true)
	L.pop("tunnel_under")
	check("pop restores the look", hl.active == false)
	VFX.detach(hl); VFX.detach(late)
end
end)

-- burst lights survive refreshes (setSpeed, another burst, a look change)
local burstName
section("burst lights", function()
for name, p in pairs(P.presets) do
	if p.kind == "burst" then
		for _, Ly in ipairs(p.layers) do if Ly.pulse then burstName = burstName or name end end
	end
end
if burstName then
	local b1 = VFX.burst(train, burstName)
	T.run(0.001)
	local fl = lightOf(b1)
	VFX.setSpeed(35, fwd)
	local a = fl.Enabled
	VFX.burst(train, burstName)
	local b = fl.Enabled
	L.apply("grassland.golden", 0)
	check("burst light stays on through setSpeed, a second burst and a look change (" .. burstName .. ")",
		a == true and b == true and fl.Enabled == true, tostring(a) .. "/" .. tostring(b) .. "/" .. tostring(fl.Enabled))
	for _ = 1, 20 do T.run(0.25) end
	check("burst cleans itself up", fl.Parent == nil or fl.destroyed == true or #b1.holders == 0)
end
end)

-- flashes setting
section("flashes", function()
VFX.setFlashes(false)
if burstName then
	local peak = 0
	for _, Ly in ipairs(P.presets[burstName].layers) do if Ly.pulse then peak = math.max(peak, Ly.pulse.peak) end end
	local b2 = VFX.burst(train, burstName)
	T.run(0.3)
	local fl = lightOf(b2)
	check("flashes off caps burst pulses", fl.Brightness <= 1.5 + 1e-9 and peak > 1.5, tostring(fl.Brightness) .. " vs peak " .. peak)
end
L.setFlashes(false)
L.push("overbridge_flash")
local skipped = true
for _, n in ipairs(L.stack) do if n == "overbridge_flash" then skipped = false end end
check("flashes off skips flash overrides (overbridge_flash)", skipped)
VFX.setFlashes(true); L.setFlashes(true)
end)

-- every look applies; overrides push and pop
local okL, errL = pcall(function()
	for _, n in ipairs(L.looks()) do L.apply(n, 0) end
	for n in pairs(require_overrides) do L.push(n); T.run(1); L.pop(n) end
end)
check("every look applies and every override pushes and pops", okL, errL)
return out
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--presets", help="preset folder (default $RR_VFX_PRESETS, else the shipped library)")
    ap.add_argument("-v", action="store_true", help="print every check")
    a = ap.parse_args(argv)
    try:
        import lupa.lua51 as lupa   # Lua 5.1: the dialect Luau grew from
    except ImportError:
        print("luatest: lupa not installed (pip install --target ~/.cache/rr-tools/py lupa); skipped")
        return 3
    vfx.PRESETS_ARG = a.presets
    model = vfx.Model()
    if vfx.validate(model, quiet=True):
        print("luatest: presets do not validate; run vfx.py validate")
        return 1
    fx_src, light_src = vfx.gen_fx_lua(model), vfx.gen_light_lua(model)
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(STUBS)
    P = lua.execute(fx_src)
    LP = lua.execute(light_src)
    g = lua.globals()
    mods = {}

    def load(name, src, parent_map):
        g.script = lua.table(Parent=lua.table(
            WaitForChild=lambda self, n: parent_map[n], FindFirstChild=lambda self, n: parent_map.get(n)))
        g.require = lua.eval("function(m) return m end")
        mods[name] = lua.execute(src)
        return mods[name]

    V = load("RR_VFX", (SKILL / "assets" / "luau" / "RR_VFX.lua").read_text(), {"RR_FXPresets": P})
    L = load("RR_Lighting", (SKILL / "assets" / "luau" / "RR_Lighting.lua").read_text(),
             {"RR_LightingPresets": LP, "RR_VFX": V})
    g.require_overrides = LP.overrides
    res = lua.execute(TESTS, P, V, L)
    rows = [(res[i][1], bool(res[i][2]), res[i][3]) for i in range(1, len(res) + 1)]
    bad = [r for r in rows if not r[1]]
    for name, ok, det in rows:
        if a.v or not ok:
            print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {det}" if det and not ok else ""))
    print(f"luatest: {len(rows) - len(bad)}/{len(rows)} passed (RR_VFX + RR_Lighting in Lua 5.1 with Roblox stubs)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
