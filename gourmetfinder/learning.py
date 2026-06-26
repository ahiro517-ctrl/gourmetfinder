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
            new_weights[k] = max(lo, min(hi, updated))

    return new_weights


def learn_chain_keywords(
    keywords: list[str],
    feedback: list[Feedback],
    *,
    name_by_place_id: dict[str, str],
) -> list[str]:
    """× かつ タグに「チェーン」を含むフィードバックから、店名をチェーン語に追加する。

    完全な店名を入れると汎用性が低いが、明示的に「チェーン嫌」と言われた店は
    次回から確実に減点したいので、店名そのものを追加する保守的な実装。
    """
    new_keywords = list(keywords)
    for fb in feedback:
        if _sign(fb.evaluation) != -1:
            continue
        if "チェーン" not in (fb.tags or ""):
            continue
        name = name_by_place_id.get(fb.place_id, "")
        if name and name not in new_keywords:
            new_keywords.append(name)
    return new_keywords
