# rr-ui-foundry trial: friction log

Trial: HUD mission 260927-ticket-hud turned into a component kit, plus the Create Match panel (DTU), phone and PC
renders, and a multiuse-critic pass-1 critic.md (profile B). I followed SKILL.md steps 1-4 and 6 as written. The skill
did not change during the run: its md5s at the start are in `.skill-hashes-start.txt`, and `md5sum -c` passed at the end.
Severity: high = blocks or misleads a real mission; medium = costs extra passes or tokens; low = papercut.

## High

1. **BUILD PASS can't be reached for any lobby spec that differs from the shipped example: 2 false FAILs in luatest.**
   - `ui build` reported `FAIL luatest parity` and `BUILD FAIL`. Parity itself matched 1628/1628; the two failures came from runtime checks:
     - `luatest.py:438` loads the lobby spec from `U.SKILL / "specs"` instead of the specs passed with `--specs` (`h.spec_paths`). The resize check therefore compares my package with the example's geometry: "resize phone -> PC re-lays out to the PC board (max err 257.528)".
     - `luatest.py:406-407` hard-codes the example's node ids and design: `diff_plate.Text == "HARD"` and the `diff_plate` fill = `diff.hard`. My plate follows canon `ui.rules.one_accent`: the accent fill, a child `diff_value` and a `diff_pip`. So the check fails even though the behaviour is right.
     - Screens are picked by a name substring (`"Lobby" in n`, `"Hud" in n`, `luatest.py:388-389`), so a screen with a different name skips its runtime tests without saying so.
   - Evidence: I patched those two lines in a scratch copy of the scripts only (`$SCRATCH/skillcopy`) and ran it on the same package. It gave `runtime: 43/43 passed`, `parity: 1628/1628`, `luatest: all passed`.
   - Why it matters: SKILL.md step 6 says "BUILD PASS is required before handover". As shipped, only the example spec can pass.
   - Fix: use `h.spec_paths`. Derive the difficulty check from the spec (the node whose text binds `{difficulty}` and the node whose role binds `diff.{difficulty|lower}`). Otherwise report a named SKIP instead of a FAIL.

2. **Notched phones fall below canon minimums while validate still passes.**
   - SKILL.md step 2 applies min text and targets "on the phone (warnings on other devices)", and `phone_notch` counts as another device.
   - The layout rule uses one global `s = min(areaW/844, areaH/332)`. The 59 px notch insets (`tech.ui_platform.notch_inset`) give s = 0.86, even for a 360 px centred panel that has room to spare.
   - Results with the shipped kit and specs:
     - `panel.close`, p1-p3, `diff_prev` and `diff_next` are 37.8 px, under the 44 px `tech.ui_platform.touch_target_px`.
     - HUD compact titles are 15.5 px, and the "+N MORE" chip and count badge are 13.8 px, under the 16 px of `ui.rules.min_text`. That is 8 warnings, and validate still says PASS.
   - Notched phones are most current phones, and phones are most of the audience (`identity.audience.devices`).
   - Workaround in the trial: Create Match targets are drawn at 52 design px, and in the trial kit copy the panel header is 56 and the close button 52. Result: 44.7 px on the notched phone, 0 warnings.
   - I left the HUD's 8 notched-phone warnings alone. It is the mission's critic-approved design, and changing the type sizes needs a critic pass.
   - Fix: gate phone_notch like the phone. Or give centred and pinned groups their own fit: shrink only when the group itself does not fit the area.

3. **A kit job covering 2 or more screens has no path through render and crit.**
   - `ui render` and `ui crit` take one spec each. `brief_md` describes one screen. multiuse-critic wants one `critic.md`, one `contact.png` and at most one close-up, and two specs give 20 boards.
   - To show the kit's main claim (two screens, one token set) on a single sheet, I had to do these by hand:
     - build `contact.png` and `closeups.png` with `contact_sheet.py`. On the way I learned that `--tile` must be `WxH` (a plain number crashes) and that `--max-width` also caps the height (my 856 px cap tripped the warning, exit 2).
     - crop the PC frames to true size myself.
     - merge the two `facts.md` files and rewrite `brief.md`.
   - Cost: about 7 extra tool calls and about 6k tokens.
   - The PC frame sits on the auto contact sheet at x0.31 (16 px text shows as 5 px). The task asked for PC frames, and nothing shows PC at true size unless you crop it by hand.
   - Fix: `ui render A.json B.json --out DIR` (a shared sheet with each screen's phone frame @1 and a true-size PC crop per screen), and `ui crit --spec A,B`.

## Medium

4. **The shipped example was the trial task, and it contradicts its own source.**
   - `specs/hud_tickets.json` and `specs/lobby_create_match.json` already are "HUD + Create match".
   - Step 1 says "Start from specs/". It doesn't say to copy the spec into the mission (`<M>/src/<d>/spec.json` appears only under "Inside a mission"), and it doesn't say to re-check it against the source.
   - I read the DTU artifact (6KVG6BScZk1LLJScMJScC9) and found the example differs from it and from canon:
     - DTU puts the current difficulty in the one accent ("one accent hue does all the 'this is active' work (selected count, current difficulty, Join)", now canon `ui.rules.one_accent`). It keeps the tier colours in their own strip ("never appear as chrome above").
     - The example fills the plate with `diff.{difficulty}`.
     - DTU lays out rows (label left, controls right). The example stacks each label above its controls.
   - validate cannot catch this, so a mission that starts from the example ships a screen that differs from canon.
   - Fix: make step 1 say "copy into the mission, re-read the source, diff the layout and rules", and fix the example.

5. **"Fix in the spec (or kit/)" means editing the shared skill.**
   - `kit/` lives inside the skill folder, so a kit fix made during a mission changes every screen of every later mission.
   - `RR_UI_KIT` (a per-mission kit copy) appears only in the Paths env list. Nothing says when to use it or how to promote a mission's kit change back.
   - The manifest records kit hashes but no diff against the skill's kit.
   - What I did: `RR_UI_KIT=trials/rr-ui-foundry/kit`. The diff is 3 lines in `panel`.

6. **There is no board for the component kit itself.**
   - The HUD mission had a `Kit.html` board. The skill only renders screens, and `ui list` prints template names.
   - A "reusable component kit" deliverable therefore has no sheet of template x state x skin. Not boarded anywhere: chip disabled/hover, secondary button, panel without close, all four ticket kinds side by side.
   - The critic can judge components only in context.
   - Fix: `ui render --kit` (a generated spec that uses every template in every state).

## Low

7. **A copied example spec loses its icons without an error.** The spec keeps `"icons": "../assets/icons"`, resolved relative to the spec file (`uimodel.py:561`). Outside `specs/` the only sign is a warning ("placeholder on boards"). spec.md doesn't say that leaving out `icons` falls back to the skill's icons. What I did: an `icons/` copy with 2 new icons (crew, tiers).
8. **The UIScale figure reads like a contradiction of canon.** `facts.md` and the manifest say "UIScale density Small 1, Medium 0.7649". Canon `tech.ui_platform.layout` says "UIScale 1.0 phone, 1.16 PC". 0.7649 is UIScale after s; px per design px is 1.16, which is correct. Label it "UIScale after s (1.16 px per design px)".
9. **Open questions have no dry-run route.** Step "Missing canon" says to run `bible.py add-question` but never mentions `--dry-run`, which gated runs (trials, owner-gated missions) need. The Players 1/2/3 vs `gameplay.crew.max` 6 / `launch_cap` 4 conflict exists only as a note in the example spec's `data`; `bible.py search "players chip"` finds nothing. What I did: a dry-run draft in `oq-drafts.txt`.
10. **The printed critic command uses a relative path.** `ui crit` passes CRIT through as given, so the spawn prompt reads `crit/pass-1/critic.md`. A critic agent with a different cwd can't open it. Resolve CRIT to an absolute path before printing.
11. **Every run writes `__pycache__` into the skill.** `ui.py` imports `uimodel` and writes `scripts/__pycache__/` inside the skill folder on every run. One was already there at trial start (`uimodel.cpython-311.pyc`, 02:49). Set `sys.dont_write_bytecode = True` in the entry scripts.
12. **The brief's audience line came out differently on two identical runs.** The first `ui crit` for the HUD wrote "Audience: see rr-bible identity.audience". The rerun, with the same inputs, wrote the real audience lines. The likely cause is a sibling writing canon at that moment. `brief_md` falls back without saying so; it should warn when a canon lookup fails.
13. **critic.md gets a second H1.** `render` writes `facts.md` starting with an H1 "# Facts: ...". `critic_kit.py` embeds it under "## Facts (measured)", so critic.md carries a nested H1. It's cosmetic, and it shows up on every single-spec run. Start facts.md at H2.

Not tested (no claim): `ui ingest` on the DTU page. Note that it is a presentation page with 2 panels plus a legend, and ingest has no option to pick one panel.

Total: 13 (3 high, 3 medium, 7 low).
