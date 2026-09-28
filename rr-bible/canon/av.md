# Audio, VFX and feel

Thin canon: most audio and effects are still undesigned (OQ-021). What exists is below; do not invent more as canon.

## audio · Sound
- `av.audio.priority` = `crisis alarms first: in a group they tell someone in the other carriage what is wrong` | src: R2A | canon
- `av.audio.slapstick` = `slapstick lands through sound` | src: R2A | canon
- `av.audio.pack` = `whistle, hiss, wheels, alarms` | MVP SFX pack | src: PLAN | proposed
- `av.audio.speed_link` = `wheel sound follows Speed` | src: PLAN | canon
- `av.audio.junction_beep` = `beep with the junction warning lamp from 1 mile out` | src: CB | proposed
- `av.audio.horn` = `Horn cab button plays a sound; Radio button plays a loop` | src: WR | proposed
- `av.audio.depart` = `whistle before departure` | src: R2A | canon
- `av.audio.client_pool` = `one-shot sounds from a small client-side pool` | see tech.streaming.sfx_pool | src: R2A | canon
- `av.audio.priority_in_plan` = `sound + crisis effects are a COULD for the alpha (week 2, if time)` | src: R2A | canon
- `av.audio.licence` = `only owner-uploaded audio (self-made, commissioned, CC0 or bought with a game licence, proof recorded) or Roblox-licensed Creator Store audio (by Roblox or its partners)` | no NC, ND or SA licences, rips, unknown terms; community uploads per OQ default | src: SND | proposed
- `av.audio.file_standard` = `one-shots: momentary max -14 LUFS (UI clicks and chimes -20); loops: integrated -20 LUFS; music: integrated -18 LUFS; all at most -1 dBTP, no clipping` | mono measured as dual mono; files shorter than 400 ms are zero-padded; the mix hierarchy lives in data (rr-soundsmith ladder), so files never need re-uploading to rebalance | src: SND | proposed
- `av.audio.placeholder` = `synthesised placeholders are named PLACEHOLDER_ and never ship: a release needs every alpha sound final and licensed` | src: SND | proposed

## vfx · Effects
- `av.vfx.steam_valve` = `steam from the pressure valve` | src: R2A | proposed
- `av.vfx.sparks_powerbox` = `sparks from the power box` | src: R2A | proposed
- `av.vfx.glass` = `glass from the windows` | src: R2A | proposed
- `av.vfx.pressure_shake` = `camera shake as pressure rises` | src: R2A | proposed
- `av.vfx.speed_link` = `steam particle rate and camera shake follow Speed` | src: PLAN | canon
- `av.vfx.boiler_fail` = `boiler bursts, then a YOU'RE FIRED stamp on the Incident Report` | short slapstick fail | src: R2A | proposed
- `av.vfx.firebox_glow` = `three orange Neon strips behind the firebox door (#FF9A3C, #FF7A22, #FF5A14); flicker by script later` | src: CB | proposed
- `av.vfx.tunnel` = `tunnels darken client lighting while a tunnel segment is under the train` | src: R2A | canon
- `av.vfx.bridge_haze` = `bridges get fog/haze so players cannot see track still spawning` | src: R2A | canon
- `av.vfx.overbridge_flash` = `overbridge briefly darkens the cab` | free drama | src: DS | proposed
- `av.vfx.client_side` = `all effects client-side, attached to the stationary train` | src: R2A | canon

## feel · Game feel
- `av.feel.parallax` = `the player's sense of speed comes from parallax: close objects at fixed spacing are the speedometer` | src: RN | canon
- `av.feel.poles` = `telegraph poles every 128 studs, regular on purpose` | src: RN, DS | canon
- `av.feel.station_exhale` = `station approach always feels like the game exhaling (TSR board, slowing)` | src: DS | proposed
- `av.feel.tool_in_hand` = `tool in hand within 5 s of spawning; first prompt within 3 m` | src: LPB | proposed
- `av.feel.fork_loudest` = `the fork carries the loudest countdown in the game` | src: LPB | proposed
- `av.feel.clip_moments` = `every fail state has a 3-second camera moment designed to be clipped` | src: PLAN | proposed
- `av.feel.hitstop_local` = `local and cosmetic, at most 150 ms` | hit-stop freezes only the playing client's own effects, character animation and registered emitters; the server-driven world scroll never pauses; actor events play it only for the acting player | src: FEEL | proposed
- `av.feel.flash_limit` = `3 per second` | full-screen and vignette flashes: at most 3 in any 1 s, peak opacity 0.35 (red 0.25), off with the flashes setting; element lamps are exempt | src: WCAG, FEEL | proposed
- `av.feel.reduce_motion` = `motion off, meaning kept` | with Reduce Motion on, camera shake, kicks and FOV kicks stop, punches shrink, slides become fades; every event must still read through colour, haptics or sound | src: RBXA, FEEL | proposed
