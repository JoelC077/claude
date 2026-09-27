-- Paste into Studio's command bar. Select the imported model, or name it "Depot" in Workspace.
local root = game.Selection:Get()[1] or workspace:FindFirstChild("Depot")
assert(root, "select the imported model first")
local default = {Anchored = true, CanCollide = true, CastShadow = true}
local rules = {
  {"^Depot_[^_]*Gutter", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Downpipe", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Ivy", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Moss", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Barge", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Finial", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Vent", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Soot", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Ashlar", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Quoin", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*StepNosing", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Win", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Roundel", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Keystone", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Cupola", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Canopy", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*NameBoard", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Interior", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Lamp", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Ridge", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*String", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*BellCote", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Notice", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*SideLamp", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
  {"^Depot_[^_]*Edge", {CanCollide = false, CollisionFidelity = Enum.CollisionFidelity.Box}},
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

-- RECOLOUR: edit one line per group (TextureID is cleared so Color shows).
local GROUPS = {
  Brass = {color = Color3.fromHex("b08a3e"), material = Enum.Material.Metal},
  Brick = {color = Color3.fromHex("8a4b36"), material = Enum.Material.Brick},
  Cream = {color = Color3.fromHex("efe2bd"), material = Enum.Material.SmoothPlastic},
  Creamdk = {color = Color3.fromHex("d2c290"), material = Enum.Material.SmoothPlastic},
  Dark = {color = Color3.fromHex("1f2a33"), material = Enum.Material.SmoothPlastic},
  Door = {color = Color3.fromHex("b1502b"), material = Enum.Material.Wood},
  Glow = {color = Color3.fromHex("e8c46a"), material = Enum.Material.Neon},
  Gravel = {color = Color3.fromHex("b7a17a"), material = Enum.Material.Pebble},
  Hazard = {color = Color3.fromHex("f2c230"), material = Enum.Material.SmoothPlastic},
  Ink = {color = Color3.fromHex("15171c"), material = Enum.Material.SmoothPlastic},
  Iron = {color = Color3.fromHex("2b2f36"), material = Enum.Material.Metal},
  Mortar = {color = Color3.fromHex("cabb8a"), material = Enum.Material.Concrete},
  Moss = {color = Color3.fromHex("6d7d43"), material = Enum.Material.Grass},
  Pavingdk = {color = Color3.fromHex("cfc9b9"), material = Enum.Material.Concrete},
  Slatedk = {color = Color3.fromHex("2f333a"), material = Enum.Material.Slate},
  Soot = {color = Color3.fromHex("3a3f48"), material = Enum.Material.Slate},
  Stonedark = {color = Color3.fromHex("7d776b"), material = Enum.Material.Slate},
  Stonelt = {color = Color3.fromHex("aca595"), material = Enum.Material.Slate},
  Stonewm = {color = Color3.fromHex("b6ab90"), material = Enum.Material.Slate},
  Teal = {color = Color3.fromHex("2e7d7a"), material = Enum.Material.Wood},
  Timber = {color = Color3.fromHex("8f5a2a"), material = Enum.Material.Wood},
  Timberlt = {color = Color3.fromHex("b87a3d"), material = Enum.Material.WoodPlanks},
}
for _, p in ipairs(root:GetDescendants()) do
  if p:IsA("BasePart") then
    local g = GROUPS[(p.Name:split("_")[3] or "")]
    if g then
      if p:IsA("MeshPart") then p.TextureID = "" end
      p.Color = g.color; p.Material = g.material
    end
  end
end
print("recolour groups applied")
