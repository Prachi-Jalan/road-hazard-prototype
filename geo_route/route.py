"""
geo_route/route.py — the planned route as a polyline you can measure against.

Core idea for the whole module: instead of comparing raw lat/lon pairs, every
point (vehicle and hazard) gets projected onto the route and described by two
numbers:

    s  = how far ALONG the route it is, in metres from the start
    d  = how far OFF the route it is (cross-track distance), in metres

Once you have (s, d), the three contract fields fall out almost for free:

    on_route     ->  d <= ROUTE_CORRIDOR_M
    ahead        ->  s_hazard > s_vehicle
    distance_m   ->  s_hazard - s_vehicle   (along the road you'll actually drive)
"""

from dataclasses import dataclass

try:  # works both as a package (`from geo_route.route import ...`) and standalone
    from .geo_utils import LocalPlane, haversine_m, project_point_on_segment
except ImportError:
    from geo_utils import LocalPlane, haversine_m, project_point_on_segment


@dataclass
class RoutePoint:
    """A lat/lon expressed in route coordinates."""
    s_m: float           # distance along the route from the start
    cross_track_m: float # perpendicular distance from the centreline
    side: int            # +1 left of travel direction, -1 right
    snapped_lat: float   # nearest point ON the route
    snapped_lon: float
    seg_index: int


class Route:
    def __init__(self, waypoints):
        if len(waypoints) < 2:
            raise ValueError("A route needs at least 2 waypoints")
        self.waypoints = list(waypoints)
        self.plane = LocalPlane(waypoints[0][0], waypoints[0][1])
        self.xy = [self.plane.to_xy(lat, lon) for lat, lon in self.waypoints]

        # cumulative arc length at each waypoint
        self.cum_s = [0.0]
        for i in range(1, len(self.waypoints)):
            step = haversine_m(*self.waypoints[i - 1], *self.waypoints[i])
            self.cum_s.append(self.cum_s[-1] + step)

    @property
    def length_m(self):
        return self.cum_s[-1]

    # -- lat/lon -> route coordinates ---------------------------------------
    def project(self, lat, lon):
        """Find where (lat, lon) sits relative to the route."""
        px, py = self.plane.to_xy(lat, lon)
        best = None
        for i in range(len(self.xy) - 1):
            ax, ay = self.xy[i]
            bx, by = self.xy[i + 1]
            t, qx, qy, perp, side = project_point_on_segment(px, py, ax, ay, bx, by)
            if best is None or perp < best[3]:
                seg_len = self.cum_s[i + 1] - self.cum_s[i]
                best = (i, t, (qx, qy), perp, side, self.cum_s[i] + t * seg_len)
        seg_index, _t, (qx, qy), perp, side, s = best
        slat, slon = self.plane.to_latlon(qx, qy)
        return RoutePoint(
            s_m=s,
            cross_track_m=perp,
            side=side,
            snapped_lat=slat,
            snapped_lon=slon,
            seg_index=seg_index,
        )

    # -- route coordinates -> lat/lon ---------------------------------------
    def position_at_s(self, s_m):
        """(lat, lon, heading_deg) at `s_m` metres along the route."""
        s = max(0.0, min(float(s_m), self.length_m))
        i = 0
        while i < len(self.cum_s) - 2 and self.cum_s[i + 1] < s:
            i += 1
        seg_len = self.cum_s[i + 1] - self.cum_s[i]
        t = 0.0 if seg_len == 0 else (s - self.cum_s[i]) / seg_len
        ax, ay = self.xy[i]
        bx, by = self.xy[i + 1]
        lat, lon = self.plane.to_latlon(ax + t * (bx - ax), ay + t * (by - ay))
        return lat, lon, self.heading_at_segment(i)

    def heading_at_segment(self, i):
        try:
            from .geo_utils import bearing_deg
        except ImportError:
            from geo_utils import bearing_deg
        return bearing_deg(*self.waypoints[i], *self.waypoints[i + 1])

    def offset_point(self, s_m, offset_m):
        """
        Point `offset_m` to the side of the centreline at `s_m`.
        Positive offset = right of travel direction. Used to plant hazards.
        """
        try:
            from .geo_utils import destination_point
        except ImportError:
            from geo_utils import destination_point
        lat, lon, heading = self.position_at_s(s_m)
        if offset_m == 0:
            return lat, lon
        side_bearing = (heading + (90.0 if offset_m > 0 else -90.0)) % 360.0
        return destination_point(lat, lon, side_bearing, abs(offset_m))
