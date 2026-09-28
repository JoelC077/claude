# Facts: feel presets, group lever (measured by feel.py)

- Phone 844 x 390, FOV 70; camera px = rotation at the screen centre + translation of geometry 8 studs away + half the roll at the screen edge (upper bound).
- Limits: camera px by tier {'1': 40, '2': 28, '3': 18, '4': 10, '5': 4}; hit-stop <= 150 ms; screen flash <= 0.35 (red 0.25), <= 3/s; events <= 3.0 s (fail 3 s).
- Hero lever_commit: peak frame at t=0.12 s. Filmstrip frames are the same mock at six times.
- Punch amps and kick angles are delivered peaks; camera pitch + tips the view up, - down.

- lever_commit (tier 3, actor): camera 5.9 px (roll 0.5 deg, kick 0.805 deg), FOV +0 deg, hit-stop 70 ms, screen flash 0.0, haptic 1.0 for 150 ms, UI punch 6% / 0.0 px, lasts 0.64 s, loudness 0.159. Reduce motion: camera 0.0 px; reads through flash, sound, haptic. Outshouts: windows_smash (tier 2, 0.12), hud_crisis_arrival (tier 2, 0.13).
- hard_brake (tier 3, all): camera 3.4 px (roll 0.0 deg, kick 0.699 deg), FOV -4 deg, hit-stop 0 ms, screen flash 0.12, haptic 0.6 for 600 ms, UI punch 0% / 0.0 px, lasts 2.1 s, loudness 0.145. Reduce motion: camera 0.0 px; reads through flash, sound, haptic. Outshouts: windows_smash (tier 2, 0.12), hud_crisis_arrival (tier 2, 0.13).
- alert_crate_landed (tier 4, all): camera 4.1 px (roll 0.2 deg, kick 0.7 deg), FOV +0 deg, hit-stop 0 ms, screen flash 0.0, haptic 0.6 for 100 ms, UI punch 0% / 0.0 px, lasts 0.4 s, loudness 0.036. Reduce motion: camera 0.0 px; reads through alpha, sound, haptic. Outshouts: alert_junction_ahead (tier 3, 0.02), fork_countdown_tick (tier 3, 0.02).
- alert_coal_low (tier 2, all): camera 0.0 px (roll 0.0 deg, kick 0.0 deg), FOV +0 deg, hit-stop 0 ms, screen flash 0.0, haptic 0.5 for 200 ms, UI punch 8% / 4.94 px, lasts 0.8 s + loop, loudness 0.174. Reduce motion: camera 0.0 px; reads through alpha, sound, haptic. Outshouts: no higher-tier event.
- alert_fare_banked (tier 4, all): camera 0.0 px (roll 0.0 deg, kick 0.0 deg), FOV +0 deg, hit-stop 0 ms, screen flash 0.0, haptic 0.52 for 150 ms, UI punch 4% / 0.0 px, lasts 0.8 s, loudness 0.135. Reduce motion: camera 0.0 px; reads through alpha, tween, sound, haptic. Outshouts: alert_junction_ahead (tier 3, 0.02), fork_countdown_tick (tier 3, 0.02), alert_risky_route (tier 3, 0.10), windows_smash (tier 2, 0.12), hud_crisis_arrival (tier 2, 0.13).

- Sustained rumble (constant while running): Speed at max 1.66 px, pressure at redline 1.66 px, both capped 2.89 px (limit 3 px).
- Limits of these images: the plate is a mock (flat colours, default font, no Roblox lighting); easing uses Penner forms (compare with a Studio dump: feel.py plot curves --compare); sound cues are not shown; the world keeps scrolling during hit-stop because the server moves it. Studio test pending (owner).
