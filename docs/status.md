# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5 (marker build + width gate) done for 2D maps, EXE strings, 3D missions and BERU_FL1.DAT names.
  Last build: `python -X utf8 tools/build.py --marker` (2026-10-23), smoke ok, markers in dialogue, menus, tutorial.
- **Done:**
  - Step 0, rulings D1-D7, disc rebuild identical (`docs/re/disc.md`). BPE codec (`docs/re/compression.md`).
  - English engine: digraph-cell hook in all 77 EXEs (`docs/re/font.md`); works in 2D boxes, menus, 3D messages.
  - Script (`script/`, 31,973 strings, 6,690 unique, ~176k JP chars), all roundtrip-tested:
    `maps/` 2D dialogue (dead B01_10/A10_00 dropped), `exe/` menus/labels/credits (incl. data past the entry
    point; name-entry grids and dakuten tables excluded), `missions/` 3D message tracks (174 blocks, incl.
    second-script tracks), `dat/` 211 BERU_FL1.DAT names (ships, parts, guns, ammo, items, crew).
  - Width gate (`docs/re/text.md` §Box widths, enforced by `tools/lint.py` inside `tools/check.py`): dialogue
    3 rows x 34 letters (32 before the wait cursor / on a 3rd row with more after); descriptions 4 x 34;
    3D messages 3 x 30; menus = JP footprint; DAT names <= 27 bytes.
  - Debug: warp v1 (2D maps 0-59), `tools/debug/textview.py` (any text in the G10 talk box), `pclog.lua`.
  - Resident-data signature check (`オユ` at 0x80015A4C) retargeted so names can change (`patch_exe.py`).
- **Next:**
  1. Graphics-text survey (title logo, menu frames, banners, 3D HUD, name-entry arrows) -> `docs/re/graphics.md`.
  2. Debug tool: 3D mission warp (tutorial = G44, reachable by New Game), later-chapter story flags.
  3. English name-entry grids (TITLE player name; per-map ship-name grid at 0x80023200) + default name ミサキ.
  4. 3D printf groups in HT.EXE/DEMO.EXE (0x80079D64...: `%S達は、@`, `%uポイントの@`, level-up, `%sは、@`): only
     group heads are referenced, pieces by base+offset; translate in place or move the group with its code.
  5. Measure menu widths per screen (shop, equipment, item list) before translating EXE/DAT names.
  6. Translation (phase 6): glossary + synopsis, style pilot, batches by map (`references/translation.md`).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
- **States:** `work/states/en_intro_fmv.sstate` (built disc, f30000 of New Game; regenerate after builds that
  change resident code/data, `docs/re/debug.md`), `intro_fmv.sstate` (original), `map1_talk.sstate`,
  `tutorial.sstate` (original disc, G44 tutorial).
