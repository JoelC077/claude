#!/usr/bin/env python3
"""rr-ui-foundry: screen spec -> critic boards + a Roblox ScreenGui package, driven by rr-bible tokens.

  ui.py list                                    specs (specs/ or $RR_UI_SPECS) and kit templates
  ui.py show SPEC                               nodes, states, nav, boards, canon cites
  ui.py validate SPEC... [--strict] [--json]    every objective check; exit 1 on errors (--strict: warnings too)
  ui.py render SPEC --out DIR [--devices a,b] [--skins A,C] [--boards x,y] [--text-scale 1.0] [--html-only]
                                                HTML + PNG boards (device x board x skin), zone board, contact.png,
                                                closeups.png, facts.md (multiuse-critic layout)
  ui.py crit CRIT --pass N --from DIR --spec SPEC   pass-N files + brief.md from spec and canon; prints the
                                                critic_kit.py command (Profile B). Never scores anything itself.
  ui.py build SPEC... --out DIR [--skin C] [--assets ids.json] [--no-check] [--no-parity]
                                                Rojo-ready package: RR_UIKit, RR_UITheme, RR_UITemplates,
                                                screens/*, demo, icon sheet, ASSETS.md, UI_SPEC.md, manifest;
                                                gates: luaparse, bible check, lupa parity (luatest.py)
  ui.py sheet [ICONDIR] --out DIR [--cell 64]   pack SVG/PNG icons into one sprite sheet + icons.json
  ui.py ingest HTML --out SPEC [--size 844x390] [--root ROOT] [--name Screen]
                                                draft spec from an HTML mock or Design board (data-rr hints)

SPEC is a path or a name in specs/. Canon: rr-bible (found by glob or $RR_BIBLE_SKILL). Critic scripts:
multiuse-critic ($RR_CRITIC_SKILL). Standard library, plus Playwright + Pillow for render/sheet/ingest and
node luaparse / lupa for the build gates (each is skipped and named when missing).
"""
import argparse, base64, datetime, hashlib, html, json, os, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import uimodel as U  # noqa: E402

SKILL = U.SKILL
TOOLS = Path.home() / ".cache" / "rr-tools"
FONT_DIRS = [Path.home() / ".cache" / "design-critique" / "node_modules" / "@fontsource", TOOLS / "node_modules" / "@fontsource"]


def spec_path(s):
    p = Path(s)
    if p.is_file():
        return p
    root = Path(os.environ.get("RR_UI_SPECS") or SKILL / "specs")
    for c in (root / s, root / f"{s}.json"):
        if c.is_file():
            return c
    sys.exit(f"spec not found: {s}")


def load(kit, s):
    return U.Screen(kit, spec_path(s))


# ------------------------------------------------------------------ list / show / validate
def cmd_list(kit, a):
    root = Path(os.environ.get("RR_UI_SPECS") or SKILL / "specs")
    for p in sorted(root.glob("*.json")):
        sc = U.Screen(kit, p)
        print(f"  {p.stem:24} {sc.name:20} {len(sc.index):3} nodes  boards: {', '.join(b.get('name', '?') for b in sc.boards)}")
    print("templates: " + ", ".join(f"{k}{' (runtime)' if v.get('runtime') else ''}" for k, v in kit.comps.items()))
    print(f"skins: {', '.join(kit.skins)} (default {kit.default_skin}, {kit.roles['skin_oq']})  devices: {', '.join(kit.devices)}")
    return 0


def cmd_show(kit, a):
    sc = load(kit, a.spec)
    print(f"{sc.name}: {sc.raw.get('title', '')}\n  gui {sc.insets} order {sc.gui.get('display_order', 10)}"
          f"{' modal' if sc.gui.get('modal') else ''}; design {sc.design.name} area {kit.design_device.area(sc.insets)}")

    def rec(nodes, d):
        for n in nodes:
            what = n.get("template") or n.get("type")
            extra = [f"{k}={n[k]}" for k in ("pin", "stretch", "layer", "action", "on", "avoid") if n.get(k)]
            print(f"  {'  ' * d}{n['id']} [{what}] {[round(v) for v in n['rect']]} {' '.join(map(str, extra))}")
            if d < 1:
                rec(n.get("children", []), d + 1)
    rec(sc.nodes, 0)
    if sc.machine:
        print("  machine: " + "; ".join(f"{t['from']} -{t['event']}-> {t['to']}" + (f" ({t['feel']})" if t['feel'] else "")
                                         for t in sc.machine["transitions"]))
    if sc.nav["edges"]:
        print(f"  nav: default {sc.nav.get('default')}, back {sc.nav.get('back')}, rows {sc.nav['rows']}")
    print("  boards: " + ", ".join(b.get("name", "?") for b in sc.boards))
    print("  canon: " + ", ".join(sc.raw.get("canon", [])) + "  oq: " + ", ".join(sc.raw.get("oq", [])))
    return 0


def cmd_validate(kit, a):
    worst = 0
    report = {}
    for s in a.specs:
        sc = load(kit, s)
        E, W, I, F = U.check(sc)
        report[sc.name] = {"errors": E, "warnings": W, "info": I, "facts": _jsonable(F)}
        if a.json:
            continue
        status = "FAIL" if E or (a.strict and W) else "PASS"
        print(f"{status} {sc.name}: {len(E)} errors, {len(W)} warnings")
        for e in E:
            print(f"  E {e}")
        for w in W:
            print(f"  W {w}")
        for i in I:
            print(f"  i {i}")
        c = F["contrast"]
        print("  contrast (lowest per skin): " + "; ".join(f"{k} {v[0]}:1 {v[1]}" for k, v in c.items() if v))
        for d, v in F["devices"].items():
            print(f"  {d:12} k={','.join(f'{x:.3f}' for x in (v['k'] or {}).values())} min text {fmt_min(v['min_text'])}, "
                  f"min target {fmt_min(v['min_target'])}" + (f"; stack {v['stack']}" if v.get("stack") else ""))
        worst = max(worst, 1 if E or (a.strict and W) else 0)
    if a.json:
        print(json.dumps(report, indent=1))
        worst = max((1 if r["errors"] or (a.strict and r["warnings"]) else 0) for r in report.values())
    return worst


def fmt_min(v):
    return f"{v[0]:g} px ({v[1]})" if v else "-"


def _jsonable(F):
    out = dict(F)
    out["devices"] = {k: {kk: vv for kk, vv in v.items()} for k, v in F["devices"].items()}
    return json.loads(json.dumps(out, default=str))


# ------------------------------------------------------------------ fonts and icons for boards
def font_file(slug, weight):
    for d in FONT_DIRS:
        f = d / slug / "files" / f"{slug}-latin-{weight}-normal.woff2"
        if f.is_file():
            return f
    TOOLS.mkdir(parents=True, exist_ok=True)
    if shutil.which("npm"):
        subprocess.run(["npm", "install", "--prefix", str(TOOLS), "--no-audit", "--no-fund", "--loglevel=error",
                        f"@fontsource/{slug}"], capture_output=True, timeout=180)
    f = TOOLS / "node_modules" / "@fontsource" / slug / "files" / f"{slug}-latin-{weight}-normal.woff2"
    return f if f.is_file() else None


def fonts_css(kit):
    css, missing = [], []
    weights = {"display": {400}, "body": set()}
    for t in kit.types.values():
        weights[t["font"]].add(400 if t["font"] == "display" else t["weight"])
    for fam, ws in weights.items():
        name = kit.fonts[fam]["name"]
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        for w in sorted(ws):
            f = font_file(slug, w)
            if not f:
                missing.append(f"{name} {w}")
                continue
            b64 = base64.b64encode(f.read_bytes()).decode()
            css.append(f"@font-face{{font-family:'{name}';font-weight:{w};src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    return "\n".join(css), missing


def load_icons(screen):
    out = {}
    d = screen.icons_dir
    if d and d.is_dir():
        for f in d.glob("*.svg"):
            out[f.stem] = re.sub(r"<\?xml[^>]*>", "", f.read_text(encoding="utf-8"))
        for f in d.glob("*.png"):
            out.setdefault(f.stem, "data:image/png;base64," + base64.b64encode(f.read_bytes()).decode())
    return out


# ------------------------------------------------------------------ HTML emitter
def px(v):
    return f"{v:.2f}px"


def rgba(h, a=1.0):
    r, g, b = U.hex_rgb(h)
    return f"rgba({r},{g},{b},{a:.3f})" if a < 0.999 else h


def node_html(it, ox, oy, icons, kit, skin):
    x, y, w, h = it["box"]
    st = [f"left:{px(x - ox)}", f"top:{px(y - oy)}", f"width:{px(w)}", f"height:{px(h)}"]
    a = it.get("alpha", 1.0)
    if it.get("gradient") and all(it["gradient"]):
        g0, g1 = it["gradient"]
        st.append(f"background:linear-gradient(180deg,{rgba(g0, a)},{rgba(g1, a)})")
    elif it.get("fill"):
        st.append(f"background:{rgba(it['fill'], a)}")
    if it.get("pattern"):
        _, hz, ink, t = it["pattern"]
        s = max(2.0, t / 2)
        st.append(f"background:repeating-linear-gradient(45deg,{hz} 0 {px(s)},{ink} {px(s)} {px(2 * s)})")
    rad = it.get("radius")
    if rad == "circle":
        st.append("border-radius:50%")
    elif rad:
        st.append(f"border-radius:{px(rad)}")
    if it.get("stroke") and it["stroke"][0]:
        st.append(f"box-shadow:inset 0 0 0 {px(it['stroke'][1])} {it['stroke'][0]}")
    if it.get("rot"):
        st.append(f"transform:rotate({it['rot']}deg)")
    if it.get("group_alpha") is not None and it["group_alpha"] < 0.999:
        st.append(f"opacity:{it['group_alpha']:.3f}")
    attrs, inner = f' data-id="{html.escape(it["id"])}"', ""
    if it["type"] == "text":
        ta = {"left": "left", "center": "center", "right": "right"}[it.get("align", "left")]
        st += [f"font-family:'{it['font']}'", f"font-weight:{400 if it['fam'] == 'display' else it['weight']}",
               f"font-size:{px(it['size'])}", f"color:{it['color'] or '#000'}", f"text-align:{ta}"]
        if it.get("wrap"):
            st += ["display:flex", "flex-direction:column", "justify-content:center", f"line-height:{px(it['line'])}"]
        else:
            st += [f"line-height:{px(h)}", "white-space:nowrap"]
        if it.get("truncate"):
            st += ["overflow:hidden", "text-overflow:ellipsis"]
        attrs += f' data-t="1" data-trunc="{1 if it.get("truncate") else 0}"'
        inner = html.escape(it.get("text", ""))
    elif it["type"] == "image":
        name = it.get("image", "")
        tint = it.get("tint") or "#15171C"
        if name.startswith("icon.") and name[5:] in icons:
            src = icons[name[5:]]
            inner = (f'<img src="{src}" style="width:100%;height:100%">' if src.startswith("data:")
                     else src.replace("<svg ", '<svg width="100%" height="100%" ', 1))
            st.append(f"color:{tint}")
        elif name.startswith("key."):
            letter = name[4:].replace("Button", "")[:2]
            inner = (f'<div style="width:100%;height:100%;border-radius:50%;background:#15171C;color:#FFFFFF;'
                     f'font:700 {px(h * 0.6)} Montserrat;line-height:{px(h)};text-align:center">{html.escape(letter)}</div>')
        else:
            st += ["outline:1px dashed #E23A2E", "outline-offset:-1px"]
            attrs += f' data-missing="{html.escape(name)}"'
    kids = "".join(node_html(c, x, y, icons, kit, skin) for c in it.get("children", []))
    if it.get("clip") and kids:
        kids = f'<div class="n" style="left:0;top:0;width:{px(w)};height:{px(h)};overflow:hidden">{kids}</div>'
    if it.get("focus"):
        f = kit.roles["focus"]
        k = it["k"]
        pad, o, i_ = f["pad"] * k, f["outer"] * k, f["inner"] * k
        r = f"border-radius:{px(12 * k + f['radius_add'] * k)}"
        kids += (f'<div class="n" style="left:{px(-pad)};top:{px(-pad)};width:{px(w + 2 * pad)};height:{px(h + 2 * pad)};{r};'
                 f'box-shadow:inset 0 0 0 {px(o)} {kit.color(skin, "focus")},inset 0 0 0 {px(o + i_)} {kit.color(skin, "ink")}"></div>')
    return f'<div class="n"{attrs} style="{";".join(st)}">{inner}{kids}</div>'


def plate_html(kit, dev):
    W, H = dev.screen
    P = kit.roles["plate"]
    c = {k: (kit.b.value(v) or "#888888") for k, v in P.items() if k != "about"}
    poles = "".join(f'<div class="n" style="left:{px(W * f)};top:{px(H * 0.28)};width:{px(H * 0.025)};height:{px(H * 0.36)};background:{c["pole"]}"></div>'
                    for f in (0.12, 0.47, 0.82))
    return (f'<div class="n" style="left:0;top:0;width:{px(W)};height:{px(H)};background:{c["sky"]}"></div>'
            f'<div class="n" style="left:0;top:{px(H * 0.6)};width:{px(W)};height:{px(H * 0.4)};background:{c["ground"]}"></div>'
            f'<div class="n" style="left:0;top:{px(H * 0.72)};width:{px(W)};height:{px(H * 0.1)};background:{c["ballast"]}"></div>'
            f'<div class="n" style="left:0;top:{px(H * 0.74)};width:{px(W)};height:{px(3)};background:{c["rail"]}"></div>'
            f'<div class="n" style="left:0;top:{px(H * 0.79)};width:{px(W)};height:{px(3)};background:{c["rail"]}"></div>'
            + poles +
            f'<div class="n" style="left:0;top:0;width:{px(W * 0.035)};height:{px(H)};background:{c["cab"]}"></div>')


def furniture_html(kit, dev, zones_board):
    """Roblox screen furniture: top bar buttons, and on touch devices the jump button and thumbstick ring."""
    W, H = dev.screen
    ax, ay, aw, ah = dev.area("CoreUISafeInsets")
    out = []
    t = ay
    if t > 0:
        sz = min(44.0, t - 12)
        for i in range(2):
            out.append(f'<div class="n" style="left:{px(ax + 12 + i * (sz + 8))};top:{px((t - sz) / 2)};width:{px(sz)};height:{px(sz)};'
                       f'border-radius:{px(sz / 2)};background:rgba(21,23,28,.55)"></div>')
    z = kit.zones_for(dev)
    for name in ("jump", "stick"):
        if name in z:
            x, y, w, h = z[name]
            d = min(w, h) * 0.55
            cx, cy = x + w / 2, y + h / 2
            out.append(f'<div class="n" style="left:{px(cx - d / 2)};top:{px(cy - d / 2)};width:{px(d)};height:{px(d)};border-radius:50%;'
                       f'background:rgba(255,255,255,.28);box-shadow:inset 0 0 0 2px rgba(21,23,28,.35)"></div>')
    if zones_board:
        def hatch(x, y, w, h, col, label):
            return (f'<div class="n" style="left:{px(x)};top:{px(y)};width:{px(w)};height:{px(h)};'
                    f'background:repeating-linear-gradient(45deg,{col} 0 3px,transparent 3px 9px);box-shadow:inset 0 0 0 2px {col};'
                    f'font:700 11px Montserrat;color:#15171C;padding:2px 4px;box-sizing:border-box">{label}</div>')
        if ay > 0:
            out.append(hatch(0, 0, W, ay, "rgba(226,58,46,.55)", f"top bar {ay:g} px"))
        if ax > 0:
            out.append(hatch(0, ay, ax, ah, "rgba(226,58,46,.45)", ""))
            out.append(hatch(ax + aw, ay, W - ax - aw, ah, "rgba(226,58,46,.45)", ""))
        if ay + ah < H:
            out.append(hatch(0, ay + ah, W, H - ay - ah, "rgba(226,58,46,.45)", ""))
        for name, col in (("jump", "rgba(242,194,48,.8)"), ("stick", "rgba(242,194,48,.8)")):
            if name in z:
                out.append(hatch(*z[name], col, f"{name} {z['_size']}"))
        if "stick_area" in z:
            x, y, w, h = z["stick_area"]
            out.append(f'<div class="n" style="left:{px(x)};top:{px(y)};width:{px(w)};height:{px(h)};border:2px dashed rgba(21,23,28,.6);box-sizing:border-box"></div>')
        out.append(f'<div class="n" style="left:{px(ax)};top:{px(ay)};width:{px(aw)};height:{px(ah)};border:1px solid rgba(47,143,134,.9);box-sizing:border-box"></div>')
    return "".join(out)


def board_html(scene, screen, kit, fonts, icons, zones_board=False):
    dev = scene["device"]
    W, H = dev.screen
    body = [plate_html(kit, dev), furniture_html(kit, dev, False)]
    for layer in ("backdrop", "core"):
        for it in scene["layers"].get(layer, []):
            body.append(node_html(it, 0, 0, icons, kit, scene["skin"]))
    if zones_board:
        body.append(furniture_html(kit, dev, True))
    return ("<!doctype html><html><head><meta charset='utf-8'><style>" + fonts +
            "html,body{margin:0;padding:0}.n{position:absolute;box-sizing:border-box}"
            f"#s{{position:relative;width:{W:g}px;height:{H:g}px;overflow:hidden}}</style></head>"
            f"<body><div id='s'>{''.join(body)}</div></body></html>")


MEASURE_JS = r"""() => {
  const out = {overflow: [], missing: [], fonts: {}};
  for (const el of document.querySelectorAll('[data-t]')) {
    if (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 2)
      out.overflow.push({id: el.dataset.id, need: el.scrollWidth, have: el.clientWidth, truncated: el.dataset.trunc === '1'});
  }
  for (const el of document.querySelectorAll('[data-missing]')) out.missing.push(el.dataset.missing);
  return out;
}"""


def launch(pw):
    try:
        return pw.chromium.launch()
    except Exception:
        for exe in (os.environ.get("CHROMIUM_PATH"), "/opt/pw-browsers/chromium", shutil.which("chromium"),
                    shutil.which("chromium-browser"), shutil.which("google-chrome")):
            if exe and os.path.exists(exe) and os.path.isfile(exe):
                return pw.chromium.launch(executable_path=exe)
        for exe in sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome")):
            return pw.chromium.launch(executable_path=str(exe))
        raise


def find_critic():
    return U.find_sibling("multiuse-critic", "RR_CRITIC_SKILL")


# ------------------------------------------------------------------ render
def cmd_render(kit, a):
    sc = load(kit, a.spec)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    boards = [b for b in sc.boards if not a.boards or b.get("name") in a.boards.split(",")]
    if not boards:
        sys.exit("no boards match --boards")
    devs = [d for d in (a.devices.split(",") if a.devices else list(kit.devices)) if d]
    skins = [s for s in (a.skins.split(",") if a.skins else kit.skins) if s]
    for d in devs:
        if d not in kit.devices:
            sys.exit(f"unknown device {d} (have {', '.join(kit.devices)})")
    phone = kit.design_device.name
    main, dskin = boards[0], kit.default_skin if kit.default_skin in skins else skins[0]
    jobs = [(b, phone, dskin, False) for b in boards]
    jobs += [(main, d, dskin, False) for d in devs if d != phone]
    jobs += [(main, phone, s, False) for s in skins if s != dskin]
    jobs.append((main, phone, dskin, True))
    fonts, missing_fonts = fonts_css(kit)
    icons = load_icons(sc)
    files = []
    for b, d, s, z in jobs:
        scene = U.resolve(sc, kit.devices[d], s, b, text_scale=a.text_scale)
        name = f"{sc.name}__{b.get('name', 'board')}__{d}__{s}{'__zones' if z else ''}"
        (out / f"{name}.html").write_text(board_html(scene, sc, kit, fonts, icons, z), encoding="utf-8")
        files.append({"name": name, "board": b.get("name"), "device": d, "skin": s, "zones": z,
                      "size": kit.devices[d].screen, "stack": scene.get("stack", {}).get("hidden")})
    measures = {}
    if not a.html_only:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("Playwright missing: wrote HTML only (pip install playwright; see SKILL.md limits)")
            a.html_only = True
    if not a.html_only:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            br = launch(pw)
            for f in files:
                W, H = f["size"]
                ctx = br.new_context(viewport={"width": int(W), "height": int(H)}, device_scale_factor=1)
                page = ctx.new_page()
                page.set_content((out / f"{f['name']}.html").read_text(encoding="utf-8"), wait_until="load")
                page.evaluate("() => document.fonts.ready.then(() => true)")
                page.screenshot(path=str(out / f"{f['name']}.png"), clip={"x": 0, "y": 0, "width": W, "height": H})
                measures[f["name"]] = page.evaluate(MEASURE_JS)
                ctx.close()
            br.close()
    E, W_, I, F = U.check(sc, [kit.devices[d] for d in devs], skins)
    facts = facts_md(sc, kit, F, E, W_, I, files, measures, missing_fonts, a.text_scale)
    (out / "facts.md").write_text(facts, encoding="utf-8")
    (out / "render.json").write_text(json.dumps({"spec": str(sc.path), "files": files, "measures": measures},
                                                indent=1, default=str), encoding="utf-8")
    sheet_msg = "" if a.html_only else contact_sheets(out, files, phone, dskin)
    print(f"{sc.name}: {len(files)} boards -> {out}" + (" (HTML only)" if a.html_only else "") + sheet_msg)
    over = [(n, m) for n, ms in measures.items() for m in ms["overflow"] if not m["truncated"]]
    print(f"  checks: {len(E)} errors, {len(W_)} warnings; text overflow {len(over)}; fonts missing {missing_fonts or 'none'}")
    return 1 if E else 0


def contact_sheets(out, files, phone, dskin):
    critic = find_critic()
    if not critic:
        return "; multiuse-critic not found: no contact sheet"
    cs = critic / "scripts" / "contact_sheet.py"
    main = [f for f in files if f["device"] == phone and f["skin"] == dskin and not f["zones"]]
    band = [f"Phone {int(files[0]['size'][0])}x{int(files[0]['size'][1])} {main[0]['board']} ({dskin})={out / (main[0]['name'] + '.png')}@1"]
    grid = [f"{f['board']} phone={out / (f['name'] + '.png')}" for f in main[1:]]
    grid += [f"{f['board']} {f['device']}={out / (f['name'] + '.png')}" for f in files if f["device"] != phone]
    close = [f"zones {f['device']}={out / (f['name'] + '.png')}" for f in files if f["zones"]]
    close += [f"skin {f['skin']} {f['board']}={out / (f['name'] + '.png')}" for f in files
              if f["skin"] != dskin and not f["zones"]]
    msgs = []
    for target, items, tile in (("contact.png", band + grid, "400x225"), ("closeups.png", close, "560x260")):
        if not items:
            continue
        r = subprocess.run([sys.executable, str(cs), str(out / target), *items, "--tile", tile], capture_output=True, text=True)
        msgs.append(f"{target}{' (' + r.stdout.strip().splitlines()[-1] + ')' if r.stdout.strip() else ''}"
                    + ("" if r.returncode == 0 else f" exit {r.returncode}: {r.stderr.strip()[-200:]}"))
    return "; " + "; ".join(msgs)


def facts_md(sc, kit, F, E, W, I, files, measures, missing_fonts, text_scale):
    L = [f"# Facts: {sc.name} (measured by rr-ui-foundry; render = model + Chromium, not Roblox)", ""]
    L.append(f"- Design space: {kit.design_device.name} screen {kit.design_device.screen[0]:g}x{kit.design_device.screen[1]:g}, "
             f"ScreenGui {sc.insets} area {'x'.join(f'{v:g}' for v in kit.design_device.area(sc.insets)[2:])} px (top bar "
             f"{kit.design_device.insets.get('top', 0):g} px, tech.ui_platform.topbar_inset).")
    L.append(f"- Layout: pin + scale (Scale sizes + UIAspectRatioConstraint, pinned margins x the same scale); UIScale density "
             + ", ".join(f"{k} {v:g}" for k, v in kit.density.items()) + " (tech.ui_platform.layout; Large = OQ-033 default).")
    L.append(f"- Skin on the main boards: {kit.default_skin} = assumed ({kit.roles['skin_oq']} default); other skins on closeups.")
    if text_scale != 1.0:
        L.append(f"- Text stress: every text x{text_scale:g} (a stand-in for GuiService.PreferredTextSize, not its exact factor).")
    L.append("")
    L.append("| device | px per design px | smallest text | smallest target | touch zones | stack |")
    L.append("|---|---|---|---|---|---|")
    for d, v in F["devices"].items():
        k = ", ".join(f"{x:.3f}" for x in (v["k"] or {}).values())
        L.append(f"| {d} | {k} | {fmt_min(v['min_text'])} | {fmt_min(v['min_target'])} | {v['zones'].get('size', '-') if v['zones'] else '-'} | "
                 f"{'; '.join(f'{b}: {s}' for b, s in (v.get('stack') or {}).items()) or '-'} |")
    L.append("")
    L.append("- Lowest text contrast per skin (WCAG, text vs the fill it sits on): " +
             "; ".join(f"{s} {v[0]}:1 ({v[1]})" for s, v in F["contrast"].items() if v))
    L.append(f"- Minimum text (ui.rules.min_text): display {kit.min_text['display']:g} px, body {kit.min_text['body']:g} px on "
             f"{kit.design_device.name}; touch target {kit.touch_target:g} px (tech.ui_platform.touch_target_px).")
    over = sorted({(m["id"], m["truncated"]) for ms in measures.values() for m in ms["overflow"]})
    if measures:
        L.append("- Text wider than its box (Chromium): " + (", ".join(f"{i}{' (truncates)' if t else ''}" for i, t in over) or "none"))
        miss = sorted({x for ms in measures.values() for x in ms["missing"]})
        L.append("- Image placeholders on boards: " + (", ".join(miss) or "none"))
    L.append(f"- Fonts on boards: {', '.join(f['name'] for f in kit.fonts.values())}"
             + (f"; NOT loaded: {', '.join(missing_fonts)}" if missing_fonts else " (embedded woff2)"))
    L.append(f"- Checks: {len(E)} errors, {len(W)} warnings.")
    for e in E:
        L.append(f"  - E {e}")
    for w in W[:20]:
        L.append(f"  - W {w}")
    for i in I[:12]:
        L.append(f"  - i {i}")
    L.append("")
    L.append("Boards: " + ", ".join(f"{f['name']}.png" for f in files))
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ crit hand-off
def cmd_crit(kit, a):
    critic = find_critic()
    if not critic:
        print("multiuse-critic not found: set RR_CRITIC_SKILL")
        return 2
    sc = load(kit, a.spec)
    C, src = Path(a.crit), Path(getattr(a, "from"))
    pdir = C / f"pass-{a.pass_}"
    pdir.mkdir(parents=True, exist_ok=True)
    got = []
    for f in ("contact.png", "contact.json", "closeups.png", "closeups.json", "facts.md"):
        if (src / f).is_file():
            shutil.copy2(src / f, pdir / f)
            got.append(f)
    if "contact.png" not in got:
        print(f"no contact.png in {src}: run ui.py render first")
        return 1
    if not (C / "brief.md").is_file():
        (C / "brief.md").write_text(brief_md(sc, kit), encoding="utf-8")
        got.append("brief.md (new)")
    img = " --images closeups.png" if "closeups.png" in got else ""
    print(f"wrote {pdir}: {', '.join(got)}")
    print(f"next: python3 {critic / 'scripts' / 'critic_kit.py'} build {C} --pass {a.pass_} --kind full --profile B "
          f"--role \"senior UI designer\"{img}")
    print("then spawn a fresh critic on the printed prompt (multiuse-critic step 5); never score it yourself")
    return 0


def brief_md(sc, kit):
    aud = "; ".join(v for v in (kit.b.value("identity.audience.launch"), kit.b.value("identity.audience.target"),
                                  kit.b.value("identity.audience.devices")) if v) or "see rr-bible identity.audience"
    modal = "a modal panel over the game" if sc.gui.get("modal") else "a screen overlay over the running game (HUD)"
    oqs = []
    for oid in sc.raw.get("oq", []):
        q = kit.b.oq(oid)
        if q:
            oqs.append(f"{oid} {q['title']} (default in use: {q['fields'].get('default', '?')})")
    return "\n".join([
        f"# {sc.raw.get('title', sc.name)}",
        f"Purpose: {sc.raw.get('purpose', 'see spec')}",
        f"Audience: {aud}",
        f"Player view: {modal}; phone landscape {kit.design_device.screen[0]:g}x{kit.design_device.screen[1]:g} at true size "
        f"(ScreenGui {sc.insets}, top bar {kit.design_device.insets.get('top', 0):g} px); PC/tablet/console boards are scaled "
        "by the kit's pin + scale rule. Grey pills and circles are Roblox's own top bar, jump button and thumbstick.",
        "Stage: draft (generated from the spec by rr-ui-foundry; the same numbers build the Roblox package).",
        f"Fixed constraints: rr-bible tokens only (skin {kit.default_skin} = assumed, {kit.roles['skin_oq']} default); fonts "
        f"{', '.join(f['name'] for f in kit.fonts.values())}; text >= {kit.min_text['body']:g}/{kit.min_text['display']:g} px, "
        f"targets >= {kit.touch_target:g} px; clear of top bar, jump and thumbstick; exact game strings from canon.",
        "Already decided / open: " + ("; ".join(oqs) if oqs else "none"),
        "step 2: pre-answered (canon via rr-bible; owner away)",
    ]) + "\n"


# ------------------------------------------------------------------ icon sheet
def cmd_sheet(kit, a):
    src = Path(a.icondir or SKILL / "assets" / "icons")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    return make_sheet(src, out, a.cell)


def make_sheet(src, out, cell=64, scale=2):
    icons = sorted(list(src.glob("*.svg")) + list(src.glob("*.png")))
    if not icons:
        print(f"no icons in {src}")
        return 1
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright missing: no icon sheet (install playwright)")
        return 2
    cols = min(8, len(icons))
    rows = -(-len(icons) // cols)
    c = cell * scale
    cells, meta = [], {}
    for i, f in enumerate(icons):
        x, y = (i % cols) * c, (i // cols) * c
        if f.suffix == ".svg":
            body = f.read_text(encoding="utf-8").replace("<svg ", f'<svg width="{c - 8}" height="{c - 8}" ', 1)
        else:
            body = f'<img src="data:image/png;base64,{base64.b64encode(f.read_bytes()).decode()}" width="{c - 8}" height="{c - 8}">'
        cells.append(f'<div style="position:absolute;left:{x + 4}px;top:{y + 4}px;color:#FFFFFF">{body}</div>')
        meta[f.stem] = {"offset": [x, y], "size": [c, c]}
    page_html = (f"<!doctype html><html><body style='margin:0;background:transparent'>"
                 f"<div style='position:relative;width:{cols * c}px;height:{rows * c}px'>{''.join(cells)}</div></body></html>")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = launch(pw)
        ctx = br.new_context(viewport={"width": cols * c, "height": rows * c})
        pg = ctx.new_page()
        pg.set_content(page_html)
        pg.screenshot(path=str(out / "rr_ui_icons.png"), omit_background=True, clip={"x": 0, "y": 0, "width": cols * c, "height": rows * c})
        br.close()
    (out / "icons.json").write_text(json.dumps({"sheet": "rr_ui_icons.png", "cell": c, "tint": "white icons: ImageColor3 tints them",
                                                "icons": meta}, indent=1), encoding="utf-8")
    print(f"sheet: {len(icons)} icons, {cols}x{rows} cells of {c}px -> {out / 'rr_ui_icons.png'}")
    return 0


def make_hazard_tile(kit, skin, out, size=32):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    hz, ink = U.hex_rgb(kit.color(skin, "hazard")), U.hex_rgb(kit.color(skin, "hazard_ink"))
    im = Image.new("RGB", (size, size), hz)
    d = ImageDraw.Draw(im)
    for k in range(-2, 4):
        o = k * size // 2
        d.polygon([(o, size), (o + size // 4, size), (o + size // 4 + size, 0), (o + size, 0)], fill=ink)
    p = out / "rr_hazard_tile.png"
    im.save(p)
    return p


# ------------------------------------------------------------------ build (Luau package)
def theme_lua(kit, skin, icons_meta, ids=None):
    L = ["-- RR_UITheme (ModuleScript) - GENERATED by rr-ui-foundry from rr-bible canon. Do not edit:",
         "-- change canon (bible.py) or kit/roles.json and run ui.py build again.",
         f"-- Skins are the options of {kit.roles['skin_oq']}; {skin} is active"
         + (" (assumed: the open question's default)." if skin == kit.default_skin else "."), ""]
    T = {"generated": datetime.date.today().isoformat(), "skin": skin, "skinNote": kit.roles["skins"].get(skin, ""),
         "skins": {}, "sources": {}}
    for s in kit.skins:
        T["skins"][s] = {r: U.raw(f'Color3.fromHex("{c["hex"].lstrip("#")}")') for r, c in kit.colors[s].items()}
        T["sources"][s] = {r: c["key"] for r, c in kit.colors[s].items()}
    T["fonts"] = {k: dict(v["roblox"], name=v["name"]) for k, v in kit.fonts.items()}
    for v in T["fonts"].values():
        v.pop("guess", None)
    T["type"] = {k: {"font": t["font"], "weight": U.WEIGHTS.get(t["weight"], "Regular"), "size": t["size"]} for k, t in kit.types.items()}
    T["density"] = kit.density
    dd = kit.design_device
    T["design"] = {m: dict(zip(("x", "y", "w", "h"), dd.area(m))) for m in U.INSET_MODES}
    T["zones"] = {"smallScreen": kit.zone["small_screen"], "jump": {k: list(kit.zone["jump"][k]) for k in ("small", "large")},
                  "stick": {k: list(kit.zone["stick"][k]) for k in ("small", "large")}}
    T["focus"] = {"pad": kit.roles["focus"]["pad"], "outer": kit.roles["focus"]["outer"], "inner": kit.roles["focus"]["inner"],
                  "radiusAdd": kit.roles["focus"]["radius_add"]}
    ids = ids or {}
    T["assets"] = {"iconSheet": ids.get("iconSheet", "rbxassetid://0"),
                   "icons": {k: {"offset": v["offset"], "size": v["size"]} for k, v in (icons_meta or {}).items()},
                   "hazardTile": ids.get("hazardTile", "rbxassetid://0"), "hazardTilePx": 16}
    return "\n".join(L) + "\nreturn " + U.lua(T) + "\n"


def templates_lua(kit):
    errs = []
    T = {name: U.expand_runtime(kit, name, errs) for name, t in kit.comps.items() if t.get("runtime")}
    return ("-- RR_UITemplates (ModuleScript) - GENERATED by rr-ui-foundry from kit/components.json (runtime templates).\n"
            "-- Rects are design px; {slot} strings and if/unless are filled by RR_UIKit when an instance is created.\n"
            "return " + U.lua(T) + "\n"), errs


def screen_lua(sc):
    D = {"name": sc.name, "title": sc.raw.get("title", ""), "insets": sc.insets,
         "displayOrder": sc.gui.get("display_order", 10), "modal": bool(sc.gui.get("modal")),
         "data": {k: {"values": v["values"], "default": v["default"]} for k, v in sc.data.items()},
         "nodes": sc.nodes, "types": sc.types,
         "nav": {"edges": sc.nav["edges"], "default": sc.nav.get("default"), "back": sc.nav.get("back"), "modal": sc.nav.get("modal")},
         "machine": sc.machine, "boards": sc.boards}
    return (f"-- {sc.name} (ModuleScript) - GENERATED by rr-ui-foundry from {sc.path.name}. Do not edit: change the spec\n"
            "-- and run ui.py build. Rects are design px of the phone board; RR_UIKit turns them into Scale + pins.\n"
            "return " + U.lua(D, strip=("_parent", "note", "canon")) + "\n")


def luaparse_check(files):
    lp = TOOLS / "node_modules" / "luaparse"
    if not shutil.which("node"):
        return "SKIP", "node missing"
    if not lp.is_dir():
        subprocess.run(["npm", "i", "--prefix", str(TOOLS), "luaparse", "--no-audit", "--no-fund", "--loglevel=error"],
                       capture_output=True, timeout=180)
    if not lp.is_dir():
        return "SKIP", "luaparse not installable (npm i --prefix ~/.cache/rr-tools luaparse)"
    js = ("const lp=require(process.argv[1]);const fs=require('fs');let bad=0;for(const f of process.argv.slice(2)){try{"
          "lp.parse(fs.readFileSync(f,'utf8'),{luaVersion:'5.1'});}catch(e){bad++;console.log(f+': '+e.message);}}process.exit(bad?1:0);")
    r = subprocess.run(["node", "-e", js, str(lp), *map(str, files)], capture_output=True, text=True)
    return ("PASS" if r.returncode == 0 else "FAIL"), (r.stdout + r.stderr).strip()


def cmd_build(kit, a):
    if kit.errors:
        for e in kit.errors:
            print(f"  E {e}")
        return 1
    screens = [load(kit, s) for s in a.specs]
    skin = a.skin or kit.default_skin
    if skin not in kit.skins:
        sys.exit(f"unknown skin {skin}")
    bad = 0
    if not a.no_check:
        for sc in screens:
            E, W, I, F = U.check(sc)
            print(f"  {'PASS' if not E else 'FAIL'} validate {sc.name}: {len(E)} errors, {len(W)} warnings")
            for e in E:
                print(f"    E {e}")
            bad += bool(E)
        if bad:
            print("build stopped: fix the errors (or --no-check for a draft package)")
            return 1
    out = Path(a.out)
    lib = out / "src" / "shared" / "RR_UI"
    (lib / "screens").mkdir(parents=True, exist_ok=True)
    (out / "src" / "client").mkdir(parents=True, exist_ok=True)
    (out / "icons").mkdir(parents=True, exist_ok=True)
    icon_dirs = {sc.icons_dir for sc in screens if sc.icons_dir and sc.icons_dir.is_dir()}
    icons_meta = {}
    for d in icon_dirs:
        if make_sheet(d, out / "icons") == 0:
            icons_meta.update(json.loads((out / "icons" / "icons.json").read_text())["icons"])
    tile = make_hazard_tile(kit, skin, out / "icons")
    ids_file = Path(a.assets) if a.assets else out / "asset_ids.json"
    ids = json.loads(ids_file.read_text(encoding="utf-8")) if ids_file.is_file() else {}
    if ids:
        print(f"  asset ids from {ids_file}: {', '.join(sorted(ids))}")
    (lib / "RR_UITheme.lua").write_text(theme_lua(kit, skin, icons_meta, ids), encoding="utf-8")
    tl, errs = templates_lua(kit)
    for e in errs:
        print(f"  E template {e}")
    (lib / "RR_UITemplates.lua").write_text(tl, encoding="utf-8")
    for sc in screens:
        (lib / "screens" / f"{sc.name}.lua").write_text(screen_lua(sc), encoding="utf-8")
    shutil.copy2(SKILL / "assets" / "luau" / "RR_UIKit.lua", lib / "RR_UIKit.lua")
    shutil.copy2(SKILL / "assets" / "luau" / "RR_UIDemo.client.lua", out / "src" / "client" / "RR_UIDemo.client.lua")
    (out / "default.project.json").write_text(json.dumps({"name": "RR_UI", "tree": {"$className": "DataModel",
        "ReplicatedStorage": {"RR_UI": {"$path": "src/shared/RR_UI"}},
        "StarterPlayer": {"StarterPlayerScripts": {"RR_UIDemo": {"$path": "src/client/RR_UIDemo.client.lua"}}}}}, indent=2),
        encoding="utf-8")
    (out / "ASSETS.md").write_text(assets_md(icons_meta, tile), encoding="utf-8")
    (out / "UI_SPEC.md").write_text(ui_spec_md(kit, screens, skin), encoding="utf-8")
    (out / "README.md").write_text(readme_md(screens), encoding="utf-8")
    luas = sorted(out.rglob("*.lua"))
    gates = {}
    st, msg = luaparse_check(luas)
    gates["luaparse"] = st
    print(f"  {st} luaparse ({len(luas)} files){': ' + msg if st != 'PASS' and msg else ''}")
    b = kit.b
    fails = []
    for f in luas + [out / "UI_SPEC.md"]:
        code, txt = b.run("check", str(f))
        if code != 0:
            fails.append(f"{f.name}: {txt.strip()[:400]}")
    gates["bible_check"] = "PASS" if not fails else "FAIL"
    print(f"  {gates['bible_check']} bible check ({len(luas) + 1} files)" + ("".join(f"\n    {x}" for x in fails)))
    if not a.no_parity:
        r = subprocess.run([sys.executable, str(HERE / "luatest.py"), "--package", str(out),
                            "--specs", ",".join(str(sc.path) for sc in screens)], capture_output=True, text=True)
        tail = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
        gates["parity"] = "PASS" if r.returncode == 0 else ("SKIP" if r.returncode == 3 else "FAIL")
        print(f"  {gates['parity']} luatest parity: {tail}")
        if r.returncode not in (0, 3):
            print(r.stdout[-1500:])
    man = {"generated": datetime.datetime.now().isoformat(timespec="seconds"), "skin": skin,
           "skin_status": f"assumed ({kit.roles['skin_oq']} default)" if skin == kit.default_skin else "chosen",
           "screens": {sc.name: hashlib.sha1(sc.path.read_bytes()).hexdigest()[:12] for sc in screens},
           "kit": {f: hashlib.sha1((kit.dir / f).read_bytes()).hexdigest()[:12] for f in ("roles.json", "components.json")},
           "canon_cited": sorted(kit.cites), "gates": gates, "density": kit.density,
           "studio": "Studio test pending (owner); nothing here was published or uploaded"}
    (out / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    ok = all(v in ("PASS", "SKIP") for v in gates.values()) and not errs
    print(f"{'BUILD PASS' if ok else 'BUILD FAIL'}: {out}  (Studio test pending (owner))")
    return 0 if ok else 1


def assets_md(icons_meta, tile):
    L = ["# Assets to upload (owner)", "",
         "Nothing was uploaded. Upload each image in Studio (Asset Manager > Import, or Creator Hub), then write the ids",
         "into `asset_ids.json` in this folder, e.g. {\"iconSheet\": \"rbxassetid://123\", \"hazardTile\": \"rbxassetid://456\"},",
         "and run ui.py build again (or pass --assets FILE); the ids then survive every rebuild.", "",
         "| file | key in asset_ids.json | notes |", "|---|---|---|"]
    if icons_meta:
        L.append(f"| icons/rr_ui_icons.png | `assets.iconSheet` | {len(icons_meta)} white icons; icons.json has each "
                 "ImageRectOffset/Size (already in the theme); ImageColor3 tints them |")
    if tile:
        L.append("| icons/rr_hazard_tile.png | `assets.hazardTile` | 32 px hazard stripe tile, ScaleType Tile at 16 px |")
    L += ["", "Until an id is set the kit shows the icon's fallback (blank medallion) and the risk stub without stripes;",
          "gamepad glyphs come from UserInputService:GetImageForKeyCode at run time (no upload)."]
    return "\n".join(L) + "\n"


def ui_spec_md(kit, screens, skin):
    L = ["# UI spec (generated by rr-ui-foundry)", "",
         f"Skin {skin} ({kit.roles['skins'].get(skin, '')}); density by GuiService.ViewportDisplaySize: "
         + ", ".join(f"{k} {v:g}" for k, v in kit.density.items()) + ".", ""]
    for sc in screens:
        E, W, I, F = U.check(sc)
        L += [f"## {sc.name}: {sc.raw.get('title', '')}", "", f"Purpose: {sc.raw.get('purpose', '-')}",
              f"ScreenGui: ScreenInsets {sc.insets}, SafeAreaCompatibility None, DisplayOrder {sc.gui.get('display_order', 10)}"
              + (", modal (SelectionGroup, ButtonB = back)" if sc.gui.get("modal") else ""), ""]
        if sc.machine:
            L.append("States: " + ", ".join(sc.machine["states"]) + f" (initial {sc.machine['initial']})")
            L += [f"- {t['from']} --{t['event']}--> {t['to']}" + (f" (feel: {t['feel']})" if t["feel"] else "") for t in sc.machine["transitions"]]
            L.append("")
        if sc.nav["edges"]:
            L.append(f"Gamepad: default {sc.nav.get('default')}, back {sc.nav.get('back')}; rows " +
                     " / ".join(", ".join(r) for r in sc.nav["rows"]))
            L.append("")
        L.append("| device | px per design px | smallest text | smallest target |")
        L.append("|---|---|---|---|")
        for d, v in F["devices"].items():
            L.append(f"| {d} | {', '.join(f'{x:.3f}' for x in (v['k'] or {}).values())} | {fmt_min(v['min_text'])} | {fmt_min(v['min_target'])} |")
        L.append("")
        if W:
            L.append("Warnings: " + "; ".join(W[:8]))
            L.append("")
    return "\n".join(L) + "\n"


def readme_md(screens):
    names = ", ".join(sc.name for sc in screens)
    return f"""# RR_UI package (rr-ui-foundry)

Screens: {names}. Generated; rebuild with `ui.py build` instead of editing generated files.

## Install
- Rojo: `rojo serve` with default.project.json (RR_UI lands in ReplicatedStorage, the demo in StarterPlayerScripts).
- By hand: make a Folder `RR_UI` in ReplicatedStorage with ModuleScripts RR_UIKit, RR_UITheme, RR_UITemplates and a
  Folder `screens` holding one ModuleScript per screen; put RR_UIDemo in StarterPlayerScripts as a LocalScript.
- Optional: put rr-game-feel's RR_Feel, RR_FeelPresets and RR_FeelMath in the same RR_UI folder; the kit then plays
  its events (reduce motion included). Without it the kit only fades, and snaps when Reduce Motion is on.

## Use (LocalScript)
```lua
local UI = require(game.ReplicatedStorage.RR_UI.RR_UIKit)
local hud = UI.mount(require(game.ReplicatedStorage.RR_UI.screens.HudTickets))
hud:push("CoalLow")                 -- tickets: type name + slots, e.g. hud:push("CrewJoined", {{name = "Sam"}})
hud:clear("CoalLow")                -- the server's clear alert (ID)
local lobby = UI.mount(require(game.ReplicatedStorage.RR_UI.screens.LobbyCreateMatch))
lobby:send("open")                  -- state machine events; lobby.Action.Event fires (name, data) for game code
UI.setSkin("A")                     -- live reskin of every mounted screen
```

## Studio test (owner; nothing here has run in Roblox)
1. Play Solo with the demo: each screen cycles its boards; compare with the boards in the render folder.
2. Device emulator: iPhone 14 landscape, an iPad and 1920x1080; check the HUD clears the jump button and top bar.
3. Gamepad (or the emulator's controller): Select starts navigation on the lobby; ButtonB closes it.
4. Settings > Reduce Motion on: panels and tickets fade instead of sliding.
5. Upload the images in ASSETS.md and paste the ids.
"""


# ------------------------------------------------------------------ ingest (HTML mock -> draft spec)
INGEST_JS = r"""(sel) => {
  const all = [...document.querySelectorAll(sel)].filter(el => {
    const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width >= 4 && r.height >= 4 && cs.visibility !== 'hidden' && cs.display !== 'none' && parseFloat(cs.opacity) > 0.05; });
  const rgba = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(',').map(x => parseFloat(x));
    return {hex: '#' + p.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase(), a: p.length > 3 ? p[3] : 1}; };
  const own = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join(' ').replace(/\s+/g, ' ').trim();
  return all.map((el, i) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    const bg = rgba(cs.backgroundColor), bc = rgba(cs.borderTopColor);
    const grad = (cs.backgroundImage.match(/rgba?\([^)]+\)/g) || []).map(c => rgba(c)).filter(Boolean);
    let p = el.parentElement; let parent = -1; while (p) { const j = all.indexOf(p); if (j >= 0) { parent = j; break; } p = p.parentElement; }
    return {i, parent, rr: el.getAttribute('data-rr') || '', variant: el.getAttribute('data-rr-variant') || '',
      tag: el.tagName.toLowerCase(), x: r.left, y: r.top, w: r.width, h: r.height,
      bg: bg && bg.a > 0.02 ? bg : null, grad, border: parseFloat(cs.borderTopWidth) > 0 && bc ? {hex: bc.hex, w: parseFloat(cs.borderTopWidth)} : null,
      radius: parseFloat(cs.borderTopLeftRadius) || 0, color: rgba(cs.color), text: own(el), fs: parseFloat(cs.fontSize),
      fw: parseInt(cs.fontWeight) || 400, family: cs.fontFamily.split(',')[0].replace(/["']/g, '').trim(),
      button: el.matches('button, [role=button], a[href]'), align: cs.textAlign}; });
}"""


def cmd_ingest(kit, a):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ingest needs Playwright")
        return 2
    size = U.wh(a.size) or kit.design_device.screen
    W, H = int(size[0]), int(size[1])
    src = Path(a.html)
    with sync_playwright() as pw:
        br = launch(pw)
        ctx = br.new_context(viewport={"width": W, "height": H})
        page = ctx.new_page()
        if a.root:
            serve_root(page, Path(a.root))
            page.goto("http://dc.local/" + os.path.relpath(src.resolve(), Path(a.root).resolve()).replace(os.sep, "/"))
            try:
                page.wait_for_function("() => window.__dcRegistry !== undefined", timeout=15000)
            except Exception:
                pass
        else:
            page.goto(src.resolve().as_uri())
        page.wait_for_timeout(800)
        annotated = page.evaluate("() => document.querySelectorAll('[data-rr]').length")
        els = page.evaluate(INGEST_JS, "[data-rr]" if annotated else "body *")
        br.close()
    spec, notes = draft_spec(kit, els, W, H, a.name or src.stem, bool(annotated))
    spec["_ingest"] = {"source": str(src), "annotated": bool(annotated), "notes": notes}
    Path(a.out).write_text(json.dumps(spec, indent=1), encoding="utf-8")
    print(f"draft spec {a.out}: {len(els)} elements ({'data-rr' if annotated else 'heuristic, no data-rr hints'}), "
          f"{len(notes)} notes; next: edit it, then ui.py validate {a.out}")
    for n in notes[:15]:
        print(f"  - {n}")
    return 0


def serve_root(page, root):
    """Serve a Design canvas folder (Artifact read output) the way multiuse-critic's render_design.py does."""
    import mimetypes
    import urllib.parse

    def handler(route):
        u = urllib.parse.urlparse(route.request.url)
        if u.netloc != "dc.local":
            return route.abort()
        path = urllib.parse.unquote(u.path)
        f = root / "artifact-type" / "dc-runtime.js" if path.endswith("/support.js") else root / path.lstrip("/")
        if f.is_file():
            return route.fulfill(status=200, body=f.read_bytes(), content_type=mimetypes.guess_type(str(f))[0] or "application/octet-stream")
        return route.fulfill(status=404, body="")
    page.route("**/*", handler)


def draft_spec(kit, els, W, H, name, annotated):
    notes = []
    skin = kit.default_skin
    roles = {r: c["hex"] for r, c in kit.colors[skin].items()}
    special = ("kind.", "diff.", "on_diff.")

    def snap(hexv, what):
        if not hexv:
            return None
        if hexv.upper() in ("#000000", "#FFFFFF"):
            return "ink" if hexv.upper() == "#000000" else "paper_top"
        r, d = min(((r, U.delta_e(hexv, h)) for r, h in roles.items() if not r.startswith(special)), key=lambda x: x[1])
        if d > 2:
            sp = min(((r2, U.delta_e(hexv, h)) for r2, h in roles.items() if r2.startswith(special)), key=lambda x: x[1])
            if sp[1] <= 2:
                return sp[0]
        if d > 6:
            notes.append(f"{what}: {hexv} is off-palette (nearest role {r}, dE {d:.1f}); used {r}")
        return r

    def style_of(e):
        fam = "display" if kit.fonts["display"]["name"].lower() in e["family"].lower() else "body"
        cands = [(n, t) for n, t in kit.types.items() if t["font"] == fam] or list(kit.types.items())
        return min(cands, key=lambda x: abs(x[1]["size"] - e["fs"]))[0]
    canon_texts = {}
    b = kit.b
    for key in ("gameplay.alerts", "world.lexicon"):
        code, out = b.run("get", key, "--json")
        try:
            for f in json.loads(out) if code == 0 else []:
                for i, part in enumerate(str(f["value"]).split(" / ")):
                    canon_texts[part.strip()] = (f["key"], i)
        except ValueError:
            pass
    nodes = {}
    for e in els:
        rr = e["rr"] or ""
        kind, _, nid = rr.partition(":")
        nid = re.sub(r"[^A-Za-z0-9_]", "_", nid or f"{e['tag']}{e['i']}")
        n = {"id": nid}
        if kind in ("button", "chip", "panel", "ticket"):
            n["use"] = kind
            if kind == "button":
                n["variant"] = e["variant"] or ("primary" if e["bg"] and snap(e["bg"]["hex"], nid) == "accent" else "secondary")
            if e["text"]:
                n["slots"] = {"text" if kind != "panel" else "title": e["text"]}
        elif kind in U.TYPES:
            n["type"] = kind
        else:
            n["type"] = "text" if e["text"] and not e["bg"] else ("hit" if e["button"] else "frame")
        if "type" in n:
            if e["grad"] and len(e["grad"]) >= 2:
                n["gradient"] = [snap(e["grad"][0]["hex"], nid), snap(e["grad"][-1]["hex"], nid)]
            elif e["bg"]:
                n["fill"] = snap(e["bg"]["hex"], nid)
                if e["bg"]["a"] < 0.98:
                    n["alpha"] = round(e["bg"]["a"], 2)
            if e["border"]:
                n["stroke"] = [snap(e["border"]["hex"], nid), round(e["border"]["w"], 1)]
            if e["radius"]:
                n["radius"] = "circle" if e["radius"] >= min(e["w"], e["h"]) / 2 - 0.5 else round(e["radius"], 1)
            if e["text"]:
                if n["type"] == "frame":
                    n["type"] = "text"
                t = e["text"]
                if t in canon_texts:
                    k, i = canon_texts[t]
                    n["text"] = {"canon": k, "part": i}
                else:
                    n["text"] = t
                    notes.append(f"{nid}: literal text {t!r} (not in canon)")
                n["style"] = style_of(e)
                n["color"] = snap(e["color"]["hex"] if e["color"] else None, nid) or "ink"
                if e["align"] in ("center", "right"):
                    n["align"] = e["align"]
        n["_abs"] = (e["x"], e["y"], e["w"], e["h"])
        n["_parent"] = e["parent"]
        nodes[e["i"]] = n
    tops, dropped = [], set()
    for i in sorted(nodes):
        n = nodes[i]
        p = n.pop("_parent")
        ax_, ay_, aw_, ah_ = n.pop("_abs")
        n["_absr"] = (ax_, ay_)
        n["rect"] = [round(ax_, 1), round(ay_, 1), round(aw_, 1), round(ah_, 1)]
        if p in dropped or (p in nodes and nodes[p].get("use") in ("button", "chip", "ticket")):
            dropped.add(i)
            continue
        if p in nodes:
            px_, py_ = nodes[p]["_absr"]
            n["rect"][0], n["rect"][1] = round(ax_ - px_, 1), round(ay_ - py_, 1)
            nodes[p].setdefault("children", []).append(n)
        else:
            tops.append(n)
    for n in nodes.values():
        n.pop("_absr", None)
    for n in nodes.values():
        if n.get("use") == "panel":
            kids = n.get("children", [])
            head = next((c for c in kids if c.get("type") == "text" and c["rect"][1] < 50 and isinstance(c.get("text"), str)), None)
            if head:
                n.setdefault("slots", {})["title"] = head["text"]
                kids.remove(head)
                notes.append(f"{n['id']}: header text {head['text']!r} became the panel title")
    hits = []

    def collect(ns, ox, oy):
        for n in ns:
            x, y = ox + n["rect"][0], oy + n["rect"][1]
            if n.get("use") in ("button", "chip") or n.get("type") == "hit":
                hits.append((n["id"], x + n["rect"][2] / 2, y + n["rect"][3] / 2, n["rect"][3], n.get("variant")))
            collect(n.get("children", []), x, y)
    collect(tops, 0, 0)
    nav = {}
    if hits:
        rows = []
        for h in sorted(hits, key=lambda h: h[2]):
            if rows and abs(rows[-1][0][2] - h[2]) < max(h[3], rows[-1][0][3]) / 2:
                rows[-1].append(h)
            else:
                rows.append([h])
        nav["grid"] = [[h[0] for h in sorted(r, key=lambda h: h[1])] for r in rows]
        nav["default"] = next((h[0] for h in hits if h[4] == "primary"), hits[-1][0])
        notes.append(f"nav drafted from geometry: {nav['grid']} (default {nav['default']}); check the order")
    if not annotated:
        notes.append("no data-rr hints: every visible box became a node; delete decoration and add data-rr=\"button:id\" etc. for a cleaner draft")
    ay = kit.design_device.area("CoreUISafeInsets")[1]
    for n in tops:
        if n["rect"][1] < ay:
            notes.append(f"{n['id']}: starts at y {n['rect'][1]} inside the {ay:g} px top bar strip")
    return {"screen": re.sub(r"[^A-Za-z0-9]", "", name.title()) or "Screen", "title": name, "purpose": "TODO (owner words)",
            "design": {"device": kit.design_device.name}, "gui": {"display_order": 10, "insets": "CoreUISafeInsets"},
            "canon": [], "oq": [], "nodes": tops, "nav": nav, "boards": [{"name": "default"}]}, notes


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("list")
    p = sp.add_parser("show"); p.add_argument("spec")
    p = sp.add_parser("validate"); p.add_argument("specs", nargs="+"); p.add_argument("--strict", action="store_true"); p.add_argument("--json", action="store_true")
    p = sp.add_parser("render"); p.add_argument("spec"); p.add_argument("--out", required=True); p.add_argument("--devices", default="")
    p.add_argument("--skins", default=""); p.add_argument("--boards", default=""); p.add_argument("--text-scale", type=float, default=1.0)
    p.add_argument("--html-only", action="store_true")
    p = sp.add_parser("crit"); p.add_argument("crit"); p.add_argument("--pass", dest="pass_", type=int, required=True)
    p.add_argument("--from", required=True); p.add_argument("--spec", required=True)
    p = sp.add_parser("build"); p.add_argument("specs", nargs="+"); p.add_argument("--out", required=True); p.add_argument("--skin", default="")
    p.add_argument("--no-check", action="store_true"); p.add_argument("--no-parity", action="store_true")
    p.add_argument("--assets", default="", help="JSON of uploaded ids (iconSheet, hazardTile); default <out>/asset_ids.json")
    p = sp.add_parser("sheet"); p.add_argument("icondir", nargs="?"); p.add_argument("--out", required=True); p.add_argument("--cell", type=int, default=64)
    p = sp.add_parser("ingest"); p.add_argument("html"); p.add_argument("--out", required=True); p.add_argument("--size", default="")
    p.add_argument("--root", default=""); p.add_argument("--name", default="")
    a = ap.parse_args(argv)
    kit = U.Kit()
    if kit.errors and a.cmd not in ("list",):
        print("kit problems (fix canon or kit/roles.json):")
        for e in kit.errors:
            print(f"  E {e}")
        if a.cmd != "validate":
            return 1
    return {"list": cmd_list, "show": cmd_show, "validate": cmd_validate, "render": cmd_render, "crit": cmd_crit,
            "build": cmd_build, "sheet": cmd_sheet, "ingest": cmd_ingest}[a.cmd](kit, a)


if __name__ == "__main__":
    sys.exit(main())
