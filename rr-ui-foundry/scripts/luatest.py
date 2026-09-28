#!/usr/bin/env python3
"""Run the shipped RR_UIKit in a real Lua 5.1 VM against stubbed Roblox services and a stub layout engine.

  luatest.py [--package DIR] [--only parity|runtime] [-v]

  parity   every screen x device x board: mount the generated package, apply the board, measure every visible
           GuiObject with the stub layout engine (Scale + Offset, AnchorPoint, UIAspectRatioConstraint
           FitWithinMaxSize, UIScale, ScreenInsets) and compare with uimodel.resolve (the HTML boards):
           rects within 0.5 px, same visibility, texts, text sizes, fills, gradients and text colours
  runtime  state machine (legal, illegal, disabled), chips and data slots, difficulty cycle, ButtonB bind and
           unbind, gamepad focus and edges, modal SelectionGroup, reduce motion (no tweens), live reskin,
           resize to another device, HUD push / merge / expiry / clear / overflow chip, jump-button lift with
           the zone table and with a real TouchGui, RR_Feel hand-off (event names and targets)

Without --package it builds a temporary package from specs/*.json (ui.py build --no-parity). Needs lupa:
  pip install --target ~/.cache/rr-tools/py lupa     (this script adds that folder to sys.path)
Stubs model what RR_UIKit touches; they prove logic and layout math, not Roblox rendering.
Exit 0 = all passed, 1 = failures, 3 = skipped (lupa missing).
"""
import argparse, json, subprocess, sys, tempfile
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
	Event = true, SelectionGained = true, SelectionLost = true }
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


def parity(h, kit, verbose):
    fails, checks, skipped_img = [], 0, 0
    for path in sorted((U.SKILL / "specs").glob("*.json")) if not h.spec_paths else h.spec_paths:
        sc = U.Screen(kit, path)
        if sc.name not in h.screens:
            continue
        for dname, dev in kit.devices.items():
            for b in sc.boards:
                L, T = h.world(dev)
                h.mount(L, sc.name)
                L.execute(f"RRT.screen:board({board_lua(b)})")
                got = {}
                for e in rows(L, T.measure(L.eval(f"{{'{sc.name}'}}"))):
                    got[e["id"]] = e
                want = flatten_py(U.resolve(sc, dev, kit.default_skin, b))
                tag = f"{sc.name}/{dname}/{b.get('name')}"
                for i, w in want.items():
                    g = got.get(i)
                    if w["type"] == "image" and str(w.get("image", "")).startswith("icon.") and not g:
                        skipped_img += 1
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
                            fails.append(f"{tag}: {i} text size {g.get('tsize'):.2f} vs {w['size']:.2f}")
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
                extra = [i for i, g in got.items() if i not in want and not i.startswith("RR_")]
                for i in extra:
                    fails.append(f"{tag}: {i} visible in Lua but not on the board")
                if verbose:
                    print(f"  parity {tag}: {len(want)} nodes")
    return fails, checks, skipped_img


def runtime(h, kit):
    R = []

    def ok(name, cond, detail=""):
        R.append((name, bool(cond), detail))

    lobby = next((n for n in h.screens if "Lobby" in n), None)
    hud = next((n for n in h.screens if "Hud" in n), None)
    phone, console, pc = kit.devices["phone"], kit.devices["console"], kit.devices["pc"]
    if lobby:
        L, T = h.world(phone)
        s = h.mount(L, lobby)
        panel = L.eval("RRT.screen.nodes.panel")
        ok("lobby starts closed (panel hidden)", s.state == "closed" and panel.Visible is False)
        ok("open -> open, panel visible", L.eval("RRT.screen:send('open')") and s.state == "open" and panel.Visible is True)
        ok("fallback fade tweens ran (no RR_Feel)", T.tweens > 0, f"{T.tweens} tweens")
        nw = len(T.warns)
        ok("illegal event ignored and warned", L.eval("RRT.screen:send('joined')") is False and s.state == "open" and len(T.warns) == nw + 1)
        L.execute("RRT.screen:activate('p1')")
        ok("chip p1 sets players=1 and turns on", s.data.players == 1 and L.eval("RRT.screen.comps.p1.flags.on") is True
           and L.eval("RRT.screen.comps.p2.flags.on") in (None, False))
        ok("chip on shows its mark", L.eval("RRT.screen.nodes['p1.mark'].Visible") is True and L.eval("RRT.screen.nodes['p2.mark'].Visible") is False)
        L.execute("RRT.screen:activate('diff_next')")
        hard = kit.color(kit.default_skin, "diff.hard")
        ok("difficulty cycles MEDIUM -> HARD (text and plate role)", s.data.difficulty == "HARD"
           and L.eval("RRT.screen.nodes.diff_plate.Text") == "HARD" and L.eval("RRT.screen.nodes.diff_plate.BackgroundColor3.hex") == hard)
        L.execute("RRT.screen:activate('diff_prev') RRT.screen:activate('diff_prev') RRT.screen:activate('diff_prev')")
        ok("difficulty wraps backwards to INSANE", s.data.difficulty == "INSANE")
        acts = []
        L.globals().RRT.acts = L.table()
        L.execute("RRT.screen.Action.Event:Connect(function(a) table.insert(RRT.acts, a) end)")
        L.execute("RRT.screen:activate('join')")
        ok("join -> joining, Action fired", s.state == "joining" and lua_list(L, T.acts)[:1] == ["join"])
        ok("joining disables join and shows JOINING...", L.eval("RRT.screen.comps.join.flags.disabled") is True
           and L.eval("RRT.screen.nodes['join.label'].Text") == "JOINING..." and L.eval("RRT.screen.nodes.join.Selectable") is False)
        ok("disabled join ignores activation", L.eval("RRT.screen:activate('join')") is False and s.state == "joining")
        L.execute("RRT.screen:send('cancel')")
        ok("cancel -> open restores JOIN", s.state == "open" and L.eval("RRT.screen.nodes['join.label'].Text") == "JOIN"
           and L.eval("RRT.screen.comps.join.flags.disabled") in (None, False))
        bound = L.eval("RRT.bound['RR_UI_Back_" + lobby + "']")
        ok("ButtonB bound while open", bound is not None and lua_list(L, bound["keys"])[0].Name == "ButtonB")
        L.execute("RRT.bound['RR_UI_Back_" + lobby + "'].fn('x', Enum.UserInputState.Begin)")
        ok("ButtonB closes the modal and unbinds", s.state == "closed" and L.eval("RRT.bound['RR_UI_Back_" + lobby + "']") is None)
        L.execute("RRT.advance(1)")
        ok("closed hides the panel after the fade", panel.Visible is False)
        L.execute("RRT.Kit.setSkin('A')")
        a_panel = kit.color("A", "panel")
        ok("setSkin A reskins bound roles live", L.eval("RRT.screen.nodes['panel.body'].BackgroundColor3.hex") == a_panel)
        L.execute("RRT.Kit.setSkin('" + kit.default_skin + "')")
        ok("setSkin back restores", L.eval("RRT.screen.nodes['panel.body'].BackgroundColor3.hex") == kit.color(kit.default_skin, "panel"))
        ok("unknown skin refused", L.eval("RRT.Kit.setSkin('Z')") is False)

        L, T = h.world(console)
        s = h.mount(L, lobby)
        L.execute("RRT.screen:send('open')")
        ok("gamepad: open selects the default (join)", L.eval("GuiService.SelectedObject == RRT.screen.nodes.join"))
        sc = U.Screen(kit, next(p for p in (U.SKILL / "specs").glob("*.json") if U.Screen(kit, p).name == lobby))
        e = sc.nav["edges"]["join"]
        ok("gamepad: join.NextSelectionUp follows the nav graph", L.eval(f"RRT.screen.nodes.join.NextSelectionUp == RRT.screen.nodes['{e['up']}']"))
        ok("gamepad: modal panel is a SelectionGroup that stops", L.eval("RRT.screen.nodes.panel.SelectionGroup") is True
           and L.eval("RRT.screen.nodes.panel.SelectionBehaviorUp.Name") == "Stop")
        ok("gamepad: themed focus ring is the SelectionImageObject", L.eval("RRT.screen.nodes.join.SelectionImageObject == RRT.screen.focusRing"))
        ok("gamepad: key glyph visible with a gamepad", L.eval("RRT.screen.nodes['join.glyph'].Visible") is True
           and L.eval("RRT.screen.nodes['join.glyph'].Image") == "rbxasset://glyph/ButtonA")
        L, T = h.world(phone)
        h.mount(L, lobby)
        L.execute("RRT.screen:send('open')")
        ok("touch: key glyph hidden", L.eval("RRT.screen.nodes['join.glyph'].Visible") is False)
        ok("touch: no forced selection", L.eval("GuiService.SelectedObject") is None)

        L, T = h.world(phone, reduce=True)
        h.mount(L, lobby)
        L.execute("RRT.screen:send('open') RRT.screen:send('close')")
        ok("reduce motion: no tweens, hides at once", T.tweens == 0 and L.eval("(RRT.advance(0) or true) and RRT.screen.nodes.panel.Visible") is False,
           f"{T.tweens} tweens")

        L, T = h.world(phone)
        L.execute("RRT.calls = {} RRT.Kit.useFeel({ Presets = { events = { ui_panel_open = true, ui_panel_close = true, ui_button_press = true } }, "
                  "settings = { reduceMotion = false }, play = function(name, ctx) table.insert(RRT.calls, { name = name, ctx = ctx }) end })")
        h.mount(L, lobby)
        L.execute("RRT.screen:send('open')")
        calls = lua_list(L, T.calls)
        ok("RR_Feel plays ui_panel_open on the panel", calls and calls[0]["name"] == "ui_panel_open"
           and L.eval("RRT.calls[1].ctx.targets.panel == RRT.screen.nodes.panel"))
        L.execute("RRT.screen.nodes.join.MouseButton1Down:Fire()")
        calls = lua_list(L, T.calls)
        ok("RR_Feel plays ui_button_press on press", calls[-1]["name"] == "ui_button_press"
           and L.eval("RRT.screen.comps.join.flags.pressed") is True)
        L.execute("RRT.screen.nodes.join.MouseButton1Up:Fire()")
        ok("release clears pressed", L.eval("RRT.screen.comps.join.flags.pressed") in (None, False))

        L, T = h.world(phone)
        h.mount(L, lobby, state="open")
        L.execute("RRT.setDevice = RRT.setDevice")
        L.execute(f"RRT.setDevice({{ w = {pc.screen[0]}, h = {pc.screen[1]}, top = {pc.insets.get('top', 0)}, left = 0, right = 0, bottom = 0, display = 'Medium', input = 'KeyboardAndMouse' }})")
        want = flatten_py(U.resolve(sc, pc, kit.default_skin, {"state": "open"}))
        got = {e["id"]: e for e in rows(L, T.measure(L.eval(f"{{'{lobby}'}}")))}
        worst = max(abs(got[i]["w"] - w["box"][2]) + abs(got[i]["x"] - w["box"][0]) for i, w in want.items() if i in got)
        ok("resize phone -> PC re-lays out to the PC board", worst < 0.5 and len(got) >= len(want) - 2, f"max err {worst:.3f}")
    if hud:
        L, T = h.world(pc)
        s = h.mount(L, hud)
        L.execute("RRT.screen:push('CoalLow') RRT.screen:push('FareBanked')")
        st = L.eval("(function() for _, st in pairs(RRT.screen.stacks) do return st end end)()")
        ok("push two alerts", len(lua_list(L, st["items"])) == 2)
        L.execute("RRT.screen:push('FareBanked')")
        ok("same type merges (count 2, badge shows 2)", len(lua_list(L, st["items"])) == 2
           and L.eval("RRT.screen.nodes['stack.t2.badge'] and RRT.screen.nodes['stack.t2.badge'].Text") == "2")
        cash = [x for x in lua_list(L, st["items"]) if x["type"] == "FareBanked"][0]
        ok("merged ticket keeps its place and refreshes its life", cash["seq"] == 2)
        life_cash = next(n for n in U.Screen(kit, next(p for p in (U.SKILL / "specs").glob("*.json") if U.Screen(kit, p).name == hud)).nodes
                         if n.get("stack"))["stack"]["life_s"]["cash"]
        L.execute(f"RRT.advance({life_cash + 0.05}) RRT.advance(1)")
        items = lua_list(L, st["items"])
        ok("cash ticket expires after its canon life; sticky crisis stays", len(items) == 1 and items[0]["type"] == "CoalLow",
           f"life {life_cash}s")
        L.execute("RRT.screen:clear('CoalLow') RRT.advance(1)")
        ok("clear(type) removes the sticky crisis", len(lua_list(L, st["items"])) == 0 and L.eval("RRT.screen.nodes['stack.t1']") is None)
        for tname in ("CrewJoined", "CrateLanded", "PressureHigh", "RiskyRoute", "FareBanked", "CrewLeft"):
            L.execute(f"RRT.screen:push('{tname}', {{ name = 'Sam' }})")
        ok("overflow: 4 visible + '+2 MORE' chip", L.eval("RRT.screen.nodes['stack.more.chip'] and RRT.screen.nodes['stack.more.chip'].Text") == "+2 MORE")
        texts = [e.get("text") for e in rows(L, T.measure(L.eval(f"{{'{hud}'}}")))]
        ok("slot fill in body ({name} -> Sam)", "Sam left the train" in texts)
        nw = len(T.warns)
        ok("unknown alert type warns and returns nil", L.eval("RRT.screen:push('Nope')") is None and len(T.warns) == nw + 1)
        L, T = h.world(phone)
        h.mount(L, hud)
        ok("touch phone: stack lifted above the jump zone", L.eval("RRT.screen.lift.stack") > 0, f"{L.eval('RRT.screen.lift.stack'):.1f}px")
        for tname in ("CrewJoined", "CrateLanded", "PressureHigh", "RiskyRoute", "FareBanked"):
            L.execute(f"RRT.screen:push('{tname}', {{ name = 'Sam' }})")
        vis = L.eval("(function() for _, st in pairs(RRT.screen.stacks) do local v, h = st:visible() return #v end end)()")
        ok("lifted stack shows max_lifted (3)", vis == 3)
        L, T = h.world(phone)
        L.execute("local tg = Instance.new('ScreenGui') tg.Name = 'TouchGui' tg.Parent = RRT.playerGui "
                  "local f = Instance.new('Frame') f.Name = 'TouchControlFrame' f.Size = UDim2.fromScale(1, 1) f.Parent = tg "
                  "local j = Instance.new('ImageButton') j.Name = 'JumpButton' j.Size = UDim2.fromOffset(70, 70) "
                  "j.Position = UDim2.new(1, -95, 1, -90) j.Parent = f")
        h.mount(L, hud)
        ok("real classic JumpButton: no lift, 4 visible", L.eval("RRT.screen.lift.stack") == 0)
        L, T = h.world(pc)
        L.execute("RRT.calls = {} RRT.Kit.useFeel({ Presets = { events = { hud_ticket_enter = true, hud_crisis_arrival = true, hud_merge_bump = true, hud_ticket_leave = true } }, "
                  "settings = { reduceMotion = false }, play = function(name, ctx) table.insert(RRT.calls, { name = name, ctx = ctx }) end })")
        h.mount(L, hud)
        L.execute("RRT.screen:push('Breakdown')")
        names = [c["name"] for c in lua_list(L, T.calls)]
        ok("RR_Feel: ticket enter + crisis arrival", names[:2] == ["hud_ticket_enter", "hud_crisis_arrival"]
           and L.eval("RRT.calls[1].ctx.targets.ticket == RRT.screen.nodes['stack.t1.mover']")
           and L.eval("RRT.calls[2].ctx.targets.halo == RRT.screen.nodes['stack.t1.halo_red']"))
        L.execute("RRT.screen:push('Breakdown')")
        names = [c["name"] for c in lua_list(L, T.calls)]
        ok("RR_Feel: merge bump on the badge", names[-1] == "hud_merge_bump" and L.eval("RRT.calls[#RRT.calls].ctx.targets.stamp ~= nil"))
    return R


def build_temp():
    tmp = Path(tempfile.mkdtemp(prefix="rr-ui-luatest-"))
    specs = sorted(str(p) for p in (U.SKILL / "specs").glob("*.json"))
    r = subprocess.run([sys.executable, str(HERE / "ui.py"), "build", *specs, "--out", str(tmp), "--no-parity"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-1000:])
        sys.exit("temp build failed")
    return tmp


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--package", default="")
    ap.add_argument("--specs", default="", help="comma-separated spec files for parity (default: the package's screens found in specs/)")
    ap.add_argument("--only", choices=["parity", "runtime"])
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args(argv)
    try:
        from lupa import lua51
    except ImportError:
        print("SKIP: lupa missing (pip install --target ~/.cache/rr-tools/py lupa)")
        return 3
    pkg = Path(a.package) if a.package else build_temp()
    h = Harness(pkg, lua51)
    h.spec_paths = [Path(p) for p in a.specs.split(",") if p] or sorted((U.SKILL / "specs").glob("*.json"))
    kit = U.Kit()
    bad = 0
    if a.only in (None, "parity"):
        fails, checks, skipped = parity(h, kit, a.v)
        for f in fails[:40]:
            print(f"  FAIL parity {f}")
        print(f"parity: {checks - len(fails)}/{checks} node checks match" + (f" ({skipped} icons without a sheet entry skipped)" if skipped else ""))
        bad += bool(fails)
    if a.only in (None, "runtime"):
        R = runtime(h, kit)
        for name, passed, detail in R:
            if a.v or not passed:
                print(f"  {'PASS' if passed else 'FAIL'} {name}{' (' + detail + ')' if detail else ''}")
        n = sum(1 for _, p, _ in R if p)
        print(f"runtime: {n}/{len(R)} passed")
        bad += n != len(R)
    print("luatest: all passed" if not bad else "luatest: FAILED")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
