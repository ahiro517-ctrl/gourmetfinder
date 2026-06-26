"""エリア境界（ポリゴン）の内外判定。

外部ライブラリに依存しないよう、レイキャスティング法で自前実装する。
"""

from __future__ import annotations


def point_in_polygon(lat: float, lng: float, polygon: list[list[float]]) -> bool:
    """点(lat,lng)がポリゴンの内側にあれば True。

    polygon は [[lat, lng], ...] の頂点リスト（外周を順番に並べたもの）。
    レイキャスティング（点から右方向に伸ばした半直線が辺と交差する回数の偶奇）で判定する。
    """
    if len(polygon) < 3:
        return False

    x, y = lng, lat  # 経度=x, 緯度=y として扱う
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        yi, xi = polygon[i][0], polygon[i][1]
        yj, xj = polygon[j][0], polygon[j][1]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def bounding_box(polygon: list[list[float]]) -> tuple[float, float, float, float]:
    """ポリゴンの外接矩形 (min_lat, min_lng, max_lat, max_lng) を返す。"""
    lats = [p[0] for p in polygon]
    lngs = [p[1] for p in polygon]
    return min(lats), min(lngs), max(lats), max(lngs)
