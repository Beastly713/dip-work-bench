# M10-04 — Hough Line Detection

## Purpose
Demonstrate hough line detection on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `canny_low`: `50`
- `canny_high`: `150`
- `rho_resolution`: `1.0`
- `theta_resolution_degrees`: `1.0`
- `vote_threshold`: `50`
- `minimum_line_length`: `30`
- `maximum_line_gap`: `10`
- `maximum_lines`: `30`

## Generated Artifacts
- `overlay.png` — Detected Lines
- `line_edge_map.png` — Canny Edge Map
- `line_detections.csv` — Line Detections

## Key Metrics
- Detected Lines: 30
- Total Line Length: 2970.088
- Longest Line Length: 132.000

## Observation
The selected setup produced clear visual output; the leading reported metric is Detected Lines = 30.
