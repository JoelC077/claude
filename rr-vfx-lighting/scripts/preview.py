#!/usr/bin/env python3
"""preview.py: the orchestration behind `vfx.py preview` and `vfx.py crit` (run those; --help lists them).

preview lighting -> lookdev_bpy.py renders + contact.png/closeups.png + facts.md in OUT/lighting/
preview vfx      -> fxsim.py strips (+ POV composites over OUT/lighting plates) + sheets + facts.md in OUT/vfx/
crit             -> CRIT/rubric.md (multiuse-critic rubric + Profile F), CRIT/pass-N/ files, CRIT/brief.md from canon
"""
import importlib.util, json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
import vfx  # noqa: E402

POV_SETS = [  # (file, presets, look, time or None)
    ("pov_crisis", ["steam_chimney", "smoke_chimney", "steam_valve"], "hero", None),
    ("pov_cruise", ["steam_chimney", "smoke_chimney"], "hero", None),
    ("pov_boiler", ["boiler_burst", "smoke_chimney"], "hero", 0.5),
    ("pov_night", ["steam_chimney", "smoke_chimney", "headlamp", "firebox_glow"], "grassland.night", None),
    ("pov_rain", ["steam_chimney", "rain"], "grassland.storm", None),
]
CAVEAT_L = ("Previews are approximations, not Roblox: Cycles + a numpy post (filmic curve, Atmosphere fog from depth, "
            "bloom, sun rays, ColorCorrection). Skybox, Future light falloff and Roblox tone mapping are not modelled; "
            "phone variants assume no shadows and no Bloom/SunRays (tech.lighting.post_low_quality). Studio test pending (owner).")
CAVEAT_V = ("Effects are simulated from the preset data with Roblox ParticleEmitter rules; textures are procedural stand-ins "
            "for the built-ins; particles are not lit by the scene beyond a LightInfluence factor; lights show as glow dots "
            "only; drift = Workspace.GlobalWind at train speed. Studio test pending (owner).")


def critic_dir():
    return vfx.find_sibling("multiuse-critic", "RR_CRITIC_SKILL")


def sheet(out, items, tile="320x180"):
    """contact_sheet.py from multiuse-critic; returns exit code (2 = over the size limit)."""
    c = critic_dir()
    if not c:
        print("multiuse-critic not found (RR_CRITIC_SKILL): contact sheet skipped")
        return 3
    r = subprocess.run([sys.executable, str(c / "scripts" / "contact_sheet.py"), str(out), *items, "--tile", tile],
                       capture_output=True, text=True)
    if r.returncode not in (0, 2):
        print(r.stdout + r.stderr)
    return r.returncode


def sheets(d, hero, rest, tile, limit=6):
    """contact.png = hero at true size + up to `limit` tiles; closeups.png = the rest. Shrinks the batch on overflow."""
    first, later = rest[:limit], rest[limit:]
    while True:
        rc = sheet(d / "contact.png", [f"{hero[0]}={hero[1]}@1"] + [f"{l}={p}" for l, p in first], tile)
        if rc != 2 or not first:
            break
        later = [first.pop()] + later
    if later:
        sheet(d / "closeups.png", [f"{l}={p}" for l, p in later], tile)
    return rc


def has_bpy():
    return importlib.util.find_spec("bpy") is not None


def lighting(model, a, d):
    L = model.light_raw.get("preview", {})
    looks = a.names if (a.what == "lighting" and a.names) else L.get("default_set", model.looks()[:1])
    phone = [p for p in (a.phone.split(",") if a.phone is not None else L.get("phone_set", [])) if p]
    d.mkdir(parents=True, exist_ok=True)
    for n in looks:
        try:
            model.resolve_look(n.split("@")[0])
        except KeyError as e:
            print(f"preview lighting: {e}")
            return 2
    if not has_bpy():
        return swatches(model, looks, d)
    cmd = [sys.executable, str(HERE / "lookdev_bpy.py"), "--looks", ",".join(looks), "--out", str(d),
           "--phone", ",".join(phone), "--samples", str(a.samples)] + (["--quick"] if a.quick else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print("lookdev failed:\n" + "\n".join((r.stdout + r.stderr).splitlines()[-15:]))
        return 1
    facts = []
    for n in looks:
        slug = n.replace("+", "_").replace("@", "_")
        for suffix in ("", ".phone"):
            f = d / f"{slug}{suffix}.facts.json"
            if f.is_file():
                facts.append(json.loads(f.read_text()))
    hero = facts[0]
    rest = [(f["look"] + (" (phone)" if f["phone"] else ""), str(d / f["png"])) for f in facts[1:]]
    sheets(d, (hero["look"], str(d / hero["png"])), rest, "320x180")
    write_lighting_facts(model, d, facts)
    print(f"lighting preview: {len(facts)} renders, sheets and facts.md in {d}")
    return 0


def write_lighting_facts(model, d, facts):
    cu = json.loads((d / "canon_used.json").read_text()) if (d / "canon_used.json").is_file() else {}
    lines = [f"# Lighting looks: measured on the preview renders ({vfx.TODAY})", "",
             f"Player view: roof3p = standing on a coach roof, eye {cu.get('eye_3p', '?')} studs up (tech.camera.eye_3p); "
             f"door1p = leaning out of a coach doorway, eye {cu.get('eye_1p', '?')} (tech.camera.eye_1p); vertical FOV "
             f"{cu.get('fov', '?')} (tech.camera.fov_v). The train never moves (identity.pillars.stable_train).", "",
             "| look | cam | sun elev | luma | clip/crush % | train vs world | ground (HSL sat) | sky | spawn-edge fog | bands |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for f in facts:
        lines.append(f"| {f['look']}{' phone' if f['phone'] else ''} | {f['camera']} | {f['sun']['elevation_deg']}"
                     f"{' (moon)' if f['sun']['moon'] else ''} | {f['mean_luma']} | {f['clipped_pct']}/{f['crushed_pct']} | "
                     f"{f['train_vs_world_contrast']}:1 | {f['ground_mean']} ({f['ground_sat_hsl']}) | {f['sky_mean']} | "
                     f"{f['spawn_edge_fog']} at {f['spawn_edge_studs']:.0f} | {'; '.join(f['bands']) or 'none'} |")
    lines += ["", "Checks against canon:",
              "- spawn-edge fog: canon keeps haze to hide the streamer's spawn edge (tech.lighting.atmosphere, "
              "tech.streaming.window); below 0.9 the edge may show.",
              "- ground saturation: canon says nothing above about 45% (style.material.ground_value).",
              "- bands: frame and sky means tested against the Dead Rails sepia and Land or Die blue-sky bands (style.dont.*).",
              "- train vs world: relative-luminance ratio of the train to everything around it in the same frame.", "",
              "Limits: " + CAVEAT_L]
    (d / "facts.md").write_text("\n".join(lines) + "\n")


def swatches(model, looks, d):
    """No bpy: one swatch card per look (horizon, zenith, fog, ambient) so the numbers can still be compared."""
    from PIL import Image, ImageDraw
    import fxsim
    rows = []
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
        p = d / f"{n.replace('+', '_').replace('@', '_')}.swatch.png"
        im.save(p)
        rows.append((n, str(p)))
    sheets(d, rows[0], rows[1:], "384x60")
    (d / "facts.md").write_text("# Lighting looks\n\nbpy not available: swatch cards only; no render, no measurements. "
                                "Run where bpy imports (cloud image: pip bpy).\n")
    print("lighting preview: bpy not importable here, wrote swatch cards only (say so to the owner)")
    return 0


def effects(model, a, d, plates):
    import fxsim
    names = a.names if (a.what == "vfx" and a.names) else list(model.presets)
    bad = [n for n in names if n not in model.presets]
    if bad:
        print(f"unknown preset(s): {', '.join(bad)}")
        return 2
    d.mkdir(parents=True, exist_ok=True)
    stats = {}
    for n in names:
        stats[n] = fxsim.strip(model, n, d / f"strip_{n}.png", quick=a.quick)
        if a.gif:
            fxsim.gif(model, n, d / f"anim_{n}.gif", seconds=1.0 if a.quick else 3.0, quick=a.quick)
    hero_look = model.light_raw.get("preview", {}).get("hero", "grassland.day")
    povs = []
    for fname, pres, look, t in POV_SETS:
        look = hero_look if look == "hero" else look
        vj = plates / f"view_{look.replace('+', '_').replace('@', '_')}.json"
        if not vj.is_file() or any(p not in model.presets for p in pres):
            continue
        r = fxsim.pov(model, pres, vj, d / f"{fname}.png", t=t)
        r["look"] = look
        povs.append((fname, r))
    order = sorted(names, key=lambda n: (model.presets[n]["priority"], n))
    tiles = [(n, str(d / f"strip_{n}.png")) for n in order]
    if povs:
        hero = (f"{povs[0][0]} ({povs[0][1]['look']})", povs[0][1]["out"])
        rest = tiles[:6] + [(f"{f} ({r['look']})", r["out"]) for f, r in povs[1:]] + tiles[6:]
    else:
        hero, rest = tiles[0], tiles[1:]
    sheets(d, hero, rest, "384x112")
    write_vfx_facts(model, d, names, stats, povs)
    print(f"vfx preview: {len(names)} strips, {len(povs)} POV composites, sheets and facts.md in {d}"
          + ("" if povs else " (no plates: run preview all or preview lighting first for POV composites)"))
    return 0


def write_vfx_facts(model, d, names, stats, povs):
    B = model.budget_raw
    lines = [f"# Effects: measured on the simulation ({vfx.TODAY})", "",
             "Side strips: steady state at Speed " + str(model.meta['speeds'].get('normal', 35)) + " (gameplay.speed.normal) "
             "on sky, pasture and dark (tunnel light 0.22) backdrops, or a time strip for bursts; a 5-stud avatar "
             "(tech.units.avatar_h) and a 5-stud bar give scale. The train never moves: drift is Workspace.GlobalWind.", "",
             "| preset | kind | priority | anchor | phone live (budget formula) | sim live (strip) | px/stud | canon / OQ |",
             "|---|---|---|---|---|---|---|---|"]
    for n in names:
        p = model.presets[n]
        c = vfx.preset_cost(model, n, "phone")
        canon = p["canon"] if isinstance(p["canon"], str) else ", ".join(p["canon"])
        lines.append(f"| {n} | {p['kind']} | {p['priority']} | {p['anchor']} | {c['steady'] or c['burst']:.0f} | "
                     f"{'/'.join(str(x) for x in stats[n]['live'])} | {stats[n]['px_per_stud']} | {canon}{' · ' + p['oq'] if p.get('oq') else ''} |")
    if povs:
        lines += ["", "POV composites (roof3p, particles over the lookdev plate, Speed = gameplay.speed.fast):", "",
                  "| composite | look | presets | live | overdraw max / p95 / mean | screen covered |", "|---|---|---|---|---|---|"]
        for f, r in povs:
            lines.append(f"| {f} | {r['look']} | {', '.join(r['presets'])} | {r['live']} | {r['overdraw_max']} / "
                         f"{r['overdraw_p95']} / {r['overdraw_mean']} | {r['screen_covered'] * 100:.1f}% |")
    lines += ["", f"Budgets ({B.get('status', '')}):", ""]
    for tier in ("phone", "pc"):
        for s, sd in B.get("sets", {}).items():
            tot = vfx.set_cost(model, sd["presets"], tier)
            bad, _ = vfx.over_budget(model, tot, tier)
            lines.append(f"- {tier} {s}: steady {tot['steady']:.0f}, peak {tot['steady'] + tot['burst']:.0f}, fill "
                         f"{tot['fill']:.0f} stud^2, lights {tot['lights']} -> {'OVER: ' + ', '.join(w for w, _, _ in bad) if bad else 'within'}")
    lines += ["", "Limits: " + CAVEAT_V]
    (d / "facts.md").write_text("\n".join(lines) + "\n")


def run(model, a):
    out = Path(a.out)
    rc = 0
    if a.what in ("lighting", "all"):
        rc |= lighting(model, a, out / "lighting")
    if a.what in ("vfx", "all"):
        rc |= effects(model, a, out / "vfx", out / "lighting")
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


def brief(model, group):
    b = model.bible
    v = lambda k, d="?": b.value(k, d) if b.ok() else d
    speeds = "/".join(str(int(x)) for x in model.meta["speeds"].values())
    what = ("lighting looks per biome and time of day (Lighting, Atmosphere, ColorCorrection, Bloom, SunRays)"
            if group == "lighting" else "effect presets (particles, beams, trails, lights) for crises, fails and running")
    lines = [f"# Risky Rails {group} presets (rr-vfx-lighting)",
             f"- Purpose: Roblox-native {what} that make each game state read at a glance on a phone.",
             f"- Audience: {v('identity.audience.launch')}; {v('identity.audience.devices')} (phone {v('tech.ui_platform.phone')} landscape).",
             f"- Player view: players stay on the train (roofs, coaches, cab); third-person eye {v('tech.camera.eye_3p')} studs "
             f"above the floor, first-person {v('tech.camera.eye_1p')}, vertical FOV {v('tech.camera.fov_v')}. The train never moves; "
             f"the world scrolls at Speed {speeds} studs/s, so effects drift back with Workspace.GlobalWind.",
             "- Stage: look-dev presets; the images are preview approximations (see the Limits line in Facts), judged as "
             "intent: shape, colour, value, readability, not engine-exact pixels.",
             f"- Fixed constraints: tone {v('identity.tone.company')}; {v('identity.tone.not')}. Never {v('style.dont.dead_rails')} "
             f"(Dead Rails) or {v('style.dont.land_or_die')} (Land or Die); no {v('style.dont.default_green')}; red only for the "
             f"one danger signal (style.dont.red_decoration). Haze stays: it hides the streamer's spawn edge "
             f"(tech.lighting.atmosphere = {v('tech.lighting.atmosphere')}). Colours are rr-bible tokens or declared effect colours. "
             "Phone budget and priorities are in Facts (crisis signals keep full rate on phones; ambience drops first).",
             "- Owner worries / already decided: crisis effects must be the loudest thing in frame (sound carries slapstick "
             "too, av.audio.slapstick). Open, on defaults: OQ-026 time of day (looks change only with biome or fork modifier), "
             "OQ-027 rain shelved, OQ-028 derail explosion unassigned, OQ-029 phone budget. Placeholders: built-in textures "
             "stand in for custom flipbooks (asset upload is the owner's).",
             "step 2: pre-answered (canon via rr-bible; owner away)"]
    return "\n".join(lines) + "\n"


def crit(model, a):
    critic = critic_dir()
    if not critic:
        print("multiuse-critic not found: set RR_CRITIC_SKILL")
        return 2
    src = Path(a.src)
    group = a.group or src.name
    if not (src / "contact.png").is_file():
        print(f"{src}/contact.png missing: run vfx.py preview first")
        return 2
    C = Path(a.crit)
    pdir = C / f"pass-{a.pass_}"
    pdir.mkdir(parents=True, exist_ok=True)
    (C / "rubric.md").write_text(merged_rubric(critic), encoding="utf-8")
    for n in ("contact.png", "contact.json", "closeups.png", "closeups.json", "facts.md"):
        if (src / n).is_file():
            shutil.copy2(src / n, pdir / n)
    if not (C / "brief.md").is_file():
        (C / "brief.md").write_text(brief(model, group), encoding="utf-8")
        print(f"wrote {C / 'brief.md'} (edit the Owner worries line if the owner said more)")
    extra = " --images closeups.png" if (pdir / "closeups.png").is_file() else ""
    print(f"wrote {C / 'rubric.md'} (multiuse-critic rubric + Profile F) and pass-{a.pass_}/ files")
    print(f"next: python3 {critic / 'scripts' / 'critic_kit.py'} build {C} --pass {a.pass_} --kind full --profile F "
          f"--role \"senior VFX and lighting artist\"{extra}")
    print("then spawn a fresh critic on the printed prompt (multiuse-critic step 5); never score it yourself")
    return 0


if __name__ == "__main__":
    print("usage: preview.py is imported by vfx.py; run `vfx.py preview lighting|vfx|all ...` or `vfx.py crit ...`\n" + __doc__)
    sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
