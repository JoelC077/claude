#!/usr/bin/env python3
"""pack_pov.py: POV composites for the trial preset pack (workaround: preview.py's POV_SETS are hard-coded).

Usage: RR_VFX_PRESETS=<presets> python3 pack_pov.py --plates <preview>/lighting --out <preview>/pack [--skill <rr-vfx-lighting dir>]
Composites the pack's loop effects (plus the look's fx_on presets) over each lookdev plate with fxsim.pov and
writes pov_*.png + pov.json (live, overdraw, screen covered). Previews, not Roblox.
"""
import argparse, glob, json, os, sys
from pathlib import Path

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--plates", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--skill", help="rr-vfx-lighting folder (default: found by glob)")
a = ap.parse_args()
skill = a.skill or next((os.path.dirname(p) for pat in ("~/.claude/skills/**/rr-vfx-lighting/SKILL.md", "/home/user/**/rr-vfx-lighting/SKILL.md")
                         for p in glob.glob(os.path.expanduser(pat), recursive=True) if "/trials/" not in p), None)
if not skill:
    sys.exit("rr-vfx-lighting not found: pass --skill")
sys.path.insert(0, os.path.join(skill, "scripts"))
import vfx, fxsim  # noqa: E402

PACK = ["steam_chimney", "smoke_chimney", "sparks_brake"]  # coal_dust sits inside the cab: no preview camera sees it
model = vfx.Model()
P, O = Path(a.plates), Path(a.out)
O.mkdir(parents=True, exist_ok=True)
res = []
for look in ("grassland.day", "grassland.dusk", "grassland.night"):
    extra = [n for n in model.resolve_look(look)["fx_on"] if n in model.presets]
    for cam, tier, suffix in (("", "pc", ""), ("@door1p", "pc", ""), ("", "phone", ".phone")):
        slug = (look + cam).replace("@", "_")
        vj = P / f"view_{slug}.json"
        plate = P / f"{slug}{suffix}.png"
        if not (vj.is_file() and plate.is_file()):
            continue
        out = O / f"pov_{slug}{suffix}.png"
        r = fxsim.pov(model, PACK + extra, vj, out, plate=plate, tier=tier)
        r.update(look=look, camera=cam.strip("@") or "roof3p", tier=tier)
        res.append(r)
        print(f"{out.name}: live {r['live']}, overdraw max {r['overdraw_max']}, covered {r['screen_covered']*100:.1f}%")
(O / "pov.json").write_text(json.dumps(res, indent=1))
