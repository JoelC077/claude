---
name: multiuse-critic
description: "Honest, fresh-eyes critique by an independent critic agent that scores a game UI, design or 3D model against a fixed rubric (overall = lowest criterion), gives ranked fixes with a done-when check, and can loop fix → re-check until every criterion hits the bar, at a controlled token cost (one brief file per pass, the same critic continued between passes, a cost ledger). Use when asked to critique, review, roast, score or polish a Claude Design canvas, Roblox UI, HUD or screen, web page, mockup, thumbnail, or a 3D model, build or render (Risky Rails and other Roblox assets), including 'is this good?' or 'get it to 8/10'."
---

# Design critique

Get a straight-talking, rubric-scored critique from a critic agent that didn't make the work. It judges real renders and measured facts, not source code, which is what makes its feedback worth acting on. One flow covers both kinds of work; only step 3 differs:
- **Profile B, flat work:** UI and HUD screens, Claude Design canvases, HTML pages, mockups, thumbnails, and PNG or PDF exports.
- **Profile A, 3D models:** built and rendered in Blender. This is the default for Risky Rails vehicles, props and environments.

Run it when the user asks for a critique, review, score or feedback, asks for work to be polished to a score (the loop, step 8), or asked up front for a check before handover. Don't bolt it onto every design turn unasked: it costs the user time and tokens.

`<skill>` below means this skill's folder: scripts are in `<skill>/scripts`, long reference material in `<skill>/references`. Read a reference only at the step that names it.

## Files for one critique

`CRIT=<scratchpad or the project folder>/critique-<name>/`:
- `brief.md`: written once, in steps 1–2.
- `pass-N/`:
  - the renders, and `contact.png` (every view on one sheet, the player's view at true size) plus its `contact.json`
  - an optional `closeups.png`
  - `facts.md` (measurements), and `delta.md` from pass 2 on
  - `critic.md` (built by the kit) and `verdict.md` (the critic's SCORES lines, copied, not the whole answer)
- `round-N/`: the source as it stood before round N's fixes. That's how you roll back.
- `ledger.json` and `ledger.md`: one row per pass, with the scores, the fixes, and the critic's **tokens, tool calls and minutes** (`critic_kit.py log`).

## 1. Pin down what, and for what

**The thing.**
- A Design canvas link in the conversation means that canvas. Otherwise use `Artifact` `list` with `type: "Design"`: if there's one canvas, use it; if several, take the one the user named or last worked on; if still unclear, ask.
- For a 3D model, use the Blender scene or build script that was just made.

**The artboards (2D).** Take whatever the user pointed at: artboards they named, or `selectedArtboards` / `visibleArtboards` from an `<artifact-view-context>` block when they say "this one". Otherwise take all of them. With more than about 8, split them across critics.

**The profile.** 3D model → A. Anything flat → B.

**The brief** goes in `brief.md`. Start it with a `# <name>` title line, then 3–6 lines. The critic judges against it, so it matters more than anything else you hand over:
- Purpose: the one job.
- Audience.
- **Player view:** how it's really seen (step 2).
- Stage: blockout, draft or near-final.
- Fixed constraints: scale, palette, required parts, budget. For work outside Risky Rails, add a "House style" line.
- What the user is worried about, and anything already decided (step 2).

Take it from the conversation, the files and the project docs.

## 2. Ask the owner, before pass 1

In one message, ask at most 3 questions, and only ones whose answer would change the verdict and that the conversation and docs don't already answer:
1. **How the player actually sees it:** the camera, the distance, and whether it or the world moves. In the canopy run, "players never leave the train; the third-person camera sits ~9.5 studs up; the world scrolls" decided most of the critique. For UI, ask about the device, the on-screen size, Scale or Offset sizing, and whether it's a screen overlay or in the world.
2. **Fixed palette or constraints:** a triangle budget, sizes, parts that must stay.
3. **Owner-level additions** that are likely to come up: a focal point, lettering or signage, a logo, numbering. Does the owner want them, or is it deliberately plain? Settle this now; a critic "discovering" it at pass 4 costs passes.

Write the answers into `brief.md`. If the owner doesn't answer, write your assumption there and repeat it when you present.

## 3. Render and measure

Profile A: read `<skill>/references/3d-pipeline.md`. Profile B: read `<skill>/references/2d-pipeline.md`. Either way, `pass-N/` ends up with:
- **the player's view**:
  - for 3D, POV cameras at the real Roblox eye heights (third-person about 9.5 studs above the floor, first-person about 5, vertical FOV 70) and the 400 px game-distance render
  - for UI, the real-size frame on the owner's device
- the secondary views: construction cameras (3/4, side, ends, close-ups) or the boards
- `contact.png` from `scripts/contact_sheet.py`, with the player's-view frames at true size and under 1.15 MP
- `facts.md`, measured by script

Look at `contact.png` yourself before briefing, every pass. It's one image and shows every view, not just the ones you changed. Open a single render only when something on the sheet looks off. If a view is blank or wrong (a black face, a missing part, a camera inside a wall), fix the input instead of sending the critic garbage. Every image you open stays in your context and is re-sent on every later turn.

## 4. Build critic.md

`python3 <skill>/scripts/critic_kit.py build CRIT --pass N --kind full --profile A|B --role "senior game artist"` (for UI, use `"senior UI designer"`).

It writes one `critic.md`: how to work, the brief, the facts, the delta and standing scores (later passes), the rubric trimmed to the criteria being scored, and the output format. It also prints the exact prompt. **The critic reads that one file, plus `contact.png` and at most one close-up image, and nothing else.** Never paste the rubric or brief into a prompt.

## 5. Pass 1: a fresh critic on the strongest model

Spawn one subagent with the printed prompt:
- **Agent type:** `design-critic` if the owner has installed it (see below), otherwise general-purpose.
- **Model:** leave `model` unset so it inherits your session's model, or name the strongest one.

The prompt tells it:
- open the file and the images together, in parallel, in its first message
- its answer must come in its 3rd message at the latest
- opening images one at a time is a failure

Give it only the files, not the conversation or the rationale: a critic that has read the reasons starts agreeing with them. **Keep its agent id**, because every delta pass goes back to this same critic.

Then:
- Copy its SCORES lines into `pass-1/verdict.md`.
- Log the pass: `critic_kit.py log CRIT --pass 1 --kind full --agent critic-1 --model <m> --scores "A1=7,..." --tokens T --tools U --minutes M`. Take tokens, tool calls and duration from the Agent result.
- Log every pass of a continued critic under the same `--agent` name. The Agent result then reports its whole carried context, and the kit works out what the pass added.
- The kit warns when a pass goes **over 120k tokens**. Tell the owner straight away, with the likely cause.

**Optional, once, by the owner:** install `<skill>/agents/design-critic.md` as a Claude Code agent (copy it to `~/.claude/agents/`, then start a new session). It gives the critic only the Read tool, where a general-purpose agent carries every tool: about 48k tokens of context before it reads anything. It also sets the critic's thinking effort (`effort: high`; an integer caps thinking tokens) and a turn limit. Offer it, but don't install it yourself: it changes the owner's Claude Code config.

For many artboards, run one critic per group in parallel, each with its own `critic.md` and told to flag cross-group inconsistencies. If there's no Agent tool, critique it yourself from the same `critic.md`. Write your first read before opening any source, and label the result a self-review.

## 6. Check the critic's work

Before anything reaches the user or you fix anything:
- **Evidence:** drop any issue you can't see in the renders or find in the facts.
- **Concrete fixes:** drop or sharpen vague ones. Every fix names a part and a value, and every done-when is checkable.
- **Brief and constraints:** drop anything that contradicts the brief, a fixed constraint, an owner decision or a render limit.
- **Score validity:** a score without an anchor-plus-evidence line, or a score of 8 or more with a `blocks-8` issue open on that criterion, is invalid. Lower it to the highest score its own evidence supports (at most 7 if a `blocks-8` issue is open). Don't raise scores.
- **Drift:** a standing score at the bar may drop only under rubric rule 8. The critic must either cite a part that changed since that pass, or name a missed `blocks-8` issue with pixel or measurement evidence and say why it was missed. Without that, restore the standing score and note it in the ledger.
- **Doubts:** when the critic suspects something the renders can't settle (a smear, a seam, a dark face), make a diagnostic render or measurement and decide it yourself. Don't spend a pass on it.
- **Merge and trim:** merge duplicates and trim the minors. Keep every high-impact issue. Keep the `blocks-8: no` issues in the ledger's polish queue (step 9).

If you made the work, you're the least neutral judge in the room. Drop only what's factually wrong, and tell the user about any high-impact issue you dropped, with the reason.

## 7. Present (when not looping, or at the end of a loop)

Straight talk, most important first. Lead with the overall score (the lowest criterion), then the criterion table, then the ranked fixes:

> **6/10 overall. Materials (A4) is the floor; everything else is 7–8.**
> | Silhouette 8 · Proportions 8 · Topology 7 · **Materials 6** · Distance read 7 · Style 8 · Polish 7 |
> 1. **A4-1 · high · Body.** Plain Blender colours won't import into Roblox. → Bake a 256×256 palette atlas (32 px cells, so Roblox's mipmaps don't bleed between colours), one material. *Done when* every part uses the atlas and `verify_palette` passes.
> **Needs owner:** the seating layout.
> **Keep:** the joint system.
> *Critic cost (ledger): 1 pass · 139,670 tokens · 3 tool calls · 13 min.*

End by offering to run the loop, if it wasn't already asked for.

## 8. Fix loop ("keep going until it's 8/10")

**The bar is every criterion at or above the target.** No number given means 8. A request for 9 or 10 is treated as 9, and you say so.

**Hard cap: 5 critic passes in total**, including pass 1 and the final pass.

Keep every version: copy the source (canvas `project/`, the build script, or the `.blend`) to `CRIT/round-N/` before each round of fixes.

**Each round:**
1. **Fix**, in the ledger's order:
   - high-impact issues on the lowest criteria first, then every `blocks-8` issue on criteria below the bar, then quick, safe low-impact issues
   - fix the way the work's own direction would: its palette, scale and style
   - adding a part or state the brief plainly needs is fair; changing the concept or aesthetic isn't, so stop and ask
   - never buy points by deleting something the job needs or by inventing content (a fake price, a mechanic that doesn't exist). Mark placeholders and put them under Needs owner.
   - never undo an earlier round's fix because a critic dislikes it. Keep the earlier fix and note the disagreement.
2. **Re-render** the same cameras into `pass-N/`, rebuild `contact.png` and `facts.md`, and look at them yourself.
3. **Write `delta.md`.** It holds only:
   - the criteria still below the bar
   - each one's open issues (id, problem, done-when)
   - the fixes applied (what changed, which parts)

   The kit adds the standing scores, and for delta passes only the facts that changed.
4. **Run the next pass:**
   - **Delta pass: the same critic, continued.** Run `critic_kit.py build CRIT --pass N --kind delta --profile X --continued`, then `SendMessage` the printed text to the pass-1 critic's agent id. Its context carries over, so it checks the fixes against what it saw before. It scores only the criteria below the bar and lists regressions.
   - **Final pass: verify + full rubric, merged.** Once this round's fixes address every open `blocks-8` issue (so every criterion should now be at the bar), make the next pass `--kind final` instead. This is a fresh critic on the strongest model: it verifies the fixes and scores every criterion against the standing scores under rule 8. It's the only fresh critic after pass 1, and there's no separate closing check.
5. **Check its work** (step 6), copy its SCORES lines to `verdict.md`, log the pass, and update the ledger:
   - a criterion reaching the bar leaves the checking set
   - a regression puts its criterion back in the set
   - new issues join the queue
   - a valid drop in the final pass sends that criterion back into the loop, and later deltas continue the final critic

**Models.**
- **Every critic runs on the strongest model.** A cheaper delta critic was tested and rejected. It thought as long and ran slower. It gave three 9s "because none", and it missed three real, measured issues the strongest critic caught. A lenient delta can end the loop with flaws still in.
- Deltas go to the same critic by `SendMessage`. It adds only what's new: about 5k tokens of input in the test, with its earlier context served from cache.
- If that critic can't be continued (a new conversation, or a lost agent), spawn a fresh critic on the strongest model. Build its `critic.md` without `--continued`, so it carries the brief, the trimmed rubric and the previous critic's score lines.

**No-progress rule:**
- A criterion's score unchanged across two consecutive passes, or the overall score unchanged twice, means the fix approach isn't working. Change approach (rebuild the part instead of tweaking it, a different technique, a diagnostic render to prove the fix) and note the change in the ledger.
- If the same criterion stalls again, stop: it's a direction call or a limit of the tools. Report it as such.
- A valid drop that cites a part you changed is a regression. Roll that part back to `round-N`, or re-fix it next round.

**Stop when any of these is true:**
- every criterion is at the bar and the final pass agrees
- 5 passes are used up
- a second stall on the same criterion
- everything left is Needs owner or a direction call

**Report** (step 7 shape) with:
- the pass-by-pass path: pass · critic and model · criteria checked · each score · overall · what changed · tokens, tool calls, minutes. `critic_kit.py show CRIT` prints it with totals.
- what's still short, and why (the evidence and what it would take)
- the Needs owner list

Present 8 as "every criterion at the professional-delivery anchor or better", not as a precise measurement.

## 9. After the cap: post-loop polish

When the passes are used up, or the bar is met and the owner wants more, you may do a **post-loop polish**:
- Apply only the critic's non-blocking fixes (`blocks-8: no`) still in the queue, and nothing that changes the concept.
- Self-check each one with the same cameras or frames, looking at the renders yourself.
- Report them in their own section, headed **Post-loop polish (not re-scored)**, with what you checked for each.

Never change a score or claim the bar moved because of them.

## Cost rules

- **One file plus 1–2 images per pass**:
  - `critic.md`, then `contact.png` (which already holds the POV and game-distance frames), and at most one close-up
  - the critic opens them together in its first message and answers by its 3rd
  - opening images one at a time is a failure
  - more than 3 tool calls in the ledger means the protocol slipped
- **Turns cost more than images.** Every extra critic turn re-sends the whole context, images included. The canopy run's passes took 7–13 tool calls and cost 180–240k tokens and 20–43 minutes each: about 1.1M tokens in total.
- **Thinking and base context are the rest.** In the dry test, the protocol held (3 tool calls every pass), and a pass still reported about 140k tokens:
  - about 48k: a general-purpose agent's tools, before it reads anything
  - about 8k: `critic.md` plus the contact sheet
  - 50–80k: thinking
  - The levers are the `design-critic` agent (only the Read tool, with an effort setting) and critic.md's "keep your reasoning proportionate".
- **No image over 1.15 MP or 1568 px.** The reader shrinks bigger ones, and the true-size frames stop being true size.
- **Continue the same critic for deltas.** Never respawn it to re-score criteria already at the bar. Its reported tokens include everything it carries (its earlier thinking too), but the carried part is cheap cache reads. The ledger's "new this pass" column is what the pass cost.
- **Log every pass.** Warn the owner the moment a pass goes over 120k tokens, with the kit's split between new and carried tokens.
- **Your own context counts too.** View the contact sheet, not every render. Don't re-read files you wrote. Let the kit print the ledger.
