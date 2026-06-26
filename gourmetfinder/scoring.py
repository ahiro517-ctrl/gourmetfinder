"""特徴量の抽出とスコアリング。

スコア = Σ ( 重み[k] × 特徴量[k] )
特徴量はおおむね 0〜1 に正規化し、重み(weights.yaml)との掛け算で順位を決める。
"""

from __future__ import annotations

from .models import Candidate, Place

# 重み(weights.yaml)と対応する特徴量のキー
FEATURE_KEYS = ["new_store", "rating", "hidden_gem", "independent", "chain_penalty"]


def extract_features(
    place: Place,
    *,
    is_new: bool,
    is_chain: bool,
    min_rating_reviews: int,
    hidden_gem_max_reviews: int,
) -> dict[str, float]:
    """1店舗の特徴量ベクトルを作る。"""
    f = {k: 0.0 for k in FEATURE_KEYS}

    # 新店の可能性
    f["new_store"] = 1.0 if is_new else 0.0

    # 評価: 口コミが一定数あるときだけ評価を信用する。3.0→0, 5.0→1 に正規化。
    if place.rating is not None and place.review_count >= min_rating_reviews:
        f["rating"] = _clamp01((place.rating - 3.0) / 2.0)

    # 穴場度: 高評価(>=3.8)かつ口コミが少なめ
    if (
        place.rating is not None
        and place.rating >= 3.8
        and 0 < place.review_count <= hidden_gem_max_reviews
    ):
        # 口コミが少ないほど穴場度を高く
        f["hidden_gem"] = _clamp01(1.0 - place.review_count / hidden_gem_max_reviews)

    # 独立系 / チェーン
    f["independent"] = 0.0 if is_chain else 1.0
    f["chain_penalty"] = 1.0 if is_chain else 0.0

    return f


def score(features: dict[str, float], weights: dict[str, float]) -> float:
    """特徴量と重みからスコアを計算する。"""
    return sum(weights.get(k, 0.0) * v for k, v in features.items())


def build_candidate(
    place: Place,
    features: dict[str, float],
    weights: dict[str, float],
    *,
    is_new: bool,
    is_chain: bool,
) -> Candidate:
    return Candidate(
        place=place,
        features=features,
        score=score(features, weights),
        is_new=is_new,
        is_chain=is_chain,
    )


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))
