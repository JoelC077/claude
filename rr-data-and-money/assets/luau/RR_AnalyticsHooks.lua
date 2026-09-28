-- RR_AnalyticsHooks (ModuleScript, SERVER ONLY) - one call per Risky Rails game moment, so gameplay scripts
-- never assemble analytics payloads themselves. Call each hook AFTER the server has applied the change
-- (coins added, order accepted, route locked). Requires RR_Analytics already init()-ed.
-- Roblox funnels are per player, and a step logged without the earlier ones marks those complete: every planned
-- step has a hook here, and crew-wide steps take the crew list (one Player or a list of Players).
--
--   local Hooks = require(script.Parent.RR_AnalyticsHooks)
--   lobby     playerJoined(p) · tripQueued(p, tripId)
--   trip      tripBoarded(p, tripId) · tripDeparted(crew, tripId, difficultyIndex) · toolPickedUp(p) · coalShovelled(p)
--             leverCommitted(p, "risky", timeLeft, #crew) · forkResolved(crew, tripId, isFirstFork)
--             stationPaid(p, fare, newBalance, "Hard", tripId, isFirstBankOfTrip) · recoveryCharged(p, fee, newBalance, "Hard")
--             crisisEnded(p, kind, outcome, seconds, #crew) · runEnded(crew, reason, difficultyIndex, miles, tripId)
--   Depotron  terminalOpened(p, sessionId) · orderAccepted(p, sku, price, newBalance, "Easy", sessionId)
--             crateResolved(orderer, fetcherOrNil, kind, "fetched"|"slid_off", seconds, "Easy", sessionId)
--   shop      unlockBought(p, "loco_2".."loco_5" | "line_2", price, newBalance) · liveryBought(p, price, newBalance)
--   Robux     purchasePrompted(p, productId) · purchaseAccepted(p, productId) · purchaseGranted(p, productId)
--             farePackGranted(p, "fare_pack_s", coins, newBalance) · promoRedeemed(p, coins, newBalance)
--   results   resultsAction(p, action, seconds) · PlayerRemoving: playerLeft(p, phase, seconds, difficulty)

local A = require(script.Parent.RR_Analytics)
local Hooks = {}
local LEVELS = { "Easy", "Medium", "Hard", "Insane" }

local function each(players, fn)
	if players == nil then
		return
	end
	if players.UserId then
		fn(players)
		return
	end
	for _, p in ipairs(players) do
		fn(p)
	end
end

local function count(players)
	if type(players) == "number" then
		return players
	end
	if players and players.UserId then
		return 1
	end
	return players and #players or 0
end

-- lobby -------------------------------------------------------------------------------------------------
function Hooks.playerJoined(player)
	A.onboarding(player, "join") -- lobby PlayerAdded; the profile store makes it count once per lifetime
end

function Hooks.tripQueued(player, tripId)
	if tripId then
		A.funnel(player, "trip", tripId, "queued")
	end
end

-- trip place --------------------------------------------------------------------------------------------
function Hooks.tripBoarded(player, tripId)
	if tripId then
		A.funnel(player, "trip", tripId, "boarded")
	end
end

function Hooks.tripDeparted(crew, tripId, difficultyIndex)
	each(crew, function(p)
		if tripId then
			A.funnel(p, "trip", tripId, "departed")
		end
		A.progress(p, "trip", "Start", difficultyIndex)
	end)
end

function Hooks.toolPickedUp(player)
	A.onboarding(player, "picked_up_tool")
end

function Hooks.coalShovelled(player)
	A.onboarding(player, "shovelled_coal") -- count shovels in the run; report totals in the Incident Report, not here
end

function Hooks.leverCommitted(player, choice, timeLeft, crewSize)
	A.onboarding(player, "pulled_lever")
	A.event(player, "lever_pulled", timeLeft, { choice = choice, time_left = timeLeft, crew = count(crewSize) })
end

-- the whole crew passed the junction, not only the lever puller
function Hooks.forkResolved(crew, tripId, isFirstFork)
	if isFirstFork and tripId then
		each(crew, function(p)
			A.funnel(p, "trip", tripId, "first_fork")
		end)
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

function Hooks.recoveryCharged(player, fee, newBalance, difficulty)
	A.sink(player, fee, newBalance, "Gameplay", "recovery_fee", { difficulty = difficulty })
end

function Hooks.crisisEnded(player, kind, outcome, seconds, crewSize)
	A.event(player, "crisis_end", seconds, { kind = kind, outcome = outcome, crew = count(crewSize) })
end

function Hooks.runEnded(crew, reason, difficultyIndex, miles, tripId)
	local n = count(crew)
	each(crew, function(p)
		A.onboarding(p, "run_end")
		A.event(p, "run_end", miles, { reason = reason, difficulty = LEVELS[difficultyIndex], crew = n })
		if reason == "arrived" then
			A.progress(p, "trip", "Complete", difficultyIndex, nil, { crew = n, reason = reason })
			if tripId then
				A.funnel(p, "trip", tripId, "arrived")
			end
		else
			A.progress(p, "trip", "Fail", difficultyIndex, nil, { crew = n, reason = reason })
		end
	end)
end

-- Depotron: the session belongs to the player who opened the terminal; every supply step is logged on them ------
function Hooks.terminalOpened(player, sessionId)
	if sessionId then
		A.funnel(player, "supply", sessionId, "opened")
	end
end

-- @rr sink: coal toolbox sandwich medkit
function Hooks.orderAccepted(player, sku, price, newBalance, difficulty, sessionId)
	A.sink(player, price, newBalance, "Shop", sku, { difficulty = difficulty })
	if sessionId then
		A.funnel(player, "supply", sessionId, "ordered")
	end
end

-- fetcher = the crewmate who climbed to the roof (nil when the crate slid off). The funnel step goes to the orderer
-- (who owns the session); the crate event goes to whoever handled it.
function Hooks.crateResolved(orderer, fetcher, kind, outcome, seconds, difficulty, sessionId)
	local handler = fetcher or orderer
	A.event(handler, "crate_resolved", seconds, { kind = kind, outcome = outcome, difficulty = difficulty })
	if outcome == "fetched" and sessionId then
		A.funnel(orderer, "supply", sessionId, "fetched")
	end
end

-- shop ------------------------------------------------------------------------------------------------------
-- @rr sink: loco_2 loco_3 loco_4 loco_5 line_2
function Hooks.unlockBought(player, unlockId, price, newBalance)
	if type(unlockId) == "number" then
		unlockId = "loco_" .. tostring(unlockId)
	end
	A.sink(player, price, newBalance, "Shop", unlockId, { difficulty = "Lobby" })
	if string.sub(unlockId, 1, 5) == "line_" then
		A.progress(player, "lines", "Complete", A.levelIndex("lines", unlockId) or 0)
	else
		A.progress(player, "locomotives", "Complete", A.levelIndex("locomotives", unlockId) or 0)
	end
end

function Hooks.liveryBought(player, price, newBalance) -- post-launch: a livery bought with fare
	A.sink(player, price, newBalance, "Shop", "livery", { difficulty = "Lobby" })
end

-- Robux -----------------------------------------------------------------------------------------------------
-- The prompt id is kept per player and product, so the Finished handler and the grant code need only the product id.
-- Developer products: purchaseGranted in the receipt handler after the grant is saved (it returns PurchaseGranted).
-- Game passes never reach ProcessReceipt: purchaseGranted where the server applies the pass on
-- PromptGamePassPurchaseFinished (wasPurchased, ownership via UserOwnsGamePassAsync). A receipt processed after a
-- rejoin has no prompt id and logs no step.
local pending, counter = {}, 0

local function newId()
	local ok, id = pcall(function()
		return game:GetService("HttpService"):GenerateGUID(false)
	end)
	if ok and type(id) == "string" then
		return id
	end
	counter = counter + 1
	return "prompt-" .. tostring(counter)
end

function Hooks.purchasePrompted(player, productId)
	local id = newId()
	pending[tostring(player.UserId) .. ":" .. tostring(productId)] = id
	A.funnel(player, "purchase", id, "prompt_shown")
	return id
end

function Hooks.purchaseAccepted(player, productId)
	local id = pending[tostring(player.UserId) .. ":" .. tostring(productId)]
	if id then
		A.funnel(player, "purchase", id, "accepted")
	end
end

function Hooks.purchaseGranted(player, productId)
	local key = tostring(player.UserId) .. ":" .. tostring(productId)
	local id = pending[key]
	if id then
		A.funnel(player, "purchase", id, "granted")
		pending[key] = nil
	end
end

-- @rr source: fare_pack_s fare_pack_m fare_pack_l
function Hooks.farePackGranted(player, sku, coins, newBalance, difficulty)
	A.source(player, coins, newBalance, "IAP", sku, { difficulty = difficulty or "Lobby" })
end

function Hooks.promoRedeemed(player, coins, newBalance)
	A.source(player, coins, newBalance, "Promo", "promo_code", { difficulty = "Lobby" })
end

-- results and leaving -----------------------------------------------------------------------------------
function Hooks.resultsAction(player, action, secondsOnResults)
	A.event(player, "results_action", secondsOnResults, { action = action })
end

function Hooks.playerLeft(player, phase, secondsInPhase, difficulty)
	A.event(player, "player_left", secondsInPhase, { phase = phase, difficulty = difficulty or "Lobby" })
	for key in pairs(pending) do
		if string.sub(key, 1, #tostring(player.UserId) + 1) == tostring(player.UserId) .. ":" then
			pending[key] = nil
		end
	end
end

return Hooks
