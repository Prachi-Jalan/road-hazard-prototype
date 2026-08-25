"""
Generate real (not fake) sample detections from a handful of images.
Use this to give teammates real model output before video pipeline is ready.

Usage:
    python generate_image_samples.py --images dataset/valid/images --model models/pothole.pt --out ../shared/sample_detections.json --n 15
"""

import argparse
import glob
import json
import os

from ultralytics import YOLO


def compute_severity(bbox, img_width, img_height):
    x1, y1, x2, y2 = bbox
    box_area = (x2 - x1) * (y2 - y1)
    frame_area = img_width * img_height
    ratio = box_area / frame_area

    if ratio < 0.01:
        return "low"
    elif ratio < 0.05:
        return "medium"
    else:
        return "high"


def run(images_dir, model_path, out_path, conf_threshold, n):
    model = YOLO(model_path)

    image_paths = sorted(glob.glob(os.path.join(images_dir, "*.jpg")))[:n]
    if not image_paths:
        raise RuntimeError(f"No .jpg images found in {images_dir}")

    detections = []
    for i, img_path in enumerate(image_paths):
        results = model(img_path, conf=conf_threshold, verbose=False)[0]
        img_height, img_width = results.orig_shape

        for box in results.boxes:
            cls_id = int(box.cls[0])
            class_name = model.names[cls_id]
            confidence = float(box.conf[0])
            bbox = [round(v, 1) for v in box.xyxy[0].tolist()]

            detections.append({
                "hazard_type": class_name,
                "confidence": round(confidence, 3),
                "severity": compute_severity(bbox, img_width, img_height),
                "frame": i,
                "timestamp_ms": i * 1000,  # placeholder spacing since these are separate images, not real video
                "bbox": bbox,
                "source_image": os.path.basename(img_path),
            })

    with open(out_path, "w") as f:
        json.dump(detections, f, indent=2)

    print(f"Ran on {len(image_paths)} images, found {len(detections)} real detections.")
    print(f"Written to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", required=True, help="Folder of .jpg images")
    parser.add_argument("--model", required=True, help="Path to trained .pt model")
    parser.add_argument("--out", default="detections_from_images.json")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--n", type=int, default=15, help="How many images to run on")
    args = parser.parse_args()

    run(args.images, args.model, args.out, args.conf, args.n)
