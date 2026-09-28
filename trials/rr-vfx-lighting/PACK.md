# Risky Rails preset pack: steam, smoke, brake sparks, coal dust + day, dusk, night run

Studio test pending (owner). Everything below is preview-only: nothing has run in Roblox.

| preset | kind | priority | where | wire it |
|---|---|---|---|---|
| steam_chimney | loop | 2 feedback | Chimney | `VFX.attach(chimney, "steam_chimney")`; rate follows `VFX.setSpeed` |
| smoke_chimney | loop | 3 ambience | Chimney | `VFX.attach(chimney, "smoke_chimney")`; cut first on phones |
| sparks_brake (new) | loop | 2 feedback | BrakeShoe = right driving wheel at the rail; left fan offset 8.4 across | `VFX.attach(brakeShoe, "sparks_brake", {enabled = false})`, then `VFX.setActive("sparks_brake", braking)`; rate falls with Speed, so the sparks die away as the train stops |
| coal_dust | burst | 2 feedback | Firebox | `VFX.burst(firebox, "coal_dust")` on each shovel |

| look | use | status |
|---|---|---|
| `Lighting.apply("grassland.day")` | default running look | canon values (tech.lighting.*) |
| `Lighting.apply("grassland.dusk")` (new) | sun on the horizon, headlamp on | assumed (OQ-026 default C): no slot in the run yet; fits option B's end state or an evening modifier |
| `Lighting.apply("grassland.night")` | Night Running modifier, headlamp on | modifier is proposed canon (gameplay.modifiers.hard_pool) |

Files: `export/` (Luau: `RR_FXPresets.lua`, `RR_LightingPresets.lua`, `RR_VFX.lua`, `RR_Lighting.lua`,
`RR_FXDemo.client.lua`, `studio_lighting_setup.lua`, README), `src/fx/*.json` (source of truth; the export holds the
whole library with the pack inside), `preview/board/contact.png` (look-dev board), `preview/vfx/anim_*.gif` (motion).

Phone budget (assumed, OQ-029 default): pressure brake with valve + shovelling = 147 peak particles of 800; worst
crisis stack plus brakes = 197 of 800, 10 of 12 emitters. All sets within on phone and PC.

Known from the previews: from a coach roof (roof3p) the train hides the wheel-level brake sparks; players at a
doorway see them. Coal dust happens inside the cab, which no preview camera shows.

Needs owner: brake sparks have no canon (proposed question: sparks while braking, default A, not recorded: trial
run); whether dusk gets a slot (OQ-026); custom spark and smoke flipbooks (asset upload is the owner's).
