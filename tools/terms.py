"""terms.py: recurring proper-noun candidates in script/ for the glossary terms pass (references/translation.md).

    python -X utf8 tools/terms.py [--min 3] > work/terms.txt

Counts katakana runs (2+ chars, ・ allowed inside) and speaker names (text before ： at a line start) over unique
strings, and lists those not yet in glossary.md with their count. Whole runs only, never substrings.
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KATA = re.compile(r"[ァ-ヴー][ァ-ヴー・]*[ァ-ヴー]")
SPEAKER = re.compile(r"(?:^|<[RH]>|<W>)([^<>：]{1,12})：")


def main():
    lim = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 3
    seen, kata, speakers = set(), collections.Counter(), collections.Counter()
    for p in sorted((ROOT / "script").rglob("*.json")):
        for st in json.loads(p.read_text(encoding="utf-8"))["streams"]:
            for l in st["lines"]:
                if l["jp"] in seen:
                    continue
                seen.add(l["jp"])
                kata.update(KATA.findall(l["jp"]))
                speakers.update(s.strip("　") for s in SPEAKER.findall(l["jp"]))
    known = (ROOT / "glossary.md").read_text(encoding="utf-8")
    print("# speakers")
    for s, n in speakers.most_common():
        if n >= lim and f"| {s} |" not in known:
            print(f"{n}\t{s}")
    print("# katakana")
    for s, n in kata.most_common():
        if n >= lim and f"| {s} |" not in known:
            print(f"{n}\t{s}")


if __name__ == "__main__":
    main()
