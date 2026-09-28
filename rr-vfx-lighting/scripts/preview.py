#!/usr/bin/env python3
"""preview.py: the orchestration behind `vfx.py preview` and `vfx.py crit` (run those; --help lists them).

preview lighting [LOOKS]  -> lookdev_bpy.py renders (+ phone fallbacks at the phone resolution), sheets, facts.md
                             in OUT/lighting/
preview vfx [PRESETS]     -> fxsim.py strips + POV composites over the OUT/lighting plates, sheets, facts.md in OUT/vfx/
preview all [NAMES]       -> both, plus OUT/board/: contact.png (phone POV at 1:1 + player views), closeups.png (effect
                             strips at 1:1), one facts.md and manifest.json: the one board `vfx.py crit` judges
NAMES may mix looks and presets (a pack): POVs put the named loops (+ each look's fx_on) over every named look from
the roof and the doorway, plus the camera nearest each preset's anchor (stand.near_camera), on PC and phone; each
burst gets its own POV. No NAMES = the default sets in lighting.json (preview.default_set, preview.pov_sets).
crit -> CRIT/rubric.md (multiuse-critic rubric + Profile F), CRIT/pass-N/ files, CRIT/brief.md from the manifest.
"""
import sys
sys.dont_write_bytecode = True  # never leave __pycache__ inside the skill
import hashlib, importlib.util, json, os, re, shutil, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
import vfx  # noqa: E402

CAVEAT_L = ("Previews are approximations, not Roblox: Cycles + a numpy post (filmic curve, Atmosphere fog from depth, "
            "bloom, sun rays, ColorCorrection). Skybox, Future light falloff and Roblox tone mapping are not modelled; "
            "phone variants assume no shadows and no Bloom/SunRays (tech.lighting.post_low_quality). The train is a "
            "stand-in (livery open, OQ-025). Studio test pending (owner).")
CAVEAT_V = ("Effects are simulated from the preset data with Roblox ParticleEmitter rules; textures are procedural stand-ins "
            "for the built-ins; particles are not lit by the scene beyond a LightInfluence factor; lights show as glow dots "
            "only; drift = Workspace.GlobalWind at train speed. Studio test pending (owner).")
SEEN_COVER = 0.001   # a preset under 0.1% of the screen in every POV is flagged: players may never see it


def slug(n):
    return n.replace("+", "_").replace("@", "_")


def critic_dir():
    return vfx.find_sibling("multiuse-critic", "RR_CRITIC_SKILL")


def has_bpy():
    return importlib.util.find_spec("bpy") is not None


# ------------------------------------------------------------------ sheets
def sheet(out, items, tile="384x216"):
    """contact_sheet.py from multiuse-critic; items = [(label, path, true_size)]. -> exit code (2 = over the limit)."""
    c = critic_dir()
    if not c:
        print("multiuse-critic not found (RR_CRITIC_SKILL): contact sheet skipped")
        return 3
    specs = [f"{l}={p}{'@1' if t else ''}" for l, p, t in items]
    r = subprocess.run([sys.executable, str(c / "scripts" / "contact_sheet.py"), str(out), *specs, "--tile", tile],
                       capture_output=True, text=True)
    if r.returncode not in (0, 2):
        print(r.stdout + r.stderr)
    return r.returncode


def sheets(d, first, second, tile="384x216"):
    """contact.png = `first` (true-size hero + fitted player views); closeups.png = `second` + whatever did not fit.
    multiuse-critic reads one contact sheet and at most one close-up sheet; anything left over is listed, not shown."""
    first, second = list(first), list(second)
    spill = []
    while first:
        if sheet(d / "contact.png", first, tile) != 2 or len(first) == 1:
            break
        spill.insert(0, first.pop())
    rest = [(l, p, False) for l, p, _ in spill] + second
    left = []
    while rest:
        if sheet(d / "closeups.png", rest, tile) != 2 or len(rest) == 1:
            break
        left.insert(0, rest.pop())
    if not rest and (d / "closeups.png").is_file():
        (d / "closeups.png").unlink()
    return left


# ------------------------------------------------------------------ plan
def plan(model, a):
    """-> dict(presets, renders, phone, povs, pack, looks). Raises KeyError on unknown names."""
    Lp = model.light_raw.get("preview", {})
    hero = Lp.get("hero", model.looks()[0])
    presets, looks = vfx.pack_names(model, a.names)
    pack = bool(a.names)
    if not pack:
        presets = list(model.presets)
        povs = []
        for s in Lp.get("pov_sets", []):
            if all(p in model.presets for p in s["presets"]):
                povs.append({**s, "look": hero if s["look"] == "hero" else s["look"], "camera": s.get("camera", "roof3p")})
        renders = list(Lp.get("default_set", [hero]))
        phone = [p for p in (a.phone.split(",") if a.phone is not None else Lp.get("phone_set", [])) if p]
        plain = [hero]
    else:
        plain = list(dict.fromkeys(l.split("@")[0] for l in looks)) or [hero]
        loops = [p for p in presets if model.presets[p]["kind"] == "loop"]
        bursts = [p for p in presets if model.presets[p]["kind"] == "burst"]
        near = [c for c in dict.fromkeys(model.near.get(model.presets[p]["anchor"]) for p in presets)
                if c and c not in ("roof3p", "door1p")]
        povs = []
        for i, lk in enumerate(plain):
            fx = [f for f in model.resolve_look(lk, vfx.Issues())["fx_on"] if f in model.presets and f not in loops]
            if loops or fx:
                for cam in ["roof3p", "door1p"] + (near if i == 0 else []):
                    povs.append({"name": f"pov_{slug(lk)}_{cam}", "presets": loops + fx, "look": lk, "camera": cam,
                                 "phone": cam == "roof3p"})
        for b in bursts:
            p = model.presets[b]
            povs.append({"name": f"pov_{b}", "presets": loops + [b], "look": plain[0],
                         "camera": model.near.get(p["anchor"]) or "roof3p", "t": (p.get("preview") or {}).get("t", 0.4)})
        renders = [l for l in looks if "@" in l] + [x for lk in plain for x in (lk, f"{lk}@door1p")]
        phone = [p for p in (a.phone.split(",") if a.phone is not None else plain) if p]
    for pv in povs:
        renders.append(pv["look"] if pv["camera"] == "roof3p" else f"{pv['look']}@{pv['camera']}")
        if pv.get("phone") and pv["camera"] == "roof3p" and pv["look"] not in phone:
            phone.append(pv["look"])
    return {"presets": presets, "renders": list(dict.fromkeys(renders)), "phone": phone, "povs": povs, "pack": pack,
            "looks": plain if pack else list(dict.fromkeys(r.split("@")[0] for r in renders))}


# ------------------------------------------------------------------ lighting
def lighting(model, P, a, d):
    """-> list of facts dicts (or None on failure)."""
    looks = P["renders"]
    d.mkdir(parents=True, exist_ok=True)
    if not has_bpy():
        return swatches(model, looks, d)
    cmd = [sys.executable, str(HERE / "lookdev_bpy.py"), "--looks", ",".join(looks), "--out", str(d),
           "--phone", ",".join(P["phone"]), "--samples", str(a.samples), "--presets", str(vfx.presets_dir())] + \
          (["--quick"] if a.quick else [])
    r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, RR_VFX_PRESETS=str(vfx.presets_dir())))
    if r.returncode:
        print("lookdev failed:\n" + "\n".join((r.stdout + r.stderr).splitlines()[-15:]))
        return None
    facts = []
    for n in looks:
        for suffix in ("", ".phone"):
            f = d / f"{slug(n)}{suffix}.facts.json"
            if f.is_file():
                facts.append(json.loads(f.read_text()))
    def lab(f):
        return f"{f['look']}{' PHONE' if f['phone'] else ''}: luma {f['mean_luma']}, train/world {f['train_vs_world_contrast']}:1"
    first = [(lab(facts[0]), str(d / facts[0]["png"]), True)] + [(lab(f), str(d / f["png"]), False) for f in facts[1:]]
    sheets(d, first, [])
    (d / "facts.md").write_text("\n".join(lighting_facts(model, d, facts)) + "\n")
    print(f"lighting preview: {len(facts)} renders, sheets and facts.md in {d}")
    return facts


def lighting_flags(f):
    out = []
    tw = f.get("train_vs_world_contrast")
    if tw and tw < 2.0:
        out.append(f"train vs world {tw}:1 < 2:1")
    if f.get("crushed_pct", 0) > 5:
        out.append(f"crush {f['crushed_pct']}% > 5%" + (f" (train {f['crushed_train_pct']}%)" if f.get("crushed_train_pct") else ""))
    if f.get("spawn_edge_fog", 1) < 0.9:
        out.append(f"spawn-edge fog {f['spawn_edge_fog']} < 0.9")
    return out


def lighting_facts(model, d, facts, title=True):
    cu = json.loads((d / "canon_used.json").read_text()) if (d / "canon_used.json").is_file() else {}
    st = cu.get("stand", model.dims)
    lines = ([f"# Lighting looks: measured on the preview renders ({vfx.TODAY})", ""] if title else []) + [
        f"Cameras: roof3p = coach B roof, eye {cu.get('eye_3p', '?')} (tech.camera.eye_3p); door1p = leaning out of coach A's "
        f"doorway, eye {cu.get('eye_1p', '?')} (tech.camera.eye_1p); cab1p = loco cab facing the firebox, eye {cu.get('cab_eye', '?')} "
        f"above rail (tech.camera.cab_view); coach1p = inside coach A facing the power box. FOV {cu.get('fov', '?')}; phone "
        f"renders at {'x'.join(str(x) for x in cu.get('phone_res', ['?', '?']))} (tech.ui_platform.phone). Stand envelope: gauge "
        f"{st['gauge']:g}, body {st['width']:g} wide, floor {st['floor']:g}, roof {st['roof']:g} (tech.units.*, OQ-030); "
        "stand-in train: navy, cream band and interiors, hazard-yellow roof rails (style.form.rails); livery open (OQ-025).", "",
        "| look | cam | sun elev | luma | clip/crush % (train) | train vs world | hazard vs world | ground (sat) | sky | spawn-edge fog | bands |",
        "|---|---|---|---|---|---|---|---|---|---|---|"]
    flags = []
    for f in facts:
        name = f"{f['look']}{' phone' if f['phone'] else ''}"
        lines.append(f"| {name} | {f['camera']} | {f['sun']['elevation_deg']}{' (moon)' if f['sun']['moon'] else ''} | "
                     f"{f['mean_luma']} | {f['clipped_pct']}/{f['crushed_pct']} ({f.get('crushed_train_pct')}) | "
                     f"{f['train_vs_world_contrast']}:1 | {f.get('hazard_vs_world')}:1 | {f['ground_mean']} ({f['ground_sat_hsl']}) | "
                     f"{f['sky_mean']} | {f['spawn_edge_fog']} at {f['spawn_edge_studs']:.0f} | {'; '.join(f['bands']) or 'none'} |")
        fl = lighting_flags(f)
        if fl:
            flags.append(f"- {name} ({f['camera']}): " + "; ".join(fl))
    lines += ["", "Checks against canon: spawn-edge fog >= 0.9 hides the streamer's spawn edge (tech.lighting.atmosphere, "
              "tech.streaming.window); ground saturation <= 0.45 (style.material.ground_value); bands = frame and sky means "
              "tested against the Dead Rails sepia and Land or Die blue-sky bands (style.dont.*); contrast = relative "
              "luminance ratio in the same frame."]
    if flags:
        lines += ["", "Flags (maker heuristics, not canon: train vs world under 2:1 fades on a dim phone; crush over 5% "
                  "loses shape):"] + flags
    lines += ["", "Limits: " + CAVEAT_L]
    return lines


def swatches(model, looks, d):
    """No bpy: one swatch card per look (horizon, zenith, fog, ambient) so the numbers can still be compared."""
    from PIL import Image, ImageDraw
    import fxsim
    items = []
    for n in looks:
        lk = model.resolve_look(n.split("@")[0])
        C = lk["classes"]
        def hx(tv):
            return tv[1] if tv[0] == "color" else "#%02X%02X%02X" % tuple(tv[1])
        sw = [("fog", hx(C["Atmosphere"]["Color"])), ("decay", hx(C["Atmosphere"]["Decay"])),
              ("outdoor amb", hx(C["Lighting"]["OutdoorAmbient"])), ("ambient", hx(C["Lighting"]["Ambient"]))]
        im = Image.new("RGB", (768, 120), (21, 23, 28))
        dr = ImageDraw.Draw(im)
        dr.text((6, 4), f"{n}: NO BPY, swatches only (not a render)", fill=(235, 228, 200), font=fxsim.font(13))
        for i, (lab, h) in enumerate(sw):
            dr.rectangle([6 + i * 190, 26, 186 + i * 190, 96], fill=h)
            dr.text((8 + i * 190, 100), f"{lab} {h}", fill=(235, 228, 200), font=fxsim.font(11))
        p = d / f"{slug(n)}.swatch.png"
        im.save(p)
        items.append((n, str(p), False))
    sheets(d, items, [], "384x60")
    (d / "facts.md").write_text("# Lighting looks\n\nbpy not available: swatch cards only; no render, no measurements. "
                                "Run where bpy imports (cloud image: pip bpy).\n")
    print("lighting preview: bpy not importable here, wrote swatch cards only (say so to the owner)")
    return []


# ------------------------------------------------------------------ effects
def effects(model, P, a, d, plates):
    """-> (strip stats, POV results, notes)."""
    import fxsim
    names = P["presets"]
    d.mkdir(parents=True, exist_ok=True)
    stats = {}
    for n in names:
        stats[n] = fxsim.strip(model, n, d / f"strip_{n}.png", quick=a.quick)
        if a.gif:
            fxsim.gif(model, n, d / f"anim_{n}.gif", seconds=1.0 if a.quick else 3.0, quick=a.quick)
    povs, notes = [], []
    for pv in P["povs"]:
        key = pv["look"] if pv["camera"] == "roof3p" else f"{pv['look']}@{pv['camera']}"
        vj = plates / f"view_{slug(key)}.json"
        if not vj.is_file():
            notes.append(f"{pv['name']}: no plate {vj.name} (run preview all or preview lighting {key} first)")
            continue
        r = fxsim.pov(model, pv["presets"], vj, d / f"{pv['name']}.png", t=pv.get("t"))
        r.update(name=pv["name"], look=pv["look"])
        povs.append(r)
        vjp = plates / f"view_{slug(pv['look'])}.phone.json"
        if pv.get("phone") and vjp.is_file():
            r = fxsim.pov(model, pv["presets"], vjp, d / f"{pv['name']}.phone.png", t=pv.get("t"), tier="phone")
            r.update(name=pv["name"] + ".phone", look=pv["look"])
            povs.append(r)
    order = sorted(names, key=lambda n: (model.presets[n]["priority"], n))
    first = [(caption(model, r), r["out"], i == 0) for i, r in enumerate(sorted(povs, key=lambda r: r["tier"] != "phone"))]
    strips = [(strip_caption(model, n, stats[n]), str(d / f"strip_{n}.png"), True) for n in order]
    if not first:
        first, strips = strips[:1], strips[1:]
    left = sheets(d, first, strips)
    lines = vfx_facts(model, names, stats, povs, notes, P["pack"])
    if left:
        lines.insert(2, f"Not on the sheets (too many for one contact + one close-up sheet): {', '.join(l for l, _, _ in left)}.")
    (d / "facts.md").write_text("\n".join(lines) + "\n")
    print(f"vfx preview: {len(names)} strips, {len(povs)} POV composites, sheets and facts.md in {d}"
          + (f"; {len(notes)} POV(s) skipped (no plates)" if notes else ""))
    return stats, povs, notes


def seen(model, r, n):
    s = r["per_preset"].get(n, {})
    if not s.get("live"):   # lights or beams only
        return None
    return s["covered"] >= SEEN_COVER * 0.5 or s["visible"] >= 3


def caption(model, r):
    cam = r.get("camera") or "?"
    tier = " PHONE (phone rates, no shadows/Bloom/SunRays)" if r["tier"] == "phone" else ""
    shown = [n for n in r["presets"] if seen(model, r, n)]
    lights = [n for n in r["presets"] if seen(model, r, n) is None]
    unseen = [n for n in r["presets"] if seen(model, r, n) is False]
    txt = f"{r['look']} {cam}{tier}: " + (", ".join(shown) or "no effect visible")
    if lights:
        txt += f" + light {', '.join(lights)}"
    if unseen:
        txt += f"; NOT SEEN {', '.join(unseen)}"
    return txt + " · stand-in train"


def strip_caption(model, n, st):
    p = model.presets[n]
    what = f"side strip, Speed {st['speed']:g}" if p["kind"] == "loop" else "burst time strip"
    return f"{n} ({p['kind']} p{p['priority']}): {what}, {st['px_per_stud']} px/stud (construction view)"


def visibility_warnings(model, names, povs, pack):
    """Every named preset (pack) or priority-1 preset (default) under SEEN_COVER in every POV it is in."""
    out = []
    for n in names:
        p = model.presets[n]
        if not pack and p["priority"] != 1:
            continue
        rs = [r for r in povs if n in r["per_preset"]]
        if not rs:
            if any(L["class"] == "ParticleEmitter" for L in p["layers"]):
                out.append(f"- NOTE {n}: in no POV, judged from its strip only")
            continue
        if all(not r["per_preset"][n]["live"] for r in rs):
            continue
        best = max(rs, key=lambda r: r["per_preset"][n]["covered"])
        b = best["per_preset"][n]
        if b["covered"] < SEEN_COVER:
            out.append(f"- WARN {n}: under {SEEN_COVER * 100:.1f}% of the screen in every POV (best {best['name']}: "
                       f"{b['visible']} of {b['live']} visible, {b['covered'] * 100:.2f}%): players may never see it "
                       "(references/presets.md, Visible from the players' views)")
        for r in rs:
            s = r["per_preset"][n]
            if s["live"] and s["hidden"] >= 0.5 * s["live"]:
                out.append(f"- {n}: {s['hidden']} of {s['live']} hidden by the train or ground in {r['name']}")
            if s["dluma"] is not None and s["covered"] >= SEEN_COVER and abs(s["dluma"]) < 15:
                out.append(f"- {n}: faint in {r['name']} (luma change {s['dluma']:+} over its pixels; heuristic: under 15 reads weak)")
    return out


def vfx_facts(model, names, stats, povs, notes, pack, title=True):
    lines = ([f"# Effects: measured on the simulation ({vfx.TODAY})", ""] if title else []) + [
        "Side strips: steady state at Speed " + str(model.meta['speeds'].get('normal', 35)) + " (gameplay.speed.normal) "
        "on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar "
        "(tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.", "",
        "| preset | kind | priority | anchor | start | live phone / pc (budget formula, full rate) | sim live (strip) | px/stud | canon / OQ |",
        "|---|---|---|---|---|---|---|---|---|"]
    for n in names:
        p = model.presets[n]
        cp, cc = vfx.preset_cost(model, n, "phone"), vfx.preset_cost(model, n, "pc")
        canon = p["canon"] if isinstance(p["canon"], str) else ", ".join(p["canon"])
        lines.append(f"| {n} | {p['kind']} | {p['priority']} | {p['anchor']} | {p['start'] if p['kind'] == 'loop' else 'event'} | "
                     f"{cp['steady'] or cp['burst']:.0f} / {cc['steady'] or cc['burst']:.0f} | "
                     f"{'/'.join(str(x) for x in stats[n]['live'])} | {stats[n]['px_per_stud']} | {canon}{' · ' + p['oq'] if p.get('oq') else ''} |")
    if povs:
        lines += ["", "POV composites (particles over the lookdev plate from the same camera; loops at steady state, "
                  "Speed = gameplay.speed.fast; bursts fire after the loops warm up). Per preset: visible / live, hidden "
                  "by the train or ground, off-screen, share of the screen, luma change over its own pixels:", "",
                  "| POV | look | cam | tier | res | t s | overdraw max/p95 | screen | per preset |", "|---|---|---|---|---|---|---|---|---|"]
        for r in povs:
            per = []
            for n in r["presets"]:
                s = r["per_preset"][n]
                if not s["live"]:
                    per.append(f"{n} (light/beam)")
                    continue
                per.append(f"{n} {s['visible']}/{s['live']}, hid {s['hidden']}, off {s['offscreen']}, "
                           f"{s['covered'] * 100:.2f}%" + (f", Δluma {s['dluma']:+}" if s["dluma"] is not None else ""))
            lines.append(f"| {r['name']} | {r['look']} | {r.get('camera')} | {r['tier']} | {'x'.join(str(x) for x in r['res'])} | "
                         f"{r['t']} | {r['overdraw_max']}/{r['overdraw_p95']} | {r['screen_covered'] * 100:.1f}% | {'; '.join(per)} |")
    warn = visibility_warnings(model, names, povs, pack)
    if warn or notes:
        lines += ["", "Visibility (warnings are for the maker to fix before the critic; hidden counts are facts):"] + warn + \
                 [f"- skipped {x}" for x in notes]
    return lines


def budget_lines(model, names=None):
    B = model.budget_raw
    lines = [f"Budgets ({B.get('status', '')}); sets holding {'a pack preset' if names else 'any preset'}:"]
    for tier in ("phone", "pc"):
        for s, sd in B.get("sets", {}).items():
            if names and not set(sd["presets"]) & set(names):
                continue
            tot = vfx.set_cost(model, sd["presets"], tier)
            bad, _ = vfx.over_budget(model, tot, tier)
            lines.append(f"- {tier} {s}: steady {tot['steady']:.0f}, peak {tot['steady'] + tot['burst']:.0f}, emitters "
                         f"{tot['emitters']}, fill {tot['fill']:.0f} stud^2, lights {tot['lights']} -> "
                         f"{'OVER: ' + ', '.join(w for w, _, _ in bad) if bad else 'within'}")
    return lines


# ------------------------------------------------------------------ board (one critic, one sheet)
def board(model, P, a, out, lfacts, stats, povs, notes):
    d = out / "board"
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*"):
        f.unlink()
    phone = [r for r in povs if r["tier"] == "phone"]
    hero = phone[0] if phone else (povs[0] if povs else None)
    first = [(caption(model, hero), hero["out"], True)] if hero else []
    first += [(caption(model, r), r["out"], False) for r in povs if r is not hero]
    plates = {Path(r["out"]).name for r in povs}
    used = {r["look"] + ("" if r.get("camera") == "roof3p" else "@" + r["camera"]) for r in povs}
    for f in lfacts or []:   # looks with no POV (or phone renders without one) still get a tile
        key = f["look"]
        if key in used and not f["phone"]:
            continue
        if f["phone"] and any(r["look"] == key and r["tier"] == "phone" for r in povs):
            continue
        first.append((f"{key}{' PHONE' if f['phone'] else ''} (no effects): luma {f['mean_luma']}, train/world "
                      f"{f['train_vs_world_contrast']}:1 · stand-in train", str(out / "lighting" / f["png"]), False))
    order = sorted(P["presets"], key=lambda n: (model.presets[n]["priority"], n))
    strips = [(strip_caption(model, n, stats[n]), str(out / "vfx" / f"strip_{n}.png"), True) for n in order]
    left = sheets(d, first, strips)
    names = P["presets"] if P["pack"] else None
    lines = [f"# Look-dev board: {', '.join(a.names) if P['pack'] else 'default preview sets'} ({vfx.TODAY})", "",
             f"Presets from {vfx.presets_dir()}. Tiles show the player's views (POV composites: particles over the lit "
             "plate); strips on closeups.png are construction views for shape and timing only.", ""]
    if left:
        lines += [f"Not on the sheets: {', '.join(l for l, _, _ in left)} (see {out / 'vfx'} and {out / 'lighting'}).", ""]
    if lfacts:
        lines += ["## Looks", ""] + lighting_facts(model, out / "lighting", lfacts, title=False) + [""]
    lines += ["## Effects", ""] + vfx_facts(model, P["presets"], stats, povs, notes, P["pack"], title=False)
    lines += [""] + budget_lines(model, names) + ["", "Limits: " + CAVEAT_V]
    (d / "facts.md").write_text("\n".join(lines) + "\n")
    oqs = set()
    if model.budget_raw.get("oq"):
        oqs.add(model.budget_raw["oq"])
    for n in P["presets"]:
        if model.presets[n].get("oq"):
            oqs.add(model.presets[n]["oq"])
    for lk in P["looks"]:
        t = model.light_raw["times"].get(lk.split("+")[0].split(".")[-1], {})
        if t.get("oq"):
            oqs.add(t["oq"])
    man = {"names": a.names, "pack": P["pack"], "presets": P["presets"], "looks": P["looks"], "oqs": sorted(oqs),
           "povs": [r["name"] for r in povs], "presets_dir": str(vfx.presets_dir()),
           "warnings": [w for w in visibility_warnings(model, P["presets"], povs, P["pack"]) if "WARN" in w]}
    (d / "manifest.json").write_text(json.dumps(man, indent=1))
    print(f"board: {d / 'contact.png'}" + (" + closeups.png" if (d / "closeups.png").is_file() else "") +
          f", facts.md, manifest.json ({len(man['warnings'])} visibility warning(s))")
    for w in man["warnings"]:
        print(w)


def run(model, a):
    try:
        P = plan(model, a)
    except KeyError as e:
        print(f"preview: {e.args[0] if e.args else e}")
        return 2
    if a.what == "lighting" and a.names and P["presets"]:
        print("preview lighting takes looks only; use preview all for a pack of looks and effects")
        return 2
    out = Path(a.out).resolve()
    rc, lfacts, stats, povs, notes = 0, [], {}, [], []
    if a.what in ("lighting", "all"):
        lfacts = lighting(model, P, a, out / "lighting")
        rc |= 1 if lfacts is None else 0
    if a.what in ("vfx", "all") and P["presets"]:
        stats, povs, notes = effects(model, P, a, out / "vfx", out / "lighting")
    if a.what == "all" and not rc:
        board(model, P, a, out, lfacts, stats, povs, notes)
    return rc


# ------------------------------------------------------------------ critic set-up
def merged_rubric(critic):
    base = (critic / "references" / "rubric.md").read_text(encoding="utf-8")
    fx = (SKILL / "references" / "rubric-fx.md").read_text(encoding="utf-8")
    prof = fx[fx.index("## Profile F"):].rstrip() + "\n\n"
    if "## Profile F" in base:
        return base
    i = base.index("## Shared blocks")
    text = base[:i] + prof + base[i:]
    text = re.sub(r"(<!--\s*include-with:\s*A6, B5)(\s*-->)", r"\1, F5\2", text)
    text = re.sub(r"(<!--\s*include-with:\s*A5, A7, B2)(\s*-->)", r"\1, F2\2", text)
    return text


def brief(model, group, man=None):
    b = model.bible
    v = lambda k, d="?": b.value(k, d) if b.ok() else d
    speeds = "/".join(str(int(x)) for x in model.meta["speeds"].values())
    if man and man.get("pack"):
        what = (f"a look-dev pack: effects {', '.join(man['presets']) or 'none'}; looks {', '.join(man['looks'])} "
                "(Lighting, Atmosphere, ColorCorrection, Bloom, SunRays)")
        uses = "; ".join(f"{n}: {model.presets[n]['use']}" for n in man["presets"])
    elif group == "lighting":
        what, uses = "lighting looks per biome and time of day (Lighting, Atmosphere, ColorCorrection, Bloom, SunRays)", ""
    else:
        what, uses = "effect presets (particles, beams, trails, lights) for crises, fails and running", ""
    oqs = (man or {}).get("oqs") or ["OQ-026", "OQ-027", "OQ-028", "OQ-029"]
    def oq_line(o):
        q = b.oq(o) or {}
        return f"{o} {q.get('title', '')} (default {(q.get('fields') or {}).get('default', '?').split(' (')[0]})"
    oq_txt = "; ".join(oq_line(o) for o in oqs) if b.ok() else ", ".join(oqs)
    lines = [f"# Risky Rails {'look-dev pack' if man and man.get('pack') else group + ' presets'} (rr-vfx-lighting)",
             f"- Purpose: Roblox-native {what} that make each game state read at a glance on a phone."
             + (f" What each effect is for: {uses}." if uses else ""),
             f"- Audience: {v('identity.audience.launch')}; {v('identity.audience.devices')} (phone {v('tech.ui_platform.phone')} landscape).",
             f"- Player view: players stay on the train (roofs, coaches, cab); third-person eye {v('tech.camera.eye_3p')} studs "
             f"above the floor, first-person {v('tech.camera.eye_1p')}, vertical FOV {v('tech.camera.fov_v')}. The train never moves; "
             f"the world scrolls at Speed {speeds} studs/s, so effects drift back with Workspace.GlobalWind.",
             "- Stage: look-dev presets; the images are preview approximations (see the Limits lines in Facts), judged as "
             "intent: shape, colour, value, readability, not engine-exact pixels. The train is a stand-in (livery open, OQ-025): "
             "judge the looks and effects, not the train's paint. Strips are construction views; judge signal from the POV tiles.",
             f"- Fixed constraints: tone {v('identity.tone.company')}; {v('identity.tone.not')}. Never {v('style.dont.dead_rails')} "
             f"(Dead Rails) or {v('style.dont.land_or_die')} (Land or Die); no {v('style.dont.default_green')}; red only for the "
             f"one danger signal (style.dont.red_decoration). Haze stays: it hides the streamer's spawn edge "
             f"(tech.lighting.atmosphere = {v('tech.lighting.atmosphere')}). Colours are rr-bible tokens or declared effect colours. "
             "Phone budget and priorities are in Facts (crisis signals keep full rate on phones; ambience drops first).",
             "- Owner worries / already decided: crisis effects must be the loudest thing in frame (sound carries slapstick "
             f"too, av.audio.slapstick). Open, on defaults: {oq_txt}. Placeholders: built-in textures stand in for custom "
             "flipbooks (asset upload is the owner's).",
             "step 2: pre-answered (canon via rr-bible; owner away)"]
    return "\n".join(lines) + "\n"


def critic_drift(chosen):
    """Other multiuse-critic copies whose scripts differ from the one in use (printed as a warning)."""
    def h(c):
        return hashlib.sha1(b"".join((c / "scripts" / f).read_bytes() for f in ("critic_kit.py", "contact_sheet.py")
                                     if (c / "scripts" / f).is_file())).hexdigest()
    cands = vfx._walk_find(Path.home() / ".claude" / "skills", "multiuse-critic") + vfx._walk_find("/home/user", "multiuse-critic")
    ref = h(chosen)
    return [c for c in dict.fromkeys(p.resolve() for p in cands) if c != chosen.resolve() and h(c) != ref]


def crit(model, a):
    critic = critic_dir()
    if not critic:
        print("multiuse-critic not found: set RR_CRITIC_SKILL")
        return 2
    src = Path(a.src).resolve()
    if (src / "board" / "contact.png").is_file():
        src = src / "board"
    man = json.loads((src / "manifest.json").read_text()) if (src / "manifest.json").is_file() else None
    group = a.group or ("pack" if man else src.name)
    if not (src / "contact.png").is_file():
        print(f"{src}/contact.png missing: run vfx.py preview all first")
        return 2
    C = Path(a.crit).resolve()
    pdir = C / f"pass-{a.pass_}"
    pdir.mkdir(parents=True, exist_ok=True)
    (C / "rubric.md").write_text(merged_rubric(critic), encoding="utf-8")
    for n in ("contact.png", "contact.json", "closeups.png", "closeups.json", "facts.md"):
        if (src / n).is_file():
            shutil.copy2(src / n, pdir / n)
    if not (C / "brief.md").is_file():
        (C / "brief.md").write_text(brief(model, group, man), encoding="utf-8")
        print(f"wrote {C / 'brief.md'} (edit the Owner worries line if the owner said more)")
    if man and man.get("warnings"):
        print("visibility warnings on this board (fix them first, or tell the critic why not):\n" + "\n".join(man["warnings"]))
    extra = " --images closeups.png" if (pdir / "closeups.png").is_file() else ""
    print(f"critic: {critic}")
    for c in critic_drift(critic):
        print(f"WARN another multiuse-critic copy differs: {c} (the one above is used)")
    print(f"wrote {C / 'rubric.md'} (multiuse-critic rubric + Profile F) and pass-{a.pass_}/ files")
    print(f"next: python3 {critic / 'scripts' / 'critic_kit.py'} build {C} --pass {a.pass_} --kind full --profile {a.profile} "
          f"--role \"senior VFX and lighting artist\"{extra}")
    print("then spawn a fresh critic on the printed prompt (multiuse-critic step 5); never score it yourself")
    return 0


if __name__ == "__main__":
    print("usage: preview.py is imported by vfx.py; run `vfx.py preview lighting|vfx|all ...` or `vfx.py crit ...`\n" + __doc__)
    sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
