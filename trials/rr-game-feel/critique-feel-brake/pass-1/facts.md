# Facts: feel presets, group actions (measured by feel.py)

- Phone 844 x 390, FOV 70; camera px = rotation at the screen centre + translation of geometry 8 studs away + half the roll at the screen edge (upper bound).
- Limits: camera px by tier {'1': 40, '2': 28, '3': 18, '4': 10, '5': 4}; hit-stop <= 150 ms; screen flash <= 0.35 (red 0.25), <= 3/s; events <= 3.0 s (fail 3 s).
- Hero hard_brake: peak frame at t=0.15 s. Filmstrip frames are the same mock at six times.

- hard_brake (tier 3, all): camera 3.4 px (roll 0.0 deg, kick 0.696 deg), FOV 4.0, hit-stop 0 ms, screen flash 0.12, haptic 0.6 for 600 ms, UI punch 0% / 0.0 px, lasts 2.1 s, loudness 0.167. Reduce motion: camera 0.0 px; reads through haptic, flash, cue.

- Sustained rumble (constant while running): Speed at max 1.66 px, pressure at redline 1.66 px, both capped 2.89 px (limit 3 px).
- Limits of these images: the plate is a mock (flat colours, default font, no Roblox lighting); easing uses Penner forms (compare with a Studio dump: feel.py plot curves --compare); sound cues are not shown; the world keeps scrolling during hit-stop because the server moves it. Studio test pending (owner).
