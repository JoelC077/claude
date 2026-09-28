# soundmap.json and assets.json

Read before editing presets. `soundmap.json` is design (hand-edited); `assets.json` is the register (written only by
`sound.py register`). Canon numbers are `{"v": n, "canon": "key"}` (a list of keys takes a list of values); `validate`
proves each number appears in the canon value. Never restate canon prose here; cite keys in `canon` lists.

## Top level
| key | what |
|---|---|
| `meta` | `sample_rate` (placeholders), `ref_volume` (Sound.Volume that plays a file at its measured level; assumed 0.5), `stud_m`, `train_len`, `danger_life_ms` (canon), `canon`, `oq` |
| `platform` | Roblox import limits (`max_mb`, `max_min`, `max_khz` cite tech.audio.import_limits), `channels`, `formats` |
| `standards` | per class (`oneshot`, `ui`, `alarm`, `impact`, `loop`, `music`): `metric` (`m_max` or `integrated`), `target` LUFS, `tol`, `tp_max` dBTP, `len` [min, max] s, `lead_max_ms`, `tail_max_ms`, `seam`, `phone_loss_max` dB. See standards.md |
| `ladder` | in-game level per tier: `t1`..`t5` (momentary max), `ambient`, `music` (integrated); `trim_max_db`; `overlap_lu` (how far a lower tier may exceed a higher one) |
| `groups` | SoundGroup tree: `{name: {parent, setting?, note}}`; one root `Master`; `setting` names a player setting |
| `settings` | default 0..1 per setting (master, sfx, ambient, music) |
| `voices` | `max` one-shots at once, `per_group` caps, `steal` (tier_then_oldest), `protect_tier` (tiers at or under it are never dropped) |
| `ducking` | rules: `name`, `when` {`sounds`: [...], `groups`: [...]}, `duck` {group: dB}, `attack`, `hold`, `release` (s). A rule may not duck a group holding its own trigger |
| `spatial` | roll-off presets: `mode` (Enum.RollOffMode), `min`, `max` studs |
| `emitters` | role -> where it is on the train; the runtime maps roles to instances (`Sound.setEmitter`) |
| `speed_link` | `sound` (looped), `ref` and `speeds` (canon), `rate` [lo, hi] PlaybackSpeed clamp, `gain_slope` (dB per dB of Speed ratio), `silent_below` studs/s |
| `sounds` | see below |
| `events` | event -> one action: `play`, `start` [...], `stop` [...] or `toggle`; `via` `feel` (played by RR_Feel's cue; name = the rr-game-feel event) or `direct` (`Sound.event(name)`); optional `pitch`, `pitch_step` (per repeat within 1.5 s) |

## A sound
```json
"lever_clunk": {"tier": 3, "group": "Actions", "class": "oneshot", "space": "3d", "emitter": "lever",
  "spatial": "near", "stage": "alpha", "voices": 2, "cooldown": 0.08, "pitch": [0.96, 1.04], "trim_db": 0,
  "canon": ["gameplay.fork.lever"], "oq": ["OQ-031"],
  "brief": {"moment": "...", "must_say": "...", "sounds_like": "...", "layers": ["..."], "avoid": "...",
            "len": [0.35, 0.6], "variations": 3}}
```
- `tier` 1 fail, 2 crisis, 3 commit, 4 reward and actions, 5 UI, 6 ambient loops, 7 music. Match the rr-game-feel
  priority of the events that cue it (validate warns otherwise). Groups: Alarms 1-2, Actions 3-4, UI 5, Ambient 6, Music 7.
- `space` `2d` (global, fixed pan) or `3d` (needs `emitter` and a `spatial` preset). `layer3d` {emitter, gain_db, spatial}
  adds a quieter positional copy to a 2D sound (alarms, OQ-035 default A).
- `looped` true for `loop` and `music` classes (keyed, never stolen). `stage` `alpha` or `siding` (release gate
  covers alpha only). `trim_db` within `ladder.trim_max_db`: taste, not hierarchy.
- The id is the rr-game-feel cue name when a feel event cues it; `validate` checks both files agree.
- Every sound needs a `brief` (sourcing) and should have a synth recipe (`synth.py --list`).

## assets.json (script-written)
```json
"lever_clunk": {"ids": ["rbxassetid://111"], "source": "placeholder", "origin": "rr-soundsmith synth",
  "licence": "", "proof": "", "credit": "", "creator": "", "community": false,
  "files": ["PLACEHOLDER_lever_clunk.wav"], "sha1": ["324c2e0ebd81"],
  "measured": [{"m_max": -14.03, "integrated": -16.6, "true_peak": -1.77, "duration": 0.5, "phone_loss_db": 2.3}],
  "registered": "2026-09-28"}
```
The mean measured level of the files sets Volume: `Volume = ref_volume x 10^((ladder + trim - level) / 20)`, clamped
to 10 (validate fails a sound that would need more). No file (Roblox-licensed by id only): the class target is assumed.

## Mission use
Copy `presets/` to `<M>/src/sound/` and `export RR_SOUND_PRESETS=<M>/src/sound`; every command then reads and writes
there. Placeholders in `<M>/src/sound/ph/`, sheets in `<M>/src/sound/sheet/`, export in `<M>/export/sound/`.
