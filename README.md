# Velldeselba Senki: Tsubasa no Kunshou English translation

Unofficial English fan translation of **Velldeselba Senki: Tsubasa no Kunshou** (PlayStation, Sony Computer
Entertainment, 1997): the source text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |

## Build your own patched ROM

Needs Python 3.12+ (Pillow), mkpsxiso/dumpsxiso 2.30 and armips 0.11 in `tools/`, Java 8+ with jPSXdec 2.0 in
`tools/jpsxdec/` (FMV subtitles), and your own dump of the Japanese disc.

```sh
git clone https://github.com/minhnhattonthat/velldeselba-senki-en
cd velldeselba-senki-en
# copy your dump to: rom/Velldeselba Senki - Tsubasa no Kunshou (Japan).bin (+ .cue)
#   (520575216 bytes, SHA-1 24456c8d773ea331da085beb4d3f78b198c3a23d; the build refuses any other dump, see rom.sha1)
python -X utf8 tools/build.py                          # -> build/velldeselba_en.bin/.cue
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Sony Computer Entertainment's and is included
only so the translation can be checked against it. Velldeselba Senki is (c) Sony Computer Entertainment; this project
is not affiliated with them.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
