"""取材理由の文章を、寄与した特徴量からテンプレで生成する。"""

from __future__ import annotations

from .models import Candidate


def build_reasons(cand: Candidate) -> list[str]:
    """候補1件の「なぜ取材すべきか」を箇条書きで返す。"""
    place = cand.place
    f = cand.features
    reasons: list[str] = []

    if f.get("new_store", 0) > 0:
        reasons.append(
            f"新規オープンの可能性（今週はじめて検知・口コミ{place.review_count}件と少数）"
        )

    if f.get("hidden_gem", 0) > 0:
        reasons.append(
            f"穴場度が高い（★{place.rating} と高評価ながら口コミ{place.review_count}件と少なめ）"
        )
    elif f.get("rating", 0) > 0:
        reasons.append(f"高評価（★{place.rating}・口コミ{place.review_count}件）")

    if f.get("independent", 0) > 0:
        reasons.append("独立系で、このエリア独自の存在（全国チェーンではない）")

    if f.get("chain_penalty", 0) > 0:
        reasons.append("全国チェーン系のため優先度はやや低め（NGではない）")

    if not reasons:
        reasons.append("基礎情報のみ（要・現地確認）")

    return reasons


def summary_line(cand: Candidate) -> str:
    """1行サマリ。"""
    return " / ".join(build_reasons(cand))
