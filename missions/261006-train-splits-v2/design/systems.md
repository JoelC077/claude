# P8 design: systems, integration and quality gates (train splits v2)
Planning only. Paths M, V1, SK as in refs/context.md. `guard`, `rel`, `bible` = the rr-exploit-guard, rr-release-train,
rr-bible scripts. est. = estimate · U = unverified · P = PROPOSED (owner decides) · C = CORE (L2-L11).

## 1. Kickoff intake (first owner session, ~20 min est.)
| # | export | how (Studio) | why |
|---|---|---|---|
| E1 | whole place, **.rbxlx** (best: one file has everything) | File > Save to File As > type .rbxlx, on a copy | scripts + Diesel + flow in one; `placefile.py` reads it (also binary .rbxl; ZSTD needs `pip install zstandard`) |
| E2 | if E1 is too big or private: integrity system (all scripts/modules it uses) | select in Explorer > right-click > Save to File > .rbxmx | the API we bind to |
| E3 | the "universal compatibility" event layer + train-select/spawn code | same, .rbxmx | how trains are cloned and how events find carriages |
| E4 | DieselTrain model **and** its split code/labels | same, .rbxmx (model incl. children) | decide `presplit` vs `external` mode (§2) |
| E5 | TrainSplit modules as installed now (RS.Modules.TrainSplit, SSS.Scripts.TrainSystems, client script) | same, .rbxmx | diff vs V1/export (he may have edited them) |
| E6 | round / game-over flow + world-scroll driver | same, .rbxmx | 0% hand-off, stopping the scroll |
| E7 | 4 answers: did "[TrainSplitDemo] ready" print? which view (Client/Server) set RR_TestBreak? can integrity go back up? does a new run clone a fresh train? | type in chat | §3 root cause, reset design |
Scripts pasted as text (.lua) are fine for E2/E3/E5/E6; models need .rbxmx/.rbxlx.
**Upload** (pick one): (a) GitHub web: repo JoelC077/claude > `missions/261006-train-splits-v2/intake/` > Add file >
Upload files (browser limit 25 MB per file, U); (b) Google Drive folder `RR intake` (this session has a Drive connector;
reading binaries through it: U); (c) attach in the claude.ai/code chat (size limit U). Never put API keys in the files.
**Claude's first moves:** I1 extract scripts to `M/intake/scripts/` (placefile.py) + inventory (integrity API, signals,
train naming, Diesel part tree) → diff E5 against V1/export/studio and V1/src/luau → `M/design/contract.md` (frozen
version of §2 with the real names) → owner OKs it → build.

## 2. Integration contract (proposed)
**Ownership.** Joel's integrity system is the only writer of integrity; TrainSplit never writes it. One adapter file,
`SSS.Scripts.TrainSystems.TrainIntegrityBridge`, is the only code that touches his API, so his changes cost one file.
| item | rule |
|---|---|
| input | bridge binds whichever exists (I1 decides): (A) server attribute `Integrity` (0-100) on the train model, via GetAttributeChangedSignal; (B) his signal/callback calling `TrainSplit.OnIntegrity(train, value, cause)` |
| stages (per-train config) | `stages = {{id="split_c2", at=70, kind="split", brk=2}, {id="split_c1", at=30, kind="split", brk=1}, {id="destroy", at=0, kind="destroy"}}`; fire when `value <= at` (inclusive, C: L4-L7) |
| once | state per train `Intact → S70 → S30 → Destroyed`, stored as server attribute `RR_SplitStage`; a fired stage never re-fires; a rise in integrity never re-arms (default) |
| multi-cross | one hit past several stages → all fire in order, `stagger_s` apart (default 1.2 s est.; 0% keeps its own -0.2 s inhale only) |
| order | 70 always before 30 before 0, even if 30 is crossed first in a skipped frame |
| warning (P) | entering `at + warn_band` (default 5 pts est.) sends `warn` (P5/P6 beats); re-arms with 2-pt hysteresis; skipped when staggering |
| reset | `TrainSplit.Reset(train)`: cancel timers, destroy wrecks/chunks, clear state. Respawn = new train instance from the template (preferred). Same-model reuse needs `Arm()` snapshot/restore (only if E7 says so) |
| arm | `TrainSplit.Arm(train)` from Joel's spawn/select event (E3); tag `RR_Train`; refuses loud if the profile has no breaks |
| outputs (server→server) | BindableEvents `StageReached(train, id, info)`, `Snapped`, `Despawned`, `TrainDestroyed(train, t0)`, `SequenceDone(train)`; queries `GetStage`, `IsSectionPresent(train, carriage, half)` |
| 0% hand-off | at `destroy`: train anchored, scroll braked to 0 by +3 s via the bridge (E6 driver), `TrainDestroyed` fires; Joel's round flow ends the run on `SequenceDone` (+8 s, P5) or a 12 s timeout (est.). His flow must not reset the train before that |
| his events (L3) | lost parts get `RR_Lost=true` and leave the train model at despawn; his event layer skips targets where `IsSectionPresent` is false (I1 checks his path-based lookups) |
| fling | target pick = server (v1 ConfirmRiders: riders behind the plane + blast radius); impulse execution = owning client (P7 owns the numbers) |
**Remote (server→client only).** One RemoteEvent `RR_TrainSplitFX`, payload `{v=2, train, stage, seed, t0
(GetServerTimeNow + lead), lost={part ids}, chunks, flavour, fling={[userId]={dir, mag≤cap}}}`. Clients schedule fx,
sound and motion from t0 (P5/P6). `OnServerEvent` only flags misuse (v1). Late joiners read `RR_SplitStage` and wreck
attributes; nothing asks the server.
**Per-train profile registry** (`TrainSplitConfig.Trains[profile]`, profile = train attribute `RR_TrainProfile`, else
model name, else `generic`):
| key | Coal | Diesel | generic |
|---|---|---|---|
| `breaks.mode` | `tear` (v1 CSG, break_spec v2.3 cells) | `presplit` (Joel's halves mapped to RR_Half) or `external` (his split code moves parts, v2 adds fx/sound/fling via `TrainSplit.PlayStage`), I1 picks | `plane` (flat cut, P5 look) |
| `breaks.frames` | `RR_BreakN` Attachments written by Setup v2 | his labels → `RR_BreakN` | bbox centre of each carriage |
| `carriages` | auto: `RR_Carriage` attribute, else name order front→rear, N ≥ 1 | same | same |
| `stages`, `stagger_s`, `warn_band` | 70/30/0 | 70/30/0 | 70/30/0 |
| `chunks` (0%) | RR_Chunk → halves + loco/tender → ≥ 20-stud slices, cap 6 phone / 8 PC (P5) | same | same |
| `flavour`, `heart`, `blast_scale`, `sound_flavour` | coal / boiler | diesel / fuel tank | coal |
| `topple` | pivot from body bbox (replaces fixed 11.7/-8.6) | same | same |
**What it replaces:** ROOF_SIG and BREAK_DZ/FLOOR_DY/CROSS_DX → `RR_BreakN` markers (Setup v2 places them; Checker
suggests a band); `for k = 1, 2` loops → iterate markers; Shared.lostHalves → `lostSet(chain, fired)` for any order and N;
the whole-carriage topple entry for a half body → per-body topple from its bbox; Setup/Config cell mismatch → one cell
table per profile generated by break_spec.py; `EXPECTED_CROSSERS` → a per-profile range with a printed count.

## 3. Root cause of v1's silent test, and the v2 fix
Ranked causes (refs/v1-kit §5): 1 attribute set in Client view; 2 install-path mismatch → WaitForChild yields forever;
3 runtime train is a clone without RR_Breaks; 4 parts held by other joints/scripts (IN_PLACE) and empty SoundIds;
5 same value set twice. E7 answers confirm which. **Class of failure: silent preconditions.** v2 rules:
- No unbounded WaitForChild: every lookup `find(path, 5 s)` then `error("[TS2] missing <path>: install step N")`.
- Boot self-check prints one line per step: `[TS2 1/7] modules ok v2.0.0 · 2/7 remote ok · 3/7 profiles: CoalTrain,
  DieselTrain · 4/7 bridge bound to Integrity attr · 5/7 armed <train> breaks=2 carriages=2 · ...`; client prints
  `[TS2-C]` steps (seen in Client view or F9).
- `TrainSplit.Diagnose(train)` returns and prints PASS/FAIL per precondition: profile, markers, RR_Half counts, joints
  that would hold lost parts, Speed attr, SoundIds empty, remote, clients ready, reduce-motion state.
- **Test bench `RR_SplitBench`** (server Script): `Bench.set(train, value)`, `Bench.drop(train, from, to)` (multi-cross),
  `Bench.reset(train)`, `Bench.run("all")` (70 → 30 → 0 with pauses), each printing every step, run from the command
  bar in **Server** view (it prints `IsServer()` and refuses on the client). An integrity slider ScreenGui (P) exists
  only when `RunService:IsStudio()`; its remote is never created outside Studio. In live: owner-UserId admin command
  only (tech.security.admin), behind `Config.Debug`, which the release gate (I14) requires to be false.

## 4. Test strategy
**Lune (offline, every session).** `lune run tests/run_tests.luau` in `M/src/luau`. Step 1 fix to green (v1 now 91/52):
fixtures from the live roof (5.86) then marker-based, one cell table, IN_PLACE core synced. Step 2 add:
| suite | cases |
|---|---|
| thresholds | 70.0 fires, 70.01 not; inclusive 0; NaN/negative/>100 clamped and logged |
| order + stagger | 100→50 = 70 only; 100→20 = 70 then 30 at +stagger; 100→0 = 70, 30, 0 in order; 30 never before 70 |
| idempotence | same value twice; rise then fall; SplitAt twice; Reset mid-stagger cancels pending |
| multi-train | 2 trains, independent state; unknown model → generic; missing markers → loud refuse |
| profiles | Coal tear, Diesel presplit/external fixture from E4, generic plane |
| chunking | each part in exactly one chunk; cap 6/8; same seed = same chunks |
| despawn | 700 studs or 30 s; `Despawned` once; nothing left under the train with `RR_Lost` |
| contract | payload schema v=2, t0 lead, fling cap; no client-callable handler except the flag |
**Studio bench (owner).** Diagnose on Coal and Diesel → `Bench.run("all")` → paste Output into chat (task I11).
**Phone perf (owner, MicroProfiler).** Private test server on a mid phone: enable MicroProfiler in the in-game
settings, start the bench via the owner admin command, dump a frame at each beat (steps in `PERF.md`; mobile dump route U).
Budgets from P5 §5: particles ≤ 800 peak per 2 s, ≤ 400 live; emitters ≤ 12; lights ≤ 8, 0 shadowed; moving bodies ≤ 2
(70/30), chunks ≤ 6; server CFrame writes ≤ 3/frame; voices ≤ 16 (P6, est.); frame time ≤ +15% vs idle run (OQ-039 A).
**Multiplayer.** Studio Test > Clients and Servers, 3 clients, with simulated incoming lag (Studio network setting, U);
then 1 phone + 1 PC in a private server. Checks: every client sees the snap within 1 frame of t0; a rider on the lost
section is flung and seen by others; late joiner after 30% sees the right train; 6 players at 0% within budget; a
client firing the remote is flagged, nothing happens.

## 5. Security (rr-exploit-guard)
| point | risk | fix pattern |
|---|---|---|
| `RR_TrainSplitFX` / fling messages | client fires them back | no handler beyond the flag; scan proves no client→server path |
| integrity writes | a client remote in Joel's system (e.g. "I hit X") lowers integrity | server-derived damage only; RR_Guard `connect` with args, rate, state; scan E2 |
| `Integrity` attribute | other server scripts write it | single writer = his system; bridge clamps 0-100, ignores NaN |
| fling | a client flings others; client-owned wreck parts used as weapons | targets + capped impulse from server; client applies to its own character only; wreck parts `SetNetworkOwner(nil)`; debris client-only; no Touched damage/money; no-player-collide group while flung |
| keep-on fee | fling becomes a way to cost others 5 coins (gameplay.train.keep_on) | flung window exempt (owner Q) |
| admin bench | live access | owner UserId on the server, `IsStudio()` for the slider, `Config.Debug=false` at release |
Commands: `guard scan M/export --out M/security --fail-on high` (with E2/E3 scripts) → `guard explain` → fix → rescan →
`guard pack` → independent reviewer verdict → `guard fuzz` (owner runs) → `guard gate --stage alpha`. Physics/fling
abuse is outside static reach: a manual checklist in the review pack plus a 2-client grief test.

## 6. Ops
- **Version:** `TrainSplit.VERSION = "2.0.0"` (semver), payload `v=2`; kit `TrainSplitKit_v2.0.0.rbxmx`; `rel stamp`.
- **Install/upgrade (rbxmx, INSTALL.md):** 1 save a place copy; 2 move v1 modules to `ServerStorage.RR_Backup_v1`
  (disabled); 3 insert the kit, drag each folder to the path printed in INSTALL.md; 4 run Setup v2 on each train
  **template**, DRY_RUN first; 5 `Diagnose` + `Bench.run("all")`; 6 paste the output.
- **Rollback:** `Config.Enabled=false` (integrity still ends the run; no splits); else restore `RR_Backup_v1`; live:
  Creator Dashboard place version history (rr-release-train `ROLLBACK.md`).
- **Release gate:** `rel init --channel alpha` → attach place → `rel collect` → `rel gate` (G5 exploit-guard, G8 critic
  ledgers: fx F+M, sound S + listening sign-off, 3D A) → owner `rel approve` → `rel plan`. Never publish without his confirm.
- **Analytics (P):** server-only, rr-data-and-money `track.py validate/build`: `train_split(stage, profile, riders_lost)`,
  `player_flung(distance)`, `run_end.reason += train_explosion`.

## 7. Build tasks (prefix I; joins P5 V-, P6 S-, P7 tasks)
| id | deliverable | skill / commands | depends | model/effort | est. tok | done-when | owner steps |
|---|---|---|---|---|---|---|---|
| I0 | exports E1-E7 in `M/intake/` | - | - | owner | - | files readable here | export + upload (§1) |
| I1 | script extract, inventory, diff vs v1 | `placefile.py`, XML parse, diff | I0 | opus/high | 40k | inventory lists integrity API, spawn event, Diesel tree, v1 deltas | - |
| I2 | `contract.md` (real names), canon drafts | `bible add-question --dry-run`; mechanic-reviewer (P9) | I1 | opus/high | 30k | every §2 row bound to a real symbol | approve contract; record D-003 override |
| I3 | Lune suite green | `lune run tests/run_tests.luau` | - | opus/high | 50k | 0 FAIL | - |
| I4 | config v2 + profile registry + validator | Luau, Lune | I2, I3 | opus/high | 50k | Coal/Diesel/generic validate | - |
| I5 | Setup/Checker v2: markers, N carriages, presplit map, chunks (= V7) | Luau, break_spec.py | I4, E4 | opus/high | 80k | fixtures pass; chunks ≤ cap | run on templates |
| I6 | server core v2: bridge, stage machine, stagger, reset, 0% hand-off, lostSet | Luau, Lune | I4, I5 | opus/high | 120k | §4 suites pass | - |
| I7 | remote v2 + client router (t0, late join) (feeds V8, S9) | Luau, `luatest.py` | I6 | opus/high | 50k | schema tests pass | - |
| I8 | Diagnose, boot check, RR_SplitBench, Studio slider (P) | Luau | I6 | sonnet/high | 50k | every failure path prints a step | - |
| I9 | security pass | `guard scan/explain/pack/fuzz/gate` | I7, I8, I0 | opus/high + fresh reviewer | 60k | gate PASS or HOLD with owner items only | run fuzz kit; tick checklist |
| I10 | kit rbxmx + INSTALL/UPGRADE/ROLLBACK | v1 kit packer | I8, V11, S11 | sonnet/medium | 40k | kit parses; paths match code | - |
| I11 | Studio session 1 | bench | I10 | owner | 5k | Output pasted, all PASS | ~30 min |
| I12 | phone perf + multiplayer tests | `PERF.md`, `MP.md` | I11 | sonnet/medium | 30k | results inside §4 budgets | ~45 min, 1 phone |
| I13 | analytics hooks (P) | `track.py` | I6 | sonnet/medium | 25k | validate --strict PASS | approve events |
| I14 | release gate | `rel status/init/attach/collect/gate/plan` | I9, I12, V10, S13 | sonnet/medium | 30k | GATES.md GO | approve, publish |
| I15 | friction log + skill-smith hand-off (G5 fling rules, G6 canon) | SKILL-FRICTION.md, `harvest.py` | I14 | sonnet/low | 15k | logged | approve patches |
Systems total ≈ 675k tokens est. Critical path: I0 → I1 → I2 → I4 → I5 → I6 → I7 → I10 → I11.
