# M06-02 — Sobel Edge Enhancement

## Purpose
Demonstrate sobel edge enhancement on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `kernel_size`: `3`
- `scale`: `1.0`
- `threshold_enabled`: `False`
- `threshold`: `100`

## Generated Artifacts
- `sobel_x.png` — Horizontal Response
- `sobel_y.png` — Vertical Response
- `sobel_magnitude.png` — Sobel Edge Result
- `triptych.png` — Directional response triptych

## Key Metrics
- Gx Minimum: -688.000
- Gx Maximum: 640.000
- Gy Minimum: -644.000
- Gy Maximum: 469.000
- Magnitude Maximum: 709.074

## Observation
The selected setup produced clear visual output; the leading reported metric is Gx Minimum = -688.000.
