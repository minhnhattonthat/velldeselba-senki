"""patch_exe.py: give a PS-X EXE the English glyph hook (tools/asm/hook.asm).

Prepends build/hook.bin (padded to HOOK_SIZE) so the image loads at 0x80020000 - HOOK_SIZE, and redirects every
`jal` to the EXE's own Krom2RawAdd stub (addiu t2,zero,0xB0; jr t2; addiu t1,zero,0x51) to krom_hook.
"""
import struct

HOOK_BASE = 0x8001F000
HOOK_SIZE = 0x1000
STUB = struct.pack("<III", 0x240A00B0, 0x01400008, 0x24090051)
# "Resident data loaded?" check (SCPS_100.27, every HT.EXE): compares the word at 0x80015A4C, the first two
# chars of crew name オユ・キクル in BERU_FL1.DAT, else reloads and crashes. Retargeted to the constant `\2D\`
# at 0x8001610C (EXE-name table), so the name can be translated and old Japanese saves still pass.
SIG_OLD = bytes.fromhex("8386033c" "0180023c" "4c5a428c" "83496334")  # lui v1,0x8683; lui v0,0x8001; lw v0,0x5A4C(v0); ori v1,0x4983
SIG_NEW = bytes.fromhex("445c033c" "0180023c" "0c61428c" "5c326334")  # lui v1,0x5C44; ...; lw v0,0x610C(v0); ori v1,0x325C


def jal(target):
    return 0x0C000000 | ((target >> 2) & 0x03FFFFFF)


def stubs(exe):
    """RAM addresses of the Krom2RawAdd stubs in a PS-X EXE."""
    t_addr = struct.unpack_from("<I", exe, 0x18)[0]
    out, i = [], exe.find(STUB, 0x800)
    while i >= 0:
        out.append(t_addr + i - 0x800)
        i = exe.find(STUB, i + 4)
    return out


def patch(exe, hook):
    """Return (patched EXE bytes, number of jal sites redirected)."""
    assert exe[:8] == b"PS-X EXE", "not a PS-X EXE"
    assert len(hook) <= HOOK_SIZE
    t_addr, t_size = struct.unpack_from("<II", exe, 0x18)
    assert t_addr == HOOK_BASE + HOOK_SIZE, hex(t_addr)
    body = bytearray(exe[0x800:0x800 + t_size])
    n = 0
    for s in stubs(exe):
        want = struct.pack("<I", jal(s))
        new = struct.pack("<I", jal(HOOK_BASE))
        i = body.find(want)
        while i >= 0:
            if i % 4 == 0:
                body[i:i + 4] = new
                n += 1
            i = body.find(want, i + 1)
    body = bytearray(body.replace(SIG_OLD, SIG_NEW))
    head = bytearray(exe[:0x800])
    struct.pack_into("<II", head, 0x18, HOOK_BASE, t_size + HOOK_SIZE)
    return bytes(head) + hook.ljust(HOOK_SIZE, b"\0") + bytes(body) + exe[0x800 + t_size:], n
