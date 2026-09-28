# Feel kit tuning table

Generated from `/home/user/claude/trials/rr-game-feel/src/feel/feel.json` by tools/kit_tuning.py. Edit the numbers in feel.json, then re-run `feel.py validate --strict` and `feel.py build`; never edit RR_FeelPresets.lua by hand. `canon` rows must keep their value (rr-bible); `knob` rows are free within the range.

## lever pull

| event | tier / who | channel | knobs (edit in feel.json) | safe range | canon-locked |
|---|---|---|---|---|---|
| lever_detent_tick | t5 actor | punch lever_knob.scale | amp 0.08 · freq_hz 9 · damping 0.4 · dur 0.2 | amp: <= 0.3; freq_hz: 2-14 Hz; damping: 0.05-0.95 | - |
| lever_detent_tick | t5 actor | haptic | effect "Custom" · keys [[0, 0.5], [20, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| lever_commit | t3 actor | hitstop | ms 70 | ms: <= 150 ms, cooldown 0.25 s | - |
| lever_commit | t3 actor | camkick | angles_deg [0.4, 1.6, 1.0] · side_sign true · freq_hz 5 · damping 0.45 · dur 0.5 | angles_deg: spring impulse; measured peak <= 4 deg, roll <= 2; freq_hz: 2-14 Hz; damping: 0.05-0.95 | - |
| lever_commit | t3 actor | punch lever_panel.scale | amp 0.1 · freq_hz 6 · damping 0.35 · dur 0.5 | amp: <= 0.3; freq_hz: 2-14 Hz; damping: 0.05-0.95 | - |
| lever_commit | t3 actor | flash lamp | scope "element" · color "@style.brand.hazard_yellow" · peak 1.0 · in 0.02 · hold 0.25 · out 0.3 | peak: screen/vignette <= 0.35 (red 0.25); element exempt | - |
| lever_commit | t3 actor | haptic | effect "GameplayCollision" · keys [[0, 1.0], [50, 0.6], [140, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| lever_commit | t3 actor | cue | sfx "lever_clunk" |  | - |
| lever_commit_crew | t4 crew | camkick | angles_deg [0, 0.7, 0.4] · side_sign true · freq_hz 4 · damping 0.45 · dur 0.5 | angles_deg: spring impulse; measured peak <= 4 deg, roll <= 2; freq_hz: 2-14 Hz; damping: 0.05-0.95 | - |
| lever_commit_crew | t4 crew | haptic | effect "Custom" · keys [[0, 0.5], [60, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| lever_commit_crew | t4 crew | cue | sfx "points_throw" |  | - |
| lever_snapback | t5 actor | punch lever_panel.x_px | shape "sin" · amp 4 · freq_hz 12 · damping 0.25 · dur 0.25 | amp: px; noise shape delivers ~30% of amp; freq_hz: 2-14 Hz; damping: 0.05-0.95 | - |
| lever_snapback | t5 actor | haptic | effect "Custom" · keys [[0, 0.25], [30, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |

| event | camera px (RM) | kick deg | FOV deg | hit-stop ms | flash | haptic | secs | loudness | RM still reads via |
|---|---|---|---|---|---|---|---|---|---|
| lever_detent_tick | 0.0 (0.0) | 0.0 | 0.0 | 0 | 0.0 | 0.5 / 33 ms | 0.2 | 0.016 | haptic, punch |
| lever_commit | 5.9 (0.0) | 0.804 | 0.0 | 70 | 0.0 | 1.0 / 150 ms | 0.64 | 0.183 | haptic, flash, punch, cue |
| lever_commit_crew | 2.5 (0.0) | 0.358 | 0.0 | 0 | 0.0 | 0.5 / 67 ms | 0.5 | 0.022 | haptic, cue |
| lever_snapback | 0.0 (0.0) | 0.0 | 0.0 | 0 | 0.0 | 0.25 / 33 ms | 0.25 | 0.003 | haptic, punch |

## hard brake

| event | tier / who | channel | knobs (edit in feel.json) | safe range | canon-locked |
|---|---|---|---|---|---|
| hard_brake | t3 all | camkick | angles_deg [1.6, 0, 0] · freq_hz 1.8 · damping 0.55 · dur 1.2 | angles_deg: spring impulse; measured peak <= 4 deg, roll <= 2; freq_hz: 2-14 Hz; damping: 0.05-0.95 | - |
| hard_brake | t3 all | fovkick | delta_deg -4 · in 0.2 · hold 0.5 · out 1.4 · style_in "Quad" · style_out "Sine" | delta_deg: |delta| <= 12 deg | - |
| hard_brake | t3 all | flash | scope "vignette" · color "#000000" · peak 0.12 · in 0.15 · hold 0.3 · out 0.8 | peak: screen/vignette <= 0.35 (red 0.25); element exempt | - |
| hard_brake | t3 all | haptic | effect "Custom" · keys [[0, 0.6], [70, 0.25], [140, 0.55], [210, 0.2], [290, 0.45], [380, 0.2], [480, 0.4], [600, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| hard_brake | t3 all | cue | sfx "brake_hiss" |  | - |

| event | camera px (RM) | kick deg | FOV deg | hit-stop ms | flash | haptic | secs | loudness | RM still reads via |
|---|---|---|---|---|---|---|---|---|---|
| hard_brake | 3.4 (0.0) | 0.696 | 4.0 | 0 | 0.12 | 0.6 / 600 ms | 2.1 | 0.167 | haptic, flash, cue |

## crate landed

| event | tier / who | channel | knobs (edit in feel.json) | safe range | canon-locked |
|---|---|---|---|---|---|
| alert_crate_landed | t4 all | camkick | angles_deg [1.2, 0, 0.3] · freq_hz 6 · damping 0.45 · dur 0.4 | angles_deg: spring impulse; measured peak <= 4 deg, roll <= 2; freq_hz: 2-14 Hz; damping: 0.05-0.95 | - |
| alert_crate_landed | t4 all | shake | trauma 0.2 | trauma: 0-1; camera <= 10 px (tier 4); shake = trauma^2 | - |
| alert_crate_landed | t4 all | haptic | effect "GameplayCollision" · keys [[0, 0.6], [90, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| alert_crate_landed | t4 all | cue | sfx "crate_thump" |  | - |
| alert_crate_landed | t4 all | include | hud_ticket_enter at +0.1 s | | - |

| event | camera px (RM) | kick deg | FOV deg | hit-stop ms | flash | haptic | secs | loudness | RM still reads via |
|---|---|---|---|---|---|---|---|---|---|
| alert_crate_landed | 3.9 (0.0) | 0.614 | 0.0 | 0 | 0.0 | 0.6 / 100 ms | 0.4 | 0.049 | haptic, alpha, cue |

## crisis alarm

| event | tier / who | channel | knobs (edit in feel.json) | safe range | canon-locked |
|---|---|---|---|---|---|
| hud_crisis_arrival | t2 all | punch ticket.x_px | shape "sin" · amp 5 · freq_hz 5 · damping 0.05 · dur 0.5 · delay 0.3 | amp: px; noise shape delivers ~30% of amp; freq_hz: 2-14 Hz; damping: 0.05-0.95 | amp (ui.hud.crisis_extra), dur (ui.hud.crisis_extra) |
| hud_crisis_arrival | t2 all | pulse halo.alpha | min 0.3 · max 0.95 · period 1.2 |  | min (ui.hud.crisis_extra), max (ui.hud.crisis_extra) |
| alert_coal_low | t2 all | punch gauge.scale | amp 0.12 · freq_hz 5 · damping 0.3 · dur 0.7 · delay 0.1 | amp: <= 0.3; freq_hz: 2-14 Hz; damping: 0.05-0.95 | - |
| alert_coal_low | t2 all | haptic | effect "UINotification" · keys [[0, 0.5], [60, 0], [140, 0.5], [200, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| alert_coal_low | t2 all | cue | sfx "alarm_coal" |  | - |
| alert_coal_low | t2 all | include | hud_ticket_enter at +0 s | | - |
| alert_coal_low | t2 all | include | hud_crisis_arrival at +0 s | | - |
| alert_pressure_high | t2 all | shake | trauma 0.3 | trauma: 0-1; camera <= 28 px (tier 2); shake = trauma^2 | - |
| alert_pressure_high | t2 all | flash | scope "vignette" · color "@style.brand.danger_red" · peak 0.22 · in 0.05 · hold 0.1 · out 0.5 | peak: screen/vignette <= 0.35 (red 0.25); element exempt | - |
| alert_pressure_high | t2 all | haptic | effect "Custom" · keys [[0, 0.7], [80, 0], [220, 0.5], [300, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| alert_pressure_high | t2 all | cue | sfx "alarm_pressure" · vfx "steam_valve" |  | - |
| alert_pressure_high | t2 all | include | hud_ticket_enter at +0 s | | - |
| alert_pressure_high | t2 all | include | hud_crisis_arrival at +0 s | | - |
| alert_breakdown | t2 all | shake | trauma 0.45 | trauma: 0-1; camera <= 28 px (tier 2); shake = trauma^2 | - |
| alert_breakdown | t2 all | camkick | angles_deg [1.2, 0, 0.8] · freq_hz 5 · damping 0.4 · dur 0.6 | angles_deg: spring impulse; measured peak <= 4 deg, roll <= 2; freq_hz: 2-14 Hz; damping: 0.05-0.95 | - |
| alert_breakdown | t2 all | flash | scope "screen" · color "#FFFFFF" · peak 0.2 · in 0.03 · hold 0.0 · out 0.25 | peak: screen/vignette <= 0.35 (red 0.25); element exempt | - |
| alert_breakdown | t2 all | haptic | effect "GameplayCollision" · keys [[0, 0.9], [120, 0.3], [300, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| alert_breakdown | t2 all | cue | sfx "breakdown_bang" · vfx "sparks_powerbox" |  | - |
| alert_breakdown | t2 all | include | hud_ticket_enter at +0.1 s | | - |
| alert_breakdown | t2 all | include | hud_crisis_arrival at +0.1 s | | - |
| alert_passengers_upset | t2 all | haptic | effect "UINotification" · keys [[0, 0.45], [50, 0], [120, 0.45], [170, 0], [240, 0.45], [290, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| alert_passengers_upset | t2 all | cue | sfx "passengers_scream" |  | - |
| alert_passengers_upset | t2 all | include | hud_ticket_enter at +0 s | | - |
| alert_passengers_upset | t2 all | include | hud_crisis_arrival at +0 s | | - |

| event | camera px (RM) | kick deg | FOV deg | hit-stop ms | flash | haptic | secs | loudness | RM still reads via |
|---|---|---|---|---|---|---|---|---|---|
| hud_crisis_arrival | 0.0 (0.0) | 0.0 | 0.0 | 0 | 0.0 | 0.0 / 0 ms | 0.8 + loop | 0.0 | alpha, punch |
| alert_coal_low | 0.0 (0.0) | 0.0 | 0.0 | 0 | 0.0 | 0.5 / 200 ms | 0.8 + loop | 0.052 | haptic, alpha, punch, cue |
| alert_pressure_high | 1.0 (0.0) | 0.0 | 0.0 | 0 | 0.22 | 0.7 / 300 ms | 0.8 + loop | 0.187 | haptic, flash, alpha, punch, cue |
| alert_breakdown | 7.1 (0.0) | 0.647 | 0.0 | 0 | 0.2 | 0.9 / 300 ms | 0.9 + loop | 0.247 | haptic, flash, alpha, punch, cue |
| alert_passengers_upset | 0.0 (0.0) | 0.0 | 0.0 | 0 | 0.0 | 0.45 / 283 ms | 0.8 + loop | 0.042 | haptic, alpha, punch, cue |

## fare banked

| event | tier / who | channel | knobs (edit in feel.json) | safe range | canon-locked |
|---|---|---|---|---|---|
| alert_fare_banked | t4 all | tween stamp.scale | from 1.8 · to 1 · dur 0.2 · style "Quad" · dir "In" · delay 0.2 |  | - |
| alert_fare_banked | t4 all | tween cash.count | from 0 · to 1 · dur 0.6 · style "Quad" · dir "Out" · delay 0.2 |  | - |
| alert_fare_banked | t4 all | punch ticket.scale | amp 0.06 · freq_hz 6 · damping 0.35 · dur 0.4 · delay 0.4 | amp: <= 0.3; freq_hz: 2-14 Hz; damping: 0.05-0.95 | - |
| alert_fare_banked | t4 all | haptic | effect "Custom" · keys [[400, 0.4], [440, 0], [490, 0.6], [540, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| alert_fare_banked | t4 all | cue | sfx "cash_register" |  | - |
| alert_fare_banked | t4 all | include | hud_ticket_enter at +0 s | | - |

| event | camera px (RM) | kick deg | FOV deg | hit-stop ms | flash | haptic | secs | loudness | RM still reads via |
|---|---|---|---|---|---|---|---|---|---|
| alert_fare_banked | 0.0 (0.0) | 0.0 | 0.0 | 0 | 0.0 | 0.52 / 150 ms | 0.8 | 0.035 | haptic, alpha, tween, punch, cue |

## lever drag (global `lever` section)

| knob | value | meaning |
|---|---|---|
| detent | 0.7 | finger travel where the tick and commit fire |
| resist | 1.6 | knob = detent x (finger/detent)^resist: higher feels heavier |
| snap | Back Out 0.18 s | knob home after commit |
| snapback | Back Out 0.25 s | knob home when released early |
| throw_deg | 35 | in-world lever handle throw |

