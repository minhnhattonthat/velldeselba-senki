import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import bpe

TREE = ROOT / "work/disc/tree"
# (file, stream offset, expanded size, a string inside it)
KNOWN = [
    ("2D/AMPS/A01_00.MPS", 0x56000, 0x2F680, "ベルデセルバの平和のために"),
    ("3D/GMPS1/G00.MPS", 0x800, 0x4D000, None),
]


def test_roundtrip_synthetic():
    text = ("カフィ：Rベルデセルバの平和のために、WE" * 50).encode("cp932")
    for data in (text, text + bytes(range(256)) * 3, b"", b"A"):
        packed = bpe.compress(data)
        assert bpe.decompress(packed) == (data, len(packed))
    assert len(bpe.compress(text)) < len(text) // 4


@pytest.mark.parametrize("name,pos,size,needle", KNOWN)
def test_real_stream(name, pos, size, needle):
    f = TREE / name
    if not f.is_file():
        pytest.skip("disc not dumped (work/disc)")
    out, end = bpe.decompress(f.read_bytes(), pos)
    assert len(out) == size
    if needle:
        assert needle.encode("cp932") in out
    assert bpe.decompress(bpe.compress(out))[0] == out
