"""extract.py: dump every 2D map string table into script/maps/<path>.json (docs/re/text.md).

    python -X utf8 tools/extract.py [--stats]

Each file: {"file": "2D/GMPS/G10_00.MPS", "streams": [{"pos": "0x52800", "lines": [{"id", "jp", "en"}]}]}.
Existing "en" fields are kept when the "jp" is unchanged, so re-extracting never loses a translation.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import maptext
import textcodec

TREE = ROOT / "work/disc/tree"
SCRIPT = ROOT / "script/maps"


def mps_files():
    return sorted(p for p in TREE.rglob("*.MPS") if not p.relative_to(TREE).as_posix().startswith("3D/"))


def extract(path):
    rel = path.relative_to(TREE).as_posix()
    streams = []
    for pos, n, dec, strings in maptext.text_streams(path.read_bytes()):
        lines = [{"id": f"{rel[:-4]}@{pos:x}#{i}", "jp": textcodec.decode(s), "en": ""} for i, s in enumerate(strings)]
        streams.append({"pos": f"{pos:#x}", "lines": lines})
    return {"file": rel, "streams": streams}


def merge(new, old):
    keep = {l["id"]: l for s in old.get("streams", []) for l in s["lines"]}
    for s in new["streams"]:
        for l in s["lines"]:
            o = keep.get(l["id"])
            if o and o["jp"] == l["jp"]:
                l["en"] = o["en"]
    return new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    total = uniq = chars = 0
    seen = set()
    for p in mps_files():
        data = extract(p)
        if not data["streams"]:
            continue
        out = SCRIPT / (data["file"][:-4] + ".json")
        if out.is_file():
            data = merge(data, json.loads(out.read_text(encoding="utf-8")))
        if not a.stats:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        for s in data["streams"]:
            for l in s["lines"]:
                total += 1
                if l["jp"] not in seen:
                    seen.add(l["jp"]); uniq += 1
                    chars += sum(1 for c in l["jp"] if ord(c) > 0x7F and c != "　")
    print(f"{total} strings, {uniq} unique, {chars} unique JP chars (no padding)")


if __name__ == "__main__":
    main()
