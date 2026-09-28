# Feel tuning table

Generated 2026-09-28 from `src/feel/feel.json` by `feel.py tune`. Change numbers with `feel.py set 'events.E.channels[i].KNOB=VALUE'` (or edit feel.json), then `validate --strict` and `build`; never edit RR_FeelPresets.lua. `canon` knobs keep their rr-bible value; the rest are free within the range. Punch amps and kick angles are the delivered peaks.

| event | tier / who | ch | channel | knobs | safe range | canon-locked |
|---|---|---|---|---|---|---|
| lever_commit | t3 actor | 0 | hitstop | ms 70 | ms: <= 150 ms, cooldown 0.25 s; not on crew events | - |
| lever_commit | t3 actor | 1 | camkick | angles_deg [0.2, -0.82, -0.51] · side_sign true · freq_hz 5 · damping 0.45 · dur 0.5 | angles_deg: delivered peak deg: kick <= 4, roll <= 2, >= 1.5 px on the phone; + pitch = view up; freq_hz: 0.5-8 Hz; damping: 0.05-0.95 | - |
| lever_commit | t3 actor | 2 | punch lever_panel.scale | amp 0.059 · freq_hz 6 · damping 0.35 · dur 0.5 | amp: delivered peak, <= 0.3; freq_hz: 2-14 Hz; damping: 0.05-0.95 (spring ends under 5% of its peak) | - |
| lever_commit | t3 actor | 3 | flash lamp | scope "element" · color "@style.brand.hazard_yellow" · peak 1.0 · in 0.02 · hold 0.25 · out 0.3 | peak: screen/vignette <= 0.35 (red 0.25); element exempt | - |
| lever_commit | t3 actor | 4 | haptic | effect "GameplayCollision" · keys [[0, 1.0], [50, 0.6], [140, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| lever_commit | t3 actor | 5 | cue | sfx "lever_clunk" |  | - |
| lever_detent_tick | t5 actor | 0 | punch lever_knob.scale | amp 0.044 · freq_hz 9 · damping 0.4 · dur 0.2 | amp: delivered peak, <= 0.3; freq_hz: 2-14 Hz; damping: 0.05-0.95 (spring ends under 5% of its peak) | - |
| lever_detent_tick | t5 actor | 1 | haptic | effect "Custom" · keys [[0, 0.5], [20, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| lever_snapback | t5 actor | 0 | punch lever_panel.x_px | shape "sin" · amp 3 · freq_hz 12 · damping 0.3 · dur 0.25 | amp: delivered px, >= 1.5; freq_hz: 2-14 Hz; damping: 0.05-0.95 (spring ends under 5% of its peak) | - |
| lever_snapback | t5 actor | 1 | haptic | effect "Custom" · keys [[0, 0.25], [30, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| lever_commit_crew | t4 crew | 0 | camkick | angles_deg [0, -0.36, -0.2] · side_sign true · freq_hz 4 · damping 0.45 · dur 0.5 | angles_deg: delivered peak deg: kick <= 4, roll <= 2, >= 1.5 px on the phone; + pitch = view up; freq_hz: 0.5-8 Hz; damping: 0.05-0.95 | - |
| lever_commit_crew | t4 crew | 1 | haptic | effect "Custom" · keys [[0, 0.5], [60, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| lever_commit_crew | t4 crew | 2 | cue | sfx "points_throw" |  | - |
| hard_brake | t3 all | 0 | camkick | angles_deg [-0.7, 0, 0] · freq_hz 1.8 · damping 0.55 · dur 1.2 | angles_deg: delivered peak deg: kick <= 4, roll <= 2, >= 1.5 px on the phone; + pitch = view up; freq_hz: 0.5-8 Hz; damping: 0.05-0.95 | - |
| hard_brake | t3 all | 1 | fovkick | delta_deg -4 · in 0.2 · hold 0.5 · out 1.4 · style_in "Quad" · style_out "Sine" | delta_deg: |delta| <= 12 deg (- zooms in) | - |
| hard_brake | t3 all | 2 | flash | scope "vignette" · color "#000000" · peak 0.12 · in 0.15 · hold 0.3 · out 0.8 | peak: screen/vignette <= 0.35 (red 0.25); element exempt | - |
| hard_brake | t3 all | 3 | haptic | effect "Custom" · keys [[0, 0.6], [70, 0.25], [140, 0.55], [210, 0.2], [290, 0.45], [380, 0.2], [480, 0.4], [600, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| hard_brake | t3 all | 4 | cue | sfx "brake_hiss" |  | - |
| alert_crate_landed | t4 all | 0 | camkick | angles_deg [-0.7, 0, 0.2] · freq_hz 6 · damping 0.45 · dur 0.4 | angles_deg: delivered peak deg: kick <= 4, roll <= 2, >= 1.5 px on the phone; + pitch = view up; freq_hz: 0.5-8 Hz; damping: 0.05-0.95 | - |
| alert_crate_landed | t4 all | 1 | haptic | effect "GameplayCollision" · keys [[0, 0.6], [90, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| alert_crate_landed | t4 all | 2 | cue | sfx "crate_thump" |  | - |
| alert_crate_landed | t4 all | - | include | hud_ticket_enter at +0.1 s | | - |
| hud_crisis_arrival | t2 all | 0 | punch ticket.x_px | shape "sin" · amp -5 · freq_hz 4 · damping 0.05 · dur 0.5 · delay 0.3 | amp: delivered px, >= 1.5; freq_hz: 2-14 Hz; damping: 0.05-0.95 (spring ends under 5% of its peak) | amp (ui.hud.crisis_extra), dur (ui.hud.crisis_extra) |
| hud_crisis_arrival | t2 all | 1 | pulse halo.alpha | min 0.3 · max 0.95 · period 1.2 | period: >= 0.5 s | min (ui.hud.crisis_extra), max (ui.hud.crisis_extra) |
| alert_coal_low | t2 all | 0 | punch gauge.scale | amp 0.077 · freq_hz 5 · damping 0.3 · dur 0.7 · delay 0.1 | amp: delivered peak, <= 0.3; freq_hz: 2-14 Hz; damping: 0.05-0.95 (spring ends under 5% of its peak) | - |
| alert_coal_low | t2 all | 1 | haptic | effect "UINotification" · keys [[0, 0.5], [60, 0], [140, 0.5], [200, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| alert_coal_low | t2 all | 2 | cue | sfx "alarm_coal" |  | - |
| alert_coal_low | t2 all | - | include | hud_ticket_enter at +0 s | | - |
| alert_coal_low | t2 all | - | include | hud_crisis_arrival at +0 s | | - |
| alert_pressure_high | t2 all | 0 | shake | trauma 0.3 | trauma: 0-1; camera <= 28 px (tier 2); visible from about 0.3 | - |
| alert_pressure_high | t2 all | 1 | flash | scope "vignette" · color "@style.brand.danger_red" · peak 0.22 · in 0.05 · hold 0.1 · out 0.5 | peak: screen/vignette <= 0.35 (red 0.25); element exempt | - |
| alert_pressure_high | t2 all | 2 | haptic | effect "Custom" · keys [[0, 0.7], [80, 0], [220, 0.5], [300, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| alert_pressure_high | t2 all | 3 | cue | sfx "alarm_pressure" · vfx "steam_valve" |  | - |
| alert_pressure_high | t2 all | - | include | hud_ticket_enter at +0 s | | - |
| alert_pressure_high | t2 all | - | include | hud_crisis_arrival at +0 s | | - |
| alert_breakdown | t2 all | 0 | shake | trauma 0.45 | trauma: 0-1; camera <= 28 px (tier 2); visible from about 0.3 | - |
| alert_breakdown | t2 all | 1 | camkick | angles_deg [0.66, 0.0, 0.44] · freq_hz 5 · damping 0.4 · dur 0.6 | angles_deg: delivered peak deg: kick <= 4, roll <= 2, >= 1.5 px on the phone; + pitch = view up; freq_hz: 0.5-8 Hz; damping: 0.05-0.95 | - |
| alert_breakdown | t2 all | 2 | flash | scope "screen" · color "#FFFFFF" · peak 0.2 · in 0.03 · hold 0.0 · out 0.25 | peak: screen/vignette <= 0.35 (red 0.25); element exempt | - |
| alert_breakdown | t2 all | 3 | haptic | effect "GameplayCollision" · keys [[0, 0.9], [120, 0.3], [300, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| alert_breakdown | t2 all | 4 | cue | sfx "breakdown_bang" · vfx "sparks_powerbox" |  | - |
| alert_breakdown | t2 all | - | include | hud_ticket_enter at +0.1 s | | - |
| alert_breakdown | t2 all | - | include | hud_crisis_arrival at +0.1 s | | - |
| alert_passengers_upset | t2 all | 0 | haptic | effect "UINotification" · keys [[0, 0.45], [50, 0], [120, 0.45], [170, 0], [240, 0.45], [290, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| alert_passengers_upset | t2 all | 1 | cue | sfx "passengers_scream" |  | - |
| alert_passengers_upset | t2 all | - | include | hud_ticket_enter at +0 s | | - |
| alert_passengers_upset | t2 all | - | include | hud_crisis_arrival at +0 s | | - |
| alert_fare_banked | t4 all | 0 | tween stamp.scale | from 1.8 · to 1 · dur 0.2 · style "Quad" · dir "In" · delay 0.2 | dur: > 0 s; style: Enum.EasingStyle | - |
| alert_fare_banked | t4 all | 1 | tween cash.count | from 0 · to 1 · dur 0.6 · style "Quad" · dir "Out" · delay 0.2 | dur: > 0 s; style: Enum.EasingStyle | - |
| alert_fare_banked | t4 all | 2 | punch ticket.scale | amp 0.036 · freq_hz 6 · damping 0.35 · dur 0.4 · delay 0.4 | amp: delivered peak, <= 0.3; freq_hz: 2-14 Hz; damping: 0.05-0.95 (spring ends under 5% of its peak) | - |
| alert_fare_banked | t4 all | 3 | haptic | effect "Custom" · keys [[400, 0.4], [440, 0], [490, 0.6], [540, 0]] | keys: [ms, 0..1], end at 0, <= 1500 ms | - |
| alert_fare_banked | t4 all | 4 | cue | sfx "cash_register" |  | - |
| alert_fare_banked | t4 all | - | include | hud_ticket_enter at +0 s | | - |

| event | camera px (RM) | kick deg | FOV deg | hit-stop ms | flash | haptic | secs | loudness | outshouts (higher tier) | RM still reads via |
|---|---|---|---|---|---|---|---|---|---|---|
| lever_commit | 5.9 (0.0) | 0.805 | +0 | 70 | 0.0 | 1.0 / 150 ms | 0.64 | 0.159 | windows_smash, hud_crisis_arrival | flash, sound, haptic |
| lever_detent_tick | 0.0 (0.0) | 0.0 | +0 | 0 | 0.0 | 0.5 / 33 ms | 0.2 | 0.014 | route_locked | haptic; the knob keeps tracking the finger toward the detent |
| lever_snapback | 0.0 (0.0) | 0.0 | +0 | 0 | 0.0 | 0.25 / 33 ms | 0.25 | 0.041 | route_locked, alert_junction_ahead, fork_countdown_tick, lever_commit_crew, station_arrive, alert_crate_landed | haptic; the knob returns home (lever.snapback on the knob is state, not reduced) |
| lever_commit_crew | 2.5 (0.0) | 0.36 | +0 | 0 | 0.0 | 0.5 / 67 ms | 0.5 | 0.019 | alert_junction_ahead, fork_countdown_tick | sound, haptic |
| hard_brake | 3.4 (0.0) | 0.699 | -4 | 0 | 0.12 | 0.6 / 600 ms | 2.1 | 0.145 | windows_smash, hud_crisis_arrival | flash, sound, haptic |
| alert_crate_landed | 4.1 (0.0) | 0.7 | +0 | 0 | 0.0 | 0.6 / 100 ms | 0.4 | 0.036 | alert_junction_ahead, fork_countdown_tick | alpha, sound, haptic |
| hud_crisis_arrival | 0.0 (0.0) | 0.0 | +0 | 0 | 0.0 | 0.0 / 0 ms | 0.8 + loop | 0.129 | - | alpha |
| alert_coal_low | 0.0 (0.0) | 0.0 | +0 | 0 | 0.0 | 0.5 / 200 ms | 0.8 + loop | 0.174 | - | alpha, sound, haptic |
| alert_pressure_high | 1.0 (0.0) | 0.0 | +0 | 0 | 0.22 | 0.7 / 300 ms | 0.8 + loop | 0.291 | - | alpha, flash, vfx, sound, haptic |
| alert_breakdown | 7.1 (0.0) | 0.644 | +0 | 0 | 0.2 | 0.9 / 300 ms | 0.9 + loop | 0.343 | - | alpha, flash, vfx, sound, haptic |
| alert_passengers_upset | 0.0 (0.0) | 0.0 | +0 | 0 | 0.0 | 0.45 / 283 ms | 0.8 + loop | 0.166 | - | alpha, sound, haptic |
| alert_fare_banked | 0.0 (0.0) | 0.0 | +0 | 0 | 0.0 | 0.52 / 150 ms | 0.8 | 0.135 | alert_junction_ahead, fork_countdown_tick, alert_risky_route, windows_smash, hud_crisis_arrival | alpha, tween, sound, haptic |

## Lever drag (`lever` section)

| knob | value | meaning |
|---|---|---|
| notch | 0.6 | finger travel where the detent tick fires (felt before the commit) |
| detent | 0.7 | finger travel where the commit fires (once per junction) |
| resist | 1.6 | knob = detent x (finger/detent)^resist: higher feels heavier |
| snap | Back Out 0.18 s | knob home after the commit |
| snapback | Back Out 0.25 s | knob home when released early |
| throw_deg | 35 | in-world handle throw |

