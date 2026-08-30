"""
geo_route/test_geo.py — plain-assert sanity tests. Run: python test_geo.py

No pytest needed. These are the four things that must not break:
  1. output is EXACTLY the five contract fields, right types
  2. distance_m shrinks as the vehicle approaches
  3. ahead flips to false after the vehicle passes the hazard
  4. on_route is false for the 45 m off-route hazard (H3)
"""

try:
    from .config import PLANTED_HAZARDS, VEHICLE_SPEED_KMPH
    from .locate import GeoLocator
except ImportError:
    from config import PLANTED_HAZARDS, VEHICLE_SPEED_KMPH

    from locate import GeoLocator

SPEED_MPS = VEHICLE_SPEED_KMPH / 3.6
CONTRACT_KEYS = {"latitude", "longitude", "distance_m", "ahead", "on_route"}


def det_at(vehicle_s, hazard_type="pothole"):
    """A detection emitted when the vehicle is `vehicle_s` metres along the route."""
    return {
        "hazard_type": hazard_type,
        "confidence": 0.92,
        "severity": "high",
        "frame": 1,
        "timestamp_ms": int(vehicle_s / SPEED_MPS * 1000),
        "bbox": [600.0, 360.0, 690.0, 420.0],
    }


def hz(hid):
    return next(h for h in PLANTED_HAZARDS if h["hazard_id"] == hid)


def main():
    loc = GeoLocator()

    # 1. contract shape -----------------------------------------------------
    out = loc.locate(det_at(150))
    assert set(out) == CONTRACT_KEYS, f"extra/missing keys: {set(out) ^ CONTRACT_KEYS}"
    assert isinstance(out["latitude"], float) and isinstance(out["longitude"], float)
    assert isinstance(out["distance_m"], int)
    assert isinstance(out["ahead"], bool) and isinstance(out["on_route"], bool)
    print("PASS  output matches the integration contract exactly:", out)

    # 2. distance decreases on approach ------------------------------------
    h1 = hz("H1")["s_m"]
    dists = [loc.locate(det_at(h1 - g))["distance_m"] for g in (200, 150, 100, 50)]
    assert dists == sorted(dists, reverse=True), dists
    assert dists[0] == 200 and dists[-1] == 50, dists
    print("PASS  distance_m counts down on approach:", dists)

    # 3. ahead flips after passing -----------------------------------------
    before = loc.locate(det_at(h1 - 50))
    after = loc.locate(det_at(h1 + 15))
    assert before["ahead"] is True and after["ahead"] is False
    print(f"PASS  ahead True at 50 m before, False at 15 m past")

    # 4. off-route hazard is rejected --------------------------------------
    h3 = hz("H3")["s_m"]
    off = loc.locate(det_at(h3 - 100), include_debug=True)
    assert off["_debug"]["hazard_id"] == "H3", off["_debug"]["hazard_id"]
    assert off["on_route"] is False, "H3 is 45 m off the route, must not be on_route"
    assert off["ahead"] is True, "H3 is still in front of the vehicle"
    print(f"PASS  H3 (45 m off route): on_route=False, ahead=True, "
          f"cross_track={off['_debug']['cross_track_m']} m")

    # 5. a hazard on the route is accepted ---------------------------------
    on = loc.locate(det_at(hz("H4")["s_m"] - 120), include_debug=True)
    assert on["on_route"] is True and on["distance_m"] == 120
    print(f"PASS  H4 (0.5 m off centreline): on_route=True, distance_m=120")

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
