# Risky Rails standing facts (seed; never ask the owner these)

Overridden by `<project>/.rr-missions/memory/owner-prefs.md` (dated owner statements) when present.

- Game: Roblox, trains on rails; players ride the train, the world scrolls past (in-run). Lobby (Depot Lobby) is walk-around, static.
- Camera and scale: read live, never from here: `bible.py get tech.camera --values` (eye_3p, eye_1p, fov_v) and `get tech.units --values` (avatar_h, building_door, stud_m). Units are studs.
- 3D budget: <= 10k tris per MeshPart (cap 20k); one 256px palette atlas, 32px cells, Closest filtering, one material; named separate parts.
- UI devices: phone landscape 844x390 primary (true size), PC 1280x720 second; Scale + UIAspectRatioConstraint; avoid Roblox topbar, thumbstick (bottom-left) and jump button (bottom-right) zones.
- Fonts: Luckiest Guy (titles, stamps), Montserrat 600-800 (body).
- House style: chunky, readable, weathered-rural railway (stone, iron, timber, moss, soot, brass); bold ink outlines on UI; decay at edges, clean routes.
- Default bar: 8/10 every criterion; cap 5 critic passes.
- Owner preferences seen so far: likes the ticket frame (HUD); wants editable separate parts; wants numbered progress steps; target 8/10.
- Critic cost lever: `design-critic` agent not yet installed (offer once).
