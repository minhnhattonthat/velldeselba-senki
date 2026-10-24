# Text drawn as graphics

Survey state (2026-10-23). Tools: `tools/tims.py list|render <dir>` (standard TIMs anywhere on the disc),
`tools/debug/tour2d.py` (warp + shots of every 2D map on the marker build).

| Where | What | Japanese? | Plan |
|---|---|---|---|
| `BEL256T.TIM` (8bpp 256x112) | title logo ベルデセルバ戦記 + (c) line, 3D title screen (fades in) | yes, logo | done: `tools/logo.py`, seen in-game |
| `OPEN.MPS` +0x65EA0 (8bpp 320x240) | title menu after Push Start: larger logo with drop shadow on the blueprint | yes, logo | done: `logo.py` (old letters inpainted), seen in-game |
| `BERU_FL2.DAT` +0x7C (4bpp 136x48, CLUT +0xD3C) | loading screen: small logo (x 0-110) + two plane frames (x 112-134) that fly across it | yes, logo | done: `logo.py`, seen in-game; found by VRAM dump (texture at VRAM 0,256) |
| `OPEN.MPS` +0x5DC80 (4bpp 256x256) | title background piece | no | - |
| `ROLL.ZAQ` x7 (4bpp 512x185) | staff-roll concept sketches, tiny handwritten notes | notes only, illegible at size | leave (art) |
| `SCE_LOGO.TIM` | Sony logo | no | - |
| 2D maps 0-59 (tour2d, marker build) | place banners, talk boxes | none: all banner and box text is marker text, so it comes from `script/` | - |
| UI sheet (window frames, cursors) | | already English/symbols | - |
| `2D/OTHER/WORLD.MPS` (6 BPE streams, 4bpp 224x149, CLUTs in the 0x800 header at 0x18 + 32k; VRAM 896,0) | Old Sage's maps: Nades (k0), factions (k3), two route maps (k4, k5); k1/k2 no text | yes, place names | done: `tools/worldmap.py` erases and redraws in Spleen 5x8 / 6x12 bold; k0/k3 seen in-game (Geography, Balance of Power). k4/k5 screen not seen yet |
| `2D/OTHER/MAP.MPS` (32 streams, 4bpp 160x160) | terrain pieces | no | - |
| `2D/OTHER/SHIP_PIC.MPS` (24 streams, same format as WORLD; CLUTs at 0x60 + 32k) | shipyard pictures, 6 models x 4 colours, name in a title bar | yes | done: `worldmap.py` refills the bar and writes the model name; not seen in-game (no ship yet) |
| `2D/OTHER/SHIP_SET.MPS` stream 7 (4bpp 256x152) | airship route map + its town-name sprites | yes | done: `tools/routemap.py` repacks English names into the sheet; table of 23 x 16-byte entries (u16 u, v, w, h, screen x, y, node x, y) in I0100..I0700.EXE, found by searching the label rects. Cockpit "Take off" needs story flags: not seen in-game |

**verified:** 2D tour, 60/60 maps (m59 I1200 failed once in the batch run, ok on retry: flaky, not a map bug).
How WORLD.MPS was found (2026-10-24): VRAM dump on the map screen (emu.py `L.dump_ppu`), the picture rows
searched in every decompressed stream. The marker-build tour missed it: it is only loaded by a Sage topic.
Checked, no text: `SHIP_SET.MPS` streams 0-5 (ship top views with turret slots), `SHIPnn_m.MPS` (0x40-byte CLUT +
256-wide 4bpp airship interior tiles).
**open:** 3D HUD (only seen in the G44 tutorial: no Japanese), name-entry screen arrows/labels, non-TIM image
formats inside BPE streams (`work/jp_sweep.txt` hits there looked like graphic noise, not checked visually).
