# Facts: feel presets, group info (measured by feel.py)

- Phone 844 x 390, FOV 70; camera px = rotation at the screen centre + translation of geometry 8 studs away + half the roll at the screen edge (upper bound).
- Limits: camera px by tier {'1': 40, '2': 28, '3': 18, '4': 10, '5': 4}; hit-stop <= 150 ms; screen flash <= 0.35 (red 0.25), <= 3/s; events <= 3.0 s (fail 3 s).
- Hero alert_fare_banked: peak frame at t=0.22 s. Filmstrip frames are the same mock at six times.

- alert_junction_ahead (tier 3, all): camera 0.0 px (roll 0.0 deg, kick 0.0 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.4 for 50 ms, UI punch 5% / 0.0 px, lasts 0.78 s, loudness 0.018. Reduce motion: camera 0.0 px; reads through haptic, alpha, punch, cue.
- alert_risky_route (tier 3, all): camera 2.5 px (roll 0.0 deg, kick 0.512 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.7 for 50 ms, UI punch 0% / 0.0 px, lasts 0.85 s, loudness 0.028. Reduce motion: camera 0.0 px; reads through haptic, alpha, tween, cue.
- alert_fare_banked (tier 4, all): camera 0.0 px (roll 0.0 deg, kick 0.0 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.52 for 150 ms, UI punch 4% / 0.0 px, lasts 0.8 s, loudness 0.035. Reduce motion: camera 0.0 px; reads through haptic, alpha, tween, punch, cue.
- alert_crate_landed (tier 4, all): camera 3.9 px (roll 0.175 deg, kick 0.614 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.6 for 100 ms, UI punch 0% / 0.0 px, lasts 0.4 s, loudness 0.049. Reduce motion: camera 0.0 px; reads through haptic, alpha, cue.
- alert_crew_joined (tier 5, all): camera 0.0 px (roll 0.0 deg, kick 0.0 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.0 for 0 ms, UI punch 0% / 0.0 px, lasts 0.28 s, loudness 0.0. Reduce motion: camera 0.0 px; reads through alpha.
- alert_crew_left (tier 5, all): camera 0.0 px (roll 0.0 deg, kick 0.0 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.0 for 0 ms, UI punch 0% / 0.0 px, lasts 0.28 s, loudness 0.0. Reduce motion: camera 0.0 px; reads through alpha.

- Sustained rumble (constant while running): Speed at max 1.66 px, pressure at redline 1.66 px, both capped 2.89 px (limit 3 px).
- Limits of these images: the plate is a mock (flat colours, default font, no Roblox lighting); easing uses Penner forms (compare with a Studio dump: feel.py plot curves --compare); sound cues are not shown; the world keeps scrolling during hit-stop because the server moves it. Studio test pending (owner).
