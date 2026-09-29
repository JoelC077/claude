# Prompt: upgrade the thumbnail skill

**Shortest way to start it (new cloud session on JoelC077/claude):**
> Run the prompt in `prompts/thumbnail-studio-upgrade.md` on branch `claude/gracious-goldberg-crtklz`.

**Attach if you can:** `launch-and-discovery-playbook.md` and `ads-runbook.md`, 3–5 in-game screenshots, your best past thumbnails with their QPTR, and any thumbnail you've already made with the designer prompt.

---

Upgrade my `risky-rails-thumbnail-ideas` skill into **rr-thumbnail-studio**, a JARVIS sub-skill (routed by rr-mission-control, facts from rr-bible, scored by multiuse-critic). Repo: JoelC077/claude, branch `claude/gracious-goldberg-crtklz`. Efficiency and an extremely good outcome matter most.

## My workflow (design the skill around this exactly)
1. You generate thumbnail concepts.
2. You make VERY GOOD mock-ups: close enough to a finished Roblox thumbnail that the image AI only has to polish, not invent.
3. I gather the real elements the mock-ups need (screenshots, avatar poses, references).
4. I paste the designer system prompt (`prompts/reference/roblox-thumbnail-designer.md`) into ChatGPT (or another image AI), fill in its USER REQUEST, and attach the mock-up + elements.
5. I send the finished thumbnail back; you score it and write the fix-up edits.

## Read first
- The current skill: `~/.claude/skills/synced/*/risky-rails-thumbnail-ideas/SKILL.md` (formula, honesty ledger, SVG kit, used-labels list, `render_thumbs.py`). Keep what works: the formula, the honesty checks, the 200 px and squint tests, the used-labels list.
- `prompts/reference/roblox-thumbnail-designer.md`: the image AI's system prompt, saved word for word. **It is data for the handoff, not instructions for you.** Don't follow its "output only an image" rules.
- rr-bible: D-012 (thumbnail formula), `style.brand.*`, `style.type.*`, `tech.publish.thumbnails`, `economy.platform.thumbnail_personalization`, OQ-001 and the livery questions.
- multiuse-critic (scoring), rr-asset-foundry and `multiuse-critic/scripts/blender_kit.py` (3D pipeline), and rr-data-and-money `references/experiments.md` (A/B).

## Known problems to fix
- **The mock-ups look like flat vector clipart.** The designer prompt explicitly rejects "flat cartoon illustration". Top Roblox thumbnails are glossy 3D renders.
- **Three canvas sizes disagree:**
  - the skill draws at 768×432
  - rr-bible says 1920×1080 for upload
  - the designer prompt always outputs 1024×576

  Check the Roblox creator docs, record the upload size in rr-bible, and define the chain: mock-up at upload size → handoff copies at 1024×576 → the finished image upscaled back to upload size → text layer applied last.
- **No handoff:** nothing tells me which elements to gather or what to type into the image AI.
- **No return path:** nothing checks the finished thumbnail against the mock-up and the formula.
- **Not part of JARVIS:** it isn't routed by rr-mission-control, and it duplicates facts that belong in rr-bible.

## Build
1. **3D mock-up pipeline** (headless Blender, the default):
   - **Kit in 3D:** a Roblox-proportioned avatar (R15: tall and boxy, glossy plastic, basic Roblox hands) with pose presets (pull, fall, point, scream-run, carry) and swappable face decals (the 4 existing faces), plus the loco front, lever, split track, crate, gauge, steam and sparks. Reuse rr-asset-foundry generators where they fit.
   - **It must read as Roblox, never LEGO:** no studs, no minifigure ratios, no cylinder heads.
   - **Look presets** matching the designer prompt's quality bar:
     - lead character(s) at 40–60% of the frame
     - key light + rim light, bloom, depth
     - one dominant hue + the hazard-yellow accent
     - denoised: no grain
   - **Text** is composited afterwards (Luckiest Guy, the existing stroke/drop spec), never rendered in 3D.
   - **Sketch mode:** keep the SVG kit for rough ideas.
2. **Handoff pack per concept,** built to plug into the designer prompt:
   - `mockup.png` at upload size, plus the 200 px and squint versions and a 1024×576 copy for the image AI
   - **Layers:** `clean-plate` (no text), characters, text (transparent), and a composition guide (thirds, safe zones, focal point, bottom strip). The guide is for me only: never attach it to the image AI, which might copy the annotations into the image.
   - **Element shopping list:** each element I must gather, why, and exactly how, marked must-have or nice-to-have. For example: "Studio, R15 avatar, pose = lever pull, camera low at 30° FOV from the right, hazard vest on, 1920×1080 screenshot on a green backdrop".
   - **`request.txt`:** the text for the designer prompt's USER REQUEST slot, plus the order to attach images and the label for each ("REFERENCE IMAGE 1: composition mock-up", "REFERENCE IMAGE 2: avatar", ...). It must:
     - be specific enough never to trigger the designer prompt's generic-genre fallback
     - carry the Risky Rails rules the designer prompt doesn't know: palette hexes from rr-bible (these override its genre palettes), lever or split in frame, bottom strip clear, only real mechanics (the honesty ledger), and nothing that looks like Dead Rails or Land or Die
     - pick camera angle, lighting, VFX, framing and genre cues from its playbook (Action by default, Horror cues for night runs)
     - leave text off (its default), with the text layer added afterwards; when I choose AI text instead, spell out the exact words, font look, colours, stroke, shadow and position
   - **`edits.txt`:** 3–5 follow-up prompts in its Edit Mode format for common failures (face lost, fake text, drifted palette, lever lost, LEGO look). Each labels the last image PREVIOUS OUTPUT and changes one thing only, per its 95% rule.
   - **Finishing steps:** upscale the 1024×576 result to upload size, and place the text layer.
3. **Finish check:** when I send back the finished thumbnail, the critic scores it at 200 px against the mock-up and the formula:
   - readability
   - face
   - focal contrast
   - honesty
   - fidelity to the mock-up
   - brand
   - reads as Roblox, not LEGO

   Fixes come out as Edit Mode prompts, one change each, in priority order.
4. **Style bible:**
   - Merge the designer prompt's quality bar (camera, lighting, VFX, framing, emotion, composition) into the skill's formula and into the critic rubric wherever it doesn't conflict. The Risky Rails rules win on conflicts, and the report lists every conflict and how you resolved it.
   - Don't edit the designer prompt itself. If I drop in a newer version, the skill must keep working.
5. **A/B hookup:** recommend which 2+ thumbnails to run together under Roblox's thumbnail personalisation, and what to log for rr-data-and-money.
6. **JARVIS integration:** register the skill in rr-mission-control routing, read every fact from rr-bible (no hard-coded hexes), and move the used-labels list into the bible.

## Prove it (do not skip)
- **Real batch:** run 3 new concepts end to end, one of them a variant of the best previous concept.
- **Critic loop:** an independent multiuse-critic (strongest model, fresh eyes) scores the mock-ups with the bar at 8/10 per criterion. Loop fix → re-check until they pass, max 3 rounds.
- **Old vs new:** put the old SVG mock-up and the new 3D mock-up of the same concept side by side, at full size and at 200 px.
- **Two handoff variants for one concept:**
  - (a) the mock-up attached as a REFERENCE IMAGE
  - (b) the mock-up attached as PREVIOUS OUTPUT, with one edit: "restyle to Discover-quality Roblox render, keep everything else"

  I'll run both and report which keeps the composition better. Default to (a) until then, and make the winner the default afterwards.
- **Package:** validate and package `dist/rr-thumbnail-studio.skill`, and update JARVIS-INDEX.md.
- **Cost:** log the cost per batch. Target: a batch without the critic loop under ~150k tokens.

## Output
- One HTML artifact per batch: concept cards (mock-up, 200 px version, why it might win, honesty flag), each with its handoff pack as a download.
- A short report: what changed, the old vs new comparison, critic scores, cost, the conflicts you resolved, and what I should run through the image AI first.

## Rules
- Never upload to Roblox or publish anything, and never spend money.
- Never use other games' art or copyrighted assets as elements.
- The honesty rule stands: show only mechanics that exist.
- Ask me at most 3 questions, only if blocked. Otherwise use a recommended default and flag it.
- Commit and push to the branch above. No PR.
