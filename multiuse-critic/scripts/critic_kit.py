#!/usr/bin/env python3
"""One critic.md per pass, and the cost ledger.

  critic_kit.py build CRIT --pass N --kind full|delta|final --profile A|B [--criteria A1,A5]
                [--continued] [--images close-1.png] [--bar 8] [--role "senior game artist"]
  critic_kit.py log   CRIT --pass N --kind K --scores "A1=8,A5=7" --tokens T --tools U --minutes M
                [--agent ID] [--model NAME] [--fixes "..."] [--note "..."] [--budget 120000]
  critic_kit.py show  CRIT

CRIT holds brief.md, ledger.json (+ ledger.md, rendered) and pass-N/ with facts.md, delta.md,
contact.png + contact.json (from contact_sheet.py), and the critic.md this writes. Save each
critic's answer as pass-N/verdict.md; a fresh delta critic gets the previous one's score lines.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CRIT_ID = re.compile(r"^([A-Z]\d+)\b")


def read(path, default=None):
    if os.path.isfile(path):
        return open(path, encoding="utf-8").read().strip()
    if default is None:
        sys.exit(f"missing {path}")
    return default


def parse_rubric(text):
    """h2 sections by title; criteria (### A1 ...) and shared blocks (### under 'Shared blocks')."""
    h2, crit, shared, cur2, cur3 = {}, {}, {}, None, None
    for line in text.splitlines():
        if line.startswith("## "):
            cur2, cur3 = line[3:].strip(), None
            h2[cur2] = []
            continue
        if line.startswith("### ") and cur2:
            cur3 = line[4:].strip()
            m = CRIT_ID.match(cur3)
            if m:
                crit[m[1]] = {"profile": cur2, "lines": [line]}
            elif cur2.lower().startswith("shared"):
                shared[cur3] = {"lines": [line]}
            continue
        if cur3 and (m := CRIT_ID.match(cur3)):
            crit[m[1]]["lines"].append(line)
        elif cur3 and cur3 in shared:
            shared[cur3]["lines"].append(line)
        elif cur2:
            h2[cur2].append(line)
    for s in shared.values():
        body = "\n".join(s["lines"])
        m = re.search(r"<!--\s*include-with:\s*([^>]*?)\s*-->", body)
        s["with"] = {x.strip() for x in m[1].split(",")} if m else set()
        s["text"] = re.sub(r"\s*<!--.*?-->", "", body).strip()
    for c in crit.values():
        c["text"] = "\n".join(c["lines"]).strip()
    return {k: "\n".join(v).strip() for k, v in h2.items()}, crit, shared


def section(h2, prefix):
    for k, v in h2.items():
        if k.lower().startswith(prefix.lower()):
            return v
    sys.exit(f"rubric has no '## {prefix}' section")


def ledger(crit_dir):
    p = os.path.join(crit_dir, "ledger.json")
    return json.load(open(p)) if os.path.isfile(p) else []


def standing(rows):
    """Latest score per criterion, with the pass it came from."""
    out = {}
    for r in rows:
        for c, s in r["scores"].items():
            out[c] = (s, r["pass"])
    return out


def image_note(path):
    from PIL import Image
    w, h = Image.open(path).size
    mp = w * h / 1e6
    warn = "  <- OVER 1.15 MP / 1568 px: the reader will shrink it" if mp > 1.15 or max(w, h) > 1568 else ""
    return w, h, mp, warn


def build(a):
    crit_dir, pdir = a.crit, os.path.join(a.crit, f"pass-{a.pass_}")
    rubric = a.rubric or next((p for p in (os.path.join(crit_dir, "rubric.md"),
                                           os.path.join(HERE, "..", "references", "rubric.md")) if os.path.isfile(p)), None)
    h2, crits, shared = parse_rubric(read(rubric))
    profile = [k for k in h2 if k.startswith(f"Profile {a.profile}")]
    if not profile:
        sys.exit(f"rubric has no 'Profile {a.profile}' section")
    in_profile = [c for c, v in crits.items() if v["profile"] == profile[0]]
    rows, stand = ledger(crit_dir), standing(ledger(crit_dir))

    if a.criteria:
        chosen = [c.strip() for c in a.criteria.split(",") if c.strip()]
    elif a.kind == "delta":
        chosen = [c for c in in_profile if c in stand and stand[c][0] < a.bar]
        if not chosen:
            sys.exit("every scored criterion is at the bar: build --kind final instead")
    else:
        chosen = in_profile
    unknown = [c for c in chosen if c not in crits]
    if unknown:
        sys.exit(f"not in the rubric: {', '.join(unknown)}")

    images = [os.path.join(pdir, "contact.png")] + [p if os.path.isabs(p) else os.path.join(pdir, p)
                                                     for p in (a.images.split(",") if a.images else [])]
    for p in images:
        if not os.path.isfile(p):
            sys.exit(f"missing image {p}")
    if len(images) > 2:
        print(f"WARNING: {len(images)} images; the rule is the contact sheet plus at most one close-up")

    fresh = not a.continued
    btext = read(os.path.join(crit_dir, "brief.md"), "")
    if re.search(r"step 2 not answered", btext, re.I):
        print("WARNING: brief.md still says 'Step 2 NOT answered'. Answer step 2 (or write the assumed answers and "
              "'step 2: pre-answered') before spawning; a critic judging against open questions scores the wrong thing.")
    brief = btext.splitlines()
    title = re.sub(r"^#\s*", "", brief[0])
    body = "\n".join(brief[1:] if brief[0].startswith("#") else brief).strip()
    out = [f"# Critic brief — {title} — pass {a.pass_} ({a.kind})", ""]
    if fresh:
        out += ["## How to work", section(h2, "How to work"), "", "## Brief", body, ""]
    if a.kind in ("delta", "final") and stand:
        line = " · ".join(f"{c} {s} (pass {p})" for c, (s, p) in stand.items() if c in in_profile)
        out += ["## Standing scores", f"{line}. Bar: {a.bar} on every criterion. Rule 8 applies to any you lower.", ""]
    if a.kind in ("delta", "final"):
        prev = max((r["pass"] for r in rows if r["pass"] < a.pass_), default=None)
        out += [f"## Changes since pass {prev}" if prev else "## Changes", read(os.path.join(pdir, "delta.md"), "(no delta.md written)"), ""]
    facts = re.sub(r"(?m)^# ", "### ", read(os.path.join(pdir, "facts.md"), "(no facts.md)"))  # no nested H1
    prev_facts = os.path.join(crit_dir, f"pass-{a.pass_ - 1}", "facts.md")
    if a.kind == "delta" and os.path.isfile(prev_facts):
        old = set(read(prev_facts).splitlines())
        changed = [l for l in facts.splitlines() if l.strip() and l not in old]
        facts = "\n".join(changed) or "(no measured facts changed)"
        out += [f"## Facts that changed since pass {a.pass_ - 1} (the rest stand)", facts, ""]
    else:
        out += ["## Facts (measured)", facts, ""]
    out += ["## Images"]
    cj = os.path.join(pdir, "contact.json")
    for p in images:
        w, h, mp, warn = image_note(p)
        out.append(f"- `{os.path.basename(p)}` {w}x{h} ({mp:.2f} MP){warn}")
        if p.endswith("contact.png") and os.path.isfile(cj):
            for t in json.load(open(cj))["tiles"]:
                out.append(f"  {t['n']}. {t['label']} — {t['scale']}")
    out.append("")
    if fresh and a.kind == "delta":
        handoff = []
        for n in range(a.pass_ - 1, 0, -1):
            v = os.path.join(crit_dir, f"pass-{n}", "verdict.md")
            if os.path.isfile(v):
                handoff = [l for l in read(v).splitlines() if (m := CRIT_ID.match(l.strip())) and m[1] in chosen]
                break
        if handoff:
            out += ["## Previous critic's scores for these criteria (context, not a baseline to grade against)", *handoff, ""]

    out += ["## Rubric"]
    if fresh:
        out += ["### Scoring rules", section(h2, "Scoring rules"), ""]
        out += [f"### Criteria scored this pass: {', '.join(chosen)}"]
        out += [crits[c]["text"] + "\n" for c in chosen]
        out += [s["text"] + "\n" for s in shared.values() if s["with"] & set(chosen)]
        out += ["### Issue format", section(h2, "Issue format"), ""]
    else:
        out += [f"Score only: {', '.join(chosen)} (anchors, scoring rules and issue format as in pass 1).", ""]
    out += ["## Output", section(h2, f"Output — {a.kind}"), ""]

    path = os.path.join(pdir, "critic.md")
    text = "\n".join(out).rstrip() + "\n"
    open(path, "w", encoding="utf-8").write(text)
    names = " and ".join(f"`{p}`" for p in [path] + images)
    print(f"wrote {path}: {len(text):,} chars (~{len(text) // 4:,} tokens), criteria {', '.join(chosen)}")
    if fresh:
        print(f"\nSpawn prompt:\nYou're a {a.role} critiquing work you didn't make. Everything you need is in {names}. "
              f"Message 1: open all of them together, as parallel tool calls in one message. Message 2: your answer, in the "
              f"output format critic.md gives. Your answer must come by your 3rd message at the latest; opening files or "
              f"images one at a time is a failure. No scripts, no other files.")
    else:
        print(f"\nSendMessage to the same critic:\nPass {a.pass_}: the work has changed. Same rules as before: open {names} "
              f"together in one message, then answer in the {a.kind} output format critic.md gives, by your 3rd message at the latest.")


def render_ledger(crit_dir, rows, bar):
    stand, lines = {}, ["| pass | kind | critic · model | scores this pass | standing overall | tokens reported | new this pass | tool calls | min | fixes / notes |",
                        "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        stand.update(r["scores"])
        low = min(stand.items(), key=lambda kv: kv[1]) if stand else ("-", "-")
        scores = " · ".join(f"{c} {s}" for c, s in r["scores"].items())
        flag = " ⚠" if r.get("tokens", 0) > r.get("budget", 120000) else ""
        est = " est." if r.get("est") else ""
        lines.append(f"| {r['pass']} | {r['kind']} | {r.get('agent', '')} · {r.get('model', '')} | {scores} | {low[1]} ({low[0]}) | "
                     f"{r.get('tokens', 0):,}{est}{flag} | {r.get('new', r.get('tokens', 0)):,}{est} | {r.get('tools', '')} | {r.get('minutes', '')} | "
                     f"{r.get('fixes', '')} {r.get('note', '')} |")
    tot_t, tot_m = sum(r.get("new", r.get("tokens", 0)) for r in rows), sum(float(r.get("minutes") or 0) for r in rows)
    any_est = " (includes estimates)" if any(r.get("est") for r in rows) else ""
    lines += ["", f"Total: {len(rows)} passes, {tot_t:,} new critic tokens{any_est}, {tot_m:.1f} critic minutes. Bar: {bar}."]
    open(os.path.join(crit_dir, "ledger.md"), "w").write("\n".join(lines) + "\n")
    return "\n".join(lines)


def log(a):
    rows = [r for r in ledger(a.crit) if not (r["pass"] == a.pass_ and r["kind"] == a.kind)]
    scores = {k.strip(): float(v) if "." in v else int(v) for k, v in (s.split("=") for s in a.scores.split(",") if s)}
    prev = [r for r in rows if a.agent and r.get("agent") == a.agent and r["pass"] < a.pass_]
    # same critic continued: its earlier context comes along. self/handoff/fresh passes carry nothing.
    carried = max((r["tokens"] for r in prev), default=0) if a.mode == "continued" else 0
    rows.append({"pass": a.pass_, "kind": a.kind, "agent": a.agent, "model": a.model, "scores": scores,
                 "tokens": a.tokens, "new": max(0, a.tokens - carried), "carried": carried, "tools": a.tools,
                 "minutes": a.minutes, "fixes": a.fixes, "note": a.note, "budget": a.budget,
                 "est": bool(a.est), "mode": a.mode})
    rows.sort(key=lambda r: r["pass"])
    json.dump(rows, open(os.path.join(a.crit, "ledger.json"), "w"), indent=1)
    print(render_ledger(a.crit, rows, a.bar))
    if a.tokens > a.budget:
        row = rows[[r["pass"] for r in rows].index(a.pass_)]
        if row["carried"]:
            print(f"\nNOTE: {row['carried']:,} of these were carried from this critic's earlier passes (cache reads, cheap); "
                  f"this pass added {row['new']:,}.")
        print(f"\nWARNING: pass {a.pass_} reported {a.tokens:,} tokens, over the {a.budget:,} budget. Tell the owner now, "
              f"with the likely cause: long thinking (a high-effort critic), a continued critic carrying earlier passes (its thinking included), "
              f"a heavy base context (a general-purpose agent carries every tool), extra turns ({a.tools} tool calls), or an oversized image or file.")
    if a.tools and a.tools > 4:
        print(f"WARNING: {a.tools} tool calls. The rule is one file plus 1–2 images, opened together in one message.")


SPEC = {"A": ("3d-pipeline.md", ("Cameras", "Render", "facts.md", "Checks before handover")),
        "B": ("2d-pipeline.md", ("The viewer's view", "Contact sheet"))}


def spec(a):
    """Print what a maker must hand the critic for a profile, so makers never read the pipeline docs."""
    if a.profile not in SPEC:
        sys.exit(f"spec knows profiles {', '.join(SPEC)}; for others read the profile's own skill")
    fn, heads = SPEC[a.profile]
    text = read(os.path.join(HERE, "..", "references", fn), "")
    parts = re.split(r"(?m)^(?=## )", text)
    out = [f"# Maker evidence spec, Profile {a.profile} (from references/{fn})",
           "Deliver into <CRIT>/pass-N/: contact.png + contact.json (contact_sheet.py), at most one closeups.png, facts.md "
           "(measured, starts at H2), delta.md from pass 2."]
    out += [p.strip() for p in parts if any(p.startswith("## " + h) for h in heads)]
    print("\n\n".join(out))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("crit")
    b.add_argument("--pass", dest="pass_", type=int, required=True)
    b.add_argument("--kind", choices=["full", "delta", "final"], required=True)
    b.add_argument("--profile", required=True)
    b.add_argument("--criteria", default="")
    b.add_argument("--continued", action="store_true", help="delta sent by SendMessage to the critic that already has the rubric")
    b.add_argument("--images", default="", help="extra images in pass-N (at most one close-up)")
    b.add_argument("--bar", type=float, default=8)
    b.add_argument("--role", default="senior game artist")
    b.add_argument("--rubric", default="")
    lg = sub.add_parser("log")
    lg.add_argument("crit")
    lg.add_argument("--pass", dest="pass_", type=int, required=True)
    lg.add_argument("--kind", required=True)
    lg.add_argument("--scores", required=True)
    lg.add_argument("--tokens", type=int, default=0)
    lg.add_argument("--tools", type=int, default=0)
    lg.add_argument("--minutes", type=float, default=0)
    lg.add_argument("--agent", default="")
    lg.add_argument("--model", default="")
    lg.add_argument("--fixes", default="")
    lg.add_argument("--note", default="")
    lg.add_argument("--budget", type=int, default=120000)
    lg.add_argument("--bar", type=float, default=8)
    lg.add_argument("--est", "--estimated", dest="est", action="store_true",
                    help="token/minute figures are estimates, not read from an Agent result (marked 'est.')")
    lg.add_argument("--mode", choices=["continued", "fresh", "self", "handoff"], default="continued",
                    help="continued (default) subtracts this agent's earlier carried tokens; the others never do")
    sp = sub.add_parser("spec", help="print the maker evidence spec for a profile (A or B)")
    sp.add_argument("--profile", required=True)
    sh = sub.add_parser("show")
    sh.add_argument("crit")
    sh.add_argument("--bar", type=float, default=8)
    a = ap.parse_args()
    if a.cmd == "build":
        build(a)
    elif a.cmd == "log":
        log(a)
    elif a.cmd == "spec":
        spec(a)
    else:
        print(render_ledger(a.crit, ledger(a.crit), a.bar))


if __name__ == "__main__":
    main()
