# multiuse-critic: dry test of the new critic flow

**Subject:** the Depot Ticket UI artifact, a "Create match" panel (Profile B, UI). There was no 3D render in reach of this cloud session, so the 3D helpers (`scripts/blender_kit.py`) were tested separately, in Blender 5.0 on a test scene.

**Assumed owner answers** (step 2 was skipped for the test):
- the panel is a phone ScreenGui, landscape 844×390, at 85% of the screen height
- the accent is teal, which the critic had recommended

**Run at:** the session's max thinking effort, the most expensive setting.

## The loop: 6/10 → 8/10 on every criterion

| pass | critic | scores | tokens reported | new this pass | tool calls | min |
|---|---|---|---|---|---|---|
| 1 full | fresh, strongest model | B1 7 · B2 7 · B3 7 · B4 8 · B5 7 · **B6 6** | 139,670 ⚠ | 139,670 | 3 | 13.4 |
| 2 delta | same critic, continued by SendMessage | B1 8 · B2 8 · B3 8 · B5 8 · B6 8 | 190,262 ⚠ | 50,592 | 3 | 7.4 |
| 3 final | fresh, strongest model, verify + full rubric | all 8, no drops | 89,953 | 89,953 | 3 | 5.9 |

In total: 280,215 new critic tokens and 26.7 critic minutes. Every critic opened critic.md and the contact sheet together, and answered in its 2nd message. Under the merged-final rule, pass 2 would itself have been the final pass, because round 1 fixed every blocker: that's 2 passes, about 230k tokens.

## The cheaper-model delta, tested and rejected

Same pass-2 files, a fresh critic on Sonnet:

| | continued strongest critic | fresh Sonnet critic |
|---|---|---|
| tokens reported | 190,262 (50,592 new) | 108,751 |
| minutes | 7.4 | 8.5 |
| thinking | ~47k | ~50k |
| verdict | all five at 8; 3 new, real, measured nits | three 9s "below 10 because none"; no new issues |

The two agreed on every fix, but the Sonnet critic was lenient and missed what the strongest critic caught. It didn't think less or run faster either.

## Where a pass's tokens go

The protocol held, yet pass 1 still cost 140k:

| part of the critic's context | tokens |
|---|---|
| base: a general-purpose agent's tool definitions, before reading anything | ~48k |
| critic.md plus the contact sheet | ~8k |
| thinking | ~80k |

- **Continuing a critic** carries its whole context forward, earlier thinking included, as cheap cache reads. The ledger now splits "new this pass" from "reported".
- **Adding "keep your reasoning proportionate" to critic.md** cut the final pass's thinking to ~37k. That's an uncontrolled comparison, but a strong signal.
- **A lean `design-critic` agent** (Read tool only, an effort setting, a turn limit; `agents/design-critic.md`) targets the rest. It's untested here: this session blocked installing an agent into Claude Code's config. It's the owner's opt-in.

## 3D helpers (`blender_kit.py`), tested in Blender 5.0

- The palette atlas is pixel-exact (checked against the PNG). `verify_palette` passes a clean mesh and catches a planted face spanning two cells.
- POV camera: eye 9.5 studs above the floor, vertical FOV exactly 70°.
- The `flat` diagnostic render outputs exact palette hexes, and the materials are restored afterwards.
- `backfaces`: a plane facing the camera reports none; flipped, it reports 312 px.
- The FBX round trip matches the build (ratio 1.00), and a metre/stud mix-up is flagged as 3.57×. The re-import leaves the .blend clean.
- The Studio OBJ import bakes the 90° X rotation, and the Lua command-bar script is generated.
