from gourmetfinder.blocklist import is_blocked
from gourmetfinder.models import Place

KEYWORDS = ["わらやき屋", "GLASS DANCE", "美食米門"]


def _place(name):
    return Place(place_id="p", name=name, address="", lat=0, lng=0)


def test_block_exact_brand():
    assert is_blocked(_place("わらやき屋 品川"), KEYWORDS) is True


def test_block_other_branch_same_brand():
    # 別店舗・別表記でもブランド名の核で拾える
    assert is_blocked(_place("美食米門 品川港南 WINE&GRILL"), KEYWORDS) is True


def test_block_case_insensitive():
    assert is_blocked(_place("glass dance 品川港南"), KEYWORDS) is True


def test_not_blocked():
    assert is_blocked(_place("鮨処 こうなん"), KEYWORDS) is False


def test_empty_name():
    assert is_blocked(_place(""), KEYWORDS) is False
