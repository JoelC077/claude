# Audio brief format (for sourcing)

`sound.py brief ID|all` generates one brief per sound from soundmap.json, the standards and canon. Use it to search a
library, commission a sound designer, record foley or direct a replacement placeholder. Edit the soundmap, not the
generated text, so the brief and the mix never disagree.

## Fields (and why each is there)
| field | from | why |
|---|---|---|
| header: id, tier, group, class, asset state | soundmap, assets.json | the file name the owner delivers and how important it is |
| Moment | brief.moment + events (+ the feel beat, e.g. "lands with a 70 ms hit-stop") | what happens on screen when it plays |
| Must say | brief.must_say | the one message; judged first |
| Sounds like | brief.sounds_like | concrete references a designer can search or perform |
| Layers | brief.layers | how to build it; also what to keep when trimming |
| Length | brief.len + class standard | attack within the lead limit, tail limit, or "seamless loop" |
| Variations | brief.variations + runtime pitch spread | how many takes to deliver; the runtime adds pitch spread |
| Space | space, emitter, layer3d | mono for anything positional; dry, 44.1 or 48 kHz WAV, 16 or 24-bit |
| Level | class standard + ladder | normalise to the standard; the mix sets the in-game level |
| Phones | phone_loss_max | energy in 0.5-4 kHz so it survives phone speakers |
| Avoid | brief.avoid + tone canon | what would make it read wrong (horror, realism, another sound's job) |
| Licence | av.audio.licence | the gate in licensing.md |
| Done when | analyze -> register -> build | the objective check |
| Canon, Open | canon keys, OQ ids | the facts it serves and the defaults in use |

## Writing good brief text (in soundmap.json)
- `must_say` is a player's thought in a few words ("the fire is dying, go shovel"), not a sound description.
- `sounds_like` names 2-3 real, searchable sounds; never a copyrighted track or another game's asset.
- Distinctness: crisis alarms must differ in rhythm and band (av.audio.priority); say which sibling it must not
  resemble in `avoid`.
- Keep lengths inside the class standard; alarms under the danger ticket life (gameplay.alerts.life_danger_ms).
