"""logo.py: English title logo (docs/re/graphics.md), on all three copies of the art:
BEL256T.TIM (3D title screen, faded in over the flight), OPEN.MPS (title menu, logo on the blueprint) and
BERU_FL2.DAT (small logo on the loading screen; the plane flying over it is a separate sprite on the same sheet).

    python -X utf8 tools/logo.py OUTDIR    # writes OUTDIR/<file>.png previews (3x), old and new stacked

Only the lettering changes: the plane, TM and (c) line keep their pixels, and the images keep their size, place
and palette, so the game's fades and the loading-screen plane run as before. The English is Anton (fonts/, OFL),
stretched to each Japanese line's box; every new pixel takes the colour of the nearest old letter pixel (rim from
rim, inside from inside), which keeps the art's gradient, grain and outline. build.py writes what build() returns.
"""
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import tims

FONT = ROOT / "fonts/Anton-Regular.ttf"
TITLE = ("VELLDESELBA", "SENKI")

# file -> where the image is, rects (x0, y0, x1, y1) of art to keep (plane, TM, (c) line), and per line of the
# title the box the English is stretched to and the rect its colours are taken from (the old line without ベ, whose
# own gradient runs along its diagonal).
IMAGES = {
    "BEL256T.TIM": dict(tim=0, keep=[(83, 43, 126, 99), (233, 78, 256, 96), (0, 96, 256, 112)],
                        lines=[((14, 3, 245, 47), (70, 0, 256, 45)), ((128, 45, 232, 96), (126, 43, 233, 97))]),
    "OPEN.MPS": dict(tim=0x65EA0, blueprint=True, keep=[(105, 80, 156, 133), (280, 115, 320, 140), (0, 138, 320, 160)],
                     lines=[((38, 28, 296, 74), (90, 20, 300, 76)), ((160, 78, 272, 137), (156, 74, 280, 140))]),
    "BERU_FL2.DAT": dict(raw=(0x7C, 136, 48, 0xD3C), keep=[(111, 0, 136, 48)], track=0.2,  # small: wide gaps so rims don't merge
                         lines=[((1, 0, 107, 22), (22, 0, 111, 22)), ((55, 23, 105, 47), (50, 22, 111, 48))]),
}


def load(d, spec):
    """(indices HxW, CLUT colours, pixel data offset, bpp)."""
    if "raw" in spec:
        o, w, h, c = spec["raw"]
        px = np.frombuffer(d, np.uint8, w * h // 2, o)
        idx = np.stack([px & 15, px >> 4], 1).reshape(h, w)
        return idx, struct.unpack_from("<16H", d, c), o, 4
    bpp, w, h, clut, data, end = tims.parse(d, spec["tim"])
    assert bpp == 1, "8bpp TIM expected"
    return np.frombuffer(data, np.uint8).reshape(h, w).copy(), clut, end - len(data), 8


def store(d, idx, o, bpp):
    flat = idx.astype(np.uint8)
    raw = (flat[:, 0::2] | flat[:, 1::2] << 4).tobytes() if bpp == 4 else flat.tobytes()
    return d[:o] + raw + d[o + len(raw):]


def rgb(clut):
    c = np.array(clut, np.int32)
    return np.stack([(c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8], 1)


def rect(shape, r):
    m = np.zeros(shape, bool)
    m[r[1]:r[3], r[0]:r[2]] = True
    return m


def pieces(idx, clut, spec):
    """(Japanese lettering, art to keep) masks. The pieces touch (plane, 戦 and (c) are one blob), so keep is by rect."""
    if spec.get("blueprint"):  # opaque picture: the logo is the warm (red >= blue) pixels
        col = rgb(clut)[idx]
        ink = col[..., 0] >= col[..., 2] + 8
    else:
        ink = np.array(clut)[idx] != 0  # colour 0 is transparent
    keep = ink & np.logical_or.reduce([rect(idx.shape, r) for r in spec["keep"]])
    return ink & ~keep, keep


def text(word, w, h, track):
    """Mask (h, w) of word in Anton, letters track em apart, stretched to fill w x h."""
    f = ImageFont.truetype(str(FONT), 200)
    img = Image.new("L", (int(f.getlength(word) + 200 * track * len(word)) + 40, 300))
    x = 20
    for ch in word:
        ImageDraw.Draw(img).text((x, 20), ch, font=f, fill=255)
        x += f.getlength(ch) + 200 * track
    return np.asarray(img.crop(img.getbbox()).resize((w, h), Image.LANCZOS)) >= 128


def take(out, idx, dst, src):
    """out[dst] = colour of the nearest src pixel, preferring the same row (keeps the vertical gradient)."""
    iy, ix = ndimage.distance_transform_edt(~src, sampling=(1, 0.3), return_indices=True)[1]
    out[dst] = idx[iy[dst], ix[dst]]


def closest(pal, used, col):
    """Index in used whose colour is nearest to each RGB row of col."""
    return used[((col[:, None, :] - pal[used][None]) ** 2).sum(2).argmin(1)]


def inpaint(out, clut, hole, steps=400):
    """Fill hole on an opaque picture: smooth fill from its edge, then the nearest colour the picture uses outside."""
    pal = rgb(clut).astype(float)
    img = pal[out]
    img[hole] = pal[out[~hole]].mean(0)
    for _ in range(steps):
        avg = sum(np.roll(img, s, a) for s in (-1, 1) for a in (0, 1)) / 4
        img[hole] = avg[hole]
    out[hole] = closest(pal, np.unique(out[~hole]), img[hole])


def redraw(idx, clut, spec):
    old, keep = pieces(idx, clut, spec)
    kept = np.logical_or.reduce([rect(idx.shape, r) for r in spec["keep"]])
    out = idx.copy()
    if spec.get("blueprint"):  # the old letters' blended edge and drop shadow go too
        inpaint(out, clut, ndimage.binary_dilation(old, iterations=4) & ~kept)
    else:
        out[old] = idx[0, 0]  # transparent
    col = rgb(clut)[idx]
    old_rim = old & ~ndimage.binary_erosion(old)
    old_core = ndimage.binary_erosion(old, iterations=2) & (col.min(2) < 120)  # not the whitish inner rims of 戦記
    lines, r1 = [], spec.get("rim", 1)
    for word, (box, src) in zip(TITLE, spec["lines"]):
        x0, y0, x1, y1 = box  # glyphs r1 px inside the box, the rim around them fills it
        g = np.zeros_like(old)
        g[y0 + r1:y1 - r1, x0 + r1:x1 - r1] = text(word, x1 - x0 - 2 * r1, y1 - y0 - 2 * r1, spec.get("track", 0.06))
        g &= ~keep  # the plane stays in front
        rim = ndimage.binary_dilation(g) & ~g & ~keep if r1 else np.zeros_like(g)
        lines.append((g, rim, rect(idx.shape, src)))
    if spec.get("blueprint"):  # drop shadow down-right, like the old letters'
        ink = np.logical_or.reduce([g | rim for g, rim, _ in lines])
        shadow = (np.roll(ink, (2, 2), (0, 1)) | np.roll(ink, (3, 3), (0, 1))) & ~ink & ~kept
        pal = rgb(clut).astype(float)
        out[shadow] = closest(pal, np.unique(idx), pal[out[shadow]] * 0.55)
    for g, rim, r in lines:
        take(out, idx, rim, old_rim & r)
        take(out, idx, g, old_core & r)
    return out


def edit(d, spec):
    idx, clut, o, bpp = load(d, spec)
    out = redraw(idx, clut, spec)
    return store(d, out, o, bpp), idx, out, clut


def build(tree):
    """{disc path: edited file bytes}."""
    return {rel: edit((tree / rel).read_bytes(), spec)[0] for rel, spec in IMAGES.items()}


def main():
    outdir = Path(sys.argv[1])
    outdir.mkdir(parents=True, exist_ok=True)
    for rel, spec in IMAGES.items():
        d = (ROOT / "work/disc/tree" / rel).read_bytes()
        _, idx, out, clut = edit(d, spec)
        pal = rgb(clut)
        img = Image.fromarray(np.concatenate([pal[idx], pal[out]]).astype(np.uint8))
        p = outdir / f"{Path(rel).stem}.png"
        img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(p)
        print(p)


if __name__ == "__main__":
    main()
