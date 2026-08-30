"""
Road Hazard Detection — Person 1's module
Road video -> YOLO -> hazard detections + confidence + severity -> standardized JSON

Usage:
    python detect.py --video road_video.mp4 --model pothole.pt --out detections.json
"""

import argparse
import json

import cv2
from ultralytics import YOLO

CONF_THRESHOLD = 0.5
FRAME_SKIP = 5
IOU_DEDUP_THRESHOLD = 0.5
DEDUP_MEMORY_FRAMES = 30


def iou(box_a, box_b):
    xa1, ya1, xa2, ya2 = box_a
    xb1, yb1, xb2, yb2 = box_b

    inter_x1 = max(xa1, xb1)
    inter_y1 = max(ya1, yb1)
    inter_x2 = min(xa2, xb2)
    inter_y2 = min(ya2, yb2)

    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    if inter_area == 0:
        return 0.0

    area_a = (xa2 - xa1) * (ya2 - ya1)
    area_b = (xb2 - xb1) * (yb2 - yb1)
    return inter_area / float(area_a + area_b - inter_area)


def compute_severity(bbox, frame_width, frame_height):
    x1, y1, x2, y2 = bbox
    box_area = (x2 - x1) * (y2 - y1)
    frame_area = frame_width * frame_height
    ratio = box_area / frame_area

    if ratio < 0.01:
        return "low"
    elif ratio < 0.05:
        return "medium"
    else:
        return "high"


def run_detection(video_path, model_path, out_path, conf_threshold=CONF_THRESHOLD, frame_skip=FRAME_SKIP):
    model = YOLO(model_path)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    detections = []
    recent_boxes = {}

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_skip == 0:
            results = model(frame, conf=conf_threshold, verbose=False)[0]

            for box in results.boxes:
                cls_id = int(box.cls[0])
                class_name = model.names[cls_id]
                confidence = float(box.conf[0])
                bbox = [round(v, 1) for v in box.xyxy[0].tolist()]

                is_duplicate = False
                for prev_frame_idx, prev_bbox in recent_boxes.get(class_name, []):
                    if frame_idx - prev_frame_idx <= DEDUP_MEMORY_FRAMES and iou(bbox, prev_bbox) >= IOU_DEDUP_THRESHOLD:
                        is_duplicate = True
                        break

                if is_duplicate:
                    continue

                recent_boxes.setdefault(class_name, []).append((frame_idx, bbox))

                detections.append({
                    "hazard_type": class_name,
                    "confidence": round(confidence, 3),
                    "severity": compute_severity(bbox, frame_width, frame_height),
                    "frame": frame_idx,
                    "timestamp_ms": round((frame_idx / fps) * 1000),
                    "bbox": bbox,
                })

        frame_idx += 1

    cap.release()

    with open(out_path, "w") as f:
        json.dump(detections, f, indent=2)

    print(f"Processed {frame_idx} frames, found {len(detections)} unique hazard detections.")
    print(f"Output written to {out_path}")
    return detections


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Road hazard detection via YOLO")
    parser.add_argument("--video", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", default="detections.json")
    parser.add_argument("--conf", type=float, default=CONF_THRESHOLD)
    parser.add_argument("--skip", type=int, default=FRAME_SKIP)
    args = parser.parse_args()

    run_detection(args.video, args.model, args.out, conf_threshold=args.conf, frame_skip=args.skip)
