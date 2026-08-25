# Shared output schema — YOLO detection → rest of pipeline

This is the contract between Person 1 (yolo_detection) and everyone downstream
(Person 3 geo_route, Person 4 backend_api, Person 5 risk_engine).

Full pipeline:
```
ROAD VIDEO → YOLO → LOCATION → ROUTE MATCHING → DISTANCE → RISK ENGINE → WARNING → STREAMLIT
   Person 1        Person 3      Person 3        Person 3     Person 5              Person 6
```

## What Person 1's module outputs

A JSON list of hazard detections. See `sample_detections.json` in this folder — real
output from the trained model on sample images.

```json
{
  "hazard_type": "pothole",
  "confidence": 0.92,
  "severity": "high",
  "frame": 145,
  "timestamp_ms": 4833,
  "bbox": [120.5, 340.0, 210.2, 400.8]
}
```

| Field | Type | Meaning |
|---|---|---|
| `hazard_type` | string | one of: `"pothole"`, `"longitudinal crack"`, `"crocodile crack"` |
| `confidence` | float 0-1 | YOLO's raw detection confidence |
| `severity` | string | `"low"` / `"medium"` / `"high"` — based on how big the hazard looks in frame |
| `frame` | int | which video frame this was seen in (internal use only) |
| `timestamp_ms` | int | milliseconds into the video — **use this** to line up with GPS timestamps |
| `bbox` | [x1,y1,x2,y2] | pixel box in the source frame |

## Notes for downstream people

- No location/GPS data yet — that's Person 3's job to attach, by matching
  `timestamp_ms` against a GPS log recorded alongside the same video.
- Detections are de-duplicated across nearby frames when run on video.
- `sample_detections.json` was generated from still images, not video, so its
  `frame`/`timestamp_ms` values are placeholder-spaced (1 second apart per image) —
  don't build real timing logic against this file, just the shape/fields.
- Real video output will land at `yolo_detection/outputs/detections.json`, same shape.
