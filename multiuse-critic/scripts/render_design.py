#!/usr/bin/env python3
"""Render Design-canvas artboards (or plain .html pages) to PNG and measure objective problems.
python3 render_design.py ROOT OUT [--boards A.dc.html,B.dc.html]   (ROOT = the folder `Artifact read` saved into)"""
import argparse, glob, html, json, mimetypes, os, re, shutil, subprocess, tarfile, urllib.parse
from collections import Counter
from playwright.sync_api import sync_playwright
from PIL import Image, ImageFilter, ImageOps

HOST = "http://dc.local"
FONTS = os.path.expanduser("~/.cache/design-critique")
MEASURE_JS = r"""
({W, H, touch}) => {
  const cv = document.createElement('canvas'); cv.width = cv.height = 1;
  const cx = cv.getContext('2d', {willReadFrequently: true});
  const rgba = c => { cx.clearRect(0,0,1,1); cx.fillStyle = '#000'; cx.fillStyle = c; cx.fillRect(0,0,1,1);
    const d = cx.getImageData(0,0,1,1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const lin = v => (v /= 255) <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  const lum = c => 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2]);
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const over = (t, b) => [0,1,2].map(i => t[i] * t[3] + b[i] * (1 - t[3])).concat([1]);
  const hex = c => '#' + c.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join('');
  const R = r => ({x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height)});
  const seen = el => el.checkVisibility ? el.checkVisibility({checkOpacity: true, checkVisibilityCSS: true, opacityProperty: true, visibilityProperty: true}) : true;
  const say = el => (el.getAttribute('aria-label') || el.innerText || el.textContent || el.getAttribute('alt') || (el.labels && el.labels[0] && el.labels[0].innerText) || el.getAttribute('placeholder') || '').replace(/\s+/g, ' ').trim().slice(0, 50);
  const tag = el => el.tagName.toLowerCase();
  const skip = new Set(['script','style','head','meta','link','title','x-dc','helmet','template','noscript']);
  const els = [...document.body.querySelectorAll('*')].filter(el => !skip.has(tag(el)) && !el.closest('x-dc') && seen(el));
  const out = {texts: [], clipped: [], spill: [], offboard: [], overlaps: [], targets: [], clickDivs: [], unlabeled: [], images: [], placeholders: [], stats: {}};

  const bgOf = el => { const layers = []; let complex = false;
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) { const cs = getComputedStyle(n);
      if (cs.backgroundImage !== 'none') complex = true;
      const c = rgba(cs.backgroundColor); if (c[3] > 0) { layers.push(c); if (c[3] >= 1) break; } }
    let b = [255, 255, 255, 1]; for (let i = layers.length - 1; i >= 0; i--) b = over(layers[i], b);
    return {bg: b, complex}; };
  const fade = el => { let o = 1; for (let n = el; n && n.nodeType === 1; n = n.parentElement) o *= parseFloat(getComputedStyle(n).opacity); return o; };
  const clipTo = (el, q) => { let x = q.x, y = q.y, x2 = q.x + q.w, y2 = q.y + q.h;   // the part not cut off by overflow boxes
    for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) { const cs = getComputedStyle(n);
      if (/(hidden|clip|auto|scroll)/.test(cs.overflowX + cs.overflowY)) { const r = n.getBoundingClientRect();
        x = Math.max(x, r.left); y = Math.max(y, r.top); x2 = Math.min(x2, r.right); y2 = Math.min(y2, r.bottom); } }
    return {x: Math.round(x), y: Math.round(y), w: Math.max(0, Math.round(x2 - x)), h: Math.max(0, Math.round(y2 - y))}; };

  for (const el of els) {                       // text runs: own text nodes, tight bounds
    const nodes = [...el.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim());
    if (!nodes.length) continue;
    const rg = document.createRange(); let box = null;
    for (const n of nodes) { rg.selectNodeContents(n); const r = rg.getBoundingClientRect();
      if (r.width < 1) continue; box = box ? {l: Math.min(box.l, r.left), t: Math.min(box.t, r.top), r: Math.max(box.r, r.right), b: Math.max(box.b, r.bottom)} : {l: r.left, t: r.top, r: r.right, b: r.bottom}; }
    if (!box) continue;
    const cs = getComputedStyle(el), isSvg = el instanceof SVGElement;
    let fg = rgba(isSvg ? cs.fill : cs.color); if (fg[3] === 0) continue;
    const {bg, complex} = bgOf(isSvg ? el.ownerSVGElement || el : el);
    fg = [...fg.slice(0, 3), fg[3] * fade(el)];
    const fs = parseFloat(cs.fontSize), fw = parseInt(cs.fontWeight) || 400;
    const eff = over(fg, bg);
    const rect = {x: Math.round(box.l), y: Math.round(box.t), w: Math.round(box.r - box.l), h: Math.round(box.b - box.t)};
    const vis = clipTo(el, rect);
    if (vis.w < 2 || vis.h < 2) continue;         // entirely cut off: reported under clipped, not as text
    out.texts.push({i: out.texts.length, el, text: nodes.map(n => n.textContent).join(' ').replace(/\s+/g, ' ').trim().slice(0, 60),
      fs: Math.round(fs * 10) / 10, fw, family: cs.fontFamily.split(',')[0].replace(/["']/g, '').trim(),
      fg: hex(eff), bg: hex(bg), complex, ratio: Math.round(ratio(eff, bg) * 100) / 100,
      large: fs >= 24 || (fs >= 18.66 && fw >= 700), rect, vis});
  }
  for (const t of out.texts) {                  // text spilling out of its box (overflow boxes are 'clipped' instead)
    for (let n = t.el; n && n !== document.body; n = n.parentElement) { const cs = getComputedStyle(n);
      if (cs.overflowX !== 'visible' || cs.overflowY !== 'visible') break;
      const boxed = rgba(cs.backgroundColor)[3] > 0 || parseFloat(cs.borderTopWidth) > 0;
      if (!boxed) continue; const r = n.getBoundingClientRect(), q = t.rect;
      if (q.x < r.left - 2 || q.y < r.top - 2 || q.x + q.w > r.right + 2 || q.y + q.h > r.bottom + 2)
        out.spill.push({text: t.text, box: say(n).slice(0, 30), rect: t.rect});
      break; }
  }
  const ink = t => { const top = Math.max(t.vis.y, t.rect.y + 0.18 * t.fs), bot = Math.min(t.vis.y + t.vis.h, t.rect.y + t.rect.h - 0.12 * t.fs);
    return {x: t.vis.x, w: t.vis.w, y: top, h: Math.max(1, bot - top)}; };   // visible glyph box, not the line box
  for (let a = 0; a < out.texts.length; a++) for (let b = a + 1; b < out.texts.length; b++) {   // text on text
    const p = out.texts[a], q = out.texts[b]; if (p.el.contains(q.el) || q.el.contains(p.el)) continue;
    const P = ink(p), Q = ink(q);
    const w = Math.min(P.x + P.w, Q.x + Q.w) - Math.max(P.x, Q.x), h = Math.min(P.y + P.h, Q.y + Q.h) - Math.max(P.y, Q.y);
    if (w > 0 && h > 0 && w * h > 0.25 * Math.min(P.w * P.h, Q.w * Q.h))
      out.overlaps.push({a: p.text, b: q.text, at: {x: Math.round(Math.max(P.x, Q.x)), y: Math.round(Math.max(P.y, Q.y))}});
  }
  const hitTags = new Set(['button','a','input','select','textarea','summary','label']);
  for (const el of els) { const cs = getComputedStyle(el), r = el.getBoundingClientRect(), t = tag(el);
    if (/(hidden|clip)/.test(cs.overflowX + cs.overflowY) && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1) && el.textContent.trim())
      out.clipped.push({el: say(el) || t, by: {w: el.scrollWidth - el.clientWidth, h: el.scrollHeight - el.clientHeight}, rect: R(r)});
    if ((cs.textOverflow === 'ellipsis' || cs.webkitLineClamp !== 'none') && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1))
      out.clipped.push({el: say(el), by: 'truncated (ellipsis/line-clamp)', rect: R(r)});
    if ((r.right > W + 1 || r.bottom > H + 1 || r.left < -1 || r.top < -1) && !out.offboard.some(o => o.node.contains(el)))
      out.offboard.push({node: el, el: say(el) || t, rect: R(r)});
    const interactive = el.matches('button, a[href], input:not([type=hidden]), select, textarea, summary, [role=button], [role=link], [tabindex]:not([tabindex="-1"])');
    const inSentence = cs.display === 'inline' && [...el.parentElement.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());   // WCAG exempts links inside text
    if (interactive && !inSentence && (r.width < (touch ? 44 : 24) || r.height < (touch ? 44 : 24))) out.targets.push({node: el, el: say(el) || t, w: Math.round(r.width), h: Math.round(r.height), min: touch ? 44 : 24});
    const named = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || el.getAttribute('title') || (el.labels && el.labels.length)
      || (t !== 'input' && t !== 'select' && t !== 'textarea' && (el.innerText || '').trim()) || el.querySelector('img[alt]:not([alt=""])');
    if (interactive && !named) out.unlabeled.push({el: say(el) || t, note: el.getAttribute('placeholder') ? 'placeholder only, no label' : 'no accessible name', rect: R(r)});
    if (cs.cursor === 'pointer' && !hitTags.has(t) && !el.closest('button, a, label, summary') && getComputedStyle(el.parentElement).cursor !== 'pointer')
      out.clickDivs.push({el: say(el) || t, rect: R(r)});
    if (t === 'img') { if (!el.complete || el.naturalWidth === 0) out.images.push({problem: 'broken', src: (el.getAttribute('src') || '').slice(0, 60), rect: R(r)});
      if (el.getAttribute('alt') === null) out.images.push({problem: 'no alt', src: (el.getAttribute('src') || '').slice(0, 60), rect: R(r)}); }
  }
  if (!touch) {   // desktop: WCAG 2.5.8 spacing exception, a 24px circle around a small target touching nothing else is fine
    const all = els.filter(el => el.matches('button, a[href], input:not([type=hidden]), select, textarea, summary, [role=button], [role=link]')).map(el => el.getBoundingClientRect());
    out.targets = out.targets.filter(({node}) => { const r = node.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      return all.some(o => { if (o.left === r.left && o.top === r.top) return false;
        const dx = Math.max(o.left - cx, 0, cx - o.right), dy = Math.max(o.top - cy, 0, cy - o.bottom); return dx * dx + dy * dy < 144; }); });
  }
  out.targets = out.targets.map(({node, ...o}) => o);
  out.stats.contentSize = {w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight};
  out.stats.title = document.title;
  const txt = document.body.innerText;
  out.placeholders = [...new Set((txt.match(/lorem ipsum|\blorem\b|\bTODO\b|\bTBD\b|\[[A-Z0-9][A-Z0-9 _.,'\-]{2,}\]|\?\?\?|placeholder/gi) || []))].slice(0, 12);
  const count = xs => Object.entries(xs.reduce((m, x) => (m[x] = (m[x] || 0) + 1, m), {})).sort((a, b) => b[1] - a[1]);
  out.stats.fontSizes = count(out.texts.map(t => t.fs + 'px'));
  out.stats.families = count(out.texts.map(t => t.family));
  out.stats.textColors = count(out.texts.map(t => t.fg));
  const probe = document.createElement('canvas').getContext('2d'), S = 'mmmmmmmmmmlli1WQ@#';   // does the face really render?
  const has = (f, w) => ['monospace', 'serif'].some(fb => { probe.font = `${w} 40px ${fb}`; const a = probe.measureText(S).width;
    probe.font = `${w} 40px "${f}", ${fb}`; return probe.measureText(S).width !== a; });
  out.stats.fontsMissing = [...new Set(out.texts.filter(t => !/^(serif|sans-serif|monospace|system-ui|cursive|fantasy|ui-[\w-]+|-apple-system|BlinkMacSystemFont)$/i.test(t.family)
    && !has(t.family, t.fw)).map(t => t.family))];
  out.offboard = out.offboard.slice(0, 10).map(({node, ...o}) => o);
  out.texts = out.texts.map(({el, ...t}) => t);
  return out;
}
"""


def slug_of(spec):
    return re.sub(r"[^a-z0-9]+", "-", spec.partition(":")[0].lower()).strip("-")


def install_fonts(files):
    """Google Fonts are unreachable from the sandbox; npm is not. Fetch each family's @fontsource package."""
    specs = set()
    for f in files:
        for href in re.findall(r"fonts\.googleapis\.com/css2?\?[^\"'\s)]+", open(f, encoding="utf-8", errors="ignore").read()):
            specs.update(urllib.parse.parse_qs(urllib.parse.urlparse("https://" + html.unescape(href)).query).get("family", []))
    os.makedirs(FONTS, exist_ok=True)
    pj = os.path.join(FONTS, "package.json")
    if not os.path.exists(pj):   # a package.json makes installs accumulate instead of pruning each other
        json.dump({"name": "design-critique-fonts", "private": True}, open(pj, "w"))
    for slug in sorted({slug_of(s) for s in specs}):
        if not os.path.isdir(os.path.join(FONTS, "node_modules", "@fontsource", slug)):
            subprocess.run(["npm", "install", "--prefix", FONTS, "--no-audit", "--no-fund", "--loglevel=error",
                            f"@fontsource/{slug}"], capture_output=True, timeout=180)


def font_css(spec, missing):
    """@font-face CSS for one Google Fonts `family=` value, served from the @fontsource npm package."""
    name, _, axes = spec.partition(":")
    slug = slug_of(spec)
    pkg = os.path.join(FONTS, "node_modules", "@fontsource", slug)
    if not os.path.isdir(pkg):
        missing.add(name)
        return ""
    wants = []
    if axes:
        tags, _, vals = axes.partition("@")
        for tup in vals.split(";"):
            d = dict(zip(tags.split(","), tup.split(",")))
            w = d.get("wght", "400")
            lo, hi = w.split("..") if ".." in w else (w, w)
            wants.append((float(lo), float(hi), d.get("ital", "0") == "1"))
    wants = wants or [(400, 400, False)]
    css = []
    for f in sorted(os.listdir(pkg)):
        m = re.fullmatch(r"(\d{3})(-italic)?\.css", f)
        if m and any(lo <= int(m[1]) <= hi and bool(m[2]) == it for lo, hi, it in wants):
            css.append(open(os.path.join(pkg, f)).read().replace("url(./files/", f"url({HOST}/__fonts/{slug}/files/"))
    if not css:
        missing.add(f"{name} (weights {axes or '400'})")
    return "\n".join(css)


def cdn_file(url):
    """jsdelivr and cdnjs are blocked in the sandbox too; fetch the same library version from npm."""
    m = re.match(r"https://cdn\.jsdelivr\.net/npm/((?:@[^/@]+/)?[^/@]+)(?:@([^/]+))?(/[^?#]*)?", url)
    c = re.match(r"https://cdnjs\.cloudflare\.com/ajax/libs/([^/]+)/([^/]+)/([^?#]+)", url)
    if not (m or c):
        return None
    name, ver, path = (m or c).group(1), (m or c).group(2) or "latest", ((m or c).group(3) or "").lstrip("/")
    for n in [name] if m else dict.fromkeys([name.lower(), re.sub(r"\.js$", "", name.lower())]):
        d = os.path.join(FONTS, "cdn", f"{n.replace('/', '+')}@{ver}")
        if not os.path.isdir(os.path.join(d, "package")):
            os.makedirs(d, exist_ok=True)
            subprocess.run(["npm", "pack", f"{n}@{ver}", "--pack-destination", d], capture_output=True, timeout=180)
            for tgz in glob.glob(os.path.join(d, "*.tgz")):
                with tarfile.open(tgz) as t:
                    t.extractall(d, filter="data") if hasattr(tarfile, "data_filter") else t.extractall(d)
        pkg = os.path.join(d, "package")
        if not os.path.isdir(pkg):
            continue
        if m and not path:   # bare package URL: jsdelivr serves its browser entry point
            meta = json.load(open(os.path.join(pkg, "package.json")))
            path = next((meta[k] for k in ("jsdelivr", "unpkg", "browser", "main") if isinstance(meta.get(k), str)), "index.js")
        hits = [os.path.join(pkg, p) for p in (path, "dist/" + path, path.replace(".min.", "."))]   # jsdelivr minifies on the fly
        if c:
            hits += [os.path.join(r, os.path.basename(path)) for r, _, fs in os.walk(pkg) if os.path.basename(path) in fs]
        for f in hits:
            if os.path.isfile(f):
                return f
    return None


def sample_bg(img, rect, fg, scale):
    """The background a viewer actually sees behind a text run: the most common colour inside
    its box once pixels close to the text colour (the glyphs) are dropped. Catches SVG shapes,
    positioned siblings, images and gradients that a CSS ancestor walk misses."""
    x0, y0 = max(0, int(rect["x"] * scale)), max(0, int(rect["y"] * scale))
    x1, y1 = min(img.width, int((rect["x"] + rect["w"]) * scale)), min(img.height, int((rect["y"] + rect["h"]) * scale))
    if x1 <= x0 or y1 <= y0:   # text outside the captured frame (it overflows the artboard)
        return None, 0
    step = max(1, int(((x1 - x0) * (y1 - y0) / 4000) ** 0.5))
    px = [img.getpixel((x, y)) for x in range(x0, x1, step) for y in range(y0, y1, step)]
    px = [p for p in px if sum(abs(p[i] - fg[i]) for i in range(3)) > 60]
    if not px:
        return None, 0
    (col, n), = Counter((r // 6 * 6 + 3, g // 6 * 6 + 3, b // 6 * 6 + 3) for r, g, b in px).most_common(1)
    return tuple(min(255, c) for c in col), n / len(px)


def detail_views(png, scale):
    """The Read tool shrinks big images to ~1.2 MP, so tall pages and huge boards also get
    readable slices: <stem>.part<N>.png, each at most ~1400 CSS px on a side."""
    img = Image.open(png)
    side = int(1400 * scale)
    if img.width * img.height <= 2_300_000 and max(img.width, img.height) <= 2 * side:
        return []
    cols = 1 if img.width <= 1.25 * side else -(-img.width // side)   # tall pages: full-width bands
    rows = -(-img.height // side)
    tw, th = -(-img.width // cols), -(-img.height // rows)
    parts = []
    for r in range(rows):
        for c in range(cols):
            p = png[:-4] + f".part{len(parts) + 1}.png"
            img.crop((c * tw, r * th, min(img.width, (c + 1) * tw), min(img.height, (r + 1) * th + int(40 * scale)))).save(p)
            parts.append(p)
    return parts


def contrast(a, b):
    def L(c):
        c = [v / 255 for v in c]
        c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    x, y = L(a), L(b)
    return round((max(x, y) + 0.05) / (min(x, y) + 0.05), 2)


def shoot(page, png, w, h, fill, scale, meta, errors, failed):
    """Screenshot the page as it stands, measure it, and return its report entry."""
    page.screenshot(path=png, full_page=fill, clip=None if fill else {"x": 0, "y": 0, "width": w, "height": h})
    m = page.evaluate(MEASURE_JS, {"W": w, "H": 10 ** 6 if fill else h, "touch": w <= 600})
    img = Image.open(png).convert("RGB")
    for t in m["texts"]:
        fg = tuple(int(t["fg"][i:i + 2], 16) for i in (1, 3, 5))
        bg, share = sample_bg(img, t["vis"], fg, scale)
        if bg is not None and contrast(bg, tuple(int(t["bg"][i:i + 2], 16) for i in (1, 3, 5))) > 1.15:
            t["bg"], t["ratio"] = "#%02x%02x%02x" % bg + ("~busy" if share < 0.35 else "~px"), contrast(fg, bg)
    ImageOps.grayscale(img).resize((max(1, img.width // 2), max(1, img.height // 2))) \
        .filter(ImageFilter.GaussianBlur(4)).save(png[:-4] + ".squint.png")
    lows = {}
    for t in m["texts"]:
        need = 3 if t["large"] else 4.5
        if t["ratio"] < need:
            lows.setdefault((t["text"], t["fg"], t["bg"], t["fs"]), dict(t, need=need, count=0))["count"] += 1
    is_print = bool(meta.get("print") or meta.get("paper"))
    floor = 16 if is_print else 12            # 12pt is the print minimum; 12px on screen
    small = Counter((t["text"], t["fs"]) for t in m["texts"] if t["fs"] < floor)
    return {
        "title": meta.get("title") or m["stats"]["title"], "size": f"{w}x{h}", "print": is_print, "min_text_px": floor,
        "fluid": fill, "png": png, "detail_views": detail_views(png, scale),
        "errors": list(dict.fromkeys(errors))[:10], "failed_requests": list(dict.fromkeys(failed))[:10],
        "contrast_fails": sorted(lows.values(), key=lambda t: t["ratio"])[:15],
        "small_text": [{"text": k[0], "px": k[1], "count": c} for k, c in small.most_common(10)],
        **{k: m[k][:12] for k in ("clipped", "spill", "offboard", "overlaps", "targets", "clickDivs", "unlabeled", "images")},
        "placeholders": m["placeholders"], "content_size": m["stats"]["contentSize"],
        "font_sizes": m["stats"]["fontSizes"], "families": m["stats"]["families"],
        "text_colors": m["stats"]["textColors"][:12], "fonts_not_loaded": m["stats"]["fontsMissing"],
        "text_count": len(m["texts"]), "min_contrast": min((t["ratio"] for t in m["texts"]), default=None),
    }


def launch(pw):
    """Playwright's own Chromium if it matches this Playwright version; otherwise a Chromium already on the machine."""
    try:
        return pw.chromium.launch()
    except Exception:
        for exe in (os.environ.get("CHROMIUM_PATH"), "/opt/pw-browsers/chromium", shutil.which("chromium"),
                    shutil.which("chromium-browser"), shutil.which("google-chrome")):
            if exe and os.path.exists(exe):
                return pw.chromium.launch(executable_path=exe)
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root"); ap.add_argument("out")
    ap.add_argument("--boards", default="", help="comma-separated board paths under project/ (default: all)")
    a = ap.parse_args()
    root, out = os.path.abspath(a.root), os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    proj = os.path.join(root, "project") if os.path.isdir(os.path.join(root, "project")) else root
    runtime = os.path.join(root, "artifact-type", "dc-runtime.js")
    cpath = os.path.join(proj, "canvas.json")
    canvas = json.load(open(cpath)) if os.path.exists(cpath) else {"boards": {}, "order": []}
    local = sorted(os.path.relpath(p, proj) for p in glob.glob(os.path.join(proj, "**", "*.html"), recursive=True))
    boards = [b for b in a.boards.split(",") if b] or [b for b in canvas.get("order", []) if b in local] or local
    missing_fonts, report = set(), {}
    install_fonts([os.path.join(proj, p) for p in local])

    def open_page(browser, board, w, h, scale):
        """Load a board or page in a fresh tab, everything served locally, and let it settle."""
        ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=scale)
        page, errors, failed = ctx.new_page(), [], []
        page.on("console", lambda m: m.type == "error" and errors.append(m.text[:200]))
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))

        def serve(route):
            url = route.request.url
            u = urllib.parse.urlparse(url)
            if url.startswith("https://fonts.googleapis.com/css"):
                q = urllib.parse.parse_qs(u.query)
                return route.fulfill(status=200, content_type="text/css",
                                     body="\n".join(font_css(s, missing_fonts) for s in q.get("family", [])))
            if u.netloc in ("cdn.jsdelivr.net", "cdnjs.cloudflare.com") and (f := cdn_file(url)):
                return route.fulfill(status=200, body=open(f, "rb").read(), headers={"Access-Control-Allow-Origin": "*"},
                                     content_type=mimetypes.guess_type(f)[0] or "text/javascript")
            if u.netloc != "dc.local":
                failed.append(url[:120])
                return route.abort()
            path = urllib.parse.unquote(u.path)
            if path.startswith("/__fonts/"):
                slug, rest = path[len("/__fonts/"):].split("/", 1)
                f = os.path.join(FONTS, "node_modules", "@fontsource", slug, rest)
            elif path.startswith("/_blob/"):
                hits = glob.glob(os.path.join(root, "**", path.split("/")[2] + "*"), recursive=True)
                f = hits[0] if hits else None
            elif path.endswith("/support.js"):
                f = runtime
            else:
                f = os.path.join(root, path.lstrip("/"))
            if f and os.path.isfile(f):
                return route.fulfill(status=200, body=open(f, "rb").read(),
                                     content_type=mimetypes.guess_type(f)[0] or "application/octet-stream")
            failed.append(path)
            return route.fulfill(status=404, body="")

        page.route("**/*", serve)
        page.goto(f"{HOST}/" + os.path.relpath(os.path.join(proj, board), root).replace(os.sep, "/"), wait_until="load")
        if board.endswith(".dc.html"):
            try:
                page.wait_for_function("() => window.__dcRegistry !== undefined", timeout=15000)
            except Exception:
                errors.append("design runtime never booted (is artifact-type/dc-runtime.js in ROOT?)")
        page.evaluate("() => document.fonts.ready.then(() => true)")
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(1200)   # let entrance animations and chart transitions settle
        return ctx, page, errors, failed

    with sync_playwright() as pw:
        browser = launch(pw)
        for board in boards:
            meta = canvas.get("boards", {}).get(board, {})
            w, h = int(meta.get("w", 1280)), int(meta.get("h", 800))
            fill = meta.get("expand") == "fill" or not board.endswith(".dc.html")
            scale = 2 if w <= 600 else 1
            stem = re.sub(r"\.dc\.html$|\.html$", "", board).replace("/", "__")
            ctx, page, errors, failed = open_page(browser, board, w, h, scale)
            report[board] = shoot(page, os.path.join(out, stem + ".png"), w, h, fill, scale, meta, errors, failed)
            ctx.close()
            if fill and w > 600:   # fluid page: load it fresh at phone width too, where most problems show
                ctx, page, errors, failed = open_page(browser, board, 390, 844, 2)
                report[board + " @390px"] = shoot(page, os.path.join(out, stem + ".mobile.png"), 390, 844, True, 2, meta, errors, failed)
                ctx.close()
        browser.close()

    report["_fonts_unavailable"] = sorted(missing_fonts)
    json.dump(report, open(os.path.join(out, "report.json"), "w"), indent=1)
    lines = []
    for b, r in report.items():
        if b.startswith("_"):
            continue
        lines.append(f"## {b} — {r['title']} ({r['size']}{', fluid' if r['fluid'] else ''}{', print' if r['print'] else ''})")
        lines.append(f"render: {r['png']}" + (f" + detail views: {', '.join(os.path.basename(v) for v in r['detail_views'])}" if r["detail_views"] else ""))
        lines.append(f"texts: {r['text_count']} · min contrast {r['min_contrast']} · {len(r['font_sizes'])} sizes: {', '.join(s for s, _ in r['font_sizes'][:12])} · "
                     f"families: {', '.join(f for f, _ in r['families'])} · {len(r['text_colors'])} text colours")
        for key, label in [("errors", "RENDER ERRORS"), ("failed_requests", "failed requests"), ("fonts_not_loaded", "fonts not loaded (render uses fallback)"),
                           ("contrast_fails", "contrast below WCAG AA"), ("small_text", f"text under {r['min_text_px']}px"), ("clipped", "clipped/truncated content"),
                           ("spill", "text spilling out of its box"), ("offboard", "outside the artboard frame"), ("overlaps", "text overlapping text"),
                           ("targets", "targets under the minimum (44px touch, 24px desktop)"), ("clickDivs", "clickable-looking non-buttons"), ("unlabeled", "unlabeled controls"),
                           ("images", "image problems"), ("placeholders", "placeholder text")]:
            items = r[key]
            if not items:
                continue
            lines.append(f"- {label}: {len(items)}")
            for it in items[:8]:
                if key == "contrast_fails":
                    it = f"{it['ratio']}:1 (needs {it['need']}) \"{it['text']}\" {it['fs']}px {it['fg']} on {it['bg']}" + (f" x{it['count']}" if it["count"] > 1 else "")
                lines.append(f"    - {json.dumps(it, ensure_ascii=False) if not isinstance(it, str) else it}")
        lines.append("")
    if report["_fonts_unavailable"]:
        lines.append(f"Fonts that could not be fetched: {', '.join(report['_fonts_unavailable'])} — judge type from the source, not the render.")
    open(os.path.join(out, "report.md"), "w").write("\n".join(lines))
    print("\n".join(lines))
    print(f"\nPNGs + report in {out}")


if __name__ == "__main__":
    main()
