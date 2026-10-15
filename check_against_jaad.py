import os
import xml.etree.ElementTree as ET
import pandas as pd

ANNOTATIONS_FOLDER = "jaad_annotations"
RESULTS_FOLDER = "results"
CHECK_CLIPS = ["video_0001", "video_0002"]  # pick 3 of your clips once they are all run
IOU_MIN = 0.5  # how much two boxes must overlap to count as the same person
SMALL_BOX = 100  # boxes shorter than this many pixels count as "small" (far away)


def iou(box_a, box_b):
    # overlap area divided by the total area covered by the two boxes
    left = max(box_a[0], box_b[0])
    top = max(box_a[1], box_b[1])
    right = min(box_a[2], box_b[2])
    bottom = min(box_a[3], box_b[3])
    if right <= left or bottom <= top:
        return 0
    overlap = (right - left) * (bottom - top)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    return overlap / (area_a + area_b - overlap)


detections = pd.read_csv(os.path.join(RESULTS_FOLDER, "detections.csv"))
people = detections[detections["class"] == "person"]

check_rows = []
for clip_name in CHECK_CLIPS:
    xml_path = os.path.join(ANNOTATIONS_FOLDER, clip_name + ".xml")
    if not os.path.exists(xml_path):
        print("no annotation file for", clip_name, "so skipping it")
        continue

    # JAAD boxes, grouped by frame number
    jaad_boxes = {}
    root = ET.parse(xml_path).getroot()
    for track in root.findall("track"):
        # "people" tracks are groups, so only single pedestrians are used
        if track.get("label") not in ["pedestrian", "ped"]:
            continue
        for box in track.findall("box"):
            if box.get("outside") == "1":
                continue
            occlusion = "none"
            for attribute in box.findall("attribute"):
                if attribute.get("name") == "occlusion":
                    occlusion = attribute.text
            # a fully hidden person cannot be detected by anyone, so skip them
            if occlusion == "full":
                continue
            frame_num = int(box.get("frame"))
            coords = [float(box.get("xtl")), float(box.get("ytl")), float(box.get("xbr")), float(box.get("ybr"))]
            if frame_num not in jaad_boxes:
                jaad_boxes[frame_num] = []
            jaad_boxes[frame_num].append(coords)

    clip_people = people[people["clip"] == clip_name]
    total = 0
    found = 0
    missed_small = 0
    missed_large = 0

    for frame_num in jaad_boxes:
        frame_yolo = clip_people[clip_people["frame"] == frame_num]
        yolo_boxes = []
        for j in range(len(frame_yolo)):
            row = frame_yolo.iloc[j]
            yolo_boxes.append([row["x1"], row["y1"], row["x2"], row["y2"]])

        used = []
        for jaad_box in jaad_boxes[frame_num]:
            total = total + 1
            best_score = 0
            best_index = -1
            for k in range(len(yolo_boxes)):
                if k in used:
                    continue
                score = iou(jaad_box, yolo_boxes[k])
                if score > best_score:
                    best_score = score
                    best_index = k

            if best_score >= IOU_MIN:
                found = found + 1
                used.append(best_index)
            elif jaad_box[3] - jaad_box[1] < SMALL_BOX:
                missed_small = missed_small + 1
            else:
                missed_large = missed_large + 1

    missed = missed_small + missed_large
    missed_percent = round(100 * missed / total, 1)
    check_rows.append([clip_name, total, found, missed, missed_percent, missed_small, missed_large])
    print(clip_name, "-", total, "JAAD pedestrian boxes,", found, "found by YOLO,", missed, "missed")

check = pd.DataFrame(check_rows, columns=["clip", "jaad_boxes", "found", "missed", "missed_percent",
                                          "missed_small", "missed_large"])
check.to_csv(os.path.join(RESULTS_FOLDER, "jaad_check.csv"), index=False)
print("saved results/jaad_check.csv")
