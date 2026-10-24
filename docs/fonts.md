# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| `fonts/spleen-8x16.bdf` | github.com/fcambus/spleen, 2.2.0 | BSD-2-Clause (`fonts/spleen-LICENSE`) | yes, with the licence text in the README | English half-width letters, two per 16x15 BIOS-font cell (`tools/font.py`, `tools/asm/hook.asm`) | top row dropped (16 → 15 rows; no glyph uses it), 0x7F = blank pad |
| `fonts/spleen-5x8.bdf`, `fonts/spleen-6x12.bdf` | github.com/fcambus/spleen, 2.2.0 | BSD-2-Clause (`fonts/spleen-LICENSE`) | yes, with the licence text in the README | place names on the Old Sage's maps (`tools/worldmap.py`) | none (6x12 drawn bold by the tool) |
| `fonts/Anton-Regular.ttf` | github.com/google/fonts ofl/anton (main, 2026-10-24) | SIL OFL 1.1 (`fonts/anton-OFL.txt`) | yes (only rendered pixels go into the patch) | English title logo (`tools/logo.py`) | none (stretched per line by the tool) |
| `fonts/DejaVuSans-Bold.ttf` | dejavu-fonts.github.io, 2.37 (copy shipped with matplotlib) | Bitstream Vera / DejaVu licence (`fonts/dejavu-LICENSE`) | yes (only rendered pixels go into the patch) | FMV subtitles burned into the movies (`tools/fmv.py`) | none |
