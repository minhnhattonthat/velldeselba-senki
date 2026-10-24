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


def test_fmv_subtitle_lines_balanced():
    import fmv
    from PIL import ImageFont
    font = ImageFont.truetype(str(fmv.FONT), fmv.SIZE)
    a, b = fmv.lines("But Velldeselba already had people living on it.", font, 200)
    assert len(b.split()) > 1 and abs(font.getlength(a) - font.getlength(b)) < 40
    assert fmv.lines("No data.", font, 300) == ["No data."]
