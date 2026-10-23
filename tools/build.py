"""build.py: build the English disc image -> build/velldeselba_en.bin/.cue

    python -X utf8 tools/build.py [--marker] [--spike]

Steps: check the dump, unpack the disc once (work/disc), assemble the glyph hook, patch every EXE, insert text,
rebuild with mkpsxiso. Changed files go to build/files/<path> and the layout points mkpsxiso at them.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom
import datnames
import exetext
import font
import maptext
import missiontext
import namegrid
import patch_exe
import scan_bpe
import staffroll
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


def scripts(kind):
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "script" / kind).rglob("*.json"))]


def memory():
    """jp -> en from every translated line, so a string repeated across maps or EXEs is translated once."""
    tm = {}
    for kind in ("maps", "exe", "missions", "dat"):
        for data in scripts(kind):
            for st in data["streams"]:
                for l in st["lines"]:
                    if l["en"]:
                        tm.setdefault(l["jp"], l["en"])
    return tm


def pick(line, mode, tm, code=textcodec.CODE):
    if mode == "marker":
        return marker(line["id"], line["jp"], code)
    return line["en"] or tm.get(line["jp"], line["jp"])


def patch_exes(hook_bin, mode, tm):
    """Hook every EXE; insert its strings (in place, or relocated into the hook block after the hook code)."""
    tree = DISC / "tree"
    texts = {d["file"]: d for d in scripts("exe")}
    base = patch_exe.HOOK_BASE + (len(hook_bin) + 3) // 4 * 4
    limit = patch_exe.HOOK_BASE + patch_exe.HOOK_SIZE
    errors = []
    for p in sorted(tree.rglob("*")):
        if not (p.suffix.upper() == ".EXE" or p.name == "SCPS_100.27"):
            continue
        rel = p.relative_to(tree).as_posix()
        exe, blob = namegrid.apply(p.read_bytes()), b""
        edits, picked = {}, []
        for st in texts.get(rel, {"streams": []})["streams"]:
            for l in st["lines"]:
                text = pick(l, mode, tm)
                if text != l["jp"]:
                    edits[int(l["id"].rsplit("@", 1)[1], 16)] = textcodec.encode(text)
                    picked.append((int(l["id"].rsplit("@", 1)[1], 16), l["jp"], text))
        if rel == "STAFF.EXE":
            exe = staffroll.align(exe, exetext.refs(exe), picked)
        try:
            try:
                exe, blob = exetext.apply(exe, edits, base, limit)
            except ValueError:
                exe, blob = exetext.apply(exe, edits, base, limit, repack=True)
        except ValueError as e:
            errors.append(f"{rel}: {e}")
        data, n = patch_exe.patch(exe, hook_bin.ljust(base - patch_exe.HOOK_BASE, b"\0") + blob)
        if n or edits:
            write(rel, data)
    if errors:
        sys.exit("EXE text does not fit:\n" + "\n".join(errors))


def insert_spike():
    for (rel, idx), text in SPIKE.items():
        mps = (DISC / "tree" / rel).read_bytes()
        pos, n, dec, strings = maptext.text_streams(mps)[0]
        strings[idx] = textcodec.encode(text)
        write(rel, maptext.replace_stream(mps, pos, n, maptext.build(dec, strings)))


def marker(line_id, jp, code=textcodec.CODE):
    """Same layout as jp, text runs replaced by the id then filler: one full-width char -> two letters."""
    codes = [m.group() for m in code.finditer(jp)]
    texts = re.sub(code.pattern, "\0", jp).split("\0")
    last = line_id.split("/")[-1]
    if "#" in last:  # map line: G10_00@52800#88 -> G1000:88
        name, idx = last.split("#")
        stem = name.split("@")[0].replace("_", "")
    else:  # EXE string: G1000.EXE@800209e0 -> G1000:9e0
        name, addr = last.split("@")
        stem, idx = name.split(".")[0], addr[-3:]
    tag, short = f"{stem}:{idx} ", f":{idx}"
    out, first = [], True
    for i, run in enumerate(texts):
        width = sum(1 if ord(c) < 0x80 else 2 for c in run)
        if run.strip("　 "):
            head = (tag if width >= len(tag) else short) if first else ""
            run = (head + "abcdefghijklmnopqrstuvwxyz" * 3)[:max(width, len(head))]
            first = False
        else:
            run = " " * width
        out.append(run)
        if i < len(codes):
            out.append(codes[i])
    return "".join(out)


def insert_maps(mode, tm):
    """mode 'en': translated lines (others stay Japanese); 'marker': every line as its marker."""
    errors = []
    for data in scripts("maps"):
        rel = data["file"]
        mps = (DISC / "tree" / rel).read_bytes()
        streams = {f"{p:#x}": (p, n, dec) for p, n, dec, _ in maptext.text_streams(mps)}
        changed = False
        for st in data["streams"]:
            pos, n, dec = streams[st["pos"]]
            strings = []
            for l in st["lines"]:
                text = pick(l, mode, tm)
                strings.append(textcodec.encode(text))
                changed |= text != l["jp"]
            try:
                mps = maptext.replace_stream(mps, pos, n, maptext.build(dec, strings))
            except ValueError as e:
                errors.append(f"{rel}: {e}")
        if changed:
            write(rel, mps)
    if errors:
        sys.exit("text does not fit:\n" + "\n".join(errors))


def insert_missions(mode, tm):
    """3D mission message tracks (stream 1 of each mission MPS), same modes as insert_maps."""
    errors = []
    for data in scripts("missions"):
        rel = data["file"]
        mps = (DISC / "tree" / rel).read_bytes()
        pos, n, dec = list(scan_bpe.streams(mps))[1]
        texts = [pick(l, mode, tm, missiontext.CODE3D) for st in data["streams"] for l in st["lines"]]
        if texts == [l["jp"] for st in data["streams"] for l in st["lines"]]:
            continue
        try:
            write(rel, maptext.replace_stream(mps, pos, n, missiontext.build(dec, texts)))
        except ValueError as e:
            errors.append(f"{rel}: {e}")
    if errors:
        sys.exit("mission text does not fit:\n" + "\n".join(errors))


def insert_dat(mode, tm):
    """Name fields of BERU_FL1.DAT, in place."""
    for data in scripts("dat"):
        lines = data["streams"][0]["lines"]
        edits = {int(l["id"].rsplit("@", 1)[1], 16): textcodec.encode(t)
                 for l in lines for t in [pick(l, mode, tm)] if t != l["jp"]}
        if edits:
            try:
                write(data["file"], datnames.apply((DISC / "tree" / data["file"]).read_bytes(), edits))
            except ValueError as e:
                sys.exit(f"name does not fit: {e}")


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
    ap.add_argument("--marker", action="store_true", help="every map line replaced by its id marker")
    a = ap.parse_args()
    check_rom.check()
    unpack()
    shutil.rmtree(FILES, ignore_errors=True)
    FILES.mkdir(parents=True)
    mode = "marker" if a.marker else "en"
    tm = memory()
    patch_exes(hook(), "en" if a.spike else mode, tm)
    if a.spike:
        insert_spike()
    else:
        insert_maps(mode, tm)
        insert_missions(mode, tm)
        insert_dat(mode, tm)
    layout()
    run([str(ROOT / "tools/mkpsxiso/mkpsxiso.exe"), "-y", "-o", str(OUT.with_suffix(".bin")),
         "-c", str(OUT.with_suffix(".cue")), str(BUILD / "layout.xml")], cwd=BUILD)
    print(f"built {OUT.with_suffix('.bin')} ({sum(1 for _ in FILES.rglob('*') if _.is_file())} files changed)")


if __name__ == "__main__":
    main()
