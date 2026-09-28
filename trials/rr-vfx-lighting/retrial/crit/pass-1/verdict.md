FIRST READ: The eye goes up the hazard-yellow roof rails to the loco, up the white steam column into a grey smoke cap, then out to the hedges and the grey-green haze. The day roof view reads as a calm, well-hazed ride that matches the brief.
Nothing in any roof tile says "brake crisis": the sparks are hidden by the train. Dusk and night go murky, and in the door views the coach wall fills the frame while the sparks are a speck at the wheels.

SCORES:
F1 Signal: 4/10 — meets 4 because you cannot tell from roof3p that the brake crisis has started. sparks_brake shows 3/92 visible at 0.00% of screen on PC and 1/61 at 0.00% on phone (tiles 1-4). From door1p it covers 0.16% of screen against steam's 0.90% (tiles 5-7), so the crisis is quieter than the ambience, which goes against the owner's "loudest thing in frame". coal_dust reads only through the firebox flare in a cab that is 27% crushed. At night the train falls to 1.57:1 against the world (door 1.05:1). Below 7 because of C1-1, C1-2, C1-3 and C3-2.
F2 Form and motion: 6/10 — above 4 because the sparks strip has a designed fan: a hot core at the shoe with streaks thrown back. Steam and smoke stream back at Speed 35 and fade out. The day look layers near rails, middle hedges and far haze, and the hedges have a lit top and a darker side. Below 7 because the smoke is a row of equal dots (strip 4), the coal_dust burst is small and short with no embers (strip 1), the steam beads, and the dusk key is flat. That is more than one gap: C2-1, C2-2, C2-3, C2-4.
F3 Colour and value: 5/10 — the day look alone meets 7: ground #93A660 at saturation 0.28, grey-green sky #ACBEAE, 0% clip or crush, train 3.25:1. The other looks drift: dusk sky and ground are nearly the same value, dusk steam goes grey-on-grey (-4/9), the night sky is #01030F with a horizon band, cab1p crush is 27.16% and night door1p crush is 6.18%. Below 7 because of C1-2, C1-3, C3-1, C3-2 and C3-3.
F4 Phone read: 5/10 — above 4 because the day phone frame at 1:1 (tile 1) reads without shadows, Bloom or SunRays: the plume, the yellow rails and the train at 3.18:1 all hold. Below 7 because the phone loses more than one signal. Brake sparks are 1/61 visible at 0.00% of screen. The night phone view is murky (1.55:1, closeups tile 7). Dusk phone steam is faint (-4/7). storm_crisis sits at 390 of 400 steady, leaving 2.5% headroom. Issues: C1-1, C1-2, C3-2, C4-1.
F5 Style match: 6/10 — the day look matches the house style: grey-green haze, muted grass, chunky hedge boxes, capped hazard-yellow rails, and no sepia or blue-sky bands. Below 7 because two looks break the family. Dusk goes drab olive-khaki under a mauve murk. Night goes near-black and cold navy, leaning toward horror darkness. Issues: C3-1, C3-3.
F6 Polish: 6/10 — above 4 because the day tiles look finished and the steam and spark fades in the strips are clean. Below 7 because the sparks spawn inside the body (89/92 hidden, C1-1), an orange light dot is drawn on train surfaces in every POV tile (C6-1), the night horizon has a band (C3-3), and the coal dust vanishes on the dark backdrop (C2-2).

ISSUES (ranked by impact, lowest-scoring criteria first; issue format):
[C1-1] F1/F4/F6 · sparks_brake, roof3p PC and phone (tiles 1-4) and door1p (tiles 5-7)   impact: high   blocks-8: yes
  Problem: From roof3p, 89 of 92 live sparks are hidden by the train (h89), with 0.00% screen share; the phone view shows 1/61. From door1p, 28/92 are visible at 0.16% of screen with mean/p90 luma change +29/73, while steam covers 0.90%. The emitters sit inside the 17.4-wide body, so the fans never clear the sides.
  Fix: Put the sparks_brake Attachments outboard of the body at x = ±9.3, y = 1.0 on every BrakeShoe, and add the same emitter to the coach A and coach B bogies, so there are sparks under the player as well as at the loco. Set EmissionDirection outward (±X) with SpreadAngle (20, 40), Speed 18–30, Acceleration (0,-30,0) so the arcs rise 3–5 studs outside the body line. Raise Size to 0.5→0.15 and keep LightEmission 1.
  Done when: roof3p PC and phone POV show at least 50% of live sparks visible (not h), at least 1.0% of screen, and a mean luma change at least equal to steam's in the same tile; door1p sparks cover at least 1.5% of screen, more than steam.
[C1-2] F1/F3/F4 · grassland.night roof3p and door1p, grassland.dusk door1p   impact: high   blocks-8: yes
  Problem: Train vs world is 1.57:1 on night roof (phone 1.55:1), 1.05:1 on night door with 6.18% crush, and 1.11:1 on dusk door. In tile 4 the navy roof merges into the dark ground and only the rails read.
  Fix: For grassland.night, raise Lighting.OutdoorAmbient to about #3A4652 and add a warm cream PointLight inside each coach (Brightness 1.5, Range 14) so light spills from doorways and windows onto the roof edges. For grassland.dusk, raise Lighting.OutdoorAmbient by about 20%.
  Done when: train vs world is at least 2:1 on night roof3p (PC and phone), night door1p and dusk door1p, and night door1p crush is 5% or less.
[C1-3] F1/F3 · coal_dust and lighting, cab1p (closeups tile 5)   impact: high   blocks-8: yes
  Problem: 27.16% of the frame is crushed (train 27.99%) and the upper cab is solid black. The dust puff is darker than what it covers (-26/117), so the shovel event reads only through the orange grille flare. In the dark-backdrop strip at t=0.4 s the puff is nearly invisible.
  Fix: Add a cab PointLight at the cab ceiling (Brightness 0.6, Range 10, cream token). Change the coal_dust dust Color to ash grey #9A9088 with LightInfluence 0.4, so the puff sits lighter than the cab shadow and darker than the flare.
  Done when: cab1p crush is 5% or less, coal mean luma change is +15 or more, and the firebox flare is still the brightest element in the frame.
[C3-1] F3/F5 · grassland.dusk, roof3p (tile 3, closeups tile 6)   impact: med   blocks-8: yes
  Problem: Sky #685A60 and ground #6C6849 are nearly equal in value, so the horizon dissolves. The ground drifts to olive-khaki (hue about 53 deg against day's about 79 deg), which gives a drab, dusty frame rather than a warm dusk.
  Fix: Lighten grassland.dusk Atmosphere.Color to about #9C8E98 and set Atmosphere.Glare 0.4. Shift ColorCorrection.TintColor toward green, about #F0F6EC, to keep the grass grey-green. Keep the haze Density at about 0.3.
  Done when: dusk sky mean luma is at least ground + 25, ground hue is 65 deg or more, bands stay none and spawn-edge fog stays 0.9 or more.
[C3-2] F3/F1 · steam_chimney and smoke_chimney, dusk and night roof3p (tiles 3-4)   impact: med   blocks-8: yes
  Problem: At dusk, steam changes luma by -4/9 (phone -4/7) and smoke by -11/23, so the white steam reads as a dark coal plume. At night, smoke changes luma by -0/2 and is invisible. The speed plume turns grim at dusk.
  Fix: Set steam_chimney LightEmission 0.2 and LightInfluence 0.7. Darken smoke_chimney Color to about #2E2A28 at dusk. At night give the smoke LightInfluence 0.3 with a faint underside tint from the firebox (#6A4A3A).
  Done when: dusk steam mean luma change is +12 or more and p90 is 30 or more (phone too), dusk smoke p90 is 30 or more, and night steam p90 stays 40 or more.
[C3-3] F3/F5/F6 · grassland.night sky, roof3p and door1p (tiles 4, 7)   impact: med   blocks-8: yes
  Problem: The sky measures #01030F/#00030E, close to black, and a lighter fog band sits across the horizon (tile 4). This reads cold and horror-dark, not a warm-hearted night. The skybox is not modelled in the preview, so part of this may be a preview limit; confirm it in Studio.
  Fix: Set grassland.night Atmosphere.Color to about #3C4A52 and Atmosphere.Haze to 1.5, with a night Sky tinted deep blue-green (about #1A2630 at the zenith).
  Done when: night sky mean is about #1A2430 or brighter (luma 20 or more), the step from sky to horizon fog is 15 luma or less, and the Studio night capture matches.
[C4-1] F4 · phone budget, storm_crisis set (Facts, Budgets)   impact: med   blocks-8: no
  Problem: storm_crisis uses 390 of 400 on phone steady, leaving 2.5% headroom. Enlarging the sparks fans (C1-1) or adding emitters would push it over.
  Fix: In crisis sets on phone, scale smoke_chimney (priority 3) to 50% rate and steam_chimney to 75%. Keep sparks_brake and coal_dust at full rate.
  Done when: phone storm_crisis steady is 360 of 400 or less, with the crisis presets at full rate.
[C2-1] F2 · smoke_chimney, side strip (closeups strip 4)   impact: med   blocks-8: yes
  Problem: At 2.61 px/stud the puffs are 1.5–2 studs, equal in size and evenly spaced, so they read as a dotted line rather than chunky coal puffs mixed into the steam.
  Fix: Set smoke_chimney Size to NumberSequence {0:1.5, 0.5:4, 1:6.5}, Lifetime 3.5–5, SpreadAngle (6,6) and Transparency {0:0.35, 0.7:0.55, 1:1}.
  Done when: the Speed 35 strip shows puffs at least 4 studs wide by mid-strip with overlapping edges and no evenly spaced dot row.
[C2-2] F2/F6 · coal_dust burst, time strip (closeups strip 1)   impact: med   blocks-8: yes
  Problem: At t=0.4 s the puff is two brown blobs about 2 studs across and is faint by 1 s. No ember points are visible, and the puff almost disappears on the dark backdrop.
  Fix: Set the dust emitter Size to {0:1, 0.3:3.5, 1:5} and Lifetime 1.4–2.0. Add an embers emitter: Count 12, Size 0.25, LightEmission 1, Color #FFB347→#FF6A00, Lifetime 0.8–1.4, Speed 6–10 up, Acceleration (0,-8,0).
  Done when: at t=0.4 s the strip shows a puff at least 4 studs wide and at least 6 ember points on both sky and dark backdrops, and the puff is still visible at t=1 s.
[C6-1] F6 · light glow dot, POV tiles 1-2 (loco roof) and 5-7 (coach A wall)   impact: med   blocks-8: yes
  Problem: An orange glow dot sits on train surfaces in every POV tile, as if a light is shining through the body. It is likely the sparks_brake ground glow. The preview draws lights as dots only, so I can't tell how this looks in the engine.
  Fix: Put the ground-glow PointLight on an Attachment at y = 0.3, x = ±10, outboard of the body, with Shadows = true, Range 12, Brightness 3, Color #FFB347.
  Done when: no light dot overlaps train pixels in any POV tile, and the Studio capture shows the glow on the ballast beside the wheels.
[C2-3] F2 · steam_chimney, side strip (closeups strip 3)   impact: low   blocks-8: no
  Problem: The plume is a chain of equal, evenly spaced blobs (beading) rather than one continuous plume that widens.
  Fix: Set steam_chimney Size to {0:2, 1:7} with a size envelope of 0.5, Lifetime 1.8–3.0 and RotSpeed -40..40.
  Done when: the strip shows one continuous plume that widens, with no repeating blob pattern.
[C2-4] F2 · grassland.dusk key light (tile 3)   impact: low   blocks-8: no
  Problem: Sun elevation is 1.7 deg, so the light is flat. The hedges show no lit or shaded face and cast no readable shadow, and depth is muddy.
  Fix: Set grassland.dusk ClockTime so the sun sits at about 8 deg (inside the OQ-026 default C window).
  Done when: in the dusk roof3p PC view the lit and shaded faces of the hedges differ by 15 luma or more and the hedges cast visible shadows.

OVERALL: 4 (F1 Signal)
NEEDS OWNER: sparks_brake is a proposed effect, since canon has only the brake. Approve it, including sparks on coach bogies as well as the loco. OQ-026: the dusk sun elevation and when the looks change. OQ-029: whether phone default A (400 steady) stands, given the 2.5% headroom. Whether coaches carry interior lights at night, which is tied to livery OQ-025. A Studio test is needed for the night skybox and for how the lights behave.
KEEP: 1) The grassland.day look: grey-green haze sky #ACBEAE, ground at saturation 0.28, spawn-edge fog 0.956, no bands. 2) The sparks_brake fan shape in the strip: hot core at the shoe, streaks thrown back. 3) The firebox flare in cab1p (warm orange grille glow) and the hazard-yellow rails reading in every look.