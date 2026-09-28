#!/usr/bin/env python3
"""Creator Dashboard CSV exports -> normalized metrics -> weekly memo with charts, judged against canon targets.

  dash.py inspect FILE.csv [--metric M]                 what the parser sees: kind, header, date format, mapping
  dash.py ingest  FILE.csv ... [--store metrics.json] [--metric M] [--kind daily|funnel|economy] [--name N]
                  [--map "Header text=metric"]          merge exports into one store (later files win per value)
  dash.py memo    [--store metrics.json] [--week-ending YYYY-MM-DD] [--out DIR] [--sim econ.json]
                  [--revenue-is earned|gross] [--headline TEXT] [--action TEXT ...]
                                                        memo.md + memo.html + facts.json + charts/*.svg
  dash.py demo    OUT_DIR                               SYNTHETIC exports in the formats the parser handles

Metrics: dau, mau, new_users, visits, avg_session_min, playtime_min_per_dau, d1, d7, d30, revenue (Robux),
paying_users, payer_conversion, arpdau, arppu, ccu_peak, qptr, impressions, bounce. Rates are stored as
fractions, durations in minutes. Derived: ARPDAU = revenue / DAU, payer conversion = payers / DAU,
R$ per visit = revenue / visits. Targets come from rr-bible at run time (presets/targets.json maps metric ->
canon key). Store default: $RR_DATA_ROOT/metrics.json (else ~/.rr-data). Memo default: <root>/memos/<week-end>/.
Header names in real exports vary: run `inspect` on the first real file and pass --map for anything unmapped.
"""
import argparse, csv, datetime as dt, io, math, re, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rrlib  # noqa: E402
import statlib as S  # noqa: E402
import svgchart as C  # noqa: E402

METRICS = [
    ("arpdau", [r"arpdau", r"revenue per (daily )?(active )?(user|dau)", r"average revenue per dau"], "money"),
    ("arppu", [r"arppu", r"per paying user"], "money"),
    ("payer_conversion", [r"payer conversion", r"conversion rate", r"paying user rate", r"payer rate"], "rate"),
    ("d30", [r"\bd ?30\b", r"day 30\b", r"30 day retention"], "rate"),
    ("d7", [r"\bd ?7\b", r"day 7\b", r"7 day retention"], "rate"),
    ("d1", [r"\bd ?1\b", r"day 1\b", r"1 day retention", r"next day retention"], "rate"),
    ("new_users", [r"new users?", r"new players?", r"first time"], "count"),
    ("paying_users", [r"paying users?", r"\bpayers\b"], "count"),
    ("dau", [r"\bdau\b", r"daily active"], "count"),
    ("mau", [r"\bmau\b", r"monthly active"], "count"),
    ("ccu_peak", [r"peak concurrent", r"\bccu\b", r"concurrent"], "count"),
    ("revenue", [r"revenue", r"robux earned", r"earnings", r"\bearned\b", r"total robux", r"\bsales\b"], "money"),
    ("avg_session_min", [r"session (length|time|duration)", r"avg session", r"average session"], "duration"),
    ("playtime_min_per_dau", [r"play ?time per", r"avg play ?time", r"average play ?time"], "duration"),
    ("qptr", [r"qualified play ?through", r"\bqptr\b", r"play ?through rate"], "rate"),
    ("impressions", [r"impressions?"], "count"),
    ("visits", [r"\bvisits?\b", r"\bplays\b"], "count"),
    ("bounce", [r"bounce"], "rate"),
]
KIND = {m: k for m, _, k in METRICS}
LABEL = {"dau": "DAU (daily avg)", "new_users": "New users", "avg_session_min": "Session length", "d1": "D1 retention",
         "d7": "D7 retention", "d30": "D30 retention", "revenue": "Revenue", "arpdau": "ARPDAU", "arppu": "ARPPU",
         "payer_conversion": "Payer conversion", "robux_per_visit": "R$ per visit", "qptr": "Qualified play-through",
         "bounce": "Bounce"}
ADDITIVE = {"dau", "new_users", "visits", "revenue", "paying_users", "impressions"}
DFMTS = ["%Y-%m-%d", "%Y/%m/%d", "%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y", "%Y%m%d"]


def norm(h):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", h.lower())).strip()


def match_metric(text):
    n = norm(text)
    for m, pats, _ in METRICS:
        if any(re.search(p, n) for p in pats):
            return m
    return None


def parse_value(s, decimal_comma=False):
    """'12.3%' -> 0.123 ; '1,234' -> 1234 ; 'R$ 1.2K' -> 1200 ; '0:12:30' -> 12.5 min ; decimal_comma: '11,5%' -> 0.115."""
    s = (s or "").strip()
    if decimal_comma:
        s = s.replace(".", "").replace(",", ".")
    if not s or s.lower() in ("-", "n/a", "na", "null", "none", "--"):
        return None
    if re.match(r"^\d+:\d{2}(:\d{2})?$", s):
        parts = [int(x) for x in s.split(":")]
        return parts[0] * 60 + parts[1] + parts[2] / 60 if len(parts) == 3 else parts[0] + parts[1] / 60
    m = re.match(r"^(\d+)\s*m(?:in)?\s*(\d+)\s*s", s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 60
    is_pct = s.endswith("%")
    t = re.sub(r"(?i)r\$|robux|usd|\$|%|,|\s", "", s)
    mult = 1.0
    if t[-1:].lower() in ("k", "m", "b") and re.match(r"^-?[\d.]+[kmbKMB]$", t):
        mult = {"k": 1e3, "m": 1e6, "b": 1e9}[t[-1].lower()]
        t = t[:-1]
    try:
        v = float(t) * mult
    except ValueError:
        return None
    if is_pct:
        v /= 100
    return v


def parse_date(s, order=None):
    s = (s or "").strip()[:19]
    s = s.split("T")[0] if re.match(r"^\d{4}-\d{2}-\d{2}T", s) else s
    for f in DFMTS:
        try:
            return dt.datetime.strptime(s, f).date()
        except ValueError:
            pass
    m = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})$", s)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = y + 2000 if y < 100 else y
        mo, d = (b, a) if order == "dmy" else (a, b)
        try:
            return dt.date(y, mo, d)
        except ValueError:
            return None
    return None


def read_table(path):
    raw = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(raw[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    rows = [r for r in csv.reader(io.StringIO(raw), dialect) if any(c.strip() for c in r)]
    dc = dialect.delimiter == ";" and len(re.findall(r"\d,\d{1,2}(?!\d)", raw)) > len(re.findall(r"\d\.\d{1,2}(?!\d)", raw))
    hi = 0
    for i in range(min(len(rows) - 1, 10)):
        nxt = rows[i + 1]
        if len([c for c in rows[i] if c.strip()]) >= 2 and any(parse_value(c) is not None or parse_date(c) for c in nxt):
            hi = i
            break
    return [c.strip() for c in rows[hi]], rows[hi + 1:], dc


def date_order(vals):
    firsts, seconds = [], []
    for v in vals:
        m = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-]\d{2,4}$", v.strip())
        if m:
            firsts.append(int(m.group(1)))
            seconds.append(int(m.group(2)))
    if not firsts:
        return None, None
    if max(firsts) > 12:
        return "dmy", None
    if max(seconds) > 12:
        return "mdy", None
    return "mdy", "ambiguous day/month order: assumed month/day (US); pass dates as YYYY-MM-DD if wrong"


def analyse(path, metric=None, kind=None, name=None, maps=()):
    """Classify one export. Returns a dict describing what will be ingested."""
    head, rows, dc = read_table(path)
    user_map = {}
    for m in maps:
        k, _, v = m.partition("=")
        user_map[norm(k)] = v.strip()
    cols = list(zip(*rows)) if rows else [[] for _ in head]
    info = {"file": str(path), "header": head, "rows": len(rows), "notes": [], "mapping": {}, "kind": kind, "dc": dc}
    if dc:
        info["notes"].append("semicolon file with decimal commas: '11,5' read as 11.5")
    date_col = None
    for i, h in enumerate(head):
        vals = [v for v in cols[i] if v.strip()] if i < len(cols) else []
        if vals and sum(1 for v in vals[:20] if parse_date(v, "mdy") or parse_date(v, "dmy")) >= max(1, len(vals[:20]) * 0.8):
            date_col = i
            break
    info["date_col"] = head[date_col] if date_col is not None else None
    order, warn = date_order(cols[date_col]) if date_col is not None else (None, None)
    if warn:
        info["notes"].append(warn)
    lower = [norm(h) for h in head]
    if not kind:
        if any("step" in h for h in lower):
            kind = "funnel"
        elif any("flow" in h for h in lower) or any(
                i < len(cols) and cols[i] and {v.strip().lower() for v in cols[i]} <= {"source", "sink"} for i in range(len(head))):
            kind = "economy"
        else:
            kind = "daily"
    info["kind"] = kind
    text_cols = [i for i in range(len(head)) if i != date_col and i < len(cols) and cols[i] and
                 sum(1 for v in cols[i] if parse_value(v) is None and v.strip()) > len(cols[i]) * 0.5]
    info["text_cols"] = [head[i] for i in text_cols]
    num_cols = [i for i in range(len(head)) if i != date_col and i not in text_cols]
    if kind == "daily":
        long_metric = next((i for i in text_cols if re.search(r"metric|measure|kpi|name", lower[i])), None)
        info["long"] = long_metric is not None
        file_metric = metric or match_metric(Path(path).stem)
        if long_metric is not None:
            info["long_metrics"] = sorted({match_metric(r[long_metric]) or f"UNMAPPED '{r[long_metric]}'" for r in rows})
            info["long_value_col"] = num_cols[0] if num_cols else None
        for i in (num_cols if long_metric is None else []):
            m = user_map.get(lower[i]) or match_metric(head[i])
            if (m is None and len(num_cols) == 1) or (m in (None,) and lower[i] in ("value", "count", "total", "users")):
                m = file_metric if file_metric else None
                if m:
                    info["notes"].append(f"column '{head[i]}' taken as {m} (from --metric or the file name)")
            if metric and len(num_cols) == 1:
                m = metric
            info["mapping"][head[i]] = m
        info["breakdown"] = [head[i] for i in text_cols if i != long_metric]
    info["_parsed"] = (head, rows, date_col, order, text_cols, num_cols)
    info["user_map"] = user_map
    info["name"] = name or Path(path).stem
    return info


def unit_scale(metric, header, values):
    h = header.lower()
    if KIND.get(metric) == "rate":
        if "%" in h or any(v is not None and v > 1.0 for v in values):
            return 0.01, "percent -> fraction"
        return 1.0, ""
    if KIND.get(metric) == "duration":
        if re.search(r"\(s\)|sec|seconds", h):
            return 1 / 60, "seconds -> minutes"
        if re.search(r"hour|\(h\)", h):
            return 60.0, "hours -> minutes"
        med = statistics.median([v for v in values if v is not None] or [0])
        if med > 90:
            return 1 / 60, "values look like seconds (median > 90): converted to minutes"
    return 1.0, ""


def extract(info):
    head, rows, dcol, order, text_cols, num_cols = info["_parsed"]
    dc, user_long = info["dc"], info.get("user_map", {})
    out = {"daily": {}, "funnels": {}, "economy": []}
    if info["kind"] == "funnel":
        step_i = next(i for i, h in enumerate(head) if "step" in norm(h))
        name_i = next((i for i in text_cols if i != step_i), None)
        cnt_i = next((i for i in num_cols if i != step_i and re.search(r"user|player|count|value|total|people",
                                                                           norm(head[i]))), None)
        cnt_i = cnt_i if cnt_i is not None else next(i for i in num_cols if i != step_i)
        steps = []
        for r in rows:
            label = r[name_i] if name_i is not None else r[step_i]
            v = parse_value(r[cnt_i], info["dc"])
            if v is not None:
                steps.append([label.strip(), v])
        out["funnels"][info["name"]] = {"steps": steps, "source": info["file"]}
        return out
    if info["kind"] == "economy":
        lower = [norm(h) for h in head]
        flow_i = next((i for i, h in enumerate(lower) if "flow" in h), None)
        if flow_i is None:
            flow_i = next(i for i in text_cols if {r[i].strip().lower() for r in rows} <= {"source", "sink"})
        type_i = next((i for i, h in enumerate(lower) if "transaction" in h or h == "type"), None)
        sku_i = next((i for i, h in enumerate(lower) if "sku" in h or "item" in h), None)
        amt_i = next((i for i in num_cols if re.search(r"amount|value|total|currency|sum", lower[i])), num_cols[0])
        for r in rows:
            v = parse_value(r[amt_i], info["dc"])
            if v is None:
                continue
            d = parse_date(r[dcol], order) if dcol is not None else None
            out["economy"].append({"date": d.isoformat() if d else None, "flow": r[flow_i].strip().lower(),
                                   "type": r[type_i].strip() if type_i is not None else "",
                                   "sku": r[sku_i].strip() if sku_i is not None else "", "amount": v})
        return out
    if dcol is None:
        info["notes"].append("no date column: nothing ingested")
        return out
    breakdown = [head.index(b) for b in info.get("breakdown", [])]
    long_i = next((i for i in text_cols if re.search(r"metric|measure|kpi|name", norm(head[i]))), None) if info.get("long") else None
    agg, skipped = {}, set()
    totals = ("total", "all", "overall")
    has_total = bool(breakdown) and any(any(x[i].strip().lower() in totals for i in breakdown) for x in rows)
    for r in rows:
        d = parse_date(r[dcol], order)
        if not d:
            continue
        if breakdown:
            bval = " ".join(r[i].strip().lower() for i in breakdown)
            if has_total and bval not in totals:
                continue
        pairs = []
        if long_i is not None:
            m = user_long.get(norm(r[long_i])) or match_metric(r[long_i])
            vi = info.get("long_value_col")
            if m and vi is not None:
                pairs.append((m, r[long_i], parse_value(r[vi], dc)))
        else:
            for i in num_cols:
                m = info["mapping"].get(head[i])
                if m:
                    pairs.append((m, head[i], parse_value(r[i], dc)))
        for m, h, v in pairs:
            if v is None:
                continue
            key = (d.isoformat(), m)
            if breakdown and not has_total:
                if m not in ADDITIVE:
                    skipped.add(m)
                    continue
                agg[key] = agg.get(key, 0.0) + v
            else:
                agg[key] = v
    for m in sorted(skipped):
        info["notes"].append(f"{m}: split by {', '.join(info['breakdown'])} with no Total row; ratios cannot be summed, skipped")
    by_metric = {}
    for (d, m), v in agg.items():
        by_metric.setdefault(m, []).append((d, v))
    for m, pts in by_metric.items():
        hdr = next((h for h, mm in info["mapping"].items() if mm == m), m)
        sc, note = unit_scale(m, hdr, [v for _, v in pts])
        if note:
            info["notes"].append(f"{m}: {note}")
        for d, v in pts:
            out["daily"].setdefault(d, {})[m] = v * sc
    return out


def store_path(p=None):
    return Path(p) if p else rrlib.data_root() / "metrics.json"


def cmd_inspect(a):
    info = analyse(a.file, a.metric, a.kind, None, a.map)
    ex = extract(info)
    print(f"{info['file']}: kind {info['kind']}, {info['rows']} rows, header {info['header']}")
    print(f"  date column: {info['date_col']}")
    if info["kind"] == "daily":
        if info.get("long_metrics"):
            print(f"  long format: metric names -> {info['long_metrics']} (fix names with --map \"Name=metric\")")
        for h, m in info["mapping"].items():
            hint = m or f'UNMAPPED (use --map "{h}=metric")'
            print(f"  {h!r:40} -> {hint}")
        if info.get("breakdown"):
            print(f"  breakdown columns: {info['breakdown']}")
        days = sorted(ex["daily"])
        if days:
            print(f"  {len(days)} days {days[0]} .. {days[-1]}; sample {days[-1]}: "
                  + ", ".join(f"{k}={v:.4g}" for k, v in ex["daily"][days[-1]].items()))
    elif info["kind"] == "funnel":
        for n, f in ex["funnels"].items():
            print(f"  funnel {n}: " + " > ".join(f"{s} {v:,.0f}" for s, v in f["steps"]))
    else:
        print(f"  {len(ex['economy'])} economy rows; flows {sorted({r['flow'] for r in ex['economy']})}")
    for n in info["notes"]:
        print(f"  note: {n}")
    return 0


def cmd_ingest(a):
    sp = store_path(a.store)
    st = rrlib.load_json(sp) if sp.is_file() else {"daily": {}, "funnels": {}, "economy": [], "files": []}
    changed = 0
    for f in a.files:
        info = analyse(f, a.metric, a.kind, a.name, a.map)
        ex = extract(info)
        for d, vals in ex["daily"].items():
            day = st["daily"].setdefault(d, {})
            for m, v in vals.items():
                if m in day and abs(day[m] - v) > 0.01 * max(abs(v), 1e-9):
                    changed += 1
                day[m] = v
        st["funnels"].update(ex["funnels"])
        if ex["economy"]:
            keys = {(r["date"], r["flow"], r["type"], r["sku"]) for r in ex["economy"]}
            st["economy"] = [r for r in st["economy"] if (r["date"], r["flow"], r["type"], r["sku"]) not in keys]
            st["economy"] += ex["economy"]
        unm = [h for h, m in info.get("mapping", {}).items() if not m]
        st["files"].append({"file": str(f), "kind": info["kind"], "ingested": dt.date.today().isoformat(),
                            "mapping": info.get("mapping", {}), "notes": info["notes"]})
        print(f"ingested {f}: {info['kind']}, {len(ex['daily'])} days, {len(ex['funnels'])} funnels, "
              f"{len(ex['economy'])} economy rows" + (f"; UNMAPPED {unm}" if unm else ""))
        for n in info["notes"]:
            print(f"  note: {n}")
    if changed:
        print(f"  {changed} existing values replaced by newer files (> 1% different)")
    rrlib.save_json(sp, st)
    print(f"store {sp}: {len(st['daily'])} days")
    return 0


# ------------------------------------------------------------------ memo
def week_vals(daily, days, m):
    return [daily[d][m] for d in days if d in daily and daily[d].get(m) is not None]


def ret_windows(daily, last, weeks_back=0):
    """Per retention metric: the 7 most recent cohort dates (<= last) that have a value, i.e. mature cohorts."""
    out = {}
    for m in ("d1", "d7", "d30"):
        ds = sorted((d for d in daily if d <= last.isoformat() and daily[d].get(m) is not None), reverse=True)
        out[m] = ds[7 * weeks_back:7 * weeks_back + 7]
    return out


def summarize(daily, days, ret=None):
    g = lambda m: week_vals(daily, days, m)  # noqa: E731
    s = {}
    dau, new, rev, vis, pay = g("dau"), g("new_users"), g("revenue"), g("visits"), g("paying_users")
    s["dau"] = sum(dau) / len(dau) if dau else None
    s["new_users"] = sum(new) if new else None
    s["revenue"] = sum(rev) if rev else None
    s["visits"] = sum(vis) if vis else None
    pairs = lambda m: [(daily[d][m], daily[d].get("dau")) for d in days if d in daily and daily[d].get(m) is not None]  # noqa: E731
    if rev and dau and len(rev) == len(dau):
        s["arpdau"] = sum(rev) / sum(dau)
    elif g("arpdau"):
        s["arpdau"] = statistics.mean(g("arpdau"))
    if pay and dau and len(pay) == len(dau):
        s["payer_conversion"], s["_payer_conversion_n"] = sum(pay) / sum(dau), sum(dau)
    elif g("payer_conversion"):
        s["payer_conversion"] = statistics.mean(g("payer_conversion"))
    if rev and pay and sum(pay) > 0:
        s["arppu"] = sum(rev) / sum(pay)
    if rev and vis and sum(vis) > 0:
        s["robux_per_visit"] = sum(rev) / sum(vis)
    for m in ("avg_session_min", "playtime_min_per_dau", "qptr", "bounce", "ccu_peak", "impressions"):
        pv = pairs(m)
        if pv:
            w = [x[1] or 1 for x in pv]
            s[m] = sum(v * wi for (v, _), wi in zip(pv, w)) / sum(w)
    for m in ("d1", "d7", "d30"):
        rd = (ret or {}).get(m, days)
        pts = [(daily[d][m], daily[d].get("new_users")) for d in rd if d in daily and daily[d].get(m) is not None]
        if pts:
            s[f"_{m}_cohorts"] = f"{min(rd)}..{max(rd)}"
            if all(n for _, n in pts):
                n = sum(nu for _, nu in pts)
                s[m], s[f"_{m}_n"] = sum(v * nu for v, nu in pts) / n, n
            else:
                s[m] = statistics.mean(v for v, _ in pts)
    return s


def load_targets(bible):
    t = rrlib.load_json(rrlib.PRESETS / "targets.json")
    out = []
    for e in t["targets"]:
        f = bible.fact(e["canon"]) if bible.ok() else None
        cmp = rrlib.comparisons(f["value"]) if f else []
        if f and e["pick"] < len(cmp):
            op, v, _ = cmp[e["pick"]]
            out.append(dict(e, op=op, value=v, text=f["value"], status_canon=f.get("status")))
        else:
            out.append(dict(e, op=None, value=None, text=f["value"] if f else "(canon missing)", status_canon=None))
    return out


def judge(t, s):
    v = s.get(t["metric"])
    if v is None or t["op"] is None:
        return "NO DATA" if t["op"] else "UNPARSED", None
    n = s.get(f"_{t['metric']}_n")
    lo, hi = (S.wilson(round(v * n), n) if n else (v, v))
    need = t["value"]
    if t["op"] in (">=", ">"):
        met = lo >= need if n else v >= need
        miss = hi < need if n else v < need
    else:
        met = hi <= need if n else v <= need
        miss = lo > need if n else v > need
    st = "PASS" if met else ("MISS" if miss else "UNCLEAR")
    if t.get("trigger"):
        st = {"PASS": "ALERT", "MISS": "OK", "UNCLEAR": "WATCH"}[st]
    return st, (lo, hi) if n else None


def fmt_metric(m, v):
    if v is None:
        return "n/a"
    k = KIND.get(m, "rate" if m in ("payer_conversion",) else "")
    if m in ("robux_per_visit", "arpdau", "arppu"):
        return f"{v:.2f} R$"
    if k == "rate":
        return rrlib.pct(v, 1 if v >= 0.1 else 2)
    if k == "duration":
        return f"{v:.1f} min"
    if m == "revenue":
        return f"{v:,.0f} R$"
    return rrlib.fmt_num(v)


def cmd_memo(a):
    sp = store_path(a.store)
    st = rrlib.load_json(sp)
    daily = st["daily"]
    if not daily:
        print("store has no daily data: ingest exports first")
        return 1
    last = dt.date.fromisoformat(a.week_ending) if a.week_ending else dt.date.fromisoformat(max(daily))
    wk = [(last - dt.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    pw = [(last - dt.timedelta(days=i)).isoformat() for i in range(13, 6, -1)]
    s, p = summarize(daily, wk, ret_windows(daily, last)), summarize(daily, pw, ret_windows(daily, last, 1))
    if a.revenue_is == "gross":
        bible0 = rrlib.Bible()
        share = rrlib.numbers_in(bible0.value("economy.platform.creator_share", "70%"))
        share = next((x for x in share if x < 1), 0.7)
        for d in (s, p):
            for m in ("revenue", "arpdau", "arppu", "robux_per_visit"):
                if d.get(m) is not None:
                    d[m] *= share
    bible = rrlib.Bible()
    targets = load_targets(bible)
    out = Path(a.out) if a.out else rrlib.data_root() / "memos" / last.isoformat()
    (out / "charts").mkdir(parents=True, exist_ok=True)
    flags, kpi_rows, gate_rows = [], [], []
    order = ["dau", "new_users", "avg_session_min", "d1", "d7", "d30", "revenue", "arpdau", "payer_conversion",
             "arppu", "robux_per_visit", "qptr", "bounce"]
    tmap = {}
    for t in targets:
        tmap.setdefault(t["metric"], []).append(t)
    for m in order:
        if s.get(m) is None and p.get(m) is None:
            continue
        ch = ""
        if s.get(m) is not None and p.get(m):
            if KIND.get(m) == "rate" or m == "payer_conversion":
                ch = f"{(s[m] - p[m]) * 100:+.1f} pts"
                n1, n2 = p.get(f"_{m}_n"), s.get(f"_{m}_n")
                if n1 and n2:
                    r = S.two_prop(round(p[m] * n1), n1, round(s[m] * n2), n2)
                    if r["p"] < 0.05:
                        ch += " (sig.)"
                        flags.append(f"{m} moved {ch} week on week (p = {r['p']:.3f}, n {n1:,.0f} -> {n2:,.0f})")
            else:
                ch = f"{(s[m] / p[m] - 1):+.0%}"
        tl = [t for t in tmap.get(m, []) if not t.get("gate")]
        tgt, stat, cis = "-", "-", "-"
        if s.get(f"_{m}_n") and s.get(m) is not None:
            lo, hi = S.wilson(round(s[m] * s[f"_{m}_n"]), s[f"_{m}_n"])
            cis = f"{rrlib.pct(lo)}-{rrlib.pct(hi)} (n {s[f'_{m}_n']:,.0f})"
        if tl:
            t = tl[0]
            stat, _ = judge(t, s)
            tgt = f"{t['op'] or ''} {fmt_metric(m, t['value'])} `{t['canon']}`" if t["op"] else f"`{t['canon']}` unparsed"
        kpi_rows.append((LABEL.get(m, m), fmt_metric(m, s.get(m)), fmt_metric(m, p.get(m)), ch or "-", cis, tgt, stat))
    for t in [t for t in targets if t.get("gate")]:
        stat, ci = judge(t, s)
        gate_rows.append((t["gate"], t.get("label", t["metric"]), fmt_metric(t["metric"], s.get(t["metric"])),
                          f"{t['op'] or '?'} {fmt_metric(t['metric'], t['value'])}" if t["op"] else "unparsed", stat,
                          f"`{t['canon']}`"))
    # cohorts at/above the D1 spend gate
    d1t = next((t for t in targets if t["metric"] == "d1" and t.get("gate") == "spend"), None)
    if d1t and d1t["value"] is not None:
        blocks = []
        for k in range(4):
            days = [(last - dt.timedelta(days=i + 7 * k)).isoformat() for i in range(6, -1, -1)]
            v = summarize(daily, days, ret_windows(daily, last, k)).get("d1")
            if v is not None:
                blocks.append(v)
        ok = sum(1 for v in blocks if v >= d1t["value"])
        gate_rows.append(("spend", "weekly D1 cohorts at/above the gate (need 2; point estimates)", f"{ok} of last {len(blocks)}",
                          f">= {rrlib.pct(d1t['value'])}", "PASS" if ok >= 2 else "MISS", f"`{d1t['canon']}`"))
    # anomalies (trailing 14 days)
    alld = sorted(daily)
    for m in ("dau", "revenue", "new_users"):
        for d in wk:
            if d not in daily or daily[d].get(m) is None:
                continue
            prior = [daily[x][m] for x in alld if x < d and daily[x].get(m) is not None][-14:]
            if len(prior) >= 10:
                mu, sd = statistics.mean(prior), statistics.pstdev(prior)
                if sd > 0 and abs(daily[d][m] - mu) / sd >= 3:
                    flags.append(f"{d}: {m} {fmt_metric(m, daily[d][m])} is {(daily[d][m] - mu) / sd:+.1f} sd vs the "
                                 f"prior 14 days (check updates, featuring, outages)")
    for m in ("d1", "d7", "d30", "payer_conversion"):
        n = s.get(f"_{m}_n")
        if n and n < 400:
            flags.append(f"{m}: only {n:,.0f} players behind this week's rate; a +-{1.96 * math.sqrt(s[m] * (1 - s[m]) / n) * 100:.1f}"
                         f" pt swing is noise")
    # funnels
    fun_lines, fun_svgs = [], []
    for name, f in st.get("funnels", {}).items():
        steps = f["steps"]
        if not steps:
            continue
        top = steps[0][1] or 1
        rows = [(lab, v, f"{v / top:.0%}") for lab, v in steps]
        drops = [(steps[i][0], steps[i + 1][0], 1 - steps[i + 1][1] / steps[i][1]) for i in range(len(steps) - 1) if steps[i][1]]
        worst = max(drops, key=lambda x: x[2]) if drops else None
        fun_lines.append(f"{name}: " + " > ".join(f"{lab} {v:,.0f}" for lab, v in steps) +
                         (f". Biggest drop: {worst[0]} -> {worst[1]} loses {worst[2]:.0%}" if worst else ""))
        svg = C.hbar(f"Funnel: {name}", rows, lambda v: f"{v:,.0f}", subtitle="players reaching each step; % of step 1")
        (out / "charts" / f"funnel-{re.sub(r'[^a-z0-9]+', '-', name.lower())}.svg").write_text(svg, encoding="utf-8")
        fun_svgs.append(svg)
    # economy
    eco_lines = []
    eco = [r for r in st.get("economy", []) if r["date"] is None or r["date"] in wk]
    if eco:
        src = sum(r["amount"] for r in eco if r["flow"] == "source")
        snk = sum(r["amount"] for r in eco if r["flow"] == "sink")
        eco_lines.append(f"sources {src:,.0f}, sinks {snk:,.0f}, sink/source {snk / src:.2f}" if src else "no sources")
        by = {}
        for r in eco:
            by[(r["flow"], r["sku"] or r["type"])] = by.get((r["flow"], r["sku"] or r["type"]), 0) + r["amount"]
        for (fl, k), v in sorted(by.items(), key=lambda x: -x[1])[:6]:
            eco_lines.append(f"{fl} {k}: {v:,.0f}")
        if a.sim and Path(a.sim).is_file():
            sim = rrlib.load_json(a.sim)
            r_sim = sim.get("population", {}).get("sink_source_ratio")
            if r_sim and src:
                eco_lines.append(f"sim predicted sink/source {r_sim:.2f}; live {snk / src:.2f}"
                                 + (" (gap > 25%: recalibrate economy.json)" if abs(snk / src - r_sim) / r_sim > 0.25 else ""))
    # experiments (status only, never estimates)
    exp_lines = []
    exroot = rrlib.data_root() / "experiments"
    for pj in sorted(exroot.glob("*/plan.json")) if exroot.is_dir() else []:
        pl = rrlib.load_json(pj)
        due, st0 = dt.date.fromisoformat(pl["readout"]), dt.date.fromisoformat(pl["start"])
        state = ("readout due: run abtest.py analyze" if due <= last else
                 f"planned, starts {pl['start']}" if st0 > last else
                 f"running, day {(last - st0).days + 1} of {pl['days']}, readout {pl['readout']}")
        exp_lines.append(f"{pl['name']} ({pl['surface']}): {state}")
    # charts
    labs28 = [(last - dt.timedelta(days=i)).isoformat() for i in range(27, -1, -1)]
    short = [d[5:] for d in labs28]
    charts = []
    ser = lambda m: [daily.get(d, {}).get(m) for d in labs28]  # noqa: E731
    if any(v is not None for v in ser("dau")):
        tg = next((t for t in targets if t["metric"] == "dau" and t["value"]), None)
        charts.append(("dau", C.line_chart("Daily active users, last 28 days", short, [("DAU", ser("dau"))],
                                           lambda v: f"{v:,.0f}", target=(tg["value"], f"gate {tg['op']} {tg['value']:,.0f}")
                                           if tg else None, subtitle="Creator Dashboard export")))
    panels = []
    for m in ("d1", "d7", "d30"):
        if any(v is not None for v in ser(m)):
            tg = next((t for t in targets if t["metric"] == m and t["value"] is not None and not t.get("gate")), None)
            panels.append((m.upper(), ser(m), (tg["value"], f"target {rrlib.pct(tg['value'])}") if tg else None))
    if panels:
        charts.append(("retention", C.small_multiples("Retention by cohort day", short, panels,
                                                       lambda v: rrlib.pct(v, 1 if v >= 0.1 else 1),
                                                       subtitle="each panel has its own scale; line = canon target")))
    mon = []
    if any(v is not None for v in ser("revenue")):
        arp = [(daily[d]["revenue"] / daily[d]["dau"]) if daily.get(d, {}).get("dau") and daily[d].get("revenue") is not None
               else daily.get(d, {}).get("arpdau") for d in labs28]
        mon.append(("ARPDAU (R$)", arp, None))
    pc = [(daily[d]["paying_users"] / daily[d]["dau"]) if daily.get(d, {}).get("dau") and daily[d].get("paying_users") is not None
          else daily.get(d, {}).get("payer_conversion") for d in labs28]
    if any(v is not None for v in pc):
        tg = next((t for t in targets if t["metric"] == "payer_conversion" and t["value"] is not None), None)
        mon.append(("Payer conversion", pc, (tg["value"], f"target {rrlib.pct(tg['value'])}") if tg else None))
    if mon:
        charts.append(("money", C.small_multiples("Monetization", short, mon,
                                                   lambda v: f"{v:.2f}" if v >= 0.1 else rrlib.pct(v, 1),
                                                   subtitle="ARPDAU = revenue / DAU; conversion = payers / DAU")))
    for name, svg in charts:
        (out / "charts" / f"{name}.svg").write_text(svg, encoding="utf-8")
    assumed = [f"{m.upper()} = mature cohorts {s[f'_{m}_cohorts']}" for m in ("d1", "d7", "d30") if s.get(f"_{m}_cohorts")]
    assumed += [f"revenue treated as {'earned (net)' if a.revenue_is == 'earned' else 'gross, converted with economy.platform.creator_share'} Robux",
                "payer conversion CI treats each DAU-day as one trial (approximate)"]
    for f in st.get("files", [])[-12:]:
        assumed += [f"{Path(f['file']).name}: {n}" for n in f.get("notes", [])]
    facts = {"week_ending": last.isoformat(), "this_week": s, "last_week": p, "kpis": kpi_rows, "gates": gate_rows,
             "flags": flags, "funnels": fun_lines, "economy": eco_lines, "experiments": exp_lines, "notes": assumed}
    rrlib.save_json(out / "facts.json", facts)
    head = a.headline or "<!-- Claude: one line - the most important change this week and what to do about it -->"
    acts = a.action or ["<!-- Claude: at most 3 actions, each tied to a flag or gate above; the owner decides -->"]
    md = [f"# Risky Rails weekly memo · week ending {last.isoformat()}", "", f"**{head}**", "",
          "## KPIs vs canon targets", "", rrlib.md_table(["metric", "this week", "last week", "change", "95% CI", "target", "status"], kpi_rows)]
    if gate_rows:
        md += ["", "## Release gates", "", rrlib.md_table(["gate", "check", "now", "needs", "status", "canon"], gate_rows)]
    md += ["", "## What moved", ""] + ([f"- {x}" for x in flags] or ["- nothing beyond noise"])
    for title, lines in (("Funnels", fun_lines), ("Economy", eco_lines), ("Experiments (status only, no peeking)", exp_lines)):
        if lines:
            md += ["", f"## {title}", ""] + [f"- {x}" for x in lines]
    md += ["", "## Charts", ""] + [f"![{n}](charts/{n}.svg)" for n, _ in charts]
    md += [f"![funnel](charts/{p_.name})" for p_ in sorted((out / "charts").glob("funnel-*.svg"))]
    md += ["", "## Actions (owner decides)", ""] + [f"{i + 1}. {x}" for i, x in enumerate(acts)]
    md += ["", "## Data notes", ""] + [f"- {x}" for x in assumed]
    (out / "memo.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (out / "memo.html").write_text(html_memo(last, head, acts, kpi_rows, gate_rows, flags, fun_lines, eco_lines,
                                             exp_lines, [svg for _, svg in charts] + fun_svgs, assumed, s, p),
                                   encoding="utf-8")
    print(f"memo week ending {last}: {len(kpi_rows)} KPIs, {len(gate_rows)} gate checks, {len(flags)} flags, "
          f"{len(charts) + len(fun_svgs)} charts -> {out}")
    for r in kpi_rows:
        print(f"  {r[0]:22} {r[1]:>10}  (last {r[2]}, {r[3]})  {r[6]}" + (f"  CI {r[4]}" if r[4] != "-" else ""))
    for g in gate_rows:
        print(f"  gate {g[0]:9} {g[1]}: {g[2]} vs {g[3]} -> {g[4]}")
    for f_ in flags:
        print(f"  flag: {f_}")
    for x in fun_lines + eco_lines + exp_lines:
        print(f"  {x}")
    return 0


def html_memo(last, head, acts, kpis, gates, flags, funs, ecos, exps, svgs, notes, s, p):
    from xml.sax.saxutils import escape as e
    icon = {"PASS": "✓", "OK": "✓", "MISS": "✕", "ALERT": "✕", "UNCLEAR": "?", "WATCH": "?"}

    def badge(t):
        k = t.split(" ")[0]
        cls = {"PASS": "good", "OK": "good", "MISS": "bad", "ALERT": "bad"}.get(k, "warn" if k in icon else "")
        return f'<span class="b {cls}">{icon.get(k, "")} {e(t)}</span>' if cls else e(t)

    def table(hd, rows, badge_col=None):
        h = "".join(f"<th>{e(x)}</th>" for x in hd)
        b = "".join("<tr>" + "".join(f"<td>{badge(str(c)) if i == badge_col else e(str(c)).replace('`', '')}</td>"
                                     for i, c in enumerate(r)) + "</tr>" for r in rows)
        return f'<div class="tw"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'

    def tile(label, m):
        v, pv = s.get(m), p.get(m)
        if v is None:
            return ""
        d = ""
        if pv:
            ch = (v - pv) * 100 if KIND.get(m) == "rate" else (v / pv - 1) * 100
            d = f'<div class="d {"up" if ch >= 0 else "down"}">{"▲" if ch >= 0 else "▼"} {abs(ch):.1f}' \
                f'{" pts" if KIND.get(m) == "rate" else "%"} vs last week</div>'
        return f'<div class="tile"><div class="l">{e(label)}</div><div class="v">{e(fmt_metric(m, v))}</div>{d}</div>'
    tiles = "".join(tile(lab, m) for lab, m in (("Avg DAU", "dau"), ("D1 retention", "d1"), ("Revenue", "revenue"),
                                                ("Payer conversion", "payer_conversion")))
    sec = lambda t, lines: (f"<h2>{e(t)}</h2><ul>" + "".join(f"<li>{e(x)}</li>" for x in lines) + "</ul>") if lines else ""  # noqa: E731
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Risky Rails weekly memo</title><style>
:root{{--bg:#f9f9f7;--card:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--mut:#898781;--line:#e1e0d9;--good:#006300;--bad:#d03b3b;--warn:#8a5a00}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#0d0d0d;--card:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--line:#2c2c2a;--good:#0ca30c;--bad:#e66767;--warn:#fab219}}}}
:root[data-theme="dark"]{{--bg:#0d0d0d;--card:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--line:#2c2c2a;--good:#0ca30c;--bad:#e66767;--warn:#fab219}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:880px;margin:0 auto;padding:24px 16px 48px}} h1{{font-size:22px;margin:0 0 4px}} h2{{font-size:16px;margin:28px 0 8px}}
.head{{font-size:17px;font-weight:600;margin:12px 0 16px}} .tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}}
.tile{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}} .l{{color:var(--ink2);font-size:13px}}
.v{{font-size:26px;font-weight:600}} .d{{font-size:12px;color:var(--ink2)}}
.tw{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);white-space:nowrap}} th{{color:var(--ink2);font-weight:600}}
.b{{font-weight:600}} .b.good{{color:var(--good)}} .b.bad{{color:var(--bad)}} .b.warn{{color:var(--warn)}}
svg{{max-width:100%;height:auto;display:block;margin:12px 0}} li{{margin:4px 0}} .note{{color:var(--mut);font-size:12px}}
</style></head><body><main>
<h1>Risky Rails weekly memo</h1><div class="note">week ending {last.isoformat()} · numbers from dash.py; targets read from rr-bible</div>
<div class="head">{e(head) if not head.startswith("<!--") else "Headline pending"}</div>
<div class="tiles">{tiles}</div>
<h2>KPIs vs canon targets</h2>{table(["metric", "this week", "last week", "change", "95% CI", "target", "status"], kpis, 6)}
{"<h2>Release gates</h2>" + table(["gate", "check", "now", "needs", "status", "canon"], gates, 4) if gates else ""}
{sec("What moved", flags or ["nothing beyond noise"])}{sec("Funnels", funs)}{sec("Economy", ecos)}{sec("Experiments (status only)", exps)}
<h2>Charts</h2>{"".join(svgs)}
{sec("Actions (owner decides)", [x for x in acts if not x.startswith("<!--")])}
<h2>Data notes</h2><ul class="note">{"".join(f"<li>{e(x)}</li>" for x in notes)}</ul>
</main></body></html>
"""


def cmd_demo(a):
    """SYNTHETIC exports (clearly labelled) in several shapes, for tests and for learning the formats."""
    import random
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(5)
    start = dt.date(2026, 8, 31)
    days = [start + dt.timedelta(days=i) for i in range(28)]
    with open(out / "SYNTHETIC_engagement_wide.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["SYNTHETIC DATA - not a real export"])
        w.writerow(["Date", "Daily Active Users", "New Users", "Visits", "Average Session Length (s)"])
        for i, d in enumerate(days):
            dau = int(90 + 3 * i + rng.gauss(0, 6) + (25 if d.weekday() >= 5 else 0))
            w.writerow([d.strftime("%m/%d/%Y"), f"{dau:,}", int(dau * 0.55), int(dau * 1.6), int(640 + rng.gauss(0, 40))])
    with open(out / "SYNTHETIC_retention.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Cohort Date", "D1 Retention", "D7 Retention", "D30 Retention"])
        for i, d in enumerate(days):
            w.writerow([d.isoformat(), f"{9 + i * 0.12 + rng.gauss(0, 1):.1f}%", f"{2.1 + rng.gauss(0, .4):.1f}%" if i < 21 else "",
                        ""])
    with open(out / "SYNTHETIC_revenue_by_platform.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Platform", "Revenue", "Paying Users"])
        for i, d in enumerate(days):
            for plat, sh in (("Phone", .6), ("Desktop", .3), ("Tablet", .1)):
                w.writerow([d.isoformat(), plat, round((40 + i * 2) * sh + rng.gauss(0, 3)), max(0, round((1.6 + i * .05) * sh))])
    with open(out / "SYNTHETIC_onboarding_funnel.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Step", "Step Name", "Users"])
        for i, (n, v) in enumerate([("Joined", 1000), ("Picked up tool", 820), ("Shovelled coal", 700),
                                    ("Pulled lever", 610), ("First bank", 380), ("Run end", 350)]):
            w.writerow([i + 1, n, v])
    with open(out / "SYNTHETIC_economy.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Flow Type", "Transaction Type", "Item SKU", "Amount"])
        for d in days[-7:]:
            w.writerow([d.isoformat(), "Source", "Gameplay", "fare_bank", 150000 + rng.randint(-9000, 9000)])
            w.writerow([d.isoformat(), "Sink", "Shop", "coal", 21000 + rng.randint(-2000, 2000)])
            w.writerow([d.isoformat(), "Sink", "Shop", "loco_2", 60000 + rng.randint(-8000, 8000)])
    print(f"wrote SYNTHETIC exports to {out}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    i = sub.add_parser("inspect")
    i.add_argument("file")
    i.add_argument("--metric")
    i.add_argument("--kind", choices=["daily", "funnel", "economy"])
    i.add_argument("--map", action="append", default=[])
    g = sub.add_parser("ingest")
    g.add_argument("files", nargs="+")
    g.add_argument("--store")
    g.add_argument("--metric")
    g.add_argument("--kind", choices=["daily", "funnel", "economy"])
    g.add_argument("--name")
    g.add_argument("--map", action="append", default=[])
    m = sub.add_parser("memo")
    m.add_argument("--store")
    m.add_argument("--week-ending")
    m.add_argument("--out")
    m.add_argument("--sim")
    m.add_argument("--revenue-is", choices=["earned", "gross"], default="earned")
    m.add_argument("--headline")
    m.add_argument("--action", action="append")
    d = sub.add_parser("demo")
    d.add_argument("out")
    a = ap.parse_args()
    if not a.cmd:
        ap.print_help()
        return 2
    return {"inspect": cmd_inspect, "ingest": cmd_ingest, "memo": cmd_memo, "demo": cmd_demo}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
