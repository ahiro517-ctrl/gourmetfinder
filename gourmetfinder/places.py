"""Google Places API (New) クライアント。

公式ドキュメント: https://developers.google.com/maps/documentation/places/web-service
- searchNearby: 円の中の店舗を取得
- searchText  : キーワード検索（チェーンの全国件数チェックに使用）
"""

from __future__ import annotations

import time
from typing import Optional

import requests

from .models import Place

SEARCH_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
SEARCH_TEXT_URL = "https://places.googleapis.com/v1/places:searchText"

# 取得するフィールド（FieldMask）。多いほど料金が上がるので必要分だけ。
NEARBY_FIELDS = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.types",
        "places.primaryType",
        "places.rating",
        "places.userRatingCount",
        "places.priceLevel",
        "places.businessStatus",
    ]
)


class PlacesClient:
    def __init__(self, api_key: str, *, language: str = "ja", region: str = "JP"):
        if not api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY が設定されていません。")
        self.api_key = api_key
        self.language = language
        self.region = region
        self.session = requests.Session()

    def _headers(self, field_mask: str) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": field_mask,
        }

    def _post(self, url: str, field_mask: str, body: dict) -> dict:
        """POSTし、エラー時は Google のエラー本文を含めて分かりやすく投げる。"""
        resp = self.session.post(
            url, headers=self._headers(field_mask), json=body, timeout=30
        )
        if not resp.ok:
            # Google のエラー本文（原因が書かれている）を抽出して例外に載せる
            detail = ""
            try:
                err = resp.json().get("error", {})
                detail = f"{err.get('status', '')}: {err.get('message', '')}"
            except Exception:
                detail = resp.text[:500]
            raise RuntimeError(
                f"Google Places API がエラーを返しました (HTTP {resp.status_code})。\n"
                f"  内容: {detail}\n"
                f"  → 多くは『Places API (New) が未有効』『課金(請求先)未設定』"
                f"『APIキーの制限(HTTPリファラー制限など)』が原因です。"
                f" docs/SETUP_GUIDE.md の STEP 3〜4 を確認してください。"
            )
        return resp.json()

    def search_nearby_circle(
        self, lat: float, lng: float, radius_m: float, included_types: list[str]
    ) -> list[Place]:
        """1つの円の中の店舗を取得する（最大20件）。"""
        body = {
            "includedTypes": included_types,
            "maxResultCount": 20,
            "languageCode": self.language,
            "regionCode": self.region,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": radius_m,
                }
            },
        }
        data = self._post(SEARCH_NEARBY_URL, NEARBY_FIELDS, body)
        return [Place.from_places_api(p) for p in data.get("places", [])]

    def search_all_circles(
        self, circles: list[dict], included_types: list[str]
    ) -> list[Place]:
        """複数の円を検索し、place_id で重複を除いてまとめて返す。"""
        seen: dict[str, Place] = {}
        for c in circles:
            places = self.search_nearby_circle(
                c["lat"], c["lng"], c["radius_m"], included_types
            )
            for p in places:
                if p.place_id and p.place_id not in seen:
                    seen[p.place_id] = p
            time.sleep(0.2)  # 軽いレート制御
        return list(seen.values())

    def count_text_search(self, query: str) -> int:
        """キーワード検索のヒット件数（最大20）。チェーンの全国件数チェック用。"""
        body = {
            "textQuery": query,
            "languageCode": self.language,
            "regionCode": self.region,
            "maxResultCount": 20,
        }
        data = self._post(SEARCH_TEXT_URL, "places.id", body)
        return len(data.get("places", []))


def make_nationwide_counter(
    client: PlacesClient, enabled: bool
) -> Optional[callable]:
    """全国件数チェック関数を返す（無効時は None）。"""
    if not enabled:
        return None
    return client.count_text_search
