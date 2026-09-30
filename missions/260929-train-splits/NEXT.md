# v2 plan (resume ~2026-10-14, after Joel builds the 3 MVP trains)

## Joel asked for
- Better VFX (fx critic stood at 5/10 with round-1 fixes unscored; lean bigger and punchier).
- Works on every train type: 2-carriage and one continuous train. Joel provides the code that decides the train type.
- Players in broken sections get ragdoll-flung, with more explosions for comedy.

## JARVIS adds
- Per-train config block (break count and positions, tear pattern) in place of the hard-coded roof signature and the 2-carriage limit.
- A generic jagged tear that fits any carriage cross-section, plus the checker suggesting a clean break band.
- Update RR_BreakChecker to the in-place RR_Half labels.
- Update the Lune tests to the live roof signature and the in-place mode, then get back to all green.
- Pre-snap warning phase (creaks, sparks, crack line) so players can react.
- A secondary explosion when the wreck lands.
- Replace the stand-in fx in the animation GIFs with the real particle look.
- Finish the gates skipped in v1: fx and sound final critic passes, 3D critic, security re-check.
- Sounds: Joel uploads the 6 wavs and pastes the ids.

## Bring
Each train's RR_BreakChecker output (or OBJ export), plus the train-type code.
