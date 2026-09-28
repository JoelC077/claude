--!strict
-- RR_FeelKit (ModuleScript, client only, next to RR_Feel in ReplicatedStorage.RRFeel).
-- Strict-typed entry points for five Risky Rails moments: lever pull, hard brake, crate landed, crisis alarm,
-- fare banked. RR_Feel (the rr-game-feel runtime) is untyped; this module casts it once to the Runtime type
-- below, so every caller gets checked names, targets and return values. Numbers live in RR_FeelPresets
-- (generated from feel.json); see TUNING.md. Nothing here has run in Roblox: Studio test pending (owner).

local RR_Feel = require(script.Parent:WaitForChild("RR_Feel")) :: any

export type Side = number -- -1 = left branch, 1 = right branch (camera yaw and roll follow it)
export type Handle = { Stop: (self: Handle) -> () }
export type CountFormat = (amount: number) -> string
export type Targets = { [string]: GuiObject }
export type Ctx = {
	targets: Targets?,
	side: Side?,
	gain: number?,
	count: { amount: number, format: CountFormat? }?,
}
export type LeverRelease = "committed" | "snapback"
export type CrisisKind = "coal_low" | "pressure_high" | "breakdown" | "passengers_upset"
export type Moment = "lever_pull" | "hard_brake" | "crate_landed" | "crisis_alarm" | "fare_banked"

-- GuiObjects each moment animates (roles from feel.json "roles"); a missing optional part skips its channel.
export type LeverParts = { lever_panel: GuiObject, lever_knob: GuiObject, lamp: GuiObject }
export type TicketParts = { ticket: GuiObject, halo: GuiObject? }
export type FareParts = { ticket: GuiObject, stamp: GuiObject, cash: TextLabel }

type Runtime = {
	play: (name: string, ctx: Ctx?) -> Handle,
	leverDrag: (u: number, ctx: Ctx?) -> number,
	leverRelease: (ctx: Ctx?) -> LeverRelease,
	leverReset: () -> (),
	setSpeed: (speed: number) -> (),
	setPressure: (p01: number) -> (),
}

local Feel: Runtime = RR_Feel

local Kit = {}

-- Which preset events make up each moment (the runtime plays included events itself).
Kit.EVENTS = table.freeze({
	lever_pull = { "lever_detent_tick", "lever_commit", "lever_commit_crew", "lever_snapback" },
	hard_brake = { "hard_brake" },
	crate_landed = { "alert_crate_landed" },
	crisis_alarm = { "alert_coal_low", "alert_pressure_high", "alert_breakdown", "alert_passengers_upset" },
	fare_banked = { "alert_fare_banked" },
}) :: { [Moment]: { string } }

local function leverCtx(parts: LeverParts, side: Side): Ctx
	return {
		side = side,
		targets = { lever_panel = parts.lever_panel, lever_knob = parts.lever_knob, lamp = parts.lamp },
	}
end

-- Lever pull, puller's client (who = actor). u = finger travel 0..1 along the console. Returns the knob
-- position 0..1 to draw: it lags the finger (heavy) and fires the detent tick and the commit clunk once.
function Kit.leverDrag(u: number, parts: LeverParts, side: Side): number
	return Feel.leverDrag(math.clamp(u, 0, 1), leverCtx(parts, side))
end

-- Finger lifted: springs back ("snapback") before the detent, else reports "committed".
function Kit.leverRelease(parts: LeverParts, side: Side): LeverRelease
	return Feel.leverRelease(leverCtx(parts, side))
end

-- Call when a new fork opens so the next drag can commit again.
function Kit.leverNewFork()
	Feel.leverReset()
end

-- Every other client, when the server confirms the route lock (who = crew).
function Kit.leverCommitCrew(side: Side): Handle
	return Feel.play("lever_commit_crew", { side = side })
end

-- Hard brake, every client, as the server starts the stop (OQ-037 default: cord emergency stop or the redline
-- brake). Keep calling setSpeed while Speed falls so the rumble fades with it.
function Kit.hardBrake(): Handle
	return Feel.play("hard_brake")
end

-- Crate landed on the coach roof (server alert CrateLanded), every client.
function Kit.crateLanded(parts: TicketParts): Handle
	return Feel.play("alert_crate_landed", { targets = { ticket = parts.ticket } })
end

-- Crisis alarm (server alert per kind), every client. The halo keeps pulsing until handle:Stop() when the
-- crisis clears. gauge = the fuel gauge for coal_low (optional).
function Kit.crisisAlarm(kind: CrisisKind, parts: TicketParts, gauge: GuiObject?): Handle
	local targets: Targets = { ticket = parts.ticket }
	if parts.halo then
		targets.halo = parts.halo
	end
	if gauge then
		targets.gauge = gauge
	end
	return Feel.play("alert_" .. kind, { targets = targets })
end

-- HUD money text per gameplay.alerts.fare_banked: "$120"; from $10,000 it shortens to "$12K".
-- The currency word is open (OQ-003); pass your own format to change it.
local function fareText(amount: number): string
	local n = math.floor(amount + 0.5)
	if n >= 10000 then
		return "$" .. tostring(math.floor(n / 1000)) .. "K"
	end
	return "$" .. tostring(n)
end

-- Fare banked at a station, every client: the stamp lands, the cash label counts up to amount, a double tick.
function Kit.fareBanked(amount: number, parts: FareParts, format: CountFormat?): Handle
	local targets: Targets = { ticket = parts.ticket, stamp = parts.stamp, cash = parts.cash :: GuiObject }
	return Feel.play("alert_fare_banked", {
		targets = targets,
		count = { amount = amount, format = format or fareText },
	})
end

-- Sustained rumble inputs (tiny by design: the train never moves).
function Kit.setSpeed(speed: number)
	Feel.setSpeed(speed)
end

function Kit.setPressure(p01: number)
	Feel.setPressure(math.clamp(p01, 0, 1))
end

return table.freeze(Kit)
