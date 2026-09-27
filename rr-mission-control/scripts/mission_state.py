#!/usr/bin/env python3
"""rr-mission-control state: machine state + progress log for one mission folder.

  mission_state.py init   M --slug S --kind 3d|ui|mixed [--bar 8] [--steps 10] [--budget N]
  mission_state.py step   M K "result text" [--tokens N [--est]] [--stage NAME] [--image PATH]
  mission_state.py set    M key=value [key=value ...]    (dotted keys: agent.critic-depot=abc)
  mission_state.py next   M "exact next action"
  mission_state.py status M
  mission_state.py resume [ROOT]                         (newest unfinished under ROOT, else $RR_MISSIONS_ROOT, else ~/.rr-missions)

The stage name is added by `step`; do not repeat it in the text (a leading copy is stripped).
--est marks the token figure as an estimate (shown "~84k est") until a measured one replaces it.
env.critic_mode: agent | remote | handoff (caller spawns the critic) | self.
self makes step 7-10 lines carry "UNCERTIFIED"; handoff prints the pending critic hand-off.

Files: M/state.json (status, step, bar, env, agents, next) and M/progress.log
(the exact lines sent to the owner). `step` prints the owner line to paste:
  [5/10] Build v1 - Depot shell+roof up, 312 parts (84k)
Stdlib only.
"""
import argparse, datetime, json, os, sys

STAGES = ["Intake", "Readback", "Spec", "Plan", "Build v1", "Pre-flight",
          "Critic pass 1", "Fix + re-check", "Roblox export", "Debrief"]
DONE = {"done", "stopped"}
INT_KEYS = {"bar", "step", "steps", "budget", "tokens", "cap_passes"}
DEFAULT_ROOT = os.environ.get("RR_MISSIONS_ROOT") or os.path.expanduser("~/.rr-missions")


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def sp(m):
    return os.path.join(m, "state.json")


def load(m):
    if not os.path.exists(sp(m)):
        sys.exit(f"no state.json in {m}: run init")
    return json.load(open(sp(m), encoding="utf-8"))


def save(m, st):
    st["updated"] = now()
    tmp = sp(m) + ".tmp"
    json.dump(st, open(tmp, "w", encoding="utf-8"), indent=1)
    os.replace(tmp, sp(m))


def ktok(n):
    return f"{n/1000:.0f}k" if n >= 1000 else str(n)


def cmd_init(a):
    os.makedirs(a.mission, exist_ok=True)
    for d in ("refs", "tasks"):
        os.makedirs(os.path.join(a.mission, d), exist_ok=True)
    if os.path.exists(sp(a.mission)):
        if not a.force:
            sys.exit(f"{sp(a.mission)} exists (resume it; --force only for a finished mission)")
        old = json.load(open(sp(a.mission), encoding="utf-8"))
        if old.get("status") not in DONE:
            sys.exit(f"refusing --force: mission status '{old.get('status')}' is not done; resume it instead")
        bak = sp(a.mission) + ".bak-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        os.replace(sp(a.mission), bak)
        print(f"backed up old state to {bak}")
    st = {"slug": a.slug, "kind": a.kind, "status": "intake", "step": 1, "steps": a.steps,
          "bar": a.bar, "cap_passes": 5, "budget": a.budget, "tokens": 0,
          "env": {"root": os.path.abspath(os.path.dirname(os.path.abspath(a.mission.rstrip("/"))))}, "agent": {}, "next": "split + tag prompt (intake.py split)", "created": now()}
    save(a.mission, st)
    open(os.path.join(a.mission, "progress.log"), "a").close()
    print(f"mission {a.slug} initialised at {a.mission} (bar {a.bar}, {a.steps} steps)")


def cmd_step(a):
    st = load(a.mission)
    k = a.k
    if not 1 <= k <= st["steps"]:
        sys.exit(f"step {k} outside 1..{st['steps']}")
    stage = a.stage or (STAGES[k-1] if 1 <= k <= len(STAGES) else f"Step {k}")
    if a.tokens is not None:
        st["tokens"] = a.tokens
        st["tokens_est"] = bool(a.est)
    text = a.text
    for pre in (stage + " - ", stage + ": ", stage + " "):
        if text.lower().startswith(pre.lower()):
            text = text[len(pre):]
            break
    if k >= 7 and st.get("env", {}).get("critic_mode") == "self" and "UNCERTIFIED" not in text:
        text += " [UNCERTIFIED: self-assessed, no independent critic]"
    line = f"[{k}/{st['steps']}] {stage} - {text}"
    if st.get("tokens"):
        line += f" (~{ktok(st['tokens'])} est)" if st.get("tokens_est") else f" ({ktok(st['tokens'])})"
    st["step"] = k
    if k == st["steps"] and st["status"] not in DONE:
        st["status"] = "debrief"
    save(a.mission, st)
    with open(os.path.join(a.mission, "progress.log"), "a", encoding="utf-8") as f:
        f.write(f"{now()} {line}" + (f"  img={a.image}" if a.image else "") + "\n")
    b = st.get("budget")
    print(line)
    if b and st.get("tokens", 0) > 1.3 * b:
        print(f"WARN spend {ktok(st['tokens'])} > 1.3x budget {ktok(b)}: interrupt owner with a default")


def parse_val(v):
    for f in (int, float):
        try:
            return f(v)
        except ValueError:
            pass
    return {"true": True, "false": False, "yes": True, "no": False}.get(v.lower(), v)


def cmd_set(a):
    st = load(a.mission)
    for kv in a.pairs:
        if "=" not in kv:
            sys.exit(f"bad pair {kv} (want key=value)")
        k, v = kv.split("=", 1)
        cur = st
        parts = k.split(".")
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
            if not isinstance(cur, dict):
                sys.exit(f"bad key {k}: '{p}' is not a group")
        val = parse_val(v)
        if k in INT_KEYS and not isinstance(val, int):
            sys.exit(f"{k} must be an integer, got '{v}'")
        cur[parts[-1]] = val
    save(a.mission, st)
    print("set " + ", ".join(a.pairs))


def cmd_next(a):
    st = load(a.mission); st["next"] = a.action; save(a.mission, st)
    print("next: " + a.action)


def tail(m, n=5):
    p = os.path.join(m, "progress.log")
    if not os.path.exists(p):
        return []
    return [l.rstrip("\n") for l in open(p, encoding="utf-8")][-n:]


def cmd_status(a, m=None):
    m = m or a.mission
    st = load(m)
    print(f"MISSION {st['slug']}  status={st['status']}  step {st['step']}/{st['steps']}  "
          f"bar {st['bar']}  kind {st['kind']}  tokens {'~' if st.get('tokens_est') else ''}{ktok(st.get('tokens', 0))}"
          + (f"/{ktok(st['budget'])}" if st.get("budget") else ""))
    if st.get("env"):
        print("env: " + ", ".join(f"{k}={v}" for k, v in st["env"].items()))
        if st["env"].get("critic_mode") == "self":
            print("WARN critic_mode=self: scores are UNCERTIFIED (cap at bar-1); never report the bar as met")
        elif st["env"].get("critic_mode") == "handoff":
            print("NOTE critic_mode=handoff: a fresh critic is spawned by the caller; see references/orchestrated.md")
    if st.get("agent"):
        print("agents: " + ", ".join(f"{k}={v}" for k, v in st["agent"].items()))
    for l in tail(m):
        print("  " + l)
    crits = sorted(d for d in os.listdir(m) if d.startswith("critique-"))
    for c in crits:
        led = os.path.join(m, c, "ledger.json")
        print(f"crit {c}: " + ("ledger present (critic_kit.py show)" if os.path.exists(led) else "no passes yet"))
    print(f"NEXT: {st.get('next', '?')}")
    print(f"path: {os.path.abspath(m)}")


def cmd_resume(a):
    root = a.root or DEFAULT_ROOT
    if not os.path.isdir(root):
        sys.exit(f"no folder {root}")
    cands = []
    for d in os.listdir(root):
        p = os.path.join(root, d)
        if os.path.exists(sp(p)):
            st = json.load(open(sp(p), encoding="utf-8"))
            cands.append((st.get("updated", ""), p, st))
    if not cands:
        sys.exit(f"no missions under {root}")
    open_ = [c for c in cands if c[2].get("status") not in DONE]
    if len(cands) > 1:
        print("missions: " + "; ".join(f"{os.path.basename(p)}={s.get('status')}" for _, p, s in sorted(cands, reverse=True)))
    if not open_:
        print("all missions finished; newest:")
        open_ = cands
    cmd_status(a, max(open_)[1])
    print("Critic agent ids may be dead in a new session: next pass fresh (--kind final if all blocks-8 addressed).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init"); i.add_argument("mission"); i.add_argument("--slug", required=True)
    i.add_argument("--kind", choices=["3d", "ui", "mixed"], required=True)
    i.add_argument("--bar", type=int, default=8); i.add_argument("--steps", type=int, default=10)
    i.add_argument("--budget", type=int); i.add_argument("--force", action="store_true")
    s = sub.add_parser("step"); s.add_argument("mission"); s.add_argument("k", type=int); s.add_argument("text")
    s.add_argument("--tokens", type=int, help="cumulative tokens so far"); s.add_argument("--est", action="store_true", help="token figure is an estimate"); s.add_argument("--stage"); s.add_argument("--image")
    se = sub.add_parser("set"); se.add_argument("mission"); se.add_argument("pairs", nargs="+")
    n = sub.add_parser("next"); n.add_argument("mission"); n.add_argument("action")
    st = sub.add_parser("status"); st.add_argument("mission")
    r = sub.add_parser("resume"); r.add_argument("root", nargs="?", help="default $RR_MISSIONS_ROOT or ~/.rr-missions")
    a = ap.parse_args()
    {"init": cmd_init, "step": cmd_step, "set": cmd_set, "next": cmd_next,
     "status": cmd_status, "resume": cmd_resume}[a.cmd](a)


if __name__ == "__main__":
    main()
