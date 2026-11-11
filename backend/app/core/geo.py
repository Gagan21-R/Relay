"""Geometry on lat/lng (portable: no PostGIS). Haversine distances, point-in-polygon, simple shapes."""
import math

R_EARTH_M = 6_371_000


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_EARTH_M * math.asin(math.sqrt(a))


def point_in_polygon(lat: float, lng: float, poly: list) -> bool:
    """Ray casting on [[lat, lng], ...]."""
    inside = False
    n = len(poly)
    for i in range(n):
        y1, x1 = poly[i]
        y2, x2 = poly[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            x = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
            if lng < x:
                inside = not inside
    return inside


def in_any(lat: float, lng: float, polys: list) -> bool:
    return any(point_in_polygon(lat, lng, p) for p in polys)


def circle(lat: float, lng: float, radius_m: float, n: int = 16) -> list:
    dlat = radius_m / 111_320
    dlng = radius_m / (111_320 * math.cos(math.radians(lat)))
    return [[round(lat + dlat * math.sin(2 * math.pi * k / n), 5), round(lng + dlng * math.cos(2 * math.pi * k / n), 5)] for k in range(n)]


def lerp_point(a: list, b: list, t: float) -> list:
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]


ROAD_SAMPLES = (0.15, 0.3, 0.5, 0.7, 0.85)   # interior points: a polygon over a town centre does not cut every road


def road_samples(points: list) -> list:
    a, b = points[0], points[-1]
    return [lerp_point(a, b, t) for t in ROAD_SAMPLES]
