"""build.py: build the English disc image -> build/velldeselba_en.bin/.cue

    python -X utf8 tools/build.py [--marker] [--spike]

Steps: check the dump, unpack the disc once (work/disc), assemble the glyph hook, patch every EXE, insert text,
rebuild with mkpsxiso. Changed files go to build/files/<path> and the layout points mkpsxiso at them.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom
import font
import maptext
import patch_exe
import textcodec

ROM = ROOT / "rom/Velldeselba Senki - Tsubasa no Kunshou (Japan).cue"
DISC = ROOT / "work/disc"
BUILD = ROOT / "build"
FILES = BUILD / "files"
OUT = BUILD / "velldeselba_en"

# Engine-spike text: one line of the first map (G10, NPC by the start). Replaced by script/ files later.
SPIKE = {("2D/GMPS/G10_00.MPS", 88):
         "1234567890abcdefghijABCDEFGHIJ0123456789xyz<R>The quick brown fox jumps over the lazy dog.<R>"
         "MMMMMMMMMMWWWWWWWWWWmmmmmmmmmmwwwwwwwwww<W>"
         "<H>Noipask Soldier:<R>Hey, what took you so long?<R>Commander Odenaude is calling!<W><E>"}


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"{cmd[0]} failed:\n{r.stdout}\n{r.stderr}")
    return r.stdout


def unpack():
    if not (DISC / "layout.xml").is_file():
        DISC.mkdir(parents=True, exist_ok=True)
        run([str(ROOT / "tools/mkpsxiso/dumpsxiso.exe"), "-x", "tree", "-s", "layout.xml", str(ROM)], cwd=DISC)


def hook():
    (BUILD / "font.bin").write_bytes(font.blob())
    run([str(ROOT / "tools/armips/armips.exe"), str(ROOT / "tools/asm/hook.asm")], cwd=ROOT)
    return (BUILD / "hook.bin").read_bytes()


def write(rel, data):
    p = FILES / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def patch_exes(hook_bin):
    tree = DISC / "tree"
    for p in sorted(tree.rglob("*")):
        if p.suffix.upper() == ".EXE" or p.name == "SCPS_100.27":
            data, n = patch_exe.patch(p.read_bytes(), hook_bin)
            if n:
                write(p.relative_to(tree).as_posix(), data)


def insert_text(edits):
    by_file = {}
    for (rel, idx), text in edits.items():
        by_file.setdefault(rel, {})[idx] = text
    for rel, lines in by_file.items():
        mps = (DISC / "tree" / rel).read_bytes()
        for pos, n, dec, strings in maptext.text_streams(mps):
            if max(lines) >= len(strings):
                continue
            for idx, text in lines.items():
                strings[idx] = textcodec.encode(text)
            mps = maptext.replace_stream(mps, pos, n, maptext.build(dec, strings))
            break
        write(rel, mps)


def layout():
    """layout.xml with a source= for every file in build/files (paths absolute, so it runs from any cwd)."""
    xml = (DISC / "layout.xml").read_text(encoding="utf-8")
    changed = {p.relative_to(FILES).as_posix(): p for p in FILES.rglob("*") if p.is_file()}
    stack, out = [], []
    for line in xml.splitlines():
        m = re.search(r'<dir name="([^"]+)"', line)
        if m and not line.rstrip().endswith("/>"):
            stack.append(m.group(1))
        if "</dir>" in line:
            stack.pop()
        m = re.search(r'<file name="([^"]+)"', line)
        if m:
            rel = "/".join(stack + [m.group(1)])
            if rel in changed:
                line = line.replace(f'name="{m.group(1)}"', f'name="{m.group(1)}" source="{changed[rel].as_posix()}"', 1)
        line = line.replace('source="tree"', f'source="{(DISC / "tree").as_posix()}"')
        line = line.replace('file="tree/', f'file="{(DISC / "tree").as_posix()}/')
        out.append(line)
    (BUILD / "layout.xml").write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spike", action="store_true", help="insert the engine-spike line only")
    a = ap.parse_args()
    check_rom.check()
    unpack()
    shutil.rmtree(FILES, ignore_errors=True)
    FILES.mkdir(parents=True)
    patch_exes(hook())
    insert_text(SPIKE if a.spike else {})
    layout()
    run([str(ROOT / "tools/mkpsxiso/mkpsxiso.exe"), "-y", "-o", str(OUT.with_suffix(".bin")),
         "-c", str(OUT.with_suffix(".cue")), str(BUILD / "layout.xml")], cwd=BUILD)
    print(f"built {OUT.with_suffix('.bin')} ({sum(1 for _ in FILES.rglob('*') if _.is_file())} files changed)")


if __name__ == "__main__":
    main()
