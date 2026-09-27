# Owner comms: readback, progress lines, interrupts, debrief

The owner sees only four kinds of message. Precise numbers, decisions stated with their reason, no role-play, no "Sir", no emojis, no filler.

## 1. Readback (step 2, one message)
```
MISSION <id>: <objective in one line>

What you asked (tagged):
R1 "<owner words>" -> <requirement>
...                                  (every non-noise R; superseded ones shown as "6/10 -> 8/10 per your correction")

Decided (say if wrong):
- <A1 ...>
- Live view: <Blender MCP found: I'll build live in your Blender | no Blender link here: I'll post build-stage renders (shell, roof, details, dressing)>

Questions (reply with numbers, or "go"):
1. <question> - default: <x>
(max 3)

Plan: 10 steps · bar <8> every criterion · cap 5 critic passes per deliverable · est. <band> tokens.
Proceeding on defaults; reply to redirect.            <- or, if Q is blocking: "Waiting on Q1 only; starting <independent work> now."
```

### Worked example, prompt 1 (abridged)
```
MISSION 260927-depot-buildings: Depot + Main Hall in Blender, each to 8/10, Roblox-ready, every recolourable part separate.
R1 "have a look through this" -> Depot Lobby Blueprint as layout source
R3/R4 "the main hall and the depot" -> two models; R7 "8/10" (your correction of 6/10)
R9 "watch it go up in real time" -> see live view · R10/R11 separate named parts, recolour by group
Decided: heights eaves 14 / ridge 22 studs, doors 7x9, facade + open doorway.
Live view: no Blender link to your PC in this session, so I'll post 4 build-stage renders per building. Connect a Blender MCP and I'll build live instead.
1. "Main hall" isn't on the blueprint - default: single-storey stone hall behind the join-queue platform (~24x12).
2. Interiors? default: facade only.
Plan: 10 steps · bar 8 · one critic for both buildings, cap 5 passes · est. 0.45-0.75M tokens. Proceeding on defaults; reply to redirect.
```

### Worked example, prompt 2 (abridged)
```
MISSION 260927-ticket-hud: remake the notification HUD in a Risky Rails style, ticket frame kept, 8/10, Roblox export, 10 steps.
... R-lines ...
Decided: phone 844x390 first, PC second; enamel-signage + brass style on the ticket frame; exact texts and behaviour kept.
Prototype: your link didn't open for me; <match case: found "<exact listed title>" by your title, using it | no match case: 1. No design named "<owner's title>" is listed; closest is "<title>" (<how it differs>). Use it? Waiting on Q1 only; building style tokens now. Owner away: using "<title>" as fallback, flagged under Needs owner.>
(Only claim a match you saw in the `Artifact list` result.)
Plan: 10 steps · bar 8 · cap 5 passes · est. 350-600k tokens. Proceeding; reply to redirect.
```

## 2. Progress lines (`mission_state.py step` prints them)
`[k/10] <Stage> - <result, <= 15 words, numbers> (<tokens so far>)`
- One line per step transition, one per critic pass: `[8/10] Fix + re-check - Depot pass 2: A1 8 A2 8 A3 8 A4 7 A5 8 A6 8 A7 8, fixing A4-2 (262k)`.
- Images only at: step 5 (milestone strip / v1 contact sheet), each critic pass (contact.png), step 9 (hero render or board). Nothing else.
- Proactive: say the moment something matters (pass > 120k, a stall, a fallback, a needs-owner item), with the action you are taking.

## 3. Interrupts (only these)
Needs-owner blocker · spend > 1.3x estimate · capability gap discovered mid-run. Each carries a default and says when it takes effect: "Continuing with <default> now; reply to redirect." Never promise to wait N minutes; in cloud sessions use `send_later` only if a real wait is needed.

## 4. Debrief (step 10, one message)
```
[10/10] Debrief - <8/10 reached (A1 8 · A2 9 ...) | stopped at 7/10: <reason> | uncertified: self-assessed 8/10, no independent critic>
Files: <paths / links>
Assumed: <A-lines still defaults>
Asks: R1 done · R9 fallback (renders; no Blender MCP) · ... (every R, one line)
Needs owner: <list>
Cost: critic <kit show total> + build ~<k> = <total> (mark estimates "est.")
Next: <one suggested move> (e.g. install the design-critic agent; saving per multiuse-critic)
```
Delivery: images (step 5 strip, each contact.png, step 9 hero) and the debrief file via `SendUserFile` (status `proactive` when the owner is away); the one-line debrief via `PushNotification` if that tool exists; otherwise put the paths in chat.
