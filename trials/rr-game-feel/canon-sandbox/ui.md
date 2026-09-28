# UI tokens and screens

Rules, the HUD notification system (ticket frame), the lever panel, the supply terminal, the lobby panels and difficulty colours. Devices, safe zones and fonts at the platform level are in `tech.ui_platform`. The HUD skin (heritage brass vs teal-cream/mustard livery) is OPEN: OQ-001.

## rules · UI rules
- `ui.rules.one_accent` = `one accent hue does all the "this is active" work (selected, current, Join)` | src: DTU | proposed
- `ui.rules.difficulty_never_chrome` = `difficulty colours appear only as difficulty, never as chrome` | src: DTU | proposed
- `ui.rules.phone_first` = `design and judge at phone 844x390 true size first` | src: PROF, R2A | canon
- `ui.rules.clear_zones` = `HUD and cards stay clear of the thumbstick, jump button, hotbar and top bar` | src: R2A, PROF | canon
- `ui.rules.contrast` = `WCAG AA as measured: 4.5:1 body, 3:1 large text` | critic B2 anchor | src: RUB, HUDM | canon
- `ui.rules.min_text` = `body >= 12 px, titles >= 16 px at 844x390` | src: HUDM | proposed
- `ui.rules.colourblind` = `kinds and terminals carry an icon or shape backup, never colour alone` | e.g. wire terminal shape tags | src: CI, HUDM | canon
- `ui.rules.exact_texts` = `game strings come from gameplay.alerts / world.lexicon verbatim` | text diff must be 0 | src: HUDM | canon

## hud · Notification stack (ticket frame; owner likes the frame, D-017)
- `ui.hud.anchor` = `bottom-right stack, newest at the bottom` | phone 14 px right / 112 px bottom (clear of jump); PC 18.56 / 127.6 at UIScale 1.16 | src: TN, HUDM | canon
- `ui.hud.max_visible` = `4` | overflow chip "+N MORE" beside the top ticket; routine tickets leave first; a sticky crisis is never pushed off | src: TN | canon | check: (?:max|cap|up to)\s*(\d+)\s*(?:visible\s*)?tickets
- `ui.hud.ticket_size` = `290 x 64` | compact older tickets 44 tall | src: TN | canon
- `ui.hud.gap_px` = `8` | between tickets (remake used 6) | src: TN | canon
- `ui.hud.anatomy` = `ink frame r11 3 px; cream paper card; colour stub 57 px on the left; punch notches (16 px) top and bottom at the stub; perforation dots every 8 px; icon medallion 40 px; title; body; life bar; optional rotated value stamp; merge count badge` | keep all of it on every kind | src: TN, HUDM | canon
- `ui.hud.title_type` = `Luckiest Guy 20/24, ink` | ellipsis at 206 px (131 with a stamp) | src: TN | canon
- `ui.hud.body_type` = `Montserrat 700 14/17` | src: TN | canon
- `ui.hud.stamp` = `68 x 36, rotated -8 deg, Luckiest Guy 22 auto-shrinking to 16` | src: TN | canon
- `ui.hud.life_bar` = `206 x 4, drains over the ticket's life` | src: TN | canon
- `ui.hud.crisis_extra` = `crisis: ink halo + red halo (#E23A2E, pulsing 0.3-0.95), one shake on arrival (0.5 s, +-5 px)` | only the newest crisis keeps the halo in the remake | src: TN, HUDM | canon
- `ui.hud.motion` = `enter: slide from 125% + fade; leave: slide out, removed after 320 ms; merge bump scale 1.07 > 1 over 0.32 s` | src: TN | canon
- `ui.hud.compact_rule` = `the newest ticket and the newest crisis stay full size; older ones go compact (title + bar only)` | src: TN | canon
- `ui.hud.electrics_down` = `when electrics are down the stack hides or glitches` | src: R2A | canon
- `ui.hud.skin` = `heritage brass (soot-iron frame, brass pinline and rivets, aged card, rubber-stamp values) vs teal-cream/mustard livery` | OPEN, owner's call (OQ-001) | src: HUDM, RUB, THS | conflict

## hud_kinds · HUD kind colours (prototype values; skin open in OQ-001)
- `ui.hud_kinds.danger_stub_top` = `#F0604F` | crisis stub gradient top | src: TN | canon
- `ui.hud_kinds.danger_stub_bottom` = `#CF3326` | remake uses #C42E22 | src: TN | canon
- `ui.hud_kinds.danger_bar` = `#B02A20` | src: TN | canon
- `ui.hud_kinds.risk_stripe` = `#F2C230` | 45 deg hazard stripes 8 px with ink | src: TN | canon
- `ui.hud_kinds.cash_stub_top` = `#56D994` | src: TN | canon
- `ui.hud_kinds.cash_stub_bottom` = `#26A862` | src: TN | canon
- `ui.hud_kinds.cash_bar` = `#156B3D` | src: TN | canon
- `ui.hud_kinds.cash_stamp` = `#0F5C31` | src: TN | canon
- `ui.hud_kinds.info_stub_top` = `#48B6AB` | crew/teal | src: TN | canon
- `ui.hud_kinds.info_stub_bottom` = `#2A8A81` | src: TN | canon
- `ui.hud_kinds.info_bar` = `#1C6A63` | src: TN | canon
- `ui.hud_kinds.paper_top` = `#F9F2DF` | card gradient top | src: TN | canon
- `ui.hud_kinds.paper_bottom` = `#E8D9B5` | card gradient bottom | src: TN | canon
- `ui.hud_kinds.body_ink` = `#4A4133` | body text | src: TN | canon
- `ui.hud_kinds.kit_bg` = `#4D5D61` | presentation background only | src: TN | canon

## hud_remake · Heritage-brass HUD remake (self-assessed 8/10, not independently certified; option A of OQ-001)
- `ui.hud_remake.iron_top` = `#3B4047` | soot-iron frame top | src: HUDM | proposed
- `ui.hud_remake.iron_bottom` = `#22262B` | src: HUDM | proposed
- `ui.hud_remake.brass` = `#D9A441` | pinline, rivets, medallion ring (Lua export; tokens.json says #D9A627) | src: HUDM | proposed
- `ui.hud_remake.brass_light` = `#FFE29A` | src: HUDM | proposed
- `ui.hud_remake.brass_dark` = `#8A5F1C` | src: HUDM | proposed
- `ui.hud_remake.card_top` = `#F7EDD3` | aged card | src: HUDM | proposed
- `ui.hud_remake.card_bottom` = `#E7D4A6` | src: HUDM | proposed
- `ui.hud_remake.body` = `#463C2E` | src: HUDM | proposed
- `ui.hud_remake.danger_stub_bottom` = `#C42E22` | src: HUDM | proposed
- `ui.hud_remake.cash_stub_bottom` = `#23A05C` | src: HUDM | proposed
- `ui.hud_remake.info_stub_bottom` = `#27857C` | src: HUDM | proposed

## lever · Junction lever panel (sketch)
- `ui.lever.placement` = `console bottom-centre while a choice is open; route cards upper left and upper right; progress bar top-centre` | src: JLP | proposed
- `ui.lever.size_1080p` = `panel 560 x 174 px; knob 64 px wide` | the knob stays thumb-sized; shaft and panel shrink instead | src: JLP | proposed
- `ui.lever.hint` = `DRAG THE LEVER` | with a two-way arc; placeholder for a two-way arrow | src: JLP | proposed
- `ui.lever.commit` = `side lamp lights hazard yellow on commit; timer spent; hint hidden` | src: JLP | proposed
- `ui.lever.timer` = `timer bar drains toward the middle` | src: JLP | proposed
- `ui.lever.plate` = `JUNCTION` | plus a taped DO NOT PULL sign with DO NOT scribbled out | src: JLP | proposed
- `ui.lever.panel_steel` = `#48546E` | panel gradient bottom (#8A99B4 top) | src: JLP | proposed
- `ui.lever.ink` = `#161B26` | outline ink of the sketch | src: JLP | proposed
- `ui.lever.hazard` = `#F5B431` | hazard stripes (with #1C1712) | src: JLP, JB | proposed
- `ui.lever.knob` = `#F0604C` | knob gradient to #B32A20 | src: JLP | proposed
- `ui.lever.progress_safe` = `#46C35F` | journey bar green/orange/red segments with "X miles left" | src: JLP | proposed
- `ui.lever.progress_mid` = `#F08A3C` | src: JLP | proposed
- `ui.lever.progress_danger` = `#E2402F` | src: JLP | proposed

## terminal · Supply Terminal v4 (Depotron order screen)
- `ui.terminal.canvas` = `1600 x 900 boards: full cash (300), low cash (30), just ordered` | animated, marked "Final: ready for Roblox" | src: ST | proposed
- `ui.terminal.header` = `ORDER SUPPLIES` | src: ST | proposed
- `ui.terminal.screen` = `#1B2233` | dominant navy screen | src: ST | proposed
- `ui.terminal.ok_green` = `#3FD986` | ONLINE / ordered states | src: ST | proposed
- `ui.terminal.cream` = `#F6E7C8` | src: ST | proposed
- `ui.terminal.amber` = `#F6C275` | price and cash (also #E8A33D) | src: ST | proposed
- `ui.terminal.display_font` = `Archivo Black` | see style.type.terminal_display | src: ST | proposed
- `ui.terminal.purchase_note` = `in game, Roblox's own purchase window opens; the terminal only stands in for it` | src: ST | proposed

## lobby · Lobby panels (Create match)
- `ui.lobby.header` = `#C44A20` | rust header (dark #8C3216) | src: DTU | proposed
- `ui.lobby.card` = `#F5E7C9` | cream card stock (alt #ECD9AB) | src: DTU | proposed
- `ui.lobby.ink` = `#2B1810` | src: DTU | proposed
- `ui.lobby.accent_teal` = `#1FAE8E` | option A accent (dark #147A63); critic dry test assumed teal; OQ-017 | src: DTU | conflict
- `ui.lobby.accent_brass` = `#D69A2D` | option B accent (dark #A3721A); OQ-017 | src: DTU | conflict
- `ui.lobby.controls` = `Players 1/2/3 chips, Difficulty < MEDIUM >, Join; chips 44 x 44, radius 12` | src: DTU | proposed

## difficulty · Difficulty tier colours (own strip, own meaning)
- `ui.difficulty.easy` = `#4A9EC4` | src: DTU | proposed
- `ui.difficulty.medium` = `#FFC12D` | src: DTU | proposed
- `ui.difficulty.hard` = `#E06620` | src: DTU | proposed
- `ui.difficulty.insane` = `#C21F1A` | text #F7E9D8 on Insane | src: DTU | proposed
