import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import exetext

EXE = ROOT / "work/disc/tree/2D/GMPS/G1000.EXE"
NADES = 0x800201E0  # ナデス島, the start island's banner


@pytest.mark.skipif(not EXE.is_file(), reason="disc not dumped (work/disc)")
def test_strings_and_refs():
    exe = EXE.read_bytes()
    s = dict(exetext.strings(exe))
    assert s[NADES] == "ナデス島".encode("cp932")
    r = exetext.refs(exe)
    assert all(a in r for a in s if a < 0x80023B00)  # every real string is referenced


@pytest.mark.skipif(not EXE.is_file(), reason="disc not dumped (work/disc)")
def test_in_place_and_relocate():
    exe = EXE.read_bytes()
    out, blob = exetext.apply(exe, {NADES: b"\xceab"}, 0x8001F700, 0x80020000)
    assert blob == b"" and out[0x800 + NADES - 0x80020000:][:4] == b"\xceab\0"
    long = b"\xc1" * 40
    out, blob = exetext.apply(exe, {NADES: long}, 0x8001F700, 0x80020000)
    assert blob.startswith(long + b"\0")
    new = exetext.refs(out)
    assert 0x8001F700 not in new  # refs() only sees the image range; check the patched words directly
    for ref in exetext.refs(exe)[NADES]:
        if ref[0] == "ptr":
            assert struct.unpack_from("<I", out, ref[1])[0] == 0x8001F700
        else:
            hi = struct.unpack_from("<I", out, ref[1])[0] & 0xFFFF
            lo = struct.unpack_from("<I", out, ref[2])[0] & 0xFFFF
            assert ((hi << 16) + (lo - 0x10000 if lo & 0x8000 and ref[3] != exetext.ORI else lo)) & 0xFFFFFFFF == 0x8001F700
    with pytest.raises(ValueError):
        exetext.apply(exe, {NADES: b"\xc1" * 4000}, 0x8001F700, 0x80020000)
