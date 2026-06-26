"""チェーン店判定。"""

from __future__ import annotations

from typing import Callable, Optional

from .models import Place


def is_chain(
    place: Place,
    keywords: list[str],
    *,
    nationwide_count_fn: Optional[Callable[[str], int]] = None,
    nationwide_threshold: int = 8,
) -> bool:
    """店舗がチェーンらしいかどうかを判定する。

    1) 店名にチェーンのキーワードが含まれていれば True。
    2) nationwide_count_fn が渡され、同名店が全国に閾値以上あれば True。
    """
    name = place.name or ""
    for kw in keywords:
        if kw and kw in name:
            return True

    if nationwide_count_fn is not None and name:
        try:
            count = nationwide_count_fn(name)
        except Exception:
            count = 0
        if count >= nationwide_threshold:
            return True

    return False
