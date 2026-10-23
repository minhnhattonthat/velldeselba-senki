import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import textcodec as tc


def test_japanese_roundtrip():
    raw = "ノイパスク兵：Rおい、何をもたもたしてたんだ。WE".encode("cp932")
    s = tc.decode(raw)
    assert s == "ノイパスク兵：<R>おい、何をもたもたしてたんだ。<W><E>"
    assert tc.encode(s) == raw


def test_codes_with_args():
    raw = "F61　P13G88V0,0,3　G90V2,1,4P15R".encode("cp932")
    s = tc.decode(raw)
    assert "<V0,0,3>" in s and "<P13>" in s and "<F61>" in s
    assert tc.encode(s) == raw


def test_english_pairs():
    b = tc.encode("Hi!<R>Odd<W><E>")
    assert b == bytes([0x80 + ord("H"), ord("i"), 0x80 + ord("!"), 0x7F]) + b"R" + \
        bytes([0x80 + ord("O"), ord("d"), 0x80 + ord("d"), 0x7F]) + b"WE"
    assert all(x >= 0xA0 for x in b[0::2][:2])  # lead bytes never look like codes or SJIS leads
    assert tc.decode(b, english=True) == "Hi!<R>Odd<W><E>"
    assert tc.cells("Soldier: Hey!") == 7
