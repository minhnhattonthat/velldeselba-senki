"""survey.py: per-file count of Shift-JIS text runs that read as text (contain kana), over the dumped disc tree.

    python -X utf8 tools/survey.py [work/disc/tree] > work/survey.txt"""
import re
import sys
from pathlib import Path

KANA = re.compile(r"[ぁ-ヿ]")
# one SJIS char: double-byte lead 81-9F/E0-EF + trail 40-FC (not 7F)
RUN = re.compile(rb"(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\x20-\x7e]){4,}")


def runs(data):
    for m in RUN.finditer(data):
        try:
            s = m.group().decode("cp932")
        except UnicodeDecodeError:
            continue
        if len(KANA.findall(s)) >= 2:
            yield m.start(), s


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "work/disc/tree")
    for f in sorted(root.rglob("*")):
        if f.is_file() and f.stat().st_size < 4 << 20:
            hits = list(runs(f.read_bytes()))
            if hits:
                chars = sum(len(s) for _, s in hits)
                print(f"{len(hits):5} {chars:7} {f.relative_to(root).as_posix()}  e.g. {hits[len(hits)//2][1][:40]!r}")
