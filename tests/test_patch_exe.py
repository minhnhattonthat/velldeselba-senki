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
