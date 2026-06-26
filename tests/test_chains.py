from gourmetfinder.chains import is_chain
from gourmetfinder.models import Place

KEYWORDS = ["スターバックス", "丸亀製麺", "サイゼリヤ"]


def _place(name):
    return Place(place_id="p", name=name, address="", lat=0, lng=0)


def test_keyword_match():
    assert is_chain(_place("スターバックス 品川港南店"), KEYWORDS) is True


def test_independent():
    assert is_chain(_place("鮨処 こうなん"), KEYWORDS) is False


def test_nationwide_check():
    def counter(name):
        return 12

    assert is_chain(
        _place("どこにでもある店"), KEYWORDS,
        nationwide_count_fn=counter, nationwide_threshold=8,
    ) is True


def test_nationwide_below_threshold():
    def counter(name):
        return 3

    assert is_chain(
        _place("珍しい店"), KEYWORDS,
        nationwide_count_fn=counter, nationwide_threshold=8,
    ) is False
