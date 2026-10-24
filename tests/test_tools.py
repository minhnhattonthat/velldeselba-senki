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


def test_fmv_subtitle_lines_balanced():
    import fmv
    from PIL import ImageFont
    font = ImageFont.truetype(str(fmv.FONT), fmv.SIZE)
    a, b = fmv.lines("But Velldeselba already had people living on it.", font, 200)
    assert len(b.split()) > 1 and abs(font.getlength(a) - font.getlength(b)) < 40
    assert fmv.lines("No data.", font, 300) == ["No data."]
