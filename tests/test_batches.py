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
    assert [len(p.split("<R>")) for p in out.split("<H>")] == [3, 2] and lint.problems(out, jp) == []
    assert "hearts.<W><H>We must" in out


def test_boxes_break_after_a_sentence():
    jp = "男：<R>あ<W><E>"
    out = batches.fit("Man:<R>Are you folks the Federation army? Looks like there's some Gidan folks too...<W><E>", jp)
    assert out == "Man:<R>Are you folks the<R>Federation army?<W><H>Looks like there's some<R>Gidan folks too...<W><E>"
    out = batches.fit("Zeshika:<R>Lieutenant Colonel Kafi, come with me.<W><E>", jp)
    assert out == "Zeshika:<R>Lieutenant Colonel Kafi,<R>come with me.<W><E>"


def test_wrap_pulls_a_word_down_to_a_lone_last_word():
    assert batches.wrap("I mean, Colonel Gashizakino's promotion.<W><E>", 0) == \
        ["I mean,", "Colonel Gashizakino's promotion.<W><E>"]


def test_title_stays_with_name():
    assert batches.words("Heh. I can't let Captain <F62> outdo me. Ha ha!") == \
        ["Heh.", "I", "can't", "let", "Captain <F62>", "outdo", "me.", "Ha ha!"]
    assert batches.words("the Captain, sir") == ["the", "Captain,", "sir"]
    assert batches.words("rescue His Majesty's ship") == ["rescue", "His Majesty's", "ship"]


def test_running_text_refits_to_the_same_rows():
    jp = "ガークス：<R>あ<W><H>い<W><E>"
    en = batches.fit("Garks:<R>My thanks for what you did earlier.<W><H>Please keep this between us...<W><E>", jp)
    assert batches.fit(batches.running("2D/X@0#1", en, jp), jp) == en
    m = "Hauezna:<R>We will now descend<R>to Yarskill.<R><@20>"
    assert batches.running("3D/GMPS1/G00#0", m, m) == "Hauezna:<R>We will now descend to Yarskill.<R><@20>"


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
