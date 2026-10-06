# P3 facts: Roblox engine for train splits v2. Researched 2026-10-06
create.roblox.com and devforum are blocked here, so the docs were read from Roblox's official docs source
(github.com/Roblox/creator-docs, commit 9f840b1, 2026-10-02). `cr/` = `https://create.roblox.com/docs/`. DevForum and
press items come from search snippets only.
Confidence: **V** = verified in the docs · **A** = announced · **C** = community · **U** = unverified.

## A. VFX
| fact | v2 help / limit | source | date | conf |
|---|---|---|---|---|
| Flipbook layouts: 2x2 / 4x4 / 8x8 (at most 64 frames) or Custom X×Y. Modes: Loop, OneShot (spans the Lifetime), PingPong, Random. At most 30 fps. The texture must be an exact multiple of the grid, with padding between frames. | A 64-frame fireball is possible, but it needs an owner upload (rr-vfx-lighting cannot author flipbooks). | cr/reference/engine/classes/ParticleEmitter, cr/effects/particle-emitters | 2026-10 | V |
| Low-memory clients (older phones) **switch flipbooks off automatically**. Reused textures cost less. | Every flipbook needs a plain-texture fallback that still reads. | cr/effects/particle-emitters | 2026-10 | V |
| Squash stretches tall (+) or wide (−). LightEmission: 1 = additive. Brightness only applies at LightInfluence 0, and LightInfluence defaults to 0 from Instance.new and 1 when inserted in Studio. Lifetime is capped at 20 s. | Squash gives slapstick stretch. Set LightInfluence explicitly. | ParticleEmitter API | 2026-10 | V |
| Shape: Box, Sphere, Cylinder or Disc. ShapeStyle: Volume or Surface. ShapeInOut. ShapePartial: a disc rim gives a ring, a sphere gives a dome. Acceleration in studs/s². Drag = speed half-life in s. | A Disc with ShapePartial=1 makes a **particle ring shockwave**, which gets round "no mesh shockwave". | same | 2026-10 | V |
| TimeScale 0-1 exists on ParticleEmitter, Explosion, Fire, Smoke and Sparkles. Also: LockedToPart, VelocityInheritance, ZOffset (studs; negative hides particles), Orientation (FacingCamera / WorldUp / VelocityParallel / VelocityPerpendicular), WindAffectsDrag (GlobalWind, when Drag > 0). | Per-effect slow-mo and freeze-frames. VelocityParallel suits spark streaks. | same | 2026-10 | V |
| Changing emitter properties at runtime "can have a dramatic impact on performance". Particles do not batch. Fill-rate grows with screen coverage. | Use Emit() bursts from pre-built emitters. Large near-camera smoke is the phone killer. | cr/performance-optimization/improve | 2026-10 | V |
| Lower quality settings emit fewer particles than Rate. Emit() reportedly bypasses this. Roblox gives no numeric particle or overdraw budget. | Keep the canon OQ-029 budgets and measure on the owner's phone. | devforum.roblox.com/t/1994624; cr/performance-optimization/design | old / 2026-10 | C / V |
| Beam (2 attachments, CurveSize, Segments, TextureSpeed). Trail (Lifetime, Min/MaxLength, WidthScale). Highlight: at most 255 shown per client. | Trails behind flung players. Highlight outlines for 6 players are cheap. | Beam / Trail API, cr/effects/highlighting | 2026-10 | V |
| Lights: shadows **off below quality 4**. Advice: fewer lights, Shadows=false, small Range. SpotLight Angle at most 180. Range max of 60 studs. | Flash lights stay short-lived with Shadows=false. | cr/effects/light-sources, improve | 2026-10 | V (Range: C) |
| **Explosion** instance: fixed-size visual. BlastRadius at most 100 studs. Force **does not fall off with distance**. It breaks JointInstances and WeldConstraints within DestroyJointRadiusPercent (never constraints). It **kills Humanoids** unless they have a ForceField or the percent is 0. It ignores obstacles. Visible=false keeps the force without the visual. | Not a 0% train killer: 100 studs is less than the 165-stud train (tech.units.train_len). Use it only Visible=false with DestroyJointRadiusPercent=0, or not at all. | cr/reference/engine/classes/Explosion | 2026-10 | V |
| Post effects: Bloom, Blur, ColorCorrection, DepthOfField, SunRays, plus the new **ColorGradingEffect** (Lighting only). Some "work differently or not at all" at low quality; SunRays "may not render on low-end". | The explosion read cannot rely on Bloom or SunRays. A ColorCorrection flash is safer. | cr/environment/post-processing-effects, PostEffect API | 2026-10 | V |
| New in 2025-26: emissive masks and 4K textures (Spring 2026 roadmap). No new particle features were found (no sub-emitters, collisions or bursts). | Emissive masks could make glowing torn edges. | devforum.roblox.com/t/4625473 | 2026 spring | A |
| Textures: png/jpg/tga/bmp. The docs conflict: "up to 4096²" in one place, "1024² max" in another. All uploads are moderated and hidden until approved. | Upload early. Author flipbooks at 1024² until a 4K one is tested. | cr/art/modeling/texture-specifications, cr/projects/assets | 2026-10 | V (flipbook max: U) |

## B. Animation and physics
| fact | v2 help / limit | source | date | conf |
|---|---|---|---|---|
| Parts joined by welds form an assembly = **one rigid body**. Physics runs at 240 Hz with adaptive islands; still assemblies sleep. | An unanchored welded half is one body. Its collision cost still scales with part count (est.). | cr/physics/assemblies, /adaptive-timestepping, /sleep-system | 2026-10 | V |
| The server always owns anchored parts. Unanchored parts are **auto-assigned to nearby clients**. SetNetworkOwner is server-only and covers the whole mechanism. Re-anchoring resets ownership. | A server-unanchored wreck near players becomes client-owned unless set with SetNetworkOwner(nil). | cr/physics/network-ownership | 2026-10 | V |
| An owning client can teleport an assembly, give it Inf/NaN velocity and **fling other players**. It can also fake Touched. | Debris must never grant damage or money through Touched. Wreck ownership is an exploit vector. | cr/scripting/security/network-ownership | 2026-10 | V |
| Streaming: assemblies stream in whole. "Avoid moving assemblies with unnecessarily large numbers of instances" (network and CPU spikes). Client physics only runs in streamed areas. | A server-side wreck of 200-1,000 parts is costly. Prefer client-only debris. No engine cost figure exists (U): profile it. | cr/workspace/streaming | 2026-10 | V |
| No replay or determinism API exists. Debris created on a client exists only there. | Sync = a server event with a seed and start time, then each client plays a scripted CFrame path. | API ref (absence) | 2026-10 | V |
| Server authority (AuthorityMode=Server) is **beta**. It needs streaming, fixed simulation and deferred signals. | Not for v2. A future fix for fling exploits. | cr/projects/server-authority | 2026-10 | V |

## C. Character ragdoll and fling (R15)
| fact | v2 help / limit | source | date | conf |
|---|---|---|---|---|
| **Avatar Joint Upgrade** (the default for new places): AnimationConstraint + BallSocketConstraint replace Motor6D. `IsA("Motor6D")` returns false. C0/C1 are read-only. **IsKinematic=false = force ragdoll.** | Ragdoll = a property flip. Old Motor6D ragdoll code breaks. Check the place's setting. | AnimationConstraint API; devforum.roblox.com/t/4298561, /t/4656414 | 2026 (est. H1) | V/A |
| StarterPlayer.ClassicDeath=false gives BreakJointsOnDeath=false and a **ragdoll on death** (needs AJU). RequiresNeck=false stops the death when the neck breaks. | A free ragdoll at 0%. | StarterPlayer / Humanoid API | 2026-10 | V |
| States: **Physics** is set and unset manually. **Ragdoll is deprecated.** FallingDown recovers by itself, then GettingUp. PlatformStand = free-fall, no control. SetStateEnabled **does not replicate**. | Fling sequence: Physics + IsKinematic off, then impulse, then restore + GettingUp, all on the owning client. | Humanoid API, HumanoidStateType | 2026-10 | V |
| ApplyImpulse acts at the centre of mass; ApplyAngularImpulse adds spin. Server-owned parts take it from the server only. Parts with *automatic* client ownership take it from either side. | Whether a character counts as "automatic" is not stated (U). Plan: the server sends a capped direction and strength, and the client applies it. Test both in Studio. | BasePart API | 2026-10 | V |
| Seat: a "SeatWeld" 2 studs up. Exit by jumping or by destroying SeatWeld. **3 s re-sit cooldown** (may change). | Unseat (destroy SeatWeld) before the impulse. | Seat API | 2026-10 | V |
| Collision groups stop player-to-player collisions, but exploits can bypass them. How an Explosion's neck kill interacts with AJU is unverified. | Put flung players in a no-player-collide group. Fling abuse is outside static scans. | devforum.roblox.com/t/1882550 | old | C / U |

## D. Slow motion and camera
| fact | v2 help / limit | source | date | conf |
|---|---|---|---|---|
| There is **no global or physics time scale**: TimeScale exists only on the 5 effect classes. | Fake slow-mo with effect TimeScale, animation speed, scripted debris and poses, and the camera. Real physics keeps full speed. | API ref (absence) | 2026-10 | V |
| Camera shake has no built-in API. The norm is a client RenderStepped CFrame offset. | rr-game-feel covers it. | community | n/a | C |
| GuiService.ReducedMotionEnabled (read-only) = the Roblox Reduce Motion toggle. | Gate shake, FOV, slow-mo and the fling camera on it. | GuiService API, cr/production/publishing/accessibility | 2026-10 | V |
| **HapticEffect supersedes HapticService.** Types: GameplayExplosion, GameplayCollision, UI*, Custom waveform. Works on iOS/Android, PlayStation, Xbox and Quest, scaled by the user setting. Client only. | Explosion and landing haptics on phones. | HapticEffect API | 2026-10 | V |

## E. Clips and sharing
| fact | v2 help / limit | source | date | conf |
|---|---|---|---|---|
| CaptureService (client): TakeScreenshotCaptureAsync (UICaptureMode, default None) or CaptureScreenshot, then PromptSaveCapturesToGallery or **PromptShareCapture** (share sheet + invite link + launchData; a download where sharing is not allowed). CaptureBegan/Ended let the game hide its HUD. | An auto screenshot at peak chaos, then a Share prompt with an invite: a growth loop. | CaptureService API; devforum.roblox.com/t/2838188 | 2024; doc 2026-10 | V |
| **StartVideoCaptureAsync**: at most **30 s**, **voice muted**, params ignored. Fails with NoDeviceSupport, CapturingAlready or NoSpaceOnDevice. Beta since **July 2025**. **No retroactive buffer API was found.** | Recording must start *before* the moment. The platform list is unknown (U), so handle failure quietly. | CaptureService API; devforum.roblox.com/t/3823116 | 2025-07 | V/A |
| Capture uploads: gallery permission, the Maturity questionnaire, **20 videos/user/day**, moderation. | Only for a later in-game clip wall (PROPOSED). | CaptureService API | 2026-10 | V |
| **Roblox Moments**: a feed of clips up to 30 s, **13+**, beta, RDC Sept 2025. | Clips can reach it, but not for players under 13. 2026 status: U. | techcrunch.com 2025-09-05 | 2025-09 | A |
| Rules on prompting or rewarding captures: none found. | Do not reward shares until checked. | none | n/a | U |

## Implications for v2
- **Fling runs on each client.** The server picks the targets and a capped impulse and destroys SeatWelds. The owning client sets Physics, sets IsKinematic=false, applies the impulse and recovers. The keep-on 5-coin fee for flung players needs an owner call.
- **Wreck debris is client-side, scripted and seeded.** Server-unanchored train parts drift to client ownership (exploit) and stream expensively. Use real physics only with SetNetworkOwner(nil) and a phone profile.
- **The 0% blow-up must not use an Explosion instance** (it kills, is not distance-scaled and reaches only 100 of 165 studs). Use a particle stack (Disc-rim shockwave) plus scripted pushes.
- **Slow motion = TimeScale, animation speed and the camera only.** Physically simulated bodies break it, which is one more reason to script the debris.
- **Clipability:** begin StartVideoCaptureAsync near 0% (30 s window), then offer Save or Share after game over. The screenshot + PromptShareCapture path is the fallback. No Moments for players under 13.
- **The phone floor sets the look:** flipbooks, Bloom, SunRays, shadows and part of the particles drop away on low-end phones. The fallback layer alone must meet 8/10 (D-020).
- **Owner uploads (flipbooks, textures, audio) go through moderation:** schedule them first on the critical path.
- **Honour Reduce Motion and use HapticEffect.**
