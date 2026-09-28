#!/usr/bin/env python3
"""Risky Rails tracking plan: validate it against canon and budgets, build the Luau plan + docs, scan game code.

  track.py validate [--plan FILE]            schema, budgets, cardinality, privacy, canon funnel + canon events
  track.py build    [--plan FILE] [--out DIR] RR_AnalyticsPlan.lua (generated) + TRACKING_PLAN.md; validates first.
                                              Default out: <data root>/track/ (never the skill's own folder)
  track.py scan     SRC_DIR [--plan FILE] [--strict]
                                              Luau tree: direct AnalyticsService calls outside RR_Analytics, ids the
                                              plan does not define, and COVERAGE: every planned onboarding step,
                                              funnel step, event, progression status and economy SKU must be logged
                                              somewhere (a funnel step never logged is silently auto-completed by
                                              Roblox, so a missing hook hides the drop). Dynamic ids are declared on
                                              the line before the call: `-- @rr sink: coal toolbox`. When game code
                                              sits next to RR_AnalyticsHooks, hooks it never calls are listed
                                              (--strict makes that an error).

Plan: --plan, else $RR_TRACKING_PLAN, else <data root>/presets/tracking-plan.json (a mission's copy), else the
skill's preset. Canon via rr-bible (found by glob or $RR_BIBLE_SKILL): the onboarding steps must equal
release.kpi.funnel in order, and the events named in its note (run_end(reason), ...) must exist with those fields.
Exit 0 = OK, 1 = errors, 2 = usage.
"""
import argparse, json, os, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rrlib  # noqa: E402

ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,39}$")
FORBIDDEN = {"name", "username", "user", "userid", "user_id", "displayname", "message", "chat", "text", "email",
             "ip", "id", "uid", "player"}
RESERVED = {"exp_exposure"}


def plan_path(p=None):
    return rrlib.preset("tracking-plan.json", p, "RR_TRACKING_PLAN")


def snake(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def validate(plan, bible=None):
    E, W = [], []
    bible = bible or rrlib.Bible()
    B = plan.get("budgets", {})
    fmax, emax = B.get("fields_per_event", 3), B.get("enum_values", 20)

    def fields_ok(where, fields, tag_slots=0):
        if len(fields) + tag_slots > min(3, fmax):
            E.append(f"{where}: {len(fields)} fields + {tag_slots} experiment tag > 3 custom fields")
        for f in fields:
            n = f.get("name", "")
            if snake(n) in FORBIDDEN:
                E.append(f"{where}: field '{n}' would hold ids or free text (privacy + cardinality)")
            if "enum" in f:
                if len(f["enum"]) > emax:
                    E.append(f"{where}.{n}: {len(f['enum'])} enum values > budget {emax}")
                if len(set(f["enum"])) != len(f["enum"]):
                    E.append(f"{where}.{n}: duplicate enum values")
            elif "buckets" in f:
                b = f["buckets"]
                if not b or any(not isinstance(x, (int, float)) for x in b) or b != sorted(b) or len(set(b)) != len(b):
                    E.append(f"{where}.{n}: buckets must be ascending numbers")
            else:
                E.append(f"{where}.{n}: field needs enum or buckets")

    # experiments first (they reserve a field slot on tagged targets)
    exps = {k: v for k, v in plan.get("experiments", {}).items() if not k.startswith("_")}
    tagged = {}
    for k, x in exps.items():
        if not ID_RE.match(k):
            E.append(f"experiment id '{k}' must be snake_case <= 40 chars")
        if len(x.get("arms", [])) < 2 or len(x["arms"]) != len(x.get("weights", [])):
            E.append(f"experiment {k}: needs >= 2 arms and one weight per arm")
        if any(w <= 0 for w in x.get("weights", [])):
            E.append(f"experiment {k}: weights must be > 0")
        if not x.get("salt"):
            E.append(f"experiment {k}: salt missing")
        for t in x.get("tag", []):
            tagged[t] = tagged.get(t, 0) + (1 if x.get("active") else 0)
            if tagged[t] > 1:
                E.append(f"{t}: tagged by more than one active experiment (one slot only)")

    # onboarding vs canon
    ob = plan.get("onboarding", {})
    steps = [s["id"] for s in ob.get("steps", [])]
    canon_key = ob.get("canon", "release.kpi.funnel")
    f = bible.fact(canon_key) if bible.ok() else None
    if not bible.ok():
        W.append("rr-bible not found: onboarding and canon events unchecked")
    elif not f:
        E.append(f"onboarding: canon key {canon_key} missing")
    else:
        want = [snake(x) for x in f["value"].split(">")]
        if steps != want:
            E.append(f"onboarding steps {steps} != canon {canon_key} {want}")
        for ev, args in re.findall(r"(\w+)\(([^)]*)\)", f.get("note", "")):
            mine = next((e for e in plan.get("events", []) if e["id"] == ev), None)
            need = [a.strip() for a in args.split(",") if a.strip()]
            if not mine:
                E.append(f"canon event {ev}({', '.join(need)}) missing from events")
                continue
            have = {x["name"] for x in mine.get("fields", [])} | set(mine.get("implicit", []))
            miss = [a for a in need if a not in have]
            if miss:
                E.append(f"event {ev}: canon fields {miss} missing (fields or implicit)")
    if len(steps) > B.get("funnel_steps", 12):
        E.append("onboarding: too many steps")
    fields_ok("onboarding", [], 1 if tagged.get("onboarding") else 0)

    funnels = plan.get("funnels", {})
    if len(funnels) > B.get("funnels", 5):
        E.append(f"{len(funnels)} funnels > budget")
    for k, fu in funnels.items():
        ids = [s["id"] for s in fu.get("steps", [])]
        if not ID_RE.match(k) or any(not ID_RE.match(i) for i in ids) or len(set(ids)) != len(ids):
            E.append(f"funnel {k}: ids must be unique snake_case")
        if len(ids) > B.get("funnel_steps", 12):
            E.append(f"funnel {k}: {len(ids)} steps > budget")
        if not fu.get("question"):
            E.append(f"funnel {k}: no question (what decision does it inform?)")

    eco = plan.get("economy", {})
    PL = plan.get("platform_limits", {})
    for k, n in (("transaction_types", len(eco.get("transaction_types", []))), ("funnels", len(plan.get("funnels", {})) + 1),
                 ("custom_events", len(plan.get("events", [])) + 1)):
        if PL.get(k) and n > PL[k]:
            E.append(f"{k}: {n} > platform limit {PL[k]} (extra values become 'Other' or are dropped)")
    for k, b in B.items():
        if k in PL and isinstance(b, (int, float)) and b > PL[k]:
            E.append(f"budget {k} = {b} exceeds the platform limit {PL[k]}")
    skus = [s["sku"] for s in eco.get("sources", []) + eco.get("sinks", [])]
    if len(skus) != len(set(skus)):
        E.append("economy: duplicate skus")
    if len(skus) > B.get("skus", 40):
        E.append(f"economy: {len(skus)} skus > budget")
    for s in eco.get("sources", []) + eco.get("sinks", []):
        if s.get("type") not in eco.get("transaction_types", []):
            E.append(f"economy sku {s['sku']}: type {s.get('type')} not in transaction_types")
    fields_ok("economy", eco.get("fields", []), 1 if tagged.get("economy") else 0)

    for k, p in plan.get("progression", {}).items():
        if not ID_RE.match(k):
            E.append(f"progression {k}: id must be snake_case")
        if not p.get("levels"):
            E.append(f"progression {k}: levels missing")
        if not set(p.get("statuses", ["Start", "Complete", "Fail"])) <= {"Start", "Complete", "Fail"}:
            E.append(f"progression {k}: statuses must be Start, Complete or Fail")
        fields_ok(f"progression.{k}", p.get("fields", []), 1 if tagged.get(k) else 0)

    evs = plan.get("events", [])
    ids = [e["id"] for e in evs]
    if len(set(ids)) != len(ids):
        E.append("events: duplicate ids")
    if len(ids) + 1 > B.get("custom_events", 30):
        E.append(f"events: {len(ids)} + exp_exposure > budget")
    for e in evs:
        if not ID_RE.match(e["id"]) or e["id"] in RESERVED:
            E.append(f"event {e['id']}: snake_case <= 40 chars and not reserved")
        for k in ("question", "where", "value"):
            if not e.get(k):
                E.append(f"event {e['id']}: '{k}' missing (no vanity events)")
        fields_ok(f"event {e['id']}", e.get("fields", []), 1 if tagged.get(e["id"]) else 0)
        if e.get("max_per_min", 1) > 60:
            W.append(f"event {e['id']}: > 60 per minute per player: log outcomes, not ticks")

    targets = set(ids) | set(funnels) | set(plan.get("progression", {})) | {"onboarding", "economy"}
    for t in tagged:
        if t not in targets:
            E.append(f"experiment tag '{t}' names nothing in the plan")
    cur = plan.get("currency", {}).get("name")
    if bible.ok():
        c = bible.fact("economy.currency.name")
        if c and c.get("status") == "conflict":
            W.append(f"currency '{cur}': canon economy.currency.name is a conflict (OQ-003); label it assumed")
    return E, W


def lua(v, ind=0):
    pad, pad1 = "\t" * ind, "\t" * (ind + 1)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v)
    if isinstance(v, list):
        if all(not isinstance(x, (dict, list)) for x in v):
            return "{ " + ", ".join(lua(x) for x in v) + " }"
        return "{\n" + "".join(f"{pad1}{lua(x, ind + 1)},\n" for x in v) + pad + "}"
    key = (lambda k: k if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", k) else f"[{json.dumps(k)}]")
    flat = all(not isinstance(x, dict) and (not isinstance(x, list) or all(not isinstance(y, (dict, list)) for y in x))
               for x in v.values())
    if flat and len(v) <= 4:
        return "{ " + ", ".join(f"{key(k)} = {lua(x)}" for k, x in v.items()) + " }"
    return "{\n" + "".join(f"{pad1}{key(k)} = {lua(x, ind + 1)},\n" for k, x in v.items()) + pad + "}"


def runtime_plan(plan):
    fl = lambda fs: [{k: f[k] for k in ("name", "enum", "buckets") if k in f} for f in fs]  # noqa: E731
    eco = plan["economy"]
    return {
        "version": plan.get("version", "?"),
        "currency": plan["currency"]["name"],
        "budgets": {"max_per_min_default": plan.get("budgets", {}).get("max_per_min_default", 20)},
        "onboarding": [{"id": s["id"], "name": s["name"]} for s in plan["onboarding"]["steps"]],
        "funnels": {k: {"steps": [{"id": s["id"], "name": s["name"]} for s in f["steps"]]}
                    for k, f in plan.get("funnels", {}).items()},
        "economy": {"types": {t: True for t in eco["transaction_types"]},
                    "sources": {s["sku"]: True for s in eco.get("sources", [])},
                    "sinks": {s["sku"]: True for s in eco.get("sinks", [])},
                    "fields": fl(eco.get("fields", []))},
        "progression": {k: {"levels": p["levels"], "fields": fl(p.get("fields", []))}
                        for k, p in plan.get("progression", {}).items()},
        "events": {e["id"]: {"fields": fl(e.get("fields", [])), "max_per_min": e.get("max_per_min", 20)}
                   for e in plan.get("events", [])},
        "experiments": {k: {"arms": x["arms"], "weights": x["weights"], "salt": x["salt"],
                            "active": bool(x.get("active")), "tag": x.get("tag", [])}
                        for k, x in plan.get("experiments", {}).items() if not k.startswith("_")},
    }


def doc(plan):
    fdesc = lambda fs: "; ".join(f"{f['name']}: " + (", ".join(f["enum"]) if "enum" in f else  # noqa: E731
                                 "buckets " + ", ".join(str(b) for b in f["buckets"]) + f" {f.get('unit', '')}")
                                 for f in fs) or "-"
    L = [f"# Risky Rails tracking plan ({plan.get('version')})", "",
         "GENERATED by rr-data-and-money track.py from presets/tracking-plan.json. Server-only calls through "
         "RR_Analytics; fields map in order to CustomField01..03.", "",
         f"Currency: **{plan['currency']['name']}** ({plan['currency'].get('note', '')})", "",
         "## Onboarding funnel (LogOnboardingFunnelStepEvent, once per player)", "",
         plan["onboarding"].get("question", ""), ""]
    L.append(rrlib.md_table(["#", "step", "where"], [(i + 1, f"`{s['id']}` {s['name']}", s["where"])
                                                     for i, s in enumerate(plan["onboarding"]["steps"])]))
    for k, f in plan.get("funnels", {}).items():
        L += ["", f"## Funnel `{k}` (LogFunnelStepEvent)", "", f"{f['question']} Session: {f['session']}.", ""]
        L.append(rrlib.md_table(["#", "step", "where"], [(i + 1, f"`{s['id']}` {s['name']}", s["where"])
                                                         for i, s in enumerate(f["steps"])]))
    eco = plan["economy"]
    L += ["", "## Economy (LogEconomyEvent)", "", eco.get("question", ""), "",
          f"Fields: {fdesc(eco.get('fields', []))}", ""]
    L.append(rrlib.md_table(["flow", "sku", "type", "where"],
                            [("Source", s["sku"], s["type"], s["where"]) for s in eco.get("sources", [])] +
                            [("Sink", s["sku"], s["type"], s["where"]) for s in eco.get("sinks", [])]))
    L += ["", "## Progression (LogProgressionEvent: Start / Complete / Fail)", ""]
    L.append(rrlib.md_table(["path", "levels", "fields", "question"],
                            [(k, ", ".join(p["levels"]), fdesc(p.get("fields", [])), p.get("question", ""))
                             for k, p in plan.get("progression", {}).items()]))
    L += ["", "## Custom events (LogCustomEvent)", ""]
    L.append(rrlib.md_table(["event", "value", "fields", "where", "question"],
                            [(f"`{e['id']}`", e["value"], fdesc(e.get("fields", [])), e["where"], e["question"])
                             for e in plan.get("events", [])]))
    exps = {k: v for k, v in plan.get("experiments", {}).items() if not k.startswith("_")}
    L += ["", "## Experiments (exposure = custom event `exp_exposure`: experiment, arm)", ""]
    L.append(rrlib.md_table(["experiment", "arms", "active", "tags", "who"],
                            [(k, "/".join(f"{a} {w}" for a, w in zip(x["arms"], x["weights"])), x.get("active"),
                              ", ".join(x.get("tag", [])), x.get("who", "")) for k, x in exps.items()]))
    return "\n".join(L) + "\n"


def cmd_validate(a):
    plan = rrlib.load_json(plan_path(a.plan))
    E, W = validate(plan)
    for w in W:
        print("  W", w)
    for e in E:
        print("  E", e)
    print(f"{'PASS' if not E else 'FAIL'} tracking plan: {len(E)} errors, {len(W)} warnings")
    return 1 if E else 0


def cmd_build(a):
    plan = rrlib.load_json(plan_path(a.plan))
    E, W = validate(plan)
    if E:
        for e in E:
            print("  E", e)
        print("FAIL: fix the plan before building")
        return 1
    out = Path(a.out) if a.out else rrlib.data_root() / "track"
    out.mkdir(parents=True, exist_ok=True)
    head = ("-- RR_AnalyticsPlan (ModuleScript) - GENERATED by rr-data-and-money track.py from tracking-plan.json.\n"
            "-- Do not edit: change the plan and run `track.py build`. Required by RR_Analytics.init().\n")
    (out / "RR_AnalyticsPlan.lua").write_text(head + "return " + lua(runtime_plan(plan)) + "\n", encoding="utf-8")
    docs = Path(a.docs) if a.docs else out
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "TRACKING_PLAN.md").write_text(doc(plan), encoding="utf-8")
    for w in W:
        print("  W", w)
    print(f"built {out / 'RR_AnalyticsPlan.lua'} and {docs / 'TRACKING_PLAN.md'}")
    return 0


CALL_RE = re.compile(r"\b\w+\s*[.:]\s*(onboarding|event|expose|arm)\s*\(\s*[\w.]+\s*,\s*\"([a-z0-9_]+)\"")
FUNNEL_RE = re.compile(r"\b\w+\s*[.:]\s*funnel\s*\(\s*[\w.]+\s*,\s*\"([a-z0-9_]+)\"\s*,\s*[^,]+,\s*\"([a-z0-9_]+)\"")
FUNNEL_NAME_RE = re.compile(r"\b\w+\s*[.:]\s*funnel\s*\(\s*[\w.]+\s*,\s*\"([a-z0-9_]+)\"")
PROG_NAME_RE = re.compile(r"\b\w+\s*[.:]\s*progress\s*\(\s*[\w.]+\s*,\s*\"([a-z0-9_]+)\"")
PROG_RE = re.compile(r"\b\w+\s*[.:]\s*progress\s*\(\s*[\w.]+\s*,\s*\"([a-z0-9_]+)\"\s*,\s*\"(Start|Complete|Fail)\"")
ECON_RE = re.compile(r"\b\w+\s*[.:]\s*(source|sink)\s*\([^\"]*\"(\w+)\"\s*,\s*\"([a-z0-9_]+)\"")
ECON_DYN_RE = re.compile(r"\b\w+\s*[.:]\s*(source|sink)\s*\([^\"]*\"(\w+)\"\s*,\s*[A-Za-z_]")
DECL_RE = re.compile(r"--\s*@rr\s+(source|sink)\s*:\s*(.+)")
HOOK_DEF_RE = re.compile(r"^\s*function\s+Hooks\.(\w+)\s*\(")


def cmd_scan(a):
    plan = rrlib.load_json(plan_path(a.plan))
    src = Path(a.src)
    files = [p for p in src.rglob("*") if p.suffix in (".lua", ".luau") and p.is_file()]
    used = {k: set() for k in ("onboarding", "funnel", "step", "event", "progress", "status", "source", "sink", "expose")}
    issues, hooks_file, hook_defs, game_text = [], None, [], []
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        is_rr = p.stem in ("RR_Analytics", "RR_AnalyticsPlan")
        if p.stem == "RR_AnalyticsHooks":
            hooks_file = p
            hook_defs = [m.group(1) for ln in text.splitlines() for m in [HOOK_DEF_RE.match(ln)] if m]
        elif not is_rr:
            game_text.append(text)
        pending, active = [], []  # `-- @rr` lines: they cover the function below them, or the calls after them
        for n, line in enumerate(text.splitlines(), 1):
            code = line.split("--", 1)[0]
            if re.search(r"AnalyticsService", code) and not p.stem.startswith("RR_Analytics"):
                issues.append(f"{p}:{n}: direct AnalyticsService use; route it through RR_Analytics")
            m = DECL_RE.search(line)
            if m:
                pending.append((m.group(1), m.group(2).split()))
                continue
            if re.match(r"\s*(local\s+)?function\b", code):
                active, pending = pending, []
            decl = active + pending
            for m in CALL_RE.finditer(code):
                kind = "expose" if m.group(1) in ("expose", "arm") else m.group(1)
                used[kind].add(m.group(2))
            for m in FUNNEL_NAME_RE.finditer(code):
                used["funnel"].add(m.group(1))
            for m in FUNNEL_RE.finditer(code):
                used["step"].add(f"{m.group(1)}.{m.group(2)}")
            for m in PROG_NAME_RE.finditer(code):
                used["progress"].add(m.group(1))
            for m in PROG_RE.finditer(code):
                used["status"].add(f"{m.group(1)}.{m.group(2)}")
            for m in ECON_RE.finditer(code):
                used[m.group(1)].add(m.group(3))
            dyn = ECON_DYN_RE.search(code)
            if dyn:  # a variable sku: covered only by a `-- @rr source|sink: ...` line just above
                mine = [ids for k, ids in decl if k == dyn.group(1)]
                if mine:
                    used[dyn.group(1)].update(mine[-1])
                else:
                    issues.append(f"{p}:{n}: {dyn.group(1)} with a variable sku and no `-- @rr {dyn.group(1)}: ...` line "
                                  "above it (scan cannot check the sku against the plan)")
    eco = plan.get("economy", {})
    planned = {"onboarding": {s["id"] for s in plan["onboarding"]["steps"]}, "funnel": set(plan.get("funnels", {})),
               "step": {f"{k}.{s['id']}" for k, f in plan.get("funnels", {}).items() for s in f["steps"]},
               "event": {e["id"] for e in plan.get("events", [])}, "progress": set(plan.get("progression", {})),
               "status": {f"{k}.{st}" for k, p in plan.get("progression", {}).items() for st in p.get("statuses", [])},
               "source": {x["sku"] for x in eco.get("sources", [])}, "sink": {x["sku"] for x in eco.get("sinks", [])},
               "expose": {k for k in plan.get("experiments", {}) if not k.startswith("_")}}
    declared = {k for k, p in plan.get("progression", {}).items() if p.get("statuses")}
    used["status"] = {x for x in used["status"] if x.split(".")[0] in declared} | \
        {x for x in used["status"] - planned["status"] if x.split(".")[0] in declared}
    for k in used:
        for x in sorted(used[k] - planned[k]):
            issues.append(f"code uses {k} '{x}' that the plan does not define (it will be dropped at run time)")
    gaps = {k: sorted(planned[k] - used[k]) for k in planned if k != "expose" and planned[k] - used[k]}
    for k, v in gaps.items():
        issues.append(f"planned {k} never logged: {', '.join(v)}" + (" (Roblox marks a skipped step complete: this "
                                                                     "drop would read as 100% pass-through)"
                                                                     if k == "step" else ""))
    warns = []
    if hooks_file and game_text:
        blob = "\n".join(game_text)
        idle = [h for h in hook_defs if not re.search(rf"[.:]{h}\s*\(", blob)]
        if idle:
            warns.append(f"hooks never called from game code: {', '.join(idle)}")
    elif hooks_file:
        print("  I only the RR_Analytics modules here: hook wiring in game code unchecked (scan the owner's tree)")
    for i in issues:
        print("  E", i)
    for w in warns:
        print("  W", w)
    fail = bool(issues) or (a.strict and warns)
    print(f"{'FAIL' if fail else 'PASS'} scan of {len(files)} Luau files: {len(issues)} issues, {len(warns)} warnings")
    return 1 if fail else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    v = sub.add_parser("validate")
    v.add_argument("--plan")
    b = sub.add_parser("build")
    b.add_argument("--plan")
    b.add_argument("--out", help="folder for RR_AnalyticsPlan.lua (default: <data root>/track)")
    b.add_argument("--docs", help="folder for TRACKING_PLAN.md (default: same as --out)")
    s = sub.add_parser("scan")
    s.add_argument("src")
    s.add_argument("--plan")
    s.add_argument("--strict", action="store_true", help="hooks never called from game code are errors")
    a = ap.parse_args()
    if not a.cmd:
        ap.print_help()
        return 2
    return {"validate": cmd_validate, "build": cmd_build, "scan": cmd_scan}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
