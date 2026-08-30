"""
Person 5 - Risk + Warning Engine

Takes:
1. YOLO detection output
2. Geospatial output

Returns:
{
    "severity": "High",
    "warning": True,
    "level": "critical",
    "message": "Pothole ahead — 120 m"
}

This is intentionally rule-based for the 2-day MVP.
"""

# -----------------------------
# Thresholds
# -----------------------------

CONFIDENCE_THRESHOLD = 0.70

WARNING_DISTANCE_M = 150
CRITICAL_DISTANCE_M = 75


# -----------------------------
# Severity calculation
# -----------------------------

def derive_severity(confidence, bbox):
    """
    Estimate hazard severity using:
    - YOLO confidence
    - Bounding-box size

    bbox format:
    {
        "x1": ...,
        "y1": ...,
        "x2": ...,
        "y2": ...
    }
    """

    x1 = bbox["x1"]
    y1 = bbox["y1"]
    x2 = bbox["x2"]
    y2 = bbox["y2"]

    width = max(0, x2 - x1)
    height = max(0, y2 - y1)

    box_area = width * height

    # Simple MVP thresholds.
    # These can be tuned after testing on real video.

    if confidence >= 0.85 and box_area >= 5000:
        return "High"

    elif confidence >= 0.70 and box_area >= 2000:
        return "Medium"

    else:
        return "Low"


# -----------------------------
# Main risk engine
# -----------------------------

def evaluate_risk(yolo_output, geo_output):
    """
    Combine YOLO and geospatial information.

    YOLO input:
    {
        "hazard_type": "pothole",
        "confidence": 0.92,
        "bbox": {
            "x1": 120,
            "y1": 340,
            "x2": 210,
            "y2": 400
        },
        "frame_timestamp": "2026-08-25T10:15:32.500Z"
    }

    Geospatial input:
    {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "distance_m": 120,
        "ahead": True,
        "on_route": True
    }
    """

    # Get YOLO information
    hazard_type = yolo_output["hazard_type"]
    confidence = float(yolo_output["confidence"])
    bbox = yolo_output["bbox"]

    # Get geospatial information
    distance_m = float(geo_output["distance_m"])
    ahead = bool(geo_output["ahead"])
    on_route = bool(geo_output["on_route"])

    # Calculate severity
    severity = derive_severity(
        confidence,
        bbox
    )

    # -----------------------------
    # Warning decision
    # -----------------------------

    warning = False
    level = "info"

    # Hazard must satisfy all three conditions:
    #
    # 1. Confidence >= 70%
    # 2. Hazard is ahead
    # 3. Hazard is on the driver's route

    relevant_hazard = (
        confidence >= CONFIDENCE_THRESHOLD
        and ahead
        and on_route
    )

    if relevant_hazard:

        # Very close hazard
        if distance_m <= CRITICAL_DISTANCE_M:
            warning = True
            level = "critical"

        # Hazard within warning range
        elif distance_m <= WARNING_DISTANCE_M:
            warning = True

            if severity == "High":
                level = "critical"
            else:
                level = "warning"

    # -----------------------------
    # Warning message
    # -----------------------------

    hazard_name = hazard_type.replace("_", " ").capitalize()

    if ahead:
        message = f"{hazard_name} ahead — {round(distance_m)} m"
    else:
        message = f"{hazard_name} detected"

    # -----------------------------
    # Required output contract
    # -----------------------------

    return {
        "severity": severity,
        "warning": warning,
        "level": level,
        "message": message
    }


# -----------------------------
# Quick manual test
# -----------------------------

if __name__ == "__main__":

    yolo_output = {
        "hazard_type": "pothole",
        "confidence": 0.92,
        "bbox": {
            "x1": 120,
            "y1": 340,
            "x2": 210,
            "y2": 400
        },
        "frame_timestamp": "2026-08-25T10:15:32.500Z"
    }

    geo_output = {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "distance_m": 120,
        "ahead": True,
        "on_route": True
    }

    result = evaluate_risk(
        yolo_output,
        geo_output
    )

    print(result)