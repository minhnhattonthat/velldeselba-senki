# Font and glyph drawing

- **Font = BIOS kanji ROM** (verified): every EXE calls the B0:51 stub (Krom2RawAdd: SJIS → 16x15 1bpp bitmap).
  Stub addresses: SCPS_100.27 0x8005C900, TITLE.EXE 0x80047154, A0100.EXE 0x800644CC, HT.EXE (GMPS1) 0x800407B4,
  G1000.EXE 0x800629A4 (in RAM, state `work/states/map1_talk.sstate`).
- G10 map EXE: 4 `jal` to the stub: 0x800625EC, 0x80062878, 0x80064A4C, 0x80064CE0. The one at 0x800625BC is the
  glyph converter: 15 rows x 16 px 1bpp → 4bpp halfwords with fg/bg nibbles (args a1/a2 colours, a3 stride).
- Cells are 16x15 at 320x240; the dialogue box fits ~18 cells x 3 lines. The BIOS ROM has no half-width ASCII.
- **Plan (phase 5 spike):** the inserter encodes English as pairs of 8-px letters in an unused SJIS range
  (e.g. 0xF040-0xF9FC); a hook at each stub call returns a 30-byte cell built from two 8x15 glyphs, and passes other
  codes to the BIOS. No layout changes, 36 chars per line. Upgrade to real VWF only if lines need more.
- **Free RAM candidate:** 0x8001EDF0-0x8001FFFF is zero in both a 2D map and the 3D tutorial dump (guess: unused;
  trap-fill and tour before relying on it). EXEs load at 0x80020000.
