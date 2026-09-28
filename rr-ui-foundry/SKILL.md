---
name: rr-ui-foundry
description: "Risky Rails (Roblox) UI foundry: turns a Claude Design canvas, HTML mock or written brief into production Roblox UI for fixed-layout screens (HUD, modal, lobby panel, buttons, chips, tickets). One JSON screen spec drives the critic boards (phone, notched phone, tablet, PC, console; every state and skin; a kit board of every component state) and a generated Luau package: Scale layout with pinned margins and own fit on small screens, safe areas, live jump-button and thumbstick avoidance, components bound to rr-bible colour roles so one token change or Kit.setSkin reskins every screen, state machines, gamepad and console navigation, reduce motion, and a Rojo export gated by validate, luaparse, the canon check and Lua parity plus runtime tests. Use whenever Risky Rails needs a HUD, menu, lobby panel, modal, button, chip or ticket built, exported, reskinned, or made phone, gamepad or console safe, or a mission has a UI deliverable. Not for scrolling lists or text input yet, critique only (multiuse-critic), juice (rr-game-feel) or 3D."
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
Never restate canon; the kit reads it at run time through `bible.py` (`bible.py get ui.rules`, `ui.hud`,
`ui.lobby`, `tech.ui_platform`, `gameplay.alerts`): colour tokens (roles in `kit/roles.json`), fonts, type sizes,
min text and touch targets, devices, insets, touch zones, density, alert texts and lifetimes, HUD rules. Canon
numbers in specs are `{"v": 8, "canon": "ui.hud.gap_px"}` (validate proves they match); game strings are
`{"canon": "gameplay.alerts.coal_low", "part": 0}`; list every rule the screen keeps in the spec's `canon`
(the critic's brief quotes them, so it never proposes a canon-breaking fix). Missing canon: `bible.py
add-question` with options and a default (`--dry-run` in trials and owner-gated runs; put the draft in the
mission folder), cite the OQ in the spec's `oq`, label the work "assumed (OQ-nnn default)". New copy is allowed
but listed as literal for the owner. The owner's new words beat canon: do the work, then record it
(`add-fact ... --src "owner DATE"` or `decide`). A decided OQ stays valid in specs; its option wins.

## Workflow
1. **Spec.** Copy the closest example from `specs/` (`hud_tickets.json`, `lobby_create_match.json`) to
   `<M>/src/<d>/spec.json` (plus its own `icons` folder if it names one; the skill's icons are the fallback),
   then re-read the source design and diff layout and rules against it: the examples are patterns, not the
   design. From a mock: `ui ingest MOCK.html --out spec.json` (a Design canvas: `Artifact read` it first as in
   `<critic>/references/2d-pipeline.md`, then `--root ROOT`); `data-rr="button:join"` hints give a clean draft;
   `DECIDE` lines are off-palette colours for the owner. Read `references/spec.md` before writing a spec.
2. **Validate:** `ui validate SPEC` must PASS (0 errors): schema, roles in every skin and what each role is for,
   canon refs and numbers, WCAG contrast per skin, min text and targets on every touch device (warnings on PC and
   console), top bar, jump and thumbstick zones, groups that collide on small screens, off-screen, icons, nav
   graph, state machine, feel event names. `--strict` also fails on warnings. Every line names a node, a device
   and a number.
3. **Render:** `ui render SPEC... --out DIR` writes HTML + PNG per board (every board on the phone, the first
   board on phone_notch, tablet, pc and console, each other skin, a zone board), `contact.png` (phone at true
   size plus a true-size PC crop, under 1.15 MP), `closeups.png` and `facts.md`. Two specs = one set: each
   screen's phone at true size on one sheet (a kit job judges both together). `--kit` adds the component board
   (every template x state x variant; best rendered on its own). `--text-scale 1.3` is a text-size stress board.
   Look at `contact.png` once; fix blank or broken boards before a critic sees them.
4. **Judge (never self-score):** `ui crit CRIT --pass 1 --from DIR --spec A[,B] [--owner away]` copies the pass
   files, writes `brief.md` (purpose, source, the canon rules kept, open and decided OQs) and prints the
   `critic_kit.py build ... --profile B` command. Owner present (default): ask multiuse-critic step 2 first.
   Continue with `<critic>/SKILL.md` steps 4-9 (fresh critic, delta passes, bar 8 unless the owner said
   otherwise). No Agent tool: rr-mission-control's critic route (remote session, handoff, or an UNCERTIFIED
   self-review). A critic fix that breaks canon goes to the owner as a question, not into the spec.
5. **Fix in the spec**, keep the previous spec in `CRIT/round-N/`, re-run 2-4. A kit change inside a mission:
   copy `kit/` to `<M>/kit`, set `RR_UI_KIT=<M>/kit` for every command, and never edit the skill's `kit/`
   mid-mission; the manifest records the diff; promote it to the skill only with the owner's OK.
6. **Build:** `ui build SPEC... --out PKG [--skin C]` writes the Rojo package (`references/export.md`) and runs
   the gates: validate, luaparse (install once: `npm i --prefix ~/.cache/rr-tools luaparse`), `bible check` on
   every file, and `luatest.py` parity + runtime tests derived from the specs (needs `pip install --target
   ~/.cache/rr-tools/py lupa`; else SKIP, named). **BUILD PASS** is required before handover; `--no-check` or
   `--no-parity` gives BUILD DRAFT, never a handover.
7. **Handover** says: files, gates, assumptions (the skin and its OQ status from `manifest.json`), Needs owner
   (ASSETS.md uploads, open OQs, OQ drafts, kit diffs to promote), and "Studio test pending (owner)" with the
   README's check (it removes the demo before publishing).

## Layout rule: pin + scale, own fit
Sizes are Scale of the design area + UIAspectRatioConstraint; each top-level group pins to an edge or the
centre and its margins are design px x its scale, so a HUD hugs its corner instead of floating. Bigger areas
scale every group by s = min(areaW/designW, areaH/designH); a smaller area (a notched phone) shrinks each group
only as much as that group needs to fit (a centred panel stays 1.0), and validate fails groups that then
collide. UIScale density per `GuiService.ViewportDisplaySize` comes from `tech.ui_platform.layout`. The design
space is the phone's ScreenGui area (CoreUISafeInsets, under the top bar). Details, `stretch`, `avoid`, layers
and pins: `references/spec.md`.

## Components, skins, states
Templates in `kit/components.json` (ticket, ticket_compact, more_chip, button with primary/secondary/cta/icon
variants and an icon slot, chip, panel with the ticket seam) are built from five primitives (frame, text, image,
hit, stack). Colours are roles; `kit/roles.json` maps each role to a bible token per skin; skins A/B/C are
OQ-001's options: while it is open the default is labelled assumed, once decided its option is the main skin.
One accent does "this is active": selected and current get an accent ring, only the cta is solid accent.
`Kit.setSkin` rebinds live; a token change in the bible plus `ui build` reskins every screen. Component states,
screen state machines, gamepad nav and the HUD stack policy: `references/kit.md`.

## Runtime (what the owner wires)
```lua
local UI = require(game.ReplicatedStorage.RR_UI.RR_UIKit)
local hud = UI.mount(require(game.ReplicatedStorage.RR_UI.screens.HudTickets))
hud:push("CoalLow") ; hud:clear("CoalLow")          -- server's show / clear alert (ID)
local lobby = UI.mount(require(game.ReplicatedStorage.RR_UI.screens.LobbyCreateMatch))
lobby:send("open") ; lobby.Action.Event:Connect(function(name, data) end) ; UI.setSkin("A")
```
The generated README lists the calls for the screens actually built. Motion: if rr-game-feel's RR_Feel sits in
the same folder, transitions play its events; otherwise the kit only fades, and snaps when Reduce Motion is on.
Gamepad: `ButtonB` is the back event, focus starts on `nav.default` only when `PreferredInput` is Gamepad.

## Inside a mission (rr-mission-control)
UI deliverable = `<M>/src/<d>/spec.json` (+ icons folder). Step 5 build = write the spec; step 6 pre-flight =
`ui validate` + `ui render`; steps 7-8 = `ui crit` into `<M>/critique-<d>/`; step 9 export = `ui build ... --out
<M>/export/<d>/` (BUILD PASS). rr-mission-control does not name this skill yet and prescribes
`render_design.py` and a hand-made layout parity check for UI: for kind ui, these steps replace them; say so in
the mission plan and list "route kind ui to rr-ui-foundry" under Needs owner until mission-control adds it.

## Open decisions
Read them, never assume their defaults from memory: `bible.py get OQ-001` (skin; `ui render SPEC --skins A,C` is
its side-by-side board), `OQ-017` (menu accent), `OQ-033` (platforms, TV density), `OQ-034` (HUD offset vs the
jump button), `OQ-003` (currency). `ui list` prints the main skin and its status.

## Honest limits
- No Roblox Studio or Studio MCP in the cloud. The boards are Chromium renders of the model and luatest runs the
  real kit against stubs: layout math, states and wiring are proven; Roblox's text metrics, UIStroke and
  UICorner rendering, GetImageForKeyCode glyphs, touch-control positions on real phones and frame pacing are not.
- The spec language has frame, text, image, hit and stack only: no ScrollingFrame, TextBox, list or grid
  layouts, sliders or localization yet, so shops, settings, inventories and leaderboards need new primitives
  (with parity and runtime tests) first. Say so instead of faking them.
- `--text-scale` approximates `GuiService.PreferredTextSize`; the kit sets TextSize without a
  UITextSizeConstraint, so truncation under Large text is a warning to check in Studio.
- Insets and touch zones are the docs' example values and the PlayerModule source (dated platform facts);
  `phone_notch` bottom inset is assumed. Measure `GuiService:GetGuiInset()` in Studio before launch.
- ingest is a draft: it snaps colours to roles and matches canon strings, it does not understand intent.
- Never publish, upload assets, spend or change the owner's config: ASSETS.md lists uploads for the owner.

## Maintain
`python3 <ui>/scripts/selftest.py` exercises every command on temp copies (must print all passed; no
`__pycache__` is written). Add a template: `references/kit.md` (last section), then `ui render --kit`.
