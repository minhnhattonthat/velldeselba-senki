# FMVs

- `STR/STR1-5.STR` (played by `STR/MV.EXE`) and `TENKY_A.STR` (Tenky logo, no speech). MDEC v2 video + interleaved
  XA stereo 37.8 kHz, 2x speed, 10.01 sectors/frame = 14.985 fps. STR1 288x192, others 272x176. No Japanese text
  drawn in the video (contact sheets: `work/fmv/thumbs`); only speech needs subtitles.
- Speech: STR1 intro (ship computer + hero, crash landing), STR2 Kafi's history of the Pask, STR3 none (music),
  STR4/STR5 the two endings (same three hero lines at ~108-119 s).
- jPSXdec v2.0 (`tools/jpsxdec`, github.com/m35/jpsxdec) reads the 2336-byte-sector files dumpsxiso extracts.
  `-replaceframes` XML: root `<str-replace version="0.3">`, `<replace frame="N">file.png</replace>` with N the
  0-based frame index; `format=` only takes bs/mdec (PNG is the default, don't pass it).
- Use full `replace`, not `partial-replace`: v2 frames have one quantization scale per frame, so partial replace
  encodes the text at the original (often coarse) scale and it washed out on dark, static frames.
- `tools/fmv.py`: subtitles from `script/fmv/STRn.tsv` (start, end, jp, en; seconds), white DejaVu Sans Bold with a
  black outline straight on the video (no background box, D10), re-encoded into `work/fmv/out/STR/STRn.STR` (cached);
  build.py copies them into the disc. File sizes and sectors stay the same. Verified in-game on STR1 (work/qa/fmv2).
- Transcripts: faster-whisper large-v3 on CPU (cublas missing), Japanese, VAD off, word timestamps
  (`work/fmv/STRn.ja2.tsv`), then checked clip by clip: Whisper invents lines over music ("ご視聴ありがとう
  ございました", "エジェクト" echoed from the prompt) and mishears terms (推力 -> 水力, 引力圏 -> 援軍).
  Unsure readings: STR1 152 s 乗員は強制排出 (heard as 石の木と木は), 162 s セーフティングタイム, 54 s
  うるせえ line timing.
