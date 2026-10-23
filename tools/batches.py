"""batches.py: check and merge translated batches into script/ (docs/translator-brief.md).

    python -X utf8 tools/batches.py split [max_chars max_lines kinds]   all untranslated unique JP -> b001...
    python -X utf8 tools/batches.py check <batch>    fit + lint work/tl/<batch>.out.tsv against work/tl/<batch>.tsv
    python -X utf8 tools/batches.py merge <batch>     check, then write the fitted English into script/**.json

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


def wrap(seg, first_row, three_d=False):
    """Greedy word wrap of one hard-break segment; first_row = index of its first row in the page."""
    rows, cur = [], ""
    for word in seg.split(" "):
        cand = f"{cur} {word}" if cur else word
        i = first_row + len(rows)
        if three_d:
            over = lint.width3d(cand) > 15
        else:
            over = lint.width(cand) > (16 if i % 3 == 2 or "<W>" in cand else 17)
        if cur and over:
            rows.append(cur)
            cur = word
        else:
            cur = cand
    return rows + [cur]


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
    spaces to the same cells, so the icons stay in their columns."""
    jrows, rows = jp.split("<R>"), []
    for k, row in enumerate(en.split("<R>")):
        toks, jtoks = re.split(r"(<[^>]*>)", row), re.split(r"(<[^>]*>)", jrows[min(k, len(jrows) - 1)])
        for i in range(0, min(len(toks), len(jtoks)) - 1, 2):  # text runs followed by a code
            if jtoks[i].endswith("　"):
                toks[i] = toks[i].ljust(2 * lint.textcodec.cells(jtoks[i]))
        rows.append("".join(toks))
    return "<R>".join(rows)


def fit(en, jp, three_d=False):
    if three_d:
        return fit3d(en)
    if "<W>" not in jp:
        return pad_box(en, jp)
    pages = []
    for page in en.split("<H>"):
        rows = []
        for seg in page.split("<R>"):
            rows += wrap(seg.strip(), len(rows))
        pages.append("<R>".join(rows))
    return "<H>".join(pages)


def problems(i, en, jp):
    out = [] if en.isascii() else ["non-ASCII"]
    if "\t" in en or "\\u" in en:
        out.append("tab or \\u escape")
    if i.startswith("3D/"):
        return out + lint.problems3d(en, jp)
    if i.startswith("BERU_FL1.DAT"):
        n = len(lint.textcodec.encode(en))
        return out + ([f"{n} bytes > {lint.datnames.FIELD - 1}"] if n > lint.datnames.FIELD - 1 else [])
    return out + lint.problems(en, jp, ".EXE@" in i or "SCPS" in i)


SPEAKER = re.compile(r"(?:<P\d+>)?([^<：]*)：")


def form(i, jp):
    """(form, limit) shown to the translator."""
    if i.startswith("3D/"):
        return "msg3d", "wrapped: 30/row, 3 rows per message"
    if "<W>" in jp:
        return "dlg", "wrapped: 34/row"
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
            fitted[i] = fit(en, src[i], i.startswith("3D/"))
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


if __name__ == "__main__":
    {"split": split, "check": check, "merge": merge}[sys.argv[1]](*sys.argv[2:])
