# FRICTION — rr-asset-foundry trial (freight wagon family, 3 presets)

Task: wagon family generator, 3 presets (open coal, box van, crate flat), FBX + studio_setup.lua per variant, variant contact sheet, multiuse-critic pass-1 critic.md (profile A) for the coal wagon.
Format: [severity] where — what — evidence. Severity: H = wrong/blocking, M = unclear/wasteful, L = polish.

## Run log (what was done, per SKILL.md)
list --match -> show wagon -> plan x3 (no warnings) -> make x3 --renders full (20 s, 19 s, 17 s; all OK) -> read facts.md x3 -> looked at renders/34.png x3 -> variant sheet (see F5) -> crit --pass 1 (1 s) -> multiuse-critic steps 2-4 (step 2 pre-answered from canon, see F2) -> critic_kit build -> verify x3 (PASS). Re-run of the same make: "up to date", 0 s; a different plan into the same folder: refused with a clear message. quick_validate: valid.

## Friction (12)

F1 [H] scripts/fkit.py feature_px (l.432, l.440) — the A5 "key features >= 5 px at game distance" check measures the wrong thing, so it can never warn and facts.md tells the critic the opposite of the truth.
- It takes max(w, h) of a whole part's bounding box ("Largest projected side"); multiuse-critic rubric A5 and 3d-pipeline.md judge the smaller dimension. Parts hold several pieces in one mesh (WagonOpenCoal_Strap_Iron_01 = every strap on one side; WagonFlatCrates_Stanchion_Iron_01 = 4 posts, 48 tris), so even min(w, h) of the part box spans the whole side.
- Evidence, same Cam_34 at 400x225: facts.md says "Strap 102.2 px", "Stanchion 154.3 px"; per piece (mesh islands, smaller side) Strap 2.7 px, EndStrap 3.2 px, Coal Lump 4.5 px: three features under 5 px, zero warnings.
- Key match is a substring (`f"_{key}" in o.name`): "Door" also matches DoorHandle/DoorRail/DoorStrap. WagonBoxVan facts "Door 6.0 px" is WagonBoxVan_DoorHandle_Iron_02 (its smaller side: 1.5 px).
- Workaround: crit/siding_pov.py measures per island with exact `_<Key>_` tokens; pass-1/facts.md's A5 line replaced with its numbers.

F2 [H] families/wagon.py VIEW["player"] + pov() = _rolling.pov_next_vehicle — the wagon's player view contradicts canon, and the crit brief and POV renders inherit it.
- The family says "Players ride the train and never leave it: they see a wagon from the next vehicle's end platform or roof"; POV 3P/1P are rendered from a coupled next vehicle.
- Canon: gameplay.train.layout = locomotive cab + coach (measured); D-013 "no tender car"; gameplay.train.keep_on. The only canon home for wagons is the yard: world.prefabs.15 "Yard interior, sidings | 5 roads at 40 centres", world.biomes.mvp_forks "marshalling yard". bible.py search "freight" and "never leave": nothing.
- SKILL.md rule "Canon a new family needs but the bible lacks: add-question" was not applied to where wagons appear; the family also hard-codes gameplay prose instead of citing D-002.
- Workaround: crit/siding_pov.py (3P abeam, 3P 50 studs ahead, 1P abeam from the coach edge, siding at 40-stud centres; 18 s); contact.png rebuilt with the siding POV as the true-size player view; brief.md step 2 pre-answered as an ASSUMPTION with canon keys. Question prepared, NOT recorded (trial scope; owner gate):
  `python3 <rr-bible>/scripts/bible.py add-question "Where do freight wagons appear, and how does the player see them?" --option "A: yard dressing on the marshalling-yard sidings (world.prefabs.15), seen from the coach at 40+ studs while the world scrolls" --option "B: Depot Lobby yard dressing, seen on foot and close" --option "C: coupled into the crew's train (would change gameplay.train.layout; conflicts with D-013 no tender)" --default "A (only canon place for sidings; the train is cab + coach)" --src FDY --affects world.prefabs.15 --blocks "rr-asset-foundry wagon POV and critic brief"` (dry run: would be OQ-037; recorded 2026-09-28 as OQ-045).

F3 [M] make/crit — no way to pick the POV premise (no --pov / view option; pov() is family code). Any family used in more than one place (wagon on a siding vs in the lobby yard; crate on the coach roof vs the yard) needs a hand-written helper outside the skill. Evidence: the 97-line crit/siding_pov.py.

F4 [M] foundry.py cmd_crit — one POV stand only (need = pov3p, game, pov1p, 34, side, end). multiuse-critic 3d-pipeline.md: "If the camera or the world moves ..., render 2-3 POV positions along the path"; the foundry's own brief says the world scrolls (D-002).

F5 [M] SKILL.md has no route to a variant sheet for variants made one by one. `sheet` needs a batch folder (batch.json). The only documented route, `batch wagon --vary preset=open_coal,box_van,flat_crates` (dry run), would:
- rebuild all three as WagonOpenCoalV001-V003 under batch-WagonOpenCoal (named after the default preset though it holds a box van and a flat);
- use seeds 2, 3, 4 (`seed=(a.seed or 1)+i`), so the sheet would not show the delivered seed-1 variants; no --seed value gives seed 1 to every variant.
- Workaround: multiuse-critic contact_sheet.py called directly on the three variants' game/34/side renders -> sheet/wagon-variants.png (1224x753, 0.92 MP). Suggest `fdy sheet VARIANT_DIR...`.

F6 [M] foundry.py cmd_crit brief skeleton — "Purpose" is the family DESC ("Freight wagons (flat with crates, open coal wagon, box van, oval tank) on two axles or bogies."), not the one job multiuse-critic asks for. It reads as answered, unlike the step-2 line, so it would reach the critic unnoticed. Rewritten by hand.

F7 [M] plan / facts.md / studio_setup.lua list all 13 family groups for every variant. The coal wagon uses 8 (facts "parts" line) yet its Lua has Roof, Tank, Crate, Hazard and Ink GROUPS lines that recolour nothing (the owner edits Roof on a coal wagon: no effect, no message), and facts.md hands the critic 5 colour tokens that are not on the model. Trimmed by hand in pass-1/facts.md. (The shared 13-cell atlas is fine.)

F8 [L] scripts/forge.py Cam_Side/Cam_End — the ortho frames fit the asset's bounds only; the 5-stud avatar (at hi+2.5) is cut to a sliver at the right edge of the side and end views (variants' side.png/end.png, contact tiles 6-7): no scale reference in the only views where lengths read true.

F9 [L] forge.py l.115 — back faces are checked from Cam_34 and Cam_POV_3P only; the 1P POV, side and end are not (3d-pipeline.md: "Run it on every POV and construction camera"). The siding cameras were checked by hand: 0.

F10 [L] `list --match "freight wagon open coal box van crate flat"` returns building, prop, wagon in alphabetical order; the wagon (most hits) comes last. No ranking or scores.

F11 [L] `show wagon` prints "open questions: OQ-025"; plan, facts and README label OQ-025 and OQ-030 (SKILL.md: OQ-030 on all rolling stock).

F12 [L] Critic hand-off: SKILL.md says "follow multiuse-critic from its step 2" but not what to do when the owner can't be asked (subagent or overnight mission). critic_kit build does not refuse a brief still saying "Step 2 NOT answered", so the skeleton line would go to the critic verbatim. multiuse-critic's fallback (write the assumption, repeat it when presenting) was used.

## Worked
- list/show/plan made the family, params, canon keys and statuses clear in 3 calls; plan resolved every token with no warnings.
- make: 16-19 s per variant with full renders on 4 cores (the SKILL's "about 5 s plus 15-30 s" is right); every objective check passed; output capped at 5 lines.
- Per variant: plain + atlas FBX, studio_setup.lua (luaparse ok, bible check PASS), README with Studio steps and "Studio test pending (owner)", FBX reimport size check, OQ labels. verify: PASS x3.
- plan.json caching: an identical make is "up to date" in 0 s; a different plan into the same folder is refused with a clear fix.
- crit: pass folder in 1 s (renders reused), and it printed the exact critic_kit command; it never scores.
- Sibling discovery (rr-bible, multiuse-critic) worked with no env vars.
