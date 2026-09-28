# Roblox tech facts

Units, avatar and camera, mesh budgets, import/export pitfalls, lighting and materials, streaming and networking, data, security, publishing gates, and what the cloud session can and cannot do.

## units · Units and scale
- `tech.units.stud_m` = `0.28` | 1 stud is about 0.28 m (Roblox); the Drawing Set's 0.35 m derivation is not used | src: BP, PROF | platform | check: (?:\b1|\ba|\bone)\s*stud\s*(?:≈|~|=|is about|is roughly|is approx\.?|is)?\s*(0\.\d+)\s*m\b
- `tech.units.stud_m_ds` = `0.35` | derived from a 5-stud rig for the speed table | src: DS | superseded
- `tech.units.avatar_h` = `5` | avatar about 5 studs tall (R15 rig about 5.2) | src: PROF, CI | platform
- `tech.units.building_door` = `7 x 9` | lobby building doors at least 7 wide x 9 tall | src: PROF, DEPM | proposed
- `tech.units.train_doorway` = `5 x 7` | cab-to-coach doorway as built; two players pass while a third shovels | src: CB | measured
- `tech.units.segment_len` = `512` | studs per track segment | src: DS, DIM | canon | check: (?:(\d+)\s*studs?\s*(?:per|each)\s*segment|segment\s*length\s*(?:=|:|of|is)?\s*(\d+))
- `tech.units.pole_spacing` = `128` | telegraph poles, fixed, never jittered: the speedometer | src: DS, RN | canon | check: poles?\s*(?:every|at)\s*(\d+)\s*stud
- `tech.units.track_piece` = `16` | studs per straight track piece (ballast, sleepers, rails) | src: LBJ, JTV | canon
- `tech.units.ballast_w` = `24` | ballast bed width | src: DS, LBJ | canon
- `tech.units.corridor_clear` = `15` | no props within 15 studs of any track centreline | src: DS, LBJ | canon
- `tech.units.train_len` = `165` | train length in studs (drawing) | src: DS | proposed
- `tech.units.cab_inside` = `16.35 W x 14 D x 8 H` | cab interior; heights from cab floor 0; rail at 3 | src: CB | measured

## camera · Avatar camera
- `tech.camera.eye_3p` = `9.5` | third-person camera about 9.5 studs above the floor | src: PROF, CRIT | platform
- `tech.camera.eye_1p` = `4.5` | first-person eye in the cab rig (player about 5.2 tall); critic kit uses 5, within tolerance | src: CI, CB | measured
- `tech.camera.fov_v` = `70` | Roblox vertical FOV | src: PROF, CRIT | platform | check: (?:vertical\s*)?FOV\s*(?:of|=|:)?\s*(\d+)
- `tech.camera.popper` = `CanCollide=false parts do not block the Roblox (Popper) camera` | overhead decoration can be CanCollide=false | src: CRIT | platform
- `tech.camera.cab_view` = `cab camera eye about 12 studs above rail` | used for junction drawings; tune curves from the cab camera | src: JTV, LBJ | proposed

## mesh · Mesh budgets and import/export
- `tech.mesh.tris_target` = `10000` | triangles per MeshPart in a moving/scrolling world | src: PROF, CRIT | proposed
- `tech.mesh.tris_cap` = `20000` | hard MeshPart cap | src: PROF, CRIT | platform
- `tech.mesh.atlas` = `one 256 px palette atlas, 32 px cells, Closest filtering, one material` | src: PROF | assumed
- `tech.mesh.backface_cull` = `Roblox culls back faces; check normals from every camera` | src: CRIT | platform
- `tech.mesh.fbx_unit_bug` = `FBX can import about 3.57x off; state expected stud size at handover` | src: CRIT, REX | platform
- `tech.mesh.obj_rotation` = `Studio OBJ imports into Blender rotated 90 deg about X; bake before measuring` | src: CRIT | platform
- `tech.mesh.obj_names` = `Studio OBJ export renumbers parts; never map by exported names` | src: CRIT | platform
- `tech.mesh.recolour` = `a MeshPart with TextureID or SurfaceAppearance hides its Color; recolourable exports ship without the atlas texture` | export both plain and _atlas FBX when the atlas look is wanted | src: REX, DEPM | platform
- `tech.mesh.naming` = `<Bldg>_<Part>_<Mat>_<nn>, one object per editable part, never joined` | src: REX | canon
- `tech.mesh.coplanar` = `overlapping coplanar faces render pitch-black in Cycles; stagger depths` | cost 4 diagnostic renders once | src: MEM | measured

## lighting · Lighting and materials
- `tech.lighting.technology` = `Future` | ShadowMap as the phone-safe fallback; never Voxel for lit interiors | src: CB, WR | proposed
- `tech.lighting.materials_2022` = `MaterialService.Use2022Materials = false` | the 2022 set bleaches every tint (washed-out grass) | src: GP | canon
- `tech.lighting.outdoor_ambient` = `70,80,70` | default 128 grey drains saturation | src: GP | proposed
- `tech.lighting.atmosphere` = `Density about 0.3, colour tinted grey-green` | keep haze: it hides the streamer's spawn edge | src: GP | proposed
- `tech.lighting.color_correction` = `Saturation +0.12, Contrast +0.05` | one global effect, not per-part retints | src: GP | proposed
- `tech.lighting.surfacegui_pps` = `50` | PixelsPerStud at least 50 on in-world screens | src: CB | proposed
- `tech.lighting.terrain` = `Terrain cannot be pooled: streamed segment ground is parts; Terrain only for the static far layer` | Terrain colours are global per material | src: GP | platform
- `tech.lighting.technology_api` = `Lighting.Technology is deprecated and not scriptable; superseded by LightingStyle (Soft or Realistic) plus PrioritizeLightingQuality, both scriptable` | canon Future (tech.lighting.technology) maps to LightingStyle Realistic + PrioritizeLightingQuality true (proposed by VFXL); set in Studio | src: RBXD | platform
- `tech.lighting.light_range_max` = `120` | PointLight, SpotLight and SurfaceLight Range is clamped to 120 studs | src: RBXD | platform
- `tech.lighting.post_low_quality` = `some post effects render differently or not at all at low graphics QualityLevel (Automatic by default)` | judge every look with Bloom and SunRays off too (phone fallback) | src: RBXD | platform

## streaming · World streaming and networking
- `tech.streaming.window` = `4 segments ahead, 2 behind, pool 8` | spawn edge at 2,048 studs; never spawn inside the sightline | src: DS | proposed
- `tech.streaming.corridor_bands` = `0-15 track, 15-45 verge, 45-150 middle ground, 150-600 far ground` | studs from centreline | src: RN, DS | canon
- `tech.streaming.scatter` = `seed scatter from the segment index; 6-10 props open side, 2-4 enclosed; jitter +-8 studs, 360 deg, scale +-10%; poles exempt` | seeded so the Daily Line is identical for everyone | src: DS | canon
- `tech.streaming.persistent_train` = `set the train model's streaming mode to Persistent` | client scripts can always find it | src: R2A | canon
- `tech.streaming.segment_root` = `weld each segment to one anchored root part and move only that part` | try before moving the world client-side | src: R2A | proposed
- `tech.streaming.client_world_fallback` = `move the world on each device instead of the server if the live check stutters (3-4 days)` | src: R2A | proposed
- `tech.streaming.live_check` = `publish; full trip with 3+ players incl. one phone; Studio Incoming Replication Lag about 200 ms; F9 open; pass = smooth scenery, lever and HUD respond within 0.5 s` | src: R2A | canon
- `tech.streaming.fx_client` = `effects on the client, attached to the train; never tween world parts (fights the server's PivotTo)` | src: R2A | canon
- `tech.streaming.sfx_pool` = `play one-shot sounds from a small client pool; never clone Sounds on the server` | src: R2A | canon
- `tech.streaming.reserved_servers` = `reserved servers cannot be joined from the friends list` | a dropped phone loses the trip until rejoin exists | src: R2A | platform

## data · Save data and teleports
- `tech.data.store` = `ProfileStore` | src: R2A | canon
- `tech.data.store_name` = `PlayerData_alpha1` | versioned so alpha data can be wiped | src: R2A | canon
- `tech.data.award_order` = `award coins on the server at results, end the session, and only then teleport` | src: R2A | canon
- `tech.data.hints_flag` = `hints-seen flag saved in the same profile` | src: R2A | canon
- `tech.data.teleport_data` = `lobby sends expected players' UserIds in TeleportData; add a TrainType field now` | src: R2A | canon
- `tech.data.launching_lock` = `a Launching lock on the pad during teleport; a failed teleport puts the player back on the pad` | src: R2A | canon

## security · Exploit and purchase safety
- `tech.security.never_trust_client` = `the server checks prices and takes coins; never trust the GUI` | src: R2A, CI | canon
- `tech.security.process_receipt` = `ProcessReceipt copes with retries: record each PurchaseId in the profile (lobby and trip place); never grant twice` | src: R2A | canon
- `tech.security.one_crate` = `each order spawns exactly one crate; double taps must not duplicate` | src: R2A | canon
- `tech.security.fare_grants` = `anti-exploit on fare grants; server-authoritative gameplay with client-side smoothing` | src: PLAN | canon
- `tech.security.admin` = `admin commands only for the owner's UserId: skip to mile N, arrive now, force event/route/fail, send everyone home, 4x speed` | turn debug off before launch | src: R2A, LPB | canon

## ui_platform · Roblox UI platform facts
- `tech.ui_platform.phone` = `844 x 390` | phone landscape, primary, judged at true size | src: PROF, HUDM | canon
- `tech.ui_platform.pc` = `1280 x 720` | second | src: PROF | canon
- `tech.ui_platform.layout` = `Scale sizing + UIAspectRatioConstraint; UIScale 1.0 phone, 1.16 PC` | src: PROF, HUDM | canon
- `tech.ui_platform.no_go` = `top bar strip (GuiService:GetGuiInset), thumbstick bottom-left, jump button bottom-right, hotbar` | src: PROF, CRIT, R2A | platform
- `tech.ui_platform.touch_target_px` = `44` | minimum; drag frames Active | src: R2A, DTU | canon
- `tech.ui_platform.fonts` = `Font.fromEnum(Enum.Font.LuckiestGuy); Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Bold)` | as exported by the HUD package | src: HUDM, REX | measured

## publish · Publishing and platform gates (Sep 2026; recheck in Creator Hub before launch)
- `tech.publish.under16_gate` = `250 unique plays by highly engaged age-checked users within 60 days` | PLAN's 500 is stale | src: LPB | platform
- `tech.publish.testers` = `Trusted Friends of the age-checked owner can playtest at any age once the maturity questionnaire is done` | src: LPB | platform
- `tech.publish.prereqs` = `age check, 2FA, ID verification, content maturity questionnaire, 1,000 R$ publishing fee` | src: PLAN, LPB | platform
- `tech.publish.thumbnails` = `16:9, 1920 x 1080, up to 10; personalisation from 2; nothing essential in the bottom strip` | src: LPB | platform

## cloud · What the cloud session can and cannot do (measured 2026-09-27)
- `tech.cloud.blender` = `headless bpy 5.0 (Cycles only, no viewport)` | src: DEPM, REX | measured
- `tech.cloud.browser` = `Playwright + Chromium (/opt/pw-browsers/chromium)` | src: HUDM | measured
- `tech.cloud.no_studio` = `no Roblox Studio and no Studio MCP: never claim an in-Studio test; say "Studio test pending (owner)"` | src: REX, HUDM | measured
- `tech.cloud.no_ffmpeg` = `no ffmpeg: build-up animations as GIF via Pillow` | src: DEPM | measured
- `tech.cloud.lua_check` = `npm luaparse works (Lua 5.3 grammar); luau-analyze and selene not installed` | src: HUDM | measured
- `tech.cloud.fonts` = `Google Fonts blocked in the sandbox; fonts via npm @fontsource` | src: THS | measured
