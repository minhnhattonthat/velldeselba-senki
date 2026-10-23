import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import maptext
import textcodec

TREE = ROOT / "work/disc/tree"
SCRIPTS = sorted((ROOT / "script/maps").rglob("*.json"))
EXE_SCRIPTS = sorted((ROOT / "script/exe").rglob("*.json"))
MISSION_SCRIPTS = sorted((ROOT / "script/missions").rglob("*.json"))


@pytest.mark.skipif(not TREE.is_dir(), reason="disc not dumped (work/disc)")
@pytest.mark.parametrize("path", EXE_SCRIPTS, ids=lambda p: p.stem)
def test_exe_roundtrip(path):
    import exetext
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = dict(exetext.strings((TREE / data["file"]).read_bytes()))
    for l in data["streams"][0]["lines"]:
        assert textcodec.encode(l["jp"]) == raw[int(l["id"].rsplit("@", 1)[1], 16)], l["id"]


@pytest.mark.skipif(not TREE.is_dir(), reason="disc not dumped (work/disc)")
@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.stem)
def test_roundtrip(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    streams = {f"{pos:#x}": (dec, s) for pos, n, dec, s in maptext.text_streams((TREE / data["file"]).read_bytes())}
    assert [s["pos"] for s in data["streams"]] == list(streams)
    for st in data["streams"]:
        dec, strings = streams[st["pos"]]
        assert [textcodec.encode(l["jp"]) for l in st["lines"]] == strings
        assert maptext.build(dec, strings) == dec  # the whole text region is covered by the table


@pytest.mark.skipif(not TREE.is_dir(), reason="disc not dumped (work/disc)")
def test_dat_roundtrip():
    import datnames
    d = (TREE / "BERU_FL1.DAT").read_bytes()
    data = json.loads((ROOT / "script/dat/BERU_FL1.DAT.json").read_text(encoding="utf-8"))
    edits = {int(l["id"].rsplit("@", 1)[1], 16): textcodec.encode(l["jp"]) for l in data["streams"][0]["lines"]}
    assert datnames.apply(d, edits) == d
    assert len(edits) == len(datnames.names(d))


@pytest.mark.skipif(not TREE.is_dir(), reason="disc not dumped (work/disc)")
@pytest.mark.parametrize("path", MISSION_SCRIPTS, ids=lambda p: p.stem)
def test_mission_roundtrip(path):
    import missiontext
    import scan_bpe
    data = json.loads(path.read_text(encoding="utf-8"))
    dec = list(scan_bpe.streams((TREE / data["file"]).read_bytes()))[1][2]
    texts = [l["jp"] for l in data["streams"][0]["lines"]]
    new = missiontext.build(dec, texts)
    assert missiontext.blocks(new) == texts
    tracks = [missiontext.track(dec, b) for b in missiontext.sections(dec)]
    if all(t is None or t[1] == t[2] for t in tracks):  # no dead compiler source: byte-identical
        assert new == dec


@pytest.mark.skipif(not TREE.is_dir(), reason="disc not dumped (work/disc)")
def test_text_section_grows():
    import scan_bpe
    mps = (TREE / "2D/GMPS/G10_00.MPS").read_bytes()
    pos, n, dec, strings = maptext.text_streams(mps)[0]
    room = (maptext.REGION - maptext.TABLE - sum(map(len, strings))) // len(strings)
    noise = bytes((i * 97) % 0x5F + 0xA0 for i in range(room))  # incompressible-ish letter-pair leads
    big = maptext.build(dec, [s[:-1] + noise + b"E" for s in strings])
    out = maptext.replace_stream(mps, pos, n, big)
    counts = [int.from_bytes(out[o:o + 2], "little") for o in maptext.SECTIONS]
    assert len(out) > len(mps) and 0x1000 + sum(counts) * 0x800 == len(out)
    assert {p: d for p, _, d in scan_bpe.streams(out)}[pos] == big
