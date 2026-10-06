# Start Train Split v2 in a local chat

## 1. Get the files (terminal, in your clone of JoelC077/claude)
```
git fetch origin
git checkout claude/zealous-newton-h08ds8
git pull
```
Everything is in `missions/261006-train-splits-v2/`. Start with `ROADMAP.md`.

## 2. Tools (install once; the first session can check these for you)
- Python 3.11+, then:
  `pip install pyloudnorm soundfile pedalboard librosa scipy zstandard imageio-ffmpeg numpy pillow bpy`
- Lune 0.10.x (offline Luau tests): https://github.com/lune-org/lune
- Optional: Roblox Studio MCP, so Claude can drive Studio itself.
- Optional: open Studio with a **copy** of your place.

## 3. Paste this as the first message
```
Resume JARVIS mission 261006-train-splits-v2, session 1 (use rr-mission-control).
Branch: claude/zealous-newton-h08ds8. Read missions/261006-train-splits-v2/ROADMAP.md, mission.md and state.json first.
Running locally: Studio is open with a copy of my place (Studio MCP: yes/no).
If the MCP is connected, read the place directly instead of asking for an export.
My answers:
Q1 (alpha week of 12 Oct, v2 after it): ...
Q2 (sound sources A/B/C): ...
Q3 (extras a-f): ...
(a) did "[TrainSplitDemo] ready" ever print: ...
(b) Client or Server view when I set RR_TestBreak: ...
(c) can integrity go back up: ...
(d) does each run clone a fresh train: ...
Push to this branch at the end of every session.
```
Or type `go` instead of the answers to take the defaults.

## 4. Before or alongside
- Make the repo private: GitHub > Settings > General > Danger Zone.
- If your alpha is the week of 12 Oct, see "Before the alpha" in ROADMAP.md.
