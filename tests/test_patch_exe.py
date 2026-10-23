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
