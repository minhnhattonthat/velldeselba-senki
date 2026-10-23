"""fmv.py: English subtitles burned into the FMVs (docs/re/fmv.md).

    python -X utf8 tools/fmv.py [n ...]    rebuild work/fmv/out/STR/STRn.STR for movies n (default: all with subs)

script/fmv/STRn.tsv: start<TAB>end<TAB>jp<TAB>en per line, seconds from the movie start (faster-whisper timings,
VAD off). Frames are decoded once to PNG, the English is drawn on every frame it spans (DejaVu Sans Bold, black
outline, bottom centre), and jPSXdec -replaceframes (partial-replace: only changed macroblocks inside the subtitle
band) re-encodes them into a copy of the STR. Cached by a hash of the .tsv and this file; build.py takes the
outputs. Needs Java and tools/jpsxdec (jPSXdec v2.0).
"""
import hashlib
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work/disc/tree"
WORK = ROOT / "work/fmv"
OUT = WORK / "out"
JAR = ROOT / "tools/jpsxdec/jpsxdec_v2.0/jpsxdec.jar"
FONT = ROOT / "fonts/DejaVuSans-Bold.ttf"
FPS = 150 / 10.01  # 2x CD speed, 10.01 sectors per frame
SIZE, BAND = 11, 32  # font px; subtitle band: the bottom 2 macroblock rows (the only area re-encoded)


def jpsxdec(*args):
    r = subprocess.run(["java", "-jar", str(JAR), *map(str, args)], capture_output=True, text=True)
    if r.returncode or "error" in r.stdout.lower():
        sys.exit(f"jpsxdec {' '.join(map(str, args))} failed:\n{r.stdout}{r.stderr}")


def subs(n):
    rows = []
    for l in (ROOT / f"script/fmv/STR{n}.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        start, end, _jp, en = l.split("\t")
        if en:
            rows.append((float(start), float(end), en))
    return rows


def lines(en, font, width):
    """Word-wrap to the frame width, at most 2 lines."""
    words, out = en.split(), [""]
    for w in words:
        cand = f"{out[-1]} {w}".strip()
        if font.getlength(cand) <= width or not out[-1]:
            out[-1] = cand
        else:
            out.append(w)
    assert len(out) <= 2, f"subtitle too long for 2 lines: {en}"
    return out


def burn(img, en, font):
    """Text on a black box snapped to 16x16 macroblocks: flat blocks cost almost no bits, so the re-encoded frame
    (same sector budget) keeps the letters sharp; over busy video they washed out."""
    d = ImageDraw.Draw(img)
    rows = lines(en, font, img.width - 12)
    y = img.height - 4 - SIZE * len(rows) - 2 * (len(rows) - 1)
    w = max(font.getlength(r) for r in rows)
    x0, x1 = (img.width - w) / 2 - 3, (img.width + w) / 2 + 3
    d.rectangle((int(x0) // 16 * 16, img.height - BAND, -(-int(x1) // 16) * 16 - 1, img.height - 1), fill="black")
    for r in rows:
        x = (img.width - font.getlength(r)) / 2
        d.text((x, y), r, font=font, fill="white", stroke_width=1, stroke_fill="black")
        y += SIZE + 2


def movie(n):
    src, out = TREE / f"STR/STR{n}.STR", OUT / f"STR/STR{n}.STR"
    tsv = ROOT / f"script/fmv/STR{n}.tsv"
    key = hashlib.sha1(tsv.read_bytes() + Path(__file__).read_bytes()).hexdigest()
    stamp = out.with_suffix(".sha1")
    if out.is_file() and stamp.is_file() and stamp.read_text() == key:
        return out
    frames = WORK / f"frames/STR{n}"
    if not frames.is_dir():
        jpsxdec("-f", src, "-x", WORK / f"STR{n}.idx")
        jpsxdec("-x", WORK / f"STR{n}.idx", "-i", 0, "-vf", "png", "-noaud", "-dir", frames)
    files = sorted(frames.glob("*.png"))
    burned = WORK / f"burned/STR{n}"
    shutil.rmtree(burned, ignore_errors=True)
    burned.mkdir(parents=True)
    font = ImageFont.truetype(str(FONT), SIZE)
    xml = ['<?xml version="1.0"?>', '<str-replace version="0.3">']
    for start, end, en in subs(n):
        for k in range(round(start * FPS), min(round(end * FPS), len(files) - 1) + 1):
            img = Image.open(files[k]).convert("RGB")
            burn(img, en, font)
            p = burned / f"{k:05d}.png"
            img.save(p)
            xml.append(f'  <replace frame="{k}">{p}</replace>')
    xml.append("</str-replace>")
    (burned / "replace.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, out)
    jpsxdec("-f", out, "-x", OUT / f"STR{n}.idx")
    jpsxdec("-x", OUT / f"STR{n}.idx", "-i", 0, "-replaceframes", burned / "replace.xml")
    stamp.write_text(key)
    return out


def built():
    """{disc path: patched STR} for every movie with subtitles."""
    return {f"STR/{p.stem}.STR": movie(p.stem[3:]) for p in sorted((ROOT / "script/fmv").glob("STR*.tsv"))}


if __name__ == "__main__":
    for n in sys.argv[1:] or [p.stem[3:] for p in sorted((ROOT / "script/fmv").glob("STR*.tsv"))]:
        print(movie(n))
