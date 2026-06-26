from gourmetfinder.models import Place
from gourmetfinder.scoring import build_candidate, extract_features, score

WEIGHTS = {
    "new_store": 3.0,
    "rating": 2.0,
    "hidden_gem": 1.5,
    "independent": 1.5,
    "chain_penalty": -2.0,
}


def _place(**kw):
    base = dict(
        place_id="p1",
        name="テスト店",
        address="東京都港区港南",
        lat=35.628,
        lng=139.741,
        rating=4.4,
        review_count=20,
    )
    base.update(kw)
    return Place(**base)


def test_new_store_feature():
    f = extract_features(
        _place(review_count=10),
        is_new=True,
        is_chain=False,
        min_rating_reviews=5,
        hidden_gem_max_reviews=40,
    )
    assert f["new_store"] == 1.0


def test_rating_needs_enough_reviews():
    f = extract_features(
        _place(rating=4.8, review_count=2),
        is_new=False,
        is_chain=False,
        min_rating_reviews=5,
        hidden_gem_max_reviews=40,
    )
    assert f["rating"] == 0.0  # 口コミ不足なので評価は信用しない


def test_hidden_gem():
    f = extract_features(
        _place(rating=4.5, review_count=8),
        is_new=False,
        is_chain=False,
        min_rating_reviews=5,
        hidden_gem_max_reviews=40,
    )
    assert f["hidden_gem"] > 0


def test_chain_penalizes_score():
    indie = extract_features(
        _place(), is_new=False, is_chain=False,
        min_rating_reviews=5, hidden_gem_max_reviews=40,
    )
    chain = extract_features(
        _place(), is_new=False, is_chain=True,
        min_rating_reviews=5, hidden_gem_max_reviews=40,
    )
    assert score(indie, WEIGHTS) > score(chain, WEIGHTS)


def test_build_candidate():
    p = _place()
    f = extract_features(
        p, is_new=True, is_chain=False,
        min_rating_reviews=5, hidden_gem_max_reviews=40,
    )
    c = build_candidate(p, f, WEIGHTS, is_new=True, is_chain=False)
    assert c.score > 0
    assert c.is_new is True
