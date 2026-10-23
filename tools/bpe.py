"""bpe.py: the game's compression, Philip Gage's byte-pair encoding (C/C++ Users Journal, 1994).

Stream = u32 LE length of the blocks (not counting these 4 bytes), then blocks until that length is used up. Block = pair table
(run-length coded: count byte > 127 skips count-127 codes; else count+1 entries follow, each `left` then `right` only
when left != code), u16 BE expanded size, then the packed bytes. Decoder in the game: 0x8006F930 (a0 = src, a1 = dst,
returns dst end), tables at scratchpad 0x1F800000 (left), 0x1F800100 (right), stack 0x1F800200. docs/re/compression.md.
"""
import struct


def decompress(src, pos=0):
    """Return (data, end offset) for the stream at src[pos]."""
    p = pos + 4
    end = p + struct.unpack_from("<I", src, pos)[0]
    out = bytearray()
    while p < end:
        left = list(range(256))
        right = [0] * 256
        c = 0
        while c < 256:
            count = src[p]; p += 1
            if count > 127:
                c += count - 127
                count = 0
            if c == 256:
                break
            for _ in range(count + 1):
                left[c] = src[p]; p += 1
                if left[c] != c:
                    right[c] = src[p]; p += 1
                c += 1
        size = src[p] << 8 | src[p + 1]; p += 2
        stack = []
        for b in src[p:p + size]:
            stack.append(b)
            while stack:
                x = stack.pop()
                if left[x] == x:
                    out.append(x)
                else:
                    stack.append(right[x])
                    stack.append(left[x])
        p += size
    return bytes(out), end


def _pack_block(buf, maxchars=220, thresh=3):
    """Gage's compressor for one block (len(buf) <= 0xFFFF): repeatedly replace the commonest pair with an unused code."""
    data = bytearray(buf)
    left = list(range(256))
    right = [0] * 256
    used = set(data)
    while True:
        counts = {}
        for a, b in zip(data, data[1:]):
            counts[a, b] = counts.get((a, b), 0) + 1
        if not counts:
            break
        (a, b), n = max(counts.items(), key=lambda kv: kv[1])
        free = next((c for c in range(256) if c not in used and left[c] == c), None)
        if n < thresh or free is None:
            break
        left[free], right[free] = a, b
        used.add(free)
        out = bytearray()
        i = 0
        while i < len(data):
            if i + 1 < len(data) and data[i] == a and data[i + 1] == b:
                out.append(free); i += 2
            else:
                out.append(data[i]); i += 1
        data = out
    # pair table, run-length coded: Gage's fileout() as published
    tab = bytearray()
    c = 0
    while c < 256:
        if left[c] == c:
            n = 1; c += 1
            while n < 127 and c < 256 and left[c] == c:
                n += 1; c += 1
            tab.append(n + 127)
            n = 0
            if c == 256:
                break
        else:
            n = 0; c += 1
            while (n < 127 and c < 256 and left[c] != c) or (n < 125 and c < 254 and left[c + 1] != c + 1):
                n += 1; c += 1
            tab.append(n)
            c -= n + 1
        for _ in range(n + 1):
            tab.append(left[c])
            if left[c] != c:
                tab.append(right[c])
            c += 1
    return bytes(tab) + struct.pack(">H", len(data)) + bytes(data)


def compress(data, block=0x2000):
    """Pack data as one stream (u32 length + blocks). Not byte-identical to the original packer; decodes the same."""
    body = b"".join(_pack_block(data[i:i + block]) for i in range(0, len(data), block)) if data else b""
    return struct.pack("<I", len(body)) + body
