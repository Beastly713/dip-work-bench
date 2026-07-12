# M10-05 — Hough Circle Detection

## Purpose
Demonstrate hough circle detection on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `median_kernel`: `5`
- `dp`: `1.2`
- `minimum_distance`: `20`
- `canny_high_threshold`: `100.0`
- `accumulator_threshold`: `30.0`
- `minimum_radius`: `5`
- `maximum_radius`: `80`
- `maximum_circles`: `10`

## Generated Artifacts
- `overlay.png` — Detected Circles
- `circle_preprocessed.png` — Median-Blurred Input
- `circle_detections.csv` — Circle Detections

## Key Metrics
- Detected Circles: 10
- Average Radius: 76.376
- Largest Radius: 79.280

## Observation
The selected setup produced clear visual output; the leading reported metric is Detected Circles = 10.
