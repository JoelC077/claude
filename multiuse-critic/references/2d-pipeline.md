# 2D pipeline (Profile B): UI, screens, thumbnails, canvases, web pages

Read this at step 3 when the work is flat. It ends with the same three things as the 3D pipeline: renders, a contact sheet and `facts.md`.

## Render a Design canvas

1. `Artifact` `list` with `scope: "files"` and the canvas `url`.
2. `Artifact` `read` with `paths`. Include:
   - every file under `project/` in that listing: the index, all artboards (`<dc-import>` children must be present), and any support files and design-system tokens
   - `artifact-type/dc-runtime.js`, the engine that renders artboards

   The result names the folder it saved into: that's ROOT.
3. Uploaded images and fonts: `grep -oh '/_blob/[0-9a-f]\{32\}' -r ROOT/project | sort -u`, then `read` each id as the `path`. They land in ROOT too.
4. Run `python3 <skill>/scripts/render_design.py ROOT OUT --boards Main.dc.html,Pricing.dc.html`, or leave out `--boards` to render all of them. It needs Python Playwright, Pillow and Chromium (else `pip install playwright pillow --break-system-packages`). If Playwright's own browser is missing, it falls back to a Chromium already on the machine; set `CHROMIUM_PATH` to point it at one. Google Fonts are blocked in the sandbox, so the script pulls the same families from npm (@fontsource).
5. What lands in OUT:
   - `<board>.png` at true size
   - `.squint.png`, greyscale and blurred
   - `.partN.png` slices of huge boards
   - `.mobile.png` for fluid pages
   - `report.md`, with measured contrast, small text, clipping, overlaps, targets, unlabelled controls, broken images, placeholders, and the type and colour inventory. Copy its findings into `facts.md`.
6. Look at the contact sheet yourself before briefing, and open a single PNG only if something looks off. If a board is blank or wrong, fix the input (a missing runtime, asset or child board) rather than sending the critic garbage.

Render limits to pass on: interactive boards show their first state only, and faces under "fonts not loaded" render in a fallback.

**Other flat inputs:**
- A hand-built HTML artifact: `read` it and run the script on that folder.
- An image: use it as is.
- A PDF: `pdftoppm -png -r 110`.
- A Figma frame: `get_screenshot`.

## The viewer's view (UI's POV camera)

Judge UI at the size it really appears on the device the owner named in step 2. That frame goes on the contact sheet at true size (`@1`); B2 and the Motion note are judged on it.

- **Authored at screen size** (a board of 1280×720, or 844×390 for a phone in landscape): that board render is the frame. For a phone, scale a PC board by the device ratio only if the owner said the UI scales with the screen (Scale sizing). With Offset sizing, it keeps its pixel size and simply takes more of the screen.
- **A mock-up page** (panels on a presentation page): crop the UI from the render and scale it to its on-screen size on a device-size frame with Pillow (for example, a phone in landscape at 844×390 with the panel at 85% of the height). Put the scale in `facts.md`, with the resulting text size of the smallest text and the target size of the smallest control.
- **In-world UI** (SurfaceGui, signs, screens in a cab): it's seen through the 3D POV camera, so use `references/3d-pipeline.md`'s cameras and judge its pixel size there.
- **Thumbnails and icons:** the real tile is 200 px wide (an icon is shown at about 150 px). Put that tile on the sheet at true size.
- **Roblox screen furniture:** on a phone, the thumbstick (bottom-left) and jump button (bottom-right) cover the bottom corners, and the top bar takes a strip at the top (Studio reports it as `GuiService:GetGuiInset()`). Draw those zones on the phone frame when they matter.

## Contact sheet

`python3 <skill>/scripts/contact_sheet.py CRIT/pass-N/contact.png "Phone 844x390=phone.png@1" "Tile 200px=tile.png@1" "Board: Main=Main.png" "Squint=Main.squint.png" ...`

The real-size frames go in the band (`@1`); boards, squint and mobile views are fitted into the grid. Keep it under 1.15 MP (the script warns and exits 2 if it isn't). Boards that need a closer look go on `closeups.png`, the one optional second image.
