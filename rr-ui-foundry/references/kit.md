# Component kit, roles, skins and the runtime

## Roles and skins (kit/roles.json)
- A role is a meaning (`accent`, `panel`, `header`, `on_header`, `kind.danger.top`, `diff.hard`, `focus`, ...).
  Each role names one rr-bible colour key per skin. Specs and templates use roles only, so:
  - `bible.py add-fact style.world.brass "#..." --replace` + `ui.py build` reskins every screen that uses a role
    mapped to it (the selftest proves it on a temp canon copy);
  - `Kit.setSkin("A")` rebinds every bound property of every mounted screen at run time.
- Skins A, B, C are the options of OQ-001 (heritage brass, teal-cream/mustard livery, hybrid). While it is open
  `default_skin` is the main skin, labelled "assumed (OQ-001 default)"; once decided, the decision's option is the
  main skin ("decided: A (D-nnn)") everywhere (boards, theme, manifest). `ui.py render SPEC --skins A,C` is the
  side-by-side board.
- Rules the roles keep (validate checks the spec side): one accent hue for "this is active"
  (`ui.rules.one_accent`: selected and current get an accent ring, the cta is the only solid accent); difficulty
  colours only as difficulty (`diff.*` marks); danger red only for the danger signal; kinds carry an icon too
  (`ui.rules.colourblind`). `ui.py render --kit` boards every template state in every skin, so a role that fails
  contrast in one state (a pressed face) shows up before a screen uses it.
- Type styles (`type`) name a font role, weight and design px size; canon sizes are `{"v", "canon"}`.
- Adding a role: add it to `roles` with a key for every skin; `ui.py validate` fails if one does not resolve.

## Templates (kit/components.json)
| template | parts | slots | states |
|---|---|---|---|
| `ticket` (runtime) | mover (Feel target), halo (newest crisis), frame, card, stub + hazard stripes, medallion + icon, title (short with a stamp), body, life bar, stamp (-8 deg), notches, perforation, badge | kind, title, body, stamp, icon, count, life, halo, sticky | - |
| `ticket_compact` (runtime) | same frame at 44 px: title + life bar | as ticket | - |
| `more_chip` (runtime) | "+{n} MORE" | n | - |
| `button` | shadow, face, label or icon, gamepad glyph | text, icon, hint; variants cta (the one call to action: solid accent, 30 px label), primary, secondary, icon | hover (face lifts 1), pressed (face drops 3, darker), disabled (alpha .45) |
| `chip` | face, accent ring, label, mark | text | on (ink edge 3, inner accent ring, underline mark; face stays cream), pressed, disabled |
| `panel` | shadow, body (content), header 64 + title, ticket seam (perforation + notches), close button 48 inset 8 | title, closable | - |

Runtime templates ship to Luau with their slots, because tickets are created live; the others are expanded
into each screen at build time. Rects may be px or `"P%"`, `"P%+N"`, `"P%-N"` of the instance size.

Adding a template: write it in components.json (`root` for a hit or comp root, `parts`, `slots`, `variants`,
`states` keyed by part id, `runtime: true` if game code creates it live), add it to `kit_spec` in ui.py if it
has states the kit board should show, then `ui.py render --kit`, use it in a spec, `validate`, `render` and
`build` (parity and runtime must pass). Keep every part addressable by id; the state overrides are `fill`,
`gradient`, `stroke`, `color`, `alpha` (root), `visible`, `text`, `dy`.

## Runtime (assets/luau/RR_UIKit.lua)
- `Kit.mount(def, {parent, state})` builds one ScreenGui per layer (ScreenInsets per spec, SafeAreaCompatibility
  None, ZIndexBehavior Sibling), registers every design-px property and re-applies them when the ScreenGui's
  AbsoluteSize or `GuiService.ViewportDisplaySize` changes.
- Colour binding: every coloured property remembers its role (and slot table); `screen:set` re-resolves roles
  with slots (the difficulty plate), `Kit.setSkin` re-resolves all.
- Component flags (`on`, `hover`, `pressed`, `disabled`) are applied in that order from the template's states;
  disabled hits are not Selectable and ignore Activated.
- Machine: `screen:send(event)` -> look (hide/show/disable/text) + feel event; `screen.Changed` fires
  `(to, from, event)`; `screen:can(event)` tests without warning.
- Actions: string actions fire `screen.Action` (name, data) and send the event if the machine has it;
  `set`/`cycle` change data.
- Gamepad: SelectionImageObject = a themed ring (focus + ink strokes), NextSelection* from the nav graph,
  modal SelectionGroup + Stop, SelectedObject = default on open when PreferredInput is Gamepad, ButtonB bound
  with ContextActionService at priority 3000 while open, key glyphs from `GetImageForKeyCode` shown only for
  gamepads.
- Touch zones: `avoid` reads `PlayerGui.TouchGui.TouchControlFrame.JumpButton` (or the DynamicThumbstick's
  `ThumbstickStart`) when present, else the canon worst-case zones for Touch input, and lifts the group. It
  re-lifts when TouchGui appears after mount and when the button's Visible, AbsolutePosition or AbsoluteSize
  change (luatest covers both).
- Data-bound `on` states (chips) are applied at mount, not only after the first `screen:set`.
- Motion: `Kit.useFeel(module)` or a sibling `RR_Feel`: transitions and stack events call `Feel.play(event,
  {targets = {panel | ticket | halo | stamp | button}})`; without it `Kit.fade` (0.15 s, snaps under
  `GuiService.ReducedMotionEnabled` or RR_Feel's reduceMotion setting). Stack reflow tweens 0.18 s unless
  reduce motion.
- HUD stack: `screen:push(type, slots)` (merge, life timers from canon, sticky crises), `screen:clear(type)`,
  overflow chip, compact older tickets, halo only on the newest crisis, `max_lifted` while lifted.
