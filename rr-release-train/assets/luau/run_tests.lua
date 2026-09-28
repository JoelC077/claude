-- run_tests.lua (rr-release-train). Runs the place's spec modules and checks the RR_Version stamp.
-- Where: Open Cloud Luau Execution on a SAVED place version (release.py publish --live does this before
-- publishing), or paste into Studio's command bar (Play Solo, Server view) for the owner's own run: the
-- "[RR tests]" lines in Output are the result.
-- Specs: any ModuleScript whose Name ends in ".spec" under ServerScriptService, ServerStorage or
-- ReplicatedStorage. It returns either a function (one test) or a table of name -> function.
-- A test passes when it returns without error; use assert(). Returns one JSON-able table.
-- release.py replaces the EXPECTED line below; in Studio leave it and read `version` in the output.
-- LIVE DATA: on Open Cloud this runs in the production universe, where DataStores are the real ones. Specs must
-- not call DataStoreService/ProfileStore/MessagingService/MemoryStoreService; data modules should check
-- _G.RR_RELEASE_TEST and stub themselves while it is true (release gate G6 fails a spec that names them).
local EXPECTED = "{{EXPECTED_VERSION}}"
_G.RR_RELEASE_TEST = true

local result = { expected = EXPECTED, version = nil, specs = 0, tests = 0, passed = 0, failed = 0, failures = {} }

local function fail(where, err)
	result.failed = result.failed + 1
	if #result.failures < 25 then
		table.insert(result.failures, where .. ": " .. string.sub(tostring(err), 1, 300))
	end
end

local stamp = game:GetService("ReplicatedStorage"):FindFirstChild("RR_Version")
if stamp and stamp:IsA("ModuleScript") then
	local ok, v = pcall(require, stamp)
	if ok and type(v) == "table" then
		result.version = v.version
		result.channel = v.channel
	else
		fail("RR_Version", ok and "did not return a table" or v)
	end
end

for _, serviceName in ipairs({ "ServerScriptService", "ServerStorage", "ReplicatedStorage" }) do
	local service = game:GetService(serviceName)
	for _, inst in ipairs(service:GetDescendants()) do
		if inst:IsA("ModuleScript") and string.sub(inst.Name, -5) == ".spec" then
			result.specs = result.specs + 1
			local where = serviceName .. "." .. inst.Name
			local ok, spec = pcall(require, inst)
			if not ok then
				fail(where .. " (require)", spec)
			elseif type(spec) == "function" then
				result.tests = result.tests + 1
				local okRun, err = pcall(spec)
				if okRun then result.passed = result.passed + 1 else fail(where, err) end
			elseif type(spec) == "table" then
				local names = {}
				for name, fn in pairs(spec) do
					if type(fn) == "function" then table.insert(names, tostring(name)) end
				end
				table.sort(names)
				for _, name in ipairs(names) do
					result.tests = result.tests + 1
					local okRun, err = pcall(spec[name])
					if okRun then result.passed = result.passed + 1 else fail(where .. " > " .. name, err) end
				end
			else
				fail(where, "returned " .. type(spec) .. ", expected a function or a table of functions")
			end
		end
	end
end

_G.RR_RELEASE_TEST = nil
local versionOk = (EXPECTED == "{{" .. "EXPECTED_VERSION}}") or (result.version == EXPECTED)
result.versionOk = versionOk
result.ok = versionOk and result.failed == 0
print(string.format("[RR tests] %s | version %s (expected %s) | %d tests, %d passed, %d failed",
	result.ok and "PASS" or "FAIL", tostring(result.version), EXPECTED, result.tests, result.passed, result.failed))
for _, f in ipairs(result.failures) do print("[RR tests] " .. f) end
return result
