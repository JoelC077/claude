-- WagonFlatCrates (rr-asset-foundry wagon, preset flat_crates). Studio command bar, model selected.
-- Collision: box proxies (Collider_Proxy parts) collide; visual parts do not.
-- Recolour: edit one GROUPS line and re-run. KEEP_ATLAS = true keeps the _atlas.fbx texture (Color is then hidden).
-- Paste into Studio's command bar. Select the imported model, or name it "WagonFlatCrates" in Workspace.
local root = game.Selection:Get()[1] or workspace:FindFirstChild("WagonFlatCrates")
assert(root, "select the imported model first")
local default = {Anchored = true, CanCollide = false, CastShadow = true}
local rules = {
  {"_Collider_Proxy_", {Transparency = 1, CanCollide = true, CastShadow = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"_Lod1_", {CanCollide = false, CastShadow = false}},
  {"_LadderRung_", {CanCollide = true, CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition}},
}
local n = 0
for _, p in ipairs(root:GetDescendants()) do
  if p:IsA("BasePart") then
    for k, v in pairs(default) do p[k] = v end
    for _, r in ipairs(rules) do
      if p.Name:match(r[1]) then for k, v in pairs(r[2]) do p[k] = v end end
    end
    n += 1
  end
end
print(("setup done: %d parts"):format(n))

local KEEP_ATLAS = false
local GROUPS = {
  Chassis = {color = Color3.fromHex("15181B"), material = Enum.Material.Metal}, -- style.world.soot_black
  Steel = {color = Color3.fromHex("8A929B"), material = Enum.Material.Metal}, -- style.thumb.steel
  Buffer = {color = Color3.fromHex("C9412E"), material = Enum.Material.SmoothPlastic}, -- style.brand.buffer_red
  Iron = {color = Color3.fromHex("363A42"), material = Enum.Material.Metal}, -- style.world.ironwork
  Timber = {color = Color3.fromHex("8F5A2A"), material = Enum.Material.WoodPlanks}, -- style.depot_kit.timber_dark
  Crate = {color = Color3.fromHex("B27A3F"), material = Enum.Material.WoodPlanks}, -- style.thumb.crate
  Patch = {color = Color3.fromHex("B1502B"), material = Enum.Material.CorrodedMetal}, -- style.depot_kit.red_oxide
}
local recoloured = 0
for _, p in ipairs(root:GetDescendants()) do
  if p:IsA("BasePart") then
    local g = GROUPS[(p.Name:split("_")[3] or "")]
    if g then
      if p:IsA("MeshPart") and not KEEP_ATLAS then p.TextureID = "" end
      if not KEEP_ATLAS then p.Color = g.color end
      p.Material = g.material
      if g.reflectance then p.Reflectance = g.reflectance end
      recoloured += 1
    end
  end
end
print(("recolour groups applied to %d parts"):format(recoloured))
