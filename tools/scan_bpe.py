"""scan_bpe.py: find BPE streams (tools/bpe.py) in disc files and report how much Japanese each holds.

    python -X utf8 tools/scan_bpe.py [--align 4] FILE.. > work/bpe_scan.txt
A stream counts when its u32 length fits the file and the blocks end exactly on it."""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bpe
import survey


def streams(d, align=4):
    pos = 0
    while pos + 8 <= len(d):
        n = struct.unpack_from("<I", d, pos)[0]
        if 16 <= n <= len(d) - pos - 4:
            try:
                ok = _exact(d, pos, n)
            except IndexError:
                ok = False
            if ok:
                yield pos, n, bpe.decompress(d, pos)[0]
                pos += (n + 4 + align - 1) // align * align
                continue
        pos += align


def _exact(d, pos, n):
    """Re-walk the block headers: the last block must end exactly at pos+n."""
    p, end = pos + 4, pos + 4 + n
    while p < end:
        c = 0
        while c < 256:
            count = d[p]; p += 1
            if count > 127:
                c += count - 127; count = 0
            if c > 256:
                return False
            if c == 256:
                break
            for _ in range(count + 1):
                left = d[p]; p += 1
                if left != c:
                    p += 1
                c += 1
            if c > 256:
                return False
        size = d[p] << 8 | d[p + 1]
        p += 2 + size
    return p == end


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--align", type=int, default=4)
    a = ap.parse_args()
    for f in a.files:
        d = Path(f).read_bytes()
        for pos, n, out in streams(d, a.align):
            jp = sum(len(s) for _, s in survey.runs(out))
            print(f"{f} {pos:#08x} {n:#07x} -> {len(out):#07x} jp={jp}")
