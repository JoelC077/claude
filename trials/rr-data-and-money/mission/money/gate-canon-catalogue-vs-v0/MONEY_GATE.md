# Money gate: FAIL

Catalogue 26be9e0bde975912, checked 2026-09-28. FAIL blocks release; HOLD needs the owner (and risky-rails-mechanic-reviewer for gameplay items); only the owner waives.

| severity | product | rule | finding | canon |
|---|---|---|---|---|
| FAIL | fare_pack_l | M07 | 20,000 fare > 10 runs of earnings (7,224; run fare 722 from sim, assumed fares) | `economy.passes.fare_packs` |
| HOLD | express_depot | M01 | sells access: not named in D-007 (time, status, identity); owner confirms it is time or identity in practice | `D-007` |
| HOLD | private_server | M01 | sells access: not named in D-007 (time, status, identity); owner confirms it is time or identity in practice | `D-007` |
| HOLD | toolbelt | M01 | sells convenience: not named in D-007 (time, status, identity); owner confirms it is time or identity in practice | `D-007` |
| HOLD | toolbelt | M03 | changes gameplay (gameplay.supplies.hand): run risky-rails-mechanic-reviewer, then the owner decides | `gameplay.supplies.hand` |
| FUTURE | auto_stoker | M01 | [post_launch, not in this release] sells power: D-007 allows time, status, identity only | `D-007` |
| FUTURE | auto_stoker | M04 | [post_launch, not in this release] one buyer changes the whole crew's run: pay-to-win in co-op | `identity.pillars.four_systems` |
| INFO | auto_stoker | M13 | price 449 R$ is proposed in canon (economy.passes.auto_stoker), not decided | `economy.passes.auto_stoker` |
| INFO | double_fare | M13 | price 299 R$ is proposed in canon (economy.passes.double_fare), not decided | `economy.passes.double_fare` |
| INFO | express_depot | M13 | price 199 R$ is proposed in canon (economy.passes.express_depot), not decided | `economy.passes.express_depot` |
| INFO | fare_pack_l | M13 | price 599 R$ is proposed in canon (economy.passes.fare_packs), not decided | `economy.passes.fare_packs` |
| INFO | fare_pack_m | M13 | price 249 R$ is proposed in canon (economy.passes.fare_packs), not decided | `economy.passes.fare_packs` |
| INFO | fare_pack_s | M13 | price 99 R$ is proposed in canon (economy.passes.fare_packs), not decided | `economy.passes.fare_packs` |
| INFO | first_class | M13 | price 399 R$ is proposed in canon (economy.passes.first_class), not decided | `economy.passes.first_class` |
| INFO | livery_high | M13 | price 199 R$ is proposed in canon (economy.passes.liveries), not decided | `economy.passes.liveries` |
| INFO | livery_low | M13 | price 49 R$ is proposed in canon (economy.passes.liveries), not decided | `economy.passes.liveries` |
| INFO | private_server | M13 | price 150 R$ is proposed in canon (economy.passes.private_server), not decided | `economy.passes.private_server` |
| INFO | supplies_robux | M01 | sells survival: D-007 allows time, status, identity only (hidden per OQ-010 default; keep it hidden) | `D-007` |
| INFO | toolbelt | M13 | price 149 R$ is proposed in canon (economy.passes.toolbelt), not decided | `economy.passes.toolbelt` |
