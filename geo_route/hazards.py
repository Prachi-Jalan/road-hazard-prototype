"""
geo_route/hazards.py — the simulated ground-truth hazard map.

Hazards are authored in ROUTE coordinates (metres along the route + lateral
offset) and converted to lat/lon at load time. Two reasons:

1. An "on route" hazard is then guaranteed to be genuinely on the polyline —
   no fiddling with decimal places until the demo looks right.
2. You can move a hazard for the golden demo by editing one number
   (`s_m` in config.py) instead of hunting for a plausible lat/lon.
"""

try:
    from .config import PLANTED_HAZARDS
    from .route import Route
except ImportError:
    from config import PLANTED_HAZARDS
    from route import Route


def build_hazard_map(route: Route, specs=PLANTED_HAZARDS):
    """Expand the config specs into full hazard records with lat/lon."""
    hazards = []
    for spec in specs:
        lat, lon = route.offset_point(spec["s_m"], spec["offset_m"])
        rp = route.project(lat, lon)
        hazards.append({
            "hazard_id": spec["hazard_id"],
            "hazard_type": spec["hazard_type"],
            "latitude": round(lat, 7),
            "longitude": round(lon, 7),
            "s_m": round(rp.s_m, 2),
            "cross_track_m": round(rp.cross_track_m, 2),
        })
    return hazards


def normalise_type(hazard_type):
    """
    Loose type matching between YOLO class names and the hazard map.

    Person 1's model has 3 classes (pothole / longitudinal crack /
    crocodile crack) and the crack classes are barely trained yet, so we
    match on a coarse family rather than the exact string.
    """
    t = (hazard_type or "").strip().lower()
    if "pothole" in t:
        return "pothole"
    if "crack" in t:
        return "crack"
    return t or "unknown"
