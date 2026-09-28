# Optional: Claude Code prompt hook (not installed)

1. `mkdir -p ~/.claude/hooks && cp jarvis-hook.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/jarvis-hook.sh`
2. Merge `settings.fragment.json` into `~/.claude/settings.json` (keep any existing hooks; add this entry to the UserPromptSubmit array).
3. Test: `echo '{"prompt":"make me a coal wagon"}' | ~/.claude/hooks/jarvis-hook.sh` prints the reminder; `echo '{"prompt":"fix my tax spreadsheet"}' | ...` prints nothing.
Remove: delete the entry from settings.json. Stdout of a UserPromptSubmit hook is added as context; the hook never blocks a prompt.
