local Remote = game.ReplicatedStorage.Remotes.PullLever
Remote.OnServerEvent:Connect(function(player, choice)
	if typeof(choice) ~= "string" or (choice ~= "safe" and choice ~= "risky") then return end
	workspace.Train:SetAttribute("Fork", choice)
end)
