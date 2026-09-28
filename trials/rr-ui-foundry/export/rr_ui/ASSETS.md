# Assets to upload (owner)

Nothing was uploaded. Upload each image in Studio (Asset Manager > Import, or Creator Hub), then write the ids
into `asset_ids.json` in this folder, e.g. {"iconSheet": "rbxassetid://123", "hazardTile": "rbxassetid://456"},
and run ui.py build again (or pass --assets FILE); the ids then survive every rebuild.

| file | key in asset_ids.json | notes |
|---|---|---|
| icons/rr_ui_icons.png | `assets.iconSheet` | 12 white icons; icons.json has each ImageRectOffset/Size (already in the theme); ImageColor3 tints them |
| icons/rr_hazard_tile.png | `assets.hazardTile` | 32 px hazard stripe tile, ScaleType Tile at 16 px |

Until an id is set the kit shows the icon's fallback (blank medallion) and the risk stub without stripes;
gamepad glyphs come from UserInputService:GetImageForKeyCode at run time (no upload).
