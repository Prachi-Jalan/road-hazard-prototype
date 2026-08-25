# yolo_detection — Person 1

Road video → YOLO → hazard detections + confidence + severity → standardized JSON.
See `/shared/schema.md` for the exact output contract everyone else builds against.

## Setup
```bash
cd yolo_detection
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Model
Trained a YOLOv8n model on a Roboflow pothole/crack dataset (3 classes: pothole,
longitudinal crack, crocodile crack). Weights aren't in git (too big) — ask in the
group chat for the `pothole.pt` file, put it in a local `models/` folder.

## Run on video
```bash
python detect.py --video videos/road_video.mp4 --model models/pothole.pt --out outputs/detections.json --conf 0.25
```

## Run on images (for quick real sample data)
```bash
python generate_image_samples.py --images path/to/images --model models/pothole.pt --out ../shared/sample_detections.json --n 15
```
