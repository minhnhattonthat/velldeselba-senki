import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import patch_exe

TREE = ROOT / "work/disc/tree"


@pytest.mark.skipif(not TREE.is_dir(), reason="disc not dumped (work/disc)")
def test_resident_check_retargeted():
    exe = (TREE / "SCPS_100.27").read_bytes()
    assert exe.count(patch_exe.SIG_OLD) == 1
    out, n = patch_exe.patch(exe, b"\0" * 16)
    assert n and patch_exe.SIG_OLD not in out and patch_exe.SIG_NEW in out
    # the new check compares the BERU_FL1.DAT word it now loads (0x8001610C -> file offset 0x610C)
    dat = (TREE / "BERU_FL1.DAT").read_bytes()
    lui, _, lw, ori = struct.unpack("<4I", patch_exe.SIG_NEW)
    assert (lw & 0xFFFF) == 0x610C
    assert struct.unpack_from("<I", dat, 0x610C)[0] == ((lui & 0xFFFF) << 16 | (ori & 0xFFFF))


@pytest.mark.skipif(not TREE.is_dir(), reason="disc not dumped (work/disc)")
def test_name_grid_and_copy_patch():
    import namegrid
    exe = (TREE / "TITLE.EXE").read_bytes()
    out = namegrid.apply(exe)
    top = namegrid.first_row(exe)
    assert len(out) == len(exe) and out[top + 4:top + 14] == "ＡＢＣＤＥ".encode("cp932")
    diff = [i for i in range(len(exe)) if exe[i] != out[i]]
    assert top - 29 * 0x20 <= min(diff) and max(diff) < top + 0x20  # only grid rows change
    patched, _ = patch_exe.patch(out, b"\0" * 16)
    assert exe.count(patch_exe.NAME_COPY_OLD) == 1 and patch_exe.NAME_COPY_NEW in patched


@pytest.mark.skipif(not TREE.is_dir(), reason="disc not dumped (work/disc)")
def test_results3d_keeps_entry_points():
    exe = (TREE / "3D/GMPS1/HT.EXE").read_bytes()
    i = exe.find(patch_exe.RESULTS_JP)
    out = patch_exe.results3d(exe)
    assert len(out) == len(exe) and out[:i] == exe[:i] and out[i + 0xC8:] == exe[i + 0xC8:]
    # the code points 0x1C/0x38/0x60/0xB0/0xB6 into the block (after each '//'): same placeholder there
    for off in (0x1C, 0x38, 0x60, 0xB0, 0xB6):
        assert out[i + off:i + off + 2] == exe[i + off:i + off + 2], hex(off)
    placeholders = lambda b: [b[k:k + 2] for k in range(0, len(b), 2) if b[k:k + 2] in (b"%u", b"%s", b"%S", b"//")]
    assert placeholders(out[i:i + 0xC8]) == placeholders(exe[i:i + 0xC8])
