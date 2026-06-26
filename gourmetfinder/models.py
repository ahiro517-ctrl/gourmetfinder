"""データ構造の定義。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Place:
    """Google Places から取得した1店舗の情報。"""

    place_id: str
    name: str
    address: str
    lat: float
    lng: float
    types: list[str] = field(default_factory=list)
    primary_type: str = ""
    rating: Optional[float] = None
    review_count: int = 0
    price_level: str = ""
    business_status: str = ""

    @classmethod
    def from_places_api(cls, raw: dict) -> "Place":
        """Places API (New) のレスポンス1件を Place に変換する。"""
        loc = raw.get("location", {}) or {}
        name = (raw.get("displayName", {}) or {}).get("text", "")
        return cls(
            place_id=raw.get("id", ""),
            name=name,
            address=raw.get("formattedAddress", ""),
            lat=loc.get("latitude", 0.0),
            lng=loc.get("longitude", 0.0),
            types=raw.get("types", []) or [],
            primary_type=raw.get("primaryType", "") or "",
            rating=raw.get("rating"),
            review_count=raw.get("userRatingCount", 0) or 0,
            price_level=raw.get("priceLevel", "") or "",
            business_status=raw.get("businessStatus", "") or "",
        )


@dataclass
class Candidate:
    """スコアリング済みの取材候補。"""

    place: Place
    features: dict[str, float]
    score: float
    is_new: bool
    is_chain: bool
    reasons: list[str] = field(default_factory=list)
