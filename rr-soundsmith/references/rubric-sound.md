# Profile S: sound plan (merged into CRIT/rubric.md by `sound.py crit`)

Read by the critic only through critic.md; `sound.py crit` inserts the section below into a copy of multiuse-critic's
rubric (before "Shared blocks") and adds S5 to the House style block. Edit anchors here, keep the headings.

## Profile S — Sound plan (event map, mix and measured audio for Roblox)

You cannot hear anything. Judge what the images and Facts show: the loudness ladder (bar = in-game target, dot = the
same sound through a phone speaker), waveform and spectrogram tiles, the timeline of each sound against the
rr-game-feel channels, and the measurement and event tables. Placeholder timbre is not the brief: never score "how it
sounds"; score the plan, the levels, timing, distinctness, phone survival and coverage as measured.

### S1 Signal and hierarchy
Does each event get a sound that says what happened and how urgent, and do more important tiers sit louder (fail > crisis > commit > reward > UI > loops)?
- **4:** Tiers overlap on the ladder, a routine sound sits above a crisis alarm, or two crisis alarms look alike in the tiles (same rhythm, same band) so the other carriage could not tell them apart.
- **7:** The ladder steps in order and each crisis alarm has its own rhythm or band; one pair is close (under 2 LU apart across tiers) or one alarm's shape resembles another's.
- **9:** Clean steps by tier on the bars and on the phone dots, every crisis alarm distinct in both rhythm and spectrum, and the lever commit and the fail are the two sounds that stand out.

### S2 Timing and envelope
Attack against the feel beat (hit-stop, kick, flash at 0 ms), length against the moment, tails, loop seams.
- **4:** Sounds start late (lead silence), long tails run past the moment or into the next event, or a loop shows a seam.
- **7:** Attacks land on the feel beat and lengths suit their moments; one sound is too long, too slow to peak, or one tail lingers.
- **9:** Every impact peaks within 10 ms of its feel beat, lengths match the moment (UI under 0.1 s, alarms under the ticket life), tails are clean, loops seamless.

### S3 Clarity on a phone
Judge the dots on the ladder, the phone-loss numbers and the spectrogram bands (ticks mark 500 Hz and 4 kHz).
- **4:** A crisis or commit sound lives mostly below 150 Hz and drops more than 6 dB on a phone, or phone dots invert the hierarchy.
- **7:** Alarms and commits keep their energy in 0.5-4 kHz; one sound loses more than its limit or two concurrent sounds share the same band.
- **9:** Every tier-1 to tier-3 sound survives a phone speaker within 3 dB, the hierarchy holds on the dots, and concurrent sounds sit in different bands.

### S4 Mix safety and fatigue
Peaks, ducking, voice limits and repetition over a 12-minute trip.
- **4:** Peaks over -1 dBTP or clipping, ducking that pumps (long attack, instant release) or removes the ambience entirely, no voice caps, or frequent sounds without variations or cooldowns.
- **7:** Safe peaks and sensible ducking; one frequent sound (click, shovel, glass) lacks variations or a cooldown, or one duck is deeper than it needs.
- **9:** Every file within the peak ceiling, ducks of 3-14 dB with short attacks and smooth releases, caps and cooldowns on every repeatable sound, variations wherever a sound repeats within a minute.

### S5 Style match
See the shared House style block, applied to sound through the brief text and the placeholder plan: slapstick lands through sound, chunky and toy-like, never horror.
- **4:** The plan reads grim or realistic: screams of pain, horror stings, war explosions, modern diesel horns on a steam alpha.
- **7:** Comic and physical on most sounds; one brief is generic (a stock app notification, a cinematic boom).
- **9:** Every brief sounds like the same incompetent train company: clunky levers, droopy alarms, cartoon bangs, never cruel.

### S6 Coverage and polish
- **4:** Events with no sound, sounds no event plays, missing licence or placeholder labels, or 3D sounds without emitter roles.
- **7:** Full coverage with one gap (an info event silent, a missing variation, an unlabelled placeholder in Facts).
- **9:** Every event mapped, every sound briefed, licence states clean, placeholders labelled, emitters named, nothing left over.
