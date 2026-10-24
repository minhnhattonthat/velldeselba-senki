# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6 (translation) in progress. Rulings D1-D9. Pilot (G10 opening) approved by the user 2026-10-23.
  Trial wave b001/b032/b046 (profiles+items, G05-G10 dialogue, 3D missions) translated, reviewed (Approved),
  merged; archived in work/tl/trial/. Remaining dialogue re-split into 46 batches (work/tl/b001-b046, 5,563
  strings). All 46 batches translated, reviewed, Important fixes applied, merged (maps + missions done). Minors
  for the polish pass: work/tl/trial/*.review.md. 3D tracks G06/G09/G17/G25/G30/K15/K16/K19 shortened to fit
  (trims synced back into the out.tsv files). Build, check (241 tests, 0 lint) and boot smoke pass.
- **Done:**
  - Step 0, disc rebuild identical (`docs/re/disc.md`), BPE codec, digraph English font hook in all EXEs.
  - Script extracted and roundtrip-tested (`script/`: maps, exe, missions, dat). Width gate (`tools/lint.py`).
  - 2D map text sections grow by whole sectors when English is longer (`maptext._grow`; header u16 sector counts
    at 0x24/0x26/0x28/0x30, verified in-game on G10).
  - Translation pipeline: `tools/batches.py split|check|merge` (global dedup, per-batch terms, dialogue/3D wrap,
    profile icon padding); `docs/translator-brief.md`, `docs/reviewer-brief.md`, `docs/synopsis.md`,
    `docs/style-reference.md`, glossary seeded from five reader passes + trial wave.
  - English player-name entry: Latin grid in all 62 EXEs (`tools/namegrid.py`), TITLE copy loop calls
    `name_pack` (hook.asm 0x8001F100) to store letter pairs; default name Misaki. Verified: typed "A" stored as
    `cd69 f361 eb69 c17f`, dialogue shows "Misaki".
  - Graphics survey (`docs/re/graphics.md`): only the title logo is Japanese art.
  - 2026-10-24 (user report): dialogue wrap now balanced (`batches.wrap`; `boxes` ends a page a row early so no
    box holds a lone row); existing script rewrapped. Name-entry blank slots showed "Su": the pad string `　〆`
    had been translated via the TM; kept Japanese in all 62 EXEs. FMV subtitles: STR1/2/4/5 (`tools/fmv.py`,
    `script/fmv/`, `docs/re/fmv.md`), seen in-game on STR1.
  - 2026-10-24 later: 3D results/ammo messages in English (`patch_exe.results3d`, not seen in-game: no battle
    warp); polish pass p001 (78 minors) merged; `<F63>` ship name counted as 8 cells; `tools/release.py`
    (test package v0.9-test built and re-applied OK, patch 45 MB, mostly FMV frames); `texttour.py` dialogue tour.
    No unextracted Japanese left in built EXEs (only grid/kana tables and code bytes).
  - 2026-10-24 visual QA round 1 (30 sheets, 4 reviewers): fixes for English-only box breaks mid-sentence.
    `batches.page` picks the fewest boxes, then sentence/clause breaks (429 lines refitted), 137 lines tightened
    (p002a/b). Ship-interior banner "Airship Sky" (original shows the debug name + 上空 too). Non-bugs checked on
    the JP disc are listed in `docs/visual-qa-brief.md`.
  - Visual QA rounds 2-9: fragment boxes tightened (p003, p004: 89 lines), wrap keeps titles with names
    ("Captain <F62>", "His Majesty"), pulls a word down to a lone last word, prefers rows ending a sentence.
    **Gate passes** (`qa_gate.py check work/qa/manifest.tsv work/qa/verdicts`: 27/27 ok, texttour 100 lines +
    60-map banner tour). Re-run both tours and `init` after any script change (texttour's picks shift with it).
- **Next:**
  1. Visual QA covers 2D dialogue samples and banners only; see item 2 for what is still unseen.
  2. Not yet seen in-game: shops, ship parts, options, save screens, DEMO.EXE, HT.EXE 3D menus, 3D trims and
     results (no warp to battle missions; 3D warp unsolved, docs/re/debug.md).
  3. EXE/DAT batches never got a second review (the review agent's report was lost in a context reset).
  4. Staff roll guesses: 吉川剛史, 見城加奈子, 手島大 (given name), 新島平佐. Title logo stays original art (D5 scope).
  5. Ship name stays full-width (one letter per cell); a name_pack-style converter would halve its width.
  6. Release v1.0 when the user asks (`tools/release.py 1.0`); publishing is the user's call.
  - Staff roll engine notes: STAFF.EXE sends codes > 0x989E to its own kanji table (patched to 0xFFFF,
    patch_exe.STAFF_SPLIT); roles are right-aligned by x in a 16-byte entry table (tools/staffroll.py); English
    only fits when packed (exetext repack mode).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
- **States:** `work/states/en_intro_fmv.sstate` (built disc incl. name entry, f30000 of New Game; regenerate after
  builds that change resident code/data, `docs/re/debug.md`), `intro_fmv.sstate` (original), `tutorial.sstate`.
