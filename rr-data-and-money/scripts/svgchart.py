#!/usr/bin/env python3
"""Tiny stdlib SVG charts for memos and sim reports (line, small multiples, horizontal bars, grouped columns).

Follows the dataviz method: one axis, thin marks (2px lines, bars <= 24px with 4px rounded data-ends), recessive
hairline grid, text in ink tokens (never the series colour), a legend for >= 2 series, selective end labels,
native <title> tooltips on every point/bar, light and dark tokens (prefers-color-scheme and data-theme).
Palette: the validated reference categorical slots 1-3 (all-pairs safe), so at most 3 series per chart.
`python3 svgchart.py --demo OUT_DIR` writes sample charts.
"""
import math, sys
from pathlib import Path
from xml.sax.saxutils import escape

LIGHT = "--s:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--mut:#898781;--grid:#e1e0d9;--base:#c3c2b7;" \
        "--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a"
DARK = "--s:#1a1a19;--ink:#ffffff;--ink2:#c3c2b7;--mut:#898781;--grid:#2c2c2a;--base:#383835;" \
       "--s1:#3987e5;--s2:#d95926;--s3:#199e70"
STYLE = ("<style>.c{%s}@media (prefers-color-scheme: dark){:root:where(:not([data-theme=\"light\"])) .c{%s}}"
         ":root[data-theme=\"dark\"] .c{%s}"
         ".c text{font-family:system-ui,-apple-system,\"Segoe UI\",sans-serif;font-size:11px;fill:var(--ink2)}"
         ".c .t{fill:var(--ink);font-size:13px;font-weight:600}.c .st{fill:var(--mut)}.c .ax{fill:var(--mut);"
         "font-variant-numeric:tabular-nums}.c .v{fill:var(--ink)}.c .hit{fill:transparent}</style>") % (LIGHT, DARK, DARK)
SERIES = ["var(--s1)", "var(--s2)", "var(--s3)"]


def nice_ticks(vmax, n=4):
    if not vmax or vmax <= 0:
        return [0, 1]
    raw = vmax / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    top = step * math.ceil(vmax / step - 1e-9)
    return [i * step for i in range(int(round(top / step)) + 1)]


def _open(w, h, title, subtitle):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" class="c" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
         f'role="img" aria-label="{escape(title)}">', STYLE,
         f'<rect width="{w}" height="{h}" fill="var(--s)" rx="8"/>',
         f'<text class="t" x="16" y="22">{escape(title)}</text>']
    if subtitle:
        s.append(f'<text class="st" x="16" y="38">{escape(subtitle)}</text>')
    return s


def _legend(names, x, y):
    out = []
    for i, n in enumerate(names):
        out.append(f'<line x1="{x}" y1="{y - 4}" x2="{x + 14}" y2="{y - 4}" stroke="{SERIES[i]}" stroke-width="2" '
                   f'stroke-linecap="round"/><text x="{x + 19}" y="{y}">{escape(n)}</text>')
        x += 30 + 6.5 * len(n)
    return out


def _panel(x0, y0, w, h, labels, series, fmt, target, title=None):
    """Line panel inside (x0, y0, w, h). series = [(name, [v or None])]."""
    out = []
    if title:
        out.append(f'<text class="v" x="{x0}" y="{y0 - 6}">{escape(title)}</text>')
    vals = [v for _, vs in series for v in vs if v is not None]
    vmax = max(vals + ([target[0]] if target else []) + [0]) * 1.08
    ticks = nice_ticks(vmax)
    top = ticks[-1] or 1
    n = len(labels)
    px = (lambda i: x0 + (w * i / (n - 1) if n > 1 else w / 2))
    py = (lambda v: y0 + h - h * v / top)
    for t in ticks:
        yy = py(t)
        out.append(f'<line x1="{x0}" x2="{x0 + w}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="var(--grid)" stroke-width="1"/>')
        out.append(f'<text class="ax" x="{x0 - 6}" y="{yy + 3.5:.1f}" text-anchor="end">{escape(fmt(t))}</text>')
    out.append(f'<line x1="{x0}" x2="{x0 + w}" y1="{y0 + h}" y2="{y0 + h}" stroke="var(--base)" stroke-width="1"/>')
    every = max(1, math.ceil(n / 6))
    for i, lab in enumerate(labels):
        if (n - 1 - i) % every == 0:
            out.append(f'<text class="ax" x="{px(i):.1f}" y="{y0 + h + 15}" text-anchor="middle">{escape(str(lab))}</text>')
    if target:
        ty = py(target[0])
        out.append(f'<line x1="{x0}" x2="{x0 + w}" y1="{ty:.1f}" y2="{ty:.1f}" stroke="var(--ink2)" stroke-width="1"/>')
        out.append(f'<text x="{x0 + 4}" y="{ty - 4:.1f}" stroke="var(--s)" stroke-width="3" paint-order="stroke">'
                   f'{escape(target[1])}</text>')
    ends = []
    for si, (name, vs) in enumerate(series):
        col = SERIES[si % 3]
        d, pen = [], False
        for i, v in enumerate(vs):
            if v is None:
                pen = False
                continue
            d.append(f'{"L" if pen else "M"}{px(i):.1f},{py(v):.1f}')
            pen = True
        if d:
            out.append(f'<path d="{" ".join(d)}" fill="none" stroke="{col}" stroke-width="2" '
                       f'stroke-linejoin="round" stroke-linecap="round"/>')
        for i, v in enumerate(vs):
            if v is not None:
                out.append(f'<circle class="hit" cx="{px(i):.1f}" cy="{py(v):.1f}" r="7"><title>{escape(name)} '
                           f'{escape(str(labels[i]))}: {escape(fmt(v))}</title></circle>')
        last = max((i for i, v in enumerate(vs) if v is not None), default=None)
        if last is not None:
            ex, ey = px(last), py(vs[last])
            out.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="4" fill="{col}" stroke="var(--s)" stroke-width="2"/>')
            if all(abs(ey - e) > 13 for e in ends):
                out.append(f'<text class="v" x="{ex + 8:.1f}" y="{ey + 4:.1f}">{escape(fmt(vs[last]))}</text>')
                ends.append(ey)
    return out


def line_chart(title, labels, series, fmt=str, target=None, subtitle="", width=640, height=250):
    """series: [(name, values)] (<= 3); target: (value, 'label') drawn as a reference line."""
    s = _open(width, height, title, subtitle)
    top = 48 if subtitle else 36
    if len(series) > 1:
        s += _legend([n for n, _ in series], 16, top + 8)
        top += 16
    s += _panel(56, top + 10, width - 56 - 70, height - top - 10 - 30, labels, series, fmt, target)
    return "\n".join(s + ["</svg>"])


def small_multiples(title, labels, panels, fmt=str, subtitle="", width=720, height=230):
    """panels: [(panel_title, values, target or None)]; one series each, own scale, same x."""
    s = _open(width, height, title, subtitle)
    top = (48 if subtitle else 36) + 22
    k = len(panels)
    pw = (width - 16) / k
    for i, (pt, vs, tgt) in enumerate(panels):
        x0 = 16 + i * pw + 44
        s += _panel(x0, top, pw - 44 - 40, height - top - 30, labels, [(pt, vs)], fmt, tgt, title=pt)
    return "\n".join(s + ["</svg>"])


def _hbar_path(x0, x1, y, h, r=4):
    r = max(0.0, min(r, (x1 - x0) / 2, h / 2))
    return (f"M{x0:.1f},{y:.1f} H{x1 - r:.1f} Q{x1:.1f},{y:.1f} {x1:.1f},{y + r:.1f} V{y + h - r:.1f} "
            f"Q{x1:.1f},{y + h:.1f} {x1 - r:.1f},{y + h:.1f} H{x0:.1f} Z")


def hbar(title, rows, fmt=str, subtitle="", width=640):
    """rows: [(label, value, note)] -> horizontal bars from one baseline, value + note at the tip."""
    top = (48 if subtitle else 36) + 8
    bh, gap, lw = 18, 12, 170
    height = top + len(rows) * (bh + gap) + 12
    s = _open(width, height, title, subtitle)
    vmax = max([v for _, v, _ in rows] + [1])
    span = width - lw - 16 - 150
    s.append(f'<line x1="{lw}" x2="{lw}" y1="{top - 4}" y2="{height - 12}" stroke="var(--base)" stroke-width="1"/>')
    for i, (lab, v, note) in enumerate(rows):
        y = top + i * (bh + gap)
        x1 = lw + span * v / vmax
        tip = fmt(v) + (f" · {note}" if note else "")
        s.append(f'<text x="{lw - 8}" y="{y + 13}" text-anchor="end">{escape(str(lab))}</text>')
        s.append(f'<path d="{_hbar_path(lw, max(lw + 1, x1), y, bh)}" fill="var(--s1)"><title>{escape(str(lab))}: '
                 f'{escape(tip)}</title></path>')
        s.append(f'<text class="v" x="{x1 + 6:.1f}" y="{y + 13}">{escape(tip)}</text>')
    return "\n".join(s + ["</svg>"])


def columns(title, labels, series, fmt=str, subtitle="", width=640, height=250):
    """Grouped columns: series = [(name, values)] (<= 3), bars <= 24px, 2px gap, rounded tops."""
    s = _open(width, height, title, subtitle)
    top = 48 if subtitle else 36
    if len(series) > 1:
        s += _legend([n for n, _ in series], 16, top + 8)
        top += 16
    x0, y0 = 56, top + 10
    w, h = width - x0 - 16, height - top - 10 - 30
    vmax = max([v or 0 for _, vs in series for v in vs] + [0]) * 1.08
    ticks = nice_ticks(vmax)
    tmax = ticks[-1] or 1
    for t in ticks:
        yy = y0 + h - h * t / tmax
        s.append(f'<line x1="{x0}" x2="{x0 + w}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="var(--grid)" stroke-width="1"/>')
        s.append(f'<text class="ax" x="{x0 - 6}" y="{yy + 3.5:.1f}" text-anchor="end">{escape(fmt(t))}</text>')
    n, k = len(labels), len(series)
    band = w / max(1, n)
    bw = min(24.0, (band * 0.7 - 2 * (k - 1)) / k)
    every = max(1, math.ceil(n / 8))
    for i, lab in enumerate(labels):
        gx = x0 + i * band + (band - (k * bw + 2 * (k - 1))) / 2
        for si, (name, vs) in enumerate(series):
            v = vs[i] or 0
            bx, by = gx + si * (bw + 2), y0 + h - h * v / tmax
            r = min(4, bw / 2, (y0 + h - by) / 2) if v > 0 else 0
            d = (f"M{bx:.1f},{y0 + h:.1f} V{by + r:.1f} Q{bx:.1f},{by:.1f} {bx + r:.1f},{by:.1f} H{bx + bw - r:.1f} "
                 f"Q{bx + bw:.1f},{by:.1f} {bx + bw:.1f},{by + r:.1f} V{y0 + h:.1f} Z")
            s.append(f'<path d="{d}" fill="{SERIES[si % 3]}"><title>{escape(name)} {escape(str(lab))}: '
                     f'{escape(fmt(v))}</title></path>')
        if (n - 1 - i) % every == 0:
            s.append(f'<text class="ax" x="{x0 + i * band + band / 2:.1f}" y="{y0 + h + 15}" '
                     f'text-anchor="middle">{escape(str(lab))}</text>')
    s.append(f'<line x1="{x0}" x2="{x0 + w}" y1="{y0 + h}" y2="{y0 + h}" stroke="var(--base)" stroke-width="1"/>')
    return "\n".join(s + ["</svg>"])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--demo":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        labs = [f"09-{d:02d}" for d in range(1, 29)]
        dau = [100 + 3 * i + (i % 7) * 4 for i in range(28)]
        (out / "demo-line.svg").write_text(line_chart("DAU", labs, [("DAU", dau)], lambda v: f"{v:,.0f}",
                                                      target=(100, "gate: DAU >= 100")))
        (out / "demo-hbar.svg").write_text(hbar("Funnel", [("join", 1000, "100%"), ("first bank", 420, "42%")],
                                                lambda v: f"{v:,.0f}"))
        print("wrote", out)
    else:
        print(__doc__)
