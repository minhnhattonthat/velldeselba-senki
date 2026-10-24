"""batches.py: check and merge translated batches into script/ (docs/translator-brief.md).

    python -X utf8 tools/batches.py split [max_chars max_lines kinds]   all untranslated unique JP -> b001...
    python -X utf8 tools/batches.py check <batch>    fit + lint work/tl/<batch>.out.tsv against work/tl/<batch>.tsv
    python -X utf8 tools/batches.py merge <batch>     check, then write the fitted English into script/**.json
    python -X utf8 tools/batches.py pick <batch> REGEX...   merged lines whose id matches -> <batch>.tsv/.out.tsv
                                                             (running text) for later edits, then check + merge

Input `work/tl/<batch>.tsv`: id<TAB>speaker<TAB>form<TAB>limit<TAB>jp. Output `<batch>.out.tsv`: id<TAB>en.
Translators write dialogue pages (<H>) as running text; fit() wraps them into rows (lint.width), keeping any <R>
they wrote as a hard break (after the speaker label). Other forms are taken as written.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import lint

TL = ROOT / "work/tl"


TITLE = re.compile(r"(Captain|Lieutenant|Colonel|Commander|Admiral|Major|Sergeant|General|President|Dr\.)$")


def words(seg):
    """Words to wrap; a title stays with the name after it ("Captain <F62>"), and a laugh with itself ("Ha ha")."""
    out = []
    for w in seg.split(" "):
        prev = out[-1] if out else ""
        glue = ((TITLE.search(prev) and re.match(r"[A-Z<]", w)) or (prev in ("His", "Her", "Your") and
                w.startswith("Majesty")) or (prev.lower() in ("ha", "heh") and w.lower().startswith(("ha", "heh"))))
        if glue and lint.width(f"{prev} {w}") <= 15:
            out[-1] = f"{prev} {w}"
        else:
            out.append(w)
    return out


def greedy(seg, first_row, three_d=False, cap=99):
    """Greedy word wrap of one hard-break segment; first_row = index of its first row in the page."""
    rows, cur = [], ""
    for word in words(seg):
        cand = f"{cur} {word}" if cur else word
        i = first_row + len(rows)
        if three_d:
            over = lint.width3d(cand) > min(15, cap)
        else:
            over = lint.width(cand) > min(16 if i % 3 == 2 or "<W>" in cand else 17, cap)
        if cur and over:
            rows.append(cur)
            cur = word
        else:
            cur = cand
    return rows + [cur]


def wrap(seg, first_row, three_d=False):
    """Balanced wrap: of the layouts with greedy's row count (narrower caps, or a row break after a sentence), the
    one with the most rows ending a sentence, then the narrowest."""
    alts = [greedy(seg, first_row, three_d)]
    w = lint.width3d if three_d else lint.width
    for cap in range(max(map(w, alts[0])) - 1, 0, -1):
        alt = greedy(seg, first_row, three_d, cap)
        if len(alt) > len(alts[0]):
            break
        alts.append(alt)
    ws = words(seg)
    for k in range(1, len(ws)):
        if END.search(ws[k - 1]):
            head = greedy(" ".join(ws[:k]), first_row, three_d)
            alt = head + greedy(" ".join(ws[k:]), first_row + len(head), three_d)
            if len(alt) == len(alts[0]):
                alts.append(alt)
    best = max(alts, key=lambda a: (sum(bool(END.search(r)) for r in a[:-1]), -max(map(w, a))))
    if len(best) > 1 and " " not in best[-1] and len(words(best[-2])) > 1:  # pull a word down to a lone one
        *head, word = words(best[-2])
        if " " in " ".join(head) and len(greedy(f"{word} {best[-1]}", first_row + len(best) - 1, three_d)) == 1:
            best = best[:-2] + [" ".join(head), f"{word} {best[-1]}"]
    return best


def boxes(rows):
    """A page whose last box would hold one row ends a row early (<W><H>), so the last two boxes hold 2 rows each.
    Words the wait cursor pushes off that row move to the new box; skipped if they don't fit there."""
    if len(rows) > 3 and len(rows) % 3 == 1:
        head, tail = rows[:-2], " ".join(rows[-2:])
        while lint.width(head[-1]) > 16:
            head[-1], _, word = head[-1].rpartition(" ")
            tail = f"{word} {tail}"
        tail = wrap(tail, 0)
        if head[-1] and len(tail) == 2:
            return "<R>".join(head) + "<W><H>" + "<R>".join(tail)
    return "<R>".join(rows)


END = re.compile(r"(\.|!|\?|…)[\"')」]*(<[^>]*>)*$")
CLAUSE = re.compile(r"[,;:—-][\"')]*(<[^>]*>)*$")


def page(text, r0):
    """Running text -> boxes (<W><H> between them): the fewest boxes, breaking after a sentence where it can, else
    after a clause; a box ending on a one-word row or a last box of one row costs extra. None if a word won't fit."""
    ws, memo = words(text), {}

    def best(i, r0):  # (boxes, penalty), rows per box, for ws[i:] starting at row r0
        if (i, r0) not in memo:
            memo[i, r0] = None
            for j in range(i + 1, len(ws) + 1):
                last = j == len(ws)
                rows = wrap(" ".join(ws[i:j]) + ("" if last else "<W>"), r0)
                if r0 + len(rows) > 3:
                    break
                pen = 2 * (j - i > 1 or not last) * (" " not in rows[-1])
                if last:
                    cand = ((1, pen + 3 * (r0 == 0 and len(rows) == 1 and i > 0)), [rows])
                else:
                    rest = best(j, 0)
                    if rest is None:
                        continue
                    pen += 3 - r0 - len(rows)  # rows left empty in a box that isn't the last
                    pen += 0 if END.search(ws[j - 1]) else 2 if CLAUSE.search(ws[j - 1]) else 4
                    cand = ((rest[0][0] + 1, rest[0][1] + pen), [rows] + rest[1])
                if memo[i, r0] is None or cand[0] <= memo[i, r0][0]:  # ties: the fuller earlier box
                    memo[i, r0] = cand
        return memo[i, r0]

    got = best(0, r0)
    return None if got is None else "<H>".join("<R>".join(b) for b in got[1])


def fit3d(en):
    """3D messages (between <@hh> waits): wrap each to 30 letters; a message keeps its trailing CRLF."""
    out = []
    for part in re.split(r"(<@[0-9a-f]{2}>)", en):
        if re.fullmatch(r"<@[0-9a-f]{2}>", part) or not part:
            out.append(part)
            continue
        tail = part.endswith("<R>")
        body = part[:-3] if tail else part
        rows = []
        for seg in body.split("<R>"):
            rows += wrap(seg.strip(), 0, True)
        out.append("<R>".join(rows) + ("<R>" if tail else ""))
    return "".join(out)


def pad_box(en, jp):
    """Profiles/items: a text run the JP padded with 　 before a code (icons drawn at the cursor) is padded with
    spaces to the same cells, so the icons stay in their columns. A row the JP pads to the box width before <R> is
    padded too: the profile box wraps at 17 cells and doesn't break on a <R> mid-row (playtest: "andfelE")."""
    jrows, erows, rows = jp.split("<R>"), en.split("<R>"), []
    for k, row in enumerate(erows):
        toks, jtoks = re.split(r"(<[^>]*>)", row), re.split(r"(<[^>]*>)", jrows[min(k, len(jrows) - 1)])
        for i in range(0, min(len(toks), len(jtoks)) - 1, 2):  # text runs followed by a code
            if jtoks[i].endswith("　"):
                toks[i] = toks[i].ljust(2 * lint.textcodec.cells(jtoks[i]))
        if k < len(erows) - 1 and k < len(jrows) - 1 and jtoks[-1].endswith("　"):
            toks[-1] = toks[-1].ljust(2 * lint.textcodec.cells(jtoks[-1]))
        rows.append("".join(toks))
    return "<R>".join(rows)


def fit(en, jp, three_d=False):
    if three_d:
        return fit3d(en)
    if "<W>" not in jp:
        return pad_box(en, jp)
    pages = []
    for pg in en.split("<H>"):
        segs = [s.strip() for s in pg.split("<R>")]
        head = segs[:1] if len(segs) == 2 and LABEL.match(segs[0]) else []
        boxed = page(segs[-1], len(head)) if len(segs) == len(head) + 1 else None
        if boxed is not None:
            pages.append("<R>".join(head + [boxed]))
            continue
        rows = []
        for seg in segs:
            rows += wrap(seg, len(rows))
        pages.append(boxes(rows))
    return "<H>".join(pages)


def mission(i):
    """3D mission message block (3D/*/G00#0), not a 3D program string (3D/GMPS1/HT.EXE@...)."""
    return i.startswith("3D/") and ".EXE@" not in i


def problems(i, en, jp):
    out = [] if en.isascii() else ["non-ASCII"]
    if "\t" in en or "\\u" in en:
        out.append("tab or \\u escape")
    if mission(i):
        return out + lint.problems3d(en, jp)
    if i.startswith("BERU_FL1.DAT"):
        n = len(lint.textcodec.encode(en))
        return out + ([f"{n} bytes > {lint.datnames.FIELD - 1}"] if n > lint.datnames.FIELD - 1 else [])
    return out + lint.problems(en, jp, *lint.limits(i))


SPEAKER = re.compile(r"(?:<P\d+>)?([^<：]*)：")


def form(i, jp):
    """(form, limit) shown to the translator."""
    if mission(i):
        return "msg3d", "wrapped: 30/row, 3 rows per message"
    if "<W>" in jp:
        return "dlg", "wrapped: 34/row"
    if i.startswith("STAFF.EXE@"):
        return "staff", f"max {lint.STAFF_CELLS * 2} letters per row"
    if ".EXE@" in i or "SCPS" in i:
        return "menu", "max letters per row: " + ", ".join(str(lint.width(r) * 2) for r in jp.split("<R>"))
    return "box",f"{jp.count('<R>') + 1} rows x 34, padding auto"


def glossary():
    """[(jp, en)] from the glossary tables; 'a / b' cells pair up."""
    out = []
    for l in (ROOT / "glossary.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in l.strip("|").split("|")]
        if len(cells) >= 2 and re.search(r"[ぁ-ヶ一-龯]", cells[0]):
            jps, ens = cells[0].split(" / "), cells[1].split(" / ")
            out += zip(jps, ens) if len(jps) == len(ens) else [(j, cells[1]) for j in jps]
    return out


def has_term(jp, term):
    """term as a whole katakana/kanji run (ミン must not match inside タイミング)."""
    kata, kanji = r"ァ-ヶー・", r"一-龯"
    edge = kata if re.match(f"[{kata}]", term[-1]) else kanji
    start = kata if re.match(f"[{kata}]", term[0]) else kanji
    return re.search(f"(?<![{start}]){re.escape(term)}(?![{edge}])", jp) is not None


def split(max_chars=3500, max_lines=150, kinds="maps,missions"):
    """Every untranslated unique JP string of the given script kinds -> work/tl/b001.tsv... (+ .terms.txt)."""
    TL.mkdir(parents=True, exist_ok=True)
    if list(TL.glob("b[0-9][0-9][0-9].tsv")):
        sys.exit("work/tl already holds b*.tsv batches: merge or remove them first")
    done, seen, batches, cur, size = set(), set(), [], [], 0
    files = [p for k in kinds.split(",") for p in sorted((ROOT / "script" / k).rglob("*.json"))]
    for p in sorted((ROOT / "script").rglob("*.json")):
        for st in json.loads(p.read_text(encoding="utf-8"))["streams"]:
            done |= {l["jp"] for l in st["lines"] if l["en"]}
    for p in files:
        for st in json.loads(p.read_text(encoding="utf-8"))["streams"]:
            for l in st["lines"]:
                jp = l["jp"]
                n = len(re.sub(r"<[^>]*>|　", "", jp))
                if not n or jp in done or jp in seen:
                    continue
                seen.add(jp)
                if cur and (size + n > int(max_chars) or len(cur) >= int(max_lines)):
                    batches.append(cur)
                    cur, size = [], 0
                cur.append(l)
                size += n
    batches += [cur] if cur else []
    terms = glossary()
    for b, lines in enumerate(batches, 1):
        rows = []
        for l in lines:
            m = SPEAKER.match(l["jp"])
            rows.append("\t".join([l["id"], m.group(1) if m else "", *form(l["id"], l["jp"]), l["jp"]]))
        (TL / f"b{b:03d}.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        hits = sorted({f"{j} = {e}" for j, e in terms if any(has_term(l["jp"], j) for l in lines)})
        (TL / f"b{b:03d}.terms.txt").write_text("\n".join(hits) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(batches)} batches, {len(seen)} strings -> {TL}")


def load(batch):
    src = {}
    for l in (TL / f"{batch}.tsv").read_text(encoding="utf-8").splitlines():
        i, _speaker, _form, _limit, jp = l.split("\t")
        src[i] = jp
    out = {}
    for n, l in enumerate((TL / f"{batch}.out.tsv").read_text(encoding="utf-8").splitlines(), 1):
        if not l.strip():
            continue
        i, _, en = l.partition("\t")
        if i in out:
            sys.exit(f"line {n}: duplicate id {i}")
        out[i] = en.strip()
    return src, out


def check(batch):
    src, out = load(batch)
    bad = [f"missing: {i}" for i in src if i not in out] + [f"extra: {i}" for i in out if i not in src]
    fitted = {}
    for i, en in out.items():
        if i in src:
            fitted[i] = fit(en, src[i], mission(i))
            bad += [f"{i}: {p}" for p in problems(i, fitted[i], src[i])]
    print("\n".join(bad) if bad else "OK")
    return fitted, not bad


def merge(batch):
    fitted, ok = check(batch)
    if not ok:
        sys.exit(1)
    done = 0
    for p in sorted((ROOT / "script").rglob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        hit = False
        for st in data["streams"]:
            for l in st["lines"]:
                if l["id"] in fitted:
                    l["en"], hit = fitted[l["id"]], True
                    done += 1
        if hit:
            p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"merged {done}/{len(fitted)}")


LABEL = re.compile(r"^(<P\d+>)?(<F62>|<%S><_00>|[^<:]{1,30}):(<P\d+>)?$")


def unwrap(rows):
    """Wrapped rows -> running text, keeping the hard break after a speaker label and after a <W>."""
    out, cur = [], []
    for r in rows:
        cur.append(r)
        if LABEL.match(r) or "<W>" in r:
            out.append(" ".join(cur))
            cur = []
    return "<R>".join(out + ([" ".join(cur)] if cur else []))


def running(i, en, jp):
    """Merged English back to the running text a translator writes (fit() wraps it again)."""
    if mission(i):
        return "".join(p if re.fullmatch(r"<@[0-9a-f]{2}>", p) or not p else
                       unwrap(p[:-3].split("<R>")) + "<R>" if p.endswith("<R>") else unwrap(p.split("<R>"))
                       for p in re.split(r"(<@[0-9a-f]{2}>)", en))
    if "<W>" in jp:
        return "<H>".join(unwrap(pg.split("<R>")) for pg in en.split("<H>"))
    return en


def pick(batch, *patterns):
    """Batch of already-merged lines (ids matching any regex) for later edits; keeps rows already in out.tsv."""
    pats = [re.compile(p) for p in patterns]
    out = TL / f"{batch}.out.tsv"
    old = dict(l.split("\t", 1) for l in out.read_text(encoding="utf-8").splitlines() if l) if out.is_file() else {}
    rows, outs = [], []
    for p in sorted((ROOT / "script").rglob("*.json")):
        for st in json.loads(p.read_text(encoding="utf-8"))["streams"]:
            for l in st["lines"]:
                if l["en"] and any(r.search(l["id"]) for r in pats):
                    m = SPEAKER.match(l["jp"])
                    rows.append("\t".join([l["id"], m.group(1) if m else "", *form(l["id"], l["jp"]), l["jp"]]))
                    outs.append(f"{l['id']}\t{old.get(l['id'], running(l['id'], l['en'], l['jp']))}")
    (TL / f"{batch}.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    out.write_text("\n".join(outs) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(rows)} lines -> {TL / batch}.tsv")


if __name__ == "__main__":
    {"split": split, "check": check, "merge": merge, "pick": pick}[sys.argv[1]](*sys.argv[2:])
