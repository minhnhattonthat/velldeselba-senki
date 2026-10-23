# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5 (marker build) for 2D map text; phases 1-4 done for it. 3D missions and EXE strings still at phase 1.
  Last build: `python -X utf8 tools/build.py --marker` (2026-10-23), boots, markers show in dialogue.
- **Done:**
  - Step 0, rulings D1-D7, disc rebuild identical (`docs/re/disc.md`).
  - BPE codec + recompressor that beats the original (`tools/bpe.py`, `docs/re/compression.md`).
  - English engine: digraph-cell hook on Krom2RawAdd, prepended to all 77 EXEs at 0x8001F000 (`docs/re/font.md`).
    Dialogue box: 34 chars/line, 3 lines, 32 on a page's last line (wait cursor).
  - 2D map text: 18,624 strings (5,762 unique, ~160k JP chars) in `script/maps/**.json`, roundtrip-tested.
    Build inserts `en` (falls back to `jp`); `--marker` puts `<map>:<index>` markers everywhere; all streams fit.
  - Warp tool v1 (`docs/re/debug.md`): map index poke from `work/states/intro_fmv.sstate` (2D maps 0-59).
- **Next:**
  1. EXE strings (place-name banners, menus, items, names; ~2.8k unique chars, repeated per map EXE): extract
     with pointer xrefs (`lui/addiu`), in-place when it fits, else relocate into the hook block.
  2. Marker tour of all 60 maps (warp + talk) to find non-text entries and other box variants (choices, menus,
     profiles `<F61>`), then the width gate per variant.
  3. 3D mission text: bytecode with u16-length-prefixed SJIS, CRLF lines (`docs/re/text.md`); 3D warps.
  4. Name entry grid, graphics text survey (title logo, banners), FMV subtitle check, staff roll (STAFF.EXE).
  5. Translation batches (phase 6) once the width gate is measured; glossary first.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
- **States:** `work/states/intro_fmv.sstate` (original disc, f30000 of New Game), `en_intro_fmv.sstate` (built
  disc), `map1_talk.sstate`, `tutorial.sstate`. Regenerate after EXE size changes (`docs/re/debug.md`).
