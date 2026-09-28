#!/usr/bin/env python3
"""make_places.py - stand-in Lobby/Trip place files for the v0.4.0 dry-run trial (NOT the real game).

  make_places.py OUTDIR --stamp-version 0.3.0            # the "before stamp" build
  make_places.py OUTDIR --stamp-file RR_Version.lua      # the owner pasted rel stamp's module and re-exported

No Studio in the cloud, so the owner's File > Save to File is simulated: the base scripts come from the builder's
trial fixture (crisis manager, lever, spec), plus this release's real mission exports:
- Ticket HUD (missions/260927-ticket-hud/export/roblox/src): NotificationHud + NotificationController as
  ModuleScripts in ReplicatedStorage.RR_Notifications (both places); NotificationDemo LocalScript left in the
  Lobby's StarterPlayerScripts on purpose (ASSETS.md says "delete for release": does G9 catch it?).
- Depot buildings (missions/260927-depot-buildings/export/*/parts.csv): one MeshPart per row, Color from the csv
  hex, grouped as Workspace.Depot and Workspace.MainHall (Lobby only).
"""
import argparse, csv, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLAUDE = HERE.parents[2]
sys.path.insert(0, str(CLAUDE / "rr-release-train" / "scripts"))
sys.path.insert(0, str(HERE.parent))
import placefile  # noqa: E402
import make_fixture as fx  # noqa: E402

HUD = CLAUDE / "missions/260927-ticket-hud/export/roblox/src"
DEPOT = CLAUDE / "missions/260927-depot-buildings/export"


def build(out, stamp_src, lobby):
    I, r = [], [0]

    def add(cls, parent, **props):
        ref = r[0]; r[0] += 1
        I.append((ref, cls, parent, props)); return ref
    ws = add("Workspace", None, Name="Workspace", StreamingEnabled=True)
    add("Lighting", None, Name="Lighting")
    rs = add("ReplicatedStorage", None, Name="ReplicatedStorage")
    sss = add("ServerScriptService", None, Name="ServerScriptService")
    sp = add("StarterPlayer", None, Name="StarterPlayer")
    sps = add("StarterPlayerScripts", sp, Name="StarterPlayerScripts")
    add("ModuleScript", rs, Name="RR_Version", Source=stamp_src)
    rem = add("Folder", rs, Name="Remotes")
    add("RemoteEvent", rem, Name="PullLever")
    add("ModuleScript", sss, Name="CrisisManager", Source=fx.CRISIS % "false")
    add("Script", sss, Name="Lever", Source=fx.LEVER)
    add("ModuleScript", sss, Name="Crisis.spec", Source=fx.SPEC)
    nf = add("Folder", rs, Name="RR_Notifications")
    for m in ("NotificationHud", "NotificationController"):
        add("ModuleScript", nf, Name=m, Source=(HUD / f"{m}.lua").read_text())
    train = add("Model", ws, Name="Train")
    for i in range(30):
        add("Part", train, Name=f"Coach{i}", Anchored=i % 10 != 0, Color=("rgb8", 42, 96, 64))
    if lobby:
        add("LocalScript", sps, Name="NotificationDemo", Source=(HUD / "NotificationDemo.client.lua").read_text())
        for bld, model in (("depot", "Depot"), ("hall", "MainHall")):
            m = add("Model", ws, Name=model)
            for row in csv.DictReader(open(DEPOT / bld / "parts.csv")):
                h = row["hex"].lstrip("#")
                add("MeshPart", m, Name=row["name"], Anchored=True, CanCollide=row["cancollide"] == "true",
                    Color=("rgb8", int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)))
    placefile.write_binary(out, I)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdir")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--stamp-version")
    g.add_argument("--stamp-file")
    a = ap.parse_args()
    src = (Path(a.stamp_file).read_text() if a.stamp_file
           else f'return {{\n\tversion = "{a.stamp_version}",\n\tchannel = "alpha",\n}}\n')
    o = Path(a.outdir); o.mkdir(parents=True, exist_ok=True)
    build(o / "Lobby.rbxl", src, True)
    build(o / "Trip.rbxl", src, False)
    print(f"wrote {o}/Lobby.rbxl, {o}/Trip.rbxl")
