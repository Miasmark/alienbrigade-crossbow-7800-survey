-- abmodel.lua: assert the Alien Brigade display-list builder model on every build, live.
-- When the builder (f8:F56B) finishes it does INC $F3 (f8:F66D).  At that write this script
-- re-computes the lists from the draw list ($227D type, $22FF slot; $FF ends a zone, $FE = the
-- zone's tile row) and the slot arrays, and compares them byte for byte with the buffer just
-- built ($F2 = 0 -> $1AB8, else $1CB8).  Output model.txt: builds checked, exact, mismatching,
-- the largest draw list seen, and per-build stats (entries, list bytes) as a histogram.
-- Inputs as probe.lua (SCRIPT, END, POKES).
local M = manager.machine
local cpu = M.devices[":maincpu"]
local mem = cpu.spaces["program"]
local P = M.ioport.ports
local function fld(n)
  for _, t in ipairs({":JOYSTICKS", ":BUTTONS", ":joysticks", ":buttons"}) do
    local f = P[t] and P[t].fields[n]
    if f then return f end
  end
end
local stick = {l = fld("P1 Left"), r = fld("P1 Right"), u = fld("P1 Up"), d = fld("P1 Down")}
local fire = fld("P1 Button 1")
local steps = {}
for n, s, b in string.gmatch(os.getenv("SCRIPT") or "600:-:0", "(%d+):([lrud%-]+):(%d+)") do
  steps[#steps + 1] = {tonumber(n), s, tonumber(b)}
end
local total = 0
for _, s in ipairs(steps) do total = total + s[1] end
local END = tonumber(os.getenv("END") or tostring(total))
local pokes = {}
for fr, list in string.gmatch(os.getenv("POKES") or "", "(%d+):([^;]+)") do
  local t = pokes[tonumber(fr)] or {}
  for ad, val in string.gmatch(list, "(%x+)=(%x+)") do t[#t + 1] = {tonumber(ad, 16), tonumber(val, 16)} end
  pokes[tonumber(fr)] = t
end
local f = 0
local builds, exact, bad, maxent, maxbytes = 0, 0, 0, 0, 0
local hist = {}
local firstbad = {}
local r = function(a) return mem:read_u8(a) end

local function model()
  local out = {}
  local zone = 0
  for y = 0, 0x81 do
    local t = r(0x227D + y)
    if t == 0xFF then
      out[#out + 1] = 0; out[#out + 1] = 0
      zone = zone + 1
      if zone >= 10 then break end
    elseif t == 0xFE then
      out[#out + 1] = r(0x224E + zone); out[#out + 1] = 0x60; out[#out + 1] = r(0x2258 + zone)
      out[#out + 1] = r(0x2262 + zone); out[#out + 1] = (0xFF - r(0x2110)) & 255
    else
      local x = r(0x22FF + y)
      local hx
      if t == 0 and r(0xD6) == 0 then hx = 0x9F else hx = r(0x2615 + x) end
      local yy = r(0x25A7 + x)
      if yy < 0xA0 then
        local p = ((r(0x2381 + x) + r(0x24CB + x)) + (r(0x23EF + x) << 8)) & 0xFFFF
        local pw = r(p)
        if pw >= 0x10 then
          out[#out + 1] = r(p + 1); out[#out + 1] = pw
          out[#out + 1] = (r(p + 2) + (yy & 15) - (r(0x245D + x) & 0x7F)) & 255
          out[#out + 1] = hx
        end
      end
    end
  end
  return out
end

TAP = mem:install_write_tap(0x00F3, 0x00F3, "f3", function(offset, data)
  if data == 0 then return data end
  local pc = cpu.state["PC"].value
  if pc < 0xF660 or pc > 0xF672 then return data end
  local base = (r(0xF2) == 0) and 0x1AB8 or 0x1CB8
  local m = model()
  local ok = true
  for i = 1, #m do
    if r(base + i - 1) ~= m[i] then ok = false break end
  end
  builds = builds + 1
  if ok then exact = exact + 1 else
    bad = bad + 1
    if #firstbad < 5 then firstbad[#firstbad + 1] = string.format("f%d pc %04X base %04X", f, pc, base) end
  end
  local n = r(0x2114)
  if n > maxent then maxent = n end
  if #m > maxbytes then maxbytes = #m end
  local k = math.floor(n / 5) * 5
  hist[k] = (hist[k] or 0) + 1
  return data
end)

local done = false
FR = emu.register_frame_done(function()
  f = f + 1
  local t, cur = f, nil
  for _, s in ipairs(steps) do
    if t <= s[1] then cur = s break end
    t = t - s[1]
  end
  for k, fl in pairs(stick) do fl:set_value((cur and cur[2]:find(k)) and 1 or 0) end
  fire:set_value((cur and cur[3] % 2 == 1) and 1 or 0)
  local p = pokes[f]
  if p then for _, w in ipairs(p) do mem:write_u8(w[1], w[2]) end end
  if f >= END and not done then
    done = true
    local o = io.open("model.txt", "w")
    o:write(string.format("frames %d builds %d exact %d mismatching %d  max draw-list entries %d  max list bytes %d\n",
      f, builds, exact, bad, maxent, maxbytes))
    for _, l in ipairs(firstbad) do o:write("first mismatches: " .. l .. "\n") end
    local ks = {}
    for k in pairs(hist) do ks[#ks + 1] = k end
    table.sort(ks)
    for _, k in ipairs(ks) do o:write(string.format("entries %d-%d: %d builds\n", k, k + 4, hist[k])) end
    o:close()
    M:exit()
  end
end)
