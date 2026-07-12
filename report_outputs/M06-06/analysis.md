# M06-06 — High-Boost Filtering

## Purpose
Demonstrate high-boost filtering on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `kernel_size`: `5`
- `sigma`: `1.0`
- `boost`: `1.8`

## Generated Artifacts
- `result.png` — High-Boost Image
- `blurred_image.png` — Blurred Image
- `detail_mask.png` — Detail Mask

## Key Metrics
- Detail Minimum: -52.704
- Detail Maximum: 68.090
- Detail Standard Deviation: 5.470
- Input Standard Deviation: 47.855
- Output Standard Deviation: 51.274

## Observation
The selected setup produced clear visual output; the leading reported metric is Detail Minimum = -52.704.
