"""
geo_route/run_demo.py — run this to see the module work end to end.

    python run_demo.py                    # uses a generated detection stream
    python run_demo.py ../shared/detections.json   # uses Person 1's real output

The generated stream simulates what Person 1's video output will look like:
the same hazard detected in several frames as the vehicle drives towards it,
so you can watch distance_m count down and `ahead` flip to false after the
vehicle passes it.

Writes geo_route/sample_geo_output.json for Person 5 and Person 6 to build
against right now, without waiting on the video pipeline.
"""

import json
import os
import sys

try:
    from .config import PLANTED_HAZARDS, VEHICLE_SPEED_KMPH
    from .locate import GeoLocator
except ImportError:
    from config import PLANTED_HAZARDS, VEHICLE_SPEED_KMPH
    from locate import GeoLocator

HERE = os.path.dirname(os.path.abspath(__file__))


def generate_detection_stream(speed_kmph=VEHICLE_SPEED_KMPH):
    """
    Emit detections as if a dashcam saw each planted hazard from 200 m, 150 m,
    100 m, 50 m and 10 m out, plus one frame after passing it.
    """
    speed_mps = speed_kmph / 3.6
    dets = []
    for hz in PLANTED_HAZARDS:
        for i, gap in enumerate([200, 150, 100, 50, 10, -20]):
            vehicle_s = hz["s_m"] - gap
            if vehicle_s < 0:
                continue
            t_ms = int((vehicle_s / speed_mps) * 1000)
            # bbox grows as the hazard gets closer (only used by fallback mode)
            box_h = max(8, int(2400 / max(gap, 10)))
            y2 = 300 + box_h + 40
            dets.append({
                "hazard_type": hz["hazard_type"],
                "confidence": round(0.55 + 0.07 * i, 2),
                "severity": "high" if hz["hazard_type"] == "pothole" else "medium",
                "frame": int(t_ms / 33.3),
                "timestamp_ms": t_ms,
                "bbox": [600.0, float(y2 - box_h), 600.0 + box_h * 1.6, float(y2)],
            })
    dets.sort(key=lambda d: d["timestamp_ms"])
    return dets


def main():
    locator = GeoLocator()

    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = json.load(f)
        detections = data["detections"] if isinstance(data, dict) else data
        source = sys.argv[1]
    else:
        detections = generate_detection_stream()
        source = "generated stream"

    print(f"Route length: {locator.route.length_m:,.0f} m   "
          f"| speed: {VEHICLE_SPEED_KMPH:.0f} km/h | source: {source}\n")
    print("Hazard map (ground truth):")
    for hz in locator.hazard_map:
        flag = "ON  route" if hz["cross_track_m"] <= 25 else "OFF route"
        print(f"  {hz['hazard_id']}  {hz['hazard_type']:<20} "
              f"s={hz['s_m']:>7.1f} m  offset={hz['cross_track_m']:>5.1f} m  {flag}")

    print(f"\n{'t(ms)':>7} {'type':<20} {'match':<9} {'dist_m':>7} "
          f"{'ahead':>6} {'on_route':>9}  message preview")
    print("-" * 92)

    results = []
    for det in detections:
        geo = locator.locate(det, include_debug=True)
        dbg = geo.pop("_debug")
        results.append({"detection": det, "geo": geo})
        preview = (f"{det['hazard_type'].title()} ahead — {geo['distance_m']} m"
                   if geo["ahead"] and geo["on_route"] else "(no warning)")
        print(f"{dbg['t_ms']:>7} {det['hazard_type']:<20} "
              f"{(dbg['hazard_id'] or dbg['mode']):<9} {geo['distance_m']:>7} "
              f"{str(geo['ahead']):>6} {str(geo['on_route']):>9}  {preview}")

    out_path = os.path.join(HERE, "sample_geo_output.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {len(results)} records -> {out_path}")


if __name__ == "__main__":
    main()
