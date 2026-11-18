-- probe.lua: one scripted, windowless session for the Alien Brigade / Crossbow survey.
-- (Modelled on the homebrew's build/harness/harness/session.lua + flight.lua; EXROM SuperGame aware.)
-- Environment (all optional):
--   SCRIPT  "frames:stick:button;..." stick = letters of l r u d or -, button bits: 1 fire,
--           2 button 2, 4 pause, 8 select, 16 reset
--   SNAPS   "a,b,c" frames to snapshot
--   DUMPS   "a,b,c" frames at which RAM $0000-$27FF is written to dump_f<frame>.bin
--           (a sidecar dump_f<frame>.txt has the bank in and the last MARIA register writes)
--   END     frame to exit on (default: script length)
--   XT      "1": log distinct fetched instructions with their bank, indirect-jump targets and
--           bank-select stores to exectrace.log (toolkit exectrace.lua's format, for dyn.py)
--   XTFROM  frame from which XT logging is armed (default 0)
--   REGS    "1": regs.txt = every distinct (pc, bank, register, value) write to MARIA $20-$3F
--           with count and min/max raster line
--   BANKS   "1": banks.txt = per (pc, value) bank-select write counts, the raster lines seen,
--           whether inside an NMI (NMI depth from the vector fetch / RTI is not tracked; the
--           stack pointer and the line are logged instead), and per-frame switch counts
--   PEEK    "addr,addr" hex: frames.txt gets a line per frame with those bytes
--   WATCH   "lo-hi[,lo-hi]" hex RAM ranges: watch.txt gets distinct (pc, bank, addr) writers with
--           counts and first/last frame, value set (up to 16)
--   WFROM/WTO  frame window for WATCH (default all)
--   POKES   "frame:addr=val,addr=val;..." hex
--   CNT     "lo-hi" hex: counts.txt = writes per (pc, value) in the range
local M = manager.machine
local cpu = M.devices[":maincpu"]
local mem = cpu.spaces["program"]
local P = M.ioport.ports
local scr
for _, s in pairs(M.screens) do scr = s break end

local function fld(n)
  for _, t in ipairs({":JOYSTICKS", ":BUTTONS", ":joysticks", ":buttons"}) do
    local f = P[t] and P[t].fields[n]
    if f then return f end
  end
end
local stick = {l = fld("P1 Left"), r = fld("P1 Right"), u = fld("P1 Up"), d = fld("P1 Down")}
local fire = fld("P1 Button 1")
local fire2 = fld("P1 Button 2")
local pause, select, reset
for _, t in ipairs({":CONSOLE", ":console", ":console_buttons"}) do
  if P[t] and P[t].fields["Pause"] then pause = P[t].fields["Pause"] end
  if P[t] and P[t].fields["Select"] then select = P[t].fields["Select"] end
  if P[t] and P[t].fields["Reset"] then reset = P[t].fields["Reset"] end
end
local steps = {}
for n, s, b in string.gmatch(os.getenv("SCRIPT") or "600:-:0", "(%d+):([lrud%-]+):(%d+)") do
  steps[#steps + 1] = {tonumber(n), s, tonumber(b)}
end
local total = 0
for _, s in ipairs(steps) do total = total + s[1] end
local function set(env)
  local t = {}
  for w in string.gmatch(os.getenv(env) or "", "%d+") do t[tonumber(w)] = true end
  return t
end
local snaps, dumps = set("SNAPS"), set("DUMPS")
local END = tonumber(os.getenv("END") or tostring(total))
local f = 0

local function line()
  local lines = scr.frame_period / scr.scan_period
  local left = scr:time_until_pos(0, 0) / scr.scan_period
  return math.floor((lines - left) % lines)
end

-- bank tracking (EXROM SuperGame: window value v shows file bank (v & 7) + 1)
local bank = 1
local function key(addr)
  if addr >= 0x8000 and addr <= 0xBFFF then return string.format("b%d:%04X", bank, addr) end
  if addr >= 0x4000 and addr < 0x8000 then return string.format("f0:%04X", addr) end
  if addr >= 0xC000 then return string.format("f8:%04X", addr) end
  return string.format("ram:%04X", addr)
end

local XT = os.getenv("XT") == "1"
local XTFROM = tonumber(os.getenv("XTFROM") or "0")
local seen_x, seen_j, seen_s = {}, {}, {}
local pending_j = nil
local BANKS = os.getenv("BANKS") == "1"
local bsw, bframe, bper = {}, 0, {}
T_BANK = mem:install_write_tap(0x8000, 0xBFFF, "banksel", function(offset, data)
  local v = (data & 7) + 1
  local pc = cpu.state["PC"].value
  if XT and f >= XTFROM then
    local k = string.format("%s %d", key(pc), v)
    seen_s[k] = (seen_s[k] or 0) + 1
  end
  if BANKS then
    local k = string.format("%s -> b%d", key(pc), v)
    local e = bsw[k]
    if not e then e = {n = 0, lmin = 999, lmax = -1, sp = {}, first = f} bsw[k] = e end
    e.n = e.n + 1
    local l = line()
    if l < e.lmin then e.lmin = l end
    if l > e.lmax then e.lmax = l end
    e.sp[cpu.state["SP"].value] = true
    e.last = f
    bframe = bframe + 1
  end
  bank = v
  return data
end)
if XT then
  T_XT = mem:install_read_tap(0x4000, 0xFFFF, "exectrace", function(offset, data)
    if f < XTFROM then return data end
    local pc = cpu.state["PC"].value
    if pc ~= offset then return data end
    local k = key(pc)
    if pending_j then
      seen_j[pending_j .. " " .. k] = true
      pending_j = nil
    end
    seen_x[k] = true
    if data == 0x6C then pending_j = k end
    return data
  end)
end

-- MARIA register writes
local REGS = os.getenv("REGS") == "1"
local regs, lastreg = {}, {}
T_REG = mem:install_write_tap(0x20, 0x3F, "maria", function(offset, data)
  lastreg[offset] = data
  if REGS then
    local k = string.format("%s reg %02X = %02X", key(cpu.state["PC"].value), offset, data)
    local e = regs[k]
    if not e then e = {n = 0, lmin = 999, lmax = -1, first = f} regs[k] = e end
    e.n = e.n + 1
    local l = line()
    if l < e.lmin then e.lmin = l end
    if l > e.lmax then e.lmax = l end
  end
  return data
end)

-- RAM write watch
local watch = {}
local WFROM = tonumber(os.getenv("WFROM") or "0")
local WTO = tonumber(os.getenv("WTO") or "99999999")
T_W = {}
for lo, hi in string.gmatch(os.getenv("WATCH") or "", "(%x+)%-(%x+)") do
  T_W[#T_W + 1] = mem:install_write_tap(tonumber(lo, 16), tonumber(hi, 16), "w" .. lo, function(offset, data)
    if f < WFROM or f > WTO then return data end
    local k = string.format("%s -> %04X", key(cpu.state["PC"].value), offset)
    local e = watch[k]
    if not e then e = {n = 0, first = f, vals = {}, nv = 0} watch[k] = e end
    e.n = e.n + 1
    e.last = f
    if not e.vals[data] and e.nv < 16 then e.vals[data] = true e.nv = e.nv + 1 end
    return data
  end)
end


-- CNT "lo-hi[,lo-hi]": counts.txt = number of writes per (pc, value) in those ranges (any address)
local cnt = {}
T_C = {}
for lo, hi in string.gmatch(os.getenv("CNT") or "", "(%x+)%-(%x+)") do
  T_C[#T_C + 1] = mem:install_write_tap(tonumber(lo, 16), tonumber(hi, 16), "c" .. lo, function(offset, data)
    local k = string.format("%s val %02X", key(cpu.state["PC"].value), data)
    cnt[k] = (cnt[k] or 0) + 1
    return data
  end)
end

local peek = {}
for a in string.gmatch(os.getenv("PEEK") or "", "[^,]+") do peek[#peek + 1] = tonumber(a, 16) end
local fout = (#peek > 0) and io.open("frames.txt", "w")
local pokes = {}
for fr, list in string.gmatch(os.getenv("POKES") or "", "(%d+):([^;]+)") do
  local t = pokes[tonumber(fr)] or {}
  for ad, val in string.gmatch(list, "(%x+)=(%x+)") do t[#t + 1] = {tonumber(ad, 16), tonumber(val, 16)} end
  pokes[tonumber(fr)] = t
end

local function finish()
  if XT then
    local lines = {}
    for k in pairs(seen_x) do lines[#lines + 1] = "X " .. k end
    for k in pairs(seen_j) do lines[#lines + 1] = "J " .. k end
    for k, n in pairs(seen_s) do lines[#lines + 1] = string.format("S %s x%d", k, n) end
    table.sort(lines)
    local o = io.open("exectrace.log", "w")
    for _, l in ipairs(lines) do o:write(l, "\n") end
    o:close()
  end
  if REGS then
    local lines = {}
    for k, e in pairs(regs) do
      lines[#lines + 1] = string.format("%s  x%d lines %d-%d first f%d", k, e.n, e.lmin, e.lmax, e.first)
    end
    table.sort(lines)
    local o = io.open("regs.txt", "w")
    for _, l in ipairs(lines) do o:write(l, "\n") end
    o:close()
  end
  if BANKS then
    local lines = {}
    for k, e in pairs(bsw) do
      local sps = {}
      for s in pairs(e.sp) do sps[#sps + 1] = string.format("%02X", s) end
      table.sort(sps)
      lines[#lines + 1] = string.format("%s  x%d lines %d-%d f%d-f%d sp %s", k, e.n, e.lmin, e.lmax, e.first, e.last, table.concat(sps, ","))
    end
    table.sort(lines)
    local o = io.open("banks.txt", "w")
    for _, l in ipairs(lines) do o:write(l, "\n") end
    o:write("per-frame switch counts (count: frames)\n")
    local ks = {}
    for k in pairs(bper) do ks[#ks + 1] = k end
    table.sort(ks)
    for _, k in ipairs(ks) do o:write(string.format("%d: %d\n", k, bper[k])) end
    o:close()
  end
  if next(watch) then
    local lines = {}
    for k, e in pairs(watch) do
      local vs = {}
      for v in pairs(e.vals) do vs[#vs + 1] = string.format("%02X", v) end
      table.sort(vs)
      lines[#lines + 1] = string.format("%s  x%d f%d-f%d vals %s", k, e.n, e.first, e.last, table.concat(vs, ","))
    end
    table.sort(lines)
    local o = io.open("watch.txt", "w")
    for _, l in ipairs(lines) do o:write(l, "\n") end
    o:close()
  end
  if next(cnt) then
    local lines = {}
    for k, n in pairs(cnt) do lines[#lines + 1] = string.format("%s  x%d", k, n) end
    table.sort(lines)
    local o = io.open("counts.txt", "w")
    for _, l in ipairs(lines) do o:write(l, "\n") end
    o:close()
  end
  if fout then fout:close() end
end

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
  if fire2 then fire2:set_value((cur and math.floor(cur[3] / 2) % 2 == 1) and 1 or 0) end
  if pause then pause:set_value((cur and cur[3] % 8 >= 4) and 1 or 0) end
  if select then select:set_value((cur and cur[3] % 16 >= 8) and 1 or 0) end
  if reset then reset:set_value((cur and cur[3] >= 16) and 1 or 0) end
  if snaps[f] then M.video:snapshot() end
  if dumps[f] then
    local o = io.open(string.format("dump_f%05d.bin", f), "wb")
    local parts = {}
    for a = 0, 0x27FF do parts[#parts + 1] = string.char(mem:read_u8(a)) end
    o:write(table.concat(parts))
    o:close()
    o = io.open(string.format("dump_f%05d.txt", f), "w")
    o:write(string.format("bank b%d\n", bank))
    for r = 0x20, 0x3F do
      if lastreg[r] then o:write(string.format("reg %02X = %02X\n", r, lastreg[r])) end
    end
    o:close()
  end
  if BANKS then
    bper[bframe] = (bper[bframe] or 0) + 1
    bframe = 0
  end
  if fout then
    local v = {}
    for _, a in ipairs(peek) do v[#v + 1] = string.format("%02X", mem:read_u8(a)) end
    fout:write(string.format("%d %s\n", f, table.concat(v, " ")))
  end
  local p = pokes[f]
  if p then for _, w in ipairs(p) do mem:write_u8(w[1], w[2]) end end
  if f >= END and not done then
    done = true
    finish()
    M:exit()
  end
end)
