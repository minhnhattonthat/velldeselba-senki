import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches
import lint


def test_fit_dialogue_wraps_within_lint():
    jp = "ハウエズナ：<R>あ<W><H>い<W><E>"
    en = "Hauezna:<R>That over there is your airship, Lieutenant, and it is ready.<W><H>Now, I'll go.<W><E>"
    out = batches.fit(en, jp)
    assert out.startswith("Hauezna:<R>") and lint.problems(out, jp) == []


def test_fit_balances_rows_and_boxes():
    jp = "ガークス：<R>あ<W><E>"
    assert batches.fit("Garks:<R>Why would an aide kidnap the King?<W><E>", jp) == \
        "Garks:<R>Why would an aide<R>kidnap the King?<W><E>"
    long = "The royal house of Danaspi is the anchor of our hearts. We must win it back, no matter what.<W><E>"
    out = batches.fit("Soldier:<R>" + long, jp)
    assert [len(p.split("<R>")) for p in out.split("<H>")] == [2, 2] and lint.problems(out, jp) == []


def test_box_keeps_icon_columns():
    jp = "名前：　　<G88>　<G90><R>説明。<E>"
    out = batches.fit("Name:<G88><G90><R>About.<E>", jp)
    assert out == "Name:     <G88>  <G90><R>About.<E>"


def test_fit3d_wraps_messages_and_keeps_waits():
    out = batches.fit3d("Accelerate:<R>To speed up, press the Cross button and hold it down.<R><@28>Done.<R><@20>")
    assert out == "Accelerate:<R>To speed up, press the Cross<R>button and hold it down.<R><@28>Done.<R><@20>"


def test_has_term_whole_runs_only():
    assert batches.has_term("ノイパスク兵：", "ノイパスク")
    assert not batches.has_term("タイミング", "ミン")
