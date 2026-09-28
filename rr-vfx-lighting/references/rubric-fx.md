# Profile F: effects and lighting (merged into CRIT/rubric.md by `vfx.py crit`)

Read by the critic only through critic.md; `vfx.py crit` inserts the section below into a copy of multiuse-critic's
rubric (before "Shared blocks") and adds F5 to the House style block and F2 to the Motion note. Edit anchors here.

## Profile F — Effects and lighting (Roblox look-dev presets)

Judge the preview images as intent: shape, colour, value and readability. They are approximations of Roblox (the
Limits line in Facts says how), so never score engine-exact pixels; do score what the preset data would plainly do.
Judge signal from the player-view (POV) tiles and the per-effect visibility numbers in Facts; side strips are
construction views for shape and timing. The train is a stand-in (livery open): judge looks and effects, not its paint.

### F1 Signal
Does each effect or look say its game state at a glance from the player's view (crisis, speed, danger, fail)?
- **4:** You cannot tell which crisis an effect belongs to, or a look hides the train, the interaction points or the HUD area.
- **7:** Every crisis effect is recognisable in the POV frame, but one reads late (too small, too brief or lost against its backdrop) or two crises look alike.
- **9:** Each crisis effect is unmistakable within a second from the roof or door view, louder than any ambience; looks keep the train and interactables the clearest thing in frame.

### F2 Form and motion
Particles: silhouette over life, size and transparency curves, drift with the train's speed. Lighting: key direction, shadow shape, depth layering.
- **4:** Uniform blobs or dots, popping in or out, effects that drift the wrong way for a moving train, or flat lighting with no key direction.
- **7:** Clear shapes that grow and fade believably and stream back with speed; one effect is lumpy, too sparse or ends abruptly, or one look has muddy depth.
- **9:** Every effect has a designed shape at start, middle and end, chunky enough for the toy-like style; looks layer near, middle and far ground cleanly with a readable key light.

### F3 Colour and value
- **4:** Off-palette, muddy or washed-out colour; values collapse so the train, ground and sky merge; night or tunnel goes black.
- **7:** Disciplined palette with clear value steps; one look or effect drifts (too saturated ground, grey-on-grey smoke, a crushed or clipped area).
- **9:** Every colour is a house token or a declared effect colour used on purpose; value separates sky, ground, train and effects in every look, day to night.

### F4 Phone read
Judge the phone-fallback renders (no shadows, no Bloom or SunRays) and the phone budget in Facts.
- **4:** The look depends on post effects or shadows that phones drop, or the crisis stack is over the phone budget.
- **7:** Phone renders still read, with one noticeable loss (a night look goes murky, a glow disappears); budgets are within limits but tight.
- **9:** Phone fallback looks intentional, not broken; every crisis signal survives the priority scaling; budgets have headroom.

### F5 Style match
See the shared House style block, applied to light, haze and effect colour.
- **4:** It looks like another game: Dead Rails sepia or desert haze, Land or Die blue sky, realistic grit or horror darkness.
- **7:** It shares the palette and tone, but one look or effect breaks the family (a realistic smoke, a cold horror tunnel, a neon glow).
- **9:** Slapstick, chunky, readable and warm-hearted in every look and effect: you would assume the same art director made them with the approved assets.

### F6 Polish
- **4:** Placeholder-looking effects, abrupt transitions, visible emitter boxes or seams, effects clipping through the train.
- **7:** Finished where players look; small issues remain (an ember colour off, a beam end too hard, a look's horizon band).
- **9:** Rewards a close look: timings, fades and colour ramps are deliberate, and the set is consistent across all presets.
