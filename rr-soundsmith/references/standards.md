# File standard, measurement and mix rules

Canon: `bible.py get av.audio.file_standard` (proposed). This file explains how it is measured and why.

## Why one standard per class and the mix in data
Every file is levelled to its class standard; the hierarchy lives in `ladder` and each Sound's Volume is computed from
the file's measured level. Rebalancing is a data change and a rebuild, never a re-upload (Roblox import quota and
moderation delay: `bible.py get tech.audio.import_quota`). Files that miss the standard still work: `register` records
the measured level and the mix compensates; the standard exists for headroom and consistency.

## How audiolib measures (ITU-R BS.1770-4, EBU R128 terms)
- K-weighting: the two BS.1770 biquads derived for any sample rate (equal to the spec tables at 48 kHz).
- **Momentary max (m_max):** highest 400 ms block (100 ms hop). One-shots use it: it tracks how hard the sound hits.
  Files under 400 ms are zero-padded to one block, so very short clicks read lower than they feel; the UI class
  standard (-20) accounts for it.
- **Integrated:** gated mean (absolute -70 LUFS, relative -10 LU). Loops and music use it.
- **Short-term max and LRA:** 3 s blocks; LRA = 95th minus 10th percentile after a -20 LU relative gate.
- **Mono counts as dual mono** (+3.01 dB: heard on two speakers), so mono SFX and stereo beds compare fairly.
- **True peak:** 4x oversampled (windowed-sinc polyphase); without numpy only the sample peak is reported, labelled.
- Verified in selftest on EBU Tech 3341 cases 1-4 (within 0.1 LU) and a 3342 LRA case (10 LU).
- **Phone loss:** momentary max lost through a rough phone-speaker model (4th-order high-pass at 450 Hz, 2nd-order
  low-pass at 10 kHz). A model, not a device: the owner's phone decides (fidelity.md).
- **Loop seam:** the last->first step against the largest step within 20 ms either side (a click shows as over 2x
  with a jump over 0.01). Edge level difference is reported for information only (rhythmic loops differ by design).
- Silence threshold -60 dBFS (lead and tail), clipping = 3 or more consecutive samples at 0.9995 of full scale,
  DC offset = channel mean.

## What analyze fails and warns
| FAIL (fix the file) | WARN (fix or accept; the mix compensates level) |
|---|---|
| format not wav/mp3/ogg/flac, over 20 MB or 7 min, over 48 kHz, channel count not 1/2/3/6 | under 44.1 kHz, 8-bit |
| clipping, peak over 0 dBTP | peak above the class ceiling (-1 dBTP) |
| more than 50 ms of silence before the sound (it feels late) | lead or tail silence over the class limit, length outside the class range |
| loop seam click | level outside target +- tol, DC offset, phone loss over the class limit, stereo on a 3D sound, negative L/R correlation |

Without a decoder (.ogg/.mp3/.flac and no ffmpeg) only format, length, rate and channels are read from the header.
`--fix-out DIR` writes `<name>_std.wav` (24-bit): trims long lead/tail silence of one-shots, `--mono` downmixes
(keeps the louder channel when the channels cancel), then gain toward the target within the peak ceiling (max +30 dB).
It never touches the source, keeps the INFO tags (a placeholder stays tagged), refuses clipped or over-48 kHz files
(re-export those) and needs numpy for trimming and mono (without it: gain only).

## Mix rules (checked by validate)
- Ladder order t1 >= t2 >= t3 >= t4 >= t5 >= ambient; no one-shot louder than a more important tier by over `overlap_lu`.
- Ducking: -40..0 dB, attack 5 ms-1 s, release 50 ms-5 s, never ducking the trigger's own group; every trigger should
  clear the ducked sounds by 3 LU or more.
- Volume = `ref_volume x 10^(gain/20)` must stay at or under 10 (Sound.Volume range, tech.audio.volume).
- Voices: 16 one-shots, Alarms 4, Actions 8, UI 4 (assumed for phones; the owner's Studio test decides).
