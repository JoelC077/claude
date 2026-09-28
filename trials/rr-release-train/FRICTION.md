# rr-release-train trial friction: v0.4.0 Ticket HUD + depot buildings

Trial 2026-09-28: full dry-run release following SKILL.md step by step (status, config, init, collect, mark,
attach, version, changelog, notes, notes-check, stamp, re-attach, gate, plan, publish dry run, rollback dry run).
Cloud session, owner away, no Studio, rr-exploit-guard not built yet. Outputs: `v0.4.0/` (README there).
Severity: HIGH = a gate passes or stays silent on a real problem, or a step cannot be done right; MED = misleading
or weak output; LOW = polish or token waste. 20 items: 5 HIGH, 9 MED, 6 LOW.

## HIGH
1. **G9 misses placeholder asset ids.** The shipped HUD module has `Hud.IconSheet = "rbxassetid://0"` and
   `Hud.HazardTile = "rbxassetid://0"` (NotificationHud.lua:17-18; ASSETS.md: "asset ids are placeholders until
   you do this"; canon `assets.missions.hud_package` says "icons need upload"). G9 only looks for instances named
   `PLACEHOLDER*` (gates.py:492, placefile.py:400), so the headline feature would ship with blank icons and G9 said
   nothing. Needs: flag `rbxassetid://0` / empty asset ids in scripts and props.
2. **G9 misses a demo script left in the build.** `StarterPlayer/StarterPlayerScripts/NotificationDemo.client.lua`
   (ASSETS.md: "Studio test; delete for release") fires every alert type at every player on join. Extracted by
   attach, not flagged by any gate. Needs: flag scripts named `*Demo*`, `*Test*` (non-spec), or listed as
   "delete for release" in the shipped missions' export notes.
3. **G10 filters open questions by keyword, not by what ships.** It listed OQ-019 (marketing budget) and OQ-024
   (launch player cap) but not OQ-001 (HUD skin: `blocks: final HUD export`; canon default is C hybrid, this build
   ships A heritage brass) nor OQ-015 (Main Hall: where, and does it stay?; `affects: assets.missions.main_hall`).
   Both touch C-2/C-1 directly. Needs: also match OQs whose `blocks`/`affects` touch in-build missions' canon keys
   (`assets.missions.*`, `ui.hud.*`, `world.lobby.*`).
4. **Owner-named version vs channel has no path.** Task/owner named "v0.4.0"; history is empty so `rel version`
   proposed 0.1.0-alpha.1; `--set 0.4.0` only warns "does not carry the 'alpha' tag" and G1 WARNs. SKILL.md says
   "`--set` only when the owner names one" but not what to do when the named version conflicts with OQ-037
   default A (closed alpha = 0.1.0-alpha.N, 1.0.0 at soft launch) or implies earlier releases (0.1-0.3) that
   history.json does not know. No way to seed history ("last shipped 0.3.x"). Needs: one line in step 4 (ask:
   0.4.0-alpha.1 or record the scheme via `bible decide OQ-037`), and a `version --after X` / history seed.
5. **G2 passes on the agent's word.** `mark --in-build yes` needs no owner citation (unlike approve/evidence), so
   G2 PASSed "2 in build" although the owner never confirmed either mission is in Studio (I marked them from the
   release name, trial assumption). SKILL.md step 3 says ask the owner, but nothing records that it happened.
   Needs: `mark --in-build yes --via "chat DATE"` stored and shown in GATES.md G2, or G2 WARN when absent.

## MED
6. **notes-check FAIL still writes the "clean" files.** Probe (scratch copy, bad notes): FAIL with 7 errors, yet
   `PATCH_NOTES.md` was rewritten with "Flight or Die edition" (mtime same second). SKILL.md calls these the
   clean outputs the owner posts. Needs: write to a temp name, promote on PASS only.
7. **Changelog is dated and "released" during a dry run.** `changelog --apply` prepended `## [0.4.0] - 2026-09-28`
   to CHANGELOG.md on draft day; alpha is the week of 12 Oct (`release.dates.alpha`). No `[Unreleased]` stage,
   nothing re-dates it at publish, and `abandon` is not said to remove it. Needs: write `[Unreleased]` (or keep it
   in next/) and stamp the date at publish/record.
8. **G4 says "names and numbers clean" but HUD numbers drift from canon.** NotificationHud.lua:44 `gap = 6,
   compactHeight = 40` vs canon `ui.hud.gap_px = 8`, `ui.hud.ticket_size` "compact older tickets 44 tall";
   `bible check` PASS (it does not map Luau table fields to ui.hud.* keys). Canon itself notes "(remake used 6)",
   so it is known drift, but G4's wording gives false comfort. Cross-skill (rr-bible check); G4 should say
   "numbers checked: N matched" so zero coverage is visible.
9. **G8 fix is wrong when the standing is below bar.** HUD standing 6/8 (critique-hud) with the last fix still
   pending (commit 2ee7f87 "HUD at 7/10 pending last fix"). G8's fix says "one independent --kind final pass"; a
   final pass on unfixed work re-confirms 6. Needs: below bar -> "finish the fix loop in rr-mission-control, then
   a final pass"; only "certify" when self-scored at bar. (No Agent tool in this session, so no critic could run
   here anyway; G8 is advisory in alpha.)
10. **G9 audio extra check is a false WARN.** rr-soundsmith `sound validate --release` "FAILED" on library-level
    feel-parity notes ("ui_button_press exists in rr-game-feel without a cue") though the places hold 0 Sound
    instances; GATES.md truncates it mid-sentence ("... there to"). In live this blocks. Cause: the preset cmds
    take no release input (`sound.py validate --release`, `vfx.py budget --tier phone` in presets/gates.json), so
    they judge the sibling's library, not this build. Needs: pass `next/places/*/audit` to them; full detail lines.
11. **SMOKE.md change checks are generic.** S6/S7 = "C-n works as the patch notes say: <title>". The missions hold
    concrete checks (ASSETS.md "Watch: UIStroke on rotated stamp, hazard tile scale, +N MORE chip position after
    UIScale"; depot: trim non-collide, recolour groups). Needs: pull each in-build mission's "watch"/done-when lines
    into its smoke row (e.g. "5 alerts at once: +N MORE chip beside the top ticket, icons not blank").
12. **ROLLBACK.md has no target on a first release.** "Target: none recorded"; points to Version History but never
    asks the owner to write down each place's current live version number before publishing, so under pressure
    nobody knows which version to restore. Needs: a pre-publish step (or `record --baseline`) in PUBLISH_PLAN.md.
13. **Notes brief is not enough on its own.** SKILL.md step 6: "Read only the brief"; notes.md also says "Read
    NOTES_BRIEF.md only", yet the headline template (`# Risky Rails <ver>: <headline>`), the optional Management
    notice line and the good/bad examples live only in references/notes.md. I had to read both. Needs: put the
    6-line template and one good/bad pair in the brief; then notes.md is only for edge cases.
14. **Releases root is ambiguous in a Studio-only project.** Default `<git top of cwd>/releases` = the JARVIS
    tooling repo root; the builder's earlier trial already has a 0.1.0-alpha.1 in flight at
    `trials/rr-release-train/releases/next`, which `status` would silently resume if pointed there. SKILL.md does
    not say where releases live when there is no game repo. Needs: one line (e.g. `<missions root>/../releases`,
    or set `$RR_RELEASES_ROOT` once) and `status` naming the release's opener/date.

## LOW
15. `rel notes` prints the whole brief (25 lines) and writes it; reading the file per SKILL.md doubles the tokens.
    Print the path + counts only.
16. `rel config` echoes the full config.json on every call (3 calls = 3 dumps in the first-time setup).
17. `mark --note` is shown to the notes writer as "wording hint"; SKILL.md only says "retitle ... (`--title`,
    `--note`)". My first provenance note ("TRIAL ASSUMPTION: owner not asked") leaked into NOTES_BRIEF.md. Say
    "--note = player wording hint" and give a separate internal note field.
18. Missions always arrive as `Added`; the HUD was a remake (`Changed`) and needed a manual `--section`.
19. Publish dry-run blockers list approval/key/host but not the gate verdict behind the missing approval (NO-GO:
    G5, G6). One line "approval impossible until gate GO (G5, G6)" would save a status round-trip.
20. G7 extra check reports rr-vfx-lighting budgets for effect sets (boiler_fail, derail) not in this build; noise
    in GATES.md.

## Environment, not skill (for the record)
- No Studio: place files are stand-ins built by `v0.4.0/make_places.py` from the real mission exports; G4's
  off-palette #2A6040 and G7's sizes describe the stand-ins, not the game.
- rr-exploit-guard has scripts but no SKILL.md/CLI yet: G5 PENDING, reported correctly.
- apis.roblox.com blocked (CONNECT 403) and no key: publish refuses live, as designed. `--live` was never passed.
