"""
geo_route/geo_utils.py — pure geometry helpers. Standard library only.

No numpy, no geopy, no shapely: keeps `pip install` friction at zero for a
2-day sprint and for whoever clones this on a laptop 10 minutes before demo.
"""

import math

EARTH_RADIUS_M = 6371008.8


def haversine_m(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres between two lat/lon points."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2):
    """Initial compass bearing from point 1 to point 2, in degrees [0, 360)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def angle_diff_deg(a, b):
    """Smallest signed difference a-b, wrapped to (-180, 180]."""
    return (a - b + 180.0) % 360.0 - 180.0


def destination_point(lat, lon, bearing, distance_m):
    """Point reached by travelling `distance_m` from (lat, lon) on `bearing`."""
    d = distance_m / EARTH_RADIUS_M
    br = math.radians(bearing)
    p1, l1 = math.radians(lat), math.radians(lon)
    p2 = math.asin(math.sin(p1) * math.cos(d) + math.cos(p1) * math.sin(d) * math.cos(br))
    l2 = l1 + math.atan2(
        math.sin(br) * math.sin(d) * math.cos(p1),
        math.cos(d) - math.sin(p1) * math.sin(p2),
    )
    return math.degrees(p2), (math.degrees(l2) + 540.0) % 360.0 - 180.0


class LocalPlane:
    """
    Flat-earth projection around a reference point.

    Converts lat/lon <-> local metres (x = east, y = north). Error is well
    under a metre across a few km, which is far better than our simulated
    GPS needs, and it lets us do plain 2-D vector maths for the
    point-to-polyline projection.
    """

    def __init__(self, ref_lat, ref_lon):
        self.ref_lat = ref_lat
        self.ref_lon = ref_lon
        self._mx = EARTH_RADIUS_M * math.cos(math.radians(ref_lat))

    def to_xy(self, lat, lon):
        x = math.radians(lon - self.ref_lon) * self._mx
        y = math.radians(lat - self.ref_lat) * EARTH_RADIUS_M
        return x, y

    def to_latlon(self, x, y):
        lat = self.ref_lat + math.degrees(y / EARTH_RADIUS_M)
        lon = self.ref_lon + math.degrees(x / self._mx)
        return lat, lon


def project_point_on_segment(px, py, ax, ay, bx, by):
    """
    Project P onto segment AB.

    Returns (t, qx, qy, perp_dist, side) where:
      t         - 0..1 position along AB of the closest point (clamped)
      qx, qy    - the closest point itself
      perp_dist - distance from P to that closest point, metres
      side      - +1 if P is left of A->B, -1 if right, 0 if collinear
    """
    abx, aby = bx - ax, by - ay
    seg_len_sq = abx * abx + aby * aby
    if seg_len_sq == 0.0:
        return 0.0, ax, ay, math.hypot(px - ax, py - ay), 0
    t = ((px - ax) * abx + (py - ay) * aby) / seg_len_sq
    t = max(0.0, min(1.0, t))
    qx, qy = ax + t * abx, ay + t * aby
    cross = abx * (py - ay) - aby * (px - ax)
    side = 1 if cross > 0 else (-1 if cross < 0 else 0)
    return t, qx, qy, math.hypot(px - qx, py - qy), side
