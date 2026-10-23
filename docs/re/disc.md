# Disc layout and files

Dump: `rom.sha1` (SCPS-10027, 1 track MODE2/2352, 520,575,216 bytes). Boot: `SYSTEM.CNF` → `SCPS_100.27`.

- **Rebuild: verified.** `dumpsxiso -x tree -s layout.xml` then `mkpsxiso -y layout.xml` gives a byte-identical .bin
  (SHA-1 matches `rom.sha1`, 2026-10-23, work/disc).
- **Files are opened by name** (guess, strong): every EXE holds ISO paths such as `\2D\AMPS\A01_00.MPS`,
  `cdrom:\3D\GMPS1\HT.EXE;1`, `\XALIB.XA;1`; no LBA tables seen yet. So grown files should survive a rebuild that moves
  LBAs. Verify by booting a build where an early file grew.
- `TITLE.EXE`, `TITLE3.EXE`, `STAFF.EXE` (staff roll, raw SJIS), per-map `2D/<X>MPS/<map>.EXE` and
  `3D/<set>/HT.EXE` are full PS-X EXEs (load 0x80020000); map EXEs replace each other.
- `*.MPS`: a sequence of BPE streams (`compression.md`), sector-aligned, header holds their offsets/sizes
  (layout not decoded yet). `2D/*MPS/<map>_<nn>.MPS` = 2D town/field map data incl. its dialogue; `3D/*/Gnn.MPS`
  = 3D flight missions (mission text too); `D0x.MPS`, `OPEN.MPS` at root.
- `STR/*.STR` (7 FMVs), `TENKY_A.STR` (logo), `XALIB.XA` (voice/music). FMV subtitles: not checked yet.

## Text by location (tools/survey.py, tools/scan_bpe.py → work/bpe_scan.txt)

| Where | Encoding | Size (rough) |
|---|---|---|
| BPE streams in `*.MPS` | SJIS + ASCII control codes, offset table | ~600k chars incl. codes, padding, map-variant duplicates |
| Raw in EXEs (`SCPS_100.27`, `TITLE*.EXE`, map EXEs, `HT.EXE`, `STAFF.EXE`) | SJIS | ~2.8k chars unique (menus, items, names, system msgs, credits) |
