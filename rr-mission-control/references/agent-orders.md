# Agent orders, DAG templates, model/effort/budget (step 4)

## Model and effort per role
| role | model | effort | reads | replies |
|---|---|---|---|---|
| orchestrator (you) | session model | think hard once at spec/triage, lightly elsewhere | mission.md, facts, contact.png, kit output | step lines |
| scout (ref > ~30k tokens) | small model OK | low | the URL/path only | `refs/<name>.facts.md` + 3 lines |
| maker v1 | strongest | high | its order file + listed facts | <= 10 lines + output paths |
| maker fix (continued) | same agent | medium | fix list message only | <= 10 lines |
| script | none | - | - | files |
| critic full / final | strongest, `design-critic` type if installed | high (per multiuse-critic) | critic.md + contact.png (+1 closeup) | kit format |
| critic delta | continued critic | - | SendMessage text | kit format |
| exporter | continued maker (mandatory while its id is alive); if dead, a fresh mid-tier model is fine (mechanical work) | low-medium | export order + export spec | <= 10 lines |

Never a cheap model on a judgement task (critic, maker, triage): measured lenient. `plan.py check` rejects it.

## Budget table (used by `plan.py`)
| task | tokens |
|---|---|
| scout | 15k |
| maker v1 | 70k |
| maker fix round (continued) | 25k |
| critic full (general-purpose) | 140k (measured 90-190k; ~48k is agent base, 50-80k thinking) |
| critic delta (continued, new tokens) | 35k |
| critic final (fresh) | 120k |
| exporter continued / fresh | 30k / 70k |
| design-critic agent installed | saving per multiuse-critic (plan.py uses 48k) |
Warn the owner at 120k for any single critic pass (kit prints it) and at 1.3x the plan estimate overall.

## DAG templates (plan.json; full examples in `examples/`)
- **3D, N buildings:** T0 kit spec by the orchestrator in mission.md (palette, modules, cameras, naming; no agent) -> makers in parallel (the first writes `src/kit.py`) -> pre-flight scripts -> one critic full for all buildings (per-building score block, one contact sheet) -> fix/delta ... -> one final -> export (continued maker) -> debrief. One CRIT for up to 3 same-kind deliverables; split only when the images exceed the contact-sheet limit.
- **UI, one screen system:** T0 style tokens (orchestrator) -> maker v1 canvas -> pre-flight -> full -> fix -> delta -> final -> export -> debrief.
- **Mixed:** run the UI and 3D chains in parallel after a joint T0; export tasks depend on their own final pass only.
Plan 2 fix rounds (`"repeat": 2`) and delta+final per deliverable; the cap is 5 passes. Each task lists `reqs` so every R is owned (`plan.py --mission` checks).

## Order file templates (`<M>/tasks/T#.md`, one file per subagent)

### Maker v1
```
# T<n> <deliverable> v1  (mission <slug>)
Goal: <one sentence>. Stage: draft for critic pass 1 at bar <bar>.
Read only: <M>/refs/<x>.facts.md, <M>/mission.md sections Spec + Acceptance (<deliverable>). Kit API (3D): `blender_kit` functions palette_image, add cameras by name, render, tris, verify_palette, reimport; run `python3 -c "import sys; sys.path.insert(0,'<critic>/scripts'); import blender_kit; help(blender_kit)"` if you need signatures. Do not read the critic pipeline docs.
Tools: 3D -> one build.py at <M>/src/<deliverable>/ that rebuilds from an empty scene in its own file (cloud) / in its own new collection RR_<slug> in a new file (live MCP), never clearing or saving over the owner's data, using <critic>/scripts/blender_kit.py (palette atlas, named cameras, kit.render). UI -> Claude Design canvas / HTML with boards: <list>.
Must: every Acceptance line; every editable part a separate named object <Bldg>_<Part>_<Mat>_<nn>; cameras/frames exactly: <list>.
Milestones: render Cam_POV_3P + Cam_34 at 640x360 after shell, roof, details, dressing -> <M>/progress/<deliverable>-<k>.png   (3D only; if a Blender MCP is attached, build through it instead and skip milestone renders)
Pre-flight before you report: <list of kit checks / render_design.py>; fix objective failures.
Outputs: working source in <M>/src/<deliverable>/ (never inside CRIT). The orchestrator copies it to <CRIT>/round-N/ before each fix round.
Reply in <= 10 lines: what exists, pre-flight results, open doubts. No code, no narration.
```

### Maker fix (SendMessage to the same maker)
```
Round <n> fixes for <deliverable>. First copy <M>/src/<deliverable>/ to <CRIT>/round-<n>/ (frozen rollback; never edit it), then edit src/.
1. [A4-1] <part>: <problem> -> <fix with value>. Done when: <check>.
2. ...
Keep: <KEEP items>. Do not change concept or undo earlier fixes.
Re-render the same cameras into <CRIT>/pass-<n+1>/, re-run pre-flight, rebuild contact.png. Reply <= 10 lines.
```

### Scout
```
# T<n> scout <ref>
Fetch <url/path> once (Artifact read, or list type=Design then read by title). Save raw to <M>/refs/<name>/.
Write <M>/refs/<name>.facts.md (<= 1.5k tokens): units, zones/boards with numbers, palette hex, fonts, exact texts, states/behaviour, and anything ambiguous under "Needs owner". Tables, no prose.
Reply in 3 lines: saved paths, ambiguities.
```

### Exporter
```
# T<n> export <deliverable>
Read <me>/references/roblox-export.md section <3D|UI> and <M>/mission.md Spec.
Inputs: final source at <M>/src/<deliverable>/. Outputs: <M>/export/<deliverable>/.
Run the verify steps listed there; reply <= 10 lines with file list, sizes and verify results.
```

## Spawning rules
- One message per wave: spawn every ready task of the wave together.
- Record each agent id: `mission_state.py set <M> agent.<role>-<deliverable>=<id>`.
- Critics get only what `critic_kit.py build` prints. Makers never see the critic's reasoning, only your checked fix list.
- If there is no Agent tool: do makers yourself in sequence (keep build files, not your context, as the memory; hard rule 2 is waived for build files only). Critics follow SKILL.md Steps 7-8 (remote session, else self-review = UNCERTIFIED).
