## 1. Depot Lobby Blueprint (Rev 01, 06 Sep 2026)
Title: "Depot Lobby — Layout Plan" + "Floor Paving Plan". Footer: "ENVIRONMENT REFERENCE — NOT FOR FINAL DIMENSIONS".

### Global facts
- Units: studs (1 stud ~ 0.28 m). Grid square = 5 studs. Occupancy 6 players max; "small hub, don't over-build".
- Numbers are a starting point; nudge once fence-panel / station footprints measured in Studio.
- Boundary = palisade fence itself (mix bent-bar / vine-overgrown panels); NO separate architectural wall.
- North (up, -y in plan) = direction from spawn to join-queue platform.
- Coordinates below: plan x right (0 = west), y down (0 = north), studs.

### Zones (x, y, w, d)
| # | Zone | Rect / pos | Size | Notes |
|---|---|---|---|---|
| - | Main lobby (fenced) | 0,0 | 60 x 70 | |
| - | Depot yard (dashed) | 10,70 | 40 x 20 | south extension |
| 1 | Spawn | (30,60) | - | faces north, station/depot behind |
| 2 | Central path | 26,15 | 8 x 45 | cracked paving strip spawn -> queue |
| 3 | Lamp posts | (23,28)(37,28)(23,47)(37,47) | 4 | iron railway lanterns, ~19 studs apart |
| 4 | Game info board | 1.5,32 | 3 x 8 | west wall; timber/iron frame, peeling notices, one vine |
| 5 | Classes pad | 44,30 | 12 x 12 | placeholder, post-launch |
| 6 | Boundary fence | perimeter | - | palisade, bent-bar/vine variants |
| 7 | **Depot building** | 18,76 | **24 x 14** | **two-gable stone station house, front faces the yard (north, toward display track)** |
| 8 | Display track | 14,70 | 32 x 6 | equipped train sits here; gravel ballast |
| 9 | Foliage + clutter | yard corners | - | moss, ivy, crates, drums; heaviest near building |
| 10 | Join-queue platform | 20,5 | 20 x 10 | main CTA, boldest lighting + signage |

### "Main hall" vs "depot" (interpretation needed)
- The blueprint names only ONE building: the **Depot building / station house (24 x 14, two-gable, stone)**. There is no zone called "main hall". Candidates: (a) the "main lobby" 60x70 fenced area is the "main hall" (but notes say no walls - it is open-air), or (b) the owner means a building not in this blueprint. No heights, wall thickness, roof pitch, windows/doors or interior given anywhere. Flag to owner / decide with stated assumption.

### Materials / colours (light theme tokens; dark theme alternate)
- Paving: clean walkway #f7f3e6 (path, platform, spawn approach); weathered concrete #cabb8a (default yard slab); cracked/lifted slab #ad9968 (edges/corners only); grass through seams #6d7d43 (fence line & corners); gravel ballast #b7a17a (under display track).
- Paving rule: routes clean; decay (cracks, lifted slabs, grass) within ~8 studs of fence and yard corners, dappled checkerboard of cracked vs grass 5x5 slabs. Slab = 5x5 studs.
- Named materials: stone (depot), iron (lanterns, info-board frame), timber (info board), palisade fence (bent-bar, vine), crates, drums, moss, ivy.
- Sheet palette (drawing only): ink #1f3b57, accent #b1502b, paper #f2ecda.

---
