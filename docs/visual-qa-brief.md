# Visual-QA reviewer brief - Velldeselba Senki: Tsubasa no Kunshou (PS1)

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- Optional: the original ROM's sheets (`work/qa/tour_jp/`, same ids) and `glossary.md`.

## How to look
- Read each sheet whole first. Where text is small, zoom into it with
  `python -X utf8 $SKILL/scripts/sheet.py SHEET.png --crop x,y,w,h --zoom 3 --out <scratch>.png` and read that.
- When something looks wrong, open the same id from `tour_jp/` (`sheet.py EN.png --compare JP.png`). If the
  original shows the same thing, it is the game's own behaviour: `ok`, with a note.

## Judge
An `issue` is any of:
- Japanese still visible;
- text overflowing a box, clipped by a frame, or running off screen;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a page ending mid-sentence, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok` (the controller adds the game's own below):
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- a map or scene still loading after a warp;
- anything identical in the original's sheet.
- English is drawn two letters per 16x15 font cell, so a few gaps are by design: a blank half cell after a run
  with an odd letter count (e.g. before a name or number), and the speaker label on its own row.
- Dialogue tour (`texttour/`): every shot is the same NPC by the G10 door; the box content is swapped in by the
  debug tool, so the NPC and the map never match the text. Shots between two lines show no box: ok. A shot whose
  box still types is ok. `index.txt` in the tour folder maps each frame to its script id.
- Map tour (`tour2d/`): the first tile per map is the place-name banner, the second the plain map after it.
  Same in the original (checked in `work/qa/tour_jp/`): m01/m02 show no banner (a close-up of the map); m24 is
  black at both shots; ship interiors (m45-m54) read "Airship Sky" (JP 自機・軍上空, the debug scene name plus
  the area suffix the game appends). Other ship banners (Ship, Milt, Gashizaki, Pirates, Chibaraga) are the debug
  scene names too (`script/exe/2D/AMPS/A0100.EXE.json`).
- Dialogue: a box may end mid-sentence when the line is longer than the box and has no sentence or clause end
  to break at; flag it only when a nearby `.`/`,` break was clearly possible.
- A row that ends with the page cursor holds 32 letters, not 34, so a 33-34 letter line ("Received the Giant Sea
  Otter Pelt.") wraps even though other 34-letter rows fit.
- The Japanese title logo is kept as original art.
- Name entry: the `〆` end mark at the right of the name field is the original's.

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
