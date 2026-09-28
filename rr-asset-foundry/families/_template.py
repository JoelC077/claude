"""TemplateName family: one line on what it makes and how it reads in game.
Frame: x = length, y = depth (front faces -y), z up, z = 0 ground (rolling stock and track: z = 0 rail top).
Rules: references/families.md. Colours are rr-bible token keys; numbers that canon holds are '@key' defaults."""
import fkit                      # frame_boxes, arc, arc_z, shell (geometry helpers; k.* makes the parts)

FAMILY = "TEMPLATE_NAME"
DESC = "What the family makes, in one sentence (list shows it)."
TAGS = ["TEMPLATE_NAME"]         # words a request would use; `foundry.py list --match` searches them
OPEN = []                        # rr-bible open questions that label every output of this family (e.g. "OQ-025")
PARAMS = {                       # name: (type, default, min, max, help) | ("choice", default, [..], help) | ("bool", default, help)
    "width": ("float", 8.0, 2, 40, "x size, studs"),
    "depth": ("float", 6.0, 2, 40, "y size, studs"),
    "height": ("float", 5.0, 1, 30, "z size, studs"),
    "door_w": ("float", "@tech.units.building_door#0", 4, 12, "an example of a canon default: read, never restated"),
}
GROUPS = {                       # recolour group: (rr-bible colour token, Roblox Material[, Reflectance])
    "Body": ("style.depot_kit.stone", "Slate"),
    "Trim": ("style.depot_kit.iron", "Metal"),
}
PRESETS = {"base": {"params": {}, "note": "the default variant"}}
DEFAULT_PRESET = "base"
VIEW = {"ground": "style.lobby.concrete",              # stage ground token
        "features": ["Trim"],                          # part names measured at game distance (>= style.line.min_feature_px)
        "player": "Where the player stands and how the thing is seen (goes into the critic brief)."}
OPTIONS = {"merge": "none", "collide": True, "lod": False}


def validate(p, canon):
    """Plan-time warnings; canon(key) returns a number from rr-bible."""
    return []


def build(k, p):
    W, D, H = p["width"], p["depth"], p["height"]
    k.box("Block", "Body", (0, 0, H / 2), (W, D, H))
    k.box("Cap", "Trim", (0, 0, H + 0.15), (W + 0.4, D + 0.4, 0.3))          # overlaps, never shares a face plane
    k.proxy((0, 0, (H + 0.3) / 2), (W, D, H + 0.3))
    k.measure("footprint", f"{W:g} x {D:g} studs")
