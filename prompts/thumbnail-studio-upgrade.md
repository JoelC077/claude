# Prompt: upgrade the thumbnail skill (paste into a new session)

**Before sending, attach if you can:** `launch-and-discovery-playbook.md` and `ads-runbook.md`, 3–5 in-game screenshots, your best past thumbnail(s) with their QPTR if you have them, and the name of the image AI you'll finish in (ChatGPT, Midjourney, ...).

---

Upgrade my `risky-rails-thumbnail-ideas` skill into **rr-thumbnail-studio**, a JARVIS sub-skill (routed by rr-mission-control, facts from rr-bible, scored by multiuse-critic). Repo: JoelC077/claude, branch `claude/gracious-goldberg-crtklz`. Efficiency and an extremely good outcome matter most.

## My workflow (design the skill around this exactly)
1. You generate thumbnail concepts.
2. You make VERY GOOD mock-ups: close enough to a finished Roblox thumbnail that an image AI only has to polish, not invent.
3. I take the mock-ups and gather the real elements they need (screenshots, avatar poses, references).
4. I feed the mock-up + elements into ChatGPT (or another image AI) to make the finished thumbnail.
5. (New) I send the finished thumbnail back; you score it and write the fix-up edit prompts.

## Read first
- The current skill: `~/.claude/skills/synced/*/risky-rails-thumbnail-ideas/SKILL.md` (formula, honesty ledger, SVG kit, used-labels list, `render_thumbs.py`). Keep everything that works: the formula, the honesty checks, the 200 px and squint tests, the used-labels list.
- rr-bible: D-012 (thumbnail formula), `style.brand.*`, `style.type.*`, `tech.publish.thumbnails`, `economy.platform.thumbnail_personalization`, OQ-001 and the livery questions.
- multiuse-critic (scoring), rr-asset-foundry and `multiuse-critic/scripts/blender_kit.py` (3D pipeline), rr-data-and-money `references/experiments.md` (A/B).

## Known problems to fix
- **The mock-ups look like flat vector clipart.** Real top Roblox thumbnails are 3D renders: chunky avatars, rim light, bloom, depth of field, saturated colour. Clipart is a weak starting point for an image AI.
- **Canvas conflict:** the skill draws at 768×432; rr-bible says Roblox thumbnails are 1920×1080. Resolve it against the Roblox creator docs, and record the answer in the bible.
- **No handoff:** nothing tells me what elements to gather or what to type into the image AI.
- **No return path:** nothing checks the finished thumbnail against the mock-up and the formula.
- It isn't routed by JARVIS and duplicates facts that belong in rr-bible.

## Build
1. **3D mock-up pipeline (headless Blender, the default):**
   - a 3D version of the kit: a blocky Roblox-proportioned avatar with pose presets (pull, fall, point, scream-run, carry) and swappable face decals (the 4 existing faces), the loco front, the lever, the split track, a crate, a gauge, steam, sparks
   - reuse rr-asset-foundry generators where they fit
   - camera, lighting and look presets that match top Roblox thumbnails (key + rim light, bloom, a shallow depth of field, one dominant hue + hazard-yellow accent)
   - text composited afterwards (Luckiest Guy, the existing stroke/drop spec), never rendered in 3D
   - keep the SVG kit as a fast "sketch" mode for rough ideas
2. **Handoff pack per concept** (the core of the upgrade):
   - `mockup.png` at full size, plus the 200 px and squint versions
   - layers as separate PNGs: `clean-plate` (no text), characters, text (transparent), and a composition guide (thirds, safe zones, focal point, bottom strip)
   - **element shopping list:** each element I must gather, why, and exactly how. For example: "in Studio, R15 avatar, pose = lever pull, camera low at 30° FOV from the right, hazard vest on, screenshot at 1920×1080 on a green backdrop". Mark each must-have or nice-to-have.
   - **image-AI prompt pack** for my tool, written to that tool's strengths: which images to attach and in what order; the main prompt (keep the layout and pose, Roblox 3D-render style, palette hexes, NO text, bottom strip clear, no sepia/desert, no blue-sky/white-plane); 3–5 follow-up edit prompts for common failures (face lost, extra fingers, fake text, drifted palette, lost lever); and a note to add the text layer on top in an editor afterwards, because image AIs garble text.
3. **Finish check:** when I send back the finished thumbnail, the critic scores it at 200 px against the mock-up and the formula (readability, face, focal contrast, honesty, fidelity to the mock-up, brand) and returns ranked fixes as ready-to-paste edit prompts.
4. **A/B hookup:** recommend which 2+ thumbnails to run together under Roblox's thumbnail personalisation, and what to log for rr-data-and-money.
5. **JARVIS integration:** register the skill in rr-mission-control routing, read all facts from rr-bible (no hard-coded hexes), and move the used-labels list into the bible so it persists.

## Prove it (do not skip)
- Run a real batch of 3 new concepts end to end. Make one a variant of the best previous concept.
- Independent multiuse-critic (strongest model, fresh eyes) scores the mock-ups with the bar at 8/10 per criterion. Loop fix → re-check until they pass, max 3 rounds.
- Put the old SVG mock-up and the new 3D mock-up of the same concept side by side at full size and 200 px.
- Validate and package `dist/rr-thumbnail-studio.skill` and update JARVIS-INDEX.md.
- Log the cost per batch. Target: a batch without the critic loop under ~150k tokens.

## Output
- One HTML artifact per batch: concept cards (mock-up, 200 px version, why it might win, honesty flag) plus a download of each handoff pack.
- A short report: what changed, old vs new comparison, critic scores, cost, and what I should test with the image AI first.

## Rules
- Never upload to Roblox or publish anything, and never spend money.
- Never use other games' art or copyrighted assets as elements.
- The honesty rule stands: show only mechanics that exist.
- Ask me at most 3 questions, only if blocked. Otherwise use a recommended default and flag it.
- Commit and push to the branch above. No PR.
