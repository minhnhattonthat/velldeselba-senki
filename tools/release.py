"""release.py: check -> build -> boot smoke -> leftover Japanese -> visual-QA gate -> xdelta3 patch -> re-apply and
compare -> README + zip.

    python -X utf8 tools/release.py VERSION [--force] [--no-qa]     (e.g. 1.0) -> release/Velldeselba_EN_vVERSION.zip

The patch is against the .bin in rom/ (rom.sha1); the zip holds the patch and README.txt only (no .cue: players keep
their own). --no-qa skips the visual-QA gate for test packages; the publish guard still requires it. Release dirs
stay local (gitignored); publishing is the user's call. The playable image stays in build/.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SCRIPTS

ROM = ROOT / "rom/Velldeselba Senki - Tsubasa no Kunshou (Japan).bin"
BUILT = ROOT / "build/velldeselba_en.bin"
QA = ROOT / "work/qa"
KEEP_JP = {"　〆"}  # name-entry pad + end mark: read by the code as characters (docs/status.md)
JP = re.compile(r"[぀-ヿ一-鿿]")


def run(*cmd):
    if subprocess.run([str(c) for c in cmd], cwd=ROOT).returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}")


def hashes(p):
    md5, sha1, crc = hashlib.md5(), hashlib.sha1(), 0
    with open(p, "rb") as f:
        while b := f.read(1 << 22):
            crc = zlib.crc32(b, crc)
            md5.update(b)
            sha1.update(b)
    return {"size": p.stat().st_size, "crc32": f"{crc:08x}", "md5": md5.hexdigest(), "sha1": sha1.hexdigest()}


def leftover():
    """Script lines that would still show Japanese (empty English, or Japanese inside the English)."""
    tm, bad = {}, []
    files = sorted((ROOT / "script").rglob("*.json"))
    for p in files:
        for st in json.loads(p.read_text(encoding="utf-8"))["streams"]:
            tm.update({l["jp"]: l["en"] for l in st["lines"] if l["en"]})
    for p in files:
        for st in json.loads(p.read_text(encoding="utf-8"))["streams"]:
            for l in st["lines"]:
                en = l["en"] or tm.get(l["jp"], "")
                if (JP.search(en) or (not en and JP.search(l["jp"]))) and l["jp"] not in KEEP_JP:
                    bad.append(f"{l['id']}: {l['jp'][:30]}")
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version")
    ap.add_argument("--force", action="store_true", help="overwrite this version's existing release files")
    ap.add_argument("--no-qa", action="store_true", help="skip the visual-QA gate (test packages only)")
    a = ap.parse_args()
    rel, z = ROOT / "release" / f"v{a.version}", ROOT / "release" / f"Velldeselba_EN_v{a.version}.zip"
    if (rel.exists() or z.exists()) and not a.force:
        sys.exit(f"{rel} exists; pass --force to overwrite")

    run(sys.executable, "-X", "utf8", "tools/check.py")
    run(sys.executable, "-X", "utf8", "tools/build.py")
    run(sys.executable, "-X", "utf8", Path(SCRIPTS) / "emu.py", BUILT.with_suffix(".cue"), "--out", QA / "release_smoke",
        "--route", "tools/routes/boot.txt", "--smoke")
    if bad := leftover():
        sys.exit("still Japanese:\n" + "\n".join(bad[:30]) + f"\n({len(bad)} lines)")
    if not a.no_qa:
        run(sys.executable, "-X", "utf8", Path(SCRIPTS) / "qa_gate.py", "check", QA / "manifest.tsv", QA / "verdicts")

    shutil.rmtree(rel, ignore_errors=True)
    rel.mkdir(parents=True)
    patch = rel / f"Velldeselba_EN_v{a.version}.xdelta"
    run("xdelta3", "-e", "-9", "-f", "-s", ROM, BUILT, patch)
    test = ROOT / "work/release_reapplied.bin"
    run("xdelta3", "-d", "-f", "-s", ROM, patch, test)
    o, b = hashes(ROM), hashes(BUILT)
    if hashes(test)["sha1"] != b["sha1"]:
        sys.exit("re-applied patch differs from the build")
    test.unlink()
    info = (f"{ROM.name}\n  size {o['size']}  CRC32 {o['crc32']}\n  MD5 {o['md5']}\n  SHA-1 {o['sha1']}\n"
            f"Patched .bin: size {b['size']}  CRC32 {b['crc32']}  SHA-1 {b['sha1']}")
    readme = (ROOT / "docs/README.template.txt").read_text(encoding="utf-8")
    (rel / "README.txt").write_text(readme.replace("{VERSION}", a.version).replace("{HASHES}", info)
                                    .replace("{PATCH}", patch.name), encoding="utf-8", newline="\r\n")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as zf:
        for f in sorted(rel.iterdir()):
            zf.write(f, f.name)
    print(z, f"patch sha1 {hashes(patch)['sha1']}")


if __name__ == "__main__":
    main()
