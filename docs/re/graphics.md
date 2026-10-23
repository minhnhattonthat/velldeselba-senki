# Text drawn as graphics

Survey state (2026-10-23). Tools: `tools/tims.py list|render <dir>` (standard TIMs anywhere on the disc),
`tools/debug/tour2d.py` (warp + shots of every 2D map on the marker build).

| Where | What | Japanese? | Plan |
|---|---|---|---|
| `BEL256T.TIM` (8bpp 256x112) | title logo ベルデセルバ戦記 + (c) line | yes, logo | redraw in English (D6) |
| `OPEN.MPS` +0x65EA0 (8bpp 320x240) | title screen: same logo on blueprint background | yes, logo | redraw, same art as BEL256T |
| `OPEN.MPS` +0x5DC80 (4bpp 256x256) | title background piece | no | - |
| `ROLL.ZAQ` x7 (4bpp 512x185) | staff-roll concept sketches, tiny handwritten notes | notes only, illegible at size | leave (art) |
| `SCE_LOGO.TIM` | Sony logo | no | - |
| 2D maps 0-59 (tour2d, marker build) | place banners, talk boxes | none: all banner and box text is marker text, so it comes from `script/` | - |
| UI sheet (window frames, cursors) | | already English/symbols | - |

**verified:** 2D tour, 60/60 maps (m59 I1200 failed once in the batch run, ok on retry: flaky, not a map bug).
**open:** 3D HUD (only seen in the G44 tutorial: no Japanese), name-entry screen arrows/labels, non-TIM image
formats inside BPE streams (`work/jp_sweep.txt` hits there looked like graphic noise, not checked visually).
