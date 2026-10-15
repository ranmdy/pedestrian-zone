# Test notes

This file records every test run, what came out, and what I changed because of it. Part 1 is the first test on 2 clips. Part 2 is the full run on the 18 clips used in the README.

# Part 1: first test on 2 clips (video_0001 and video_0002)

These two clips are a parking lot and an indoor garage. They were good for testing the code but are not in the final set of clips, because the question is about streets.

Date of run: 15 October 2026
Clips: video_0001 and video_0002 from JAAD_clips.zip
Settings: yolov8n.pt, CONF_MIN = 0.4, MAX_CLIPS = 2
Run time: about 38 seconds for 810 frames on CPU (Apple Silicon Mac)

## What detect.py wrote

results/clips.csv

| clip | frames | fps | width | height |
|---|---|---|---|---|
| video_0001 | 600 | 29.97 | 1920 | 1080 |
| video_0002 | 210 | 29.97 | 1920 | 1080 |

results/detections.csv has 8472 rows. Detections per class:

| clip | car | person | truck |
|---|---|---|---|
| video_0001 | 6915 | 600 | 62 |
| video_0002 | 631 | 264 | 0 |

No bicycle, motorcycle or bus was detected in these two clips.

## Person detections

| clip | frames with a person | first frame with a person | most persons in one frame | person box height in pixels (min / median / max) | median confidence |
|---|---|---|---|---|---|
| video_0001 | 552 of 600 | 0 | 2 | 70 / 220 / 448 | 0.77 |
| video_0002 | 184 of 210 | 23 | 3 | 166 / 279 / 359 | 0.72 |

## Quick comparison with the JAAD hand labels

I counted frames where JAAD has at least one box labelled "pedestrian" or "ped" (not "people", which are groups), and skipped boxes marked as outside the frame. This is a rough count of frames, not a box by box match. The box by box match is planned for check_against_jaad.py.

| clip | JAAD frames with a pedestrian | YOLO frames with a person | JAAD first frame | YOLO first frame | JAAD most in one frame | YOLO most in one frame |
|---|---|---|---|---|---|---|
| video_0001 | 600 | 552 | 0 | 0 | 3 | 2 |
| video_0002 | 192 | 184 | 18 | 23 | 2 | 3 |

## Things to keep in mind for analyze.py

1. The frame rate is 29.97, not exactly 30. analyze.py should use the fps value from clips.csv, not a fixed 30.
2. Both clips are 1920 x 1080, but other JAAD clips may differ, so the danger zone must be worked out from each clip's own width and height.
3. YOLO found a person in fewer frames than JAAD has labels for (552 vs 600, and 184 vs 192), and it found the first person in video_0002 five frames later than JAAD. This fits the known limitation that YOLO misses some pedestrians.
4. In video_0002, YOLO had a frame with 3 persons where JAAD has at most 2 pedestrians. Checked by eye in the annotated frame: YOLO drew two boxes on the same woman (confidence 0.45 and 0.79), so one person was counted twice.
5. Cars are by far the most common class in video_0001 (6915 detections, about 11.5 per frame). These are likely parked or nearby cars. They do not affect the pedestrian numbers but they make detections.csv large.
6. JAAD's own scene tags say video_0002 is "indoor" with no time of day or weather. It may not suit a crosswalk comparison, so I should watch it before deciding to keep it in the final 15 to 20 clips.

## analyze.py and make_video.py on the same 2 clips

First zone tried: top 0.68, bottom 0.88, top edge 0.42 to 0.58, bottom edge 0.25 to 0.75.
In the annotated frame 100 of video_0002, two people walking right in front of the car were drawn as outside the zone. Their feet are hidden by the car's hood, so YOLO's box stops at the hood line (about 0.89 to 0.90 of the height), just below the 0.88 edge.

Zone changed to: top 0.68, bottom 0.95, top edge 0.42 to 0.58, bottom edge 0.20 to 0.80. Both people are now inside.

| clip | zone_frames with bottom 0.88 | zone_frames with bottom 0.95 |
|---|---|---|
| video_0001 | 284 | 278 |
| video_0002 | 24 | 107 |

summary.csv with the new zone:

| clip | frames | ped_frames | zone_frames | zone_percent | zone_seconds | first_ped_seconds | max_box_height |
|---|---|---|---|---|---|---|---|
| video_0001 | 600 | 552 | 278 | 46.3 | 9.3 | 0.0 | 448 |
| video_0002 | 210 | 184 | 107 | 51.0 | 3.6 | 0.77 | 359 |

The box height chart for video_0001 jumps down at about 2.2 seconds. Because there is no tracking, the chart shows the tallest person in each frame, and when the closest person leaves the frame the line switches to someone further away.

The crosswalk chart was tested with two fake label rows in a separate scratch folder (deleted afterwards). It draws correctly. my_labels.csv in this project is still empty.

## check_against_jaad.py on the same 2 clips

Boxes marked as fully occluded in JAAD are skipped. A JAAD box counts as found when a YOLO person box overlaps it with IoU of at least 0.5, and each YOLO box can only be used once.

| clip | JAAD boxes | found | missed | missed % | missed small (under 100 px) | missed large |
|---|---|---|---|---|---|---|
| video_0001 | 849 | 587 | 262 | 30.9 | 177 | 85 |
| video_0002 | 324 | 216 | 108 | 33.3 | 0 | 108 |

Looking closer at video_0002:
- Only 10 of the 324 JAAD boxes had no YOLO box touching them at all.
- 38 misses are cases where both JAAD pedestrians in a frame match the same YOLO box best. Each YOLO box can only be used once, so the second one counts as missed. This is likely when the two walkers overlap in the image, but I have not checked those frames by eye.
- 58 of the other 70 misses overlap a YOLO box by 0.3 to 0.5 IoU, which is just under the 0.5 rule. In frame 100, the JAAD boxes go about 10 to 20 pixels lower than YOLO's, past the hood line.
So "missed" here partly means "detected, but the box does not line up well enough", not only "not seen".


# Part 2: full run on 18 clips

Date of run: 15 October 2026
Settings: yolov8n.pt, CONF_MIN = 0.4, MAX_CLIPS = 0, zone top 0.68, bottom 0.95, top edge 0.42 to 0.58, bottom edge 0.20 to 0.80
Run time: detect.py took about 90 seconds for all 18 clips (5010 frames) on CPU

## How the clips were chosen

I listed all 346 JAAD clips with their JAAD tags (time of day, weather, location, road type), their size, and two counts from the JAAD annotation files: frames with a labelled pedestrian, and frames where the traffic file marks a pedestrian crossing.

What the full dataset looks like:
- Width: 336 clips are 1920 wide, 10 are 1280 wide.
- Time of day (JAAD tag): 336 daytime, 4 nighttime, 4 afternoon, 1 evening.
- Weather (JAAD tag): 166 clear, 143 cloudy, 28 rain, 6 snow, 1 "cloud".
- Location (JAAD tag): 306 street, 38 plaza, 2 indoor.

After keeping street location, street road type, 1920 x 1080 and at least 30 frames with a pedestrian, there were 175 clips with a crossing and 106 without. From these I took 9 of each, as described in the README.

## Checking the zone on every clip

Before running YOLO, I drew the zone on the middle frame of each of the 18 clips and looked at all of them together. In every clip the zone sits on the road ahead, with the top edge just under the horizon and the bottom edge over the hood. The three clips from the second camera (video_0099, video_0127, video_0137) sit a little differently, but the zone is still on the road. I did not change the zone.

While doing this I saw that JAAD tags video_0127 as nighttime, but the frames are in daylight with snow. My own labels should record what I actually see.

## detect.py

All 18 clips opened and ran. 19517 detections were kept: 13468 car, 5446 person, 385 truck, 217 bus, 1 bicycle, 0 motorcycle.

Frame rates read from the videos: 29.97 fps for most clips, 30.0 for video_0099, video_0127 and video_0137, and 59.94 for video_0039 and video_0041. This is why analyze.py reads fps from clips.csv instead of using 30.

## analyze.py

Before running, I changed EXAMPLE_CLIP from video_0001 to video_0046, because video_0001 is not in the new set and the box height chart would have had no data. I chose video_0046 because it has one pedestrian crossing at a crosswalk. With no tracking, a clip with one pedestrian gives the clearest chart.

The crosswalk chart was skipped because my_labels.csv is still empty. That is expected.

The full summary table is in the README Results section.

### Things in the results I checked by hand

1. Very tall person boxes in video_0099, video_0127 and video_0137 (935, 734 and 683 px). I sorted the person boxes in these clips by height. The tallest ones all start at the top of the image (y1 under 20) and on the right side (x1 over 1300). That is the dark camera mount in the corner. There were 24 such boxes (2 + 20 + 2), with confidence 0.41 to 0.49. None of them had their feet point in the zone, so zone_frames does not change. Without them, max_box_height would be 415, 247 and 464, and ped_frames for video_0127 would be 129 instead of 133. No other clip has boxes in that corner.
2. Tall person boxes in video_0020 (up to 657 px). These are on the left edge of the image, on a large statue of human figures beside the road. They are not in the zone.
3. video_0023 has 0 frames with a pedestrian. JAAD has pedestrians in 185 of its 240 frames. See the JAAD check below.
4. The box height chart for video_0046 rises from about 60 px to 340 px over 6.6 seconds as the car gets closer to the pedestrian, then drops. The pedestrian has left the frame, and the last few points are a different, smaller pedestrian.

## make_video.py

I set CLIP_NAME = "video_0046". The pedestrian's feet are in the zone from frame 55 to frame 134, and I chose frame 94 (in the middle) as SNAPSHOT_FRAME. In that frame the pedestrian is on the marked crosswalk and drawn in red, and a car further up the road is drawn in blue. The video is results/example_video_0046.mp4, 210 frames. It is not committed because .gitignore leaves out results/*.mp4.

## check_against_jaad.py

CHECK_CLIPS = video_0023, video_0039, video_0046. I picked them to be different: night and rain, a busy city crossing, and a quiet daytime crossing with one person.

| clip | JAAD boxes | found | missed | missed % | missed small | missed large |
|---|---|---|---|---|---|---|
| video_0023 | 394 | 0 | 394 | 100.0 | 232 | 162 |
| video_0039 | 1762 | 865 | 897 | 50.9 | 469 | 428 |
| video_0046 | 200 | 157 | 43 | 21.5 | 31 | 12 |

Extra test on video_0023, to see if the confidence limit was the reason: I ran YOLO on the clip with conf = 0.05 and only the person class. This was a separate test, so it does not change detections.csv. It found 38 person boxes in total. The highest confidence was 0.36, and only 3 of 240 frames had a person at 0.25 or more. So lowering CONF_MIN would not fix this clip. The model does not see these pedestrians in the dark and rain.

## Comparison using JAAD's crossing flag (not my labels)

This table groups the clips by the JAAD flag that was used to choose them. It is here only as a check of the pipeline. The README chart uses my own labels. I should fill in my_labels.csv before reading this, so I am not influenced by it.

| JAAD crossing flag | clips | mean zone_percent | median zone_percent | clips with 0 zone frames | mean zone_seconds |
|---|---|---|---|---|---|
| no | 9 | 14.6 | 6.1 | 3 | 1.3 |
| yes | 9 | 23.9 | 10.6 | 4 | 1.5 |

The means are pulled up a lot by single clips (video_0039 at 91.9% in the crossing group, video_0137 at 74.8% in the other group), and the crossing group includes the night clip where YOLO found nobody. With 9 clips per group, this difference should not be read as a real effect.

## List of checks done

- detect.py: ran on a made-up video and on a broken file (skipped with a message), then on 2 clips, then on all 18.
- analyze.py: ran with empty labels (crosswalk chart skipped with a message) and with two fake label rows in a separate scratch folder (crosswalk chart drawn correctly; the fake labels were deleted and never used in this project).
- point_in_zone: checked by eye on the annotated frames, where people with feet inside the yellow trapezoid are red and people outside are green.
- Zone position: checked on a middle frame of every clip.
- Unusual numbers: every very tall box and the clip with zero pedestrians were looked into (see above).
- check_against_jaad.py: on 2 test clips I also checked the matching by hand for one frame (video_0002, frame 100), and checked why some boxes were counted as missed.
- All scripts are under about 125 lines, use plain settings at the top, and have no classes.
