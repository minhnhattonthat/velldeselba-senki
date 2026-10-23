"""tims.py: find and render PS1 TIM images in the disc tree, raw and inside BPE streams (graphics survey).

    python -X utf8 tools/tims.py list                  # every TIM: file, stream, offset, bpp, size
    python -X utf8 tools/tims.py render OUTDIR [--min 16]   # one PNG per TIM (CLUT 0), plus index.txt

TIM: u32 0x10, u32 flags (bpp 0-3, bit 3 = CLUT), [CLUT block], image block (u32 len, u16 x, y, w, h, data).
"""
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import scan_bpe

TREE = ROOT / "work/disc/tree"
SKIP = (".STR", ".XA", ".VAB", ".DA")


def parse(d, o):
    """(bpp, width px, height, clut colours, image data, end) for a TIM at o, or None."""
    if d[o:o + 4] != b"\x10\0\0\0" or o + 20 > len(d):
        return None
    flags = struct.unpack_from("<I", d, o + 4)[0]
    bpp, has_clut = flags & 7, flags & 8
    if flags & ~0xF or bpp > 3:
        return None
    p, clut = o + 8, None
    if has_clut:
        n, _, _, cw, ch = struct.unpack_from("<IHHHH", d, p)
        if n != 12 + cw * ch * 2 or not 0 < cw * ch <= 4096:
            return None
        clut = struct.unpack_from(f"<{cw * ch}H", d, p + 12)
        p += n
    elif bpp < 2:
        return None
    if p + 12 > len(d):
        return None
    n, _, _, w, h = struct.unpack_from("<IHHHH", d, p)
    if n != 12 + w * h * 2 or not (w and h) or p + n > len(d):
        return None
    width = {0: w * 4, 1: w * 2, 2: w, 3: w * 2 // 3}[bpp]
    return bpp, width, h, clut, d[p + 12:p + n], p + n


def find(d):
    o = d.find(b"\x10\0\0\0")
    while o >= 0:
        t = parse(d, o)
        if t:
            yield o, t
        o = d.find(b"\x10\0\0\0", o + 4)


def sources():
    for p in sorted(TREE.rglob("*")):
        if not p.is_file() or p.suffix.upper() in SKIP:
            continue
        d = p.read_bytes()
        rel = p.relative_to(TREE).as_posix()
        yield rel, "raw", d
        for pos, n, dec in scan_bpe.streams(d):
            yield rel, f"{pos:#x}", dec


def rgb(c):
    return bytes(((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31))


def png(path, w, h, rows):
    raw = b"".join(b"\0" + r for r in rows)
    chunk = lambda t, b: struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def pixels(bpp, width, h, clut, data):
    rows = []
    stride = len(data) // h
    for y in range(h):
        line = data[y * stride:(y + 1) * stride]
        if bpp == 0:
            idx = [b >> s & 15 for b in line for s in (0, 4)]
        elif bpp == 1:
            idx = list(line)
        else:
            idx = None
        if idx is not None:
            rows.append(b"".join(rgb(clut[i] if i < len(clut) else 0) for i in idx[:width]))
        elif bpp == 2:
            rows.append(b"".join(rgb(c) for c in struct.unpack_from(f"<{width}H", line)))
        else:
            rows.append(bytes(line[:width * 3]))
    return rows


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    out = Path(sys.argv[2]) if cmd == "render" else None
    lim = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 16
    if out:
        out.mkdir(parents=True, exist_ok=True)
        index = []
    k = 0
    for rel, where, d in sources():
        for o, (bpp, w, h, clut, data, end) in find(d):
            line = f"{rel} {where} {o:#x} {4 << bpp if bpp < 2 else 16 if bpp == 2 else 24}bpp {w}x{h}"
            if out is None:
                print(line)
                continue
            if w < lim or h < lim:
                index.append(f"skip (smaller than {lim}px): {line}")
                continue
            name = f"{k:05d}.png"
            png(out / name, w, h, pixels(bpp, w, h, clut, data))
            index.append(f"{name} {line}")
            k += 1
    if out:
        (out / "index.txt").write_text("\n".join(index) + "\n", encoding="utf-8")
        print(f"{k} images -> {out}")


if __name__ == "__main__":
    main()
