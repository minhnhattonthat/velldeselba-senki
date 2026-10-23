"""patch_exe.py: give a PS-X EXE the English glyph hook (tools/asm/hook.asm).

Prepends build/hook.bin (padded to HOOK_SIZE) so the image loads at 0x80020000 - HOOK_SIZE, and redirects every
`jal` to the EXE's own Krom2RawAdd stub (addiu t2,zero,0xB0; jr t2; addiu t1,zero,0x51) to krom_hook.
"""
import struct

import textcodec

HOOK_BASE = 0x8001F000
HOOK_SIZE = 0x1000
STUB = struct.pack("<III", 0x240A00B0, 0x01400008, 0x24090051)
# "Resident data loaded?" check (SCPS_100.27, every HT.EXE): compares the word at 0x80015A4C, the first two
# chars of crew name オユ・キクル in BERU_FL1.DAT, else reloads and crashes. Retargeted to the constant `\2D\`
# at 0x8001610C (EXE-name table), so the name can be translated and old Japanese saves still pass.
SIG_OLD = bytes.fromhex("8386033c" "0180023c" "4c5a428c" "83496334")  # lui v1,0x8683; lui v0,0x8001; lw v0,0x5A4C(v0); ori v1,0x4983
SIG_NEW = bytes.fromhex("445c033c" "0180023c" "0c61428c" "5c326334")  # lui v1,0x5C44; ...; lw v0,0x610C(v0); ori v1,0x325C

# TITLE.EXE 0x80025B00: the loop copying the entered player name (0x80010200) to 0x800159EC, byte by byte.
# Replaced by name_pack(dst = fp, src = s2) (hook.asm, 0x8001F100): grid letters -> English letter pairs.
NAME_PACK = 0x8001F100
NAME_COPY_OLD = bytes.fromhex("00004292000000000a004010211840022120c003000062900100632401009426"
                              "000082a00000629000000000f9ff4014010084242110d403000040a0")
# 0x80025AE8 branches to 0x80025B04 when a name was typed, so the call starts there: nop; move a0,fp; jal; move a1,s2
NAME_COPY_NEW = struct.pack("<4I", 0, 0x03C02021, 0x0C000000 | (NAME_PACK >> 2 & 0x03FFFFFF), 0x02402821) + bytes(44)

# STAFF.EXE 0x80023374: only codes <= 0x989E go to Krom2RawAdd (the hook); higher ones to its own level-2 kanji
# table, which would draw letter pairs (0xA0xx-0xFFxx) as garbage. Threshold raised to 0xFFFF: the English roll
# has no level-2 kanji left. andi a0,t0,0xffff; ori v0,zero,0x989e -> 0xffff; sltu v0,v0,a0
STAFF_SPLIT_OLD = bytes.fromhex("ffff0431" "9e980234" "2b104400")
STAFF_SPLIT_NEW = bytes.fromhex("ffff0431" "ffff0234" "2b104400")


# 3D results/HUD messages (every HT.EXE, DEMO.EXE; docs/re/text.md): one 2-byte-token stream for the 3D text engine.
# '@'+0 pauses for the next value (the text continues on the same line), '//' ends a block, %u/%s/%S are filled in
# order, one value per call. The code points at fixed offsets (after each '//'), so each slot is rewritten in place:
# same placeholders in the same order, English letter pairs between them, NUL fill.
RESULTS_JP = "撃墜数　%u@".encode("cp932")
RESULTS = [  # (slot size, pieces: str = English text, bytes = kept as is)
    (0x1C, ["Kills ", b"%u@\0", ", total ", b"%u\r\n//"]),
    (0x1C, [b"%S\0\0", "'s crew stole ", b"@\0%u", "Z.", b"\r\n//"]),
    (0x28, [b"%s", " gained ", b"@\0%u", " EXP", b"@\0", "!", b"\r\n//"]),
    (0x50, [b"%s", ": ", b"@\0", "Level up!", b"\r\n\r\n%s", " reached", b"\r\n", "level ", b"%u", ".", b"\r\n",
            "Gunnery: +", b"%u\r\n", "Repair:  +", b"%u\r\n//"]),
    (0x06, [b"%s", ":"]),
    (0x12, [b"%s", ", out of ammo!"]),
]


def results3d(body):
    """English 3D results/ammo messages in place (body unchanged when it has none)."""
    i = body.find(RESULTS_JP)
    if i < 0:
        return body
    assert body[i + 0xC6:i + 0xCA] == b"\0\0//", "3D results block moved"
    out = bytearray()
    for size, pieces in RESULTS:
        slot = b"".join(p if isinstance(p, bytes) else textcodec.encode(p) for p in pieces)
        assert len(slot) <= size, (slot, size)
        out += slot.ljust(size, b"\0")
    return body[:i] + out + body[i + len(out):]


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
    body = bytearray(body.replace(SIG_OLD, SIG_NEW).replace(NAME_COPY_OLD, NAME_COPY_NEW)
                     .replace(STAFF_SPLIT_OLD, STAFF_SPLIT_NEW))
    body = bytearray(results3d(bytes(body)))
    head = bytearray(exe[:0x800])
    struct.pack_into("<II", head, 0x18, HOOK_BASE, t_size + HOOK_SIZE)
    return bytes(head) + hook.ljust(HOOK_SIZE, b"\0") + bytes(body) + exe[0x800 + t_size:], n
