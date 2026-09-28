# Feel kit: lever pull, hard brake, crate landed, crisis alarm, fare banked

Trial run of rr-game-feel (mission layout, `<M>` = this folder). Status: presets validated, exported, Luau
compiled and strict-typechecked with real Luau tools; **critic passes pending (handoff)**; **Studio test pending (owner)**.
Everything is "preview", nothing has run in Roblox.

## Moments -> preset events
| moment | events (feel.json) | who | tier | notes |
|---|---|---|---|---|
| lever pull | lever drag curve (`lever` section), `lever_detent_tick`, `lever_commit`, `lever_commit_crew`, `lever_snapback` | actor / crew | 3 (commit, signature) | OQ-031 default (drag console), OQ-006 |
| hard brake | `hard_brake` (new) | all | 3 | assumed (OQ-043 default; sandbox OQ-037 until the 2026-09-28 reconcile) and OQ-018 A |
| crate landed | `alert_crate_landed` (+ `hud_ticket_enter`) | all | 4 | roof-thump camera kick added |
| crisis alarm | `hud_crisis_arrival` inside `alert_coal_low`, `alert_pressure_high`, `alert_breakdown`, `alert_passengers_upset` | all | 2 | ticket shake fixed to deliver canon +-5 px |
| fare banked | `alert_fare_banked` (+ `hud_ticket_enter`) | all | 4 | unchanged |

## What changed vs the skill's presets (src/feel/feel.json; the skill folder is untouched)
- `hard_brake`: pitch kick 1.6 (measured 0.70 deg), FOV -4 deg (0.2 in, 0.5 hold, 1.4 out), black vignette 0.12
  (the part reduce motion keeps), 600 ms haptic judder, cue `brake_hiss`. Loudness 0.167: under the lever commit
  (0.18) and every crisis. A 0.2-trauma shake was tried and removed (about 0.1 deg, invisible).
- `hud_crisis_arrival`: 12 Hz noise measured 1.49 px against canon +-5 px; now a 5 Hz spring (damping 0.05) =
  4.62 px, matching the HUD export keyframes (-5, +5, -4, +3 px over 0.5 s). Applies to every crisis alarm.
- `lever_snapback`: noise 4 px at 14 Hz measured 0.66 px; now a 12 Hz spring = 2.74 px.
- `alert_crate_landed`: its shake measured 0.4 px; added a camera kick [1.2, 0, 0.3] = 3.9 px (tier-4 limit 10).
`validate --strict` PASS (34 events, 0 warnings); `luatest.py --presets` PASS (parity 6.7e-16, 34 events x full/RM).

## Deliverables
- `export/feel/`: `RR_FeelKit.luau` (`--!strict`, typed API for the five moments), `RR_FeelKitExample.client.luau`
  (`--!strict` wiring example), generated `RR_FeelPresets.lua`, runtime `RR_Feel.lua`, `RR_FeelMath.lua`,
  `RR_FeelDemo.client.lua`, `FEEL_SPEC.md`, `README.md` (install), `TUNING.md` + `tuning.csv` (the tuning table).
- `sheets/kit_curves_{1_lever,2_brake_crate_fare,3_crisis}.png`: curve-plot contact sheets (0.95 MP each).
- `plots/` (all timelines, easing, lever, sustain), `src/feel/preview/` (phone previews, GIFs per group and event).
- `critique-feel-{lever,crisis,info,crate,brake}/pass-1/critic.md`: critic orders ready for fresh critics.
- `tools/run_kit.sh` (whole pipeline, ~70 s), `tools/check_luau.sh [--install]`, `tools/kit_tuning.py`.
- `canon-sandbox/`: copy of rr-bible canon holding the hard-brake question (not the real bible).

## Luau verification (real tools, `tools/check_luau.sh`)
- `luau-compile --null` (luau-lang/luau latest release): all 6 files PASS. A broken file fails (checked).
- `luau-lsp analyze` 1.70.1 with Roblox types (`globalTypes.None.d.luau`) and a sourcemap: `RR_FeelKit.luau` and
  the example are clean in `--!strict`; a negative test (`"pressure"` kind, string amount) is rejected.
- The skill runtime is untyped: nonstrict analysis reports 5 diagnostics in `RR_Feel.lua` (4 look like
  new-solver refinement false positives at lines 571-583, 1 `Feel._motorOn` added to a sealed table) and the same
  5 in the demo; forced `--!strict` gives 207 / 15 / 71 / 249 errors (Feel / Math / Presets / Demo).

## Critic handoff (critic route: handoff; no Agent tool here, remote sessions cannot see these untracked files)
Spawn one fresh critic per order, on the strongest model, with only the pass folder; it writes `verdict.md` there:
`<M>/critique-feel-lever/pass-1/critic.md`, `...-crisis/...`, `...-info/...`, `...-crate/...`, `...-brake/...`
(spawn prompt printed by `critic_kit.py build`; bar 8). Then resume the maker with the verdict paths: fixes go in
`src/feel/feel.json` only (the pass-1 JSON is already kept in `critique-feel-<x>/round-1/`), re-run `tools/run_kit.sh --pass 2`.

## Owner gates
- Canon: done 2026-09-28 (bible reconcile): the hard-brake question is OQ-043 in the real rr-bible (the sandbox
  number OQ-037 is the release-version question there) and `hard_brake` cites OQ-043. Decide OQ-018 (cord) and
  OQ-043 together.
- Studio test (fidelity.md list), plus: install `RR_FeelKit` as a fourth ModuleScript in ReplicatedStorage.RRFeel;
  call `Kit.hardBrake()` when the server starts a hard stop and keep calling `Kit.setSpeed` as Speed falls.
- Sound: `brake_hiss` is reused for the hard brake; rr-soundsmith has no brake screech yet.
