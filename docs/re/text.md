# Text

## Encoding (verified: decoded script reads as Japanese, matches screen)
Shift-JIS (cp932) full-width characters; control codes are **ASCII letters/digits** mixed in. Consequence: English
cannot be plain ASCII without renderer work (`R`, `E`, `W`... are codes). Options for phase 5: full-width ASCII
(wide, wasteful), or a renderer hook giving half-width/VWF glyphs a separate byte range.

## Control codes (guess from context, confirm in the marker build)
| Code | Seen | Meaning (guess) |
|---|---|---|
| `R` | between lines | line break |
| `W` | before `E` | wait for button |
| `E` | end of every string | end of string |
| `F61`, `F62`... | string start | face/portrait or speaker style, 2 digits |
| `P13` ... `P15` | around words | colour on / colour off (P + 2 digits) |
| `G88`, `G90`... | profiles | icon/graphic, 2 digits |
| `V0,0,3` | profiles | value/gauge, 3 comma-separated digits |
| `：` (full-width colon) after a name | speaker line | plain text, not a code |
| 3D missions: `\r\n` line breaks, `@` + 1 byte between messages | G00.MPS tutorial | separate format, not decoded |

## Script containers
- **2D maps** (`2D/*MPS/*.MPS`): one BPE stream holds a text region of exactly 0x11000 bytes: 0x1000 bytes of u16
  LE offsets (up to 2048 entries, relative to 0x1000), then strings (each ends in `E`), zero-padded; map data follows
  from 0x11000. Budget per map: 64 KiB of text. Example A01_00.MPS @0x56000: 315 entries, text ends 0x6CC3.
  A second, smaller text stream exists in some maps (A01_00 @0x5F800, ~600 chars): not decoded yet.
- **3D missions** (`3D/*/G*.MPS`, `K*.MPS`; `tools/missiontext.py`): stream 1 starts with a 0x3800-byte script
  area (RAM 0x801A8400 in the tutorial). u16 at +4 = lo: the message track starts at lo+4; u16 at +6 = hi: a second
  script section at hi when non-zero (G06 G09 G17 G24 G25 G30 K15 K16 K19: the track must fit before it, i.e. in
  the JP byte length; move it only after an in-game test). HT.EXE's interpreter (0x8004011C, pc at 0x80079EE0)
  reads 2-byte tokens: SJIS, CRLF, `@`+param (ends a message, timed), `*`+face, `%S` `_`+byte (player name), `//`
  (ends a block; blocks run in order, one per mission trigger), 0x1A = end. A blank line = next page. After the
  last real `//` some missions hold dead compiler source (`@set_model0`...) up to the 0x1A; the build drops it.
  The tutorial is G44. 166 blocks in 86 missions; 3D box: 3 rows x 30 letters (measured in the tutorial).
- **EXEs**: raw SJIS at the file start (map EXE 0x800 = RAM 0x80020000), referenced by `lui/addiu` pairs.
  Same menu strings repeat in every map EXE (~870 chars each).

## Box widths (width gate, measured 2026-10-23 with tools/debug/textview.py; enforced by tools/lint.py)
- Dialogue box (strings with `<W>`): 3 rows per box, 17 cells = **34 letters** per row. The wait cursor takes the
  17th cell of a row ending at `<W>`, and of a box's 3rd row when more rows follow (that 17th cell wraps into a
  new box after a wait): **32 letters** there. A page (`<H>`) longer than 3 rows just continues in a new box
  (JP does this 4.5k times: speaker row + 3 rows). The JP data obeys this except 6 original overflows.
- Item descriptions / profiles (no `<W>`): 4 rows x 17 cells, no wait cursor.
- EXE menus and labels: footprint of the JP row (lint: no wider than the JP). Not measured per menu yet.
- `<F62>` = player name (default ミサキ); lint counts 4 cells.

## Not text (excluded from script/, build leaves them as is)
- Name-entry grid rows (`<$20><$20>`/`<Gnn><$20>` rows in TITLE.EXE and every map EXE, 30 per EXE) and the 6
  dakuten conversion tables after them: the English name grid is engine work (see Name entry).
- B01_10.MPS and A10_00.MPS: offset tables zeroed and no EXE loads them.
- 3D-engine printf formats in DEMO.EXE / 3D HT.EXE (`%sは、@`, `%uポイントの@`, `レベル%uになった。`, `%s、弾切れです！`):
  CRLF + `@` format, not extracted yet (exetext skips them: no SJIS lead at the start / not referenced).

## Name entry
New Game opens a kana grid (default name ミサキ). Needs an English letter grid (graphics + table).
