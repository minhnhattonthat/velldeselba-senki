"""scenes.py: the warp scene list. Map index = entry in the resident EXE/MPS name table (RAM 0x8001610C, 22-byte
entries, read from a RAM dump). Warp: tools/debug/warp.lua (docs/re/debug.md).

    python -X utf8 tools/debug/scenes.py work/qa/m1ram/ram_000004.bin   # print index -> name
"""
import sys

TABLE, STRIDE = 0x1610C, 22


def names(ram):
    out = []
    for i in range(256):
        raw = ram[TABLE + i * STRIDE:TABLE + (i + 1) * STRIDE].split(b"\0")[0]
        if not raw.startswith(b"\\"):
            break
        out.append(raw.decode("ascii"))
    return out


if __name__ == "__main__":
    for i, n in enumerate(names(open(sys.argv[1], "rb").read())):
        print(i, n)
