#!/usr/bin/env python3
"""Tile every view of one pass into a single contact sheet the critic reads as one image.

python3 contact_sheet.py OUT.png "Label=path@1" "Label=path" ... [--tile 400x225] [--max-width 1568] [--max-mp 1.15]

  Label=path@1   pasted at true size in the top band: POV frames, the 400 px game-distance render,
                 a real-size UI frame. That's what the player sees, so it is never scaled.
  Label=path     fitted into a --tile cell in the grid below: construction views, boards, close-ups.

Writes OUT.png and OUT.json (each tile's label, source, box and scale); critic_kit.py turns the JSON into
the Images list in critic.md. The image reader shrinks anything over ~1.15 MP or 1568 px on the long
side, and a shrunk sheet stops being 1:1, so an oversized sheet is a warning and exit code 2.
"""
import argparse, json, os, sys
from PIL import Image, ImageDraw, ImageFont

LABEL_H, GAP, BG, CELL, INK = 18, 6, (32, 32, 36), (90, 90, 96), (235, 235, 235)


def font():
    try:
        return ImageFont.load_default(size=13)
    except TypeError:   # Pillow < 10.1
        return ImageFont.load_default()


def parse(spec):
    label, _, rest = spec.partition("=")
    if not rest:
        sys.exit(f"bad item {spec!r}: use Label=path or Label=path@1")
    true_size = rest.endswith("@1")
    path = rest[:-2] if true_size else rest
    if not os.path.isfile(path):
        sys.exit(f"missing image: {path}")
    return {"label": label.strip(), "src": path, "true": true_size, "img": Image.open(path).convert("RGB")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("items", nargs="+")
    ap.add_argument("--tile", default="400x225")
    ap.add_argument("--max-width", type=int, default=1568)
    ap.add_argument("--max-mp", type=float, default=1.15)
    a = ap.parse_args()
    tw, th = (int(v) for v in a.tile.lower().split("x"))
    items = [parse(s) for s in a.items]
    band = [it for it in items if it["true"]]
    grid = [it for it in items if not it["true"]]

    widest = max([it["img"].width for it in band] + [0])
    if widest + 2 * GAP > a.max_width:
        sys.exit(f"a true-size view is {widest}px wide; render it at most {a.max_width - 2 * GAP}px wide")

    def layout(W):
        placed = []   # (item, label_x, label_y, img_x, img_y, w, h, scale, cell or None)
        x, y, shelf = GAP, GAP, 0
        for it in band:                               # shelf-pack true-size views, left to right
            w, h = it["img"].size
            if x > GAP and x + w + GAP > W:
                x, y, shelf = GAP, y + LABEL_H + shelf + GAP, 0
            placed.append((it, x, y, x, y + LABEL_H, w, h, 1.0, None))
            x, shelf = x + w + GAP, max(shelf, h)
        top = y + LABEL_H + shelf + GAP if band else GAP
        cols = max(1, (W - GAP) // (tw + GAP))
        for i, it in enumerate(grid):                 # then the fitted grid
            r, c = divmod(i, cols)
            cx, cy = GAP + c * (tw + GAP), top + r * (LABEL_H + th + GAP)
            s = min(tw / it["img"].width, th / it["img"].height, 1.0)
            w, h = max(1, round(it["img"].width * s)), max(1, round(it["img"].height * s))
            placed.append((it, cx, cy, cx + (tw - w) // 2, cy + LABEL_H + (th - h) // 2, w, h, s, (cx, cy + LABEL_H, tw, th)))
        H = max((cell[1] + cell[3] if cell else iy + h) for _, _, _, _, iy, _, h, _, cell in placed) + GAP
        used = max((cell[0] + cell[2] if cell else ix + w) for _, _, _, ix, _, w, _, _, cell in placed) + GAP
        return placed, used, H

    # Try every width that changes the packing and keep the smallest sheet: that's what the MP budget counts.
    widths = {widest + 2 * GAP, GAP + sum(it["img"].width + GAP for it in band)}
    widths |= {GAP + c * (tw + GAP) for c in range(1, len(grid) + 1)}
    widths = sorted(w for w in widths if w <= a.max_width) or [a.max_width]
    placed, W, H = min((layout(w) for w in widths), key=lambda p: (p[1] * p[2], p[2]))

    sheet = Image.new("RGB", (W, H), BG)
    d, f = ImageDraw.Draw(sheet), font()
    tiles = []
    for n, (it, lx, ly, ix, iy, w, h, s, cell) in enumerate(placed, 1):
        if cell:
            d.rectangle([cell[0], cell[1], cell[0] + cell[2] - 1, cell[1] + cell[3] - 1], fill=CELL)
        sheet.paste(it["img"] if s == 1.0 else it["img"].resize((w, h), Image.LANCZOS), (ix, iy))
        scale = "1:1 true size" if it["true"] else f"fit x{s:.2f}"
        d.text((lx + 2, ly + 2), f"{n}. {it['label']}  ({scale})", fill=INK, font=f)
        tiles.append({"n": n, "label": it["label"], "src": os.path.abspath(it["src"]),
                      "box": [ix, iy, w, h], "scale": scale})
    sheet.save(a.out)
    mp = W * H / 1e6
    json.dump({"sheet": [W, H], "megapixels": round(mp, 2), "tiles": tiles},
              open(os.path.splitext(a.out)[0] + ".json", "w"), indent=1)
    print(f"{a.out}: {W}x{H} ({mp:.2f} MP), {len(tiles)} tiles")
    for t in tiles:
        print(f"  {t['n']}. {t['label']} ({t['scale']})")
    if mp > a.max_mp or max(W, H) > a.max_width:
        print(f"WARNING: over {a.max_mp} MP or {a.max_width}px on a side, so the reader will shrink it and the 1:1 tiles "
              "won't be 1:1. Use a smaller --tile, drop grid views, or move close-ups to a second image.")
        sys.exit(2)


if __name__ == "__main__":
    main()
