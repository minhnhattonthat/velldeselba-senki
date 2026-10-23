"""texttour.py: show many script lines in the 2D dialogue box in one run, one shot per page, for visual QA.

    python -X utf8 tools/debug/texttour.py [--out work/qa/texttour] [--per 25] [ID-REGEX ...]

Without ids it picks up to --per lines from each group: pages split early so no box holds a lone row ("split"),
the widest rows ("wide"), colour codes ("colour"), player/ship names ("names"). Same setup as textview.py (G10 NPC
from en_intro_fmv.sstate); textview.lua hands the box the next listed string on every opening and circle is
pressed every PAGE frames. Writes shots, index.txt (frame -> id) and contact sheets (sheet*.png).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import lint
import textcodec
from skill import SCRIPTS
from textview import WALK

PAGE = 180  # frames per page: a full box types out in ~130 after the box opens


def lines():
    for p in sorted((ROOT / "script/maps").rglob("*.json")):
        for st in json.loads(p.read_text(encoding="utf-8"))["streams"]:
            for l in st["lines"]:
                if "<W>" in l["jp"] and l["en"]:
                    yield l


def pick(per):
    groups = {
        "split": lambda l: l["en"].count("<H>") > l["jp"].count("<H>"),
        "wide": lambda l: max(lint.width(r) for r in re.split("<R>|<H>", l["en"])) >= 17,
        "colour": lambda l: "<P0" in l["en"],
        "names": lambda l: "<F62>" in l["en"].split(":", 1)[-1] or "<F63>" in l["en"],
    }
    out, seen = [], set()
    for g, test in groups.items():
        hits = [l for l in lines() if test(l) and l["en"] not in seen]
        step = max(1, len(hits) // per)
        for l in hits[::step][:per]:
            seen.add(l["en"])
            out.append(l)
    return out


def waits(en):
    """Button presses one string takes: each <W>, plus each full box a page runs past."""
    return sum(max(0, (len(pg.split("<R>")) - 1) // 3) + pg.count("<W>") for pg in en.split("<H>"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--out", default="work/qa/texttour")
    ap.add_argument("--per", type=int, default=25)
    a = ap.parse_args()
    items = [l for l in lines() if any(re.search(p, l["id"]) for p in a.ids)] if a.ids else pick(a.per)
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "list.lua").write_text("VIEW_LIST = {\n" + "".join(f'"{textcodec.encode(l["en"]).hex()}",\n'
                                                            for l in items) + "}\n", encoding="utf-8")
    route = out / "route.txt"
    route.write_text("".join(f"{n} {k}\n" for n, k in WALK), encoding="utf-8")
    start = sum(n for n, _ in WALK)
    presses = sum(waits(l["en"]) + 1 for l in items)
    frames = start + presses * PAGE
    first = -(-start // PAGE) * PAGE  # emu.py's mash presses on multiples of PAGE
    frames = first + presses * PAGE
    shots = [first + k * PAGE - 4 for k in range(presses + 1)]
    cmd = [sys.executable, "-X", "utf8", str(Path(SCRIPTS) / "emu.py"), str(ROOT / "build/velldeselba_en.cue"),
           "--out", str(out), "--state-in", str(ROOT / "work/states/en_intro_fmv.sstate"), "--route", str(route),
           "--frames", str(frames), "--timeout", str(120 + frames // 60), "--shots", ",".join(map(str, shots)), "--mash", str(PAGE),
           "--mash-key", "circle", "--debugger", "--script", str(out / "list.lua"),
           "--script", str(ROOT / "tools/debug/textview.lua")]
    if subprocess.call(cmd):
        sys.exit("emulator run failed")
    opened = [(int(m[1]), int(m[2])) for m in re.finditer(r"f(\d+) item (\d+)", (out / "log.txt").read_text())]
    index = []
    for f in shots:
        cur = [i for fr, i in opened if fr <= f]
        if cur and (out / f"f{f:06d}.png").is_file():
            index.append(f"f{f:06d}\t{items[(cur[-1] - 1) % len(items)]['id']}")
    (out / "index.txt").write_text("\n".join(index) + "\n", encoding="utf-8")
    subprocess.call([sys.executable, "-X", "utf8", str(Path(SCRIPTS) / "sheet.py"), str(out), "--cols", "4",
                     "--out", str(out / "sheet.png")])
    print(f"{len(items)} lines, {len(index)} shots, {len(opened)} box openings")


if __name__ == "__main__":
    main()
