"""
geo_route/locate.py — THE deliverable.

Takes one YOLO detection from Person 1 and returns the exact geospatial
object the integration contract requires:

    {"latitude": 12.9716, "longitude": 77.5946,
     "distance_m": 120, "ahead": true, "on_route": true}

Nothing extra in the default output — Person 5 and Person 6 can consume it
without translating anything. Pass include_debug=True to get a `_debug` key
with the working (route coordinates, match mode, cross-track distance) for
your own tuning and for the Streamlit map.

HOW A HAZARD GETS ITS COORDINATES
---------------------------------
Mode A "planted" (default, used for the demo):
    match the detection to a known hazard in the ground-truth map that lies
    just ahead of the vehicle. Deterministic, so the golden demo produces
    the same numbers every run and distance counts down smoothly as the
    vehicle approaches. This is the honest version of "simulated GPS".

Mode B "projected" (automatic fallback):
    if no planted hazard matches, estimate range from the bounding box using
    a crude flat-road pinhole model and project that from the vehicle's
    position along its heading. This is NOT real camera-to-GPS projection
    (explicitly out of scope) — it just guarantees the pipeline never returns
    null on an unexpected detection mid-demo.
"""

import math
from datetime import datetime, timezone

try:
    from .config import (AHEAD_TOLERANCE_M, CAMERA_HEIGHT_M, FOCAL_LENGTH_PX,
                         FRAME_WIDTH_PX, HORIZON_Y_PX, MATCH_WINDOW_BACK_M,
                         MATCH_WINDOW_FWD_M, MAX_RANGE_M, MIN_RANGE_M,
                         ROUTE_CORRIDOR_M, ROUTE_WAYPOINTS, VIDEO_START_UTC)
    from .geo_utils import angle_diff_deg, bearing_deg, destination_point, haversine_m
    from .gps_sim import VehicleSimulator
    from .hazards import build_hazard_map, normalise_type
    from .route import Route
except ImportError:
    from config import (AHEAD_TOLERANCE_M, CAMERA_HEIGHT_M, FOCAL_LENGTH_PX,
                        FRAME_WIDTH_PX, HORIZON_Y_PX, MATCH_WINDOW_BACK_M,
                        MATCH_WINDOW_FWD_M, MAX_RANGE_M, MIN_RANGE_M,
                        ROUTE_CORRIDOR_M, ROUTE_WAYPOINTS, VIDEO_START_UTC)
    from geo_utils import angle_diff_deg, bearing_deg, destination_point, haversine_m
    from gps_sim import VehicleSimulator
    from hazards import build_hazard_map, normalise_type
    from route import Route


# ---------------------------------------------------------------------------
# Input normalisation — be liberal in what we accept
# ---------------------------------------------------------------------------
def parse_bbox(bbox):
    """Accept [x1,y1,x2,y2] or {"x1":..,"y1":..,"x2":..,"y2":..}."""
    if bbox is None:
        return None
    if isinstance(bbox, dict):
        return (float(bbox["x1"]), float(bbox["y1"]),
                float(bbox["x2"]), float(bbox["y2"]))
    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        return tuple(float(v) for v in bbox)
    raise ValueError(f"Unrecognised bbox format: {bbox!r}")


def resolve_t_ms(detection, video_start_utc=VIDEO_START_UTC):
    """
    Get milliseconds-since-video-start from a detection.

    Person 1's real output uses `timestamp_ms`. The written contract in the
    assignment PDF says `frame_timestamp` (ISO 8601). Both are handled here
    so a rename upstream cannot break the pipeline mid-sprint.
    """
    if "timestamp_ms" in detection and detection["timestamp_ms"] is not None:
        return int(detection["timestamp_ms"])
    iso = detection.get("frame_timestamp")
    if iso:
        start = datetime.fromisoformat(video_start_utc.replace("Z", "+00:00"))
        t = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return int((t - start).total_seconds() * 1000)
    raise KeyError("Detection has neither 'timestamp_ms' nor 'frame_timestamp'")


# ---------------------------------------------------------------------------
# Mode B helper: bbox -> rough range and lateral offset
# ---------------------------------------------------------------------------
def estimate_range_from_bbox(bbox):
    """
    Crude flat-road range estimate: an object's bottom edge sits lower in the
    frame the closer it is.  range ~= f * camera_height / (y_bottom - horizon)

    Returns (range_m, lateral_m) where lateral is +right of the camera axis.
    """
    x1, _y1, x2, y2 = bbox
    dy = max(y2 - HORIZON_Y_PX, 1.0)
    rng = (FOCAL_LENGTH_PX * CAMERA_HEIGHT_M) / dy
    rng = max(MIN_RANGE_M, min(rng, MAX_RANGE_M))
    x_centre = (x1 + x2) / 2.0
    lateral = (x_centre - FRAME_WIDTH_PX / 2.0) * rng / FOCAL_LENGTH_PX
    return rng, lateral


# ---------------------------------------------------------------------------
# The locator
# ---------------------------------------------------------------------------
class GeoLocator:
    def __init__(self, route=None, simulator=None, hazard_map=None):
        self.route = route or Route(ROUTE_WAYPOINTS)
        self.simulator = simulator or VehicleSimulator(self.route)
        self.hazard_map = hazard_map if hazard_map is not None else build_hazard_map(self.route)

    # -- hazard position, mode A ------------------------------------------
    def _match_planted(self, detection, vehicle):
        wanted = normalise_type(detection.get("hazard_type"))
        best, best_delta = None, None
        for hz in self.hazard_map:
            delta = hz["s_m"] - vehicle.s_m
            if not (-MATCH_WINDOW_BACK_M <= delta <= MATCH_WINDOW_FWD_M):
                continue
            same_type = normalise_type(hz["hazard_type"]) == wanted
            # prefer a type match; fall back to any hazard in the window
            score = (0 if same_type else 1, abs(delta))
            if best is None or score < best_delta:
                best, best_delta = hz, score
        return best

    # -- hazard position, mode B ------------------------------------------
    def _project_from_bbox(self, detection, vehicle):
        bbox = parse_bbox(detection.get("bbox"))
        if bbox is None:
            return None, None
        rng, lateral = estimate_range_from_bbox(bbox)
        offset_deg = math.degrees(math.atan2(lateral, rng))
        brg = (vehicle.heading_deg + offset_deg) % 360.0
        lat, lon = destination_point(vehicle.latitude, vehicle.longitude,
                                     brg, math.hypot(rng, lateral))
        return (lat, lon), rng

    # -- main entry point --------------------------------------------------
    def locate(self, detection, include_debug=False):
        """detection (dict) -> geospatial contract dict."""
        t_ms = resolve_t_ms(detection)
        vehicle = self.simulator.state_at_ms(t_ms)

        planted = self._match_planted(detection, vehicle)
        if planted is not None:
            lat, lon = planted["latitude"], planted["longitude"]
            mode, hazard_id = "planted", planted["hazard_id"]
        else:
            pos, _rng = self._project_from_bbox(detection, vehicle)
            if pos is None:  # nothing to work with: fall back to the vehicle
                pos = (vehicle.latitude, vehicle.longitude)
            lat, lon = pos
            mode, hazard_id = "projected", None

        rp = self.route.project(lat, lon)

        # on_route: inside the corridor around the planned polyline, and not
        # past the destination. "Nearby" is not enough.
        on_route = (rp.cross_track_m <= ROUTE_CORRIDOR_M) and (rp.s_m <= self.route.length_m)

        # ahead / distance: use along-route geometry when the hazard is on the
        # route (that is the distance the driver will actually travel), and
        # straight-line + bearing when it is not.
        along_delta = rp.s_m - vehicle.s_m
        if on_route:
            ahead = along_delta > -AHEAD_TOLERANCE_M
            distance = abs(along_delta)
        else:
            brg = bearing_deg(vehicle.latitude, vehicle.longitude, lat, lon)
            ahead = abs(angle_diff_deg(brg, vehicle.heading_deg)) <= 90.0
            distance = haversine_m(vehicle.latitude, vehicle.longitude, lat, lon)

        out = {
            "latitude": round(lat, 7),
            "longitude": round(lon, 7),
            "distance_m": int(round(distance)),
            "ahead": bool(ahead),
            "on_route": bool(on_route),
        }

        if include_debug:
            out["_debug"] = {
                "mode": mode,
                "hazard_id": hazard_id,
                "t_ms": t_ms,
                "hazard_type": detection.get("hazard_type"),
                "confidence": detection.get("confidence"),
                "vehicle": vehicle.as_dict(),
                "hazard_s_m": round(rp.s_m, 2),
                "cross_track_m": round(rp.cross_track_m, 2),
                "along_delta_m": round(along_delta, 2),
                "corridor_m": ROUTE_CORRIDOR_M,
            }
        return out

    def locate_many(self, detections, include_debug=False):
        return [self.locate(d, include_debug=include_debug) for d in detections]


# Convenience singleton so other people can just do:
#   from geo_route.locate import locate_detection
_DEFAULT = None


def locate_detection(detection, include_debug=False):
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = GeoLocator()
    return _DEFAULT.locate(detection, include_debug=include_debug)
