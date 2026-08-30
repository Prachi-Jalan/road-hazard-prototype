from risk_engine import evaluate_risk


# -----------------------------
# Shared test YOLO detection
# -----------------------------

def make_yolo(confidence=0.92):
    return {
        "hazard_type": "pothole",
        "confidence": confidence,
        "bbox": {
            "x1": 120,
            "y1": 340,
            "x2": 210,
            "y2": 400
        },
        "frame_timestamp": "2026-08-25T10:15:32.500Z"
    }


# -----------------------------
# Shared test geospatial data
# -----------------------------

def make_geo(distance=120, ahead=True, on_route=True):
    return {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "distance_m": distance,
        "ahead": ahead,
        "on_route": on_route
    }


# -----------------------------
# Test 1
# Hazard is ahead and on route
# -----------------------------

def test_normal_warning():

    result = evaluate_risk(
        make_yolo(),
        make_geo(distance=120)
    )

    assert result["warning"] is True
    assert result["level"] == "critical"
    assert result["severity"] == "High"

    print("TEST 1 PASSED")


# -----------------------------
# Test 2
# Hazard is very close
# -----------------------------

def test_critical_distance():

    result = evaluate_risk(
        make_yolo(),
        make_geo(distance=50)
    )

    assert result["warning"] is True
    assert result["level"] == "critical"

    print("TEST 2 PASSED")


# -----------------------------
# Test 3
# Hazard is too far away
# -----------------------------

def test_hazard_too_far():

    result = evaluate_risk(
        make_yolo(),
        make_geo(distance=200)
    )

    assert result["warning"] is False
    assert result["level"] == "info"

    print("TEST 3 PASSED")


# -----------------------------
# Test 4
# Hazard is behind the vehicle
# -----------------------------

def test_hazard_behind_vehicle():

    result = evaluate_risk(
        make_yolo(),
        make_geo(
            distance=50,
            ahead=False
        )
    )

    assert result["warning"] is False
    assert result["level"] == "info"

    print("TEST 4 PASSED")


# -----------------------------
# Test 5
# Hazard is not on route
# -----------------------------

def test_hazard_off_route():

    result = evaluate_risk(
        make_yolo(),
        make_geo(
            distance=50,
            on_route=False
        )
    )

    assert result["warning"] is False
    assert result["level"] == "info"

    print("TEST 5 PASSED")


# -----------------------------
# Test 6
# Confidence is too low
# -----------------------------

def test_low_confidence():

    result = evaluate_risk(
        make_yolo(confidence=0.50),
        make_geo(distance=50)
    )

    assert result["warning"] is False
    assert result["level"] == "info"

    print("TEST 6 PASSED")


# -----------------------------
# Run all tests
# -----------------------------

if __name__ == "__main__":

    test_normal_warning()
    test_critical_distance()
    test_hazard_too_far()
    test_hazard_behind_vehicle()
    test_hazard_off_route()
    test_low_confidence()

    print("\nALL TESTS PASSED!")