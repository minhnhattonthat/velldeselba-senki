"""worldmap.py: English place names on the Old Sage's map pictures (2D/OTHER/WORLD.MPS, docs/re/graphics.md).

    python -X utf8 tools/worldmap.py OUTDIR    # writes OUTDIR/k.png previews (2x) of the edited pictures

WORLD.MPS: 0x800 header (u16 sector offsets of 6 BPE streams from 0x800, u16 sector counts, then 16-colour CLUTs
at 0x18 + 32k), then the streams. Each stream is a 224 px wide 4bpp picture (112 bytes per row). Labels are erased
(their colours inside the box are refilled from neighbouring pixels) and redrawn with Spleen (fonts/, BSD-2).
build.py calls build() and writes the file when it differs from the original.
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

REL = "2D/OTHER/WORLD.MPS"
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


def pictures(mps):
    return [(pos, n, dec) for pos, n, dec in scan_bpe.streams(mps)]


def edit(mps):
    """(new file bytes, {k: edited pixel rows})."""
    out, edited = bytearray(mps), {}
    counts = struct.unpack_from("<6H", mps, 12)
    for k, (pos, n, dec) in enumerate(pictures(mps)):
        if k not in PICTURES:
            continue
        spec, px = PICTURES[k], pixels(dec)
        for box, _ in spec["labels"]:
            erase(px, box, spec["erase"])
        for _, label in spec["labels"]:
            draw(px, spec, label)
        edited[k] = px
        new = bpe.compress(packed(px, dec[len(px) * W // 2:]))
        assert bpe.decompress(new)[0] == packed(px, dec[len(px) * W // 2:])
        if len(new) > counts[k] * 0x800:
            raise ValueError(f"WORLD.MPS picture {k}: {len(new):#x} bytes > slot {counts[k] * 0x800:#x}")
        out[pos:pos + counts[k] * 0x800] = new.ljust(counts[k] * 0x800, b"\0")
    return bytes(out), edited


def build(tree):
    return edit((tree / REL).read_bytes())[0]


def main():
    from PIL import Image
    outdir = Path(sys.argv[1])
    outdir.mkdir(parents=True, exist_ok=True)
    mps = (ROOT / "work/disc/tree" / REL).read_bytes()
    for k, px in edit(mps)[1].items():
        c = struct.unpack_from("<16H", mps, 0x18 + 32 * k)
        pal = [v for x in c for v in ((x & 31) * 8, (x >> 5 & 31) * 8, (x >> 10 & 31) * 8)]
        img = Image.new("P", (W, len(px)))
        img.putdata([v for row in px for v in row])
        img.putpalette(pal)
        img.convert("RGB").resize((W * 2, len(px) * 2), Image.NEAREST).save(outdir / f"{k}.png")
        print(outdir / f"{k}.png")


if __name__ == "__main__":
    main()
