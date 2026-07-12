# M09-03 — Colour-Range Segmentation

## Purpose
Demonstrate colour-range segmentation on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `red_range`: `[150, 255]`
- `green_range`: `[70, 210]`
- `blue_range`: `[50, 190]`

## Generated Artifacts
- `mask.png` — Colour-Range Mask
- `extracted_region.png` — Extracted Region
- `overlay.png` — Colour-Range Overlay

## Key Metrics
- Selected Pixels: 168119
- Rejected Pixels: 94025
- Selected Percentage: 64.132
- Rejected Percentage: 35.868

## Observation
The selected setup produced clear visual output; the leading reported metric is Selected Pixels = 168119.
