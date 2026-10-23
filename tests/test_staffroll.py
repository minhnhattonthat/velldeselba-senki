import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import staffroll


def test_role_keeps_right_edge_name_untouched():
    exe = bytearray(64)
    struct.pack_into("<IiII", exe, 0, 0x80020100, 16, 48, 6)   # role: 14 cells, ends at 240
    struct.pack_into("<IiII", exe, 16, 0x80020200, 272, 0, 4)  # name column
    refs = {0x80020100: [("ptr", 0)], 0x80020200: [("ptr", 16)]}
    out = staffroll.align(bytes(exe), refs, [(0x80020100, "エグゼクティブプロデューサー", "Executive Producer"),
                                              (0x80020200, "佐藤　明", "Akira Sato")])
    assert struct.unpack_from("<i", out, 4)[0] == 240 - 9 * 16
    assert struct.unpack_from("<i", out, 20)[0] == 272
