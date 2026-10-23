"""extract.py: dump every 2D map string table into script/maps/<path>.json, every referenced EXE string into
script/exe/<path>.json and every 3D mission message block into script/missions/<path>.json (docs/re/text.md).

    python -X utf8 tools/extract.py [--stats]

Each file: {"file": "2D/GMPS/G10_00.MPS", "streams": [{"pos": "0x52800", "lines": [{"id", "jp", "en"}]}]}.
Existing "en" fields are kept when the "jp" is unchanged, so re-extracting never loses a translation.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import datnames
import exetext
import maptext
import missiontext
import scan_bpe
import textcodec

TREE = ROOT / "work/disc/tree"
SCRIPT = ROOT / "script/maps"
EXE_SCRIPT = ROOT / "script/exe"
MISSION_SCRIPT = ROOT / "script/missions"


def mps_files():
    return sorted(p for p in TREE.rglob("*.MPS") if not p.relative_to(TREE).as_posix().startswith("3D/"))


def extract(path):
    rel = path.relative_to(TREE).as_posix()
    streams = []
    for pos, n, dec, strings in maptext.text_streams(path.read_bytes()):
        lines = [{"id": f"{rel[:-4]}@{pos:x}#{i}", "jp": textcodec.decode(s), "en": ""} for i, s in enumerate(strings)]
        if lines[0]["jp"].count("<E>") > 1:
            continue  # zeroed offset table (B01_10, A10_00): no EXE loads these maps
        streams.append({"pos": f"{pos:#x}", "lines": lines})
    return {"file": rel, "streams": streams}


def mission_files():
    return sorted((TREE / "3D").rglob("*.MPS"))


def extract_mission(path):
    """Message-track blocks of one 3D mission (stream 1): {"file", "streams": [{"pos", "lines": [...]}]}."""
    rel = path.relative_to(TREE).as_posix()
    pos, n, dec = list(scan_bpe.streams(path.read_bytes()))[1]
    lines = [{"id": f"{rel[:-4]}#{i}", "jp": t, "en": ""} for i, t in enumerate(missiontext.blocks(dec))]
    return {"file": rel, "streams": [{"pos": f"{pos:#x}", "lines": lines}] if lines else []}


def extract_dat(path):
    """Name fields of BERU_FL1.DAT (tools/datnames.py)."""
    lines = [{"id": f"BERU_FL1.DAT@{o:x}", "jp": textcodec.decode(raw), "en": ""}
             for o, raw in datnames.names(path.read_bytes())]
    return {"file": "BERU_FL1.DAT", "streams": [{"pos": "dat", "lines": lines}]}


def exe_files():
    return sorted(p for p in TREE.rglob("*") if p.suffix.upper() == ".EXE" or p.name == "SCPS_100.27")


# Not text to translate: name-entry grid rows (the English grid is engine work, docs/re/text.md) and the
# dakuten conversion tables that follow them.
GRID_ROW = re.compile(r"^(<\$20><\$20>|<G\d\d><\$20>)")
DAKUTEN = ("がぎぐげご", "かきくけこ", "ぱぴぷぺぽ", "はひふへほ", "ぁぃぅぇぉ", "あいうえお")


def nontext(jp):
    return bool(GRID_ROW.match(jp)) or jp.startswith(DAKUTEN) and all("ぁ" <= c <= "ヴ" for c in jp)


def extract_exe(path):
    """Referenced SJIS strings of one EXE: {"file", "streams": [{"pos": "exe", "lines": [...]}]}."""
    rel = path.relative_to(TREE).as_posix()
    exe = path.read_bytes()
    r = exetext.refs(exe)
    lines = [{"id": f"{rel}@{a:x}", "jp": jp, "en": ""}
             for a, raw in exetext.strings(exe, r) if a in r
             for jp in [textcodec.decode(raw)] if not nontext(jp)]
    return {"file": rel, "streams": [{"pos": "exe", "lines": lines}] if lines else []}


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
    jobs = ([(p, extract, SCRIPT) for p in mps_files()] + [(p, extract_exe, EXE_SCRIPT) for p in exe_files()]
            + [(p, extract_mission, MISSION_SCRIPT) for p in mission_files()]
            + [(TREE / "BERU_FL1.DAT", extract_dat, ROOT / "script/dat")])
    for p, fn, dest in jobs:
        data = fn(p)
        if not data["streams"]:
            continue
        out = dest / (data["file"] + ".json" if fn in (extract_exe, extract_dat) else data["file"][:-4] + ".json")
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
