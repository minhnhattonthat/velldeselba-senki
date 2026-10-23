# Compression: byte-pair encoding (verified)

Philip Gage's BPE (C/C++ Users Journal, Feb 1994), codec in `tools/bpe.py`, tests `tests/test_bpe.py`.

- **Verified:** a PCSX-Redux write watch on the tutorial text in RAM (0x801A8536) hit `sb` at PC 0x8006FC40, inside
  the decoder at 0x8006F930 (`a0` = src, `a1` = dst, returns dst end). Tables in the scratchpad: left 0x1F800000,
  right 0x1F800100, expansion stack 0x1F800200. Decoding A01_00.MPS @0x56000 gives readable script; roundtrip test passes.
- Stream: u32 LE = byte length of the blocks that follow (the 4-byte field itself not counted). Each block: pair
  table (count byte > 127 skips count-127 codes, else count+1 entries `left[,right]`, right only when left != code),
  u16 **big-endian** packed size, packed bytes. The game's loop test is loose (it checks a pre-read byte), so the
  length must be exact; `scan_bpe.py` only accepts streams whose blocks end exactly on it.
- Our compressor is Gage's algorithm (8 KiB blocks, pair threshold 3): it decodes the same but is not byte-identical
  to the original packer, so unchanged streams must be copied, not recompressed.
