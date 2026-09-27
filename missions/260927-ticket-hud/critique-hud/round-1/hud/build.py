#!/usr/bin/env python3
"""Rebuilds every board of the Risky Rails ticket HUD remake into ./project/ (one script, static HTML)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "project"); os.makedirs(P, exist_ok=True)

# ---------- tokens ----------
T = dict(ink="#15171c", iron="#2a2e33", iron2="#3b4047", brass="#d9a441", brassD="#8a5f1c",
         card1="#f7edd3", card2="#e7d4a6", body="#463c2e", soot="rgba(21,23,28,.16)")
KINDS = {
  "danger": dict(stub="linear-gradient(180deg,#f0604f,#c42e22)", bar="#b02a20", stamp="#15171c", tag="CRISIS"),
  "risk":   dict(stub="repeating-linear-gradient(-45deg,#f2c230 0 8px,#15171c 8px 16px)", bar="#15171c", stamp="#15171c", tag="RISK"),
  "cash":   dict(stub="linear-gradient(180deg,#56d994,#23a05c)", bar="#156b3d", stamp="#0f5c31", tag="CASH"),
  "info":   dict(stub="linear-gradient(180deg,#48b6ab,#27857c)", bar="#1c6a63", stamp="#15171c", tag="CREW"),
}
TYPES = {
  "CoalLow": ("danger", "coal", "COAL LOW!", "Shovel coal in the firebox!", None),
  "PressureHigh": ("danger", "gauge", "PRESSURE HIGH!", "The boiler's gonna blow!", None),
  "Breakdown": ("danger", "wrench", "BREAKDOWN!", "Grab a wrench and fix it!", None),
  "PassengersUpset": ("danger", "passenger", "PASSENGERS UPSET!", "Check the carriages, fast!", None),
  "JunctionAhead": ("risk", "lever", "JUNCTION AHEAD!", "Safe or risky? Pull it!", None),
  "RiskyRoute": ("risk", "fork", "RISKY ROUTE!", "Multiplier up", "X2"),
  "FareBanked": ("cash", "coin", "FARE BANKED!", "Station paid out", "$120"),
  "CrateLanded": ("info", "crate", "CRATE LANDED!", "Grab it before it slides off!", None),
  "CrewJoined": ("info", "crewjoin", "CREW JOINED!", "{name} is aboard", None),
  "CrewLeft": ("info", "crewleave", "CREW LEFT!", "{name} left the train", None),
}
S = 'stroke="#15171c" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"'
ICONS = {
 "coal": f'<path d="M10 44 L18 26 L30 22 L40 30 L54 28 L58 44 Z" fill="#3a3f48" {S}/><path d="M20 30 L28 27" stroke="#8b939e" stroke-width="4" stroke-linecap="round"/><path d="M40 20 q4 -8 0 -14 q10 6 4 16" fill="#f2c230" {S}/>',
 "gauge": f'<circle cx="32" cy="34" r="22" fill="#dfe4ea" {S}/><path d="M32 34 L46 22" {S}/><path d="M16 36 a16 16 0 0 1 6 -14" stroke="#e23a2e" stroke-width="5" fill="none"/><circle cx="32" cy="34" r="4" fill="#15171c"/>',
 "wrench": f'<path d="M14 50 L36 28 a10 10 0 1 1 8 -12 l-8 6 l4 6 l8 -4 a10 10 0 0 1 -12 10 L22 58 Z" fill="#8b939e" {S}/>',
 "passenger": f'<circle cx="32" cy="22" r="10" fill="#f2c9a0" {S}/><path d="M14 56 q2 -18 18 -18 q16 0 18 18 Z" fill="#e23a2e" {S}/><path d="M27 21 l3 2 M37 21 l-3 2" stroke="#15171c" stroke-width="3"/>',
 "lever": f'<rect x="14" y="44" width="36" height="12" rx="3" fill="#5d6470" {S}/><path d="M32 46 L44 14" {S}/><circle cx="44" cy="14" r="7" fill="#e23a2e" {S}/>',
 "fork": f'<path d="M32 58 V36 L16 16 M32 36 L48 16" fill="none" stroke="#15171c" stroke-width="11" stroke-linecap="round"/><path d="M32 58 V36 L16 16 M32 36 L48 16" fill="none" stroke="#f2c230" stroke-width="5" stroke-linecap="round"/>',
 "coin": f'<circle cx="32" cy="32" r="22" fill="#f2c230" {S}/><circle cx="32" cy="32" r="14" fill="none" stroke="#b8860b" stroke-width="3"/><text x="32" y="41" font-family="Luckiest Guy" font-size="24" text-anchor="middle" fill="#15171c">$</text>',
 "crate": f'<rect x="12" y="16" width="40" height="36" rx="3" fill="#b87a3d" {S}/><path d="M12 16 L52 52 M52 16 L12 52" stroke="#8f5a2a" stroke-width="4"/><rect x="12" y="16" width="40" height="36" rx="3" fill="none" {S}/>',
 "crewjoin": f'<circle cx="26" cy="22" r="9" fill="#f2c9a0" {S}/><path d="M10 54 q2 -16 16 -16 q14 0 16 16 Z" fill="#48b6ab" {S}/><path d="M48 18 v16 M40 26 h16" stroke="#15171c" stroke-width="6" stroke-linecap="round"/>',
 "crewleave": f'<circle cx="26" cy="22" r="9" fill="#f2c9a0" {S}/><path d="M10 54 q2 -16 16 -16 q14 0 16 16 Z" fill="#8b939e" {S}/><path d="M40 26 h16" stroke="#15171c" stroke-width="6" stroke-linecap="round"/>',
}

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Montserrat,sans-serif;overflow:hidden}
.scene{position:relative;overflow:hidden;background:
 linear-gradient(180deg,#9fc3c9 0%,#c9d6b8 45%,#7f8f55 46%,#5f6e3e 70%,#4d5a33 100%)}
.scene .hill{position:absolute;left:-10%;width:70%;height:40%;top:30%;background:#6f8150;border-radius:50% 50% 0 0;opacity:.8}
.scene .hill.b{left:45%;width:80%;top:34%;background:#667a47}
.scene .rail{position:absolute;left:0;right:0;height:10px;background:#5a4a3a;}
.scene .rail.a{top:74%}.scene .rail.b{top:80%}
.scene .sleepers{position:absolute;left:0;right:0;top:72%;height:34px;background:repeating-linear-gradient(90deg,#3e3024 0 14px,transparent 14px 40px);opacity:.7}
.scene .train{position:absolute;left:18%;top:52%;width:34%;height:22%;background:#2a2e33;border:4px solid #15171c;border-radius:10px 10px 4px 4px}
.scene .train:before{content:"";position:absolute;left:8%;top:-40%;width:12%;height:40%;background:#2a2e33;border:4px solid #15171c;border-bottom:none}
.scene .train:after{content:"";position:absolute;right:6%;top:18%;width:26%;height:40%;background:#f2c230;border:4px solid #15171c;border-radius:4px}
.zone{position:absolute;border:2px dashed rgba(255,255,255,.55);border-radius:50%;background:rgba(0,0,0,.18)}
.topbar{position:absolute;left:0;right:0;top:0;height:36px;background:rgba(0,0,0,.28)}
.topbar i{position:absolute;top:4px;width:28px;height:28px;border-radius:8px;background:rgba(0,0,0,.45)}
.stack{position:absolute;display:flex;flex-direction:column;align-items:flex-end;gap:6px;transform-origin:bottom right}
.slot{position:relative;width:290px}
.slot.crisis{padding:5px 0}
.t{position:relative;width:290px;height:64px}
.t.c{height:40px}
.shadow{position:absolute;inset:0;top:4px;border-radius:11px;background:rgba(21,23,28,.45)}
.frame{position:absolute;inset:0;border-radius:11px;background:linear-gradient(180deg,#3b4047,#22262b);border:3px solid #15171c}
.card{position:absolute;left:3px;top:3px;right:3px;bottom:3px;border-radius:8px;overflow:hidden;
 background:repeating-linear-gradient(135deg,rgba(138,95,28,.06) 0 2px,transparent 2px 7px),linear-gradient(180deg,#f7edd3,#e7d4a6)}
.stub{position:absolute;left:0;top:0;bottom:0;width:54px;border-right:2px solid rgba(21,23,28,.35)}
.rivet{position:absolute;left:5px;width:8px;height:8px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#ffe29a,#d9a441 55%,#8a5f1c);border:1.5px solid #15171c}
.notch{position:absolute;left:46px;width:16px;height:16px;border-radius:50%;background:#15171c}
.perf{position:absolute;left:57px;width:4px;height:4px;border-radius:50%;background:#15171c;opacity:.8}
.med{position:absolute;left:8px;width:42px;height:42px;border-radius:50%;background:#15171c;display:flex;align-items:center;justify-content:center}
.med .ring{width:38px;height:38px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#ffe29a,#d9a441 55%,#8a5f1c);display:flex;align-items:center;justify-content:center}
.med .disc{width:31px;height:31px;border-radius:50%;background:#f7edd3;display:flex;align-items:center;justify-content:center}
.med svg{width:28px;height:28px}
.t.c .med{width:30px;height:30px;left:13px}.t.c .med .ring{width:29px;height:29px}.t.c .med .disc{width:23px;height:23px}.t.c .med svg{width:21px;height:21px}
.title{position:absolute;left:68px;top:5px;font-family:'Luckiest Guy',cursive;font-size:20px;line-height:24px;color:#15171c;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;letter-spacing:.3px}
.t.c .title{top:3px;font-size:18px;line-height:22px}
.body{position:absolute;left:68px;top:30px;font-weight:700;font-size:13.5px;line-height:17px;color:#463c2e;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar{position:absolute;left:68px;bottom:6px;height:5px;border-radius:3px;background:rgba(21,23,28,.16);overflow:hidden}
.bar b{display:block;height:100%;border-radius:3px}
.t.c .bar{bottom:5px}
.stamp{position:absolute;right:10px;top:11px;min-width:62px;height:34px;padding:0 6px;border-radius:6px;transform:rotate(-8deg);
 font-family:'Luckiest Guy',cursive;font-size:22px;line-height:30px;text-align:center;background:rgba(247,237,211,.9);border:3px double currentColor}
.t.c .stamp{top:3px;height:26px;min-width:50px;font-size:17px;line-height:20px}
.halo{position:absolute;left:-7px;right:-7px;top:0;bottom:0;border-radius:18px;background:#15171c}
.halo:after{content:"";position:absolute;inset:3px;border-radius:15px;background:#e23a2e;opacity:.9}
.badge{position:absolute;right:-8px;top:-10px;min-width:26px;height:26px;padding:0 5px;border-radius:13px;background:#15171c;border:2px solid #d9a441;
 color:#ffe29a;font-family:'Luckiest Guy',cursive;font-size:17px;line-height:23px;text-align:center}
.more{position:absolute;right:300px;top:6px;white-space:nowrap;padding:3px 10px 2px;border-radius:12px;background:#15171c;border:2px solid #d9a441;color:#ffe29a;font-family:'Luckiest Guy',cursive;font-size:16px;line-height:18px}
.lb{position:absolute;top:44px;right:12px;width:176px;border-radius:10px;background:rgba(18,18,21,.72);color:#f7edd3;padding:8px 10px;font-size:13px;font-weight:700}
.lb .h{display:flex;justify-content:space-between;font-family:'Luckiest Guy';font-size:15px;color:#ffe29a;margin-bottom:4px}
.lb .r{display:flex;justify-content:space-between;line-height:19px}
.kit{background:#4d5d61;padding:28px 32px;color:#f7edd3}
.kit h1{font-family:'Luckiest Guy';font-size:34px;color:#ffe29a;letter-spacing:.5px}
.kit h2{font-family:'Luckiest Guy';font-size:20px;color:#ffe29a;margin:18px 0 4px}
.kit p.n{font-size:13px;font-weight:600;color:#f7edd3;margin-bottom:10px;max-width:880px}
.kit .row{display:flex;flex-wrap:wrap;gap:22px 26px;align-items:flex-end}
.kit .cap{font-size:12px;font-weight:700;color:#dfe4ea;margin-top:6px}
@keyframes rrshake{0%,100%{transform:translateX(0)}20%{transform:translateX(-5px)}40%{transform:translateX(5px)}60%{transform:translateX(-4px)}80%{transform:translateX(3px)}}
"""

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;")

def ticket(tp, compact=False, name="Maya", life=0.6, value=None, merge=None, sticky=False):
    kind, icon, title, body, stamp = TYPES[tp]
    k = KINDS[kind]; body = body.replace("{name}", name); stamp = value or stamp
    crisis = kind == "danger"
    H = 40 if compact else 64
    ndots = 3 if compact else 6
    perf = "".join(f'<i class="perf" style="top:{int(9 + i * (H - 26) / (ndots - 1))}px"></i>' for i in range(ndots))
    wtext = 212 - (74 if stamp else 0)
    med_top = (H - 6 - (30 if compact else 42)) // 2
    parts = [f'<div class="shadow"></div><div class="frame"></div><div class="card">',
             f'<div class="stub" style="background:{k["stub"]}"></div>',
             f'<i class="rivet" style="top:4px"></i><i class="rivet" style="bottom:4px"></i>',
             f'<div class="med" style="top:{med_top}px"><div class="ring"><div class="disc"><svg viewBox="0 0 64 64">{ICONS[icon]}</svg></div></div></div>',
             f'<div class="title" style="width:{wtext}px">{esc(title)}</div>']
    if not compact:
        parts.append(f'<div class="body" style="width:{wtext}px">{esc(body)}</div>')
    if not sticky:
        parts.append(f'<div class="bar" style="width:{wtext if compact else 212}px"><b style="width:{int(life*100)}%;background:{k["bar"]}"></b></div>')
    if stamp:
        parts.append(f'<div class="stamp" style="color:{k["stamp"]}">{esc(stamp)}</div>')
    parts.append('</div>')
    parts.append(f'<i class="notch" style="top:-8px"></i><i class="notch" style="top:{H-8}px"></i>')
    parts.append(perf.replace('class="perf"', 'class="perf"'))
    if merge: parts.append(f'<div class="badge">{merge}</div>')
    inner = f'<div class="t{" c" if compact else ""}" aria-label="{esc(title)}">{"".join(parts)}</div>'
    if crisis:
        return f'<div class="slot crisis"><div class="halo" style="top:0;bottom:0"></div>{inner}</div>'
    return f'<div class="slot">{inner}</div>'

HEAD = '<!doctype html><html><head><meta charset="utf-8"><title>{t}</title><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Luckiest+Guy&family=Montserrat:wght@600;700;800&display=swap"><style>' + CSS + '</style></head><body>'

def scene(w, h, stack_html, scale=1.0, right=16, bottom=128, pc=False):
    zones = ""
    if not pc:
        zones = ('<div class="zone" style="left:34px;bottom:30px;width:120px;height:120px"></div>'
                 '<div class="zone" style="right:30px;bottom:26px;width:86px;height:86px"></div>')
    tb = '<div class="topbar"><i style="left:8px"></i><i style="left:44px"></i></div>'
    lb = ""
    if pc:
        lb = ('<div class="lb"><div class="h"><span>People</span><span>Cash</span></div>' + "".join(
            f'<div class="r"><span>{n}</span><span>{c}</span></div>' for n, c in
            [("JoelRails", "$340"), ("MayaChoo", "$210"), ("Tinkerbolt", "$95"), ("Jin_Loco", "$60")]) + '</div>')
    return (f'<div class="scene" style="width:{w}px;height:{h}px"><div class="hill"></div><div class="hill b"></div>'
            f'<div class="sleepers"></div><div class="rail a"></div><div class="rail b"></div><div class="train"></div>'
            f'{tb}{zones}{lb}<div class="stack" style="right:{right}px;bottom:{bottom}px;transform:scale({scale})">{stack_html}</div></div>')

def board(fname, title, w, h, stack, pc=False):
    sc = 1.16 if pc else 1.0
    html = HEAD.replace("{t}", title) + scene(w, h, stack, scale=sc, right=18.56 if pc else 14, bottom=127.6 if pc else 112, pc=pc) + '</body></html>'
    open(os.path.join(P, fname), "w").write(html)

C = lambda *a, **k: ticket(*a, compact=True, **k)
BOARDS = {}
# newest at bottom
BOARDS["Phone.html"] = ("Phone - crisis at bottom", 844, 390, C("FareBanked", life=.3) + C("JunctionAhead", life=.5) + ticket("CrewJoined", name="MayaChoo", life=.7) + ticket("CoalLow", life=.9))
BOARDS["PhoneRoutine.html"] = ("Phone - three routine tickets", 844, 390, C("CrateLanded", life=.3) + C("CrewLeft", life=.5, name="Tinkerbolt") + ticket("FareBanked", value="$200", merge=3, life=.9))
BOARDS["PhoneCrises.html"] = ("Phone - two crises + junction", 844, 390, C("PressureHigh", sticky=True) + C("Breakdown", life=.5) + ticket("JunctionAhead", life=.8))
BOARDS["PhoneOverflow.html"] = ("Phone - four crises, +1 more", 844, 390, '<div class="more">+1 MORE</div>' + C("PassengersUpset", sticky=True) + C("Breakdown", life=.4) + C("PressureHigh", life=.6) + ticket("CoalLow", life=.95))
BOARDS["PC.html"] = ("PC 1280x720", 1280, 720, C("RiskyRoute", life=.4) + C("CrewJoined", life=.6, name="Jin_Loco") + ticket("FareBanked", value="$12K", merge=2, life=.5) + ticket("Breakdown", life=.9))
for f, (t, w, h, s) in BOARDS.items():
    board(f, t, w, h, s, pc=f.startswith("PC"))

# kit
row = lambda items: '<div class="row">' + "".join(f'<div>{x}<div class="cap">{c}</div></div>' for x, c in items) + '</div>'
kit = [HEAD.replace("{t}", "Kit"), '<div class="kit" style="width:1400px;height:1180px"><h1>RISKY RAILS - TICKET NOTIFICATIONS</h1>',
 '<p class="n">Railway-company ticket: soot-iron frame, brass-riveted enamel stub, punched notches + perforation, brass medallion, rubber-stamp values. Newest at the bottom, max 4 shown.</p>',
 '<h2>CRISIS - red stub, ink + red halo, one shake on arrival</h2>', row([(ticket(t), t) for t in ["CoalLow", "PressureHigh", "Breakdown", "PassengersUpset"]]),
 '<h2>JUNCTION &amp; RISK - hazard stub</h2>', row([(ticket("JunctionAhead"), "JunctionAhead"), (ticket("RiskyRoute"), "RiskyRoute - stamp X2")]),
 '<h2>CASH - green stub, value stamp, merges</h2>', row([(ticket("FareBanked"), "FareBanked $120"), (ticket("FareBanked", value="$160", merge=2), "merged x2 (+$40 each)"), (ticket("FareBanked", value="$12K", merge=9), "$12,000 shows $12K")]),
 '<h2>CREW &amp; INFO - teal stub</h2>', row([(ticket("CrateLanded"), "CrateLanded"), (ticket("CrewJoined", name="MayaChoo"), "CrewJoined"), (ticket("CrewLeft", name="Tinkerbolt"), "CrewLeft (names cap 10 chars)")]),
 '<h2>OLDER TICKETS GO COMPACT - newest + newest crisis stay full</h2>', row([(C("CoalLow"), "compact crisis keeps halo"), (C("JunctionAhead"), "compact risk"), (C("FareBanked"), "compact cash"), (C("CrewJoined"), "compact info"), (C("Breakdown", sticky=True), "sticky: no bar, stays until fixed")]),
 '<h2>MOTION</h2><p class="n">Enter: slide in from the right (125%) + fade, 0.28s back-out. Leave: slide right + fade, removed after 0.32s. Crisis: one 0.5s shake (+/-5px, 0.35s delay) and halo pulse 0.3-0.95 opacity, 1.2s loop. Merge: stamp and badge bump 1.07 to 1, 0.32s. Life bar drains left over the ticket life (danger 7s, risk 6s, cash 4.5s, info 5s). Over the cap routine tickets leave first; sticky crises are never pushed off; overflow shows "+N MORE".</p>',
 '<div class="row"><div style="position:relative;width:380px;height:40px"><div class="more" style="left:0;right:auto">+1 MORE</div></div></div></div></body></html>']
open(os.path.join(P, "Kit.html"), "w").write("".join(kit))
canvas = {"order": ["Phone.html", "PhoneRoutine.html", "PhoneCrises.html", "PhoneOverflow.html", "PC.html", "Kit.html"],
          "boards": {f: {"w": w, "h": h} for f, (t, w, h, s) in BOARDS.items()}}
canvas["boards"]["Kit.html"] = {"w": 1400, "h": 1180}
json.dump(canvas, open(os.path.join(P, "canvas.json"), "w"), indent=1)
json.dump({"tokens": T, "kinds": KINDS, "types": TYPES}, open(os.path.join(HERE, "tokens.json"), "w"), indent=1)
print("boards:", ", ".join(canvas["order"]))
