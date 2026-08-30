# Dataset Testing Plan

## Goal

Test Person 1's YOLO pothole detector on unseen road images and a real road video.

## Test Images

- 10–15 images containing potholes
- 10 images without potholes
- Images should be different from the training images where possible.

## Test Categories

### Correct detection
A real pothole is present and YOLO detects it.

### Missed detection
A real pothole is present but YOLO does not detect it.

### False positive
No pothole is present but YOLO detects one.

### Correct rejection
No pothole is present and YOLO does not detect one.

## Confidence thresholds

Test:

- 0.30
- 0.40
- 0.50
- 0.60
- 0.70

## Final deliverable

Recommend one confidence threshold based on the balance between:

- detecting real potholes
- minimizing false positives
- minimizing missed potholes