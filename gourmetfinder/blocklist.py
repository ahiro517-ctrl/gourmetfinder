"""取材NGリストの判定。

チェーン判定(chains.py)が「減点」なのに対し、こちらは「完全除外」。
取材を断られる運営会社・店舗のキーワードが店名に含まれる店は、
スコアに関係なく候補から外す（pipeline.build_candidates で使用）。
"""

from __future__ import annotations

from .models import Place


def is_blocked(place: Place, keywords: list[str]) -> bool:
    """店名が取材NGキーワードを含むなら True（大文字小文字は区別しない）。"""
    name = (place.name or "").lower()
    if not name:
        return False
    for kw in keywords:
        if kw and kw.lower() in name:
            return True
    return False
