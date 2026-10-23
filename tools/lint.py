"""lint.py: fit and control-code check of every translated line in script/ (the width gate, docs/re/text.md).

    python -X utf8 tools/lint.py [--jp]      exit 1 on any problem; --jp checks the Japanese instead (rule test)

Widths in letters (one 16x15 cell = 2 letters, textcodec.cells):
- dialogue (any string with <W>): 3 rows per box, a page (<H>) longer than 3 rows continues in a new box.
  Rows hold 34 letters; 32 on a row that ends at <W> or that is a box's 3rd row with more rows after it (the
  wait cursor takes the 17th cell, which otherwise wraps into the next box).
- boxes without <W> (item descriptions, profiles): 34 letters per row, no more rows than the Japanese.
- EXE strings without <W> (menus, labels): each row no wider than the Japanese row (same screen footprint).
Codes other than <R>/<W>/<H> must match the Japanese in order; <F62> (player name) counts as 4 cells.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import textcodec

LAYOUT = {"R", "W", "H"}
NAME_CELLS = 4


def width(row):
    """Cells of one row: text runs (trailing full-width padding ignored) plus the player name."""
    row = row.split("<W>")[0]
    runs = textcodec.CODE.split(row)[::4]
    return sum(textcodec.cells(t.rstrip("　")) for t in runs) + NAME_CELLS * row.count("<F62>")


def codes(s):
    return [m.group() for m in textcodec.CODE.finditer(s) if m.group(1) not in LAYOUT]


def problems(text, jp, exe=False):
    out = []
    if codes(text) != codes(jp):
        out.append(f"codes {codes(text)} != {codes(jp)}")
    if "<W>" in jp:
        pages = text.split("<H>")
        for pi, pg in enumerate(pages):
            rows = pg.split("<R>")
            for i, r in enumerate(rows):
                after = [x for x in rows[i + 1:] if x not in ("", "<W><E>", "<E>")]
                lim = 16 if "<W>" in r or (i % 3 == 2 and (after or pi + 1 < len(pages))) else 17
                if width(r) > lim:
                    out.append(f"page {pi + 1} row {i + 1}: {width(r) * 2} letters > {lim * 2}")
    else:
        rows, jrows = text.split("<R>"), jp.split("<R>")
        if len(rows) > len(jrows):
            out.append(f"{len(rows)} rows > {len(jrows)}")
        for i, r in enumerate(rows):
            lim = width(jrows[min(i, len(jrows) - 1)]) if exe else 17
            if width(r) > lim:
                out.append(f"row {i + 1}: {width(r) * 2} letters > {lim * 2}")
    return out


def main():
    use_jp = "--jp" in sys.argv
    bad = 0
    for kind in ("maps", "exe"):
        for p in sorted((ROOT / "script" / kind).rglob("*.json")):
            for st in json.loads(p.read_text(encoding="utf-8"))["streams"]:
                for l in st["lines"]:
                    text = l["jp"] if use_jp else l["en"]
                    if not text:
                        continue
                    for msg in problems(text, l["jp"], kind == "exe"):
                        bad += 1
                        print(f"{l['id']}: {msg}")
    print(f"{bad} problems")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
