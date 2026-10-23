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
- No "a/an" right before `<F62>`; no ordinal glued to a number code ("1th"). "<F62>'s" and honorifics
  ("<F62>-san", "<F62>-sama") are fine: keep them where the JP has them.
- Copy the speaker from the Japanese label; never infer it from who is addressed (a pilot line was mislabelled).
- Dead or test strings (ダミー, 体験版 notes) are still translated plainly.

## Notes from earlier batches
- A label without a rank (plain カフィ) stays without one ("Kafi:"); ranks change by chapter: copy the JP's.
- Item and ammo names are proper names from the glossary (b001); in running dialogue they may be lowercase
  ("burst shells"), never another word ("incendiary rounds" was wrong).
- Avoid double negatives with "doubt" ("I doubt X has nothing to do with it"): say it plainly.
- Keep formal speakers formal in short lines too (Hauezna "It's hopeless, sir." not "No good.").
- Don't add a gender the JP doesn't give ("Bring the envoy here", not "him").
- Japanese-isms to avoid: "Thank you for your hard work" -> "Good work out there".
- A number code `<Vnn,...>` can be 1: no plural noun after it ("that's <V12,0,4> over the limit", not "<V12,0,4> items").
- Ellipses: …… is "...", anything longer is "......" (6 dots); never 9.
- Fixed speaker forms (wave 1): ギダン技術将校 Gidan Engineer Officer; 全員 Everyone; 修理係 Repair Tech; ム連士官
  Federation Officer; 宿屋のおかみ Innkeeper; カ・ジャルコの父 Ka Jarko's Father; 市民 Citizen; 医者 Doctor;
  発明家 Inventor. 空賊さん as address -> "sky pirate" (no -san on common nouns).
- Wave 2 forms: ギダン司令官 Gidan Commander; おやじ (shop label) Shopkeeper; 覆面男 Masked Man; 金 meaning money is
  "money" or the bare Z amount (Gold is the cargo item). The glossary table has the rest.
- Wave 3 forms: ダ・クダのだんな Boss Da Kuda; other Xのだんな Mister X; 親分 Boss / "the boss"; 一同 Everyone;
  ノイパスク士官 Noipask Officer; ノイパスク兵(士)たち Noipask Soldiers; 国王の付き人 King's Attendant; 子供 Child;
  ム連邦民間人 Federation Civilian; 酒場のマスター Bartender. US spelling (rumors, mechanized, armor).
- Wave 4 forms: コステリフ・タカテリフ長官 Commanders Kosterif and Takaterif; ム連邦大統領 Federation President;
  管制塔員 Tower Controller; ギダン軍特使 Gidan Envoy; ギダン衛生兵 Gidan Medic; -kun kept like -san.
  仲間になりました -> "X has joined the crew." A label 中佐 is "Lieutenant Colonel"; only direct address shortens
  it to "Colonel".

## Consistency
Never edit `glossary.md` or any file other than your output. For a recurring name or term not in the glossary, pick a
form, use it consistently, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
