import os
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_FOLDER = "results"
LABELS_FILE = "my_labels.csv"
EXAMPLE_CLIP = "video_0001"  # clip used for the box height chart

# danger zone corners as fractions of the image width and height
# keep these the same as in make_video.py
ZONE_TOP = 0.68
ZONE_BOTTOM = 0.95
ZONE_TOP_LEFT = 0.42
ZONE_TOP_RIGHT = 0.58
ZONE_BOTTOM_LEFT = 0.20
ZONE_BOTTOM_RIGHT = 0.80


def point_in_zone(x, y, width, height):
    top_y = ZONE_TOP * height
    bottom_y = ZONE_BOTTOM * height
    if y < top_y or y > bottom_y:
        return False
    # 0 at the top edge of the zone, 1 at the bottom edge
    t = (y - top_y) / (bottom_y - top_y)
    # the zone gets wider further down, so the left and right edges depend on y
    left_x = (ZONE_TOP_LEFT + t * (ZONE_BOTTOM_LEFT - ZONE_TOP_LEFT)) * width
    right_x = (ZONE_TOP_RIGHT + t * (ZONE_BOTTOM_RIGHT - ZONE_TOP_RIGHT)) * width
    return left_x <= x <= right_x


detections = pd.read_csv(os.path.join(RESULTS_FOLDER, "detections.csv"))
clips = pd.read_csv(os.path.join(RESULTS_FOLDER, "clips.csv"))
people = detections[detections["class"] == "person"]

summary_rows = []
for i in range(len(clips)):
    clip_name = clips["clip"][i]
    total_frames = clips["frames"][i]
    fps = clips["fps"][i]
    width = clips["width"][i]
    height = clips["height"][i]

    clip_people = people[people["clip"] == clip_name]
    ped_frames = set()
    zone_frames = set()
    max_box_height = 0

    for j in range(len(clip_people)):
        row = clip_people.iloc[j]
        # feet position = bottom middle of the box
        feet_x = (row["x1"] + row["x2"]) / 2
        feet_y = row["y2"]
        box_height = row["y2"] - row["y1"]

        ped_frames.add(row["frame"])
        if point_in_zone(feet_x, feet_y, width, height):
            zone_frames.add(row["frame"])
        if box_height > max_box_height:
            max_box_height = box_height

    if len(ped_frames) > 0:
        first_ped_seconds = round(min(ped_frames) / fps, 2)
    else:
        first_ped_seconds = None  # no pedestrian seen in this clip

    zone_percent = round(100 * len(zone_frames) / total_frames, 1)
    summary_rows.append([clip_name, total_frames, round(total_frames / fps, 1), len(ped_frames),
                         len(zone_frames), zone_percent, round(len(zone_frames) / fps, 1),
                         first_ped_seconds, round(max_box_height)])
    print("done", clip_name, "-", len(ped_frames), "frames with a pedestrian,", len(zone_frames), "in the zone")

summary = pd.DataFrame(summary_rows, columns=["clip", "frames", "clip_seconds", "ped_frames", "zone_frames",
                                              "zone_percent", "zone_seconds", "first_ped_seconds", "max_box_height"])

labels = pd.read_csv(LABELS_FILE)
summary = summary.merge(labels, on="clip", how="left")
summary.to_csv(os.path.join(RESULTS_FOLDER, "summary.csv"), index=False)
print("saved results/summary.csv")

# chart 1: frames with a pedestrian in the danger zone, per clip
plt.figure(figsize=(10, 5))
plt.bar(summary["clip"], summary["zone_frames"])
plt.xticks(rotation=60)
plt.ylabel("frames with a pedestrian in the zone")
plt.title("Frames with a pedestrian in the danger zone, per clip")
plt.tight_layout()
plt.savefig(os.path.join(RESULTS_FOLDER, "zone_frames_per_clip.png"))
plt.close()

# chart 2: crosswalk vs no crosswalk, using percent because clips have different lengths
labelled = summary[summary["crosswalk"].notna()]
if len(labelled) == 0:
    print("my_labels.csv has no crosswalk values yet, so the crosswalk chart was skipped")
else:
    averages = labelled.groupby("crosswalk")["zone_percent"].mean()
    counts = labelled.groupby("crosswalk")["zone_percent"].count()
    bar_names = []
    for name in averages.index:
        bar_names.append("crosswalk: " + str(name) + " (" + str(counts[name]) + " clips)")
    plt.figure(figsize=(6, 5))
    plt.bar(bar_names, averages.values)
    plt.ylabel("average % of frames with a pedestrian in the zone")
    plt.title("Crosswalk vs no crosswalk")
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_FOLDER, "crosswalk_vs_none.png"))
    plt.close()

# chart 3: tallest pedestrian box in each frame of one clip, over time
example = people[people["clip"] == EXAMPLE_CLIP].copy()
example["box_height"] = example["y2"] - example["y1"]
tallest = example.groupby("frame")["box_height"].max()
fps = clips[clips["clip"] == EXAMPLE_CLIP]["fps"].iloc[0]
plt.figure(figsize=(10, 5))
plt.plot(tallest.index / fps, tallest.values, ".")
plt.xlabel("time in clip (seconds)")
plt.ylabel("tallest pedestrian box (pixels)")
plt.title("Pedestrian box height over time, " + EXAMPLE_CLIP)
plt.tight_layout()
plt.savefig(os.path.join(RESULTS_FOLDER, "box_height_" + EXAMPLE_CLIP + ".png"))
plt.close()

print("saved charts in results/")
