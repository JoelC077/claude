--[[
RR_SoundDemo.client.lua (rr-soundsmith): a Studio listening test for the Risky Rails mix. LocalScript in
StarterPlayerScripts; needs RR_Sound and RR_SoundMap in ReplicatedStorage (RR_Feel optional). Play Solo, then:
  1-9, 0   fire the events of the current page (run page: crisis alarms, lever, fare, crate, fail ...)
  L        switch page: run <-> lobby (lobby bed, queue pad join/leave, 5-tick countdown, launch whistle)
  T        trip_start / trip_end (loops)          Z X C   Speed 20 / 35 / 50 (av.audio.speed_link)
  N        depart: Speed 0 -> 35 over 5 s         B       brake to a stop over 4 s (wheels fade to silence)
  R        radio toggle                           P       print Sound.stats() to the Output
Emitters: any Attachment or BasePart in Workspace named RR_Emitter_<role> (e.g. RR_Emitter_lever) is used for that
role; otherwise 3D sounds play 2D and say so once. Listen on a phone too (Device emulator is not a speaker test).
]]
local RS = game:GetService("ReplicatedStorage")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")

local Sound = require(RS:WaitForChild("RR_Sound"))
local Map = require(RS:WaitForChild("RR_SoundMap"))
local Feel = RS:FindFirstChild("RR_Feel") and require(RS.RR_Feel) or nil

Sound.init(Map, { feel = Feel })

for _, d in ipairs(workspace:GetDescendants()) do
	local role = string.match(d.Name, "^RR_Emitter_(.+)$")
	if role and (d:IsA("Attachment") or d:IsA("BasePart")) then
		Sound.setEmitter(role, d)
	end
end

local PAGES = {
	run = {
		"alert_coal_low", "alert_pressure_high", "alert_breakdown", "alert_passengers_upset", "fork_countdown_tick",
		"lever_commit", "alert_fare_banked", "alert_crate_landed", "boiler_burst", "depart",
	},
	lobby = { "lobby_enter", "queue_join", "queue_leave", "queue_countdown_tick", "queue_launch", "lobby_leave" },
}
local page = "run"
local KEYS = {
	Enum.KeyCode.One, Enum.KeyCode.Two, Enum.KeyCode.Three, Enum.KeyCode.Four, Enum.KeyCode.Five,
	Enum.KeyCode.Six, Enum.KeyCode.Seven, Enum.KeyCode.Eight, Enum.KeyCode.Nine, Enum.KeyCode.Zero,
}

local function fire(name)
	local ev = Map.events[name]
	if not ev then
		print("[RR_SoundDemo] " .. name .. " is not in RR_SoundMap")
		return
	end
	if name == "queue_countdown_tick" then
		task.spawn(function() -- the last 5 s of the queue pad countdown, one tick per second
			for _ = 1, 5 do
				Sound.event(name)
				task.wait(1)
			end
		end)
	elseif ev.via == "feel" and Feel then
		Feel.play(name, {})
	else
		Sound.event(name) -- without RR_Feel, feel events run their sound side directly
	end
	print("[RR_SoundDemo] " .. name)
end

local speed, ramp = 0, nil
local function setSpeed(v)
	speed = v
	Sound.setSpeed(v)
end
RunService.Heartbeat:Connect(function(dt)
	if ramp then -- Sound.setSpeed every frame while Speed changes, as game code should
		ramp.t = math.min(ramp.t + dt, ramp.dur)
		local k = ramp.t / ramp.dur
		setSpeed(ramp.from + (ramp.to - ramp.from) * (ramp.brake and (1 - (1 - k) ^ 2) or k))
		if ramp.t >= ramp.dur then
			ramp = nil
		end
	end
end)

local tripOn = false
UIS.InputBegan:Connect(function(input, processed)
	if processed then
		return
	end
	for i, k in ipairs(KEYS) do
		if input.KeyCode == k and PAGES[page][i] then
			fire(PAGES[page][i])
		end
	end
	local kc = input.KeyCode
	if kc == Enum.KeyCode.L then
		page = page == "run" and "lobby" or "run"
		print("[RR_SoundDemo] page: " .. page .. " (" .. table.concat(PAGES[page], ", ") .. ")")
	elseif kc == Enum.KeyCode.T then
		tripOn = not tripOn
		Sound.event(tripOn and "trip_start" or "trip_end")
		setSpeed(tripOn and 35 or 0)
	elseif kc == Enum.KeyCode.N then
		ramp = { from = 0, to = 35, t = 0, dur = 5 }
	elseif kc == Enum.KeyCode.B then
		ramp = { from = speed, to = 0, t = 0, dur = 4, brake = true }
	elseif kc == Enum.KeyCode.Z then
		setSpeed(20)
	elseif kc == Enum.KeyCode.X then
		setSpeed(35)
	elseif kc == Enum.KeyCode.C then
		setSpeed(50)
	elseif kc == Enum.KeyCode.R then
		Sound.event("radio_button")
	elseif kc == Enum.KeyCode.P then
		local st = Sound.stats()
		print(string.format("[RR_SoundDemo] played %d dropped %d stolen %d cooled %d missing %d active %d",
			st.played, st.dropped, st.stolen, st.cooled, st.missing, st.active))
	end
end)

print("[RR_SoundDemo] ready: 1-0 events (page " .. page .. "), L page, T trip, N depart, B brake, Z/X/C speed, R radio, P stats")
