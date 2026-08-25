from ultralytics import YOLO
from pathlib import Path
import csv

MODEL_PATH = "yolo_detection/models/pothole.pt"
IMAGE_DIR = Path("dataset_testing/test_images")
OUTPUT_FILE = "dataset_testing/evaluation_log.csv"

THRESHOLDS = [0.30, 0.40, 0.50, 0.60, 0.70]

model = YOLO(MODEL_PATH)

rows = []

for image_path in sorted(IMAGE_DIR.iterdir()):

    if image_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
        continue

    actual = "pothole" if image_path.name.startswith("pothole_") else "no_pothole"

    for threshold in THRESHOLDS:

        results = model(
            str(image_path),
            conf=threshold,
            verbose=False
        )

        detections = []

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                confidence = float(box.conf[0])

                detections.append(
                    f"{class_name}:{confidence:.3f}"
                )

        detected = len(detections) > 0

        rows.append({
            "image": image_path.name,
            "actual": actual,
            "threshold": threshold,
            "detected": detected,
            "detections": "; ".join(detections)
        })

with open(OUTPUT_FILE, "w", newline="") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "image",
            "actual",
            "threshold",
            "detected",
            "detections"
        ]
    )

    writer.writeheader()
    writer.writerows(rows)

print(f"\nTesting complete.")
print(f"Results saved to: {OUTPUT_FILE}")
print(f"Total test cases: {len(rows)}")