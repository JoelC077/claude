# Security review pack · rr-exploit-guard

You are an independent security reviewer for a Roblox game (Risky Rails). You did not write this code.
Assume the client is fully hostile: it fires any remote, any number of times, with any arguments (the first handler argument, the Player, is the only thing it cannot forge).
For each item decide SAFE (no exploitable path), VULN (name the path) or UNSURE (what you would need).
The scanner's findings are hints, not verdicts: confirm or reject them; 'trusted by name' validators and Guard specs are only names, so read them. Do not edit code. Write `verdict.md` next to this file in exactly this format (fill in `reviewer:`; `independent: yes` only if you neither wrote nor fixed this code):

```
reviewer: <your agent id or name>
independent: yes
scan: 25ffd7857bea
R01 | SAFE | <= 25 words, cite file:line
R02 | VULN | <the exploit path, file:line>
NEW: <file:line> | <critical|high|medium> | <a problem the scanner missed>
```

Ask of every item: If an exploiter sends any values 1000 times a second, what is the worst outcome?

Scan: 2026-09-29T23:50:38+00:00 · 20 files · 0 items · inputs sha256 25ffd7857bea

No entry points take client values and nothing sensitive was found: nothing to review.
