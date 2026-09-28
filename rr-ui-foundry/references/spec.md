# Screen spec format (specs/*.json)

Read before writing or editing a spec. `ui.py validate` enforces every rule here; `ui.py show SPEC` prints the
expanded tree. The two examples in `specs/` cover a HUD stack and a modal with states and gamepad nav.

## Top level
```json
{"screen": "LobbyCreateMatch", "title": "...", "purpose": "one job, in the owner's words",
 "design": {"device": "phone"}, "gui": {"display_order": 30, "insets": "CoreUISafeInsets", "modal": true},
 "canon": ["ui.lobby.controls"], "oq": ["OQ-017"], "icons": "../assets/icons",
 "data": {...}, "types": {...}, "nodes": [...], "nav": {...}, "machine": {...}, "boards": [...]}
```
- `design.device` must be the kit's design device (phone). Top-level rects are **phone-screen px** (844 x 390,
  as drawn in the mock); the ScreenGui area starts under the 58 px top bar (`tech.ui_platform.topbar_inset`).
- `gui.insets`: CoreUISafeInsets for anything interactive or important (default); DeviceSafeInsets or None only
  for backgrounds. Nodes with `"layer": "backdrop"` go to a second ScreenGui with ScreenInsets None (full screen,
  one DisplayOrder lower), e.g. a modal scrim.
- `canon` / `oq`: keys this screen relies on (checked to exist; cited in the brief and manifest).
- `purpose` feeds the critic brief; `title` the boards and UI_SPEC.md.

## Nodes (primitives)
| key | meaning |
|---|---|
| `id` | unique; parts of a template become `instance.part` (e.g. `join.label`); refs may use a unique suffix |
| `type` | `frame`, `text`, `image`, `hit` (TextButton), `stack` (HUD list) |
| `use` + `variant` + `slots` | instantiate a template from `kit/components.json` instead of `type` |
| `rect` | `[x, y, w, h]` design px; top level: phone screen, children: relative to the parent |
| `pin` | `tl tc tr cl cc cr bl bc br`; default from the rect (thirds). Top level: the edge the group hugs |
| `stretch` | top level only: `x`, `y` or `xy` spans between its margins (bars, scrims); no aspect lock |
| `layer` | `core` (default) or `backdrop` |
| `avoid` | top level: `["jump"]`, `["stick"]`: lift above the real touch control at run time |
| `fill`, `gradient` `[top, bottom]`, `stroke` `[role, px]`, `alpha`, `radius` (px or `"circle"`), `clip`, `rot` | style; colours are **roles** (or `@bible.key` for a one-off token), never hex |
| `text`, `style`, `color`, `align`, `valign`, `wrap`, `truncate` | text; `style` is a type style in `kit/roles.json` |
| `image`, `tint` | `icon.<name>` (icons folder, packed into the sheet) or `key.<KeyCode>` (gamepad glyph) |
| `action` | on a hit: `"join"` (Action event + machine event if one exists), `{"set": {"players": 1}}`, `{"cycle": {"difficulty": 1}}` |
| `on` | component `on` state while a data condition holds: `"players=1"` |
| `visible`, `if`, `unless` | default visibility; template conditions on slots (`"stamp"`, `"kind=risk"`) |
| `children`, `note` | children in the parent's design space; notes are dropped from exports |

`{slot}` / `{slot|lower}` / `{slot|upper}` in texts and roles bind to screen `data` (live via `screen:set`) or to
template slots. Children of a `use: panel` are placed relative to the panel and parented to its content part.

## Layout: pin + scale
- A top-level group gets `Size = Scale of the design area`, a `UIAspectRatioConstraint` (its design ratio,
  FitWithinMaxSize) and a `UIScale` = density; so it becomes design size x s x density, where
  s = min(areaW / 844, areaH / 332). Its AnchorPoint is its pin and its margin from that edge is design px x
  s x density (the kit updates the offsets on resize).
- Children use pure Scale of their parent (exact, because the parent scales uniformly); children of a stretch
  node keep their shape with their own aspect constraint.
- Text size, stroke, corner radius and tile size = design px x s (UIScale adds the density).
- Density: Small (phones, tablets) and Medium (PC) come from `tech.ui_platform.layout`; Large (TV) is OQ-033.

## data, types, stack
- `data`: `{"difficulty": {"values": {"canon": "gameplay.difficulty.tiers", "upper": true}, "default": "MEDIUM"}}`.
- `types` (HUD): `{"CoalLow": {"kind": "danger", "icon": "coal", "text": {"canon": "gameplay.alerts.coal_low"}}}`;
  the text splits on " / " into title, body, stamp.
- `stack` on a `type: "stack"` node: `template`, `compact` (older tickets), `dir: "up"` (newest at the bottom),
  `gap`, `max` (canon), `max_lifted` (while lifted above the jump button, OQ-034), `full: ["newest",
  "newest_crisis"]`, `crisis` / `sticky` conditions (sticky = never pushed off, no life bar, cleared by the
  server), `merge: "type"` (count badge), `life_s` per kind (canon ms x 0.001), `overflow` template (+N MORE),
  `feel` event names (enter, leave, merge, crisis). The same policy runs in uimodel.py and RR_UIKit.lua.

## nav (gamepad and console)
`{"grid": [["close"], ["p1", "p2", "p3"], ["diff_prev", "diff_next"], ["join"]], "default": "join",
"back": "close", "modal": "panel"}`: rows become NextSelectionLeft/Right; up/down go to the nearest item by x in
the next row. `edges` overrides single links. `modal` gets SelectionGroup + SelectionBehavior Stop; `back` is
activated by ButtonB while the modal is visible. Every hit must be reachable from `default`.

## machine
`states` map a state to its look: `hide`, `show`, `disable` (id lists) and `text` (`{"join.label": "JOINING..."}`).
`transitions`: `[from, event, to, feel_event_or_null]`; `from` may be `"*"`. Events not allowed in the current
state are ignored and warned. Feel names must exist in rr-game-feel's presets.

## boards
Each board is a picture the critic sees and the demo cycles: `{"name": "insane", "state": "open",
"data": {...}, "select": "join", "comp_states": {"diff_next": "pressed"}}`; HUD boards list `push`
(`[["CrewJoined", {"name": "Joel"}], ["CoalLow"]]`) and optional `life` fractions for the life bars.
Keep 2-4 boards: the first one is the main board (all devices and skins).
