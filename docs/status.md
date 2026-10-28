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
  - 2026-10-24 (user request): title logo English "VELLDESELBA / SENKI" (`tools/logo.py`, Anton OFL) on all three
    copies: BEL256T.TIM (3D title), OPEN.MPS (title menu), BERU_FL2.DAT (loading screen, new find). Plane, TM,
    (c) kept; size/place/palette unchanged, so the title fade and the loading-screen plane fly-over run as before.
    Verified cold boot work/qa/logo.
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
  - Playtest 1 (story from Nades): two wording fixes (Kafi's "the Commander and Colonel Zexel", Quartermaster's
    ammo line); got lost before the Old Sage. Profiles: the profile box wraps at 17 cells and ignores `<R>`
    mid-row, so `pad_box` pads rows to the JP width (79 lines; seen in-game). I03's 64 KB table overflowed from the
    padding: `maptext.build` now stores identical strings once when a table overflows (I03 only; map loads).
    Field menu (triangle) seen in English; Ship/Equip/Cargo need a ship. Savestates from older builds keep the old
    map text in RAM: warp to reload before judging map text.
  - Playtests 2-3: route to the Old Sage found (brief). His Geography/Balance of Power "freeze" was a stale
    savestate; fine on a fresh one. Their map pictures (`2D/OTHER/WORLD.MPS`) had Japanese place names: redrawn in
    English (`tools/worldmap.py`), seen in-game. EXE/DAT strings reviewed (749; fixes in 26bbaf5). FMV subtitles
    without background box (D10), balanced lines.
  - Ship pictures (SHIP_PIC.MPS, 24) and the airship route map's town names (SHIP_SET.MPS sheet + rect table in
    I0100..I0700.EXE) in English; both need a ship / take-off flags to see in-game (airship cockpit "Take off"
    says "not ready to set sail" at game-start flags; state `work/states/en_i01.sstate`).
- **Next:**
  1. Visual QA covers 2D dialogue samples and banners only; see item 2 for what is still unseen. Take-off gate
     found (2026-10-24, docs/re/debug.md): flags 9999+1169 send the ship into the first 3D sortie
     (`work/states/en_sortie1.sstate`, after the intro; pause > RESTART replays it). Playtest 4 (sortie): intro
     messages OK; 3D option menus (DEMO.EXE/HT.EXE) left old text behind and highlights missed the options: rows
     padded to the JP width, options moved under the game's fixed highlight cells (1 JP cell = 2 letters; View
     Y/Throttle now "Invert ...: Off On"), verified work/qa/opt. Open: the ship never moved in 2000 frames of
     throttle (flag-skip state? check on a sortie reached by play); combat/results text still unseen.
  2. Not yet seen in-game: shops, ship parts, options, save screens, DEMO.EXE, HT.EXE 3D menus, 3D trims and
     results, route map (neither take-off branch shows it; it must come with later destination choices).
  3. EXE/DAT batches never got a second review (the review agent's report was lost in a context reset).
  4. Staff roll readings checked against MobyGames' credits (mobygames.com/game/59766, credits/playstation):
     Takafumi Yoshikawa, Kanako Mishiro, Hiroshi Teshima, Heiza Niishima, Takafumi Fujisawa. Kept ours where
     Moby looks wrong (一色緑 Isshiki, 木崎文智 Fumitomo, 鉄羅紀明 Noriaki).  5. Ship name stays full-width (one letter per cell); a name_pack-style converter would halve its width.
  6. v1.0 released 2026-10-24 on GitHub (minhnhattonthat/velldeselba-senki, user request); patch SHA-1
     700bf52ca1f31973b100e23c19ce3944521fc998. Next version: `tools/release.py 1.1`.
  - Staff roll engine notes: STAFF.EXE sends codes > 0x989E to its own kanji table (patched to 0xFFFF,
    patch_exe.STAFF_SPLIT); roles are right-aligned by x in a 16-byte entry table (tools/staffroll.py); English
    only fits when packed (exetext repack mode).
- **Issue #1 (font hard to read), fixed 2026-10-29:** the game's glyph converter ORs each pixel one to the right,
  so Spleen's 2 px stems drew 3 px and letters touched. `font.thin` drops the last pixel of each run; drawn
  text is now Spleen's own shape (seen in dialogue, work/qa/font1). Not yet re-seen: field/3D menus, name entry,
  staff roll (if any renderer doesn't bold, its text is 1 px thin there). Re-run texttour + banner tour and
  `qa_gate.py init` before release 1.1 (sheets changed).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
- **States:** `work/states/en_intro_fmv.sstate` (built disc incl. name entry, f30000 of New Game; regenerate after
  builds that change resident code/data, `docs/re/debug.md`), `intro_fmv.sstate` (original), `tutorial.sstate`.
