"""lint.py: fit and control-code check of every translated line in script/ (the width gate, docs/re/text.md).

    python -X utf8 tools/lint.py [--jp]      exit 1 on any problem; --jp checks the Japanese instead (rule test)

Widths in letters (one 16x15 cell = 2 letters, textcodec.cells):
- dialogue (any string with <W>): 3 rows per box, a page (<H>) longer than 3 rows continues in a new box.
  Rows hold 34 letters; 32 on a row that ends at <W> or that is a box's 3rd row with more rows after it (the
  wait cursor takes the 17th cell, which otherwise wraps into the next box).
- boxes without <W> (item descriptions, profiles): 34 letters per row, no more rows than the Japanese.
- EXE strings without <W> (menus, labels): each row no wider than the Japanese row (same screen footprint).
  Except the staff roll (STAFF.EXE): roles end at the screen centre and names start there, 15 cells each side.
- BERU_FL1.DAT names (ships, parts, items, crew): at most 27 bytes (27 letters); menu widths not measured yet.
- 3D mission blocks: a message ends at <@hh> or a blank line (<R><R>); 3 rows of 30 letters (JP max 15 chars;
  not yet measured on screen).
Codes other than <R>/<W>/<H> must match the Japanese in order; <F62>/<%S> (player name) count as 4 cells,
<F63> (ship name, full-width letters) as 8.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import datnames
import missiontext
import textcodec

LAYOUT = {"R", "W", "H"}
NAME_CELLS = 4
SHIP_CELLS = 8  # ship name <F63>: typed on the grid, stored full-width (one letter per cell), 8 slots like the name
STAFF_CELLS = 15


def limits(i):
    """(exe, cap) for problems() from a line id."""
    if i.startswith("STAFF.EXE@"):
        return False, STAFF_CELLS
    return ".EXE@" in i or "SCPS" in i, 17


def width(row):
    """Cells of one row: text runs (trailing padding ignored: JP 　, or the spaces pad_box adds) plus the player
    name."""
    row = row.split("<W>")[0]
    runs = textcodec.CODE.split(row)[::4]
    return (sum(textcodec.cells(t.rstrip("　 ")) for t in runs) + NAME_CELLS * row.count("<F62>")
            + SHIP_CELLS * row.count("<F63>"))


def codes(s):
    return [m.group() for m in textcodec.CODE.finditer(s) if m.group(1) not in LAYOUT]


def problems(text, jp, exe=False, cap=17):
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
            lim = width(jrows[min(i, len(jrows) - 1)]) if exe else cap
            if width(r) > lim:
                out.append(f"row {i + 1}: {width(r) * 2} letters > {lim * 2}")
    return out


MSG3D = re.compile(r"<@[0-9a-f]{2}>|<R><R>")


def width3d(row):
    return sum(textcodec.cells(t) for t in missiontext.CODE3D.split(row)[::3] if t) + NAME_CELLS * row.count("<%S>")


def problems3d(text, jp):
    """3D mission blocks: messages end at <@hh> or a blank line; up to 3 rows of 15 cells (30 letters)."""
    out = []
    keep =lambda s: [m.group() for m in missiontext.CODE3D.finditer(s) if m.group() != "<R>"]
    if keep(text) != keep(jp):
        out.append(f"codes {keep(text)} != {keep(jp)}")
    for mi, msg in enumerate(MSG3D.split(text)):
        rows = msg.split("<R>")
        while rows and rows[-1] == "":
            rows.pop()
        if len(rows) > 3:
            out.append(f"message {mi + 1}: {len(rows)} rows > 3")
        for i, r in enumerate(rows):
            w = width3d(r)
            if w > 15:
                out.append(f"message {mi + 1} row {i + 1}: {w * 2} letters > 30")
    return out


def main():
    use_jp = "--jp" in sys.argv
    bad = 0
    for kind in ("maps", "exe", "missions", "dat"):
        for p in sorted((ROOT / "script" / kind).rglob("*.json")):
            for st in json.loads(p.read_text(encoding="utf-8"))["streams"]:
                for l in st["lines"]:
                    text = l["jp"] if use_jp else l["en"]
                    if not text:
                        continue
                    if kind == "missions":
                        found = problems3d(text, l["jp"])
                    elif kind == "dat":
                        n = len(textcodec.encode(text))
                        found = [f"{n} bytes > {datnames.FIELD - 1}"] if n > datnames.FIELD - 1 else []
                    else:
                        found = problems(text, l["jp"], *limits(l["id"]))
                    for msg in found:
                        bad += 1
                        print(f"{l['id']}: {msg}")
    print(f"{bad} problems")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
