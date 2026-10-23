-- warp.lua: put the game on any map by its EXE-table index (docs/re/debug.md).
--   emu.py rom.cue --state-in work/states/intro_fmv.sstate --script tools/debug/warp.lua --var MAP=0 --frames 3000
-- Writes the resident "current map" word (0x80010238) every frame until the map loads, so the game's own
-- map change after the intro FMV loads MAP instead of G1000. ENTRY (0x80010234) is the entrance, -1 = default.
local MAP_ADDR, ENTRY_ADDR = 0x10238, 0x10234
local mem = PCSX.getMemPtr()
local function w32(a, v)
  for i = 0, 3 do mem[a + i] = bit.band(bit.rshift(v, 8 * i), 0xFF) end
end
local until_frame = WARP_FRAMES or 600
L.on_frame(function(f)
  if f <= until_frame then
    w32(MAP_ADDR, MAP)
    w32(MAP_ADDR + 4, MAP)
    w32(ENTRY_ADDR, ENTRY or 0xFFFFFFFF)
  end
end)
