---
name: rr-mission-control
description: "JARVIS front door for Risky Rails (Roblox): turns a long or messy owner prompt into a planned, critic-checked, Roblox-ready mission. Use when the owner asks to make, build or remake a Risky Rails building, model, prop, UI, HUD or screen, especially with a score target, 'in Blender', 'export for Roblox', progress updates, or a blueprint/artifact/Design link; also 'mission status' or 'resume'. Not for critique-only requests (multiuse-critic), mechanic reviews or one-line questions."
---

# RR Mission Control

Take the owner's raw prompt and run it as a mission that gets the best result for the fewest tokens: every ask tagged and coverage-checked, references pulled once, one readback (max 3 questions), a task DAG with model/effort/budget, script pre-flight, the multiuse-critic loop to the bar (default 8/10), Roblox export, numbered progress and a debrief, resumable from files. You are the orchestrator: you hold the plan, the owner's words and the judgement calls; subagents build; multiuse-critic judges; scripts measure. Be precise and proactive (state risks and decisions before being asked). No butler voice, no "Sir", no emojis, no filler.

Paths: `<me>` = this skill's folder. `<critic>` = the multiuse-critic skill folder: `dirname "$(find ~/.claude/skills /home/user -maxdepth 5 -path '*multiuse-critic/SKILL.md' 2>/dev/null | head -1)"`; store it with `mission_state.py set <M> env.critic=<path>` so a resumed session reuses it. `<R>` = missions root: a folder the owner or harness names (then `export RR_MISSIONS_ROOT=<R>`; init records it as `env.root`), else `<project>/.rr-missions` if a project repo is open, else `~/.rr-missions` (never the session scratchpad: it is not findable from a new session; Cowork: `~/.rr-missions` unless the owner names a folder). `<M>` = `<R>/<YYMMDD-slug>/`.

Read a reference only at the step that names it.

## Hard rules (these are what make it cheap and good)

1. **Read once, write to disk.** Each reference (artifact, design, blueprint) is fetched once and distilled into `<M>/refs/<name>.facts.md` (tables, hex, dims, exact texts, max ~1.5k tokens). Everyone after reads the facts file, never the raw source.
2. **Your context is a dispatcher's.** You read `mission.md`, facts files, `contact.png` per pass and kit output. You never read build scripts, raw HTML, full critic answers or render folders. Don't re-read files you wrote.
3. **One-file orders.** Every subagent gets exactly one order file `<M>/tasks/T#.md` (template: `references/agent-orders.md`) and replies in at most 10 lines. Never paste conversation or rationale.
4. **Judgement stays strong.** Makers and critics run on the strongest model (cheaper critics were measured lenient). Only scouts (fact extraction) may use a small model. Deterministic work is a script, not a model.
5. **Continue, don't respawn.** The same maker is continued via SendMessage across fix rounds; the critic follows multiuse-critic (continued deltas, fresh `--kind final` only). Agent ids live in state (`mission_state.py set`).
6. **No lost asks.** Every non-noise line of the prompt maps to an R-id (`intake.py cover` must pass before building and at debrief).
7. **Write-ahead.** Update `mission.md` / state before announcing a step, so any session can resume from files alone.
8. **Never modify or overwrite owner files.** Live-MCP builds run in a NEW file (`bpy.ops.wm.read_homefile` then `save_as <owner dir>/rr-<slug>.blend`) or a new collection `RR_<slug>`; never reset the scene of the owner's open file. Exports go to a new dated folder and never replace existing files. Never commit or push mission files unless asked.

## The 10 steps (the numbering is the progress protocol)

| # | Step | Gate to leave |
|---|---|---|
| 1 | Intake: split + tag prompt, probe environment, pull refs | refs resolved or fallback recorded |
| 2 | Readback: objective, R-table, defaults, max 3 questions | no blocking question open |
| 3 | Spec + acceptance (rubric-injected), `brief.md` per deliverable | `intake.py cover` = 0 orphans |
| 4 | Plan: task DAG with model/effort/budget | `plan.py check` passes |
| 5 | Build v1 (makers, parallel per deliverable) + progress renders | one-script rebuild works |
| 6 | Pre-flight (scripts only) + you look at `contact.png` | zero objective failures |
| 7 | Critic pass 1 (fresh, strongest) | verdict checked (critic step 6) |
| 8 | Fix rounds, delta passes, final pass | bar met with final agreement, or a stop rule |
| 9 | Export for Roblox + load/reimport check | export verified |
| 10 | Debrief + memory | every R done / fallback / waived / blocked |

Small jobs may skip steps; keep the numbering and say "skipped". If the owner asks for N steps, use these 10 (map if N differs). Post every step with `mission_state.py step` (format: `references/comms.md`).

## Step 1 - Intake

1. `python3 <me>/scripts/mission_state.py init <M> --slug <slug> --kind 3d|ui|mixed --bar 8` (use the bar the owner last stated; clarifications win; a 9/10 or 10/10 request becomes 9 and you say so). Never `--force` an unfinished mission; resume it. If `<R>` is inside a git repo, append `<R>` (relative to the repo root) to `.git/info/exclude` (local, not .gitignore) unless the owner says otherwise.
2. Write the prompt verbatim with the Write tool to `<M>/prompt.raw` (and each later owner message to `<M>/clarify-<n>.raw`), then `python3 <me>/scripts/intake.py split <M> --file <M>/prompt.raw [--clarify-file <M>/clarify-1.raw]`. Never pass the prompt as a shell string (quotes, `$`, `!`, `&` get mangled). It prints one summary line and writes `<M>/lines.md` (L-ids with guessed tags); read lines.md once when writing the R-table and correct tags there.
3. **Environment probe, before the plan** (call, never trust a brief's claim; record with `set`): **critic route** first: ToolSearch "select:Agent" returns Agent -> `env.critic_mode=agent`; else `create_session` (Claude Code Remote) -> `remote`; else, if you run inside a workflow/orchestrator/subagent (your final text is a return value) -> `handoff`; else `self`. Say the mode in the readback. `handoff`/`self`: plan.py costs assume no subagents. Also: `design-critic` agent? Blender MCP (ToolSearch "blender")? `python3 -c "import bpy"`? Playwright? Artifact/Design access? Owner present or away?
4. **Refs:** "this" / links / "the prototype" resolve to artifacts. Use `Artifact read` for artifact links; a claude.ai/design link cannot be opened by Artifact, so `Artifact list type=Design` and match by the owner-given title and the link's `file=` name first (ignore punctuation and word order); only if neither matches, propose the closest and name the mismatch; if still unresolved, ask in the readback and name your fallback. Refs over ~30k tokens go to one scout subagent (small model, order template "scout"). Output: `refs/<name>.facts.md`.
5. Read `references/rr-profile.md` (standing Risky Rails facts) so you never ask what it answers.

## Step 2 - Readback (one message, then start)

Template in `references/comms.md`. It contains a `Working files: <M>` line, objective line, the R-table in the owner's own words, decisions and defaults (each "say if wrong"), at most 3 questions each with a default, the plan in one line (steps, bar, cap, token band from `plan.py`). Questions merge the critic's step-2 questions (player view, fixed constraints, owner-level additions), so multiuse-critic never asks again.

Never add owner-visible features as defaults (signage, extra rooms, effects); derived `R*` rows are only for technical constraints (scale, perf, format). Ask only if the answer changes the outcome, no ref/profile/prompt answers it, and a wrong default costs more than one fix round. Never ask about style when the owner gave licence ("a style you deem fitting"): decide, state it, offer one alternative at debrief. A question **blocks** only if a wrong guess wastes most of the work (e.g. which design file); otherwise end with "Proceeding on defaults; reply to redirect." and continue. If a blocking question is open, still do everything independent of it (e.g. build the depot while the "main hall" is unanswered). Owner away (cloud/Cowork async, subagent run): write the readback and questions into `mission.md` (Q-lines) and deliver it, then proceed on the best match even for a blocking question; mark that R `fallback` ("assumed: <choice>") and list it under Needs owner.

## Step 3 - Spec and brief

Write `mission.md` from `references/mission-template.md` (worked examples for both owner prompts are there). Per deliverable:
- Parts / boards, dimensions, palette, states, exact texts (from facts files; fidelity rule `exact` or `inspired` per ref).
- **Acceptance** = rubric-injected done-whens (template lists them for profile A and B) plus the owner's specific asks.
- Fixed camera set (3D) or device frames (UI). Progress renders use the same frames so they double as critic inputs.
- `<M>/critique-<deliverable>/brief.md` in multiuse-critic's format (read `<critic>/SKILL.md` steps 1-2 for it; title + Purpose, Audience, Player view, Stage, Fixed constraints, Owner worries/already decided incl. assumptions and placeholders). Write "step 2: pre-answered" in the last line.
Then `python3 <me>/scripts/intake.py cover <M>` must print `COVERAGE OK`.

## Step 4 - Plan

Write `<M>/plan.json` (task DAG; templates and model/effort table in `references/agent-orders.md`, examples in `references/examples/`). Then `python3 <me>/scripts/plan.py check <M>/plan.json --mission <M>/mission.md`. It validates deps and R-coverage, prints parallel waves and a token estimate. Put the estimate band in the readback if you had not yet sent it. Independent deliverables are parallel makers after a T0 style/kit spec written by you into mission.md (no T0 agent).

## Step 5 - Build

Spawn makers from their order files, in one message per wave. Working source lives in `<M>/src/<deliverable>/`; `CRIT/round-N/` is only the frozen copy you make before fix round N. 3D: one `build.py` that rebuilds everything, using `<critic>/scripts/blender_kit.py` (palette atlas, named cameras, `kit.render`), every editable part a separately named object. UI: a Claude Design canvas or HTML with the same board set the critic will render.

**"Watch it go up live":** if a Blender MCP to the owner's machine exists, the maker builds through it, stage by stage, so the owner watches. Otherwise (cloud: pip `bpy` headless, Cycles only) the build script renders the POV and 3/4 cameras at milestones (shell, roof, details, dressing); post them as one strip via `contact_sheet.py` plus a build-up GIF (Pillow, default; MP4 only if ffmpeg exists) with the step line (delivery: see Step 10). Say which mode in the readback, never pretend.

## Step 6 - Pre-flight

Scripts only, run by the maker in its continued context: 3D `kit.tris`, `verify_palette`, `backfaces` per camera, avatar fit, `reimport` (studs; 3.57x = unit bug), footprint vs blueprint; UI `render_design.py` report (contrast, small text, clipping, overlap, targets, Roblox topbar/thumbstick/jump zones). Fix objective failures before any critic pass. Then build `contact.png` and look at it yourself once; fix blank or broken views.

## Steps 7-8 - Critic loop

Run `<critic>/SKILL.md` steps 3-9 (you did 1-2) with `CRIT=<M>/critique-<group>/`, profile A|B, bar, role "senior game artist|senior UI designer". Mission-specific additions only:
- **One critic per mission** for up to 3 same-kind deliverables: one CRIT, one contact sheet holding every deliverable's cameras/boards, a per-deliverable score block in the brief. Split into more CRITs only when the images exceed the contact-sheet limit.
- If `critic_kit.py build` exits non-zero or prints `missing`, stop and fix `pass-N/` before spawning.
- Record ids: `mission_state.py set <M> agent.critic=<id>`; post each pass with `mission_state.py step` (scores + tokens). Before each fix round copy `src/<d>/` to `CRIT/round-N/`.
- **Independence is the product. Never self-score toward the bar.** A score counts only if it comes from a fresh critic that did not build the thing. By `env.critic_mode`: `agent` as above; `remote`: each pass is a `create_session` whose prompt is the critic order plus "write verdict.md into `<CRIT>/pass-N/`" (unreachable files: publish as an Artifact, give the link); `handoff`: prepare `<CRIT>/pass-N/` (`critic_kit.py build`, the critic order in `critic.md`), set `next` to "critic pass N: spawn fresh critic on <CRIT>/pass-N/critic.md", and return to the caller with that path; the caller runs the critic and resumes you with the verdict path (loop: `references/orchestrated.md`, the default for workflow/cloud runs). `self` (no route at all): one labelled self-review for fix ideas only; lines say UNCERTIFIED (the script adds it), self scores are capped at bar-1 in every report, the debrief outcome is "uncertified", and export waits for the owner's go.
- Token figures you did not read from a tool result are estimates: pass `--est` to `mission_state.py step` and mark them "est." in the ledger/debrief.

## Step 9 - Export

Read `references/roblox-export.md`. Export is done by the continued maker whenever its id is alive. 3D: per building a plain `<B>.fbx` (no texture; Color3 per group, recolourable) and, if the owner wants the atlas look, `<B>_atlas.fbx` (atlas texture blocks Studio recolouring; say so), `studio_setup.lua`, reimport in studs, `.blend` + `build.py`. UI: ScreenGui builder ModuleScript + controller + icon sheet + `ASSETS.md`, syntax-checked. Export runs only after the bar is met or a stop rule fired (say which).

## Step 10 - Debrief and memory

`python3 <me>/scripts/intake.py cover <M> --final` (every R needs a final status). Send the debrief (`references/comms.md`): outcome line, files, assumptions, Needs owner, R-table, cost (`critic_kit.py show` + build estimate), one next move. Append owner-confirmed preferences only to `<R>/memory/owner-prefs.md` (dated) and one measured lesson to `memory/lessons.md`. `mission_state.py set <M> status=done`. Part counts, scores and tokens in the debrief come from state/ledger/kit output, not memory. Delivery: running as a subagent/workflow step, the debrief and paths are your final text (no SendUserFile). Otherwise images and the debrief via `SendUserFile` (status `proactive` when the owner is away); a one-line `PushNotification` if that tool exists; otherwise paths in chat.

## Status and resume

"status", "resume", "continue": `python3 <me>/scripts/mission_state.py resume [<R>]` (default `$RR_MISSIONS_ROOT`, else `~/.rr-missions`; newest unfinished; also try `<project>/.rr-missions` and any root named in the session) or `status <M>`. It prints the step, last log lines, agent ids and the next action; read `mission.md` only if needed. Dead agent ids (new session): next critic pass is fresh (`--kind final` if all blocks-8 were addressed, else fresh delta without `--continued`); makers restart from `src/<d>/` and their order file; `<critic>` comes from `env.critic`.

## Failure handling

- Ref unreachable: fallback + ask in readback; blocking only if nothing substitutes.
- Maker fails a gate twice: re-plan that part (rebuild, not tweak), note it in the log.
- Budget: `plan.py` estimate x1.3 exceeded: interrupt with a default ("continuing to cap unless you say stop").
- Anything impossible here (live Blender without MCP, Studio publish): deliver the nearest real alternative, mark the R `fallback` with the reason.
