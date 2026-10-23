"""textview.py: show any script text in the 2D dialogue box, for width checks (docs/re/debug.md).

    python -X utf8 tools/debug/textview.py "Name:<R>line one<R>line two<W><E>" --out work/qa/view [--pages 2]

Boots the built disc from work/states/en_intro_fmv.sstate, walks to the G10 NPC, talks, and textview.lua swaps
the box's string for TEXT. One shot per page (f<frame>.png) plus a sheet.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import textcodec
from skill import SCRIPTS

# from en_intro_fmv: the FMV ends and G10 loads (~f1100); walk to the NPC by the door and talk
WALK = [(1500, "-"), (150, "up"), (100, "left"), (6, "circle"), (90, "-")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("--out", default="work/qa/view")
    ap.add_argument("--pages", type=int, default=1)
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    steps = WALK + [(6, "circle"), (90, "-")] * (a.pages - 1)
    route = out / "route.txt"
    route.write_text("".join(f"{n} {k}\n" for n, k in steps), encoding="utf-8")
    frames, shots = 0, []
    for n, k in steps:
        frames += n
        if k == "-" and frames > WALK[0][0]:
            shots.append(frames - 2)
    cmd = [sys.executable, "-X", "utf8", str(Path(SCRIPTS) / "emu.py"), str(ROOT / "build/velldeselba_en.cue"),
           "--out", str(out), "--state-in", str(ROOT / "work/states/en_intro_fmv.sstate"), "--route", str(route),
           "--frames", str(frames), "--shots", ",".join(map(str, shots)), "--debugger",
           "--script", str(ROOT / "tools/debug/textview.lua"),
           "--var", f'VIEW_HEX="{textcodec.encode(a.text).hex()}"']
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
