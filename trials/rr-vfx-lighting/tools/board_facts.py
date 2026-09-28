#!/usr/bin/env python3
"""board_facts.py: one facts.md for the combined look-dev board (workaround: the skill writes lighting and vfx facts separately).

Usage: python3 board_facts.py --preview <preview dir> --out <board>/facts.md --sets cruise,arrival_brake,...
Pulls the lighting table and effect rows from <preview>/lighting|vfx/facts.md, the pack POV numbers from
<preview>/pack/pov.json, and the phone budget lines for the named sets.
"""
import argparse, json, re
from pathlib import Path
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--preview", required=True); ap.add_argument("--out", required=True); ap.add_argument("--sets", required=True)
a = ap.parse_args()
P = Path(a.preview)
L = (P / "lighting/facts.md").read_text().splitlines()
V = (P / "vfx/facts.md").read_text().splitlines()
pov = json.loads((P / "pack/pov.json").read_text())
sets = a.sets.split(",")
out = ["# Look-dev board facts: pack = steam_chimney, smoke_chimney, sparks_brake, coal_dust; looks grassland.day, .dusk, .night", ""]
out += [l for l in L[2:] if not l.startswith("Limits")]
out += ["", "## Effects (side strips at Speed 35; phone live uses the budget formula at full rate)", ""]
tab = [l for l in V if l.startswith("|")]
out += tab[:2] + [l for l in tab[2:] if l.split("|")[1].strip() in ("steam_chimney", "smoke_chimney", "sparks_brake", "coal_dust")]
out += ["", "## Pack POV composites (Speed = gameplay.speed.fast 50; loops at steady state; the look's fx_on presets added)", "",
        "| composite | tier | live | hidden by geometry | overdraw max | screen covered |", "|---|---|---|---|---|---|"]
for r in pov:
    out.append(f"| {Path(r['out']).stem} | {r['tier']} | {r['live']} | {r['hidden_by_depth']} | {r['overdraw_max']} | {r['screen_covered']*100:.1f}% |")
out += ["", "- coal_dust fires inside the cab (anchor Firebox): no preview camera is in the cab, so it appears only in its time strip.",
        "- sparks_brake sits at the loco wheels at rail level: from coach B's roof (roof3p) the train body hides it; door1p sees about half.", "",
        "## Phone budget, pack-relevant sets (all PC sets within)", ""]
out += [l for l in V if l.startswith("- phone ") and l.split()[2].rstrip(":") in sets]
out += ["", next(l for l in L if l.startswith("Limits")), next(l for l in V if l.startswith("Limits"))]
Path(a.out).write_text("\n".join(out) + "\n")
print(f"wrote {a.out} ({len(out)} lines)")
