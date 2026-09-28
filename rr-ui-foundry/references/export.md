# Export package, gates and the Studio check

## What `ui.py build SPEC... --out PKG` writes (Rojo-friendly)
| path | what |
|---|---|
| `default.project.json` | Rojo, what ships: `src/shared/RR_UI` -> ReplicatedStorage.RR_UI (no demo) |
| `demo.project.json` | the same plus the Studio demo in StarterPlayerScripts |
| `src/shared/RR_UI/RR_UIKit.lua` | the runtime (copied from `assets/luau/`) |
| `src/shared/RR_UI/RR_UITheme.lua` | generated from rr-bible: every skin's role colours, fonts, type, density, design areas, touch zones, focus ring, asset ids |
| `src/shared/RR_UI/RR_UITemplates.lua` | generated runtime templates (tickets, more chip) |
| `src/shared/RR_UI/screens/<Screen>.lua` | generated screen data: expanded nodes, data, types, nav, machine, boards |
| `src/client/RR_UIDemo.client.lua` | Studio check (returns at once outside Studio): mounts every screen, cycles boards; K skin, L next event, H random alert |
| `icons/rr_ui_icons.png` + `icons.json` | icon sheet (white, tinted by ImageColor3), 128 px cells |
| `icons/rr_hazard_tile.png` | 32 px hazard stripe tile |
| `ASSETS.md` | what to upload and the `asset_ids.json` keys (ids survive rebuilds) |
| `UI_SPEC.md` | per screen: ScreenGui settings, states, transitions, gamepad rows, measured sizes per device |
| `README.md` | install, the calls for the screens actually built, the Studio test, "remove the demo before publishing" |
| `manifest.json` | spec hashes, kit dir + hashes (+ the diff vs the skill's kit when `RR_UI_KIT` is a mission copy), skin and its status, canon keys cited, gate results |

Generated files say so in their header; change the spec, kit or canon and rebuild instead of editing them. A
rebuild into the same folder replaces `screens/` (no stale modules). `--skin A` builds with another active skin
(all skins are always in the theme). `--no-check` (validate SKIPPED) or `--no-parity` gives **BUILD DRAFT**:
never a handover.

## Gates (BUILD PASS needs all PASS or SKIP; manifest `gates`)
1. `ui.py validate` per spec (0 errors); icons with no file fail the build too.
2. luaparse (Lua 5.1 grammar) on every .lua; the kit and generated files avoid Luau-only syntax so this and the
   Lua 5.1 VM both work. Missing node/npm -> SKIP, said so.
3. `bible.py check` on every .lua and UI_SPEC.md: colours, fonts, banned names, canon numbers.
4. `luatest.py --package PKG --specs a.json,b.json` (the build passes the specs; never the skill's examples):
   parity (every visible GuiObject's rect within 0.5 px of the HTML board, same texts, text sizes, fills,
   gradients, strokes, text colours; all devices and boards) and runtime tests derived from each spec, whatever
   its names: every transition (state + look vs the model), illegal events, disabled controls, set/cycle actions,
   string actions, gamepad focus and links, modal group, glyphs, ButtonB, press, reduce motion, reskin, resize to
   PC and the notched phone, HUD push/merge/expiry/sticky/clear/overflow/slots, live touch-zone lift. Nothing to
   test in a spec = a named SKIP (`-v`); 0 checks or a missing package = FAIL. No lupa -> SKIP, said so.

## Studio test (owner; the handover says "Studio test pending (owner)")
1. Play Solo with the demo; compare each board with the rendered PNGs.
2. Device emulator: iPhone 14 landscape, an iPad, 1920 x 1080. The HUD clears the jump button and the top bar;
   note `GuiService:GetGuiInset()` and the JumpButton's AbsolutePosition if they differ from the facts
   (`tech.ui_platform.topbar_inset`, `jump_zone_small`) and record them with `bible.py add-fact ... --status measured`.
3. Controller: Select or the default focus reaches every control; ButtonB closes the lobby.
4. Settings > Reduce Motion: panels and tickets fade or snap, nothing slides.
5. Upload the ASSETS.md images, write `asset_ids.json`, rebuild.

## Fidelity (what the boards cannot show)
- Fonts: the boards embed the same Google fonts (Luckiest Guy, Montserrat); Roblox's text rasteriser and line
  metrics differ slightly, so a label that just fits on a board may truncate in Studio.
- UIStroke uses BorderStrokePosition Inner (`tech.ui_platform.stroke_position`) to match the boards' inset
  strokes; older clients without the property draw it outside (pcall'd).
- ClipsDescendants clips to the rectangle, not the rounded corner; the boards clip the same way on purpose.
- The mock plate behind the boards is a stand-in for the world (rr-game-feel's plate tokens), not a screenshot.
