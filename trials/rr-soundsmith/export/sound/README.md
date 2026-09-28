# Risky Rails sound package (rr-soundsmith, 2026-09-28)

Files
- `RR_SoundMap.lua` ModuleScript, GENERATED data (sounds, groups, ducking, events, voices). Regenerate, never edit.
- `RR_Sound.lua` ModuleScript, the client runtime. `RR_SoundDemo.client.lua` LocalScript listening test.
- `studio_sound_setup.lua` run once in the command bar: SoundService.RR_Mix SoundGroup tree. A group Volume you set
  there is kept as its base; player settings and ducking multiply on top.
- `SOUND_SPEC.md` event -> sound table by phase, ladder, ducking, voices, open decisions. `AUDIO_BRIEFS.md` sourcing
  briefs (summary table first). `LICENCES.md` register.

Wire it (client only)
1. ReplicatedStorage: RR_SoundMap, RR_Sound (and RR_Feel from rr-game-feel if you use it).
2. In one LocalScript: `local Sound = require(RS.RR_Sound); Sound.init(require(RS.RR_SoundMap), {feel = Feel})`.
3. Emitters: `Sound.setEmitter("lever", leverAttachment)` for each role in SOUND_SPEC (missing roles play 2D).
4. Game code: `Sound.event("trip_start")`, `Sound.event("ui_button_press")`, and `Sound.setSpeed(speed)` whenever Speed
   changes: each Heartbeat or on the train's replicated Speed value Changed, including the ~5 s departure ramp and the
   arrival braking (the wheels then fade to silence at the StopMarker). Calling it only on throttle notches makes the
   wheel loop jump between notches and never fade.
5. Lobby place: `Sound.event("lobby_enter")` on join, queue events from the queue pad script, `lobby_leave` before
   the teleport.
   Events marked `via feel` play when RR_Feel plays that event; do not call them twice.

Runtime choice: legacy Sound + SoundGroup (still supported; Roblox now recommends the Audio API, see
tech.audio.soundgroup_status). Chosen for SoundGroup nesting and scripted ducking that is tested in a Lua VM; a port to
AudioPlayer/AudioEmitter/AudioFader keeps RR_SoundMap unchanged.

State: 0 placeholder and 29 unassigned sounds. Placeholders never ship (`sound.py validate --release`).
Studio listening test pending (owner): see rr-soundsmith references/fidelity.md.
