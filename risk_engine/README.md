# Risk + Warning Engine

## Purpose

This module combines YOLO hazard detections with geospatial information to decide whether the driver should receive a warning.

The engine is intentionally rule-based for the Smart India Hackathon prototype.

## Inputs

### YOLO detection

```json
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

Geospatial data

{
  "latitude": 12.9716,
  "longitude": 77.5946,
  "distance_m": 120,
  "ahead": true,
  "on_route": true
}

Risk Rules
YOLO confidence must be at least 0.70.
The hazard must be ahead of the vehicle.
The hazard must be on the driver's route.
Hazards within 150 m can trigger a warning.
Hazards within 75 m are treated as critical.
Severity is derived from detection confidence and bounding-box size.


Output

The engine returns:
{
  "severity": "High",
  "warning": true,
  "level": "critical",
  "message": "Pothole ahead — 120 m"
}

Testing

Run:

python3 risk_engine/test_risk_engine.py

The test suite checks:

Normal warning
Critical-distance warning
Hazard too far away
Hazard behind the vehicle
Hazard off the route
Low-confidence detection

All tests should pass before integration.

Integration

The risk engine receives:

YOLO detection + Geospatial output

and produces:

Risk/Warning output

for the backend and frontend components.
