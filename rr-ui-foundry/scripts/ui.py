#!/usr/bin/env python3
"""rr-ui-foundry: screen spec -> critic boards + a Roblox ScreenGui package, driven by rr-bible tokens.

  ui.py list                                    specs (specs/ or $RR_UI_SPECS) and kit templates
  ui.py show SPEC                               nodes, states, nav, boards, canon cites
  ui.py validate SPEC... [--strict] [--json]    every objective check; exit 1 on errors (--strict: warnings too)
  ui.py render SPEC... --out DIR [--kit] [--devices a,b] [--skins A,C] [--boards x,y] [--text-scale 1.3] [--html-only]
                                                HTML + PNG boards (device x board x skin), zone board, contact.png
                                                (phone @1 + a true-size PC crop), closeups.png, facts.md. Several
                                                specs = one sheet for the set (each screen in DIR/<Screen>/);
                                                --kit adds a board of every template x state x variant
  ui.py crit CRIT --pass N --from DIR --spec A[,B] [--owner present|away]
                                                pass-N files + brief.md (spec, source, the canon rules it keeps);
                                                prints the critic_kit.py command (Profile B). Never scores.
  ui.py build SPEC... --out DIR [--skin C] [--assets ids.json] [--no-check] [--no-parity]
                                                Rojo-ready package: RR_UIKit, RR_UITheme, RR_UITemplates,
                                                screens/*, Studio demo, icon sheet, ASSETS.md, UI_SPEC.md, manifest;
                                                gates: validate, luaparse, bible check, luatest (parity+runtime).
                                                --no-check = BUILD DRAFT (never a handover)
  ui.py sheet [ICONDIR] --out DIR [--cell 64]   pack SVG/PNG icons into one sprite sheet + icons.json
  ui.py ingest HTML --out SPEC [--size 844x390] [--root ROOT] [--name Screen]
                                                draft spec from an HTML mock or Design board (data-rr hints)

SPEC is a path or a name in specs/. Canon: rr-bible (found by glob or $RR_BIBLE_SKILL). Critic scripts:
multiuse-critic ($RR_CRITIC_SKILL). Standard library, plus Playwright + Pillow for render/sheet/ingest and
node luaparse / lupa for the build gates (each is skipped and named when missing).
"""
import sys
sys.dont_write_bytecode = True  # noqa: E402  (keep the skill folder free of __pycache__)
import argparse, base64, datetime, difflib, hashlib, html, json, os, re, shutil, subprocess
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
    try:
        return U.Screen(kit, spec_path(s))
    except U.SpecError as e:
        sys.exit(f"spec error: {e}")


# ------------------------------------------------------------------ list / show / validate
def cmd_list(kit, a):
    root = Path(os.environ.get("RR_UI_SPECS") or SKILL / "specs")
    for p in sorted(root.glob("*.json")):
        sc = load(kit, p)
        print(f"  {p.stem:24} {sc.name:20} {len(sc.index):3} nodes  boards: {', '.join(b.get('name', '?') for b in sc.boards)}")
    print("templates: " + ", ".join(f"{k}{' (runtime)' if v.get('runtime') else ''}" for k, v in kit.comps.items()))
    print(f"skins: {', '.join(kit.skins)} (main {kit.default_skin}: {kit.skin_status})  devices: {', '.join(kit.devices)}")
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
        print("  contrast (lowest per skin): " + fmt_contrast(F["contrast"]))
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


def fmt_contrast(c):
    """'A 3.19:1 diff_next.label (board insane; large text, AA 3:1)' per skin: the bar each text is held to."""
    return "; ".join(f"{k} {v[0]}:1 {v[1]} (board {v[2]}; {'large text, AA 3:1' if v[3] < 4 else 'AA 4.5:1'})"
                     for k, v in c.items() if v)


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
    """Icons for the boards: the spec's own folder wins, the skill's shared set fills the rest."""
    out = {}
    for d in screen.icon_dirs:
        if d and d.is_dir():
            for f in d.glob("*.svg"):
                out.setdefault(f.stem, re.sub(r"<\?xml[^>]*>", "", f.read_text(encoding="utf-8")))
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
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    screens = [load(kit, x) for x in a.specs]
    if a.kit:
        kp = out / "kit_board.json"
        kp.write_text(json.dumps(kit_spec(kit), indent=1), encoding="utf-8")
        screens.append(load(kit, kp))
    if not screens:
        sys.exit("render: give one or more SPECs, or --kit")
    devs = [d for d in (a.devices.split(",") if a.devices else list(kit.devices)) if d]
    skins = [x for x in (a.skins.split(",") if a.skins else kit.skins) if x]
    bad = [d for d in devs if d not in kit.devices] + [x for x in skins if x not in kit.skins]
    if bad:
        sys.exit(f"unknown device or skin: {', '.join(bad)} (devices {', '.join(kit.devices)}; skins {', '.join(kit.skins)})")
    if a.html_only is False:
        try:
            import playwright  # noqa: F401
        except ImportError:
            print("Playwright missing: writing HTML only (pip install playwright; see SKILL.md limits)")
            a.html_only = True
    multi = len(screens) > 1
    kit_devs = [d for d in devs if d in (kit.design_device.name, "pc")] or devs[:1]  # the kit board is not a screen
    results = [render_one(kit, sc, out / sc.name if multi else out, a, kit_devs if sc.name == "KitBoard" else devs, skins)
               for sc in screens]
    if multi:
        (out / "facts.md").write_text(f"## Facts: {' + '.join(r['sc'].name for r in results)} (one kit, one token set)\n\n"
                                      + "\n".join(r["facts"].replace("## Facts:", "### Facts:", 1) for r in results), encoding="utf-8")
    sheet_msg = "" if a.html_only else contact_sheets(out, results)
    code = 0
    for r in results:
        over = [(n, m) for n, ms in r["measures"].items() for m in ms["overflow"] if not m["truncated"]]
        trunc = sorted({m["id"] for ms in r["measures"].values() for m in ms["overflow"] if m["truncated"]})
        print(f"{r['sc'].name}: {len(r['files'])} boards -> {r['out']}" + (" (HTML only)" if a.html_only else ""))
        print(f"  checks: {len(r['E'])} errors, {len(r['W'])} warnings; text overflow {len(over)}; "
              f"truncated {len(trunc)}{' (text stress: ' + ', '.join(trunc[:6]) + ')' if trunc and a.text_scale != 1 else ''}; "
              f"fonts missing {r['missing_fonts'] or 'none'}")
        if trunc and a.text_scale != 1:
            print(f"  W text stress x{a.text_scale:g}: {len(trunc)} texts truncate (Roblox PreferredTextSize would cut them)")
        code = max(code, 1 if r["E"] else 0)
    if sheet_msg:
        print("sheets" + sheet_msg)
    return code


def render_one(kit, sc, out, a, devs, skins):
    out.mkdir(parents=True, exist_ok=True)
    boards = [b for b in sc.boards if not a.boards or b.get("name") in a.boards.split(",")]
    if not boards:
        sys.exit(f"{sc.name}: no boards match --boards")
    phone = kit.design_device.name
    main, dskin = boards[0], kit.default_skin if kit.default_skin in skins else skins[0]
    jobs = [(b, phone, dskin, False) for b in boards]
    jobs += [(main, d, dskin, False) for d in devs if d != phone]
    jobs += [(main, phone, x, False) for x in skins if x != dskin]
    jobs.append((main, phone, dskin, True))
    fonts, missing_fonts = fonts_css(kit)
    icons = load_icons(sc)
    files = []
    for b, d, x, z in jobs:
        scene = U.resolve(sc, kit.devices[d], x, b, text_scale=a.text_scale)
        name = f"{sc.name}__{b.get('name', 'board')}__{d}__{x}{'__zones' if z else ''}"
        (out / f"{name}.html").write_text(board_html(scene, sc, kit, fonts, icons, z), encoding="utf-8")
        tops = [bx["box"] for bx in scene["boxes"] if bx["top"] and bx["layer"] == "core"]
        files.append({"name": name, "board": b.get("name"), "device": d, "skin": x, "zones": z, "screen": sc.name,
                      "size": kit.devices[d].screen, "stack": scene.get("stack", {}).get("hidden"), "tops": tops,
                      "png": str(out / f"{name}.png")})
    measures = {}
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
                page.screenshot(path=f["png"], clip={"x": 0, "y": 0, "width": W, "height": H})
                measures[f["name"]] = page.evaluate(MEASURE_JS)
                ctx.close()
            br.close()
        pcf = next((f for f in files if f["device"] == "pc" and f["skin"] == dskin and not f["zones"]), None)
        if pcf and pcf["tops"]:
            crop = crop_true_size(pcf, out / f"{sc.name}__pc_crop.png")
            if crop:
                pcf["crop"] = str(crop)
    E, W_, I, F = U.check(sc, [kit.devices[d] for d in devs], skins, text_scale=a.text_scale)
    facts = facts_md(sc, kit, F, E, W_, I, files, measures, missing_fonts, a.text_scale)
    (out / "facts.md").write_text(facts, encoding="utf-8")
    (out / "render.json").write_text(json.dumps({"spec": str(sc.path), "files": files, "measures": measures},
                                                indent=1, default=str), encoding="utf-8")
    return {"sc": sc, "out": out, "files": files, "measures": measures, "E": E, "W": W_, "I": I, "facts": facts,
            "phone": phone, "dskin": dskin, "missing_fonts": missing_fonts}


def crop_true_size(f, path, pad=16):
    """The screen's own groups on the PC board at 1:1 (the sheet would otherwise show PC at x0.3)."""
    try:
        from PIL import Image
    except ImportError:
        return None
    W, H = f["size"]
    x0 = max(0, min(b[0] for b in f["tops"]) - pad)
    y0 = max(0, min(b[1] for b in f["tops"]) - pad)
    x1 = min(W, max(b[0] + b[2] for b in f["tops"]) + pad)
    y1 = min(H, max(b[1] + b[3] for b in f["tops"]) + pad)
    if x1 - x0 > 900 or y1 - y0 > 520 or x1 <= x0 or y1 <= y0:
        return None
    Image.open(f["png"]).crop((int(x0), int(y0), int(x1), int(y1))).save(path)
    return path


def contact_sheets(out, results):
    """contact.png: every screen's main phone board and its PC crop at true size, then the other states;
    closeups.png: zones, other skins and the remaining devices. Tiles shrink until each sheet fits the reader."""
    critic = find_critic()
    if not critic:
        return "; multiuse-critic not found: no contact sheet"
    cs = critic / "scripts" / "contact_sheet.py"
    multi = len(results) > 1
    short = {r["sc"].name: (re.findall(r"[A-Z][a-z0-9]*", r["sc"].name) or [r["sc"].name])[0] for r in results}
    if len(set(short.values())) < len(short):
        short = {k: k for k in short}
    band, band_pc, grid, close = [], [], [], []
    for r in results:
        phone, dskin, files = r["phone"], r["dskin"], r["files"]
        main = [f for f in files if f["device"] == phone and f["skin"] == dskin and not f["zones"]]
        if not main:
            continue
        pre = f"{short[r['sc'].name]} " if multi else ""
        W, H = main[0]["size"]
        band.append(f"{pre}phone {int(W)}x{int(H)} {main[0]['board']} ({dskin})={main[0]['png']}@1")
        pcf = next((f for f in files if f.get("crop")), None)
        if pcf:
            band_pc.append((f"{pre}PC {int(pcf['size'][0])}x{int(pcf['size'][1])} {pcf['board']}, crop", pcf["crop"]))
        grid += [f"{pre}{f['board']} phone={f['png']}" for f in main[1:]]
        others = [f for f in files if f["device"] != phone and not f["zones"]]
        for f in others:
            (grid if (not multi or f["device"] == "phone_notch") else close).append(f"{pre}{f['board']} {f['device']}={f['png']}")
        close += [f"{pre}zones {f['device']}={f['png']}" for f in files if f["zones"]]
        close += [f"{pre}skin {f['skin']} {f['board']}={f['png']}" for f in files if f["skin"] != dskin and not f["zones"]]
    pcs1 = [f"{l}={p}@1" for l, p in band_pc]
    pcs_t = [f"{l}={p}" for l, p in band_pc]
    flat = [x[:-2] for x in band]
    # contact variants (items, moved to closeups): true-size views first; drop grid tiles, then PC crops, then phones
    variants = [(band + pcs1 + grid, []), (band + pcs1, grid), (band + pcs_t, grid), (band + grid + pcs_t, [])]
    variants += [(band[:n] + flat[n:] + pcs_t, grid) for n in range(len(band) - 1, 0, -1)]
    variants.append((flat + pcs_t, grid))
    msgs = []

    def run(target, items, tiles):
        r = None
        for tile in tiles:
            r = subprocess.run([sys.executable, str(cs), str(out / target), *items, "--tile", tile], capture_output=True, text=True)
            if r.returncode == 0:
                break
        return r
    moved = []
    if band:
        for items, rest in variants:
            r = run("contact.png", items, ("400x225", "320x180", "270x152"))
            if r.returncode == 0:
                moved = rest
                break
        msgs.append(sheet_msg("contact.png", r))
    if close + moved:
        r = run("closeups.png", moved + close, ("560x260", "400x185", "320x148", "260x120", "220x102"))
        msgs.append(sheet_msg("closeups.png", r))
    return "; " + "; ".join(msgs)


def sheet_msg(target, r):
    last = r.stdout.strip().splitlines()[0] if r.stdout.strip() else ""
    return f"{target} ({last.split(': ', 1)[-1]})" + ("" if r.returncode == 0 else
                                                      f" exit {r.returncode}: {r.stderr.strip()[-200:] or 'over the reader budget'}")


def facts_md(sc, kit, F, E, W, I, files, measures, missing_fonts, text_scale):
    dd, pc = kit.design_device, kit.devices.get("pc")
    L = [f"## Facts: {sc.name} (measured by rr-ui-foundry; render = model + Chromium, not Roblox)", ""]
    L.append(f"- Design space: {dd.name} screen {dd.screen[0]:g}x{dd.screen[1]:g}, ScreenGui {sc.insets} area "
             f"{'x'.join(f'{v:g}' for v in dd.area(sc.insets)[2:])} px (top bar {dd.insets.get('top', 0):g} px, tech.ui_platform.topbar_inset).")
    pcx = kit.fit(pc, "CoreUISafeInsets") * kit.density.get(pc.display, 1) if pc else None
    L.append("- Layout: pin + scale with own fit (a smaller area shrinks a group only as much as it needs). px per design px: "
             + (f"PC {pcx:.2f} (tech.ui_platform.layout); " if pcx else "")
             + "UIScale after the fit: " + ", ".join(f"{k} {v:g}" for k, v in kit.density.items()) + " (Large = OQ-033).")
    L.append(f"- Skin on the main boards: {kit.default_skin} = {kit.skin_status}; other skins on closeups.")
    if text_scale != 1.0:
        L.append(f"- Text stress: every text x{text_scale:g} (a stand-in for GuiService.PreferredTextSize, not its exact "
                 "factor); sizes below include it.")
    if sc.raw.get("purpose"):
        L.append(f"- Purpose: {sc.raw['purpose']}")
    L.append("")
    L.append("| device | px per design px | smallest text | smallest target | touch zones | stack |")
    L.append("|---|---|---|---|---|---|")
    for d, v in F["devices"].items():
        k = ", ".join(f"{x:.3f}" for x in (v["k"] or {}).values())
        L.append(f"| {d} | {k} | {fmt_min(v['min_text'])} | {fmt_min(v['min_target'])} | {v['zones'].get('size', '-') if v['zones'] else '-'} | "
                 f"{'; '.join(f'{b}: {st}' for b, st in (v.get('stack') or {}).items()) or '-'} |")
    L.append("")
    L.append("- Lowest text contrast per skin (WCAG vs the fill it sits on; canon ui.rules.contrast: 4.5:1 body, 3:1 large "
             "text >= 18.66 px bold or 24 px): " + fmt_contrast(F["contrast"]))
    L.append(f"- Minimum text (ui.rules.min_text): display {kit.min_text['display']:g} px, body {kit.min_text['body']:g} px, "
             f"touch target {kit.touch_target:g} px (tech.ui_platform.touch_target_px); errors on every touch device.")
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


KIT_TEXTS = {"danger": "gameplay.alerts.coal_low", "risk": "gameplay.alerts.junction_ahead",
             "cash": "gameplay.alerts.fare_banked", "info": "gameplay.alerts.crate_landed"}
KIT_ICONS = {"danger": "coal", "risk": "lever", "cash": "coin", "info": "crate"}


def kit_spec(kit):
    """A generated spec that boards every kit template in every state and variant (ui.py render --kit):
    controls (button variants x normal/hover/pressed/disabled, chips off/on/pressed/disabled), panels (with and
    without close), tickets (four kinds full and compact, halo, stamp, count badge, +N MORE)."""
    cols = (150, 290, 430, 570)
    nodes, controls, dis, press, hover, grid = [], [], [], {}, {}, []
    variants = [v for v in (kit.comps["button"].get("variants") or {}) if v != "icon"] + ["icon"]
    for r, var in enumerate(variants[:4]):
        for c, state in enumerate(("normal", "hover", "pressed", "disabled")):
            nid = f"b_{var}_{state}"
            w = 52 if var == "icon" else 130
            slots = {"icon": "chevron_right"} if var == "icon" else {"text": var.upper()}
            nodes.append({"id": nid, "use": "button", "variant": var, "rect": [cols[c], 66 + r * 58, w, 52], "slots": slots,
                          "action": "noop"})
            controls.append(nid)
            if c == 0:
                grid.append([])
            grid[-1].append(nid)
            {"hover": hover, "pressed": press}.get(state, {})[nid] = state
            if state == "disabled":
                dis.append(nid)
    for c, state in enumerate(("off", "on", "pressed", "disabled")):
        nid = f"c_{state}"
        nodes.append({"id": nid, "use": "chip", "rect": [cols[c], 306, 44, 44], "slots": {"text": str(c + 1)},
                      "on": "sel=1" if state == "on" else None, "action": "noop"})
        nodes[-1] = {k: v for k, v in nodes[-1].items() if v is not None}
        controls.append(nid)
        if c == 0:
            grid.append([])
        grid[-1].append(nid)
        if state == "pressed":
            press[nid] = "pressed"
        if state == "disabled":
            dis.append(nid)
    panels = ["pn_close", "pn_plain"]
    nodes.append({"id": "pn_close", "use": "panel", "rect": [30, 70, 380, 180], "slots": {"title": "WITH CLOSE", "closable": True}})
    nodes.append({"id": "pn_plain", "use": "panel", "rect": [434, 70, 380, 180], "slots": {"title": "NO CLOSE"}})
    tickets = []
    for r, kind in enumerate(("danger", "risk", "cash", "info")):
        parts = [x.strip() for x in str(kit.b.value(KIT_TEXTS[kind]) or "?").split(" / ")]
        base = {"kind": kind, "icon": KIT_ICONS[kind], "title": parts[0], "life": 0.6, "sticky": kind == "danger"}
        full = dict(base, body=parts[1] if len(parts) > 1 else "", halo=kind == "danger", count=2 if kind == "info" else None)
        if kind == "cash" and len(parts) > 2:
            full["stamp"] = parts[2]
        nodes.append({"id": f"t_{kind}", "use": "ticket", "rect": [150, 66 + r * 72, 290, 64], "slots": {k: v for k, v in full.items() if v is not None}})
        nodes.append({"id": f"tc_{kind}", "use": "ticket_compact", "rect": [450, 66 + r * 48, 290, 44], "slots": base})
        tickets += [f"t_{kind}", f"tc_{kind}"]
    nodes.append({"id": "t_more", "use": "more_chip", "rect": [150, 360, 92, 26], "slots": {"n": 2}})
    tickets.append("t_more")
    return {"screen": "KitBoard", "title": "Component kit: every template x state x variant",
            "purpose": "Kit board, not a screen: controls rows = " + ", ".join(variants[:4]) + " buttons, then chips; columns = "
                       "normal, hover, pressed, disabled (chips: off, on, pressed, disabled). Panels with and without close. "
                       "Tickets: danger (crisis halo), risk, cash (stamp), info (count badge) full and compact, +N MORE.",
            "source": "generated by ui.py render --kit from kit/components.json", "design": {"device": kit.design_device.name},
            "gui": {"display_order": 10, "insets": "CoreUISafeInsets"}, "canon": ["ui.hud.anatomy", "ui.lobby.controls", "ui.rules.one_accent"],
            "data": {"sel": {"values": [0, 1], "default": 1}},
            "nodes": [{"id": "board", "type": "frame", "rect": [0, 58, 844, 332], "pin": "cc",
                       "note": "one group, so the board scales as a unit (separate groups would pin apart on PC)",
                       "children": [dict(n, rect=[n["rect"][0], n["rect"][1] - 58, n["rect"][2], n["rect"][3]]) for n in nodes]}],
            "nav": {"grid": grid + [["pn_close.close"]], "default": grid[0][0]},
            "machine": {"initial": "controls", "states": {
                "controls": {"hide": panels + tickets, "disable": dis},
                "panels": {"hide": controls + tickets},
                "tickets": {"hide": controls + panels}},
                "transitions": [["*", "controls", "controls", None], ["*", "panels", "panels", None], ["*", "tickets", "tickets", None]]},
            "boards": [{"name": "controls", "state": "controls", "comp_states": dict(hover, **press)},
                       {"name": "panels", "state": "panels"}, {"name": "tickets", "state": "tickets"}]}


# ------------------------------------------------------------------ crit hand-off
def cmd_crit(kit, a):
    critic = find_critic()
    if not critic:
        print("multiuse-critic not found: set RR_CRITIC_SKILL")
        return 2
    scs = [load(kit, x) for x in a.spec.split(",") if x]
    C, src = Path(a.crit).resolve(), Path(getattr(a, "from")).resolve()
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
        (C / "brief.md").write_text(brief_md(scs, kit, a.owner), encoding="utf-8")
        got.append("brief.md (new)")
    img = " --images closeups.png" if "closeups.png" in got else ""
    print(f"wrote {pdir}: {', '.join(got)}")
    print(f"next: python3 {critic / 'scripts' / 'critic_kit.py'} build {C} --pass {a.pass_} --kind full --profile B "
          f"--role \"senior UI designer\"{img}")
    print("then spawn a fresh critic on the printed prompt (multiuse-critic step 5); never score it yourself")
    if a.owner == "present":
        print("owner present: ask multiuse-critic step 2's questions before pass 1 and write the answers into brief.md")
    return 0


def brief_md(scs, kit, owner="present"):
    keys = ("identity.audience.launch", "identity.audience.target", "identity.audience.devices")
    vals = [kit.b.value(k) for k in keys]
    miss = [k for k, v in zip(keys, vals) if not v]
    if miss:
        print(f"warning: rr-bible lookup failed for {', '.join(miss)}; the brief says so (re-run ui.py crit once bible.py reads cleanly)")
    aud = "; ".join(v for v in vals if v) or f"UNKNOWN: rr-bible lookup failed ({', '.join(miss)})"
    one = len(scs) == 1
    title = scs[0].raw.get("title", scs[0].name) if one else "UI kit set: " + " + ".join(sc.name for sc in scs)
    L = [f"# {title}"]
    for sc in scs:
        pre = "" if one else f"{sc.name}: "
        view = "a modal panel over the game" if sc.gui.get("modal") else "a screen overlay over the running game (HUD)"
        L.append(f"Purpose: {pre}{sc.raw.get('purpose', 'see spec')} ({view})")
        if sc.raw.get("source"):
            L.append(f"Source: {pre}{sc.raw['source']}")
    dd = kit.design_device
    L += [f"Audience: {aud}",
          f"Player view: phone landscape {dd.screen[0]:g}x{dd.screen[1]:g} at true size (ScreenGui CoreUISafeInsets, top bar "
          f"{dd.insets.get('top', 0):g} px); the PC crop is true size too; other boards are scaled by the kit's pin + scale "
          "rule. Grey pills and circles are Roblox's own top bar, jump button and thumbstick.",
          "Stage: draft (generated from the spec by rr-ui-foundry; the same numbers build the Roblox package).",
          f"Fixed constraints: rr-bible tokens only (skin {kit.default_skin} = {kit.skin_status}); fonts "
          f"{', '.join(f['name'] for f in kit.fonts.values())}; text >= {kit.min_text['body']:g}/{kit.min_text['display']:g} px, "
          f"targets >= {kit.touch_target:g} px; clear of top bar, jump and thumbstick; exact game strings from canon."]
    canon = list(dict.fromkeys(k for sc in scs for k in sc.raw.get("canon", [])))
    if canon:
        rules = []
        for k in canon:
            v = kit.b.value(k)
            rules.append(f"{k} = {str(v)[:150]}" if v is not None else f"{k} = (missing in rr-bible)")
        L.append("Canon this design keeps (rr-bible; a fix that would break one goes under NEEDS OWNER, not ISSUES): "
                 + "; ".join(rules))
    oqs = []
    for oid in dict.fromkeys(o for sc in scs for o in sc.raw.get("oq", [])):
        q = kit.b.oq(oid)
        if q:
            oqs.append(f"{oid} {q['title']} (" + (f"decided: {q['fields'].get('default', '?')}, {q['decided']}" if q.get("decided")
                                                   else f"open; default in use: {q['fields'].get('default', '?')}") + ")")
    L.append("Already decided / open: " + ("; ".join(oqs) if oqs else "none"))
    L.append("step 2: pre-answered (canon via rr-bible; owner away)" if owner == "away"
             else "step 2: ask the owner (multiuse-critic step 2) and write the answers here before pass 1")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ icon sheet
def cmd_sheet(kit, a):
    src = Path(a.icondir or SKILL / "assets" / "icons")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    return make_sheet(src, out, a.cell)


def make_sheet(src, out, cell=64, scale=2):
    """Pack icons (a folder, or a list of files) into one white sprite sheet + icons.json."""
    icons = sorted(src, key=lambda f: f.stem) if isinstance(src, (list, tuple)) else \
        sorted(list(Path(src).glob("*.svg")) + list(Path(src).glob("*.png")))
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
         f"-- Skins are the options of {kit.skin_oq}; {skin} is active: {kit.skin_label(skin)}.", ""]
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
    screens = [load(kit, x) for x in a.specs]
    names = [sc.name for sc in screens]
    if len(set(names)) != len(names):
        sys.exit(f"two specs share a screen name: {', '.join(names)}")
    skin = a.skin or kit.default_skin
    if skin not in kit.skins:
        sys.exit(f"unknown skin {skin} (have {', '.join(kit.skins)})")
    gates = {}
    if a.no_check:
        gates["validate"] = "SKIPPED (draft)"
        print("  SKIPPED validate (--no-check): this is a draft package, never a handover")
    else:
        bad = 0
        for sc in screens:
            E, W, I, F = U.check(sc)
            print(f"  {'PASS' if not E else 'FAIL'} validate {sc.name}: {len(E)} errors, {len(W)} warnings")
            for e in E:
                print(f"    E {e}")
            bad += bool(E)
        if bad:
            print("build stopped: fix the errors (or --no-check for a draft package)")
            return 1
        gates["validate"] = "PASS"
    out = Path(a.out)
    lib = out / "src" / "shared" / "RR_UI"
    shutil.rmtree(lib / "screens", ignore_errors=True)  # a rebuild must not keep another build's screens
    (lib / "screens").mkdir(parents=True, exist_ok=True)
    (out / "src" / "client").mkdir(parents=True, exist_ok=True)
    (out / "icons").mkdir(parents=True, exist_ok=True)
    used, lost = {}, []
    for sc in screens:
        for name in sorted(sc.icon_refs()):
            f = sc.icon_file(name)
            if f:
                used.setdefault(name, f)
            else:
                lost.append(f"{sc.name}: {name}")
    for f in (out / "icons").glob("rr_ui_icons.png"):
        f.unlink()
    icons_meta = {}
    if used and make_sheet(list(used.values()), out / "icons") == 0:
        icons_meta = json.loads((out / "icons" / "icons.json").read_text())["icons"]
    if lost:
        print(f"  E icons without a file (boards show a placeholder, Roblox shows nothing): {', '.join(lost)}")
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
    ship = {"name": "RR_UI", "tree": {"$className": "DataModel", "ReplicatedStorage": {"RR_UI": {"$path": "src/shared/RR_UI"}}}}
    demo = json.loads(json.dumps(ship))
    demo["tree"]["StarterPlayer"] = {"StarterPlayerScripts": {"RR_UIDemo": {"$path": "src/client/RR_UIDemo.client.lua"}}}
    (out / "default.project.json").write_text(json.dumps(ship, indent=2), encoding="utf-8")
    (out / "demo.project.json").write_text(json.dumps(demo, indent=2), encoding="utf-8")
    (out / "ASSETS.md").write_text(assets_md(icons_meta, tile), encoding="utf-8")
    (out / "UI_SPEC.md").write_text(ui_spec_md(kit, screens, skin), encoding="utf-8")
    (out / "README.md").write_text(readme_md(screens), encoding="utf-8")
    luas = sorted(out.rglob("*.lua"))
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
                            "--specs", ",".join(str(sc.path.resolve()) for sc in screens)], capture_output=True, text=True)
        lines = r.stdout.strip().splitlines()
        tail = "; ".join(x for x in lines if x.startswith(("parity:", "runtime:"))) or (lines or ["(no output)"])[-1]
        gates["luatest"] = "PASS" if r.returncode == 0 else ("SKIP" if r.returncode == 3 else "FAIL")
        print(f"  {gates['luatest']} luatest (parity+runtime): {tail}")
        if r.returncode not in (0, 3):
            print(r.stdout[-1500:] + (("\n" + r.stderr[-1500:]) if r.stderr.strip() else ""))
    else:
        gates["luatest"] = "SKIPPED (--no-parity)"
    man = {"generated": datetime.datetime.now().isoformat(timespec="seconds"), "skin": skin,
           "skin_status": kit.skin_label(skin),
           "screens": {sc.name: hashlib.sha1(sc.path.read_bytes()).hexdigest()[:12] for sc in screens},
           "kit": kit_record(kit), "canon_cited": sorted(kit.cites), "gates": gates, "density": kit.density,
           "studio": "Studio test pending (owner); nothing here was published or uploaded"}
    (out / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    hard = [k for k, v in gates.items() if v not in ("PASS", "SKIP") and not v.startswith("SKIPPED")]
    if hard or errs or lost:
        verdict, code = "BUILD FAIL", 1
    elif a.no_check or a.no_parity:
        verdict, code = "BUILD DRAFT (gates skipped: " + ", ".join(k for k, v in gates.items() if v.startswith("SKIPPED")) + ")", 0
    else:
        verdict, code = "BUILD PASS", 0
    print(f"{verdict}: {out}  (Studio test pending (owner))")
    return code


def kit_record(kit):
    """Kit hashes, and when a mission kit copy (RR_UI_KIT) differs from the skill's kit, the diff to promote."""
    rec = {"dir": str(kit.dir), "files": {f: hashlib.sha1((kit.dir / f).read_bytes()).hexdigest()[:12]
                                          for f in ("roles.json", "components.json")}}
    if kit.dir.resolve() != U.KIT_DIR.resolve():
        diff = []
        for f in ("roles.json", "components.json"):
            a_, b_ = (U.KIT_DIR / f).read_text().splitlines(), (kit.dir / f).read_text().splitlines()
            diff += [x for x in difflib.unified_diff(a_, b_, f"skill/{f}", f"mission/{f}", n=0, lineterm="")]
        rec["diff_vs_skill_kit"] = diff[:200]
        rec["promote"] = "owner OK needed before copying this kit change into the skill's kit/"
    return rec


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
         f"Skin {skin} ({kit.roles['skins'].get(skin, '')}; {kit.skin_label(skin)}); density by GuiService.ViewportDisplaySize: "
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
    use = ["local UI = require(game.ReplicatedStorage.RR_UI.RR_UIKit)"]
    steps = []
    for sc in screens:
        var = re.sub(r"^[A-Z]", lambda m: m[0].lower(), sc.name)
        use.append(f"local {var} = UI.mount(require(game.ReplicatedStorage.RR_UI.screens.{sc.name}))")
        if sc.types:
            t0 = next(iter(sc.types))
            slot = next((m[0] for t in sc.types.values() for m in U.SLOT.findall(t["body"] or "")), None)
            ts = next((t for t, v in sc.types.items() if slot and "{" + slot in (v["body"] or "")), None)
            use.append(f'{var}:push("{t0}")' + " " * max(1, 28 - len(t0)) + "-- alert types: " + ", ".join(sc.types))
            if ts:
                use.append(f'{var}:push("{ts}", {{{slot} = "Sam"}})' + "   -- slots fill the body text")
            use.append(f'{var}:clear("{t0}")' + " " * max(1, 27 - len(t0)) + "-- the server's clear alert (ID)")
            steps.append(f"{sc.name}: push each alert type with the demo's H key; tickets stack, merge and expire as on the boards.")
        if sc.machine:
            evs = list(dict.fromkeys(t["event"] for t in sc.machine["transitions"]))
            first = next((t["event"] for t in sc.machine["transitions"] if t["from"] in (sc.machine["initial"], "*")), evs[0])
            use.append(f'{var}:send("{first}")' + " " * max(1, 27 - len(first)) + "-- machine events: " + ", ".join(evs))
            use.append(f"{var}.Action.Event:Connect(function(name, data) end)   -- controls fire (name, data) for game code")
            steps.append(f"{sc.name}: L sends the next event ({', '.join(evs)}); every state looks like its board.")
        nav = sc.nav
        if nav.get("default") or nav.get("back"):
            steps.append(f"{sc.name} with a controller: focus starts on {nav.get('default')}, every control is reachable"
                         + (f", ButtonB = {nav.get('back')}" if nav.get("back") else "") + ".")
    use.append('UI.setSkin("A")                -- live reskin of every mounted screen')
    st = "\n".join(f"{i}. {x}" for i, x in enumerate(
        ["Play Solo with `demo.project.json` (or RR_UIDemo in StarterPlayerScripts): each screen cycles its boards; "
         "compare with the rendered PNGs."] + steps +
        ["Device emulator: iPhone 14 landscape, an iPad and 1920x1080: clear of the top bar, jump button and thumbstick; "
         "note GuiService:GetGuiInset() and the JumpButton's AbsolutePosition if they differ from the facts.",
         "Settings > Reduce Motion on: panels and tickets fade or snap, nothing slides.",
         "Upload the images in ASSETS.md and write asset_ids.json, then rebuild."], 1))
    return f"""# RR_UI package (rr-ui-foundry)

Screens: {names}. Generated; rebuild with `ui.py build` instead of editing generated files.

## Install
- Rojo: `rojo serve` with default.project.json (RR_UI lands in ReplicatedStorage; this is what ships).
  `demo.project.json` adds the Studio demo (RR_UIDemo) for the check below.
- By hand: make a Folder `RR_UI` in ReplicatedStorage with ModuleScripts RR_UIKit, RR_UITheme, RR_UITemplates and a
  Folder `screens` holding one ModuleScript per screen.
- Optional: put rr-game-feel's RR_Feel, RR_FeelPresets and RR_FeelMath in the same RR_UI folder; the kit then plays
  its events (reduce motion included). Without it the kit only fades, and snaps when Reduce Motion is on.
- **Remove RR_UIDemo before publishing** (it binds H/K/L and cycles boards; it returns at once outside Studio).

## Use (LocalScript)
```lua
{chr(10).join(use)}
```

## Studio test (owner; nothing here has run in Roblox)
{st}
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
    if not src.is_file():
        sys.exit(f"ingest: no such file {src}")
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
    notes, decide = [], []
    chrome = [r for r in kit.roles["roles"] if not r.startswith(U.SPECIAL_ROLES) and r not in ("danger", "hazard", "hazard_ink")]
    by_key = {}                        # bible token key -> the chrome role that uses it (default skin first)
    for sk in [kit.default_skin] + [x for x in kit.skins if x != kit.default_skin]:
        for r in chrome:
            c = kit.colors.get(sk, {}).get(r)
            if c:
                by_key.setdefault(c["key"], (r, sk))
    code, out = kit.b.run("tokens", "--format", "json")
    try:
        tokens = json.loads(out).get("colors", {}) if code == 0 else {}
    except ValueError:
        tokens = {}
    skins_hit = {}

    def snap(hexv, what):
        """Exact bible token -> the role mapped to it (any skin), else that token as @key; otherwise the nearest
        chrome role in any skin. Difficulty, kind and danger roles are never picked for chrome. Over 6 dE is a
        decision for the owner, not a silent pick."""
        if not hexv:
            return None
        hexv = hexv.upper()
        if hexv in ("#000000", "#FFFFFF"):
            notes.append(f"{what}: pure {'black' if hexv == '#000000' else 'white'} mapped to "
                         f"{'ink' if hexv == '#000000' else 'paper_top'} (mock default, not a token)")
            return "ink" if hexv == "#000000" else "paper_top"
        exact = [k for k, v in tokens.items() if str(v).upper() == hexv]
        for k in exact:
            if k in by_key:
                r, sk = by_key[k]
                skins_hit[sk] = skins_hit.get(sk, 0) + 1
                return r
        if exact:
            notes.append(f"{what}: {hexv} = rr-bible {exact[0]} (no role maps it; used @{exact[0]}: add a role if it recurs)")
            return "@" + exact[0]
        best = min(((r, sk, U.delta_e(hexv, c["hex"])) for sk in kit.skins for r in chrome
                    for c in [kit.colors.get(sk, {}).get(r)] if c), key=lambda x: x[2])
        if best[2] > 6:
            decide.append(f"{what}: {hexv} is off-palette (nearest role {best[0]} in skin {best[1]}, dE {best[2]:.1f}): owner "
                          "decides (new token via bible.py add-fact, or that role)")
        elif best[2] > 2:
            notes.append(f"{what}: {hexv} snapped to {best[0]} (skin {best[1]}, dE {best[2]:.1f})")
        return best[0]

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
    if skins_hit:
        notes.append("exact token matches by skin: " + ", ".join(f"{k} {v}" for k, v in sorted(skins_hit.items()))
                     + f" (main skin {kit.default_skin}: {kit.skin_status})")
    notes = [f"DECIDE {d}" for d in decide] + notes
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
    p = sp.add_parser("render"); p.add_argument("specs", nargs="*"); p.add_argument("--out", required=True); p.add_argument("--devices", default="")
    p.add_argument("--kit", action="store_true", help="add the kit board (every template x state x variant)")
    p.add_argument("--skins", default=""); p.add_argument("--boards", default=""); p.add_argument("--text-scale", type=float, default=1.0)
    p.add_argument("--html-only", action="store_true")
    p = sp.add_parser("crit"); p.add_argument("crit"); p.add_argument("--pass", dest="pass_", type=int, required=True)
    p.add_argument("--from", required=True); p.add_argument("--spec", required=True, help="SPEC or A,B for a set rendered together")
    p.add_argument("--owner", choices=("present", "away"), default="present",
                   help="present (default): the brief asks multiuse-critic step 2's questions; away: canon pre-answers them")
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
