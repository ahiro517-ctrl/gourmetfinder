"""フィードバックからの軽量学習（スコア重みの調整）。

考え方（パーセプトロン的な更新）:
  ○（取材したい）   → その店の特徴量の方向に重みを少し増やす（次から上位に）
  ×（却下）         → その店の特徴量の方向に重みを少し減らす（次から下位に）
  △（微妙）         → 変更しない

例) チェーン店を ○ にし続けると chain_penalty が 0 に近づき、減点が弱まる。
"""

from __future__ import annotations

from dataclasses import dataclass


# 評価ラベル（スプレッドシートに人が記入する値）
LIKE = {"○", "◯", "o", "O", "取材したい", "取材", "yes", "Yes"}
DISLIKE = {"×", "x", "X", "却下", "no", "No"}

# 各特徴量の「意味としての符号」。学習でこの符号は反転させない。
#  +1: 大きいほど良い（独立系・高評価・新店・穴場）
#  -1: 大きいほど悪い（チェーン）
# これにより「× された独立系が多い → independentがマイナスに反転 → チェーンが上位」
# という誤学習を防ぐ。学習は符号を保ったまま強さ(絶対値)だけ調整する。
FEATURE_SIGNS = {
    "new_store": 1,
    "rating": 1,
    "hidden_gem": 1,
    "independent": 1,
    "chain_penalty": -1,
}

# このいずれかをタグに含む × を「チェーンだから却下」とみなし、チェーン語を学習する
CHAIN_TAG_HINTS = ("チェーン", "全国", "ナショナル", "大手", "フランチャイズ")


@dataclass
class Feedback:
    place_id: str
    evaluation: str
    tags: str
    features: dict[str, float]


def _sign(evaluation: str) -> int:
    e = (evaluation or "").strip()
    if e in LIKE:
        return 1
    if e in DISLIKE:
        return -1
    return 0


def update_weights(
    weights: dict[str, float],
    feedback: list[Feedback],
    *,
    learning_rate: float,
    bounds: dict[str, float],
) -> dict[str, float]:
    """フィードバックに基づいて重みを更新して返す（破壊的変更はしない）。"""
    new_weights = dict(weights)
    lo = bounds.get("min", -5.0)
    hi = bounds.get("max", 5.0)

    for fb in feedback:
        s = _sign(fb.evaluation)
        if s == 0:
            continue
        for k, v in fb.features.items():
            if v == 0:
                continue
            updated = new_weights.get(k, 0.0) + learning_rate * s * v
            updated = max(lo, min(hi, updated))
            # 特徴量の意味としての符号を超えない（反転させない）
            sign_dir = FEATURE_SIGNS.get(k, 0)
            if sign_dir > 0:
                updated = max(0.0, updated)
            elif sign_dir < 0:
                updated = min(0.0, updated)
            new_weights[k] = updated

    return new_weights


def _brand_token(name: str) -> str:
    """店名から「ブランド名」らしき部分を取り出す。

    多くのチェーンは「ブランド名 + 支店名」（例: 『PRONTO 品川店』『スターバックス 品川港南店』）
    なので、最初の空白までを取るとブランド名になりやすい。空白が無ければ全体を使う。
    """
    name = (name or "").strip()
    for sep in (" ", "　"):
        if sep in name:
            return name.split(sep)[0]
    return name


def learn_chain_keywords(
    keywords: list[str],
    feedback: list[Feedback],
    *,
    name_by_place_id: dict[str, str],
) -> list[str]:
    """× かつ「チェーン系」を示すタグのフィードバックから、ブランド名をチェーン語に追加する。

    タグに『チェーン/全国/ナショナル/大手/フランチャイズ』のいずれかを含む × を対象とし、
    店名の先頭ブランド部分を登録する（同チェーンの他支店にも効くようにするため）。
    """
    new_keywords = list(keywords)
    for fb in feedback:
        if _sign(fb.evaluation) != -1:
            continue
        tags = fb.tags or ""
        if not any(h in tags for h in CHAIN_TAG_HINTS):
            continue
        token = _brand_token(name_by_place_id.get(fb.place_id, ""))
        if token and token not in new_keywords:
            new_keywords.append(token)
    return new_keywords
