# PLACEHOLDER SFX (rr-soundsmith)

Synthesised 2026-09-28 from code only (no samples, so no third-party rights). For prototyping timing and mix in Studio. Never ship: `sound.py validate --release` fails while an alpha sound uses one.

Owner, to hear them in Studio: import in Asset Manager (name them `PLACEHOLDER <id>`), then `sound.py register <id> --file <this folder>/PLACEHOLDER_<id>.wav --id <asset id> --source placeholder --origin "rr-soundsmith synth"` and `sound.py build`.

| id | file | s | level | TP | phone loss | check | sha1 |
|---|---|---|---|---|---|---|---|
| alarm_coal | PLACEHOLDER_alarm_coal.wav | 1.70 | -14.0 m_max | -14.55 | 2.51 dB | PASS | 2945921ff47b |
| lever_clunk | PLACEHOLDER_lever_clunk.wav | 0.50 | -14.03 m_max | -1.41 | 2.32 dB | PASS | 324c2e0ebd81 |
| brake_hiss | PLACEHOLDER_brake_hiss.wav | 1.60 | -14.0 m_max | -6.77 | 1.27 dB | PASS | a6d09cbdef2c |
| whistle | PLACEHOLDER_whistle.wav | 1.80 | -14.0 m_max | -6.92 | 0.46 dB | PASS | de7962988f46 |
| lobby_bed | PLACEHOLDER_lobby_bed.wav | 12.00 | -20.0 integrated | -8.88 | 0.87 dB | PASS | 31b780b202cb |
