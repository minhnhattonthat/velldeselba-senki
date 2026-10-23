# Velldeselba Senki: Tsubasa no Kunshou (PS1) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md, `python tools/skill.py` prints it). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Build:    `python -X utf8 tools/build.py` -> build/velldeselba_en.bin/.cue (checks the dump against `rom.sha1` first; FMV subtitles via `tools/fmv.py`, cached, ~3 min when they change)
- Check:    `python -X utf8 tools/check.py`  (pytest `tests/` + lint; the pre-commit hook runs this)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/velldeselba_en.cue --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 $SKILL/scripts/emu.py <cue> --out work/qa/warp --state-in work/states/intro_fmv.sstate --script tools/debug/warp.lua --var MAP=<index> --var WARP_FRAMES=2500 --frames 3600 --sheet` (indices: `tools/debug/scenes.txt`; making the state and limits: `docs/re/debug.md`; never ask the user to play to a scene)
- Release:  `python -X utf8 tools/release.py VERSION [--no-qa]` (xdelta vs the .bin; QA gate `work/qa/manifest.tsv`; never publish without the user)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original disc: `rom/Velldeselba Senki - Tsubasa no Kunshou (Japan).bin/.cue` (gitignored; one MODE2/2352 track; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`).
- Emulator: `tools/pcsx/` (PCSX-Redux nightly 29213.20261023.13 x64, via `$SKILL/scripts/fetch_emu.py pcsx`; gitignored). BIOS: `tools/bios/scph5500.bin` (`fetch_emu.py psx-bios`). Savestates: `work/states/`.
- Disc tools: `tools/mkpsxiso/` (mkpsxiso/dumpsxiso v2.30, github.com/Lameguy64/mkpsxiso), `tools/armips/` (v0.11.0, github.com/Kingcom/armips). capstone 5 via pip.
- Text: `script/`. Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Japanese game: confirm = circle, cancel = cross (`--mash-key circle`). Close PCSX-Redux before building (stop own runs by the PID emu.py prints).

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
