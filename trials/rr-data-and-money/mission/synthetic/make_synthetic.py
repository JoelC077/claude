#!/usr/bin/env python3
"""SYNTHETIC data for the rr-data-and-money trial (seeded, reproducible). Not Risky Rails data.
Writes SYNTHETIC_dashboard_30d.csv (one wide Creator-Dashboard-style export, 30 days to 2026-09-27) and
SYNTHETIC_thumbs_2arm.csv (thumbnail personalization totals, 14 days to 2026-09-27).
Story baked in: slow growth; outage 2026-09-10 (DAU dip); onboarding tweak 2026-09-15 (D1 up about 1.5 pts);
Update 1 on 2026-09-19 with a featuring bump 2026-09-20..21; payer conversion under the 1.5% canon target.
  python3 make_synthetic.py [--out DIR]"""
import argparse, csv, datetime as dt, math, random
from pathlib import Path
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--out", default=str(Path(__file__).resolve().parent))
a = ap.parse_args()
rng = random.Random(20260928)
end = dt.date(2026, 9, 27); days = [end - dt.timedelta(days=29 - i) for i in range(30)]
rows = []
for i, d in enumerate(days):
    wk = 1.18 if d.weekday() >= 5 else 1.0
    new = 70 + i * 1.2
    if d == dt.date(2026, 9, 10): new *= 0.55
    if d in (dt.date(2026, 9, 20), dt.date(2026, 9, 21)): new *= 1.9
    if d >= dt.date(2026, 9, 19): new *= 1.12
    new = round(new * wk * rng.uniform(0.9, 1.1))
    dau = round((new * 1.55 + 18 + i * 1.6) * rng.uniform(0.95, 1.05))
    if d == dt.date(2026, 9, 10): dau = round(dau * 0.62)
    d1p = (0.104 if d < dt.date(2026, 9, 15) else 0.121) + rng.gauss(0, 0.012)
    d7p = 0.021 + rng.gauss(0, 0.004)
    d1 = max(0, round(new * d1p)) / new
    d7 = max(0, round(new * d7p)) / new
    payers = sum(1 for _ in range(dau) if rng.random() < 0.0128)
    rev = sum(rng.choice([99, 99, 249, 299, 299, 399, 49]) for _ in range(payers))
    sess_s = round(rng.gauss(655, 45))
    imp = round((3900 + i * 25) * (1.8 if d in (dt.date(2026, 9, 20), dt.date(2026, 9, 21)) else 1) * rng.uniform(0.92, 1.08))
    rows.append({
        "Date": d.strftime("%m/%d/%Y"),
        "Daily Active Users": dau,
        "New Users": new,
        "Visits": round(dau * rng.uniform(1.35, 1.5)),
        "Average Session Time (seconds)": sess_s,
        "Day 1 Retention": "" if i >= 29 else f"{d1:.1%}",
        "Day 7 Retention": "" if i >= 23 else f"{d7:.1%}",
        "Robux Earned": round(rev * 0.7),
        "Paying Users": payers,
        "Home Impressions": imp,
        "Qualified Play-Through Rate": f"{rng.gauss(0.031, 0.002):.2%}",
    })
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
p = out / "SYNTHETIC_dashboard_30d.csv"
with open(p, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
# thumbnail personalization, 14 days: B (crash) truly better; the bandit shifts impressions towards B late on
A_imp, B_imp, A_q, B_q = 0, 0, 0, 0
for i in range(14):
    tot = round(4100 * rng.uniform(0.9, 1.1)); share_b = 0.5 if i < 4 else min(0.62, 0.5 + 0.015 * (i - 3))
    bi = round(tot * share_b); ai = tot - bi
    A_imp += ai; B_imp += bi
    A_q += sum(1 for _ in range(ai) if rng.random() < 0.0305); B_q += sum(1 for _ in range(bi) if rng.random() < 0.0352)
t = out / "SYNTHETIC_thumbs_2arm.csv"
with open(t, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["variant", "impressions", "qualified_plays", "session_min_per_qualified_play"])
    w.writerow(["A_lever_calm", A_imp, A_q, 10.9]); w.writerow(["B_boiler_blast", B_imp, B_q, 10.1])
print("wrote", p, "and", t)
