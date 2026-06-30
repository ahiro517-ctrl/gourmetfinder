from gourmetfinder.learning import Feedback, learn_chain_keywords, update_weights

WEIGHTS = {
    "new_store": 3.0,
    "rating": 2.0,
    "hidden_gem": 1.5,
    "independent": 1.5,
    "chain_penalty": -2.0,
}
BOUNDS = {"min": -5.0, "max": 5.0}


def test_like_increases_active_weights():
    fb = [Feedback("p1", "○", "良い", {"new_store": 1.0, "rating": 0.5})]
    w = update_weights(WEIGHTS, fb, learning_rate=0.3, bounds=BOUNDS)
    assert w["new_store"] > WEIGHTS["new_store"]
    assert w["rating"] > WEIGHTS["rating"]


def test_dislike_decreases_active_weights():
    fb = [Feedback("p1", "×", "", {"new_store": 1.0})]
    w = update_weights(WEIGHTS, fb, learning_rate=0.3, bounds=BOUNDS)
    assert w["new_store"] < WEIGHTS["new_store"]


def test_neutral_no_change():
    fb = [Feedback("p1", "△", "", {"new_store": 1.0})]
    w = update_weights(WEIGHTS, fb, learning_rate=0.3, bounds=BOUNDS)
    assert w == WEIGHTS


def test_liking_chain_reduces_penalty():
    # チェーンを ○ にすると chain_penalty が 0 に近づく（減点が弱まる）
    fb = [Feedback("p1", "○", "", {"chain_penalty": 1.0})]
    w = update_weights(WEIGHTS, fb, learning_rate=0.3, bounds=BOUNDS)
    assert w["chain_penalty"] > WEIGHTS["chain_penalty"]


def test_bounds_respected():
    fb = [Feedback("p1", "○", "", {"new_store": 1.0})] * 100
    w = update_weights(WEIGHTS, fb, learning_rate=0.3, bounds=BOUNDS)
    assert w["new_store"] <= BOUNDS["max"]


def test_learn_chain_keyword_uses_brand_token():
    # 「ブランド名 + 支店名」から先頭ブランドを学習する
    fb = [Feedback("p1", "×", "チェーン嫌", {})]
    kw = learn_chain_keywords(
        ["既存"], fb, name_by_place_id={"p1": "スターバックス 品川港南店"}
    )
    assert "スターバックス" in kw


def test_learn_chain_keyword_various_tags():
    # 「全国」「ナショナル」など『チェーン』以外の語でも反応する
    fb = [Feedback("p1", "×", "ナショナルチェーンNG", {})]
    kw = learn_chain_keywords(["既存"], fb, name_by_place_id={"p1": "PRONTO 品川店"})
    assert "PRONTO" in kw


def test_learn_chain_keyword_ignores_non_chain_tag():
    fb = [Feedback("p1", "×", "遠い", {})]
    kw = learn_chain_keywords(["既存"], fb, name_by_place_id={"p1": "遠い店"})
    assert "遠い店" not in kw


def test_independent_weight_never_inverts():
    # 独立系の店を大量に × しても independent はマイナスに反転しない（0で下げ止まる）
    fb = [Feedback("p1", "×", "", {"independent": 1.0})] * 100
    w = update_weights(WEIGHTS, fb, learning_rate=0.3, bounds=BOUNDS)
    assert w["independent"] >= 0.0


def test_chains_never_outrank_independents_after_heavy_dislike():
    # 独立系を大量に × した後でも、独立系スコア > チェーンスコア が保たれる
    fb = [Feedback("p1", "×", "", {"rating": 0.5, "independent": 1.0})] * 100
    w = update_weights(WEIGHTS, fb, learning_rate=0.3, bounds=BOUNDS)
    indie = w["independent"] * 1.0  # 独立系の寄与
    chain = w["chain_penalty"] * 1.0  # チェーンの寄与
    assert indie >= chain
