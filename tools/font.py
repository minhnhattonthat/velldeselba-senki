"""font.py: the 8x15 half-width font for English (docs/fonts.md), from fonts/spleen-8x16.bdf.

glyphs() -> {char: 15 row bytes, MSB = leftmost pixel}, for ASCII 0x20-0x7F (0x7F = a blank pad glyph).
blob() -> 96 * 15 bytes in code order, the table the hook (tools/asm/hook.asm) indexes.
"""
from pathlib import Path

BDF = Path(__file__).resolve().parents[1] / "fonts/spleen-8x16.bdf"
ROWS = 15
SKIP_TOP = 1  # BIOS cells are 16x15; Spleen rows 1-15 keep the whole cap height and descenders


def _bdf(path=BDF):
    out, cur, bits = {}, None, None
    for line in path.read_text(encoding="ascii").splitlines():
        if line.startswith("ENCODING "):
            cur = int(line.split()[1])
        elif line == "BITMAP":
            bits = []
        elif line == "ENDCHAR":
            if cur is not None and bits is not None:
                out[cur] = bytes(int(b, 16) for b in bits)
            cur, bits = None, None
        elif bits is not None:
            bits.append(line)
    return out


def glyphs():
    src = _bdf()
    g = {}
    for code in range(0x20, 0x7F):
        rows = src[code]
        assert len(rows) == 16, (chr(code), len(rows))
        g[chr(code)] = rows[SKIP_TOP:SKIP_TOP + ROWS]
    g["\x7f"] = bytes(ROWS)
    return g


def blob():
    g = glyphs()
    return b"".join(g[chr(c)] for c in range(0x20, 0x80))


if __name__ == "__main__":
    g = glyphs()
    lost = [c for c in g if c != "\x7f" and _bdf()[ord(c)][0]]
    print(f"{len(blob())} bytes; glyphs losing a pixel in the dropped top row: {lost!r}")
