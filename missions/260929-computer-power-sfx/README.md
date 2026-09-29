# Retro computer power up / power down (1.0 s each)

| File | What you hear | m_max | True peak | Phone loss |
|---|---|---|---|---|
| `PLACEHOLDER_computer_power_up.wav` | switch click, power-supply whine spinning up, square-wave arpeggio C5-E5-G5-C6 with chip echo, held "ta-da" C major chord (scoops into pitch, vibrato) with a sparkle | -14.0 LUFS | -4.94 dBTP | 1.97 dB |
| `PLACEHOLDER_computer_power_down.wav` | same arpeggio falling, wobbly droopy pitch dive (cartoon "shrink") with a collapsing CRT whine, off-switch click | -14.0 LUFS | -4.59 dBTP | 0.98 dB |

48 kHz mono 16-bit, one-shot standard (av.audio.file_standard); `sound.py analyze`: 2 pass, 0 warn, 0 fail.
Regenerate or tweak: `python3 computer_power_sfx.py` (deterministic; needs rr-soundsmith and numpy).

Synthesised from code, no samples, so there are no third-party rights. The `PLACEHOLDER_` name follows
av.audio.placeholder. To ship them, rename the files, then register them as `--origin self-made`
(`sound.py register`) after uploading. That is the owner's call. The Studio listening test is still pending.
