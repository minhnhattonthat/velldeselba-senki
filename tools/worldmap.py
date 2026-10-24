"""worldmap.py: English text on the 2D/OTHER picture files (docs/re/graphics.md): the Old Sage's maps
(WORLD.MPS) and the shipyard's ship pictures (SHIP_PIC.MPS, model name in the title bar).

    python -X utf8 tools/worldmap.py OUTDIR    # writes OUTDIR/<file>_k.png previews (2x) of the edited pictures

Both files: 0x800 header with n u16 sector offsets of the BPE streams (from 0x800), n u16 sector counts at 2n, then
n 16-colour CLUTs at 4n + 32k; then the streams. Each stream is a 224 px wide 4bpp picture (112 bytes per row).
Map labels are erased (their colours inside the box are refilled from neighbouring pixels); title bars are refilled
flat. English is drawn with Spleen (fonts/, BSD-2). build.py writes the files build() returns.
"""
import struct
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import bpe
import font
import scan_bpe

W = 224
FONTS = {"small": ROOT / "fonts/spleen-5x8.bdf", "big": ROOT / "fonts/spleen-6x12.bdf"}
ADV = {"small": 5, "big": 7}  # big: 6 px cells drawn bold (+1 px), so 7 px per letter

# picture -> (style, erase box (x0, y0, x1, y1) inclusive-exclusive, colour indices erased, labels)
# label: (text, x, y, align) with x the left edge ("l") or right edge ("r") and y the top row.
PICTURES = {
    0: dict(font="small", fill=0, outline=None, under=True, erase=[c for c in range(16) if c != 15],  # on water
            labels=[((46, 88, 100, 106), ("Nades Island", 50, 94, "l"))]),
    3: dict(font="small", fill=2, outline=12, under=False, erase=[2, 12],
            labels=[((119, 38, 144, 50), ("Munogi", 131, 40, "c")),
                    ((30, 57, 61, 69), ("Noipask", 45, 59, "c")),
                    ((14, 109, 39, 122), ("Gidan", 26, 111, "c")),
                    ((139, 103, 157, 116), ("Kuna", 148, 105, "c")),
                    ((86, 120, 124, 135), ("Oldanaspi", 104, 123, "c"))]),
    4: dict(font="big", fill=10, outline=None, under=False, erase=[10, 3],  # 3: grey edge of the old letters
            labels=[((127, 8, 177, 23), ("Nunurus", 128, 9, "l")),
                    ((19, 22, 57, 37), ("Munogi", 56, 23, "r")),
                    ((139, 43, 188, 57), ("Youtakon", 140, 44, "l")),
                    ((3, 60, 42, 74), ("Ferum", 41, 61, "r")),
                    ((147, 92, 187, 107), ("Ayamemi", 148, 93, "l")),
                    ((11, 110, 49, 125), ("Yadas", 48, 111, "r")),
                    ((167, 126, 222, 141), ("Panasgal", 219, 127, "r"))]),
    5: dict(font="big", fill=15, outline=None, under=False, erase=[15, 5],  # 5: grey edge of the old letters
            labels=[((106, 8, 166, 24), ("Panasgal", 163, 9, "r")),
                    ((151, 42, 174, 57), ("Deze", 152, 43, "l")),
                    ((3, 50, 44, 64), ("Danaspi", 4, 51, "l")),
                    ((113, 61, 143, 75), ("Ogatsu", 142, 62, "r")),
                    ((170, 72, 222, 90), ("Houdepui", 219, 77, "r")),
                    ((21, 77, 61, 91), ("Denamus", 22, 78, "l")),
                    ((46, 124, 75, 139), ("Dant", 47, 125, "l"))]),
}
# SHIP_PIC.MPS: 6 models x 4 colour schemes, in this order
SHIPS = ["Parnat Pock", "Gazelant", "Garganak", "Sebrentream", "Valgart", "Jitegart"]
FILES = {"2D/OTHER/WORLD.MPS": PICTURES,
         "2D/OTHER/SHIP_PIC.MPS": {k: {"bar": SHIPS[k // 4]} for k in range(24)}}


def pixels(dec):
    h = len(dec) // (W // 2)
    return [[(dec[y * W // 2 + x // 2] >> (4 * (x & 1))) & 15 for x in range(W)] for y in range(h)]


def packed(px, tail):
    out = bytearray()
    for row in px:
        out += bytes(row[x] | row[x + 1] << 4 for x in range(0, W, 2))
    return bytes(out) + tail


def erase(px, box, colours):
    """Refill the label colours inside box from the commonest neighbouring non-label pixel, outside in."""
    x0, y0, x1, y1 = box
    hole = {(x, y) for y in range(y0, y1) for x in range(x0, x1) if px[y][x] in colours}
    while hole:
        done = {}
        for x, y in hole:
            near = Counter(px[y + dy][x + dx] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                           if (x + dx, y + dy) not in hole and 0 <= y + dy < len(px) and 0 <= x + dx < W)
            if near:
                done[x, y] = near.most_common(1)[0][0]
        assert done, "erase box has no edge"
        for (x, y), c in done.items():
            px[y][x] = c
        hole -= done.keys()


def text_mask(text, style):
    """Set of (x, y) pixels of text, origin top-left."""
    glyphs, bold = font._bdf(FONTS[style]), style == "big"
    on = set()
    for i, ch in enumerate(text):
        for y, bits in enumerate(glyphs[ord(ch)]):
            for x in range(8):
                if bits & 0x80 >> x:
                    on.add((i * ADV[style] + x, y))
                    if bold:
                        on.add((i * ADV[style] + x + 1, y))
    return on


def draw(px, spec, label):
    text, x, y, align = label
    on = text_mask(text, spec["font"])
    w = max(a for a, _ in on) + 1
    x -= {"l": 0, "c": w // 2, "r": w - 1}[align]
    on = {(x + a, y + b) for a, b in on}
    if spec["outline"] is not None:
        for a, b in {(a + dx, b + dy) for a, b in on for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - on:
            px[b][a] = spec["outline"]
    for a, b in on:
        px[b][a] = spec["fill"]
    if spec["under"]:
        base = max(b for _, b in on) + 2
        for a in range(x, x + w):
            px[base][a] = spec["fill"]


def title_bar(px, clut, text):
    """Ship picture: refill the title bar's interior with its flat colour and centre text in its brightest colour.
    The interior: the fill colour at (217, 5), rows where column 217 keeps it, leftwards to the bar's border."""
    f = px[5][217]
    y0 = next(y for y in range(30) if px[y][217] == f)
    y1 = next(y for y in range(y0, 40) if px[y][217] != f)
    x1 = next(x for x in range(217, W) if px[5][x] != f)
    x0 = 217
    while not all(px[r][x0 - i] != f for r in (y0 + 1, y1 - 2) for i in range(3)):
        x0 -= 1
    lum = [(c & 31) + (c >> 5 & 31) + (c >> 10 & 31) for c in clut]
    ink = max({px[y][x] for y in range(y0, y1) for x in range(x0, x1)} - {f}, key=lum.__getitem__)
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[y][x] = f
    on = text_mask(text, "big")
    w = max(a for a, _ in on) + 1
    assert w <= x1 - x0, f"{text}: {w} px > bar {x1 - x0}"
    for a, b in on:
        px[y0 + (y1 - y0 - 12) // 2 + b][x0 + (x1 - x0 - w) // 2 + a] = ink


def pictures(mps):
    return [(pos, n, dec) for pos, n, dec in scan_bpe.streams(mps)]


def edit(mps, specs):
    """(new file bytes, {k: edited pixel rows})."""
    out, edited = bytearray(mps), {}
    streams = pictures(mps)
    n = len(streams)
    counts = struct.unpack_from(f"<{n}H", mps, 2 * n)
    for k, (pos, _, dec) in enumerate(streams):
        if k not in specs:
            continue
        spec, px = specs[k], pixels(dec)
        if "bar" in spec:
            title_bar(px, struct.unpack_from("<16H", mps, 4 * n + 32 * k), spec["bar"])
        for box, _ in spec.get("labels", []):
            erase(px, box, spec["erase"])
        for _, label in spec.get("labels", []):
            draw(px, spec, label)
        edited[k] = px
        new = bpe.compress(packed(px, dec[len(px) * W // 2:]))
        assert bpe.decompress(new)[0] == packed(px, dec[len(px) * W // 2:])
        if len(new) > counts[k] * 0x800:
            raise ValueError(f"picture {k}: {len(new):#x} bytes > slot {counts[k] * 0x800:#x}")
        out[pos:pos + counts[k] * 0x800] = new.ljust(counts[k] * 0x800, b"\0")
    return bytes(out), edited


def build(tree):
    """{disc path: edited file bytes}."""
    return {rel: edit((tree / rel).read_bytes(), specs)[0] for rel, specs in FILES.items()}


def main():
    from PIL import Image
    outdir = Path(sys.argv[1])
    outdir.mkdir(parents=True, exist_ok=True)
    for rel, specs in FILES.items():
        mps = (ROOT / "work/disc/tree" / rel).read_bytes()
        n = len(pictures(mps))
        for k, px in edit(mps, specs)[1].items():
            c = struct.unpack_from("<16H", mps, 4 * n + 32 * k)
            pal = [v for x in c for v in ((x & 31) * 8, (x >> 5 & 31) * 8, (x >> 10 & 31) * 8)]
            img = Image.new("P", (W, len(px)))
            img.putdata([v for row in px for v in row])
            img.putpalette(pal)
            out = outdir / f"{Path(rel).stem}_{k}.png"
            img.convert("RGB").resize((W * 2, len(px) * 2), Image.NEAREST).save(out)
            print(out)


if __name__ == "__main__":
    main()
