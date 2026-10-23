# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1 (recon), with phase 3 identity rebuild already verified by hand. No build script yet.
- **Done:** Step 0 (tools, guard, pre-commit, smoke on original). Rulings D1-D6. Disc dump/rebuild identical.
  BPE codec found + tested. 2D map text container decoded. Font = BIOS kanji ROM via Krom2RawAdd (no half-width).
  Routes: `tools/routes/boot.txt`, `tools/routes/newgame.txt` (→ flight tutorial). State: `work/states/tutorial.sstate`.
- **Next:** decode MPS header (stream offsets), 2nd text stream per map, 3D mission text offsets, EXE string refs;
  confirm control codes; find the glyph-draw routine (plan: hook Krom2RawAdd for a custom half-width/VWF range);
  graphics-text survey; phase 2 debug tool (find map id / story flags in RAM).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
