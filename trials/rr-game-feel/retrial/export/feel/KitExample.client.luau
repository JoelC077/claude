--!strict
-- Re-trial wiring example (rr-game-feel after fixes): the five moments through RR_FeelTyped.
-- Two-way lever with one commit per junction, HUD money format, actor routing. Studio test pending (owner).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local Feel = require(ReplicatedStorage:WaitForChild("RRFeel"):WaitForChild("RR_FeelTyped"))

type LeverParts = { panel: Frame, knob: GuiButton, lamp: Frame }

local function wireLever(parts: LeverParts, travelPx: number, junctionId: () -> number)
	local dragging, startX = false, 0
	local targets = { lever_panel = parts.panel, lever_knob = parts.knob, lamp = parts.lamp }
	parts.knob.InputBegan:Connect(function(input: InputObject)
		if input.UserInputType == Enum.UserInputType.Touch or input.UserInputType == Enum.UserInputType.MouseButton1 then
			dragging, startX = true, input.Position.X
		end
	end)
	-- global tracking: the finger leaves the 64 px knob while dragging
	UserInputService.InputChanged:Connect(function(input: InputObject)
		if not dragging then return end
		local u = (input.Position.X - startX) / travelPx -- signed: - left branch, + right branch
		local shown = Feel.leverDrag(u, { targets = targets, fork = junctionId() })
		parts.knob.Position = UDim2.new(0.5, shown * travelPx, 0.5, 0)
	end)
	UserInputService.InputEnded:Connect(function(input: InputObject)
		if not dragging then return end
		dragging = false
		if Feel.leverRelease({ targets = targets }) == "snapback" then
			Feel.animateValue(parts.knob.Position.X.Offset, 0, { style = "Back", dir = "Out", dur = 0.25 }, function(v: number)
				parts.knob.Position = UDim2.new(0.5, v, 0.5, 0)
			end)
		end
	end)
end

-- HUD: call after NotificationController builds the ticket at rest (its own slide, shake and halo code removed)
local function onTicket(typeName: string, parts: { mover: Frame, stamp: TextLabel?, haloRed: Frame? }, amount: number?,
	formatCash: (number) -> string)
	if typeName == "FareBanked" then
		Feel.play("alert_fare_banked", { targets = { ticket = parts.mover, stamp = parts.stamp, cash = parts.stamp },
			count = { amount = amount or 0, format = formatCash } })
	elseif typeName == "CrateLanded" then
		Feel.play("alert_crate_landed", { targets = { ticket = parts.mover } })
	elseif typeName == "CoalLow" then
		Feel.play("alert_coal_low", { targets = { ticket = parts.mover, halo = parts.haloRed } })
	end
end

local function onHardBrake(actorUserId: number?)
	Feel.playFor("hard_brake", actorUserId, nil)
end

return { wireLever = wireLever, onTicket = onTicket, onHardBrake = onHardBrake }
