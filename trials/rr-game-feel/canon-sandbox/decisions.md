# Decisions

Dated, sourced decisions. `by: owner` means the owner decided or adopted it (a plan he then built on counts as adopted; the evidence is in `src`). Anything else is provisional. New decisions are appended by `bible.py decide` (from an open question) and keep their number forever. Read one with `bible.py get D-003`.

### D-001 · 2026-09-05 · Game shape: 1-6 player co-op run, one train per server, safe/risky forks, banked fare
- decision: Build Risky Rails as a 1-6 player, one-train-per-server co-op survival run: keep the loco alive, pull a physical lever at each fork (safe or risky, stacking multipliers), bank fare at stations.
- by: owner (adopted the plan; the MVP board and build follow it)
- src: PLAN, NB, WR

### D-002 · 2026-09-05 · The train never moves; the world scrolls
- decision: Static train rig at the origin; prefab track segments stream toward and past it. Falling off is handled by the company, not physics.
- by: owner (built: segment streamer done 14 Sep)
- src: PLAN, WR

### D-003 · 2026-09-05 · Four crisis systems, not eight
- decision: Firebox/coal, boiler pressure, breakdowns, passengers. Cut: cleaning, weather as a system, fuel separate from coal, integrity separate from breakdowns, walking passengers, hub, era simulations, PvP, trading, pets, gacha, rebirth.
- by: owner (adopted plan; enforced by the mechanic reviewer)
- src: PLAN, MRS

### D-004 · 2026-09-05 · The fork is a physical lever under a countdown, never a UI vote
- decision: A lever pulled left or right under a signal-gantry countdown; the cab screens show the branches. "A lever is a clip."
- by: owner (adopted plan)
- src: PLAN, MRS

### D-005 · 2026-09-05 · Passengers sit
- decision: Seated NPCs with mood states; no walking or boarding minigame.
- by: owner (adopted plan; reaffirmed in the alpha timetable)
- src: PLAN, R2A

### D-006 · 2026-09-05 · One locomotive family; eras are models and stat sheets
- decision: Locomotives differ in speed, fuel burn, capacity and durability; steam, diesel, electric, bullet are models and sounds; the coal interaction is reskinned, not re-simulated.
- by: owner (adopted plan)
- src: PLAN

### D-007 · 2026-09-05 · Never sell odds
- decision: Monetise time, status and identity only. Nothing sold changes a fork's odds; no revives, no rerolls.
- by: owner (adopted plan)
- src: PLAN

### D-008 · 2026-09-06 · Depot Lobby follows Blueprint Rev 01
- decision: 60 x 70 fenced lobby for 6 players with depot yard, zones as drawn; numbers are a starting point to nudge after Studio measurements.
- by: owner (adopted; missions build to it)
- src: BP, DEPM

### D-009 · 2026-09-10 · Biomes change only on a fork modifier
- decision: One base biome per line carries the ordinary stretches; fork-triggered biomes are the exceptions.
- by: owner
- src: RN

### D-010 · 2026-09-10 · Line 1 base biome is lowland grassland
- decision: Lowland farmland/grassland base (opposite of Dead Rails' desert); ground palette tuned for it.
- by: owner (adopted; palette tuned in Studio)
- src: RN, GP, NB

### D-011 · 2026-09-10 · Segment 512 studs, poles every 128
- decision: Segment length 512 studs; telegraph poles at a fixed 128-stud rhythm; corridor bands 0-15/15-45/45-150/150-600.
- by: owner (adopted Dimension System doc)
- src: DS, NB

### D-012 · 2026-09-13 · Thumbnail and icon formula
- decision: All thumbnail and icon work follows the playbook formula (one idea at 200 px, faces, mid-action, hazard yellow + one hue, 1-3 words top, lever or split visible, honesty; icon rules separate).
- by: owner (adopted: the thumbnail skill is built on it)
- src: LPB, THS

### D-013 · 2026-09-18 · Coal lives in two cab bins
- decision: Two coal bins against the cab's back wall either side of the doorway to the coach; no tender car, no longer engine.
- by: owner (cab plan)
- src: CB, WR

### D-014 · 2026-09-18 · Cab walls navy and charcoal
- decision: Front wall navy, side walls charcoal, instead of the suggested deep green.
- by: owner (as built)
- src: CB

### D-015 · 2026-09-25 · Alpha scope and date
- decision: Alpha departs the week of 12 Oct 2026 with 3-5 testers, steam train only; the diesel moves to the sidings after the alpha.
- by: owner (timetable issued 25 Sep, edited 27 Sep)
- src: R2A

### D-016 · 2026-09-25 · One HUD alert stack
- decision: One server-driven RemoteEvent (show by ID, clear by ID), one client script owns the stack, counts per ID; built before modifiers and supplies so they plug in.
- by: owner (timetable)
- src: R2A

### D-017 · 2026-09-25 · Fair crises for small crews
- decision: Event gaps x1.6 solo, x1.25 for 2, x1 for 3+; first event 45-75 s after departure is the windows; difficulty 1 with fewer than 3 players has one crisis at a time; no crisis needs two people.
- by: owner (timetable MUST)
- src: R2A

### D-018 · 2026-09-25 · Coins persist in ProfileStore
- decision: Coins saved in ProfileStore (PlayerData_alpha1), awarded on the server at results before the teleport home; purchases idempotent by PurchaseId.
- by: owner (timetable MUST)
- src: R2A

### D-019 · 2026-09-27 · Keep the ticket frame
- decision: Notifications keep the ticket frame (stub, punch notches, perforation, medallion, stamp).
- by: owner
- src: owner 2026-09-27, HUDM

### D-020 · 2026-09-27 · Quality bar 8/10 on every criterion
- decision: Visual work targets 8/10 on every multiuse-critic criterion (corrected from 6/10), certified by an independent critic.
- by: owner
- src: owner 2026-09-27, MEM, DEPM

### D-021 · 2026-09-27 · Separate named parts for recolouring
- decision: Every editable part is its own named object so it can be recoloured later.
- by: owner
- src: owner 2026-09-27, MEM

### D-022 · 2026-09-27 · Export both plain and atlas FBX
- decision: Ship <B>.fbx (no texture, Color3 per group via studio_setup.lua) and <B>_atlas.fbx when the atlas look is wanted.
- by: mission 260927-depot-buildings default (owner away) - provisional
- src: DEPM, REX
