"""datnames.py: name fields of BERU_FL1.DAT, the resident state template loaded at 0x80010000 (docs/re/text.md).

Ships, places, parts, ammo, items and crew are records whose first 0x1C bytes are a NUL-padded SJIS name
(stats follow), so a name holds at most 27 bytes. New games copy these into the save; old saves keep theirs.
"""
FIELD = 0x1C
LEADS = set(range(0x81, 0xA0)) | set(range(0xE0, 0xF0))


def names(d):
    """[(offset, raw bytes)] of every name field: SJIS text from a field start, NUL-padded to FIELD bytes."""
    out, p = [], 0
    while p < len(d) - FIELD:
        if d[p] in LEADS:
            end = d.index(b"\0", p)
            raw = d[p:end]
            ok = len(raw) >= 4 and len(raw) % 2 == 0 and all(raw[i] in LEADS for i in range(0, len(raw), 2))
            if ok and not any(d[end:p + FIELD]) and _sjis(raw):
                out.append((p, raw))
                p += FIELD
                continue
        p += 1
    return out


def _sjis(raw):
    try:
        raw.decode("cp932")
        return True
    except UnicodeDecodeError:
        return False


def apply(d, edits):
    """edits {offset: bytes}; raises when a name is longer than its field allows."""
    d = bytearray(d)
    for off, raw in edits.items():
        if len(raw) > FIELD - 1:
            raise ValueError(f"BERU_FL1.DAT@{off:x}: {len(raw)} bytes > {FIELD - 1}")
        d[off:off + FIELD] = raw.ljust(FIELD, b"\0")
    return bytes(d)
