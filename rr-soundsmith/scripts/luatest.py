#!/usr/bin/env python3
"""Run RR_Sound.lua in a real Lua 5.1 VM against stubbed Roblox services (no Studio needed).

  luatest.py [--map FILE] [-v]

Runs the suite on the map generated from the current soundmap.json (every sound given fake asset ids), or on
--map RR_SoundMap.lua from a build (sounds without ids get two fake ids; a map missing the sounds the suite drives
is load-checked only and exits 2). Checks: group tree and pools, Volume and SoundGroup per sound, emitters and the 2D
fallback, cooldowns, per-sound voices, group caps, global cap and tier stealing, playing crisis alarms protected from
crisis impacts, ducking attack/hold/release in dB (deepest rule wins), Studio group volumes kept as the base, speed
link (rate clamp, gain, braking fade to silence), Feel.Cue bridge (and no double play), countdown pitch steps, loops
(start, toggle, stop), missing asset ids, settings, the 3D layer of 2D alarms (same take, stops with its voice), and a
10-second random soak within the voice cap. Stubs model only what RR_Sound touches; they prove logic, not Roblox audio.

Needs lupa (optional test dependency): pip install --target ~/.cache/rr-tools/py lupa. Exit 0 = all passed.
"""
import argparse, random, sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path.home() / ".cache" / "rr-tools" / "py"))

STUBS = r"""
local T = { warns = 0, now = 0 }
RRT = T
warn = function(...) T.warns = T.warns + 1; T.lastWarn = table.concat({...}, " ") end
task = { spawn = function(fn) fn() end, delay = function(t, fn) end }
local function Signal()
	local s = { fns = {} }
	function s:Connect(fn) table.insert(self.fns, fn); local c = {}; function c:Disconnect() end; return c end
	function s:Fire(...) for _, f in ipairs(self.fns) do f(...) end end
	return s
end
RRSignal = Signal
local function newInst(class)
	local props = { ClassName = class, Name = class, children = {}, Volume = 0.5, PlaybackSpeed = 1, IsPlaying = false,
		TimeLength = 0, TimePosition = 0, plays = 0 }
	local inst = {}
	local mt = {}
	mt.__index = function(_, k) return props[k] end
	mt.__newindex = function(_, k, v)
		if k == "Parent" then
			local old = props.Parent
			if old then old._rm(inst) end
			if v then table.insert(v.children, inst) end
		end
		props[k] = v
	end
	setmetatable(inst, mt)
	props._rm = function(c) for i = #props.children, 1, -1 do if props.children[i] == c then table.remove(props.children, i) end end end
	props.FindFirstChild = function(self, name) for _, c in ipairs(props.children) do if c.Name == name then return c end end return nil end
	props.Play = function(self) props.IsPlaying = true; props.plays = props.plays + 1 end
	props.Stop = function(self) props.IsPlaying = false end
	props.Destroy = function(self) self.Parent = nil end
	props.IsA = function(self, c) return c == class end
	return inst
end
Instance = { new = newInst }
Enum = { RollOffMode = { Inverse = "Inverse", Linear = "Linear", LinearSquare = "LinearSquare", InverseTapered = "InverseTapered" } }
local services = {
	SoundService = newInst("SoundService"),
	RunService = { Heartbeat = Signal(), IsClient = function() return true end, IsServer = function() return false end },
	ContentProvider = { PreloadAsync = function(self, list) T.preloaded = #list end },
}
game = { GetService = function(self, n) return services[n] end }
RRServices = services
"""


def lupa_runtime():
    try:
        from lupa import lua51
    except ImportError:
        return None
    return lua51.LuaRuntime(unpack_returned_tuples=True)


def test_map_lua():
    import sound as snd
    m = snd.Model()
    for sid in m.sounds:
        n = m.sounds[sid].get("brief", {}).get("variations", 1)
        m.assets[sid] = {"ids": [f"rbxassetid://{1000 + i}" for i in range(n)], "source": "placeholder"}
    rm = snd.runtime_map(m)
    return "return " + snd.lua(rm), rm


REQ_SOUNDS = ["lever_clunk", "ui_click", "glass_smash", "ticket_chime", "whistle", "brake_hiss", "cash_register",
              "alarm_coal", "alarm_pressure", "breakdown_bang", "passengers_scream", "coupling_snap", "crate_thump",
              "boiler_boom", "wheels_loop", "horn", "stamp_slam", "countdown_tick", "radio_loop"]
REQ_EVENTS = ["trip_start", "trip_end", "lever_commit", "fork_countdown_tick", "radio_button"]
INJECT = """return function(map)
	for _, s in pairs(map.sounds) do
		if #s.ids == 0 then s.ids = { "rbxassetid://1000", "rbxassetid://1001" } end
	end
end"""


class Rig:
    def __init__(self, map_src, inject=False):
        self.L = lupa_runtime()
        L = self.L
        L.execute(STUBS)
        self.map = L.execute(map_src)
        if inject:
            L.execute(INJECT)(self.map)
        L.globals().RRMAP = self.map
        self.S = L.execute((SKILL / "assets" / "luau" / "RR_Sound.lua").read_text(encoding="utf-8"))
        L.execute("math.randomseed(7)")
        self.t = 0.0
        self.S._now = lambda *a: self.t
        self.feel = L.execute("return { Cue = { Event = RRSignal() } }")
        self.S.init(self.map, L.table_from({"feel": self.feel}))
        self.T = L.globals().RRT
        self.svc = L.globals().RRServices

    def advance(self, secs, dt=1 / 60):
        n = int(round(secs / dt))
        for _ in range(n):
            self.t += dt
            self.S.step(dt)

    def group(self, name):
        mix = self.svc.SoundService.FindFirstChild(self.svc.SoundService, "RR_Mix")

        def find(node):
            for c in node.children.values():
                if c.Name == name:
                    return c
                r = find(c)
                if r is not None:
                    return r
            return None
        return find(mix)

    def stats(self):
        return self.S.stats()


def run(map_src, verbose=False, inject=False):
    fails, n = [], 0

    def ok(cond, msg):
        nonlocal n
        n += 1
        if not cond:
            fails.append(msg)
        if verbose:
            print(("ok   " if cond else "FAIL ") + msg)

    r = Rig(map_src, inject)
    S, M = r.S, r.map
    same = r.L.eval("function(a, b) return rawequal(a, b) end")
    snd = M.sounds
    # groups and pools
    for g in ("Master", "SFX", "Alarms", "Actions", "UI", "Ambient", "Music"):
        ok(r.group(g) is not None, f"group {g} created under RR_Mix")
    ok(r.group("Alarms").Parent.Name == "SFX", "Alarms nests under SFX")
    ok(r.T.preloaded and r.T.preloaded > 20, f"pool preloaded ({r.T.preloaded} Sounds)")
    # plain play
    h = S.play("lever_clunk")
    ok(h is not None, "lever_clunk plays")
    inst = h.inst
    ok(abs(inst.Volume - snd.lever_clunk.volume) < 1e-9, "Volume from the map")
    ok(same(inst.SoundGroup, r.group("Actions")), "SoundGroup = Actions")
    ok(inst.Parent.Name == "RR_SoundPool", "no emitter: 3D sound falls back to 2D pool folder")
    ok(r.T.warns >= 1, "fallback warned")
    lo, hi = snd.lever_clunk.pitch[1], snd.lever_clunk.pitch[2]
    ok(lo <= inst.PlaybackSpeed <= hi, "pitch within spread")
    att = r.L.eval('Instance.new("Attachment")')
    S.setEmitter("lever", att)
    r.t += 0.2
    h2 = S.play("lever_clunk")
    ok(same(h2.inst.Parent, att), "emitter role parents the Sound")
    # cooldown
    r.t += 1
    a = S.play("ui_click")
    b = S.play("ui_click")
    ok(a is not None and b is None, "cooldown blocks a second ui_click within 30 ms")
    ok(r.stats().cooled >= 1, "cooled counted")
    # per-sound voices: glass_smash voices 3, length ~1.4 s
    r.t += 2
    st0 = r.stats().stolen
    for _ in range(4):
        S.play("glass_smash")
        r.t += 0.2
    ok(r.stats().stolen == st0 + 1, "4th glass_smash restarts its own oldest voice (voices 3)")
    # group cap: UI cap 4, tier 5 cannot steal tier 5
    r.t += 5
    r.advance(0.1)
    d0 = r.stats().dropped
    M.voices.perGroup.UI = 2
    S.play("ui_click")
    r.t += 0.031
    S.play("ui_click")
    r.t += 0.01
    ok(S.play("ticket_chime") is None and r.stats().dropped == d0 + 1, "UI group full: a tier-5 voice is dropped (tier 5 never steals)")
    M.voices.perGroup.UI = 4
    # global cap with a low max: tier 2 steals tier 4, tier 4 cannot steal tier 2
    r.t += 5
    r.advance(0.1)
    M.voices.max = 3
    for sid in ("whistle", "brake_hiss", "cash_register"):
        S.play(sid)
    s0, d1 = r.stats().stolen, r.stats().dropped
    ok(S.play("alarm_coal") is not None and r.stats().stolen == s0 + 1, "full: crisis alarm steals the oldest tier-4 voice")
    r.t += 0.5
    S.play("breakdown_bang")
    r.t += 0.5
    S.play("passengers_scream")
    ok(r.stats().active <= 3, "global cap holds")
    r.t += 0.5
    res = S.play("crate_thump")
    ok(res is None and r.stats().dropped == d1 + 1, "full of crisis voices: a tier-4 sound is dropped, not stealing")
    M.voices.max = 16
    # ducking
    r.t += 10
    r.advance(3)
    amb = r.group("Ambient")
    ok(abs(amb.Volume - 1.0) < 1e-6, "Ambient at 0 dB before any alarm")
    S.play("alarm_pressure")
    r.advance(0.06)
    ok(abs(amb.Volume - 10 ** (-8 / 20)) < 1e-3, f"crisis rule ducks Ambient to -8 dB within attack ({amb.Volume:.3f})")
    ok(abs(r.group("UI").Volume - 10 ** (-3 / 20)) < 1e-3, "crisis rule ducks UI -3 dB")
    ok(abs(r.group("Alarms").Volume - 1.0) < 1e-6, "Alarms never duck themselves")
    S.play("boiler_boom")
    r.advance(0.05)
    ok(abs(amb.Volume - 10 ** (-14 / 20)) < 1e-3, "deepest active rule wins (fail -14 dB)")
    r.advance(snd.boiler_boom.length + 0.5 + 0.1)
    rel_mid = amb.Volume
    r.advance(3)
    ok(abs(amb.Volume - 1.0) < 1e-6, "Ambient returns to 0 dB after release")
    ok(rel_mid < 1.0, "release is gradual, not a jump")
    # speed link
    r.t += 1
    S.event("trip_start")
    wl = None
    for c in r.svc.SoundService.FindFirstChild(r.svc.SoundService, "RR_SoundPool").children.values():
        if c.Name == "wheels_loop_1":
            wl = c
    ok(wl is not None and wl.IsPlaying, "trip_start starts wheels_loop")
    base = snd.wheels_loop.volume
    S.setSpeed(35)
    ok(abs(wl.PlaybackSpeed - 1) < 1e-9 and abs(wl.Volume - base) < 1e-9, "Speed 35 = recorded rate and level")
    S.setSpeed(20)
    ok(abs(wl.PlaybackSpeed - 0.6) < 1e-9, "Speed 20 clamps rate to 0.6")
    ok(wl.Volume < base, "Speed 20 is quieter")
    S.setSpeed(50)
    ok(abs(wl.PlaybackSpeed - 50 / 35) < 1e-9 and wl.Volume > base, "Speed 50: rate 1.43, louder")
    S.setSpeed(0)
    ok(wl.Volume == 0, "stopped train: wheels silent")
    vols = []
    for k in range(0, 241):  # arrival braking over 4 s, setSpeed every frame (brake curve: Speed ~ sqrt(distance))
        S.setSpeed(35 * (1 - k / 240) ** 0.5)
        vols.append(wl.Volume)
    ok(all(b_ <= a_ + 1e-12 for a_, b_ in zip(vols, vols[1:])) and vols[0] > 0 and vols[-1] == 0,
       "braking ramp: wheels fade monotonically to silence at the stop")
    S.event("trip_end")
    ok(not wl.IsPlaying, "trip_end stops the loops")
    # feel bridge
    r.t += 1
    p0 = r.stats().played
    r.feel.Cue.Event.Fire(r.feel.Cue.Event, "lever_commit", r.L.table_from({"type": "cue", "sfx": "lever_clunk"}))
    ok(r.stats().played == p0 + 1, "Feel.Cue lever_commit plays lever_clunk")
    r.t += 1
    ok(S.event("lever_commit") is None and r.stats().ignored >= 1, "Sound.event on a feel event is ignored while Feel is connected")
    r.feel.Cue.Event.Fire(r.feel.Cue.Event, "some_new_event", r.L.table_from({"type": "cue", "sfx": "stamp_slam"}))
    ok(r.stats().played == p0 + 2, "unmapped feel cue with a known sfx still plays (warned)")
    # countdown pitch steps via feel
    pitches = []
    for i in range(3):
        r.t += 1.0
        r.feel.Cue.Event.Fire(r.feel.Cue.Event, "fork_countdown_tick", r.L.table_from({"type": "cue", "sfx": "countdown_tick"}))
        pool = [c for c in r.svc.SoundService.FindFirstChild(r.svc.SoundService, "RR_SoundPool").children.values()
                if str(c.Name).startswith("countdown_tick")]
        pitches.append(max(c.PlaybackSpeed for c in pool if c.IsPlaying))
    ok(all(abs(p - e) < 1e-9 for p, e in zip(pitches, (1.0, 1.06, 1.12))), f"countdown pitch steps {pitches}")
    # toggle radio
    S.event("radio_button")
    radio = [c for c in r.svc.SoundService.FindFirstChild(r.svc.SoundService, "RR_SoundPool").children.values() if c.Name == "radio_loop_1"]
    ok(radio and radio[0].IsPlaying, "radio_button toggles the radio on")
    S.event("radio_button")
    ok(radio and not radio[0].IsPlaying, "and off")
    # settings
    S.setSetting("sfx", 0.5)
    ok(abs(r.group("SFX").Volume - 0.5) < 1e-9, "setSetting sfx 0.5 -> SFX group Volume")
    S.setSetting("sfx", 1)
    # layer3d
    fb = r.L.eval('Instance.new("Attachment")')
    S.setEmitter("firebox", fb)
    r.t += 3
    h = S.play("alarm_coal")
    layer = [c for c in fb.children.values()]
    ok(len(layer) == 1 and abs(layer[0].Volume - h.inst.Volume * 10 ** (snd.alarm_coal.layer3d.gainDb / 20)) < 1e-9,
       "alarm_coal: 2D voice plus a quieter positional layer at the firebox")
    ok(h.inst.Parent.Name == "RR_SoundPool", "the main alarm voice stays 2D (OQ-035 default)")
    # playing crisis alarms are protected from crisis impacts; layers follow their voice
    r3 = Rig(map_src, inject)
    S3, M3 = r3.S, r3.map
    for role in ("firebox", "boiler", "powerbox", "coach"):
        S3.setEmitter(role, r3.L.eval('Instance.new("Attachment")'))
    r3.t = 100.0
    al = [S3.play(x) for x in ("alarm_coal", "alarm_pressure", "breakdown_bang", "passengers_scream")]
    for _ in range(3):
        r3.t += 0.16
        S3.play("glass_smash")
    r3.t += 0.05
    S3.play("coupling_snap")
    r3.t += 0.05
    boom = S3.play("boiler_boom")
    ok(all(h_ is not None and h_.inst.IsPlaying for h_ in al) and boom is not None,
       f"Alarms cap {M3.voices.perGroup.Alarms}: glass x3, coupling and the fail never cut a playing crisis alarm")
    r3.t += 10
    r3.advance(0.1)
    M3.voices.perGroup.Alarms = 4
    c1, c2 = S3.play("alarm_coal"), S3.play("alarm_pressure")
    for _ in range(3):
        r3.t += 0.16
        S3.play("glass_smash")
    ok(c1.inst.IsPlaying and c2.inst.IsPlaying, "cap 4: a windows_smash burst leaves COAL LOW and PRESSURE HIGH playing")
    r3.t += 10
    r3.advance(0.1)
    M3.voices.perGroup.Alarms = 1
    h1 = S3.play("alarm_coal")
    d0 = S3.stats().dropped
    r3.t += 0.1
    ok(S3.play("glass_smash") is None and S3.stats().dropped == d0 + 1 and h1.inst.IsPlaying,
       "cap 1: a crisis impact is dropped rather than cutting a playing alarm")
    r3.t += 0.1
    lay_ok = h1.layer is not None and h1.layer.IsPlaying
    S3.play("alarm_pressure")
    ok(lay_ok and not h1.inst.IsPlaying and not h1.layer.IsPlaying,
       "an alarm may replace another alarm; the stolen voice stops its positional layer too")
    M3.voices.perGroup.Alarms = 6
    takes, same = set(), True
    for _ in range(6):
        r3.t += 2.5
        r3.advance(0.05)
        h_ = S3.play("breakdown_bang")
        same = same and h_ is not None and h_.layer is not None and h_.layer.SoundId == h_.inst.SoundId and h_.layer.IsPlaying
        takes.add(h_.inst.SoundId if h_ is not None else None)
    nids = len(list(M3.sounds.breakdown_bang.ids.values()))
    ok(same and (len(takes) > 1 or nids < 2), f"positional layer plays the same take as its voice ({len(takes)} takes)")
    # Studio group volumes are the base; destroy restores them
    r4 = Rig(map_src, inject)
    r4.S.destroy()
    r4.group("Ambient").Volume = 0.8
    r4.group("Alarms").Volume = 1.6
    r4.S.init(r4.map, r4.L.table_from({"feel": r4.feel}))
    ok(abs(r4.group("Ambient").Volume - 0.8) < 1e-9 and abs(r4.group("Alarms").Volume - 1.6) < 1e-9,
       "Studio group volumes survive Sound.init (base)")
    r4.S.play("alarm_pressure")
    r4.advance(0.06)
    r4.S.setSetting("sfx", 0.5)
    ok(abs(r4.group("Ambient").Volume - 0.8 * 10 ** (-8 / 20)) < 1e-3 and abs(r4.group("Alarms").Volume - 1.6) < 1e-9
       and abs(r4.group("SFX").Volume - 0.5) < 1e-9, "ducking and settings multiply the Studio base")
    r4.S.destroy()
    ok(abs(r4.group("Ambient").Volume - 0.8) < 1e-9, "destroy restores the Studio base")
    # missing ids
    r2 = Rig(map_src, inject)
    r2.map.sounds.horn.ids = r2.L.table_from([])
    r2.S.destroy()
    r2.S.init(r2.map)
    ok(r2.S.play("horn") is None and r2.S.stats().missing == 1, "sound without an asset id: skipped and counted")
    ok(r2.S.event("lever_commit") is not None, "without Feel connected, feel events run directly")
    # soak
    ids = [k for k in snd.keys()]
    rnd = random.Random(3)
    peak = 0
    for _ in range(600):
        r.t += 1 / 60
        S.step(1 / 60)
        if rnd.random() < 0.3:
            S.play(rnd.choice(ids))
        peak = max(peak, r.stats().active)
    ok(peak <= M.voices.max, f"10 s random soak: at most {peak} voices (cap {M.voices.max})")
    S.stopAll()
    ok(r.stats().active == 0, "stopAll clears voices")
    return n, fails


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", help="an RR_SoundMap.lua from sound.py build (needs asset ids for most tests)")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    if lupa_runtime() is None:
        print("SKIP luatest: lupa not installed (pip install --target ~/.cache/rr-tools/py lupa)")
        return 0
    inject = False
    if a.map:
        src = Path(a.map).read_text(encoding="utf-8")
        L = lupa_runtime()
        L.execute(STUBS)
        mp = L.execute(src)
        snds, evs = set(mp.sounds.keys()), set(mp.events.keys())
        print(f"loaded {a.map}: {len(snds)} sounds, {len(evs)} events")
        miss = [x for x in REQ_SOUNDS if x not in snds] + [x for x in REQ_EVENTS if x not in evs]
        if miss:
            print(f"luatest: load check only, 0 tests (the suite drives {', '.join(miss)}, missing from this map)")
            return 2
        inject = True
    else:
        src, _ = test_map_lua()
    n, fails = run(src, a.verbose, inject)
    for f in fails:
        print("FAIL " + f)
    print(f"luatest: {n - len(fails)}/{n} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
