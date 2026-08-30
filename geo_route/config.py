"""
geo_route/config.py — all tunable constants in ONE place.

Person 3 (GPS + Route Matching). Everything here is SIMULATED on purpose:
the 2-day scope rules say simulated GPS is acceptable and expected.

If a demo value looks wrong on stage, change it HERE, not in the logic files.
"""

# ---------------------------------------------------------------------------
# 1. THE PLANNED ROUTE (A -> B)
# ---------------------------------------------------------------------------
# A fixed test route in Bengaluru. Ordered list of (latitude, longitude).
# This is the driver's planned route: "on_route" means "inside the corridor
# around this polyline", NOT just "geographically nearby".
ROUTE_WAYPOINTS = [
    (12.9716, 77.5946),   # A - start
    (12.9722, 77.5982),
    (12.9731, 77.6021),
    (12.9748, 77.6058),
    (12.9769, 77.6089),
    (12.9795, 77.6112),
    (12.9824, 77.6130),   # B - destination
]

# ---------------------------------------------------------------------------
# 2. VEHICLE SIMULATION
# ---------------------------------------------------------------------------
VEHICLE_SPEED_KMPH = 40.0     # constant speed along the route
VEHICLE_START_S_M = 0.0       # metres along route at video t=0

# Anchor that ties Person 1's video clock to the GPS clock.
# Person 1 gives timestamp_ms = milliseconds since the START of the video.
# We treat "video t=0" as "vehicle at VEHICLE_START_S_M".
# Share this string with Person 1/2 so the timestamp alignment is agreed.
VIDEO_START_UTC = "2026-08-25T10:15:00.000Z"

# ---------------------------------------------------------------------------
# 3. PLANTED (GROUND-TRUTH) HAZARDS
# ---------------------------------------------------------------------------
# Defined by distance ALONG the route (s_m) and lateral offset from the
# centreline (offset_m; positive = right of travel direction).
# Lat/lon are computed from these at load time, so "on route" hazards are
# guaranteed to sit exactly on the polyline.
#
# H3 is deliberately 45 m off the route (imagine a parallel service road)
# so you can DEMO that on_route correctly returns false for a nearby-but-
# not-on-my-route hazard. Keep it in — it is the strongest judge-facing proof
# that on_route is real logic and not hardcoded true.
PLANTED_HAZARDS = [
    {"hazard_id": "H1", "hazard_type": "pothole",         "s_m": 300.0,  "offset_m": 1.5},
    {"hazard_id": "H2", "hazard_type": "longitudinal crack", "s_m": 780.0,  "offset_m": -2.0},
    {"hazard_id": "H3", "hazard_type": "pothole",         "s_m": 900.0,  "offset_m": 45.0},
    {"hazard_id": "H4", "hazard_type": "pothole",         "s_m": 1500.0, "offset_m": 0.5},
    {"hazard_id": "H5", "hazard_type": "crocodile crack", "s_m": 2100.0, "offset_m": 2.5},
]

# ---------------------------------------------------------------------------
# 4. DECISION THRESHOLDS
# ---------------------------------------------------------------------------
ROUTE_CORRIDOR_M = 25.0       # hazard within this cross-track distance = on_route
AHEAD_TOLERANCE_M = 5.0       # small buffer so a hazard level with the bumper
                              # isn't flagged "behind" one frame early
MATCH_WINDOW_BACK_M = 20.0    # planted-hazard matching search window, behind
MATCH_WINDOW_FWD_M = 250.0    # planted-hazard matching search window, ahead

# ---------------------------------------------------------------------------
# 5. CAMERA MODEL (fallback mode only)
# ---------------------------------------------------------------------------
# Used ONLY when a detection cannot be matched to a planted hazard.
# This is a crude flat-road pinhole estimate, NOT real camera-to-GPS
# projection (explicitly out of scope). It exists so the pipeline never
# returns null and the demo never stalls on an unexpected detection.
FRAME_WIDTH_PX = 1280
FRAME_HEIGHT_PX = 720
FOCAL_LENGTH_PX = 800.0       # rough for a dashcam at 1280x720
CAMERA_HEIGHT_M = 1.4         # camera above road surface
HORIZON_Y_PX = 300.0          # image row where the road meets the horizon
MIN_RANGE_M = 5.0
MAX_RANGE_M = 300.0
