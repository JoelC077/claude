# rr-ui-foundry · design notes (2026-09-28)

## Job
Turn a UI design (Claude Design board, HTML mock or a written brief) into production Roblox UI: a screen spec
that drives both HTML boards for multiuse-critic and a generated Luau package (ScreenGui builder data + one kit
runtime), with rr-bible tokens, safe areas, states, gamepad navigation and reduce-motion built in.

## Pipeline
```
mock (Design board / HTML)  --ui.py ingest-->  draft spec (colours snapped to roles, texts matched to canon)
spec JSON (specs/<screen>.json, design px of the phone board)
  -> ui.py validate   schema, roles and tokens resolve for every skin, canon refs, contrast per skin, min text and
                      touch targets per device, safe areas and touch zones, nav graph, state machine, literals
  -> ui.py render     HTML per device x state x skin from the SAME layout resolver -> Playwright PNGs, zone board,
                      skin board, contact.png (phone @1) + closeups.png + facts.md
  -> ui.py crit       CRIT pass files + brief from spec and canon -> critic_kit.py build --profile B (never self-scored)
  -> ui.py build      RR_UITheme.lua (bible tokens, skins, fonts, type, density, zones), RR_UITemplates.lua,
                      screens/*.lua (data), RR_UIKit.lua (runtime), demo, Rojo project, ASSETS.md, UI_SPEC.md,
                      manifest; gates: luaparse, bible check, lupa parity (Luau rects == HTML rects per device)
```

## Decisions (with why)
1. **One spec, two emitters, one proof.** Python expands templates and resolves layout once; HTML boards and Luau
   data come from the same numbers. `luatest.py` runs the shipped kit in Lua 5.1 against a stub layout engine
   (Scale, Offset, AnchorPoint, UIAspectRatioConstraint, UIScale, ScreenInsets) and compares every rect with the
   HTML resolver per device. Fixes the HUD mission's hand-rolled "layout parity" (friction #11).
2. **Pin + scale layout.** Sizes are Scale + UIAspectRatioConstraint (FitWithinMaxSize), so a group scales by
   s = min(areaW/designW, areaH/designH) on bigger areas; on smaller ones (notched phone, s 0.86) each group keeps
   its own fit (shrinks only as much as its margin + size need), because one global s pushed the HUD titles and
   every 44 px target under canon minimums (trial friction #2); validate fails groups that then collide. Positions pin to an edge or centre with margins scaled by the same s
   (kit-updated offsets). Pure Scale positions float: the HUD's 112 px bottom margin becomes 223 px on PC instead
   of canon's 127.6. UIScale density per GuiService.ViewportDisplaySize comes from `tech.ui_platform.layout`
   (phone 1.0, PC 1.16 => 0.765 of the fit scale); Large (TV) is OQ-033. Text, stroke and corners = design x s.
3. **Design space = the ScreenGui area of the design device.** Mock coordinates are phone-screen px; the
   CoreUISafeInsets area starts under the 58 px top bar. A node in the top strip fails unless it sits in a
   backdrop layer (ScreenInsets None). SafeAreaCompatibility None. `phone_notch` (59/58/59/21) is the worst case.
4. **Touch zones are measured, not guessed**: Roblox PlayerModule geometry recorded as platform facts; checked per
   device; `avoid` lifts a group above the real JumpButton or thumbstick at run time. Found: canon's HUD offset
   overlaps the ability-controls jump button by 24 px (OQ-034).
5. **Tokens by role.** Specs hold no hex. Roles map per skin to rr-bible keys; the three skins are OQ-001's options
   (C labelled assumed while open; once decided, the decision's option is the main skin). The theme is generated from the bible, and every coloured property is bound to a
   role, so one token change plus `build` (or `Kit.setSkin` live) reskins every screen. `render --skins A,C`
   produces OQ-001's side-by-side board.
6. **Components are data templates** (panel, button, chip, ticket, compact ticket, more chip; plus a themed focus ring) of five primitives
   (frame, text, image, hit, stack) with slots, variants and states; expanded in Python for boards and
   instantiated by the kit at run time (tickets arrive live).
7. **State machines are declared**: screen states set node looks; transitions name rr-game-feel events; illegal
   events are ignored and warned. Component states: button normal/hover/pressed/selected/disabled, chip off/on.
8. **Gamepad first-class**: nav graph from grid rows or geometry; validator proves reachability, no dead ends and
   symmetric edges; modal = SelectionGroup + Stop; SelectedObject only when PreferredInput is Gamepad; ButtonB is
   the back event; key glyphs from GetImageForKeyCode; themed SelectionImageObject.
9. **Motion belongs to rr-game-feel** (`Feel.play`, event names checked against feel.json). Without it the kit
   only fades, and snaps under GuiService.ReducedMotionEnabled. No hand-rolled juice here.
10. **Honest outputs**: never publish or upload; ASSETS.md lists uploads; "Studio test pending (owner)".

11. **Tests come from the spec, not the examples** (2026-09-28 fix pass): luatest runtime walks each spec's machine,
   actions, nav, stack types and avoid groups and compares the live Lua tree with the model after every step; the
   first run found a real kit bug (chips showed no selected state until the first tap).

## Plugs
- rr-bible: tokens, fonts, type sizes, alert texts, HUD rules, platform facts and OQs read at run time via
  bible.py; `bible check` on every export. New facts: tech.ui_platform.* (insets, zones, input, display size).
- rr-mission-control: UI deliverable = `<M>/src/<d>/spec.json`; pre-flight = validate; renders feed the critic;
  step 9 export = `ui.py build`. OPEN integration (owner-gated, mission-control's maintainer): mission-control
  does not route kind ui here yet; its step 6 (`render_design.py`) and roblox-export.md's hand-made layout parity
  should point to `ui validate/render/crit/build` for kind ui.
- multiuse-critic: contact_sheet.py and critic_kit.py found by glob; Profile B; phone board at true size.
- rr-game-feel: event names for transitions; RR_Feel used when present in the same folder.

## Limits
Fixed layouts only: no ScrollingFrame, TextBox, list/grid layouts, sliders or localization primitives yet.
No Studio: the stub engine models Roblox layout, not its renderer. Web fonts approximate Roblox text metrics;
TextSize, UIStroke and GetImageForKeyCode need the owner's Studio check. Insets are the docs' example values.
