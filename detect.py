import os
import cv2
import pandas as pd
from ultralytics import YOLO

CLIPS_FOLDER = "videos"
RESULTS_FOLDER = "results"
MODEL_FILE = "yolov8n.pt"
CONF_MIN = 0.4
MAX_CLIPS = 0  # 2 clips for a first test, set to 0 to run on every clip

# COCO class numbers for the classes we keep
KEEP_CLASSES = {0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

os.makedirs(RESULTS_FOLDER, exist_ok=True)

# the first time this runs, ultralytics downloads yolov8n.pt (about 6 MB)
model = YOLO(MODEL_FILE)

clip_files = []
for file_name in sorted(os.listdir(CLIPS_FOLDER)):
    if file_name.endswith(".mp4"):
        clip_files.append(file_name)

if MAX_CLIPS > 0:
    clip_files = clip_files[:MAX_CLIPS]

print("found", len(clip_files), "clips")

detection_rows = []
clip_rows = []

for file_name in clip_files:
    clip_name = file_name.replace(".mp4", "")
    cap = cv2.VideoCapture(os.path.join(CLIPS_FOLDER, file_name))
    if not cap.isOpened():
        print("could not open", file_name, "so skipping it")
        continue

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    frame_num = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        results = model(frame, verbose=False)
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            conf = float(box.conf[0])
            if class_id not in KEEP_CLASSES:
                continue
            if conf < CONF_MIN:
                continue

            # box corners in pixels: (x1, y1) is top left, (x2, y2) is bottom right
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            row = [clip_name, frame_num, KEEP_CLASSES[class_id], round(conf, 3),
                   round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)]
            detection_rows.append(row)

        frame_num = frame_num + 1
        if frame_num % 100 == 0:
            print("   ", clip_name, "frame", frame_num)

    cap.release()
    # analyze.py needs fps for seconds and width/height for the danger zone
    clip_rows.append([clip_name, frame_num, fps, width, height])
    print("done", clip_name, frame_num, "frames")

det_df = pd.DataFrame(detection_rows, columns=["clip", "frame", "class", "conf", "x1", "y1", "x2", "y2"])
det_df.to_csv(os.path.join(RESULTS_FOLDER, "detections.csv"), index=False)

clips_df = pd.DataFrame(clip_rows, columns=["clip", "frames", "fps", "width", "height"])
clips_df.to_csv(os.path.join(RESULTS_FOLDER, "clips.csv"), index=False)

print("saved", len(detection_rows), "detections to results/detections.csv")
print("saved info for", len(clip_rows), "clips to results/clips.csv")
