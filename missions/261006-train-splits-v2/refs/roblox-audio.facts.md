# P4 facts: Roblox audio, licence-clean sourcing, production (2026-10-06)

Docs source: create.roblox.com is blocked for both the shell and WebFetch, so the official docs were read from their source
repo instead, **github.com/Roblox/creator-docs** (sparse clone, HEAD 2026-10-06). "Docs" below means
create.roblox.com/docs/<path>, read from that repo.
Conf: H = official docs read today · M = devforum or secondary source via WebSearch summary · L = unverified.
Where v1 stood: 6 self-made synth WAVs (48 kHz mono, -14 LUFS M-max, ≤ -1 dBTP). Sound critic 8/10 after 2 passes;
**no human has heard them and none are uploaded**. They play on legacy Sound/SoundGroup (RR_Sound runtime, scripted ducking).

## A. Engine
| item | fact | source · conf |
|---|---|---|
| Audio API objects | AudioPlayer, AudioEmitter, AudioListener, AudioDeviceOutput/Input, Wire. Effects: AudioFader, AudioEqualizer (3-band, MidRange), AudioFilter (type/freq/Q/gain), AudioCompressor, AudioLimiter (MaxLevel, Release), AudioReverb (full: decay, density, diffusion, low shelf, HF cut), AudioEcho, AudioDistortion (Level 0-1), AudioPitchShifter (Pitch 0.5-2, WindowSize), AudioChorus, AudioFlanger, AudioTremolo, AudioGate, AudioChannelMixer/Splitter. + AudioAnalyzer (Peak/Rms/spectrum) | docs reference/engine/classes/Audio*.yaml · H |
| Sidechain | **Yes.** AudioCompressor has Input, **Sidechain** and Output pins, so true wire-based ducking works | AudioCompressor.yaml · H |
| Time-stretch | **No time-stretch object.** Speed without a pitch change = PlaybackSpeed plus an AudioPitchShifter that counters it (0.5-2 only, artefacts likely), or pre-rendered stretched variants | class list · H (no class); quality L |
| Attenuation | AudioEmitter.DistanceAttenuationMode: Custom (default; SetDistanceAttenuation takes a distance→volume table), Inverse, InverseTapered, Linear, LinearSquared, with Bounds (default 4-10000 studs). AngleAttenuation (directional) on emitters and listeners | AudioEmitter.yaml, enums/DistanceAttenuationMode · H |
| Acoustic sim | AcousticSimulationEnabled on emitter **and** listener: automatic occlusion, diffraction (shortest path only) and reverb, **Audio API only**. Studio beta Jan 2026; live in published places is L. SimulationFidelity is deprecated. Low value here: the train is the set and the world scrolls | AudioEmitter.yaml (H); devforum t/3634265 (M) |
| Legacy vs new | Docs: "Sound, SoundGroup and SoundEffect objects are now discouraged in favor of audio objects". Sound has **no wire pins**, so a legacy Sound cannot pass through Audio API effects or feed a sidechain. Both systems play at once and share one engine | audio/objects.md, Sound.yaml (H); shared engine: devforum t/3928632 (M) |
| Mixing consequence | An Audio API sidechain cannot duck legacy SoundGroups, so mixed setups need scripted ducking (as v1 RR_Sound does). Toolbox inserts still create Sound | inference · M |
| Client/server | Listener auto-created per client (SoundService.DefaultListenerLocation: Camera/Character/None). Legacy: Play() from a LocalScript is heard only on that client (RespectFilteringEnabled) | SoundService.yaml (H), rr-bible tech.audio.local_playback |
| Voices | **No documented voice cap and no priority property** (none on Sound, AudioPlayer, SoundGroup or emitter). Devforum: about 300 sources linked to emitters, past which some stop playing; 1000+ AudioPlayers cause Sound-task spikes. Voice stealing must be our own Lua pool. Phone budget unknown: v1 assumed 16 one-shots | devforum t/3928632 · M; phone cap L |
| Pitch / slow-mo | AudioPlayer.PlaybackSpeed 0-20 (speed and pitch coupled); Sound.PlaybackSpeed likewise. AudioPlayer.Volume 0-10 | AudioPlayer.yaml · H |
| Preload | ContentProvider:PreloadAsync(instances) yields until the content loads (Sound named; AudioPlayer.Asset is a content property → L). AudioPlayer.AutoLoad + IsReady. An unloaded sound misses its first play | ContentProvider.yaml, AudioPlayer.yaml · H |
| Loops / regions | Looping, LoopRegion and PlaybackRegion on AudioPlayer and on Sound. **Several variations can share one asset as a "sound sheet"**, which saves imports and preloads | AudioPlayer.yaml, Sound.yaml · H |

## B. Assets
| item | fact | conf |
|---|---|---|
| Formats | mp3, ogg, wav, flac; a single track; < 20 MB and < 7 min; ≤ 48 kHz; mono, 2.0, 3.0 or 5.1. Studio transcodes on import | docs audio/assets.md · H |
| Quota / cost | **Free.** 2,000 imports per 30 days if ID-verified, 100 if not | H |
| Upload routes | Asset Manager, Creator Dashboard, **Open Cloud Assets API** (POST apis.roblox.com/assets/v1/assets with an API key; apis.roblox.com is blocked here) | H |
| Moderation | Uploads are moderated before use: usually minutes to hours; devforum reports of items stuck for months. Copyright fingerprinting runs on uploads | devforum t/4734119, t/1589251 · M |
| Privacy | Uploads are private to the owner by default. Grant use to specific experiences or friends through asset privacy | H |

## C. Licence-clean sources (canon av.audio.licence: self-made, commissioned, CC0, purchased with a game licence, Roblox-licensed)
| source | commercial · attribution · in a game | allowed by canon? | fetch: owner / this session | conf |
|---|---|---|---|---|
| Roblox Creator Store (Roblox + partners) | free, no credit; licensed **only inside Roblox** (no trailers or ads off-platform) | yes (`roblox_licensed`); community uploads refused (OQ-036) | owner in Studio Toolbox / no | H (docs), off-platform limit M |
| Sonniss GDC bundles | royalty-free, commercial, **no attribution**, unlimited projects; no AI training; raw files never redistributed except inside a project | yes (purchased/free-licence class) - keep assets private, never on the Creator Store | owner (large download) / **no** (sonniss.com blocked) | M |
| Freesound CC0 | public domain | yes | owner / no (freesound.org blocked; API needs a token for originals) | M |
| Freesound CC-BY | commercial OK with credit | **not under current canon** (CC-BY is refused): an owner decision | owner / no | M |
| Freesound CC-BY-NC, Sampling+ | **NOT ALLOWED** (non-commercial) | refused | - | M |
| Zapsplat free | commercial, **credit required** | not under canon unless the owner extends it | owner / no (blocked) | M |
| Zapsplat Gold (paid) | no attribution, also for past Gold downloads | yes (purchased) | owner / no | M |
| Pixabay SFX | Pixabay Content Licence: commercial, no credit, no standalone resale. Uploader provenance varies (rip risk) | owner decision (not CC0; a game-use licence) | owner / no (blocked) | M |
| BBC Sound Effects (RemArc) | **NOT ALLOWED**: personal, educational and research use only. Commercial use goes through a paid BBC licence or Pro Sound Effects | refused | - | M |
| Soundly Free/Pro | cleared for commercial games; games made while subscribed stay cleared. Freesound add-on: CC0 only | yes (purchased/licensed) | owner (desktop app) / no | M |
| BOOM Library (paid; some free) | media licence that covers games; free packs commercial with no credit; no raw redistribution | yes (purchased) | owner / no | M |
| Pro Sound Effects (paid) | commercial game licences, includes the BBC library | yes (purchased) | owner / no | M (price L) |
| GitHub-hosted CC0 packs | e.g. Kenney starter kits: README says sounds are CC0, repo LICENSE is MIT | yes, with the proof kept | **yes: git and raw.githubusercontent.com work** | H (tested) |

## D. Production recipe (event → layers; cite: industry practice, M)
| event | layers (t 0 = hit) |
|---|---|
| metal stress/creak | low groans (modal resonances 80-400 Hz, slow pitch bends) + high squeals + rivet ticks; builds 1-3 s before 70%/30% |
| tear/rip | sharp crack (2-6 kHz transient) + ripping sheet-metal noise burst + rivet pops in a short sequence + low thump |
| glass | initial break + shard tinkle tail (several random 3-8 kHz grains) + falling bits 0.3-1 s |
| explosion | **crack** (0-20 ms) + **body/pressure** (60-250 Hz, 0.1-0.5 s) + **sub thump** (30-60 Hz) + **tail/roll** (2-6 s) + debris. Distances: close = full crack; mid = less HF; far = low roll + delay (~1 s per 343 m, sound slower than light) |
| crash · debris · fire | crunch + thud + metal ring-out · 1-3 s of scattered small hits, dense to sparse · crackle grains + roar bed (loop -20 LUFS integrated) |
| scrape/drag | looped grind with pitch and volume tied to speed; sparks hiss layer |
| alarm/siren | PROPOSED only (the owner did not ask) |
| ragdoll/fling | whoosh tied to speed (PlaybackSpeed by velocity) + body impacts in 3 tiers + **comedic sweeteners** (boing, slide whistle, cartoon pop): slapstick canon (av.audio.slapstick) |
- **Variation:** 3-6 round-robin variants for each frequent sound, pitch ±3-5 %, gain ±1.5 dB, never the same variant twice in a row. Pack the variants in one asset with PlaybackRegion.
- **Pre-boom duck:** 100-250 ms of near-silence or a strong duck (ambient and music) before the 0 % boom; a sidechain does it natively in the Audio API.
- **Phone low end:** the phone band is about 300 Hz-8 kHz (soundsmith model: HP 450 Hz). Add harmonic saturation to the body and sub (2nd and 3rd harmonics) so the "missing fundamental" is still felt, and keep a 150-400 Hz punch layer. Check each sound against the soundsmith phone-loss model.
- **Loudness:** canon (proposed) one-shots -14 LUFS M-max, loops -20 integrated, ≤ -1 dBTP. Industry: ASWG-R001 -24 LUFS for console (M), -18 for portable (L). Roblox publishes no loudness target (L).
- **Slow-mo:** pitch down 0.5-0.8 (coupled), or pre-render time-stretched variants offline (better). Low-pass the world and keep the comedic layer dry.
- **Priority / stealing:** no engine priority, so a Lua pool per bus with tiers (boom > tear > crash > debris > whoosh). Steal the oldest or quietest at the lowest tier and cap each sound at half its group.

## E. Tools in this session (tested 2026-10-06)
| tool | result |
|---|---|
| pip install pyloudnorm 0.2.0 · soundfile 0.14.0 (libsndfile 1.2.2) · pedalboard 0.9.25 · librosa 0.11.0 · scipy 1.17.1 | **all installed and imported cleanly**; numpy stayed 1.26.4. Not persistent: a new session must reinstall (add them to the env setup script) |
| encoders | soundfile writes **OGG Vorbis and FLAC**; pedalboard writes **MP3**. This removes v1's "no .ogg" limit |
| pedalboard effects tested | HPF, Distortion, Compressor, Reverb, Convolution (custom IRs), PitchShift, Limiter, Chorus, Phaser, Bitcrush, Delay, LadderFilter, time_stretch, all OK. pedalboard is GPL-3: fine for tools, and the audio it renders is not GPL |
| WebFetch audio download | **No.** WebFetch is blocked for create.roblox.com, sonniss, zapsplat, pixabay and upload.wikimedia. bbcrewind failed. WebFetch returns text, not binaries |
| shell download | freesound, sonniss, pixabay, zapsplat, wikimedia, archive.org, opengameart and kenney.nl all fail (CONNECT 403). **GitHub works**: pulled Kenney `break.ogg` (10.8 KB, OGG 44.1 kHz stereo, -18.0 LUFS, -1.26 dBFS peak) and measured it, then **deleted** it |
| synthesis judgement | numpy + pedalboard can make production-grade **sub booms, rumble, whooshes, fire beds, alarms, noise debris, cartoon sweeteners** and passable modal metal clanks or creaks. It is **weak** at realistic glass, a complex metal tear, crunchy collapse and anything vocal. v1's 8/10 was a model critic, not ears. "Best ever" needs recorded sources layered with synthesised low end and sweeteners |

## Honest path to "best sounds ever"
- **Claude here:** design layer specs and briefs; synthesise sub, whoosh, sweetener and fire layers; layer, edit, saturate and level recorded material; render round-robin and distance variants and sound sheets as OGG; measure LUFS, true peak and phone loss; write the Audio API wiring (sidechain duck, bus faders, Lua voice pool).
- **Needs the owner (free):** download recorded sources (Sonniss GDC bundles are free with no attribution; Freesound CC0) and drop a curated subset into the repo, or widen the network policy for freesound.org and cdn.freesound.org.
- **Needs the owner:** upload to Roblox (quota 2,000 per 30 days, moderation), grant the experience access, and run listening tests on **his phone speaker and on headphones**. Claude cannot hear: every "sounds good" before that is a measurement or a model's opinion.
- **Owner decisions:** extend the canon licence to CC-BY, Zapsplat free or Pixabay? (default: no, stay CC0 + purchased). Move the split system to the Audio API? (default: yes for v2 split audio, keeping legacy Sound for everything else, with scripted cross-ducking).
- **Paid, optional:** a pack such as BOOM or Pro Sound Effects destruction/metal/glass titles (est. tens to low hundreds of USD, L) lifts glass and tear realism most. Soundly Pro is an alternative.
- **Human ears, PROPOSED:** for a true "best ever" bar, a short commissioned pass by a game sound designer on the 3 hero sounds (70 % split, 30 % split, 0 % explosion). Default: not needed for v2 if the Sonniss + synth hybrid passes the owner's phone test.
