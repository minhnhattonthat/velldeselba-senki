Velldeselba Senki: Tsubasa no Kunshou - English translation v{VERSION}
=======================================================================

Unofficial English fan translation of Velldeselba Senki: Tsubasa no Kunshou (PlayStation, Japan, 1997).
This package holds a patch only. You need your own dump of the Japanese disc; no game data is included, and
pre-patched images are not provided.

What is translated
------------------
All dialogue (2D maps and 3D missions), menus, shops, item, ship-part and place names, profiles, the name entry
grid (English letters), the staff roll, and the 3D battle results. The FMVs have English subtitles burned in.
The title logo is the original artwork.

Base disc (must match)
----------------------
{HASHES}

Patching
--------
1. Use xdelta3 (command line) or Delta Patcher (GUI).
   xdelta3 -d -s "Velldeselba Senki - Tsubasa no Kunshou (Japan).bin" {PATCH} "Velldeselba Senki (English).bin"
2. Copy your original .cue next to the patched .bin and change the file name inside it to the new .bin name.
   The patched image keeps the original single-track layout.
3. Start a new game (cold boot). Japanese saves load, but names already stored in them stay Japanese.

Tested on PCSX-Redux. Report problems (untranslated text, overflow, crashes) on the project's GitHub issues page,
with a memory card file if you can.

Notes
-----
- Honorifics are kept (-sama, -dono); names are in Western order.
- Translation and tooling were produced with AI assistance (Claude) and reviewed in-game.
- English letters: Spleen font (BSD-2-Clause). FMV subtitles: DejaVu Sans Bold (Bitstream Vera licence).
- Original game (c) its respective owners. This is a non-commercial fan work.
