# mission.md template (steps 2-3)

`mission.md` is the human-readable contract; `state.json` (mission_state.py) is the machine state. Keep mission.md under ~150 lines: facts live in `refs/*.facts.md`, renders in `critique-*/`, and are referenced by path only.

Worked examples, filled in for the owner's two real prompts:
- `examples/mission-p1.md` (3D: main hall + depot, Blender, bar 8) with `examples/plan-p1.json`
- `examples/mission-p2.md` (UI: notification HUD remake, Roblox export, 10 steps) with `examples/plan-p2.json`
Copy the closest one and edit; don't write from scratch.

```markdown
# Mission <YYMMDD-slug>
Objective: <one sentence: what, how many, to what bar, delivered as what>
Kind: 3d|ui|mixed · Profile: A|B · Bar: 8 (owner said X; clarification C2) · Cap: 5 passes/deliverable
Env: <cloud|cowork|local>; blender=<mcp|bpy-headless|none>; agents=<yes|no>; design-critic=<installed|not>

## Source prompt
See prompt.txt (verbatim) and lines.md (L/C ids). Never edit either.

## Requirements
| id | owner words | requirement | type | source | status | done-when |
|---|---|---|---|---|---|---|
| R1 | "..." | ... | deliverable | L2,L3 | open | <checkable> |
| R*9 | (implied) | ... | derived | L6 | open | ... |
| R10 | "Thank you" | - | noise | L7 | noise | - |

## Decisions and assumptions
A1 <decision> (default|owner|profile) - repeat at debrief
Q1 <question> - default: <x> - answer: <pending|...>   (max 3, all in the readback)

## Spec
### <Deliverable>
Parts/boards · dims · palette · states · exact texts · fidelity: exact|inspired per ref
Cameras / frames: <fixed list; progress renders use these>

## Acceptance (rubric-injected; the maker gets this as a checklist)
<per deliverable, see lists below + owner-specific done-whens>

## Needs owner / placeholders
## Next action
<exact next command, so resume is trivial>
```

## Requirement types
`deliverable, reference, quality, process, tool, comms, export, editability, style-keep, style-licence, constraint, context, derived, noise`.
- Every non-noise L/C line is cited in some row's `source` cell, one id at a time, no ranges (script-checked; prose mentions do not count). Derived rows are for technical constraints only (scale, perf, format); never add an owner-visible feature as a default. Implied needs are `R*n`, type `derived`, with the reason in `requirement`.
- Clarifications supersede: keep the old row with status `superseded` and cite the C line in the new one.
- Status flow: open -> planned -> done -> verified (evidence path), or fallback (nearest real alternative, reason), waived (owner said), blocked (reason). `intake.py cover --final` accepts only final statuses.
- Politeness is noise. "Have fun" / "a style you deem fitting" = style-licence (decide, don't ask).

## Rubric-injected acceptance (copy the relevant list into Acceptance)
Profile A (3D, criteria A1-A7 from `<critic>/references/rubric.md`):
- A1/A5 a clear focal point readable at game distance (400x225 render: key features >= 5 px)
- A2 5-stud avatar stand-ins; doors >= 7 wide x 9 tall studs; steps and rails at Roblox scale
- A3 <= 10k tris per MeshPart (cap 20k); no hidden interior faces; `backfaces` clean from every camera
- A4 one 256px palette atlas, 32px cells, `verify_palette` passes; weathering from palette cells, not noise textures
- A6 Risky Rails house style (`rr-profile.md`); A7 no floating parts, trims meet, pivots sane
- Every editable part a separately named object (`<Bldg>_<Part>_<Mat>_<nn>`); CanCollide plan; reimport in studs
Profile B (UI, criteria B1-B6):
- B1 one job per element; most urgent state reads first
- B2 body text >= 12 px and titles >= 16 px at 844x390 true size; AA contrast 4.5:1 body, 3:1 large
- B3 clear of Roblox topbar (top 36 px), thumbstick (bottom-left) and jump button (bottom-right, ~ 120x120 from corner) zones; Scale + UIAspectRatioConstraint plan stated
- B4 palette from the design tokens; state colours distinct for colour-blind (shape/icon backup)
- B5 Risky Rails house style; kept elements the owner named are preserved exactly
- B6 motion defined (enter/leave/attention), all states rendered (overflow, compact, merge)

## Brief.md from the mission (per deliverable)
```
# <Deliverable name>
Purpose: <the one job, from Objective + R deliverable row>
Audience: Risky Rails players (Roblox, 13+ mixed), owner as art director
Player view: <from rr-profile + Q answers: 3P eye 9.5, FOV 70, ... | phone landscape 844x390 true size, Scale>
Stage: draft
Fixed constraints: <from Spec + Acceptance: dims, palette, tri budget, must-keep parts/texts>
Owner worries / already decided: <A-lines, Q answers, placeholders>. step 2: pre-answered
```
