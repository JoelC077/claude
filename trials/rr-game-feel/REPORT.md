# rr-game-feel fix report (2026-09-28)

I couldn't write `/home/user/claude/trials/rr-game-feel/REPORT.md`, because the harness blocks subagents from writing report files. This text is the report content.

Inputs were FRICTION.md (17 items) and two independent reviews. All high and medium findings are applied, plus the cheap low ones. The exceptions are listed under "Rejected / partial".

- **Review scores:** [7, 6.5]
- **Package:** `/home/user/claude/dist/rr-game-feel.skill`
- **Validator:** quick_validate says "Skill is valid!".
- **Tests:** selftest passed all 61 checks; luatest passed; `validate --strict` passed (33 events, 0 errors, 0 warnings).
- **Cleanup:** no `__pycache__` is left in the skill or the trial folder.
- Nothing has run in Roblox Studio.

## Changes (skill at /home/user/claude/rr-game-feel)
- **Knobs now mean what the player sees.**
  - Punch `amp` and camkick `angles_deg` are now the peak the player actually gets. The spring is divided by its own peak, with identical code in Python (`peak_gain`) and Lua (`M.peakGain`).
  - Existing presets were converted so their motion looks the same as before.
- **Canon numbers bind to a phrase.**
  - A canon reference can carry `"match": "+-5 px"`, the exact phrase in the fact's value or note that holds the number.
  - A number without a phrase gets a warning when the fact contains several numbers.
  - A swapped pulse range (min above max) is an error.
  - The flash limits and `hitstop_ms_max` are now bound to `av.feel.flash_limit` and `av.feel.hitstop_local`. SKILL.md cites those keys instead of restating the numbers.
- **Visibility checks.** validate warns about:
  - a shake too weak to see on a phone;
  - a pixel punch below `punch_px_min`;
  - a camera kick whose frequency is outside `camkick_freq_hz`.
- **Camera directions.**
  - The convention is documented: + pitch looks up, + yaw turns left, + roll tilts left.
  - validate checks the pitch sign against the intent's wording (forward, nod, back), and that side-following kicks move "toward the side".
  - Found while fixing: the preview drew yaw mirrored compared with the runtime, and `lever_commit` turned the view away from the pulled side. Both are fixed.
  - `depart` and `station_arrive` had their pitch signs inverted. Both are fixed.
- **Loudness hierarchy.**
  - Loudness now includes the HUD alarm: pixel shake weighted by its length, halo pulse depth, and stamp scale travel.
  - No event may be louder than the median of any higher tier. Deliberate exceptions carry a reason in `quiet_ok` or `loud_ok`.
  - `show`, `facts.md` and `tune` list every higher-tier event an event outshouts. The trial's false "quieter than every crisis" claim can't be written from memory again.
- **Reduce motion.**
  - Every event must keep a channel that every device has: something visible, or a sound cue.
  - A haptic alone fails, because PC has no haptics.
  - An event whose meaning is carried outside the feel channels says what carries it in `rm_reads`.
- **Open questions.**
  - validate warns when a cited OQ's title shares no word with the event that cites it. This is what catches the OQ-037 collision.
  - `OQ-TBD-<slug>` is a NOTE for the owner, not an error.
  - SKILL.md gives the full `add-question ... --dry-run` command followed by `lint`. It tells runs not to number questions themselves during trials or parallel work.
- **Runtime (RR_Feel.lua).**
  - The lever is two-way: the finger travel is signed, and the detent tick fires at `lever.notch`, before the commit.
  - A new `ctx.fork` (junction id) re-arms the lever. `leverReset` is now documented.
  - A flash that ends during a frame stall no longer leaves the vignette stuck on screen.
  - The FOV kick is applied as a change on top of the current FOV, so a FOV set by a fail camera survives.
  - New `Feel.playFor(name, actorUserId, ctx)` plays each event only on the clients its `who` names.
  - `_motorOn` is now a local. The runtime shows 0 non-strict diagnostics, down from 5.
- **Strict-typed Luau.**
  - `build` now generates `RR_FeelTyped.luau` (`--!strict`), which type-checks event names, roles, the context table and settings.
  - The syntax gate is luau-compile, else luaparse, else SKIP. SKIP is reported as "syntax unchecked", never as a false FAIL.
  - After that, `build` runs a luau-lsp strict typecheck.
  - New `scripts/luau_check.py` has `--status` and `--install`, pinned to luau 0.740, luau-lsp 1.70.1, and the type definitions at that tag.
- **HUD wiring (README).**
  - A one-writer rule, with exactly what to delete in NotificationController.
  - `haloRed` opacity must be 1.
  - The count-up uses `Hud.formatCash`.
  - Also covers two-way lever wiring, the `Kit.useFeel` hook for rr-ui-foundry, and live tuning.
- **New commands.**
  - `tune` writes TUNING.md and a CSV with correct ranges, canon locks and measured results.
  - `set PATH=VALUE` edits the presets, keeping canon bindings and the house layout. `fmt` reformats the file.
  - `changed --since` names the groups to re-preview and re-critique.
  - `preview E1,E2 --name` makes one set so a single critic sees all the moments, with the lever drag curve in its close-ups.
  - `preview EVENT` now writes to `ev_<event>/` instead of overwriting the group folder.
  - `plot --compare` reads raw Studio Output lines and exits 2 when it finds no curves.
- **Hygiene.**
  - `--presets` is accepted after the subcommand, and every command prints which presets file it used.
  - Export headers name the source file.
  - The scripts never write `__pycache__`, and usage errors exit 2.
  - The dead `fov` branch is fixed.
  - The matrix FOV column shows the sign.
  - The critic brief no longer repeats the stable-train line.
  - Sound cue names are checked against rr-soundsmith. A missing sibling skill is a NOTE, not a failure.
- **Preset fixes.**
  - `hud_crisis_arrival`: a 4 Hz spring whose first move is 5 px to the left, damping 0.05. Its note says it approximates the HUD export keyframes.
  - `lever_snapback`: now a visible 3 px wiggle.
  - Crate landed: the invisible shake is replaced by a −0.7° camera kick.
  - Lever and crew kicks: yaw and roll corrected.
- **Docs.**
  - SKILL.md (126 lines) adds a moments-to-events map, the critic route, a re-critique-only-changed-groups rule and the presets rule.
  - schema.md adds "Adding an event", the sign conventions and the visibility rules.
  - fidelity.md and design-notes.md are refreshed.
- **Trial tools.** `run_kit.sh` now sets PYTHONDONTWRITEBYTECODE. `check_luau.sh` uses pinned versions, and its `--help` no longer prints a code line.

## Re-trial (in /home/user/claude/trials/rr-game-feel/retrial)
- **Old presets, new gates.** Run on the trial's original presets, the new gates flag every issue the reviewers raised: OQ-037, the brake's +1.6 pitch, the invisible crate shake, the lever yaw, the hard brake beating most crises, and unbound canon numbers.
- **Corrected mission.** The hard brake kick is now −0.7° and cites `OQ-TBD-hard-brake` (recorded as OQ-043 on 2026-09-28; the retrial files now cite OQ-043).
  - `validate --strict` passes.
  - `show` states the truth: the brake is louder than windows_smash and hud_crisis_arrival.
- **Previews and critic.** One set preview and one critic order of about 3.3k tokens cover all five moments; the trial needed five critic orders.
- **Build.**
  - `tune` produced 136 knobs.
  - `build` passed: luau-compile on all six files plus the strict typecheck.
  - luatest passed on the mission presets.
- **Typed wiring example.** `KitExample.client.luau` (two-way lever with fork, HUD adapter, `playFor`) passes the strict typecheck. A caller with a wrong event or role name fails it; that case is in the selftest.
- **Old bugs reproduced.** The new luatest checks fail on the original runtime (vignette stuck at 0.782, FOV back at 70) and pass on the fixed one.

## Rejected / partial (with reason)
- **Review 2, reduce motion ("haptic and cue shouldn't count"): partly done.** Canon `av.feel.reduce_motion` names "colour, haptics or sound", so a sound cue still counts. A haptic alone no longer counts.
- **Review 2, `feel ingest`: deferred.** It needs a Lua table parser. Live tuning is documented, and `feel set` copies numbers back one command per knob.
- **Review 2, haptic ramp as the finger nears the detent: not done.** The notch tick before the commit already gives the "felt before the commit" cue. A ramp would need per-frame haptic updates from leverDrag.
- **Review 1, "4 Hz" shake: taken with a correction.** The HUD keyframes are 0.1 s apart (5 Hz lobe spacing), but there are 4 lobes ending at rest. I used 4 Hz with the first move 5 px to the left, and the note says "approximates".
- **Review 1, ship a HUD adapter module: not shipped.** It would hard-code the internals of the HUD package. The README's deletion list and the re-trial's `onTicket` show the pattern instead.
- **Old trial outputs (KIT.md, export/): left as the historical record.** The corrected versions are in `retrial/`.
- **Event tiers: unchanged.** rr-soundsmith's tier parity depends on them.
- **rr-soundsmith's cue suggestions (`ui_click`, `ticket_chime`): not applied.** That parity needs both skills to change together.

## Owner gates
- **Record the hard-brake question.** Done 2026-09-28 (bible reconcile): OQ-043, default A; the trial and retrial presets cite it.
- **Studio test** (the list in fidelity.md): pitch and yaw directions as they feel, HUD wiring with the controller's own motion removed, and haptics on a real phone.
- **Critic pass:** spawn a fresh critic on `retrial/critique-feel-kit/pass-1/critic.md` (handoff route).

## Files
- Skill: `/home/user/claude/rr-game-feel/` (new `scripts/luau_check.py`)
- Package: `/home/user/claude/dist/rr-game-feel.skill`
- Re-trial outputs: `/home/user/claude/trials/rr-game-feel/retrial/` (`src/feel/feel.json`, `src/feel/preview/kit/`, `critique-feel-kit/pass-1/critic.md`, `export/feel/`)

## Independent certification after fixes
Fresh critic on the fixed re-trial: overall 4 ({'G1': 4, 'G2': 6, 'G3': 7, 'G4': 7, 'G5': 7, 'G6': 6}); 9 blocks-8 issues. Verdict saved at /home/user/claude/trials/rr-game-feel/retrial/critique-feel-kit/pass-1/verdict.md.
