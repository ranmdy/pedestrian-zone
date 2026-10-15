# Pedestrian Zone

Measuring how often, and for how long, pedestrians are in the road space right in front of a car, using YOLO on dashcam clips from the JAAD dataset.

## Status

Work in progress. `detect.py` is done. `analyze.py`, `make_video.py` and the full results are still being written.

## Question

How often, and for how long, are pedestrians inside the area right in front of the car, and does this change between scenes with a crosswalk and scenes without one?

## Data

The clips come from JAAD (Joint Attention in Autonomous Driving), made by Amir Rasouli, Iuliia Kotseruba and John K. Tsotsos at York University. The annotations and code are at https://github.com/ykotseruba/JAAD.

The video clips are licensed under the Creative Commons Attribution 4.0 International License. The JAAD code is under the MIT License.

The videos are not included in this repository. To get them, download `JAAD_clips.zip` (about 3.1 GB) from the link in the JAAD README, unzip it, and copy the clips you want into a folder called `videos/` inside this project.

## Setup

Use Python 3.11. PyTorch does not support newer versions such as 3.14 yet.

```
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to run

```
python detect.py
```

This runs YOLOv8n on every clip in `videos/` and writes `results/detections.csv` (one row per detection) and `results/clips.csv` (frame count, fps and size of each clip).

## Reference

Rasouli, A., Kotseruba, I. and Tsotsos, J. K. (2017). Are They Going to Cross? A Benchmark Dataset and Baseline for Pedestrian Crosswalk Behavior. ICCV Workshops, pages 206-213.

Ultralytics YOLO documentation: https://docs.ultralytics.com
