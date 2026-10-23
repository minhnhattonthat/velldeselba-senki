-- pclog.lua: log the PC every PCLOG_EVERY frames (default 250), to see where a hang loops.
--   emu.py ... --script tools/debug/pclog.lua [--var PCLOG_EVERY=100]
local every = PCLOG_EVERY or 250
L.on_frame(function(f)
  if f % every == 0 then
    local r = PCSX.getRegisters()
    L.log(string.format("f%d pc=%08X ra=%08X", f, r.pc, r.GPR.n.ra))
  end
end)
