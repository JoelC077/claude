# Facts: feel presets, group lever (measured by feel.py)

- Phone 844 x 390, FOV 70; camera px = rotation at the screen centre + translation of geometry 8 studs away + half the roll at the screen edge (upper bound).
- Limits: camera px by tier {'1': 40, '2': 28, '3': 18, '4': 10, '5': 4}; hit-stop <= 150 ms; screen flash <= 0.35 (red 0.25), <= 3/s; events <= 3.0 s (fail 3 s).
- Hero lever_commit: peak frame at t=0.12 s. Filmstrip frames are the same mock at six times.

- fork_countdown_tick (tier 3, all): camera 0.0 px (roll 0.0 deg, kick 0.0 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.35 for 33 ms, UI punch 6% / 0.0 px, lasts 0.35 s, loudness 0.018. Reduce motion: camera 0.0 px; reads through haptic, punch, cue.
- lever_detent_tick (tier 5, actor): camera 0.0 px (roll 0.0 deg, kick 0.0 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.5 for 33 ms, UI punch 4% / 0.0 px, lasts 0.2 s, loudness 0.016. Reduce motion: camera 0.0 px; reads through haptic, punch.
- lever_commit (tier 3, actor): camera 5.9 px (roll 0.502 deg, kick 0.804 deg), FOV 0.0, hit-stop 70 ms, screen flash 0.0, haptic 1.0 for 150 ms, UI punch 6% / 0.0 px, lasts 0.64 s, loudness 0.183. Reduce motion: camera 0.0 px; reads through haptic, flash, punch, cue.
- lever_commit_crew (tier 4, crew): camera 2.5 px (roll 0.205 deg, kick 0.358 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.5 for 67 ms, UI punch 0% / 0.0 px, lasts 0.5 s, loudness 0.022. Reduce motion: camera 0.0 px; reads through haptic, cue.
- lever_snapback (tier 5, actor): camera 0.0 px (roll 0.0 deg, kick 0.0 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.25 for 33 ms, UI punch 0% / 2.74 px, lasts 0.25 s, loudness 0.003. Reduce motion: camera 0.0 px; reads through haptic, punch.
- route_locked (tier 4, all): camera 0.0 px (roll 0.0 deg, kick 0.0 deg), FOV 0.0, hit-stop 0 ms, screen flash 0.0, haptic 0.0 for 0 ms, UI punch 0% / 0.0 px, lasts 0.95 s, loudness 0.0. Reduce motion: camera 0.0 px; reads through alpha.

- Sustained rumble (constant while running): Speed at max 1.66 px, pressure at redline 1.66 px, both capped 2.89 px (limit 3 px).
- Limits of these images: the plate is a mock (flat colours, default font, no Roblox lighting); easing uses Penner forms (compare with a Studio dump: feel.py plot curves --compare); sound cues are not shown; the world keeps scrolling during hit-stop because the server moves it. Studio test pending (owner).
