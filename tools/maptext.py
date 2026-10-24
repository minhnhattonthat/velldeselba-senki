"""maptext.py: string tables inside BPE streams of 2D map MPS files (docs/re/text.md).

Table = 0x1000 bytes of u16 LE offsets (relative to 0x1000) + strings ending in `E`, inside a fixed 0x11000-byte
region at the start of the expanded stream; whatever follows (map data) is kept byte for byte.
"""
import struct

import bpe
import scan_bpe

TABLE, REGION = 0x1000, 0x11000


def parse(dec):
    """Strings (bytes, each ending in E) of a text stream, or None when dec isn't one."""
    if len(dec) < TABLE + 4 or dec[:2] != b"\0\0":
        return None
    offs = list(struct.unpack_from("<2048H", dec, 0))
    n = 1
    while n < 2048 and offs[n] > offs[n - 1]:
        n += 1
    offs = offs[:n]
    out = []
    for i, o in enumerate(offs):
        a = TABLE + o
        end = TABLE + offs[i + 1] if i + 1 < n else _end(dec, a)
        if end is None or end > REGION or dec[end - 1:end] != b"E":
            return None
        out.append(dec[a:end])
    return out


def _end(dec, a):
    """End of the last string: the first zero byte at a code position (strings never hold a raw 0)."""
    z = dec.find(b"\0", a)
    return z if z > a else None


def build(dec, strings, share=False):
    """Expanded stream with the string table replaced; raises when the text overflows the region.
    A table that overflows is retried with identical strings stored once (offsets then repeat)."""
    body = bytearray()
    offs = []
    seen = {}
    for s in strings:
        if share and s in seen:
            offs.append(seen[s])
            continue
        seen[s] = len(body)
        offs.append(len(body))
        body += s
    if TABLE + len(body) > REGION or max(offs) > 0xFFFF:
        if not share:
            return build(dec, strings, True)
        raise ValueError(f"text {len(body):#x} bytes > {REGION - TABLE:#x}")
    region = struct.pack(f"<{len(offs)}H", *offs).ljust(TABLE, b"\0") + bytes(body)
    return region.ljust(REGION, b"\0") + dec[REGION:]


def text_streams(mps):
    """[(stream pos, packed length, expanded bytes, strings)] for the text streams in an MPS file."""
    out = []
    for pos, n, dec in scan_bpe.streams(mps):
        s = parse(dec)
        if s:
            out.append((pos, n, dec, s))
    return out


def replace_stream(mps, pos, n, dec):
    """Recompress dec into the slot of the stream at pos (length n); a stream that ends its section grows the
    section by whole sectors (later sections move; the game sums the header counts: docs/re/disc.md)."""
    packed = bpe.compress(dec)
    slot = _slot(mps, pos, n)
    if len(packed) > slot:
        mps = _grow(mps, pos + slot, len(packed) - slot)
        slot = _slot(mps, pos, n)
    out = bytearray(mps)
    out[pos:pos + slot] = packed.ljust(slot, b"\0")
    return bytes(out)


SECTIONS = (0x24, 0x26, 0x28, 0x30)  # header u16s: sector counts of the 4 sections after the 0x1000-byte header


def _grow(mps, at, extra):
    """Insert zero sectors (>= extra bytes) at `at`, which must be the end of a section; bumps its sector count."""
    counts = [struct.unpack_from("<H", mps, o)[0] for o in SECTIONS]
    end = 0x1000
    for o, c in zip(SECTIONS, counts):
        end += c * 0x800
        if end == at and 0x1000 + sum(counts) * 0x800 == len(mps):
            k = -(-extra // 0x800)
            out = bytearray(mps[:at] + bytes(k * 0x800) + mps[at:])
            struct.pack_into("<H", out, o, c + k)
            return bytes(out)
    raise ValueError(f"stream ending @{at:#x}: {extra:#x} bytes over its slot, not at a section end")


def _slot(mps, pos, n):
    """Bytes free from pos to the next non-zero byte after this stream (zero padding is reusable)."""
    end = pos + 4 + n
    while end < len(mps) and mps[end] == 0:
        end += 1
    return end - pos
