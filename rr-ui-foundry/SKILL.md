---
name: rr-ui-foundry
description: "Risky Rails (Roblox) UI foundry: turns a Claude Design canvas, HTML mock or written screen brief into production Roblox UI. One JSON screen spec drives the critic boards (phone, notched phone, tablet, PC, console; every state and skin; safe-area and touch-zone overlays) and a generated Luau package: Scale + UIAspectRatioConstraint ScreenGui builder with pinned margins, UIScale density per display size, ScreenInsets safe areas, jump-button and thumbstick avoidance, a component kit (ticket, chip, button, panel) bound to rr-bible colour roles so one token change or Kit.setSkin reskins every screen, state machines, gamepad and console navigation, reduce motion, and a Rojo export gated by luaparse, the canon check and a Lua layout-parity test. Use whenever Risky Rails needs a HUD, menu, lobby panel, modal, button, chip or ticket built, exported, reskinned, or made phone, gamepad or console safe, or a mission has a UI deliverable. Not for critique only (multiuse-critic), juice (rr-game-feel) or 3D."
---

# RR UI Foundry

Design board to Roblox UI with one source of truth: a screen spec. The same numbers draw the HTML boards the
critic judges and build the Luau the owner drops into Studio, and a Lua test proves they agree. Precise,
proactive, no fluff: say what you measured, what you assumed and what the owner must decide.

Paths (find by glob, never hard-code): `<ui>` = this folder;
`<bible>` = `dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path '*rr-bible/SKILL.md' 2>/dev/null | head -1)"`;
`<critic>` = the same with `*multiuse-critic/SKILL.md`. The scripts find both themselves (env overrides
`RR_BIBLE_SKILL`, `RR_CRITIC_SKILL`, `RR_FEEL_SKILL`, `RR_UI_SPECS`, `RR_UI_KIT`). `ui` below =
`python3 <ui>/scripts/ui.py`; every script has `--help`.

## Canon first
Never restate canon; the kit reads it at run time through `bible.py`: colour tokens (roles in `kit/roles.json`),
fonts (`style.type.*`, Roblox faces from `tech.ui_platform.fonts`), type sizes (`ui.hud.*_type`), min text and
targets (`ui.rules.min_text`, `tech.ui_platform.touch_target_px`), devices, insets and touch zones
(`tech.ui_platform.*`), density (`tech.ui_platform.layout`), alert texts and lifetimes (`gameplay.alerts.*`),
HUD rules (`ui.hud.*`). Canon numbers in specs are `{"v": 8, "canon": "ui.hud.gap_px"}` (validate proves they
match); game strings are `{"canon": "gameplay.alerts.coal_low", "part": 0}`. Missing canon: `bible.py
add-question` with options and a default, cite the OQ in the spec's `oq`, label the work "assumed (OQ-nnn
default)". New copy is allowed but listed as literal for the owner. The owner's new words beat canon: do the
work, then record it (`add-fact ... --src "owner DATE"` or `decide`).

## Workflow
1. **Spec.** Start from `specs/` (examples: `hud_tickets.json`, `lobby_create_match.json`) or draft one from a
   mock: `ui ingest MOCK.html --out spec.json` (a Design canvas: `Artifact read` it first as in
   `<critic>/references/2d-pipeline.md`, then `--root ROOT`). `data-rr="button:join"` hints give a clean draft;
   without hints every box becomes a node. Read `references/spec.md` before writing or editing a spec.
2. **Validate:** `ui validate SPEC` must PASS (0 errors): schema, roles in every skin, canon refs and numbers,
   WCAG contrast per skin, min text and targets on the phone (warnings on other devices), top bar, jump and
   thumbstick zones, off-screen, nav graph (reachable, no dead ends, symmetry), state machine, feel event names.
   `--strict` also fails on warnings. Every line names a node, a device and a number.
3. **Render:** `ui render SPEC --out DIR` writes HTML + PNG per board (every board on the phone, the first board
   on phone_notch, tablet, pc and console, each other skin, a zone board), `contact.png` (phone at true size,
   under 1.15 MP), `closeups.png` (zones and skins) and `facts.md`. `--text-scale 1.3` is a text-size stress
   board. Look at `contact.png` once; fix blank or broken boards before a critic sees them.
4. **Judge (never self-score):** `ui crit CRIT --pass 1 --from DIR --spec SPEC` copies the pass files, writes
   `brief.md` from the spec and canon, and prints the `critic_kit.py build ... --profile B` command. Continue
   with `<critic>/SKILL.md` steps 4-9 (fresh critic, delta passes, bar 8 unless the owner said otherwise). No
   Agent tool: rr-mission-control's critic route (remote session, handoff, or an UNCERTIFIED self-review).
5. **Fix in the spec** (or `kit/`), keep the previous spec in `CRIT/round-N/`, re-run 2-4.
6. **Build:** `ui build SPEC... --out PKG [--skin C]` writes the Rojo package (`references/export.md`) and runs
   the gates: validate, luaparse (install once: `npm i --prefix ~/.cache/rr-tools luaparse`), `bible check` on
   every file, and `luatest.py` parity + runtime (needs `pip install --target ~/.cache/rr-tools/py lupa`; else
   SKIP, named). BUILD PASS is required before handover.
7. **Handover** says: files, gates, assumptions (skin C is OQ-001's default), Needs owner (ASSETS.md uploads,
   open OQs), and "Studio test pending (owner)" with the README's 5-step check.

## Layout rule: pin + scale (why it looks the same everywhere)
Sizes are Scale of the design area + UIAspectRatioConstraint, so every group scales by s = min(areaW/designW,
areaH/designH); groups pin to an edge or the centre and their margins are design px x s, so a HUD hugs its
corner instead of floating (pure Scale positions put the HUD's 112 px bottom margin at 223 px on PC). UIScale
density per `GuiService.ViewportDisplaySize` comes from `tech.ui_platform.layout` (PC 1.16 px per design px).
The design space is the phone's ScreenGui area (CoreUISafeInsets, under the 58 px top bar). Details, and when to
use `stretch`, `avoid`, layers and pins: `references/spec.md`.

## Components, skins, states
Templates in `kit/components.json` (ticket, ticket_compact, more_chip, button, chip, panel) are built from five
primitives (frame, text, image, hit, stack). Colours are roles; `kit/roles.json` maps each role to a bible token
per skin; skins A/B/C are OQ-001's options, C (default) is labelled assumed. `Kit.setSkin` rebinds live; a token
change in the bible plus `ui build` reskins every screen. Component states (hover, pressed, on, disabled),
screen state machines, gamepad nav and the HUD stack policy: `references/kit.md`.

## Runtime (what the owner wires)
```lua
local UI = require(game.ReplicatedStorage.RR_UI.RR_UIKit)
local hud = UI.mount(require(game.ReplicatedStorage.RR_UI.screens.HudTickets))
hud:push("CoalLow") ; hud:clear("CoalLow")          -- server's show / clear alert (ID)
local lobby = UI.mount(require(game.ReplicatedStorage.RR_UI.screens.LobbyCreateMatch))
lobby:send("open") ; lobby.Action.Event:Connect(function(name, data) end) ; UI.setSkin("A")
```
Motion: if rr-game-feel's RR_Feel sits in the same folder, transitions play its events (`ui_panel_open`,
`hud_ticket_enter`, ...); otherwise the kit only fades, and snaps when Reduce Motion is on. Gamepad: `ButtonB` is
the back event, focus starts on `nav.default` only when `UserInputService.PreferredInput` is Gamepad.

## Inside a mission (rr-mission-control)
UI deliverable = `<M>/src/<d>/spec.json` (+ icons folder). Step 5 build = write the spec; step 6 pre-flight =
`ui validate` + `ui render`; steps 7-8 = `ui crit` into `<M>/critique-<d>/`; step 9 export = `ui build ... --out
<M>/export/<d>/` (BUILD PASS). The maker's order points at this SKILL.md steps 1-6.

## Open decisions (defaults in use; the owner decides)
OQ-001 HUD skin (default C, then a critic pass on A vs C: `ui render SPEC --skins A,C` gives that board),
OQ-017 menu accent (follows OQ-001), OQ-033 platforms and TV density (default: phone + PC gated, gamepad nav
built in, console boards as a check, TV density 1.0), OQ-034 HUD offset vs the newer jump button (default: kit
lifts the stack at run time and shows 3 tickets while lifted), OQ-003 currency naming. `bible.py get OQ-034`.

## Honest limits
- No Roblox Studio or Studio MCP in the cloud. The boards are Chromium renders of the model and luatest runs the
  real kit against stubs: layout math, states and wiring are proven; Roblox's text metrics, UIStroke and
  UICorner rendering, GetImageForKeyCode glyphs, touch-control positions on real phones and frame pacing are not.
- Insets and touch zones are the docs' example values and the PlayerModule source (dated platform facts);
  `phone_notch` bottom inset is assumed. Measure `GuiService:GetGuiInset()` in Studio before launch.
- ingest is a draft: it snaps colours to roles and matches canon strings, it does not understand intent.
- Never publish, upload assets, spend or change the owner's config: ASSETS.md lists uploads for the owner.

## Maintain
`python3 <ui>/scripts/selftest.py` exercises every command on temp copies (must print all passed). Remove
`__pycache__` after running scripts. Add a template: `references/kit.md` (last section).
