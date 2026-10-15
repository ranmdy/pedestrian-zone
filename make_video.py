import os
import cv2
import numpy as np
import pandas as pd

CLIPS_FOLDER = "videos"
RESULTS_FOLDER = "results"
CLIP_NAME = "video_0002"
SNAPSHOT_FRAME = 100  # this frame is also saved as a picture for the README

# danger zone corners as fractions of the image width and height
# keep these the same as in analyze.py
ZONE_TOP = 0.68
ZONE_BOTTOM = 0.95
ZONE_TOP_LEFT = 0.42
ZONE_TOP_RIGHT = 0.58
ZONE_BOTTOM_LEFT = 0.20
ZONE_BOTTOM_RIGHT = 0.80

# colours are in BGR order because that is what OpenCV uses
ZONE_COLOUR = (0, 255, 255)
IN_ZONE_COLOUR = (0, 0, 255)
PERSON_COLOUR = (0, 200, 0)
VEHICLE_COLOUR = (255, 128, 0)


def point_in_zone(x, y, width, height):
    top_y = ZONE_TOP * height
    bottom_y = ZONE_BOTTOM * height
    if y < top_y or y > bottom_y:
        return False
    t = (y - top_y) / (bottom_y - top_y)
    left_x = (ZONE_TOP_LEFT + t * (ZONE_BOTTOM_LEFT - ZONE_TOP_LEFT)) * width
    right_x = (ZONE_TOP_RIGHT + t * (ZONE_BOTTOM_RIGHT - ZONE_TOP_RIGHT)) * width
    return left_x <= x <= right_x


detections = pd.read_csv(os.path.join(RESULTS_FOLDER, "detections.csv"))
clip_dets = detections[detections["clip"] == CLIP_NAME]

cap = cv2.VideoCapture(os.path.join(CLIPS_FOLDER, CLIP_NAME + ".mp4"))
if not cap.isOpened():
    print("could not open", CLIP_NAME)
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# trapezoid corners in pixels, going round the shape
zone = np.array([
    [int(ZONE_BOTTOM_LEFT * width), int(ZONE_BOTTOM * height)],
    [int(ZONE_TOP_LEFT * width), int(ZONE_TOP * height)],
    [int(ZONE_TOP_RIGHT * width), int(ZONE_TOP * height)],
    [int(ZONE_BOTTOM_RIGHT * width), int(ZONE_BOTTOM * height)],
])

out_path = os.path.join(RESULTS_FOLDER, "example_" + CLIP_NAME + ".mp4")
writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

frame_num = 0
while True:
    ok, frame = cap.read()
    if not ok:
        break

    cv2.polylines(frame, [zone], True, ZONE_COLOUR, 3)

    frame_dets = clip_dets[clip_dets["frame"] == frame_num]
    for j in range(len(frame_dets)):
        row = frame_dets.iloc[j]
        x1 = int(row["x1"])
        y1 = int(row["y1"])
        x2 = int(row["x2"])
        y2 = int(row["y2"])

        if row["class"] == "person":
            feet_x = (x1 + x2) // 2
            if point_in_zone(feet_x, y2, width, height):
                colour = IN_ZONE_COLOUR
            else:
                colour = PERSON_COLOUR
            cv2.circle(frame, (feet_x, y2), 6, colour, -1)
        else:
            colour = VEHICLE_COLOUR

        cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)
        text = row["class"] + " " + str(round(row["conf"], 2))
        cv2.putText(frame, text, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, colour, 2)

    writer.write(frame)
    if frame_num == SNAPSHOT_FRAME:
        cv2.imwrite(os.path.join(RESULTS_FOLDER, "example_frame.jpg"), frame)

    frame_num = frame_num + 1

cap.release()
writer.release()
print("saved", out_path, "with", frame_num, "frames")
print("saved results/example_frame.jpg (frame", SNAPSHOT_FRAME, ")")
