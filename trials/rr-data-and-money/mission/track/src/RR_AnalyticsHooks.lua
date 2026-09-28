-- RR_AnalyticsHooks (ModuleScript, SERVER ONLY) - one call per Risky Rails game moment, so gameplay scripts
-- never assemble analytics payloads themselves. Call each hook AFTER the server has applied the change
-- (coins added, order accepted, route locked). Requires RR_Analytics already init()-ed.
--
--   local Hooks = require(script.Parent.RR_AnalyticsHooks)
--   Hooks.leverCommitted(player, "risky", 3.4, crewSize)          -- lever handler, after gameplay.fork.lock
--   Hooks.stationPaid(player, fare, newBalance, "Hard", tripId, isFirstBankOfTrip)
--   Hooks.runEnded(crewPlayers, "stall", 3, milesDone, tripId)    -- results start, once per trip
--   Hooks.orderAccepted(player, "coal", price, newBalance, "Easy", terminalSessionId)
--   Hooks.unlockBought(player, 2, price, newBalance)                -- loco_2 .. loco_5
--   Hooks.playerLeft(player, "run", secondsInPhase, "Hard")         -- PlayerRemoving
--   Hooks.playerJoined / crisisEnded / resultsAction / purchaseStep     -- see below

local A = require(script.Parent.RR_Analytics)
local Hooks = {}
local LEVELS = { "Easy", "Medium", "Hard", "Insane" }

function Hooks.playerJoined(player)
	A.onboarding(player, "join") -- lobby PlayerAdded; the profile store makes it count once per lifetime
end

function Hooks.toolPickedUp(player)
	A.onboarding(player, "picked_up_tool")
end

function Hooks.coalShovelled(player)
	A.onboarding(player, "shovelled_coal") -- count shovels in the run; report totals in the Incident Report, not here
end

function Hooks.leverCommitted(player, choice, timeLeft, crewSize, tripId, isFirstFork)
	A.onboarding(player, "pulled_lever")
	A.event(player, "lever_pulled", timeLeft, { choice = choice, time_left = timeLeft, crew = crewSize })
	if isFirstFork and tripId then
		A.funnel(player, "trip", tripId, "first_fork")
	end
end

function Hooks.stationPaid(player, fare, newBalance, difficulty, tripId, isFirstBankOfTrip)
	if fare > 0 then
		A.source(player, fare, newBalance, "Gameplay", "fare_bank", { difficulty = difficulty })
	end
	A.onboarding(player, "first_bank")
	if isFirstBankOfTrip and tripId then
		A.funnel(player, "trip", tripId, "first_bank")
	end
end

function Hooks.runEnded(players, reason, difficultyIndex, miles, tripId)
	local crew = #players
	local status = reason == "arrived" and "Complete" or "Fail"
	for _, player in ipairs(players) do
		A.onboarding(player, "run_end")
		A.event(player, "run_end", miles, { reason = reason, difficulty = LEVELS[difficultyIndex], crew = crew })
		A.progress(player, "trip", status, difficultyIndex, nil, { crew = crew, reason = reason })
		if status == "Complete" and tripId then
			A.funnel(player, "trip", tripId, "arrived")
		end
	end
end

function Hooks.orderAccepted(player, sku, price, newBalance, difficulty, terminalSessionId)
	A.sink(player, price, newBalance, "Shop", sku, { difficulty = difficulty })
	if terminalSessionId then
		A.funnel(player, "supply", terminalSessionId, "ordered")
	end
end

function Hooks.unlockBought(player, locoNumber, price, newBalance)
	A.sink(player, price, newBalance, "Shop", "loco_" .. tostring(locoNumber), { difficulty = "Lobby" })
	A.progress(player, "locomotives", "Complete", locoNumber - 1)
end

function Hooks.crisisEnded(player, kind, outcome, seconds, crewSize)
	A.event(player, "crisis_end", seconds, { kind = kind, outcome = outcome, crew = crewSize })
end

function Hooks.resultsAction(player, action, secondsOnResults)
	A.event(player, "results_action", secondsOnResults, { action = action })
end

-- step = "prompt_shown" (before Prompt*Purchase), "accepted" (Finished event), "granted" (after the receipt saved)
function Hooks.purchaseStep(player, promptId, step)
	A.funnel(player, "purchase", promptId, step)
end

function Hooks.playerLeft(player, phase, secondsInPhase, difficulty)
	A.event(player, "player_left", secondsInPhase, { phase = phase, difficulty = difficulty or "Lobby" })
end

-- ===== Mission additions (trial 2026-09-28): the skill's hooks never log trip steps 1-3 or supply steps 1 and 3,
-- so the dashboard funnels would start at zero. These fill them, plus the crate outcome event. =====

-- step = "queued" (lobby pad), "boarded" (trip place, loaded on the train), "departed" (whistle)
function Hooks.tripStep(player, tripId, step)
	if tripId then
		A.funnel(player, "trip", tripId, step)
	end
end

function Hooks.terminalOpened(player, terminalSessionId)
	A.funnel(player, "supply", terminalSessionId, "opened")
end

-- kind = coal|toolbox|sandwich|medkit, outcome = fetched|slid_off; once per crate, from the server crate handler
function Hooks.crateResolved(player, kind, outcome, secondsSinceLanding, difficulty, terminalSessionId)
	A.event(player, "crate_resolved", secondsSinceLanding, { kind = kind, outcome = outcome, difficulty = difficulty })
	if outcome == "fetched" and terminalSessionId then
		A.funnel(player, "supply", terminalSessionId, "fetched")
	end
end

return Hooks
