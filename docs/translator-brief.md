# Translator brief - Velldeselba Senki: Tsubasa no Kunshou (PS1, 1997)

You translate part of the Japanese script of Velldeselba Senki into English for a fan patch. It is an airship-combat
RPG: the player (default name Misaki, shown as `<F62>`) fell from space onto the planet Velldeselba, was taken in by
the Noipask army, and fights in a war between Noipask, the kingdom of Gidan and the Munogi Federation.
Work only on the batch named in your dispatch. Do all translation yourself; do not dispatch subagents.

## Read first
1. `docs/style-reference.md` - character voices and approved example pairs. Match this voice.
2. `work/tl/<batch>.terms.txt` - binding glossary rows for this batch (full table and style rules in `glossary.md`:
   read its "Rulings" and "Style rules" sections too).
3. `docs/synopsis.md` - plot, who is who and the late reveals. Don't give a reveal away early.

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`. Lines are in file order: use neighbours for context. Each line is a
whole string the game shows; it may hold several boxes. Codes in angle brackets:
- `<R>` line break, `<W>` wait for a button, `<H>` new box (page), `<E>` end. `<F62>` player name, `<F63>` the
  player's ship name. `<P13>`, `<P07>`, `<P15>` colour on/off. `<G..>`, `<V..>` icons. Anything else: copy it.
- 3D missions (ids `3D/...`): `<%S>` player name, `<_00>` and similar = portrait, `<@hh>` = timed wait that ends a
  message, `<R>` line break.

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (never a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII: straight quotes, `...`, `--`; no tabs inside
the English, no Japanese or full-width characters, no `\uXXXX`.

How to lay out each form (the check tool wraps rows for you):
- **dlg**: keep the speaker label and its `<R>` (`Noipask Soldier:<R>`, player `<F62>:<R>`), keep every `<W>`,
  `<H>` and `<E>` where the Japanese has them (one English page per Japanese page). Write each page as running
  text with no other `<R>`; the tool wraps at 34 letters. Aim for at most 3 rows per page including the speaker row
  (about 90 letters after a speaker label, 100 on later pages); a page may run longer when the meaning needs it.
- **msg3d**: same idea per message: each run of text between `<@hh>` codes is one message of at most 3 rows of 30
  letters (about 85 letters). Keep a `<R>` right before each `<@hh>` where the Japanese has one, and a `<R>` after a
  label like `Accelerate:`. Keep every `<@hh>` in order.
- **box** (profiles, item descriptions; no `<W>`): no more rows (`<R>`) than the Japanese, at most 34 letters per row,
  write `<R>` yourself. Copy the codes in the same order; skip the Japanese padding spaces (the tool re-pads).
Every non-layout code (`<F62>`, `<P13>`, `<G88>`, `<@28>`...) must appear in the same order as in the Japanese.

## Validate
Run `python -X utf8 tools/batches.py check <batch>` from the repo root and fix every reported id until it prints OK.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese doesn't
  state; don't summarise or skip. Adapt wordplay so the joke still lands (no translator notes).
- Names and terms exactly as in the glossary. Never abbreviate (no "Lt.", "Col.", "HQ", "Fed."). If a line can't fit
  without losing meaning, keep the meaning and report `LONG: id`.
- Honorifics kept, hyphenated (-san, -sama, -dono); military ranks are translated (少尉 -> Lieutenant in address).
  Western name order. Register is per character (style reference); sound effects become English onomatopoeia.
- Punctuation: 「」 -> "...", 『』 -> '...', …… -> `...`, ！？ -> `!?`. Buttons: □ Square, ○ Circle, × Cross,
  △ Triangle, Ｌ１ L1, ＳＥＬＥＣＴ SELECT.
- No "a/an" right before `<F62>`; no suffix glued to a code ("<F62>'s" is fine).
- Copy the speaker from the Japanese label; never infer it from who is addressed (a pilot line was mislabelled).
- Dead or test strings (ダミー, 体験版 notes) are still translated plainly.

## Consistency
Never edit `glossary.md` or any file other than your output. For a recurring name or term not in the glossary, pick a
form, use it consistently, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
