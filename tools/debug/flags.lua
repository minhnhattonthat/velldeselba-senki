-- flags.lua: set story flag bits before play (docs/re/debug.md). The bitfield starts at 0x80010280.
-- FLAG_SET = {9999,1169} sets those bits (the airship take-off gate); FLAG_BITS = n sets bits 0..n-1, and an
-- optional FLAG_CLEAR = m zeroes bits n..m-1. Bits are rewritten for the first 30 frames: a write on frame 1 alone
-- was lost after the savestate load.
local BASE = 0x80010280 - 0x80000000
local mem = PCSX.getMemPtr()
local function set(b, on)
  local a, m = BASE + (b >> 3), 1 << (b & 7)
  if on then mem[a] = mem[a] | m else mem[a] = mem[a] & ~m end
end
assert(FLAG_SET or FLAG_BITS, "set FLAG_SET or FLAG_BITS")
L.on_frame(function(n)
  if n > 30 then return end
  for _, b in ipairs(FLAG_SET or {}) do set(b, true) end
  for b = 0, (FLAG_CLEAR or FLAG_BITS or 0) - 1 do set(b, b < (FLAG_BITS or 0)) end
  if n == 30 then L.log("flags set") end
end)
