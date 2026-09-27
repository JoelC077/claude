# Facts: Risky Rails Ticket Notifications (Design KNNSWzQoyjGpBDfM7ciGpo, v1790511614-3133). Treated as the prototype: owner link unopenable, owner title not listed. Raw: /home/user/claude/.mission-work/refs/ticket-notifications/project/

## 2. HUD: "Risky Rails Ticket Notifications" (Design artifact)
Boards (canvas.json): PC 1280x720 (UIScale 1.16); Phone 844x390 (UIScale 1.0) x6 scenarios: crisis at bottom / three routine tickets / three crises / two crises + junction / four crises pinned (+1 hidden) / three pinned crises + junction; Live demo (interactive, 1280x720); Kit (shown at 1.25x, 1295x1154).
Fonts: Luckiest Guy (titles, stamps), Montserrat 600/700/800 (body). Kit bg #4d5d61.

### Placement
- Stack bottom-right: container right 18.56, bottom 127.6, 290 wide x 420 tall, scale 1.16 on PC (origin bottom-right), newest at bottom, 8px gap, max 4 shown, "+N MORE" chip beside top ticket.
- PC board also has a top-right "People | Cash" leaderboard panel (176 wide, rgba(18,18,21,.72), r10): JoelRails $340, MayaChoo $210, Tinkerbolt $95, Jin_Loco $60.

### The ticket frame (anatomy, full size 290 x 64)
- Drop shadow: same rect offset y+4, rgba(21,23,28,.45), r11.
- Outer: #15171c ink, r11, 3px border; inner paper 284x58 r8, gradient #f9f2df -> #e8d9b5.
- Left stub 57 wide, colour per kind, r8 left corners.
- Ticket punch notches: 16px ink circles at x52 top (-8) and bottom (y56) = perforation cut-outs; perforation line of 4px ink dots at x58 every 8px (y10..50).
- Icon medallion: 40px ink circle + 35px cream #f9f2df disc at (11.5,12); 64x64 chunky SVG icons with 8px ink outline, two-tone fill + highlight.
- Title: x70 y6, Luckiest Guy 20/24, #15171c, ellipsis, width 206 (131 if value stamp).
- Body: x70 y31, Montserrat 700 14/17, #4a4133.
- Life bar: x70 y52, 206x4 r2, track rgba(21,23,28,.14), fill = kind barColor, drains over life.
- Value stamp: 68x36 at (209,12), cream bg, 2.5px outline in stampInk, rotate -8deg, Luckiest Guy 22 (auto-shrinks 22->16 by length).
- Merge badge: count number (e.g. "3") when repeats merge.
- Crisis extra: slot +14px; ink halo 304x78 r18 + red halo #e23a2e 300x74 r16 op .9 (pulses rr-pulse .3->.95), shake on arrival.
- Compact (older tickets): H 44, inner 38, medallion 34/29, only title + bar, stamp 18->14, 3 perforation dots.

### Kinds (Live script)
| kind | stub | bar | stamp ink | life |
|---|---|---|---|---|
| danger (crisis) | #f0604f -> #cf3326 | #b02a20 | #15171c | 7000ms (sticky variant: no bar, stays until fixed) |
| risk | hazard stripes -45deg #f2c230/#15171c 8px | #15171c | #15171c | 6000 |
| cash | #56d994 -> #26a862 | #156b3d | #0f5c31 | 4500 |
| info (crew/teal) | #48b6ab -> #2a8a81 | #1c6a63 | #15171c | 5000 |

### Notification types (exact text)
- CoalLow (danger, coal): "COAL LOW!" / "Shovel coal in the firebox!"
- PressureHigh (danger, gauge): "PRESSURE HIGH!" / "The boiler's gonna blow!"
- Breakdown (danger, wrench): "BREAKDOWN!" / "Grab a wrench and fix it!"
- PassengersUpset (danger, passenger): "PASSENGERS UPSET!" / "Check the carriages, fast!"
- JunctionAhead (risk, lever): "JUNCTION AHEAD!" / "Safe or risky? Pull it!"
- RiskyRoute (risk, fork): "RISKY ROUTE!" / "Multiplier up" / stamp "X2"
- FareBanked (cash, coin): "FARE BANKED!" / "Station paid out" / "$120" (merges: +$40 each, count badge; $12,000 -> "$12K")
- CrateLanded (info, crate): "CRATE LANDED!" / "Grab it before it slides off!"
- CrewJoined (info, crewjoin): "CREW JOINED!" / "{name} is aboard"
- CrewLeft (info, crewleave): "CREW LEFT!" / "{name} left the train" (names cap at 10 chars + "…")

### States / behaviour
- Enter: slide from translateX(125%) + fade in; leave: slide out, removed after 320ms.
- Crisis arrival: rr-shake 0.5s (delay .35s; ±5px). Merge: rr-bumpA/B scale 1.07->1, 0.32s.
- Newest ticket + newest crisis stay full; others compact (compact crisis keeps halo).
- Cap 4 visible; over cap routine tickets leave first; sticky crisis never pushed off; overflow -> "+1 MORE".
- Kit section labels: "CRISIS · red stub, ink-and-red halo, one shake on arrival"; "JUNCTION & RISK · hazard stub"; "CASH · green stub, value stamp"; "CREW & INFO · teal stub"; "OLDER TICKETS GO COMPACT · the newest ticket and the newest crisis stay full size".
- Other palette in use: #f2c230 / #ffd95e (yellow), #f7f1e3, icon greys #2b2f36 #3a3f48 #5d6470 #6b7380 #8b939e #dfe4ea, wood #8f5a2a #b87a3d #d9a262, skin #dca47a #f2c9a0.
