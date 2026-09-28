#!/usr/bin/env python3
"""Run the Luau runtime in a real Lua 5.1 VM against stubbed Roblox services (no Studio needed).

  luatest.py [--presets FILE] [--only parity|runtime] [-v]

  parity   RR_FeelMath.lua vs feelmath.py: every easing style x direction, noise, springs, envelopes, pulses,
           haptic keys, lever curve (signed), spring peak gain (max abs error must be < 1e-9)
  runtime  RR_Feel.lua + the generated RR_FeelPresets.lua: every event plays and steps for 5 s without a Lua
           error; camera and FOV return to rest (default and scripted cameras); targets restore; camera angles
           match feelmath.sample_event frame by frame; reduce motion; flash limiter; hit-stop cooldown and
           animation freeze; lever notch/commit/snapback, two-way and once per junction (ctx.fork); a stalled
           flash never leaves colour on screen; FOV kicks keep a FOV another script set; playFor routing;
           haptics (HapticEffect and gamepad fallback); curve dump

Needs lupa (Lua 5.1 in Python), an optional test dependency:
  pip install --target ~/.cache/rr-tools/py lupa     (this script adds that folder to sys.path)
Stubs model only what RR_Feel touches; they prove logic, not Roblox rendering. Exit 0 = all passed.
"""
import argparse, math, sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path.home() / ".cache" / "rr-tools" / "py"))
import feelmath as fm  # noqa: E402

STUBS = r"""
local T = { now = 0, delays = {}, created = {}, motor = 0, warns = 0, renderFn = nil, haptic_ok = true }
RRT = T
function T.runDue()
	local rest, due = {}, {}
	for _, d in ipairs(T.delays) do
		if d.at <= T.now + 1e-12 then table.insert(due, d) else table.insert(rest, d) end
	end
	T.delays = rest
	for _, d in ipairs(due) do d.fn() end
end
os.clock = function() return T.now end
warn = function(...) T.warns = T.warns + 1 end
task = { delay = function(t, fn) table.insert(T.delays, { at = T.now + t, fn = fn }) end }

local CF = {}
CF.__index = CF
local function cf(x, y, z, p, yw, r) return setmetatable({ x = x or 0, y = y or 0, z = z or 0, p = p or 0, yw = yw or 0, r = r or 0 }, CF) end
CF.__mul = function(a, b) return cf(a.x + b.x, a.y + b.y, a.z + b.z, a.p + b.p, a.yw + b.yw, a.r + b.r) end
CF.__eq = function(a, b) return a.x == b.x and a.y == b.y and a.z == b.z and a.p == b.p and a.yw == b.yw and a.r == b.r end
function CF:Inverse() return cf(-self.x, -self.y, -self.z, -self.p, -self.yw, -self.r) end
CFrame = { new = function(x, y, z) return cf(x, y, z) end, Angles = function(p, y, r) return cf(0, 0, 0, p, y, r) end }

local UD = {}
UD.__index = function(u, k)
	if k == "X" then return { Scale = rawget(u, "xs"), Offset = rawget(u, "xo") } end
	if k == "Y" then return { Scale = rawget(u, "ys"), Offset = rawget(u, "yo") } end
	return UD[k]
end
UDim = { new = function(s, o) return { Scale = s, Offset = o } end }
local function ud(xs, xo, ys, yo) return setmetatable({ xs = xs or 0, xo = xo or 0, ys = ys or 0, yo = yo or 0 }, UD) end
UD.__add = function(a, b) return ud(a.xs + b.xs, a.xo + b.xo, a.ys + b.ys, a.yo + b.yo) end
UD.__eq = function(a, b) return a.xs == b.xs and a.xo == b.xo and a.ys == b.ys and a.yo == b.yo end
UDim2 = { new = ud, fromScale = function(x, y) return ud(x, 0, y, 0) end, fromOffset = function(x, y) return ud(0, x, 0, y) end }

local C3 = {}
C3.__index = C3
function C3:ToHSV()
	local r, g, b = self.R, self.G, self.B
	local mx, mn = math.max(r, g, b), math.min(r, g, b)
	local h, d = 0, mx - mn
	if d > 0 then
		if mx == r then h = ((g - b) / d) % 6 elseif mx == g then h = (b - r) / d + 2 else h = (r - g) / d + 4 end
		h = h / 6
	end
	return h, mx == 0 and 0 or d / mx, mx
end
Color3 = { fromRGB = function(r, g, b) return setmetatable({ R = r / 255, G = g / 255, B = b / 255 }, C3) end }
NumberSequence = { new = function(k) return { keys = k } end }
NumberSequenceKeypoint = { new = function(t, v) return { t, v } end }
FloatCurveKey = { new = function(t, v, m) return { Time = t, Value = v, Mode = m } end }

Enum = setmetatable({}, { __index = function(t, k)
	local sub = setmetatable({}, { __index = function(s, item)
		local v = { Name = item, Value = (item == "Camera") and 200 or 0, EnumType = k }
		rawset(s, item, v)
		return v
	end })
	rawset(t, k, sub)
	return sub
end })

local function signal()
	local s = { conns = {} }
	function s:Connect(fn) table.insert(self.conns, fn) return { Disconnect = function() end } end
	return s
end

local DEFAULTS = {
	Frame = { BackgroundTransparency = 0, Rotation = 0, Visible = true, ZIndex = 1 },
	TextLabel = { BackgroundTransparency = 1, TextTransparency = 0, TextStrokeTransparency = 1, Rotation = 0, Visible = true, ZIndex = 1, Text = "" },
	ImageLabel = { BackgroundTransparency = 1, ImageTransparency = 0, Rotation = 0, Visible = true, ZIndex = 1 },
	CanvasGroup = { GroupTransparency = 0, BackgroundTransparency = 0, Rotation = 0, Visible = true, ZIndex = 1 },
	TextButton = { BackgroundTransparency = 0, TextTransparency = 0, TextStrokeTransparency = 1, Rotation = 0, Visible = true, ZIndex = 1, Text = "" },
	ScrollingFrame = { BackgroundTransparency = 0, Rotation = 0, Visible = true, ZIndex = 1 },
	UIScale = { Scale = 1 },
}
local GUI = { Frame = true, TextLabel = true, ImageLabel = true, CanvasGroup = true, TextButton = true, ScrollingFrame = true }
local Inst = {}
local EVENTS = { MouseButton1Down = true, MouseButton1Click = true, Activated = true, InputBegan = true,
	InputChanged = true, InputEnded = true }
function Inst.__index(o, k)
	local p = rawget(o, "_p")
	if p[k] ~= nil then return p[k] end
	if Inst[k] then return Inst[k] end
	if EVENTS[k] then
		p[k] = signal()
		return p[k]
	end
	return nil
end
function Inst.__newindex(o, k, v)
	local p = rawget(o, "_p")
	if k == "Parent" then
		local old = p.Parent
		if old then
			for i, c in ipairs(rawget(old, "_c")) do if c == o then table.remove(rawget(old, "_c"), i) break end end
		end
		if v then table.insert(rawget(v, "_c"), o) end
	end
	p[k] = v
end
function Inst:FindFirstChild(n) for _, c in ipairs(rawget(self, "_c")) do if c.Name == n then return c end end return nil end
function Inst:FindFirstChildOfClass(cl) for _, c in ipairs(rawget(self, "_c")) do if c.ClassName == cl then return c end end return nil end
function Inst:WaitForChild(n) return self:FindFirstChild(n) end
function Inst:IsA(cl) return self.ClassName == cl or (cl == "GuiObject" and GUI[self.ClassName] == true) end
function Inst:GetDescendants()
	local out = {}
	local function walk(o) for _, c in ipairs(rawget(o, "_c")) do table.insert(out, c) walk(c) end end
	walk(self)
	return out
end
function Inst:Destroy() self.Parent = nil rawget(self, "_p").destroyed = true end
function Inst:Clone() return Instance.new(self.ClassName) end
function Inst:GetPropertyChangedSignal() return signal() end
function Inst:SetWaveformKeys(k) rawget(self, "_p").keys = k end
function Inst:Play() table.insert(T.hapticsPlayed, self) end
function Inst:Fire(...) for _, fn in ipairs(self.Event.conns) do fn(...) end end
T.hapticsPlayed = {}

Instance = { new = function(cl)
	if cl == "HapticEffect" and not T.haptic_ok then error("HapticEffect is not a valid class") end
	local o = setmetatable({ _p = { ClassName = cl, Name = cl }, _c = {} }, Inst)
	for k, v in pairs(DEFAULTS[cl] or {}) do rawget(o, "_p")[k] = v end
	if GUI[cl] then rawget(o, "_p").Position = ud(0, 0, 0, 0) end
	if cl == "BindableEvent" then rawget(o, "_p").Event = signal() end
	if cl == "HapticEffect" then rawget(o, "_p").Ended = signal() end
	table.insert(T.created, o)
	return o
end }

local playerGui = Instance.new("Folder")
playerGui.Name = "PlayerGui"
local tracks = { { Speed = 1, AdjustSpeed = function(self, s) self.Speed = s end } }
T.tracks = tracks
local animator = { ClassName = "Animator", GetPlayingAnimationTracks = function() return tracks end }
local hum = { FindFirstChildOfClass = function(_, c) if c == "Animator" then return animator end end }
local player = { UserId = 7, Character = { FindFirstChildOfClass = function(_, c) if c == "Humanoid" then return hum end end },
	WaitForChild = function(_, n) return playerGui end }
T.playerGui = playerGui
T.camera = { CFrame = CFrame.new(), FieldOfView = 70 }
local services = {
	Players = { LocalPlayer = player },
	RunService = { BindToRenderStep = function(_, n, p, fn) T.renderFn = fn T.renderPriority = p end, IsStudio = function() return true end },
	TweenService = { GetValue = function(_, t, st, dr) return T.ease(st.Name, dr.Name, t) end },
	GuiService = { ReducedMotionEnabled = false, GetPropertyChangedSignal = function() return signal() end },
	HapticService = { IsVibrationSupported = function() return true end, IsMotorSupported = function() return true end,
		SetMotor = function(_, it, m, v) T.motor = v end },
	Workspace = Instance.new("Workspace"),
}
services.Workspace.CurrentCamera = T.camera
services.UserInputService = { InputChanged = signal(), InputEnded = signal(), InputBegan = signal() }
local rs = Instance.new("Folder")
local rrfeel = Instance.new("Folder")
rrfeel.Name = "RRFeel"
rrfeel.Parent = rs
for _, n in ipairs({ "RR_Feel", "RR_FeelMath", "RR_FeelPresets" }) do
	local m = Instance.new("ModuleScript")
	m.Name = n
	m.Parent = rrfeel
end
services.ReplicatedStorage = rs
T.services = services
T.printed = 0
print = function() T.printed = T.printed + 1 end
game = { GetService = function(_, n) return services[n] end }
"""


def lua_runtime():
    try:
        from lupa import lua51
    except ImportError:
        return None
    return lua51.LuaRuntime(unpack_returned_tuples=True)


def parity(L, verbose=False):
    src = (SKILL / "assets" / "luau" / "RR_FeelMath.lua").read_text()
    M = L.execute(src)
    worst = {}

    def upd(k, a, b):
        worst[k] = max(worst.get(k, 0.0), abs(a - b))
    for st in fm.STYLES:
        for dr in fm.DIRECTIONS:
            for i in range(101):
                upd("ease", M.easeOwn(st, dr, i / 100), fm.ease(st, dr, i / 100))
    for i in range(400):
        x = i * 0.137 - 7
        upd("noise1", M.noise1(11, x), fm.noise1(11, x))
    for shape in ("sin", "cos", "noise"):
        for i in range(80):
            t = i / 100
            upd("spring", M.spring(t, 0.7, 6, 0.35, shape, 0.6, 67), fm.spring(t, 0.7, 6, 0.35, shape, 0.6, 67))
    for i in range(120):
        t = i / 50
        upd("envelope", M.envelope(t, 0.1, 0.2, 0.9, "Quad", "Sine"), fm.envelope(t, 0.1, 0.2, 0.9, "Quad", "Sine"))
        upd("pulse", M.pulse(t, 0.3, 0.95, 1.2), fm.pulse(t, 0.3, 0.95, 1.2))
    keys = [[0, 1.0], [200, 0.8], [600, 0.3], [1000, 0]]
    lk = L.table_from([L.table_from(k) for k in keys])
    for i in range(130):
        upd("keysAt", M.keysAt(lk, i / 100), fm.keys_at(keys, i / 100))
    for i in range(-100, 101):
        upd("lever", M.leverDisplay(i / 100, 0.7, 1.6), fm.lever_display(i / 100, 0.7, 1.6))
    for shape in ("sin", "cos", "noise"):
        for f, z, d in ((4, 0.05, 0.5), (6, 0.35, 0.4), (12, 0.3, 0.25), (1.2, 0.6, 1.5)):
            upd("peakGain", M.peakGain(f, z, shape, d), fm.peak_gain(f, z, shape, d))
    bad = {k: v for k, v in worst.items() if v > 1e-9}
    lines = [f"  parity {k}: max |lua - python| = {v:.2e}" for k, v in worst.items()] if verbose else []
    return not bad, lines + ([f"  parity FAIL {k}: {v:.3e}" for k, v in bad.items()] or
                             [f"  parity: RR_FeelMath.lua == feelmath.py on {len(worst)} functions (max err "
                              f"{max(worst.values()):.1e})"])


class Rt:
    """One fresh RR_Feel runtime in Lua with stubs; step() advances real time by one 60 Hz frame."""

    def __init__(self, presets_lua, haptic_ok=True, reduce=False, scripted_camera=False):
        self.L = L = lua_runtime()
        L.execute(STUBS)
        self.T = L.globals()["RRT"]
        self.T.haptic_ok = haptic_ok
        self.T.services.GuiService.ReducedMotionEnabled = reduce
        math_src = (SKILL / "assets" / "luau" / "RR_FeelMath.lua").read_text()
        feel_src = (SKILL / "assets" / "luau" / "RR_Feel.lua").read_text()
        L.execute("RRMODS = {}")
        mods = L.globals()["RRMODS"]
        mods.RR_FeelMath = L.execute(math_src)
        mods.RR_FeelPresets = L.execute(presets_lua)
        self.T.ease = mods.RR_FeelMath.easeOwn
        L.execute("""
            script = { Parent = { WaitForChild = function(_, n) return { __module = n } end } }
            require = function(m) return RRMODS[m.__module or m.Name] end
        """)
        self.F = L.execute(feel_src)
        mods.RR_Feel = self.F
        self.scripted = scripted_camera
        self.dt = 1 / 60
        self.frame = 0
        self.targets = {}
        self.cues = []
        self.F.Cue.Event.Connect(self.F.Cue.Event, lambda name, cue: self.cues.append(name))

    def target_table(self, roles):
        L = self.L
        tbl = L.table()
        for r in roles:
            cl = "TextLabel" if r == "cash" else "Frame"
            o = L.globals().Instance.new(cl)
            o.Name = r
            o.Parent = self.T.playerGui   # a live GuiObject; effects on unparented (destroyed) targets stop
            child = L.globals().Instance.new("TextLabel")
            child.Parent = o
            self.targets[r] = (o, child)
            tbl[r] = o
        return tbl

    def step(self):
        T = self.T
        T.now = self.frame * self.dt
        T.runDue()
        if not self.scripted:
            T.camera.CFrame = self.L.globals().CFrame.new()
        T.renderFn(self.dt)
        self.frame += 1
        c = T.camera.CFrame
        return (math.degrees(c.p), math.degrees(c.yw), math.degrees(c.r), c.x, c.y, T.camera.FieldOfView)


def runtime(presets_lua, model, verbose=False):
    ok, out = True, []
    roles = list(model.raw["roles"])

    def check(cond, msg):
        nonlocal ok
        if not cond:
            ok = False
            out.append("  FAIL " + msg)
        elif verbose:
            out.append("  ok   " + msg)

    # 1) every event plays, steps, and leaves camera, FOV, overlay and targets at rest
    for name in model.events:
        for reduce in (False, True):
            rt = Rt(presets_lua, reduce=reduce)
            ctx = rt.L.table_from({"side": -1})
            ctx.targets = rt.target_table(roles)
            ctx.count = rt.L.table_from({"amount": 120})
            base = {r: o.BackgroundTransparency for r, (o, child) in rt.targets.items()}
            h = rt.F.play(name, ctx)
            for _ in range(300):
                last = rt.step()
            h.Stop(h)
            for _ in range(3):
                last = rt.step()
            check(all(abs(v) < 1e-9 for v in last[:5]) and abs(last[5] - 70) < 1e-9,
                  f"{name}{' (reduce motion)' if reduce else ''}: camera and FOV back at rest {tuple(round(v, 4) for v in last)}")
            smp = fm.sample_event(model.r, name, reduce_motion=reduce)
            away = {k.split(":")[2] for k, v in smp["lanes"].items() if ":tween:" in k and k.split(":")[3] in fm.REST
                    and abs(v[-1] - fm.REST[k.split(":")[3]]) > 1e-9 and k.split(":")[3] in ("x", "y", "alpha")}
            for r, (o, child) in rt.targets.items():
                if r not in away:   # targets an event sends away on purpose (a console that leaves) stay away
                    sc = o.FindFirstChild(o, "RR_FeelScale")
                    check(sc is None or abs(sc.Scale - 1) < 1e-9,
                          f"{name}: {r} scale restored")
                    check(abs(o.BackgroundTransparency - base[r]) < 1e-9, f"{name}: {r} transparency restored")
            ov = rt.T.playerGui.FindFirstChild(rt.T.playerGui, "RR_FeelOverlay")
            if ov:
                fl = ov.FindFirstChild(ov, "Flash")
                check(abs(fl.BackgroundTransparency - 1) < 1e-9, f"{name}: screen flash cleared")
    out.append(f"  runtime: {len(model.events)} events x (full, reduce motion) played and stepped 5 s in Lua 5.1")

    # 1b) UI channels really drive the targets
    rt = Rt(presets_lua)
    ctx = rt.L.table()
    ctx.targets = rt.target_table(roles)
    ctx.count = rt.L.table_from({"amount": 120})
    rt.F.play("alert_fare_banked", ctx)
    tk, tk_child = rt.targets["ticket"]
    st, _ = rt.targets["stamp"]
    cash, _ = rt.targets["cash"]
    rt.step()
    mid = (tk.Position.xs, tk_child.TextTransparency, st.Visible)
    for _ in range(4):
        rt.step()
    check(mid[0] > 0.5 and mid[1] > 0.5 and mid[2] is False,
          f"fare_banked frame 1: ticket off to the right {mid[0]:.2f}, faded {mid[1]:.2f}, stamp hidden before its slam")
    for _ in range(20):
        rt.step()
    check(st.Visible is True, "stamp visible once its slam starts")
    for _ in range(80):
        rt.step()
    check(abs(tk.Position.xs) < 1e-9 and abs(tk_child.TextTransparency) < 1e-9 and str(cash.Text) == "120",
          f"fare_banked end: ticket home, opaque, cash counted to {cash.Text}")

    # 1c) UI parity: the ticket slide and fade match the preview lanes frame by frame; reduce motion fades in place
    for reduce in (False, True):
        rt = Rt(presets_lua, reduce=reduce)
        ctx = rt.L.table()
        ctx.targets = rt.target_table(roles)
        rt.F.play("hud_ticket_leave", ctx)
        smp = fm.sample_event(model.r, "hud_ticket_leave", reduce_motion=reduce)
        kx = next(k for k in smp["lanes"] if k.endswith(":tween:ticket:x"))
        ka = [k for k in smp["lanes"] if k.endswith(":tween:ticket:alpha") or k.endswith(":tween:ticket:fadealpha")]
        tk, tk_child = rt.targets["ticket"]
        worst = 0.0
        for i in range(1, 25):
            rt.step()
            a = 1.0
            for k in ka:
                a *= smp["lanes"][k][i]
            worst = max(worst, abs(tk.Position.xs - smp["lanes"][kx][i]), abs((1 - tk_child.TextTransparency) - a))
        check(worst < 1e-9, f"hud_ticket_leave{' (reduce motion: fades in place)' if reduce else ''}: Lua UI == preview "
                            f"(max diff {worst:.1e}, x ends {tk.Position.xs:.2f})")

    # 2) camera parity with feelmath.sample_event, frame by frame
    for name, side in (("boiler_burst", 1), ("coupling_snap", 1), ("lever_commit", -1), ("alert_breakdown", 1)):
        rt = Rt(presets_lua)
        ctx = rt.L.table_from({"side": side})
        ctx.targets = rt.target_table(roles)
        rt.F.play(name, ctx)
        s = fm.sample_event(model.r, name, side=side)
        L = s["lanes"]
        worst = 0.0
        for i in range(1, min(len(s["t"]), 150)):
            got = rt.step()   # the runtime advances its clock before drawing: step k == preview frame k + 1
            want = [sum(L[k][i] for k in L if (k == "cam:" + a) or (":camkick:" in k and k.endswith(":" + a)))
                    for a in ("pitch", "yaw", "roll")]
            want += [L.get("cam:x", [0] * (i + 1))[i], L.get("cam:y", [0] * (i + 1))[i],
                     70 + sum(L[k][i] for k in L if k.endswith(":fovkick"))]
            worst = max(worst, max(abs(a - b) for a, b in zip(got, want)))
        check(worst < 1e-6, f"{name}: Lua camera == Python preview frame by frame (max diff {worst:.1e})")
    out.append("  runtime: camera and FOV match the preview simulation frame by frame")

    # 3) scripted camera: no accumulation
    rt = Rt(presets_lua, scripted_camera=True)
    rt.F.play("boiler_burst", rt.L.table())
    for _ in range(300):
        last = rt.step()
    check(all(abs(v) < 1e-9 for v in last[:5]), f"scripted camera returns to rest after boiler_burst {last[:5]}")

    # 4) reduce motion
    rt = Rt(presets_lua, reduce=True)
    rt.F.play("boiler_burst", rt.L.table())
    mx = max(max(abs(v) for v in rt.step()[:5]) for _ in range(120))
    check(mx < 1e-12, "reduce motion: boiler_burst leaves the camera still")
    rt.F.setSetting("reduceMotion", False)
    check(rt.F.settings.reduceMotion is False, "setSetting overrides Roblox's Reduce Motion")

    # 5) flash limiter: 6 window smashes in 0.5 s start at most 3 screen flashes
    rt = Rt(presets_lua)
    started = 0
    for k in range(30):
        if k % 5 == 0:
            rt.F.play("windows_smash", rt.L.table())
        rt.step()
        started = max(started, rt.F.stats().flashesLastSecond)
    check(started <= model.r["a11y"]["flash"]["per_second_max"], f"flash limiter: {started} screen flashes in 1 s")

    # 6) hit-stop: cooldown and animation freeze
    rt = Rt(presets_lua)
    check(rt.F.hitStop(70) is True and rt.F.hitStop(70) is False, "hit-stop cooldown refuses a second stop")
    rt.step()
    check(rt.T.tracks[1].Speed == 0, "hit-stop freezes the character's animation tracks")
    for _ in range(12):
        rt.step()
    check(rt.T.tracks[1].Speed == 1, "hit-stop restores animation speed")

    # 7) lever
    rt = Rt(presets_lua)
    ctx = rt.L.table_from({"side": -1})
    ctx.targets = rt.target_table(roles)
    v1 = rt.F.leverDrag(0.5, ctx)
    check(v1 < 0.5, f"lever: knob lags the finger before the detent ({v1:.3f} at 0.5)")
    v2 = rt.F.leverDrag(0.75, ctx)
    rt.F.leverDrag(0.9, ctx)
    check(v2 == 1 and rt.cues.count("lever_commit") == 1, "lever: commit fires once past the detent")
    check(rt.F.leverRelease(ctx) == "committed", "lever: release after commit keeps it")
    rt.F.leverReset()
    check(rt.F.leverRelease(ctx) == "snapback", "lever: early release snaps back")
    # two-way, notch before the commit, once per junction (ctx.fork)
    rt = Rt(presets_lua)
    ctx = rt.L.table_from({"fork": 1})
    ctx.targets = rt.target_table(roles)
    lv = model.r["lever"]
    v = rt.F.leverDrag(-(lv["notch"] + lv["detent"]) / 2, ctx)
    rt.step()
    knob, _ = rt.targets["lever_knob"]
    check(v < 0 and knob.FindFirstChild(knob, "RR_FeelScale") is not None and "lever_commit" not in rt.cues,
          f"lever: left drag gives a negative knob ({v:.3f}); the detent tick plays at the notch, before the commit")
    rt.F.leverDrag(-0.9, ctx)
    yaws = [rt.step()[1] for _ in range(6)]
    check(rt.cues.count("lever_commit") == 1 and max(yaws) > 0 and min(yaws) >= 0,
          f"lever: a left commit turns the view left, toward the pull (Roblox + yaw = left; peak {max(yaws):.3f})")
    check(rt.F.leverRelease(ctx) == "committed" and rt.F.leverDrag(0.9, ctx) == -1, "lever: stays committed to its side")
    ctx2 = rt.L.table_from({"fork": 2})
    ctx2.targets = ctx.targets
    for u in (0.2, 0.5, 0.8):
        rt.F.leverDrag(u, ctx2)
    check(rt.cues.count("lever_commit") == 2, "lever: a new junction (ctx.fork) commits again")
    seen = []
    rt.F.animateValue(0, 35, model_lever_snap(rt, model), lambda v: seen.append(v))
    for _ in range(20):
        rt.step()
    check(abs(seen[-1] - 35) < 1e-9 and max(seen) > 35, "animateValue: world lever throw overshoots (Back) and lands")

    # 7b) a flash that ends during a stall (hitch, app switch) leaves nothing on screen
    rt = Rt(presets_lua)
    rt.F.play("alert_pressure_high", rt.L.table())
    for _ in range(12):
        rt.step()
    rt.frame += 60
    for _ in range(5):
        rt.step()
    ov = rt.T.playerGui.FindFirstChild(rt.T.playerGui, "RR_FeelOverlay")
    vig = [ov.FindFirstChild(ov, f"Vignette{i}").BackgroundTransparency for i in range(1, 5)] if ov else [0]
    check(all(abs(x - 1) < 1e-12 for x in vig), f"stalled vignette flash is cleared ({min(vig):.3f})")

    # 7c) FOV kick as a delta: a FOV set by another script mid-kick survives
    rt = Rt(presets_lua)
    rt.F.play("boiler_burst", rt.L.table())
    for _ in range(20):
        rt.step()
    rt.T.camera.FieldOfView = 50
    for _ in range(300):
        last = rt.step()
    check(abs(last[5] - 50) < 1e-9, f"FOV set by a fail camera during a kick is kept ({last[5]:.4f})")

    # 7d) playFor routes by who
    rt = Rt(presets_lua)
    got = [rt.F.playFor("shovel_coal", 7, rt.L.table()) is not None, rt.F.playFor("shovel_coal", 8, rt.L.table()) is None,
           rt.F.playFor("lever_commit_crew", 7, rt.L.table()) is None, rt.F.playFor("lever_commit_crew", 8, rt.L.table()) is not None,
           rt.F.playFor("depart", None, rt.L.table()) is not None]
    check(all(got), f"playFor: actor only on the actor, crew only elsewhere, all everywhere {got}")

    # 8) haptics
    rt = Rt(presets_lua)
    rt.F.play("alert_fare_banked", rt.L.table())
    for _ in range(20):
        rt.step()
    check(len(rt.T.hapticsPlayed) == 0, "haptic waits for its first key (400 ms)")
    for _ in range(20):
        rt.step()
    hp = list(rt.T.hapticsPlayed.values())
    check(len(hp) == 1 and hp[0]["keys"][1].Time == 0, "HapticEffect plays with keys shifted to start at 0")
    rt = Rt(presets_lua, haptic_ok=False)
    rt.F.play("boiler_burst", rt.L.table())
    peak = max((rt.step(), rt.T.motor)[1] for _ in range(30))
    for _ in range(80):
        rt.step()
    check(peak > 0.5 and rt.T.motor == 0, f"gamepad fallback drives SetMotor (peak {peak:.2f}) and stops it")
    rt.F.setSetting("haptics", False)

    # 9) the Studio demo builds, every button plays, the lever drags, commits and snaps
    rt = Rt(presets_lua)
    rt.L.execute((SKILL / "assets" / "luau" / "RR_FeelDemo.client.lua").read_text())
    buttons = [o for o in rt.T.created.values() if o.ClassName == "TextButton" and o.Name != "Knob"]
    clicked = 0
    for b in buttons:
        if str(b.Text) == "DUMP":
            continue
        for sig in ("MouseButton1Down", "MouseButton1Click"):
            for fn in getattr(b, sig).conns.values():
                fn()
        clicked += 1
        for _ in range(12):
            rt.step()
    check(clicked >= len(model.events) + 5, f"demo: {clicked} buttons clicked without a Lua error")
    knob = next(o for o in rt.T.created.values() if o.Name == "Knob")
    E = rt.L.globals().Enum
    mk = lambda typ, x: rt.L.table_from({"UserInputType": getattr(E.UserInputType, typ), "Position": rt.L.table_from({"X": x})})  # noqa: E731
    rt.cues.clear()
    for fn in knob.InputBegan.conns.values():
        fn(mk("MouseButton1", 100))
    uis = rt.T.services.UserInputService
    for x in (130, 160, 200, 230):
        for fn in uis.InputChanged.conns.values():
            fn(mk("MouseMovement", x))
        rt.step()
    for _ in range(40):
        rt.step()
    for fn in uis.InputEnded.conns.values():
        fn(mk("MouseButton1", 230))
    check(rt.cues.count("lever_commit") == 1 and abs(knob.Position.xo - (-22 + 120)) < 1e-9,
          f"demo lever: drag commits once and the knob lands at the end ({knob.Position.xo})")

    # 10) curve dump
    rt = Rt(presets_lua)
    lines = str(rt.F.curveDump(10)).splitlines()
    check(len(lines) == 11 * 3 * 11, f"curveDump: {len(lines)} lines")
    check(rt.T.renderPriority == 201, "camera effects bound after the camera scripts (Camera + 1)")
    return ok, out


def model_lever_snap(rt, model):
    sp = model.r["lever"]["snap"]
    return rt.L.table_from({"style": sp["style"], "dir": sp["dir"], "dur": sp["dur"]})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--presets")
    ap.add_argument("--only", choices=("parity", "runtime"))
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args(argv)
    L = lua_runtime()
    if L is None:
        print("SKIP luatest: lupa not installed (pip install --target ~/.cache/rr-tools/py lupa)")
        return 3
    import feel
    model = feel.Model(a.presets)
    ok = True
    if a.only in (None, "parity"):
        good, lines = parity(L, a.v)
        ok &= good
        print("\n".join(lines))
    if a.only in (None, "runtime"):
        good, lines = runtime(feel.gen_presets_lua(model), model, a.v)
        ok &= good
        print("\n".join(lines))
    print("luatest PASS" if ok else "luatest FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
