# Facts: feel presets, group crisis (measured by feel.py)

- Phone 844 x 390, FOV 70; camera px = rotation at the screen centre + translation of geometry 8 studs away + half the roll at the screen edge (upper bound).
- Limits: camera px by tier {'1': 40, '2': 28, '3': 18, '4': 10, '5': 4}; hit-stop <= 150 ms; screen flash <= 0.35 (red 0.25), <= 3/s; events <= 3.0 s (fail 3 s).
- Hero alert_breakdown: peak frame at t=0.03 s. Filmstrip frames are the same mock at six times.

- hud_crisis_arrival (tier 2, all): camera 0.0 px (roll 0.0 deg, kick 0.0 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.0 for 0 ms, UI punch 0% / 4.62 px, lasts 0.8 s + loop, loudness 0.0. Reduce motion: camera 0.0 px; reads through alpha, punch.
- alert_coal_low (tier 2, all): camera 0.0 px (roll 0.0 deg, kick 0.0 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.5 for 200 ms, UI punch 8% / 4.62 px, lasts 0.8 s + loop, loudness 0.052. Reduce motion: camera 0.0 px; reads through haptic, alpha, punch, cue.
- alert_pressure_high (tier 2, all): camera 1.0 px (roll 0.057 deg, kick 0.0 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.22 red, haptic 0.7 for 300 ms, UI punch 0% / 4.62 px, lasts 0.8 s + loop, loudness 0.187. Reduce motion: camera 0.0 px; reads through haptic, flash, alpha, punch, cue.
- alert_breakdown (tier 2, all): camera 7.1 px (roll 0.576 deg, kick 0.647 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.2, haptic 0.9 for 300 ms, UI punch 0% / 4.62 px, lasts 0.9 s + loop, loudness 0.247. Reduce motion: camera 0.0 px; reads through haptic, flash, alpha, punch, cue.
- alert_passengers_upset (tier 2, all): camera 0.0 px (roll 0.0 deg, kick 0.0 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.45 for 283 ms, UI punch 0% / 4.62 px, lasts 0.8 s + loop, loudness 0.042. Reduce motion: camera 0.0 px; reads through haptic, alpha, punch, cue.
- windows_smash (tier 2, all): camera 1.4 px (roll 0.082 deg, kick 0.0 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.178, haptic 0.8 for 100 ms, UI punch 0% / 0.0 px, lasts 0.25 s, loudness 0.134. Reduce motion: camera 0.0 px; reads through haptic, flash, cue.
- coupling_snap (tier 2, all): camera 10.2 px (roll 0.63 deg, kick 0.892 deg), FOV 4.0, hit-stop 0 ms, screen flash 0.0, haptic 1.0 for 400 ms, UI punch 0% / 0.0 px, lasts 0.9 s, loudness 0.251. Reduce motion: camera 0.0 px; reads through haptic, cue.

- Sustained rumble (constant while running): Speed at max 1.66 px, pressure at redline 1.66 px, both capped 2.89 px (limit 3 px).
- Limits of these images: the plate is a mock (flat colours, default font, no Roblox lighting); easing uses Penner forms (compare with a Studio dump: feel.py plot curves --compare); sound cues are not shown; the world keeps scrolling during hit-stop because the server moves it. Studio test pending (owner).
