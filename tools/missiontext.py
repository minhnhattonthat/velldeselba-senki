"""missiontext.py: message track of 3D mission scripts (3D/*/G*.MPS, K*.MPS; docs/re/text.md).

Stream 1 of a mission MPS starts with a 0x3800-byte script area. Header u16 at +4 = lo: the message track starts at
lo + 4. The track is read in 2-byte tokens by HT.EXE's interpreter (0x8004011C): SJIS chars, CRLF, '@' + param
(ends a message; param = wait), '*' + face, '%S' + '_' + byte (player name), '//' ends a block (blocks run in
order, one per mission trigger). The track ends at the last '//' that real text follows; after it there may be dead
leftover compiler source, then 0x1A (^Z). Header u16 at +6 = hi: when non-zero, a second script sits at hi (after
the ^Z), with the same header (offsets relative to hi) and sometimes its own track; it is never moved, so the main
track must fit before it.
"""
import re
import struct

import textcodec

AREA = 0x3800
SJIS_LEAD = set(range(0x81, 0xA0)) | set(range(0xE0, 0xF0))
CODE3D = re.compile(r"<R>|<([@*_])([0-9a-f]{2})>|<//>|<%S>")


def _block_start(t):
    return t[0] in SJIS_LEAD or t[:1] in (b"*", b"%")


def sections(s):
    """Script bases: 0, plus the second script at hi when there is one (its own header, its hi is 0)."""
    hi = struct.unpack_from("<H", s, 6)[0]
    return [0, hi] if hi else [0]


def track(s, base=0):
    """(start, end, z, limit) of the message track of the script at base, or None. end = after the last real
    '//' (or z); z = the ^Z; limit = how far a rebuilt track (plus its ^Z) may reach."""
    lo, hi = struct.unpack_from("<HH", s, base + 4)
    if lo == 0:
        return None
    start = pc = end = base + lo + 4
    while pc < AREA:
        t = s[pc:pc + 2]
        if t[0] == 0x1A:
            end = end if end > start else pc
            z = pc
            break
        pc += 2
        if t == b"//":
            end = pc
            if s[pc] != 0x1A and not _block_start(s[pc:pc + 2]):
                z = s.index(b"\x1a", pc)  # dead compiler source up to the ^Z
                break
    else:
        raise ValueError("no ^Z in the script area")
    return start, end, z, base + hi if hi else AREA


def decode(b):
    out, i = [], 0
    while i < len(b):
        t = b[i:i + 2]
        if t[0] in SJIS_LEAD:
            out.append(t.decode("cp932"))
        elif t == b"\r\n":
            out.append("<R>")
        elif t == b"//":
            out.append("<//>")
        elif t == b"%S":
            out.append("<%S>")
        elif t[:1] in (b"@", b"*", b"_"):
            out.append(f"<{chr(t[0])}{t[1]:02x}>")
        else:
            out.append(f"<${t[0]:02x}><${t[1]:02x}>")
        i += 2
    return "".join(out)


def encode(text):
    def sub(m):
        g = m.group()
        if g == "<R>":
            return "<$0d><$0a>"
        if g in ("<//>", "<%S>"):
            return "".join(f"<${c:02x}>" for c in g[1:-1].encode())
        return f"<${ord(m.group(1)):02x}><${m.group(2)}>"
    return textcodec.encode(CODE3D.sub(sub, text))


def _blocks(s, base):
    t = track(s, base)
    if not t:
        return []
    parts = decode(s[t[0]:t[1]]).split("<//>")
    return parts[:-1] if parts[-1] == "" else parts


def blocks(s):
    """Script text of each '//' block of every track (without the '//'): main script first, then the second."""
    return [b for base in sections(s) for b in _blocks(s, base)]


def build(s, texts):
    """Script area with every track rebuilt from block texts (as blocks() lists them); raises when one would
    reach past its limit. The second script is rebuilt first, so the main one's offsets never move."""
    counts = [len(_blocks(s, base)) for base in sections(s)]
    for base, n, k in reversed(list(zip(sections(s), counts, [sum(counts[:i]) for i in range(len(counts))]))):
        if n:
            s = _build(s, base, texts[k:k + n])
    return s


def _build(s, base, texts):
    start, end, z, limit = track(s, base)
    body = encode("<//>".join(texts) + ("<//>" if s[end - 2:end] == b"//" else ""))
    new = s[:start] + body
    if end == z:  # no dead source: the track ran straight into the ^Z
        new += s[z:z + 2]
    else:
        new += b"\x1a\x00"
    if len(new) > limit:
        raise ValueError(f"track {len(new) - start:#x} bytes > room {limit - start:#x}")
    if limit == AREA:
        return new.ljust(AREA, b"\0") + s[AREA:]
    return new.ljust(limit, b"\0") + s[limit:]
