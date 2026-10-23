import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from lint import problems

JP = "男：<R>あいう<R>えお<W><E>"
L34, L32 = "x" * 34, "x" * 32


def test_dialogue_widths():
    assert problems(f"Man:<R>{L34}<R>{L32}<W><E>", JP) == []
    assert problems(f"Man:<R>{L34}x<R>{L32}<W><E>", JP)       # 35 letters
    assert problems(f"Man:<R>{L34}<R>{L34}<W><E>", JP)        # row before the wait cursor
    assert problems(f"Man:<R>{L34}<R>{L34}<R>{L32}<W><E>", JP)  # 3rd row with more after it
    assert problems(f"{L34}<R>{L34}<R>{L32}<R>{L32}<W><E>", JP) == []


def test_codes_must_match():
    jp = "<P13>あ<P15><W><E>"
    assert problems("<P13>a<P15><W><E>", jp) == []
    assert problems("a<W><E>", jp)


def test_menu_footprint():
    assert problems("Save", "セーブ", exe=True) == []
    assert problems("Saves", "セーブ", exe=True) == []
    assert problems("Saved!!", "セーブ", exe=True)
