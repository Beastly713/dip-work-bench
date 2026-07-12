# M09-02 — Intensity-Range Thresholding

## Purpose
Demonstrate intensity-range thresholding on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `intensity_range`: `[80, 180]`
- `include_boundaries`: `True`

## Generated Artifacts
- `mask.png` — Intensity-Range Mask
- `overlay.png` — Selected-Range Overlay

## Key Metrics
- Selected Pixels: 173762
- Rejected Pixels: 88382
- Selected Percentage: 66.285
- Rejected Percentage: 33.715

## Observation
The selected setup produced clear visual output; the leading reported metric is Selected Pixels = 173762.
