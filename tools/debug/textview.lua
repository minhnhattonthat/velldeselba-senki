-- textview.lua: show any text in the 2D dialogue box (docs/re/debug.md). Used by tools/debug/textview.py.
-- On the exec of the NPC-talk box opener (G1000.EXE 0x8005A5CC, a0 = string; 0x8005A190 opens banners and event
-- boxes), copies VIEW_HEX into free space at the end of the map's text region and points a0 at it.
local OPEN = VIEW_OPEN or 0x8005A5CC
local BUF = VIEW_BUF or 0x8017D000  -- G10 text region 0x8016C900-0x8017D900; its strings end near 0x80178000
-- VIEW_LIST (texttour.py): a list of hex strings, one per box opening, in order.
local list = VIEW_LIST or { assert(VIEW_HEX, "set VIEW_HEX (textview.py does)") }
local item = 0
local skip = VIEW_SKIP or 0
local mem = PCSX.getMemPtr()
L.on_exec(OPEN, function()
  if skip > 0 then skip = skip - 1; return end
  item = item + 1
  local hex = list[(item - 1) % #list + 1]
  local n = #hex / 2
  for i = 0, n - 1 do mem[BUF - 0x80000000 + i] = tonumber(hex:sub(2 * i + 1, 2 * i + 2), 16) end
  mem[BUF - 0x80000000 + n] = 0
  PCSX.getRegisters().GPR.n.a0 = BUF
  L.log(string.format("f%d item %d box -> %08X (%d bytes)", L.frame, item, BUF, n))
end)
