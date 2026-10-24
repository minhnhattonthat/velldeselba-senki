"""tour2d.py: warp to every 2D map (or the given indices) and shoot it, for marker/graphics tours.

    python -X utf8 tools/debug/tour2d.py [--out work/qa/tour2d] [--state work/states/en_intro_fmv.sstate] [0 5 40..]

Per map: warp.lua from the state, shots while the place banner shows and after it; then one contact sheet of
all maps (tour.png, one tile per map, name in index.txt). Uses the built disc.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SCRIPTS

SHOTS = (1900, 2600)  # banner, then the plain map (warped from the built-disc state: the map shows ~f1800)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("maps", nargs="*", type=int)
    ap.add_argument("--out", default="work/qa/tour2d")
    ap.add_argument("--state", default="work/states/en_intro_fmv.sstate")
    a = ap.parse_args()
    names = [l.split(" ", 1)[1] for l in (ROOT / "tools/debug/scenes.txt").read_text().splitlines()]
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    index, tiles = [], []
    for m in a.maps or range(60):
        d = out / f"m{m:02d}"
        r = subprocess.run([sys.executable, "-X", "utf8", str(Path(SCRIPTS) / "emu.py"),
                            str(ROOT / "build/velldeselba_en.cue"), "--out", str(d), "--state-in", str(ROOT / a.state),
                            "--script", str(ROOT / "tools/debug/warp.lua"), "--var", f"MAP={m}",
                            "--var", "WARP_FRAMES=1800", "--frames", str(SHOTS[-1] + 2),
                            "--shots", ",".join(map(str, SHOTS))], capture_output=True, text=True)
        shots = [d / f"f{s:06d}.png" for s in SHOTS]
        ok = r.returncode == 0 and all(p.is_file() for p in shots)
        index.append(f"m{m:02d} {names[m]} {'ok' if ok else f'FAIL exit {r.returncode}'}")
        print(index[-1], flush=True)
    old = (out / "index.txt").read_text(encoding="utf-8").splitlines() if a.maps and (out / "index.txt").is_file() else []
    index = sorted({l[:3]: l for l in old + index}.values())  # a rerun of some maps keeps the others' lines
    (out / "index.txt").write_text("\n".join(index) + "\n", encoding="utf-8")
    tiles = [str(p) for m in range(60) for s in SHOTS if (p := out / f"m{m:02d}" / f"f{s:06d}.png").is_file()]
    subprocess.run([sys.executable, "-X", "utf8", str(Path(SCRIPTS) / "sheet.py"), *tiles, "--cols", "4",
                    "--max", "16", "--out", str(out / "tour.png")])


if __name__ == "__main__":
    main()
