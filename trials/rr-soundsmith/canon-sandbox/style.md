# House style

Palette tokens (with role and material), type, line weights, forms, material rules and the don'ts. Hex values are the tokens `bible.py tokens` exports and `bible.py check` enforces. UI-only tokens live in `ui.md`. The full Visual Identity doc is not reachable from the cloud (OQ-020); where it and this file disagree, the owner decides.

## brand · 2D brand identity (thumbnails, icon, store, marketing)
- `style.brand.hazard_yellow` = `#F2C230` | the identity accent: hazard yellow against teal-cream or mustard livery; thumbnail text fill, vests, risk stripes | src: THS, LPB, TN | canon
- `style.brand.hazard_light` = `#FFD95E` | highlight on hazard yellow (HUD prototype) | src: TN | canon
- `style.brand.ink` = `#15171C` | ink-black outlines, text stroke, stripes | src: THS, TN, RUB | canon
- `style.brand.teal` = `#2F8F86` | livery teal used on the thumbnail loco and teal torso | src: THS | canon
- `style.brand.teal_dark` = `#1F6B64` | loco smokebox teal | src: THS | canon
- `style.brand.teal_bg_top` = `#3FB3A6` | teal background gradient, top | src: THS | canon
- `style.brand.teal_bg_bottom` = `#16544E` | teal background gradient, bottom | src: THS | canon
- `style.brand.cream` = `#EFE4C8` | livery cream band | src: THS | canon
- `style.brand.danger_red` = `#E23A2E` | the ONE danger signal (gauge needle, knob, lamp, crisis halo); never decoration | src: THS, TN | canon
- `style.brand.buffer_red` = `#C9412E` | red buffer beam on the loco | src: THS, RUB | canon
- `style.brand.mustard` = `#D9A627` | no fixed mustard yet; candidates #D9A627 (HUD remake) and #A9781E (Noticeboard chrome); see OQ-001 | src: HUDM, NB | conflict
- `style.brand.livery_teal_sheet` = `#1F5E5B` | "faded municipal teal, the company's colour" on drawing sheets; differs from the thumbnail teal; see OQ-001 | src: RN, DS | proposed
- `style.brand.danger_bg_top` = `#FFB347` | danger background gradient top (then #D9522B, #5A1712) | src: THS | canon
- `style.brand.danger_bg_mid` = `#D9522B` | src: THS | canon
- `style.brand.danger_bg_bottom` = `#5A1712` | src: THS | canon
- `style.brand.night_bg_top` = `#1B2540` | night background gradient top | src: THS | canon
- `style.brand.night_bg_bottom` = `#07090F` | src: THS | canon

## thumb · Thumbnail kit part colours (risky-rails-thumbnail-ideas kit v1)
- `style.thumb.skin` = `#F2C9A0` | avatar skin | src: THS | canon
- `style.thumb.dark` = `#2B2F36` | legs, boiler face, lever base | src: THS | canon
- `style.thumb.steel` = `#8A929B` | buffers, gauge rim, lever shaft | src: THS | canon
- `style.thumb.glass` = `#9FD3E0` | cab windows, sweat drops | src: THS | canon
- `style.thumb.crate` = `#B27A3F` | supply crate wood | src: THS | canon
- `style.thumb.glow` = `#FFF6C8` | headlamp glow | src: THS | canon
- `style.thumb.ballast` = `#8F8471` | track split ballast | src: THS | canon
- `style.thumb.sleeper` = `#5E3F2A` | sleepers | src: THS | canon

## world · In-world shared trim (all rolling stock reads as one company)
- `style.world.ironwork` = `#363A42` | charcoal ironwork: railings, ladder, brackets, outside door frames; Metal | src: WR | proposed
- `style.world.brass` = `#C9953A` | fittings, pipes, rails, gauge rims, trim bands; Metal, Reflectance 0.12-0.15 (only brass shines) | src: WR, CB | proposed
- `style.world.cream` = `#EBDDBE` | interior trim, coach walls, tape labels, sandwich bar back; SmoothPlastic | src: WR | proposed
- `style.world.navy` = `#1B2A3B` | cab front wall (owner's as-built navy), power box interior, riveted panels; Metal | src: WR, CB | measured
- `style.world.hazard` = `#E8AC22` | warning and hazard paint, handrails, edge lining in 3D; SmoothPlastic | src: WR | proposed
- `style.world.walnut` = `#7A4A26` | desks, coach doors, sandwich tray; Wood | src: WR | proposed
- `style.world.diamond_plate` = `#8A8D98` | mid-grey diamond plate, walked floors only (balcony deck); fixes the default pink tint | src: WR | proposed
- `style.world.soot_black` = `#15181B` | boiler backhead, corner posts, cornice; Metal or CorrodedMetal | src: CB | proposed
- `style.world.red` = `#C8412E` | valve handles, big levers, knobs; SmoothPlastic | src: CB | proposed
- `style.world.hazard_old` = `#E8B021` | earlier 3D hazard yellow (cab handrails); unified to #E8AC22 | src: CB | superseded

## cab · Driver's cab (navy/charcoal build)
- `style.cab.wall_front_low` = `#142130` | front wall below the 3-stud rail, one step darker; CorrodedMetal | src: CB | proposed
- `style.cab.wall_side` = `#4B4547` | side walls above the rail (owner's as-built charcoal); Metal | src: CB | measured
- `style.cab.wall_side_low` = `#3A3537` | side walls below the rail; CorrodedMetal | src: CB | proposed
- `style.cab.steel` = `#3A3F45` | skirting and kick plates; DiamondPlate | src: CB | proposed
- `style.cab.floor_plate` = `#4A4F55` | steel floor plate in front of the firebox; DiamondPlate | src: CB | proposed
- `style.cab.floor_wood` = `#6B4A2E` | floor and window sills; WoodPlanks | src: CB | proposed
- `style.cab.roof` = `#1F2327` | roof inside; Metal | src: CB | proposed
- `style.cab.slab` = `#263241` | the two slabs either side of the backhead, one shade lighter than the navy wall | src: CB | proposed
- `style.cab.desk` = `#26332D` | desk and button box (green-cab variant); SmoothPlastic | src: CB | proposed
- `style.cab.rivet_navy` = `#2A3C50` | rivets on navy, one step lighter, 0.2 studs | src: CB | proposed
- `style.cab.rivet_charcoal` = `#5E575A` | rivets on charcoal | src: CB | proposed
- `style.cab.coal` = `#262626` | coal lumps; Slate, shades 22-38 grey | src: CB | proposed
- `style.cab.screen_bg` = `#0B150F` | CRT screen face; SmoothPlastic | src: CB, CI | proposed
- `style.cab.screen_text` = `#7CFF9B` | CRT green text; Neon | src: CB, CI | proposed
- `style.cab.screen_amber` = `#FFB547` | CRT amber (coins, warnings) | src: CI | proposed
- `style.cab.tape_label` = `#EDE3C8` | tape label cream on cab labels; WR unifies interior cream to #EBDDBE (pick one) | src: CB, CI | proposed
- `style.cab.glass` = `#BFD9E6` | window glass; Glass, Transparency 0.5 | src: CB | proposed
- `style.cab.button_on` = `#52D68A` | cab button cap when on; Neon | src: WR | proposed
- `style.cab.wall_green` = `#2F6B4F` | green-cab option; owner built navy/charcoal instead (CI wire panel sketch still green) | src: CB, CI | superseded
- `style.cab.wall_green_low` = `#1E3A2C` | green-cab lower wall | src: CB | superseded

## light · Light colours
- `style.light.cab_lamp` = `#FFE7A6` | PointLight Brightness 1.4, Range 14, shadows on, in a brass roof cage | src: CB | proposed
- `style.light.firebox` = `#FF7A22` | PointLight Brightness 2, Range 9 on a Neon part inside the firebox door | src: CB | proposed
- `style.light.firebox_hot` = `#FF9A3C` | Neon strip, lightest of three behind the firebox door | src: CB | proposed
- `style.light.firebox_deep` = `#FF5A14` | Neon strip, deepest | src: CB | proposed
- `style.light.desk` = `#CFE3EC` | SurfaceLight Brightness 0.8, Range 8, Face Bottom, under the window sill | src: CB | proposed

## ground · Line 1 ground palette, lowland grassland (Use2022Materials off)
- `style.ground.pasture` = `#7C8A56` | 45% coverage, dominant field tone, olive not emerald; Grass | src: GP | canon
- `style.ground.damp_hollow` = `#5E7049` | 15%, dips, ditch edges, shaded embankment side; LeafyGrass | src: GP | canon
- `style.ground.dry_ridge` = `#97A06A` | 14%, high points, sun-baked; Ground | src: GP | canon
- `style.ground.straw` = `#B0A578` | 8%, dead grass, use sparingly; Sand | src: GP | canon
- `style.ground.bare_earth` = `#6B5945` | 7%, gates, crossings, fence gaps; Mud | src: GP | canon
- `style.ground.cinder_verge` = `#55503F` | 6%, sooty strip beside the sleepers; Asphalt | src: GP | canon
- `style.ground.ballast` = `#8C8680` | 5%, the 24-stud raised bed; warm grey, never blue grey; Pebble | src: GP | canon
- `style.ground.hedgerow` = `#4A5C41` | props only (bushes, tree clumps), darker than any ground tone so it silhouettes | src: GP | canon
- `style.ground.rail` = `#9A9187` | rail tops in the ground drawing | src: GP | proposed

## lobby · Depot Lobby paving (light theme of the blueprint)
- `style.lobby.walkway` = `#F7F3E6` | clean walkway: path, platform, spawn approach | src: BP | canon
- `style.lobby.concrete` = `#CABB8A` | weathered concrete, default yard slab | src: BP | canon
- `style.lobby.cracked` = `#AD9968` | cracked or lifted slab, edges and corners only | src: BP | canon
- `style.lobby.grass_seams` = `#6D7D43` | grass through the seams, fence line and corners | src: BP | canon
- `style.lobby.gravel` = `#B7A17A` | gravel ballast under the display track | src: BP | canon

## depot_kit · Depot and Main Hall kit palette (mission-made, not owner-approved)
- `style.depot_kit.stone` = `#9A9384` | atlas cell 0 | src: DEPM | assumed
- `style.depot_kit.stone_dark` = `#7D776B` | cell 1 | src: DEPM | assumed
- `style.depot_kit.mortar` = `#CABB8A` | cell 2, mortar and sills (= lobby concrete) | src: DEPM | assumed
- `style.depot_kit.timber_dark` = `#8F5A2A` | cell 3 | src: DEPM | assumed
- `style.depot_kit.timber_light` = `#B87A3D` | cell 4 | src: DEPM | assumed
- `style.depot_kit.slate_roof` = `#4A4F57` | cell 5 | src: DEPM | assumed
- `style.depot_kit.iron` = `#2B2F36` | cell 6 | src: DEPM | assumed
- `style.depot_kit.moss` = `#6D7D43` | cell 7 | src: DEPM | assumed
- `style.depot_kit.interior_dark` = `#1F2A33` | cell 8, glass and dark interior plane | src: DEPM | assumed
- `style.depot_kit.window_glow` = `#E8C46A` | cell 9 | src: DEPM | assumed
- `style.depot_kit.brass` = `#B08A3E` | cell 10 | src: DEPM | assumed
- `style.depot_kit.paving` = `#F7F3E6` | cell 11 | src: DEPM | assumed
- `style.depot_kit.soot` = `#3A3F48` | cell 12 | src: DEPM | assumed
- `style.depot_kit.red_oxide` = `#B1502B` | cell 13, doors | src: DEPM | assumed
- `style.depot_kit.gravel` = `#B7A17A` | cell 14 | src: DEPM | assumed
- `style.depot_kit.chimney_brick` = `#8A4B36` | cell 15 | src: DEPM | assumed
- `style.depot_kit.cream` = `#EFE2BD` | as exported, group Cream, SmoothPlastic | src: DEPM | assumed
- `style.depot_kit.cream_dark` = `#D2C290` | as exported, group Creamdk, SmoothPlastic (depot) | src: DEPM | assumed
- `style.depot_kit.paving_dark` = `#CFC9B9` | as exported, group Pavingdk, Concrete (depot) | src: DEPM | assumed
- `style.depot_kit.slate_dark` = `#2F333A` | as exported, group Slatedk, Slate (depot) | src: DEPM | assumed
- `style.depot_kit.stone_light` = `#ACA595` | as exported, group Stonelt, Slate | src: DEPM | assumed
- `style.depot_kit.stone_warm` = `#B6AB90` | as exported, group Stonewm, Slate (depot) | src: DEPM | assumed
- `style.depot_kit.teal_trim` = `#2E7D7A` | as exported, group Teal, Wood | src: DEPM | assumed
- `style.depot_kit.red` = `#B3312A` | as exported, group Red, SmoothPlastic (hall) | src: DEPM | assumed

## type · Typefaces
- `style.type.display` = `Luckiest Guy` | titles, stamps, thumbnail text; Roblox Enum.Font.LuckiestGuy | src: PROF, TN, THS, HUDM | canon
- `style.type.body` = `Montserrat` | UI body 600-800; Roblox family rbxasset://fonts/families/Montserrat.json | src: PROF, TN, HUDM | canon
- `style.type.display_fallback` = `Lilita One` | thumbnail fallback face | src: THS | canon
- `style.type.tape_label` = `Special Elite` | the "tape-label font": in-world tape labels and notices, turned 1-2 degrees | src: CB, CI, WR | proposed
- `style.type.crt` = `VT323` | CRT and terminal screens (Depotron); Roblox availability unverified | src: CI | proposed
- `style.type.terminal_display` = `Archivo Black` | Supply Terminal v4 display face; Roblox availability unverified | src: ST | proposed
- `style.type.ui_condensed` = `Barlow Condensed` | lever panel sketch and in-world plates; Roblox availability unverified | src: JLP, CI | proposed
- `style.type.signage_display` = `Big Shoulders Display` | Create match sketch; Roblox availability unverified | src: DTU | proposed
- `style.type.thumb_text` = `96-120 px on a 768x432 canvas, cap height >= 70 px, 1-3 words, rotation -6 to +6 deg` | src: THS | canon

## line · Line weights and minimum sizes
- `style.line.thumb_outline_px` = `7` | ink outline on thumbnail parts at 768x432 | src: THS | canon
- `style.line.thumb_text_stroke_px` = `16` | ink stroke painted under the text fill, plus drop shadow | src: THS | canon
- `style.line.hud_frame_px` = `3` | ticket outer ink border, radius 11, at 290x64 | src: TN | canon
- `style.line.icon_outline_px` = `8` | chunky icon outline at 64 px, two-tone fill plus highlight | src: TN | canon
- `style.line.min_feature_px` = `5` | key features must span >= 5 px at the 400 px game-distance render | src: RUB | canon
- `style.line.motion_min_px` = `5` | repeated detail under 2 px flickers in motion: thicken to >= 5 px, merge, or drop | src: RUB | canon

## form · Forms and detail language
- `style.form.base` = `chunky, readable, slightly toy-like forms` | src: RUB | canon
- `style.form.rails` = `capped-post yellow rails; ink-black details; red buffer beams` | src: RUB | canon
- `style.form.materials` = `weathered rural railway: stone, iron, timber, moss, soot, brass` | src: PROF | canon
- `style.form.decay` = `decay at the edges, clean along the routes players use` | src: BP, PROF | canon
- `style.form.incompetence` = `hazard tape, mismatched patch plates, "temporary" fixes, taped-off notices` | travels with the track everywhere | src: RN | canon
- `style.form.wall_lines` = `three horizontal lines per wall: hard edge at the floor, rail at 3 studs, line at the roof` | src: CB | proposed
- `style.form.relief` = `details stick out 0.05-0.3 studs so they cast shadows; flush detail vanishes at distance` | src: CB | proposed
- `style.form.handmade` = `one bent thing in a room of straight things (a handrail 3-4 degrees out of true)` | src: CB | proposed
- `style.form.clutter` = `6-8 props per small room, in corners and against walls, never mid-floor` | src: CB | proposed
- `style.form.railing` = `dark round ironwork, chunky capped corner posts, thin bars about one per stud, wider wood or brass top rail` | set by the roof ladder | src: WR | proposed
- `style.form.instruments` = `do not add instruments; add the jobs the existing ones imply` | src: WR | proposed

## material · Material and colour rules
- `style.material.reflectance` = `only brass shines (Reflectance 0.12-0.15); walls and floors stay at 0` | src: CB, WR | proposed
- `style.material.two_colours` = `two colours per surface at most` | src: WR | proposed
- `style.material.diamond_plate` = `diamond plate only on floors people walk on` | src: WR | proposed
- `style.material.steps` = `below the rail one step darker; rivets one step lighter` | src: CB | proposed
- `style.material.ground_value` = `vary value more than hue; nothing above about 45% saturation` | src: GP | canon
- `style.material.patches` = `irregular patch edges, uneven sizes (two big blobs and five small)` | src: GP | canon
- `style.material.decay_dial` = `rust, patch density, hazard tape, straw and bare earth increase with distance from the depot` | same assets, different weights | src: DS, GP | canon
- `style.material.sky` = `desaturate the sky together with the ground` | src: GP | canon

## dont · Never
- `style.dont.dead_rails` = `sepia, orange-desert, western or zombie looks` | src: PLAN, LPB, THS, RUB | canon
- `style.dont.land_or_die` = `blue-sky plus white-plane looks` | src: LPB, THS, RUB | canon
- `style.dont.default_green` = `uniform saturated Roblox-default grass green` | src: GP | canon
- `style.dont.red_decoration` = `red anywhere except the one danger signal (2D)` | src: THS | canon
- `style.dont.hairlines` = `hairline repeated detail (cresting, slats, 1 px strokes) on anything seen in motion` | src: RUB | canon
- `style.dont.dishonest_art` = `art that promises a moment the game does not have` | src: THS, LPB | canon
- `style.dont.invented_text` = `invented names or text on signage without the owner` | names come from world.lexicon or the owner | src: DEPM | assumed
