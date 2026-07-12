# M10-06 — Harris Corner Detection

## Purpose
Demonstrate harris corner detection on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `block_size`: `2`
- `aperture_size`: `3`
- `harris_k`: `0.04`
- `quality_level`: `0.01`
- `minimum_distance`: `10`
- `maximum_corners`: `100`
- `subpixel_refinement`: `False`

## Generated Artifacts
- `overlay.png` — Detected Corners
- `harris_response.png` — Harris Response
- `corner_detections.csv` — Corner Detections

## Key Metrics
- Detected Corners: 100
- Maximum Harris Response: 25502720.000
- Response Threshold: 255027.200

## Observation
The selected setup produced clear visual output; the leading reported metric is Detected Corners = 100.
