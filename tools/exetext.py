"""exetext.py: Shift-JIS strings in PS-X EXEs and every reference to them (docs/re/text.md §EXEs).

strings(exe) -> [(addr, raw bytes without the NUL)] in the data area before the entry point.
refs(exe)    -> {addr: [ref]} where ref = ("ptr", word_off) or ("pair", lui_off, lo_off, lo_op);
                offsets are file offsets of instruction/data words, so patching is a plain byte write.
"""
import struct

LOADSTORE = {0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B}
ADDIU, ORI = 0x09, 0x0D


def header(exe):
    pc0, _, t_addr, t_size = struct.unpack_from("<IIII", exe, 0x10)
    return pc0, t_addr, t_size


def refs(exe):
    pc0, t_addr, t_size = header(exe)
    img = exe[0x800:0x800 + t_size]
    lo_end = t_addr + t_size
    words = struct.unpack_from(f"<{len(img) // 4}I", img)
    out = {}
    for i, w in enumerate(words):
        if t_addr <= w < lo_end:
            out.setdefault(w, []).append(("ptr", 0x800 + 4 * i))
        if w >> 26 == 0x0F and (w >> 21) & 31 == 0:  # lui rt, imm
            rt, hi = (w >> 16) & 31, w & 0xFFFF
            for k in range(1, 17):
                if i + k >= len(words):
                    break
                w2 = words[i + k]
                op, rs, rt2 = w2 >> 26, (w2 >> 21) & 31, (w2 >> 16) & 31
                if rs == rt and (op in (ADDIU, ORI) or op in LOADSTORE):
                    lo = w2 & 0xFFFF
                    addr = (hi << 16) | lo if op == ORI else ((hi << 16) + (lo - 0x10000 if lo & 0x8000 else lo)) & 0xFFFFFFFF
                    if t_addr <= addr < lo_end:
                        out.setdefault(addr, []).append(("pair", 0x800 + 4 * i, 0x800 + 4 * (i + k), op))
                if rt2 == rt and op not in LOADSTORE and op not in (0x04, 0x05) or (op == 0 and (w2 >> 11) & 31 == rt):
                    break  # rt overwritten
    return out


def _is_text(raw):
    i, sjis = 0, 0
    while i < len(raw):
        c = raw[i]
        if c >= 0x80:
            if not (0x81 <= c <= 0x9F or 0xE0 <= c <= 0xEF) or i + 1 >= len(raw):  # no half-width kana
                return False
            if not 0x40 <= raw[i + 1] <= 0xFC or raw[i + 1] == 0x7F:
                return False
            try:
                raw[i:i + 2].decode("cp932")
            except UnicodeDecodeError:
                return False
            sjis += 1
            i += 2
        elif 0x20 <= c < 0x7F or c in (0x0D, 0x0A):
            i += 1
        else:
            return False
    return sjis > 0


def apply(exe, edits, base, limit, repack=False):
    """Write new string bytes into exe (original layout). edits = {addr: bytes without NUL}.
    In place when the text plus NUL fits the old string's 4-aligned slot; otherwise moved, and every reference
    repointed: into the smallest hole left in the EXE (slots of moved strings, tails of shortened ones; never one
    holding another reference target), else appended to a blob that loads at `base` (must stay below `limit`).
    repack: move every referenced edited string, so a run of adjacent slots becomes one hole (for EXEs whose
    English only fits when packed, like the staff roll). Returns (exe, blob)."""
    pc0, t_addr, t_size = header(exe)
    out = bytearray(exe)
    r = refs(exe)
    targets = sorted(r)
    unreferenced = lambda a, n: not any(a <= t < a + n for t in targets)
    blob, moved, holes = bytearray(), [], []
    for addr, new in sorted(edits.items()):
        o = 0x800 + addr - t_addr
        old_end = exe.index(b"\0", o) + 1
        slot = (old_end - 0x800 + 3) // 4 * 4 + 0x800 - o
        data = new + b"\0"
        if len(data) <= slot and not (repack and addr in r):
            out[o:o + slot] = data.ljust(slot, b"\0")
            used = (len(data) + 3) // 4 * 4
            if slot - used >= 4 and unreferenced(addr + used, slot - used):
                holes.append([addr + used, slot - used])
            continue
        if addr not in r:
            raise ValueError(f"{addr:#x}: {len(data)} bytes > slot {slot} and no reference to relocate")
        moved.append((addr, data))
        if unreferenced(addr + 1, slot - 1):
            holes.append([addr, slot])
    merged = []
    for h in sorted(holes):
        if merged and merged[-1][0] + merged[-1][1] == h[0]:
            merged[-1][1] += h[1]
        else:
            merged.append(h)
    holes = merged
    for addr, data in sorted(moved, key=lambda m: -len(m[1])):
        size = (len(data) + 3) // 4 * 4
        hole = min((h for h in holes if h[1] >= size), key=lambda h: h[1], default=None)
        if hole:
            dest = hole[0]
            out[0x800 + dest - t_addr:0x800 + dest - t_addr + size] = data.ljust(size, b"\0")
            hole[0] += size
            hole[1] -= size
        else:
            dest = base + len(blob)
            blob += data.ljust(size, b"\0")
            if base + len(blob) > limit:
                raise ValueError(f"relocation space full at {addr:#x} ({len(blob)} bytes)")
        for ref in r[addr]:
            if ref[0] == "ptr":
                struct.pack_into("<I", out, ref[1], dest)
            else:
                _, lui_off, lo_off, op = ref
                hi = dest >> 16 if op == ORI else (dest + 0x8000) >> 16
                w = struct.unpack_from("<I", out, lui_off)[0]
                struct.pack_into("<I", out, lui_off, (w & 0xFFFF0000) | hi)
                w = struct.unpack_from("<I", out, lo_off)[0]
                struct.pack_into("<I", out, lo_off, (w & 0xFFFF0000) | (dest & 0xFFFF))
    return bytes(out), bytes(blob)


def strings(exe, r=None):
    """Strings start after a NUL or at any referenced address (some follow a pointer table directly). Past the
    entry point (code, then more data: menus, staff-roll roles) only referenced strings of 2+ SJIS chars count,
    or of one when a pointer table holds it (staff-roll role 歌)."""
    pc0, t_addr, t_size = header(exe)
    img = exe[0x800:0x800 + t_size]
    r = refs(exe) if r is None else r
    out, o = [], 0
    while o < len(img):
        data = t_addr + o < pc0
        if img[o] and (data and (o == 0 or img[o - 1] == 0) or t_addr + o in r):
            z = img.find(b"\0", o)
            raw = img[o:z]
            wide = sum(ord(c) > 0x7F for c in raw.decode("cp932")) if z > o and _is_text(raw) else 0
            ptr = any(ref[0] == "ptr" for ref in r.get(t_addr + o, []))
            if wide and (data or wide >= 2 or ptr):
                out.append((t_addr + o, raw))
                o = z
                continue
        o += 1
    return out
