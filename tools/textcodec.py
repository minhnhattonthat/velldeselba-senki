"""textcodec.py: game text <-> editable script text (docs/re/text.md).

Script form: plain text, control codes in angle brackets: <R> line break, <W> wait, <E> end, <P13> colour,
<V0,0,3>, <F62>... (letter + digits/commas); any other byte below 0x80 as <$hh>. Japanese decodes to SJIS characters; English encodes as letter
pairs, one 16x15 cell per pair: bytes (0x80 + c1, c2) for ASCII c1, c2 in 0x20-0x7F (tools/asm/hook.asm).
A run with an odd number of letters is padded with PAD (0x7F, a blank half cell).
"""
import re

CODE_LETTERS = set("ABCDEFGHLNOPRSTUVWZ")  # the interpreter's jump table (0x80022C14 in G1000.EXE)
PAD = "\x7f"
CODE = re.compile(r"<([A-Z])([0-9,]*)>|<\$([0-9a-f]{2})>")


def decode(b, english=False):
    """Game bytes -> script text. Bytes < 0x80 are codes: a letter plus its digit/comma args. english=True reads
    leads 0xA0-0xFF as letter pairs (our build); otherwise they are SJIS (0xE0-0xEF kanji in the original)."""
    out, i = [], 0
    while i < len(b):
        c = b[i]
        if c < 0x80 and not 0x41 <= c <= 0x5A:
            out.append(f"<${c:02x}>"); i += 1  # raw byte outside a code (NUL, stray digits)
        elif c < 0x80:
            ch = chr(c)
            j = i + 1
            while j < len(b) and (0x30 <= b[j] <= 0x39 or b[j] == 0x2C):
                j += 1
            out.append(f"<{ch}{b[i + 1:j].decode('ascii')}>")
            i = j
        elif english and c >= 0xA0:
            out.append(chr(c - 0x80) + chr(b[i + 1]))
            i += 2
        else:
            out.append(b[i:i + 2].decode("cp932")); i += 2
    return "".join(out).replace(PAD, "")


def encode(s):
    """Script text (English, or Japanese full-width) -> game bytes."""
    out = bytearray()
    pos = 0
    for m in list(CODE.finditer(s)) + [None]:
        run = s[pos:m.start() if m else len(s)]
        out += _run(run)
        if m:
            letter, args, raw = m.groups()
            out += bytes([int(raw, 16)]) if raw else (letter + args).encode("ascii")
            pos = m.end()
    return bytes(out)


def _run(run):
    out = bytearray()
    ascii_buf = []

    def flush():
        if len(ascii_buf) % 2:
            ascii_buf.append(PAD)
        for a, b in zip(ascii_buf[::2], ascii_buf[1::2]):
            out.extend((0x80 + ord(a), ord(b)))
        ascii_buf.clear()

    for ch in run:
        if 0x20 <= ord(ch) <= 0x7F:
            ascii_buf.append(ch)
        else:
            flush()
            out += ch.encode("cp932")
    flush()
    return out


def cells(run):
    """Screen cells a text run takes (English: 2 letters per cell)."""
    return len(_run(run)) // 2
