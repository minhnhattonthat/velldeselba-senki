"""batches.py: check and merge translated batches into script/ (docs/translator-brief.md).

    python -X utf8 tools/batches.py split <batch> <script/...json> [start end]   one file's untranslated lines
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


def wrap(seg, first_row):
    """Greedy word wrap of one hard-break segment; first_row = index of its first row in the page."""
    rows, cur = [], ""
    for word in seg.split(" "):
        cand = f"{cur} {word}" if cur else word
        i = first_row + len(rows)
        lim = 16 if i % 3 == 2 or "<W>" in cand else 17
        if cur and lint.width(cand) > lim:
            rows.append(cur)
            cur = word
        else:
            cur = cand
    return rows + [cur]


def fit(en, jp):
    if "<W>" not in jp:
        return en
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


def split(batch, path, start=0, end=None):
    """One batch from one script file's lines [start, end): non-empty JP, not yet translated."""
    out = TL / f"{batch}.tsv"
    if out.exists():
        sys.exit(f"{out} exists")
    data = json.loads((ROOT / path).read_text(encoding="utf-8"))
    rows = []
    for l in [l for st in data["streams"] for l in st["lines"]][int(start):end and int(end)]:
        if l["en"] or not re.sub(r"<[^>]*>|　", "", l["jp"]):
            continue
        m = SPEAKER.match(l["jp"])
        form = "dlg" if "<W>" in l["jp"] else "box"
        rows.append("\t".join([l["id"], m.group(1) if m else "", form, "auto", l["jp"]]))
    TL.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print(f"{out}: {len(rows)} lines")


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
            fitted[i] = fit(en, src[i])
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
