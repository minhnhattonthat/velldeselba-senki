# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-10-23 | Honorifics and name order | drop + Western; keep + Western; keep + JP order | Keep honorifics (hyphenated, e.g. Name-sama), Western name order |
| D2 | 2026-10-23 | Romanization source for names | official art + Hepburn fallback; strict Hepburn; earlier patch | Official romaji (disc, manual, box, in-game logos) first, Hepburn/natural spelling otherwise |
| D3 | 2026-10-23 | Credits | stay Japanese, translate | Translate the staff roll |
| D4 | 2026-10-23 | Abbreviations | engine work first (default), abbreviate | Full names and terms; VWF/wider box/relocation before any abbreviation, which is a flagged last resort |
| D5 | 2026-10-23 | Graphics text left in Japanese | none (default), list | None: title logo, menus, banners all go English |
| D6 | 2026-10-23 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through checkpoints, report at the end |
| D7 | 2026-10-23 | English font engine (made under D6) | full-width ASCII; digraph cells from an 8 px font; true VWF | Digraph cells: a hook on the BIOS-font call builds each 16x15 cell from two 8 px Spleen letters. 34 chars/line vs 17 full-width, no layout code changed. VWF stays an upgrade if lines prove too short |
| D8 | 2026-10-23 | Register / tone | formal military; casual; mixed by character | Mixed by character: each speaker keeps their own voice (officers clipped and formal, crew and civilians casual); voice notes per character in `docs/style-reference.md` |
| D9 | 2026-10-23 | Sound effects in text | translate; romaji; drop | Translate to English onomatopoeia (e.g. ドーン -> "Boom!") |
| D10 | 2026-10-24 | FMV subtitle background (user request) | black box behind the text; none | No background fill: outlined white text straight on the video |
