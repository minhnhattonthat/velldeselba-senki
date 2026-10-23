# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| `fonts/spleen-8x16.bdf` | github.com/fcambus/spleen, 2.2.0 | BSD-2-Clause (`fonts/spleen-LICENSE`) | yes, with the licence text in the README | English half-width letters, two per 16x15 BIOS-font cell (`tools/font.py`, `tools/asm/hook.asm`) | top row dropped (16 → 15 rows; no glyph uses it), 0x7F = blank pad |
