# M06-05 — Unsharp Masking

## Purpose
Demonstrate unsharp masking on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `kernel_size`: `5`
- `sigma`: `1.0`
- `amount`: `0.7`

## Generated Artifacts
- `result.png` — Unsharp Image
- `blurred_image.png` — Blurred Image
- `detail_mask.png` — Detail Mask

## Key Metrics
- Detail Minimum: -52.704
- Detail Maximum: 68.090
- Detail Standard Deviation: 5.470
- Input Standard Deviation: 47.855
- Output Standard Deviation: 49.003

## Observation
The selected setup produced clear visual output; the leading reported metric is Detail Minimum = -52.704.
