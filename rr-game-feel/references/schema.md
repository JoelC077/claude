# Preset format (presets/feel.json)

Read before editing presets. `feel.py validate --strict` enforces every rule here.

## Values
- A plain number is a knob: tune it freely within `limits`.
- `{"v": 0.5, "canon": "ui.hud.crisis_extra"}` is a canon number: validate fails unless the number (x `scale`,
  e.g. 0.32 s x 1000 = 320 ms) appears in that rr-bible fact. Strings must equal the fact (`"844 x 390"`).
- `"@style.brand.hazard_yellow"` is a colour token resolved through rr-bible; `#FFFFFF`/`#000000` are neutral.
  Red (hue within ~15 deg of 0, saturated) is refused on events above tier 2 (style.dont.red_decoration).
- Missing canon: `bible.py add-question` (options + default), cite the OQ in the event's `oq` list.

## Event
```json
"lever_commit": {"group": "lever", "priority": 3, "who": "actor", "trigger": "...", "intent": "...",
  "canon": ["ui.lever.commit"], "oq": ["OQ-031"], "alert": "gameplay.alerts.x",
  "include": [{"event": "hud_ticket_enter", "delay": 0.1}], "channels": [ ... ]}
```
- `priority` tier: 1 fail, 2 crisis, 3 commit, 4 reward, 5 UI. Loudness must not exceed the loudest of a higher tier.
- `who`: `local` (the pressing player), `actor` (only the acting player's client: hit-stop lives here), `crew`
  (everyone but the actor; no hit-stop), `all`.
- `group` decides the preview folder and critic group; keep a group at 7 events or fewer (two images per critic).
- `include` pulls another event's channels in, shifted by `delay` (depth <= 4). The HUD enter lives once.

## Channels (all take `delay` s; motion types also `rm`)
| type | fields | runtime |
|---|---|---|
| tween | target, prop (scale, x, y, x_px, y_px, rot, alpha, count), from, to, dur, style, dir, before (from, rest, hidden) | engine easing (TweenService:GetValue) stepped on the feel clock |
| punch | target, prop (scale, rot, x_px, y_px), amp, freq_hz, damping, dur, shape (sin, cos, noise) | damped spring or decaying noise, additive |
| pulse | target, prop (alpha, scale), min, max, period, dur (omit = loop until handle:Stop()) | sine loop starting at min |
| shake | trauma (0..1) | adds camera trauma |
| camkick | angles_deg [pitch, yaw, roll], freq_hz, damping, dur, side_sign | spring on the camera; yaw and roll follow ctx.side |
| fovkick | delta_deg, in, hold, out, style_in, style_out | FOV offset envelope (named so no line reads as a FOV value) |
| hitstop | ms | freezes this client's feel clock, character animation, registered emitters |
| flash | scope (screen, vignette, element), color, peak, in, hold, out, target (element) | overlay; element = child frame |
| haptic | effect (HapticEffectType name or Custom), keys [[ms, 0..1], ...] ending at 0 | HapticEffect; gamepad SetMotor fallback |
| cue | sfx, vfx | fires Feel.Cue(event, cue) for sound and VFX modules (vfx names checked against rr-vfx-lighting) |

Property meanings: `x`/`y` are Position scale offsets from the layout position (fractions of the parent, equal to
the element's own size for a full-size mover such as the HUD's); `x_px`/`y_px` pixel offsets; `rot` and `scale`
tweens are absolute (Rotation, UIScale.Scale), punches add to them; `alpha` 1 = as designed, 0 = gone (CanvasGroup
GroupTransparency, else every transparency in the subtree); `count` 0..1 of `ctx.count.amount`, text via
`ctx.count.format`. Delayed tweens hold `from` before they start (`before: rest` holds the rest value, `hidden`
hides the element until it starts). Motion channels run on the feel clock (they hold during hit-stop); flash,
haptic, hit-stop and cue run on real time.

## Reduce motion (`a11y.reduce_motion`, channel `rm` overrides)
Numbers scale the channel (0 removes it); `fade` keeps the resting end and fades instead of sliding; `snap` jumps
to `to`; `skip` drops it; `keep` = 1. Tween keys are `tween_<prop>`. Element flashes are never reduced (a lamp is
state). Every event must still read with reduce motion on (haptic, flash, alpha, punch, scale tween or a cue).

## Global sections
- `shake`: power, decay_per_s, max_trauma, freq_hz, max_angle_deg [p, y, r], max_offset_studs [x, y, z], sustain_cap.
- `sustain`: speed (floor = gain x Speed / ref) and pressure (floor above threshold); sum capped; keep it tiny.
- `lever`: detent, resist, snap and snapback eases, throw_deg, the three lever events.
- `a11y`: reduce_motion table, flash limits (per_second_max, screen_peak_max, red_peak_max), default settings.
- `profiles`: subtle/default/loud multipliers per channel type; flashes and hit-stop never above 1.
- `limits`: tier camera px, sustain px, hit-stop, kick, roll, FOV, punch, haptic, durations, loudness weights.
- `preview`: mock plate colours (tokens), scroll speed, pole spacing, ticket size, the hero event per group.
