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
