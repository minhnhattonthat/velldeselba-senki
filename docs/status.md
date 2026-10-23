# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6 (translation) in progress. Rulings D1-D9. Pilot (G10 opening) approved by the user 2026-10-23.
  Trial wave b001/b032/b046 (profiles+items, G05-G10 dialogue, 3D missions) translated, reviewed (Approved),
  merged; archived in work/tl/trial/. Remaining dialogue re-split into 46 batches (work/tl/b001-b046, 5,563
  strings); wave 1 = b001-b008 dispatched.
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
- **Next:**
  1. Waves 2-6 (b009-b046), reviewers per batch (sonnet), fix Critical/Important, merge; minors to the polish
     list (work/tl/*.review.md). Glossary: merge NEW TERM reports between waves.
  2. EXE strings (605 unique: menus, shop, staff roll, TITLE) and DAT names: measure menu widths per screen first.
  3. Ship-name entry (map EXEs) stores full-width letters (one per cell): `<F63>` not counted by lint; add a
     converter like name_pack or cap the ship name length.
  4. 3D printf groups in HT.EXE/DEMO.EXE (base+offset pieces).
  5. Title logo redraw; staff roll (STAFF.EXE text is in script/exe).
  6. Polish pass (minors), whole-game sampled review, in-game QA tour, release tooling (`tools/release.py`).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
- **States:** `work/states/en_intro_fmv.sstate` (built disc incl. name entry, f30000 of New Game; regenerate after
  builds that change resident code/data, `docs/re/debug.md`), `intro_fmv.sstate` (original), `tutorial.sstate`.
