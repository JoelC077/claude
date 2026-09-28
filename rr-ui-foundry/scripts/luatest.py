#!/usr/bin/env python3
"""Run the shipped RR_UIKit in a real Lua 5.1 VM against stubbed Roblox services and a stub layout engine.

  luatest.py [--package DIR] [--only parity|runtime] [-v]

  parity   every screen x device x board: mount the generated package, apply the board, measure every visible
           GuiObject with the stub layout engine (Scale + Offset, AnchorPoint, UIAspectRatioConstraint
           FitWithinMaxSize, UIScale, ScreenInsets) and compare with uimodel.resolve (the HTML boards):
           rects within 0.5 px, same visibility, texts, text sizes, fills, gradients and text colours
  runtime  derived from each spec (any screen name, ids, states, data, types): every machine transition
           (state + look == the model), illegal events, disabled controls, set/cycle actions (data + look),
           string actions, gamepad default focus, NextSelection links, modal SelectionGroup, key glyphs,
           ButtonB bind/unbind, press feedback, reduce motion, fallback fade, live reskin, resize phone -> PC
           and -> notched phone, HUD push / merge / expiry / sticky / clear / overflow / slot fill / unknown
           type, touch-zone lift (worst case, real JumpButton, TouchGui added late, button shown late),
           RR_Feel hand-off. A check the spec gives nothing to test is a named SKIP; 0 checks = FAIL.

  luatest.py --package PKG --specs a.json,b.json    (ui.py build passes both)
Without --package it builds a temporary package from specs/*.json (ui.py build --no-parity) and deletes it.
Needs lupa:
  pip install --target ~/.cache/rr-tools/py lupa     (this script adds that folder to sys.path)
Stubs model what RR_UIKit touches; they prove logic and layout math, not Roblox rendering.
Exit 0 = all passed, 1 = failures (or nothing tested), 3 = skipped (lupa missing).
"""
import sys
sys.dont_write_bytecode = True  # noqa: E402  (keep the skill folder free of __pycache__)
import argparse, re, shutil, subprocess, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path.home() / ".cache" / "rr-tools" / "py"))
import uimodel as U  # noqa: E402

STUBS = r"""
local T = { now = 0, delays = {}, warns = {}, tweens = 0, bound = {}, device = nil }
RRT = T
local Sig = {}
Sig.__index = Sig
local function signal() return setmetatable({ fns = {} }, Sig) end
function Sig:Connect(fn)
	table.insert(self.fns, fn)
	local s = self
	return { Connected = true, Disconnect = function() for i, f in ipairs(s.fns) do if f == fn then table.remove(s.fns, i) break end end end }
end
function Sig:Fire(...) local list = {} for i, f in ipairs(self.fns) do list[i] = f end for _, f in ipairs(list) do f(...) end end
T.signal = signal

Enum = setmetatable({}, { __index = function(t, typ)
	local e = setmetatable({}, { __index = function(tt, name) local it = { Name = name, EnumType = typ } rawset(tt, name, it) return it end })
	rawset(t, typ, e)
	return e
end })

UDim = { new = function(s, o) return { Scale = s or 0, Offset = o or 0 } end }
local U2 = {}
U2.__index = function(u, k)
	if k == "X" then return { Scale = rawget(u, "xs"), Offset = rawget(u, "xo") } end
	if k == "Y" then return { Scale = rawget(u, "ys"), Offset = rawget(u, "yo") } end
end
local function ud2(xs, xo, ys, yo) return setmetatable({ xs = xs or 0, xo = xo or 0, ys = ys or 0, yo = yo or 0 }, U2) end
U2.__add = function(a, b) return ud2(a.xs + b.xs, a.xo + b.xo, a.ys + b.ys, a.yo + b.yo) end
UDim2 = { new = ud2, fromScale = function(x, y) return ud2(x, 0, y, 0) end, fromOffset = function(x, y) return ud2(0, x, 0, y) end }
Vector2 = { new = function(x, y) return { X = x or 0, Y = y or 0 } end }
local function hex2(v) v = math.floor(v * 255 + 0.5) if v < 0 then v = 0 end if v > 255 then v = 255 end return string.format("%02X", v) end
Color3 = {
	fromHex = function(h) h = string.upper(string.gsub(h, "#", "")) return { hex = "#" .. h } end,
	new = function(r, g, b) return { hex = "#" .. hex2(r) .. hex2(g) .. hex2(b) } end,
}
ColorSequence = { new = function(a, b) return { Keypoints = { { Value = a }, { Value = b or a } } } end }
Font = { fromEnum = function(e) return { enum = e.Name } end, new = function(f, w) return { family = f, weight = w and w.Name } end }
TweenInfo = { new = function(...) return { ... } end }
task = { delay = function(t, fn) table.insert(T.delays, { at = T.now + (t or 0), fn = fn }) end, spawn = function(fn, ...) fn(...) end, wait = function() end }
os.clock = function() return T.now end
warn = function(...) local p = {} for i = 1, select("#", ...) do p[i] = tostring(select(i, ...)) end table.insert(T.warns, table.concat(p, " ")) end
function T.advance(dt)
	T.now = T.now + dt
	local guard = 0
	while true do
		local due, rest = nil, {}
		for _, d in ipairs(T.delays) do
			if not due and d.at <= T.now + 1e-9 then due = d else table.insert(rest, d) end
		end
		T.delays = rest
		if not due then break end
		due.fn()
		guard = guard + 1
		if guard > 10000 then error("delay loop") end
	end
end

local GUIOBJ = { Frame = true, TextLabel = true, ImageLabel = true, TextButton = true, ImageButton = true }
local EVENTS = { MouseEnter = true, MouseLeave = true, MouseButton1Down = true, MouseButton1Up = true, Activated = true,
	Event = true, SelectionGained = true, SelectionLost = true, ChildAdded = true, DescendantAdded = true }
local IM = {}
local function defaults(class)
	local p = { Name = class, Visible = true, ZIndex = 1 }
	if GUIOBJ[class] then
		p.Size = ud2(0, 100, 0, 100) p.Position = ud2(0, 0, 0, 0) p.AnchorPoint = Vector2.new(0, 0)
		p.Rotation = 0 p.BackgroundTransparency = 0 p.BackgroundColor3 = Color3.new(1, 1, 1)
		p.Selectable = false p.Active = false p.ClipsDescendants = false
	end
	if class == "TextLabel" or class == "TextButton" then p.Text = "" p.TextSize = 14 p.TextTransparency = 0 p.TextColor3 = Color3.new(0, 0, 0) end
	if class == "ImageLabel" or class == "ImageButton" then p.Image = "" p.ImageTransparency = 0 end
	if class == "UIStroke" then p.Thickness = 1 p.Transparency = 0 p.Color = Color3.new(0, 0, 0) end
	if class == "UIScale" then p.Scale = 1 end
	if class == "UIAspectRatioConstraint" then p.AspectRatio = 1 end
	if class == "ScreenGui" then p.Enabled = true p.AbsoluteSize = Vector2.new(0, 0) p.AbsolutePosition = Vector2.new(0, 0) end
	return p
end
local IMT = {}
IMT.__index = function(o, k)
	local m = IM[k]
	if m then return m end
	local p = rawget(o, "_p")
	if p[k] ~= nil then return p[k] end
	if EVENTS[k] then local s = signal() p[k] = s return s end
	if k == "AbsoluteSize" or k == "AbsolutePosition" then
		local x, y, w, h = T.layout(o)
		if k == "AbsoluteSize" then return Vector2.new(w, h) end
		return Vector2.new(x, y)
	end
	return nil
end
IMT.__newindex = function(o, k, v)
	local p = rawget(o, "_p")
	if k == "Parent" then
		local old = p.Parent
		if old then local kids = rawget(old, "_kids") for i, c in ipairs(kids) do if c == o then table.remove(kids, i) break end end end
		p.Parent = v
		if v then table.insert(rawget(v, "_kids"), o) end
		if v and p.ClassName == "ScreenGui" then T.placeGui(o) end
		if v then
			local ca = rawget(v, "_p").ChildAdded
			if ca then ca:Fire(o) end
			local a = v
			while a do
				local da = rawget(a, "_p").DescendantAdded
				if da then da:Fire(o) for _, d in ipairs(o:GetDescendants()) do da:Fire(d) end end
				a = rawget(a, "_p").Parent
			end
		end
		return
	end
	p[k] = v
	local sigs = rawget(o, "_sigs")
	if sigs[k] then sigs[k]:Fire() end
end
Instance = { new = function(class)
	local o = setmetatable({ _p = defaults(class), _kids = {}, _sigs = {} }, IMT)
	rawget(o, "_p").ClassName = class
	if class == "BindableEvent" then
		local ev = signal()
		rawget(o, "_p").Event = ev
		rawset(o, "Fire", function(self, ...) ev:Fire(...) end)
	end
	T.created = (T.created or 0) + 1
	return o
end }
function IM:FindFirstChild(n) for _, c in ipairs(rawget(self, "_kids")) do if c.Name == n then return c end end return nil end
function IM:WaitForChild(n) local c = self:FindFirstChild(n) if not c then error("WaitForChild: no " .. n .. " in " .. tostring(self.Name)) end return c end
function IM:GetChildren() local out = {} for i, c in ipairs(rawget(self, "_kids")) do out[i] = c end return out end
function IM:GetDescendants() local out = {} local function rec(x) for _, c in ipairs(rawget(x, "_kids")) do table.insert(out, c) rec(c) end end rec(self) return out end
function IM:IsA(c) local k = self.ClassName return k == c or (c == "GuiObject" and GUIOBJ[k] == true) or (c == "GuiBase2d" and (GUIOBJ[k] or k == "ScreenGui")) or (c == "LuaSourceContainer" and k == "ModuleScript") end
function IM:IsDescendantOf(a) local p = self.Parent while p do if p == a then return true end p = p.Parent end return false end
function IM:Destroy() self.Parent = nil rawget(self, "_p").Destroyed = true end
function IM:GetPropertyChangedSignal(prop) local s = rawget(self, "_sigs") if not s[prop] then s[prop] = signal() end return s[prop] end

-- the stub layout engine (the Roblox rules the kit relies on)
local function child(o, class) for _, c in ipairs(rawget(o, "_kids")) do if c.ClassName == class then return c end end return nil end
function T.layout(o)
	local p = rawget(o, "_p")
	if p.ClassName == "ScreenGui" then return p.AbsolutePosition.X, p.AbsolutePosition.Y, p.AbsoluteSize.X, p.AbsoluteSize.Y, 1 end
	local px, py, pw, ph, c = T.layout(p.Parent)
	local S, P, A = p.Size, p.Position, p.AnchorPoint
	local w = S.X.Scale * pw + S.X.Offset * c
	local h = S.Y.Scale * ph + S.Y.Offset * c
	local ar = child(o, "UIAspectRatioConstraint")
	if ar and h > 0 and w > 0 then
		if w / h > ar.AspectRatio then w = h * ar.AspectRatio else h = w / ar.AspectRatio end
	end
	local us = child(o, "UIScale")
	local d = us and us.Scale or 1
	w, h = w * d, h * d
	local ax = px + P.X.Scale * pw + P.X.Offset * c
	local ay = py + P.Y.Scale * ph + P.Y.Offset * c
	return ax - A.X * w, ay - A.Y * h, w, h, c * d
end
function T.area(mode)
	local d = T.device
	local W, H, t, l, r, b = d.w, d.h, d.top, d.left, d.right, d.bottom
	if mode == "None" then return 0, 0, W, H end
	if mode == "DeviceSafeInsets" then return l, 0, W - l - r, H - b end
	return l, t, W - l - r, H - t - b
end
function T.placeGui(g)
	local mode = g.ScreenInsets and g.ScreenInsets.Name or "CoreUISafeInsets"
	local x, y, w, h = T.area(mode)
	local p = rawget(g, "_p")
	p.AbsolutePosition = Vector2.new(x, y)
	p.AbsoluteSize = Vector2.new(w, h)
end
function T.setDevice(d)
	T.device = d
	for _, g in ipairs(T.playerGui:GetChildren()) do
		if g.ClassName == "ScreenGui" then T.placeGui(g) local s = rawget(g, "_sigs") if s.AbsoluteSize then s.AbsoluteSize:Fire() end end
	end
end
function T.visible(o)
	local x = o
	while x and x.ClassName ~= "ScreenGui" do if x.Visible == false then return false end x = x.Parent end
	return x ~= nil
end
function T.measure(prefixes)
	local out = {}
	for _, g in ipairs(T.playerGui:GetChildren()) do
		local ok = false
		for _, pre in ipairs(prefixes) do if string.sub(g.Name, 1, #pre) == pre then ok = true end end
		if g.ClassName == "ScreenGui" and ok then
			for _, o in ipairs(g:GetDescendants()) do
				if GUIOBJ[o.ClassName] and T.visible(o) then
					local x, y, w, h, c = T.layout(o)
					local e = { id = o.Name, x = x, y = y, w = w, h = h, cls = o.ClassName, image = o.Image }
					if o.BackgroundTransparency < 1 then e.fill = o.BackgroundColor3.hex end
					local gr = child(o, "UIGradient")
					if gr then e.g1 = gr.Color.Keypoints[1].Value.hex e.g2 = gr.Color.Keypoints[2].Value.hex end
					local st = child(o, "UIStroke")
					if st then e.stroke = st.Color.hex e.sw = st.Thickness * c end
					if o.ClassName == "TextLabel" then e.text = o.Text e.tsize = o.TextSize * c e.tcolor = o.TextColor3.hex end
					table.insert(out, e)
				end
			end
		end
	end
	return out
end

T.playerGui = Instance.new("Folder")
T.playerGui.Name = "PlayerGui"
local function svc(tbl, name)
	local sigs = {}
	tbl.GetPropertyChangedSignal = function(self, prop) if not sigs[prop] then sigs[prop] = signal() end return sigs[prop] end
	tbl._fire = function(prop) if sigs[prop] then sigs[prop]:Fire() end end
	tbl.Name = name
	return tbl
end
local GS = svc({ SelectedObject = nil, ReducedMotionEnabled = false }, "GuiService")
GuiService = setmetatable(GS, { __index = function(t, k)
	if k == "ViewportDisplaySize" then return Enum.DisplaySize[T.device.display] end
	return nil
end })
local UIS = svc({}, "UserInputService")
UserInputService = setmetatable(UIS, { __index = function(t, k)
	if k == "PreferredInput" then return Enum.PreferredInput[T.device.input] end
	if k == "TouchEnabled" then return T.device.input == "Touch" end
	if k == "GamepadEnabled" then return T.device.input == "Gamepad" end
	if k == "InputBegan" then local s = signal() rawset(t, k, s) return s end
	return nil
end })
function UIS:GetImageForKeyCode(kc) return "rbxasset://glyph/" .. kc.Name end
TweenServiceStub = { Create = function(self, inst, info, props)
	return { Play = function() T.tweens = T.tweens + 1 for k, v in pairs(props) do inst[k] = v end end, Completed = signal() }
end }
local CAS = { BindActionAtPriority = function(self, name, fn, touch, prio, ...) T.bound[name] = { fn = fn, keys = { ... } } end,
	UnbindAction = function(self, name) T.bound[name] = nil end }
Players = { LocalPlayer = { WaitForChild = function(self, n) return T.playerGui end } }
local services = { Players = Players, GuiService = GuiService, UserInputService = UserInputService, TweenService = TweenServiceStub,
	ContextActionService = CAS, ReplicatedStorage = Instance.new("Folder") }
game = { GetService = function(self, n) return services[n] end }

local cache = {}
function require(m)
	if cache[m] ~= nil then return cache[m] end
	local src = rawget(m, "_p").Source
	local fn, err = loadstring(src, "=" .. m.Name)
	if not fn then error(err) end
	setfenv(fn, setmetatable({ script = m }, { __index = _G }))
	local r = fn()
	cache[m] = r
	return r
end
function T.module(parent, name, src)
	local m = Instance.new("ModuleScript")
	m.Name = name
	rawget(m, "_p").Source = src
	m.Parent = parent
	return m
end
"""


class Harness:
    def __init__(self, pkg, lupa_mod):
        self.pkg, self.lupa = pkg, lupa_mod
        lib = pkg / "src" / "shared" / "RR_UI"
        self.files = {p.stem: p.read_text(encoding="utf-8") for p in lib.glob("*.lua")}
        self.screens = {p.stem: p.read_text(encoding="utf-8") for p in (lib / "screens").glob("*.lua")}

    def world(self, dev, reduce=False):
        L = self.lupa.LuaRuntime(unpack_returned_tuples=True)
        L.execute(STUBS)
        T = L.globals().RRT
        L.execute(f"RRT.device = {{ w = {dev.screen[0]}, h = {dev.screen[1]}, top = {dev.insets.get('top', 0)}, "
                  f"left = {dev.insets.get('left', 0)}, right = {dev.insets.get('right', 0)}, bottom = {dev.insets.get('bottom', 0)}, "
                  f"display = '{dev.display}', input = '{dev.input}' }}")
        if reduce:
            L.execute("GuiService.ReducedMotionEnabled = true")
        L.execute("RRT.lib = Instance.new('Folder') RRT.lib.Name = 'RR_UI' RRT.scr = Instance.new('Folder') RRT.scr.Name = 'screens' RRT.scr.Parent = RRT.lib")
        for name, src in self.files.items():
            T.module(T.lib, name, src)
        for name, src in self.screens.items():
            T.module(T.scr, name, src)
        L.execute("RRT.Kit = require(RRT.lib:WaitForChild('RR_UIKit'))")
        return L, T

    def mount(self, L, name, state=None):
        st = f", state = '{state}'" if state else ""
        return L.eval(f"(function() local def = require(RRT.scr:WaitForChild('{name}')) RRT.def = def "
                      f"RRT.screen = RRT.Kit.mount(def, {{ parent = RRT.playerGui{st} }}) return RRT.screen end)()")


def lua_list(L, tbl):
    return [tbl[i] for i in range(1, len(tbl) + 1)] if tbl else []


def rows(L, tbl):
    return [dict(e.items()) for e in lua_list(L, tbl)]


def flatten_py(scene):
    out = {}

    def rec(it):
        out[it["id"]] = it
        for c in it.get("children", []):
            rec(c)
    for layer in scene["layers"].values():
        for it in layer:
            rec(it)
    return out


def board_lua(b):
    return U.lua(b)


def compare(want, got, tag, fails):
    """Model tree (uimodel.resolve, flattened) vs Lua measure rows; appends failures, returns checks made."""
    checks = 0
    for i, w in want.items():
        g = got.get(i)
        if w["type"] == "image" and str(w.get("image", "")).startswith("icon.") and not g:
            continue
        checks += 1
        if not g:
            fails.append(f"{tag}: {i} drawn on the board but missing or hidden in Lua")
            continue
        d = max(abs(g["x"] - w["box"][0]), abs(g["y"] - w["box"][1]), abs(g["w"] - w["box"][2]), abs(g["h"] - w["box"][3]))
        if d > 0.5:
            fails.append(f"{tag}: {i} rect lua ({g['x']:.1f},{g['y']:.1f},{g['w']:.1f},{g['h']:.1f}) vs board "
                         f"({w['box'][0]:.1f},{w['box'][1]:.1f},{w['box'][2]:.1f},{w['box'][3]:.1f})")
        if w["type"] == "text":
            if (g.get("text") or "") != (w.get("text") or ""):
                fails.append(f"{tag}: {i} text {g.get('text')!r} vs {w.get('text')!r}")
            if abs((g.get("tsize") or 0) - w["size"]) > 0.05:
                fails.append(f"{tag}: {i} text size {g.get('tsize') or 0:.2f} vs {w['size']:.2f}")
            if w.get("color") and g.get("tcolor") != w["color"]:
                fails.append(f"{tag}: {i} text colour {g.get('tcolor')} vs {w['color']}")
        if w.get("gradient") and all(w["gradient"]):
            if (g.get("g1"), g.get("g2")) != tuple(w["gradient"]):
                fails.append(f"{tag}: {i} gradient {g.get('g1')},{g.get('g2')} vs {w['gradient']}")
        elif w.get("fill") and g.get("fill") != w["fill"]:
            fails.append(f"{tag}: {i} fill {g.get('fill')} vs {w['fill']}")
        if w.get("stroke") and w["stroke"][0]:
            if g.get("stroke") != w["stroke"][0] or abs((g.get("sw") or 0) - w["stroke"][1]) > 0.05:
                fails.append(f"{tag}: {i} stroke {g.get('stroke')} {g.get('sw')} vs {w['stroke']}")
    for i in got:
        if i not in want and not i.startswith("RR_"):
            fails.append(f"{tag}: {i} visible in Lua but not on the board")
    return checks


def measure(L, T, name):
    return {e["id"]: e for e in rows(L, T.measure(L.eval(f"{{'{name}'}}")))}


def look_diff(L, T, sc, dev, board, skin=None):
    """Live Lua tree vs the model's board for the same state/data/pushes: [] when they agree."""
    fails = []
    compare(flatten_py(U.resolve(sc, dev, skin or sc.kit.default_skin, board)), measure(L, T, sc.name),
            f"{sc.name}/{dev.name}", fails)
    return fails


def load_specs(h, kit):
    """Screen models for the package's screens, from --specs (never the skill's examples by name)."""
    specs, missing = {}, []
    for path in h.spec_paths:
        sc = U.Screen(kit, path)
        if sc.name in h.screens:
            specs[sc.name] = sc
        else:
            missing.append(f"{path.name} ({sc.name}) is not in the package")
    return specs, missing


def parity(h, kit, specs, verbose):
    fails, checks = [], 0
    for name, sc in specs.items():
        for dname, dev in kit.devices.items():
            for b in sc.boards:
                L, T = h.world(dev)
                h.mount(L, name)
                L.execute(f"RRT.screen:board({U.lua(b)})")
                want = flatten_py(U.resolve(sc, dev, kit.default_skin, b))
                checks += compare(want, measure(L, T, name), f"{name}/{dname}/{b.get('name')}", fails)
                if verbose:
                    print(f"  parity {name}/{dname}/{b.get('name')}: {len(want)} nodes")
    return fails, checks


def dev_lua(dev):
    return (f"{{ w = {dev.screen[0]}, h = {dev.screen[1]}, top = {dev.insets.get('top', 0)}, left = {dev.insets.get('left', 0)}, "
            f"right = {dev.insets.get('right', 0)}, bottom = {dev.insets.get('bottom', 0)}, display = '{dev.display}', input = '{dev.input}' }}")


def feel_stub(L, names):
    ev = ", ".join(f"{n} = true" for n in sorted(set(n for n in names if n)))
    L.execute("RRT.calls = {} RRT.Kit.useFeel({ Presets = { events = { " + ev + " } }, settings = { reduceMotion = false }, "
              "play = function(name, ctx) table.insert(RRT.calls, { name = name, ctx = ctx }) end })")


def calls(L, T):
    return [c["name"] for c in lua_list(L, T.calls)]


def runtime(h, kit, specs):
    """Behaviour tests derived from each spec. Rows: (name, True/False, detail) or (name, None, why) for a SKIP."""
    R = []

    def ok(name, cond, detail=""):
        R.append((name, bool(cond), detail))

    def skip(name, why):
        R.append((name, None, why))
    phone, pc, notch, console = (kit.devices[d] for d in ("phone", "pc", "phone_notch", "console"))
    for name, sc in specs.items():
        P = f"{name}: "
        m = sc.machine
        b0 = sc.boards[0] if sc.boards else {"name": "default"}
        st0 = b0.get("state") or (m["initial"] if m else None)
        look0 = (m["states"].get(st0, {}) if m else {}) or {}
        disabled0 = {sc.ref(r) for r in look0.get("disable", [])}
        hits = [i for i, n in sc.index.items() if n.get("type") == "hit"]
        feels = [t["feel"] for t in (m["transitions"] if m else [])] + ["ui_button_press"]
        # ---- state machine
        if not m:
            skip(P + "state machine", "no machine in the spec")
        else:
            L, T = h.world(phone)
            s = h.mount(L, name)
            ok(P + f"starts in {m['initial']}", s.state == m["initial"])
            tweens = {}
            for t in m["transitions"]:
                fr = m["initial"] if t["from"] == "*" else t["from"]
                L, T = h.world(phone)
                s = h.mount(L, name, state=fr)
                sent = L.eval(f"RRT.screen:send('{t['event']}')")
                tw = T.tweens
                L.execute("RRT.advance(1)")
                bad = look_diff(L, T, sc, phone, {"state": t["to"]})
                ok(P + f"{fr} -{t['event']}-> {t['to']}: state and look match the model", sent and s.state == t["to"] and not bad,
                   "; ".join(bad[:2]))
                tweens[id(t)] = tw
            hides = {k: {sc.ref(x) for x in v.get("hide", [])} for k, v in m["states"].items()}
            shower = next((t for t in m["transitions"] if t["from"] != "*" and hides.get(t["from"], set()) - hides.get(t["to"], set())), None)
            if shower:
                ok(P + f"fallback fade runs without RR_Feel ({shower['event']})", tweens[id(shower)] > 0, f"{tweens[id(shower)]} tweens")
            else:
                skip(P + "fallback fade", "no transition shows a hidden node")
            allowed = {t["event"] for t in m["transitions"] if t["from"] in (m["initial"], "*")}
            ill = next((t["event"] for t in m["transitions"] if t["event"] not in allowed), "__rr_nope")
            L, T = h.world(phone)
            s = h.mount(L, name)
            nw = len(T.warns)
            ok(P + f"illegal event '{ill}' in {m['initial']} is ignored and warned",
               L.eval(f"RRT.screen:send('{ill}')") is False and s.state == m["initial"] and len(T.warns) == nw + 1)
            for sname, look in m["states"].items():
                dis = [r for r in (sc.ref(x) for x in look.get("disable", [])) if r and sc.index[r].get("type") == "hit"]
                if dis:
                    L, T = h.world(phone)
                    s = h.mount(L, name, state=sname)
                    good = all(L.eval(f"RRT.screen:activate('{x}')") is False and L.eval(f"RRT.screen.nodes['{x}'].Selectable") is False
                               for x in dis)
                    ok(P + f"{sname}: {len(dis)} disabled controls ignore activation and are not selectable", good and s.state == sname)
            hider = next((t for t in m["transitions"] if m["states"].get(t["to"], {}).get("hide")
                          and t["from"] != "*" and not m["states"].get(t["from"], {}).get("hide")), None)
            if hider:
                L, T = h.world(phone, reduce=True)
                h.mount(L, name, state=hider["from"])
                L.execute(f"RRT.screen:send('{hider['event']}') RRT.advance(0)")
                ids = [r for r in (sc.ref(x) for x in m["states"][hider["to"]]["hide"]) if r]
                ok(P + f"reduce motion: {hider['event']} hides at once, no tweens", T.tweens == 0
                   and all(L.eval(f"RRT.screen.nodes['{i}'].Visible") is False for i in ids), f"{T.tweens} tweens")
            else:
                skip(P + "reduce motion", "no transition hides anything")
            ft = next((t for t in m["transitions"] if t["feel"]), None)
            if ft and any(n.get("feel") == "panel" for n in sc.index.values()):
                L, T = h.world(phone)
                feel_stub(L, feels)
                h.mount(L, name, state=m["initial"] if ft["from"] == "*" else ft["from"])
                L.execute(f"RRT.screen:send('{ft['event']}')")
                ok(P + f"RR_Feel plays {ft['feel']} on the panel", ft["feel"] in calls(L, T)
                   and L.eval("(function() for _, c in ipairs(RRT.calls) do if c.ctx and c.ctx.targets and c.ctx.targets.panel "
                              "== RRT.screen.feel.panel then return true end end return false end)()"))
            else:
                skip(P + "RR_Feel transition hand-off", "no feel event or no panel feel target")
        # ---- actions and data
        acts = [(i, sc.index[i]["action"]) for i in hits if sc.index[i].get("action") is not None and i not in disabled0]
        if not acts:
            skip(P + "actions", "no enabled controls with an action")
        for hid, a in acts:
            L, T = h.world(phone)
            s = h.mount(L, name, state=st0)
            if isinstance(a, dict):
                data = {k: v["default"] for k, v in sc.data.items()}
                for k, v in (a.get("set") or {}).items():
                    data[k] = v
                for k, d in (a.get("cycle") or {}).items():
                    vals = sc.data[k]["values"]
                    data[k] = vals[(vals.index(data[k]) + d) % len(vals)] if data[k] in vals else vals[0]
                L.execute(f"RRT.screen:activate('{hid}')")
                got = {k: L.eval(f"RRT.screen.data['{k}']") for k in data}
                bad = look_diff(L, T, sc, phone, {"state": st0, "data": data})
                ok(P + f"{hid} {json_short(a)}: data and look match the model", got == data and not bad,
                   "; ".join(bad[:2]) or (f"data {got} vs {data}" if got != data else ""))
                for k, d in (a.get("cycle") or {}).items():
                    vals = sc.data[k]["values"]
                    for _ in range(len(vals) - 1):
                        L.execute(f"RRT.screen:activate('{hid}')")
                    ok(P + f"{hid} cycles {k} through all {len(vals)} values and wraps",
                       L.eval(f"RRT.screen.data['{k}']") == sc.data[k]["default"])
            else:
                L.globals().RRT.acts = L.table()
                L.execute("RRT.screen.Action.Event:Connect(function(x) table.insert(RRT.acts, x) end)")
                to = next((t["to"] for t in (m["transitions"] if m else []) if t["from"] in (st0, "*") and t["event"] == a), None)
                L.execute(f"RRT.screen:activate('{hid}')")
                ok(P + f"{hid} fires Action '{a}'" + (f" and moves {st0} -> {to}" if to else ""),
                   lua_list(L, T.acts)[:1] == [a] and (to is None or s.state == to))
        # ---- gamepad and back button
        nav = sc.nav
        edges = {a: e for a, e in nav["edges"].items() if e}
        if not edges:
            skip(P + "gamepad nav", "no nav graph")
        else:
            L, T = h.world(console)
            h.mount(L, name, state=st0)
            if nav.get("default") and nav.get("modal") and m:
                ok(P + f"gamepad: focus starts on {nav['default']}", L.eval(f"GuiService.SelectedObject == RRT.screen.nodes['{nav['default']}']"))
            wrong = [f"{a}.{d}" for a, e in edges.items() for d, b in e.items()
                     if b and not L.eval(f"RRT.screen.nodes['{a}'].NextSelection{d.title()} == RRT.screen.nodes['{b}']")]
            ok(P + f"gamepad: {sum(len(e) for e in edges.values())} NextSelection links follow the nav graph", not wrong, ", ".join(wrong[:4]))
            ok(P + "gamepad: themed focus ring on every control",
               all(L.eval(f"RRT.screen.nodes['{a}'].SelectionImageObject == RRT.screen.focusRing") for a in edges))
            if nav.get("modal"):
                ok(P + "gamepad: modal is a SelectionGroup that stops", L.eval(f"RRT.screen.nodes['{nav['modal']}'].SelectionGroup") is True
                   and L.eval(f"RRT.screen.nodes['{nav['modal']}'].SelectionBehaviorUp.Name") == "Stop")
            glyphs = [i for i, n in sc.index.items() if n.get("gamepad_only")]
            if glyphs:
                shown = all(L.eval(f"RRT.screen.nodes['{g}'] ~= nil and RRT.screen.nodes['{g}'].Visible") for g in glyphs)
                L2, T2 = h.world(phone)
                h.mount(L2, name, state=st0)
                hidden = all(L2.eval(f"RRT.screen.nodes['{g}'] == nil or RRT.screen.nodes['{g}'].Visible == false") for g in glyphs)
                ok(P + f"key glyphs ({len(glyphs)}) show with a gamepad, hide on touch", shown and hidden)
                ok(P + "touch: no forced gamepad selection", L2.eval("GuiService.SelectedObject") is None)
        if nav.get("back") and nav.get("modal") and m:
            L, T = h.world(phone)
            s = h.mount(L, name, state=st0)
            key = f"RR_UI_Back_{name}"
            bound = L.eval(f"RRT.bound['{key}']")
            ok(P + "ButtonB bound while the modal is open", bound is not None and lua_list(L, bound["keys"])[0].Name == "ButtonB")
            if bound is not None:
                act = sc.index[nav["back"]].get("action")
                to = next((t["to"] for t in m["transitions"] if t["from"] in (st0, "*") and t["event"] == act), st0)
                L.execute(f"RRT.bound['{key}'].fn('x', Enum.UserInputState.Begin) RRT.advance(1)")
                still = L.eval(f"RRT.bound['{key}']") is not None
                ok(P + f"ButtonB activates {nav['back']} ({st0} -> {to}) and unbinds when closed",
                   s.state == to and (still == L.eval("RRT.screen:isOpen()")))
        else:
            skip(P + "ButtonB back", "no nav.back on a modal with a machine")
        press = nav.get("default") if nav.get("default") in hits and nav.get("default") not in disabled0 else \
            next((x for x in hits if x not in disabled0 and sc.index[x].get("comp")), None)
        if press:
            L, T = h.world(phone)
            feel_stub(L, feels)
            h.mount(L, name, state=st0)
            L.execute(f"RRT.screen.nodes['{press}'].MouseButton1Down:Fire()")
            ok(P + f"press {press}: pressed state + ui_button_press", L.eval(f"RRT.screen.comps['{press}'].flags.pressed") is True
               and calls(L, T)[-1:] == ["ui_button_press"])
            L.execute(f"RRT.screen.nodes['{press}'].MouseButton1Up:Fire()")
            ok(P + "release clears pressed", L.eval(f"RRT.screen.comps['{press}'].flags.pressed") in (None, False))
        # ---- stack (HUD)
        stn = next((n for n in sc.index.values() if n.get("stack")), None)
        if stn:
            stack_tests(h, kit, sc, stn, ok, skip)
        else:
            skip(P + "HUD stack", "no stack node")
        # ---- reskin and resize (every screen)
        L, T = h.world(phone)
        h.mount(L, name, state=st0)
        L.execute(f"RRT.screen:board({U.lua(b0)})")
        other = next((k for k in kit.skins if k != kit.default_skin), None)
        if other:
            L.execute(f"RRT.Kit.setSkin('{other}')")
            bad = look_diff(L, T, sc, phone, b0, skin=other)
            ok(P + f"setSkin {other} rebinds every colour live", not bad, "; ".join(bad[:2]))
            L.execute(f"RRT.Kit.setSkin('{kit.default_skin}')")
            bad = look_diff(L, T, sc, phone, b0)
            ok(P + f"setSkin {kit.default_skin} restores", not bad, "; ".join(bad[:2]))
        ok(P + "unknown skin refused", L.eval("RRT.Kit.setSkin('__nope')") is False)
        for dev in (pc, notch):
            L, T = h.world(phone)
            h.mount(L, name, state=st0)
            L.execute(f"RRT.screen:board({U.lua(b0)}) RRT.setDevice({dev_lua(dev)}) RRT.advance(1)")
            bad = look_diff(L, T, sc, dev, b0)
            ok(P + f"resize phone -> {dev.name} re-lays out to the {dev.name} board", not bad, "; ".join(bad[:2]))
    return R


def json_short(a):
    return " ".join(f"{k} {v}" for k, v in a.items())


def stack_tests(h, kit, sc, stn, ok, skip):
    name, st, P = sc.name, stn["stack"], f"{sc.name}: "
    phone, pc = kit.devices["phone"], kit.devices["pc"]
    types = sc.types
    kind = {t: {"kind": v["kind"]} for t, v in types.items()}
    sticky = [t for t in types if U.cond_ok(st.get("sticky"), kind[t])]
    crisis = [t for t in types if U.cond_ok(st.get("crisis"), kind[t])]
    routine = [t for t in types if t not in sticky]

    def extra(t):
        return {m[0]: "Sam" for m in U.SLOT.findall(types[t]["body"] or "")}

    def push_lua(t):
        ex = extra(t)
        return f"RRT.screen:push('{t}'{', ' + U.lua(ex) if ex else ''})"
    if not types:
        skip(P + "HUD stack", "no alert types")
        return
    a = routine[0] if routine else next(iter(types))
    b = next((t for t in sticky if t != a), None) or next((t for t in types if t != a), a)
    L, T = h.world(pc)
    h.mount(L, name)
    L.execute(push_lua(a) + " " + push_lua(b))
    bad = look_diff(L, T, sc, pc, {"push": [[a, extra(a)], [b, extra(b)]]})
    ok(P + f"push {a} + {b}: tickets match the model", not bad, "; ".join(bad[:2]))
    if st.get("merge") == "type":
        L.execute(push_lua(a))
        bad = look_diff(L, T, sc, pc, {"push": [[a, extra(a)], [b, extra(b)], [a, extra(a)]]})
        ok(P + f"same type merges ({a} x2: count badge, keeps its place)", not bad, "; ".join(bad[:2]))
    life = st.get("life_s", {}).get(types[a]["kind"])
    if life and a not in sticky:
        L.execute(f"RRT.advance({life + 0.05}) RRT.advance(1)")
        left = [x["type"] for x in lua_list(L, L.eval("(function() for _, s in pairs(RRT.screen.stacks) do return s.items end end)()"))]
        ok(P + f"{a} expires after its canon life ({life:g} s)" + ("; sticky " + b + " stays" if b in sticky else ""),
           a not in left and (b not in sticky or b in left), f"left {left}")
    L.execute(f"RRT.screen:clear('{b}') RRT.advance(1)")
    left = [x["type"] for x in lua_list(L, L.eval("(function() for _, s in pairs(RRT.screen.stacks) do return s.items end end)()"))]
    ok(P + f"clear('{b}') removes it", b not in left)
    nw = len(T.warns)
    ok(P + "unknown alert type warns and returns nil", L.eval("RRT.screen:push('__Nope')") is None and len(T.warns) == nw + 1)
    order = list(types)[: int(st.get("max", 4)) + 2]
    if len(order) > int(st.get("max", 4)):
        L, T = h.world(pc)
        h.mount(L, name)
        L.execute(" ".join(push_lua(t) for t in order))
        bad = look_diff(L, T, sc, pc, {"push": [[t, extra(t)] for t in order]})
        ok(P + f"overflow: {len(order)} live pushes match the model (cap, compact, halo, +N chip, slot fill)", not bad, "; ".join(bad[:2]))
    else:
        skip(P + "overflow", f"fewer than max+1 alert types ({len(types)})")
    if crisis and st.get("feel"):
        fe = st["feel"]
        L, T = h.world(pc)
        feel_stub(L, list(fe.values()))
        h.mount(L, name)
        L.execute(push_lua(crisis[0]))
        want = [fe.get("enter"), fe.get("crisis")]
        ok(P + "RR_Feel: ticket enter + crisis arrival", calls(L, T)[:2] == [w for w in want if w],
           f"{calls(L, T)[:3]}")
        if st.get("merge") == "type" and fe.get("merge"):
            L.execute(push_lua(crisis[0]))
            ok(P + "RR_Feel: merge bump", calls(L, T)[-1:] == [fe["merge"]])
    else:
        skip(P + "stack RR_Feel hand-off", "no crisis type or no feel events")
    # touch-zone lift: the model's worst case, then Roblox's real controls (added late, shown late)
    top = next((n for n in sc.nodes if n["id"] == stn["id"] or U._find(n.get("children", []), lambda x: x is stn)), stn)
    if not top.get("avoid"):
        skip(P + "touch-zone lift", "no avoid on the stack's group")
        return
    mode = sc.insets
    base, _ = U.place_top(kit, phone, top, mode)
    want0 = base[1] - U.avoid_lift(kit, phone, top, base)[1]
    ax, ay, aw, ah = phone.area(mode)

    def lift_for(jx, jy, jw, jh):  # a real JumpButton at layer px
        bx, by, bw, bh = base[0] - ax, base[1] - ay, base[2], base[3]
        return max(0.0, by + bh - jy) if (bx < jx + jw and jx < bx + bw and by < jy + jh and jy < by + bh) else 0.0
    L, T = h.world(phone)
    h.mount(L, name)
    got0 = L.eval(f"RRT.screen.lift['{top['id']}']")
    ok(P + f"touch phone, no TouchGui yet: lifted {want0:.0f} px above the worst-case jump zone", abs(got0 - want0) < 0.5, f"{got0:.1f}")
    if st.get("max_lifted") and want0 > 0:
        L.execute(" ".join(push_lua(t) for t in list(types)[: int(st.get("max", 4)) + 1]))
        n_vis = L.eval("(function() for _, s in pairs(RRT.screen.stacks) do local v = s:visible() return #v end end)()")
        ok(P + f"lifted stack shows max_lifted ({int(st['max_lifted'])})", n_vis == int(st["max_lifted"]))
    classic = (aw - 95, ah - 90, 70, 70)
    ability = (aw - 136, ah - 136, 72, 72)
    L.execute("RRT.tg = Instance.new('ScreenGui') RRT.tg.Name = 'TouchGui' local f = Instance.new('Frame') f.Name = 'TouchControlFrame' "
              "f.Size = UDim2.fromScale(1, 1) f.Parent = RRT.tg local j = Instance.new('ImageButton') j.Name = 'JumpButton' "
              "j.Size = UDim2.fromOffset(70, 70) j.Position = UDim2.new(1, -95, 1, -90) j.Parent = f RRT.tg.Parent = RRT.playerGui")
    got = L.eval(f"RRT.screen.lift['{top['id']}']")
    ok(P + f"TouchGui added after mount: re-lifts to the real classic JumpButton ({lift_for(*classic):.0f} px)",
       abs(got - lift_for(*classic)) < 0.5, f"{got:.1f}")
    L, T = h.world(phone)
    L.execute("local tg = Instance.new('ScreenGui') tg.Name = 'TouchGui' tg.Parent = RRT.playerGui local f = Instance.new('Frame') "
              "f.Name = 'TouchControlFrame' f.Size = UDim2.fromScale(1, 1) f.Parent = tg RRT.jb = Instance.new('ImageButton') "
              "RRT.jb.Name = 'JumpButton' RRT.jb.Visible = false RRT.jb.Size = UDim2.fromOffset(72, 72) "
              "RRT.jb.Position = UDim2.new(1, -136, 1, -136) RRT.jb.Parent = f")
    h.mount(L, name)
    hidden = L.eval(f"RRT.screen.lift['{top['id']}']")
    L.execute("RRT.jb.Visible = true")
    shown = L.eval(f"RRT.screen.lift['{top['id']}']")
    ok(P + f"JumpButton hidden at mount then shown: lift 0 -> {lift_for(*ability):.0f} px", hidden == 0 and abs(shown - lift_for(*ability)) < 0.5,
       f"{hidden:.1f} -> {shown:.1f}")


def build_temp():
    tmp = Path(tempfile.mkdtemp(prefix="rr-ui-luatest-"))
    specs = sorted(str(p) for p in (U.SKILL / "specs").glob("*.json"))
    r = subprocess.run([sys.executable, str(HERE / "ui.py"), "build", *specs, "--out", str(tmp), "--no-parity"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-1000:])
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit("temp build failed")
    return tmp, [Path(p) for p in specs]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--package", default="", help="a ui.py build output folder (default: a temp build of specs/)")
    ap.add_argument("--specs", default="", help="comma-separated spec files of the package's screens (ui.py build passes them)")
    ap.add_argument("--only", choices=["parity", "runtime"])
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args(argv)
    try:
        from lupa import lua51
    except ImportError:
        print("SKIP: lupa missing (pip install --target ~/.cache/rr-tools/py lupa)")
        return 3
    tmp = None
    if a.package:
        pkg = Path(a.package)
        if not (pkg / "src" / "shared" / "RR_UI" / "RR_UIKit.lua").is_file():
            print(f"luatest: FAILED (no package at {pkg}: expected src/shared/RR_UI/RR_UIKit.lua)")
            return 1
        spec_paths = [Path(p) for p in a.specs.split(",") if p]
        if not spec_paths:
            print("luatest: FAILED (--package needs --specs: the spec files the package was built from)")
            return 1
    else:
        tmp, spec_paths = build_temp()
        pkg = tmp
    try:
        h = Harness(pkg, lua51)
        h.spec_paths = spec_paths
        kit = U.Kit()
        specs, missing = load_specs(h, kit)
        bad = 0
        for x in missing:
            print(f"  FAIL {x}")
        bad += bool(missing)
        untested = sorted(set(h.screens) - set(specs))
        if untested:
            print(f"  note: no spec given for {', '.join(untested)} (not tested)")
        total = 0
        if a.only in (None, "parity"):
            fails, checks = parity(h, kit, specs, a.v)
            for f in fails[:40]:
                print(f"  FAIL parity {f}")
            print(f"parity: {checks - len(fails)}/{checks} node checks match")
            bad += bool(fails)
            total += checks
        if a.only in (None, "runtime"):
            R = runtime(h, kit, specs)
            for n, passed, detail in R:
                if passed is False or (a.v and passed) :
                    print(f"  {'PASS' if passed else 'FAIL'} {n}{' (' + detail + ')' if detail else ''}")
                elif passed is None and a.v:
                    print(f"  SKIP {n} ({detail})")
            ran = [r for r in R if r[1] is not None]
            n = sum(1 for r in ran if r[1])
            sk = len(R) - len(ran)
            print(f"runtime: {n}/{len(ran)} passed" + (f", {sk} skipped (nothing in the spec to test; -v names them)" if sk else ""))
            bad += n != len(ran)
            total += len(ran)
        if total == 0:
            print("luatest: FAILED (0 checks ran: no spec matched a screen in the package)")
            return 1
        print("luatest: all passed" if not bad else "luatest: FAILED")
        return 1 if bad else 0
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
