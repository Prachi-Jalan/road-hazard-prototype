# road-hazard-prototype

Smart India Hackathon 2026 — Smart Road Hazard Detection & Warning prototype, 6-person team.

```
ROAD VIDEO → YOLO → LOCATION → ROUTE MATCHING → DISTANCE → RISK ENGINE → WARNING → STREAMLIT
   Person 1   Person 1  Person 3    Person 3      Person 3    Person 5    Person 5  Person 6
```

Demo target: `"POTHOLE AHEAD — 120 m | Severity: High | Confidence: 92%"`

## Folder structure
```
/yolo_detection      <- Person 1: video -> YOLO -> hazard JSON
/dataset_testing     <- Person 2
/geo_route           <- Person 3: GPS + route matching + distance
/backend_api         <- Person 4
/risk_engine         <- Person 5
/frontend_ui         <- Person 6: Streamlit
/shared              <- shared schemas + sample data everyone can build against now
```

## Start here
- `shared/schema.md` — the JSON contract Person 1 produces and everyone downstream consumes
- `shared/sample_detections.json` — real model output on sample images, use this to
  start building your piece today without waiting on video pipeline to be finished
- each person's folder has its own README with setup instructions for that piece

## Git workflow
- `main` stays demo-able at all times
- work on your own branch: `git checkout -b yourname-feature`
- push, open a PR into `main`, quick look before merging
- small commits, merge often — 2 day sprint, don't let branches sit
