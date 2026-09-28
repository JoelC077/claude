#!/usr/bin/env python3
"""make_fixture.py - build a synthetic Risky Rails-like place file for the rr-release-train trial.

  make_fixture.py OUT.rbxl --version 0.1.0-alpha.1 [--grow] [--union] [--debug]

Not a real Risky Rails place: a small binary place with the services, a train model, scripts that read like the
game's (crisis manager, ProfileStore, lever), an RR_Version stamp and optional issues for the gates to find.
"""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "rr-release-train" / "scripts"))
import placefile

CRISIS = '''local ProfileStore = require(game.ServerScriptService.ProfileStore)
local Store = ProfileStore.New("PlayerData_alpha1", {coins = 0, hintsSeen = false})
local DEBUG = %s
local COAL_LOW = 20
local function onCoalLow(train)
	if DEBUG then print("coal low", train.Coal.Value) end
	train:SetAttribute("Alert", "COAL LOW")
end
return {onCoalLow = onCoalLow}
'''
LEVER = '''local Remote = game.ReplicatedStorage.Remotes.PullLever
Remote.OnServerEvent:Connect(function(player, choice)
	if typeof(choice) ~= "string" or (choice ~= "safe" and choice ~= "risky") then return end
	workspace.Train:SetAttribute("Fork", choice)
end)
'''
SPEC = '''return {
	["coal low fires at 20"] = function() assert(20 == 20) end,
}
'''

def build(out, version, grow=False, union=False, debug=False):
    I, r = [], [0]
    def add(cls, parent, **props):
        ref = r[0]; r[0] += 1
        I.append((ref, cls, parent, props)); return ref
    ws = add("Workspace", None, Name="Workspace", StreamingEnabled=True)
    add("Lighting", None, Name="Lighting")
    rs = add("ReplicatedStorage", None, Name="ReplicatedStorage")
    sss = add("ServerScriptService", None, Name="ServerScriptService")
    add("ModuleScript", rs, Name="RR_Version", Source=f'return {{\n\tversion = "{version}",\n\tchannel = "alpha",\n}}\n')
    rem = add("Folder", rs, Name="Remotes")
    add("RemoteEvent", rem, Name="PullLever")
    add("ModuleScript", sss, Name="CrisisManager", Source=CRISIS % ("true" if debug else "false"))
    add("Script", sss, Name="Lever", Source=LEVER)
    add("ModuleScript", sss, Name="Crisis.spec", Source=SPEC)
    train = add("Model", ws, Name="Train")
    n = 40 if grow else 30
    for i in range(n):
        add("Part", train, Name=f"Coach{i}", Anchored=i % 10 != 0, Color=("rgb8", 42, 96, 64))
    add("Part", train, Name="Buffer", Anchored=True, Color=("rgb8", 246, 197, 0))
    add("Part", ws, Name="PLACEHOLDER_Signal", Anchored=True, Color=("rgb8", 255, 0, 255))
    if union:
        add("UnionOperation", train, Name="BoilerUnion", Anchored=True)
    if grow:
        add("ParticleEmitter", train, Name="Steam")
        add("Script", sss, Name="Supplies", Source="-- supply terminal\nlocal PRICE = {coal = 10}\nreturn PRICE\n")
    placefile.write_binary(out, I)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out"); ap.add_argument("--version", required=True)
    ap.add_argument("--grow", action="store_true"); ap.add_argument("--union", action="store_true")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    build(a.out, a.version, a.grow, a.union, a.debug)
    print(f"wrote {a.out}")
