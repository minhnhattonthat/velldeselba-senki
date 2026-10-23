"""staffroll.py: keep staff-roll roles right-aligned in English (STAFF.EXE).

The roll is a table of 16-byte entries (u32 string pointer, s32 x, u32 y step, u32 kind) in the data after the code
(0x80032970 on). Roles sit in the left half with x chosen so the Japanese ends at 240 px (screen centre 256 minus
a cell); names start at x = 272; x = -1000 centres. The drawer uses x as given, so an English role of another width
needs a new x: the right edge (x + width) is kept. Cells are 16 px (textcodec.cells).
"""
import struct

import textcodec

CELL = 16
CENTRE = 256


def align(exe, refs, lines):
    """exe with the x of every left-half entry moved so the English keeps the Japanese right edge.
    refs = exetext.refs() of the original EXE (pointer words are file offsets; repointing keeps them);
    lines = [(addr, jp, en)]."""
    out = bytearray(exe)
    for addr, jp, en in lines:
        for ref in refs.get(addr, []):
            if ref[0] != "ptr":
                continue
            x, _, kind = struct.unpack_from("<iII", exe, ref[1] + 4)
            if 0 <= x < CENTRE and kind < 16:
                right = x + CELL * textcodec.cells(jp)
                struct.pack_into("<i", out, ref[1] + 4, max(0, right - CELL * textcodec.cells(en)))
    return bytes(out)
