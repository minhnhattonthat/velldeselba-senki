# Translation reviewer brief - Velldeselba Senki: Tsubasa no Kunshou

You review one batch of the JP->English fan translation. Read-only: no edits, no git, no subagents. Mechanical
validity (ids, control codes, ASCII, row widths) is already enforced by `tools/batches.py check` - judge translation
quality. Return the report as your final message.

## Inputs (paths in your dispatch)
- `work/tl/<batch>.tsv` (id, speaker, form, limit, Japanese) and `work/tl/<batch>.out.tsv` (id, English). Read ALL of
  both; pair them by id. Neighbouring lines are context.
- `glossary.md` (rulings and style rules at the top), `docs/style-reference.md`, `docs/synopsis.md`, and the
  translator's report (unverified claims).

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say
  what it means.
- Consistency: glossary names/terms exactly (one-letter slips are what players notice); speaker labels exactly as
  the glossary forms; ranks as the JP uses them (少尉 Lieutenant, 大尉 Captain); honorifics kept (-san, -sama);
  no abbreviations ("Lt.", "Col.", "HQ").
- Voice per character (style reference + synopsis voices): the player rough and casual, Kafi warm-firm, the King
  archaic and jolly, Sidel slow and "..."-led, Fragnum refined, Ba Magg over-formal, the twins splitting sentences.
- Spoilers: a line must not reveal more than the Japanese does at that point.
- Things players catch that reviewers miss: jokes losing their punch; "1th"-style suffixes after a code; stock
  phrases that read awkwardly ("... GET!"); "a <F62>".
- Naturalness: would a fan-translation reader stumble?

## Report
### Issues
#### Critical (meaning reversed, broken code grammar, wrong speaker)
#### Important (clear mistranslation, glossary inconsistency, abbreviation)
#### Minor (style - deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
Approved | Needs fixes - one sentence why.
