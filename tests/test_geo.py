from gourmetfinder.geo import bounding_box, point_in_polygon

# 簡単な四角形（品川エリアを模した近似）
POLY = [
    [35.6335, 139.7385],
    [35.6340, 139.7475],
    [35.6180, 139.7490],
    [35.6170, 139.7400],
]


def test_inside():
    assert point_in_polygon(35.6250, 139.7430, POLY) is True


def test_outside_north():
    assert point_in_polygon(35.6500, 139.7430, POLY) is False


def test_outside_east():
    assert point_in_polygon(35.6250, 139.7600, POLY) is False


def test_degenerate_polygon():
    assert point_in_polygon(35.62, 139.74, [[0, 0], [1, 1]]) is False


def test_bounding_box():
    mn_lat, mn_lng, mx_lat, mx_lng = bounding_box(POLY)
    assert mn_lat == 35.6170
    assert mx_lng == 139.7490
