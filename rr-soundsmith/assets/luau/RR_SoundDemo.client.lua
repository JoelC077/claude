--[[
RR_SoundDemo.client.lua (rr-soundsmith): a Studio listening test for the Risky Rails mix. LocalScript in
StarterPlayerScripts; needs RR_Sound and RR_SoundMap in ReplicatedStorage (RR_Feel optional). Play Solo, then:
  1-9, 0   fire the events listed in DEMO below (crisis alarms, lever, fare, crate, fail ...)
  T        trip_start / trip_end (loops)          Z X C   Speed 20 / 35 / 50 (av.audio.speed_link)
  R        radio toggle                           P       print Sound.stats() to the Output
Emitters: any Attachment or BasePart in Workspace named RR_Emitter_<role> (e.g. RR_Emitter_lever) is used for that
role; otherwise 3D sounds play 2D and say so once. Listen on a phone too (Device emulator is not a speaker test).
]]
local RS = game:GetService("ReplicatedStorage")
local UIS = game:GetService("UserInputService")

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

local DEMO = {
	"alert_coal_low", "alert_pressure_high", "alert_breakdown", "alert_passengers_upset", "fork_countdown_tick",
	"lever_commit", "alert_fare_banked", "alert_crate_landed", "boiler_burst", "depart",
}
local KEYS = {
	Enum.KeyCode.One, Enum.KeyCode.Two, Enum.KeyCode.Three, Enum.KeyCode.Four, Enum.KeyCode.Five,
	Enum.KeyCode.Six, Enum.KeyCode.Seven, Enum.KeyCode.Eight, Enum.KeyCode.Nine, Enum.KeyCode.Zero,
}

local function fire(name)
	local ev = Map.events[name]
	if ev and ev.via == "feel" and Feel then
		Feel.play(name, {})
	else
		Sound.event(name) -- without RR_Feel, feel events run their sound side directly
	end
	print("[RR_SoundDemo] " .. name)
end

local tripOn = false
UIS.InputBegan:Connect(function(input, processed)
	if processed then
		return
	end
	for i, k in ipairs(KEYS) do
		if input.KeyCode == k and DEMO[i] then
			fire(DEMO[i])
		end
	end
	if input.KeyCode == Enum.KeyCode.T then
		tripOn = not tripOn
		Sound.event(tripOn and "trip_start" or "trip_end")
		Sound.setSpeed(tripOn and 35 or 0)
	elseif input.KeyCode == Enum.KeyCode.Z then
		Sound.setSpeed(20)
	elseif input.KeyCode == Enum.KeyCode.X then
		Sound.setSpeed(35)
	elseif input.KeyCode == Enum.KeyCode.C then
		Sound.setSpeed(50)
	elseif input.KeyCode == Enum.KeyCode.R then
		Sound.event("radio_button")
	elseif input.KeyCode == Enum.KeyCode.P then
		local st = Sound.stats()
		print(string.format("[RR_SoundDemo] played %d dropped %d stolen %d cooled %d missing %d active %d",
			st.played, st.dropped, st.stolen, st.cooled, st.missing, st.active))
	end
end)

print("[RR_SoundDemo] ready: 1-0 events, T trip, Z/X/C speed, R radio, P stats")
