"""namegrid.py: the name-entry grid in English (docs/re/text.md, Name entry).

TITLE.EXE (player name) and every map EXE (ship name) hold the same 30 grid rows, 0x20 apart: 5 pages x 6 rows,
each row 30 bytes = 4-byte edge, 5 keys, a full-width gap, 5 keys, 4-byte edge; a page's bottom row has 2 keys
(the dakuten keys) before its arrow/OK codes. Keys are full-width Shift-JIS; only the key characters change, so
the layout and the cursor code stay as they are. TITLE's name_pack (tools/asm/hook.asm) turns the typed name into
English letter pairs; ship names stay full-width (one letter per cell).
"""
LETTERS = ["ABCDEFGHIJ", "KLMNOPQRST", "UVWXYZ.-'!", "abcdefghij", "klmnopqrst", "uvwxyz "]
SYMBOLS = ["1234567890", "!?.,'-&+=/", ":         ", "          ", "          ", "       "]
PAGES = [LETTERS, LETTERS, SYMBOLS, LETTERS, SYMBOLS]  # hiragana, katakana, alnum, kanji, kanji pages

FULL = {" ": "　", ".": "．", "-": "－", "'": "’", "!": "！", "?": "？", ",": "，", "&": "＆", "+": "＋",
        "=": "＝", "/": "／", ":": "："}


def full(c):
    if c.isalnum():
        return chr(ord(c) + 0xFEE0).encode("cp932")
    return FULL[c].encode("cp932")


def first_row(exe):
    """File offset of the hiragana page's top row (あいうえお), or -1."""
    i = exe.find("あいうえお".encode("cp932"))
    return i - 4 if i >= 4 else -1


def apply(exe):
    """EXE bytes with every grid page in Latin letters (unchanged when the EXE has no grid)."""
    top = first_row(exe)
    if top < 0:
        return exe
    out = bytearray(exe)
    for p, page in enumerate(PAGES):
        for r, keys in enumerate(page):
            row = top - p * 0xC0 - r * 0x20
            out[row + 4:row + 14] = b"".join(full(c) for c in keys[:5])
            out[row + 16:row + 16 + 2 * len(keys[5:])] = b"".join(full(c) for c in keys[5:])
    return bytes(out)
