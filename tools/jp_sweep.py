"""jp_sweep.py: Japanese left in the built disc tree, raw and inside every BPE stream (marker-build check).

    python -X utf8 tools/jp_sweep.py [--min 3] [--show 2]

Uses build/files/<path> where the build changed a file, else the original from work/disc/tree. Prints, per file,
the number of SJIS runs holding at least --min kana and a few examples. Compressed text is invisible to
jp_left.py on the disc image; this looks inside the streams.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import scan_bpe
import survey

TREE, FILES = ROOT / "work/disc/tree", ROOT / "build/files"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=3)
    ap.add_argument("--show", type=int, default=2)
    a = ap.parse_args()
    total = 0
    for p in sorted(TREE.rglob("*")):
        if not p.is_file() or p.suffix.upper() in (".STR", ".XA", ".VAB", ".DA"):
            continue
        rel = p.relative_to(TREE).as_posix()
        data = (FILES / rel).read_bytes() if (FILES / rel).is_file() else p.read_bytes()
        hits = [("raw", o, s) for o, s in survey.runs(data)]
        for pos, n, dec in scan_bpe.streams(data):
            hits += [(f"{pos:#x}", o, s) for o, s in survey.runs(dec)]
        hits = [h for h in hits if sum(1 for c in h[2] if "ぁ" <= c <= "ヶ") >= a.min]
        if hits:
            total += len(hits)
            ex = "  ".join(f"{w}@{o:#x} {s[:24]}" for w, o, s in hits[:a.show])
            print(f"{len(hits):5d} {rel}  {ex}")
    print(f"{total} runs")


if __name__ == "__main__":
    main()
