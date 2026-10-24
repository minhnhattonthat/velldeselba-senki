"""routemap.py: English place names on the airship route map (docs/re/graphics.md).

    python -X utf8 tools/routemap.py OUTDIR    # OUTDIR/sheet.png (new label sheet, 3x) and screen.png (labels at
                                               # their screen positions, 2x) for checking overlaps

The names are sprites cut from a 256x152 4bpp sheet, stream 7 of 2D/OTHER/SHIP_SET.MPS (map picture x < 216,
y < 120; node dots at x 248-255, y 105-118; names in the rest). Each I-map EXE (I0100..I0700) holds the same table
of 23 entries, 16 bytes each, u16: u, v, w, h (rect in the sheet), x, y (label on screen), node x, node y.
The sheet's name area is cleared and the English names packed into it (Spleen 5x8, white with a dark outline);
each entry gets its new rect, and x moves so a label left of its node keeps its right edge.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import bpe
import font
import scan_bpe

SHEET = "2D/OTHER/SHIP_SET.MPS"
STREAM = 6
W, H = 256, 152
EXES = [f"2D/IMPS/I0{m}.EXE" for m in ("100", "110", "300", "310", "400", "410", "500", "600", "700")]
ENTRY0 = struct.pack("<8H", 216, 92, 36, 12, 228, 83, 232, 74)  # first entry of the table, original disc
NAMES = ["Keperak", "Deze", "Panasgal", "Ogatsu", "Dak", "Dant", "Miderekisata", "Denamus", "Danaspi", "Zurak",
         "Kuna City", "Maxilaraki", "Danadeuno", "Wazano", "Schach", "Yarskill", "Glacial", "Azamig", "Gajis", "Gar",
         "Yazusa", "Adakuda", "Daha"]  # table order (glossary spellings)
INK, EDGE = 15, 2  # sheet colours: white letters, dark outline
SIDE = (216, 248, 120)  # side column x0, x1 and y end; rows of LH px
LH = 10
DOTS = 105  # node dot sprites at x 248-255 from this row down to 118: kept
BOTTOM = (120, 152)


def label(text):
    """(w, h, {(x, y): colour}) for text: Spleen 5x8 with a 1 px outline."""
    glyphs = font._bdf(ROOT / "fonts/spleen-5x8.bdf")
    on = {(1 + 5 * i + x, 1 + y) for i, ch in enumerate(text)
          for y, bits in enumerate(glyphs[ord(ch)]) for x in range(8) if bits & 0x80 >> x}
    edge = {(x + dx, y + dy) for x, y in on for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - on
    px = {p: EDGE for p in edge} | {p: INK for p in on}
    return max(x for x, _ in px) + 1, LH, px


def pack():
    """[(u, v, w, h, pixels)] per name: names that fit the side column go there, the rest in bottom rows."""
    labels = [label(t) for t in NAMES]
    out, side_y, row, bx = [None] * len(NAMES), 0, BOTTOM[0], 0
    for i in sorted(range(len(NAMES)), key=lambda i: -labels[i][0]):
        w, h, px = labels[i]
        if w <= SIDE[1] - SIDE[0] and side_y + h <= SIDE[2] and len(NAMES[i]) <= 6:
            out[i] = (SIDE[0], side_y, w, h, px)
            side_y += h
            continue
        if bx + w > W:
            row, bx = row + h, 0
        assert row + h <= BOTTOM[1], "names do not fit the sheet"
        out[i] = (bx, row, w, h, px)
        bx += w
    return out


def sheet(dec):
    """New stream 7 bytes: name area cleared, packed names drawn."""
    px = [[(dec[y * W // 2 + x // 2] >> (4 * (x & 1))) & 15 for x in range(W)] for y in range(H)]
    for y in range(H):
        for x in range(W):
            if y >= BOTTOM[0] or (SIDE[0] <= x and y < DOTS) or (SIDE[0] <= x < SIDE[1] and y < SIDE[2]):
                px[y][x] = 0
    for u, v, w, h, pix in pack():
        for (x, y), c in pix.items():
            px[v + y][u + x] = c
    return bytes(row[x] | row[x + 1] << 4 for row in px for x in range(0, W, 2)) + dec[W * H // 2:]


def entries(exe):
    o = exe.find(ENTRY0)
    assert o >= 0 and exe.find(ENTRY0, o + 1) < 0, "route-map table not found once"
    return o, [list(struct.unpack_from("<8H", exe, o + 16 * i)) for i in range(len(NAMES))]


def patch_exe(exe, orig):
    """exe with the table rewritten; the table is the original EXE's (orig), found again in exe (the build grows
    EXEs, which moves it)."""
    t, ents = entries(orig)
    table = orig[t:t + 16 * len(NAMES)]
    o = exe.find(table)
    assert o >= 0 and exe.find(table, o + 1) < 0, "route-map table not found once in the built EXE"
    out = bytearray(exe)
    for i, (e, (u, v, w, h, _)) in enumerate(zip(ents, pack())):
        x = e[4] + e[2] - w if e[4] + e[2] <= e[6] else e[4]  # left of the node: keep the right edge
        struct.pack_into("<8H", out, o + 16 * i, u, v, w, h, x, e[5] + (e[3] - h) // 2, e[6], e[7])
    return bytes(out)


def patch_sheet(mps):
    streams = list(scan_bpe.streams(mps))
    n = len(streams)
    counts = struct.unpack_from(f"<{n}H", mps, 2 * n)
    pos, _, dec = streams[STREAM]
    new = bpe.compress(sheet(dec))
    if len(new) > counts[STREAM] * 0x800:
        raise ValueError(f"route-map sheet {len(new):#x} bytes > slot {counts[STREAM] * 0x800:#x}")
    out = bytearray(mps)
    out[pos:pos + counts[STREAM] * 0x800] = new.ljust(counts[STREAM] * 0x800, b"\0")
    return bytes(out)


def main():
    from PIL import Image, ImageDraw
    outdir = Path(sys.argv[1])
    outdir.mkdir(parents=True, exist_ok=True)
    tree = ROOT / "work/disc/tree"
    mps = (tree / SHEET).read_bytes()
    n = len(list(scan_bpe.streams(mps)))
    c = struct.unpack_from("<16H", mps, 4 * n + 32 * STREAM)
    pal = [v for x in c for v in ((x & 31) * 8, (x >> 5 & 31) * 8, (x >> 10 & 31) * 8)]
    data = sheet(list(scan_bpe.streams(mps))[STREAM][2])
    img = Image.new("P", (W, H))
    img.putdata([(data[i // 2] >> (4 * (i & 1))) & 15 for i in range(W * H)])
    img.putpalette(pal)
    img = img.convert("RGB")
    img.resize((W * 3, H * 3), Image.NEAREST).save(outdir / "sheet.png")
    orig = (tree / EXES[0]).read_bytes()
    o = entries(orig)[0]
    exe = patch_exe(orig, orig)
    scr = Image.new("RGB", (320, 240), (40, 40, 80))
    d = ImageDraw.Draw(scr)
    for i in range(len(NAMES)):
        u, v, w, h, x, y, nx, ny = struct.unpack_from("<8H", exe, o + 16 * i)
        scr.paste(img.crop((u, v, u + w, v + h)), (x, y))
        d.rectangle((nx - 1, ny - 1, nx + 1, ny + 1), fill=(255, 0, 0))
    scr.resize((640, 480), Image.NEAREST).save(outdir / "screen.png")
    print(outdir / "sheet.png", outdir / "screen.png")


if __name__ == "__main__":
    main()
