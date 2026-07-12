# M10-01 — Canny Edge Detection

## Purpose
Demonstrate canny edge detection on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `blur_kernel`: `5`
- `sigma`: `1.0`
- `low_threshold`: `50`
- `high_threshold`: `150`
- `aperture_size`: `3`
- `l2_gradient`: `True`

## Generated Artifacts
- `result.png` — Canny Edge Map
- `smoothed_input.png` — Smoothed Input

## Key Metrics
- Edge Pixels: 12228
- Edge Percentage: 4.665

## Observation
The selected setup produced clear visual output; the leading reported metric is Edge Pixels = 12228.
