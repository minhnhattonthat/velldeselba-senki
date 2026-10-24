import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import pytest

import check_rom


def test_rom_pin():
    rom = check_rom.ROOT / "rom"
    if not any(rom.glob("*.bin")):
        pytest.skip("no ROM")
    check_rom.check()


def test_worldmap_edits_only_labelled_pictures():
    import worldmap
    for rel, specs in worldmap.FILES.items():
        src = worldmap.ROOT / "work/disc/tree" / rel
        if not src.is_file():
            pytest.skip("disc not dumped")
        mps = src.read_bytes()
        new, edited = worldmap.edit(mps, specs)
        assert len(new) == len(mps) and set(edited) == set(specs)
        old, out = worldmap.pictures(mps), worldmap.pictures(new)
        assert [p for p, _, _ in old] == [p for p, _, _ in out]
        assert [d for k, (_, _, d) in enumerate(old) if k not in edited] == \
               [d for k, (_, _, d) in enumerate(out) if k not in edited]


def test_routemap_names_packed_apart():
    import routemap
    boxes = [(u, v, u + w, v + h) for u, v, w, h, _ in routemap.pack()]
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        assert x1 <= routemap.W and y1 <= routemap.H
        assert y0 >= routemap.BOTTOM[0] or (x0 >= routemap.SIDE[0] and x1 <= routemap.SIDE[1])  # off map and dots
        for a0, b0, a1, b1 in boxes[i + 1:]:
            assert x1 <= a0 or a1 <= x0 or y1 <= b0 or b1 <= y0


def test_fmv_subtitle_lines_balanced():
    import fmv
    from PIL import ImageFont
    font = ImageFont.truetype(str(fmv.FONT), fmv.SIZE)
    a, b = fmv.lines("But Velldeselba already had people living on it.", font, 200)
    assert len(b.split()) > 1 and abs(font.getlength(a) - font.getlength(b)) < 40
    assert fmv.lines("No data.", font, 300) == ["No data."]
