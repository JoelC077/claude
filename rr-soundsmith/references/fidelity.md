# What the cloud cannot know (and the owner's listening test)

Nothing here has played in Roblox and nobody in the cloud listens. Measurements are exact for the files; the
mapping from files to what a player hears is modelled. Say "measured" for file numbers, "modelled" for phone loss and
the in-game level, and "Studio test pending (owner)" at handover.

## Modelled or assumed
| item | assumption | how the owner checks |
|---|---|---|
| Sound.Volume curve | Volume scales amplitude linearly; 0.5 plays the file at its measured level (`meta.ref_volume`) | play a -14 LUFS test file at Volume 0.5 and 1.0; PlaybackLoudness should rise about 2x (6 dB) |
| SoundGroup nesting | group Volumes multiply (tech.audio.volume) | set SFX to 0.5: Actions sounds drop about 6 dB |
| Roll-off | presets `near`, `coach`, `train` feel right on a 165-stud train | walk the train with the lever and firebox emitters; alarms must still be heard in the far coach (2D) |
| Stereo on 3D sounds | mono is safest for positional sounds | compare a stereo and a mono file on an Attachment |
| Phone speakers | the high-pass 450 Hz / low-pass 10 kHz model | listen on a real phone at half volume: every tier 1-3 sound audible over the wheels |
| Voice caps | 16 one-shots is safe on phones | F9 memory and frame time during the bug-bash soak |
| Load latency | PreloadAsync at init removes first-play lag | first lever pull after joining must not be late |
| Doppler | world parts are moved by CFrame, so engine Doppler is effectively off; DistanceFactor is set from 1/stud_m | none needed unless pass-by sounds are added |
| Ducking | scripted dB ramps on Heartbeat match the plan exactly | during COAL LOW the wheels dip, then return within a second |

## Listening test (about 15 minutes, owner)
1. Run `studio_sound_setup.lua` once; put RR_Sound, RR_SoundMap (and RR_Feel) in ReplicatedStorage; add
   RR_SoundDemo.client.lua to StarterPlayerScripts; add Attachments named `RR_Emitter_<role>` where they belong.
2. Play Solo, press T (trip), then 1-0: can you name each crisis from the far coach with your eyes shut?
3. Z/X/C: the wheels follow Speed; 0 at a stop.
4. On a phone (Team Test or a private server): repeat step 2 at half volume.
5. Report in one line per sound: keep, louder, quieter, replace. Those become `trim_db` edits or new briefs.
