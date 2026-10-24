# Debug tool: warps (phase 2)

## Resident game state (verified on G10 and warp tests, 2026-10-23)
- `BERU_FL1.DAT` (32 KiB) is loaded to RAM 0x80010000 and holds the persistent state: memory-card header and icon
  (0x80010000), player name SJIS at 0x80010200 (default ミサキ), **current map index u32 at 0x80010238**, a second
  map word at 0x8001023C (both must be written), entrance u32 at 0x80010234 (-1 default), story flag bitfields from
  0x80010280 (pointer at 0x8007B490 in G1000.EXE; all zero at game start).
- Map index = entry in the EXE name table at 0x8001610C (22-byte entries; `tools/debug/scenes.txt`): 0-59 are the
  2D map EXEs (A0100 ... I1200). G1000.EXE's map change (0x8002DE50, a0 = index) builds `cdrom:<name>` and LoadExecs.
- 3D missions: table entries after the 2D ones (`\3D\GMPS1\G00.MPS`...) use a different stride/trigger; MAP=70 gave
  a black screen. Not solved yet.

## Warp
1. One-time state (cold boot → New Game → name OK → tutorial → intro FMV, ~2 min):
   `emu.py rom.cue --out work/qa/regen --route tools/routes/newgame.txt --frames 30000 --mash 60 --mash-key circle --state-out work/states/intro_fmv.sstate`
2. `emu.py rom.cue --out work/qa/warp --state-in work/states/intro_fmv.sstate --script tools/debug/warp.lua --var MAP=<index> --var WARP_FRAMES=2500 --frames 3600 --sheet`
   The game's own map load after the FMV then loads MAP. Verified: 0 (A0100, ship deck), 40 (G1000, start), 59 (I1200).

## Text viewer (width checks)
`python -X utf8 tools/debug/textview.py "Name:<R>text<W><E>" --out work/qa/view --pages 2`: from
`en_intro_fmv.sstate` (built disc; regenerate with step 1 on `build/velldeselba_en.cue` after builds that move
code), walks to the G10 NPC left of the start, talks, and `textview.lua` points the box at TEXT. Box openers in
G1000.EXE: 0x8005A5CC = NPC talk (caller 0x800344B4 indexes the text table at 0x8016C900), 0x8005A190 = banners
and event boxes (place-name banner opens first on map load). PCSX-Redux crashed once (exit 3221225477) at boot
with the exec breakpoint set; a rerun was fine.

## Airship take-off gate (I0100.EXE, 2026-10-24)
Take off at the helm (0x8002C3AC; flag base pointer at 0x800856F0 = 0x80010280) tests bit 9999 (word +0x4E0 bit
15, ship ready); then bit 1169 (+0x90 b17) set with 1450 (+0xB4 b10) clear sends the ship to 0x5F (first sortie),
else 1191 (+0x94 b7) set with 1412 (+0xB0 b4) clear sends it to 0x39; otherwise "not ready to set sail yet" (#926).
First sortie: `emu.py build/velldeselba_en.cue --out work/qa/takeoff --state-in work/states/en_helm.sstate --script
tools/debug/flags.lua --var "FLAG_SET={9999,1169}" --route tools/routes/takeoff.txt --state-out
work/states/en_sortie1.sstate` (helm state from a playtester; the 3D sortie starts ~f1000). Found by a write watch on
the text box pointer 0x8008D344, then the caller's return address.

- Story flags are game-start values, so NPCs say their early lines. Still to do: flags for later chapters, a text
  viewer (force string N of the loaded map) for the tour, 3D mission warps.
