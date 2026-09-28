#!/usr/bin/env bash
# UserPromptSubmit hook: adds a one-line JARVIS reminder when the prompt looks like Risky Rails work.
p="$(cat)"
if printf '%s' "$p" | grep -qiE 'risky ?rails|roblox|studio|\bloco|locomotive|\btrain\b|wagon|coach|depot|\bhud\b|lever|crate|\bfare\b|robux|exploit|thumbnail|patch notes|ship v[0-9]'; then
  echo "JARVIS: this looks like Risky Rails work. Start with the rr-mission-control skill and let it route."
fi
exit 0
